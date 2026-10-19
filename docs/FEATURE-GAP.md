# 特性缺口清单（wiki / 注册表侧）—— FEATURE-GAP

> 目标：给用户一份「原版 Create 航空学 × 浮空群岛 vs 我们的 26.3 交付件」的详细特性对照。
> 数据来源：① mcmod 页面（Create `class/2021` 及航空学/Simulated 词条）② `tools/diff_pack.py`（原包 112 jar vs mods-stable 71 jar）③ 原包 `create-aeronautics-bundled-1.21.1-1.3.2.jar` 内嵌 3 个 jar（aeronautics / simulated / offroad）的 `assets/<ns>/blockstates|models|lang` 与交付件逐项 diff。
> 代码侧细节另见 `docs/FEATURE-GAP-code.md`；渲染/物品修复记录见 `docs/fix-be-renderers-batch.md`、`docs/fix-item-functional.md`。

## 0. 关键总数（注册表侧实测）

| 类别 | 原包（aeronautics bundle 内嵌 3 jar） | 交付件（aeronautics-fabric-...jar） | 缺失 |
|---|---|---|---|
| blockstates（aeronautics） | 43 | 43 | 0 |
| blockstates（simulated） | 95 | 95 | 0 |
| blockstates（offroad） | 3 | 0 | **3** |
| item 模型/定义（aeronautics） | 46 | 46 | 0 |
| item 模型/定义（simulated） | 86 | 86 | 0 |
| item 模型/定义（offroad） | 7 | 0 | **7** |
| lang keys（aeronautics） | 219 | 261 | 0 |
| lang keys（simulated） | 650 | 707 | 0 |
| lang keys（offroad） | 49 | 0 | **49** |

**结论：aeronautics / simulated 两个 namespace 的注册表资源**（方块、物品、lang）**逐项齐全**；唯一整块缺失是 bundle 内的 **offroad**（车轮/轮胎/轮座/钻孔轴承/切石轮 + borehead 实体）。

## 1. 未移植 mod（整块特性缺失）

来源：`python tools/diff_pack.py`（原包 112 jar → 已覆盖 56/110 id，未覆盖 54 个 jar）。按优先级分组：

### P0（会崩 / 核心玩法必需）

| mod id / jar | 缺失内容 | 备注 |
|---|---|---|
| `createabyss` / `createhighseas` / `createsubmarine`（create_submarine） | 潜艇/深海整套 | 无 26.3 构建 |
| `createenchantmentindustry` | 附魔工业 | NeoForge 1.21.1，移植成本高 |
| `createrailwaysnavigator` | 铁路导航 | 硬依赖 DragonLib（无 26.3 构建）|

### P1（常用玩法 / 航空学附属）

| mod id / jar | 缺失内容 |
|---|---|
| **offroad（bundle 内嵌）** | 车轮/轮胎/轮座/钻孔轴承/切石轮 + borehead 实体（见 §2，**已定位为注册缺失**）|
| `aerocopycats` / `copycats` | 伪装方块+（模型系统未移植）|
| `aeronauticscompat` / `aeroworks` / `aerocopycats` | 航空学兼容/扩展 |
| `createaeronauticstoolgun` / `createaeronauticsthrowableropeconnector` / `aeronauticsutilityobjects` | 工具枪/可投掷绳连接器/传动连杆 |
| `createpropulsion` / `createthrustersbundled`（gadgets-and-gizmos） | 推进器/喷气 |
| `createdieselgenerators` / `createliquidfuel` / `portableengineliquidfuel` | 柴油/液体燃料/便携引擎液体燃料 |
| `createoreexcavation` / `create_mechanical_extruder` / `create-central-kitchen` / `create_connected` / `create_power_loader` / `create_jetpack` | Create 附属机器/物流/装备 |
| `tfmg` / `mechanicals` / `createdeco` / `design-n-decor` / `sliceanddice` | 装饰/机械/食物切片 |
| `sablecreateadditioncompat` / `waystonessable` | Sable 兼容 |
| `climbable_ropes` / `mynethersdelight` / `culturaldelights` / `minersdelight` / `abnormalsdelight` | 绳索/食物（多卡 26.3 数据/树重做）|

### P2（库 / 结构 / 任务 / 外观）

| mod id / jar | 缺失内容 |
|---|---|
| `ftblibrary` / `ftbquests` / `ftbteams` / `ftbqopt` | FTB 任务链整块 |
| `yungsapi` / `blueprint` / `paxi` / `dragonlib` / `lodestone` / `mysteriousmountainlib` / `playeranimator` / `modernfix` | 库/前置（多数非玩法）|
| `awakenedislands` / `naturesspirit` / `mss`（MoogsSoaringStructures） | 结构/地形 |
| `sophisticatedbackpacks` / `sophisticatedcore` / `sophisticatedstorage` | 背包/存储（仅 NeoForge 26.3）|
| `createdragonsplus` / `createjetpack` / `createoreexcavation` | 其他 Create 附属 |

> 说明：`create-aeronautics-bundled` 本身已装，但它内嵌的 **offroad** 没有进交付件（见 §2），因此 bundle 的「车轮/轮胎」玩法缺失。

## 2. 已移植但注册缺失（原包有、交付件没有的 registry 条目）

### 2.1 offroad（bundle 内嵌，整块缺失）

| 类型 | 原包 | 交付件 | 缺失条目 |
|---|---|---|---|
| 方块 blockstates | 3 | 0 | `wheel_mount`、`rockcutting_wheel`、`borehead_bearing` |
| 物品 item | 7 | 0 | `wheel_mount`、`rockcutting_wheel`、`borehead_bearing`、`tire`、`small_tire`、`large_tire`、`monstrous_tire` |
| 实体 | 1+ | 0 | `offroad:borehead_contraption_entity`（lang 有 entity key）|
| lang | 49 | 0 | 全部 offroad 词条 |
| 代码 | `dev.ryanhcode.offroad.*` | 无 | 整个包类/网络/渲染 |

**优先级：P1**（航空学载具的轮子/轮胎是核心玩法；但不是崩溃项）。

### 2.2 aeronautics / simulated

- `aeronautics`：blockstates 43/43、item 46/46、lang 219→261（只多不少）⇒ **0 缺失**；
- `simulated`：blockstates 95/95、item 86/86、lang 650→707 ⇒ **0 缺失**。

### 2.3 已装 mod 的注册表抽查

- `create-fly`（Create 26.2 字节码补丁）：方块/物品注册来自原 Create，注册表本身完整；缺失主要集中在渲染/数据降级（见 `docs/DEGRADATIONS.md`）。
- `sable` / `sablecompanion`：sublevel/物理相关方块与物品已注册；渲染层为 R415/R425 补丁。
- 其他移植 mod（interiors/create-framed/createaddition/escalated/structures 等）注册表检查见各自 `docs/port-*.md`，本轮未发现额外「原包有、交付件无」的 id。

## 3. 已注册但代码桩 / 功能缺失

### 3.1 渲染层（P1 视觉，部分已有候选）

| 方块/实体 | 现状 | 优先级 | 备注 |
|---|---|---|---|
| `aeronautics:laser_pointer` | 透镜已注册；**激光束**候选 `g62/64926763` 等 promote | P1 | `submitCustomGeometry + SimRenderTypes.laser` |
| `simulated:laser_sensor` / `optical_sensor` | 只注册方块；光束/透镜未做 | P1 | 原实现无 lens partial，同激光束 |
| `simulated:nameplate` / `linked_typewriter` | 方块已注册；文本渲染未做 | P2 | 26.3 无 `Font.drawInBatch`，需 TextFeatureRenderer |
| `simulated:portable_engine`（16 色） | hatch/pipe/coil 最小版已做；filtering/发光层缺 | P2 | 需 per-buffer RenderType |
| 4 项 A 表（absorber/spring/merging_glue/hot_air_burner） | 无表驱动渲染 | P1/P2 | absorber BE 类型未注册（死内容）；spring/merging_glue/hot_air_burner 为程序化几何 |
| `aeronautics:gyroscopic_propeller_bearing` | 4 活塞候选已做（ABC3+）；待 promote | P1 | 未 promote 前旧件只有 plate |
| `simulated:rope_winch` | coil 动态候选已做；静态版已 promote | P2 | `shiftUVScrolling` 近似 |
| 52 个 BE renderer 桩（create-fly/aeronautics） | R422/R423/R433 已补 22 个；其余按 FEATURE-GAP-code 表 | P1→P2 | 批量补 |

### 3.2 物品/交互功能（P0/P1）

| 物品/方块 | 现状 | 优先级 | 备注 |
|---|---|---|---|
| `create:super_glue` | **右键方块崩**：26.3 删 `LocalPlayer.swing(InteractionHand)` | **P0** | ponder 的 create 修复件（不归 aeronautics）|
| `simulated:honey_glue` | 行为在 `HoneyGlueClientHandler`；**Alt+右键**两次才工作 | P1 | 普通右键无行为是设计；待 probe 用正确用法验 |
| `simulated:merging_glue` | block/BE 在，`MergingGlueItemHandler` 预览；绑定待验 | P1 | 需两端 sublevel 测试 |
| `simulated:spring` / `rope_coupling` / `contraption_diagram` / `plunger_launcher` | `useOn`/`use` 已实现 | P1 | 待探针逐项功能验证 |
| `simulated:physics_staff` / `aeronautics:aviators_goggles` | 客户端 handler/装备渲染 | P2 | 非 Item 方法 |
| `create:wrench` / `create:extendo_grip` | Create 物品 + simulated `ExtendoGripItemMixin` | P2 | 非本 mod |
| hold 类（assembler/throttle/handle/steering） | R426–R432 已修；sublevel 内 hold 判据待结构静止后回归 | P1 | `docs/fix-hold-all.md` |

### 3.3 数据/注册层（P0/P1）

| 项 | 现状 | 优先级 |
|---|---|---|
| `SimAdvancements` 4 条空 icon | R431 已数据根修 | 已完成 |
| 397 个 `item.*` 名称 | R406 已补 | 已完成 |
| `ProcessingRecipe` 框架 | 垫片 `g10/shim/proc-recipe-compat.jar` | 已完成 |
| Create 15 条 Ponder/渲染管线 / 120 trim 调色板 / 层状矿 / 堆肥 | 见 `docs/DEGRADATIONS.md` | P2 |

## 4. 建议修复批次（按 P0→P1）

1. **P0**：等 ponder 的 create `swing` 修复 promote（super_glue 崩溃）；随后全物品右键冒烟。
2. **P1-a**：laser 束候选（`g62/64926763`）判读/promote；laser_sensor/optical_sensor 复用。
3. **P1-b**：offroad 整包（车轮/轮胎/轮座/钻孔轴承）——需要新移植，工作量大；先确认是否用户必需。
4. **P1-c**：物品功能验证（honey_glue Alt、merging_glue、spring/rope/diagram/plunger）；按探针结果补 handler。
5. **P1-d**：剩余 BE renderer 桩（create-fly/aeronautics）按 FEATURE-GAP-code 批量补；gyro 活塞/rope coil 候选 promote。
6. **P2**：text（nameplate/typewriter）、portable engine filtering/发光层、结构/装饰/FTB 类 mod。

## 5. 方法与局限

- 注册表侧：原包 bundle 的 3 个内嵌 jar 解包后按 `assets/<ns>/blockstates|models/item|items|lang/en_us.json` 与交付件逐项 diff；这是 26.3 下最可靠、无需启动游戏的 registry 代理指标。
- mcmod 页面只用于核对「特性名称/机制」（Create 2021、Create: Aeronautics、Create: Simulated），页面正文是 HTML，未能逐条抓取全部物品表；因此 §1/§3 的完整性以注册表资产 + `FEATURE-GAP-code.md` + 修复文档为准。
- 未移植 mod 清单来自 `tools/diff_pack.py` 实时输出（56/110 覆盖，54 个 jar 未覆盖）；库/前置类 mod 不影响玩法，已归 P2。
