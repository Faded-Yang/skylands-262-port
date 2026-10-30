#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_preset_original.py —— 只做「把原版浮岛地形变成可选世界类型」，地形内容一字不改。

## 用户要求（最终）

> 「算了，什么也不要动，我要原模原样的浮岛原效果，把"浮岛效果做成世界类型"保留，其他复原」

⇒ 本脚本**只做包装**，不做任何地形修改：
  · 噪声设置 = 原版 aerolith 的转换结果，**逐字节搬**（不 add carvers、不改 aquifers、不改 sea_level）
  · 密度函数 6 个 = 原样
  · 维度类型 = 原样（height=576，浮岛在 y=320~447 需要）
  · 世界预设 = 从 26.3 原版 normal.json 复制，只把 overworld 的 type/settings 指向 `skylands:sky_islands`
  · minecraft:normal 标签并入 + 中英语言

**不包含**：carver 覆盖、船结构覆盖、岛加厚、aquifers 改动 —— 全都不加。
> 原版 aerolith 的 `noise_settings` **没有 `carvers` 键** ⇒ 原版就没有洞穴雕刻器，保持缺失。

## 用法

    python tools/build_preset_original.py
"""
import json
import os
import sys
import zipfile

BASE = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
MC_JAR = r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar"
SRC = os.path.join(BASE, r"work\dp26\_off_aerolith-1.3.2-26.3.zip")   # 原版转换（未改任何地形）
OUT = os.path.join(BASE, r"work\run26\mods-stable\sky262-preset-1.0.0.jar")
NS, ID = "skylands", "sky_islands"
MOD_ID, VERSION = "zsky262_preset", "1.0.0"

LANG = {
    "zh_cn": {"generator.skylands.sky_islands": "浮岛世界"},
    "en_us": {"generator.skylands.sky_islands": "Sky Islands"},
}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    src = zipfile.ZipFile(SRC)
    mc = zipfile.ZipFile(MC_JAR)
    e = {}

    # 1) 密度函数 6 个：原样
    n = 0
    for k in src.namelist():
        if "/density_function/" in k:
            e[k] = src.read(k).decode("utf-8", "replace")
            n += 1
    print("[1] 密度函数 %d 个（原样）" % n)

    # 2) 噪声设置：逐字节原样搬，只换命名空间路径
    raw = src.read("data/minecraft/worldgen/noise_settings/overworld.json").decode("utf-8", "replace")
    ns = json.loads(raw)
    e["data/%s/worldgen/noise_settings/%s.json" % (NS, ID)] = raw
    print("[2] 噪声设置（未改动） 顶层键: %s" % ", ".join(sorted(ns.keys())))
    print("    sea_level=%s  carvers=%s  aquifers=%s"
          % (ns.get("sea_level"),
             "存在" if "carvers" in ns else "缺失（原版就没有）",
             "存在" if "aquifers" in ns else "缺失"))

    # 3) 维度类型：原样
    dtraw = src.read("data/minecraft/dimension_type/overworld.json").decode("utf-8", "replace")
    d = json.loads(dtraw)
    e["data/%s/dimension_type/%s.json" % (NS, ID)] = dtraw
    print("[3] 维度类型（未改动） min_y=%s height=%s" % (d.get("min_y"), d.get("height")))

    # 4) 世界预设：26.3 原版 normal.json 做模板，只改 overworld 的两处引用
    cand = [k for k in mc.namelist()
            if "/worldgen/world_preset/" in k and not k.startswith("data/minecraft/tags/")
            and k.endswith(".json")]
    cand.sort(key=lambda k: (not k.endswith("/normal.json"), k))
    preset = json.loads(mc.read(cand[0]).decode("utf-8", "replace"))
    ow = preset["dimensions"]["minecraft:overworld"]
    ow["type"] = "%s:%s" % (NS, ID)
    ow["generator"]["settings"] = "%s:%s" % (NS, ID)
    e["data/%s/worldgen/world_preset/%s.json" % (NS, ID)] = json.dumps(preset, indent=2, ensure_ascii=False) + "\n"
    print("[4] 世界预设（只改了 overworld.type 与 generator.settings）")

    # 5) 标签 + 语言 + fabric.mod.json
    e["data/minecraft/tags/worldgen/world_preset/normal.json"] = json.dumps(
        {"values": ["minecraft:normal", "minecraft:large_biomes", "minecraft:amplified",
                    "%s:%s" % (NS, ID)]}, indent=2, ensure_ascii=False) + "\n"
    for lang, kv in LANG.items():
        e["assets/%s/lang/%s.json" % (NS, lang)] = json.dumps(kv, indent=2, ensure_ascii=False) + "\n"
    e["fabric.mod.json"] = json.dumps({
        "schemaVersion": 1, "id": MOD_ID, "version": VERSION,
        "name": "Sky Islands World Preset",
        "description": "把「天穹群岛」原版浮岛地形做成可选的世界类型（地形内容未作任何修改）。",
        "authors": ["skylands-262 port"], "license": "MIT", "environment": "*",
        "depends": {"fabricloader": ">=0.19.0", "minecraft": ">=26.1- <26.4-"},
    }, indent=2, ensure_ascii=False) + "\n"

    mc.close()
    src.close()

    if os.path.exists(OUT):
        os.remove(OUT)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as w:
        for k, v in sorted(e.items()):
            w.writestr(k, v.encode("utf-8"))
    print("\n写出 %s (%d 条目, %d B)  id=%s" % (os.path.basename(OUT), len(e), os.path.getsize(OUT), MOD_ID))
    for k in sorted(e):
        print("   " + k)
    return 0


if __name__ == "__main__":
    sys.exit(main())
