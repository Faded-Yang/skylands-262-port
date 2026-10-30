# NS loot_table 26.3 恢复（任务 B 步骤 2）

> 日期：2026-10-20 凌晨 ｜ 角色：crashfix-26 ｜ 结果：**TITLE_SCREEN_OK + WORLD_OK，registry 0 错误**

## 0. 结论速览

| 项 | 结果 |
|---|---|
| 源数据 | 原包 720 个 `data/natures_spirit/loot_table/**`（1.21.x schema） |
| 转换 | 程序化重写（脚本 `work/_ns_loot_conv.py`）→ `g70/out/natures_spirit-fabric-2.3.0-26.3-loot2.jar`，**18,231,953 B，SHA256 e17b3f95dcc0e93c223560f2111eddaafcc554578757ab1284ebd5f2a3d4fc56**；
| staging | `g70/stage/ns-loot2`（live 98 同集合，仅替换 NS jar） |
| 标题 | **TITLE_SCREEN_OK 29.1s** |
| 进世界 | **WORLD_OK joined=true 42.6s**；`Registry loading errors` **0**；`Loaded 2386 advancements` |

## 1. 映射/结构（详见 docs/API-263-data-schema.md 追加小节）

- condition 注册表：`BuiltInRegistries.LOOT_CONDITION_TYPE`（`minecraft:loot_condition_type`）；
- 旧 `minecraft:block_state_property` → `minecraft:match_block`，字段 `block`→`blocks`、`properties`→`state`；
- `minecraft:match_tool`：旧 `predicate` 平铺为 ItemPredicate 字段；shears → 引用串 `minecraft:tool/can_shear`，silk_touch → `minecraft:tool/can_silk_touch`；
- 其余 condition id 同名，仅 `condition` 键改 `type`；`any_of`/`all_of`/`inverted` 的 term/terms 递归转换；
- 函数：`function`→`type`，函数内 `conditions`→`condition`（多条件 union 处理）；条目 `functions`→`modifier`；
- 条目/池 `conditions` 列表→`condition`（单个，多个 → `all_of`）；
- `location_check` 的 `predicate.block` 使用 BlockPredicate（`blocks`/`state`）。

## 2. 踩坑与修复

- 第一版（loot1）报 `Unknown registry key ... minecraft:block_state_property`：漏了**函数对象内部的 `conditions`**（如 `set_count.conditions`）；
- 修复：`conv_function` 同时转换 `conditions`→`condition`；loot2 registry 0 错误、世界通过。
- 失败时只贴第一行 Caused by + 元素名，符合 Lead 要求。

## 3. 给 probe 的 MCP 验收步骤

~~~powershell
node tools\mcp_fabric_client.mjs player.getState
node tools\mcp_fabric_client.mjs screenshot.take --out ns-loot-shots
node tools\mcp_fabric_client.mjs chat.send '{"message":"/loot give @s loot natures_spirit:blocks/aspen_slab"}'
node tools\mcp_fabric_client.mjs chat.get
node tools\mcp_fabric_client.mjs screenshot.take --out ns-loot-shots
~~~
断言：世界可进、0 registry 错误；`/loot give` 不报 unknown loot table / parse error；聊天出现获得物品；至少 2 张 PNG；失败贴 `Registry loading errors` 首行 + 元素名。

## 4. 下一步（任务 B 后续）

- recipe（ingredients/result 26.3 格式）→ 先扫描 831 个旧 recipe 类型/结构，再转换、世界测试；
- advancement（conditions 数组→对象）最后做。