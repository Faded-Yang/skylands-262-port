#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_super_is_interface.py —— 查「Create 类的父类在 26.3 里变成了 interface」

## 为什么必须单独查

26.3 把若干**原 class 改成了 interface**（已知：`Explosion` → interface、`Feature` → interface）。
Create 的 `class X extends Feature` 在**类定义期**直接
`IncompatibleClassChangeError: class X has interface ... as super class`。
这类错误 `javac` 不会报（Create 是按 26.2 编的），审计器的 A/B/C/D 也看不到
（`Feature` 这个名字在 26.3 里**存在**，只是在别的"种类"里）。

做法：沿 Create 继承链上溯到第一个 MC 祖先，看它在 26.3 的 javap 缓存里 `kind` 是不是
`interface` / `@interface`。

用法：
    python tools/audit_super_is_interface.py
输出：notes/create-super-is-interface.txt
"""
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAR = ROOT / "work" / "run26" / "mods-aero" / "create-fly-26.2-6.0.9-2-26.3-patched.jar"
MC = Path(r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar")
CACHE = ROOT / "tools" / ".cache" / "createapiaudit" / "javap-cache.json"
OUT = ROOT / "notes" / "create-super-is-interface.txt"

spec = importlib.util.spec_from_file_location("ac", str(ROOT / "tools" / "audit_create_api.py"))
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)


def main():
    z = zipfile.ZipFile(MC)
    mc_names = {n[:-6] for n in z.namelist() if n.endswith(".class")}
    z.close()
    cache = json.loads(CACHE.read_text(encoding="utf-8"))["classes"]

    z = zipfile.ZipFile(JAR)
    info = {}
    for n in z.namelist():
        if not n.endswith(".class") or n.startswith("META-INF/"):
            continue
        try:
            d = ac.parse_class(z.read(n))
            info[d["name"]] = d
        except Exception:
            pass
    z.close()

    rows = []
    for cn, d in info.items():
        cur, seen, anc, chain = cn, {cn}, None, []
        while True:
            sup = (info.get(cur, {}).get("supers") or [None])[0]
            if not sup:
                break
            if sup in info:
                if sup in seen:
                    break
                seen.add(sup)
                chain.append(sup)
                cur = sup
                continue
            if sup in mc_names:
                anc = sup
            break
        if not anc:
            continue
        ci = cache.get(anc)
        if not ci:
            continue
        if ci.get("kind") in ("interface", "@interface"):
            rows.append((cn, anc, ci.get("kind"), chain))

    rows.sort()
    lines = ["# Create 类的父类在 26.3 里变成了 interface（类定义期硬错）", "",
             "jar: %s" % JAR, "共 %d 条" % len(rows), "",
             "| # | Create 类 | 26.3 祖先（现在是 interface） | Create 中间层 |",
             "|---|---|---|---|"]
    for i, (cn, anc, kind, chain) in enumerate(rows, 1):
        lines.append("| %d | %s | %s | %s |"
                     % (i, cn, anc, " > ".join(x.split("/")[-1] for x in chain) or "-"))
    lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    for cn, anc, kind, chain in rows:
        print("%-74s extends %s" % (cn, anc))
    print("\n共 %d 条 → %s" % (len(rows), OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
