# 可玩性审计（mcpfabric，2026-10-20 18:00 起）

> 工具：mcpfabric 0.8.0+26.3（bridge 127.0.0.1:25599）+ `tools/mcpfabric_client.mjs`、`tools/mcp_prep.mjs`、`tools/sweep_blocks.mjs`、`tools/sweep_items.mjs`。
> 测试局：`work/run26/port/g33/game-g119fab`（g119 staging + mcpfabric）、`game-g122`（g122 staging + mcpfabric）。
> 纪律：mcpfabric 只用于验证局，不进 `mods-stable`；测试语言固定 `lang:zh_cn`。

## 1. 全量放置 / 物品 sweep（g119 staging）

### block sweep（`sweep_blocks.mjs`）
```
{ "placed": 4187, "failures": 0, "unknown": 25 }
```
- placed 4187 = 期望 blockstate 总数；0 failure、0 crash。
- unknown 25：**24 个是 `block_ids.json` 里的旧版残留 id**（当前 jar 无 blockstate/model）：createframed framed_radon_lamp×16、natures_spirit×2、aeronautics:levitite_blend、createaddition:bioethanol/connector_old/copper_wire_casing/liquid_blaze_burner/seed_oil；
- **1 个真实缺口**：`createaddition:accumulator`（models/item 存在，方块未注册）。
- 结论：**PASS（放置 4187/0 fail）**，unknown 属清单过期 + 1 注册缺口（R590 已处理，g117 件应清零，待新清单复跑）。

### item sweep（`sweep_items.mjs`）
```
{ "ok": 4740, "unknown": 71, "rawkey": 0, "error": 0 }
```
- **rawkey=0 PASS**（本轮 lang 修复生效）；
- unknown 71 分类（按 staging jar 资源核对）：
  - 资源存在但未注册 **55**：simulated×32（portable_engine 16 色 / directional_gearshift / linked_typewriter / creative_physics_staff/* 等）、createframed×19、ends_delight×3、aeronautics:levitite_blend_bucket×1；
  - 过期 id 16（createframed framed_radon_lamp×16）。
- 结论：R591 已由 `sky262-audit-items 0.1.0`（g121/g122）补注册 19 BlockItem+4 Item 并重生成 item_ids=4763，**待 g122 新清单复跑期望 4763/0**。

## 2. 任务书 GUI（g122 staging，quests `29f01fb7`）

- `/questbook open`（chat.send，客户端命令）→ `screen.get`：`other / "Quest Book"` 427x240 ✅
- `ui.widgets` 返回 17 个 widget：章节按钮×7、`<-`/`->`、任务格×4（type=other）、底部按钮 `Submit/Check/Claim/Close`；
- `ui.click` 章节「储存」→ widgets 更新；`ui.click` `->` → 章节切到「军工载具」并换任务格 ✅；
- `ui.click` 任务格（`猎犬A型装甲车`）→ **Submit 由 disabled 变 enabled**（选中生效）；点 `Submit` → 服务端回执 `[sky262quests] submit 503B5C53A9CA46DA -> missing-items` ✅（提交链路真实工作）；
- 截图：`work/run26/port/g33/quest-audit/q1_initial.png`、`q2_chapter.png`、`q3_next_page.png`、`q4_cell.png`、`q5_Submit.png`；
- ⚠ **英文文案是测试语言问题，不是 bug**：按钮文本来自 lang key `quest.gui.submit/check/claim/close`、提示来自 `quest.gui.hint/tip.*`；`en_us.json` 里就是 `Submit/Check/Claim/Close` + `Click a quest to view details`，`zh_cn.json` 是 提交/检查/领取/关闭 + 点击任务查看详情；本局 `options.txt` 当时为 `lang:en_us` → 复验需 `lang:zh_cn`（mcp_prep 已强写）。
- 结论：**任务书 widget 化 PASS**（章节/翻页/选中/提交都可用；任务格以 type=other 暴露，点击按坐标命中，选中逻辑生效）。

## 3. 食物真吃（环境已修正，待复验）
- 首轮 `control.startUsing` 无效：`screen.get` = `pause / paused:true`（单人游戏失焦自动暂停）→ 玩家不 tick，食物不消耗；
- 已修：`game-g122/options.txt` 写 `pauseOnLostFocus:false`；`lang:zh_cn` 由 `tools/mcp_prep.mjs` 写入；
- 复验流程：`gamemode survival @p` → `effect give @p hunger` 降 hunger → `control.startUsing` 3s → `stopUsing` → `player.getState` food/saturation + `/clear`；对照 `minecraft:apple`。

## 4. 冲压机链路（g122）：**PASS**

关键布局（用户纠正）：**冲压机与置物台之间必须留 1 格空气**，press 的轴是水平方向（`HorizontalKineticBlock`，`getRotationAxis = HORIZONTAL_FACING 的轴`，见 `work/refs/create-fly/.../MechanicalPressBlock.java`）。

实测布局（世界坐标 `-332/100/-41`）：
```
y=99   stone（支撑）
y=100  create:depot
y=101  air（必须留空）
y=102  create:mechanical_press[facing=west]
y=102  x=-331 create:shaft[axis=x]
y=102  x=-330 create:creative_motor[facing=west]
```
- 建法：`world.setBlock` 放方块（含状态），等 ~2.5s 网络建立；
- 读数（`command.run data get block ...`）：motor `Speed=-16.0f, Network.Size=3`、shaft `Speed=-16`、**press `Speed=-16.0f, Network.Size=3, Running=1b`** ✅
- 投料：`give minecraft:copper_ingot 4` → `inventory.selectHotbar` → 站到置物台侧面（水平视线）`control.lookAt` 置物台 → `interact.useItem`（真实右键）→ depot `HeldItem=copper_ingot×4, Locked:1b`；
- 产出（4 秒后）：depot `Inventory:[{id:"create:copper_sheet",count:2}]` —— **4 铜锭 → 2 铜板**，press `Finished=1b` ✅
- 注意：
  - `create:copper_ingot` 不存在，Create 6 用 **`minecraft:copper_ingot`**；
  - 本版 mcpfabric bridge **没有 container.***；投料用真实右键（`interact.useItem`）即可，等价于容器转移；
  - press 轴是水平（facing 轴），不是竖直：shaft 必须放在 press 的东/西（facing 轴两侧），不能放头顶；
  - 置物台与 press 必须有 1 格空气，否则 press 不工作（用户纠正）。

## 5. 门/牌匾（g122，live createdeco）：PASS

### 门（createdeco:andesite_door）
- 真实放置：give → inventory.selectHotbar → interact.placeBlock（贴石头 face=up）→ world.getBlock：
  - lower: {id:"createdeco:andesite_door", facing:"north", half:"lower", hinge:"left", open:"false"}
  - upper: {half:"upper", facing:"north", open:"false"} —— 两半同 id、half 正确 ✅
- 空手右击门（control.lookAt 对准 → interact.useItem）：target=block, Success → lower+upper 均 open=true ✅
- 敲上半 interact.breakBlock {mode:"instant"} → y/y+1 均 air ✅（双半联动拆除）
- 截图：g33/func-audit/door_open.png、door_client_view.png

### 牌匾（createdeco:black_placard）
- 贴墙：interact.placeBlock {face:"south"} → {face:"wall", facing:"south"} ✅；贴地 → {face:"floor"} ✅
- 截图：g33/func-audit/placard_wall.png

### 重要坑（已验证）
- 交互方块必须真实放置（interact.placeBlock）；用 world.setBlock 或 /setblock 放的门在客户端不显示（幽灵方块），准星穿过去 → interact.useItem 返回 target=air、无法开门；真实放置后立即生效。
- interact.useItem 依赖客户端准星 mc.hitResult；先用 vision.describeScene 的 lookingAt 确认准星命中哪个方块。

## 6. CEI 思索 + ponder 3D（g122，live create-fly）

- 打开方式：客户端命令 `/ponder <id>`（不需旧 probe），`chat.send` 即可；
- **cogwheel 场景**：`/ponder create:cogwheel` → 白平台 + 齿轮/传动轴 3D ✅，标题中文「使用齿轮来传递旋转力」；
- **windmill 场景**：从 ponder index 点条目进入 → 白平台 + 风车/风帆 3D ✅（证明 3D 渲染管线正常，R421 结论成立）；
- **CEI index**：`/ponder create_enchantment_industry:blaze_enchanter` → 中文 UI（「思索……认识烈焰人附魔室」「通入液态经验来激活它」「关联词条」）✅；
- **CEI 场景缺口**：`/ponder create_enchantment_industry:experience_nugget` → 日志 `Could not find ponder scenes for item: create_enchantment_industry:experience_nugget`，界面不打开；CEI 的 ExperienceScene 未绑定到该 item（需 CEI lane 检查 scene 注册 id）；
- `[sky262 ponder]` 日志：`frameEmpty=false`，偶发 `tex=72x72`（ponder icon cache）；
- 截图：`func-audit/ctrl_cogwheel_a.png`、`cmp_cogwheel_1.png`、`cmp_cei_1.png`、`ceiicon_0.png`、`cei_grid_6.png`（windmill 3D 场景）。

## 7. final sweep（post-promote，live 114 + quests 86900d5b）

```
blocks: placed=4187  failures=0  unknown=0
items : ok=4763     unknown=0   rawkey=0   error=0
```
- 命令：`node tools/sweep_blocks.mjs --game <dir>` / `node tools/sweep_items.mjs --game <dir>`
- 清单：`python tools/regen_ids.py <staging>`（本机生成 4187/4763）
- 日志：`work/run26/port/g29/g123_blocks.log`、`g123_items.log`

## 8. harness 补充结论（mcpfabric）

- `/ponder <item-id>` 是 **客户端命令**，用 `chat.send {"/ponder ..."}` 可直接打开思索（无需旧 probe、无需按键注入）；打开的是 tag 索引时无 3D 区属正常；
- bridge 实际提供 `container.*`（远端的 tools.js 列表未包含，但 RPC 可用）；
- 交互必须「真实放置」：`interact.placeBlock` 放置的门/牌匾，`world.setBlock`/`/setblock` 放的是客户端幽灵方块（准星穿过、useItem target=air）；
- 交互排查：`vision.describeScene` 的 `lookingAt`。