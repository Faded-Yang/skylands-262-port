#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R369：地形 v2 结果 + 代理发现的 6 条关键事实。超预算就搬旧行到冷层。"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
COLD = os.path.join(P, "docs", "SOLVED-FAMILIES.md")
h = open(HOT, encoding="utf-8", errors="replace").read()
b0 = len(h.encode("utf-8"))
shutil.copy2(HOT, HOT + ".bak-r369-" + datetime.datetime.now().strftime("%H%M%S"))

ROWS = [
 "| 🎉🎉 **【R369 地形 v2：A 岛厚 ✅ / D 水柱 ✅ / C 船 ✅ / B 结构上岛 ⚠】** "
 "`sky262-preset-1.0.0.jar` 重建为 **9,871 B / 23 条目 / mod id 改为 `zsky262_preset`**。"
 "**A**：`final_density = max(原低层, 岛A, 岛B) + beardifier`，两带 2D mask × 两段式锥底；实测 1,115,136 列 ⇒ 中带 p50=11、高带 p50=17、**合计中位 14.1**（目标≥12）；锥形：距边缘 0/1-2/3-5/6-10/11-19/20-40 格 → 厚度 3/4/7/9/9/**17**；离散 29/26 个 blob，最大 403×403 / 479×479。"
 "**D**：carver 只挖 y≥168 + **`aquifers` 整键删除**；实测水 y≤63=28,847,093 / y64-79=**236** / y80-159=7 / y≥160=0 ⇒ 无外溢。"
 "**C**：`medieval_buildings:ship`、`structory:boat` 改 `{\"absolute\":62}` 并删投影；实测 boat 落 **y=61**（原点 62）| —— | R369 |",

 "| ★★★★★ **【R369 ⚠ `wg_render` 调色板 bug：历史地形数据全部偏高】** 26.3 区块 NBT 的 `sections[].block_states.palette` **混用三种形态**："
 "`\"minecraft:air\"` / `{\"\":\"minecraft:stone\"}` / `{\"id\":..,\"properties\":..}`。旧 `palette_names()` 只认 `{\"Name\":..}` ⇒ 其余变 `'?'` 被当**实心**。"
 "**⇒ 修好前所有分层统计/厚度/空气占比数字都要重测**（已修 `tools/wg_render.py`）| —— | R369 |",

 "| ★★★★ **【R369 结构 `start_height` 的投影语义】** 带 `project_start_to_heightmap` 时，`start_height` 是**相对地表的偏移**，不是绝对高度"
 "（`JigsawPlacement#addPieces`：`y = start_height + getFirstFreeHeight(...)`）。⇒ **地表 jigsaw 不需要改任何 JSON**，岛够高够多就自然落岛顶；"
 "村庄只刷海平面 / 船浮空是**同一机制**。**B 实测**：40 个结构起点 高带 320-460 = 10 个(25%) / 海平面 1 / y<60 = 23(57.5%)；"
 "落岛实例 `ruined_portal_jungle` 369、`ocean_ruin_cold` 360、`trail_ruins` 345、`structory:abandoned_chapel` 363。"
 "**缺口：样本区是海洋群系，村庄/哨塔一个都没匹配上 ⇒ 村庄落岛只有机制证据、无实例** | —— | R369 |",

 "| ★★★★ **【R369 Fabric 资源包按 `mod id` 排序、后加载者胜】** 两个交叉探针实测（jar 名与 id 反序，**id 决定谁赢**）。"
 "本 mod 要覆盖 `structory:boat` / `medieval_buildings:ship` ⇒ **id 必须是 `zsky262_preset`**（z 开头排最后）并加 `recommends`。"
 "⚠ **若删掉 structory / medieval_buildings，必须同时删本 mod**，否则 `Unbound values in registry ... template_pool` 让世界加载失败（实测过） | —— | R369 |",

 "| ⚠ **【R369 无头生成两坑】** ① `/forceload` **单次上限 256 区块**，且**一个 tick 内同步生成** ⇒ 必须 `max-tick-time=-1`，否则 60s 看门狗直接杀服；"
 "② 老存档不会变 —— 新地形只在新生成区块出现 ⇒ **建议新建世界**。工具：`tools/wg_gen2.py` / `wg_islands3.py`（流式）/ `wg_structs_y.py` / `wg_struct_table.py` | —— | R369 |",
]

anchor = "| 阶段A 生物刷新（现成 mod） |"
h = h.replace(anchor, "\n".join(ROWS) + "\n" + anchor)

# 体积控制
lines = h.split("\n")
st = next(k for k, l in enumerate(lines) if l.strip().startswith("| 族 | 结论 |"))
en = st
while en < len(lines) and lines[en].startswith("|"):
    en += 1
rows = lines[st + 2:en]
KEEP = 9
moved, kept = rows[:-KEEP], rows[-KEEP:]
with open(COLD, "a", encoding="utf-8", newline="\n") as f:
    f.write("\n\n## 搬出索引行（t10）\n\n| 族 | 结论 | 轮次 |\n|---|---|---|\n")
    for r in moved:
        f.write(r + "\n")
h2 = "\n".join(lines[:st + 2] + kept + lines[en:])
open(HOT, "w", encoding="utf-8", newline="\n").write(h2)

tot = sum(os.path.getsize(f) for f in [
    os.path.expanduser("~/.dsh/AGENTS.md"),
    r"C:\Users\95959\OneDrive\Desktop\Work\AGENTS.md",
    HOT,
])
print("moved %d; hot %d -> %d B; total %d B %s"
      % (len(moved), b0, len(h2.encode("utf-8")), tot, "OK" if tot <= 40960 else "OVER"))
