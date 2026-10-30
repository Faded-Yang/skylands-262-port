#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""est_gap_263.py —— 估「一个已 remap 到 named 的旧 jar」在 26.3 上的 **真实 API 缺口规模**。

只解决一件事：remap_intermediary 只改了**类名**，成员名还是 `method_xxxx` / `field_xxxx`
（因为 mapping 文件里的 desc 是混淆空间的，按 (owner,name,desc) 查必然 miss）。
本脚本 **不按名字** 判，而按 **(owner, 翻译后的 desc)** 判：

  - 引用名是 `method_*` / `field_*`（intermediary）⇒ 只要 26.3 的继承链里有**唯一**一个
    描述符相同的成员，就能自动改名（无需知道语义）。
  - 引用名是普通名字（已经是 named）⇒ 必须 (name, desc) 都在，否则是真缺口。

输出：A/B/C/D 分级 + 可自动解决 / 需人工 的条数。

    python tools/est_gap_263.py <named.jar> [--mc 26.3.jar] [--prefix net/minecraft] [--txt out.txt]
"""
import argparse
import collections
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from audit_jar_api import parse_class  # noqa: E402

MC = Path(r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar")
MAPS = ROOT / "work/run26/port/_maps"


def load_classmap(tiny: Path):
    """2 列 tiny: c <intermediary> <named>；并顺手建 (named owner, 旧名) -> 新名 的 name-only 表。"""
    cmap = {}
    nameonly = {}
    cur = None
    for ln in tiny.read_text(encoding="utf-8", errors="replace").splitlines():
        if ln.startswith("c\t") or ln.startswith("c "):
            p = ln.split("\t")
            if len(p) >= 3:
                cmap[p[1]] = p[2]
                cur = p[2]
        elif ln.startswith("\tm\t") or ln.startswith("\tf\t"):
            p = ln.split("\t")
            if cur and len(p) >= 5:
                nameonly[(cur, p[3])] = p[4]
    return cmap, nameonly


class Index:
    def __init__(self, jar: Path):
        z = zipfile.ZipFile(jar)
        self.names = {n[:-6] for n in z.namelist() if n.endswith(".class")}
        self.sup = {}
        self.meth = collections.defaultdict(list)   # name -> [(owner, desc)]
        self.fld = collections.defaultdict(list)
        self.by_owner = collections.defaultdict(lambda: {"M": collections.defaultdict(list),
                                                         "F": collections.defaultdict(list)})
        for n in z.namelist():
            if not n.endswith(".class"):
                continue
            try:
                d = parse_class(z.read(n))
            except Exception:
                continue
            own = d["name"]
            self.sup[own] = d["supers"] + d["interfaces"]
            for nm, descs in d["methods"].items():
                for ds in descs:
                    self.by_owner[own]["M"][nm].append(ds)
            for nm, descs in d["fields"].items():
                for ds in descs:
                    self.by_owner[own]["F"][nm].append(ds)
        z.close()

    def chain(self, c):
        out, seen, stack = [], set(), [c]
        while stack:
            x = stack.pop(0)
            if x in seen:
                continue
            seen.add(x)
            if x not in self.names and not x.startswith("java/"):
                continue
            out.append(x)
            for p in self.sup.get(x, []):
                stack.append(p)
        return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jar")
    ap.add_argument("--mc", default=str(MC))
    ap.add_argument("--prefix", default="net/minecraft")
    ap.add_argument("--txt", default=None)
    ap.add_argument("--map", default=str(MAPS / "i21n-ns1.tiny"))
    ap.add_argument("--renames", default=str(ROOT / "tools/rename_121_to_263.json"))
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ren = {"classes": {}, "members": {}}
    rp = Path(args.renames)
    if rp.is_file():
        ren = json.loads(rp.read_text(encoding="utf-8"))
    rcls = ren.get("classes") or {}
    rmem = ren.get("members") or {}
    cmap, nameonly = load_classmap(Path(args.map))
    rev = {}
    for k, v in cmap.items():
        rev.setdefault(v, k)
    idx = Index(Path(args.mc))
    named = set(cmap.values())

    def cls26(name):
        """旧 named 类名 -> 26.3 类名（存在则原样，否则按简单名唯一匹配）。"""
        if name in rcls:
            return rcls[name]
        if name in idx.names:
            return name
        simple = name.rsplit("/", 1)[-1]
        cands = [n for n in idx.names if n.rsplit("/", 1)[-1] == simple]
        return cands[0] if len(cands) == 1 else None

    def map_desc(s):
        def rep(m):
            n = m.group(1)
            return "L" + (cls26(n) or n) + ";"
        return re.sub(r"L([^;<>]+);", rep, s)

    z = zipfile.ZipFile(args.jar)
    gap = collections.defaultdict(list)
    auto = collections.Counter()
    manual = collections.Counter()
    for n in z.namelist():
        if not n.endswith(".class"):
            continue
        try:
            d = parse_class(z.read(n))
        except Exception:
            continue
        for _k, (kind, owner, nm, ds) in d["member_refs"].items():
            if not owner.startswith(args.prefix):
                continue
            o26 = cls26(owner)
            d26 = map_desc(ds)
            if not (nm.startswith("method_") or nm.startswith("field_")):
                alt = rmem.get("%s|%s|%s" % (owner, nm, ds))
                if alt:
                    nm = alt
            if o26 is None:
                gap["C:class-missing"].append((owner, nm, ds))
                manual["C"] += 1
                continue
            is_inter = nm.startswith("method_") or nm.startswith("field_")
            table = "M" if kind == "M" else "F"
            if is_inter:
                # 先看 name-only 表：枚举常量 / 同型不同名成员靠这个唯一搞定
                named_hit = None
                for c in idx.chain(o26):
                    if (c, nm) in nameonly:
                        named_hit = nameonly[(c, nm)]
                        break
                if named_hit and any(named_hit in idx.by_owner[c][table]
                                     and d26 in idx.by_owner[c][table][named_hit]
                                     for c in idx.chain(o26)):
                    auto["name-only"] += 1
                    continue
                cands = set()
                for c in idx.chain(o26):
                    for namex, descl in idx.by_owner[c][table].items():
                        if d26 in descl:
                            cands.add((c, namex))
                if len(cands) == 1:
                    auto["member-auto"] += 1
                elif not cands:
                    gap["D:none-by-desc"].append((o26, nm, ds, d26))
                    manual["D"] += 1
                else:
                    gap["B:ambiguous-by-desc"].append((o26, nm, ds, sorted(cands)))
                    manual["B"] += 1
            else:
                ok = any(nm in idx.by_owner[c][table] and d26 in idx.by_owner[c][table][nm]
                         for c in idx.chain(o26))
                if ok:
                    auto["named-ok"] += 1
                else:
                    # 同名不同 desc？
                    same = [(c, idx.by_owner[c][table][nm]) for c in idx.chain(o26)
                            if nm in idx.by_owner[c][table]]
                    if same:
                        gap["A:desc-changed"].append((o26, nm, d26, same[0][1]))
                        manual["A"] += 1
                    else:
                        gap["A:name-missing"].append((o26, nm, d26))
                        manual["A"] += 1
    print(f"== {args.jar}")
    print(f"  可自动解析（intermediary 名，desc 唯一命中）: {auto['member-auto']}")
    print(f"  可自动解析（name-only 表命中后 desc 匹配）: {auto['name-only']}")
    print(f"  已经是合法 named 引用: {auto['named-ok']}")
    print(f"  需人工/规则处理: {sum(manual.values())}  " + json.dumps(manual, ensure_ascii=False))
    for k in sorted(gap):
        print(f"\n-- {k}: {len(gap[k])}")
        for row in gap[k][:60]:
            print("   ", row)

    if args.txt:
        Path(args.txt).write_text("\n".join(f"{k}\t{len(v)}" for k, v in gap.items()), encoding="utf-8")


if __name__ == "__main__":
    main()
