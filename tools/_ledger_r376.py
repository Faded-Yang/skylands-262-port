#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R376：remap 的 Signature 属性漏改（重大通用坑）+ 26.3 Block id 必填 + cd/ed 暂缓。"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
COLD = os.path.join(P, "docs", "SOLVED-FAMILIES.md")
h = open(HOT, encoding="utf-8", errors="replace").read()
shutil.copy2(HOT, HOT + ".bak-r376-" + datetime.datetime.now().strftime("%H%M%S"))

ROWS = [
 "| ★★★★★ **【R376 remap 必踩的 `Signature` 属性坑（通用，所有 1.21.x mod 都用得上）】** "
 "`remap_intermediary.py` **只改 Class / NameAndType / 成员引用**，**不碰 `Signature` 属性、注解、调试属性**。"
 "残留形如 `Signature: Ljava/util/function/Supplier<Lnet/minecraft/class_2248;>;` ⇒ 运行期 `NoClassDefFoundError: class_2248`，"
 "而且**在普通常量池扫描里看不到**（所以会误判成「0 处 class_ 引用」）。"
 "**修法：`tools/sweep_utf8_intermediary.py`** —— 常量池**索引不变**、只换 Utf8 值（最安全的收尾清扫）。"
 "**⇒ 以后任何 remap 之后都必须跑一次这个清扫，再判「干净」** | —— | R376 |",

 "| ★★★★★ **【R376 26.3 要求方块 `Properties` 必须带 id】** `NoClassDefFoundError` 之后暴露的下一个坎："
 "`ExceptionInInitializerError → NullPointerException: Block id not set`，这句出自 **26.3 自己的** "
 "`net/minecraft/world/level/block/state/BlockBehaviour$Properties`。"
 "⇒ 1.21.x 的 FD 附属用 FD 注册辅助建块时**没设 id** ⇒ 每处方块构造都要补 `Properties.setId(...)` 或改走 `Registry.register`。"
 "**这是源码级移植的量，不是字节码补丁能解决的**。`cultural-delights` / `ends-delight` 按**暂缓**处理 | —— | R376 |",

 "| ⚠ **【R376 纠正：cd/ed 之前根本没被 remap 过】** 扫 `_fixed\\cd-v4.jar` / `ed-v4.jar`：**24 / 38 个 class 里仍有 `net/minecraft/class_xxxx`**。"
 "上一轮「0 处 class_ 引用」的结论是在**别的产物**（v3 = 只 widen+lenient）上得到的。**⇒ 判「干净」必须扫实际要交付的那个 jar** | —— | R376 |",

 "| ✅ **【R376 新工具两件（通用）】** ① `tools/sweep_utf8_intermediary.py` —— remap 后的**收尾清扫**（Signature/注解里的类名）；"
 "② `tools/neoforge_to_fabric.py` —— **纯数据 NeoForge jar → Fabric mod jar**（读 `neoforge.mods.toml` 生成 `fabric.mod.json`，只留 `data/` + `assets/`） | —— | R376 |",
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
    f.write("\n\n## 搬出索引行（t17）\n\n| 族 | 结论 | 轮次 |\n|---|---|---|\n")
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
