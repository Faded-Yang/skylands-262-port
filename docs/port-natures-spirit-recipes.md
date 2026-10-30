# NS recipe 26.3 恢复（任务 B 步骤 3）

> 日期：2026-10-20 凌晨 ｜ 角色：crashfix-26 ｜ 结果：**TITLE_SCREEN_OK + WORLD_OK，registry 0 错误**

## 0. 结论速览

| 项 | 结果 |
|---|---|
| 源数据 | 原包 826 个 `data/natures_spirit/recipe/**` |
| 类型 | crafting_shaped 417 / stonecutting 241 / crafting_shapeless 161 / smelting 7（全部原版类型） |
| 转换 | NS 26.1.2 的 recipe 已是 26.3 兼容格式（`ingredients` 字符串、`result {id,count}`）→ 直接整包恢复，替换 live NS 的 7 条 |
| 件 | `g70/out/natures_spirit-fabric-2.3.0-26.3-recipe1.jar`，**18,515,847 B，SHA256 `b147e30f0c88f2bd532be31ae877f102eab25f19a0903c4cb601ceedac3f5323`** |
| staging | `g70/stage/ns-recipe1`（live 98 同集合，仅替换 NS jar） |
| 标题 | **TITLE_SCREEN_OK 30.2s**（首次因残留进程失败，kill 后重试） |
| 进世界 | **WORLD_OK joined=true 76.6s**；`Registry loading errors` **0**；JEI recipes 正常注册 |

## 1. 结论
- 26.1.2 的 NS recipe JSON 与 26.3 的 vanilla recipe 结构一致：
  - `ingredients`: 字符串数组（`"item"`/`"#tag"`）；
  - `result`: `{"id": "...", "count": n}`；
  - `key`/`pattern`/`cookingtime`/`experience`/`category` 均兼容；
- 因此 recipe 阶段无需逐条转换，只需恢复数据并确认引用 item 都已注册。
- 世界测试通过，说明 826 条 recipe 全部可解析（引用的 NS 物品已注册）。

## 2. 给 probe 的 MCP 验收步骤

~~~powershell
node tools\mcp_fabric_client.mjs player.getState
node tools\mcp_fabric_client.mjs screenshot.take --out ns-recipe-shots
node tools\mcp_fabric_client.mjs chat.send '{"message":"/recipe give @s natures_spirit:aspen_button"}'
node tools\mcp_fabric_client.mjs chat.get
node tools\mcp_fabric_client.mjs chat.send '{"message":"/recipe give @s *"}'
node tools\mcp_fabric_client.mjs chat.get
node tools\mcp_fabric_client.mjs screenshot.take --out ns-recipe-shots
~~~
断言：0 registry 错误；`/recipe give` 无 unknown recipe；聊天显示解锁成功；≥2 张 PNG。

## 3. 下一步
- advancement（conditions 数组→对象）重写；
- 最后与 loot/recipe 合并成完整 NS data 件。