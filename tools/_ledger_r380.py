#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R380：interiors 完整移植成功（60 jar）+ 反编译改源码的方法论 + 三个致命卡点。"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
COLD = os.path.join(P, "docs", "SOLVED-FAMILIES.md")
h = open(HOT, encoding="utf-8", errors="replace").read()
shutil.copy2(HOT, HOT + ".bak-r380-" + datetime.datetime.now().strftime("%H%M%S"))

ROWS = [
 "| 🎉🎉🎉 **【R380 `interiors` 完整移植成功，mods-stable 60 jar】** 首个 **1.20.1 Create 附属**打通："
 "`WORLD_OK 34.0s`（`logged in with entity id 13` + `Loaded 2085 advancements`）、`TITLE_SCREEN_OK` 24.9s/25.3s、"
 "`Registry loading errors: 0`、`Mixin apply failed: 0`、模型 `Missing textures: 0`。"
 "**无降级保留**：方块/物品/实体注册、**136 条配方**、55 战利品表、标签、创造栏、坐下/移动行为。"
 "报告 `docs/port-interiors.md`；源码 `work/run26/port/g6/interiors/src27/`；一键重建 `work/run26/port/g6/_all.py` | —— | R380 |",

 "| ★★★★★ **【R380 方法论转变：不再改字节码，改成「反编译→改源码→用 26.3 真 API 重新 javac」】** "
 "理由：`est_gap_263` 那 26 条「人工」**没有一条是纯改名**（`fallOn` F→D、`CompoundTag.getInt` Optional 化、"
 "`ItemStack.is(Item)` / `Entity.getCustomData` / `DyeItem.getDyeColor` 消失、`SeatBlock` 构造器换序、`use`→`useItemOn`、record 组件改名），"
 "**改字节码要动栈帧；改源码让编译器兜底**，实际一个会话做完。"
 "**流程**：CFR 0.152 反编译 23 class → 16 java → 用 i21n 表机械改名（8,254 类 / 76,563 成员）→ 人工修语义 → "
 "`javac --release 21`（classpath = 26.3.jar + 全部 libraries + create-fly + aeronautics(registrate 垫片) + fabric-api 42 子模块）→ 22 class 与原 assets/data 重打包 | —— | R380 |",

 "| ★★★★★ **【R380 三个「不报编译错但会让世界加载失败」的致命卡点】** "
 "① **registrate 垫片的 `AbstractRegistrate.register()` 是空实现**（javap `Code: 0: return`）—— `.register()` 只把 Runnable 塞进 `PENDING`，"
 "**必须显式调 `AbstractRegistrate.flush()`**。现象：53 个块只有 `queue block`、没有 `create block`，**标题照过、进世界才炸成「标签全部 missing references」**。"
 "⇒ 任何用这个 registrate 垫片的新 mod 都会踩。"
 "② **`CreativeModeTab$Output` 在 26.3 变成 protected 嵌套类型**（javap -v InnerClasses 实锤）⇒ 源码无法命名 ⇒ 标签页建空；"
 "用 Fabric `CreativeModeTabEvents.modifyOutputEvent(TAB_KEY)` 填（回调参数 `FabricCreativeModeTabOutput` 是 public）。`AllCreativeModeTabs$TabInfo` 也已消失。"
 "③ **26.3 物品模型入口是 `assets/<ns>/items/<id>.json`** —— 不生成它物品不可见、进不了创造栏（从旧 `models/item` 批量生成）| —— | R380 |",

 "| ★★★★ **【R380 1.20.1→26.3 数据层实测要点（866 条目）】** 目录改名：`recipes`→`recipe` / `loot_tables`→`loot_table` / `advancements`→`advancement` / `tags/{blocks,items}`→`{block,item}`；"
 "**配方**：Ingredient→裸字符串、`result.item`→`result.id`、**`category` 是 `building` 不是 `building_blocks`（方向易搞反）**；"
 "**进度表**：`recipe_unlocked` 的 `recipe`→**`recipes: [..]`（复数+列表）**、`requirements` 必须与 `criteria` **完全一致**；"
 "`create:block/belt_offset` 贴图在 Create 26.3 已删 ⇒ 换 `interiors:block/chair/side_top_kelp`。"
 "三重校验（对全部已装 jar 的 `assets/*/items` + `tags/item` 反查）：**136 条配方全保留、0 丢弃** | —— | R380 |",
]

anchor = "| 阶段A 生物刷新（现成 mod） |"
h = h.replace(anchor, "\n".join(ROWS) + "\n" + anchor)
h = h.replace("（**59 jar**，`TITLE_SCREEN_OK` 25.7s", "（**60 jar**，`TITLE_SCREEN_OK` 25.3s")
h = h.replace("`interiors` ≈2–2.5 人日、`create-framed` ≈3 人日已量化）",
              "**`interiors` ✅ 已进世界（首个 1.20.1 Create 附属打通，方法论已证明）**、`create-framed` 待做）")

lines = h.split("\n")
st = next(k for k, l in enumerate(lines) if l.strip().startswith("| 族 | 结论 |"))
en = st
while en < len(lines) and lines[en].startswith("|"):
    en += 1
rows = lines[st + 2:en]
KEEP = 10
moved, kept = rows[:-KEEP], rows[-KEEP:]
with open(COLD, "a", encoding="utf-8", newline="\n") as f:
    f.write("\n\n## 搬出索引行（t21）\n\n| 族 | 结论 | 轮次 |\n|---|---|---|\n")
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
