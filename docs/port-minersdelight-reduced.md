# minersdelight reduced 26.3 移植（广度件 #3）

> 日期：2026-10-20 凌晨 ｜ 角色：crashfix-26 ｜ 结果：**TITLE_SCREEN_OK + WORLD_OK，registry 0**

## 0. 结论速览

| 项 | 结果 |
|---|---|
| 源 | Modrinth `miners-delight` 1.21.1 **NeoForge** 构建 `minersdelight-1.21.1-1.4.5.jar`（assets 与 loader 无关） |
| 端口方式 | **数据驱动 reduced**（assets + 手写注册，无原代码） |
| 规模 | **10 方块 + 71 物品**（10 BlockItem + 61 普通 Item；assets 69 item 模型/10 blockstates） |
| 依赖 | 26.3 + Fabric API + Fabric Loader（无 FD/NeoForge 前置） |
| 标题 | **TITLE_SCREEN_OK 30.8s** |
| 进世界 | **WORLD_OK joined=true 44.9s**；registry 0 错误 |
| 件 | `g70/out/sky262-minersdelight-1.4.5-26.3-reduced.jar`，**146,724 B，SHA256 `c79392ec516b5c0d6e701560e555e70c6ce1407ba3e83ad7cfd3d07ac66fd617`** |
| staging | `g70/stage/md-final`（base live **98** + 本件 = **99 jar**） |

## 1. 实现（沿用 #1/#2 流程）

生成器：`work/_gen_miners.py`（由 MND 生成器替换命名空间/包名/源 jar 得到）
- 解析原包 `assets/minersdelight/blockstates/*.json`（10）与 `models/item/*.json`（69）；
- 每个 block 生成单默认 variant blockstate + 通用 Block；每个 item 生成 26.3 item model definition；
- 注册类：`g70/src/minersdelight/com/sky262/minersdelight/MinersDelightReduced.java`；
- Block/Item `Properties.setId`（26.3 硬约束）；Fabric 创造栏 `minersdelight:main`；
- 资源：`g70/res-minersdelight`（textures/models/lang + fabric.mod.json，**无 data**）；
- 打包：`tools/pack_jar.py`（带目录条目）。

## 2. 自检（Lead 要求三项）

- blockstate/model 存在性：**missing_bs_models []，missing_item_models []**；
- lang：4 个语言文件全部 JSON 合法、值均为字符串（badlang []）；
- `Properties.setId`：类内使用（`block()`/`item()` 辅助方法统一 setId）；
- data：**0 条目**（无 data 引用未注册内容）；日志 `[minersdelight] reduced initialized, blocks=10 items=71`。

## 3. 给 probe 的 MCP 验收步骤

~~~powershell
node tools\mcp_fabric_client.mjs player.getState
node tools\mcp_fabric_client.mjs screenshot.take --out md-shots
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s minersdelight:cave_carrot 1"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s minersdelight:bat_wing 1"}'
node tools\mcp_fabric_client.mjs chat.get
node tools\mcp_fabric_client.mjs chat.send '{"message":"/setblock ~ ~ ~ minersdelight:cave_carrot_crate"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/setblock ~ ~1 ~ minersdelight:copper_pot"}'
node tools\mcp_fabric_client.mjs world.getBlock '{"x":0,"y":0,"z":0}'
node tools\mcp_fabric_client.mjs screenshot.take --out md-shots
~~~
断言：0 crash、0 registry 错误；give 不报 unknown item；world.getBlock 读回 `minersdelight:cave_carrot_crate`/`minersdelight:copper_pot`；≥2 张 PNG。

## 4. 已知降级

- 无食物效果/BE/交互/配方/世界生成/交易；方块整块碰撞；
- 创造栏 tab 名称直译（无原始 key 本地化，避免 lang 依赖）。