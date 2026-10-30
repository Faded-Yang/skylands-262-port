#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性：把 R366（汉化进展）追加进热层台账。"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
h = open(HOT, encoding="utf-8", errors="replace").read()
b0 = len(h.encode("utf-8"))
shutil.copy2(HOT, HOT + ".bak-r366-" + datetime.datetime.now().strftime("%H%M%S"))

ROWS = [
    "| ✅ **【R366 汉化：工具 + 现状】** 新增 `tools\\lang_audit.py`（逐 namespace 统计 en_us / zh_cn / 缺失，"
    "**注意 `assets/<ns>/lang/x.json` 是 4 段，别写成 `len(parts)<5`**）+ `tools\\merge_zhcn.py`"
    "（按 **namespace 匹配**把旧版 jar 的 `zh_cn` 合并进新 jar，**只补缺失、不覆盖**，自动 `.bak-zh`）。"
    "现状：en_us **8,509** 条 / zh_cn **7,629** 条（**87.0%**）。**`aeronautics`/`simulated` 上游自带全中文（219/219、650/650）** | —— | R366 |",
    "| ✅ **【R366 Sable 汉化完成 128/128】** 这是我们自己移植的 mod、上游无中文。已全量翻译并写回 "
    "`assets/sable/lang/zh_cn.json`（提交在 `tools\\_sable_zh.py`）。术语统一：sub-level→子维度 / contraption→装置 / schematic→蓝图 / force group→力组。"
    "**注意 `commands.sable.sub_level.shatter.sub_level.only_single_block`（单数）与 `commands.data.sub_level.query` 两个 key 一开始被我写错了名字**，已修 | —— | R366 |",
    "| ⚠ **【R366 汉化剩余 ~1,100 条的分布】** `jei` 354 / `xaeroworldmap` 327（**完全无 zh_cn**）/ `xaerominimap` 129 / `sodium` 105（**完全无 zh_cn**）"
    "/ `inventoryprofilesnext` 48 / `ponder` 40 / `balm` 22 / 其余散点。**首选来源是 CFPA 汉化资源包**（`CFPAOrg/Minecraft-Mod-Language-Package`，"
    "GitHub release 里有按 MC 版本打包的 `assets/<ns>/lang/zh_cn.json`）；旧 jar 那一轮已榨出 +218 条（JEI +70 / Waystones +118 / AppleSkin +22 / Jade +8）| —— | R366 |",
    "| ★★★ **【R366 翻译硬约束】** 必须原样保留占位符（`%s` `%d` `%.2f` `%1$s`）**数量和顺序**，否则运行期 `String.format` 崩；"
    "还要保留 `§` 颜色码与 `\\n`。**只改 `zh_cn.json`，绝不动 `en_us.json`** | —— | R366 |",
]

anchor = "| 阶段A 生物刷新（现成 mod） |"
if anchor in h:
    h = h.replace(anchor, "\n".join(ROWS) + "\n" + anchor)
open(HOT, "w", encoding="utf-8", newline="\n").write(h)
tot = sum(os.path.getsize(f) for f in [
    os.path.expanduser("~/.dsh/AGENTS.md"),
    r"C:\Users\95959\OneDrive\Desktop\Work\AGENTS.md",
    HOT,
])
print("hot %d -> %d B; total %d B %s" % (b0, len(h.encode("utf-8")), tot, "OK" if tot <= 40960 else "OVER"))
