# Item 模型 / 贴图 / 可穿戴件审计（live 116，2026-10-21）

> 输入：用户反馈「物品栏方块图标异常 / create_jetpack 显示纹路图集 / 可穿戴件疑似不生效」，以及 follow-up「清掉 116 启动日志剩余 20 条 Missing textures」。
> 方法：静态扫描 live 116 jar + MC 26.3 原版资源：`assets/*/items/*.json` → `models` parent/texture 闭包 → `textures/*.png` 存在性；同时扫 blockstate/block model 闭包，并用 `g33/game-v102/logs/latest.log` 的运行时警告交叉验证。
> **未启动游戏、未改 `mods-stable`**；所有产物在 `work/run26/port/g200/`。

## 0. 本轮结论（20 条 log 已定位，staging 预期剩 0）

- 20 条 = **17 条 TFMG 流体 block model 的 particle 贴图** + **3 条 simulated 实体 diagram 贴图**。
- **不是贴图文件缺失**：20 个 PNG 全部在 jar 内且可正常解码；根因是它们位于 `textures/fluid` / `textures/entity`，没有被 `assets/minecraft/atlases/blocks.json` 的 blocks atlas 收录（26.3 只自动扫描 block/item 目录；需要显式 single source）。
- 修法：在 **tfmg jar** 加 blocks atlas 配置（49 个 fluid still/flow single sources）；在 **aeronautics jar** 现有 atlas 配置里追加 3 个 diagram single sources。26.3 `SpriteSourceList.load` 会合并所有资源包的 atlas 定义，不会覆盖 create/aeronautics 已有源。
- 静态核对：20/20 log 纹理已覆盖；预期下次启动 `Missing textures in model` = **0**。若仍非 0，优先查新出现的 atlas 解析错误或其他资源包覆盖，而不是继续补 PNG。
- `createaddition:metal_girder` 已从异常清单移除：它不是物品，jar 内只有 `models/block/connector/girder_base.json` 方块模型部件；`anomalies.tsv` 中 0 条 metal_girder。

## 1. 总览（live 116 current → staging-116-defs）

| 检查项 | baseline 116（1.0.5） | staging 116-defs | 说明 |
|---|---:|---:|---|
| 运行时 `Missing textures in model`（v102 log） | 20 | **0（预期）** | 17 TFMG 流体 + 3 simulated diagram，见 2.6 |
| item 模型闭包缺失 | 0 | 0 | 已修 |
| 真实 item 贴图缺失（非 minecraft/missingno） | 0 | 0 | 剩 3 条 create `missingno` 故意 |
| 真实 block 贴图缺失 | 0 | 0 | 8 条全部 `missingno` 故意 |
| blockstate 引用缺失模型 | 0 | 0 | — |
| item 定义缺失（`items/*.json`） | 365 | **327** | 本轮补 **38** 个真实可见物品；见 2.4/2.10 |
| 有 `models/item` 但无 item 定义 | 129 | 129 | trim/自定义 renderer 零件，不是错误 |
| bad JSON | 0 | 0 | 116 jar 全部解析通过 |

> 115 轮的 46 个 item 模型、create_jetpack 图标、create_connected 图标、44 trim 贴图、20 条 atlas log 等已随 1.0.5 进入 base；本轮只处理“残留 item 定义”里的真实可见物品。

## 2. 异常清单与修法

### 2.1 create_connected 45 个 item 模型（已在 116 base）

- 45 个 `models/item/<id>.json` 原本指向不存在的 `block/.../item` 子模型；已改为 blockstate 实际存在的 block 模型，物品栏显示 3D 方块图标。116 base 上 `item_model_missing=0`。

### 2.2 item 贴图

- **create trim 44 个**（`create:trims/items/card_*_trim_*`）：已在 1.0.5 base 修复（复制原版基础 trim 贴图），当前 live 116 已无真实 item 贴图缺失。**降级**：trim 材质 palette 丢失，显示单色 overlay。
- 116 base 上真实 block 贴图缺失为 0；staging `block_texture_missing=8` 全部是 `minecraft:missingno`（custom renderer 故意占位），不修。
- 115 轮已修的 tray/girder/bamboo/constantan 等 fallback 已在 116 base 中，不再列为异常。

### 2.3 create_jetpack 图标（已在 116 base）

- 根因：32×32 `textures/item/jetpack.png` 与上游 3D 模型 UV 皮肤 SHA 相同，`item/generated` 把整张皮肤当图标 → 纹路图集。
- 116 base 已是 16×16 fallback 图标（双罐+背带），本轮无需再改。

### 2.4 item 定义缺失（本轮 365 → 327）

- 当前 live 116（1.0.5）剩余 **365** 条；其中 minecraft 183 条是扫描器对 vanilla/special/air 的条目，不作为 mod 资源缺口。
- 非 MC 的 **182** 条按静态特征分：
  - **33 条 item texture only**：已有 `textures/item/<id>.png` + `item.*` lang，但缺 `models/item` 和 `items`；
  - **4 条 block texture only**（dndecor）：只有 `textures/block/<id>.png`，缺 blockstate/model；
  - **1 条派生纹理**（waystones `warp_scroll_bound`，可由 base warp_scroll 复制）；
  - 其余 144 条无任何 item/block 贴图或 model/blockstate。
- 本轮只补前 **38** 条“有可见资源来源”的真实物品：生成 `model/item/<id>.json`（`item/generated` + layer0）+ `items/<id>.json`（26.3 格式，指向 `ns:item/<id>`）；block texture only 先把 block 贴图复制到 `item/` 路径。
- 剩余 **327** 条（MC 183 + mod 144）不补，原因见 2.10 与 `remaining_defs.json`。

### 2.5 blockstate / block model

- 116 baseline `blockstate_model_missing=0`；staging 仍 0。此前 corndelight nachos 单复数问题已在 116 base 修好。

### 2.6 本轮 20 条 Missing textures 明细

来源：`work/run26/port/g33/game-v102/logs/latest.log`（2026-10-21 03:12:59，20 条）。逐条保存：`work/run26/port/g200/missing20.json`。

| 类别 | 条数 | 模型 | 缺失贴图 | 分类 | 修法 |
|---|---:|---|---|---|---|
| TFMG 流体 block model particle | 17 | `tfmg:block/gasoline`、`molten_steel`、`naphtha`、`sulfuric_acid`、`napalm`、`creosote`、`cooling_fluid`、`diesel`、`kerosene`、`molten_plastic`、`liquid_asphalt`、`liquid_concrete`、`molten_slag`、`heavy_oil`、`lubrication_oil`、`liquid_silicon`、`crude_oil` | `tfmg:fluid/<name>_still` | **假缺失：PNG 存在，未进 blocks atlas** | tfmg jar 加 `assets/minecraft/atlases/blocks.json`，49 个 fluid single sources |
| simulated 实体 diagram | 3 | `simulated:entity/contraption_diagram_large/medium/small` | `simulated:entity/diagram_large/medium/small` | **假缺失：PNG 存在，未进 blocks atlas** | aeronautics jar 现有 atlas 追加 3 个 diagram single sources |

- **故意占位**：这 20 条中 **0 条** `minecraft:missingno`；全部是 atlas 配置遗漏。
- 静态验证：20/20 纹理均被 staging atlas 覆盖（`_check_atlas2.py`）；staging 内无 atlas JSON 解析错误。
- **剩余**：预期 **0 条**；staging 启动后以最新 log 的 `Missing textures in model` 计数为准。

### 2.7 createaddition:metal_girder 从清单移除

- 已确认 `createaddition:metal_girder` **不是物品**；createaddition jar 内只有 `models/block/connector/girder_base.json` 方块模型部件，没有对应 item definition/模型。
- 因此不再作为 item 缺失列出；本轮 `anomalies.tsv` 已过滤 metal_girder（0 行）。

### 2.8 task-40 紫黑/破碎模型的静态边界

- **create_connected**：item 模型已在 116 base 修复；blockstate 闭包 0 缺失。
- **TFMG**：真实 item/block 闭包 0 缺失；锂火把「透视」若仍存在属于 renderer/shader。
- **aero-works / sliceanddice**：静态 blockstate/model/texture 闭包未报缺失；若画面仍紫黑，优先查自定义 renderer/动画/着色器。
- **dndecor**：剩余 `missingno` 为 custom renderer 占位，不是缺资源。

### 2.9 完整异常清单

- `work/run26/port/g200/anomalies.tsv`（345 行；含 116 baseline 异常 + 20 条 log texture；已排除 metal_girder）。
- 原始扫描：`scan_results.json`（current live 116 baseline）/ `scan_results_defs_live.json`（staging）；本轮选择/剩余：`selected_item_defs.json` / `remaining_defs.json`。

### 2.10 真实可见物品补齐（38 个）

选择判据（静态、无 GPU）：在 current live 116 的 365 条剩余里，优先取 **有 item 贴图** 或 **有 block 贴图可派生** 且带 `item.*` lang 的 id；排除 crop/potted/wall_sign、无任何视觉资源的技术件、以及 stale lang key。完整清单：`work/run26/port/g200/selected_item_defs.json`。

| jar | 数量 | id（示例/全量见 JSON） | 资源来源 |
|---|---:|---|---|
| sky262-createdeco | 13 | `andesite_sheet`、五色 `*_coin`、`industrial_iron_ingot/nugget/sheet`、`zinc_sheet` | `createdeco:textures/item/*.png` |
| sky262-diesel-generators | 19 | `biodiesel/crude_oil/diesel/ethanol/gasoline/plant_oil_bucket`、`chemical_sprayer`、`hammer`、`lighter`、`wire_cutters`、`wood_chip` 等 | `createdieselgenerators:textures/item/*.png` |
| sky262-design-n-decor | 5 | `belt`、`belt_connector`、`dark_metal_brick_stairs`、`diagonal_girder`、`text_plate` | 1 个 item 贴图 + 4 个 block 贴图复制到 item |
| waystones | 1 | `warp_scroll_bound` | 复制 `item/warp_scroll` |
| **合计** | **38** | — | 全部生成 model + `items` 定义 |

- 选择依据是“可见资源 + item lang”；未做创造栏 GUI 实拍（本任务静态），因此如果某个 id 实际被隐藏但仍被注册，补定义不会创建新物品，也不会影响其他物品。
- 38 个均生成 26.3 `items/<id>.json`：`{"model":{"type":"minecraft:model","model":"<ns>:item/<id>"}}`；对应 `models/item/<id>.json` 使用 `minecraft:item/generated`。
- staging 校验：`item_model_missing=0`、`item_texture_missing` 真实项 0、`badjson=0`，item 定义缺失 365→327。

**剩余 327 不补的原因**（完整逐条 `remaining_defs.json`）：

| 原因 | 数量 | 说明 |
|---|---:|---|
| vanilla/special/air 扫描器条目 | 183 | minecraft 命名空间非 mod 缺口，不处理 |
| 无贴图/无 model/无 blockstate，且无 item lang | 65 | 技术件/非物品/无资源来源，强行造图标会伪装成真物品 |
| stale color/lang key | 35 | createframed 的旧颜色 key，jar 内无对应 item model/blockstate/texture，不是实际物品 |
| 有 item lang 但无任何 item/block 贴图或 model | 32 | 可能真实但无美术来源（如 createaddition figurine/goblet、create package、create_connected chip/music disc 等），不伪造贴图 |
| technical/model part | 12 | simulated 的 core/inner_cube 等模型部件，不是独立物品 |

## 3. 可穿戴件静态结论（lab 实测待 probe 释放实例）

| 物品 | 注册/组件（静态证据） | 能否穿 | 使用效果 | lab 待验 |
|---|---|---|---|---|
| `create_jetpack:jetpack` / `netherite_jetpack` | `JetpackItem extends Item`；`Item.Properties` 只 `setId` + `stacksTo(1)`；**无 `DataComponents.EQUIPPABLE`** | **不能穿**（无装备槽） | 手持右键 `use` → THRUST 60 tick；server tick 每 tick y 速度约 +0.32、`ClientboundSetEntityMotionPacket` 同步、雪粒子；`hasJetpack` 只扫描背包 | 手持右键看 `[sky262jetpack] thrust tick`、y 位移/粒子；确认「不是穿上而是手持」 |
| `create:goggles` | `AllItems.GOGGLES` 注册时 `.component(EQUIPPABLE, Equippable.builder(HEAD).build())` | **可穿（头盔槽）** | `GogglesItem.isWearingGoggles` 供 Create HUD/overlay 判定；无 armor 属性 | 戴头盔槽，看 goggles overlay / HUD |
| `aeronautics:aviators_goggles` | `AviatorsGogglesItem extends Item`；`AeroItems` 只在 properties 加 `AeroDataComponents.LEVITATING`；**无 EQUIPPABLE/equipment 资源** | **不可穿**（当前 reduced port） | 仅物品组件，无装备/护甲槽；不属于 Create goggles predicates | 右键/装备尝试，预期无槽；记录「当前不可穿」 |
| `create:copper_backtank` / `netherite_backtank` | `BacktankItem extends BlockItem`；`AllArmorMaterials.chest(...)` → `humanoidArmor` + `EQUIPPABLE` `EquipmentSlot.CHEST`；有 `equipment/copper.json`/`netherite.json` 与装备纹理 | **可穿（胸甲槽）** | 空气条/耐久、`BacktankUtil` 供气；`BacktankItem.SLOT=CHEST` | 穿胸甲槽，空气条显示、消耗空气 |
| `create:cardboard_helmet/chestplate/leggings/boots` | `CardboardArmorItem extends Item`；`AllItems` 注册时 `.component(EQUIPPABLE, HEAD/CHEST/LEGS/FEET)` + armor attributes + `equipment/cardboard.json` | **可穿（四甲槽）** | 护甲值/耐久；stealth overlay 由 client mixin | 穿四槽，看护甲值与 cardboard 潜行 overlay |
| `create:copper_diving_helmet/boots`、`netherite_diving_*` | `DivingHelmetItem/DivingBootsItem`；注册时 `.component(EQUIPPABLE, HEAD/BOOTS)` + `humanoidArmor`/attributes + `equipment/copper`/`netherite` | **可穿（头/脚槽）** | 水下呼吸/岩浆、下潜加速；`DivingHelmetItem.breatheUnderwater` | 穿头/脚，水下呼吸/岩浆、下潜速度 |

> 结论对用户：**jetpack 在这个 reduced port 是「手持右键推进器」，不是可穿戴装备**；aviators_goggles 目前也不是装备。若要「背在身上」，需单独改代码加 `EQUIPPABLE(CHEST)`/Curios，不是资源修复能完成。

## 4. 修复 staging（base live 116 current）

- staging：`work/run26/port/g200/stage/mods-itemfix-defs-live`（116 jar = current live 硬链接 + **4 个替换件**；**未写 live**）。
- 候选件：`work/run26/port/g200/out116-defs-live/`。
- 改动仅资源（`assets/**`），**0 个 class 改动**；4 个 jar：
  - createdeco：13 个 item texture only → 13 model + 13 items；
  - design-n-decor：5 个（1 item + 4 block texture）→ model/items + 4 个 item 贴图复制；
  - diesel-generators：19 个 item texture only → 19 model + 19 items；
  - waystones：1 个 bound scroll → 1 贴图复制 + model + items。
- 基线/候选逐 jar SHA、changed entries、`class_changed=false`、`non_asset_changes=[]`：`work/run26/port/g200/staging_manifest_defs_live.json`。
- staging 重扫：item 定义 365→327，item_model_missing 0，真实 item/block 贴图缺失 0，badjson 0；仅剩 3 条 create `missingno` 与 8 条 block `missingno`（故意）。

| jar | 变化 entry 数 | base live SHA-256（前 16） | 候选 SHA-256（前 16） |
|---|---:|---|---|
| sky262-createdeco-2.1.3-beta-port.21.jar | 26 | b21fac217513a6d8 | a190b39bfb29e520 |
| sky262-design-n-decor-2.2b-beta-port.32.jar | 14 | a2b0b0e0dc1742cd | 391e0ecd2a4697ba |
| sky262-diesel-generators-1.3.15-beta-port.3.jar | 38 | 179c89a3ed3c8578 | f22a18efed49058e |
| waystones-fabric-26.3-26.3.0.1.jar | 3 | cfc19951cd15863c | aece9c10d09c22d7 |

## 5. 后续 / lab 实测协议（probe 释放实例后）

1. **图标**：创造栏搜索并截图：`create_jetpack:jetpack`、`create_connected:brake/brass_chute/fan_*`、`tfmg:aluminum_axe`、`dndecor` 楼梯、`create:cardboard_*`（trim 变体检查）；本轮重点搜索 `createdeco` 硬币/锭/片、`createdieselgenerators` 桶/工具、`dndecor` belt/stairs/girder、`waystones:warp_scroll_bound`，确认图标不再是 missing model。
2. **jetpack**：give → 手持右键（不是装备槽）→ 检查日志 `[sky262jetpack] thrust tick player=... y=... dy=...`、y 位移/雪粒子；记录「不能穿、能用（手持）」。
3. **goggles / backtank / cardboard / diving**：give → 右键装备或 `/item replace entity @s armor.head|chest|legs|feet with ...` → 确认槽位、护甲值/装备外观、goggles overlay、backtank 空气条、diving 水下/岩浆效果。
4. **aviators_goggles**：右键/装备尝试 → 预期不进入槽位；记录「当前 reduced port 不可穿」。
5. **本轮 20 条 log 验证**：staging 启动后 grep `Missing textures in model` 应为 **0**；同时 grep `Failed to parse atlas definition` 应为 0。若仍有，附最新 log 行 + 实际加载 jar 路径。
6. **回归**：0 crash-report、无 missing model/texture log、RAPIER/渲染不回归。

## 6. 已知降级（写进交付说明）

- jetpack 图标为 fallback 像素图标，不是上游 3D 物品模型。
- create trim 材质 palette 丢失（单色 overlay）。
- bamboo_mat 用木纹替代、girder_base 用 create girder 替代（115 轮已入 base）。
- 144 个 mod item 定义仍缺（327 总剩余 - MC 183；多为无贴图/技术件/stale lang，未强造资源）。
- jetpack/aviators_goggles **不可穿戴**是 reduced port 的功能缺口；需代码另立项。
- TFMG/simulated 的 20 条 log 只是 atlas 配置修复；无新增降级。
