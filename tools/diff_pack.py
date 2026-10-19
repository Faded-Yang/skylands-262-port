#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diff_pack.py —— 精确算出「原包 112 个 jar」里哪些的 mod 还没进 `mods-stable`。

## 方法（精确，不靠文件名猜）

1. **从原包每个 jar 里读出它自己的 mod id**：
   - Fabric: `fabric.mod.json` 的 `id`
   - NeoForge: `META-INF/neoforge.mods.toml` / `META-INF/mods.toml` 的 `modId="..."`
2. **从 mods-stable 每个 jar 里读出已装的 mod id**（同样两种来源）
3. **取差集**

这样不会再因为「文件名 slug 猜错」而误报（上一版把 `BetterF3` 切成 `BetterF` 导致漏判）。

## 用法

    python tools/diff_pack.py [--orig <原包 mods 目录>] [--json out.json]
"""
import json
import os
import re
import sys
import zipfile

BASE = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
DEFAULT_ORIG = os.path.expandvars(
    r"%APPDATA%\.minecraft\versions\Create 航空学 × 浮空群岛\mods")
DEFAULT_NEW = os.path.join(BASE, "work", "run26", "mods-stable")

COMMON_NS = {"minecraft", "c", "fabric", "common", "forge", "neoforge", "tags"}
TOML_ID = re.compile(r'modId\s*=\s*"([^"]+)"')
TOML_IDS_ANY = re.compile(r'\bmodId\s*=\s*"([^"]+)"')


def ids_of_jar(path):
    """返回 (主 id, 全部 id 集合, jar 里的 namespace 集合)"""
    out = set()
    nss = set()
    try:
        z = zipfile.ZipFile(path)
    except Exception:
        return None, out, nss
    names = z.namelist()
    if "fabric.mod.json" in names:
        try:
            m = json.loads(z.read("fabric.mod.json").decode("utf-8", "replace"))
            if m.get("id"):
                out.add(m["id"])
        except Exception:
            pass
    for meta in ("META-INF/neoforge.mods.toml", "META-INF/mods.toml"):
        if meta in names:
            try:
                txt = z.read(meta).decode("utf-8", "replace")
                # 只取 [[dependencies 之前的 modId（之后的都是依赖声明，含 modId="minecraft"）
                head = txt.split("[[dependencies", 1)[0]
                for mid in TOML_IDS_ANY.findall(head):
                    out.add(mid)
            except Exception:
                pass
    for n in names:
        parts = n.split("/")
        if len(parts) > 2 and parts[0] in ("assets", "data"):
            nss.add(parts[1])
    z.close()
    main = None
    return main, out, nss


def scan(d):
    rows = []
    for f in sorted(os.listdir(d)):
        if not f.endswith(".jar"):
            continue
        _, ids, nss = ids_of_jar(os.path.join(d, f))
        rows.append((f, ids, nss))
    return rows


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    orig = DEFAULT_ORIG
    new = DEFAULT_NEW
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--orig":
            orig = argv[i + 1]
        if a == "--new":
            new = argv[i + 1]
    if not os.path.isdir(orig):
        print("★ 原包目录不存在:", orig)
        return 1

    o_rows = scan(orig)
    n_rows = scan(new)
    n_ids = set()
    n_nss = set()
    for _, ids, nss in n_rows:
        n_ids |= {x.lower().replace("-", "").replace("_", "") for x in ids}
        n_nss |= {x.lower() for x in nss}

    print("原包 jar: %d   已装 jar: %d" % (len(o_rows), len(n_rows)))
    print("已装 mod id: %d   已装 namespace: %d" % (len(n_ids), len(n_nss)))

    covered, missing, noid = [], [], []
    for f, ids, nss in o_rows:
        if not ids:
            noid.append((f, nss))
            continue
        idsl = {x.lower().replace("-", "").replace("_", "") for x in ids}
        nssl = {x.lower() for x in nss}
        if idsl & n_ids:
            covered.append((f, sorted(idsl & n_ids)))
        else:
            missing.append((f, sorted(idsl), sorted(nssl)))

    print("\n=== 已覆盖 %d / %d ===" % (len(covered), len([r for r in o_rows if r[1]])))
    print("  (诊断) 前 5 个匹配依据:", covered[:5])
    print("\n=== ★ 未覆盖 %d 个 ===" % len(missing))
    for f, ids, nss in missing:
        print("  %-56s ids=%s" % (f[:56], ",".join(ids)[:60]))
    if noid:
        print("\n=== 读不出 mod id 的 %d 个（可能纯资源/库）===" % len(noid))
        for f, nss in noid:
            print("  %-56s ns=%s" % (f[:56], ",".join(sorted(nss))[:50]))

    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        json.dump({
            "covered": [{"jar": f, "by": b} for f, b in covered],
            "missing": [{"jar": f, "ids": ids, "namespaces": nss} for f, ids, nss in missing],
            "unknown": [{"jar": f, "namespaces": nss} for f, nss in noid],
        }, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("\n写出:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
