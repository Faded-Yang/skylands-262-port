#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_carvers_islands.py —— 让洞穴真正生成在浮岛岩体里。

## 之前错在哪（两层错）

1. **carver 的 Y 下界 140 落在岛下方的虚空里**。浮岛实测分布：中层 176..220、空隙 224..311、高层 320..447。
2. **更致命**：上次重建 `cave.json` 时源包没有该文件，我用 `{"type": "minecraft:cave"}` 现编，
   **`count` / `probability` / `replaceable` / `lava_level` 全部丢失** ⇒ 雕刻器没有配置，根本不工作。

## 正确做法

从 **MC 26.3 原版 jar** 里取完整的 `carver/cave.json` 与 `carver/canyon.json`，只改两处：
  · `y`  → 对齐浮岛岩体带 `[170, 450]`
  · `count` → 从 `very_biased_to_bottom`（强烈偏底部=浪费在虚空）改成 `uniform`，让雕刻尝试在岛带内均匀铺开

其余字段（`probability` / `thickness` / `horizontal_radius_multiplier` / `replaceable` / `lava_level` …）**原样保留**。

## 用法

    python tools/fix_carvers_islands.py [--world <世界目录>]
"""
import json
import os
import shutil
import sys
import zipfile

MC_JAR = r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar"
BASE = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"

# 实测浮岛岩体带：中层 176..220 / 高层 320..447。取 [170,450] 覆盖两端并留一点余量。
Y_MIN, Y_MAX = 170, 450
# 每区块雕刻尝试次数：均匀分布，别全堆在底部
COUNT_MIN, COUNT_MAX = 2, 14


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    world = os.path.join(BASE, r"work\run26\watch\saves\sky islands")
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--world":
            world = argv[i + 1]

    dp = os.path.join(world, "datapacks")
    pack = os.path.join(dp, "aerolith-1.3.2-26.3.zip")
    if not os.path.exists(pack):
        print("★ 找不到数据包:", pack)
        return 1

    mc = zipfile.ZipFile(MC_JAR)
    z = zipfile.ZipFile(pack)
    data = {n: z.read(n) for n in z.namelist()}
    z.close()

    for name in ("cave", "canyon"):
        src = "data/minecraft/worldgen/carver/%s.json" % name
        try:
            d = json.loads(mc.read(src).decode("utf-8", "replace"))
            origin = "26.3 原版"
        except KeyError:
            print("  ★ 26.3 jar 里没有", src)
            continue

        d["y"] = {"type": "minecraft:uniform",
                  "min_inclusive": {"absolute": Y_MIN},
                  "max_inclusive": {"absolute": Y_MAX}}
        if "count" in d:
            d["count"] = {"type": "minecraft:uniform",
                          "min_inclusive": COUNT_MIN,
                          "max_inclusive": COUNT_MAX}
        data[src] = (json.dumps(d, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
        print("  %-7s <- %s | y=[%d,%d] count=uniform(%d,%d) probability=%s replaceable=%s"
              % (name, origin, Y_MIN, Y_MAX, COUNT_MIN, COUNT_MAX,
                 d.get("probability"), d.get("replaceable")))
    mc.close()

    shutil.copy2(pack, pack + ".bak-carvercfg")
    with zipfile.ZipFile(pack, "w", zipfile.ZIP_DEFLATED) as w:
        for n, b in data.items():
            w.writestr(n, b)
    print("\n  数据包已更新: %d 条目, %d B" % (len(data), os.path.getsize(pack)))

    # 清区块让洞穴真的重新生成
    ov = os.path.join(world, "dimensions", "minecraft", "overworld")
    for sub in ("region", "entities", "poi"):
        p = os.path.join(ov, sub)
        if os.path.isdir(p):
            n = len(os.listdir(p))
            shutil.rmtree(p)
            print("  清 %s (%d 文件)" % (sub, n))
    print("\n完成。重启游戏后区块会按新 carver 配置生成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
