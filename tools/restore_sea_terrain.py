#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
restore_sea_terrain.py —— 恢复「原版浮岛地形（含平整海面）」，只把洞穴限制在浮岛高度。

## 背景（用户的明确反馈）

我们之前把 y<104 的地面整片挖成虚空（`final_density = min(原, gradient(104→120))` + `sea_level=-64`），
结果**更糟**：
  · 没了海洋 ⇒ 原本该在海面以下的地牢/结构特征建筑全部悬空
  · 液体没了承托 ⇒ 流成一条一条
  · 用户原话：「效果甚至不如给海面开个大洞」

## 正确做法

**保留 aerolith 的原版地形（`sea_level=64` 的平整海面）**，唯一改动是：
  把 carver（洞穴/峡谷雕刻器）的 Y 下界抬到 **140**。
海面水顶实测 y=63 ⇒ 余量 77 格 ⇒ **结构上不可能再挖穿海面**，
而洞穴依然出现在浮岛高度的岩体里（用户要的「在高山里开裂缝通到洞穴」）。

## 用法

    python tools/restore_sea_terrain.py --src <原版aerolith.zip> --world "<世界目录>"
"""
import json
import os
import shutil
import sys
import zipfile

Y_MIN, Y_MAX = 140, 480


def build_pack(src_zip, out_zip):
    z = zipfile.ZipFile(src_zip)
    data = {n: z.read(n) for n in z.namelist()}
    z.close()

    ns_path = "data/minecraft/worldgen/noise_settings/overworld.json"
    ns = json.loads(data[ns_path].decode("utf-8", "replace"))
    ns["sea_level"] = 64                                  # 恢复平整海面
    ns["carvers"] = {"air": ["minecraft:cave", "minecraft:canyon"]}   # 重新启用雕刻器
    data[ns_path] = (json.dumps(ns, indent=2, ensure_ascii=False) + "\n").encode("utf-8")

    # carver 的 Y 范围抬到浮岛高度
    for name in ("cave", "canyon"):
        pth = "data/minecraft/worldgen/carver/%s.json" % name
        if pth in data:
            d = json.loads(data[pth].decode("utf-8", "replace"))
        else:
            d = {"type": "minecraft:%s" % name}
        d["y"] = {"type": "minecraft:uniform",
                  "min_inclusive": {"absolute": Y_MIN},
                  "max_inclusive": {"absolute": Y_MAX}}
        data[pth] = (json.dumps(d, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
        print("  carver %-7s y=[%d,%d]" % (name, Y_MIN, Y_MAX))

    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as w:
        for n, b in data.items():
            w.writestr(n, b)
    print("  写出 %s (%d 条目, %d B)" % (os.path.basename(out_zip), len(data), os.path.getsize(out_zip)))


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    base = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
    src = os.path.join(base, r"work\dp26\_off_aerolith-1.3.2-26.3.zip")
    world = os.path.join(base, r"work\run26\watch\saves\sky islands")
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--src":
            src = argv[i + 1]
        if a == "--world":
            world = argv[i + 1]

    print("源:", src)
    print("目标世界:", world)
    dp = os.path.join(world, "datapacks")
    os.makedirs(dp, exist_ok=True)

    # 清掉现有数据包，只留我们这一个
    for f in os.listdir(dp):
        os.remove(os.path.join(dp, f))
        print("  移除旧数据包:", f)

    out_zip = os.path.join(dp, "aerolith-1.3.2-26.3.zip")
    build_pack(src, out_zip)

    # 清区块（保留 worldgen 设置）
    ov = os.path.join(world, "dimensions", "minecraft", "overworld")
    for sub in ("region", "entities", "poi"):
        p = os.path.join(ov, sub)
        if os.path.isdir(p):
            n = len(os.listdir(p))
            shutil.rmtree(p)
            print("  清 %s (%d 文件)" % (sub, n))

    print("\n完成。进游戏后请新建/重进世界让区块按新地形生成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
