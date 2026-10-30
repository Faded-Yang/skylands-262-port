#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_create_trims.py -- 修 Create 硬纸板盔甲的 4 个物品模型（日志里 8 条 Multiple atlases）。

## 根因（实证，不是"贴图统一图集"那么简单）

Create 的 4 件硬纸板盔甲走 `minecraft:select`（按 `minecraft:trim_material` 选子模型），
每个 case 指向 `create:item/cardboard_<piece>_<material>_trim`，其 `layer1` 是
`create:trims/items/card_<piece>_trim_<material>` —— **这个 sprite 在 26.3 里根本不存在**：

  * 1.21.1：`assets/minecraft/atlases/items.json` 里由 `paletted_permutations` 用
    `palette_key: minecraft:trims/color_palettes/trim_palette` 现场生成 `<texture>_<material>`。
  * 26.3：调色板改到 `assets/minecraft/textures/palettes/trim_base.png`，
    `palette_key: minecraft:trim_base`，permutation 指向 `minecraft:trim/<material>`。
    `trims/color_palettes/trim_palette` 已不存在 ⇒ 日志 `Failed to load palette image trim_palette`
    ⇒ 整条 permutation 源一个 sprite 都不产出。

于是 `layer1` 解析成 missingno（它在 **blocks** 图集），而 `layer0` 在 **items** 图集
⇒ 26.3 的 `CuboidItemModelWrapper.validateAtlasUsage` 直接抛
`Multiple atlases used in model` —— 这就是那 8 条（4 个物品 × 2 次资源重载）的真因。

## 修法

把 Create 那份 `assets/minecraft/atlases/items.json` 的 `palette_key`/`permutations`
换成 26.3 的调色板命名（纹理列表原样保留）。这样 `card_<piece>_trim_<material>`
会被正常生成进 items 图集，模型能 bake，图标也保留原来的材质染色。

用法：
    python tools/patch_create_trims.py --src <create jar> --out <patched jar>
"""
import argparse
import io
import json
import os
import shutil
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")

ATLAS = "assets/minecraft/atlases/items.json"

# 26.3 的 permutation 表（照抄 26.3.jar 的 assets/minecraft/atlases/items.json）
PERM_26 = {
    "amethyst": "minecraft:trim/amethyst",
    "copper": "minecraft:trim/copper",
    "copper_darker": "minecraft:trim/copper_darker",
    "diamond": "minecraft:trim/diamond",
    "diamond_darker": "minecraft:trim/diamond_darker",
    "emerald": "minecraft:trim/emerald",
    "gold": "minecraft:trim/gold",
    "gold_darker": "minecraft:trim/gold_darker",
    "iron": "minecraft:trim/iron",
    "iron_darker": "minecraft:trim/iron_darker",
    "lapis": "minecraft:trim/lapis",
    "netherite": "minecraft:trim/netherite",
    "netherite_darker": "minecraft:trim/netherite_darker",
    "quartz": "minecraft:trim/quartz",
    "redstone": "minecraft:trim/redstone",
    "resin": "minecraft:trim/resin",
}
PALETTE_KEY_26 = "minecraft:trim_base"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    z = zipfile.ZipFile(args.src)
    old = json.loads(z.read(ATLAS))

    # 只保留 paletted_permutations 源，纹理列表原样搬；换掉 palette_key / permutations
    new_sources = []
    perms = {}
    for src in old.get("sources", []):
        if src.get("type", "").endswith("paletted_permutations"):
            keep = dict(src)
            keep["type"] = "minecraft:paletted_permutations"
            keep["palette_key"] = PALETTE_KEY_26
            keep["permutations"] = PERM_26
            new_sources.append(keep)
            perms = keep["permutations"]
        else:
            new_sources.append(src)
    if not any("paletted_permutations" in s.get("type", "") for s in new_sources):
        raise SystemExit("%s 里没找到 paletted_permutations 源，不需要打这个补丁" % ATLAS)

    atlas_bytes = json.dumps({"sources": new_sources}, indent=2).encode("utf-8")
    print("[atlas] palette_key %r -> %r，permutations %d 项"
          % (old["sources"][0].get("palette_key"), PALETTE_KEY_26, len(perms)))
    for s in new_sources:
        for t in s.get("textures", []):
            print("        texture:", t)

    # 原样复制其它条目，只替换那一个 JSON
    if os.path.abspath(args.out) != os.path.abspath(args.src):
        shutil.copyfile(args.src, args.out)
    tmp = args.out + ".tmp"
    with zipfile.ZipFile(args.src) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        replaced = 0
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == ATLAS:
                data = atlas_bytes
                replaced += 1
            zout.writestr(item, data)
    assert replaced == 1, replaced
    os.replace(tmp, args.out)
    print("[out]", args.out, "已替换", ATLAS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
