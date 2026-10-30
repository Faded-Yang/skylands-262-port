#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_preset_r368.py —— 重建 R368 那版（用户认可的「v2 前一个版本」）。

## 用户裁定

> 「不是还原到这儿啊，是 v2 的前一个版本，那个时候就不错」

⇒ 精确复刻 **R368** 的 15 条目版本：
  · 6 个 `custom:` 密度函数 —— 原版 aerolith
  · 噪声设置 —— **原版逐字节 + 只加 `carvers` 指向 `skylands:*`**
  · carver `skylands:cave` / `canyon` —— 26.3 原版完整配置，只改 `y=[170,450]` + `count=uniform(2,14)`
  · 维度类型 —— 原版（`height=576`）
  · 世界预设 —— 只改 `overworld.type` / `generator.settings`
  · `minecraft:normal` 标签 + 中英 lang

**不包含**（这些是 v2/R369 才加的，用户已否决）：
  · 岛加厚 `island_a` / `island_b` / `island_top_*`
  · `aquifers` 删除
  · 船结构覆盖（`structory:boat` / `medieval_buildings:ship`）
  · `max(原低层, 岛A, 岛B)` 三层叠加

## 用法

    python tools/build_preset_r368.py
"""
import json
import os
import sys
import zipfile

BASE = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
MC_JAR = r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar"
SRC = os.path.join(BASE, r"work\dp26\_off_aerolith-1.3.2-26.3.zip")
OUT = os.path.join(BASE, r"work\run26\mods-stable\sky262-preset-1.0.0.jar")
NS, ID = "skylands", "sky_islands"
MOD_ID, VERSION = "zsky262_preset", "1.0.0"
Y_MIN, Y_MAX = 170, 450
COUNT_MIN, COUNT_MAX = 2, 14

LANG = {
    "zh_cn": {"generator.skylands.sky_islands": "浮岛世界"},
    "en_us": {"generator.skylands.sky_islands": "Sky Islands"},
}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    src = zipfile.ZipFile(SRC)
    mc = zipfile.ZipFile(MC_JAR)
    e = {}

    # 1) 密度函数：原样 6 个
    n = 0
    for k in src.namelist():
        if "/density_function/" in k:
            e[k] = src.read(k).decode("utf-8", "replace")
            n += 1
    print("[1] 密度函数 %d 个（原版）" % n)

    # 2) 噪声设置：原版 + 只加 carvers
    raw = src.read("data/minecraft/worldgen/noise_settings/overworld.json").decode("utf-8", "replace")
    ns = json.loads(raw)
    ns["carvers"] = {"air": ["%s:cave" % NS, "%s:canyon" % NS]}
    e["data/%s/worldgen/noise_settings/%s.json" % (NS, ID)] = json.dumps(ns, indent=2, ensure_ascii=False) + "\n"
    print("[2] 噪声设置 sea_level=%s carvers=%s aquifers=%s"
          % (ns.get("sea_level"), json.dumps(ns["carvers"]),
             "保留（原版）" if "aquifers" in ns else "缺失"))

    # 3) carver：26.3 原版完整配置，只改 y 与 count
    for cn in ("cave", "canyon"):
        d = json.loads(mc.read("data/minecraft/worldgen/carver/%s.json" % cn).decode("utf-8", "replace"))
        d["y"] = {"type": "minecraft:uniform",
                  "min_inclusive": {"absolute": Y_MIN}, "max_inclusive": {"absolute": Y_MAX}}
        if "count" in d:
            d["count"] = {"type": "minecraft:uniform",
                          "min_inclusive": COUNT_MIN, "max_inclusive": COUNT_MAX}
        e["data/%s/worldgen/carver/%s.json" % (NS, cn)] = json.dumps(d, indent=1, ensure_ascii=False) + "\n"
        print("[3] carver %-7s y=[%d,%d] count=uniform(%d,%d) 字段 %d 个"
              % (cn, Y_MIN, Y_MAX, COUNT_MIN, COUNT_MAX, len(d)))

    # 4) 维度类型：原样
    e["data/%s/dimension_type/%s.json" % (NS, ID)] = \
        src.read("data/minecraft/dimension_type/overworld.json").decode("utf-8", "replace")
    d = json.loads(e["data/%s/dimension_type/%s.json" % (NS, ID)])
    print("[4] 维度类型 min_y=%s height=%s" % (d.get("min_y"), d.get("height")))

    # 5) 世界预设
    cand = [k for k in mc.namelist()
            if "/worldgen/world_preset/" in k and not k.startswith("data/minecraft/tags/")
            and k.endswith(".json")]
    cand.sort(key=lambda k: (not k.endswith("/normal.json"), k))
    preset = json.loads(mc.read(cand[0]).decode("utf-8", "replace"))
    ow = preset["dimensions"]["minecraft:overworld"]
    ow["type"] = "%s:%s" % (NS, ID)
    ow["generator"]["settings"] = "%s:%s" % (NS, ID)
    e["data/%s/worldgen/world_preset/%s.json" % (NS, ID)] = json.dumps(preset, indent=2, ensure_ascii=False) + "\n"
    print("[5] 世界预设 OK")

    # 6) 标签 + 语言 + fabric.mod.json
    e["data/minecraft/tags/worldgen/world_preset/normal.json"] = json.dumps(
        {"values": ["minecraft:normal", "minecraft:large_biomes", "minecraft:amplified",
                    "%s:%s" % (NS, ID)]}, indent=2, ensure_ascii=False) + "\n"
    for lang, kv in LANG.items():
        e["assets/%s/lang/%s.json" % (NS, lang)] = json.dumps(kv, indent=2, ensure_ascii=False) + "\n"
    e["fabric.mod.json"] = json.dumps({
        "schemaVersion": 1, "id": MOD_ID, "version": VERSION,
        "name": "Sky Islands World Preset",
        "description": "把「天穹群岛」浮岛地形做成可选的世界类型。",
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
    if len(e) != 15:
        print("  ⚠ 条目数不是预期的 15（实际 %d）" % len(e))
    for k in sorted(e):
        print("   " + k)
    return 0


if __name__ == "__main__":
    sys.exit(main())
