# abnormals_delight reduced 26.3 移植（广度件 #4）

> 日期：2026-10-20 凌晨 ｜ 角色：crashfix-26 ｜ 结果：**TITLE_SCREEN_OK + WORLD_OK，registry 0**

## 0. 结论速览

| 项 | 结果 |
|---|---|
| 源 | Modrinth `abnormals-delight` 1.21.1 **NeoForge** `abnormals_delight-1.21.1-6.0.3.jar`（assets 与 loader 无关） |
| 端口方式 | **数据驱动 reduced**（assets + 手写注册，无原代码） |
| 规模 | **16 方块 + 57 物品**（16 个 cabinet + 57 item 模型；BlockItem 覆盖方块） |
| 依赖 | 26.3 + Fabric API + Fabric Loader（无 Team Abnormals/blueprint/FD 前置） |
| 标题 | **TITLE_SCREEN_OK 28.2s** |
| 进世界 | **WORLD_OK joined=true 44.4s**；registry 0 错误 |
| 件 | `g70/out/sky262-abnormalsdelight-6.0.3-26.3-reduced.jar`，**120,538 B，SHA256 `1481d5014ee68d7a4348c85950bdc9d8984cc48cccd104a19519f092c32c80e4`** |
| staging | `g70/stage/abn-final`（base live **99** + 本件 = **100 jar**） |

## 1. 实现（沿用 #1-#3）

- 生成器：`work/_gen_abn.py`（由 Miner's Delight 生成器替换命名空间/包名/源 jar）；
- 解析 `blockstates/*.json`（16）与 `models/item/*.json`（57）→ 通用 Block/BlockItem/Item；
- 单默认 variant blockstate；26.3 `items/*.json` item model definition；
- 注册类：`g70/src/abnormalsdelight/com/sky262/abnormalsdelight/AbnormalsDelightReduced.java`；
- `Properties.setId`、Fabric 创造栏、无 data、`tools/pack_jar.py` 打包。

## 2. 自检（Lead 要求）

- blockstate/model 存在性：**missing models []**；
- 外部命名空间贴图：**缺失 0**（模型贴图全部自包含，`missing texture refs by namespace: []`）；
- lang：17 个语言文件 JSON 合法、值均为字符串（badlang []）；
- `Properties.setId`：统一辅助方法使用；data：**0 条目**；
- 日志：`[abnormals_delight] reduced initialized, blocks=16 items=57`。

## 3. 给 probe 的 MCP 验收步骤

~~~powershell
node tools\mcp_fabric_client.mjs player.getState
node tools\mcp_fabric_client.mjs screenshot.take --out abn-shots
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s abnormals_delight:cherry_cookie 1"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s abnormals_delight:copper_knife 1"}'
node tools\mcp_fabric_client.mjs chat.get
node tools\mcp_fabric_client.mjs chat.send '{"message":"/setblock ~ ~ ~ abnormals_delight:aspen_cabinet"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/setblock ~ ~1 ~ abnormals_delight:maple_cabinet"}'
node tools\mcp_fabric_client.mjs world.getBlock '{"x":0,"y":0,"z":0}'
node tools\mcp_fabric_client.mjs screenshot.take --out abn-shots
~~~
断言：0 crash、0 registry 错误；give/setblock 不报 unknown；读回一致；≥2 张 PNG。

## 4. 已知降级

- 无食物效果/BE/交互/配方/世界生成/交易；cabinet 为通用整块碰撞；创造栏名称直译。