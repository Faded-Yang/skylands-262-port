#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_fabric_api_dep.py —— 把 `fabric.mod.json` 里**旧的依赖 id `fabric`** 改成 `fabric-api`。

## 为什么

1.20.x 时代的 mod 常写 `"depends": {"fabric": "*"}`（那时 Fabric API 的 mod id 就叫 `fabric`）。
现在的 Fabric API（0.163.0+26.3）提供的 id 是 `fabric-api`，于是 Loader 直接拒载：

    Incompatible mods found!
     - 安装 fabric，任意版本。
    模组 'Create: Sky Village' (create_sky_village) 0.0.29I 需要 fabric 的 任意版本，但没有安装它！

修法：`depends/breaks/recommends/suggests` 里键名 `fabric` → `fabric-api`（值不变）。

## 用法

    python tools/fix_fabric_api_dep.py <jar>... [--dry-run]
"""
import json
import shutil
import sys
import zipfile

SECTIONS = ("depends", "breaks", "recommends", "suggests", "conflicts", "provides")


def patch(jar, dry):
    try:
        z = zipfile.ZipFile(jar)
    except Exception as e:
        return ("skip", str(e))
    names = z.namelist()
    if "fabric.mod.json" not in names:
        z.close()
        return ("nofmj", "")
    data = {n: z.read(n) for n in names}
    z.close()
    try:
        mod = json.loads(data["fabric.mod.json"].decode("utf-8", "replace"))
    except Exception as e:
        return ("badjson", str(e))
    hits = []
    for sec in SECTIONS:
        d = mod.get(sec)
        if isinstance(d, dict) and "fabric" in d:
            d["fabric-api"] = d.pop("fabric")
            hits.append(sec)
    if not hits:
        return ("nochange", "")
    data["fabric.mod.json"] = (json.dumps(mod, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if dry:
        return ("dry", ",".join(hits))
    shutil.copy2(jar, jar + ".bak-fabricdep")
    with zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED) as w:
        for n, b in data.items():
            w.writestr(n, b)
    return ("ok", ",".join(hits))


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    dry = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    for j in args:
        st, info = patch(j, dry)
        print("  %-9s %s %s" % (st, j, info))
    return 0


if __name__ == "__main__":
    sys.exit(main())
