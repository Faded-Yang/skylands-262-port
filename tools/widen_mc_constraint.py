#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
widen_mc_constraint.py —— 把 mod jar 里 `fabric.mod.json` 的 Minecraft 版本约束放宽到接受 26.3。

## 为什么

原包（以及几乎所有 mod）会写死 `"minecraft": "~26.2"` 之类。26.3 因此会被 Fabric Loader 拒绝，
即使 mod 的 API 其实还能跑。放宽约束后才能进入"能不能真的跑"的验证阶段。
这是给 Create-Fly 验证过的范式（`create-fly-26.2-...-patched.jar` 就是这么来的）。

## 用法

    python tools/widen_mc_constraint.py <dir-or-jar>... [--target ">=26.1- <26.4-"] [--dry-run]

会就地重写 jar，原文件备份为 `<jar>.bak-ver`。
"""
import json
import os
import shutil
import sys
import zipfile

DEFAULT_TARGET = ">=26.1- <26.4-"


def widen_jar(path, target, dry):
    try:
        z = zipfile.ZipFile(path)
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

    deps = mod.get("depends")
    if not isinstance(deps, dict) or "minecraft" not in deps:
        return ("nomc", "")
    old = deps["minecraft"]
    if isinstance(old, list):
        old_s = ",".join(str(x) for x in old)
    else:
        old_s = str(old)
    if old_s == target:
        return ("already", old_s)

    deps["minecraft"] = target
    data["fabric.mod.json"] = (json.dumps(mod, indent=2, ensure_ascii=False) + "\n").encode("utf-8")

    if dry:
        return ("dry", "%s -> %s" % (old_s, target))

    shutil.copy2(path, path + ".bak-ver")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as w:
        for n, b in data.items():
            w.writestr(n, b)
    return ("ok", "%s -> %s" % (old_s, target))


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    target = DEFAULT_TARGET
    dry = "--dry-run" in sys.argv
    if "--target" in sys.argv:
        target = sys.argv[sys.argv.index("--target") + 1]
    args = []
    i = 1
    while i < len(sys.argv):
        a = sys.argv[i]
        if a in ("--target",):
            i += 2
        elif a.startswith("--"):
            i += 1
        else:
            args.append(a)
            i += 1
    if not args:
        print(__doc__)
        return 2

    jars = []
    for p in args:
        if os.path.isdir(p):
            jars += [os.path.join(p, f) for f in sorted(os.listdir(p)) if f.endswith(".jar")]
        else:
            jars.append(p)

    from collections import Counter
    cnt = Counter()
    for j in jars:
        st, info = widen_jar(j, target, dry)
        cnt[st] += 1
        print("  %-8s %-56s %s" % (st, os.path.basename(j)[:56], info), flush=True)
    print("\n汇总:", dict(cnt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
