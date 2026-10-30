#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_mixins26.py —— 对 Sable / Aeronautics / Simulated 的全部 mixin 配置做 26.3 运行期审计。

为什么需要：`compileJava` 0 错 ≠ 能跑。@Mixin/@Shadow/@Inject 的目标类、目标方法、
目标字段全是**运行期解析**的；26.3 相对 1.21.x 改了大量类形态（class→interface、方法改名、
方法搬家），这些在 javac 阶段一个都报不出来，只会在启动时以
`InvalidMixinException` / `MixinApplyError` 炸掉。

它做什么：
  1. 读 4 个 *.mixins.json（sable / sable-fabric / aeronautics / simulated）的全部条目；
  2. 把点号条目映射成源码路径，解析每个类的 `@Mixin(Xxx.class)` / `@Mixin(targets="...")`；
  3. 用 javap 查目标类在 26.3 里 **存在吗 / 是 class 还是 interface**，并取回
     全部方法名+描述符、字段名+描述符（含父类链，@Shadow 允许影子继承成员）；
  4. 解析 @Inject/@Redirect/@WrapOperation/@WrapMethod/@ModifyVariable/@ModifyArg(s)/
     @ModifyConstant/@ModifyExpressionValue/@ModifyReturnValue/@ModifyReceiver 的
     `method=` / `value=`，以及 @Shadow(method/field)、裸 @Shadow、@Accessor、@Invoker、
     @Overwrite 的成员名，逐个核对目标里是否存在；
     **@Shadow/@Accessor/@Invoker/@Overwrite 还会把源码里的 Java 类型声明换算成 JVM 描述符**
     （泛型擦除、数组、内部类 `$`、常见 JDK/joml 类型），按 `name + descriptor` 精确匹配 ——
     Mixin 就是这么匹配的，只比名字会把 `canFallAtLeast(DDF)Z` vs `(DDD)Z` 判成 OK；
  5. 打一张表：mixin 类 | 目标 | 状态(class/interface/不存在) | 缺失的方法/字段；
  6. 把「致命（@Shadow/@Accessor/@Invoker/@Overwrite 缺成员、目标不存在、class→interface）」
     与「可降级（注入点方法缺失 → require=0）」分开，供修批脚本消费。

用法：
  python tools/audit_mixins26.py                 # 全量审计 + 打表
  python tools/audit_mixins26.py --validate      # 只校验 json 条目 ↔ 源文件 / jar 成对
  python tools/audit_mixins26.py --json out.json # 额外落一份机器可读报告
  python tools/audit_mixins26.py --no-cache      # 忽略 javap 缓存
  python tools/audit_mixins26.py --only sable    # 只审某个配置（可多次）

性能：javap 结果按「jar 集合指纹」缓存到 tools/.cache/mixinaudit26/，
      单类一次 javap（8 线程并行），首跑约 20~40s，复跑 < 2s。
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path

# ---------------------------------------------------------------------------
# 路径
# ---------------------------------------------------------------------------
TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent                      # skylands-262
MC_DIR = Path(os.environ.get("APPDATA", "")) / ".minecraft"
MC_JAR = MC_DIR / "versions" / "26.3" / "26.3.jar"
JAVAP = MC_DIR / "runtime" / "java-runtime-epsilon" / "bin" / "javap.exe"
CACHE_DIR = TOOLS / ".cache" / "mixinaudit26"
CACHE_FILE = CACHE_DIR / "javap-cache.json"

WORK = ROOT / "work"
SABLE = WORK / "sable-26" / "src"
AERO = WORK / "aero-port" / "aeronautics-26" / "src"

# 4 个配置：name, json, 源码根, 移走目录
CONFIGS = [
    dict(name="sable",
         cfg=SABLE / "common" / "src" / "main" / "resources" / "sable.mixins.json",
         src=SABLE / "common" / "src" / "main" / "java",
         drop=SABLE / "_dropped_mixin26"),
    dict(name="sable-fabric",
         cfg=SABLE / "fabric" / "src" / "main" / "resources" / "sable-fabric.mixins.json",
         src=SABLE / "fabric" / "src" / "main" / "java",
         drop=SABLE / "_dropped_mixin26"),
    dict(name="aeronautics",
         cfg=AERO / "main" / "resources" / "aeronautics.mixins.json",
         src=AERO / "main" / "java",
         drop=AERO / "_dropped_mixin26"),
    dict(name="simulated",
         cfg=AERO / "main" / "resources" / "simulated.mixins.json",
         src=AERO / "main" / "java",
         drop=AERO / "_dropped_mixin26"),
]

SECTIONS = ("mixins", "client", "server")

# class→interface 时可能的实现类提示（人工确认过 / 便于脚本给出建议）
IFACE_IMPL_HINTS = {
    "net.minecraft.world.level.Explosion": "net.minecraft.world.level.ServerExplosion",
    "net.minecraft.world.level.LevelAccessor": None,
}

INJECTORS = (
    "Inject", "Redirect", "WrapOperation", "WrapMethod", "ModifyVariable",
    "ModifyArg", "ModifyArgs", "ModifyConstant", "ModifyExpressionValue",
    "ModifyReturnValue", "ModifyReceiver", "ModifyExpressionValue",
)
# 这些注解的 method= 缺失时可以用 require = 0 降级
REQUIRE_CAPABLE = set(INJECTORS)

MEMBER_FATAL = ("Shadow", "Accessor", "Invoker", "Overwrite")


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------
def eprint(*a):
    print(*a, file=sys.stderr)


def strip_comments(src: str) -> str:
    """去掉 // 与 /* */ 注释（保留字符串/字符字面量与换行），避免注释里的 @Mixin 假命中。"""
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c == '"':
            # 文本块 """ ... """
            if src.startswith('"""', i):
                j = src.find('"""', i + 3)
                if j < 0:
                    j = n
                else:
                    j += 3
                out.append(src[i:j])
                i = j
                continue
            j = i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == '"':
                    j += 1
                    break
                j += 1
            out.append(src[i:j])
            i = j
            continue
        if c == "'":
            j = i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == "'":
                    j += 1
                    break
                j += 1
            out.append(src[i:j])
            i = j
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            j = src.find("\n", i)
            if j < 0:
                j = n
            out.append(" " * (j - i))
            i = j
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "*":
            j = src.find("*/", i + 2)
            if j < 0:
                j = n
            else:
                j += 2
            chunk = src[i:j]
            out.append("".join("\n" if ch == "\n" else " " for ch in chunk))
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out)


def match_paren(src: str, open_idx: int) -> int:
    """src[open_idx] == '('，返回配对 ')' 的下标（找不到返回 -1）。"""
    depth = 0
    i, n = open_idx, len(src)
    while i < n:
        c = src[i]
        if c == '"':
            if src.startswith('"""', i):
                j = src.find('"""', i + 3)
                i = n if j < 0 else j + 3
                continue
            i += 1
            while i < n:
                if src[i] == "\\":
                    i += 2
                    continue
                if src[i] == '"':
                    i += 1
                    break
                i += 1
            continue
        if c == "'":
            i += 1
            while i < n:
                if src[i] == "\\":
                    i += 2
                    continue
                if src[i] == "'":
                    i += 1
                    break
                i += 1
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def split_top(s: str, sep: str = ","):
    """按顶层分隔符切分（忽略 () [] {} <> 内部与字符串内部）。"""
    parts, cur = [], []
    depth = 0
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c == '"':
            j = i + 1
            while j < n:
                if s[j] == "\\":
                    j += 2
                    continue
                if s[j] == '"':
                    j += 1
                    break
                j += 1
            cur.append(s[i:j])
            i = j
            continue
        if c in "([{<":
            depth += 1
        elif c in ")]}>":
            depth -= 1
        if c == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
            i += 1
            continue
        cur.append(c)
        i += 1
    if cur:
        parts.append("".join(cur))
    return parts


def unquote(v: str):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        body = v[1:-1]
        return body.replace('\\"', '"').replace("\\\\", "\\")
    return v


def parse_annotation_args(argstr: str):
    """返回 [(key|None, [raw values])]，值已去引号；{a,b} 展开成多值。"""
    res = []
    if argstr is None:
        return res
    for chunk in split_top(argstr, ","):
        if not chunk.strip():
            continue
        eq = -1
        depth = 0
        in_str = False
        i = 0
        while i < len(chunk):
            c = chunk[i]
            if in_str:
                if c == "\\":
                    i += 2
                    continue
                if c == '"':
                    in_str = False
            else:
                if c == '"':
                    in_str = True
                elif c in "([{<":
                    depth += 1
                elif c in ")]}>":
                    depth -= 1
                elif c == "=" and depth == 0:
                    eq = i
                    break
            i += 1
        if eq >= 0:
            key = chunk[:eq].strip()
            val = chunk[eq + 1:].strip()
        else:
            key, val = None, chunk.strip()
        vals = []
        if val.startswith("{") and val.endswith("}"):
            for p in split_top(val[1:-1], ","):
                if p.strip():
                    vals.append(unquote(p))
        else:
            vals.append(unquote(val))
        res.append((key, vals))
    return res


def find_annotations(src: str, name: str):
    """在已去注释的源码中找 @name，产出 (start, end, argstr|None)。"""
    pat = re.compile(r"@" + re.escape(name) + r"\b")
    for m in pat.finditer(src):
        i = m.end()
        while i < len(src) and src[i].isspace():
            i += 1
        if i < len(src) and src[i] == "(":
            j = match_paren(src, i)
            if j < 0:
                continue
            yield (m.start(), j + 1, src[i + 1:j])
        else:
            yield (m.start(), m.end(), None)


# ---------------------------------------------------------------------------
# jar 索引 / javap
# ---------------------------------------------------------------------------
def collect_jars():
    jars = []
    if MC_JAR.is_file():
        jars.append(MC_JAR)
    libs26 = WORK / "aero-port" / "libs26"
    if libs26.is_dir():
        for p in sorted(libs26.glob("*.jar")):
            if "1.21" in p.name:          # 1.21.x 的旧 jar 会把已删类“查成存在”
                continue
            jars.append(p)
    exp = WORK / "sable-26" / "port26" / "libs" / "expanded"
    if exp.is_dir():
        jars += sorted(exp.glob("*.jar"))
    mods = WORK / "run26" / "mods-aero"
    if mods.is_dir():
        jars += sorted(mods.glob("*.jar"))
    # 去重
    seen, out = set(), []
    for p in jars:
        k = str(p).lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(p)
    return out


def collect_dirs():
    dirs = []
    for d in (WORK / "sable-26" / "port26" / "build" / "classes" / "java" / "main",
              WORK / "aero-port" / "aeronautics-26" / "build" / "classes" / "java" / "main"):
        if d.is_dir():
            dirs.append(d)
    return dirs


class ClassIndex:
    def __init__(self, jars, dirs):
        self.binary = {}      # a.b.C$D -> jar/dir
        for p in jars:
            try:
                with zipfile.ZipFile(p) as z:
                    for n in z.namelist():
                        if n.endswith(".class") and not n.startswith("META-INF/"):
                            fqn = n[:-6].replace("/", ".")
                            self.binary.setdefault(fqn, str(p))
            except Exception as e:
                eprint(f"[warn] 读不了 jar {p}: {e}")
        for d in dirs:
            for f in d.rglob("*.class"):
                fqn = str(f.relative_to(d))[:-6].replace(os.sep, ".").replace("/", ".")
                self.binary.setdefault(fqn, str(d))

    def __contains__(self, fqn):
        return fqn in self.binary

    def all_class_names(self):
        return self.binary.keys()


def fingerprint(jars, dirs):
    h = hashlib.sha1()
    for p in jars:
        try:
            st = p.stat()
            h.update(f"{p}|{st.st_size}|{st.st_mtime_ns}".encode())
        except OSError:
            h.update(str(p).encode())
    for d in dirs:
        for f in d.rglob("*.class"):
            try:
                st = f.stat()
                h.update(f"{f}|{st.st_size}|{st.st_mtime_ns}".encode())
            except OSError:
                pass
    return h.hexdigest()


JAVAP_SEM = None


def parse_javap(text: str):
    """解析 javap -p -s 的单个类输出 → dict(kind, supers, interfaces, methods, fields)。"""
    lines = text.splitlines()
    kind = None
    for ln in lines:
        m = re.match(
            r"^(?:public |protected |private |static |final |abstract |sealed |non-sealed )*"
            r"(@interface|interface|class|enum|record)\s+([\w.$]+)", ln)
        if m:
            kind = m.group(1)
            break
    if kind is None:
        return None
    # 头部（extends / implements 可能换行）拼平
    hstart = next(i for i, ln in enumerate(lines) if re.search(r"\b(class|interface|enum|record|@interface)\s+[\w.$]+", ln))
    head = []
    for ln in lines[hstart:hstart + 12]:
        head.append(ln)
        if "{" in ln:
            break
    headtxt = re.sub(r"\s+", " ", "".join(head))
    supers = []
    interfaces = []
    em = re.search(r"\bextends\s+([\w.$]+)", headtxt)
    if em:
        supers.append(em.group(1))
    im = re.search(r"\bimplements\s+(.+?)\s*\{", headtxt)
    if im:
        for x in split_top(im.group(1), ","):
            x = x.strip()
            if not x:
                continue
            # 去掉泛型
            x = re.sub(r"<.*$", "", x).strip()
            if re.match(r"^[\w.$]+$", x):
                interfaces.append(x)
    methods, fields = {}, {}
    static_methods = set()
    cur = None
    blocks = []
    for ln in lines[hstart + 1:]:
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
        desc = dm.group(1) if dm else ""
        sig = flat[:dm.start()] if dm else flat
        if "(" in sig:
            pre = sig[:sig.index("(")]
            nm = re.search(r"([\w$]+)\s*$", pre)
            if not nm:
                continue
            name = nm.group(1)
            # 构造器：javap 打印成类的简单名
            if name == re.split(r"[.$]", _simple_of(headtxt))[-1]:
                name = "<init>"
            methods.setdefault(name, set()).add(desc)
            if re.search(r"\bstatic\b", sig):
                static_methods.add(name + "|" + desc)
        else:
            if re.search(r"\bstatic\s*\{\s*\}", sig):
                methods.setdefault("<clinit>", set()).add(desc)
                static_methods.add("<clinit>|" + desc)
                continue
            nm = re.search(r"([\w$]+)\s*;\s*$", sig)
            if not nm:
                continue
            fields.setdefault(nm.group(1), set()).add(desc)
    return dict(kind=kind, supers=supers, interfaces=interfaces,
                methods={k: sorted(v) for k, v in methods.items()},
                fields={k: sorted(v) for k, v in fields.items()},
                static_methods=sorted(static_methods))


def _simple_of(headtxt):
    m = re.search(r"(?:class|interface|enum|record|@interface)\s+([\w.$]+)", headtxt)
    return m.group(1) if m else ""


HEADER_RE = re.compile(
    r"^(?:public |protected |private |static |final |abstract |sealed |non-sealed )*"
    r"(@interface|interface|class|enum|record)\s+([\w.$]+)")


def parse_javap_sections(text: str):
    """javap 一次查多个类时，按「类头行」切段并解析。返回 {fqn: info}。"""
    sections, cur = [], None
    for ln in text.splitlines():
        if HEADER_RE.match(ln):
            if cur:
                sections.append(cur)
            cur = [ln]
        elif cur is not None:
            cur.append(ln)
    if cur:
        sections.append(cur)
    out = {}
    for sec in sections:
        d = parse_javap("\n".join(sec))
        if not d:
            continue
        m = HEADER_RE.match(sec[0])
        if not m:
            continue
        d["fqn"] = m.group(2)
        out[d["fqn"]] = d
    return out


class JavapOracle:
    """按类缓存 javap 结果；一次 javap 批量查多个类（比一类一进程快 ~20x）。
    缓存按「类所在 jar/目录的时间戳」逐类失效 —— 重编 mod 只重查 mod 自己的类。"""

    def __init__(self, jars, dirs, index, use_cache=True):
        self.cp = os.pathsep.join(str(p) for p in list(jars) + list(dirs))
        self.fp = fingerprint(jars, dirs)
        self.index = index
        self.cache = {}
        self.dirty = False
        if use_cache and CACHE_FILE.is_file():
            try:
                data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
                if data.get("schema") == 3:
                    self.cache = data.get("classes", {}) or {}
            except Exception:
                self.cache = {}

    def info(self, fqn):
        return self.cache.get(fqn)

    def _stamp(self, fqn):
        p = self.index.binary.get(fqn)
        if not p:
            return None
        try:
            st = Path(p).stat()
            return f"{st.st_size}:{st.st_mtime_ns}"
        except OSError:
            return None

    def ensure(self, names):
        todo = []
        for fqn in sorted(set(names)):
            if fqn not in self.index:
                self.cache[fqn] = dict(missing=True, _stamp="absent")
                continue
            st = self._stamp(fqn)
            c = self.cache.get(fqn)
            if c and c.get("_stamp") == st:
                continue
            todo.append(fqn)
        if not todo:
            return
        t0 = time.time()
        chunks = [todo[i:i + 30] for i in range(0, len(todo), 30)]
        done = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
            futs = {ex.submit(self._batch, ch): ch for ch in chunks}
            for fut in concurrent.futures.as_completed(futs):
                ch = futs[fut]
                try:
                    got = fut.result()
                except Exception as e:
                    got = {}
                    eprint(f"[warn] javap 批失败: {e}")
                for fqn in ch:
                    d = got.get(fqn)
                    if d is None:
                        d = dict(missing=True)
                    d["_stamp"] = self._stamp(fqn)
                    self.cache[fqn] = d
                done += len(ch)
                eprint(f"  [javap] {done}/{len(todo)}  ({time.time()-t0:.1f}s)")
        self.dirty = True
        eprint(f"  [javap] 完成 {len(todo)} 个类，用时 {time.time()-t0:.1f}s")

    def _batch(self, names):
        try:
            r = subprocess.run([str(JAVAP), "-p", "-s", "-cp", self.cp] + list(names),
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=180)
        except Exception:
            return {}
        return parse_javap_sections(r.stdout or "")

    def save(self):
        if not self.dirty:
            return
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps({"schema": 3, "fingerprint": self.fp, "classes": self.cache},
                                         ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Java 源码解析
# ---------------------------------------------------------------------------
def parse_imports(src):
    imports, wilds = {}, set()
    for m in re.finditer(r"\bimport\s+(static\s+)?([\w.$*]+)\s*;", src):
        if m.group(1):
            continue
        fq = m.group(2)
        if fq.endswith(".*"):
            wilds.add(fq[:-2])
        elif fq == "*":
            continue
        else:
            imports[fq.rsplit(".", 1)[-1]] = fq
    return imports, wilds


def variants(name):
    """a.b.C.D -> 先原样，再把尾部类名嵌套用 $ 连接（逐个 k 尝试）。"""
    yield name
    parts = name.split(".")
    for k in range(len(parts) - 1, 0, -1):
        yield ".".join(parts[:k]) + "$" + "$".join(parts[k:])


def resolve_class_ref(name, imports, wilds, index):
    name = name.strip()
    if not name:
        return None
    if "." not in name:
        cands = []
        if name in imports:
            cands.append(imports[name])
        for w in wilds:
            cands.append(w + "." + name)
        cands.append("java.lang." + name)
        for c in cands:
            for v in variants(c):
                if v in index:
                    return v
        return None
    first, rest = name.split(".", 1)
    if first in imports:
        base = imports[first] + "." + rest
        for v in variants(base):
            if v in index:
                return v
    for v in variants(name):
        if v in index:
            return v
    for w in wilds:
        for v in variants(w + "." + name):
            if v in index:
                return v
    return None


MODIFIERS = {"public", "protected", "private", "static", "final", "abstract",
             "native", "synchronized", "transient", "volatile", "default",
             "strictfp", "sealed", "non-sealed"}


def skip_annotation(src, i):
    """src[i] == '@'，返回注解结束后的下标。"""
    j = i + 1
    n = len(src)
    while j < n and (src[j].isalnum() or src[j] in "_$."):
        j += 1
    while j < n and src[j].isspace():
        j += 1
    if j < n and src[j] == "(":
        k = match_paren(src, j)
        return (k + 1) if k >= 0 else n
    return j


def next_member(src, pos):
    """从 pos 起找下一个成员声明，返回 (kind, name, decl_start, decl_end)。
    kind ∈ method/field/init/unknown。"""
    i, n = pos, len(src)
    while i < n:
        c = src[i]
        if c.isspace():
            i += 1
        elif c == "@":
            i = skip_annotation(src, i)
        else:
            break
    start = i
    last_ident = None
    angle = 0
    while i < n:
        c = src[i]
        if c == "@":
            i = skip_annotation(src, i)
            continue
        if c == "<":
            angle += 1
            i += 1
            continue
        if c == ">":
            angle = max(0, angle - 1)
            i += 1
            continue
        if c == "(" and angle == 0:
            pre = src[start:i]
            nm = re.findall(r"[A-Za-z_$][\w$]*", pre)
            if not nm:
                return ("unknown", None, start, i)
            name = nm[-1]
            if name == "static":
                return ("init", "<clinit>", start, i)
            return ("method", name, start, i)
        if c in ";={" and angle == 0:
            pre = src[start:i]
            ids = re.findall(r"[A-Za-z_$][\w$]*", pre)
            if not ids:
                return ("unknown", None, start, i)
            if c == "{" and ids[-1] == "static":
                return ("init", "<clinit>", start, i)
            return ("field", ids[-1], start, i)
        if c.isalpha() or c in "_$":
            j = i + 1
            while j < n and (src[j].isalnum() or src[j] in "_$"):
                j += 1
            last_ident = src[i:j]
            i = j
            continue
        i += 1
    return ("unknown", last_ident, start, i)


def top_level_kind(src):
    """返回 mixin 类自身的 class/interface/enum/record。"""
    m = re.search(r"^(?:[\w@]+\s+)*(?:public\s+|protected\s+|private\s+|static\s+|final\s+|"
                  r"abstract\s+|sealed\s+|non-sealed\s+)*(class|interface|enum|record)\s+([A-Za-z_$][\w$]*)",
                  src, re.M)
    if m:
        return m.group(1), m.group(2)
    # 兜底：任意位置
    m = re.search(r"\b(class|interface|enum|record)\s+([A-Za-z_$][\w$]*)", src)
    if m:
        return m.group(1), m.group(2)
    return None, None


def parse_mixin_targets(src, imports, wilds, index):
    """返回 [(raw, resolved|None, source)]"""
    out = []
    for (_s, _e, argstr) in find_annotations(src, "Mixin"):
        if argstr is None:
            continue
        for key, vals in parse_annotation_args(argstr):
            if key == "targets":
                for v in vals:
                    out.append((v, v if v in index else None, "targets"))
            elif key in (None, "value"):
                for v in vals:
                    raw = v.strip()
                    if raw.endswith(".class"):
                        raw = raw[:-6].strip()
                    out.append((raw, resolve_class_ref(raw, imports, wilds, index), "class"))
    return out


def parse_method_spec(spec):
    """'foo(Lnet/...;)V' -> ('foo','(Lnet/...;)V')；'Lowner;foo(...)V' -> ('foo','(...)V')；
    '*' / '' -> None（全方法通配，不查存在性）"""
    spec = spec.strip()
    if not spec or spec == "*":
        return None
    # Mixin 也接受 Lowner;name(desc)ret 形式
    if spec.startswith("L"):
        k = spec.find(";")
        if k > 0:
            spec = spec[k + 1:]
    if not spec:
        return None
    if "(" in spec:
        name = spec[:spec.index("(")].strip()
        desc = spec[spec.index("("):].strip()
        return name, desc
    return spec, None


def member_sig(src, pos):
    """从 pos 找下一个成员，返回 (kind, name, decl_text, params_text|None)。"""
    kind, name, s0, e0 = next_member(src, pos)
    if not name:
        return kind, name, None, None
    if kind == "method":
        close = match_paren(src, e0)
        params = src[e0 + 1:close] if close > 0 else ""
        return kind, name, src[s0:e0], params
    return kind, name, src[s0:e0], None


def split_desc_params(desc: str):
    """'(Lfoo;ID)V' -> ['Lfoo;','I','D']"""
    if not desc or "(" not in desc:
        return None
    body = desc[1:desc.index(")")]
    out, i = [], 0
    while i < len(body):
        c = body[i]
        if c == "[":
            j = i
            while j < len(body) and body[j] == "[":
                j += 1
            if j < len(body) and body[j] == "L":
                k = body.index(";", j)
                out.append(body[i:k + 1])
                i = k + 1
            else:
                out.append(body[i:j + 1])
                i = j + 1
        elif c == "L":
            k = body.index(";", i)
            out.append(body[i:k + 1])
            i = k + 1
        else:
            out.append(c)
            i += 1
    return out


def collect_refs(src, ann_name):
    """为一个注入器注解名收集 (kind, member, desc|None, ann_span, require)。"""
    refs = []
    for (s, e, argstr) in find_annotations(src, ann_name):
        if argstr is None:
            continue
        _hk, _hn, _hdecl, hparams = member_sig(src, e)
        hstatic = bool(re.search(r"\bstatic\b", _hdecl or ""))
        args = parse_annotation_args(argstr)
        require = None
        for k, v in args:
            if k == "require" and v:
                try:
                    require = int(v[0])
                except ValueError:
                    require = 0
        for k, v in args:
            if k == "method" and v:
                for item in v:
                    got = parse_method_spec(item)
                    if not got:
                        continue
                    name, desc = got
                    refs.append(dict(kind="method", member=name, desc=desc,
                                     ann=ann_name, ann_start=s, ann_end=e, require=require,
                                     handler_params=hparams, handler_static=hstatic,
                                     handler_name=_hn, handler_decl=_hdecl, handler_kind=_hk))
    return refs


def derive_accessor_name(method_name, prefix_get=("get", "set", "is")):
    for p in prefix_get:
        if method_name.startswith(p) and len(method_name) > len(p):
            rest = method_name[len(p):]
            return rest[0].lower() + rest[1:]
    return method_name


# ---------------------------------------------------------------------------
# Java 类型 → JVM 描述符（@Shadow 是按 name + descriptor 精确匹配的！）
# ---------------------------------------------------------------------------
JAVA_PRIMS = {
    "void": "V", "boolean": "Z", "byte": "B", "char": "C", "short": "S",
    "int": "I", "long": "J", "float": "F", "double": "D",
}
JAVA_LANG = {
    "String", "Object", "Integer", "Long", "Double", "Float", "Boolean", "Byte",
    "Short", "Character", "Number", "Class", "Enum", "Record", "Throwable",
    "Exception", "RuntimeException", "Iterable", "Comparable", "CharSequence",
    "Void", "Math", "System", "StringBuilder",
}

# JDK/常见第三方里「不装在我们的 jar 里、但描述符必须认识」的类型
KNOWN_INTERNAL = {t: "java/lang/" + t for t in JAVA_LANG}
KNOWN_INTERNAL.update({
    "List": "java/util/List", "ArrayList": "java/util/ArrayList",
    "Map": "java/util/Map", "HashMap": "java/util/HashMap",
    "Set": "java/util/Set", "HashSet": "java/util/HashSet",
    "LinkedHashMap": "java/util/LinkedHashMap", "LinkedHashSet": "java/util/LinkedHashSet",
    "Collection": "java/util/Collection", "Optional": "java/util/Optional",
    "Iterator": "java/util/Iterator", "Queue": "java/util/Queue",
    "Deque": "java/util/Deque", "ArrayDeque": "java/util/ArrayDeque",
    "UUID": "java/util/UUID", "Objects": "java/util/Objects",
    "Arrays": "java/util/Arrays", "Comparator": "java/util/Comparator",
    "Random": "java/util/Random", "Collections": "java/util/Collections",
    "Supplier": "java/util/function/Supplier", "Consumer": "java/util/function/Consumer",
    "Predicate": "java/util/function/Predicate", "Function": "java/util/function/Function",
    "BiFunction": "java/util/function/BiFunction",
    "UnaryOperator": "java/util/function/UnaryOperator",
    "Logger": "org/slf4j/Logger",
    "Vector3f": "org/joml/Vector3f", "Vector3d": "org/joml/Vector3d",
    "Vector3i": "org/joml/Vector3i", "Matrix4f": "org/joml/Matrix4f",
    "Matrix3f": "org/joml/Matrix3f", "Quaternionf": "org/joml/Quaternionf",
    "Vector4f": "org/joml/Vector4f",
})


def strip_type_annotations(t: str) -> str:
    out, i, n = [], 0, len(t)
    while i < n:
        c = t[i]
        if c == "@":
            i += 1
            while i < n and (t[i].isalnum() or t[i] in "_$."):
                i += 1
            while i < n and t[i].isspace():
                i += 1
            if i < n and t[i] == "(":
                j = match_paren(t, i)
                i = (j + 1) if j >= 0 else n
            continue
        out.append(c)
        i += 1
    return "".join(out)


def strip_generics(t: str) -> str:
    out, depth = [], 0
    for c in t:
        if c == "<":
            depth += 1
        elif c == ">":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(c)
    return "".join(out)


def strip_leading_modifiers(t: str) -> str:
    toks = t.split()
    i = 0
    while i < len(toks) and toks[i] in MODIFIERS:
        i += 1
    return " ".join(toks[i:])


def _strip_leading_type_params(t: str) -> str:
    t = t.strip()
    while t.startswith("<"):
        depth, j = 0, 0
        for k, ch in enumerate(t):
            if ch == "<":
                depth += 1
            elif ch == ">":
                depth -= 1
                if depth == 0:
                    j = k + 1
                    break
        t = t[j:].strip()
    return t


def guess_internal(name: str) -> str:
    """把 a.b.Outer.Inner 猜成 a/b/Outer$Inner（包名段小写，类名段首字母大写）。"""
    parts = name.split(".")
    out = parts[0]
    for p in parts[1:]:
        last = out.rsplit(".", 1)[-1]
        out += ("$" if last[:1].isupper() else ".") + p
    return out


def type_to_desc(t: str, resolve):
    """Java 源码类型 → JVM 描述符；解析不了返回 None（不误报）。"""
    t = strip_type_annotations(t).strip()
    if not t:
        return None
    dims = 0
    while True:
        if t.endswith("[]"):
            dims += 1
            t = t[:-2].strip()
        elif t.endswith("..."):
            dims += 1
            t = t[:-3].strip()
        else:
            break
    if t.startswith("?"):
        t = t[len("? extends"):].strip() if t.startswith("? extends") else "Object"
    t = _strip_leading_type_params(t)
    t = strip_generics(t).strip()
    if not t:
        return None
    if t in JAVA_PRIMS:
        base = JAVA_PRIMS[t]
    else:
        fqn = resolve(t)
        if fqn:
            internal = fqn.replace(".", "/")
        elif t in KNOWN_INTERNAL:
            internal = KNOWN_INTERNAL[t]
        elif "." in t:
            internal = guess_internal(t).replace(".", "/")
        else:
            return None
        base = "L" + internal + ";"
    return "[" * dims + base


def param_type(p: str) -> str:
    p = strip_type_annotations(p).strip()
    p = strip_leading_modifiers(p)
    m = re.match(r"^(.*\S)\s+([A-Za-z_$][\w$]*)$", p)
    if m and re.search(r"[A-Za-z_$]", m.group(1)):
        return m.group(1)
    return p


def member_return_type(decl: str, name: str) -> str:
    t = strip_type_annotations(decl)
    t = strip_leading_modifiers(t).strip()
    if t.endswith(name):
        t = t[:-len(name)].strip()
    return _strip_leading_type_params(t)


def member_desc(kind, name, decl, params, resolve):
    """返回成员的 JVM 描述符（方法：含参数；字段：类型）。无法解析 -> None。"""
    if kind == "method":
        ret = member_return_type(decl, name)
        retd = type_to_desc(ret, resolve)
        if retd is None:
            return None
        pds = []
        for p in split_top(params or "", ","):
            if not p.strip():
                continue
            d = type_to_desc(param_type(p), resolve)
            if d is None:
                return None
            pds.append(d)
        return "(" + "".join(pds) + ")" + retd
    if kind == "field":
        return type_to_desc(member_return_type(decl, name), resolve)
    return None


def accessor_field_desc(decl, name, params, resolve):
    ret = member_return_type(decl, name)
    ps = [p for p in split_top(params or "", ",") if p.strip()]
    if not ps and ret != "void":
        return type_to_desc(ret, resolve)
    if len(ps) == 1 and ret == "void":
        return type_to_desc(param_type(ps[0]), resolve)
    return None


def refs_for_class(src, resolve=None):
    """汇总一个 mixin 类的全部成员引用。desc 尽量从源码声明换算成 JVM 描述符。"""
    if resolve is None:
        resolve = lambda _t: None

    def sig_of(pos):
        return member_sig(src, pos)

    refs = []
    for ann in INJECTORS:
        refs += collect_refs(src, ann)
    # @Shadow：裸 @Shadow 的成员名来自紧随其后的声明
    for (s, e, argstr) in find_annotations(src, "Shadow"):
        args = parse_annotation_args(argstr) if argstr else []
        keys = {k for k, _ in args}
        if "method" in keys or "field" in keys:
            for k, v in args:
                if k == "method":
                    for item in v:
                        got = parse_method_spec(item)
                        refs.append(dict(kind="method", member=got[0], desc=got[1],
                                         ann="Shadow", ann_start=s, ann_end=e, require=None))
                elif k == "field":
                    for item in v:
                        refs.append(dict(kind="field", member=item.strip(), desc=None,
                                         ann="Shadow", ann_start=s, ann_end=e, require=None))
            continue
        kind, name, decl, params = sig_of(e)
        if not name or kind not in ("method", "field"):
            continue
        desc = member_desc(kind, name, decl, params, resolve)
        refs.append(dict(kind=kind, member=name, desc=desc,
                         ann="Shadow", ann_start=s, ann_end=e, require=None))
    # @Accessor / @Invoker：值可显式给，也可从方法名推导；描述符从声明换算
    for ann in ("Accessor", "Invoker"):
        for (s, e, argstr) in find_annotations(src, ann):
            args = parse_annotation_args(argstr) if argstr else []
            vals = [v for k, vs in args if k in (None, "value") for v in vs]
            kind, name, decl, params = sig_of(e)
            if not name:
                for item in vals:
                    if ann == "Accessor":
                        refs.append(dict(kind="field", member=item.strip(), desc=None,
                                         ann=ann, ann_start=s, ann_end=e, require=None))
                    else:
                        got = parse_method_spec(item)
                        if got:
                            refs.append(dict(kind="method", member=got[0], desc=got[1],
                                             ann=ann, ann_start=s, ann_end=e, require=None))
                continue
            if ann == "Accessor":
                target_name = vals[0].strip() if vals else derive_accessor_name(name)
                desc = accessor_field_desc(decl, name, params, resolve)
                refs.append(dict(kind="field", member=target_name, desc=desc,
                                 ann=ann, ann_start=s, ann_end=e, require=None))
            else:
                target_name = (parse_method_spec(vals[0])[0] if vals and parse_method_spec(vals[0])
                               else derive_accessor_name(name, ("call", "invoke")))
                desc = member_desc("method", name, decl, params, resolve)
                refs.append(dict(kind="method", member=target_name, desc=desc,
                                 ann=ann, ann_start=s, ann_end=e, require=None))
    # @Overwrite：后面跟的方法名 + 描述符
    for (s, e, argstr) in find_annotations(src, "Overwrite"):
        kind, name, decl, params = sig_of(e)
        if name and kind == "method":
            refs.append(dict(kind="method", member=name, desc=member_desc(kind, name, decl, params, resolve),
                             ann="Overwrite", ann_start=s, ann_end=e, require=None))
    # 去重
    seen, out = set(), []
    for r in refs:
        k = (r["kind"], r["member"], r["desc"], r["ann_start"])
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


# ---------------------------------------------------------------------------
# 审计
# ---------------------------------------------------------------------------
def load_configs(only=None):
    out = []
    for c in CONFIGS:
        if only and c["name"] not in only:
            continue
        if not c["cfg"].is_file():
            eprint(f"[warn] 配置不存在: {c['cfg']}")
            continue
        data = json.loads(c["cfg"].read_text(encoding="utf-8"))
        out.append((c, data))
    return out


def audit(only=None, use_cache=True):
    jars, dirs = collect_jars(), collect_dirs()
    index = ClassIndex(jars, dirs)
    oracle = JavapOracle(jars, dirs, index, use_cache)
    eprint(f"[info] classpath: {len(jars)} jars + {len(dirs)} dirs, index={len(index.binary)} classes")

    # 1) 展开条目
    items = []
    for c, data in load_configs(only):
        pkg = data.get("package", "")
        default_require = (data.get("injectors") or {}).get("defaultRequire", 1)
        for sect in SECTIONS:
            for entry in data.get(sect) or []:
                rel = entry.replace(".", "/") + ".java"
                path = c["src"] / pkg.replace(".", "/") / rel
                items.append(dict(cfg=c, data=data, section=sect, entry=entry,
                                  pkg=pkg, path=path, default_require=default_require))

    # 2) 解析源码 + 收集目标
    for it in items:
        it["exists"] = it["path"].is_file()
        it["mixin_kind"] = None
        it["targets"] = []
        it["refs"] = []
        it["parse_error"] = None
        if not it["exists"]:
            continue
        try:
            raw = it["path"].read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            it["parse_error"] = f"读取失败: {e}"
            continue
        src = strip_comments(raw)
        it["mixin_kind"], _nm = top_level_kind(src)
        imports, wilds = parse_imports(src)
        it["targets"] = parse_mixin_targets(src, imports, wilds, index)

        def _resolve_type(t, _imports=imports, _wilds=wilds, _pkg=pkg):
            fqn = resolve_class_ref(t, _imports, _wilds, index)
            if fqn:
                return fqn
            pkg_candidate = _pkg + "." + t
            if pkg_candidate in index:
                return pkg_candidate
            if t in _imports:
                return _imports[t]
            if "." in t:
                return t
            return None

        it["refs"] = refs_for_class(src, _resolve_type)
        it["type_resolver"] = _resolve_type

    # 3) 目标类 + 父类链入 javap
    need = set()
    for it in items:
        for (_raw, fqn, _how) in it["targets"]:
            if fqn:
                need.add(fqn)
    oracle.ensure(need)
    # 父类/接口（@Shadow 可影子继承成员），最多两轮
    extra = set()
    for fqn in need:
        info = oracle.info(fqn)
        if info and not info.get("missing"):
            extra.update(info.get("supers") or [])
            extra.update(info.get("interfaces") or [])
    oracle.ensure(extra)
    extra2 = set()
    for fqn in extra:
        info = oracle.info(fqn)
        if info and not info.get("missing"):
            extra2.update(info.get("supers") or [])
            extra2.update(info.get("interfaces") or [])
    oracle.ensure(extra2 - extra)

    def all_members(fqn, seen=None):
        seen = seen or set()
        if fqn in seen:
            return set(), set()
        seen.add(fqn)
        info = oracle.info(fqn)
        ms, fs = set(), set()
        if not info or info.get("missing"):
            return ms, fs
        ms |= set((info.get("methods") or {}).keys())
        fs |= set((info.get("fields") or {}).keys())
        for s in (info.get("supers") or []):
            a, b = all_members(s, seen)
            ms |= a
            fs |= b
        return ms, fs

    def method_descs(fqn, name):
        info = oracle.info(fqn)
        if not info or info.get("missing"):
            return set()
        return set((info.get("methods") or {}).get(name) or [])

    def all_method_descs(fqn, name, seen=None):
        seen = seen or set()
        if fqn in seen:
            return set()
        seen.add(fqn)
        info = oracle.info(fqn)
        out = set()
        if not info or info.get("missing"):
            return out
        out |= set((info.get("methods") or {}).get(name) or [])
        for s in (info.get("supers") or []):
            out |= all_method_descs(s, name, seen)
        return out

    def all_field_descs(fqn, name, seen=None):
        seen = seen or set()
        if fqn in seen:
            return set()
        seen.add(fqn)
        info = oracle.info(fqn)
        out = set()
        if not info or info.get("missing"):
            return out
        out |= set((info.get("fields") or {}).get(name) or [])
        for s in (info.get("supers") or []):
            out |= all_field_descs(s, name, seen)
        return out

    def field_descs(fqn, name):
        info = oracle.info(fqn)
        if not info or info.get("missing"):
            return set()
        return set((info.get("fields") or {}).get(name) or [])

    # 4) 逐条判定
    for it in items:
        it["status"] = "OK"
        it["problems"] = []       # (level, code, text)
        it["missing_methods"] = []
        it["missing_fields"] = []
        if not it["exists"]:
            it["status"] = "FILE-MISSING"
            it["problems"].append(("fatal", "FILE-MISSING", f"源码不存在: {it['path']}"))
            continue
        if it["parse_error"]:
            it["status"] = "PARSE-ERROR"
            it["problems"].append(("fatal", "PARSE-ERROR", it["parse_error"]))
            continue
        if not it["targets"]:
            it["status"] = "NO-MIXIN-ANNOTATION"
            it["problems"].append(("fatal", "NO-TARGET", "找不到 @Mixin 目标（或 targets= 无法解析）"))
            continue
        mkind = it["mixin_kind"]
        target_kinds = []
        stub_fqns = set()
        for (raw, fqn, how) in it["targets"]:
            if fqn is None:
                it["problems"].append(("fatal", "TARGET-UNRESOLVED",
                                       f"无法解析目标 {raw}（不在任何已知 jar）"))
                target_kinds.append(("?", raw))
                continue
            info = oracle.info(fqn)
            if not info or info.get("missing"):
                it["problems"].append(("fatal", "TARGET-MISSING", f"目标类不存在: {fqn}"))
                target_kinds.append(("missing", fqn))
                continue
            kind = info.get("kind", "?")
            target_kinds.append((kind, fqn))
            srcpath = index.binary.get(fqn, "")
            if "\\build\\classes\\" in srcpath or "/build/classes/" in srcpath:
                stub_fqns.add(fqn)
                it["problems"].append(
                    ("warn", "STUB-TARGET",
                     f"目标 {fqn} 只在 stub/build 目录里（真实 jar 里没有）——成员无法校验；\n"
                     f"          运行时若真缺类，Mixin 只 WARN 跳过，不会硬崩"))
                continue
            if kind == "interface" and mkind == "class":
                hint = IFACE_IMPL_HINTS.get(fqn)
                extra_txt = f"（可能是实现类: {hint}）" if hint else ""
                it["problems"].append(
                    ("fatal", "IFACE-MISMATCH",
                     f"目标 {fqn} 是 interface，而 mixin 是 class{extra_txt}"))
        it["targets_resolved"] = target_kinds

        # 成员核对：注入点只查目标本身（Mixin 只能注入目标类自身声明的方法）
        target_fqns = [f for (k, f) in target_kinds
                       if k not in ("missing", "?") and f not in stub_fqns]
        primary = target_fqns[0] if target_fqns else None
        if primary is None:
            if stub_fqns and not [p for p in it["problems"] if p[0] == "fatal"]:
                it["status"] = "UNVERIFIED-STUB"
            else:
                it["status"] = it["problems"][0][1] if it["problems"] else "UNKNOWN"
            continue

        for r in it["refs"]:
            if not r["member"]:
                continue
            name = r["member"]
            ann_name = r.get("ann")
            if ann_name in INJECTORS:
                # 注入点：只查目标类自身。缺失是否致命取决于 require / defaultRequire。
                if r["require"] is not None:
                    effective_require = r["require"]
                else:
                    effective_require = it["default_require"]
                level = "warn" if effective_require == 0 else "fix"
                tag = "（已安全：require/defaultRequire=0）" if effective_require == 0 else ""
                if r["kind"] == "method":
                    descs = method_descs(primary, name)
                    if not descs:
                        it["missing_methods"].append(name + (r["desc"] or ""))
                        it["problems"].append(
                            (level, "METHOD-MISSING",
                             f"{ann_name} 目标方法不存在: {name}{r['desc'] or ''} (in {primary}){tag}"))
                    elif r["desc"] and r["desc"] not in descs:
                        it["missing_methods"].append(name + r["desc"])
                        it["problems"].append(
                            (level, "METHOD-DESC-MISMATCH",
                             f"{ann_name} 方法 {name} 描述符不符: 注解 {r['desc']} / 实际 {sorted(descs)}{tag}"))
                    # @Inject 的 handler 签名必须 = 目标方法参数 + CallbackInfo（+ sugar）
                    if ann_name == "Inject" and r.get("handler_params") is not None and descs:
                        exp = []
                        bad = False
                        for p in split_top(r["handler_params"], ","):
                            ps = p.strip()
                            if not ps:
                                continue
                            if "@" in ps:
                                break          # sugar 参数从第一个带注解的参数开始
                            ptype = param_type(ps)
                            pbase = strip_generics(strip_type_annotations(ptype)).strip()
                            if pbase in ("CallbackInfo", "CallbackInfoReturnable") or pbase.startswith("CallbackInfo"):
                                break
                            d = type_to_desc(ptype, it["type_resolver"])
                            if d is None:
                                bad = True
                                break
                            exp.append(d)
                        if not bad:
                            # Mixin 允许 handler 只声明目标参数的一个前缀（不捕获的参数可省略），
                            # 但类型/顺序必须对得上，且不能比目标参数多。
                            ok = False
                            for d in descs:
                                tps = split_desc_params(d) or []
                                if len(exp) <= len(tps) and tps[:len(exp)] == exp:
                                    ok = True
                                    break
                            if not ok:
                                it["problems"].append(
                                    ("fatal", "INJECT-HANDLER-DESC",
                                     f"@Inject 回调 {r.get('ann_start')} handler 参数与目标方法不符: "
                                     f"handler {exp} / 目标 {name} 实际 "
                                     f"{[(d, split_desc_params(d)) for d in sorted(descs)]}"))
                    # 静态性必须一致：目标 static <=> handler static
                    if descs and r.get("handler_static") is not None:
                        sinfo = oracle.info(primary) or {}
                        sset = set(sinfo.get("static_methods") or [])
                        tys = [(name + "|" + d) in sset for d in sorted(descs)]
                        if r["handler_static"] and not any(tys):
                            it["problems"].append(
                                ("fatal", "INJECT-HANDLER-STATIC",
                                 f"{ann_name} handler 是 static，但目标方法 {name} 是实例方法"))
                        elif (not r["handler_static"]) and tys and all(tys):
                            it["problems"].append(
                                ("fatal", "INJECT-HANDLER-STATIC",
                                 f"{ann_name} handler 是实例方法，但目标方法 {name} 是 static（26.3 改成静态）"))
                    # @WrapMethod：handler 参数（去掉末尾 Operation）+ 返回类型必须与目标方法完全一致
                    if (ann_name == "WrapMethod" and r.get("handler_kind") == "method"
                            and r.get("handler_decl") and r.get("handler_params") is not None and descs):
                        ps = [p for p in split_top(r["handler_params"], ",") if p.strip()]
                        hparams_d, okparse = [], True
                        for p in ps:
                            if "@" in p:
                                break          # MixinExtras sugar（@Local/@Share/...）不是目标参数
                            t = strip_generics(strip_type_annotations(param_type(p))).strip()
                            if t.endswith("Operation"):
                                continue
                            d = type_to_desc(t, it["type_resolver"])
                            if d is None:
                                okparse = False
                                break
                            hparams_d.append(d)
                        hret = type_to_desc(member_return_type(r["handler_decl"], r["handler_name"]),
                                            it["type_resolver"])
                        if okparse and hret:
                            good = False
                            for d in descs:
                                tps = split_desc_params(d) or []
                                tret = d[d.index(")") + 1:]
                                if tps == hparams_d and tret == hret:
                                    good = True
                                    break
                            if not good:
                                it["problems"].append(
                                    ("fatal", "WRAPMETHOD-SIG",
                                     f"@WrapMethod handler 签名与目标不一致: handler ({hparams_d}){hret} / "
                                     f"目标 {name} 候选 {sorted(descs)}"))
                else:
                    if name not in (oracle.info(primary) or {}).get("fields", {}):
                        it["missing_fields"].append(name)
                        it["problems"].append(
                            (level, "FIELD-MISSING",
                             f"{ann_name} 目标字段不存在: {name} (in {primary}){tag}"))
                    elif r["desc"] and r["desc"] not in all_field_descs(primary, name):
                        it["missing_fields"].append(name + r["desc"])
                        it["problems"].append(
                            (level, "FIELD-DESC-MISMATCH",
                             f"{ann_name} 字段 {name} 描述符不符: 注解 {r['desc']} / 实际 "
                             f"{sorted(all_field_descs(primary, name))}{tag}"))
            else:
                # 影子/访问器/覆写：允许继承，但 name + descriptor 都要对
                ms, fs = all_members(primary)
                if r["kind"] == "method":
                    if name == "<init>":
                        continue
                    if name not in ms:
                        it["missing_methods"].append(name + (r["desc"] or ""))
                        it["problems"].append(
                            ("fatal", "SHADOW-METHOD-MISSING",
                             f"@Shadow/@Overwrite 方法不存在: {name} (in {primary} + 父类链)"))
                    elif r["desc"]:
                        cands = all_method_descs(primary, name)
                        if r["desc"] not in cands:
                            it["missing_methods"].append(name + r["desc"])
                            it["problems"].append(
                                ("fatal", "SHADOW-DESC-MISMATCH",
                                 f"@Shadow/@Overwrite 方法 {name} 描述符不符: 源码声明 {r['desc']} / "
                                 f"目标实际 {sorted(cands)}"))
                else:
                    if name not in fs:
                        it["missing_fields"].append(name)
                        it["problems"].append(
                            ("fatal", "SHADOW-FIELD-MISSING",
                             f"@Shadow/@Accessor 字段不存在: {name} (in {primary} + 父类链)"))
                    elif r["desc"]:
                        cands = all_field_descs(primary, name)
                        if r["desc"] not in cands:
                            it["missing_fields"].append(name + r["desc"])
                            it["problems"].append(
                                ("fatal", "SHADOW-FIELD-DESC-MISMATCH",
                                 f"@Shadow/@Accessor 字段 {name} 描述符不符: 源码声明 {r['desc']} / "
                                 f"目标实际 {sorted(cands)}"))

        if it["problems"]:
            codes = [p[1] for p in it["problems"]]
            if any(p[0] == "fatal" for p in it["problems"]):
                it["status"] = "FATAL:" + next(p[1] for p in it["problems"] if p[0] == "fatal")
            elif any(p[0] == "fix" for p in it["problems"]):
                if any(p[1] == "METHOD-DESC-MISMATCH" for p in it["problems"] if p[0] == "fix"):
                    it["status"] = "FIX:DESC-MISMATCH"
                else:
                    it["status"] = "FIX:METHOD-MISSING"
            elif it["missing_fields"]:
                it["status"] = "MISSING-FIELD"
            else:
                it["status"] = "OK-WARN"
    oracle.save()
    return items, oracle


# ---------------------------------------------------------------------------
# 报表
# ---------------------------------------------------------------------------
def print_table(items):
    w = [3, 15, 46, 52, 10, 22]
    hdr = ["#", "config", "mixin", "target", "kind", "status"]
    line = " | ".join(h.ljust(x) for h, x in zip(hdr, w))
    print(line)
    print("-" * len(line))
    for i, it in enumerate(items, 1):
        tgts = ", ".join(f"{k}:{f}" for k, f in it.get("targets_resolved", [])) or "-"
        rows = [str(i), it["cfg"]["name"], it["entry"], tgts,
                it.get("mixin_kind") or "?", it["status"]]
        print(" | ".join(str(x).ljust(y) for x, y in zip(rows, w)))
        for lvl, code, txt in it["problems"]:
            if lvl == "warn" and code == "SHADOW-DESC?":
                continue
            print(f"      -> [{lvl}] {code}: {txt}")


def summarize(items):
    total = len(items)
    bad = [it for it in items if it["status"] != "OK"]
    by_status = {}
    for it in items:
        by_status[it["status"]] = by_status.get(it["status"], 0) + 1
    print("\n===== 汇总 =====")
    print(f"总条目: {total}")
    print(f"有问题的条目: {len(bad)}")
    for k, v in sorted(by_status.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {k:<28} {v}")
    fatals = [it for it in items if it["status"].startswith("FATAL")]
    inj = [it for it in items if it["status"].startswith("FIX:")]
    print(f"致命（必须摘/移或改）: {len(fatals)}")
    print(f"仅注入点缺失（可 require=0 降级）: {len(inj)}")
    return dict(total=total, bad=len(bad), by_status=by_status,
                fatal=len(fatals), inject_only=len(inj))


def validate(only=None, jar_map=None):
    """校验 json 条目 ↔ 源码文件（可选：↔ 构建出的 jar 里的 class）。"""
    problems = 0
    total = 0
    for c, data in load_configs(only):
        pkg = data.get("package", "")
        entries = []
        for sect in SECTIONS:
            for e in data.get(sect) or []:
                entries.append((sect, e))
        print(f"=== {c['name']}: {c['cfg'].name}  entries={len(entries)} pkg={pkg}")
        for sect, e in entries:
            total += 1
            rel = e.replace(".", "/")
            p = c["src"] / pkg.replace(".", "/") / (rel + ".java")
            ok_src = p.is_file()
            ok_jar = True
            if jar_map and c["name"] in jar_map:
                cls = pkg + "." + e
                ok_jar = cls in jar_map[c["name"]]
            if not (ok_src and ok_jar):
                problems += 1
                what = []
                if not ok_src:
                    what.append("NO-SOURCE")
                if not ok_jar:
                    what.append("NO-CLASS-IN-JAR")
                print(f"  BAD {sect:<8} {e:<60} {'/'.join(what)}")
        print(f"  entries={len(entries)}")
    print(f"\nTOTAL entries={total} bad={problems}")
    return problems


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", action="append", default=None)
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--json", default=None)
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--bad-only", action="store_true")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.validate:
        sys.exit(0 if validate(args.only) == 0 else 1)

    t0 = time.time()
    items, oracle = audit(args.only, use_cache=not args.no_cache)
    out_items = items if not args.bad_only else [it for it in items if it["status"] != "OK"]
    print_table(out_items)
    summary = summarize(items)
    print(f"\n用时 {time.time()-t0:.1f}s")
    print(f"javap 缓存: {CACHE_FILE}（{len(oracle.cache)} 类）")

    if args.json:
        payload = dict(summary=summary, items=[
            dict(config=it["cfg"]["name"], section=it["section"], entry=it["entry"],
                 mixin_kind=it.get("mixin_kind"), file=str(it["path"]),
                 exists=it["exists"], status=it["status"],
                 targets=[dict(kind=k, fqn=f) for k, f in it.get("targets_resolved", [])],
                 missing_methods=it["missing_methods"],
                 missing_fields=it["missing_fields"],
                 problems=[dict(level=l, code=c, text=t) for l, c, t in it["problems"]])
            for it in items])
        Path(args.json).write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                                   encoding="utf-8")
        print(f"报告已写: {args.json}")


if __name__ == "__main__":
    main()
