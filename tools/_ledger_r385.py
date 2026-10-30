#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R385：g9 零进展但三条订正 + 关键结论（卡点不是 Create 版本，是 MC 26.1.2→26.3）。"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
COLD = os.path.join(P, "docs", "SOLVED-FAMILIES.md")
h = open(HOT, encoding="utf-8", errors="replace").read()
shutil.copy2(HOT, HOT + ".bak-r385-" + datetime.datetime.now().strftime("%H%M%S"))

ROWS = [
 "| ⚠ **【R385 g9 零进展（仍 65 jar），但三条订正必须记住】** ① **`create-enchantment-industry` 只有 26.1.2 一个 26.x 世代**"
 "（2.5.1/2.5.2/-b/-c），**全部要求 `create >=6.0.9-4` 且强依赖 `create-dragons-plus`** ⇒ 「改用更低版本」这条路不存在（再往下只有 1.21.11/1.20.1）；"
 "② **`aeroworks` 根本没有 Fabric 构建**（`P26k79kP` 12 个版本 loaders 全是 `neoforge`）⇒ 之前归「高优先」是错的，应归「需 NeoForge 垫片」；"
 "③ 原包 114 个 jar 的真实 project id 已全部反查出来（`work/run26/port/g9/_pack/modrinth.index.json`，含 sha1+URL） | —— | R385 |",

 "| ★★★★★ **【R385 关键结论：EI/DP 的卡点不是 Create 版本，是 MC 26.1.2→26.3】** "
 "`FlowableFluid$Still/Flowing` 确认在 6.0.9-2 里**不存在**（6.0.9-2 里叫 `FluidEntry$Still/$Flowing`，构造器 private）—— "
 "但 `_scanrefs.py` 实测 **EI/DP 对 Create 的类级缺口只有这 2 个类**（已重建 `g9/_shim/fluid-compat.jar`，2 类，编译 0 错）。"
 "真正卡住的是它们是 **26.1.2 世代源码**（既不是 intermediary、也不是 1.21.1）⇒ **g8 的 `map_121_263.json` 帮不上忙**，必须对着 26.3.jar 逐族改："
 "**`CriterionTrigger.Listener` 整套被删**（只能降级 code-only）、`RecipeAccess` 只剩 propertySet/stonecutterRecipes、`RecipeMap.create` 改吃 `HolderLookup`、"
 "`EntityType.SHEEP`→`EntityTypes.SHEEP`、颜色方块→`ColorCollection`、`BlockEntityRenderers.register` 变 private、"
 "Fabric 附件 `Entity` 不再声明 `AttachmentTarget`、`ValueOutput.store`/`PoseStack.mulPose`/`placeItemBackInInventory` 签名全变。"
 "**进度：DP 391→87、EI 522→202**（删两边 JEI 集成 + 修 136 处 CFR 滥加 `(Object)` 强转 + 4 处嵌套类型前向引用 + 包搬迁 + 战利品 `ConstantValue`→`Holder.direct`）| —— | R385 |",

 "| ★★★★ **【R385 EI+DP 是「成对」移植，且还要 1.5–2 个完整轮次】** "
 "15 个 API 族、400+ 错。**不建议在没有 DP 的情况下单独硬推 EI**（运行时必然缺类）。"
 "**下轮最划算的顺序**：先批量改「同名但签名变了」的族（`mulPose` 12 / `store` 18 / `placeItemBackInInventory` 8 / `add(Object[])` 6），再逐个清 symbol。"
 "**可复用资产**（`work/run26/port/g9/`）：`_mr.py`/`_deps.py`（按 project id 查 Modrinth）、`_scanrefs.py`（class 级缺口）、"
 "`_javac9.py`+`_jar9.py`、**`_auto_cast.py`（按错误行批量去 CFR 的 `(Object)`，两轮修 136 处，最省力）**、`_errs.py`/`_blocks.py`（错误直方图） | —— | R385 |",
]

anchor = "| 阶段A 生物刷新（现成 mod） |"
h = h.replace(anchor, "\n".join(ROWS) + "\n" + anchor)
h = h.replace("剩 `slice-and-dice`(65 错, Kotlin) / `escalated`(542) / `design-n-decor`(1869) / `create-jetpack`(纯 Kotlin) 等）",
              "剩 5 个 1.20.1 目标（`createaddition`/`copycats`/`escalated`/`create-jetpack`/`railways-navigator`，**已验证 1.20.1 能通**）+ "
              "EI/DP 成对 400+ 错（还要 1.5–2 轮）+ 4 个无 Fabric 构建需 NeoForge 垫片）")

lines = h.split("\n")
st = next(k for k, l in enumerate(lines) if l.strip().startswith("| 族 | 结论 |"))
en = st
while en < len(lines) and lines[en].startswith("|"):
    en += 1
rows = lines[st + 2:en]
KEEP = 9
moved, kept = rows[:-KEEP], rows[-KEEP:]
with open(COLD, "a", encoding="utf-8", newline="\n") as f:
    f.write("\n\n## 搬出索引行（t26）\n\n| 族 | 结论 | 轮次 |\n|---|---|---|\n")
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
