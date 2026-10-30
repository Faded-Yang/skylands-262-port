#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R375：cultural-delights 定位结论 + ends-delight 待测 + 下一批（11 个 nf_ref=0）。"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
COLD = os.path.join(P, "docs", "SOLVED-FAMILIES.md")
h = open(HOT, encoding="utf-8", errors="replace").read()
shutil.copy2(HOT, HOT + ".bak-r375-" + datetime.datetime.now().strftime("%H%M%S"))

ROWS = [
 "| ⚠ **【R375 `cultural-delights` 的定位（别重查）】** `mods-stable(49) + FarmersDelight-26.3-3.6.28`（**只加 FD**）⇒ ✅ `WORLD_OK`"
 " ⇒ **FD 26.3 本身没问题、依赖可满足**。再叠加 `cd-v4` ⇒ ❌ **启动期静默挂死**：日志停在 `[Render thread/INFO]: Sable loaded!`，"
 "**无异常、无 crash-report、无 registry 报错**，200s 超时被杀。"
 "上一轮的 `class_2248` 已被「以 mods-stable 为基线 + `launch.py` 权威同步」排除（**不是旧 jar 残留**）。"
 "**下一步**：`-Xlog:class+load`（写文件）/ `jstack` 看卡在哪个 `<clinit>`；若是 4 个作物 `configured_feature` 则逐类型转，"
 "**若卡在 Sable 相关类就先放弃**（mixin 冲突，不值得耗）。**每个静默挂死最多 2 次尝试就转下一个** | —— | R375 |",

 "| ⏳ **【R375 `ends-delight` 已备未测】** `port\_fixed\ed-v4.jar` 已生成；测法同 `staging-fd`（需同时加 FarmersDelight 26.3） | —— | R375 |",

 "| ★★★★ **【R375 下一批：11 个 `nf_ref=0` 的 NeoForge mod 是快速提量机会】** 上轮扫描结论：原包 112 个 NeoForge jar 里 "
 "**`nf_ref=0` 的 11 个**（`Explorify` / `Geophilic` / `Structory` 系 / `gadgets-and-gizmos` 等）**不需要 remap、不需要改 API，只换入口**。"
 "**手法**：纯数据 mod（0 class）最简单 —— 只留 `fabric.mod.json` + `data/` + `assets/`，**剥掉所有 class 与内嵌库**，当数据包 jar 用；"
 "其余用 `fix_accesswidener.py`（AW 头要 official）+ `fix_fabric_api_dep.py`（`fabric`→`fabric-api`）+ `widen_mc_constraint.py` + `lenient_mixins.py` + `convert_121_data.py`。"
 "**每个单独 staging 测**，标题+进世界都过才 promote；**每 promote 一个就复跑一次 `mods-stable`** | —— | R375 |",
]

anchor = "| 阶段A 生物刷新（现成 mod） |"
h = h.replace(anchor, "\n".join(ROWS) + "\n" + anchor)

lines = h.split("\n")
st = next(k for k, l in enumerate(lines) if l.strip().startswith("| 族 | 结论 |"))
en = st
while en < len(lines) and lines[en].startswith("|"):
    en += 1
rows = lines[st + 2:en]
KEEP = 10
moved, kept = rows[:-KEEP], rows[-KEEP:]
with open(COLD, "a", encoding="utf-8", newline="\n") as f:
    f.write("\n\n## 搬出索引行（t16）\n\n| 族 | 结论 | 轮次 |\n|---|---|---|\n")
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
