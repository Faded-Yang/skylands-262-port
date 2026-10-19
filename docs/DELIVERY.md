# 天穹群岛 → MC 26.3 + Fabric —— 交付说明

> **本文件是给用户看的「最终说明书」**：装了什么、每个 mod 损失了什么、哪些没装以及为什么。
> 详细技术记录在各 *fix-\* / port-\* / worldgen-\* * 文档里，本文件只做汇总与索引。
>
> 最后更新：R407 之后（**71 jar**，方块放置 / 物品 tooltip / 按住右键编辑值 / 值编辑屏开屏 四类崩溃已修；450 个物品名补全汉化）

---

## 一、怎么用

| 要做的事 | 做法 |
|---|---|
**启动游戏** | 双击 `启动浮岛世界.bat` |
**新建浮岛世界** | 创建世界 → **世界类型选「浮岛世界」** |
**看 mod 列表** | 标题画面 → **Mods** 按钮（Mod Menu） |
**老存档** | 不受影响，但**新地形只在新生成的区块出现** |

**版本**：MC 26.3 / Fabric Loader 0.19.5 / Java 25 / 144 个 mod 项（含 Fabric API 子模块）

---

## 二、装了什么（71 jar）

### 核心（自己移植的）
| jar | 来源 | 说明 |
|---|---|---|
`create-fly-26.2-6.0.9-2-26.3-patched.jar` | Create-Fly 26.2 | **字节码补丁**顶替 Create（上游无 26.3 分支）|
`aeronautics-fabric-0.1.0-port.26.3.jar` | 源码级移植 | |
`sable-fabric-26.3.jar` | 源码级移植 | |
`sablecompanion-1.6.0-26.3.jar` | 源码级移植 | |

### 26.3 原生构建（33 个，直接下载）
Sodium / Iris / Lithium / FerriteCore / ImmediatelyFast / MoreCulling / BadOptimizations /
Clumps / DynamicFPS / PacketFixer / spark / Chunky / JEI / Jade / Controlling /
InventoryProfilesNext / MouseTweaks / AppleSkin / BetterF3 / ClothConfig / Architectury /
Balm / CristelLib / libIPN / Searchables / Waystones / Xaero 小地图 + 世界地图 /
Towns&Towers / Structory / Geophilic / MoogsStructureLib / lithostitched

### 移植成功的（自己改的）
| mod | 原版本 | 验收 |
|---|---|---|
`sky-villages` | 1.21.1 Fabric | 进世界 |
`create-sky-village` | 1.20.1 Fabric | 进世界 |
`DungeonsArise` | NeoForge 1.21.1 | 进世界 |
`SkyVillages` | NeoForge 1.21.1 | 进世界 |
`no-void-structures` | 2.0.1 | 进世界 |
`create-hangars` | 1.0.0 | 进世界 |
`MoogsSoaringStructures` | NeoForge | 进世界 |
`rabbit_pathfinding_fix` | 1.0.5 | 进世界 |
`strayed-fates-forsaken` | 1.21.4 | 进世界 |
`imst`（沉浸结构） | 1.21.11 | 进世界 |
`Structory_Towers` | 1.21.1 | 进世界 |
`sablephysicscompat` | 1.3.0 | 进世界（B 级，见降级）|
`structures`（热气球） | 1.2 | 进世界 |
`interiors` | 1.20.1 Fabric | 进世界 |
`create-framed` | 1.20.1 Fabric | 进世界 |
`escalated` | 1.20.1 Fabric | 进世界 |
`createaddition` | 1.20.1 Fabric | 进世界（21 条降级，见 4.9）|
`passivemobspawn` | 1.0.0 | 进世界 |
`sablejade` | 1.3.0 | 进世界 |
`JadeAddons` | 6.1.2 | 进世界（**插件包名必须迁到 `jadeaddons`**，见 4.10）|
`constraintfix` | 1.6.0 | 进世界（绳索修复；玩法级场景未验，见 5.1）|
`FarmersDelight` | 26.3 官方 | 进世界 |
`chefsdelight` / `corndelight` / `ends_delight` | 混合 | 进世界 |

### 自建辅助
| jar | 作用 |
|---|---|
`sky262-preset-1.0.0.jar` | **浮岛世界类型**（`zsky262_preset`）|
`sky262-recipes-1.0.0.jar` | 88 条配方 |
`sky262crashfix-1.0.0.jar` | 修 `InputConstants.UNKNOWN` -1→0 导致的崩溃 |
`modmenu-21.0.0.jar` | mod 列表界面（Fabric 本身没有）|

### 汉化
**100%**：10,579 英文 / 10,807 中文 / 缺 0（42 个 namespace 全达标）

> R406 补了 397 条 `item.*`（26.3 的方块物品用 `item.*` 前缀，之前只有 `block.*` ⇒ 物品栏里显示原始 key）。

---

## 三、浮岛地形（最终定稿）

**= 原版 aerolith 地形，只改一处**

| 项 | 值 |
|---|---|
`sea_level` | 64（平整海面） |
密度函数 | 原版 6 个 `custom:` 函数，一字未改 |
`aquifers` | 保留原版 |
**唯一改动** | carver `skylands:cave` / `canyon`，`y=[170,450]`、`count=uniform(2,14)` |
维度高度 | `height=576`（浮岛在 y=320~447，原版 384 装不下）|

**已知限制（用户接受）**：岛只有 2~5 格厚 ⇒ **洞穴几乎挖不出来**；船可能浮空；局部可能有水柱。

> ⚠ **曾被否决的三个改法**（不要再试）：拆低层地面（R363）、岛加厚成"分层大陆"（R369）、三层叠加（R370）。
> 用户原话：「什么也不要动，我要原模原样的浮岛原效果」。

---

## 四、降级清单（按 mod 分组）

> **完整技术细节在括注的文档里**。这里只列「玩家能感知到的损失」。

### 4.1 Create 本体（`docs/DEGRADATIONS.md` §10~§11）
- **层状矿不生成**（`LayeredOreFeature`）
- **Create 物品不可堆肥**（`ComposterBlock.COMPOSTABLES` 重定向失效）
- **15 条 Ponder/渲染管线缺席**（黑屏修复的代价）
- **120 个 trim 调色板失败**（纯外观）
- 部分 `RenderSystem` 重定向失效
- **R407 视觉降级（纯视觉，功能不受影响）**：① 按住右键编辑数值时，手臂不再被强制取消挥动（会自然挥一次）；② 拖动存储仓（StockKeeper）滚动条时不再隐藏鼠标光标

### 4.2 `escalated`（`docs/port-1201.md` §1.4）
- datagen 整块、Ponder 教程
- 配置上限写死（128/32/10/10）
- **客户端 BER + Flywheel Visual ⇒ 扶梯踏步动画没了**（方块仍静态渲染）
- 5 个 advancement、SAFE_NBT 标签、`setMaxUpStep`
- 6 张 `minecraft:air` 手栏杆战利品表、2 个配方换材料

### 4.3 `interiors`（`docs/port-interiors.md` §7）
- datagen 入口全剥、无 Create 风格 tooltip
- 大椅子乘客抬高改 `positionRider`
- 2 条 mixin `require=0`（不匹配静默跳过）
- 创造栏用 Fabric 事件填充、kelp 顶面贴图替换
- **无降级**：方块/物品/实体注册、136 配方、55 战利品表、标签、坐下/移动行为

### 4.4 `create-framed`（`docs/port-framed.md`）
- 7 条降级，详见文档

### 4.5 食物 4 个（`docs/port-delight.md` §4）
- `corndelight`：堆肥概率；内容取 1.21 Fabric 移植版（1.0.0）而非 NeoForge 1.2.10
- `chefsdelight`：datagen 全摘（含村民交易）
- `ends_delight`：战利品注入（末影人掉龙牙等）、紫颂多肉自然生成、炉子物品展示渲染、
  **龙牙刀额外伤害**（mixin 注入点没了）、4 个刀的材质数值

### 4.6 `DungeonsArise`（`docs/port-batch2.md`）
- `minecraft:potion` 从诱捕豁免实体 tag 里删掉（26.3 无此 id）
- 唱片集合从 `music_discs` 换成 `creeper_drop_music_discs` ⇒ **可获得的唱片变少**

### 4.7 `sablephysicscompat`
- B 级：数据全解析，但 selector 指向的 mod 未安装

### 4.9 `createaddition`（`docs/port-createaddition.md` §8）
**这是降级最多的一个（21 条）**：
- **配方丢 75 条**：`create:*` 那 51 条因 26.3 schema 全变、create jar 内无样本可对照，**整类丢弃**；
  另有 `liquid_burning` 14 条、IE·Mek 3 条、tag 引不到的 7 条。**保留** rolling 15 + charging 23 + 原版合成 28
- **特斯拉线圈不能给物品充能**（垫片没有 `EnergyStorage.ITEM`）
- **客户端渲染全删 ⇒ 电线不画出来**（机器仍有静态模型）
- 液体子系统整体删、Flywheel 视觉删、环境音删
- 网络层空壳（护目镜实时数值不刷新）
- **动态结构 `MovementBehaviour` 删**（连接器、PEI、蓄电池不随结构移动）
- 拆机器时槽内物品不掉落、SequencedAssembly 支持删、配置写死默认
- JEI / REI / EMI / CC / Ponder 集成删

### 4.10 `JadeAddons`（`docs/port-smallmods.md`）
**一个「WORLD_OK ≠ 功能生效」的典型**：Jade 会**静默拒收**放在 `snownee.jade.` 包下的第三方插件
（`Built-in plugin registered by non-Jade mod`），**世界照样进得去**，只在日志留一行 ERROR，插件不生效。
已把包名迁到 `jadeaddons`。**验证要看日志有没有 `Start loading plugin from ...`**。

### 4.8 世界类型
- 每次进世界会弹「不支持使用实验性设置的世界」确认框 —— **点一下即可，这是正常行为**

---

## 四点五、⚠ 已知问题（未修 / 修中）

| 问题 | 严重度 | 状态 |
|---|---|---|
~~铭牌/手柄/接收器 + 邻居更新 = 服务器崩溃~~ | ~~高~~ | ✅ **已修（R395/R397/R398）** |
~~`ItemContainerContents.allItemsCopyStream()` 缺失~~ | ~~中~~ | ✅ **已修（R395，改用 `itemCopies()`）** |
~~`RenderTypes.glint` / `InterpolationHandler` / `PonderRenderTypes` 三族渲染地雷~~ | ~~高~~ | ✅ **已修（R400）** |
~~ponder 的 GLSL 编译失败（15 条 `moj_import`）~~ | ~~中~~ | ✅ **已修（R401，15 → 0）** |
~~`MutableQuadView.diffuseShade()` 已删（看一眼方块就崩客户端）~~ | ~~高~~ | ✅ **已修（R402，等价 `shadeDirectionOverride()==null`）** |
~~`ClockManager` 家族（时钟方块每 tick 崩）~~ | ~~高~~ | ✅ **已修（R402）** |
~~`Render pass color attachment count` 不匹配（**大部分 Create 方块一进画面就崩**）~~ | ~~极高~~ | ✅ **已修（R403）** |
~~`simulated:laser_pointer` 放下就崩服务器（垫片接口没人实现）~~ | ~~高~~ | ✅ **已修（R405，A/B 实测）** |
~~物品 tooltip 崩溃（悬停 Create 物品/翻创造背包就崩，JEI 报「获取原料提示框时崩溃」）~~ | ~~高~~ | ✅ **已修（R406，全物品探针 4→0）** |
~~397 个物品名显示原始 key（`item.simulated.*` 之类）~~ | ~~中~~ | ✅ **已修（R406，补 397 条 `item.*`）** |
~~按住右键编辑转速控制器 → 客户端崩（`LocalPlayer.swinging` 字段已删）~~ | ~~高~~ | ✅ **已修（R407，探针 A/B：值编辑屏正常打开）** |
~~打开 Create 值编辑屏 → `NoClassDefFoundError: org/lwjgl/glfw/GLFW`（26.3 已换 SDL）~~ | ~~高~~ | ✅ **已修（R407，GLFW 家族收口，4 处调用改走 SDL）** |
~~物理组装后 sublevel 方块隐形（碰撞还在）~~ | ~~高~~ | ✅ **已修（R415）：组装出的方块现在可见（有贴图/光照）**——支持 ≤64 格的小结构；**更大的结构（分块渲染）还没画**，第二步 |
~~机械手（deployer）打死生物 → 服务器崩（`Inventory.placeItemBackInInventory` 1 参已删）~~ | ~~高~~ | ✅ **已修（R408，A/B 实测）** |
~~按住小键盘+打开「思索」→ 客户端崩（`executeSolid` / `renderAllFeatures` 两处 26.3 API）~~ | ~~高~~ | ✅ **已修（R409 不崩 + R421 场景几何恢复）**：思索界面能正常打开，且 **3D 演示动画完整显示**（白平台+齿轮/装置，与参照图一致） |
~~航空学物理不生效（Sable 物理后端只登记了 no-op 实现）~~ | ~~极高~~ | ✅ **已修（R408 启用 Rapier；R409 组装后 sublevel 创建实测 PASS：server/client 各 1、pipeline=Rapier）**<br>⚠ 重力/运动（真的浮/落/推动）仍在验证（task-26） |
~~物理组装器只是普通方块、无「按住并拖拽以组装」~~ | ~~高~~ | ⚠ **大部分修复**：R408 恢复交互/提示/进度条；R409 组装后确实创建 sublevel；**R414 修好物理唤醒**（组装后 ~1 s 内自己下落/可推动）；**仍缺：sublevel 方块渲染（R414 后看见的是空气）——task-28 在重写** | |
~~按 E 打开创造物品栏，看不到可用的翻页键（只有两枚极小的 10×12 按钮，且不是参照图样式）~~ | ~~中~~ | ✅ **已修（R412：顶部 `< 1/3 >` 大箭头 + 居中页码，点击/PageUp/PageDown 可翻页）**；末页右箭头置灰待下一个小件 |
~~物品栏里 Create 系 mod 的标签页名是 `[NEEDS_TRANSLATION]` 占位符~~ | ~~中~~ | ✅ **已修（R408b，现为「机械动力：工艺与附加」）** |
~~缺「机械动力：内饰」标签页（注册了但内容为空被隐藏）~~ | ~~低~~ | ✅ **已修（R408b：24 个标签页、内饰 53 件物品，实测通过）** |
| ✅ ~~Create 的 Ponder 教学动画画不出来~~（R421 已修：26.3 palette 键名 `id/properties`，178 个 ponder nbt 批量改名后场景几何可见） |
| **⚠（历史记录）Create 的 Ponder 教学动画仍画不出来** —— 管线编译已修好、PonderUI 能打开、场景渲染流程能起跑，但几何体提交进 26.3 相位那一步没做：`PreparedFrame.executeSolid()` 在 26.3 需要 `RenderPass` 参数，而 `SceneRenderer.prepare()` 拿不到它（在 `GuiRenderer`/`CommandEncoder` 层）⇒ **这是 26.3 相位模型的架构级移植，不是改名** | **中（可见功能损失）** | **未做** |
| `createaddition` 的 `vi_vn.json`（越南语）第 39 行有非法控制字符 ⇒ MC 跳过它并打警告（**中文不受影响**） | 极低 | 不修 |

### R403 的关键修复：为什么「看一眼 Create 方块就崩」被根治了

**根因**：`PonderRenderPipelines` 里 **8 条 `ponder:pipeline/entity_block_*` 不透明管线声明了 0 个 color target**，
而 26.3 的主世界 pass 恒有 1 个 color attachment ⇒ `FrontendRenderPass.setPipeline:103` 直接拒绝。

这 8 条 RenderType 被 `EntityBlockRenderType → PonderRenderTypes → SuperByteBufferTask` 这条
「把方块模型当实体画」的路径使用 ⇒ **凡是用 `SuperByteBuffer` 自绘模型的 Create 方块，一进画面就崩**。

**vanilla 权威（判断依据）**：`pipeline/solid_block` = `withColorTargetState(ColorTargetState.DEFAULT)` 恰好 1 个；
多目标只出现在 OIT（2 个 target ⇔ 2 个 attachment）；0 target 只出现在 0 attachment 的 `INTEGRATE_DEPTH`。
⇒ **不变量：pipeline 的 target 数照「绑到哪个 pass」写。**

**修法**：`<clinit>` 里 8 处各插 2 条指令（`getstatic ColorTargetState.DEFAULT` + `withColorTargetState`），
**只有 1 个 class 变**（7984 → 8099 B），其余 14,335 entry 逐字节不动。

**验收**：8 个 Create 方块摆眼前全不崩（齿轮 / 流体罐 / 邮筒 / 数码管 / 布谷鸟钟 / 创意电机 / 传动轴 / 变速箱），
且探针打出 `DRAWN rt='ponder:entity_block_*' pipelineTargets=1 passAttachments=1` ⇒ **证明真的被画出来了**，不只是不崩。

### 已修的 4 处同族 NPE（同一根因，全部有 A/B 实证）

**根因**：26.3 把 `neighborChanged` 第 5 参从 `BlockPos` 换成 `@Nullable Orientation`（普通世界恒 `null`），
端口只改了签名、方法体还在读它 ⇒ `NullPointerException` ⇒ `ReportedException: Exception while updating neighbours` ⇒ **服务器线程崩**。

| 类 | 行 | 修法要点 |
|---|---|---|
`NameplateBlock` | 225 | 补「自身升 controller」分支 + 所属 controller 刷新，再判 hasSupport |
`HandleBlock` | 108 | 删掉「邻居是不是自己正下方」那道门（**门只是短路，等价物就是 `canSurvive`**）|
`DirectionalLinkedReceiverBlock` | 108 | 同上 |
`ModulatingLinkedReceiverBlock` | 112 | 同上 |

**验证方式**（每次全新存档副本）：旧 jar **必崩**且栈精确到行号；新 jar `WORLD_OK` 且 0 NPE；
**拆除语义保留**（有支撑的活、孤立的被 `canSurvive` 拆、拆掉支撑后变空气）。
全 jar 扫描 14 个含 `neighborChanged` 的类，修后含 `Object.equals` 的为 **0** ⇒ 无残留。

> **`ValueInput.contains` 那条警报已撤回**：`fabric-api` 的 `FabricValueInput` 本身就提供 `default boolean contains(String)`，
> 运行期被 `ValueInputMixin` 织进 `ValueInput`。实测放 `simulated:spring` 再读档，`NoSuchMethodError` 计数 0。

## 五、没装的东西（~39 个）与原因

> 精确清单用 `python tools/diff_pack.py` 生成（46/110 已覆盖）

| 类别 | 数量 | 状态与原因 |
|---|---|---|
**Create 附属** | ~21 | **4 个已成**（interiors / create-framed / escalated / **createaddition**）。<br>`railways-navigator` 硬依赖 **DragonLib**（无 26.3 构建，需 2 轮）。<br>`copycats` 卡在**客户端模型系统**（降级=失去意义）。<br>`EI`/`DP` 成对 400+ 错（还要 1.5~2 轮）。<br>`create-connected`/`power-loader`/`mechanical-extruder`/`central-kitchen` **无 Fabric 构建** |
**Farmer's Delight 系** | 4 | `culturaldelights` 卡在 **26.3 把「树」整套重做**；`mynethersdelight` 同形态更大；<br>`minersdelight`/`abnormals_delight` 只有 NeoForge 版 |
**库** | ~10 | `blueprint`/`yungsapi`/`paxi`/`dragonlib`/`lodestone`/`mysterious_mountain_lib`/`playeranimator`/`passivemobspawn`/`modernfix` 等，多为依赖 |
**FTB 任务链** | 4 | `ftblibrary`/`ftbquests`/`ftbteams`/`ftbqopt`，一整块功能 |
**Sophisticated 系列** | 3 | 只有 NeoForge 26.3 版 |
**结构** | ~4 | `awakened_islands`、`natures_spirit`（≈8~12 人日）、`MoogsSoaringStructures` id 对不上 |
**Sable 兼容** | ~4 | `sablejade`/`waystonessable`/`sable_createaddition_compat`/`portable_engine_liquid_fuel` |
**其他** | ~3 | `climbable_ropes`(99 错)/`constraintfix`(58 错)/`CreateDragonsPlus` |
**小工具已上** | — | `passivemobspawn` / `sablejade` / `JadeAddons` / `constraintfix` ✅ |

---

## 六、关键技术事实（备查）

| 事实 | 说明 |
|---|---|
**26.3 完全不混淆** | 无 remap 配置；1.21.x 的 Fabric jar 是 intermediary，**必须先 remap** 否则首个类加载就炸 |
**`ProcessingRecipe` 框架被删** | 26.3 改用 `CreateRecipe<T>` 家族；已备公共垫片 `g10/shim/proc-recipe-compat.jar` |
**registrate 垫片是空实现** | `register()` 与一批 builder 方法都不做事 ⇒ 必须显式调用 + `flush()` |
**方块/物品 id 必须前置** | `Properties` 在 `new Block()/new Item()` **之前**带 id |
**物品模型入口变了** | `assets/<ns>/items/<id>.json`（旧 `models/item/` 不再被当入口）|
**`Ingredient` 不允许为空** | `Ingredient.of()` 抛异常，用 `Items.BARRIER` 哨兵 |
**验收必须进世界** | 编译过 / 标题过都 ≠ 能跑（item components 在注册表加载期才绑定）|

---

## 七、工具索引

```
tools/diff_pack.py              算剩余 mod 清单（逐 jar 读 mod id）
tools/lang_audit.py             汉化审计（en/zh 独立解析，坏文件会单独报）
tools/fix_broken_lang.py        修损坏的 zh_cn.json（行注释 / BOM）
tools/build_preset_r368.py      重建浮岛世界类型 jar
tools/probe_fabric_builds.py    查某 mod 最新的 Fabric 构建版本
tools/launch26/launch.py        26.3 启动器（--watch-title / --timeout）
```

---

## 八、R509 增量（本阶段新增内容与降级，给用户看的摘要）

> 交付件当前 **93 jar / 174 mods**；下方只列「本轮之后新增或变化」的部分，旧内容见上文。

### 新增可玩内容

| 内容 | 状态 | 已知降级 |
|---|---|---|
**任务系统 sky262-quests** | J 键任务书；22 章 / 543 任务；进度存档；提交/领取/锁定/奖励；命令 /sky262quests | 专用服务器进度同步、跨章节依赖连线待做 |
**jetpack（喷气背包）** | 右键推力约 60 tick、约 3 格/次 | 无燃料、无悬停/下潜、无装备槽 |
**mechanical-extruder（挤出机）** | 2 方块；动力接入 + 配方匹配 + 产出物品（水+沙→砂岩实测通过） | 无 BER 动画/思索演示；配方为自建数据包加载器；无流体槽 |
**power-loader（电力装载机）** | 4 方块；按转速强制加载周围区块 | 无 BER；强制加载非引用计数 |
**ore-excavation（矿石挖掘）** | 6 方块 + 11 物品 | 世界生成/多方块/Atlas 界面未做 |
**central-kitchen（中央厨房）** | 机械臂与 Farmer's Delight 锅/砧板交互点已注册 | 无 mixin、无思索、无缺失 mod 联动 |
**sliceanddice（切割砧）** | 2 方块 + 4 物品；551 条切割配方数据已加载 | 切割产物/刀臂动画、洒水器行为未做 |
**createdeco（装饰方块）** | 累积 196 个方块 + 创造栏标签页 | door/container/lamp 等复杂族未做 |
**design-n-decor** | 累积 357 个方块 + 创造栏标签页 | 纯装饰近似：齿轮/飞轮/风扇不会转、无方块实体 |
**diesel-generators** | 累积 43 个方块（装饰/水泥/管道）+ 创造栏标签页 | 机器与 6 种流体方块押后 |
**yungsapi / Paxi** | 已放回交付件（结构生成实测 0 崩溃；Paxi 数据包注入生效） | — |

### 本轮修复的关键问题（用户能感知的）
- 创造模式物品栏崩溃、物品名未汉化；
- 长按交互方块手部动画/进度条反复重置；
- 强力胶/蜂蜜胶/融合胶、示意图、柱塞等物品功能；
- 打印器（结构打印器）：界面、打印 11 方块、方块贴图、容器部件渲染；
- 生物群系/结构生成崩溃（yungsapi 源码移植）。

### 验证口径（本工程纪律）
1. 任何 jar 必须「标题画面 + 进入世界」双实测才允许合并；
2. 装饰/累积类 mod 每次构建后断言「旧 ids 是新 ids 的子集」、代码注册 key 必须存在于 blockstates；
3. 手写 jar 必须包含目录条目，且方块/物品 Properties 必须先 setId；
4. 只带「与已注册内容一致」的 data（否则会拖垮原版 tag 导致世界进不去）。

---

## 九、R560 收口（当前交付件 97 jar / 179 mod 项）

### 装饰线定稿
| 包 | 方块数 | 备注 |
|---|---|---|
| **createdeco** | **389/389** | 含门/活板门（两套 Half 映射）、placard/wedge/lamp/container 等；`Missing model=0` |
| **Design-n-Decor** | **774/846** | 全可解析族完成；剩 velvet 32（缺 Create 座椅贴图，永久跳过）+ 杂项 40（casing/part/slope 等不再尝试） |

共同验收基线：`Missing model for variant=0`、`Exception loading blockstate=0`、ids 只增不减、variant model 断言 problems=0、variant fix 幂等、lang 审计 0 坏文件。

### 本轮新增/修复（用户可感知）
- **食物**：Cultural Delights（26 方块/78 物品）、My Nether's Delight（47 方块/101 物品，powdery 木组已恢复）；
- **任务书**：按钮/锁定提示/物品名全中文，图标不再出现「空气」；fallback 日志从 11286 条降到 2 条；
- **语言大坑修根**：26.3 一次解析所有 mod lang，任一坏 JSON 会导致全部 mod 语言失效；已修 extruder zh_cn 缺逗号、createaddition vi_vn 控制字符，物品名/tooltip 恢复正常；
- **sliceanddice**：切割砧真实行为（551 条配方，放入蛋糕产出 4 份切片）；
- **aeroworks**：控制台面板 / 摇杆输入行为可用；
- **createfix**：修复 Create `RuntimeDataGenerator` 在 26.3 下的 `CuttingRecipe→Holder` 崩溃（modded 木组跳过运行时切割配方生成，原版不受影响）；
- **验证基础设施**：游戏内 MCP（截图/状态/放置/交互）+ 单实例启动锁，避免并发抢 GPU/端口。

### 综合验收（97 jar，MCP 实测）
- Create 基础方块（mechanical_press/cogwheel/shaft）放置读回 3/3；
- physics_assembler 右键交互正常、拉杆渲染器注册；
- throttle_lever 长按交互 60 tick 无崩溃；
- 任务书中文、无语言加载失败；0 registry error、0 crash。

### natures_spirit（生物群系）—— 本轮打通
- 编译 **0 错误**；数据层完成 26.3 schema 迁移（biome 必填 `features`(11 step)/`carvers`、effects 颜色字符串、旧 `{"Name","Properties"}` → `{"id","properties"}`、`configured_feature`→`feature` 目录、noise `firstOctave`→`base_octave`、placement `random_offset`→`offset`）；
- **153 个 NS 生物群系可加载/可生成/可定位**（`/locate biome` 实测 3/3 命中，传送后地表正常）；
- **地形特征已恢复**：tree/ore 两类（107 feature + 133 placed_feature）在 `alpine_clearings`/`redwood_forest` 试点生效，实测红杉林成片生成；树形用 26.3 原版 placer（NS 自定义 placer 待反射注册后还原）。
- **掉落表 720 + 配方 826 已恢复**：实测 `/loot give` 掉出白杨木台阶、`/recipe give` 解锁配方。
- 暂缓：全量 153 群系的 features 填充（当前仅 2 个试点）、advancement（513 条待 26.3 重写）、NS 自定义 placer 的反射注册还原树形。