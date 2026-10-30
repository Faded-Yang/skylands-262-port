# culturaldelights reduced 26.3 移植（广度件 #1）

> 日期：2026-10-19 深夜 ｜ 角色：crashfix-26 ｜ base：live **94** jar ｜ 结果：**TITLE_SCREEN_OK + WORLD_OK**

## 0. 结论速览

| 项 | 结果 |
|---|---|
| 源包 | work/run26/port/cultural-delights/orig/culturaldelights-0.17.7.jar（Fabric 0.17.7，1.21.1 资产） |
| 端口方式 | **数据驱动 reduced**（资产 + 手写注册，无原代码移植） |
| 规模 | **26 方块 + 78 物品**（26 BlockItem + 52 普通 Item） |
| 依赖 | 26.3 + Fabric API + Fabric Loader（无 create/blueprint/其它前置） |
| 标题 | TITLE_SCREEN_OK（55.3s） |
| 进世界 | WORLD_OK, joined=true（72.4s） |
| 产物 | g70/out/sky262-culturaldelights-0.17.7-26.3-reduced.jar（162,278 B，SHA256 e3ac867c50da34b4edbfb89455b36db8e41a1b488a3a37974ef49892fd6539c7） |
| staging | g70/stage/cd-reduced（live 94 + 本件 = 95） |

## 1. 剩余缺口 top-3 评估（按「无前置/无世界生成/无流体/无 BE」排序）

| # | 候选 | 源构建 | 规模（类/资源/数据） | 依赖/卡点 | 降级方案 | 预估 |
|---|---|---|---|---|---|---|
| **1** | **Cultural Delights**（本件，已完成） | Fabric 0.17.7（本地有 jar） | 25 java → 26 方块 + 72 模型物品 | 原代码卡 26.3 tree/worldgen；**reduced 绕开** | 资产 + 数据驱动方块/物品；食物效果/作物/树/配方/成就全砍 | 已出件 |
| 2 | **My Nether's Delight** | Fabric refabricated 2.0.4（需下载） | 131 类 / 142 资源 / 440 数据（XL） | 世界生成/交易/方块多；无流体；BE 少 | reduced：只取 assets，生成方块/物品；砍 worldgen/交易/配方；BE 方块退化为普通 Block | 0.5–1 天 |
| 3 | **Miner's Delight** | 只有 NeoForge 构建（需下载） | 69 类 / 110 资源 / 199 数据 | NeoForge API（仅原代码需要）；reduced 不需要；无流体/BE 迹象 | 取 assets（loader 无关）→ 生成方块/物品；食物效果降级为普通 Item | 0.5 天 |

**明确排除**（Lead 指定，已确认前置不在 live）：climbable_ropes（需 player-animation-lib + simulated）、copycats（客户端模型系统）、waystonessable（依赖本体库）。

## 2. reduced 实现（可复现）

生成器：work/_gen_cd_reduced.py
- 解析原包 assets/culturaldelights/blockstates/*.json → 26 个 block id；models/item/*.json → 72 个 item id；
- 每个 block 生成**单默认 variant** blockstate（model 取原 blockstate 里第一个 model，避开 26.3 已删的方块属性）；
- 每个 item 生成 26.3 item model definition：{"model":{"type":"minecraft:model","model":"culturaldelights:item/<id>"}}；
- 注册类：g70/src/culturaldelights/com/baisylia/culturaldelights/CulturalDelightsReduced.java
  - BlockBehaviour.Properties.of().setId(ResourceKey.create(Registries.BLOCK, id))（26.3 硬约束）；
  - new Item.Properties().setId(...)；BlockItem 用 useBlockDescriptionPrefix()；
  - Fabric 创造栏 culturaldelights:main，CreativeModeTabEvents.modifyOutputEvent 填物品；
- 资源：g70/res-culturaldelights/（textures/models/lang + fabric.mod.json，**无 data**）；
- 打包：python tools/pack_jar.py build/culturaldelights res-culturaldelights out/...jar（带目录条目）。

## 3. 三查证据

1. **jar 结构**：374 entries，1 class，**data=0**；blockstates=26，items=72；fabric.mod.json id=culturaldelights、entrypoint 正确；
2. **注册/资产命名空间**：blockstate 示例 culturaldelights:block/avocado_crate、item 示例 culturaldelights:item/avocado，与原包命名空间一致；
3. **进世界日志**：[culturaldelights] reduced initialized, blocks=26 items=78；WORLD_OK joined=true；无 registry 错误；仅少量模型/贴图缺失（视觉）。

## 4. 已知降级/限制

- 无食物效果（全部普通 Item）；无作物生长/树/世界生成；无配方/成就/战利品表/交易；无 BE/交互；
- 方块均为整块碰撞、无朝向/多状态（原 blockstate 复杂变体已合并）；
- 少数 block 模型缺失（日志 Missing block model），贴图缺失警告（Missing textures in model）— 视觉降级，不影响进世界。

## 5. 给 probe 的 MCP 验收步骤

前提：staging 启动后保持世界在线；日志确认 [MCP] WebSocket server ready on port 25576。

~~~powershell
# 1) 状态 + 首张截图
node tools\mcp_fabric_client.mjs player.getState
node tools\mcp_fabric_client.mjs screenshot.take --out cd-shots

# 2) 给物品（验证注册）
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s culturaldelights:avocado 1"}'
node tools\mcp_fabric_client.mjs chat.get

# 3) 放方块 + 读回
node tools\mcp_fabric_client.mjs chat.send '{"message":"/setblock ~ ~ ~ culturaldelights:avocado_crate"}'
node tools\mcp_fabric_client.mjs world.getBlock '{"x":0,"y":0,"z":0}'

# 4) 截图证据
node tools\mcp_fabric_client.mjs screenshot.take --out cd-shots
~~~

断言：0 crash；player.getState 正常；/give 不报 unknown item；world.getBlock 读回 culturaldelights:avocado_crate；至少 2 张 PNG。失败先看 logs/latest.log 的 culturaldelights 行，再用 reflect.invoke 最后手段。
## 6. 2026-10-20 食物功能补齐（aero）

- 40 个食物 id 注册 `FoodProperties`：snack 2/0.3（avocado/corn_cob/cucumber/cut_*/pickle/popcorn/rice_ball/tortilla_chips/smoked_* 等 18）、meal 6/0.6（burrito/taco/roll/pasta/curry/empanada/elote 等 22）；
- 生产件 `g108/out/sky262-culturaldelights-0.17.7-26.3-reduced.jar`，SHA `2f3f830f1158f80d353fc2ec2db5b99a37f67666d5007873d648abb818fbee2c`；base 114；staging `g109/stage-final/mods-candidate`；
- 橱窗/display case：原 jar **无该方块**（仅 27 作物/箱子/垫子 blockstates），待用户给准确 id；
- 其余降级（作物生长/世界生成/配方/成就/交易/BE）不变。