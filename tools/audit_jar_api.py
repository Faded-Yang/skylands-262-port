#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_jar_api.py —— 全量审计**任意 mod jar** 对某个 MC 版本的 API 引用缺口。

> 由 `audit_create_api.py`（Create-Fly 26.2→26.3 专用）泛化而来。
> `audit_create_api.py` **保留原样**（不动历史工具）；本文件是其通用版：
>   参数：`audit_jar_api.py <jar> [--mc 26.3|<path>] [--txt ..] [--json ..]`
> 已去掉 Create 特有过滤；**两个假阳性修法照旧保留**：
>   (1) `parse_javap` 里 **interface 的 `extends` 列表要当成 interfaces 而不是 super**
>       —— 否则接口的父接口方法会被当成「不存在」；
>   (2) 解析链里 **JDK 父类 / `java/lang/Object`** 一律视为已解析（`chain()` 里 `java/` 前缀特例）。

## 它做什么

1. 逐个解析 jar 内全部 .class 的常量池 **和字节码**，收集指向 `net/minecraft/**`
   与 `com/mojang/**` 的引用：
     - CONSTANT_Methodref / InterfaceMethodref -> owner + name + descriptor
     - CONSTANT_Fieldref                      -> owner + name + descriptor
     - CONSTANT_Class                         -> 类名
   「引用次数」= 字节码里真正引用该常量池条目的指令条数（getstatic/invokevirtual/new/...），
   不是常量池条目数；另列 cp 条目数（去重后每个 class 最多 1）。
2. 用 javap -p -s 按 owner 批量核对 26.3（+ 其依赖库）里：
     - 类是否存在（A 类）
     - 方法是否存在（B 类；**沿父类/接口链解析**，避免把继承来的方法误判为缺失）
     - 字段是否存在（C 类）
     - 名字在、描述符不在 -> D 类（描述符不符）
3. 输出分级表 + JSON。A/B/C/D 每级按引用次数降序，并给出「涉及的 Create 类数量」
   （= 决定能不能批量修的关键指标）。

## 分级定义

  A : 类整个不存在
  B : 类在、方法名在整个继承链里都找不到
  C : 类在、字段名在整个继承链里都找不到
  D : 名字在（同类/父类），但没有任何一个描述符与引用点一致

D 里再细分 `D-method` / `D-field`。B/C 行里额外标出：
  - `疑似改名`：同类里有**同描述符**的别的名字（B: 方法；C: 字段）
  - `疑似换签名`：同类里有同名但别的描述符（本来就会归到 D）

## 可修性判断（自动给出，供人复核）

  B/C/D 全部可以在**常量池层面**改 owner（方法引用与字段引用都一样：JVM 按
  owner+name+desc 解析）——前提是我们写一个同名同描述符的桥接成员。
    - 有「疑似改名」-> 桥接方法体直接转调新名字（最省事）
    - 无 -> 桥接方法体要手写（返回占位值 = 语义降级；或实现等价逻辑）
  A 只能提供同名占位类，风险最高。

## 用法

    python tools/audit_jar_api.py work/run26/port/foo/foo-1.21.1.jar
    python tools/audit_jar_api.py <jar> --mc 26.3 --no-cache
    python tools/audit_jar_api.py <jar> --mc 26.2 --txt a.txt --json a.json

输出（缺省）：notes\\jar-api-audit\\<jar名>.txt + .json
            javap 缓存：tools\\.cache\\jarapiaudit\\javap-cache-<mcver>.json
"""
import argparse
import concurrent.futures
import json
import os
import re
import sys
import time
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MC_HOME = Path(r"C:\Users\95959\AppData\Roaming\.minecraft")
DEFAULT_MC_VER = "26.3"
JAVAP = MC_HOME / "runtime" / "java-runtime-epsilon" / "bin" / "javap.exe"

# 缓存/输出按 MC 版本 + jar 名分开（缓存只按类名 key，混版本会串味）
def cache_file(mc_ver):
    return ROOT / "tools" / ".cache" / "jarapiaudit" / ("javap-cache-%s.json" % mc_ver)


OUTDIR = ROOT / "notes" / "jar-api-audit"

NAMESPACES = ("net/minecraft/", "com/mojang/")

# 视为「平台/JDK」的前缀：这些类不在 mc jar 里也不需要审计
JDK_PREFIXES = ("java/", "javax/", "jdk/", "sun/", "com/sun/")

# ---------------------------------------------------------------- class parsing


def parse_pool(buf):
    """返回 (entries, pool_end)。entries 是 [(tag, start, end)]，按 cp index 顺序。"""
    if buf[:4] != b"\xca\xfe\xba\xbe":
        raise ValueError("not a class file")
    pos = 8
    count = u2(buf, pos)
    pos += 2
    entries = []
    i = 1
    while i < count:
        tag = buf[pos]
        start = pos
        if tag == 1:                                  # Utf8
            ln = u2(buf, pos + 1)
            pos += 3 + ln
        elif tag in (3, 4):                           # Integer / Float
            pos += 5
        elif tag in (5, 6):                           # Long / Double（占 2 槽）
            pos += 9
        elif tag in (7, 8, 16, 19, 20):               # Class / String / MethodType / Module / Package
            pos += 3
        elif tag in (9, 10, 11, 12, 17, 18):          # refs / NameAndType / (Invoke)Dynamic
            pos += 5
        elif tag == 15:                               # MethodHandle
            pos += 4
        else:
            raise ValueError("unknown constant pool tag %d at %d" % (tag, pos))
        entries.append((tag, start, pos))
        i += 2 if tag in (5, 6) else 1
    return entries, pos


def u2(buf, off):
    return int.from_bytes(buf[off:off + 2], "big")


def u4(buf, off):
    return int.from_bytes(buf[off:off + 4], "big")


def utf8_value(buf, start):
    ln = u2(buf, start + 1)
    return buf[start + 3:start + 3 + ln].decode("utf-8", "replace")


def build_len_table():
    L = [1] * 256
    for op in range(0x15, 0x1A):      # iload..aload
        L[op] = 2
    for op in range(0x36, 0x3B):      # istore..astore
        L[op] = 2
    for op in range(0x99, 0xA9):      # if<cond>, goto, jsr
        L[op] = 3
    L[0x10] = 2                       # bipush
    L[0x11] = 3                       # sipush
    L[0x12] = 2                       # ldc
    L[0x13] = 3                       # ldc_w
    L[0x14] = 3                       # ldc2_w
    L[0x84] = 3                       # iinc
    L[0xA9] = 2                       # ret
    for op in range(0xB2, 0xB9):      # get/put/invoke
        L[op] = 3
    L[0xB9] = 5                       # invokeinterface
    L[0xBA] = 5                       # invokedynamic
    L[0xBB] = 3                       # new
    L[0xBC] = 2                       # newarray
    L[0xBD] = 3                       # anewarray
    L[0xC0] = 3                       # checkcast
    L[0xC1] = 3                       # instanceof
    L[0xC5] = 4                       # multianewarray
    L[0xC6] = 3                       # ifnull
    L[0xC7] = 3                       # ifnonnull
    L[0xC8] = 5                       # goto_w
    L[0xC9] = 5                       # jsr_w
    return L


ILEN = build_len_table()

# opcode -> ('M'|'F'|'C', 操作数宽度)
SITE_OPS = {}
for _op in (0xB2, 0xB3, 0xB4, 0xB5):
    SITE_OPS[_op] = ("F", 2)
for _op in (0xB6, 0xB7, 0xB8, 0xB9):
    SITE_OPS[_op] = ("M", 2)
for _op in (0xBB, 0xBD, 0xC0, 0xC1, 0xC5):
    SITE_OPS[_op] = ("C", 2)
SITE_OPS[0x12] = ("L", 1)
SITE_OPS[0x13] = ("L", 2)
SITE_OPS[0x14] = ("L", 2)


def iter_sites(code):
    """遍历字节码，yield (kind, cp_index)。kind: M/F/C/L(ldc 类常量)。"""
    i = 0
    n = len(code)
    while i < n:
        op = code[i]
        rec = SITE_OPS.get(op)
        if rec:
            kind, w = rec
            idx = code[i + 1] if w == 1 else u2(code, i + 1)
            yield kind, idx
            i += ILEN[op]
        elif op == 0xAA:                       # tableswitch
            pad = (4 - ((i + 1) % 4)) % 4
            base = i + 1 + pad
            low = int.from_bytes(code[base + 4:base + 8], "big", signed=True)
            high = int.from_bytes(code[base + 8:base + 12], "big", signed=True)
            i = base + 12 + 4 * max(0, high - low + 1)
        elif op == 0xAB:                       # lookupswitch
            pad = (4 - ((i + 1) % 4)) % 4
            base = i + 1 + pad
            npairs = int.from_bytes(code[base + 4:base + 8], "big", signed=True)
            i = base + 8 + 8 * max(0, npairs)
        elif op == 0xC4:                       # wide
            i += 6 if code[i + 1] == 0x84 else 4
        else:
            i += ILEN[op]


def skip_attr(buf, pos):
    ln = u4(buf, pos + 2)
    return pos + 6 + ln


def parse_class(data):
    """返回 dict(name, supers(list), interfaces(list), methods{name:{desc}}, fields{name:{desc}},
    member_refs{key: (tag, owner, name, desc)}, class_refs{name}, sites[(kind, cp_idx)])。"""
    entries, pool_end = parse_pool(data)
    cp = {}
    i = 1
    for tag, s, e in entries:
        cp[i] = (tag, s, e)
        i += 2 if tag in (5, 6) else 1

    utf8_cache = {}

    def utf8(idx):
        v = utf8_cache.get(idx)
        if v is None:
            tag, s, e = cp[idx]
            if tag != 1:
                raise ValueError("cp %d is not Utf8" % idx)
            v = utf8_value(data, s)
            utf8_cache[idx] = v
        return v

    def cls_name(idx):
        tag, s, e = cp[idx]
        if tag != 7:
            return None
        return utf8(u2(data, s + 1))

    pos = pool_end
    access = u2(data, pos)
    this_name = cls_name(u2(data, pos + 2))
    pos += 6
    icount = u2(data, pos)
    pos += 2
    interfaces = []
    for _ in range(icount):
        nm = cls_name(u2(data, pos))
        if nm:
            interfaces.append(nm)
        pos += 2
    supers = []
    sup = cls_name(u2(data, pool_end + 4))
    if sup and sup != "java/lang/Object":
        supers.append(sup)

    def read_members(pos):
        count = u2(data, pos)
        pos += 2
        out = {}
        for _ in range(count):
            mname = utf8(u2(data, pos + 2))
            mdesc = utf8(u2(data, pos + 4))
            acount = u2(data, pos + 6)
            pos += 8
            attrs = []
            for _ in range(acount):
                aname = utf8(u2(data, pos))
                alen = u4(data, pos + 2)
                attrs.append((aname, pos + 6, alen))
                pos += 6 + alen
            out.setdefault(mname, {})[mdesc] = attrs
        return out, pos

    fields, pos = read_members(pos)
    methods, pos = read_members(pos)

    # 常量池里的引用
    member_refs = {}
    class_refs = set()
    for idx, (tag, s, e) in cp.items():
        if tag == 7:
            nm = cls_name(idx)
            if nm:
                class_refs.add(nm)
        elif tag in (9, 10, 11):
            owner = cls_name(u2(data, s + 1))
            nat = u2(data, s + 3)
            if owner is None or nat not in cp:
                continue
            ns = cp[nat][1]                    # NameAndType: tag,name_index,desc_index
            nm = utf8(u2(data, ns + 1))
            ds = utf8(u2(data, ns + 3))
            member_refs[idx] = ("F" if tag == 9 else "M", owner, nm, ds)

    sites = []
    for mname, descs in methods.items():
        for mdesc, attrs in descs.items():
            for aname, apos, alen in attrs:
                if aname != "Code":
                    continue
                clen = u4(data, apos + 4)
                cstart = apos + 8
                code = data[cstart:cstart + clen]
                for kind, cp_idx in iter_sites(code):
                    if kind == "L":            # ldc / ldc_w / ldc2_w
                        e = cp.get(cp_idx)
                        if e and e[0] == 7:
                            cn = cls_name(cp_idx)
                            if cn:
                                sites.append(("C", cn, None, None))
                        continue
                    ref = member_refs.get(cp_idx)
                    if ref:
                        sites.append(ref)
    return dict(
        name=this_name,
        supers=supers,
        interfaces=interfaces,
        methods={k: set(v) for k, v in methods.items()},
        fields={k: set(v) for k, v in fields.items()},
        member_refs=member_refs,
        class_refs=class_refs,
        sites=sites,
    )


# ---------------------------------------------------------------- javap oracle

HEADER_RE = re.compile(
    r"^(?:public |protected |private |static |final |abstract |sealed |non-sealed |strictfp )*"
    r"(@interface|interface|class|enum|record)\s+([\w.$]+)")


def split_top(s, sep=","):
    """按顶层分隔符切分（忽略 <> 内的逗号）。"""
    out, buf, depth = [], [], 0
    for ch in s:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        if ch == sep and depth == 0:
            out.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        out.append("".join(buf).strip())
    return [x for x in out if x]


def parse_javap(text):
    lines = text.splitlines()
    kind = None
    head_i = None
    for i, ln in enumerate(lines):
        m = HEADER_RE.match(ln)
        if m:
            kind = m.group(1)
            head_i = i
            break
    if kind is None:
        return None
    head = []
    for ln in lines[head_i:head_i + 8]:
        head.append(ln)
        if "{" in ln:
            break
    headtxt = re.sub(r"\s+", " ", "".join(head))
    supers, interfaces = [], []
    if kind in ("interface", "@interface"):
        em = re.search(r"\bextends\s+(.+?)\s*\{", headtxt)
        if em:
            for x in split_top(em.group(1)):
                x = re.sub(r"<.*$", "", x).strip()
                if re.match(r"^[\w.$]+$", x):
                    interfaces.append(x)
    else:
        em = re.search(r"\bextends\s+([\w.$]+)", headtxt)
        if em:
            supers.append(em.group(1))
        im = re.search(r"\bimplements\s+(.+?)\s*\{", headtxt)
        if im:
            for x in split_top(im.group(1)):
                x = re.sub(r"<.*$", "", x).strip()
                if re.match(r"^[\w.$]+$", x):
                    interfaces.append(x)
    sm = re.search(r"(?:class|interface|enum|record|@interface)\s+([\w.$]+)", headtxt)
    simple = sm.group(1).split(".")[-1] if sm else ""

    methods, fields = defaultdict(set), defaultdict(set)
    final_methods = set()
    cur = None
    blocks = []
    for ln in lines[head_i + 1:]:
        if ln.rstrip() == "}":
            break
        if ln.startswith("  ") and not ln.startswith("    "):
            if cur:
                blocks.append(cur)
            cur = [ln]
        elif cur is not None:
            cur.append(ln)
    if cur:
        blocks.append(cur)
    for blk in blocks:
        flat = "".join(x.rstrip() for x in blk)
        dm = re.search(r"descriptor:\s*(\S+)", flat)
        if not dm:
            continue
        desc = dm.group(1)
        sig = flat[:dm.start()]
        if "(" in sig:
            pre = sig[:sig.index("(")]
            nm = re.search(r"([\w$]+)\s*$", pre)
            if not nm:
                continue
            name = nm.group(1)
            if name == simple:
                name = "<init>"
            methods[name].add(desc)
            if re.search(r"\bfinal\b", pre) and not re.search(r"\bprivate\b", pre):
                final_methods.add(name + "|" + desc)
        else:
            nm = re.search(r"([\w$]+)\s*;\s*$", sig)
            if nm:
                fields[nm.group(1)].add(desc)
    return dict(kind=kind, supers=supers, interfaces=interfaces,
                methods={k: sorted(v) for k, v in methods.items()},
                fields={k: sorted(v) for k, v in fields.items()},
                final_methods=sorted(final_methods))


def jvm_name(fqn):
    return fqn.replace(".", "/")


def dot_name(jvm):
    return jvm.replace("/", ".")


PKG_RE = re.compile(r"L([\w/$]+);")


def desc_key(d):
    """把描述符里的类型换成简单名（只看形状，不看包）。"""
    return PKG_RE.sub(lambda m: "L" + m.group(1).split("/")[-1] + ";", d)


class Oracle:
    """javap 批量查询 + 缓存。"""

    def __init__(self, cp_jars, known, cache_path, use_cache=True, workers=6):
        self.cp = os.pathsep.join(str(p) for p in cp_jars)
        self.known = known            # set of jvm class names
        self.cache = {}
        self.workers = workers
        self.dirty = False
        self.cache_path = Path(cache_path)
        if use_cache and self.cache_path.is_file():
            try:
                d = json.loads(self.cache_path.read_text(encoding="utf-8"))
                if d.get("schema") == 2:
                    self.cache = d.get("classes", {})
            except Exception:
                self.cache = {}

    def info(self, jvm):
        return self.cache.get(jvm)

    def ensure(self, names):
        todo = [n for n in sorted(set(names)) if n not in self.cache]
        if not todo:
            return
        t0 = time.time()
        chunks = [todo[i:i + 40] for i in range(0, len(todo), 40)]
        done = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as ex:
            futs = {ex.submit(self._batch, ch): ch for ch in chunks}
            for fut in concurrent.futures.as_completed(futs):
                ch = futs[fut]
                try:
                    got = fut.result()
                except Exception as e:
                    got = {}
                    eprint("[warn] javap 批失败: %s" % e)
                for fqn in ch:
                    d = got.get(fqn)
                    self.cache[fqn] = d if d else {"missing": True}
                done += len(ch)
                eprint("  [javap] %d/%d (%.1fs)" % (done, len(todo), time.time() - t0))
        self.dirty = True
        eprint("  [javap] 完成 %d 个类，%.1fs" % (len(todo), time.time() - t0))

    def _batch(self, names):
        cmd = [str(JAVAP), "-p", "-s", "-cp", self.cp] + [dot_name(n) for n in names]
        try:
            r = __import__("subprocess").run(cmd, capture_output=True, text=True,
                                             encoding="utf-8", errors="replace", timeout=240)
        except Exception:
            return {}
        out = {}
        for fqn, d in parse_sections(r.stdout).items():
            out[jvm_name(fqn)] = d
        return out

    def save(self):
        if not self.dirty:
            return
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps({"schema": 2, "classes": self.cache},
                                         ensure_ascii=False), encoding="utf-8")


def parse_sections(text):
    secs, cur = [], None
    for ln in text.splitlines():
        if HEADER_RE.match(ln):
            if cur:
                secs.append(cur)
            cur = [ln]
        elif cur is not None:
            cur.append(ln)
    if cur:
        secs.append(cur)
    out = {}
    for sec in secs:
        d = parse_javap("\n".join(sec))
        if not d:
            continue
        m = HEADER_RE.match(sec[0])
        if m:
            out[m.group(2)] = d
    return out


def eprint(*a):
    print(*a, file=sys.stderr, flush=True)


# ---------------------------------------------------------------- resolution

def make_resolver(oracle):
    chain_cache = {}

    def chain(jvm):
        """BFS 继承链（含自身），按需 javap。返回 [jvm,...]。"""
        if jvm in chain_cache:
            return chain_cache[jvm]
        out, seen, stack = [], set(), [jvm, "java/lang/Object"]
        while stack:
            c = stack.pop(0)
            if c in seen:
                continue
            seen.add(c)
            if c not in oracle.known and not c.startswith("java/"):
                continue
            info = oracle.cache.get(c)
            if not info or info.get("missing"):
                continue
            out.append(c)
            for p in info.get("supers", []) + info.get("interfaces", []):
                pj = jvm_name(p)
                if pj not in seen:
                    stack.append(pj)
        chain_cache[jvm] = out
        return out

    def resolve(owner, kind, name, desc):
        """返回 (status, where, alts)。
        status: ok / missing_name / missing_desc
        where : 命中或最近声明类
        alts  : 该名字下所有描述符 list
        """
        where = None
        alts = []
        for c in chain(owner):
            info = oracle.cache.get(c) or {}
            table = info.get("methods" if kind == "M" else "fields") or {}
            if name in table:
                where = where or c
                alts.extend(table[name])
                if desc in table[name]:
                    return "ok", c, sorted(set(alts))
        if where:
            return "missing_desc", where, sorted(set(alts))
        return "missing_name", None, []

    return resolve


# ---------------------------------------------------------------- main

def resolve_mc(arg):
    """--mc 既接受版本号（26.3）也接受 jar 路径。返回 (mc_path, mc_ver)。"""
    p = Path(arg)
    if p.is_file():
        return p, "%s @ %s" % (p.stem, p.parent.name)
    mc_ver = arg.strip()
    return MC_HOME / "versions" / mc_ver / (mc_ver + ".jar"), mc_ver


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jar", nargs="?", default=None, help="要审计的 mod jar（缺省则报错）")
    ap.add_argument("--mc", default=DEFAULT_MC_VER, help="MC 版本号（26.3）或 jar 路径")
    ap.add_argument("--txt", default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--top", type=int, default=80)
    args = ap.parse_args()

    t0 = time.time()
    if not args.jar:
        print(__doc__)
        return 2
    jar = Path(args.jar)
    mc, mc_ver = resolve_mc(args.mc)
    if not jar.is_file():
        eprint("jar 不存在: %s" % jar)
        return 2
    if not mc.is_file():
        eprint("MC jar 不存在: %s" % mc)
        return 2
    stem = re.sub(r"[^\w.+-]+", "_", jar.stem)[:80]
    out_txt = Path(args.txt) if args.txt else OUTDIR / (stem + ".txt")
    out_json = Path(args.json) if args.json else OUTDIR / (stem + ".json")

    # ---- 1. MC 类索引 + 依赖库 classpath
    mcz = zipfile.ZipFile(mc)
    mc_names = {n[:-6] for n in mcz.namelist() if n.endswith(".class")}
    mcz.close()

    cp_jars = [mc]
    vjson = mc.with_suffix(".json")
    if vjson.is_file():
        try:
            vd = json.loads(vjson.read_text(encoding="utf-8"))
            for lib in vd.get("libraries", []):
                art = (lib.get("downloads") or {}).get("artifact") or {}
                p = art.get("path")
                if not p:
                    continue
                full = MC_HOME / "libraries" / p
                if full.is_file():
                    cp_jars.append(full)
                    try:
                        z = zipfile.ZipFile(full)
                        mc_names.update(n[:-6] for n in z.namelist() if n.endswith(".class"))
                        z.close()
                    except Exception:
                        pass
        except Exception as e:
            eprint("[warn] 读 26.3.json 失败: %s" % e)

    # ---- 2. 解析本 jar 全部 class
    z = zipfile.ZipFile(jar)
    names = z.namelist()
    class_entries = [n for n in names if n.endswith(".class") and not n.startswith("META-INF/")]
    eprint("jar: %s (%d 条目 / %d class)" % (jar.name, len(names), len(class_entries)))

    member_refs = defaultdict(lambda: dict(sites=0, cp=0, classes=set()))
    class_counts = defaultdict(lambda: dict(sites=0, cp=0, owner=0, classes=set()))
    jar_own = {}
    own_names = set()
    parsed = 0
    bad = 0
    for n in class_entries:
        try:
            d = parse_class(z.read(n))
        except Exception as e:
            bad += 1
            if bad <= 5:
                eprint("  [skip] %s: %s" % (n, e))
            continue
        parsed += 1
        cname = d["name"]
        jar_own[cname] = (d["supers"], d["methods"])
        own_names.add(cname)
        for key, (kind, owner, nm, ds) in d["member_refs"].items():
            k = (kind, owner, nm, ds)
            r = member_refs[k]
            r["cp"] += 1
            r["classes"].add(cname)
            if any(owner.startswith(p) for p in NAMESPACES):
                class_counts[owner]["owner"] += 1
        for cn in d["class_refs"]:
            r = class_counts[cn]
            r["cp"] += 1
            r["classes"].add(cname)
        for kind, a, b, c in d["sites"]:
            if kind == "C":
                class_counts[a]["sites"] += 1
            else:
                member_refs[(kind, a, b, c)]["sites"] += 1
        if parsed % 500 == 0:
            eprint("  [parse] %d/%d (%.1fs)" % (parsed, len(class_entries), time.time() - t0))
    z.close()
    eprint("  解析完成 %d class（失败 %d），%.1fs" % (parsed, bad, time.time() - t0))

    # 外部依赖引用（非 MC / 非 JDK / 非本 jar）——用来识别缺的 mod 依赖
    ext_counts = {}
    for cn, v in class_counts.items():
        if any(cn.startswith(p) for p in NAMESPACES) or cn.startswith(JDK_PREFIXES):
            continue
        if cn in own_names:
            continue
        e = ext_counts.setdefault(cn, dict(sites=0, cp=0, classes=set()))
        e["sites"] += v["sites"]
        e["cp"] += v["cp"]
        e["classes"] |= v["classes"]

    # 目标命名空间内的引用
    tgt_members = {k: v for k, v in member_refs.items()
                   if any(k[1].startswith(p) for p in NAMESPACES)}
    tgt_classes = {k: v for k, v in class_counts.items()
                   if any(k.startswith(p) for p in NAMESPACES)}

    eprint("  目标成员引用 %d 种 / 类引用 %d 种" % (len(tgt_members), len(tgt_classes)))

    # ---- 3. javap 核对
    oracle = Oracle(cp_jars, mc_names, cache_file(mc_ver), use_cache=not args.no_cache)
    need = {"java/lang/Object"}
    for k in tgt_members:
        need.add(k[1])
    for k in tgt_classes:
        need.add(k)
    eprint("  javap 待查 %d 个 owner 类..." % len(need))
    # 逐轮补查父类/接口 —— 否则「继承来的方法」会被误判成缺失
    todo = {n for n in need if n in mc_names or n.startswith("java/")}
    for _round in range(10):
        oracle.ensure(todo)
        more = set()
        for n in todo:
            info = oracle.info(n)
            if not info or info.get("missing"):
                continue
            for p in (info.get("supers") or []) + (info.get("interfaces") or []):
                pj = jvm_name(p)
                if (pj in mc_names or pj.startswith("java/")) and pj not in oracle.cache:
                    more.add(pj)
        if not more:
            break
        todo |= more
    oracle.save()
    resolve = make_resolver(oracle)

    # 简单名索引（查「疑似改名」的类）；**包含嵌套类**，并额外建一张小写表
    simple_index = defaultdict(list)
    simple_lower = defaultdict(list)
    for n in mc_names:
        s = n.split("/")[-1]
        simple_index[s].append(n)
        simple_lower[s.lower()].append(n)

    rows = []
    # A 类：按 class 聚合（同一个缺失类下几十个成员引用只算一条）
    a_agg = {}

    def a_slot(cn):
        return a_agg.setdefault(cn, dict(sites=0, cp=0, classes=set(), members=[]))
    for (kind, owner, nm, ds), v in tgt_members.items():
        cinfo = oracle.info(owner)
        owner_missing = owner not in mc_names or not cinfo or cinfo.get("missing")
        if not owner_missing:
            continue
        a = a_slot(owner)
        a["sites"] += v["sites"]
        a["cp"] += v["cp"]
        a["classes"] |= v["classes"]
        if v["sites"]:
            a["members"].append((v["sites"], kind, nm, ds))

    for cn, v in tgt_classes.items():
        if cn in mc_names and oracle.info(cn) and not oracle.info(cn).get("missing"):
            continue
        a = a_slot(cn)
        a["sites"] += v["sites"]
        a["cp"] += v["cp"]
        a["classes"] |= v["classes"]

    # 缺失类的「同简单名」候选（极其重要：26.3 把 com/mojang/blaze3d/** 大量搬到了
    # com/mojang/renderpearl/**，纯包名搬家可以被自动识别）
    cand_map = {}
    cand_need = set()
    for cn in a_agg:
        s = cn.split("/")[-1]
        cs = [x for x in simple_index.get(s, []) if x != cn]
        if not cs:                       # 大小写变了（RedStoneWireBlock -> RedstoneWireBlock）
            cs = [x for x in simple_lower.get(s.lower(), []) if x != cn]
        cs = cs[:6]
        cand_map[cn] = cs
        cand_need |= set(cs)
    if cand_need:
        oracle.ensure(cand_need)

    def cand_score(cn):
        mem = a_agg[cn]["members"]
        if not mem:
            return None, 0.0
        best, best_s = None, -1.0
        for c in cand_map.get(cn, []):
            info = oracle.info(c)
            if not info or info.get("missing"):
                continue
            mt = set(info.get("methods") or {})
            ft = set(info.get("fields") or {})
            hit = 0
            for _s, k, n, _d in mem:
                if n in (mt if k == "M" else ft):
                    hit += 1
            sc = hit / float(len(mem))
            if sc > best_s:
                best, best_s = c, sc
        return best, max(0.0, best_s)

    for cn, a in a_agg.items():
        cand, sc = cand_score(cn)
        a["members"].sort(reverse=True)
        ex = ", ".join(("%s%s" % (m[2], m[3]) if m[1] == "M" else "%s:%s" % (m[2], m[3]))
                       for m in a["members"][:3])
        rows.append(dict(level="A", kind="C", owner=cn,
                         name="%d 个成员" % len(a["members"]) if a["members"] else "",
                         desc="", sites=a["sites"], cp=a["cp"], classes=len(a["classes"]),
                         class_list=sorted(a["classes"]),
                         rename=([cand] if cand and sc > 0 else []), cand_score=round(sc, 2),
                         note=ex, why="类不存在"))

    for (kind, owner, nm, ds), v in tgt_members.items():
        cinfo = oracle.info(owner)
        owner_missing = owner not in mc_names or not cinfo or cinfo.get("missing")
        if owner_missing:
            continue
        status, where, alts = resolve(owner, kind, nm, ds)
        if status == "ok":
            continue
        lvl = ("B" if kind == "M" else "C") if status == "missing_name" else "D"
        own_info = oracle.info(owner) or {}
        table = own_info.get("methods" if kind == "M" else "fields") or {}
        same_desc_other_name = []
        for other, descs in table.items():
            if other != nm and ds in descs:
                same_desc_other_name.append(other)
        pkg_only = []
        if status == "missing_desc":
            dk = desc_key(ds)
            pkg_only = [x for x in alts if x != ds and desc_key(x) == dk][:3]
        rows.append(dict(level=lvl, kind=kind, owner=owner, name=nm, desc=ds,
                         sites=v["sites"], cp=v["cp"], classes=len(v["classes"]),
                         class_list=sorted(v["classes"]),
                         where=where, alts=alts, pkg_only=pkg_only,
                         rename=sorted(same_desc_other_name)[:6],
                         why=("名字不存在" if status == "missing_name" else "描述符不符")))

    # E 类：本 jar 的类覆盖了 MC 里已变成 final 的方法 → 类定义期 IncompatibleClassChangeError
    e_rows = []
    for cname, (supers, methods) in jar_own.items():
        if not supers:
            continue
        sup = supers[0]
        if sup not in mc_names:
            continue
        for mname, descs in methods.items():
            if mname in ("<init>", "<clinit>"):
                continue
            for ds in descs:
                st, where, _alts = resolve(sup, "M", mname, ds)
                if st != "ok" or not where:
                    continue
                info = oracle.info(where) or {}
                if (mname + "|" + ds) in set(info.get("final_methods") or []):
                    e_rows.append(dict(level="E", kind="M", owner=cname, name=mname, desc=ds,
                                       sites=1, cp=1, classes=1, class_list=[cname],
                                       where=where, why="覆盖 final 方法"))
    rows.extend(e_rows)

    # 合并同 key（成员行与 Class 行可能重复 A）
    merged = {}
    for r in rows:
        k = (r["level"], r["kind"], r["owner"], r["name"], r["desc"])
        if k in merged:
            m = merged[k]
            m["sites"] += r["sites"]
            m["cp"] += r["cp"]
            m["classes"] = max(m["classes"], r["classes"])
            for c in r.get("class_list", []):
                if c not in m.setdefault("class_list", []):
                    m["class_list"].append(c)
        else:
            merged[k] = r
    rows = sorted(merged.values(), key=lambda r: (-r["sites"], -r["classes"], r["owner"]))

    by_level = defaultdict(list)
    for r in rows:
        by_level[r["level"]].append(r)

    # ---- 4. 输出
    lines = []
    W = lines.append
    W("# %s @ MC %s API 缺口审计" % (jar.name, mc_ver))
    W("")
    W("jar : %s" % jar)
    W("MC  : %s" % mc)
    W("时间: %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    W("规模: %d class（解析成功 %d） / 目标成员引用 %d 种 / 目标类引用 %d 种"
      % (len(class_entries), parsed, len(tgt_members), len(tgt_classes)))
    W("口径: 引用次数 = 字节码指令条数（getstatic/invoke*/new/checkcast...）；"
      "本 jar 类数 = 引用它的本 jar class 个数")
    W("")
    W("## 汇总")
    W("")
    W("| 级别 | 含义 | 条目数 | 引用次数 | 涉及本jar类 |")
    W("|---|---|---|---|---|")
    for lvl, desc in (("A", "类整个不存在"), ("B", "方法缺失"), ("C", "字段缺失"),
                      ("D", "描述符不符"), ("E", "覆盖 final 方法")):
        rs = by_level.get(lvl, [])
        tot = sum(r["sites"] for r in rs)
        cls = set()
        for r in rs:
            cls |= set(r.get("class_list", []))
        W("| %s | %s | %d | %d | %d |" % (lvl, desc, len(rs), tot, len(cls)))
    W("")

    def emit(lvl, title, limit):
        rs = by_level.get(lvl, [])
        if not rs:
            W("## %s %s（0 条）" % (lvl, title))
            W("")
            return
        W("## %s %s（%d 条，共 %d 处引用）" % (lvl, title, len(rs), sum(r["sites"] for r in rs)))
        W("")
        W("| # | owner | 成员 | 描述符 | 引用 | 本jar类 | 提示 |")
        W("|---|---|---|---|---|---|---|")
        for i, r in enumerate(rs[:limit], 1):
            name = r["name"] or "-"
            hint = r.get("note") or ""
            if r.get("rename"):
                rn = "/".join(r["rename"][:2]) if r["level"] == "A" else "/".join(r["rename"][:3])
                hint = ("疑似改名→" + rn) + (("（成员名命中 %d%%）" % round(r.get("cand_score", 0) * 100))
                                              if r["level"] == "A" and r.get("cand_score") else "") \
                    + (("；" + hint) if hint else "")
            elif r["level"] == "D":
                hint = "%s 在 %s: %s" % (r["name"], (r.get("where") or "?").split("/")[-1],
                                         " ".join(x[:36] for x in r.get("alts", [])[:2]))
                if r.get("pkg_only"):
                    hint = "仅包名不同：%s；" % (" ".join(x[:36] for x in r["pkg_only"][:1])) + hint
            W("| %d | %s | %s | %s | %d | %d | %s |"
              % (i, r["owner"], name, r["desc"] or "-", r["sites"], r["classes"], hint))
        if len(rs) > limit:
            W("| ... | 余下 %d 条见 JSON | | | | | |" % (len(rs) - limit))
        W("")

    for lvl, title, lim in (("A", "类缺失", 120), ("B", "方法缺失", args.top),
                            ("C", "字段缺失", 120), ("D", "描述符不符", 60),
                            ("E", "覆盖 final 方法（类定义期硬错）", 40)):
        emit(lvl, title, lim)

    # 按族（owner）聚合，判断批量性
    W("## 按 owner 聚合（Top 40，看能否一个桥接类批量兜住）")
    W("")
    W("| # | owner | 条目 | 引用 | 本jar类 | 级别 |")
    W("|---|---|---|---|---|---|")
    agg = defaultdict(lambda: dict(n=0, sites=0, classes=set(), lv=set()))
    for r in rows:
        a = agg[r["owner"]]
        a["n"] += 1
        a["sites"] += r["sites"]
        a["classes"] |= set(r.get("class_list", []))
        a["lv"].add(r["level"])
    for i, (owner, a) in enumerate(sorted(agg.items(), key=lambda kv: -kv[1]["sites"])[:40], 1):
        W("| %d | %s | %d | %d | %d | %s |"
          % (i, owner, a["n"], a["sites"], len(a["classes"]), "".join(sorted(a["lv"]))))
    W("")
    # 外部依赖：按包（前三段）聚合
    W("## 外部依赖引用（非 MC / 非 JDK / 非本 jar）——看缺哪个 mod 依赖")
    W("")
    if not ext_counts:
        W("（无：本 jar 只引用 MC / JDK / 自己）")
        W("")
    else:
        pkg_agg = defaultdict(lambda: dict(n=0, sites=0, classes=0, sample=[]))
        for cn, v in ext_counts.items():
            seg = cn.split("/")
            pkg = "/".join(seg[:3]) if len(seg) >= 3 else "/".join(seg[:-1]) or cn
            a = pkg_agg[pkg]
            a["n"] += 1
            a["sites"] += v["sites"]
            a["classes"] = max(a["classes"], len(v["classes"]))
            if len(a["sample"]) < 3:
                a["sample"].append(cn)
        W("| # | 包前缀 | 类数 | 引用次数 | 例子 |")
        W("|---|---|---|---|---|")
        for i, (pkg, a) in enumerate(sorted(pkg_agg.items(), key=lambda kv: -kv[1]["sites"])[:25], 1):
            W("| %d | %s | %d | %d | %s |"
              % (i, pkg, a["n"], a["sites"], "<br>".join(x.split("/")[-1] for x in a["sample"])))
        W("")
        W("> 注意：这些类 **不在 MC jar 里**，靠其它 mod 提供。如果本 jar 启动时连带 loader/依赖，"
          "它们可能已经是 mods 目录里另一个 jar 的，**不要盲目当缺失**。")
        W("")

    W("## 可修性判断")
    W("")
    W("- **B/C/D**：JVM 按 `owner+name+descriptor` 解析，**方法引用和字段引用都能改常量池 owner**"
      "（字段并非只能改名字；`getstatic Bridge.IGNORE : LPushReaction;` 完全合法）。"
      "写一个同名同描述符的桥接静态成员即可批量兜住。")
    W("- 有「疑似改名」的条目：桥接体直接转调新名字（零语义损失）。")
    W("- 无改名的条目：桥接体返回占位值（语义降级）或手写等价实现。")
    W("- **A（类缺失）**：必须提供同名占位类，风险最高；有「疑似改名」的优先改成真实新类。")
    W("")

    OUTDIR.mkdir(parents=True, exist_ok=True)
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    Path(out_txt).write_text("\n".join(lines), encoding="utf-8")

    out_json.parent.mkdir(parents=True, exist_ok=True)
    Path(out_json).write_text(json.dumps(dict(
        jar=str(jar), mc=str(mc), mc_ver=str(mc_ver), when=time.strftime("%Y-%m-%d %H:%M:%S"),
        classes=len(class_entries), parsed=parsed,
        external={k: dict(sites=v["sites"], cp=v["cp"], classes=sorted(v["classes"]))
                  for k, v in sorted(ext_counts.items(), key=lambda kv: -kv[1]["sites"])},
        summary={lvl: dict(n=len(by_level.get(lvl, [])),
                           sites=sum(r["sites"] for r in by_level.get(lvl, [])))
                 for lvl in "ABCD"},
        rows=rows,
    ), ensure_ascii=False, indent=1), encoding="utf-8")

    eprint("")
    for lvl in "ABCDE":
        rs = by_level.get(lvl, [])
        eprint("  %s: %d 条 / %d 处引用" % (lvl, len(rs), sum(r["sites"] for r in rs)))
    eprint("写出: %s" % out_txt)
    eprint("      %s" % out_json)
    eprint("总用时 %.1fs" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
