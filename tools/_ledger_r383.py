#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R383：FD 系 +4（65 jar）+ 五条关键修正（尤其 Block/Item id 必须前置）。"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
COLD = os.path.join(P, "docs", "SOLVED-FAMILIES.md")
h = open(HOT, encoding="utf-8", errors="replace").read()
shutil.copy2(HOT, HOT + ".bak-r383-" + datetime.datetime.now().strftime("%H%M%S"))

ROWS = [
 "| 🎉 **【R383 FD 系 +4，mods-stable 65 jar】** 新增 `FarmersDelight-26.3-3.6.28+refabricated`（官方） / `chefsdelight-1.0.6-26.3` / "
 "`corndelight-1.0.0-26.3` / `ends_delight-2.6-26.3`。**65 jar 交付物本体再跑进世界通过**：`entity id 5` / `Loaded 2343 advancements` / "
 "`Registry errors 0` / mixin 失败 0 / `Loading 144 mods`。降级见 `docs/port-delight.md` §4 | —— | R383 |",

 "| ★★★★★ **【R383 26.3 硬要求：方块/物品的 `Properties` 必须在 `new Block()/new Item()` **之前**带 id】** "
 "不只是方块 —— **`Item` 构造器会调 `itemIdOrThrow()` 并拿它当 `DataComponentInitializers` 的 key**，"
 "**占位 id 会把物品模型/组件带歪 ⇒ 「先注册后补 id」整体不可行**。"
 "**定下的修法**：`Reg.pb/pi` 从 **ThreadLocal 名字栈**补 id + 注册助手 push/pop（`work/run26/port/g8/_idfix.py`，可复用） | —— | R383 |",

 "| ★★★★★ **【R383 用「Fabric 版 + 从 26.2 反编译重编」比 1.21.1 移植便宜一个数量级】** 原包 6 个 FD 附属**全是 NeoForge 版**，"
 "但其中 **4 个在 Modrinth 有 Fabric 构建**，`chefsdelight` 甚至有 **26.2 Fabric 官方构建**。"
 "**⇒ 动手前先查「同 mod 有没有更接近 26.3 的 Fabric 构建」，别从 1.21.1 硬啃** | —— | R383 |",

 "| ★★★★ **【R383 两个会让「编得过但运行期炸」的流水线 bug】** ① **`g7/cp_join.txt` 里混着 1.21.1 的 client jar**"
 "（`libraries/net/minecraft/client/1.21.1-*`）⇒ javac 把 26.3 已删的类解析到 1.21.1 上，**编得过、运行期 `NoClassDefFoundError`**"
 "（corn 的 `ItemNameBlockItem` 实测炸过）；② **`g7/map.json` 是 intermediary→1.21.1 名**（1727/8254 在 26.3 不存在），"
 "且**内类 key 是 `$` 形式而 CFR 输出 `.` 形式** ⇒ 会产出 `BlockBehaviour.LootItemRandomChanceWithEnchantedBonusCondition1` 这种垃圾。"
 "**新流水线**：`g8/_rewrite26.py` + 自动推导的 `map_121_263.json`（**612 条**搬迁，`_mkmap.py`）+ `g8/_javac8.py`（显式剔除 1.21.1 client） | —— | R383 |",

 "| ★★★★ **【R383 数据层再补五条 + Fabric API 26.3 删除项】** 战利品条件 **`conditions:[]` → 单数 `condition`** 且条件对象用 **`type`** 键；"
 "`block_state_property` 已删；**Ingredient 的 tag 是 `\"#tag\"` 裸串**（对象形态报 `No key fabric:type`），"
 "多候选要 `{\"fabric:type\":\"fabric:any\",\"ingredients\":[...]}`；worldgen 目录 **`configured_feature/` → `feature/`**，"
 "FD 的 `wild_crop` → **`in_order`**；`c:` 约定标签改名（`c:foods/vegetables`→`c:foods/vegetable` 等）；渲染层改用方块模型 **`render_type`**。"
 "**Fabric API 26.3 删了 `FabricItemGroup` / `BlockRenderLayerMap` / `CompostingChanceRegistry` / `FuelRegistry`** | —— | R383 |",

 "| ⚠ **【R383 `culturaldelights` 卡在「26.3 把树整套重做」，不是改名能解决的】** 编译到 40 错：**`ConfiguredFeature` 类整个不存在**、"
 "`TreeGrower` 变 **final 且无公开构造器**、`SaplingBlock` 构造器 **protected**、`LeavesBlock` 要多一个 `AmbientLeavesBlockSoundPlayer`、"
 "`DirectionProperty` / `StrippableBlockRegistry` / `TradeOfferHelper` **全删**。"
 "`mynethersdelight`（97 类）同形态但更大；`minersdelight` / `abnormals_delight` Modrinth **只有 NeoForge/Forge 构建**，要先做 `net.neoforged` 垫片 | —— | R383 |",
]

anchor = "| 阶段A 生物刷新（现成 mod） |"
h = h.replace(anchor, "\n".join(ROWS) + "\n" + anchor)
h = h.replace("（**61 jar**，`TITLE_SCREEN_OK` 23.7s", "（**65 jar**，进世界 `WORLD_OK` / `entity id 5` / `Loaded 2343 advancements`")
h = h.replace("精确剩余 64 个", "精确剩余 60 个")

lines = h.split("\n")
st = next(k for k, l in enumerate(lines) if l.strip().startswith("| 族 | 结论 |"))
en = st
while en < len(lines) and lines[en].startswith("|"):
    en += 1
rows = lines[st + 2:en]
KEEP = 9
moved, kept = rows[:-KEEP], rows[-KEEP:]
with open(COLD, "a", encoding="utf-8", newline="\n") as f:
    f.write("\n\n## 搬出索引行（t24）\n\n| 族 | 结论 | 轮次 |\n|---|---|---|\n")
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
