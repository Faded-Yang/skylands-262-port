#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_create_shaderlenient.py —— 把 `ShaderManagerLenientMixin` 塞进 Create jar 并注册。

## 为什么

26.3 的 `ShaderManager.apply` 在「required 管线编译失败」时抛
`RuntimeException: Failed to load required shader programs`，直接打断整次资源 reload
（AtlasManager 的共享 PreparationBarrier 失败 ⇒ 一个 atlas 都不建 ⇒ 全黑）。

Create 26.2 的 GLSL 编不出 26.3 的 SPIR-V（#moj_import 未展开 / 缺 layout(location) /
ProjMat 等改成 snippet），15 条 create:/ponder: 管线必然失败。

垫片只把「required 缺失就抛」那一处 `List.isEmpty()` 改成 true（optional 那处不动）。

## 用法

    python tools/patch_create_shaderlenient.py --dry-run
    python tools/patch_create_shaderlenient.py
"""
import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JAR = ROOT / "work" / "run26" / "mods-aero" / "create-fly-26.2-6.0.9-2-26.3-patched.jar"
CLS = ROOT / "work" / "blackfix" / "out" / "com" / "zurrtum" / "create" / "client" / "mixin" / "ShaderManagerLenientMixin.class"
ENTRY = "com/zurrtum/create/client/mixin/ShaderManagerLenientMixin.class"
MIXIN_JSON = "create.client.mixins.json"
MIXIN_NAME = "ShaderManagerLenientMixin"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jar", default=str(DEFAULT_JAR))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    jar = Path(args.jar)
    if not CLS.is_file():
        print("!! 缺 %s（先 javac）" % CLS, file=sys.stderr)
        return 2

    zin = zipfile.ZipFile(jar)
    names = set(zin.namelist())
    cfg = json.loads(zin.read(MIXIN_JSON).decode("utf-8"))
    already = MIXIN_NAME in cfg["client"]
    print("class 已存在: %s / 已注册: %s" % (ENTRY in names, already))
    if already and ENTRY in names:
        print("无需改动。")
        return 0

    cfg["client"].append(MIXIN_NAME)
    tail = json.dumps(cfg, indent=2, ensure_ascii=False) + "\n"

    if args.dry_run:
        print(tail[:300])
        return 0

    bak = jar.with_name(jar.name + ".bak-black")
    if not bak.exists():
        shutil.copy2(jar, bak)
        print("备份 -> %s" % bak.name)

    cls_bytes = CLS.read_bytes()
    tmp = jar.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == MIXIN_JSON:
                data = tail.encode("utf-8")
            elif item.filename == ENTRY:
                continue
            else:
                data = zin.read(item.filename)
            zi = zipfile.ZipInfo(item.filename, date_time=item.date_time)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = item.external_attr
            zout.writestr(zi, data)
        zi = zipfile.ZipInfo(ENTRY, date_time=(2026, 10, 17, 0, 0, 0))
        zi.compress_type = zipfile.ZIP_DEFLATED
        zout.writestr(zi, cls_bytes)
    zin.close()
    shutil.move(str(tmp), str(jar))
    print("已写入 %s（注册 %s）" % (jar, MIXIN_NAME))
    return 0


if __name__ == "__main__":
    sys.exit(main())
