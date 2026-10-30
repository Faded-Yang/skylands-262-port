#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R390：createaddition 进世界（67 jar）+ 六条关键结论（尤其「tag 连锁炸」）。"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
COLD = os.path.join(P, "docs", "SOLVED-FAMILIES.md")
h = open(HOT, encoding="utf-8", errors="replace").read()
shutil.copy2(HOT, HOT + ".bak-r390-" + datetime.datetime.now().strftime("%H%M%S"))

ROWS = [
 "| 🎉🎉🎉 **【R390 `createaddition` 进世界，mods-stable 67 jar】** `WORLD_OK`（34.4s，`Loaded 2343 advancements`，`Registry loading errors: 0`）。"
 "**错误轨迹 269 → 250 → 204 → 130 → 67 → 19 → 7 → 1 → 0**（139 class）。"
 "产物 `g10/ca/createaddition-1.3.4-26.3.jar`（1.4 MB / 469 资源 / 139 编译类 / 30 垫片类 / 44 物品模型），创造页实测 **44 条**。"
 "**已用 mods-stable 本体复跑进世界 = WORLD_OK**，jar SHA-256 与实测一致。报告 `docs/port-createaddition.md` | —— | R390 |",

 "| ★★★★★ **【R390 最贵的一课：一个 tag 引用已删 id，会连锁炸掉别家 data】** "
 "`minecraft:mineable/pickaxe` 引用了已删的 `createaddition:liquid_blaze_burner` ⇒ **该 tag 整条加载失败** ⇒ "
 "`imst:igloo/main`（硬引用该 tag 的 `processor_list`）解析失败 ⇒ **`Unbound values in registry`** ⇒ **整个注册表失败**，"
 "**看起来完全像别的 mod 坏了**（这次差点误判成 imst 的问题）。"
 "**⇒ 已加离线校验器 `g10/_tag_inv.py`（扫 26.3 + mods-stable 建真实 tag 清单）+ `g10/_recipe_check.py`（逐条查配方/标签引用）。"
 "换整合包内容后必须重跑 `_tag_inv.py`** | —— | R390 |",

 "| ★★★★★ **【R390 公共垫片必须打进 mod jar】** `proc-recipe-compat.jar` 只放在**编译 classpath** 上是不够的——**运行期没人打包它** ⇒ "
 "第一次进世界 `NoClassDefFoundError: ProcessingRecipeRecipeBuilder$ProcessingRecipeFactory`。"
 "`g10/_build_ca.py` 现在把 **30 个垫片 class 一起写进 mod jar**。**⇒ 以后任何公共垫片都要随交付 jar 一起打** | —— | R390 |",

 "| ★★★★ **【R390 创造页不能用 `REGISTRATE.getAll(...)`】** 垫片的 `BlockBuilder/ItemBuilder.register()` 直接进 `BuiltInRegistries`、"
 "**没走 `doRegister`** ⇒ `BY_REGISTRY` 是空的 ⇒ **创造页空白（物品在、拿不到）**。**改成扫 `BuiltInRegistries.ITEM` 按命名空间筛** | —— | R390 |",

 "| ★★★★ **【R390 另外三条必记】** ① **`fabric.mod.json` 里 Fabric API 的 mod id 是 `fabric-api` 不是 `fabric`**（写 `fabric` → `HARD_DEP_NO_CANDIDATE` 启动即失败）；"
 "② **26.3 loot 的第二个坑**：条件对象的键要从 `condition` 改成 **`type`**（不是只把 `conditions` 数组改成单值），另外**池子上的 `name` 在 26.3 是非法键**；"
 "③ **`CompoundTag`→`ValueInput/ValueOutput` 用 `CompoundTag.CODEC` 桥**（多一层 `CABE` 子键）⇒ **14 条错一次清零且零功能降级**（存档语义不变）| —— | R390 |",

 "| ⚠ **【R390 `createaddition` 的 21 条降级（交付说明要带）】** **配方丢 75 条**（`create:*` 51 条因 26.3 schema 全变且 create jar 内**无样本可对照**整类丢弃；"
 "`liquid_burning` 14；IE·Mek 3；tag 引不到的 7）——保留 rolling 15 + charging 23 + 原版合成 28。"
 "**特斯拉线圈不能给物品充能**（垫片无 `EnergyStorage.ITEM`）；客户端渲染全删（电线不画）；Flywheel 视觉删；液体子系统整体删；"
 "网络层空壳（goggle 实时数值不刷）；环境音删；**动态结构 MovementBehaviour 删**（连接器、PEI、蓄电池不随结构工作）；"
 "展示板集成删；列车能量阈值条件删；JEI·REI·EMI·CC·Ponder 删；配置写死默认；SequencedAssembly 支持删；拆机器槽内物品不掉落；旧存档 NBT 迁移路径删 | —— | R390 |",
]

anchor = "| 阶段A 生物刷新（现成 mod） |"
h = h.replace(anchor, "\n".join(ROWS) + "\n" + anchor)
h = h.replace("（**66 jar**，进世界 `WORLD_OK`", "（**67 jar**，进世界 `WORLD_OK`")
h = h.replace("`createaddition` 269 错在案（还需 1 轮 + 数据层）",
              "**`createaddition` ✅ 已进世界**（119 轮轨迹 269→0，含 75 条配方降级）")

lines = h.split("\n")
st = next(k for k, l in enumerate(lines) if l.strip().startswith("| 族 | 结论 |"))
en = st
while en < len(lines) and lines[en].startswith("|"):
    en += 1
rows = lines[st + 2:en]
KEEP = 9
moved, kept = rows[:-KEEP], rows[-KEEP:]
with open(COLD, "a", encoding="utf-8", newline="\n") as f:
    f.write("\n\n## 搬出索引行（t31）\n\n| 族 | 结论 | 轮次 |\n|---|---|---|\n")
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
