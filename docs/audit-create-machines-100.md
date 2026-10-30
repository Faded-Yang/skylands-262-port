# audit-create-machines-100 —— Create 机器链路可玩性审计（100 项）

> 背景：用户反馈「Create 内容加入后续内容后几乎完全不能用」。本审计覆盖 18 类机器链路：
> 放置 / 旋转网络（Speed、Network.Size）/ 投料 / 产出 / 崩溃。
> 静态部分已完成；动态部分待客户端锁空后用 mcpfabric 执行并回填。

## 0. 结论速览（静态）

| 检查项 | 结果 | 证据 |
|---|---|---|
| recipe 数据完整性 | **与上游 create-fly 26.2-6.0.9-2 逐类型一致** | 见 §1 表；仅 `create:sequenced_assembly` 3 条按设计删除（DELIVERY 声明） |
| recipe 加载错误 | 近期 4 个审计局日志 **0 条** Parsing error / Unable to load recipe | `g33/game-audit100` 等 latest.log grep |
| 机器 BE 类 | 18 类全部存在（Press/Mixer/Basin/Depot/Millstone/Saw/Deployer/Bearing/Gearbox/Clutch/Gearshift/Fan/Spout/ItemDrain/Funnel/Chute/Crafter/Controls） | create-fly jar 类表 |
| 机器 renderer/BER | 除 bearing/clutch/gearshift/controls（按设计无 BER 或走 contraption 渲染）外全部存在 | create-fly jar 类表 |
| sky262-createfix 干扰 | 仅 1 个 mixin：RuntimeDataGenerator 跳过 modded 木头运行时切割配方，**不涉及机器逻辑** | jar 内容 |

## 1. recipe 类型覆盖（live `sky262-create-recipes` vs 上游 26.2 jar）

| recipe type | 上游 26.2 | live | 机器 |
|---|---:|---:|---|
| create:pressing | 11 | 11 | press |
| create:mixing | 11 | 11 | mixer/basin |
| create:milling | 47 | 47 | millstone |
| create:cutting | 156 | 156 | saw |
| create:deploying | 233 | 233 | deployer |
| create:splashing | 33 | 33 | fan（bulk washing） |
| create:haunting | 20 | 20 | fan |
| minecraft:smoking | 1 | 1 | fan（bulk smoking，其余走 vanilla 数据） |
| create:filling | 10 | 10 | spout |
| create:emptying | 2 | 2 | item drain |
| create:item_application | 8 | 8 | deployer |
| create:compacting | 7 | 7 | press |
| create:mechanical_crafting | 4 | 4 | crafting table |
| create:item_copying | 1 | 1 | crafting table |
| create:sandpaper_polishing | 1 | 1 | 砂纸 |
| create:sequenced_assembly | 3 | **0（有意删）** | 序列组装（降级） |

> 结论：**不是 recipe 缺失导致「几乎不能用」**（与反馈 #4 的 press PASS 一致）。

## 2. 动态测试矩阵（mcpfabric，待锁空执行）

统一步骤：`creative_motor[/facing] + shaft 链` 建网络 → `perception/world.getBlock` 读目标机器 BE 数据（`Speed`/`Network.Size`/`Running`/`Finished`）→ 投料 → 等待 → 读产物 → 检查 crash/错误日志。

| # | 链路 | 放置/联网 | 投料方式 | 期望产出 | 状态 |
|---|---|---|---|---|---|
| 1 | press + depot | | depot 上放铜锭 | copper_sheet | 待测 |
| 2 | mixer + basin | | basin 内放配方料 | 混合产物 | 待测 |
| 3 | millstone | | 手持/漏斗投料 | milling 产物 | 待测 |
| 4 | saw | | 传送带/depot 投料 | cutting 产物 | 待测 |
| 5 | deployer | | 手持物品/工具 | deploying 产物 | 待测 |
| 6 | mechanical bearing | | 扳手/右键 | 旋转 contraption | 待测 |
| 7 | gearbox | | 旋转网络 | 多轴输出 | 待测 |
| 8 | clutch | | 红石信号 | 通断 | 待测 |
| 9 | gearshift | | 红石信号 | 换向 | 待测 |
| 10 | encased fan + bulk washing | | 上方水/物品 | splashing 产物 | 待测 |
| 11 | encased fan + bulk smoking | | 上方火/物品 | smoking 产物 | 待测 |
| 12 | spout | | 传送带 + 流体罐 | filling 产物 | 待测 |
| 13 | item drain | | 容器物品 | emptying 产物 | 待测 |
| 14 | funnel | | 容器/物品 | 转移 | 待测 |
| 15 | chute | | 上方物品 | 下落/转移 | 待测 |
| 16 | crafting table | | 摆放配方物品 | mechanical crafting 产物 | 待测 |
| 17 | train controls | | 放置到列车/车厢 | 控制界面 | 待测 |
| 18 | （对照）press 全链路 | | motor+shaft+press+depot | 4 铜锭→2 铜板 | 待测（回归 #4 PASS 基线） |

## 2.5 静态地雷排查（2026-10-21 全量 scan_landmines）

- 全量：groups=1159（HIGH 32 / MED 59 / LOW 74；未安装可选依赖 755 忽略）。
- 机器主链路**无 HIGH**；HIGH 集中在 RRV/REI 按钮、PotionBrewing、ComputerCraft、蓝图/剪贴板等可选/边缘路径。
- 两个机器相邻风险（已判不阻塞，但动态需盯）：
  1. `ComponentsIngredient.test` 调 `DataComponentPatch.entrySet()`（26.3 已删）——
     静态核对：**live 全部 recipe 中 `fabric:components` 类型 = 0**，机器配方匹配不会走到该 test ⇒ 非阻塞；
  2. `BearingVisual.<init>` 调 `com.mojang.math.Axis.of(Vector3f)`（26.3 签名 `Vector3fc`）——
     `AllBlockEntityRenders` 引用 BearingVisual ⇒ 若该 visual 被实例化会 NoSuchMethodError；
     但当前 live 启动 0 崩溃，说明注册路径可能未触发；**动态轴承测试时重点看客户端是否崩**，崩则用 FluidFix 同款 bridge 修。

## 5. 动态结果（2026-10-21 01:00–01:12，lab 实例 game-lab）

> 实例中途被 kill（Lead 排 A/B 组装器），以下为已完成部分。

### 5.1 press + depot（重点项）

| 检查 | 结果 | 证据 |
|---|---|---|
| 放置 | ✅ creative_motor → shaft → mechanical_press → depot 全部 setblock 成功 | 命令回执 |
| 旋转网络 | ✅ motor Speed=16.0；shaft Network.Size=2 Speed=-16；press Network.Size=3 Speed=-16、Source=[-320,72,-39] | `data get block` |
| press BE 字段 | ✅ `{Speed:-16.0f, Network:{Size:3}, Running:0b, Ticks:0, Finished:0b}` | 同上 |
| 投料（depot 库存） | ✅ `data merge block ... {Inventory:[{id:"minecraft:copper_ingot",count:4}]}` 写入成功 | data get 回读 |
| **产出** | ❌ **press Running 始终 0、Ticks 0、depot 库存不变** | 等待 2.5s 后复读 |
| 崩溃 | 无 | 日志无异常 |

### 5.2 ~~缺失 c: 标签~~（**已撤回，误报**）

- 初扫 top-level jar 时以为 92 个 `c:` 标签缺失；**复核发现它们在 fabric-api 的嵌套模块里**：
  `fabric-api-0.163.0+26.3.jar!fabric-convention-tags-v2-…jar` 内含 `data/c/tags/item/ingots/copper.json` 等全部常规标签；
- 因此 press「不动」**不是标签问题**；与 Lead/probe 结论一致：**`data merge` 写 depot Inventory 不会触发 press**（press 压的是 depot 的 HeldItem/实体），A/B 真实右键两臂均 PASS；
- 结论：机器代码/BE 正常，投料必须用**真实交互**（右键/漏斗/传送带），不能用 NBT merge。

### 5.3 已验证的测试手法（后续复用）

- 建网：`creative_motor[facing=X]` → `shaft[axis=...]` → 机器；**按顺序逐个 setblock 并各等 300ms**，否则网络可能不合并（第一次连续 setblock 时 Speed=0）；
- 读状态：`data get block <pos>`，看 `Speed`/`Network.Size`/`Running`/`Ticks`/`Finished`；
- 投料：`data merge block <depot> {Inventory:[{id:"minecraft:copper_ingot",count:4}]}`（26.3 组件格式）；press 的加工目标是**机器正下方方块里的 ItemEntity**（`PressingBehaviour` 扫 `AABB(pos.below())`，要求 `onGround`）；
- 右键投料受限：press 正上方挡视线，玩家需站在地板层平视 depot 侧面；本次未成功（hitResult=air），改用 data merge/召唤 item 实体；
- 截图：`vision.screenshot` 返回 base64（字段 `base64`）。

### 5.4 ~~common-tags 候选~~（**作废，不 promote**）

- `sky262-common-tags-1.0.0.jar`：20,422 B / `7ab53d7a6799a1b45a4e053c87a32f82f0977431724dea906e2bae70441037fd`
  - 纯数据 jar（无代码），补 92 个缺失的 `c:` 常规 item 标签（159 个不同标签/832 次引用全部覆盖）；
  - 生成规则：ingots/nuggets/plates(storage_blocks)/rods/wires/dyes/crops/foods/glass/chests/barrels/stripped_logs 等按物品命名精确映射（例：`c:ingots/copper`→`minecraft:copper_ingot`、`c:zinc_plates`→`createaddition:zinc_sheet`、`c:iron_plates`→`create:iron_sheet`）；
  - staging：**`g86/stage/mods-commontags-final`（115 jar = live + 本件）**；
  - 结论：作废（fabric-api 已提供这些标签，本件多余且映射可能不如上游准确）。
- 验证判据（press）：Network Speed=-16 不变，**Press Running→1、Ticks→120、Finished→1，depot 出现 `create:copper_sheet`**。

### 5.5 下一步（待新实例）

1. 生成并安装 **`sky262-common-tags`**（纯数据 jar，补齐上述 92 个 `c:` 标签，值按物品命名规则映射，如 `c:ingots/copper`→`minecraft:copper_ingot`、`c:ingots/zinc`→`create:zinc_ingot`、`c:iron_plates`→`create:iron_sheet`）；
2. 重跑 press（铜锭→铜板）验证从 "Running=0" 变为 "Finished=1 + depot 出现 copper_sheet"；
3. 再跑其余 17 条矩阵；失败项按 §3 排查；
4. 若 common-tags 恢复后仍有机器不动，再逐个查（mixer 需 basin、millstone 需上方漏斗等）。

## 6. 第二轮矩阵（live 116，2026-10-21，真实交互投料）

### 6.1 基线（live 116 静态确认）

- live jars=116；create-fly=`2290891b…`（19,650,964 B，含 `FluidFix`，无旧 keyfix 桥——由 crashfix 1.0.5 覆盖）；
- create-recipes：1607 条，类型齐全（pressing 11 / mixing 11 / filling 10 / emptying 2 / mechcraft 4；sequenced_assembly 仍 0＝原样）；
- CEI=`9ccc31c3…`（816,449 B，含 `[cei]` 日志；ponder 绑定正常）；
- fabric-convention-tags-v2（fabric-api 嵌套模块）提供全部 `c:` 标签，recipe 匹配无标签缺口。

### 6.2 本轮测试方法（吸取教训）

- **投料只用真实交互/实体**：`interact.useItem` 对准方块（先 `world.raycast` 验证视线），或掉落实体/漏斗/传送带；**禁用 NBT merge 写库存**；
- press 布局：floor y=Y-2、depot y=Y-1、press y=Y；玩家站 y=Y-2（eye≈Y-0.4），从侧面右键 depot，视线低于 press 底面；
- 每条流程：放置 → 建网（逐块 setblock + 300ms）→ 读 `Speed/Network.Size` → 投料 → 等 2–4s → 读产出 BE/实体 → 截图 → 复检 bridge 存活（崩溃探测）。

### 6.3 已就绪的场景脚本（`work/run26/port/g33/lab100/`）

| 脚本 | 覆盖 | 布局要点 |
|---|---|---|
| `lablib.mjs` | 共享 helper | 连接/命令/teleport/lookAt/give/hotbar/use/raycast/截图 |
| `press2.mjs` | #1 press（真实右键投料） | motor+shaft+press+depot，玩家低位侧视 |
| `bearing.mjs` | #6 mechanical bearing（**重点 BearingVisual**） | motor→shaft(y)→bearing[up]；读 BE→扳手右键旋转→截图→bridge 存活 |
| `deployer.mjs` | #5 deployer | depot 上放 `create:shaft`（右键）；deployer 右键插入 `oak_planks`；期望 `create:cogwheel` |
| `fan.mjs` | #10 fan splashing | motor→shaft→fan[up]→水；上方掉落 `create:crushed_raw_copper`；期望 copper_nugget |

### 6.4 待补场景

- #11 fan smoking（fan[up]+火）、#12 spout（需流体供给）、#13 item drain（含水容器物品）、#16 mechanical crafting（3×3 crafter + 图案）、#17 train controls（右键开 UI）；其余常规项按 §2 矩阵补脚本。

## 6.7 Round 3（2026-10-21 19:16–19:45，live 1.0.6 / 117 jar + mcp 118）

> 关键工具修正：`lablib.teleport` 之前误用 command（`players.teleport` 是 RPC 方法名），导致之前所有 aim 都站在旧位置 —— 本轮已改为 `call("players.teleport", …)`；`players.give` 可能给到非选中槽，必须扫描 `player.getInventory` 后 `inventory.selectHotbar`（helper `hold(itemId)`）；薄/小形状目标统一改用 `interact.placeBlock`（显式 pos+face、构造 BlockHitResult，绕开 client crosshair）。

### 6.7.1 belt（PASS）

- 放置：`create:belt_connector`（物品 id 不是 `create:belt`）对**两个 shaft** 各 `interact.placeBlock(face=up)` 一次 → 5 格 belt 自动生成：`part=start/middle/end, facing=south, slope=horizontal, casing=false`；
- 控制器 BE：`{Length: 5, Speed: 16.0f, IsController: 1b, Network:{Size:2}, Inventory:{PositiveOrder:1b}}`；
- 输入：belt 上方放 `create:andesite_funnel[facing=down]`，掉落铁锭 → 被带上带走：`z=-44.5 → -40.87`（约 3.6 格，沿 +z 到 end）；截图 `work/run26/port/g33/lab100/lab-shots/matrix3/belt2.png`；
- 结论：**belt + funnel 传送 PASS**；funnel 无需额外电力。

### 6.7.2 mechanical crafter（建网 PASS，投料待手测）

- 2 个 crafter（`facing=north,pointing=up`）相邻；东侧 `create:cogwheel[axis=z]` 啮合 + shaft[axis=z] + motor → **crafter Speed=-16/16, Network.Size=5/4**（cogwheel 啮合供电成立；crafter 没有 `hasShaftTowards`，不能直连轴）；
- 投料：`interact.placeBlock(crafter, face=up)` 持铁锭/燧石均返回 `Pass[]`（未插入）→ 需漏斗/GUI 手测；无 crash；
- 结论：**供电/网格 PASS**；配方投料待人工验证。

### 6.7.3 deployer（建网 + 插料 PASS，产出待查）

- 布局：deployer `facing=down, axis_along_first=true` + 侧向 shaft[axis=x] + motor → `Speed=16, Network.Size=3`，State 在 expanding/retracting 循环；
- **插料 PASS**：对 deployer 的 **facing 面（down）** 调用 `interact.placeBlock`（命中点距中心 1.0 > 0.75 才进 item 槽）→ `Inventory:[{oak_planks×4}], HeldItem=oak_planks`；
- 目标：depot 上 `HeldItem=create:shaft` 已就位；
- 产出：10 s 内 depot 仍为 shaft，未变 `create:cogwheel`（Timer 出现 -24，State 循环）→ **待查**（可能需 Mode=PUNCH/目标须走 Depot Inventory/延时）；无 crash。

### 6.7.4 controls（限制，非 bug）

- `create:controls[facing=south]` 可放置，但 `data get block` = **不是方块实体**（standalone controls 没有 BE；train controls 只在**列车/contraption** 上装配后才有交互）；
- 右键（placeBlock face=up）均 `Pass[]`、screen 始终 none；
- 结论：**standalone 无法开 UI**，需先组装列车（下一轮或手测）；不算机器 bug。

### 6.7.5 工具教训（写入复用）

- `interact.placeBlock({x,y,z,face})` 是最可靠的真实交互方式：自带 reach 检查、显式 face、会用 `useItemOn`；
- 但 deployer/belt 这类需要 `hitLocation` 的方块要选对 face（deployer 必须 facing 面）；
- `player.getInventory` 的 `slot` 用于 `inventory.selectHotbar`，不要假设 give 落在 slot 0。

## 6.6 Round 2（2026-10-21 04:14–04:28）：P0 crash 定位 + 修复候选

### 6.6.1 P0：basin/mixer 配方匹配当场崩服（IncompatibleClassChangeError）

服务端崩溃（`crash-2026-10-21_04.19.47-server.txt`）：

```
java.lang.IncompatibleClassChangeError: Method 'boolean dev.eriksonn.aeronautics.compat.ContainerBridge.countSpace(Container,List,int,int)' must be Methodref constant
  at BasinBlockEntity.acceptItemOutputsIntoBasin(BasinBlockEntity.java:560)
  at ... MixedRecipe.matches -> BasinOperatingBlockEntity.getMatchingRecipes -> updateBasin
```

- 根因：create-fly 里 **80 处**对 `dev/eriksonn/aeronautics/compat/ContainerBridge` 的调用使用了 `invokestatic` + **InterfaceMethodref(tag 11)**，而该 `ContainerBridge` 实际是 **class**（access=0x31，非 interface）→ JVM 要求 Methodref，链接期抛 ICCE；
- 影响面：**30 个类、80 处调用**，覆盖 basin、belt、funnel、chute、crafter、deployer movement、arm、packager、schematicannon、train 等——即「Create 机器几乎不能用 / 一点就崩」的直接主因之一；
- 该错误来自我们移植时的 apicompat 注入（原版 create 用的是别的接口常量，注入时复用了 InterfaceMethodref 而未改 tag）。

### 6.6.2 修复候选（staging，实测 PASS）

- 做法：ASM 等价的常量池修复——把指向 `ContainerBridge` 的 **InterfaceMethodref(tag 11) 改为 Methodref(tag 10)**（两种常量结构相同，仅 tag 字节不同），共 30 类 / 80 处；不改任何字节码指令。
- 产物：`work/run26/port/g31/basinfix/create-fly-26.2-6.0.9-2-26.3-basinfix.jar`
  - 19,677,550 B，SHA `ceab8ec48d84bb534e00b51f061db5b96b47f6e20fe09c2636b360934e484593`
  - staging：**`g86/stage/mods-basinfix-final`（116 = live 116 换掉 create-fly）**；测试用 `mods-basinfix-mcp`（117，含 mcpfabric）。
- 实测（basinfix 实例）：
  - basin(71)+mixer(73，**间隔 1 格**，large cogwheel 斜向啮合 16→32 RPM)：mixing `andesite+iron_nugget → create:andesite_alloy` **成功**，mixer `Running=1, Ticks=32`；
  - 无再崩（本 log 无 ICCE；crash-reports 只有旧 04:19 那份）；截图 `lab-shots/matrix2/mixer3_basinfix.png`。
- 建议：**P0 promote**（Lead 决策），promote 后可正常用 basin 类机器。

### 6.6.3 本轮其它机器（正确布局后）

| 机器 | 结果 |
|---|---|
| fan splashing | **PASS**：fan(朝 +X)→water→depot；depot `HeldItem.FanProcessingType=create:splashing`、`FanProcessingTime 134→-1`，产物 `minecraft:copper_nugget ×9`（**注意：自由掉落实体不会被加工，必须放在 depot/belt 等 transported handler 上**） |
| millstone | **PASS**：轴从**下方**接；小麦掉落进 `Inventory`，`Timer 71→0` 后产出 `create:wheat_flour + minecraft:wheat_seeds` |
| mixer | **PASS**（见上）：必须 **basin 在 mixer 下方 2 格**（`getBasin()=below(2)`）、**≥32 RPM**（SpeedLevel.MEDIUM）；large cogwheel 需**斜向**啮合小 cog/mixer 才能 2× |
| press/deployer | 网络 PASS；真实右键投料自动化受 depot 13px 薄板 + 遮挡限制，需手测（probe A/B 已 PASS） |
| controls | 放置 PASS；UI 打开需手测（raycast/crosshair 对薄形状不可靠） |

### 6.6.4 结论

- **不是 create-fly 上游逻辑 bug**，是我们移植注入的常量池类型错误；修复后 basin/mixer 正常。
- fan/millstone「之前 FAIL」是布局/投料方式错误（自由实体 vs depot、轴上/下），非 bug。
### 6.5 结果（2026-10-21 04:0x，live 1.0.3 / 116 jar，实例 game-lab2）

> 全部用真实命令放置 + 逐块 300ms 建网；投料尝试真实右键；截图在 `work/run26/port/g33/lab-shots/matrix/`。

| # | 机器 | 放置 | 旋转网络（Speed/Size） | 投料/行为 | 结论 |
|---|---|---|---|---|---|
| 1 | press+depot | ✅ | ✅ Speed=-16, Size=3, Source 正确 | 自动右键投料受工具限制（depot 13px 薄板 + press 遮挡，server raycast 全 miss）；数据 merge 可入库存但不触发 | **网络 PASS；产出需人工右键**（probe A/B 已 PASS） |
| 2 | millstone | ✅ | ✅ Speed=16, Size=3（轴必须从**下方**接） | 掉落小麦 3s 未加工（物品滑落到地面） | 网络 PASS；加工 FAIL 待查（物品需在磨盘正上方中心/掉落位置） |
| 3 | saw | ✅ | ✅ Speed=-16, Size=3（轴在 facing 背面） | BE `Breaking` 已指向后方方块（无料时仍自转） | 网络 PASS |
| 4 | deployer | ✅ | ✅ Speed=16, Size=3（**必须 `axis_along_first=true` 且轴为水平**） | 状态在 waiting/retracting 循环；手持插入因 ray 瞄准未成功 | 网络 PASS；插入/部署待测 |
| 5 | bearing | ✅ | ✅ Speed=16, Size=3（轴在下） | 扳手右键 Success；**全程 0 crash** | **PASS**（`BearingVisual Axis.of` 风险未触发） |
| 6 | fan（splashing） | ✅ | ✅ Speed=16, Size=3 | 5s 内 `crushed_raw_copper` 未变（物品悬浮在水面/气流中） | 网络 PASS；**washing 未生效，FAIL 待查** |
| 7 | mixer+basin | ✅ | ❌ `hasShaftTowards=false`（轴不能直连）；顶部 cogwheel 方案 Speed 仍 0 | 未投料 | 网络未建立；需正确 cogwheel 啮合方式 |
| 8 | mechanical_crafter | ✅ | ❌ shaft 接背面 Speed=0 | 未投料 | 网络未建立（可能需 cogwheel/朝向修正） |
| 9 | controls（列车控制） | ✅ | —（无需动力） | 右键 ray miss（薄形状+server raycast 限制），UI 未打开 | 放置 PASS；UI 待手测 |
| 10 | gearbox/clutch/gearshift / spout / item drain / 其余 | 未测 | | | 待下一轮 |

**本轮确定非 bug 项**：机器 BE/网络/渲染均无崩溃；bearing 最可疑项 PASS；press 网络与 probe A/B 一致。
**待查 FAIL**：millstone 加工、fan washing、mixer/crafter 建网、controls UI。
**工具限制**：mcpfabric `world.raycast`（server-side）对 13px 薄板（depot）与小型机器形状连续 miss；`interact.useItem` 依赖客户端 crosshair，自动化右键需要更精确的 aim/站姿；后续建议用 `interact.placeBlock`（带 x,y,z/face）或先 `control.lookAt` 后等待 ≥2 tick 再 use。

## 3. 若动态失败：排查顺序

1. 先 `screen.get` / `player.getState` 确认不是交互上下文问题（需要蹲下/空手/正确的面）；
2. 机器 BE 数据读 `Speed`/`Network.Size`：为 0 ⇒ 旋转网络没连上（shaft 朝向/面）；
3. 有转速但不产出 ⇒ 配方匹配（`recipe matched` 日志）/输入槽位置；
4. 崩溃 ⇒ crash-report 栈，按栈定位（参考 `docs/landmines` 静态扫描结果）。

## 4. 证据路径

- 截图：`g33/create-audit100/`
- 日志：`g33/<game>/logs/latest.log`
- 静态扫描：`work/run26/port/g31/out/landmines-current.md`
