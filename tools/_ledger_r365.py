#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性：把 R365（45 mod 进世界 + F 类移植实测）追加进热层台账。"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
h = open(HOT, encoding="utf-8", errors="replace").read()
b0 = len(h.encode("utf-8"))
shutil.copy2(HOT, HOT + ".bak-r365-" + datetime.datetime.now().strftime("%H%M%S"))

ROWS = [
    "| 🎉🎉🎉 **【R365 45 mod + 进世界，用户确认】** 用户原话「能进，有了部分mod」。`work\\run26\\mods-full` = **45 jar**"
    "（33 A2 类 + 核心 8 + 依赖 3 + `explorify` + `medieval-buildings`）。`启动浮岛世界.bat` 已指向它。"
    "**原始目标「启动并进入世界」至此达成并经用户目视确认** | —— | R365 |",

    "| ★★★★★ **【R365 F 类（有 Fabric 版但版本低）的实测天花板】** 对最近的 7 个（26.2 / 26.1.2）试「放宽 `fabric.mod.json` 的 minecraft 约束 + mixin `require=0`」"
    "（工具 `tools\\widen_mc_constraint.py` / `tools\\lenient_mixins.py`）：**只 2 个活**（`explorify` / `medieval-buildings`）。失败原因分三类，以后别再重复试："
    "① **`create-dragons-plus` / `create-enchantment-industry`** 引用 `com.zurrtum.create.infrastructure.fluids.FlowableFluid$Still`，要求 Create **6.0.9-4+**，我们只有 6.0.9-2 ⇒ `NoClassDefFoundError`（放宽依赖约束能过 loader，但运行期必崩）；"
    "② **`yungs-api` / `paxi`** 是 **handler 描述符错误**（`InvalidInjectionException: Invalid descriptor`），**`require=0` 救不了**（那只救「目标不存在」）；"
    "③ **`chefs-delight`** 缺 **Farmer's Delight**（原包 mod 列表里本来就没有，是坏依赖）| —— | R365 |",

    "| ★★★★ **【R365 「改 jar」路线的结论：天花板很低】** 只要 mod 引用了 26.3 里已删除/改签名的类或方法，就必须改代码 = 真源码移植。"
    "**剩余待移植的 26 个按起点版本分层**：`1.21.x` **9 个**（`natures-spirit`/`sky-villages`/`when-dungeons-arise`/`dragonlib`/`lodestonelib`/`cultural-delights`/`ends-delight`/`immersive-structures`/`strayed-fates-forsaken`）"
    "→ 只需 1.21→26.3（我们有 Sable/Aeronautics 的完整经验）；`1.20.1` **11 个**（`createaddition`/`create-jetpack`/`copycats`/`interiors`/`slice-and-dice`/`escalated`/`create-framed`/`create-ore-excavation`/`create-design-n-decor`/`create-railways-navigator`/`create-sky-village`）"
    "→ 还要加 1.20→1.21；`只有 NeoForge` **40 个** → 再加 loader 迁移。**建议顺序：先 1.21.x 那 9 个** | —— | R365 |",

    "| ⚠ **【R365 地形仍未做真浮岛】** 地形代理的「真浮岛」密度式（`tools\\wg_realislands.py`：`min(cap, mask-0.024*depth)` + 30 个 ore `height_range` 抬到 150..340）**已实现但没验证成功**——"
    "用 **mod jar** 跑 `runServer` 时包被加载（`Found new data pack`、0 解析错误）但地形不生效；**同一套 JSON 放进世界 `datapacks\\` 就生效**。"
    "⇒ **下一轮必须改用「拷世界 + 往 `datapacks\\` 放 zip」验证**，别走 mod jar。当前玩家世界仍是「切地版」（薄壳岛 2~5 格、无矿）| —— | R365 |",
]

anchor = "| 阶段A 生物刷新（现成 mod） |"
if anchor in h:
    h = h.replace(anchor, "\n".join(ROWS) + "\n" + anchor)
else:
    h += "\n" + "\n".join(ROWS) + "\n"
open(HOT, "w", encoding="utf-8", newline="\n").write(h)
tot = sum(os.path.getsize(f) for f in [
    os.path.expanduser("~/.dsh/AGENTS.md"),
    r"C:\Users\95959\OneDrive\Desktop\Work\AGENTS.md",
    HOT,
])
print("hot %d -> %d B; total %d B %s" % (b0, len(h.encode("utf-8")), tot, "OK" if tot <= 40960 else "OVER"))
