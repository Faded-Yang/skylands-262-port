#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""压缩热层台账：把冗长的 R366 汉化三行合并成一行，其余旧行搬到冷层。"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
ARC = os.path.join(P, "docs", "SOLVED-FAMILIES.md")
h = open(HOT, encoding="utf-8", errors="replace").read()
b0 = len(h.encode("utf-8"))
shutil.copy2(HOT, HOT + ".bak-t7-" + datetime.datetime.now().strftime("%H%M%S"))

lines = h.split("\n")
st = next(k for k, l in enumerate(lines) if l.strip().startswith("| 族 | 结论 |"))
en = st
while en < len(lines) and lines[en].startswith("|"):
    en += 1
rows = lines[st + 2:en]

# 1) 把 R366 的三行合并成一行（长内容已在 docs\zh-cn-localization.md）
SHORT = (
    "| ✅ **【R366 汉化 100% 完成】** `tools\\lang_audit.py` 实测：en 8,628 / zh 8,850 / **缺 0（100.0%）**。"
    "来源：CFPA 汉化包 +372（xaeroworldmap +288 / xaerominimap +83）、**自译 +743**（jei 354 / sodium 105 / IPN 48 / "
    "xaerominimap 46 / ponder 40 / balm 22 / waystones 17 …）、旧 jar 合并 +218（JEI +70 / Waystones +118）、"
    "**Sable 128/128 我做**。`aeronautics`/`simulated` 上游自带全中文。"
    "工具：`merge_zhcn.py`（按 namespace 合旧 jar）、`merge_zhcn_src.py`（**带占位符校验**：有 `%1$s` 比多重集、裸 `%s` 比顺序）。"
    "译源 `work\\run26\\notes\\manual\\`。详见 `docs\\zh-cn-localization.md`。"
    "**⚠ 以后往 `mods-full` 加 mod 必须重跑 `lang_audit.py`** | —— | R366 |"
)
new_rows = [r for r in rows if "R366" not in r]
new_rows.append(SHORT)

KEEP = 8
moved, kept = new_rows[:-KEEP], new_rows[-KEEP:]
with open(ARC, "a", encoding="utf-8", newline="\n") as f:
    f.write("\n\n## 搬出索引行（t7）\n\n| 族 | 结论 | 轮次 |\n|---|---|---|\n")
    for r in moved:
        f.write(r + "\n")

out = lines[:st + 2] + kept + lines[en:]
h2 = "\n".join(out)
open(HOT, "w", encoding="utf-8", newline="\n").write(h2)
tot = sum(os.path.getsize(f) for f in [
    os.path.expanduser("~/.dsh/AGENTS.md"),
    r"C:\Users\95959\OneDrive\Desktop\Work\AGENTS.md",
    HOT,
])
print("rows %d -> %d (kept %d, moved %d); hot %d -> %d B; total %d B %s"
      % (len(rows), len(kept), len(kept), len(moved), b0, len(h2.encode("utf-8")), tot,
         "OK" if tot <= 40960 else "STILL OVER"))
