# HAND-TEST CHECKLIST —— skylands-262（MC 26.3 / Fabric 0.19.5 / Java 25）

> 用途：用户照单逐项手测，快速反馈「哪项不符合预期」。

> 格式约定：`✅ 正常` / `⚠️ 降级可接受` / `❌ 不符合预期（请附截图 + `latest.log` 相关行 + 你执行的命令）`。

> 前置：创造模式 + 开启作弊；新建世界即可（需要结构验证时可 `tp` 到 `/locate` 返回坐标）。

> 通用判据（每轮都先看）：标题可进、进世界 0 crash、`Registry loading errors=0`、语言无 `Unable to load languages`。

---

## 0. 反馈模板（复制填写）

```
模块/项：<例如 TFMG-1>
结果：✅ / ⚠️ / ❌
执行：<命令或操作>
实际：<看到什么，与预期差在哪>
证据：<截图路径 / latest.log 关键行>
```

---

## 1. Create 基础 / 物理交互

| # | 怎么测 | 预期 | 已知降级（不算失败） |
|---|---|---|---|
| C-1 | `/give @s create:cogwheel`、`/give @s create:shaft`；把 shaft/cogwheel 放在一起，用创造动力源或手摇测试旋转 | 方块可放置、齿轮/轴有旋转动画、相邻动力可传递 | create-fly 为 26.3 补丁 fork；极个别 Create 附属的 ponder/动画可能缺失 |
| C-2 | `/give @s create:mechanical_press`；放在动力轴上并供能，放入物品 | 机器响应动力、可执行压制（或至少可放置/有状态） | 部分机器只保证「可放置/可见」，行为未逐台验证 |
| C-3 | 把 Create 方块放到 sable/浮空结构上，移动结构 | 方块跟随结构移动（物理交互正常） | simulated 实体渲染/部分物理混入仍为已知降级；若方块不跟随请记录结构名 |
| C-4 | `/give @s create:wrench`，右键方块 | 扳手可旋转/拆卸（按 Create 逻辑） | 个别附属方块只注册了静态模型，扳手无反应 |

---

## 2. 装饰：createdeco / Design-n-Decor

| # | 怎么测 | 预期 | 已知降级（不算失败） |
|---|---|---|---|
| D-1 | `/give @s createdeco:andesite_bars`、`createdeco:black_placard`、`createdeco:zinc_support_wedge`、`createdeco:blue_brick_stairs`、`createdeco:andesite_trapdoor`；逐个 `/setblock` | 物品名中文、方块可放、模型/贴图正常、按 F3 对准方块确认目标方块一致 | createdeco 389/389 纯装饰；无 BE/交互/动画；wedge/support 等形状为近似 |
| D-2 | `/give @s dndecor:amber_cogwheel`、`dndecor:amber_display_board`、`dndecor:amber_container`；三轴旋转放置 | 可放置、三个轴向变体有模型 | DnD 774/846；velvet 32 + 杂项 40 永久跳过；无 BE/交互；部分模型/贴图近似 |
| D-3 | 装饰方块上叠放/破坏、检查碰撞 | 不崩溃、掉落正常 | 部分方块用整块碰撞（形状近似） |

---

## 3. TFMG（436 方块全量）

| # | 怎么测 | 预期 | 已知降级（不算失败） |
|---|---|---|---|
| T-1 | `/give @s tfmg:lithium_torch`、`tfmg:aluminum_block` | 中文名「锂火把」「铝块」；可拿在手上 | 无配方/战利品/成就数据 |
| T-2 | `/setblock ~ ~ ~ tfmg:zinc_frame`；`/setblock ~ ~1 ~ tfmg:zinc_truss`；`/setblock ~ ~2 ~ tfmg:machine_input`；`/setblock ~ ~3 ~ tfmg:fossilstone` | 4/4 放置成功；按 F3 对准方块确认目标方块一致；模型正常 | 机器/BE/流体方块全部为**静态装饰**（无功能、无 BE、整块碰撞） |
| T-3 | 尝试给机器接动力/流体 | 不崩溃即可 | 无机器行为、无流体逻辑；16 个无自有模型的方块用 vanilla air/barrier 兜底（视觉降级） |

---

## 4. create_connected

| # | 怎么测 | 预期 | 已知降级（不算失败） |
|---|---|---|---|
| CC-1 | `/give @s create_connected:brake`、`create_connected:brass_chute`、`create_connected:fluid_vessel`、`create_connected:andesite_encased_cross_connector`；逐个放置 | 可放置、模型正常、中文名可用 | 本件为 **decorative only, no behaviour**（fabric.mod.json 原话）；物流/传动/连接行为全无 |
| CC-2 | 把 brass_chute/fluid_vessel 接到 Create 物流/流体系统 | 不崩溃即可 | 不参与 Create 物流/流体网络 |

---

## 5. create_submarine / create_high_seas / create_abyss

| # | 怎么测 | 预期 | 已知降级（不算失败） |
|---|---|---|---|
| S-1 | `/give @s create_submarine:ballast_tank`、`create_high_seas:anchor`、`create_high_seas:boat_engine`；放置 | 可放置/可读回，中文名可用 | 全部为 fallback cube_all；流体/BE/潜水控制/声呐/压载/氧气系统全无 |
| S-2 | 尝试组装潜艇/驾驶 | 不崩溃即可 | 无控制行为（43 方块静态广度） |

---

## 6. createpropulsion

| # | 怎么测 | 预期 | 已知降级（不算失败） |
|---|---|---|---|
| P-1 | `/give @s createpropulsion:cable`、`createpropulsion:advanced_tilt_adapter`、`createpropulsion:platinum_fluid_tank`；放置 | 可放置/读回，中文名可用 | 全部 fallback cube_all；推进器/引擎/线缆/铂系加工/流体全无 |
| P-2 | 把 cable 接动力、tilt_adapter 装结构 | 不崩溃即可 | 无推进/线缆行为 |

---

## 7. copycats（reduced）

| # | 怎么测 | 预期 | 已知降级（不算失败） |
|---|---|---|---|
| K-1 | `/give @s copycats:copycat_base`、`copycats:copycat_block`、`copycats:copycat_beam`；放置 | 可放置/读回 | **平铺 cube_all**；copycat 模型/贴图/形状/动能/多重状态系统全无（本件只保证方块在） |
| K-2 | 用 copycat 方块贴到别的方块上 | 不崩溃即可 | 不会复制外观/形状 |

---

## 8. 食物 ×4（reduced）

| # | 怎么测 | 预期 | 已知降级（不算失败） |
|---|---|---|---|
| F-1 | `/give @s culturaldelights:avocado`；`/setblock ~ ~ ~ culturaldelights:avocado_crate` | 中文名、可放置/读回 | 无食物效果/作物/树/配方/成就 |
| F-2 | `/give @s minersdelight:cave_carrot`；`/setblock ~ ~ ~ minersdelight:cave_carrot_crate`、`minersdelight:copper_pot` | 中文名「洞穴萝卜」、可放置 | 无食用效果/烹饪/BE |
| F-3 | `/give @s mynethersdelight:bullet_pepper`；`/setblock ~ ~ ~ mynethersdelight:blackstone_cooking_pot` | 中文名、可放置 | 无烹饪/BE/交易；powdery 木组未注册（Create 运行时生成器规避） |
| F-4 | `/give @s abnormals_delight:cherry_cookie`、`abnormals_delight:copper_knife`；放置 `abnormals_delight:aspen_cabinet` | 中文名「樱桃曲奇/铜刀」、可放置 | 无食物效果/刀板/锅交互 |

---

## 9. 任务系统（sky262-quests）

| # | 怎么测 | 预期 | 已知降级（不算失败） |
|---|---|---|---|
| Q-1 | 按 **J** 打开任务书 | 22 章 / 543 任务；按钮「关闭/提交/检查/领取」中文；描述多行可读 | 极少数 titleItem 回退英文物品名；跨章节依赖线未做 |
| Q-2 | 完成一个任务 → 提交 → 领取；关闭重开界面 | 进度/提交/领取状态正确刷新；重进世界持久化 | 专用服务器跨端同步为 S2C 实现，单人集成服正常；按钮实时刷新需手验 |
| Q-3 | 检查锁定任务提示 | 锁定条件/提示中文 | 依赖线（A①）未做，部分任务可能只显示锁定不显示前置链 |

---

## 10. Natures Spirit：群系 / 植被 / 掉落

| # | 怎么测 | 预期 | 已知降级（不算失败） |
|---|---|---|---|
| N-1 | `/locate biome natures_spirit:redwood_forest`；`/locate biome natures_spirit:blooming_highlands` | 返回坐标；`tp` 后可见红杉林/高原植被与地表 | 树形使用 26.3 原版 placer（自定义树形降级）；resourcepacks 移除 |
| N-2 | `/give @s natures_spirit:aspen_planks`、`natures_spirit:redwood_planks`；放置 | 中文名/可放置 | 部分自定义方块只有资源+基础注册 |
| N-3 | `/loot give @s loot natures_spirit:blocks/aspen_slab` | 聊天显示获得物品；背包可见 | 少数表引用未注册旧 id 时可能空表 |
| N-4 | `/advancement grant @s only natures_spirit:recipes/building_blocks/alluaudia_bundle` | 成功提示/成就面板出现 | shoot_coconut 成就跳过；2 个原版覆盖成就未恢复 |

---

## 11. 结构：hangars / 浮空岛 / no-void

| # | 怎么测 | 预期 | 已知降级（不算失败） |
|---|---|---|---|
| R-1 | `/locate structure igcah:plains_hangar`（或 birch_hangar/savannah_hangar）；`tp` 到坐标 | 返回坐标；机库完整木构、可进入 | loot_table 已移除（机库箱子无战利品） |
| R-2 | `/sky262_islands spawn`；观察浮空岛 | 日志 `loaded template ... placed ok=true`；命中 levitite/andesite 等方块 | 岛为原版 StructureTemplate 放置，**不是 sable 物理 sublevel**，不会随物理体系移动；概率硬编码 1/4096 |
| R-3 | `/locate structure minecraft:village_plains`；`tp` 查看 | 结构可定位/生成，且不在虚空（no-void 覆盖生效） | reduced 纯数据；若村庄仍在虚空上方/被隐藏属已知限制（记录坐标） |
| R-4 | `/locate structure minecraft:igloo` 等原版结构 | 可定位 | no-void 故意隐藏部分原版结构定位（这是行为本身） |

---

## 12. 流体：CEI / DragonsPlus

| # | 怎么测 | 预期 | 已知降级（不算失败） |
|---|---|---|---|
| L-1 | `/setblock ~ ~ ~ create_enchantment_industry:experience`；`/give @s create_enchantment_industry:experience_bucket`；倒出/回收 | 流体方块存在、桶可倒/装、读回一致 | 流体行为（流动/交互）可能不完整；无 CEI 机器行为 |
| L-2 | `/setblock ~ ~ ~ create_dragons_plus:dragon_breath`；`/give @s create_dragons_plus:dragon_breath_bucket` | 流体方块/桶可用 | DP 保持 live 旧件（create 版本下限原因）；部分流体交互降级 |

---

## 13. 流体燃料兼容壳（仅加载）

| # | 怎么测 | 预期 | 已知降级（不算失败） |
|---|---|---|---|
| U-1 | 打开 Mods 列表/搜索 `portable_engine_liquid_fuel`、`createliquidfuel` | 两个 mod 均在列（版本 2.0.0-26.3-shell / 3.0.0-26.3-shell） | **只有壳：无物品/方块/数据/行为**（占位，待行为移植） |
| U-2 | 给便携引擎/烈焰燃烧器接液体（若你会搭） | 不崩溃即可 | 无燃料兼容行为；不做功能判定 |

---

## 14. 记录建议

- 每模块至少测 1 项，重点模块（TFMG/装饰/NS/结构）测 2–3 项；
- ❌ 项请附：命令、截图、`latest.log` 中相关行（尤其 `Registry loading errors` / `Failed to parse` / `Missing model`）；
- 已知降级（⚠️）请只记录「符合预期」或「比预期更差」两种情况，不必逐条复述本文档。