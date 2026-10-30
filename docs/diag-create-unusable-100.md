# diag-create-unusable-100 —— Create 内容“几乎不能用”的其它静态嫌疑

> 只读静态对比；未改 live。优先参考 docs/fix-create-data.md、docs/audit-create-machines-100.md、docs/audit-data-refs.md。

## 1. 结论（按优先级）

| 优先级 | 嫌疑 | 证据 | 影响 | 建议 |
|---|---|---|---|---|
| **P0** | create:sequenced_assembly 数据整体缺失（0 条） | live create-fly 的 data/create/recipe 无实际 json；sky262-create-recipes 1607 条中 sequenced_assembly=0；docs/fix-create-data.md 明确删了 precision_mechanism/sturdy_sheet/track 等 3 条 | 精密机构/坚固板/轨道不可得 ⇒ 机械动力中后期进度与列车内容直接卡死 | 单独按 26.3 schema 转换这 3 条，最小化注入；验证 registry + 配方 parser |
| **P1** | 68 个 create item 无配方输出（其中含 blaze_burner、encased shaft/cogwheel、track、sturdy_sheet、precision_mechanism 等） | 693 items vs 1002 输出；静态 recipe 输出集合差集 | 部分非创造物品不可获得；需区分动态/创造/真实缺口 | 逐项分类：creative/dynamic/真正缺；只修真实缺口 |
| **P2** | 后续 mod 的 mixin 叠加改变 Create BE/行为（CEI/DP/aeronautics/constraintfix + crashfix 1.0.5） | docs/audit-critical-100.md B1/B2；静态 mixin target 表 | 机器“存在但功能不对/自动化失效” | 先做 base+Create A/B，再逐个加附属；与数据 P0 分开修 |
| **P3** | Ponder / UI / 贴图资源缺失或损坏 | 见 §2：ref 路径缺失 0，ponder/GUI 全量 hash 相同 | **基本排除**；不是本轮“不能用”的静态原因 | 不投入 |
| **P4** | mechanical_crafting 只有 4 条 | docs/audit-create-machines-100.md：上游 4 / live 4，一致 | **不是缺口**；机械合成台可合成 crushing_wheel/extendo_grip/potato_cannon/wand | 不改 |
| **P5** | createfix 跳过 modded namespace cutting | 日志 [sky262-createfix] skipped runtime cutting recipe... | 只影响 modded 木材切割，不是整机不可用 | 已知降级，后置 |

## 2. assets 对比：ponder/UI/贴图不是原因

对比基准：work/refs/create-fly（上游解包树）vs live create-fly-26.2-6.0.9-2-26.3-patched.jar。

- assets/create/ponder：ref 178 个路径，live 215 个，**缺失 0**；
- assets/create/textures/gui：ref 38，live 43，**缺失 0**；
- assets/ponder：ref 49，live 49，**hash 全同**（49/49）；
- assets/create/ponder：**hash 全同**（178/178）；textures/gui：**hash 全同**（38/38）；
- blockstates 643→644、models 2478→2632、items 693→694、textures 3098→3268，ref 路径均未缺失；
- lang: en_us 3641 keys / zh_cn 3643 keys，live 与 ref **missing keys = 0**。

结论：Ponder 场景 nbt、GUI 贴图、模型、语言资源完整且未损坏；**“装了别的 mod 后不能用”不是 assets 缺文件导致**。

## 3. recipe 数据：sequenced_assembly 是硬缺口

### 3.1 数据来源结构
- live create-fly jar 的 data/create/recipe 只有目录条目（实际 json=0）；配方由 sky262-create-recipes 的 1607 条静态数据提供。
- 静态 1607 条类型：crafting_shaped 374、stonecutting 327、crafting_shapeless 272、create:deploying 233、create:cutting 156、create:crushing 59、create:milling 47、create:splashing 33、create:haunting 20、create:mixing 11、create:pressing 11、create:filling 10、create:item_application 8、create:compacting 7、create:mechanical_crafting 4、create:emptying 2 等。
- **create:sequenced_assembly = 0**。
- Create 自己的 RuntimeDataGenerator 只生成 **cutting/splashing**（源码 work/refs/create-fly/.../RuntimeDataGenerator.java），不会补 sequenced_assembly。

### 3.2 缺失的 3 条（docs/fix-create-data.md）
- precision_mechanism：精密机构；中后期机器/自动化关键中间件；
- sturdy_sheet：坚固板；列车/轨道/高级 contraption 的关键材料；
- track：列车轨道；没有轨道 ⇒ 列车内容整体不可用（轨道物品也出现在 68 个无配方输出里）。

原因：26.2 schema 的 sequenced_assembly 在 26.3 解析失败，整个目录被删；docs/audit-create-machines-100.md 也标注 “sequenced_assembly 上游 3 / live 0（有意删）”。

### 3.3 68 个无输出 item 的分类
- 真实影响较大的：precision_mechanism、incomplete_precision_mechanism、sturdy_sheet、unprocessed_obsidian_sheet、refined_radiance_casing、shadow_steel_casing、track、blaze_burner、elevator_contact、各色 toolbox、encased shaft/cogwheel 系列；
- 其中 creative_*、handheld_worldshaper、schematic、shopping_list、rare_* package、minecart_contraption 等是创造/动态/非普通配方，**不能算缺口**；
- 因此 68 是上界，真正需要补的以 P0 的 3 条 + 明确关键机器件为优先；不要一次性补 68 条。

## 4. 与“后续 mod 加入后不能用”的关系
- P0/P1 是**本来就存在的基线缺口**，不会因为装新 mod 才出现；它解释“Create 内容不完整/中后期卡死”，不解释“装了 mod 后突然不能用”。
- “装了别的 Create mod 后突然不能用”更符合 docs/audit-critical-100.md 的 B1/B2：
  - B1 crashfix 1.0.5 对所有 SmartBlockEntity 在 setLevel 提前 initialize；
  - B2 CEI/DP/aeronautics/constraintfix 同时向 SmartBlockEntity/Behaviour/Basin 等注入。
- 本轮先修 P0/P1 数据（可回归、低风险）；P2 用 base+Create 逐 mod A/B 定位，不要和 P0 混在一起。

## 5. 建议动作
1. P0：把 precision_mechanism / sturdy_sheet / track 三条 26.2 sequenced_assembly 转成 26.3 schema；只加这 3 条，先验证 registry 不炸、配方能读；再补其它真实缺口。
2. P1：对 68 个无输出 item 做分类表；只补“非 creative/非动态”的真实缺口。
3. P3 不做：assets/ponder/UI/textures 已证明完整且 hash 一致。
4. P2：另开 A/B，按 audit-critical-100 的 staging 做 base+Create 逐 mod。
