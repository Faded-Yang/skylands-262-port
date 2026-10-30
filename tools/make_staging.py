#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_staging.py —— 把已验证的 `mods-full` **硬链接**镜像到 `staging`，再叠加候选 jar。

## 为什么不用 .ps1

第一版写成 `make_staging.ps1`（含中文注释），被 PowerShell 5.1 按 ANSI 读 ⇒ **整个脚本
解析失败**，而 `launch.py` 看到 `--mods staging` 是个空目录/不存在，于是**只加载 0 个 mod
也报 `TITLE_SCREEN_OK`** —— 一次彻底的假阳性。故改成 Python（永远 UTF-8，不受代码页影响）。

## 用法

    python tools/make_staging.py                            # 只镜像
    python tools/make_staging.py <候选.jar> [候选2.jar ...]  # 镜像 + 候选

输出会打印「镜像 N + 候选 M」，**M 必须是你要测的数量**；若是 0 而你以为加了东西，
那就是假阳性 —— 这一点务必核对。
"""
import os
import shutil
import sys
from pathlib import Path

FULL = Path("work/run26/mods-full")
STAG = Path("work/run26/staging")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    extra = [Path(a) for a in sys.argv[1:] if not a.startswith("--")]
    if not FULL.is_dir():
        raise SystemExit("没有 %s" % FULL)
    if STAG.exists():
        shutil.rmtree(STAG)
    STAG.mkdir(parents=True)

    n = 0
    for f in sorted(FULL.glob("*.jar")):
        dst = STAG / f.name
        try:
            os.link(f, dst)                       # 硬链接：不占空间、不影响原文件
        except Exception:
            shutil.copy2(f, dst)
        n += 1

    m = 0
    for e in extra:
        if not e.is_file():
            print("  !! 缺文件: %s" % e, file=sys.stderr)
            continue
        shutil.copy2(e, STAG / e.name)
        m += 1
    print("staging: 镜像 %d + 候选 %d = %d jar" % (n, m, n + m))
    if extra and m != len(extra):
        print("  ⚠ 候选数不符，本次测试结果不可信", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
