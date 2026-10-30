#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R384：汉化审计工具假阴性 bug 修复（之前「100%」是假的）+ 两个损坏 lang 文件 + 真 100%。"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
COLD = os.path.join(P, "docs", "SOLVED-FAMILIES.md")
h = open(HOT, encoding="utf-8", errors="replace").read()
shutil.copy2(HOT, HOT + ".bak-r384-" + datetime.datetime.now().strftime("%H%M%S"))

ROWS = [
 "| ★★★★★ **【R384 `lang_audit.py` 有假阴性 bug —— 之前几次「汉化 100%」是假的】** "
 "旧版把 `en_us` 与 `zh_cn` 的解析放在**同一个 try** 里，**任一失败就 `continue` 跳过整个 namespace** "
 "⇒ **损坏的 `zh_cn.json` 会让它从报告里彻底消失**，表现为「100% 覆盖」。"
 "实测踩到：`createframed` 的 `zh_cn.json` 有 `// Translator's note:` 行注释（JSON 不允许），`ends_delight` 带 **UTF-8 BOM** "
 "⇒ 两个 namespace 共 **386 条缺口被隐藏**（真覆盖 96.0%，不是 100%）。"
 "**修法**：en/zh **独立解析**；zh 解析失败时记「文件损坏」并单独列出；**看到 100% 必须怀疑工具** | —— | R384 |",

 "| ✅ **【R384 两个损坏 lang 文件的成因与修法（`tools/fix_broken_lang.py`）】** "
 "① **行注释**：`//` 必须**在字符串感知的前提下**剥（不能简单按 `//` 切，译文里可能含 `//`）；"
 "② **UTF-8 BOM**：`EF BB BF` 开头 ⇒ 用 `utf-8-sig` 解码。**改前备份 `.bak-langfix`，改后必须重新 `json.loads` 验证** | —— | R384 |",

 "| 🎉 **【R384 汉化真 100%（65 jar）】** 修完两个坏文件 + 补齐最后 40 条（farmersdelight 32 / chefsdelight 4 / createframed 3 / corndelight 1）"
 "⇒ `lang_audit.py` 实测 **en 9,772 / zh 9,996 / 缺 0**，39 个 namespace 全部达标，无损坏文件 | —— | R384 |",
]

anchor = "| 阶段A 生物刷新（现成 mod） |"
h = h.replace(anchor, "\n".join(ROWS) + "\n" + anchor)
h = h.replace("汉化已回到 100%（8,808/9,030，补了 DA 14 + mss 7 + modmenu 1）",
              "**汉化真 100%（en 9,772 / zh 9,996 / 缺 0，R384 修完审计工具假阴性后重测）**")

lines = h.split("\n")
st = next(k for k, l in enumerate(lines) if l.strip().startswith("| 族 | 结论 |"))
en = st
while en < len(lines) and lines[en].startswith("|"):
    en += 1
rows = lines[st + 2:en]
KEEP = 9
moved, kept = rows[:-KEEP], rows[-KEEP:]
with open(COLD, "a", encoding="utf-8", newline="\n") as f:
    f.write("\n\n## 搬出索引行（t25）\n\n| 族 | 结论 | 轮次 |\n|---|---|---|\n")
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
