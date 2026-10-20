# Known Limitations —— skylands-262（MC 26.3 / Fabric 0.19.5）

> 以下为有意保留的降级；均不影响「标题可进 + 世界可进 + 0 crash」基线。

## 装饰：createdeco / Design-n-Decor
- 装饰方块无 BlockEntity、无交互/动画（纯外观）；ponder 未做。
- DnD 剩 72 id 未移植：velvet 32（缺 create seat 贴图，永久跳过）+ 杂项 40（casing/part/slope 等枚举，未尝试）。
- 少量 cosmetic 贴图缺失（如 dndecor:block/display_board），不影响 missing model 判据。
- 部分方块用近似模型/属性降级（属性兜底、原版 placer 等价）。

## natures_spirit
- 树形使用 26.3 原版 placer：NS 自定义 FoliagePlacer/TrunkPlacer/TreeDecorator 未移植（26.3 重构 tree worldgen API，需逐类移植 28 个类，2–4 轮高回归风险，已押后）。
- 2 个自定义 feature type（huge_brown/red_mushroom）数据删除；少量自定义 rule test 用 tag_match 等价替代。
- advancement 502 条，shoot_coconut 跳过（26.3 结构差异）。
- resourcepacks/ 整体移除：Paxi 会把 mod jar 内 resourcepacks 当 datapack 加载，旧 1.21 覆盖会污染 registry（死路）；需要时按 26.3 重建。
- village 结构数据未恢复；地形特征族只恢复 tree/ore/simple_block/vegetation_patch。

## 食物（reduced 类）
- culturaldelights / minersdelight / mynethersdelight：assets+手写注册，部分食物无食用效果/无作物生长逻辑；少数缺 FD 刀板/锅交互扩展。

## 机械 / 机器
- 柴油发电机：43 方块可放置，机器无功能行为（无发电/无流体逻辑）。
- 挤出机：配方/动力连通 PASS，产物渲染/BER 未完成（外观降级）。
- sliceanddice：配方加载、交互可用；部分切割产物模型简化。
- 中央厨房：机械臂×FD 联动为降级实现，ponder 未做。

## CEI ponder（experience 场景）
- `experience/{basic,advance,beacon_base}.nbt` 的旧 1.21 block-entity payload 已移除（26.3 BE schema 不兼容）；场景几何/动画主体保留，**BE 初始状态回退默认**（隧道过滤、传送带内容、粉碎轮库存等），不影响打开与可见性。

## 流体（CEI / DragonsPlus）
- CEI 流体注册已正确（live）；游戏内 `create_enchantment_industry:experience` setblock/读回已 PASS（探针实拍 `fluids_live.png`）。
- DP 保持 live 旧件：新构建仅 create 依赖下限升至 >=6.0.9-4，live create 为 6.0.9-2 ⇒ 不可启动；不升级 create-fly（上游链风险）。

## 结构 / 世界生成
- Awakened Islands：岛用 vanilla StructureTemplate 直接 placed 到世界上空（玩家 +24 或新 chunk y=200），**不是 sable 物理 sublevel**，不会随浮空岛物理体系移动；概率/结构内容与原版一致（同 island1.nbt）；NeoForge Config 未移植（概率硬编码 1/4096）。
- Sophisticated Backpacks / Storage（reduced）：storage 的桶/箱/decoration_table 等 49 个方块外观改为 vanilla cube 近似（原自定义 loader/Blockbench 形状不保留）；物品图标为**扁平 item/generated**（原 mod 自定义 model loader/3D 动态渲染在 26.3 不存在，已统一降级），无紫黑；背包/存储方块与升级**纯外观**，无 GUI/无存储/无升级效果；不依赖 sophisticatedcore；8 个升级模块 item/generated 占位。
- Create: Connected：109 方块**纯外观**（无 BlockEntity/无机械行为/无流体）；data 全丢（无配方/无 tag）；9 个 copycat 系列方块模型缺 → cube_all 近似；创造栏页签存在但 probe 未见截图（探针 tab 定位限制）。
- Sable x Create Additions Compat：mixin 为 best-effort（`defaultRequire=0`，注入失败仅 WARN 不崩溃）；跨子世界接线行为未深度验证（手测项）；已丢弃目标缺失的 2 个 client mixin（LiquidBlazeBurner/WireNode）。
- Create: Hangars：结构已可生成；**loot_table 已移除**（机库内箱子无战利品，细节押后）。
- No Void Structures：已验证「数据加载 + 世界可进 + /locate structure 返回坐标（village_plains/pillager_outpost/swamp_hut）」；结构不在虚空生成的目标行为待浮空岛地图验证。
- 浮空岛世界（aeronautics/sable）结构/地形仍降级：simulated 实体缺 EntityRenderer（honey_glue 首帧 NPE 历史问题）。

## 任务系统
- titleItem 为 air 的条目走 fallback 显示英文物品名（Sandworm gauntlet / Ice gauntlet），不出现「空气」但非中文；需补 zh_cn 键。
- 少数任务格标题回退到任务标题（原 icon 缺失），属数据问题非 GUI bug。

## 平台 / 验证
- 语言加载为全局硬依赖：任一 mod lang JSON 坏都会让所有 mod lang 失效（已修两处；新增件必须跑 tools/lang_audit.py）。
- 26.3 worldgen 数据 schema 与 1.21 差异大（feature 平铺 / provider 数据化 / configured_feature 目录改名 / noise firstOctave→base_octave / placement random_offset→offset / blockstate id-properties），数据包类件必须按 docs/api-landmines.md 校验。
- 所有件仅验证「标题 + 进世界 + 抽样 MCP」；未做长时稳定性/存档兼容/多人测试。

## 液体燃料：portable_engine_liquid_fuel / createliquidfuel（占位，待行为移植）
- 两件均为**纯行为 addon**（`data_maps/fluid/*.json` + mixin；无 assets/方块/物品）；当前交付为**兼容壳（shell）**，只保证 mod id/依赖/加载，**无任何数据或行为**。
- `portable_engine_liquid_fuel` 2.0.0：目标行为 = simulated PortableEngine 熔岩罐 burn_time（lava 20000；super fuel 表），需 mixin 26.3 simulated；
- `createliquidfuel` 3.0.0：目标行为 = Create BlazeBurner 流体燃料接入（liquid_fuel.json：lava/createaddition 油等），需 mixin 26.3 create-fly + 流体接入；
- **验收口径**：仅加载/进世界/0 crash；无方块/物品可 give/setblock，不做功能判定。
- 行为移植排在「用户手测反馈之后」优化批次，每项约 2 轮。

## TFMG（The Factory Must Grow，reduced 分批）
- 机器/BlockEntity/流体方块退化为**静态装饰方块**（无功能、无 BE、整块碰撞）；
- recipe/loot/advancement/tags/worldgen 数据未恢复；复杂多状态方块合并为单默认 variant；
- 分批累积件，旧 ids 只增不减；模型/贴图缺失按批统计，属 cosmetic。

## sophisticated backpacks / storage（壳）
- 背包/升级**无 GUI、无存储功能**（右键无反应）；storage 59 方块纯装饰、无 BE。
- item 图标重建为 vanilla `item/generated`（原 mod 走自定义 model loader，26.3 无该 loader 会紫黑）；外观为扁平图标，非原 3D/dynamic 渲染。
- 不依赖 sophisticatedcore（reduced 版手写注册，fmj 无 core 依赖）。

## ponder 入口：CEI `create:experience_nugget` 不可用（其余 6 个入口正常）

- 现象：`/ponder create:experience_nugget` → 聊天回执 `No value present`，界面不打开；
- 根因：`create_enchantment_industry/ponder/experience/{basic,advance,beacon_base}.nbt` 是 1.21.1 旧 block-entity 数据（Direction 存 int、枚举大写 ANDESITE/WAITING/PUNCH、旧 ItemStack `{Slot,count,id}`），26.3 `PonderSceneRegistry.compile` 放结构时 `ServerSidedFilteringBehaviour.read` 的 `Direction.CODEC` 解析失败 → `Optional.orElseThrow`；
- 尝试过：palette 迁移（已生效，语言/方块显示恢复）、移除 141–146 处 `blocks[].nbt`（会另触发 StackOverflowError）；
- 现状：保留原始 nbt；受影响仅该条目，`blaze_enchanter` / `super_experience_nugget` / `cogwheel` 等入口正常；
- 后续可行路径：写完整的 1.21.1→26.3 block-entity NBT 转换（枚举小写、Direction int→string、旧 ItemStack→`{id,count,components}`），可复用 `tools/convert_121_data.py` 的映射表。