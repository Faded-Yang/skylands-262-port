#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""应急：热层台账超预算被尾部截断。把「已解族索引」里较旧的行整段搬进冷层，只留最近 8 行 + 指针。"""
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
shutil.copy2(HOT, HOT + ".bak-t9-" + datetime.datetime.now().strftime("%H%M%S"))

lines = h.split("\n")
st = next(k for k, l in enumerate(lines) if l.strip().startswith("| 族 | 结论 |"))
en = st
while en < len(lines) and lines[en].startswith("|"):
    en += 1
rows = lines[st + 2:en]
KEEP = 8
moved, kept = rows[:-KEEP], rows[-KEEP:]
with open(COLD, "a", encoding="utf-8", newline="\n") as f:
    f.write("\n\n## 搬出索引行（t9 应急压缩）\n\n| 族 | 结论 | 轮次 |\n|---|---|---|\n")
    for r in moved:
        f.write(r + "\n")

# 表头加一句指针
hdr = "> 动手前扫一眼；精确修法在 `docs\\fix-*.md`（26.3）。**不要再去 `API-1.21.11.md` 找签名修法**。"
new_hdr = (hdr + "\n> 更早的已解族整段在 `docs\\SOLVED-FAMILIES.md`（搜「搬出索引行」）。")
out = lines[:st + 2] + kept + lines[en:]
txt = "\n".join(out).replace(hdr, new_hdr, 1)
open(HOT, "w", encoding="utf-8", newline="\n").write(txt)

tot = sum(os.path.getsize(f) for f in [
    os.path.expanduser("~/.dsh/AGENTS.md"),
    r"C:\Users\95959\OneDrive\Desktop\Work\AGENTS.md",
    HOT,
])
print("moved %d rows; hot %d -> %d B; total %d B %s"
      % (len(moved), b0, len(txt.encode("utf-8")), tot, "OK" if tot <= 40960 else "STILL OVER"))
