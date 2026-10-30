#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_staging2.py —— 用**任意基线目录**（默认 `mods-stable`）硬链接镜像出 staging，再叠加候选 jar。

`make_staging.py` 把基线写死成 `mods-full`；本文件是它的基类可配版：
交付物是 `mods-stable`，实验必须以 **mods-stable** 为基线，否则「测过的」和「交付的」不是同一个集合。

用法：
    python tools/make_staging2.py <目标目录> [--base <基线目录>] <候选.jar> [...]

⚠ 必看输出 `镜像 N + 候选 M`：M 必须是你要测的数量，否则就是假阳性。
"""
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = ROOT / "work" / "run26" / "mods-stable"


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    argv = sys.argv[1:]
    base = DEFAULT_BASE
    cands = []
    if not argv:
        print(__doc__)
        return 2
    dst = Path(argv[0])
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--base":
            base = Path(argv[i + 1])
            i += 2
        else:
            cands.append(Path(a))
            i += 1
    if not base.is_dir():
        raise SystemExit("没有基线目录: %s" % base)
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    n = 0
    for f in sorted(base.glob("*.jar")):
        try:
            os.link(f, dst / f.name)
        except Exception:
            shutil.copy2(f, dst / f.name)
        n += 1
    m = 0
    for c in cands:
        if not c.is_file():
            print("  !! 缺文件: %s" % c, file=sys.stderr)
            continue
        shutil.copy2(c, dst / c.name)
        m += 1
    print("staging(%s): 镜像 %d + 候选 %d = %d jar" % (dst, n, m, n + m))
    if cands and m != len(cands):
        print("  ⚠ 候选数不符，本次测试结果不可信", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
