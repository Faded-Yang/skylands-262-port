#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mk_intermediary_to_named.py —— 把 Fabric 的 `intermediary` 映射补上第三列 **Mojang 官方名**。

## 为什么需要

MC **26.3 是未混淆的**（`26.3.jar` 里全是 `net/minecraft/core/BlockPos` 这种真名，
**没有** `class_2338`），且 Fabric Loader 在 26.3 上打印 `Mappings not present!`
= **运行时不做任何重映射**（生产环境本来也不重映射 mod，只重映射游戏本体）。

而 Modrinth 上的 1.21.x Fabric jar 全部是 **intermediary 映射**（`class_2338` /
`method_10264`）。它们放上 26.3 后引用的是 `net/minecraft/class_2338`，26.3 里根本没有，
首个类加载就 `NoClassDefFoundError`。

⇒ **1.21.x → 26.3 的第一步不是改 API，而是「intermediary → 官方名」重映射。**

## 做法（严格三列连接，不靠猜）

1. `intermediary-<ver>-v2.jar` 里的 `mappings/mappings.tiny` 是 **official ↔ intermediary**
   （official = 混淆名 `dcc`）。**带描述符**。
2. Mojang `client.txt` 给出 **official ↔ 官方名**（`dcc` → `net.minecraft.core.BlockPos`）。
   方法/字段行只有类型文本，没有 JVM 描述符。
3. 本脚本把 client.txt 的成员签名**算成描述符**，再用 offical 类名反查，得到
   **official 空间的描述符**，与 intermediary 表的描述符**精确匹配**
   ⇒ 产出 `official / intermediary / named` 三列 tiny v2。

> 不用「按名字硬配」：同名重载会串味。这里用描述符做 key。

## 用法

    python tools/mk_intermediary_to_named.py \
        --intermediary work/run26/port/_maps/intermediary-1.21.1-v2.jar \
        --mojang      work/run26/port/_maps/client-1.21.1.txt \
        --out         work/run26/port/_maps/intermediary-1.21.1-named.tiny

产出后用 tiny-remapper：

    java -jar tools/.../tiny-remapper.jar in.jar out.jar <tiny> intermediary named
"""
import argparse
import io
import json
import re
import sys
import zipfile
from pathlib import Path

PRIM = {"void": "V", "boolean": "Z", "byte": "B", "char": "C", "short": "S",
        "int": "I", "float": "F", "double": "D", "long": "J"}


def strip_generics(s):
    """去掉 <...>（可能嵌套），保留数组后缀。"""
    out, depth = [], 0
    for ch in s:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def split_args(s):
    """按顶层逗号切参数表。"""
    out, buf, depth = [], [], 0
    for ch in s:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if "".join(buf).strip():
        out.append("".join(buf).strip())
    return out


def type_desc(t, cls_map):
    """Mojang 类型文本 -> official 空间描述符片段。"""
    t = strip_generics(t).strip()
    dims = 0
    while t.endswith("[]"):
        t = t[:-2].strip()
        dims += 1
    if t in PRIM:
        d = PRIM[t]
    else:
        obf = cls_map.get(t)
        if obf is None:
            # ⚠ 关键：**只有 net.minecraft / com.mojang 的类被混淆**。
            # JDK / LWJGL / joml 等类名在 official 空间里就是原名，
            # 这里不能返回 None（否则整条方法签名报废 —— 曾导致方法命中率只有 3.5%）。
            obf = t.replace(".", "/")
        d = "L" + obf + ";"
    return "[" * dims + d


def parse_mojang(path, log=print):
    """返回 dict：
       obf2named: {obfClass: namedClass}
       named2obf: {namedClass: obfClass}
       members  : {(obfClass, obfName, obfDesc): namedName}
    """
    obf2named, named2obf = {}, {}
    raw = []          # (obfClass, kind, obfName, mojangName, mojangDescText)
    cur = None
    cls_re = re.compile(r"^(\S+) -> (\S+):\s*$")
    mem_re = re.compile(r"^\s{4}(\S.*?) -> (\S+)\s*$")
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for ln in f:
            ln = ln.rstrip("\n")
            m = cls_re.match(ln)
            if m:
                cur = m.group(2)
                obf2named[cur] = m.group(1)
                named2obf[m.group(1)] = cur
                continue
            m = mem_re.match(ln)
            if m and cur:
                sig, obf = m.group(1), m.group(2)
                # ⚠ 关键：Mojang 的 client.txt 给**方法**加了行号前缀 `17:17:`，
                # 不剥掉会被当成返回类型的一部分（曾导致方法命中率只有 4.6%：
                # 算出 `(F)L17:17:org/joml/Quaternionf;` 这种畸形描述符）。
                sig = re.sub(r"^\d+:\d+:", "", sig)
                # 方法形如 "int getX(int, ...)"，字段形如 "int x"
                mm = re.match(r"^(.*?)\s+([\w$<>]+)\s*\((.*)\)$", sig)
                if mm:
                    ret, name, args = mm.group(1).strip(), mm.group(2), mm.group(3)
                    raw.append((cur, "M", obf, name, ret, args))
                else:
                    parts = sig.rsplit(" ", 1)
                    if len(parts) == 2:
                        raw.append((cur, "F", obf, parts[1].strip(), parts[0].strip(), None))
                continue
    log("  mojang: %d 类, 原始成员行 %d" % (len(obf2named), len(raw)))

    members = {}
    bad = 0
    for obf_cls, kind, obf_name, mj_name, a, args in raw:
        if kind == "M":
            ret = type_desc(a, named2obf)
            if ret is None:
                bad += 1
                continue
            ds = []
            ok = True
            for x in split_args(args):
                td = type_desc(x, named2obf)
                if td is None:
                    ok = False
                    break
                ds.append(td)
            if not ok:
                bad += 1
                continue
            desc = "(" + "".join(ds) + ")" + ret
            members[(obf_cls, obf_name, desc)] = mj_name
        else:
            td = type_desc(a, named2obf)
            if td is None:
                bad += 1
                continue
            members[(obf_cls, obf_name, td)] = mj_name
    log("  成员描述符建成 %d 条（算不出 %d）" % (len(members), bad))
    return obf2named, named2obf, members


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--intermediary", required=True, help="intermediary-<ver>-v2.jar")
    ap.add_argument("--mojang", required=True, help="client.txt（Mojang 官方映射）")
    ap.add_argument("--out", required=True, help="输出 tiny v2 路径（official/intermediary/named）")
    ap.add_argument("--out-ns1", default=None,
                    help="另写一份「描述符在 intermediary 空间」的两列 tiny（intermediary/named）。"
                         "⚠ tiny-remapper 用输入 jar 的**原始描述符**去查成员；我们的描述符在 official 空间，"
                         "含 MC 类型时对不上 → 字段/方法名改不了。用这份就能对上。")
    args = ap.parse_args()

    z = zipfile.ZipFile(args.intermediary)
    inner = [n for n in z.namelist() if n.endswith("mappings.tiny")]
    if not inner:
        print("intermediary jar 里没有 mappings.tiny", file=sys.stderr)
        return 2
    text = z.read(inner[0]).decode("utf-8", "replace")
    z.close()
    lines = text.splitlines()
    print("intermediary: %s（%d 行），头: %s" % (inner[0], len(lines), lines[0]))

    obf2named, named2obf, members = parse_mojang(args.mojang)

    out = ["tiny\t2\t0\tofficial\tintermediary\tnamed"]
    stat = dict(cls=0, m=0, f=0, m_hit=0, f_hit=0)
    miss_examples = []
    cur_obf = None
    for ln in lines[1:]:
        if ln.startswith("c\t"):
            p = ln.split("\t")
            cur_obf = p[1]
            named = obf2named.get(cur_obf)
            if named:
                stat["cls"] += 1
                out.append("c\t%s\t%s\t%s" % (cur_obf, p[2], named.replace(".", "/")))
            else:
                out.append("c\t%s\t%s\t%s" % (cur_obf, p[2], p[2]))
                cur_obf = None      # 别把成员挂到未映射的类上
        elif ln.startswith("\t"):
            p = ln[1:].split("\t")
            # p = ['m', desc, officialName, interName] ，tiny v2 要求**三个命名空间都给出名字**
            if p[0] in ("m", "f") and len(p) >= 4:
                kind, desc, obfname, internm = p[0], p[1], p[2], p[3]
                hit = None
                if cur_obf:
                    hit = members.get((cur_obf, obfname, desc))
                if hit:
                    stat[kind.lower() + "_hit"] += 1
                elif len(miss_examples) < 8 and cur_obf:
                    miss_examples.append("%s %s %s" % (cur_obf, obfname, desc))
                stat[kind.lower()] += 1
                out.append("\t%s\t%s\t%s\t%s\t%s"
                           % (kind, desc, obfname, internm, hit or internm))
            else:
                # 嵌套类等其它行：把最后一个名字补成三列，否则 tiny-remapper 报
                # 「missing name columns」
                if len(p) >= 3:
                    out.append("\t" + "\t".join(p + [p[-1]]))
                else:
                    out.append(ln)
        else:
            out.append(ln)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("写出 %s" % args.out)
    print("  类 %d 命中 / 方法 %d 条（命中 %d）/ 字段 %d 条（命中 %d）"
          % (stat["cls"], stat["m"], stat["m_hit"], stat["f"], stat["f_hit"]))
    if miss_examples:
        print("  未命中示例:", "; ".join(miss_examples))

    # ---- 再写一份「描述符在 intermediary 空间」的两列版（给 tiny-remapper 用）
    if args.out_ns1:
        off2int = {}
        for ln in lines[1:]:
            if ln.startswith("c\t"):
                q = ln.split("\t")
                off2int[q[1]] = q[2]
        d2 = ["tiny\t2\t0\tintermediary\tnamed"]
        for ln in out[1:]:
            if ln.startswith("c\t"):
                q = ln.split("\t")
                d2.append("c\t%s\t%s" % (q[2], q[3]))
            elif ln.startswith("\t"):
                q = ln[1:].split("\t")
                if q[0] in ("m", "f") and len(q) >= 5:
                    desc_ns1 = re.sub(r"L([^;]+);",
                                      lambda m: "L" + off2int.get(m.group(1), m.group(1)) + ";",
                                      q[1])
                    d2.append("\t%s\t%s\t%s\t%s" % (q[0], desc_ns1, q[3], q[4]))
                elif len(q) >= 3:
                    d2.append("\t" + "\t".join(q[:2] + [q[-1]]))
        Path(args.out_ns1).write_text("\n".join(d2) + "\n", encoding="utf-8")
        print("写出 %s（描述符已换到 intermediary 空间）" % args.out_ns1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
