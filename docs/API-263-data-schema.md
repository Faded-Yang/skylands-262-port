# 26.3 数据（datapack）schema 变更清单

> 来源：把 natures_spirit 2.3.0（26.1.2 数据）搬进 26.3 时逐层踩出来的。适用于任何"旧数据包 + 26.3"的移植。

## 1. 目录/注册表改名

| 旧 | 26.3 |
|---|---|
| `data/<ns>/worldgen/configured_feature/**` | `data/<ns>/worldgen/feature/**`（vanilla 已无 `configured_feature`） |
| `data/<ns>/tags/worldgen/configured_feature` | `tags/worldgen/feature` |

放错目录的表现：`Unbound values in registry ... worldgen/feature: [ns:xxx]`，但文件确实在 jar 里。

## 2. biome JSON（26.3 必填项）

```json
{
  "attributes": {},
  "carvers": [],
  "effects": { "foliage_color": "#rrggbb", "grass_color": "#rrggbb", "water_color": "#rrggbb" },
  "features": [[],[],[],[],[],[],[],[],[],[],[]],
  "has_precipitation": true,
  "temperature": 0.8,
  "downfall": 0.4
}
```

- **features 必填**（11 个 step 的 list，缺失报 `No key features`）；
- **carvers 必填**，类型是 HolderSet codec：`[]` 合法、`{}` 非法；
- `effects` 颜色是 **STRING_RGB_COLOR** `"#rrggbb"`（旧版 int 会 parse 失败）；
- `spawners`/`spawn_costs` 已并入 `attributes`。

## 3. 方块状态（entity/block predicate 里）

| 旧 | 26.3 |
|---|---|
| `{"Name":"minecraft:birch_sapling","Properties":{"stage":"0"}}` | `{"id":"minecraft:birch_sapling","properties":{"stage":"0"}}` |
| 无属性块 | 可直接写字符串 `"minecraft:stone"` |

**必须递归转换**：不只是 feature 的顶层，还要进 `placement[].predicate.state` 这类嵌套位置（漏了会只剩少数元素报错）。

## 4. worldgen 其它字段

| 旧 | 26.3 |
|---|---|
| noise `firstOctave` | `base_octave` |
| placement modifier `minecraft:random_offset` + `{xz_spread,y_spread}` | `minecraft:offset` + `{x,y,z}`（x=z=xz_spread） |

## 5. feature config 新增必填字段（26.3）

残缺 feature JSON 会报 `No key <field>`：

- tree：`below_trunk_provider`（如 `{"type":"minecraft:simple_state_provider","state":{"id":"minecraft:dirt"}}`）
- ore：`discard_chance_on_air_exposure`（通常 `0.0`）
- 其它：`default` / `to_place` / `features` / `can_place_on` / `half_height` / `prioritize_tip` / `extra_edge_column_chance`

做法：按 `type` 分组，用 26.3 vanilla 同 type 的 JSON 当模板补默认值。

## 6. loot_table / recipe / advancement

- loot condition `minecraft:block_state_property` 在 26.3 的 `loot_condition_type` 注册表里已不存在（需查 `LootItemConditionType` 找新 id）；
- advancement 的 `conditions` 从数组改成对象；
- recipe 的 ingredients 结构也变了。

**"保世界"裁剪顺序**（先让世界能进，再补内容）：

1. 删 `worldgen/feature|placed_feature|structure|structure_set|template_pool`（保留 biome，features 置空）；
2. 删 `advancement`、`recipe`（回落到原版）；
3. 删 `loot_table`。

每步都会暴露下一层 schema 差异；逐层用「第一行 `Caused by` + 原版同 type JSON 对照」定位，不要盲改。

## 7. 数据源教训

源码构建（mixin/移植版）的 jar 可能比发布 jar **少上千条 data**（本次少了 1823 条：recipe 831、advancement 513、worldgen 479）。做数据移植时**数据一律从原发布 jar 取**，类用源码构建。


## 26.3 loot table schema 迁移（crashfix-26，2026-10-20）

### 注册名来源（refs 路径）
- loot condition 类型注册表：`BuiltInRegistries.LOOT_CONDITION_TYPE`（注册键 `minecraft:loot_condition_type`），bootstrap 位于
  `work/refs/mc26.3/net/minecraft/world/level/storage/loot/predicates/LootItemConditionTypes.java`；
- loot function 类型注册表：`BuiltInRegistries.LOOT_FUNCTION_TYPE`，bootstrap `.../loot/functions/LootItemFunctions.java`；
- 26.3 condition ids（原始字符串）：inverted, any_of, all_of, random_chance, random_chance_with_enchanted_bonus, entity_properties, killed_by_player, entity_scores, match_block, match_tool, table_bonus, survives_explosion, damage_source_properties, location_check, weather_check, time_check, int_value_check, float_value_check, enchantment_active_check, environment_attribute_check。

### condition id 映射（1.21.x → 26.3）
| 旧 id | 26.3 id | 备注 |
|---|---|---|
| `minecraft:block_state_property` | `minecraft:match_block` | 字段 `block`→`blocks`，`properties`→`state`（值格式同 StatePropertiesPredicate） |
| `minecraft:match_tool` | `minecraft:match_tool` | 旧 `predicate` 改为 ItemPredicate 平铺字段（`items`/`count`）；常用形态直接换引用串：shears→`minecraft:tool/can_shear`、silk_touch→`minecraft:tool/can_silk_touch` |
| survives_explosion / any_of / all_of / inverted / random_chance / table_bonus / location_check / entity_properties / killed_by_player / entity_scores / damage_source_properties / weather_check / time_check | 同名 | 仅 `condition` 键改 `type`；term/terms 递归 |

### JSON 结构变化
- 条件对象：`"condition": "<id>"` → `"type": "<new id>"`；条件可以是**引用字符串**（item modifier 条件，如 `"minecraft:tool/can_shear"`）；
- 函数对象：`"function": "<id>"` → `"type": "<id>"`；
- 条目的 `conditions` 列表 → `condition`（单个）；多条件合并为 `{"type":"minecraft:all_of","terms":[...]}`；
- 条目的 `functions` 列表 → `modifier`（单元素对象或列表）；
- `match_block` 示例：`{"type":"minecraft:match_block","blocks":"natures_spirit:aspen_door","state":{"half":"lower"}}`；
- `match_tool` 示例（保留非标准形态）：`{"type":"minecraft:match_tool","items":"#minecraft:cluster_max_harvestables"}`；
- `location_check` 内 `predicate.block` 使用 BlockPredicate（`blocks`/`state`/`nbt`/components）；
- loot function ids 仍为：set_count / explosion_decay / apply_bonus / limit_count / copy_components / copy_state 等（名字未变，仅 `function`→`type`）；copy_components 的 `include`/`exclude` 可省略，`source` 必填。

### NS loot_table 恢复（步骤 2）
- 原包 720 个 `data/natures_spirit/loot_table/**`，按上述规则程序化转换（脚本 `work/_ns_loot_conv.py`）；
- 只恢复 `natures_spirit` 命名空间，跳过 `data/minecraft/**` 覆盖；候选：`g70/out/natures_spirit-fabric-2.3.0-26.3-loot1.jar`；
- 首测：进世界 + registry 错误数待验。

## 8. NS 数据迁移踩坑补充（A1–A15 实战）

- **26.3 的 feature JSON 没有 `config` 包装层**：字段平铺在顶层（旧格式 `{"type":..., "config": {...}}` 会导致 "No key ..." 的一长串报错，看着像字段缺失，其实在 config 里嵌套）；
- **block state provider 是数据注册表**：`data/<ns>/worldgen/block_state_provider/<name>.json`，类型名是 `minecraft:weighted` / `minecraft:noise`（无 `_provider` 后缀）；feature 里用字符串 id 引用；
- **foliage_placer / trunk_placer / tree_decorator 的 type 是代码注册表**（构造器 private，需要 accessor mixin 或反射注册自定义类型）；
- ⚠ **Paxi 会把 mod jar 里的 `resourcepacks/**` 当作 datapack 加载**：旧 1.21 数据包覆盖会污染 registry（表现为原版 `minecraft:birch` 等也解析失败）。移植时要么删除 jar 内 `resourcepacks/`，要么把它们按 26.3 格式重写；
- 删 feature/placed_feature 后**必须级联过滤** `biome.features` 与引用方，否则出现悬空引用（unbound）。