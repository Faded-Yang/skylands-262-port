# NS advancement 26.3 恢复 + 完整 NS data 件（任务 B 完成）

> 日期：2026-10-20 凌晨 ｜ 角色：crashfix-26 ｜ 结果：**TITLE_SCREEN_OK + WORLD_OK，registry 0，advancements 2888（+502）**

## 0. 结论

| 项 | 结果 |
|---|---|
| 源 | NS 原包 503 条 `data/natures_spirit/advancement/**` |
| 恢复 | **502/503**（跳过 `adventure/shoot_coconut`：自定义 criterion `natures_spirit:coconut_hit` 的 codec 已降级，数据条件为 null 无法解析）；
| 原版覆盖 | 2 条（`adventure/adventuring_time`、`husbandry/whole_pack`）按 Lead 指示**不恢复**；
| 件 | `g70/out/natures_spirit-fabric-2.3.0-26.3-adv2.jar`，**18,741,319 B，SHA256 `c1d1258fd57672146eaf72e1900a2157c97a57b9f4e2dd239dfb254b4d42fdc5`**（base = live nsA15，已含 loot 720 + recipe 826 + worldgen/structure） |
| staging | `g70/stage/ns-adv2`（live 98 同集合，仅替换 NS jar） |
| 标题 | **TITLE_SCREEN_OK 29.0s** |
| 进世界 | **WORLD_OK joined=true 50.6s**；registry 0 错误；`Loaded 2888 advancements`（+502） |

## 1. schema 映射（advancement 26.3）

- `minecraft:recipe_unlocked` 条件：`recipe` → **`recipes`**（26.3 TriggerInstance 用 HolderSet<Recipe>，字段复数）；
- `minecraft:enter_block` 条件：`block` → **`blocks`**；
- `minecraft:player_killed_entity` 条件：
  - `entity` 数组 → 单个对象；
  - 内部 `condition` → `type`；
  - EntityPredicate 的 `type` → `minecraft:entity_type`、`equipment` → `minecraft:equipment`；
  - `killing_blow` 的 `direct_entity`/`source_entity` 递归同上；
- `inventory_changed`（items/ItemPredicate）、`display.icon {id,count}`、`rewards.recipes`、`requirements` 与 26.3 已兼容，无需改。

## 2. 坑与修复

- adv1 失败：`No key recipes in MapLike[{"recipe":...}]`（全部 recipe_unlocked 条件）→ 改字段为 `recipes`；
- adv2 通过：0 registry、2888 advancements、世界/标题均 PASS。

## 3. 给 probe 的 MCP 验收步骤

~~~powershell
node tools\mcp_fabric_client.mjs player.getState
node tools\mcp_fabric_client.mjs screenshot.take --out ns-adv-shots
node tools\mcp_fabric_client.mjs chat.send '{"message":"/advancement grant @s only natures_spirit:recipes/building_blocks/alluaudia_bundle"}'
node tools\mcp_fabric_client.mjs chat.get
node tools\mcp_fabric_client.mjs chat.send '{"message":"/advancement grant @s only natures_spirit:adventure/..."}'
node tools\mcp_fabric_client.mjs screenshot.take --out ns-adv-shots
~~~
断言：0 registry 错误；grant 不报 unknown advancement；聊天显示成功/提示；≥2 张 PNG。

## 4. 状态
- 任务 B 三步（loot → recipe → advancement）全部完成；adv2 即**完整 NS data 件**（loot 720 + recipe 826 + advancement 502 + worldgen/structure 等），可直接 promote 替换 live nsA15（98 不变）。