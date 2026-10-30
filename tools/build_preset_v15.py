#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_preset_v15.py —— 重建为「v1.5」：原版浮岛地形 + 只保留 v2 里真正有用的部分。

## 用户决定

「算了，换回v1，不折腾了，凑合吧，现在推进mod的移植项目，再看看现有v2有什么可保留的其他功能，如果有可以保留」

⇒ 地形回退到**原版 aerolith**（平整海面 + 薄浮岛），**不**做 v2 的加厚/加层（那是"分层大陆"，已被否决）。
但 v2 里有三样**独立于地形形状**的成果要保留：

| v2 成果 | 为什么保留 |
|---|---|
carver 只在 y≥168（水下不雕刻） | **防止水从海床漏成水柱**（这是用户明确抱怨的问题） |
`structory:boat` / `medieval_buildings:ship` → `absolute:62` 且删投影 | **船不再浮空** |
mod id = `zsky262_preset` | Fabric 资源包按 id 排序、后加载者胜 ⇒ 才能覆盖上面两个结构 |
dimension_type `height=576` | 浮岛在 y=320~447，原版 height=384（上限 y=320）装不下 |
6 个 `custom:` 密度函数一起打包 | 否则新世界引用悬空、卡在「正在准备生成世界」（v1 踩过） |

**保留 `aquifers` 原样**（v2 把它整个删了，会失去地下洞穴/岩浆湖；既然现在 carver 已经在 y≥168，
水下本来就不雕刻，不需要再牺牲 aquifers）。

## 用法

    python tools/build_preset_v15.py
"""
import json
import os
import sys
import zipfile

BASE = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
MC_JAR = r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar"
SRC = os.path.join(BASE, r"work\dp26\_off_aerolith-1.3.2-26.3.zip")   # 原版转换（sea_level=64、无 carvers）
OUT = os.path.join(BASE, r"work\run26\mods-stable\sky262-preset-1.0.0.jar")
NS, ID = "skylands", "sky_islands"
MOD_ID, VERSION = "zsky262_preset", "1.0.0"
Y_MIN, Y_MAX = 168, 450
COUNT_MIN, COUNT_MAX = 2, 14
SHIP_Y = 62

LANG = {
    "zh_cn": {"generator.skylands.sky_islands": "浮岛世界"},
    "en_us": {"generator.skylands.sky_islands": "Sky Islands"},
}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    src = zipfile.ZipFile(SRC)
    mc = zipfile.ZipFile(MC_JAR)
    e = {}

    # 1) 密度函数（custom:，id 不变）
    n = 0
    for k in src.namelist():
        if "/density_function/" in k:
            e[k] = src.read(k).decode("utf-8", "replace")
            n += 1
    print("[1] 密度函数 %d 个" % n)

    # 2) 噪声设置：原样 + 只加 carvers
    noise = json.loads(src.read("data/minecraft/worldgen/noise_settings/overworld.json").decode("utf-8", "replace"))
    noise["carvers"] = {"air": ["%s:cave" % NS, "%s:canyon" % NS]}
    e["data/%s/worldgen/noise_settings/%s.json" % (NS, ID)] = json.dumps(noise, indent=2, ensure_ascii=False) + "\n"
    print("[2] 噪声设置 sea_level=%s carvers=%s aquifers=%s"
          % (noise.get("sea_level"), json.dumps(noise["carvers"]),
             "保留" if "aquifers" in noise else "缺失"))

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

    # 4) 维度类型 height=576（独立 id）
    dt = json.loads(src.read("data/minecraft/dimension_type/overworld.json").decode("utf-8", "replace"))
    e["data/%s/dimension_type/%s.json" % (NS, ID)] = json.dumps(dt, indent=1, ensure_ascii=False) + "\n"
    print("[4] 维度类型 min_y=%s height=%s" % (dt.get("min_y"), dt.get("height")))

    # 5) 世界预设（原版 normal 做模板）
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

    # 6) 船：改 absolute:62 + 删投影（保留 v2 成果）
    fixed = 0
    for path, lid in (("data/structory/worldgen/structure/boat.json", "structory:boat"),
                      ("data/medieval_buildings/worldgen/structure/ship.json", "medieval_buildings:ship")):
        # 目标 mod 的原始定义从 mods-stable 的对应 jar 里取
        found = None
        for jar in os.listdir(os.path.join(BASE, "work/run26/mods-stable")):
            if not jar.endswith(".jar"):
                continue
            try:
                z = zipfile.ZipFile(os.path.join(BASE, "work/run26/mods-stable", jar))
            except Exception:
                continue
            if path in z.namelist():
                found = z.read(path).decode("utf-8", "replace")
                z.close()
                break
            z.close()
        if found is None:
            print("    ★ 找不到 %s 的原定义，跳过" % lid)
            continue
        d = json.loads(found)
        d["start_height"] = {"absolute": SHIP_Y}
        d.pop("project_start_to_heightmap", None)
        e[path] = json.dumps(d, indent=2, ensure_ascii=False) + "\n"
        fixed += 1
        print("[6] %-24s start_height=absolute:%d 已删投影" % (lid, SHIP_Y))
    print("    共修 %d 个船结构" % fixed)

    # 7) 标签 + 语言 + fabric.mod.json
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
        "recommends": {"structory": "*", "medieval_buildings": "*"},
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
