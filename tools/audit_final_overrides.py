#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_final_overrides.py —— 全量查 Create-Fly 里「覆盖了 26.3 final 方法」的类（E 类）。

## 为什么需要它（R354→R355 的教训）

`audit_create_api.py` 的 E 检测只看**直接父类**（`supers[0]`）且要求直接父类是 MC 类。
于是 `Indicator extends AbstractSimiWidget extends AbstractWidget` 这种
「中间隔了一层 Create 类」的 final 覆盖**完全漏掉** —— 而它同样是**类定义期**
`IncompatibleClassChangeError`，会在启动时炸。

本脚本：对每个 Create 类，**沿 Create 继承链上溯到第一个 MC 祖先**，再用 26.3 的
javap 缓存沿 MC 继承链解析 `(name, desc)`；命中 `final` ⇒ 报 E。

## 用法

    python tools/audit_final_overrides.py            # 打印 + 写 notes/create-final-overrides.txt
"""
import importlib.util
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAR = ROOT / "work" / "run26" / "mods-aero" / "create-fly-26.2-6.0.9-2-26.3-patched.jar"
MC_HOME = Path(r"C:\Users\95959\AppData\Roaming\.minecraft")
MC = MC_HOME / "versions" / "26.3" / "26.3.jar"
CACHE = ROOT / "tools" / ".cache" / "createapiaudit" / "javap-cache.json"
OUT = ROOT / "notes" / "create-final-overrides.txt"

spec = importlib.util.spec_from_file_location("ac", str(ROOT / "tools" / "audit_create_api.py"))
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)


def main():
    z = zipfile.ZipFile(MC)
    mc_names = {n[:-6] for n in z.namelist() if n.endswith(".class")}
    z.close()
    cache = json.loads(CACHE.read_text(encoding="utf-8"))["classes"]

    z = zipfile.ZipFile(JAR)
    classes = [n for n in z.namelist() if n.endswith(".class") and not n.startswith("META-INF/")]
    info = {}
    for n in classes:
        try:
            info[ac.parse_class(z.read(n))["name"]] = ac.parse_class(z.read(n))
        except Exception:
            pass
    z.close()
    print("Create 类 %d（解析 %d） / MC 类 %d / javap 缓存 %d"
          % (len(classes), len(info), len(mc_names), len(cache)))

    def is_create(cn):
        return cn in info

    def chain_mc(cn):
        """26.3 里沿继承链取所有声明类（只看已缓存/已知的）。"""
        out, seen, stack = [], set(), [cn, "java/lang/Object"]
        while stack:
            c = stack.pop(0)
            if c in seen:
                continue
            seen.add(c)
            ci = cache.get(c)
            if not ci or ci.get("missing"):
                continue
            out.append(c)
            for p in (ci.get("supers") or []) + (ci.get("interfaces") or []):
                pj = p.replace(".", "/")
                if pj not in seen:
                    stack.append(pj)
        return out

    # 每条 MC 继承链只算一次
    chain_cache = {}

    def finals_in(ancestor, name, desc):
        """返回声明 (name,desc) 为 final 的那个类，否则 None。"""
        for c in chain_cache.setdefault(ancestor, chain_mc(ancestor)):
            ci = cache.get(c) or {}
            mt = ci.get("methods") or {}
            if desc in (mt.get(name) or []):
                if (name + "|" + desc) in set(ci.get("final_methods") or []):
                    return c
                return None
        return None

    rows = []
    for cn, d in info.items():
        # 沿 Create 链上溯到第一个 MC 祖先
        cur, seen, anc, mid = cn, {cn}, None, []
        while True:
            sup = (info.get(cur, {}).get("supers") or [None])[0]
            if not sup:
                break
            if sup in info:
                mid.append(sup)
                if sup in seen:
                    break
                seen.add(sup)
                cur = sup
                continue
            if sup in mc_names:
                anc = sup
            break
        if not anc:
            continue
        for mname, descs in d["methods"].items():
            if mname in ("<init>", "<clinit>"):
                continue
            for ds in descs:
                who = finals_in(anc, mname, ds)
                if who:
                    rows.append(dict(create_class=cn, method=mname, desc=ds,
                                     final_decl=who, mc_ancestor=anc,
                                     create_chain=mid))

    rows.sort(key=lambda r: (r["create_class"], r["method"]))
    lines = ["# Create-Fly 里覆盖 26.3 final 方法的类（全量，含 Create 中间层）", "",
             "jar: %s" % JAR, "共 %d 条" % len(rows), ""]
    lines.append("| # | Create 类 | 方法 | 描述符 | 26.3 final 声明处 | Create 中间层 |")
    lines.append("|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        lines.append("| %d | %s | %s | %s | %s | %s |"
                     % (i, r["create_class"], r["method"], r["desc"], r["final_decl"],
                        " > ".join(x.split("/")[-1] for x in r["create_chain"]) or "-"))
    lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    for r in rows:
        print("%-72s %-24s %-46s final@%s"
              % (r["create_class"], r["method"], r["desc"], r["final_decl"].split("/")[-1]))
    print("\n共 %d 条 → %s" % (len(rows), OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
