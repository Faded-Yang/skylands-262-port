#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lenient_mixins.py —— 把 jar 内所有 `*.mixins.json` 的 `injectors.defaultRequire` 设为 0。

## 为什么

26.3 改了若干方法签名/位置，老版本 mod 的 `@Inject` 目标常常不复存在。
Mixin 默认 `require=1`，注入失败会**硬崩**（`InvalidInjectionException` / `MixinApplyError`）。
设成 0 后失败只告警，mod 其余功能照常 —— 这是把「差一两个版本的 mod」跑起来的通用手法，
我们给 Create-Fly 就是这么做的。

## 用法

    python tools/lenient_mixins.py <jar>... [--dry-run]
"""
import json
import os
import shutil
import sys
import zipfile


def patch(jar, dry):
    try:
        z = zipfile.ZipFile(jar)
    except Exception as e:
        return ("skip", str(e))
    names = z.namelist()
    cfgs = [n for n in names if n.endswith(".mixins.json")]
    if not cfgs:
        z.close()
        return ("nocfg", "")
    data = {n: z.read(n) for n in names}
    z.close()
    changed = []
    for c in cfgs:
        try:
            d = json.loads(data[c].decode("utf-8", "replace"))
        except Exception:
            continue
        inj = d.get("injectors")
        if isinstance(inj, dict):
            if inj.get("defaultRequire") != 0:
                inj["defaultRequire"] = 0
                changed.append(c)
        else:
            d["injectors"] = {"defaultRequire": 0}
            changed.append(c)
        data[c] = (json.dumps(d, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if not changed:
        return ("already", "")
    if dry:
        return ("dry", ", ".join(changed))
    shutil.copy2(jar, jar + ".bak-lenient")
    with zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED) as w:
        for n, b in data.items():
            w.writestr(n, b)
    return ("ok", ", ".join(changed))


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
    jars = []
    for p in args:
        if os.path.isdir(p):
            jars += [os.path.join(p, f) for f in sorted(os.listdir(p)) if f.endswith(".jar")]
        else:
            jars.append(p)
    for j in jars:
        st, info = patch(j, dry)
        if st not in ("nocfg", "already"):
            print("  %-8s %-56s %s" % (st, os.path.basename(j)[:56], info), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
