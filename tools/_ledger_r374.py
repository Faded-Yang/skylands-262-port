#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R374：+2 成功，mods-stable 49 jar；绕开实验性设置框的正确做法；两处降级。"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
COLD = os.path.join(P, "docs", "SOLVED-FAMILIES.md")
h = open(HOT, encoding="utf-8", errors="replace").read()
shutil.copy2(HOT, HOT + ".bak-r374-" + datetime.datetime.now().strftime("%H%M%S"))

ROWS = [
 "| 🎉 **【R374 移植第三轮：+2 成功，mods-stable 49 jar】** **`create-sky-village`** + **`when-dungeons-arise`（DungeonsArise）** 双双进世界通过。"
 "**`mods-stable`(49) 的标题 `TITLE_SCREEN_OK` 25.3s 与进世界 `WORLD_OK` 都在交付物本体上复跑过**。"
 "新增 `create_sky_village-0.0.29I-26.3.jar` / `DungeonsArise-2.1.68-26.3.jar` | —— | R374 |",

 "| ★★★★★ **【R374 绕开「实验性设置」确认框的正确做法】** 不要去点那个框（SDL3 不认伪造输入）。"
 "**拿一个不是用浮岛预设建的存档当验收世界**：`work/run26/watch/saves/New World (1)`"
 "（`Enabled` 只有 vanilla/aeronautics/create/fabric-convention-tags-v2/sable/sky262recipes，**不弹框**），"
 "复制到 `stag1/saves/` 后 `--quickPlaySingleplayer` 直接进。"
 "⚠ 不能用空壳存档（`Overworld settings missing`），也不能用引用了已卸载 mod 结构的存档 | —— | R374 |",

 "| ★★★ **【R374 DA 最后三层的修法（都在 `tools/fix_loot_121.py`）】** "
 "① **`exploration_map.destination`**：26.3 只收「结构 tag（要 `#`）」或「结构 id 列表」，DA 两种混用 ⇒ "
 "转换器先收集 jar 里**真实存在的** tag 与结构 id，能对上 tag 就加 `#`，否则用 `[\"<id>\"]`；"
 "② **不带命名空间的条目类型**（`\"type\":\"item\"` / `\"tag\"`）：按 `== \"minecraft:item\"` 判断会**静默漏改**"
 "（踩过：`minecraft:chain` 没换掉）⇒ 必须先归一化；"
 "③ 26.3 删了通用 `minecraft:music_discs` tag ⇒ 换 `creeper_drop_music_discs`；"
 "`set_components` 旧写法 `custom_model_data:<int>`→`{\"floats\":[int]}`、`dyed_color:{\"rgb\":n}`→`n` | —— | R374 |",

 "| ⚠ **【R374 两处降级（必须写进最终交付说明）】** ① `minecraft:potion` 从 DA 的诱捕豁免实体 tag 里**删掉**"
 "（26.3 无此 id）；② 唱片集合从 `minecraft:music_discs` 换成 `creeper_drop_music_discs` ⇒ **可获得的唱片变少**。"
 "详见 `docs/port-batch2.md` | —— | R374 |",
]

anchor = "| 阶段A 生物刷新（现成 mod） |"
h = h.replace(anchor, "\n".join(ROWS) + "\n" + anchor)
h = h.replace("（47 jar，含 `modmenu-21.0.0`）",
              "（**49 jar**，含 `modmenu` / `create-sky-village` / `DungeonsArise`）")
h = h.replace("（A 层 33 已装 / F 层 30 部分 / B·N 层 44 待评估）",
              "（**A 层 33 已装；F 层已成功 3 个：sky-villages / create-sky-village / DungeonsArise，F 剩 27；B·N 层 44 待评估**）")

lines = h.split("\n")
st = next(k for k, l in enumerate(lines) if l.strip().startswith("| 族 | 结论 |"))
en = st
while en < len(lines) and lines[en].startswith("|"):
    en += 1
rows = lines[st + 2:en]
KEEP = 10
moved, kept = rows[:-KEEP], rows[-KEEP:]
with open(COLD, "a", encoding="utf-8", newline="\n") as f:
    f.write("\n\n## 搬出索引行（t15）\n\n| 族 | 结论 | 轮次 |\n|---|---|---|\n")
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
