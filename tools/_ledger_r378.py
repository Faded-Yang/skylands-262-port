#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R378：第五批 +4（58 jar）+ configured_feature 的 26.3 真相 + 两处纠错。"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
COLD = os.path.join(P, "docs", "SOLVED-FAMILIES.md")
h = open(HOT, encoding="utf-8", errors="replace").read()
shutil.copy2(HOT, HOT + ".bak-r378-" + datetime.datetime.now().strftime("%H%M%S"))

ROWS = [
 "| 🎉 **【R378 第五批：+4 成功，mods-stable 58 jar】** 新增（全 `WORLD_OK` + `TITLE_SCREEN_OK`，交付 jar 与测过的 SHA256 逐字节一致）："
 "`strayed-fates-forsaken` 36.2s/24.0s、`imst` 36.2s/24.8s、`Structory_Towers` 36.2s/26.0s、`sablephysicscompat` 36.2s/25.1s。"
 "58 jar 整体再测 TITLE 25.6s + WORLD_OK 36.2s。核心产出 **`tools/convert_features_121.py`** + `tools/feature_schema_263.py`（从 26.3.jar 反查 57 个 type 字段全表） | —— | R378 |",

 "| ★★★★★ **【R378 `configured_feature` 的 26.3 真相（全部实测）】** ① 目录 `worldgen/configured_feature` → **`worldgen/feature`**（旧目录不读）；"
 "② **`config` 扁平化**（每个 feature 类本身就是 record 并实现 Feature）；"
 "③ **删了 4 个 type**：`random_patch` / `flower` / `no_bonemeal_flower` / `forest_rock` —— patch 类的 `tries`/`xz_spread`/`y_spread` "
 "**搬进 placed_feature 的 placement**（`count` + `offset` 的 x/y/z）；`forest_rock` → **`block_blob`** + 必填 `can_place_on`；"
 "④ `tree`：`dirt_provider`+`force_dirt` → **必填 `below_trunk_provider`**（默认 `minecraft:soil_beneath_tree`）；"
 "⑤ `lake`：新增 3 个**必填** predicate（`can_place_feature` / `can_replace_with_air_or_fluid` / `can_replace_with_barrier`）；"
 "⑥ state provider 全表改名，**`simple_state_provider` 塌成裸方块状态**；"
 "⑦ **biome 的 `carvers` 从 `{air:[…],liquid:[…]}` 变成扁平数组**。"
 "57 个 type 字段全表见 `docs/port-batch3.md` §3（新 mod 撞 type 时先查这张表） | —— | R378 |",

 "| ★★★★ **【R378 纠错两条（会误导下一轮）】** ① **`Structory_Towers` 不是结构/模板池坏的** —— 26.1.2 vs 26.3 的 structure/template_pool 字段集合与 "
 "`step`/`element_type`/`processor_type` 取值**完全一致**；真因是 4 张 `potions/*` loot 表用了 26.3 **已删的 `minecraft:hide_additional_tooltip` 组件**（→ 换 `tooltip_display`）；"
 "② **`sablephysicscompat` 的三条真因**：`neoforge_to_fabric` 没剥 TOML **行尾注释** ⇒ id 变成 `\"sablephysicscompat\" #mandatory`；tag JSON 有 `//` 注释 + 尾逗号（26.3 严格 JSON）；"
 "`physics_block_properties` 在 26.3 是**单对象不是数组**。上一轮的 `FAIL_TIMEOUT` **复现不出**（全新副本第一次就 36.2s 进世界）⇒ 就是「验收世界被标实验性」那个坑 | —— | R378 |",

 "| ⚠ **【R378 `natures_spirit` 只能 Java 移植（数据救不了）】** 数据层已全转（176 feature / 220 placed / 51 biome / 47 biome carvers），但它是 **NeoForge 1.21.1 + 202 class**，"
 "且注册了**自定义 `feature_type` / `foliage_placer_type` / `tree_decorator_type`**（实测 `Unknown registry key … natures_spirit:alluaudia_feature`）⇒ 数据转换无解 | —— | R378 |",

 "| ✅ **【R378 顺手修了 4 个工具 bug】** `convert_121_data`（`spawn_overrides` 的 count 要 `min_inclusive`/`max_inclusive` 不是 `min`/`max`）、"
 "`neoforge_to_fabric`（TOML 行尾注释）、`fix_loot_121`（`hide_additional_tooltip` → `tooltip_display`）、`feature_schema_263.py`（新增，机械反查 57 个 type） | —— | R378 |",
]

anchor = "| 阶段A 生物刷新（现成 mod） |"
h = h.replace(anchor, "\n".join(ROWS) + "\n" + anchor)
h = h.replace("（**54 jar**，`watch\\mods` 已同步一致，`TITLE_SCREEN_OK` 27.0s",
              "（**58 jar**，`TITLE_SCREEN_OK` 25.6s")
h = h.replace("F+B·N 剩 ~53**", "F+B·N 剩 ~49**（`natures_spirit` 判定只能 Java 移植）")

lines = h.split("\n")
st = next(k for k, l in enumerate(lines) if l.strip().startswith("| 族 | 结论 |"))
en = st
while en < len(lines) and lines[en].startswith("|"):
    en += 1
rows = lines[st + 2:en]
KEEP = 10
moved, kept = rows[:-KEEP], rows[-KEEP:]
with open(COLD, "a", encoding="utf-8", newline="\n") as f:
    f.write("\n\n## 搬出索引行（t19）\n\n| 族 | 结论 | 轮次 |\n|---|---|---|\n")
    for r in moved:
        f.write(r + "\n")
h2 = "\n".join(lines[:st + 2] + kept + lines[en:])
open(HOT, "w", encoding="utf-8", newline="\n").write(h2)

tot = sum(os.path.getsize(f) for f in [
    os.path.expanduser("~/.dsh/AGENTS.md"),
    r"C:\Users\95959\OneDrive\Desktop\Work\AGENTS.md",
    HOT,
])
print("hot %d B; total %d B %s" % (len(h2.encode("utf-8")), tot, "OK" if tot <= 40960 else "OVER"))
