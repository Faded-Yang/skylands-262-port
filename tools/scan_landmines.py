#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scan_landmines.py —— 「运行时不存在的方法/字段/类」静态地雷扫描器（26.3）。

======================================================================
它解决什么问题
======================================================================
26.3 删了方法 / 改了签名 / 删了字段 —— 这类缺口**编译期不报错**（mod jar 早就是
字节码了），只有在**特定代码路径被执行**时才炸：
  * NoSuchMethodError / NoSuchFieldError          -> 成员被删，或签名（描述符）变了
  * NoClassDefFoundError                          -> 类被删 / 改名 / 没随包
  * 以及「签名变了但方法体还在用旧参数」导致的 NPE / CCE（本工具只能间接发现：
    若名字在、描述符不在，就是「签名变了」的强信号）

做法：**不用 javap、不用反射**，直接解析 class 文件
  (1) 常量池  (2) 字段/方法表  (3) Code 属性里的字节码指令
得到「谁引用了谁」，再与「可用成员索引」逐条比对。

======================================================================
为什么必须读字节码而不是只读常量池
======================================================================
常量池里常留下**没有被任何指令引用**的残留条目（javac 丢弃的分支、字符串拼接的
MethodHandle、反优化残留……）。这类条目运行期**不会**被解析 ⇒ 报出来就是误报。
所以「引用」只算**字节码指令真正引用到的那一条**。

======================================================================
「可用成员索引」= 哪些来源（⚠ 本工具最关键的部分）
======================================================================
只看 `26.3.jar` 会**大量误报**，因为运行期还有别的来源会往 MC 的类和接口上补成员：

  1. `versions/26.3/26.3.jar`                   —— MC 本体
  2. `fabric-api-0.163.0+26.3.jar` **及其 `META-INF/jars/*.jar` 内嵌模块（递归）**
     —— fabric-api 会用 mixin 把 default 方法**织进** MC 的接口/类。实测样本：
     `ValueInput.contains(String)` 在 26.3.jar 的 javap 里**看不到**，但
     `fabric-serialization-api` 的 `FabricValueInput` 提供了
     `default boolean contains(String)`，`ValueInputMixin` 把它织进 `ValueInput`
     ⇒ 运行期**能调通**。只查 26.3.jar 就会把它误报成地雷。
  3. `mods-stable` 里**全部 71 个 jar**（含各自内嵌 jar）—— 跨 jar 依赖。
  4. `.minecraft/libraries/**/*.jar`           —— fabric-loader / mixin / joml /
     fastutil / gson / lwjgl / guava / asm …
  5. JDK（`java.*` / `javax.*` / `jdk.*` / `sun.*`）—— **跳过，不查**。

对来源 2/3 额外做两步放宽（否则误报会淹没真地雷）：

  A. **织入放宽（woven）**：解析失败的 **接口方法** `I.m(desc)`，若 I 的某个
     实现类声明了同名同描述符的方法 ⇒ 判「很可能由 mixin 织入」⇒ **不进地雷表**。
  B. **mixin 目标标记（待验证）**：解析失败的成员，若其 owner 出现在某个
     `@Mixin(...)` 的 target 里 ⇒ 该 mixin **可能**补上了它。本工具**不**据此
     判定它存在，而是把这条从「实证地雷」降级为「**待验证**」并说明原因。
     —— 因为「mixin 认领了这个类」不等于「它补了这个成员」。

======================================================================
用法
======================================================================
    python tools/scan_landmines.py
    python tools/scan_landmines.py --mods work/run26/mods-stable --out docs/api-landmines.md
    python tools/scan_landmines.py --only aeronautics,create-fly
    python tools/scan_landmines.py --stats
    python tools/scan_landmines.py --json x.json --verbose

退出码：0 正常 / 1 参数或 IO 错 / 2 索引为空（通常 --mc 路径不对）
"""

import argparse
import io
import json
import os
import re
import subprocess
import sys
import time
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MC_HOME = Path(r"C:\Users\95959\AppData\Roaming\.minecraft")
DEFAULT_MC = MC_HOME / "versions" / "26.3" / "26.3.jar"
DEFAULT_MODS = ROOT / "work" / "run26" / "mods-stable"
DEFAULT_OUT = ROOT / "docs" / "api-landmines.md"
DEFAULT_ALLOW = ROOT / "tools" / "landmines-allow.json"

JDK_PREFIXES = ("java/", "javax/", "jdk/", "sun/", "com/sun/", "org/w3c/", "org/xml/")

# libraries 下这几个位置的 jar 必须排除，理由有两条：
#  (1) `net/minecraft/client/**` 存着 1.21.1 的 client 包（其中 `-extra.jar` 甚至是**全命名**的）
#      ⇒ 会把 26.3 已删/改名的类**掩盖**成「存在」⇒ 假阴性。
#  (2) `net/neoforged/**` 与 `cpw/mods/**` 是 Forge/NeoForge 的加载器 —— 本整合包是 **Fabric**，
#      运行期根本没有这些类。把它们放进索引会让「残留的 NeoForge 引用」静默通过 ⇒ 也是假阴性。
LIBS_SKIP_SUBSTR = (
    os.sep + "net" + os.sep + "minecraft" + os.sep,
    os.sep + "net" + os.sep + "neoforged" + os.sep,
    os.sep + "net" + os.sep + "minecraftforge" + os.sep,
    os.sep + "cpw" + os.sep + "mods" + os.sep,
)

MAX_NEST_DEPTH = 4

MIXIN_ANN = "Lorg/spongepowered/asm/mixin/Mixin;"
MIXIN_ANN_BYTES = b"Lorg/spongepowered/asm/mixin/Mixin;"

# 「未安装的可选依赖」判定：owner 的**前三段包名**在索引里完全不存在 => 这个库根本没装，
# 不是 26.3 的 API 变更。（mod 里到处都是 `if (FabricLoader.isModLoaded("rei"))` 这种可选集成，
# 字节码里留着直接引用，但那个分支永远进不去。）
NS_DEPTH = 3

# Object 的方法：任何类型都能解析到（BFS 走到 java/lang/Object 之前先短路）
OBJECT_METHODS = {
    ("equals", "(Ljava/lang/Object;)Z"),
    ("hashCode", "()I"),
    ("toString", "()Ljava/lang/String;"),
    ("getClass", "()Ljava/lang/Class;"),
    ("clone", "()Ljava/lang/Object;"),
    ("finalize", "()V"),
    ("notify", "()V"),
    ("notifyAll", "()V"),
    ("wait", "()V"),
    ("wait", "(J)V"),
    ("wait", "(JI)V"),
}

# ------------------------------------------------------------------ low level


class BadClass(Exception):
    pass


def u2(b, o):
    return (b[o] << 8) | b[o + 1]


def u4(b, o):
    return int.from_bytes(b[o:o + 4], "big")


def parse_pool(buf):
    """返回 (entries, pool_end)。entries[i] = (tag, start, end)；cp index 从 1 开始。"""
    if buf[:4] != b"\xca\xfe\xba\xbe":
        raise BadClass("bad magic")
    pos = 8
    count = u2(buf, pos)
    pos += 2
    entries = []
    i = 1
    while i < count:
        tag = buf[pos]
        start = pos
        if tag == 1:                                   # Utf8
            pos += 3 + u2(buf, pos + 1)
        elif tag in (3, 4):                            # Integer / Float
            pos += 5
        elif tag in (5, 6):                            # Long / Double（占 2 槽）
            pos += 9
        elif tag in (7, 8, 16, 19, 20):                # Class / String / MethodType / Module / Package
            pos += 3
        elif tag in (9, 10, 11, 12, 17, 18):           # refs / NameAndType / (Invoke)Dynamic
            pos += 5
        elif tag == 15:                                # MethodHandle
            pos += 4
        else:
            raise BadClass("cp tag %d at %d" % (tag, pos))
        if pos > len(buf):
            raise BadClass("cp overrun")
        entries.append((tag, start, pos))
        i += 2 if tag in (5, 6) else 1
    return entries, pos


def build_len_table():
    L = [1] * 256
    for op in range(0x15, 0x1A):
        L[op] = 2
    for op in range(0x36, 0x3B):
        L[op] = 2
    for op in range(0x99, 0xA9):
        L[op] = 3
    L[0x10] = 2
    L[0x11] = 3
    L[0x12] = 2
    L[0x13] = 3
    L[0x14] = 3
    L[0x84] = 3
    L[0xA9] = 2
    for op in range(0xB2, 0xB9):
        L[op] = 3
    L[0xB9] = 5
    L[0xBA] = 5
    L[0xBB] = 3
    L[0xBC] = 2
    L[0xBD] = 3
    L[0xC0] = 3
    L[0xC1] = 3
    L[0xC5] = 4
    L[0xC6] = 3
    L[0xC7] = 3
    L[0xC8] = 5
    L[0xC9] = 5
    return L


ILEN = build_len_table()

SITE_OPS = {}
for _op in (0xB2, 0xB3, 0xB4, 0xB5):
    SITE_OPS[_op] = ("F", 2)
for _op in (0xB6, 0xB7, 0xB8, 0xB9):
    SITE_OPS[_op] = ("M", 2)
for _op in (0xBB, 0xBD, 0xC0, 0xC1, 0xC5):
    SITE_OPS[_op] = ("C", 2)
SITE_OPS[0x12] = ("L", 1)
SITE_OPS[0x13] = ("L", 2)


def iter_sites(code):
    """遍历字节码，yield (kind, cp_index, pc)。kind: M/F/C/L(ldc)。"""
    i = 0
    n = len(code)
    while i < n:
        op = code[i]
        rec = SITE_OPS.get(op)
        if rec is not None:
            kind, w = rec
            idx = code[i + 1] if w == 1 else u2(code, i + 1)
            yield kind, idx, i
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


DESC_TYPE_RE = re.compile(r"L([^;<>]+);")


def desc_types(desc):
    return DESC_TYPE_RE.findall(desc)


# ---- 注解解析（只为从 @Mixin 里拿 target）


def _skip_element_value(b, p, collect):
    tag = b[p]
    p += 1
    if tag in (0x42, 0x43, 0x44, 0x46, 0x49, 0x4A, 0x53, 0x5A, 0x73):   # B C D F I J S Z s
        if tag == 0x73 and collect is not None:
            collect.append(("s", u2(b, p)))
        return p + 2
    if tag in (0x65, 0x63):                                              # e / c
        if tag == 0x63 and collect is not None:
            collect.append(("c", u2(b, p)))
        return p + 4
    if tag == 0x40:                                                      # @
        return _skip_annotation(b, p, None)
    if tag == 0x5B:                                                      # [
        n = u2(b, p)
        p += 2
        for _ in range(n):
            p = _skip_element_value(b, p, collect)
        return p
    raise BadClass("bad element_value tag %r" % tag)


def _skip_annotation(b, p, collect):
    ti = u2(b, p)
    n = u2(b, p + 2)
    p += 4
    for _ in range(n):
        _name_idx = u2(b, p)
        p = _skip_element_value(b, p + 2, collect)
    return p


def _extract_mixin_targets(b, attr_body, utf8):
    """从 RuntimeVisible/InvisibleAnnotations 的 body 里取 @Mixin 的 target。"""
    out = set()
    p = attr_body
    na = u2(b, p)
    p += 2
    for _ in range(na):
        ti = u2(b, p)
        npairs = u2(b, p + 2)
        p += 4
        is_mixin = (utf8(ti) == MIXIN_ANN)
        coll = [] if is_mixin else None
        for _k in range(npairs):
            p = _skip_element_value(b, p + 2, coll)      # +2 跳过 element_name_index
        if is_mixin and coll:
            for tag, idx in coll:
                try:
                    v = utf8(idx)
                except BadClass:
                    continue
                if tag == "c":
                    # 形如 Lnet/minecraft/world/level/Level;
                    if v.startswith("L") and v.endswith(";"):
                        out.add(v[1:-1])
                else:
                    if "." in v and " " not in v:
                        out.add(v.replace(".", "/"))
    return out


def parse_class(data, want_sites=False, want_mixin=False):
    """解析一个 class，返回 dict。

      name / super / ifaces / is_iface
      methods {name: set(desc)}   fields {name: set(desc)}
      class_refs set(内部名)     —— 常量池里所有 Class 常量
      type_refs  set(内部名)     —— super/ifaces/描述符/异常表/指令里真正用到的类型
      sites [(kind, owner, name, desc, enclosing_method, enclosing_desc, line)]
      mixin_targets set(内部名)
    """
    entries, pool_end = parse_pool(data)
    buf = data
    cp = {}
    i = 1
    for tag, s, e in entries:
        cp[i] = (tag, s, e)
        i += 2 if tag in (5, 6) else 1

    _utf8 = {}

    def utf8(idx):
        v = _utf8.get(idx)
        if v is None:
            ent = cp.get(idx)
            if ent is None or ent[0] != 1:
                raise BadClass("cp %r not utf8" % (idx,))
            s = ent[1]
            v = buf[s + 3:s + 3 + u2(buf, s + 1)].decode("utf-8", "replace")
            _utf8[idx] = v
        return v

    def cls_name(idx):
        ent = cp.get(idx)
        if ent is None or ent[0] != 7:
            return None
        return utf8(u2(buf, ent[1] + 1))

    pos = pool_end
    access = u2(buf, pos)
    this_name = cls_name(u2(buf, pos + 2))
    sup = cls_name(u2(buf, pos + 4))
    pos += 6
    icount = u2(buf, pos)
    pos += 2
    ifaces = []
    for _ in range(icount):
        nm = cls_name(u2(buf, pos))
        if nm:
            ifaces.append(nm)
        pos += 2

    type_refs = set()
    class_refs = set()
    if this_name:
        type_refs.add(this_name)
    if sup:
        if sup != "java/lang/Object":
            type_refs.add(sup)
    type_refs.update(ifaces)

    # 常量池里的 Class 常量（含注解里的、残留的）
    for idx, (tag, s, e) in cp.items():
        if tag == 7:
            nm = cls_name(idx)
            if nm:
                class_refs.add(nm)

    def read_members(pos, want_code):
        count = u2(buf, pos)
        pos += 2
        out = {}
        codes = []
        for _ in range(count):
            mname = utf8(u2(buf, pos + 2))
            mdesc = utf8(u2(buf, pos + 4))
            acount = u2(buf, pos + 6)
            pos += 8
            out.setdefault(mname, set()).add(mdesc)
            for t in desc_types(mdesc):
                type_refs.add(t)
            for _a in range(acount):
                aname_idx = u2(buf, pos)
                alen = u4(buf, pos + 2)
                body = pos + 6
                if want_code:
                    aname = utf8(aname_idx)
                    if aname == "Code":
                        codes.append((mname, mdesc, body, alen))
                    elif aname == "Exceptions":
                        n = u2(buf, body)
                        for k in range(n):
                            nm = cls_name(u2(buf, body + 2 + 2 * k))
                            if nm:
                                type_refs.add(nm)
                pos = body + alen
        return out, pos, codes

    fields, pos, _ = read_members(pos, False)
    methods, pos, codes = read_members(pos, want_sites)

    mixin_targets = set()
    if want_mixin:
        # 注解的 type 是 **Utf8 常量**（不是 Class 常量），所以只能比字节
        has_mixin_ann = False
        for _idx, (tag, s, e) in cp.items():
            if tag == 1 and buf[s + 3:e] == MIXIN_ANN_BYTES:
                has_mixin_ann = True
                break
        if has_mixin_ann:
            pos2 = pos
            acount = u2(buf, pos2)
            pos2 += 2
            for _k in range(acount):
                aname_idx = u2(buf, pos2)
                alen = u4(buf, pos2 + 2)
                body = pos2 + 6
                try:
                    aname = utf8(aname_idx)
                    if aname in ("RuntimeVisibleAnnotations", "RuntimeInvisibleAnnotations"):
                        mixin_targets |= _extract_mixin_targets(buf, body, utf8)
                except Exception:
                    pass
                pos2 = body + alen

    sites = []
    if want_sites and codes:
        ref_by_idx = {}
        for idx, (tag, s, e) in cp.items():
            if tag in (9, 10, 11):
                owner = cls_name(u2(buf, s + 1))
                nat = u2(buf, s + 3)
                ent = cp.get(nat)
                if owner is None or ent is None:
                    continue
                ns = ent[1]
                nm = utf8(u2(buf, ns + 1))
                ds = utf8(u2(buf, ns + 3))
                ref_by_idx[idx] = ("F" if tag == 9 else "M", owner, nm, ds)
                type_refs.add(owner)
                for t in desc_types(ds):
                    type_refs.add(t)

        for mname, mdesc, body, alen in codes:
            clen = u4(buf, body + 4)
            code = buf[body + 8:body + 8 + clen]
            if len(code) != clen:
                continue
            etpos = body + 8 + clen
            if etpos + 2 > len(buf):
                continue
            etlen = u2(buf, etpos)
            for k in range(etlen):
                base = etpos + 2 + 8 * k
                ctype = u2(buf, base + 6)
                if ctype:
                    nm = cls_name(ctype)
                    if nm:
                        type_refs.add(nm)
            apos = etpos + 2 + 8 * etlen
            if apos + 2 > len(buf):
                continue
            acount = u2(buf, apos)
            apos += 2
            line_at = None
            for _k in range(acount):
                aidx = u2(buf, apos)
                alen2 = u4(buf, apos + 2)
                try:
                    is_lnt = (utf8(aidx) == "LineNumberTable")
                except Exception:
                    is_lnt = False
                if is_lnt:
                    p = apos + 6
                    n = u2(buf, p)
                    pairs = []
                    for q in range(n):
                        if p + 6 + 4 * q > len(buf):
                            break
                        pairs.append((u2(buf, p + 2 + 4 * q), u2(buf, p + 4 + 4 * q)))
                    if pairs:
                        line_at = pairs
                apos += 6 + alen2

            for kind, idx, pc in iter_sites(code):
                if kind == "L":
                    ent = cp.get(idx)
                    if ent is not None and ent[0] == 7:
                        nm = cls_name(idx)
                        if nm:
                            type_refs.add(nm)
                    continue
                ref = ref_by_idx.get(idx)
                if ref is None:
                    continue
                rk, owner, rn, rd = ref
                if kind == "C":
                    continue
                line = None
                if line_at:
                    for start_pc, ln in line_at:
                        if start_pc <= pc:
                            line = ln
                        else:
                            break
                sites.append((rk, owner, rn, rd, mname, mdesc, line))

    return {
        "name": this_name,
        "super": sup,
        "ifaces": ifaces,
        "is_iface": bool(access & 0x0200),
        "methods": methods,
        "fields": fields,
        "class_refs": class_refs,
        "type_refs": type_refs,
        "sites": sites,
        "mixin_targets": mixin_targets,
    }


# ------------------------------------------------------------------ jar walking


def iter_jar_classes(path, depth=0):
    """yield (内部类名, class 字节)。递归展开 META-INF/jars/*.jar（最多 4 层）。"""
    try:
        z = zipfile.ZipFile(path)
    except Exception as e:
        print("[warn] cannot open %s: %s" % (path, e), flush=True)
        return
    with z:
        for info in z.infolist():
            nm = info.filename
            if not nm.endswith(".class") or nm.startswith("META-INF/"):
                continue
            if nm.endswith(("module-info.class", "package-info.class")):
                continue
            try:
                data = z.read(info)
            except Exception:
                continue
            yield nm[:-6], data
        if depth >= MAX_NEST_DEPTH:
            return
        for info in z.infolist():
            nm = info.filename
            if not (nm.endswith(".jar") and nm.startswith(("META-INF/jars/", "META-INF/jarjar/"))):
                continue
            try:
                blob = z.read(info)
                nz = zipfile.ZipFile(io.BytesIO(blob))
            except Exception:
                continue
            with nz:
                for sub in nz.infolist():
                    s = sub.filename
                    if s.endswith(".class") and not s.startswith("META-INF/") \
                            and not s.endswith(("module-info.class", "package-info.class")):
                        try:
                            yield s[:-6], nz.read(sub)
                        except Exception:
                            pass
                for sub in nz.infolist():
                    s = sub.filename
                    if not (s.endswith(".jar") and s.startswith("META-INF/jars/")):
                        continue
                    if depth + 1 >= MAX_NEST_DEPTH:
                        continue
                    try:
                        blob2 = nz.read(sub)
                        nz2 = zipfile.ZipFile(io.BytesIO(blob2))
                    except Exception:
                        continue
                    with nz2:
                        for s2 in nz2.infolist():
                            f2 = s2.filename
                            if f2.endswith(".class") and not f2.startswith("META-INF/") \
                                    and not f2.endswith(("module-info.class", "package-info.class")):
                                try:
                                    yield f2[:-6], nz2.read(s2)
                                except Exception:
                                    pass


# ------------------------------------------------------------------ JDK 继承链
#
# ⚠ 为什么需要这一段（这是一次实测误报的教训）：
#   枚举 ``Direction$Axis`` 的父类是 ``java/lang/Enum``，``ordinal()`` / ``name()`` 都声明在那里。
#   如果索引里没有 ``java/lang/Enum``，沿 BFS 走到父类就断了 ⇒ 把 **每一次** ``.ordinal()``
#   都报成 NoSuchMethodError。同理 ``ImmutableList.size()``（继承自
#   ``java/util/AbstractCollection``）、``ImmutableMap.forEach()``（``java/util/Map`` 的 default）。
#   首轮扫描里这一类占了近一半的「高危」。
#
# ⇒ 用 javap 把**索引里出现过的 java.*/javax.* 父类型及其父类型**补进索引。
#   注意：这**不是**审计 JDK（JDK 引用仍然直接跳过不查），只是让「继承来的成员」能被解析。
#   刻意不做全量 JDK 索引：只要被继承到的那一小块。

JAVAP_CANDIDATES = (
    MC_HOME / "runtime" / "java-runtime-epsilon" / "bin" / "javap.exe",
    MC_HOME / "runtime" / "java-runtime-delta" / "bin" / "javap.exe",
)

_MEMBER_KW = re.compile(r"\b(class|interface|enum|@interface)\s+([\w.$]+)")
_EXTENDS = re.compile(r"\bextends\s+(.+?)(?:\s+implements\s+|\s*\{)", re.S)
_IMPLEM = re.compile(r"\bimplements\s+(.+?)\s*\{", re.S)


def find_javap():
    for p in JAVAP_CANDIDATES:
        if Path(p).is_file():
            return str(p)
    return None


def _split_type_list(s):
    out = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        part = part.split("<", 1)[0].strip()
        if part:
            out.append(part.replace(".", "/"))
    return out


def _member_name(decl, desc, simple):
    if desc.endswith("()V") and "static {}" in decl:
        return "<clinit>"
    if "(" in desc:
        i = decl.find("(")
        head = decl[:i].strip()
        if not head:
            return None
        nm = head.split()[-1]
        if nm.split(".")[-1] == simple:
            return "<init>"
        return nm
    body = decl.rstrip(";").strip()
    toks = body.split()
    return toks[-1] if toks else None


def parse_javap_output(text):
    """解析 `javap -p -s` 的输出，返回 {owner: (is_iface, sup, [ifaces], methods, fields)}。"""
    out = {}
    cur = None
    cur_simple = None
    pending = None
    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            continue
        if s.endswith("{") and _MEMBER_KW.search(s) and not s.startswith(("descriptor", "Code")):
            m = _MEMBER_KW.search(s)
            kind = m.group(1)
            fqn = m.group(2)
            owner = fqn.replace(".", "/")
            cur_simple = fqn.rsplit(".", 1)[-1]
            sup = None
            ifaces = []
            me = _EXTENDS.search(s)
            mi = _IMPLEM.search(s)
            if kind == "interface":
                if me:
                    ifaces = _split_type_list(me.group(1))
            else:
                if me:
                    lst = _split_type_list(me.group(1))
                    if lst:
                        sup = lst[0]
                if mi:
                    ifaces = _split_type_list(mi.group(1))
            if sup == "java/lang/Object":
                sup = None
            cur = (kind == "interface", sup, ifaces, set(), set())
            out[owner] = cur
            pending = None
            continue
        if s.startswith("descriptor:") and pending is not None and cur is not None:
            desc = s.split(":", 1)[1].strip()
            nm = _member_name(pending, desc, cur_simple)
            if nm:
                (cur[3] if "(" in desc else cur[4]).add((nm, desc))
            pending = None
            continue
        if cur is not None and (";" in s or s.startswith(("public ", "private ", "protected ",
                                                         "static ", "final ", "abstract ",
                                                         "native ", "synchronized ", "default ",
                                                         "transient ", "volatile "))):
            pending = s
    return out


def run_javap(javap, names):
    args = [javap, "-p", "-s"] + [n.replace("/", ".") for n in names]
    try:
        r = subprocess.run(args, capture_output=True, timeout=180)
    except Exception as e:
        print("[warn] javap failed: %s" % e, flush=True)
        return ""
    return (r.stdout or b"").decode("utf-8", "replace")


def extend_index_with_jdk(classes, mem_m, mem_f, javap, max_rounds=6, chunk=80):
    """把 `classes` 里出现过的 JDK 父类型（递归）补进索引；只补被继承到的那部分。"""
    if not javap:
        return 0
    tried = set()
    added = 0
    for rnd in range(max_rounds):
        todo = set()
        for sup, ifaces, _ in classes.values():
            if sup and sup.startswith(JDK_PREFIXES) and sup not in classes:
                todo.add(sup)
            for i in ifaces:
                if i.startswith(JDK_PREFIXES) and i not in classes:
                    todo.add(i)
        todo -= tried
        if not todo:
            break
        todo = sorted(todo)
        tried.update(todo)
        for k in range(0, len(todo), chunk):
            part = todo[k:k + chunk]
            parsed = parse_javap_output(run_javap(javap, part))
            for owner, (is_iface, sup, ifaces, methods, fields) in parsed.items():
                if owner in classes:
                    continue
                classes[owner] = (sup, tuple(ifaces), is_iface)
                for nm, d in methods:
                    mem_m.add((owner, nm, d))
                for nm, d in fields:
                    mem_f.add((owner, nm, d))
                added += 1
        print("[jdk r%d] asked=%d added=%d total_classes=%d"
              % (rnd + 1, len(todo), added, len(classes)), flush=True)
    return added


def collect_universe_jar_list(mods_dir, mc_jar, libs_dir, use_libs):
    jars = []
    if mc_jar and Path(mc_jar).is_file():
        jars.append(str(mc_jar))
    if use_libs and libs_dir and Path(libs_dir).is_dir():
        for p in sorted(Path(libs_dir).rglob("*.jar")):
            sp = str(p)
            if any(s in sp for s in LIBS_SKIP_SUBSTR):
                continue
            jars.append(sp)
    if mods_dir and Path(mods_dir).is_dir():
        for p in sorted(Path(mods_dir).glob("*.jar")):
            jars.append(str(p))
    return jars


def build_index(jars, mod_jar_set=()):
    """建「可用成员索引」。返回 (classes, mem_m, mem_f, mixin_targeted, mixin_edges)。"""
    classes = {}
    mem_m = set()
    mem_f = set()
    mixin_targeted = set()
    mixin_edges = defaultdict(set)
    n_cls = 0
    t0 = time.time()
    for k, jpath in enumerate(jars, 1):
        got = 0
        # @Mixin 的 target 只在 mod jar 里找（libraries 里没有，且 Utf8 全扫更贵）
        want_mixin = jpath in mod_jar_set
        for name, data in iter_jar_classes(jpath):
            n_cls += 1
            got += 1
            try:
                info = parse_class(data, want_sites=False, want_mixin=want_mixin)
            except Exception:
                continue
            nm = info["name"] or name
            sup = info["super"]
            if sup == "java/lang/Object":
                sup = None
            classes[nm] = (sup, tuple(info["ifaces"]), info["is_iface"])
            for mn, descs in info["methods"].items():
                for d in descs:
                    mem_m.add((nm, mn, d))
            for fn, descs in info["fields"].items():
                for d in descs:
                    mem_f.add((nm, fn, d))
            if info["mixin_targets"]:
                mixin_targeted |= info["mixin_targets"]
                # `@Mixin(T.class) interface X` 里的 X **不继承 T**，所以类图上没 X->T 这条边。
                # 但 X 里声明的方法会被织进 T ⇒ 手动补上图边，否则「一个 mixin 接口给 T 提供方法」
                # （Create 大量使用）会全部误报。
                for t in info["mixin_targets"]:
                    mixin_edges[t].add(nm)
        print("[idx %3d/%3d] %-56s +%-6d total=%-7d %.1fs"
              % (k, len(jars), os.path.basename(jpath)[:56], got, n_cls, time.time() - t0), flush=True)
    print("[idx] classes=%d methods=%d fields=%d mixin_targets=%d mixin_edges=%d"
          % (len(classes), len(mem_m), len(mem_f), len(mixin_targeted), len(mixin_edges)), flush=True)
    return classes, mem_m, mem_f, mixin_targeted, mixin_edges


# ------------------------------------------------------------------ resolution


class Resolver:
    def __init__(self, classes, mem_m, mem_f, mixin_edges=None):
        self.classes = classes
        self.mem_m = mem_m
        self.mem_f = mem_f
        self.mixin_edges = mixin_edges or {}
        self._sup = {}
        self._lk = {}
        self._impl = None            # iface -> set(implementors)
        self._woven = {}

    def class_exists(self, name):
        if not name:
            return True
        if name.startswith("["):
            inner = name.lstrip("[")
            if inner.startswith("L") and inner.endswith(";"):
                name = inner[1:-1]
            else:
                return True
        if name.startswith(JDK_PREFIXES):
            return True
        return name in self.classes

    def is_iface(self, name):
        e = self.classes.get(name)
        return bool(e and e[2])

    def supertypes(self, owner):
        c = self._sup.get(owner)
        if c is not None:
            return c
        seen = set()
        stack = [owner]
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            ent = self.classes.get(x)
            if not ent:
                continue
            sup, ifaces, _ = ent
            if sup and sup != "java/lang/Object":
                stack.append(sup)
            stack.extend(ifaces)
        seen = frozenset(seen)
        self._sup[owner] = seen
        return seen

    def lookup(self, owner, name, desc, mem, obj_ok):
        """沿「自身 → 父类 → 父接口」BFS 找成员。

        返回 (found_owner_or_None, jdk_unknown)。
        `jdk_unknown=True` 表示链上碰到一个**没进索引的 JDK 类型**（javap 拿不到，比如
        该 JRE 里没有 awt 模块）—— 这时候「找不到」不等于「不存在」，必须降级成待验证。
        """
        key = (owner, name, desc, obj_ok)
        c = self._lk.get(key)
        if c is not None:
            return c
        seen = set()
        stack = [owner]
        jdk_unknown = False
        found = None
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            ent = self.classes.get(x)
            if ent is None:
                if x.startswith(JDK_PREFIXES):
                    jdk_unknown = True
                continue
            if (x, name, desc) in mem:
                found = x
                break
            sup, ifaces, _ = ent
            if sup:
                stack.append(sup)
            stack.extend(ifaces)
        if found is None and obj_ok and (name, desc) in OBJECT_METHODS:
            found = "<Object>"
            jdk_unknown = False
        res = (found, jdk_unknown)
        self._lk[key] = res
        return res

    def has_method(self, owner, name, desc):
        return self.lookup(owner, name, desc, self.mem_m, True)[0]

    def has_field(self, owner, name, desc):
        return self.lookup(owner, name, desc, self.mem_f, False)[0]

    # ---- 织入放宽
    def build_implementors(self):
        """type -> 直接/间接继承它（或实现它）的**所有**子类型。

        用途：mixin 的 `@Mixin(Target.class) interface Foo` 会把 `Foo` 的 default 方法
        **织进 Target**。于是「Target 上没有这个方法」在运行期可能是有的 ——
        判据就是：Target 的某个子类型声明了同名同描述符的方法。
        """
        if self._impl is not None:
            return self._impl
        impl = defaultdict(set)
        for t, mixins in self.mixin_edges.items():
            impl[t] |= set(mixins)
        for c in self.classes:
            for s in self.supertypes(c):
                if s != c:
                    impl[s].add(c)
        self._impl = impl
        return impl

    def woven_provider(self, owner, name, desc, mem=None):
        """owner 的某个子类型是否声明了 (name, desc)。返回那个子类型名或 None。"""
        key = (owner, name, desc)
        if key in self._woven:
            return self._woven[key]
        r = None
        for c in (self.build_implementors().get(owner) or ()):
            if (c, name, desc) in (mem if mem is not None else self.mem_m):
                r = c
                break
        self._woven[key] = r
        return r

    def relax(self, owner, name, desc, mem):
        """沿 owner 的**接口链**再看一层：调用点能否通过某个接口+织入解析到。"""
        for i in self.supertypes(owner):
            if i != owner and not self.is_iface(i):
                continue
            got = self.woven_provider(i, name, desc, mem)
            if got:
                return (i, got)
        return None


# ------------------------------------------------------------------ classify

HIGH_METHODS = {
    "read", "write", "tick", "tickBlockEntity", "neighborChanged", "onNeighborChange",
    "use", "useItemOn", "useWithoutItem", "onPlace", "setPlacedBy", "onRemove",
    "playerDestroy", "playerWillDestroy", "getStateForPlacement", "updateShape",
    "getShape", "randomTick", "animateTick", "saveAdditional", "loadAdditional",
    "getUpdatePacket", "getUpdateTag", "handleUpdateTag", "dropResources",
    "getDrops", "spawnAdditional", "getAnalogOutputSignal", "isSignalSource",
    "getSignal", "hasAnalogOutput", "affectNeighborsAfterRemoval",
    "getTicker", "createTicker", "serverTick", "clientTick",
    "registerBlockEntities", "registerBlocks", "registerItems", "register",
    "<clinit>", "registerClient", "init", "bootstrap",
}

MED_METHODS = {
    "render", "renderItem", "draw", "getTooltip", "tooltip", "appendHoverText",
    "matches", "assemble", "getResultItem", "isSpecial", "encode", "decode",
    "handle", "receive", "apply", "getIcon", "getRenderShape", "getTexture",
    "provideLang", "addLayers", "createGui", "extract", "write", "read", "save",
}

HIGH_CLASS_HINTS = ("Block", "BlockEntity", "Entity", "Registry", "Bootstrap",
                    "ModBlocks", "ModItems", "ModBlockEntities", "Registrate", "Ticker")
MED_CLASS_HINTS = ("Screen", "Menu", "Render", "Renderer", "Widget", "Gui", "Overlay",
                   "Model", "Sprite", "Recipe", "Serializer", "Packet", "Client",
                   "Tooltip", "Ponder")

SCENARIO = {
    "read": "从存档/网络读这个对象时",
    "write": "往存档/网络写这个对象时",
    "tick": "每 tick 更新时（世界里一直跑）",
    "tickBlockEntity": "方块实体每 tick 更新时",
    "neighborChanged": "相邻方块变化时（放置/拆除/更新）",
    "onNeighborChange": "相邻方块变化时",
    "use": "玩家右键这个方块/物品时",
    "useItemOn": "玩家右键这个方块时",
    "useWithoutItem": "玩家空手右键时",
    "onPlace": "放下这个方块时",
    "setPlacedBy": "玩家放置这个方块时",
    "onRemove": "拆掉这个方块时",
    "playerDestroy": "玩家挖掉这个方块时",
    "getStateForPlacement": "玩家放置这个方块时",
    "updateShape": "方块形状/连接需要重算时",
    "getShape": "碰撞箱/形状被查询时",
    "randomTick": "随机 tick 时",
    "saveAdditional": "存档保存时",
    "loadAdditional": "存档加载时",
    "<clinit>": "类第一次被加载时（注册期几乎必然）",
    "<init>": "构造这个对象时",
    "render": "渲染这一帧时",
    "getTooltip": "把鼠标停在物品/方块上看 tooltip 时",
    "matches": "配方匹配时",
    "assemble": "合成出结果时",
    "encode": "发包时",
    "decode": "收包时",
    "register": "注册期（启动时）",
}

ERRTYPE = {"M": "NoSuchMethodError", "F": "NoSuchFieldError", "C": "NoClassDefFoundError"}


def classify(cls_name, method_name):
    short = cls_name.rsplit("/", 1)[-1]
    short = re.sub(r"\$.*$", "", short)
    m = method_name or ""
    if m == "<clinit>":
        return "HIGH", "静态初始化（类一加载就跑，注册期必然）"
    if m in HIGH_METHODS:
        return "HIGH", "热点路径 %s()" % m
    if m == "<init>" and any(h in short for h in ("Block", "BlockEntity", "Entity", "Item")):
        return "HIGH", "方块/实体/物品构造（注册期）"
    if any(h in short for h in HIGH_CLASS_HINTS):
        return "HIGH", "方块/实体/注册类体内引用"
    if m in MED_METHODS:
        return "MED", "GUI/渲染/配方/网络 %s()" % m
    if any(h in short for h in MED_CLASS_HINTS):
        return "MED", "GUI/渲染/配方/网络 类"
    if m == "<init>":
        return "MED", "构造器"
    return "LOW", "其它路径"


def scenario_for(g, method_name):
    m = method_name or ""
    s = SCENARIO.get(m)
    if s is None:
        short = (g.get("top_cls") or "").rsplit("/", 1)[-1]
        if any(h in short for h in ("Block", "BlockEntity", "Entity")):
            s = "该方块/实体被操作时"
        else:
            s = "走到 %s() 这条路径时" % (m or "该类")
    return "%s → %s" % (s, ERRTYPE[g["kind"]])


# ------------------------------------------------------------------ scan


def scan_jar(jpath, resolver, verbose=False):
    out = []
    for nm, data in iter_jar_classes(jpath):
        try:
            info = parse_class(data, want_sites=True)
        except Exception:
            continue
        cname = info["name"] or nm
        for t in info["type_refs"]:
            if not resolver.class_exists(t):
                out.append({"kind": "C", "owner": t, "name": "", "desc": "",
                            "cls": cname, "method": "", "line": None, "pc": None})
        for kind, owner, name, desc, mname, mdesc, line in info["sites"]:
            if owner.startswith(JDK_PREFIXES):
                continue
            if kind == "M":
                found, jdkunk = resolver.lookup(owner, name, desc, resolver.mem_m, True)
                if found is None:
                    w = resolver.relax(owner, name, desc, resolver.mem_m)
                    out.append({"kind": "M", "owner": owner, "name": name, "desc": desc,
                                "cls": cname, "method": mname, "line": line,
                                "jdk_unknown": jdkunk,
                                "woven": ("%s <- %s" % w) if w else ""})
            else:
                found, jdkunk = resolver.lookup(owner, name, desc, resolver.mem_f, False)
                if found is None:
                    w = resolver.relax(owner, name, desc, resolver.mem_f)
                    out.append({"kind": "F", "owner": owner, "name": name, "desc": desc,
                                "cls": cname, "method": mname, "line": line,
                                "jdk_unknown": jdkunk,
                                "woven": ("%s <- %s" % w) if w else ""})
    return out


# ------------------------------------------------------------------ main


def main():
    ap = argparse.ArgumentParser(description="static landmine scanner for MC 26.3 mod jars")
    ap.add_argument("--mods", default=str(DEFAULT_MODS))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--json", default=None)
    ap.add_argument("--mc", default=str(DEFAULT_MC))
    ap.add_argument("--libs", default=str(MC_HOME / "libraries"))
    ap.add_argument("--no-libs", action="store_true")
    ap.add_argument("--no-jdk-index", action="store_true")
    ap.add_argument("--universe-extra", default=None,
                    help="额外加进索引、但**不当作扫描目标**的 jar 目录（做 A/B 自检用）")
    ap.add_argument("--only", default=None)
    ap.add_argument("--skip", default=None)
    ap.add_argument("--allow", default=str(DEFAULT_ALLOW))
    ap.add_argument("--max-rows", type=int, default=400)
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    mods_dir = Path(a.mods)
    if not mods_dir.is_dir():
        print("[fatal] --mods not a directory: %s" % mods_dir, file=sys.stderr)
        return 1
    mc_jar = Path(a.mc)
    if not mc_jar.is_file():
        print("[fatal] MC jar not found: %s" % mc_jar, file=sys.stderr)
        return 2

    universe = collect_universe_jar_list(mods_dir, mc_jar, a.libs, not a.no_libs)
    if a.universe_extra and Path(a.universe_extra).is_dir():
        for p in sorted(Path(a.universe_extra).rglob("*.jar")):
            universe.append(str(p))
    skip = [s for s in (a.skip or "").split(",") if s]
    if skip:
        universe = [j for j in universe if not any(s in os.path.basename(j) for s in skip)]
    n_mods = len([j for j in universe if os.path.dirname(j) == str(mods_dir)])
    print("[idx] universe jars=%d (mc=1 libs=%s mods=%d)"
          % (len(universe), "off" if a.no_libs else "on", n_mods), flush=True)
    mod_jars = [j for j in universe if os.path.dirname(j) == str(mods_dir)]
    classes, mem_m, mem_f, mixin_targeted, mixin_edges = build_index(universe, set(mod_jars))
    if not classes:
        print("[fatal] empty index", file=sys.stderr)
        return 2
    javap = None if a.no_jdk_index else find_javap()
    n_jdk = 0
    if javap:
        n_jdk = extend_index_with_jdk(classes, mem_m, mem_f, javap)
        print("[jdk] added %d JDK supertype classes (javap=%s)" % (n_jdk, javap), flush=True)
    else:
        print("[jdk] javap not found -> 继承自 JDK 的成员会落进「待验证」", flush=True)
    if a.stats:
        return 0

    targets = mod_jars
    if a.only:
        want = [s for s in a.only.split(",") if s]
        targets = [j for j in targets if any(w in os.path.basename(j) for w in want)]
    print("[scan] targets=%d" % len(targets), flush=True)

    r = Resolver(classes, mem_m, mem_f, mixin_edges)
    t0 = time.time()
    results = {}
    for i, j in enumerate(targets, 1):
        refs = scan_jar(j, r, verbose=a.verbose)
        results[os.path.basename(j)] = refs
        print("[scan %3d/%3d] %-50s raw=%-6d %.1fs"
              % (i, len(targets), os.path.basename(j)[:50], len(refs), time.time() - t0), flush=True)

    rows = []
    for jar, refs in results.items():
        for x in refs:
            y = dict(x)
            y["jar"] = jar
            rows.append(y)
    print("[sum] raw instruction-level findings=%d" % len(rows), flush=True)

    # ---------------- 允许清单
    allow = {}
    if Path(a.allow).is_file():
        try:
            allow = json.loads(Path(a.allow).read_text(encoding="utf-8"))
        except Exception as e:
            print("[warn] allowlist unreadable: %s" % e, flush=True)
    allow_members = {tuple(k) for k in (allow.get("members") or [])}
    allow_classes = set(allow.get("classes") or [])
    allow_prefix = tuple(allow.get("class_prefixes") or [])
    allow_jars = tuple(allow.get("jar_prefixes") or [])

    dropped = 0
    kept = []
    for x in rows:
        if allow_jars and any(x["jar"].startswith(p) for p in allow_jars):
            dropped += 1
            continue
        if x["kind"] != "C":
            if (x["owner"], x["name"], x["desc"]) in allow_members:
                dropped += 1
                continue
        if x["owner"] in allow_classes or (allow_prefix and x["owner"].startswith(allow_prefix)):
            dropped += 1
            continue
        kept.append(x)
    print("[sum] after allowlist=%d (dropped %d)" % (len(kept), dropped), flush=True)

    # ---------------- 归组 + 分类
    # 包名前缀集合：用于区分「26.3 删了/改名了」与「这个可选依赖根本没装」
    ns_present = set()
    ns_count = Counter()
    for c in classes:
        parts = c.split("/")
        if len(parts) > NS_DEPTH:
            k = "/".join(parts[:NS_DEPTH])
            ns_present.add(k)
            ns_count[k] += 1

    # 包名 -> 简单类名，用给「缺类」猜近名（如 RedStoneWireBlock -> RedstoneWireBlock）
    pkg_names = defaultdict(list)
    for c in classes:
        p, _, s = c.rpartition("/")
        pkg_names[p].append(s)

    # 「名字在、描述符不在」= 26.3 改签名的强信号
    owners_names = defaultdict(set)
    for (c, nm, d) in mem_m:
        owners_names[(c, nm)].add(d)
    for (c, nm, d) in mem_f:
        owners_names[(c, nm)].add(d)

    groups = defaultdict(list)
    for x in kept:
        groups[(x["kind"], x["owner"], x["name"], x["desc"])].append(x)

    out_groups = []
    n_woven = 0
    for key, sites in groups.items():
        kind, owner, name, desc = key
        # 织入放宽
        woven = None
        if kind == "M" and r.is_iface(owner):
            woven = r.woven_provider(owner, name, desc)
        if woven:
            n_woven += 1
            if a.verbose:
                print("[woven] %s.%s%s  <- %s" % (owner, name, desc, woven), flush=True)
            continue

        best = None
        for s in sites:
            lvl, why = classify(s["cls"], s["method"])
            rank = {"HIGH": 3, "MED": 2, "LOW": 1}[lvl]
            if best is None or rank > best[0]:
                best = (rank, lvl, why)
        lvl, why = best[1], best[2]

        g = {
            "kind": kind, "owner": owner, "name": name, "desc": desc,
            "level": lvl, "reason": why,
            "sites": sorted(sites, key=lambda s: (s["jar"], s["cls"], s["line"] or 0)),
            "n_sites": len(sites),
            "jars": sorted({s["jar"] for s in sites}),
            "nb": {"C": "class", "M": "method", "F": "field"}[kind],
            "alt_descs": sorted(owners_names.get((owner, name), ())),
            "mixin_targeted": owner in mixin_targeted,
            "owner_present": owner in classes,
            "top_cls": sites[0]["cls"],
            "top_method": sites[0]["method"],
            "top_line": sites[0]["line"],
        }
        parts = owner.split("/")
        g["ns_present"] = "/".join(parts[:NS_DEPTH]) in ns_present if not g["owner_present"] else True
        g["suggest"] = ""
        if kind == "C" and not g["owner_present"]:
            p, _, simple = owner.rpartition("/")
            low = simple.lower()
            for cand in pkg_names.get(p, ()):
                if cand != simple and cand.lower() == low:
                    g["suggest"] = cand
                    break
        g["jdk_unknown"] = any(s.get("jdk_unknown") for s in sites)
        g["woven"] = next((s.get("woven") for s in sites if s.get("woven")), "")
        g["pending_kind"] = ""
        if g["mixin_targeted"]:
            g["verdict"] = "待验证"
            g["pending_kind"] = "mixin-target"
        elif g["jdk_unknown"]:
            g["verdict"] = "待验证"
            g["pending_kind"] = "jdk-unknown"
        elif g["woven"]:
            g["verdict"] = "待验证"
            g["pending_kind"] = "woven-subtype"
        elif g["owner_present"]:
            g["verdict"] = "实证"
        elif g["ns_present"]:
            # 包里只有零星几个类 ⇒ 那是「为了编译而随包的一个桩/残片」，不是真依赖
            if ns_count["/".join(parts[:NS_DEPTH])] <= 8:
                g["verdict"] = "非地雷·桩"
            else:
                g["verdict"] = "实证·缺类"
        else:
            g["verdict"] = "非地雷·未安装"
        out_groups.append(g)

    print("[sum] woven-relaxed=%d  groups=%d" % (n_woven, len(out_groups)), flush=True)

    def sort_key(g):
        rank = {"HIGH": 3, "MED": 2, "LOW": 1}[g["level"]]
        verdict_rank = {"实证": 0, "实证·缺类": 1, "待验证": 2, "非地雷·桩": 3, "非地雷·未安装": 4}[g["verdict"]]
        # 同级内：net/minecraft 的缺口优先 —— 那是 26.3 改动直接砸出来的，也最可能被玩家撞上
        mc = 0 if g["owner"].startswith("net/minecraft") else 1
        return (verdict_rank, -rank, mc, -len(g["jars"]), -g["n_sites"])

    out_groups.sort(key=sort_key)

    # ---------------- 输出
    jout = a.json or str(Path(a.out).with_suffix(".json"))
    Path(jout).parent.mkdir(parents=True, exist_ok=True)
    Path(jout).write_text(json.dumps({
        "generated_by": "tools/scan_landmines.py",
        "mc_jar": str(mc_jar),
        "universe_jars": len(universe),
        "index_classes": len(classes),
        "index_methods": len(mem_m),
        "index_fields": len(mem_f),
        "mixin_targets": len(mixin_targeted),
        "targets": [os.path.basename(t) for t in targets],
        "n_groups": len(out_groups),
        "n_sites": sum(g["n_sites"] for g in out_groups),
        "woven_relaxed": n_woven,
        "groups": out_groups,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[out] %s" % jout, flush=True)

    md = render_md(out_groups, classes, mem_m, mem_f, universe, targets, len(rows),
                   n_woven, mixin_targeted, a.max_rows, n_jdk)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(md, encoding="utf-8")
    print("[out] %s" % a.out, flush=True)

    cnt = Counter(g["level"] for g in out_groups if g["verdict"] in ("实证", "实证·缺类"))
    cnt2 = Counter(g["level"] for g in out_groups if g["verdict"] == "待验证")
    cnt3 = sum(1 for g in out_groups if g["verdict"] == "非地雷·未安装")
    print("[done] groups=%d  地雷: HIGH=%d MED=%d LOW=%d | 待验证=%d | 未安装可选依赖=%d"
          % (len(out_groups), cnt.get("HIGH", 0), cnt.get("MED", 0), cnt.get("LOW", 0),
             sum(cnt2.values()), cnt3), flush=True)
    return 0


# ------------------------------------------------------------------ render


def fmt_member(g, with_owner=True):
    short = g["owner"].rsplit("/", 1)[-1] if not with_owner else g["owner"]
    if g["kind"] == "C":
        s = "类 `%s`" % g["owner"]
        if g.get("suggest"):
            s += " → 疑似改名 `%s`" % g["suggest"]
        return s
    if g["kind"] == "M":
        s = "`%s.%s%s`" % (short, g["name"], g["desc"])
    else:
        s = "`%s.%s : %s`" % (short, g["name"], g["desc"])
    alts = [a for a in (g.get("alt_descs") or []) if a != g["desc"]]
    if alts:
        s += " ⚠同名异签名: " + " / ".join("`%s`" % a[:56] for a in alts[:2])
    return s


PENDING_LABEL = {
    "mixin-target": "待验证：该类被某个 @Mixin 认领，成员可能被织入",
    "jdk-unknown": "待验证：继承链上有没建模的 JDK 类型",
    "woven-subtype": "待验证：某子类型声明了同名成员，可能是 mixin 织入",
}


def fmt_sites(g, limit=2):
    parts = []
    for s in g["sites"][:limit]:
        loc = s["cls"].rsplit("/", 1)[-1]
        if s["method"]:
            loc += "." + s["method"].split("(")[0]
        if s["line"]:
            loc += ":%d" % s["line"]
        parts.append(loc)
    txt = " / ".join(parts)
    if len(g["sites"]) > limit:
        txt += " …(+%d)" % (len(g["sites"]) - limit)
    return txt


def render_table(groups, max_rows):
    if not groups:
        return "_（无）_"
    out = ["| # | 缺失成员 | 所属 jar | 类.方法:行 | 什么情况下会炸 | 站点 |",
           "|---|---|---|---|---|---|"]
    for i, g in enumerate(groups[:max_rows], 1):
        jar = ", ".join("`%s`" % j[:-4] for j in g["jars"][:2])
        if len(g["jars"]) > 2:
            jar += " +%d" % (len(g["jars"]) - 2)
        why = scenario_for(g, g["top_method"])
        if g["verdict"] == "待验证":
            why += " 〔%s〕" % PENDING_LABEL.get(g["pending_kind"], g["pending_kind"])
        out.append("| %d | %s | %s | %s | %s | %d |"
                   % (i, fmt_member(g), jar, fmt_sites(g), why, g["n_sites"]))
    if len(groups) > max_rows:
        out.append("")
        out.append("_（还有 %d 条未显示，完整列表见同名 `.json`）_" % (len(groups) - max_rows))
    return "\n".join(out)


def render_md(groups, classes, mem_m, mem_f, universe, targets, n_raw,
              n_woven, mixin_targeted, max_rows, n_jdk=0):
    LANDS = ("实证", "实证·缺类")
    conf_hi = [g for g in groups if g["verdict"] in LANDS and g["level"] == "HIGH"]
    conf_me = [g for g in groups if g["verdict"] in LANDS and g["level"] == "MED"]
    conf_lo = [g for g in groups if g["verdict"] in LANDS and g["level"] == "LOW"]
    lands = conf_hi + conf_me + conf_lo
    pend = [g for g in groups if g["verdict"] == "待验证"]
    opt = [g for g in groups if g["verdict"] == "非地雷·未安装"]
    stub = [g for g in groups if g["verdict"] == "非地雷·桩"]
    by_member = Counter(g["kind"] for g in lands)
    n_missing_cls = sum(1 for g in lands if g["verdict"] == "实证·缺类")

    jars_hit = Counter()
    hi_per_jar = Counter()
    for g in lands:
        for j in g["jars"]:
            jars_hit[j] += 1
    for g in conf_hi:
        for j in g["jars"]:
            hi_per_jar[j] += 1

    L = []
    A = L.append
    A("# 26.3 API 地雷清单（静态扫描）")
    A("")
    A("> 由 `tools/scan_landmines.py` 生成；**只读扫描**，没有改动任何 jar。")
    A("> 复跑：`python tools/scan_landmines.py --mods work/run26/mods-stable --out docs/api-landmines.md`")
    A("")
    A("## 0. 结论")
    A("")
    A("| 指标 | 数值 |")
    A("|---|---|")
    A("| 扫描目标 jar | **%d** |" % len(targets))
    A("| 索引来源 jar（含内嵌） | %d |" % len(universe))
    A("| 索引里可解析的 class | **%d** |" % len(classes))
    A("| 索引里的 方法 / 字段 | %d / %d |" % (len(mem_m), len(mem_f)))
    A("| 被识别为 mixin target 的类 | %d |" % len(mixin_targeted))
    A("| 原始「指令级引用了但索引里没有」 | %d |" % n_raw)
    A("| 被「织入放宽」判为存在的接口方法（不进表） | %d |" % n_woven)
    A("| 去重归组后的全部条目 | %d |" % len(groups))
    A("| — 其中「可选依赖根本没装」（**不计入地雷**） | %d |" % len(opt))
    A("| — 其中「只随包了一个桩」（**不计入地雷**） | %d |" % len(stub))
    A("| — 待验证（见 §4.1） | %d |" % len(pend))
    A("| **地雷总数** | **%d** |" % len(lands))
    A("| ↳ **高危 / 中危 / 低危** | **%d / %d / %d** |"
      % (len(conf_hi), len(conf_me), len(conf_lo)))
    A("| ↳ 其中「owner 类整个不存在」 | %d |" % n_missing_cls)
    A("| 缺类 / 缺方法 / 缺字段（组数） | %d / %d / %d |"
      % (by_member["C"], by_member["M"], by_member["F"]))
    A("")
    A("**一条「地雷」= 一个 `(目标成员, 描述符)`。** 同一个缺失成员被 N 处引用只算 1 条，"
      "但会列全部站点 —— 触发点越多，玩家越容易撞上。")
    A("")
    A("### 0.1 建议先修哪几条")
    A("")
    A("排序依据：**高危** + owner 在 `net/minecraft`（= 26.3 直接改的）+ 引用站点最多。"
      "站点多 = 碰撞概率高。")
    A("")
    A("| 优先 | 缺失成员 | 站点 | 在哪里 |")
    A("|---|---|---|---|")
    _cand = [g for g in conf_hi if g["verdict"] == "实证" and g["owner"].startswith("net/minecraft")]
    _cand.sort(key=lambda g: (-g["n_sites"], -len(g["jars"])))
    for _i, _g in enumerate(_cand[:5], 1):
        A("| %d | %s | %d | %s |" % (_i, fmt_member(_g), _g["n_sites"], fmt_sites(_g, 2)))
    A("")
    A("---")
    A("")
    A("## 1. 高危 —— 方块/实体/物品的 read·write·tick·neighborChanged·use，"
      "以及注册期静态初始化")
    A("")
    A("排序：**判定置信度 → 危险级别 → `net/minecraft` 优先 → 被引用 jar 数 → 站点数**。")
    A("")
    A(render_table(conf_hi, max_rows))
    A("")
    A("## 2. 中危 —— GUI/渲染、配方匹配、tooltip、网络包")
    A("")
    A(render_table(conf_me, max_rows))
    A("")
    A("## 3. 低危 —— 只在特定交互/调试路径")
    A("")
    A(render_table(conf_lo, max_rows))
    A("")
    A("## 4. 不能当实证的三类（单列，**不计入上面的地雷数**）")
    A("")
    A("### 4.1 待验证：拿不准的三种情况（%d 条）" % len(pend))
    A("")
    A("这些成员在索引里确实找不到，但存在一种**可能是假的**理由，所以不敢当成实证：")
    A("")
    A("| 理由 | 含义 |")
    A("|---|---|")
    A("| `mixin-target` | 该类被某个 `@Mixin(...)` 认领 —— 那个 mixin **可能**把缺失成员织了进去 |")
    A("| `woven-subtype` | 它的某个子类型声明了同名同描述符的成员 —— 可能是 mixin 接口注入的 default 方法 |")
    A("| `jdk-unknown` | 继承链上碰到一个没建模的 JDK 类型（该 JRE 里没有 / javap 拿不到） → 无法判定 |")
    A("")
    A("本工具**既不**据此判定它存在，**也不**判定它不存在。表里最后一列会标出具体是哪种理由。")
    A("")
    A("要证实/证伪：在 dev 环境 `javap -p` 看**织入后**的类；或读对应 mixin 类的 `@Inject`/`@Shadow`"
      " 里的成员名；或直接写一个像 `fix-npe-and-itemhelper.md` 里那样的行为级探针跑一次。")
    A("")
    A(render_table(pend, max_rows))
    A("")
    A("### 4.2 可选依赖根本没装（%d 条，**不是地雷**）" % len(opt))
    A("")
    A("这些引用的 owner **连所在包名的前三段都不在索引里** —— 说明那个库/模组根本没装，"
      "而不是 26.3 把它删了。mod 里这类代码几乎都包在"
      " `if (FabricLoader.isModLoaded(\"xxx\"))` 里，那个分支进不去。")
    A("")
    A("**但如果清单里出现了你本以为装着的库 → 那才是真问题**（版本不对 / 没同步进 `mods-stable`）。")
    A("")
    A("| 未安装的包（前三段） | 引用条目数 | 举例（jar） |")
    A("|---|---|---|")
    _opt_pkg = Counter()
    _opt_ex = {}
    for g in opt:
        p = "/".join(g["owner"].split("/")[:3])
        _opt_pkg[p] += 1
        _opt_ex.setdefault(p, g["jars"][0] if g["jars"] else "")
    for p, c in _opt_pkg.most_common(40):
        A("| `%s` | %d | `%s` |" % (p, c, _opt_ex[p]))
    A("")
    A("### 4.3 只随包了「桩」的命名空间（%d 条，**不是地雷**）" % len(stub))
    A("")
    A("这些 owner 类不存在，但该命名空间里**只剩零星几个类**（≤%d）—— 典型是「为了能编译，"
      "随包了一个空壳 API」。只有真的装了对应 mod 才会走到，而那时提供的是真类。" % 8)
    A("")
    A("| 桩命名空间 | 条目数 | 举例（jar） |")
    A("|---|---|---|")
    _stub_pkg = Counter()
    _stub_ex = {}
    for g in stub:
        p = "/".join(g["owner"].split("/")[:3])
        _stub_pkg[p] += 1
        _stub_ex.setdefault(p, g["jars"][0] if g["jars"] else "")
    for p, c in _stub_pkg.most_common(20):
        A("| `%s` | %d | `%s` |" % (p, c, _stub_ex[p]))
    A("")
    A("## 5. 按缺失成员聚合：最普遍的洞")
    A("")
    A("| 缺失成员 | 级别 | 判定 | 站点数 | jar 数 |")
    A("|---|---|---|---|---|")
    for g in sorted(lands, key=lambda g: (-g["n_sites"], -len(g["jars"])))[:40]:
        A("| %s | %s | %s | %d | %d |"
          % (fmt_member(g), g["level"], g["verdict"], g["n_sites"], len(g["jars"])))
    A("")
    A("> ⚠ 这张表按**站点数**排，所以**可选集成**（`dan200/computercraft/*` 33 条 / 173 站点、"
      "`net/mezzdev/config/*` 43 条 / 91 站点）会挤在前排 —— 它们站点多、但**触发概率低**"
      "（对应 mod 没装，或那段 GUI 插件在 Fabric 上不注册）。**要按触发概率看，请用 §1–§3。**")
    A("")
    A("## 6. 按 jar 统计（哪个 jar 最脏）")
    A("")
    A("| jar | 地雷组数 | 其中实证高危 |")
    A("|---|---|---|")
    for j, c in jars_hit.most_common(45):
        A("| `%s` | %d | %d |" % (j, c, hi_per_jar.get(j, 0)))
    A("")
    A("---")
    A("")
    A("## 7. 扫描方法（可复现）")
    A("")
    A("### 7.1 步骤")
    A("")
    A("1. **建索引**：把下面每个 jar 里**每个 class** 解析出 `(owner, name, descriptor)`：")
    A("   - `versions/26.3/26.3.jar`（MC 本体，%d 个 class 进了索引）" % (len(classes),))
    A("   - `fabric-api-0.163.0+26.3.jar` **及其 `META-INF/jars/*.jar` 内嵌模块（递归 4 层）**")
    A("   - `mods-stable` 里**全部 %d 个 jar**（含各自内嵌 jar）⇒ 跨 jar 依赖" % len(targets))
    A("   - `.minecraft/libraries/**/*.jar`（fabric-loader / mixin / joml / fastutil / gson / lwjgl /"
      " guava / asm …；**排除** `net/minecraft/`、`net/neoforged/neoforge/` 下的 jar ——"
      "那里的 1.21.1 全命名 jar 会把 26.3 已删的类**掩盖**成存在）")
    A("   - JDK（`java.*` / `javax.*` / `jdk.*` / `sun.*`）：**本身不审计**，但为了能正确解析"
      "「继承来的成员」，用 `javap -p -s` 把**索引里出现过的 JDK 父类型（递归）** 补进索引"
      "（本次补了 %d 个）。不补的后果很具体：枚举的 `ordinal()`/`name()` 声明在 "
      "`java/lang/Enum`，首轮扫描把**每一个** `.ordinal()` 都报成了 NoSuchMethodError。" % n_jdk)
    A("   - 另外把 `@Mixin(T.class)` 的 **mixin 类手动当成 T 的子类型**：`@Mixin(T.class) interface X`"
      "里 X **不继承** T，类图上没有 X→T 这条边，但 X 声明的方法会被织进 T。不补这条边，"
      "Create 那种「mixin 接口给 `Container` 提供 default 方法」会被整批误报。")
    A("2. **读目标字节码**：每个目标 class 的常量池 + 字段/方法表 + 每条 `Code` 属性：")
    A("   - `getstatic/putstatic/getfield/putfield` → Fieldref")
    A("   - `invokevirtual/invokespecial/invokestatic/invokeinterface` → Methodref / InterfaceMethodref")
    A("   - `new/anewarray/checkcast/instanceof/multianewarray/ldc<class>` → Class")
    A("   - 另外收 super / interfaces / 字段与方法描述符 / 异常表 `catch_type` 里的类型")
    A("   - **不算**常量池里没有被任何指令引用的残留条目（那些运行期不会被解析）")
    A("3. **比对**：沿「自身 → 父类 → 全部父接口」BFS 解析成员；解析不到 ⇒ 再过两道放宽"
      "（织入/混入，§7.2），仍解析不到才记一条。")
    A("4. **去重归组**：按 `(目标成员, 描述符)` 聚合。")
    A("5. **分档**：先判「能不能当实证」，再按**外层方法名**与**外层类名**判危险级别（§7.3）。"
      "判定为「不能当实证」的三种情况直接单列，**不计入地雷数**：")
    A("   - `待验证`：owner 被 `@Mixin` 认领 / 某子类型声明了同名成员 / 继承链碰到没建模的 JDK 类型；")
    A("   - `非地雷·桩`：owner 类不存在，而它所在包只剩 ≤8 个类（随包的空壳 API）；")
    A("   - `非地雷·未安装`：owner 包名的前三段压根不在索引里（这个库没装）。")
    A("")
    A("### 7.2 ⚠ 关键：为什么「`26.3.jar` 里没有」≠「运行时没有」")
    A("")
    A("fabric-api 会**往 MC 的接口/类上织方法**。实测反例：")
    A("")
    A("| 项 | 值 |")
    A("|---|---|")
    A("| 引用 | `ValueInput.contains(String)` |")
    A("| `26.3.jar` 的 `javap` | **看不到这个成员** |")
    A("| 实际提供者 | `fabric-api` 内嵌 `fabric-serialization-api-v1` 的 `FabricValueInput`："
      "`default boolean contains(String)` |")
    A("| 织物 | `ValueInputMixin` 把该 default 方法织进 `ValueInput` |")
    A("| 运行期 | **能调通 ⇒ 不是地雷** |")
    A("")
    A("本工具为此有三层防护：")
    A("")
    A("1. **索引含 fabric-api 的内嵌模块**（递归解开 `META-INF/jars/*.jar`）。")
    A("2. **织入放宽**：解析失败的**接口方法** `I.m(desc)`，若索引里 **I 的某个实现类**"
      "声明了同名同描述符的方法 ⇒ 判「很可能由 mixin 织入」⇒ **不进地雷表**"
      "（本次共放过 %d 个）。" % n_woven)
    A("3. **mixin target 标记**：解析失败的成员若 owner 在某个 `@Mixin(...)` 的 target 里 ⇒ "
      "**降级为「待验证」**而不是「实证」，并单列在 §4。")
    A("")
    A("### 7.3 危险级别 = 玩家触发概率（**不是后果严重度**）")
    A("")
    A("| 级别 | 触发条件（任一） | 为什么 |")
    A("|---|---|---|")
    A("| **高危** | 外层方法 `<clinit>` | 类一加载就执行，注册期几乎必然 |")
    A("| | 外层方法 ∈ {`read`,`write`,`tick`,`neighborChanged`,`use`,`onPlace`,"
      "`updateShape`,`getStateForPlacement`,`randomTick`,`saveAdditional`,`loadAdditional`,"
      "`register*` …} | 放/拆/存/读/每 tick 都走 |")
    A("| | 外层类是 `*Block`/`*BlockEntity`/`*Entity`/`*Item` 且方法为 `<init>` | 注册期就构造 |")
    A("| **中危** | 外层类名含 `Screen`/`Menu`/`Render*`/`Widget`/`Gui`/`Model`/`Recipe`/`Packet`/`Client` |"
      " 开界面 / 匹配方 / 收包才走 |")
    A("| | 外层方法 ∈ {`render`,`draw`,`getTooltip`,`matches`,`assemble`,`encode`,`decode`,`handle` …} | 同上 |")
    A("| **低危** | 其余 | 只在特定交互或调试路径 |")
    A("")
    A("> 任何一条一旦触发都是崩溃；级别只回答「多容易被碰到」。")
    A("")
    A("### 7.4 误报/漏报来源（**读表前必看**）")
    A("")
    A("| # | 来源 | 方向 | 本工具的处理 |")
    A("|---|---|---|---|")
    A("| 1 | **mixin 织入**（fabric-api 或 mod 自己往 MC 类上补 default 方法 / 接口） | 误报 |"
      " 索引含 fabric-api 内嵌 + 实现类放宽 + mixin target 降级（§7.2）。**仍可能误报**："
      "注入的成员不存在于任何实现类、且 target 是靠 `targets=\"...\"` 字符串写的 |")
    A("| 2 | **Access Widener / AT** 只改可见性，不产生新成员 | 不影响 | 本工具只查存在性，不查可见性 |")
    A("| 3 | **第三方库没随包**（`net/neoforged/**` 等） | 真缺但未必是 26.3 删的 |"
      " 若库既不在 `libraries` 也不在 71 jar 里就报「缺类」。这类要人工判断是"
      "「26.3 删了」还是「这包本来就没装」 |")
    A("| 4 | **多版本库共存**（`libraries` 里 guava 20/32/33、fastutil 8.5.12/8.5.18、"
      "lwjgl 3.3.3/3.4.1/3.4.3） | **漏报** | 索引取并集 ⇒ 只在旧版存在的方法被当成存在。"
      "本工具**偏保守**：宁可漏报不误报 |")
    A("| 5 | **StackMapTable 里的类型**未纳索引 | 漏报 | 极少见；只出现在 StackMapTable 的缺类会漏 |")
    A("| 6 | **反射 / 字符串拼出来的成员名**（`Class.forName(\"...\")`、mixin `@Shadow`） | 漏报 |"
      " 字节码里没有 Methodref ⇒ 扫不到。mixin 那一层另有 `tools/audit_mixins26.py` |")
    A("| 7 | **`invokedynamic` 的 bootstrap 目标** | 漏报 | 只解析 `ldc` 的 Class 常量，不展开 MethodHandle |")
    A("| 8 | **死代码 / 不可达分支** | 误报 | 不做可达性分析 ⇒ 引用了就算。"
      "所以「低危」里可能混着永远不执行的 |")
    A("| 9 | **记录类 / 密封类 / 编译器合成桥方法** | 漏报 | 合成成员本就在 class 文件里声明，不影响 |")
    A("")
    A("### 7.5 已知的、已修过的（**不在本清单里**）")
    A("")
    A("| 位置 | 问题 | 状态 |")
    A("|---|---|---|")
    A("| `NameplateBlock` / `HandleBlock` / `DirectionalLinkedReceiverBlock` / "
      "`ModulatingLinkedReceiverBlock` | `Orientation.equals(...)` 传了 `null` ⇒ NPE。"
      "**成员本身存在**，是「参数语义变了」不是「成员没了」 | ✅ 已修，"
      "`aeronautics` SHA `2DF06E76…BD2B`，见 `docs/fix-npe-last2.md` |")
    A("| `ItemHelper.fillItemStackHandler` | 调 `ItemContainerContents.allItemsCopyStream()`"
      "（26.3 已删）| ✅ 已改用 `itemCopies()`，见 `docs/fix-npe-and-itemhelper.md` |")
    A("")
    A("> ⚠ 「成员还在、只是**签名/语义变了**」这一类（→ NPE / CCE）**不在本工具的能力边界内**。"
      "那类只能靠 A/B 实跑（`tools/launch26/launch.py`）。")
    A("")
    A("### 7.6 自检：能不能抓到**已知的真地雷**")
    A("")
    A("拿修复**前**的 create jar（`create-fly-….jar.bak-itemhelper`）原封不动复制成 "
      "`work/run26/_lmcheck/create-OLD.jar` 再跑同一扫描器：")
    A("")
    A("```")
    A("python tools/scan_landmines.py --mods work/run26/_lmcheck \\")
    A("    --universe-extra work/run26/mods-stable \\")
    A("    --out work/run26/_lmcheck/gt.md")
    A("```")
    A("")
    A("| | 结果 |")
    A("|---|---|")
    A("| 修复前的 jar | **1 条 1 站点**：`ItemContainerContents.allItemsCopyStream()Ljava/util/stream/Stream;`"
      " @ `ItemHelper.fillItemStackHandler:233` ⇒ 判 `实证` |")
    A("| 当前交付 jar | **0 条**（已改用 `itemCopies()` ⇒ 扫描器看不到它了） |")
    A("")
    A("⇒ 这就是「已知真地雷能被同名工具复现」的对照。同一轮里 `Orientation.equals(null)` 那种"
      "「成员还在、语义变了」的 NPE **不会**出现在本清单里 —— 那不在本工具的能力边界内。")
    A("")
    A("### 7.7 本工具明确**不**做的事")
    A("")
    A("- 不检查**可见性**（`private` 方法被外部调用是 `IllegalAccessError`，另一类问题）。")
    A("- 不检查**方法签名语义兼容**（参数变少/变多但描述符恰好匹配的情况不存在；"
      "描述符变了会被本工具抓到，其中「旧参数被当成新参数用」导致的 NPE 抓不到）。")
    A("- 不检查 **mixin 的 `@Shadow` 目标**（那是 `tools/audit_mixins26.py` 的活）。")
    A("- 不检查 **资源/数据包/模型 json**。")
    A("")
    return "\n".join(L)


if __name__ == "__main__":
    sys.exit(main())
