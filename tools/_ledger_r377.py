#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R377：第三批 +5（54 jar）+ 四条硬知识 + 下一步 configured_feature 转换器。"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
COLD = os.path.join(P, "docs", "SOLVED-FAMILIES.md")
h = open(HOT, encoding="utf-8", errors="replace").read()
shutil.copy2(HOT, HOT + ".bak-r377-" + datetime.datetime.now().strftime("%H%M%S"))

ROWS = [
 "| 🎉 **【R377 移植第四批：+5 成功，mods-stable 54 jar】** 新增（全部实测进世界 `WORLD_OK`）："
 "`no-void-structures`(34.1s) / `create-hangars`(36.2s) / `MoogsSoaringStructures`(34.3s) / "
 "`SkyVillages`(NeoForge 版重做, 36.2s) / `rabbit_pathfinding_fix`（7 class + mixin，`--keep all` + 手写 mixin 配置 + `lenient_mixins`）。"
 "54 jar 的标题与进世界都在交付物本体上复跑过 | —— | R377 |",

 "| ★★★★★ **【R377 `spawn_overrides` 的 `minCount/maxCount` → `count`（报错极具迷惑性）】** 结构 JSON 里 `spawn_overrides` 的 "
 "`minCount`/`maxCount` 在 26.3 要写成 **`count`**；不改会让**整批原版结构**变成 `Unbound values`"
 "（覆盖失败 ⇒ 原版条目失去绑定）。**看到「一大批原版结构 Unbound」先查这个，不要以为是结构池坏了** | —— | R377 |",

 "| ★★★★ **【R377 IntProvider 简写要补 `type`】** 旧写法 `{\"min\":a,\"max\":b}` 在 26.3 报 **`No key type`** ⇒ 必须补 "
 "`{\"type\":\"minecraft:uniform\",\"min_inclusive\":a,\"max_inclusive\":b}`。`Structory_Towers` 修了 **483 处** | —— | R377 |",

 "| ★★★★★ **【R377 验收世界每次都要用全新副本（吃掉 20 分钟的大坑）】** 同一个存档被试过「带新 mod 的加载」一次后会被**标成实验性**，"
 "之后每次加载都弹确认框、日志停在 `Loaded N advancements` ⇒ **表现成 `FAIL_TIMEOUT`（不是崩溃）**。"
 "**⇒ 批量脚本必须每测前重拷 `watch/saves/New World (1)`**（`work\\run26\\port\\_batch_g3.py` 里的 `fresh_world()`） | —— | R377 |",

 "| ⏳ **【R377 剩余最大一坨：`configured_feature` 逐类型转换器】** 26.3 的 `configured_feature` 按 feature type 分了新的字段结构，"
 "`strayed-fates` 305 / `natures-spirit` 2,839 / `imst` 324 个 JSON 都卡这一层。**写一个逐类型转换器是下一步主线**。"
 "另：`Structory_Towers` 差结构/模板池那层；`sablephysicscompat`（0 class / 50 data JSON）静默超时待查 | —— | R377 |",
]

anchor = "| 阶段A 生物刷新（现成 mod） |"
h = h.replace(anchor, "\n".join(ROWS) + "\n" + anchor)
h = h.replace("（**49 jar**，含 `modmenu` / `create-sky-village` / `DungeonsArise`）",
              "（**54 jar**，含 `modmenu` / `create-sky-village` / `DungeonsArise` / `create-hangars` / `SkyVillages` 等）")
h = h.replace("**A 层 33 已装；F 层已成功 3 个：sky-villages / create-sky-village / DungeonsArise，F 剩 27；B·N 层 44 待评估**",
              "**A 层 33 已装；F 层已成功 4 个（sky-villages / create-sky-village / DungeonsArise / SkyVillages-NeoForge 版）；"
              "B·N 层已成功 4 个（no-void-structures / create-hangars / MoogsSoaringStructures / rabbit_pathfinding_fix）；F+B·N 剩 ~62**")

lines = h.split("\n")
st = next(k for k, l in enumerate(lines) if l.strip().startswith("| 族 | 结论 |"))
en = st
while en < len(lines) and lines[en].startswith("|"):
    en += 1
rows = lines[st + 2:en]
KEEP = 10
moved, kept = rows[:-KEEP], rows[-KEEP:]
with open(COLD, "a", encoding="utf-8", newline="\n") as f:
    f.write("\n\n## 搬出索引行（t18）\n\n| 族 | 结论 | 轮次 |\n|---|---|---|\n")
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
