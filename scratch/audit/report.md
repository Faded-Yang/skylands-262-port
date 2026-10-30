# 26.3 模型烘焙审计报告（离线预测 + 真实日志对齐）

工具：tools/audit_models.py（规则镜像 26.3 反编译源码，见文件头注释）。
数据源：mods-stable 118 jar + 原版 26.3 assets 11604 文件。
所有数字由工具重算；日志只用于 4.2 的通道 B 根集合。

## 0. 为什么换 KPI

历史做法只 grep "Missing textures in model"（本次 = 0）就宣布模型修好，但 26.3 还有三类同等致命：
"Missing texture references in model"（395 行）、"Rejecting block model"（32 行 / 29 个模型）、
"Unable to bake item model"（1 行，异常栈）。它们的共同后果都是客户端把模型画成 missing。

## 1. 扫描面

- 被 blockstate 引用的 block 模型根：9944 个，来自 5479 个 blockstate 文件
- item 定义（assets/*/items/*.json）：6925 个，引用 7326 个模型
- 通道 B（Flywheel PartialModel 运行时根，日志反推）：74 个
- 模型 json 缺失 id：2；模型 json 解析失败：0
- blockstate 文件异常：0

## 2. 结论：会被画成 missing 的清单

| reason | 记录数 | 含义 |
|---|---:|---|
| missing_texture_reference | 410 | 引用了未定义的 texture slot (该面/粒子画成 missing 紫黑) |
| cross_atlas_block | 29 | block 模型用了 items 图集的 sprite -> 整个模型被 Rejecting (画成 missing) |
| unresolved_texture_reference | 14 | #slot 指向的目标 slot 不存在，无法解析 |
| missing_model | 10 | 引用的模型 json 不存在 (游戏退回 missing 模型) |
| missing_texture | 8 | 最终纹理 png 不在任何图集 (items/blocks) 里 |
| uv_out_of_bounds | 4 | UV 超出纹理像素范围 -> computeTransparency 抛异常，模型烘不出来 |
| neoforge_texture_size | 1 | 模型用了 NeoForge 的 texture_size 扩展 (26.3 不认)，uv 仍在旧坐标空间 (次级/需人工确认) |

- 受影响 id：item **94** 个 / block **116** 个
- broken.json 记录：476 条（每条带 fix_hint）
- 按通道：blockstate 341 条 / item-definition 62 条 / runtime-partial-model 73 条

通道 A（纯离线、资源可枚举）的结论：403 条记录，覆盖全部确定性破损。
通道 B 的记录是同一套规则作用在运行时注册的模型根上得到的（Create/Simulated 的 Flywheel PartialModel）；
它们的根集合离线不可枚举，但修复清单必须包含它们——游戏里这些方块/物品同样画成 missing。

## 3. 分 namespace 统计

### item（106 条 / 94 个 id）

| namespace | id 数 | 记录数 | cross_atlas_block | missing_model | missing_texture | missing_texture_reference | neoforge_texture_size | unresolved_texture_reference | uv_out_of_bounds |
|---|---|---|---|---|---|---|---|---|---|
| interiors | 34 | 34 |  |  |  | 34 |  |  |  |
| createframed | 19 | 19 | 19 |  |  |  |  |  |  |
| tfmg | 12 | 15 |  |  |  | 11 |  |  | 4 |
| simulated | 11 | 13 | 9 |  |  | 3 | 1 |  |  |
| create_aeronautics_toolgun | 7 | 7 |  |  | 7 |  |  |  |  |
| createdieselgenerators | 3 | 4 |  |  |  | 3 |  | 1 |  |
| aeronautics | 2 | 2 |  |  |  | 2 |  |  |  |
| escalated | 2 | 2 |  |  |  | 2 |  |  |  |
| create_connected | 1 | 1 |  |  |  | 1 |  |  |  |
| create_submarine | 1 | 1 |  | 1 |  |  |  |  |  |
| createaddition | 1 | 6 |  |  |  |  |  | 6 |  |
| dndecor | 1 | 2 |  |  |  | 1 |  | 1 |  |

### block（370 条 / 116 个 id）

| namespace | id 数 | 记录数 | cross_atlas_block | missing_model | missing_texture | missing_texture_reference | unresolved_texture_reference |
|---|---|---|---|---|---|---|---|
| interiors | 34 | 272 |  |  |  | 272 |  |
| simulated | 32 | 33 |  | 2 |  | 31 |  |
| createdieselgenerators | 17 | 21 |  |  |  | 21 |  |
| aeronautics | 7 | 7 |  |  |  | 7 |  |
| create_aeronautics_toolgun/create_aeronautics_toolgun | 6 | 6 |  | 6 |  |  |  |
| createdeco | 6 | 12 |  |  |  | 12 |  |
| sophisticatedbackpacks | 6 | 6 |  |  |  | 6 |  |
| tfmg | 3 | 3 |  |  |  | 3 |  |
| create_aeronautics_throwable_rope_connector | 1 | 1 | 1 |  |  |  |  |
| create_aeronautics_toolgun | 1 | 1 |  |  | 1 |  |  |
| create_submarine | 1 | 1 |  | 1 |  |  |  |
| createaddition | 1 | 6 |  |  |  |  | 6 |
| natures_spirit | 1 | 1 |  |  |  | 1 |  |

## 4. 工具预测 vs latest.log（逐类对齐）

### 4.1 对齐总表

对齐口径：日志里的 model id 与工具预测的 model 字段做集合比较（数量 + id 集合）。
通道 A = 资源可枚举的根（blockstate 引用 + items/<id>.json 引用）；
通道 B = 运行时注册的 Flywheel PartialModel 根（Create API，离线不可枚举，见 4.2）。A+B 是工具全量预测。

| 类别 | A 预测 | A+B 预测 | 日志 | A∩日志 | A+B∩日志 | A+B 仅预测 | A+B 仅日志 | 判定 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Missing block model | 1 | 2 | 2 | 1 | 2 | 0 | 0 | 一致 |
| Missing texture references | 359 | 395 | 395 | 359 | 395 | 0 | 0 | 一致 |
| Missing textures | 8 | 8 | 8 | 8 | 8 | 0 | 0 | 一致 |
| Unresolved texture references | 4 | 4 | 4 | 4 | 4 | 0 | 0 | 一致 |
| Rejecting block model | 1 | 29 | 29 | 1 | 29 | 0 | 0 | 一致 |
| Unable to bake item model | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 一致 |
| Failed to load model (parse) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 一致 |

日志原始行数（同一模型可能被多次 bake，故行数 >= 唯一 id 数）：

| 日志类 | 行数 |
|---|---:|
| missing_block_model | 2 |
| missing_texture_refs | 395 |
| missing_textures | 8 |
| unresolved_refs | 4 |
| rejecting | 32 |
| unable_item | 1 |
| unable_model | 0 |
| missing_variant | 0 |
| failed_load_model | 0 |


### 4.2 通道 A 与日志的差值 = 通道 B 的证据

通道 A 只覆盖资源可枚举的根（blockstate + item 定义）。差值集合里的每个 id 都满足：
(a) 它的 model json 存在；(b) 没有被任何 blockstate / items 定义引用；(c) 日志里它按 block 模型被 bake。
三条只能由「代码直接把模型 id 交给 SimpleModelWrapper.bake」解释——即 Flywheel 的 PartialModel：
create-fly 的 com.zurrtum.create.client.mixin.ModelBakeryMixin 在 bakeModels 之后对
PartialModelEventHandler.getRegisterAdditional() 的每个 id 调用 SimpleModelWrapper.bake(modelBaker, id, IDENTITY)，
ModelManagerMixin 又把这些 id 加进 ModelDiscovery；SimpleModelWrapper 正是打 "Rejecting block model" 的那条路径。
所以 item 命名空间的模型也会被按 block 规则拒绝，它们的 particle slot 也会打 "Missing texture references"。

- 通道 B 根数量：74，清单在 broken.json 的 runtime_roots 字段。

### 4.3 残余差异与解释

全部 7 类完全一致（数量 + id 集合）。

### 4.4 逐类明细（日志 body 与工具 detail 对照）

**Missing texture references**：比较每个模型的槽位集合

- 槽位集合一致：395 / 395

**Missing textures**：比较缺失 sprite

- create_aeronautics_toolgun:block/portable_structure_printer : log=['create_aeronautics_toolgun:block/portable_structure_printer'] tool=['create_aeronautics_toolgun:block/portable_structure_printer']
- create_aeronautics_toolgun:item/creative_magnetic_gun : log=['create_aeronautics_toolgun:item/creative_magnetic_gun'] tool=['create_aeronautics_toolgun:item/creative_magnetic_gun']
- create_aeronautics_toolgun:item/disposable_vehicle_container : log=['create_aeronautics_toolgun:item/container2'] tool=['create_aeronautics_toolgun:item/container2']
- create_aeronautics_toolgun:item/magnetic_gun : log=['create_aeronautics_toolgun:item/text_gun'] tool=['create_aeronautics_toolgun:item/text_gun']
- create_aeronautics_toolgun:item/portable_structure_container : log=['create_aeronautics_toolgun:item/container'] tool=['create_aeronautics_toolgun:item/container']
- create_aeronautics_toolgun:item/portable_structure_printer : log=['create_aeronautics_toolgun:block/portable_structure_printer'] tool=['create_aeronautics_toolgun:block/portable_structure_printer']
- create_aeronautics_toolgun:item/structure_tool : log=['create_aeronautics_toolgun:item/survival_structure_tool'] tool=['create_aeronautics_toolgun:item/survival_structure_tool']
- create_aeronautics_toolgun:item/survival_structure_tool : log=['create_aeronautics_toolgun:item/survival_structure_tool'] tool=['create_aeronautics_toolgun:item/survival_structure_tool']

**Rejecting block model**：日志的图集/精灵 vs 工具 cross_atlas

- create_aeronautics_throwable_rope_connector:block/mounted_rope_launcher : log=['{minecraft:textures/atlas/items.png=[create_aeronautics_throwable_rope_connector:item/rope_connector_launcher]}'] tool={'items': ['create_aeronautics_throwable_rope_connector:item/rope_connector_launcher']}
- createframed:item/axolotl_lucy_package : log=['{minecraft:textures/atlas/items.png=[createframed:item/package/axolotl_lucy]}'] tool={'items': ['createframed:item/package/axolotl_lucy']}
- createframed:item/black_package : log=['{minecraft:textures/atlas/items.png=[createframed:item/package/black]}'] tool={'items': ['createframed:item/package/black']}
- createframed:item/blue_package : log=['{minecraft:textures/atlas/items.png=[createframed:item/package/blue]}'] tool={'items': ['createframed:item/package/blue']}
- createframed:item/brown_package : log=['{minecraft:textures/atlas/items.png=[createframed:item/package/brown]}'] tool={'items': ['createframed:item/package/brown']}
- createframed:item/cyan_package : log=['{minecraft:textures/atlas/items.png=[createframed:item/package/cyan]}'] tool={'items': ['createframed:item/package/cyan']}
- createframed:item/fordalels_package : log=['{minecraft:textures/atlas/items.png=[createframed:item/package/fordalels]}'] tool={'items': ['createframed:item/package/fordalels']}
- createframed:item/gray_package : log=['{minecraft:textures/atlas/items.png=[createframed:item/package/gray]}'] tool={'items': ['createframed:item/package/gray']}
- createframed:item/green_package : log=['{minecraft:textures/atlas/items.png=[createframed:item/package/green]}'] tool={'items': ['createframed:item/package/green']}
- createframed:item/karpboard_package : log=['{minecraft:textures/atlas/items.png=[createframed:item/package/karpboard]}'] tool={'items': ['createframed:item/package/karpboard']}
- createframed:item/light_blue_package : log=['{minecraft:textures/atlas/items.png=[createframed:item/package/light_blue]}'] tool={'items': ['createframed:item/package/light_blue']}
- createframed:item/light_gray_package : log=['{minecraft:textures/atlas/items.png=[createframed:item/package/light_gray]}'] tool={'items': ['createframed:item/package/light_gray']}
- createframed:item/lime_package : log=['{minecraft:textures/atlas/items.png=[createframed:item/package/lime]}'] tool={'items': ['createframed:item/package/lime']}
- createframed:item/magenta_package : log=['{minecraft:textures/atlas/items.png=[createframed:item/package/magenta]}'] tool={'items': ['createframed:item/package/magenta']}
- createframed:item/orange_package : log=['{minecraft:textures/atlas/items.png=[createframed:item/package/orange]}'] tool={'items': ['createframed:item/package/orange']}
- createframed:item/pink_package : log=['{minecraft:textures/atlas/items.png=[createframed:item/package/pink]}'] tool={'items': ['createframed:item/package/pink']}
- createframed:item/purple_package : log=['{minecraft:textures/atlas/items.png=[createframed:item/package/purple]}'] tool={'items': ['createframed:item/package/purple']}
- createframed:item/red_package : log=['{minecraft:textures/atlas/items.png=[createframed:item/package/red]}'] tool={'items': ['createframed:item/package/red']}
- createframed:item/white_package : log=['{minecraft:textures/atlas/items.png=[createframed:item/package/white]}'] tool={'items': ['createframed:item/package/white']}
- createframed:item/yellow_package : log=['{minecraft:textures/atlas/items.png=[createframed:item/package/yellow]}'] tool={'items': ['createframed:item/package/yellow']}
- simulated:item/creative_physics_staff/core : log=['{minecraft:textures/atlas/items.png=[simulated:item/zapper_staff]}'] tool={'items': ['simulated:item/zapper_staff']}
- simulated:item/creative_physics_staff/core_glow : log=['{minecraft:textures/atlas/items.png=[simulated:item/zapper_staff]}'] tool={'items': ['simulated:item/zapper_staff']}
- simulated:item/creative_physics_staff/inner_cube : log=['{minecraft:textures/atlas/items.png=[simulated:item/zapper_staff]}'] tool={'items': ['simulated:item/zapper_staff']}
- simulated:item/creative_physics_staff/outer_cube : log=['{minecraft:textures/atlas/items.png=[simulated:item/zapper_staff]}'] tool={'items': ['simulated:item/zapper_staff']}
- simulated:item/creative_physics_staff/ring : log=['{minecraft:textures/atlas/items.png=[simulated:item/zapper_staff]}'] tool={'items': ['simulated:item/zapper_staff']}
- simulated:item/creative_physics_staff/sigma : log=['{minecraft:textures/atlas/items.png=[simulated:item/zapper_staff]}'] tool={'items': ['simulated:item/zapper_staff']}
- simulated:item/plunger_launcher/plunger_tether : log=['{minecraft:textures/atlas/items.png=[simulated:item/plungerlauncher]}'] tool={'items': ['simulated:item/plungerlauncher']}
- simulated:item/plunger_launcher/spool_joint : log=['{minecraft:textures/atlas/items.png=[simulated:item/plungerlauncher]}'] tool={'items': ['simulated:item/plungerlauncher']}
- simulated:item/plunger_launcher/tether_spool : log=['{minecraft:textures/atlas/items.png=[simulated:item/plungerlauncher]}'] tool={'items': ['simulated:item/plungerlauncher']}

**Unresolved texture references**：日志 body vs 工具 unresolved

- createaddition:block/biomass_pellet_block/block : log=['#west-> #all', '#down-> #all', '#south-> #all', '#east-> #all', '#north-> #all', '#up-> #all'] tool={'down': 'all', 'up': 'all', 'north': 'all', 'east': 'all', 'south': 'all', 'west': 'all'}
- createaddition:item/biomass_pellet_block : log=['#west-> #all', '#down-> #all', '#south-> #all', '#east-> #all', '#north-> #all', '#up-> #all'] tool={'down': 'all', 'up': 'all', 'north': 'all', 'east': 'all', 'south': 'all', 'west': 'all'}
- createdieselgenerators:item/andesite_girder_encased_shaft : log=['#particle-> #layer0'] tool={'particle': 'layer0'}
- dndecor:item/boiler_structure : log=['#particle-> #layer0'] tool={'particle': 'layer0'}


## 5. 修复清单（按 reason：最小修法 + 影响条数）

修复优先级 = 视觉影响 x 修复成本。每条记录的精确路径/id 见 broken.json 的 fix_hint 字段。

| # | reason | 记录数 | 唯一模型 | 影响 | 最小修法 |
|---|---|---:|---:|---|---|
| 1 | cross_atlas_block | 29 | 29 | 整个模型被 Rejecting，方块/物品直接不可见 | 把模型引用的 png 从 textures/item/ 复制到 textures/block/ 同名路径，并把模型里该 slot 改成 ns:block/...（不变图集归属），或把该模型只留在 item 通道使用 |
| 2 | missing_texture | 8 | 8 | 该面/物品画成紫黑 missing | 补 assets/<ns>/textures/<path>.png；若 png 在别处，挪到 textures/item/ 或 textures/block/ 下再改引用 |
| 3 | missing_texture_reference | 410 | 395 | 该 slot 的面/粒子画成 missing（模型仍是方块可见） | 在该模型 textures 里补 slot：particle 指向已有纹理或 #<已定义slot>；interiors 的 "#missing" 需补 missing 纹理 id 或改成真实 slot |
| 4 | unresolved_texture_reference | 14 | 4 | 被引用 slot 无法解析，最终同样画 missing | 把 #slot 指向的目标补上：createaddition 补 "all"；createdieselgenerators/dndecor 是 generated 模型的 particle->#layer0，补 layer0 |
| 5 | missing_model | 10 | 2 | 退回 missing 模型 | 新建被引用的模型 json，或把它改成存在的模型/去掉 parent；minecraft:builtin/entity 除外（见 6） |
| 6 | uv_out_of_bounds | 4 | 1 | FaceBakery.computeTransparency 抛异常，整个 item 模型烘不出来（日志已证实） | tfmg:item/crankshaft 的 uv 在旧 texture_size 坐标空间，把每个 uv 乘 16/texture_size 后重写该模型 |
| 7 | neoforge_texture_size | 1 | 1 | 次级：uv 坐标错位（是否致命待游戏内确认） | 删掉 texture_size 字段并按 16 空间重导模型，或把 uv 缩放到 16 空间 |

按 namespace 的批量修法：interiors（block 34 id / 272 条 + item 34 id）是同一椅子/地板模板漏 "#missing" 定义，
批量脚本补一个 slot 即可；createframed 19 个 package 是同一套 19 张 png 的跨图集问题，批量复制 + 改引用；
createdieselgenerators / aeronautics / simulated 的 particle 缺失同理。

## 6. 误报与可忽略项（不要修）

1. **minecraft:item/*_trim（319 条）曾是工具误报，已修**：items 图集的 paletted_permutations 会在运行时由
   base 纹理 + 调色板生成 sprite id（base + "_" + permutation），工具最初把派生 sprite 当成需要独立 png 而误报。
   修正规则（检查 base png 存在）后该误报为 0；当前 missing_textures 8 条与日志 8 条完全一致。
2. **minecraft:builtin/entity**：原版行为——实体方块（箱子/告示牌等）走 BER，blockstate 引用 builtin/entity
   本来就没有模型 json，日志必然出现这一条，不需要修。
3. **rejecting 日志 32 行 vs 29 个模型**：同一个模型被多个 blockstate state 各 bake 一次，行数是重复计数；
   本工具按唯一模型 id 统计，两边已对齐。
4. **记录数 > 模型数**：同一模型被多个 block/item id 引用时，每条记录对应一个可修复的 id（便于按 id 修），
   例如 interiors block 34 个 id 共 272 条记录。
5. **通道 B（74 个运行时根）不是误报**：Create/Simulated 的 Flywheel PartialModel 在代码里注册模型 id，
   离线无法枚举，工具从日志反推根集合；它们确实在游戏里被 Rejecting / 报缺失，修复清单必须包含。
