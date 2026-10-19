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
