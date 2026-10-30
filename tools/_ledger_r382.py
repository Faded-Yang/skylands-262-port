#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R382：精确剩余清单（46/110 覆盖，64 未覆盖）+ diff_pack.py 工具。"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
COLD = os.path.join(P, "docs", "SOLVED-FAMILIES.md")
h = open(HOT, encoding="utf-8", errors="replace").read()
shutil.copy2(HOT, HOT + ".bak-r382-" + datetime.datetime.now().strftime("%H%M%S"))

ROWS = [
 "| ★★★★★ **【R382 精确剩余清单：46 / 110 已覆盖，64 未覆盖（不再是估算）】** 新工具 `tools/diff_pack.py`："
 "**从原包每个 jar 里读真实 mod id**（Fabric: `fabric.mod.json`；NeoForge: `META-INF/neoforge.mods.toml`），再与已装 jar 的 mod id 取差集。"
 "**踩了三个匹配 bug，以后别重犯**：① **不能用 namespace 兜底** —— `minecraft` / `create` 是公共 ns，几乎所有 jar 都有 ⇒ 全误判成已覆盖；"
 "② **NeoForge TOML 的 `[[dependencies]]` 段也有 `modId=\"minecraft\"`** ⇒ 必须只取 `[[dependencies` **之前**的 `modId`；"
 "③ id 比对要**去掉 `-` 和 `_`** 再比（`cloth_config` vs `cloth-config`）。"
 "**剩余 64 个分类**：Create 附属 ~22 / Aeronautics 附加 ~5 / Farmer's Delight 系食物 ~8 / 库 ~10 / FTB 链 4 / Sophisticated 3 / 结构 ~4 / Sable 兼容 ~4 / 其他 ~4 | —— | R382 |",
]

anchor = "| 阶段A 生物刷新（现成 mod） |"
h = h.replace(anchor, "\n".join(ROWS) + "\n" + anchor)
h = h.replace("F+B·N 剩 ~48**", "**精确剩余 64 个（46/110 已覆盖，用 `tools/diff_pack.py` 逐 jar 读 mod id 算出）**")

lines = h.split("\n")
st = next(k for k, l in enumerate(lines) if l.strip().startswith("| 族 | 结论 |"))
en = st
while en < len(lines) and lines[en].startswith("|"):
    en += 1
rows = lines[st + 2:en]
KEEP = 9
moved, kept = rows[:-KEEP], rows[-KEEP:]
with open(COLD, "a", encoding="utf-8", newline="\n") as f:
    f.write("\n\n## 搬出索引行（t23）\n\n| 族 | 结论 | 轮次 |\n|---|---|---|\n")
    for r in moved:
        f.write(r + "\n")
h2 = "\n".join(lines[:st + 2] + kept + lines[en:])
open(HOT, "w", encoding="utf-8", newline="\n").write(h2)

tot = sum(os.path.getsize(f) for f in [
    os.path.expanduser("~/.dsh/AGENTS.md"),
    r"C:\Users\95959\OneDrive\Desktop\Work\AGENTS.md",
    HOT,
])
print("hot %d B; 注入合计 %d B %s" % (len(h2.encode("utf-8")), tot, "OK" if tot <= 65536 else "OVER"))
