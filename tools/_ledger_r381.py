#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R381：create-framed 打通（61 jar）+ registrate 垫片 builder 空实现（更狠的静默杀手）+ 4 个未通的量化。"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
COLD = os.path.join(P, "docs", "SOLVED-FAMILIES.md")
h = open(HOT, encoding="utf-8", errors="replace").read()
shutil.copy2(HOT, HOT + ".bak-r381-" + datetime.datetime.now().strftime("%H%M%S"))

ROWS = [
 "| 🎉🎉🎉 **【R381 `create-framed` 打通，mods-stable 61 jar】** 第二个 1.20.1 Create 附属："
 "`TITLE_SCREEN_OK 23.7s` + `WORLD_OK 36.0s`（`entity id 13` / `Loaded 2085 advancements`）。"
 "**`Registry errors 0` / blockstate 异常 0 / mixin 失败 0 / 模型贴图缺失 0**。"
 "25 class→24；**313 条配方 0 丢弃**、227 战利品表、251 标签、303 物品、249 方块全部真注册。"
 "一键重建 `work/run26/port/g7/_all.py`；报告 `docs/port-framed.md` | —— | R381 |",

 "| ★★★★★ **【R381 registrate 垫片有「一整批 builder 方法是空实现」（比 `register()` 空更狠）】** javap 实锤（aeronautics 里的 shim）："
 "`AbstractBuilder.transform` / `onRegister` / `onRegisterAfter` / `lang` **全是 `return self()`**；"
 "`CreateRegistrate.connectedTextures/blockModel/itemModel` 返回空 consumer；`setCreativeTab` 空方法。"
 "**后果（编译期完全不报错）**：`.transform(slidingDoor()).simpleItem()` 里的 `simpleItem()` 从不执行 ⇒ **17 个门的物品没注册** ⇒ "
 "标题照过、**进世界才炸成 `c:dyed/*` 标签 missing references**；`.onRegister(...)` 的门行为与 CT 连接纹理也从不注册。"
 "**修法：一切注册动作必须写在 `.register()` 之后显式调用**（如 `MovementBehaviour.REGISTRY.register(...)`）| —— | R381 |",

 "| ★★★★ **【R381 数据层新增实测要点（interiors 那轮没覆盖）】** "
 "`create:deploying` / `create:item_application`：`ingredients:[a,b]` → **`target:a` + `ingredient:b`**；"
 "`create:splashing`：`ingredients:[a]` → **单数 `ingredient:a`**；熔炉 `category` 只认 `food/blocks/misc`——**不能写 `building`**（会 `Unknown element name:building`）；"
 "战利品表的 **`minecraft:block_state_property` 在 26.3 已删除** ⇒ 门桌改原版形状（`match_block{half:lower}`）；"
 "滑动门的 **`visible=` 属性在 26.3 不存在** ⇒ 变体解析失败，须剥离并去重；"
 "进度表 `display.icon` 要 `{id:...}`、`inventory_changed.items` 要 **`[{\"items\":\"x\"}]`**（ItemPredicate 对象列表）；"
 "id 改名 `c:string`→`c:strings`、`c:colorless_glass`→`c:glass_blocks/colorless`、`create:copper_nugget`→`minecraft:copper_nugget`。"
 "**校验器必须递归 fabric-api 的 `META-INF/jars/*.jar`**，否则 `c:strings` 误判缺失、误杀 34 条配方 | —— | R381 |",

 "| ⚠ **【R381 附加 4 个 mod 的量化卡点（首次 javac 实测）】** "
 "`slice-and-dice` 44 java / **65 错**，几乎全是 **Kotlin 编译产物**的 CFR 残影（`void $this$mapValues$iv;`、匿名类 `createRecipeType.type.1`）⇒ 要手写重推 6 个 Kotlin 类；**下一个最值得做**；"
 "`escalated` 修完伪声明后 **542 错**（`StateHolder#setValue` 24 / Level 可见性 22 / ponder 包搬迁 7 / ModConfig 8 / flywheel `Instance→OrientedInstance` 6）；"
 "`design-n-decor` **1869 错**（旧 Flywheel `com.jozufozu.flywheel` + porting_lib datagen 链 + `RegistryEntry→BlockEntry`）；"
 "`create-jetpack` **纯 Kotlin**（`Intrinsics`/`CollectionsKt`/解构残影，构造器成乱码）+ JiJ 内嵌 `flightlib-2.2.3`(1.20.1) 也要移植。"
 "**排序：slice-and-dice > escalated > design-n-decor > create-jetpack** | —— | R381 |",
]

anchor = "| 阶段A 生物刷新（现成 mod） |"
h = h.replace(anchor, "\n".join(ROWS) + "\n" + anchor)
h = h.replace("（**60 jar**，`TITLE_SCREEN_OK` 25.3s", "（**61 jar**，`TITLE_SCREEN_OK` 23.7s")
h = h.replace("`create-framed` 待做）", "**`create-framed` ✅ 已进世界**；剩 `slice-and-dice`(65 错, Kotlin) / `escalated`(542) / `design-n-decor`(1869) / `create-jetpack`(纯 Kotlin) 等）")

lines = h.split("\n")
st = next(k for k, l in enumerate(lines) if l.strip().startswith("| 族 | 结论 |"))
en = st
while en < len(lines) and lines[en].startswith("|"):
    en += 1
rows = lines[st + 2:en]
KEEP = 9
moved, kept = rows[:-KEEP], rows[-KEEP:]
with open(COLD, "a", encoding="utf-8", newline="\n") as f:
    f.write("\n\n## 搬出索引行（t22）\n\n| 族 | 结论 | 轮次 |\n|---|---|---|\n")
    for r in moved:
        f.write(r + "\n")
h2 = "\n".join(lines[:st + 2] + kept + lines[en:])
open(HOT, "w", encoding="utf-8", newline="\n").write(h2)

tot = sum(os.path.getsize(f) for f in [
    os.path.expanduser("~/.dsh/AGENTS.md"),
    r"C:\Users\95959\OneDrive\Desktop\Work\AGENTS.md",
    HOT,
])
print("hot %d B; 注入合计 %d B (上限 65536) %s" % (len(h2.encode("utf-8")), tot, "OK" if tot <= 65536 else "OVER"))
