# fix-aero-data —— Aeronautics/Simulated/Offroad loot + advancements

> 参考：docs/fix-aero-recipes.md、docs/API-263-data-schema.md §6、live sky262-create-recipes 的 632 条 loot 样例。
> 数据源：work/refs/jars/extracted/aeronautics-bundled/（aeronautics/simulated/offroad neoforge 1.21.1）。

## 1. 抽取/转换

| 类别 | 源 | 转换 | 跳过 | 说明 |
|---|---|---|---|---|
| recipes | 125 | 124 | 1 | simulated:portable_engine_dyeing（26.3 未注册 type） |
| loot_table | 137 | 137 | 0 | aeronautics 40 / simulated 94 / offroad 3 |
| advancements | 138 | 107 | 31 | aeronautics 35→27、simulated 96→73（含 create:white_sail 1）、offroad 7→7 |

loot：source 全部是 minecraft:block + survives_explosion；把 pools[].conditions 数组改为 26.3 的单个 condition: {type:...}，entry 的 name 原样保留。

advancements：conditions.recipe → conditions.recipes；display.icon 已是 {id,count}；其余结构兼容。

## 2. 跳过的 advancements（31）

- **27 条 custom trigger**：aeronautics:for_every_action_builtin 等 7 条、simulated:*_builtin 20 条；live 26.3 的 class 里没有这些 trigger 的注册字符串，无法加载，必须等对应 trigger 代码移植。
- **4 条 parent 缺失**：
  - aeronautics:song_of_the_sky（parent aeronautics:head_in_the_clouds 被 custom trigger 跳过）
  - simulated:nearsighted（parent simulated:big_beam）
  - simulated:stuck_together（parent simulated:learning_the_ropes）
  - simulated:what_goes_down（parent simulated:get_a_grip）
- 没有 item/tag/recipe id 缺失导致的跳过。

## 3. 件

- work/run26/port/g70/out/sky262-aero-recipes-1.0.2.jar
  - 145,152 B
  - SHA-256 453d200826f886860d35d038dec35d0de6a41e03ff03df63b4cdb0f3a804efe5
  - 内容：124 recipe + 137 loot_table + 107 advancement；data-only，fabric version 1.0.2。
- staging：work/run26/port/g70/stage/aero-recipes（base live 116 + 新件 = 117 jar）。

## 4. 静态校验

- 137 loot：entry name 全部在 live 116 + 26.3 item 清单存在；condition 统一为 survives_explosion。
- 107 advancements：display.icon / conditions.items / rewards.recipes 全部在 live item/tag 或本 jar recipe id 中存在；parent 闭包检查通过。
- 未启游戏；用户客户端退出后 probe 验 Registry loading errors=0 + 实际掉落/成就。

## 5. loot 1.0.3 修正（conditions 数组）

probe 静态指出：26.3 loot 的 pool 级条件必须是数组形式：
  "conditions": [ { "condition": "minecraft:survives_explosion" } ]
而不是我 1.0.2 里的单数 "condition": { "type": ... }。

规范化规则（已用于 137 张表）：
- 任意 dict 的 condition 单数 -> conditions: [normalize(condition)]；
- condition 元素是字符串 -> {condition: 字符串}；
- condition 元素是 {type: X, ...} -> {condition: X, ...}；
- 原本就是 conditions 数组的，逐个元素按上述规则规范化；
- 递归 entry/function 层；最后断言每张表 pools[].conditions 是数组且元素含 condition 字符串。

结果：137 loot / 153 pools 全部为 1 元素 conditions 数组；0 个残留单数 condition。
offroad 3 张表与 live sky262-offroad-1.0.0 同名表逐对象相等（same_as_live=True）。
件：sky262-aero-recipes-1.0.3.jar，145,411 B，SHA 4abe9d73bf722f24e2d6c4e23f8063a99e796c73c5d5fd7def24df355fdcfd11；staging aero-recipes（116+1=117）。

## 6. 1.0.4 schema 修复（probe g174 前）

基于 1.0.2（453d2008；1.0.3 方向错误作废）修：
1. advancement 4 条（simulated:no_pressure / speed_is_key / thataway / the_definition_of_up）：criteria.conditions.location 数组 -> 对象；
2. loot simulated:blocks/merging_glue：entry name minecraft:air -> simulated:merging_glue；
3. filling simulated:filling/honey_glue：fluid_tag c:honey -> #c:honey；
4. mixing aeronautics:mixing/levitite_blend：fluid_tag c:water -> #c:water；
5. sequenced_assembly simulated:.../engine_assembly：sequence 的 create:cutting 步补 processing_time=50；
6. 全局：fluid_tag 全部带 #、location 无数组、loot entry name 非 air、cutting 步有 processing_time。

额外：旧 location 对象 {block:"id", condition:"minecraft:block_state_property"} 规范化为 26.3 BlockPredicate 形式 {block:{"blocks":"id"}}（否则即使数组修掉，block 谓词也会被忽略）。

件：sky262-aero-recipes-1.0.4.jar，145,094 B，SHA 3c0980486528769dc05970e4bed06691d8461c419d7b8d848bf0f62dd55bbde7；124 recipe +137 loot +107 adv；staging aero-recipes（117，base live116）。

## 7. 1.0.5（g174 剩 5 处）

- 4 条 advancement 的 location 改为 26.3 type-dispatch：
  {"location":{"type":"minecraft:match_block","blocks":"<id>"}}
  （simulated:altitude_sensor / velocity_sensor / navigation_table / gimbal_sensor）。
- mixing levitite_blend 的 fluid_results 保持 26.3 FluidStack 形式 {id, amount}（id=aeronautics:levitite_blend，amount=500；fluid 在 live 的 aero class 中存在）。
- 全局断言：fluid_results 每条有 id+amount；fluid_ingredients 有 fluid/fluid_tag（tag 带 #）+amount；filling fluid_ingredient 的 fluid_tag 带 #。
- 件：sky262-aero-recipes-1.0.5.jar，145,126 B，SHA dfddc2f6a5e7da096678083cc76faf968c721cbb1777dd71a0c20947ee11d8fc；124 recipe +137 loot +107 adv；staging aero-recipes（117，base live116）。

## 8. 1.0.8 补最后 3 条 advancement

基于 g174 1.0.8（135 adv，已有 what_goes_down/must_come_up/rewind_time）补：
- simulated:nearsighted（parent simulated:big_beam；location 数组 + block/condition 转 26.3 match_block）；
- simulated:stuck_together（parent simulated:learning_the_ropes）；
- aeronautics:song_of_the_sky（parent aeronautics:head_in_the_clouds）。

结果：138 advancements，parent 闭包 0 缺失；124 recipe + 137 loot 不变。
件：g70/out/sky262-aero-recipes-1.0.8.jar，158,723 B，SHA 2c8fe78f5cf95bc54146e0b9f552c6418e096065496ba356781ee31cbaf5297f；staging aero-recipes-108（118，base live117）。
