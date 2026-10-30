# port-batch3 —— `configured_feature` 逐类型转换器 + 第五批移植

> 日期：2026-10-18 ｜ 目标：MC **26.3** + Fabric Loader 0.19.5 + Java 25
> 验收口径：**`WORLD_OK` = `logged in with entity id`（真进世界）**；标题 = `launch.py --watch-title` 三条标记全中。
> 每个 mod 都必须同时有「标题 + 进世界」两条实测；promote 后**在交付物本体（`mods-stable`）上复跑标题**。

---

## 0. 结论（先进世界，再谈其他）

| 结果 | 等级 | mod | 进世界 | 标题 |
|---|---|---|---|---|
| ✅ 新增 | **A** | `strayed-fates-forsaken` 2.0.0.2 | `WORLD_OK` 36.2 s | `TITLE_SCREEN_OK` 24.0 s |
| ✅ 新增 | **A** | `imst`（Immersive Structures）2.2.1c | `WORLD_OK` 36.2 s | `TITLE_SCREEN_OK` 24.8 s |
| ✅ 新增 | **A** | `Structory_Towers` 1.0.17（26.2 构建） | `WORLD_OK` 36.2 s | `TITLE_SCREEN_OK` 26.0 s |
| ✅ 新增 | **B** | `sablephysicscompat` 1.3.0 | `WORLD_OK` 36.2 s | `TITLE_SCREEN_OK` 25.1 s |
| ⛔ 缺口 | **D** | `natures_spirit` 2.2.6-1.21.1 | `FAIL_REGISTRY`（见 §6） | — |

> 等级口径：**A** = 数据全量生效、日志 0 报错；**B** = 能进世界、数据全部解析成功，
> 但生效面受「它针对的 mod 不在本整合包」限制（sablephysicscompat 的 selector 大多指向
> `aether` / `twilightforest` / `natures_spirit` 等未安装的方块）；**C** = 能进但内容被静默丢弃；
> **D** = 进不了世界（含必须 Java 移植）。

- **`mods-stable`：54 jar → 58 jar**（+4）。
- 核心产出：`tools/convert_features_121.py`（**type→字段变更表 16 条** + 全自动转换）+
  `tools/feature_schema_263.py`（从 26.3.jar 机械反查 **57 个 feature type 的字段全表**，见 §3）。
- 附带修了 3 个既有工具的 bug（§7），新增 1 个工具（`fix_sable_data_121.py`）。

---

## 1. 26.3 的 `configured_feature` 到底变成了什么（全部来自 26.3.jar 实测）

1. **目录改名**：`data/<ns>/worldgen/configured_feature/x.json` → `data/<ns>/worldgen/feature/x.json`。
   26.3 里 `configured_feature` 目录**完全不被读取**（旧目录放着不报错、也不加载）。
2. **`config` 扁平化**：26.3 每个 feature 类本身就是 record 并**直接实现 `Feature` 接口**，
   所以 1.21 的 `{"type": .., "config": {…}}` 要写成 `{"type": .., …配置字段平铺…}`。
3. **方块状态**：`{"Name":..,"Properties":{..}}` → `{"id":..,"properties":{..}}`（26.3 也接受字符串 `"ns:block[prop=v]"`）。
4. **state provider 合并改名**（26.3 `BlockStateProviderTypes` 全表：`simple / weighted / rotated /
   rule_based / noise / noise_threshold / dual_noise / random_block / randomized_int / copy_properties`）。
5. **四个 feature type 被删**（26.3 `FeatureTypes.bootstrap` 里查不到）：
   `minecraft:random_patch` / `minecraft:flower` / `minecraft:no_bonemeal_flower` / `minecraft:forest_rock`。
   前三个的语义（`tries`/`xz_spread`/`y_spread` 的区域播种）**搬到了 placed_feature 的 placement 里**
   （`count` + `offset`）——证据：26.3 原版 `placed_feature/patch_grass_plain.json` 在 `biome` 之后多了
   `{"type":"count","count":32}` + `{"type":"offset", x/y/z = trapezoid(±7/±3/±7)}`，而
   `feature/grass.json` 只剩 `{"type":"minecraft:simple_block","to_place":{"id":"minecraft:short_grass"}}`。
   `forest_rock` 则变成 `minecraft:block_blob`（多一个必填 `can_place_on`）。
6. **per-type 字段变化**：见 §2 表（最要紧的是 `tree` 的 `dirt_provider`+`force_dirt` →
   `below_trunk_provider`，和 `lake` 新增 3 个**必填** predicate）。
7. 额外发现（不在 configured_feature，但同一批数据会撞）：**biome 的 `carvers`**
   1.21 是 `{"air":[…],"liquid":[…]}`，26.3 原版 `plains.json` 是**扁平数组**。
   旧写法报错原文：`Carver: Failed to parse either. First: Not a string: {"air":[...]}`。

---

## 2. type → 字段变更表（16 条，**可复用资产**；`python tools/convert_features_121.py --dump-table` 可打印）

| # | type | 1.21.x | 26.3 | 处理 |
|---|---|---|---|---|
| 1 | **（通用）** | `{"type":..,"config":{…}}` | `{"type":.., …平铺…}` | 扁平化 `config` |
| 2 | `minecraft:random_patch` | `{feature:<PlacedFeature>, tries, xz_spread, y_spread}` | **类型已删** | 内层 feature 提升；`tries/xz/y` → 引用方 placement 的 `count`+`offset`(+内层 placement) |
| 3 | `minecraft:flower` | 同上 | **类型已删** | 同上（原版 `flower_default` 是 64/7/3） |
| 4 | `minecraft:no_bonemeal_flower` | 同上 | **类型已删** | 同上 |
| 5 | `minecraft:forest_rock` | `{state}` | `minecraft:block_blob {state, can_place_on}` | 改名 + 补 `can_place_on: {type:matching_block_tag, tag:minecraft:forest_rock_can_place_on}` |
| 6 | `minecraft:tree` | `dirt_provider` + `force_dirt` | `below_trunk_provider`（**必填**，`Holder<BlockStateProvider>`，可直接写 `"minecraft:soil_beneath_tree"`） | `force_dirt=true` 时取 `dirt_provider`，否则用 `soil_beneath_tree`；`force_dirt` 删除 |
| 7 | `minecraft:lake` | `{barrier, fluid}` | 另加**必填** `can_place_feature` / `can_replace_with_air_or_fluid` / `can_replace_with_barrier` | 按 26.3 原版 `lake_lava` 默认值补齐 |
| 8 | `minecraft:disk` | `state_provider` 可写无 `type` 的 `{fallback, rules}` | 必须 `{"type":"minecraft:rule_based",…}` | 补 `type` |
| 9 | `minecraft:block_pile` / `simple_block` / `vegetation_patch` / `ore` / `scattered_ore` / `root_system` | `simple_state_provider` / `weighted_state_provider` | 裸方块状态 / `weighted` | state provider 塌缩（见 #10） |
| 10 | **（所有 state provider）** | `weighted_state_provider` / `noise_state_provider` / `dual_noise_provider` / `noise_threshold_provider` / `rotated_block_provider` / `randomized_int_state_provider` / `random_block_state_provider` / `copy_properties_provider` | `weighted` / `noise` / `dual_noise` / `noise_threshold` / `rotated` / `randomized_int` / `random_block` / `copy_properties` | 改名；`simple_state_provider` → 裸状态 |
| 11 | `minecraft:random_selector` / `simple_random_selector` / `sequence` / `overlay` / `random_boolean_selector` | 内嵌 `PlacedFeature`（`{feature:{type,config}, placement}`） | 内层同样要扁平化 | 递归处理内嵌 configured feature |
| 12 | **（方块状态）** | `{"Name","Properties"}` | `{"id","properties"}` | 键名小写 |
| 13 | **（IntProvider）** | `{"min":a,"max":b}` | `{"type":"minecraft:uniform","min_inclusive":a,"max_inclusive":b}` | 补 type + 改键名 |
| 14 | **（placement）** | `random_offset {xz_spread,y_spread}` / `offset {xz,y}` | `offset {x,y,z}`（各是 IntProvider） | 合并 |
| 15 | **（biome 文件）** | `carvers: {"air":[…],"liquid":[…]}` | `carvers: […]`（扁平数组） | 合并两层 |
| 16 | **（原版 feature id 引用）** | `patch_grass` / `patch_red_mushroom` / `patch_taiga_grass` / `patch_waterlily` … | `grass` / `red_mushroom` / `taiga_grass` / `waterlily` …（24 条映射内置） | 引用改名 + 按 #2 注入播种参数 |

---

## 3. 26.3 feature type 字段全表（57 个 type，机械反查自 26.3.jar 的 MapCodec）

> 生成方式：`python tools/feature_schema_263.py --out schema263.json`
> （javap 反汇编每个 feature 类的 `lambda$static$0`，抓 `ldc "字段名"` + `fieldOf/optionalFieldOf`；
> 带 `?` = `optionalFieldOf`，即非必填。父类建 codec 的会自动跟一层继承。）
> 用途：新 mod 撞到没见过的 type 时，先查这张表，能直接看出**缺哪个必填字段/多了哪个不存在的字段**。

| type | 26.3 字段（`?` = 可选） |
|---|---|
| `bamboo` | `probability` |
| `block_blob` | `state`, `can_place_on` |
| `block_column` | `layers`, `allowed_placement`, `prioritize_tip` |
| `block_pile` | `state_provider` |
| `blue_ice` | （无字段） |
| `bonus_chest` | （无字段） |
| `chorus_plant` | （无字段） |
| `coral_claw` | `feature` |
| `coral_tree` | `feature` |
| `delta_feature` | `contents`, `rim`, `size`, `rim_size` |
| `disk` | `state_provider`, `target`, `radius`, `half_height` |
| `end_gateway` | `exit`?, `exact` |
| `end_island` | （无字段） |
| `end_platform` | （无字段） |
| `end_podium` | `active`? |
| `end_spike` | `spikes`, `crystal_invulnerable`?, `crystal_beam_target`? |
| `fallen_tree` | `trunk_provider`, `log_length`, `stump_decorators`, `log_decorators` |
| `fill_layer` | `height`, `state` |
| `fossil` | `fossil_structures`, `overlay_structures`, `fossil_processors`, `overlay_processors`, `max_empty_corners_allowed` |
| `freeze_top_layer` | （无字段） |
| `geode` | `blocks`, `layers`, `crack`, `use_potential_placements_chance`?, `use_alternate_layer0_chance`?, `placements_require_layer0_alternate`?, `min_gen_offset`?, `max_gen_offset`?, `noise_multiplier`?, `invalid_blocks_threshold` |
| `huge_brown_mushroom` | `cap_provider`, `stem_provider`, `foliage_radius`?, `can_place_on` |
| `huge_fungus` | `valid_base_block`, `stem_state`, `hat_state`, `decor_state`, `replaceable_blocks`, `planted`? |
| `huge_red_mushroom` | `cap_provider`, `stem_provider`, `foliage_radius`?, `can_place_on` |
| `iceberg` | `state` |
| `lake` | `fluid`, `barrier`, `can_place_feature`, `can_replace_with_air_or_fluid`, `can_replace_with_barrier` |
| `large_dripstone` | `replaceable_blocks`, `floor_to_ceiling_search_range`?, `column_radius`, `height_scale`, `max_column_radius_to_cave_height_ratio`, `stalactite_bluntness`, `stalagmite_bluntness`, `wind_speed`, `min_radius_for_wind`, `min_bluntness_for_wind` |
| `monster_room` | （无字段） |
| `multiface_growth` | `block`, `search_range`?, `can_place_on_floor`?, `can_place_on_ceiling`?, `can_place_on_wall`?, `chance_of_spreading`?, `can_be_placed_on` |
| `netherrack_replace_blobs` | `target`, `state`, `radius` |
| `no_op` | （无字段） |
| `ore` | `targets`, `size`, `discard_chance_on_air_exposure` |
| `overlay` | `features` |
| `random_boolean_selector` | `feature_true`, `feature_false` |
| `random_neighbor_spread` | `block`, `accepted_neighbors`, `can_replace`, `attempts`, `xz_offset`, `y_offset` |
| `random_selector` | `features`, `default` |
| `replace_single_block` | `targets` |
| `root_system` | `feature`, `required_vertical_space_for_tree`, `level_test_distance`, `max_level_deviation`, `root_radius`, `root_replaceable`, `root_state_provider`, `root_placement_attempts`, `root_column_max_height`, `hanging_root_radius`, `hanging_roots_vertical_span`, `hanging_root_state_provider`, `hanging_root_placement_attempts`, `allowed_vertical_water_for_tree`, `allowed_tree_position` |
| `scattered_ore` | `targets`, `size`, `discard_chance_on_air_exposure` |
| `sculk_patch` | `charge_count`, `amount_per_charge`, `spread_attempts`, `growth_rounds`, `spread_rounds` |
| `sequence` | `features` |
| `simple_block` | `to_place`, `schedule_tick`? |
| `simple_random_selector` | `features` |
| `single_block_pillar` | `block`, `can_replace`?, `direction`, `chance_to_continue`?, `cap_feature`? |
| `speleothem` | `base_block`, `pointed_block`, `replaceable_blocks`, `chance_of_taller_generation`?, `chance_of_directional_spread`?, `chance_of_spread_radius2`?, `chance_of_spread_radius3`? |
| `speleothem_cluster` | `base_block`, `pointed_block`, `replaceable_blocks`, `floor_to_ceiling_search_range`, `height`, `radius`, `max_stalagmite_stalactite_height_diff`, `height_deviation`, `speleothem_block_layer_thickness`, `density`, `wetness`, `chance_of_speleothem_at_max_distance_from_center`, `max_distance_from_edge_affecting_chance_of_speleothem`, `max_distance_from_center_affecting_height_bias` |
| `spike` | `state`, `can_place_on`, `can_replace` |
| `spring_feature` | `state`, `requires_block_below`?, `rock_count`?, `hole_count`?, `valid_blocks` |
| `stepped_column_cluster` | `block`, `continue_through`, `can_replace`, `cannot_place_on`, `cluster_reach`, `column_count`, `column_reach`, `height` |
| `template` | `templates`, `processors`? |
| `tree` | `trunk_provider`, `trunk_placer`, `foliage_provider`, `foliage_placer`, `root_placer`?, `minimum_size`, `decorators`, `ignore_vines`, `below_trunk_provider` |
| `underwater_magma` | `floor_search_range`, `placement_radius_around_floor`, `placement_probability_per_valid_position` |
| `vegetation_patch` | `replaceable`, `ground_state`, `vegetation_feature`, `surface`, `depth`, `extra_bottom_block_chance`, `vertical_range`, `vegetation_chance`, `xz_radius`, `extra_edge_column_chance` |
| `vines` | （无字段） |
| `void_start_platform` | （无字段） |
| `waterlogged_vegetation_patch` | `replaceable`, `ground_state`, `vegetation_feature`, `surface`, `depth`, `extra_bottom_block_chance`, `vertical_range`, `vegetation_chance`, `xz_radius`, `extra_edge_column_chance` |
| `weighted_random_selector` | `features` |

---

## 4. `tools/convert_features_121.py`

```
python tools/convert_features_121.py <in.jar> <out.jar> [--report r.json] [--dry-run]
python tools/convert_features_121.py --dump-table        # 只打印 §2 的变更表
```

流程（三遍，保证「引用方」能在被引用方转完之后再注入播种参数）：

1. **第 1 遍**：登记所有 `configured_feature/*.json`，先记下 patch 类的 `(tries, xz_spread, y_spread, 内层 placement)`。
2. **第 2 遍**：逐个转成 `feature/*.json`：扁平化 `config` → 按 type 分派（patch 拆壳 / forest_rock 改名 /
   tree 换 dirt / lake 补 predicate）→ 递归 walk（方块状态、state provider、IntProvider、placement）。
3. **第 3 遍**：扫**其余所有** `data/**/worldgen/*.json`，处理内嵌 `PlacedFeature`
   （`template_pool` 的 `feature_pool_element`、`random_selector.default`、`vegetation_patch.vegetation_feature`…）：
   feature 引用改名 + 若是 patch 类引用就把播种参数追加到 `placement` 末尾；biome 的 `carvers` 扁平化。

设计取舍：**只重写真的变了字节的 JSON**，其余按原字节写回（避免无意义 diff）。
同一个 jar 里 `configured_feature/` 条目会被删掉、`feature/` 条目新增。

---

## 5. 每个 mod 的 A/B/C/D（过程 → 结果，全部是实测原文）

### A. `strayed-fates-forsaken` 2.0.0.2 ✅
- **原状**：Fabric 数据包，0 class，307 JSON。10 个 `configured_feature`（7×lake + 3×random_patch）、
  27 structure、249 template_pool、70 processor_list、1221 个 `.nbt` 模板。
- **失败原文**（上一轮交付的 `-datafix3.jar`）：
  ```
  Unbound values in registry ResourceKey[minecraft:root / minecraft:worldgen/feature]:
  [forsaken:cobweb_lake_empty, …, minecraft:patch_grass, minecraft:patch_red_mushroom,
   minecraft:patch_taiga_grass, minecraft:patch_waterlily, forsaken:underground_patch_frogspawn, …]
  ```
  ⇒ ① 10 个 feature 还在 `configured_feature/` 没被读；② 它的 `template_pool/*/feature/*.json`
  用内嵌 PlacedFeature 引用了 26.3 已改名的 `minecraft:patch_grass` 等。
- **处理**：`convert_features_121`（10 feature / 53,676 处方块状态（绝大多数在 processor_list）/
  15 处 `random_offset` / 21 处 lake predicate / 9 处 patch 播种注入 / 0 biome）
  → 再跑 `convert_121_data`（spawn_overrides、剩余 IntProvider）→ `fix_loot_121` → `fix_entity_predicates`。
- **结果**：`WORLD_OK 36.2s`，`TITLE_SCREEN_OK 24.0s`；日志里 `strayed_fates_forsaken` 相关 ERROR 0 条。

### B. `imst` 2.2.1c ✅
- **原状**：NeoForge，3 个 class（只有 `@Mod` 入口，mixins 是空的）⇒ 纯数据，`neoforge_to_fabric --keep data,assets`。
  5 个 `configured_feature`（2×tree / 2×block_pile / 1×random_selector）、8 placed_feature、34 structure。
- **失败 1（第一次测试）**：
  ```
  Unbound values in registry …worldgen/structure: [imst:el_dorado]
  → Caused by: Failed to parse either. First: Not a number: {"type":"minecraft:uniform","min":1,"max":3};
    Second: No key max_inclusive in MapLike[…]
  ```
  ⇒ 不是 feature 层，是 **`spawn_overrides` 的 `count`**：`convert_121_data` 把 `minCount/maxCount`
  写成 `{"type":"minecraft:uniform","min":…,"max":…}`，而 26.3 要 `min_inclusive/max_inclusive`。
  **已在 `convert_121_data.py` 里修掉**（§7）。
- **处理**：修完重跑链路（`convert_features_121` 5 feature / 81 state / 5 flatten / 2 tree below_trunk /
  1 patch 注入）→ `WORLD_OK`。
- **结果**：`WORLD_OK 36.2s`，`TITLE_SCREEN_OK 24.8s`。

### C. `Structory_Towers` 1.0.17（26.2 构建）✅
- **原状**：双 loader 数据包，0 class，0 `configured_feature`；22 structure / 30 template_pool / 49 loot_table。
- **上一轮的判断是错的**：`AGENTS.md` 记「还差结构/模板池那一层」。
  本轮实测：**26.1.2 → 26.3 的 `worldgen/structure` 与 `worldgen/template_pool` 顶层字段集合完全一致**
  （逐文件对比 26.1.2.jar 与 26.3.jar 的 34/52 个 structure、105/144 个 template_pool；`step` /
  `element_type` / `processor_type` 的取值集合也没变）。
- **真正原因**（失败原文）：
  ```
  > Errors in registry minecraft:loot_table:
  >> Errors in element structory_towers:potions/darkness:
     Caused by: IllegalStateException: No component with type: 'minecraft:hide_additional_tooltip';
     missed input: {"minecraft:hide_additional_tooltip":{}}
  ```
  4 张 `potions/*` loot table 用了 1.21 的物品组件 `hide_additional_tooltip`，26.3 已并入 `tooltip_display`。
- **处理**：`fix_loot_121` 增加映射 `hide_additional_tooltip` → `{"minecraft:tooltip_display":{"hide_tooltip":true}}`
  （代价：连物品名一起隐藏，纯展示层）。其余按标准链路（`convert_121_data` 修了 483 处 IntProvider + spawn_overrides）。
- **结果**：`WORLD_OK 36.2s`，`TITLE_SCREEN_OK 26.0s`。

### D. `sablephysicscompat` 1.3.0 ✅
- **原状**：NeoForge，0 class，43 条 data（26 个 block tag + 14 个 `physics_block_properties` + `floating_materials`）。
  上一轮记的是 `FAIL_TIMEOUT`、无 crash-report。
- **关于那次超时**：本轮**没能复现**——用全新验收世界副本、同一套基线，第一次跑就是
  `WORLD_OK 36.2s`（只是数据被静默丢弃）。按 R377 的记录，那个超时最可能是**验收世界被标成实验性**
  后卡在确认框（日志停在 `Loaded N advancements`，伪装成超时），不是 mod 本身；
  所以没用 `-Xlog:class+load` 二分——没有卡住的东西可分。
- **实测到三个独立原因**（都不是超时，是「数据被静默丢弃」）：
  1. `neoforge_to_fabric` 的 TOML 解析**没剥行尾注释** ⇒ 生成的 `fabric.mod.json` 里
     `"id": "\"sablephysicscompat\" #mandatory"`（非法 id）。
  2. tag JSON 里同时有 `//` 行注释与尾逗号 ⇒ 26.3 用 Gson `StrictJsonParser`：
     ```
     Couldn't read tag list sable:bouncy … Caused by: MalformedJsonException … path $.values[7]
     ```
  3. `physics_block_properties/*.json` 在 26.3 是**单个对象**（`{selector, properties, overrides?}`），
     而 addon 写的是**数组**：
     ```
     Couldn't parse data file 'sable:float' from 'sable:physics_block_properties/float.json':
     DataResult.Error['Not a JSON object: [{"selector":"aether:enchanted_gravitite",…'
     ```
- **处理**：修 `neoforge_to_fabric`（§7）+ 新工具 `tools/fix_sable_data_121.py`
  （去 `//` 注释 + 去尾逗号 + 把数组按条目拆成 `<stem>_splitN.json`：13 条）。
- **结果**：`WORLD_OK 36.2s`，`TITLE_SCREEN_OK 25.1s`；日志里 `sablephysicscompat` 的 ERROR 从
  **5 条（4 个 tag 读取失败 + 1 个 `physics_block_properties` 解析失败）降到 0 条**
  （只剩一条 `Found new data pack sablephysicscompat`）。

---

## 6. 缺口：`natures_spirit` 2.2.6-1.21.1（**数据层可转，Java 层不可绕**）

- **它不是数据包**：NeoForge 1.21.1，**202 个 class**、`neoforge.mods.toml`、`accesstransformer.cfg`、
  `natures_spirit.mixins.json`，没有 `fabric.mod.json`。
- **数据层已完全跑通转换器**（`ns-1.jar`）：
  176 个 feature（45 patch + 2 forest_rock + 35 tree）、220 placed_feature、51 biome、
  278 处 config 扁平化、153 处 simple_state_provider、31 处 random_offset、60 处 patch 播种注入、
  47 个 biome 的 `carvers` 扁平化、753 处方块状态。
- **但它 2,671 个 data JSON 里引用了 1,527 个自己的 id**，这些**只能由那 202 个 class 注册**。
  data-only jar（`ns-4.jar`，已修 carvers）实测的**失败原文**（三条并存的硬原因）：
  ```
  Unknown registry key in ResourceKey[minecraft:root / minecraft:worldgen/feature_type]:
      natures_spirit:alluaudia_feature / natures_spirit:large_pumpkin_feature …
  Unknown registry key in ResourceKey[minecraft:root / minecraft:worldgen/foliage_placer_type]:
      natures_spirit:aspen_foliage_placer / natures_spirit:grounded_bush_foliage_placer
  Unknown registry key in ResourceKey[minecraft:root / minecraft:worldgen/tree_decorator_type]:
      natures_spirit:wisteria_vines_tree_decorator
  Unbound values in registry …minecraft:worldgen/biome:
      [natures_spirit:blooming_sugi_forest, natures_spirit:chaparral, natures_spirit:drylands, natures_spirit:sugi_forest]
  ```
  ⇒ 它**不只注册方块**，还注册了自己的 feature type / foliage placer / tree decorator（都是 codec 级扩展），
  数据层无法替代。
- **结论**：natures_spirit 必须走 **Java 移植**（1.21.1 NeoForge → 26.3 Fabric，202 class），
  不是数据转换能解决的。**本轮不交付**，已在 `docs/DEGRADATIONS.md` 之外单列原因。

---

## 7. 顺手修掉的 3 个既有工具 bug（都会静默出错，必须记住）

| 工具 | bug | 证据 | 影响面 |
|---|---|---|---|
| `tools/convert_121_data.py` | `spawn_overrides` 的 `minCount/maxCount` 被写成 `uniform{min,max}` | `No key max_inclusive in MapLike[{"type":"minecraft:uniform","min":1,"max":3}]` | 所有带多值 count 的结构（imst 的 `el_dorado` 就挂在这） |
| `tools/neoforge_to_fabric.py` | TOML 行尾注释没剥 ⇒ `fabric.mod.json` 的 id/version 带 `" #mandatory"` | sablephysicscompat 生成的 id = `"sablephysicscompat" #mandatory` | 所有 toml 里写 `modId="x" #mandatory` 的 mod |
| `tools/fix_loot_121.py` | 不认 26.3 已删的 `hide_additional_tooltip` 组件 | `No component with type: 'minecraft:hide_additional_tooltip'` | 用了这个组件的 loot（Towers 的 4 张 potions 表） |

新增工具：`tools/fix_sable_data_121.py`（sable 系 addon 的 `//` 注释 / 尾逗号 / `physics_block_properties` 数组 → 单对象拆分）。

---

## 8. 剩余缺口 / 下一步

1. **`natures_spirit`**：只能做 Java 移植（202 class + 自定义 feature type 10 个 + 自定义方块若干）。建议单独立项，
   用 `remap_intermediary` + `audit_jar_api` 那套；数据层（`ns-1.jar` 的转换）已就绪，Java 一通就只差拼装。
2. **`configured_feature` 转换器还剩的边角**：
   - patch 类的内层 feature 若只是**字符串引用**（不是内联对象），无法本地展开（工具会打 warning 保留）。
     目前 4 个 mod 都没有这种写法。
   - `no_bonemeal_flower` 的「不可骨粉」语义在 26.3 没有对应字段（已按普通 patch 处理，等于允许骨粉）。
   - `minecraft:forest_rock` 的 `can_place_on` 固定用原版 `#minecraft:forest_rock_can_place_on`（保守、等价）。
3. **`mods-stable` 现在 58 jar**（54 + 本批 4）。四个交付 jar 与"测过的那份"**逐字节一致**（SHA256 对比），并在交付物本体（`--mods mods-stable`）上复跑：`TITLE_SCREEN_OK 25.6s` + `WORLD_OK`（`world-final58.log`）。
