# 方块进画面全量扫描（26.3 block-render sweep）

> 目的：上一轮只验了 **8 个 Create 方块**（`Render pass color attachment count` 族修完后的验收），
> 但那类崩溃**只在方块真进画面时触发**，`TITLE_SCREEN_OK` / `WORLD_OK` 回归永远看不到。
> 本轮把 `mods-stable` 里**所有有 blockstate 的方块**逐个放到 spectator 机位正前方，
> 记录「崩 / 不崩」，并把崩溃分到 A/B/C/D 四组（另加 G = GUI 物品图集、T = 非渲染的服务端 tick）。

**只读诊断**：本轮没有改任何 jar；`create-fly` 用的是交付件 `B6B1FD18…8888`（19,639,253 B）。

> **状态（后补）**：本文件是**扫描当时的证据底稿**。其中 F1（`blocksMotion`）与 F2（`submitItem`）
> 已被后续一轮修好并 A/B 通过 —— 成品 `9B5B027C…69AC`（19,639,156 B，基线 `B6B1FD18`），
> 只 5 个 entry 变，修法记在 `docs\fix-submititem-blocksmotion.md`。**F3（NeoForge 强转）仍未修。**

## 1. 扫了什么、扫了多少

候选 = `assets/<ns>/blockstates/<name>.json` 的文件名（有 blockstate 才需要客户端画得出来）。

| namespace | mod | 候选数 | 已扫 | OK | MISMATCH | CRASH | PLACE_FAIL |
|---|---|---:|---:|---:|---:|---:|---:|
| `create` | create-fly (Create 本体) | 643 | 643 | 638 | 0 | 5 | 0 |
| `createaddition` | createaddition | 23 | 23 | 23 | 0 | 0 | 0 |
| `simulated` | sable/aeronautics (namespace `simulated`) | 95 | 95 | 94 | 0 | 1 | 0 |
| `aeronautics` | aeronautics | 43 | 43 | 43 | 0 | 0 | 0 |
| `escalated` | escalated | 20 | 20 | 19 | 0 | 1 | 0 |
| `createframed` | createframed | 265 | 265 | 265 | 0 | 0 | 0 |
| `interiors` | interiors | 53 | 53 | 53 | 0 | 0 | 0 |
| `farmersdelight` | FarmersDelight | 135 | 135 | 135 | 0 | 0 | 0 |
| `waystones` | waystones | 31 | 31 | 31 | 0 | 0 | 0 |
| `ends_delight` | ends_delight | 8 | 8 | 8 | 0 | 0 | 0 |
| `corndelight` | corndelight | 6 | 6 | 6 | 0 | 0 | 0 |
| **合计** | | **1322** | **1322** | **1315** | **0** | **7** | **0** |

> `sable` 本体（`sable-fabric-26.3.jar`）**没有 blockstate**——它是物理引擎，方块在
> `aeronautics-fabric` 里的 `simulated` namespace（95 个），所以那一栏就是 sable 的方块。

## 2. 分组统计

| 组 | 条数 | 一句话 |
|---|---:|---|
| **A** | **0** | `IllegalStateException` / Render pass color attachment count 族 |
| **B** | **4** | `NoSuchMethodError` / `NoSuchFieldError` / `NoClassDefFoundError` 族 |
| **C** | **0** | 其他异常（栈摘要） |
| **D** | **0** | 无明确异常（客户端死亡 / 日志停摆） |
| **G** | **2** | `GuiItemAtlas` 物品图标图集崩（**与放哪个方块无关**，就是用户报的「按 E 翻物品栏到 30 多页必崩」） |
| **T** | **1** | **非渲染路径**：放下就崩服务器（方块实体 tick），客户端跟着退出 |
| P（放置失败，非渲染结论） | 0 | setblock 拒绝该 id |

## 组 B —— `NoSuchMethodError` / `NoSuchFieldError` / `NoClassDefFoundError` 族

| mod | 方块 | 结果 | 崩在哪 / 错误摘要 | 该方块的 render type |
|---|---|---|---|---|
| `create` | `create:andesite_ladder` | CRASH | java.lang.NoSuchMethodError: 'boolean net.minecraft.world.level.block.state.BlockState.blocksMotion()' | — |
| `create` | `create:brass_ladder` | CRASH | java.lang.NoSuchMethodError: 'boolean net.minecraft.world.level.block.state.BlockState.blocksMotion()' | — |
| `create` | `create:copper_ladder` | CRASH | java.lang.NoSuchMethodError: 'boolean net.minecraft.world.level.block.state.BlockState.blocksMotion()' | — |
| `create` | `create:lectern_controller` | CRASH | net.minecraft.ReportedException: Rendering Block Entity<br>**Caused by** `java.lang.NoSuchMethodError: 'void net.minecraft.client.renderer.SubmitNodeCollector.submitItem(com.mojang.blaze3d.vertex.PoseStack, net.minecraft.world.item.ItemDisplayContext, int, int, int, int[], java.util.List, net.` | — |

**建议修法（B）**：按报出的符号改名或补桥（缺什么补什么，不要按方法名一刀切）

## 组 G —— `GuiItemAtlas` 物品图标图集崩（**与放哪个方块无关**，就是用户报的「按 E 翻物品栏到 30 多页必崩」）

| mod | 方块 | 结果 | 崩在哪 / 错误摘要 | 该方块的 render type |
|---|---|---|---|---|
| `create` | `create:cyan_seat` | CRASH | java.lang.NoSuchMethodError: 'void net.minecraft.client.renderer.SubmitNodeCollector.submitItem(com.mojang.blaze3d.vertex.PoseStack, net.minecraft.world.item.ItemDisplayContext, int, int, int, int[], java.util.List, net. | — |
| `escalated` | `escalated:metal_narrow_walkway` | CRASH | java.lang.NoSuchMethodError: 'void net.minecraft.client.renderer.SubmitNodeCollector.submitItem(com.mojang.blaze3d.vertex.PoseStack, net.minecraft.world.item.ItemDisplayContext, int, int, int, int[], java.util.List, net. | — |

**建议修法（G）**：修 `submitItem`（见下文），这个组会一起消失

## 组 T —— **非渲染路径**：放下就崩服务器（方块实体 tick），客户端跟着退出

| mod | 方块 | 结果 | 崩在哪 / 错误摘要 | 该方块的 render type |
|---|---|---|---|---|
| `simulated` | `simulated:laser_pointer` | CRASH | net.minecraft.ReportedException: Ticking block entity<br>**Caused by** `java.lang.ClassCastException: class net.minecraft.server.level.ServerLevel cannot be cast to class net.neoforged.neoforge.common.extensions.ILevelReaderExtension (net.minecraft.server.level.ServerLevel and net.neoforged.` | — |

**建议修法（T）**：删掉 NeoForge 强转（见下文 F3）；它和渲染无关，但同样「放下就崩」

## 3. 每个族的「崩在哪 / 怎么修」（可直接派修）

### F1 · `BlockState.blocksMotion()` —— 组 B，梯子族

| 项 | 内容 |
|---|---|
| 崩在 | `com.zurrtum.create.content.decoration.MetalLadderBlock.skipRendering(MetalLadderBlock.java:48)` |
| 完整路径 | `Chunk build failed`（sodium `ChunkBuilder$WorkerRunnable`）→ `moreculling CullingUtils.shouldDrawSideCulling` → `BlockBehaviour$BlockStateBase.skipRendering` → 本方法 → `ReportedException: Render Frame` ⇒ **客户端退出** |
| 触发方块 | `create:andesite_ladder` / `create:brass_ladder` / `create:copper_ladder`（三个都实测崩） |
| 26.3 真身 | `BlockBehaviour$BlockStateBase.isSolid()`；`javap -c` 证实它 `return this.legacySolid`，与旧 `blocksMotion()` **逐指令同义**（`BlockState extends BlockBehaviour$BlockStateBase`，`invokevirtual BlockState.isSolid()` 能解析到继承方法） |
| 同符号另外 2 处（本轮未触发，但是定时炸弹） | `BlockHelper.destroyBlockAs(...)`（打碎方块掉落）、`FluidFillingBehaviour.canBeReplacedByFluid(...)`（流体填充） |
| 修法 | 3 个 class 各 1 处：`invokevirtual BlockState.blocksMotion:()Z` → `BlockState.isSolid:()Z`，**栈形不变、只改动这 3 个 class** |
| 为什么回归没抓到 | 它由**区块网格构建**触发，方块不进画面就永远不执行 |
| 复现条件（实测，与预期不同） | 本轮是 **3 个梯子各自孤零零一块**（放在草地上方、四周空气）就 3/3 复现的 —— **不需要摆两块相邻梯子**。栈顶是 `moreculling CullingUtils.shouldDrawSideCulling`，看起来它并不走「邻居是空气/满方块就短路」那条路。若要写更严格的 A/B，照旧用两块相邻梯子更保险，但**别因为「单块不崩」就判已修** |

### F2 · `SubmitNodeCollector.submitItem` 第 7 参 `List` → `ItemQuads` —— 组 B（方块侧）+ 组 G（GUI 侧）

| 项 | 内容 |
|---|---|
| 崩在 | `com.zurrtum.create.client.infrastructure.model.LinkedControllerModel.renderQuads(LinkedControllerModel.java:325)` |
| 路径①（方块） | `create:lectern_controller` → `LecternControllerRenderer.submit(:73)` → `renderInLectern(:232)` → `render(:260)` → `renderQuads(:325)` → `ReportedException: Rendering Block Entity` |
| 路径②（GUI，**用户报的那个**） | `GuiItemAtlas.drawToSlot(:132)` ← `GuiRenderer.lambda$prepareItemElements` ← `ItemStackRenderState.submit` ← `LinkedControllerModel.submit(:220)` ⇒ 打开背包/翻 JEI 物品列表翻到该物品就崩 |
| 旧签名（Create 里） | `submitItem(PoseStack, ItemDisplayContext, int, int, int, int[], java.util.List, FoilType)V` |
| 26.3 真身 | `OrderedSubmitNodeCollector.submitItem(PoseStack, ItemDisplayContext, int, int, int, int[], **ItemQuads**, FoilType)V` |
| 现成的桥 | `public static ItemQuads ItemQuads.split(java.util.List<BakedQuad>)`；`ItemQuads` 是 record(all, solid, translucent) ⇒ `split` 正是旧 `submitItem` 内部的前置分组，**逐义替换** |
| 全量面（常量池扫 71 个 jar） | 只有 Create 的 **2 个类**引用旧签名：`LinkedControllerModel`、`ItemModelRenderHelper$CustomLayer.submit(...)`（flywheel 物品渲染）。iris / moreculling 里那两处是它们自己的同名方法，与 MC 无关 |
| 修法 | 每个调用点插 **1 条** `invokestatic ItemQuads.split:(Ljava/util/List;)L.../ItemQuads;`，再把 `invokeinterface submitItem` 的描述符第 7 参换成 `ItemQuads`。⚠ **位置不能贴着调用指令插**：`submitItem` 有 **8 个参数**，第 8 参 `FoilType`（`getstatic ...FoilType.NONE`）是在 `List` **之后**入栈的 ⇒ `split` 必须插在**那条 `getstatic` 之前**；插在 `invokeinterface` 正前方会 `VerifyError: Bad type on operand stack`。**改多参调用前先数清入参顺序** |
| A/B 口径 | 旧件：世界里放 `create:lectern_controller` 必崩 / 打开背包翻到 `create:linked_controller` 必崩；新件两者都不崩 |
| 为什么它随机炸 | `GuiItemAtlas` 会在任意帧重建，所以这一族**不是**只在你翻页时才撞上——本轮扫描里它就随机废掉了 2 个批次 |

### F3 · `SimLevelUtil` 里的 NeoForge 强转 —— 组 T，`simulated:laser_pointer`

| 项 | 内容 |
|---|---|
| 崩在 | `dev.simulated_team.simulated.util.SimLevelUtil.isAreaActuallyLoaded(SimLevelUtil.java:16)` |
| 异常 | `ClassCastException: class net.minecraft.server.level.ServerLevel cannot be cast to class net.neoforged.neoforge.common.extensions.ILevelReaderExtension` |
| 路径 | `MinecraftServer.tickChildren` → `ServerLevel.tick` → `Level.tickBlockEntities` → `BoundTickingBlockEntity.tick` → `LaserPointerBlockEntity.tick(:70)` → 本方法 ⇒ `ReportedException: Ticking block entity` ⇒ 服务器停 ⇒ 客户端跟着退 |
| 触发方块 | `simulated:laser_pointer`（sable/aeronautics 的方块在 `simulated` namespace 下） |
| 根因 | 端口保留了 NeoForge 的 `((ILevelReaderExtension) level).isAreaLoaded(pos, r)`。这个接口类是 **aeronautics jar 自带的垫片**（`net/neoforged/neoforge/common/extensions/ILevelReaderExtension`），它的 `default isAreaLoaded(BlockPos,int)` 方法体**就是 `return true`** —— 但**没有任何类实现这个接口** ⇒ Fabric 上 `ServerLevel` 永远转不过去 |
| 面有多大 | 常量池扫 71 个 jar：引用该接口的只有 **1 个类**（`SimLevelUtil`）⇒ 这是整套 NeoForge 垫片里唯一漏掉「谁来实现」的一处 |
| 建议修法（首选，1 个 class + 1 行配置） | 加 `@Mixin(Level.class) public abstract class LevelILevelReaderExtensionMixin implements ILevelReaderExtension {}`：该接口**唯一的方法是 default**，不用写任何实现体，`checkcast` 立即可过，`isAreaLoaded` 返回 true（正是垫片作者写的语义）。挂到 aeronautics 的 `simulated.mixins.json` 的 `mixins` 数组 |
| 备选（纯字节码，不推荐） | 把 `SimLevelUtil` 里 `13..26` 的 5 条指令（`aload_0 / checkcast / aload_1 / iload_2 / invokeinterface isAreaLoaded / ifne`）换成一条 `goto 29` —— 等价于「恒 true」，且栈是平衡的（该段入口/出口栈都为空） |
| 顺带 | 垫片体是 `return true`，会让 tick 路径相信未加载的区块；若之后冒出「未加载区块被读」的 NPE，把垫片体改成 `((LevelReader) this).hasChunksAt(pos.offset(-r,-r,-r), pos.offset(r,r,r))`（26.3 **没有** `isAreaLoaded`，最接近的原语是 `LevelReader.hasChunksAt(BlockPos,BlockPos)`） |
| 更大的面（建议单独派一轮） | `aeronautics` **36** 个 class、`sable` **21** 个 class 引用 `net/neoforged`；多数是 ForgeConfigAPIPort / Registrate 的真垫片，但 `SimLevelUtil` 证明「**垫片声明了 ≠ 有人实现**」，值得逐条判一遍 |

### F4 · 管线表：组 A 的静态面（上一轮修完之后的复查）

`phase=dump` 把 26.3 运行期**全部**注册管线打了一遍：`targets != 1` 的共 **34** 条（`targets=2` 的 31 条全是原版 OIT —— 2 target 正对 2 attachment；`targets=0` 的 3 条全是 `integrate_depth` / `blit_depth` / `oit_water_mask` 这种 0 attachment 的 depth/blit 管线）。**其中 mod 命名空间的：0 条。**

⇒ 上一轮那 8 条 `ponder:pipeline/entity_block_*` 修完之后，「管线声明 0 个 color target」这个根因在管线表层面**已经归零**；本轮组 A 的条数也印证了这一点（见上表）。


## 4. render type 视角（真正决定崩不崩的东西）

没有任何 render type 报 pipeline/target 不匹配。

扫描期间被真正画出来的 render type（出现该 RT 的方块数，前 25 名）：

| render type | 方块数 |
|---|---:|
| `entity_cutout` | 1315 |
| `entity_shadow` | 1204 |
| `item_cutout` | 946 |
| `entity_cutout_cull` | 804 |
| `eyes` | 211 |
| `solid_moving_block` | 149 |
| `ponder:entity_block_solid` | 142 |
| `ponder:entity_block_cutout` | 51 |
| `entity_translucent_cull_item_target` | 30 |
| `item_cutout_glint` | 25 |
| `ponder:entity_block_translucent` | 18 |
| `text` | 18 |
| `entity_solid` | 8 |
| `item_translucent` | 8 |
| `banner_pattern` | 4 |
| `entity_cutout_z_offset` | 2 |
| `entity_translucent` | 2 |
| `text_polygon_offset` | 1 |

## 5. 方法与置信度（这份清单能信到什么程度）

**候选穷举**：`mods-stable` 全部 71 个 jar 里 **1322** 个 `assets/<ns>/blockstates/*.json`（有 blockstate 才需要客户端画得出来），11 个 namespace。**不是抽样。**

**每次全新存档副本**：模板冻结在 `g21/template/lm-final`，每轮 `rmtree` + `copytree` 再开，避免「同一存档被试过一次变实验性 ⇒ 伪装成超时」。

**一次只放一个方块**：spectator 机位固定、方块放在镜头正前方 5 格，每块用 `WIN <i> BEGIN` / `WIN <i> END` 两行日志包围 —— **BEGIN 没有配对的 END 就说明客户端死在这个方块上**，这是能按方块归因的关键。每块 12 tick（约 0.6 s，其中 8 tick 可见）。

**两条渲染路径都被覆盖**：

1. sodium 区块网格构建（`ChunkBuilder`）—— 梯子族死在 `Chunk build failed`，这证明**放出来的方块确实被网格化了**，不存在「放了但没画」；
2. `PreparedRenderType.draw`（Create 把方块模型当实体画的那条路）—— 探针逐窗口记录该方块真正画到的 render type。

**抑制模式**：主扫描用带 `PreparedRenderTypeMixin` 的探针。它在 `setPipeline` 之前比对「管线 target 数 vs pass attachment 数」，不一致就记一条 `MISMATCH` 并取消这次 draw，所以一条批次能扫 50 个方块而不是死在第一个。`MISMATCH` 的条数就是「生产环境会崩」的方块数。非这条路径的异常（`NoSuchMethodError` / `ClassCastException`）抑制不了，一定会崩，于是由 BEGIN/END 归因。

**已知置信度缺口（诚实披露）**：

- **43 个方块放上去立刻变 air**（自己 `canSurvive` 不过）：`aeronautics:levitite_blend`、`create:belt`、`create:factory_gauge`、`create:large_water_wheel`、`create:water_wheel_structure`、`createaddition:accumulator`、`createaddition:bioethanol`、`createaddition:connector_old`、`createaddition:copper_wire_casing`、`createaddition:liquid_blaze_burner`、`createaddition:seed_oil`、`createframed:framed_radon_lamp_black`、`createframed:framed_radon_lamp_blue`、`createframed:framed_radon_lamp_brown`、`createframed:framed_radon_lamp_cyan`、`createframed:framed_radon_lamp_gray`、`createframed:framed_radon_lamp_green`、`createframed:framed_radon_lamp_light_blue`、`createframed:framed_radon_lamp_light_gray`、`createframed:framed_radon_lamp_lime`、`createframed:framed_radon_lamp_magenta`、`createframed:framed_radon_lamp_orange`、`createframed:framed_radon_lamp_pink`、`createframed:framed_radon_lamp_purple`、`createframed:framed_radon_lamp_red`、`createframed:framed_radon_lamp_white`、`createframed:framed_radon_lamp_yellow`、`escalated:metal_narrow_escalator`、`escalated:metal_walkway_terminal`、`escalated:metal_wide_escalator_center`、`escalated:metal_wide_escalator_side`、`escalated:metal_wide_walkway_center`、`escalated:wooden_narrow_escalator`、`escalated:wooden_narrow_walkway`、`escalated:wooden_walkway_terminal`、`escalated:wooden_wide_escalator_center`、`escalated:wooden_wide_escalator_side`、`escalated:wooden_wide_walkway_center`、`escalated:wooden_wide_walkway_side`、`farmersdelight:tomatoes`、`farmersdelight:tomatoes_on_rope`、`simulated:merging_glue`、`simulated:spring`
  - 其中 **1 个仍被证明画过**（窗口里抓到了它们自己的 `ponder:entity_block_*`）：`create:belt`
  - 其余只有「**放置那一下不崩**」的弱结论 —— 它们要邻居/支撑（belt 要两个轴、large_water_wheel 要水+轴、`createframed:framed_radon_lamp_*` 要框、`escalated:*_walkway/escalator` 要相邻段）。**加「地下一块石头」复跑只救回 3 个**（`cart_assembler` / `gantry_carriage` / `controller_rail`），其余仍需逐方块搭台。
  - 按 mod 看覆盖缺口：`createframed` 16/265、`escalated` 12/20、`createaddition` 6/23、`create` 4/643、`farmersdelight` 2/135、`simulated` 2/95、`aeronautics` 1/43 —— 这些 mod 的结论**不完整**，其余 mod 是逐块扫全的。
- **一次只放一个方块** ⇒ 多方块联动（传送带、齿轮箱组、火车）不在覆盖范围；本轮只回答「这个方块**自己**进画面会不会崩」。
- render type 的归因可能带上「上一块残留 1~2 帧」（区块重网格是异步的），所以崩/不崩只按「窗口内有没有 MISMATCH」判，**不按 RT 集合判**。

## 6. 结论：哪些族还没修、先修哪个

| 组 | 条数 | 是不是「方块进画面」的锅 | 先修？ |
|---|---:|---|---|
| A（Render pass color attachment） | 0 | 是 | 本轮 **0 条**：上一轮 8 条 `entity_block_*` 修完后，管线表里已没有 mod 声明 0 个 color target 的管线 |
| B（NoSuch* / CCE） | 4 | 是 | F2 `submitItem` 与 F1 `blocksMotion` **已修**（`9B5B027C…69AC`）；本文件留作证据底稿 |
| G（GuiItemAtlas） | 2 | 否，是物品图标图集 | 跟 F2 一起消失 |
| T（方块实体 tick） | 1 | 否，是服务端 tick | F3，独立修 |
| C / D | 0 / 0 | — | 本轮为 0 |

**一句话**：`create` / `createaddition` / `simulated` / `aeronautics` / `escalated` 全部扫完，除了上面列出的几条之外，**没有一个方块是「放眼前就崩」的** —— `Render pass color attachment count` 那条生死线**真的过了**；剩下的是 3 个互不相干的独立小族：F1 梯子（渲染、组 B）、F2 物品渲染（组 B 方块侧 + 组 G 背包侧）、F3 NeoForge 强转（组 T，非渲染）。

> ⚠ 唯一需要打折的是 **`escalated`（12/20 落在「放上去就变 air」的弱集合里）** 与 **`createframed` 的 16 个 framed lamp**：它们不是「测过没事」，而是**没测到画面**。要收口这 28 个，得给它们搭相邻段/框，属于下一轮的事。

