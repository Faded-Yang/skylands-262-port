# fix-offroad-loot-schema —— offroad 3 张 loot 改 26.3 单数 condition

> 26.3 权威：work/refs/mc26.3/net/minecraft/world/level/storage/loot/LootPool.java:30-39
> LootItemCondition.CODEC.optionalFieldOf("condition") —— 单数 condition（单个 Holder），不是 1.21 的 conditions 数组。

## 背景
- live sky262-offroad-1.0.0.jar 的 3 张 loot 表使用 1.21 的 conditions 数组；
- 26.3 会忽略该字段（掉落不检查 survives_explosion），需要覆盖为单数 condition；
- 之前 sky262-aero-recipes 1.0.3 的“conditions 数组规范化”方向错误，已作废，不进 promote；1.0.2 保持。

## 件
- work/run26/port/g70/out/sky262-offroad-lootfix-1.0.0.jar
  - 1,837 B
  - SHA-256 41a5ded277476dbff08e49551ba7ae76580f8814a2ef994c72d2581e0a72a3c6
  - id zzz-sky262-offroad-lootfix（确保在 sky262-offroad 之后加载覆盖）
  - 只有 3 张表：borehead_bearing / rockcutting_wheel / wheel_mount
- staging：work/run26/port/g70/stage/offroad-lootfix（base live 116 + 新件 = 117）

## 转换
- 每个 pool 的 conditions[0] 取出 id；
- pool.condition = {type: id}（26.3 LootItemCondition.CODEC 的 inline 形式）；
- 删除 pool.conditions 数组；其余 bonus_rolls/entries/rolls/random_sequence 不变。

## 静态校验
- 3 张表 JSON 解析；
- 每个 pool 只有 condition（对象，含 type 字符串），无 conditions 数组；
- 与 live create 的 26.3 loot 样例形态一致；
- 未启游戏；用户客户端退出后 probe 验 world load + 方块掉落。
