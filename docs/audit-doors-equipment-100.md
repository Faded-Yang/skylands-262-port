# 门类联动 + 装备静态审计（100%）

> 2026-10-21 ｜ 范围：live 114 jar ｜ 门数据来自 `g123/doors.json`；装备来自 item 资源 + class 检查

## 1. 门类（107）

| namespace | 总数 | 双半 | 单块 |
|---|---:|---:|---:|
| natures_spirit | 40 | 40 | 0 |
| createframed | 34 | 34 | 0 |
| createdeco | 13 | 13 | 0 |
| create | 7 | 2 | 5 |
| copycats | 6 | 0 | 6 |
| tfmg | 5 | 0 | 5 |
| mynethersdelight | 2 | 0 | 2 |
| **合计** | **107** | **89** | **18** |

### 双半门（89）
blockstate 均含 `half=lower/upper`；`sky262-doorfix` 的 mixin（`BlockBehaviour.playerWillDestroy`，id 含 door + `DOUBLE_BLOCK_HALF`）覆盖；破坏一半会置另一半 air。vanilla/自定义 DoorBlock 已处理时无副作用。

### 单块门（18，破坏即整块消失，无需联动）
`create:andesite_door` / `brass_door` / `copper_door` / `framed_glass_door` / `train_door`；`copycats:copycat_door` / `copycat_folding_door` / `copycat_iron_door` / `copycat_iron_trapdoor` / `copycat_sliding_door` / `copycat_trapdoor`；`mynethersdelight:powdery_door` / `powdery_trapdoor`；`tfmg:aluminum_door` / `heavy_casing_door` / `heavy_plated_door` / `steel_door` / `steel_trapdoor`。

> 注意：create 5 个是**自定义渲染门**（blockstate 只有 particle 模型，几何由 BE/renderer 画），不是 reduced 单块；破坏逻辑由 Create 自身处理。

## 2. 可穿戴物品（21 个 item id）

| id | 注册方式 | 装备槽/用法 |
|---|---|---|
| `create:cardboard_helmet/chestplate/leggings/boots` | Create `BaseArmorItem`（Item + Equippable 组件） | armor 四槽 |
| `create:copper_diving_helmet/boots`、`create:netherite_diving_*` | 同上（Create 装备类） | armor head/feet |
| `create:copper_backtank` / `netherite_backtank` | `BacktankItem extends BlockItem`，静态 `SLOT` | 背部/胸甲（Create 自定义槽） |
| `create:goggles` | `GogglesItem extends Item`（不是 ArmorItem） | Create 自定义 goggles 判定；无 Curios/Trinkets 时不能进 armor 槽 |
| `aeronautics:aviators_goggles` | `AviatorsGogglesItem extends Item` | 自定义物品（非 armor） |
| `create_jetpack:jetpack` / `netherite_jetpack` | `JetpackItem extends Item` | 右键触发推力（不是 armor） |
| `sophisticatedbackpacks:backpack` + copper/iron/gold/diamond/netherite | reduced 件 `sky262.sb.Backpacks` 普通 Item | **当前无 Curios/Trinkets**，不能装备到槽；只能手持/give |
| `waystones:twinbound_feather` | `TwinboundFeatherItem extends Item` | 长按使用（传送目标），非 armor |

### 自动化试穿建议（mcpfabric）
- armor 四槽：`/item replace entity @s armor.head with <id>` / `armor.chest` / `armor.legs` / `armor.feet`；
- 主手/副手：`/item replace entity @s weapon.mainhand with <id>`；
- 背包/goggles：无 Curios/Trinkets 接口，先只验 give/手持与 mod 自身逻辑；
- `player.getState` 可读当前装备/使用状态。

## 3. 后续

- Lead lab 实测门破坏 + 装备试穿；若发现某 reduced 门仍是 plain Block 且 blockstate 无 half，则只能保证单块破坏；
- 装备功能（背包槽、jetpack 装备、goggles 判定）需 Curios/Trinkets 或对应 mod 行为，不在本静态件范围。
