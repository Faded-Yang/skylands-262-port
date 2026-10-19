# createdieselgenerators 1.3.15 移植评估（Tier B）

原包：`createdieselgenerators-1.21.1-1.3.15.jar`（3,154,746 B）→ `work/refs/diesel-generators`

## 规模
- **200 java** / 1343 entries；**66 个 blockstates**（66 方块）、326 models、311 textures、15 lang、15 mixin、11 ponder；
- data：recipe 157（旧 schema，必须删/转）、loot_table 45、tags 23、minecraft tags 10；
- **额外命名空间资源**：`assets/everycomp/`(30)、`assets/quark/`(11) —— 必须**排除**（否则污染别的 mod 命名空间）。

## 依赖
- create 6.0.7+（fork OK）；NeoForge 21.1.174+；
- 可选 `struts`（**缺失**）⇒ 相关兼容类排除；
- `dev.engine_room`(Flywheel) 48 处引用、`dev.latvian`(KubeJS)、`mezz.jei`(JEI 在包里) ⇒ Flywheel/KubeJS 类排除；
- 15 个 mixin（v1 不做）。

## Java 分类（粗）
- data/registrate/config：约 40；
- 方块/方块实体/behaviour：约 80（引擎、泵、蒸馏塔、发酵桶等）；
- 客户端渲染/ponder/JEI/KubeJS/兼容：约 60（v1 不做）；
- 工具/杂项：约 20。

## 方块清单（66）
- 装饰：asphalt_block/slab/stairs、chip_wood_block/slab/stairs/beam、sheet_metal_panel、andesite_girder(+strut/encased_shaft)、16 色 cement；
- 管道：16 色 `*_concrete_encased_fluid_pipe`；
- 流体方块：crude_oil / plant_oil / biodiesel / ethanol / gasoline / diesel（6）；
- 机器：diesel_engine / large_diesel_engine / huge_diesel_engine、pumpjack_bearing/head/crank/hole、powered_engine_shaft、distillation_tank、bulk_fermenter、basin_lid、burner、oil_barrel、canister、chemical_turret。

## reduced 方案（数据驱动，同 createdeco 模式）
- **v1 = 资源 + 方块/物品注册 + 创造栏**，行为/视觉后置；
- 分批（新增 ≤20）：
  1. batch1：asphalt(3) + chip_wood(4) + sheet_metal_panel(1) + girders(3) = 11；
  2. batch2：16 色 cement；
  3. batch3：16 色 encased fluid pipe；
  4. batch4：流体 6 + 机器骨架（BE 空壳）；
  5. batch5：剩余机器。
- 资源：只带本批 id 的 blockstates/models/textures/lang；**排除 assets/everycomp、assets/quark**；data 只保留本批 loot（先不带 data 更安全）；
- 生成器沿用 createdeco 的累积构建器（颜色列表 + 模型 parent 闭包 + 资源自检 + tab）；
- 方块属性按 blockstate 变体键反推（facing/axis/waterlogged 等），流体方块用 `LiquidBlock`（需 Fluid 注册），machine 用 Block 壳 + BE 壳。

## 风险
- 66 方块里 6 个是流体方块：需要注册 `Fluid`/`LiquidBlock` + 流体客户端渲染（`FluidType`），26.3 Fabric 流体注册较繁琐；v1 可先跳过流体方块，只做注册不了的说明；
- 机器（引擎/泵/蒸馏塔）BE 行为复杂（NeoForge 78 文件 + Flywheel 视觉缺失），走「空壳 + 后续增量」；
- 无 Flywheel ⇒ 引擎转动/飞轮视觉缺失（降级说明）。

## 建议
- 若接受「注册-only 装饰 + 机器空壳」：我按以上 5 批推进（每批累积、probe 验）；
- 若不接受：建议只做装饰/管道/水泥等无 BE 方块（约 40 个，3 批），机器与流体方块标 TODO。
