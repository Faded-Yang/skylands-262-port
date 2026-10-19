#!/usr/bin/env python3
"""pack_jar.py —— 把 classes 目录 + resources 目录打成 mod jar，并**写入目录条目**。

26.3/Fabric 下手写 zip（只写文件、不写目录条目）会导致部分资源（如 assets/<ns>/lang/*.json）
加载不到 ⇒ 物品/方块显示原始 key。所有自研/重写 jar 都用这个脚本打包。

用法：python tools/pack_jar.py <classes-dir> <resources-dir> <out.jar>
"""
import sys
import zipfile
from pathlib import Path


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 2
    classes = Path(argv[1]).resolve()
    resources = Path(argv[2]).resolve()
    out = Path(argv[3]).resolve()
    entries = []
    for root, prefix in ((classes, ""), (resources, "")):
        for p in sorted(root.rglob("*")):
            if p.is_file():
                entries.append((p.relative_to(root).as_posix(), p.read_bytes()))
    # every parent directory gets an explicit entry (sorted so parents come first)
    dirs = set()
    for name, _ in entries:
        parts = name.split("/")[:-1]
        for i in range(1, len(parts) + 1):
            dirs.add("/".join(parts[:i]) + "/")
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for d in sorted(dirs):
            info = zipfile.ZipInfo(d, date_time=(2026, 10, 19, 0, 0, 0))
            info.external_attr = 0x10
            z.writestr(info, b"")
        for name, data in entries:
            z.writestr(name, data)
    with zipfile.ZipFile(out) as z:
        bad = z.testzip()
        names = z.namelist()
    print(f"packed {out.name}: {out.stat().st_size} bytes, {len(names)} entries, "
          f"dirs={sum(1 for n in names if n.endswith('/'))}, testzip={bad}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
