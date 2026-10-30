# lab-100 交互/功能矩阵报告（interact-probe）

> 实例轮换：game-lab（ponder 矩阵后清空）/ game-matrix（promoted live 115 + mcpfabric）/ 各候选 game-g1xx。
> 关键基线：staging 与 live 逐关键 jar SHA 一致（create-fly 31ff67d0、crashfix 1.0.5、CEI 5c0fdb9b、rope 463859a6、minersdelight 833d7333、quests 86900d5b、doorfix 8ab1f1c7、sable 3f315c26）。

## 1. 脚本

| 任务 | 脚本 | 输出 |
|---|---|---|
| 全量方块右键 | work/run26/port/g33/lab/test_blocks_use_fix.mjs（原 tools/test_blocks_use.mjs 的 player.useItem 改为 interact.useItem） | g29/lab_blocks_use.json |
| 门双半 | tools/test_doors.mjs | g29/lab_doors_*.json |
| 装备 | work/run26/port/g33/lab/wear_check.mjs | 截图 |
| 物品图标 | work/run26/port/g33/lab/itemfix_check.mjs | lab-shots/itemfix/icons.png |
| 组装器视觉 | lab/asm_visual3.mjs（空手瞄准 physics_assembler + 每 0.5s 截图） | lab-shots/asm-visual/ |
| ns 树叶 | lab/leaves_check.mjs | lab-shots/leaves/ |

## 2. 结果

### 2.1 promoted live 115（mcpfabric dev）— 全部 PASS
- 标题+进世界 OK；crash-reports 空；
- Unknown tag: sable:=0、Exception loading blockstate=0、Unable to bake item_model=0、Registry loading errors=0、Multiple atlases=0；
- 门双半 129 door-like / failures=0（doorfix 8ab1f1c7 生效）；
- press 真实右键 PASS：Running=1, Ticks=106, Finished=1，depot copper_sheet（lab-shots/v101-press.png）。

### 2.2 全量方块右键（live 115）
- 进度 0→1200 / 4187（interactive 183、changed 36、errors 0），随后客户端崩溃（见 §3），未跑完；
- 崩溃为 natures_spirit 树叶 LeavesBlock.animateTick NPE，非扫描脚本问题。

### 2.3 装备/图标（itemfix staging = live115 + 21 资源替换）
- 日志：Missing textures 30→20、bake=0、blockstate=0、registry=0、crash=0；
- 图标：jetpack 16x16、create_connected 3 个 3D 方块图标、corndelight nachos 正常（lab-shots/itemfix/icons.png）；
- 可穿戴：goggles(HEAD) / copper_backtank(CHEST) / cardboard 四件 / diving 头盔+靴 全部 item replace 成功（worn2.png）；
- createaddition:metal_girder 无此物品 id（jar 内只有 models/block/connector/girder_base.json，是方块模型部件）。

### 2.4 A/B press
| 臂 | 结果 |
|---|---|
| live 115 真实右键 | PASS Running=1, Ticks=106，depot copper_sheet |
| g160（+common-tags） | PASS Running=1, Ticks=64，depot copper_sheet |
=> common-tags 对 press 非必要（未 promote）。

### 2.5 seqassembly 修复链（g171→g188）
| 版本 | 结果 | 关卡 |
|---|---|---|
| g171 | Bootstrap 崩 | doorfix target 类错（BlockBehaviour→Block） |
| g172 | PASS（除 sable tag） | - |
| g173/g174 | world-load 崩 | Float cast / 数据 schema |
| g175 | 快速 PASS（sable=0） | - |
| g176 | world-load 崩 | {"item"} 旧键 |
| g177 | world-load 崩 | ingredient 对象形式 |
| g178 | world-load 崩 | track 数组 + Holder cast |
| g180 | track 数组对象/字符串都不行 | - |
| g181 | track 仍失败 | - |
| g188 | 世界加载 OK，registry=0；recipe give 对 seq 模板不适用（vanilla 对照 OK） | - |

### 2.6 ns 树叶修复（g188）
- aspen / blue_wisteria / cedar / coconut leaves 放置 → 等待 30s → 破坏：0 crash，crash-reports 空（lab-shots/leaves/）。

## 3. 新发现的真实缺陷（已报 lead/aero）

1. natures_spirit 树叶 NPE（客户端崩溃）：LeavesBlock.animateTick 调 ambientLeavesBlockSoundPlayer 为 null；26.3 的 LeavesBlock 构造函数要求传入 AmbientLeavesBlockSoundPlayer（work/refs/mc26.3/.../LeavesBlock.java:34-40），该 mod 的自定义树叶类（ParticleLeaves/ProjectileLeaves/VinesLeaves）仍在旧构造签名/空实现。复现：place 任一 natures_spirit 树叶并等待 tick；crash-report crash-2026-10-21_02.41.31-client.txt。修复件 abd15661 后在 g188 复测 PASS。
2. 组装器/拉杆视觉（用户反馈）：已定位为客户端 tick/HUD 未注册（SimulatedFabricClient.onInitializeClient 缺 END_CLIENT_TICK/HUD 注册），aero 修复 309e81b2；仍需 crashfix phase H 的搭法做 10 tick 截图验收（我这边的平面摆放不构成可装配结构）。
3. doorfix mixin 两处签名错（已修）：BlockBehaviour.playerWillDestroy → Block.playerWillDestroy（返回 BlockState，必须 CallbackInfoReturnable<BlockState>）。
4. sable 空 tag 无效：PhysicsBlockPropertiesDefinitionLoader 用 getTagOrEmpty 的条目数判断存在性，空 JSON 标签仍报 unknown；修复 3f315c26 改为 getTag(...).isPresent()。
5. Create sequenced_assembly 数据/编解码连坏 4 关：Optional→Float、Holder→Recipe、空 ComponentsIngredient、ingredient schema；修复链 72614a35（create-fly 三处）+ seq 数据 319cf882/dd608584/最终 1.0.3。

## 4. 已知限制 / 判据说明
- recipe give 只能验证 vanilla 可解锁配方；Create sequenced_assembly 是模板生成，不可 give（vanilla minecraft:stick 对照成功、4 条 seq 全 unknown），建议以 Registry loading errors=0 + 世界加载 + 0 crash 作为 seq 数据判据；
- 组装器视觉验收需 phase H 搭法；
- createaddition:metal_girder 不是物品。

### 2.1b promoted live 116（g193）终验：全 PASS（2026-10-21 03:4x）
- 环境：实际 `work/run26/mods-stable` 116 jar + mcpfabric；
- 标题+进世界 OK、crash-reports 空；
- `Unknown tag: sable:`=0、`Exception loading blockstate`=0、`Unable to bake item_model`=0、`Registry loading errors`=0、`Multiple atlases`=0；
- `Missing textures in model`=**20**（live 115 基线 30 → 下降 10）；
- 图标：jetpack 16×16、create_connected catalyst 3D（`lab-shots/v102/icons.png`）；
- ns 树叶 30s 放置/破坏 0 crash（`lab-shots/v102/leaves.png`）；
- 结论：可发 1.0.2。
### 2.7 g148/g149：剪贴板 + Nixie Tube + blocks 224-1000（2026-10-21 03:5x）
- **clipfix 6e334359（g148）**：give `create:clipboard` 右键打开 GUI（screen=other）→ close ×3 回到 none，无 VerifyError/NPE；
- **新 P0 发现**：右键 Nixie Tube（手持物品）→ **服务端崩** `NoSuchMethodError CommandSourceStack.<init>` at create-fly `DynamicComponent.getCommandSource`（1.21 旧构造签名），crash `crash-2026-10-21_03.31.17-server.txt`；
- **修复 f574ae39（g149）**：同一操作 ×3 不再崩（无 server crash-report、不掉线）；clipboard 打开/关闭仍 PASS；
- **blocks 224→1000（GUI-aware，crashfix `test_blocks_use_gui.mjs`）**：776 blocks / interactive 245 / changed 7 / **errors 0** / guiOpened 0，0 crash、0 screen stuck；输出 `g29/lab_blocks_224_1000_g149.json`；
- 说明：此前 224 处的 ClipboardScreen NPE 主要由扫描脚本不关 GUI 造成；GUI-aware 脚本 + clipfix 后不再复现。
### 2.8 promoted live 1.0.3 终验（2026-10-21 04:xx）
- 日志（实际 mods-stable 116 + mcpfabric）：`Missing textures in model`=**0**（原 20）、bake=0、blockstate=0、registry=0、sable=0、Multiple atlases=0、crash-reports 空；
- Nixie Tube 右键（手持 clipboard）×3：Success、服务端不崩（`DynamicComponent.getCommandSource` 已修 `f574ae39`→`e78bcc12` 链）；
- 剪贴板：对准空气右键打开 ×3 → close 回 none，无 VerifyError/NPE；
- 可穿戴（live jetpack = `a1d5fe30`）：jetpack → armor.chest ✅、手持右键推进 **y 71.00→83.70** ✅、netherite_jetpack 穿上 ✅、aviators_goggles → armor.head ✅（截图 `lab-shots/jetpack/`、`lab-shots/v103/`）；
- blocks 全量覆盖（GUI-aware + 逐方块 LAB 日志）：0-224（224/0 err）、224-1000（776/0 err）、1000-3000（2000，0 crash）、2950-3200（250/0 err）、3200-4187（987/0 err）；全程 0 crash、0 screen stuck；
- 03:50 一次「服务端挂起（spark waiting for world statistics）」在随后 3 次分段复跑中未复现（含 2950-3200 精确定位段），判为长扫瞬时卡顿，非特定方块 bug；
- 结论：1.0.3 全判据 PASS。
### 2.9 1.0.4 候选（g160-promote-cand，117）验证 PASS（2026-10-21 04:2x）
- 启动日志：Missing textures=0、bake=0、blockstate=0、registry=0、sable=0、crash-reports 空；
- jetpack 穿戴推进（`11a738db`）：穿 chest + 主手空 + 长按右键 **y 71.00→85.52**；卸下后空手长按**不推**（96.68→71.74 下落）；手持 jetpack 长按仍推（71.00→83.96）；
- 无 crash；截图 `lab-shots/g160c/{worn_thrust2,unequipped_hold}.png`；
- flywheel debug 命令：`flywheel`/`create debug` 均不存在 ⇒ 该项跳过（FlwCommands 修复无法用命令验）。
### 2.10 g86 basinfix 候选（create-fly `ceab8ec4` tag 修复）烟测（2026-10-21 05:xx）
- 启动/进世界：**无 ICCE、无 crash-report**；
- 机器 BE 放置+交互 0 crash：basin（Input/OutputTanks 可读）、mechanical_mixer（BE 正常，Speed=0）、deployer（State=waiting，交互 Success）、mechanical_crafter（Phase=IDLE，ConnectedInput 正常）；截图 `lab-shots/basinfix/`；
- **未拿到断言**：
  - belt：`setblock create:belt` 成功但 ~2.5s 自毁为 air；belt 物品两步右键（shaftA→shaftB）`interact.useItem` 返回 target=air（useItemOn PASS）；**live 1.0.4 基线同表现**，非候选回归，需正确玩家式摆放；
  - mixer 供能：竖直 shaft+电机（in/out）、顶部 cogwheel+侧向 shaft、电机压顶三种摆法 Speed 均=0，需标准布局；
  - deployer/crafter 产出断言需 GUI 配置（装物品/装配方），本轮只验 BE 与交互不崩。
### 2.11 g173-final（1.0.6 数据件）进世界失败：8 处 datapack schema 错误（2026-10-21 18:5x）
- 结果：world load 报「数据包错误」，`Registry loading errors`：
  - advancement ×4：`simulated:{no_pressure,speed_is_key,thataway,the_definition_of_up}` —— `conditions.location` 用数组，26.3 要对象；
  - loot_table ×1：`simulated:blocks/merging_glue` —— entry `name: minecraft:air`（非法）；
  - recipe ×3：`simulated:filling/honey_glue`（`fluid_tag` 缺 `#`）、`aeronautics:mixing/levitite_blend`（`fluid_tag` 缺 `#` → MixingRecipe 无 result/fluid result）、`simulated:sequenced_assembly/engine_assembly`（cutting 步缺 `processing_time`）；
- 修法已发 aero（逐条对应 live 同类型 schema）；88 条 recipe 与旧 recipes jar 重复但内容相同，无害；
- 客户端已释放。
### 2.12 g174-final（aero-recipes 1.0.4 `3c098048`）：8 处→剩 5 处（2026-10-21 19:0x）
- 已修复：loot merging_glue、filling honey_glue、seqassembly engine_assembly、advancement 4 条的数组问题已改成对象；
- 剩余错误：
  - advancement ×4（no_pressure/speed_is_key/thataway/the_definition_of_up）：`location` 需要 type-dispatch：
    live 权威样例 FarmersDelight：`"location": {"type": "minecraft:match_block", "blocks": "minecraft:campfire"}`；
  - recipe `aeronautics:mixing/levitite_blend`：`fluid_results` 复数在 create:mixing 这个 build 里仍报「List is too short / must have a result or a fluid result」（CEI grinding 类型同 key 合法，但 create:mixing 不认）→ 需 aero 查 shipped MixingRecipe codec 或改数据；
- world load 仍被挡，recipe give / 掉落 / item-defs 图标待 g175。
### 2.13 g177-final（aero-recipes 1.0.6 `f5452f28` + 服务端安全件）：客户端回归 PASS（2026-10-21 19:1x）
- 世界加载成功、`Registry loading errors`=0、无 `Failed to parse`（4 条为 Realms 噪声）；
- 3 条 `recipe give` 成功（aviators_goggles / andesite_propeller / simulated:crafting/white_nameplate_from_other_nameplate）；
- 掉落：生存+钻石镐破坏 `aeronautics:andesite_propeller` → 掉落自身；`offroad:borehead_bearing` → 掉落「镗头轴承」；
- 机器 quick：press `Speed=-16.0f`/Network 3 ✅；basin+mechanical_mixer BE 正常（mixer Speed=0 为供能摆法问题）；0 crash；
- 图标：`createdieselgenerators:canister`、`waystones:bound_scroll`、`createdeco:brass_coinstack` 正常；
- **待确认**：`createdeco:brass_coin/copper_coin/iron_coin`、`dndecor:belt/belt_connector` 在构建中不存在（未知物品），item-defs 对应的真实 id 待 lead 确认；
- 截图：`lab-shots/g177/{g177_icons,g177_machines}.png`（截图失败因游戏窗口被最小化，Windows MCP 恢复窗口后正常）。
### 2.14 promoted live 1.0.6（实际 mods-stable 117 + mcpfabric）终验 PASS（2026-10-21 19:2x）
- 基线：live 117 jar、`sky262-aero-recipes-1.0.6.jar f5452f28`、旧 `sky262-recipes-1.0.0.jar` 已移除；staging 118（含 mcpfabric）；
- 结果：标题+进世界 OK；`Registry loading errors`=**0**；`Failed to parse`（排除 Realms 噪声）=**0**；loot 解析错误=0；crash 行=0；crash-reports 空；
- 3 条 `recipe give` 成功（aviators_goggles / andesite_propeller / simulated:crafting/white_nameplate）；
- 掉落：`aeronautics:andesite_propeller` → 掉「安山螺旋桨」；`offroad:borehead_bearing` → 掉「镗头轴承」；
- 截图：`lab-shots/live106/{live106_world,live106_world2}.png`；
- 结论：1.0.6 可发版收尾。
### 2.15 g182-final（1.0.7 候选）：核心 PASS，2 条新 advancement 父节点缺失（2026-10-21 19:3x）
- PASS：世界加载、`Registry loading errors`=0、无 `Failed to parse`、crash-reports 空；
- 3 条 stonecutting `recipe give` 成功（brass_bars/copper_tiles/copper_ingot）；
- 27 条 custom-trigger advancements 注册正常（grant `aeronautics:for_every_action`、`simulated:my_eye`、`aeronautics:ghostbuster` 均成功）；
- 问题：`Couldn't load advancements` 7 条，其中新引入 2 条 `simulated:must_come_up`、`simulated:rewind_time`，根因 parent `simulated:what_goes_down` 在包内与 live 都不存在；其余 5 条（createframed ×3、dungeons_arise ×2）为历史已知；
- 修法：补 `simulated:what_goes_down` 或改 parent/删除这 2 条；
- 说明：26.3 无 `advancement get`，entity predicate 语法未通过，本轮触发证据以 grant 成功 + registry=0 为准。
### 2.16 g183-final（1.0.7，aero-recipes 1.0.8）：全 PASS（2026-10-21 19:3x）
- 世界加载、`Registry loading errors`=0、`Failed to parse`=0、crash-reports 空；
- `Couldn't load advancements` 只剩历史 5 条（createframed ×3 + dungeons_arise ×2），**本包相关 0 条**；
- 3 条 stonecutting `recipe give` 成功；
- `advancement grant` 实测 `aeronautics:for_every_action`、`simulated:must_come_up`、`simulated:rewind_time` 均成功（`what_goes_down` 已存在）；
- 结论：1.0.7 可 promote。
