# mynethersdelight reduced 26.3 移植（广度件 #2）

> 日期：2026-10-20 凌晨 ｜ 角色：crashfix-26 ｜ 结果：**TITLE_SCREEN_OK + WORLD_OK**

## 0. 结论速览

| 项 | 结果 |
|---|---|
| 源包 | MyNethersDelight-1.21.1-2.0.4+1.7.8.refabricated.jar（Modrinth `my-nethers-delight-refabricated`） |
| 端口方式 | **数据驱动 reduced**（assets + 手写方块/物品注册，无原代码） |
| 规模 | **46 方块 + 100 物品**（原 47 方块/88 item 模型；powdery 木组已跳过） |
| 依赖 | 26.3 + Fabric API + Fabric Loader（无 FD/create 前置） |
| 标题 | TITLE_SCREEN_OK（59.2s，第二次重试） |
| 进世界 | WORLD_OK joined=true（71.2s，第二次重试） |
| 产物 | g70/out/sky262-mynethersdelight-2.0.4-26.3-reduced.jar（325,835 B，SHA256 01eecfaeae41ce1b12b8ea273ff1abc8d1d6d7daae4aabff7bd23754f7b3e1a7） |
| staging | g70/stage/mnd-final（live 94 + culturaldelights + 本件 = 96 jar；等于 #1 promote 后 base 95 + 本件） |

## 1. 实现（与 #1 同一套流程）

生成器：work/_gen_mnd.py（由生成 culturaldelights 的脚本替换命名空间/包名/源 jar 得到）
- 解析原包 blockstates/47 与 models/item/88 → 方块/物品 id；
- 每个 block 生成单默认 variant blockstate（取原 blockstate 第一个 model）；
- 每个 item 生成 26.3 item model definition：{"model":{"type":"minecraft:model","model":"mynethersdelight:item/<id>"}}；
- 注册类：g70/src/mnd/com/sky262/mynethersdelight/MNDReduced.java
  - Properties.setId（Block/Item）26.3 硬约束；BlockItem 用 useBlockDescriptionPrefix；
  - Fabric 创造栏 mynethersdelight:main；
- 资源：g70/res-mnd（textures/models/lang + fabric.mod.json，**无 data**）；
- 打包：tools/pack_jar.py（带目录条目）。

## 2. 卡点：Create RuntimeDataGenerator 崩溃（非显然事实）

最初 47 方块/101 物品的版本，进世界必崩：
- 日志：Failed to load level data or datapacks → ClassCastException: com.zurrtum.create...CuttingRecipe cannot be cast to net.minecraft.core.Holder；
- 栈：com.zurrtum.create.foundation.pack.RuntimeDataGenerator.addRecipe → simpleWoodRecipe → cuttingRecipes → insertIntoPack（BuiltInPackSource mixin）；
- 原因：Create 的运行时数据生成器扫描所有 item，对匹配「木头正则」的 id 生成 cutting 配方；我们的 powdery 木组（powdery_block/stripped_powdery_block/powdery_planks 等）触发该路径，26.3 下 Recipe.CODEC 期望 Holder 而拿到 CuttingRecipe → 崩溃。
**降级修法**：reduced v1 跳过 powdery 木组（powdery_block/powdery_planks/powdery_stairs/slab/fence/fence_gate/door/trapdoor/sign/wall_sign/hanging_sign/wall_hanging_sign/button/pressure_plate/cabinet/mosaic*），保留其余方块/物品。
- 验证：跳过后的 b4 版本进世界 **WORLD_OK**。

## 3. 三查证据

1. jar：611 entries，1 class，**data=0**；blockstates/items 资产齐全，fabric.mod.json id=mynethersdelight、entrypoint 正确；
2. 注册：日志 `[mynethersdelight] reduced initialized, blocks=46 items=100`；Properties.setId 已用；命名空间与原包一致；
3. 进世界：WORLD_OK joined=true；registry 0 错误；少量缺失模型/贴图警告（视觉）。

## 4. 已知降级

- 无食物效果/作物/BE/交互/世界生成/交易/配方；方块整块碰撞；
- powdery 木组（约 16 个方块/物品）未注册（Create 运行时生成器崩溃规避）；
- 部分方块无 item 模型（原 models/item 缺失），创造栏图标/物品模型可能缺失；
- 首轮世界/标题测试因残留 java 进程/环境抖动失败，kill 后重试通过（详见交付说明：跑前必须清理 java 进程）。

## 5. 给 probe 的 MCP 验收步骤

前提：staging 启动后保持世界在线；日志确认 [MCP] WebSocket server ready on port 25576。

~~~powershell
node tools\mcp_fabric_client.mjs player.getState
node tools\mcp_fabric_client.mjs screenshot.take --out mnd-shots
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s mynethersdelight:nether_bricks_cabinet 1"}'
node tools\mcp_fabric_client.mjs chat.get
node tools\mcp_fabric_client.mjs chat.send '{"message":"/setblock ~ ~ ~ mynethersdelight:nether_bricks_cabinet"}'
node tools\mcp_fabric_client.mjs world.getBlock '{"x":0,"y":0,"z":0}'
node tools\mcp_fabric_client.mjs screenshot.take --out mnd-shots
~~~

断言：0 crash；/give 不报 unknown item；world.getBlock 读回 mynethersdelight:nether_bricks_cabinet；至少 2 张 PNG。