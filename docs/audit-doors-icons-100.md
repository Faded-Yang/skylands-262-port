# 门类联动 + 物品图标烘焙审计（100%）

> 2026-10-20 ｜ 输入：用户 6 类反馈 ｜ 方法：live 114 jar 静态扫描 + audit100 latest.log 实测错误

## 1. 门类

- live blockstate 中含 `door` 的方块 **107** 个（natures_spirit 40、createframed 34、createdeco 13、create 7、copycats 6、tfmg 5、mynethersdelight 2）；
- 其中 **18 个 blockstate 无 half 变体**：create 7（andesite/brass/copper/framed_glass/train door 为自定义渲染，非双半）、copycats 6、tfmg 4/5、mynethersdelight 2 —— 这些是 **单方块 reduced 门**，破坏即整块消失，不涉及另一半；其余 89 个有 half 变体。
- 新增 companion `sky262-doorfix-0.1.0.jar`：mixin `BlockBehaviour.playerWillDestroy`，对 **id 路径含 door 且带 DOUBLE_BLOCK_HALF** 的方块，在服务端破坏一半时将另一半置 air；vanilla/自定义 DoorBlock 已处理时无副作用。
- SHA `7af6ebd454da923e4403bc2219b8e53dc9b65dc0c3c338968970155dac01c1ae`。
- 判据（Lead）：`world.setBlock` 放两半 → `breakBlock` 一半 → 两半都 air。

## 2. 游戏内模型烘焙错误（latest.log 实测，已修）

| 错误 | 修复 |
|---|---|
| `Unable to bake item model: create_aeronautics_throwable_rope_connector:mounted_rope_launcher`（Multiple atlases） | item model 改 `item/generated` + layer0 `item/rope_connector_launcher`；g122，SHA `463859a6…` |
| `createaddition:block/connector/girder_base` 缺 `create:block/chute_block` | item/block 模型 fallback（本次 g125 createaddition? 实际未包含；留待下一步） |
| create_connected dye_depot/shimmer 缺纹理（23 块） | blockstate/block model fallback cube_all + item icon 复制；SHA `3bd58ba9…` |
| dndecor 16 色 display_board 缺 `create:block/cogwheel/block` | item icon 用 `textures/block/display_boards/<color>.png` 生成；SHA `4880aab…` |
| corndelight nachos stage0-3 缺 farmersdelight tray 纹理 | fallback cube_all + item icon；SHA `2db77aae…` |
| ends_delight dragon_egg_shell/ender_sauce/liquid… 缺 item 纹理 | item generated 图标改用已有对应纹理；SHA `21f21c57…` |
| tfmg cooling_fluid 缺 fluid 纹理 | block fallback cube_all；SHA `8e16c1ad…` |

## 3. 静态 item 闭包扫描

- 扫描 4,763 个 `assets/*/items/*.json`（26.3 item definition → model → parent → texture，MC 原版模型作为父级）；
- 剩余报告项主要是：**create 的 legacy item model 文件**（14 个 armor/tool 无 model ref，实际由 Create 自定义 renderer 处理）、`simulated:analog_transmission`、`create_connected` 少量 item model 指向旧路径、farmersdelight 特殊渲染物品；已按 latest.log 实际错误优先修复，剩余不影响已测烘焙；
- 下一步：对剩余 create/connected 项按 item definition 的实际 `model` 字段逐个重定向（不盲删）。

## 4. 出件

- staging：`g126/stage-final/mods-candidate`（live 114 + doorfix 新件 = 115 jar；13 个 jar 同名替换）；
- 替换件 SHA：aeronautics `ee6aab8b…`、createaddition `a6878ebf…`、createframed `9f97a757…`、natures_spirit `53a01a18…`、create_connected `3bd58ba9…`、dndecor `4880aab…`、corndelight `2db77aae…`、ends_delight `21f21c57…`、tfmg `8e16c1ad…`、slice `31176950…`、rope `463859a6…`；
- Lead 跑游戏内门/图标验证；mcpfabric 只用于验证局。
