# 修两族：`SubmitNodeCollector.submitItem` 第 7 参类型换了 / `BlockState.blocksMotion()` 已删

> **结论**：两族都修好了，A/B 双向成立（旧件三处全崩、新件全不崩），**成品只放在
> `work/run26/port/g22/`，没有 promote 进 `mods-stable`**（方块渲染穷举扫描正在跑）。
>
> | 族 | 触发 | 旧件 `B6B1FD18…8888` | 新件 `9B5B027C…69AC` |
> |---|---|---|---|
> | **1** `submitItem` 第 7 参 `List` → `ItemQuads` | `create:lectern_controller` 方块侧 | **`FAIL_CRASH`**（`NoSuchMethodError … submitItem(…,java.util.List,…)` @ `LinkedControllerModel.renderQuads:325` ← `renderInLectern:232` ← `LecternControllerRenderer.submit:73`） | **`WORLD_OK`**，0/0/0/0 |
> | **1** 同上 | **GUI 物品图集**（`GuiItemAtlas`） | **`FAIL_CRASH`**（同一 NoSuchMethodError @ `GuiItemAtlas.drawToSlot:132` ← `getOrUpdate:92` ← `GuiRenderer.lambda$prepareItemElements$0:285`） | **`WORLD_OK` ×3**（3 次独立全新存档/全新游戏目录） |
> | **2** `BlockState.blocksMotion()` 已删 | `create:andesite/brass/copper_ladder`（sodium 区块构建线程） | **`FAIL_CRASH`**（`Chunk build failed` + `MetalLadderBlock.skipRendering:48` ← `BlockStateBase.skipRendering:1052` ← `moreculling CullingUtils.shouldDrawSideCulling:46`；随后 `ReportedException: Render Frame`） | **`WORLD_OK`**，`blocksMotion` / `Chunk build failed` / `ReportedException` = **0/0/0** |
>
> **成品**：`work/run26/port/g22/out/create-fly-26.2-6.0.9-2-26.3-patched.jar`
> **SHA-256 `9B5B027C7E503EC3FF2CC28FD6D5BCD1D66D81F7469547D294C05E38BA1669AC`，19,639,156 B**
> （基于基线 `B6B1FD1840B845523B18F6DBCE938076187B001C0A046186470BFB45BDCB8888`，19,639,253 B）
>
> ⚠ **给主代理的一个更正**：任务简报里写的「调用前栈 = `[collector, pose, ctx, i, i, i, tints[], List]`」
> **少算了第 8 个参数**。真实栈顶是 `… List FoilType`，所以 `split` **不能**贴在 `invokeinterface`
> 前面（那样会把 `FoilType` 当 `List` 吃掉）——第一次这么打，客户端 **`VerifyError: Bad type on operand
> stack`**，启动就崩。正确位置是 **`getstatic FoilType` 之前**。详见 §1.4。

---

## 0. 交付件、基线与「没动 mods-stable」的证据

| 项 | 值 |
|---|---|
| 开工时 `mods-stable/create-fly…jar` | `B6B1FD1840B845523B18F6DBCE938076187B001C0A046186470BFB45BDCB8888` / **19,639,253 B** / mtime `2026-10-18 16:28:44` |
| 收工时同一个文件 | **逐字节不变**（同 SHA / 同大小 / 同 mtime 16:28:44）——扫描代理读到的还是同一份 |
| 成品（本轮唯一产物） | `work/run26/port/g22/out/create-fly-26.2-6.0.9-2-26.3-patched.jar` |
| 成品 SHA / 大小 | **`9B5B027C7E503EC3FF2CC28FD6D5BCD1D66D81F7469547D294C05E38BA1669AC` / 19,639,156 B**（−97 B） |
| 基线声明 | 成品 **只基于** `B6B1FD18…8888`（= 上一轮 `docs/fix-renderpass.md` §9 交付的那一件，也是 `mods-stable` 里的那一件） |
| entries | **14,336**，与原 jar **同名同序**；内容变化的 entry **5 个**（§3） |
| `mods-stable` jar 数 | 71 → **71**（没动） |

验收用的 mods 目录 `g22/mods-new` 里那一份是 **硬链接**，`launch.py` 再拷进各自 `game-*/mods`；
已核对 `game-new-gui3/mods/…jar` 的 SHA = **`9B5B027C…69AC`** ⇒ 跑的就是交付字节。

---

## 1. 族 1：`submitItem` 第 7 参 `java.util.List` → `ItemQuads`

### 1.1 26.3 真身（`javap -p -s`，`26.3.jar`）

```
public interface net.minecraft.client.renderer.OrderedSubmitNodeCollector {
  public abstract void submitItem(com.mojang.blaze3d.vertex.PoseStack, net.minecraft.world.item.ItemDisplayContext,
      int, int, int, int[], net.minecraft.client.resources.model.geometry.ItemQuads,
      net.minecraft.client.renderer.item.ItemStackRenderState$FoilType);
    descriptor: (Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/world/item/ItemDisplayContext;III[ILnet/minecraft/client/resources/model/geometry/ItemQuads;Lnet/minecraft/client/renderer/item/ItemStackRenderState$FoilType;)V
```

**不是改名，是类型换了**：整个接口只有这一条 `submitItem`，第 7 参是 `ItemQuads`，不是 `List`。
（旧件常量池里那条是 `…III[ILjava/util/List;L…FoilType;)V`，JVM 解析时找不到 ⇒ `NoSuchMethodError`。）

### 1.2 `ItemQuads` 与它的 `split`（26.3 自带的桥）

```
public final class net.minecraft.client.resources.model.geometry.ItemQuads extends java.util.Record {
  private final List<BakedQuad> all; solid; translucent;
  public static final ItemQuads EMPTY;
  public static ItemQuads split(java.util.List<BakedQuad>);
}
```

`split` 的 `javap -c` 逐段（`g22/_x/ItemQuads.txt`）：

```
 0: aload_0; invokeinterface List.isEmpty; ifeq 13
 9: getstatic ItemQuads.EMPTY; areturn                      // 空表直接 EMPTY
13..36: 两个 ArrayList（solid / translucent） + 遍历
58: BakedQuad.materialInfo()
61: BakedQuad$MaterialInfo.itemRenderType()
64: RenderType.hasBlending()
67: ifeq 82  → 82: solid.add(quad)
70:        → 70: translucent.add(quad)
94..: 若 translucent 为空 → new ItemQuads(copyOf(list), copyOf(list), List.of())
121..: 若 solid 为空       → new ItemQuads(copyOf(list), List.of(), copyOf(list))
```

⇒ **按 `hasBlending()` 分 solid/translucent 分组，正是旧 `submitItem(List)` 内部会做的预处理，
逐义替换，不是近似。**

### 1.3 vanilla 自己的同一形状（两条独立佐证）

**(a) vanilla 的自定义 ItemModel 就是这么转换的** —— `CuboidItemModelWrapper.<init>`：

```
20: invokevirtual QuadCollection.getAll:()Ljava/util/List;
23: invokestatic  ItemQuads.split:(Ljava/util/List;)L…/ItemQuads;
26: putfield      itemQuads:L…/ItemQuads;
…
190: invokevirtual ItemStackRenderState$LayerRenderState.setQuads:(L…/ItemQuads;)V
```

**(b) vanilla 的 `submitItem` 调用点（`LayerRenderState.submit`）参数顺序与我们补出来的一模一样**：

```
101: getfield  quads:Lnet/minecraft/client/resources/model/geometry/ItemQuads;
105: getfield  foilType:Lnet/minecraft/client/renderer/item/ItemStackRenderState$FoilType;
108: invokeinterface net/minecraft/client/renderer/SubmitNodeCollector.submitItem:(…;L…/ItemQuads;L…$FoilType;)V
```

⇒ 我们补出来的 `invokeinterface`（owner 仍是 `SubmitNodeCollector`、`ItemQuads` 在前 `FoilType` 在后）
与 26.3 官方调用点**同形**。

### 1.4 唯一的坑：第 7 参**不在栈顶**（第一次修补的真实事故）

简报建议「在 `invokeinterface` 前插 `invokestatic split`」——**这样打出来是坏类**。
因为 `submitItem` 有 **8 个参数**，第 8 参 `FoilType` 在 `List` 之后才入栈：

```
aload_3 / aload_2 / aload_1 / iload 4 / iload 5 / iconst_0 / aload_0 / getfield tints / aload 6 / getstatic FoilType.NONE
→ 栈 = [collector, pose, ctx, i, i, 0, tints[], List, FoilType]
```

第一次（错误）版本在 `invokeinterface` 前插 `split`，结果：

```
java.lang.VerifyError: Bad type on operand stack
  Location: com/zurrtum/create/client/infrastructure/model/LinkedControllerModel.renderQuads(…)V @20: invokeinterface
  Reason: Type 'net/minecraft/client/resources/model/geometry/ItemQuads' (current frame, stack[8])
          is not assignable to 'net/minecraft/client/renderer/item/ItemStackRenderState$FoilType'
```

（客户端在 `Create.onInitializeClient` → `AllModels.register` 就死了，`game-new-blocks/crash-reports/` 里留着原始报告。）

**正确写法**：`split` 插在 **`getstatic FoilType` 之前**。栈变化：

```
… List                      →  … List
invokestatic split          →  … ItemQuads
getstatic FoilType.NONE     →  … ItemQuads FoilType
invokeinterface submitItem(… ItemQuads, FoilType)V
```

**每条指令处栈深不变、不新增分支 ⇒ 原 StackMapTable 帧不用动**；`ClassWriter(COMPUTE_MAXS)` 重算
max stack/locals。

补出来的字节码（`javap -p -c`，成品）：

```
private void renderQuads(…):
   0: aload_3            (collector)
   1: aload_2            (pose)
   2: aload_1            (ctx)
   3: iload 4 / 5: iload 5 / 7: iconst_0
   8: aload_0 / 9: getfield tints:[I
  12: aload 6            (List<BakedQuad>)
  14: invokestatic  ItemQuads.split:(Ljava/util/List;)L…/ItemQuads;
  17: getstatic     ItemStackRenderState$FoilType.NONE
  20: invokeinterface SubmitNodeCollector.submitItem:(…;L…/ItemQuads;L…$FoilType;)V
  25: return
```

### 1.5 补丁工具（单类 ASM，tree API）

`g22/asm/PatchSubmitItem.java`（ASM 9.10.1 `asm` + `asm-tree`）：

* 用 `ClassNode` 读入 → 找到 `INVOKEINTERFACE`、`name=submitItem`、`desc=旧 desc`、`owner` 以
  `SubmitNodeCollector` 结尾的节点；
* **断言** 它的前一条指令必须是 `GETSTATIC ItemStackRenderState$FoilType.L…` —— 不是就直接
  `exit 4`（**绝不允许静默产出坏类**）；
* 在**那条 getstatic 之前**插 `invokestatic ItemQuads.split`，把 `submitItem` 的 `desc` 换成新 desc；
* **`new ClassWriter(COMPUTE_MAXS)`（不传 ClassReader）** ⇒ 常量池从零重建，
  死的 `submitItem(…,java.util.List,…)` Methodref 不会残留（§3 已验证全 jar 0 条）。

### 1.6 两个调用点（全 71 jar 只有这两处；iris/moreculling 的同名方法是它们自己的）

| 类 | 方法 | 旧字节码 |
|---|---|---|
| `com/zurrtum/create/client/infrastructure/model/LinkedControllerModel` | `private renderQuads(ItemDisplayContext, PoseStack, SubmitNodeCollector, int, int, List)` | `17: invokeinterface SubmitNodeCollector.submitItem:(…Ljava/util/List;…)V` |
| `com/zurrtum/create/client/flywheel/lib/model/baked/ItemModelRenderHelper$CustomLayer` | `public submit(Object, PoseStack, SubmitNodeCollector, int, int, boolean, int)` | `24: invokeinterface SubmitNodeCollector.submitItem:(…Ljava/util/List;…)V` |

（`CustomLayer` 的 `quads` 字段泛型就是 `List<BakedQuad>`，`javap -p` 的 Signature 里写着
`Ljava/util/List<Lnet/minecraft/client/resources/model/geometry/BakedQuad;>;`。）

### 1.7 逐方法 `javap -p -c` 比对（`g22/_clsdiff.py`，归一化常量池序号与指令偏移）

```
== LinkedControllerModel.class
   members: old=37 new=37 SAME
   changed methods: 1 / 37
   --- private void renderQuads(…)
       @@ -10,0 +11 @@
       +invokestatic # // Method ItemQuads.split:(Ljava/util/List;)L…/ItemQuads;
       @@ -12 +13 @@
       -invokeinterface #, 9 // …submitItem:(…III[ILjava/util/List;L…$FoilType;)V
       +invokeinterface #, 9 // …submitItem:(…III[IL…/ItemQuads;L…$FoilType;)V
== ItemModelRenderHelper$CustomLayer.class
   members: old=14 new=14 SAME
   changed methods: 1 / 14
   --- public void submit(…)
       @@ -12,0 +13 @@  +invokestatic # // ItemQuads.split:(…)
       @@ -14 +15 @@   -invokeinterface …java/util/List…  +invokeinterface …ItemQuads…
```

⇒ **37/37 与 14/14 个方法里各只有 1 个方法变，且只变这两条（+1 条）指令。**
（原始输出：`g22/evidence/clsdiff-family1.txt`）

### 1.8 A/B

脚手架：`g22/probe`（一次性驱动 mod，**永不进 `mods-stable`**）+ `g22/_mkmods.py` / `_mkworld.py` /
`_run_world.py`；世界模板 `g18/final/saves/lm-final`，**每次跑都重新拷贝全新副本**；每个 tag 一个全新
`game-*` 目录。

#### (a) 方块侧：把 `create:lectern_controller` 放眼前

```
SETUP base=-324,72,-37 camera=tp @a -323.500 75.000 -42.500 0.00 22.62 view=south
WIN 0 BEGIN simple:minecraft:chest
WIN 0 STATE Block{minecraft:chest}[…] BE=ChestBlockEntity          ← 对照组，旧件也不崩
WIN 0 END simple:minecraft:chest
WIN 1 BEGIN simple:create:lectern_controller
```

**旧件**（`evidence/old-blocks-latest.log`、`old-blocks-console.log`）：

```
WIN 1 STATE Block{create:lectern_controller}[facing=north,has_book=true,powered=false] BE=LecternControllerBlockEntity
Caused by: java.lang.NoSuchMethodError: 'void net.minecraft.client.renderer.SubmitNodeCollector.submitItem(
    com.mojang.blaze3d.vertex.PoseStack, …item.ItemDisplayContext, int, int, int, int[], java.util.List,
    …item.ItemStackRenderState$FoilType)'
 at com.zurrtum.create.client.infrastructure.model.LinkedControllerModel.renderQuads(LinkedControllerModel.java:325)
 at …LinkedControllerModel.render(LinkedControllerModel.java:260)
 at …LinkedControllerModel.renderInLectern(LinkedControllerModel.java:232)
 at …LecternControllerRenderer.submit(LecternControllerRenderer.java:73)
 at net.minecraft.client.renderer.blockentity.BlockEntityRenderDispatcher.submit(BlockEntityRenderDispatcher.java:97)
→ net.minecraft.ReportedException: Rendering Block Entity      RESULT: FAIL_CRASH
```

⇒ **与简报给的崩栈逐帧一致**（`renderQuads:325 ← render:260 ← renderInLectern:232 ←
LecternControllerRenderer.submit:73`）。

**新件**（`evidence/new-blocks-latest.log`）：7 个方块依次放置，`WIN 1 STATE
Block{create:lectern_controller}… BE=LecternControllerBlockEntity` 之后照常走到 `WIN 1 END`：

```
RESULT: WORLD_OK     (61.9 s, joined=True)
NoSuchMethodError 0 / submitItem 0 / ItemQuads 0 / blocksMotion 0 / Chunk build failed 0 / ReportedException 0
```

#### (b) GUI 物品图集：`create:linked_controller` 进 GUI

`phase=gui`：`gamemode creative` → `item replace hotbar.0 with minecraft:stick`（让手持物是木棍，
**避免走第一人称手持渲染**这条相邻路径）→ `give @a create:linked_controller 2` →
**等客户端背包真的收到**（`GUI ITEM SEEN`，见下方教训）→ 让 HUD 物品图标画 10 tick →
再 `setScreenAndShow(new InventoryScreen(player))` 并保持 40 tick。

**旧件**（`evidence/old-gui3-latest.log`）：

```
GUI ITEM SEEN wt=26 hotbar=[1 minecraft:stick 1 create:linked_controller 1 create:linked_controller 0 …]
java.lang.NoSuchMethodError: 'void …SubmitNodeCollector.submitItem(…, java.util.List, …$FoilType)'
 at …LinkedControllerModel.renderQuads(LinkedControllerModel.java:325)
 at …LinkedControllerModel.render(LinkedControllerModel.java:260)
 at …LinkedControllerModel.submit(LinkedControllerModel.java:220)
 at …LinkedControllerModel.submit(LinkedControllerModel.java:48)
 at net.minecraft.client.renderer.item.ItemStackRenderState$LayerRenderState.submit(ItemStackRenderState.java:236)
 at net.minecraft.client.renderer.item.ItemStackRenderState.submit(ItemStackRenderState.java:121)
 at net.minecraft.client.gui.render.GuiItemAtlas.drawToSlot(GuiItemAtlas.java:132)
 at net.minecraft.client.gui.render.GuiItemAtlas.getOrUpdate(GuiItemAtlas.java:92)
 at net.minecraft.client.gui.render.GuiRenderer.lambda$prepareItemElements$0(GuiRenderer.java:285)
 at net.minecraft.client.renderer.state.gui.GuiRenderState.forEachItem(GuiRenderState.java:194)
 at net.minecraft.client.gui.render.GuiRenderer.prepareItemElements(GuiRenderer.java:280)
 at net.minecraft.client.gui.render.GuiRenderer.prepare(GuiRenderer.java:180)
RESULT: FAIL_CRASH
```

⇒ **`GuiItemAtlas.drawToSlot:132` ← `GuiRenderer.lambda$prepareItemElements` 这条 GUI 崩栈被 1:1 复现**
（另一次 `old-gui2` 也崩在同一栈；`old-gui` 那次是玩家手持物品先崩在
`FirstPersonHandsAndItemsRenderer.submitArmWithItem:559`，同族不同入口，记录在此以免混淆）。

**新件 ×3**（`evidence/new-gui1|2|3-latest.log`）：

| tag | 结果 | 提示行 |
|---|---|---|
| `new-gui1` | **`WORLD_OK`** 84.9 s | `GUI ITEM SEEN wt=31 hotbar=[stick, linked_controller ×2, air…]` → `GUI SCREEN open InventoryScreen at wt=41 (icon was on the HUD for 10 ticks)` → `PHASE_DONE itemSeen=true screenOpenFor=40ticks` |
| `new-gui2` | **`WORLD_OK`** 75.7 s | 同上（`wt=28` → `wt=38`） |
| `new-gui3` | **`WORLD_OK`** 60.8 s | 同上（`wt=32` → `wt=42`） |

三份日志里 `NoSuchMethodError` / `submitItem` / `ItemQuads` / `FAIL_TIMEOUT` **全 0**。

> **一个必须写下来的教训（第一次 gui 跑成假阳性）**：`give` 是服务端命令，客户端背包要等同步。
> 第一次 `phase=gui` 在 `wt=18` 读背包时 9 格全是 `0 minecraft:air`，随后开的
> `InventoryScreen` 里根本没有物品 —— 跑出 `WORLD_OK` 但**什么都没验证**。
> 现在的探针**等 `getItem(1)` 非空（`GUI ITEM SEEN`）才开界面**，日志里那行
> `hotbar=[1 minecraft:stick 1 create:linked_controller …]` 就是「图标真的进 GUI 了」的证据。

---

## 2. 族 2：`BlockState.blocksMotion()` 已删

### 2.1 26.3 真身

```
public class net.minecraft.world.level.block.state.BlockState extends BlockBehaviour$BlockStateBase   // 不覆写 isSolid

net.minecraft.world.level.block.state.BlockBehaviour$BlockStateBase:
  private boolean legacySolid;
  public boolean isSolid();
    Code:
       0: aload_0
       1: getfield      legacySolid:Z
       4: ireturn
```

`isSolid()` 就是 `return this.legacySolid`；旧版 `blocksMotion()` 也是同一个字段的同一个访问器
⇒ **同义改名**（`BlockState` 没有覆写，`invokevirtual BlockState.isSolid` 沿父类解析，owner 不用动）。

### 2.2 三个站点（全 jar 只有 3 个类引用 `blocksMotion`）

| 类 | 方法 | 旧指令 | 触发 |
|---|---|---|---|
| `com/zurrtum/create/content/decoration/MetalLadderBlock` | `skipRendering(BlockState, BlockState, Direction)` | `22: invokevirtual BlockState.blocksMotion:()Z` | **sodium 区块构建线程**，经 moreculling |
| `com/zurrtum/create/foundation/utility/BlockHelper` | `destroyBlockAs(Level, BlockPos, Player, ItemStack, float, Consumer)` | `271: invokevirtual …blocksMotion:()Z` | 打碎方块的掉落路径（潜在） |
| `com/zurrtum/create/content/fluids/transfer/FluidFillingBehaviour` | `canBeReplacedByFluid(BlockGetter, BlockPos, BlockState)` | `95: invokevirtual …blocksMotion:()Z` | 流体填充（潜在） |

### 2.3 修法

`g22/asm/PatchBlocksMotion.java`：`invokevirtual BlockState.blocksMotion:()Z` →
`invokevirtual BlockState.isSolid:()Z`（**opcode / owner / desc 都不变，只换名字**），
每条**断言命中数 == 1**，同样用**全新 `ClassWriter(COMPUTE_MAXS)`** 重建常量池。

### 2.4 逐方法比对（`g22/_clsdiff.py`）

```
== MetalLadderBlock.class          members: old=8  new=8  SAME    changed: 1/8
   --- public boolean skipRendering(…)
       @@ -12 +12 @@  -invokevirtual # // BlockState.blocksMotion:()Z
                      +invokevirtual # // BlockState.isSolid:()Z
== BlockHelper.class               members: old=31 new=31 SAME    changed: 1/31
   --- public static void destroyBlockAs(…)
       @@ -117 +117 @@ 同上
== FluidFillingBehaviour.class     members: old=18 new=18 SAME    changed: 1/18
   --- protected boolean canBeReplacedByFluid(…)
       @@ -41 +41 @@ 同上
```

（原始输出：`g22/evidence/clsdiff-family2.txt`）

补后 `MetalLadderBlock.skipRendering` 的关键几行：

```
21: aload_2
22: invokevirtual BlockState.isSolid:()Z
25: ifne 32
```

### 2.5 A/B（`phase=ladders`：只放三个梯子，避免族 1 先崩挡住族 2）

**梯子必须「两块相邻 + 背后石头」**：sodium 对 `isAir()` 邻居直接短路、对满方块邻居也先返回，
只有**非空气且非满方块**的邻居才会走到 `shouldRenderFace` → `CullingUtils.shouldDrawSideCulling`
→ `skipRendering`。所以探针每次摆两个相邻梯子（日志里 `WIN i NEIGHBOUR
Block{create:andesite_ladder}` 就是那第二块）。

**旧件**（`evidence/old-ladders-latest.log`，83.7 s）：

```
WIN 0 STATE Block{create:andesite_ladder}[facing=north,waterlogged=false] BE=null
WIN 0 NEIGHBOUR Block{create:andesite_ladder}[facing=north,waterlogged=false]
WIN 0 END ladder:create:andesite_ladder
[Chunk Render Task Executor #3/ERROR]: Chunk build failed
java.lang.NoSuchMethodError: 'boolean net.minecraft.world.level.block.state.BlockState.blocksMotion()'
 at com.zurrtum.create.content.decoration.MetalLadderBlock.skipRendering(MetalLadderBlock.java:48)
 at net.minecraft.world.level.block.state.BlockBehaviour$BlockStateBase.skipRendering(BlockBehaviour.java:1052)
 at ca.fxco.moreculling.utils.CullingUtils.shouldDrawSideCulling(CullingUtils.java:46)
 at net.caffeinemc.mods.sodium.client.render.model.AbstractBlockRenderContext.handler$edk000$moreculling$useMoreCulling(…:1053)
 at …AbstractBlockRenderContext.shouldDrawSide(…:109)
 at …AbstractBlockRenderContext.isFaceCulled(…:158)
 at …ChunkBuilderMeshingTask.execute(…:131)
 at …ChunkBuilder$WorkerRunnable.run(…:192)
…
WIN 1 BEGIN ladder:create:brass_ladder
net.minecraft.ReportedException: Render Frame
Caused by: java.lang.NoSuchMethodError: 'boolean …BlockState.blocksMotion()'
RESULT: FAIL_CRASH     (blocksMotion 2 行 / Chunk build failed 1 行 / ReportedException 1 行)
```

⇒ **与简报描述完全一致**（sodium 构建线程 → `Chunk build failed` → `ReportedException: Render Frame`）。

**新件**（`evidence/new-ladders-latest.log`，85.8 s）：

```
WIN 0/1/2 STATE Block{create:andesite_ladder} / {brass_ladder} / {copper_ladder}  NEIGHBOUR = 相邻梯子
PHASE_DONE phase=ladders placed=3        RESULT: WORLD_OK
blocksMotion 0 / Chunk build failed 0 / ReportedException 0 / NoSuchMethodError 0
```

`phase=blocks` 那次（新件）也顺带放了 `create:metal_girder` 与 `create:acacia_window`
（`acacia_window` 是另一个覆写 `skipRendering` 的 Create 方块；`metal_girder` 本身不调
`blocksMotion`），均 `STATE` 正常、不崩。

---

## 3. jar 级差异（`g22/_entry_diff.py`）

```
entries: old=14336 new=14336  order+set SAME
entries with different content: 5
  com/zurrtum/create/content/decoration/MetalLadderBlock.class                       6606 ->  6601
  com/zurrtum/create/content/fluids/transfer/FluidFillingBehaviour.class             16760 -> 16755
  com/zurrtum/create/foundation/utility/BlockHelper.class                            34608 -> 34555
  com/zurrtum/create/client/flywheel/lib/model/baked/ItemModelRenderHelper$CustomLayer.class  5036 -> 5237
  com/zurrtum/create/client/infrastructure/model/LinkedControllerModel.class          17184 -> 17320
```

其余 **14,331** 个 entry 解压后逐字节相同。

**死常量池清空验证**（对成品全 jar 扫常量池，不只是这 5 个类）：

| 关键词 | 命中 |
|---|---|
| `blocksMotion` | **0** |
| `(III[ILjava/util/List;L…ItemStackRenderState$FoilType;)V`（旧 submitItem desc） | **0** |
| `ItemQuads` | 2（正好是 `LinkedControllerModel` + `CustomLayer`） |
| `isSolid` | 9（旧件是 7 → 新增的是 `MetalLadderBlock` 与 `FluidFillingBehaviour`；`BlockHelper` 本来就有别的 `isSolid` 引用） |

⇒ 就算扫描器是「读常量池找旧符号」，也**不会再报**这两族。

---

## 4. 验收口径逐条对

### 族 1

| 口径 | 结果 |
|---|---|
| `create:lectern_controller` 放眼前不崩 | ✅ `new-blocks`：`WIN 1 STATE …LecternControllerBlockEntity` → `WIN 1 END`，整轮 `WORLD_OK` |
| GUI 物品图集重建不崩 | ✅ `new-gui1/2/3`：`GUI ITEM SEEN`（图标真进 GUI）→ HUD 画 10 tick → `InventoryScreen` 开 40 tick，`WORLD_OK` ×3 |
| 多跑 3 次（随机崩） | ✅ 3 次独立全新存档/全新 `game-*` 目录，全 `WORLD_OK` |
| `NoSuchMethodError`(带 `submitItem`) / `FAIL_TIMEOUT` = 0 | ✅ 3 份日志 0 / 0；`submitItem` / `ItemQuads` 关键词 0 行 |
| A/B | ✅ 旧件 `FAIL_CRASH`（方块侧 + GUI 侧各一次，栈逐帧对上）；新件不崩 |

### 族 2

| 口径 | 结果 |
|---|---|
| `andesite/brass/copper_ladder` 各一个不崩 | ✅ `new-ladders`：三块 `STATE` + 相邻梯子邻居，`WORLD_OK` |
| `blocksMotion` / `Chunk build failed` / `ReportedException: Render Frame` = 0 | ✅ 0 / 0 / 0（`new-ladders` 与 `new-blocks` 都是 0） |
| 顺带走 `skipRendering` 的方块 | ✅ `create:acacia_window`（覆写 `skipRendering`）不崩；`create:metal_girder`（不调 `blocksMotion`）不崩 |
| A/B | ✅ 旧件 `FAIL_CRASH`（`Chunk build failed` + `blocksMotion` + `ReportedException: Render Frame`）；新件 `WORLD_OK` |

---

## 4.5 交付件本体（**71 jar，不带探针**）

`g22/mods-deliv` = `mods-stable` 的 71 jar，只把 create jar 换成成品（SHA 已核对 `9B5B027C…69AC`），
**不含任何探针**。全新 `game-deliv` + 全新存档副本，`--marker "logged in with entity id"`：

```
title markers: ALL 3 HIT
server_started=True joined=True marker_seen=True in 83.9s
NoSuchMethodError 0 / NoSuchFieldError 0 / ExceptionInInitializerError 0 / NullPointerException 0
submitItem 0 / ItemQuads 0 / blocksMotion 0 / Chunk build failed 0 / ReportedException 0
RESULT: WORLD_OK
```

⇒ 标题 + 进世界 + 出生点渲染都正常，没有 `VerifyError`（第一次打坏的那版正是在这一步就死的）。

---

## 5. 交付与 promote 指引（**本轮没 promote**）

```
成品：work/run26/port/g22/out/create-fly-26.2-6.0.9-2-26.3-patched.jar
SHA-256 9B5B027C7E503EC3FF2CC28FD6D5BCD1D66D81F7469547D294C05E38BA1669AC
大小    19,639,156 B
基线    B6B1FD1840B845523B18F6DBCE938076187B001C0A046186470BFB45BDCB8888 (19,639,253 B)
```

**主代理的 promote 动作**（扫描结束后）：

1. 先核对 `mods-stable/create-fly…jar` 的 SHA **仍是** `B6B1FD18…8888`（本轮它没变；若变了说明
   扫描期间别的代理动过，需重打）。
2. 备份：`…jar.bak-submititem-blocksmotion`（真实 copy）。
3. 用 g22 的成品**覆盖**（`shutil.copy2` 后再原子 rename；不要写穿透，`g16/mods-*` 是硬链接同一 inode）。
4. 复跑：`tools/launch26/launch.py --game-dir <新目录> --mods work/run26/mods-stable` 标题 + 进世界。

---

## 6. 复现用资产（都在 `work/run26/port/g22/`）

| 文件 | 用途 |
|---|---|
| `asm/PatchSubmitItem.java` | 族 1 正式补丁（tree API；`split` 插在 `getstatic FoilType` 之前；断言 1 处） |
| `asm/PatchBlocksMotion.java` | 族 2 正式补丁（3 个类各 1 处） |
| `_patch.py` | 编译并跑两个补丁 → `oldcls/` / `newcls/` |
| `_rebuild_jar.py` / `_entry_diff.py` / `_clsdiff.py` | 重打包 / entry 级差异 / 逐方法 javap 比对（从 g20 原样拷来） |
| `_extract.py` | 从 jar 取 5 个目标类 |
| `probe/` + `_javac.py` + `_mkprobe.py` | 一次性驱动 mod（phase=`blocks` / `lectern` / `ladders` / `gui`） |
| `_mkmods.py` / `_mkworld.py` / `_run_world.py` | A/B 与验收脚手架（**每次全新存档副本**） |
| `evidence/` | 全部原始日志（`old-blocks`、`old-gui{,2,3}`、`old-ladders`、`new-blocks`、`new-ladders`、`new-gui1..3`） |
| `evidence/clsdiff-family1.txt` / `clsdiff-family2.txt` / `entry-diff.txt` | 逐方法比对 / entry 差异原始输出 |
| `_x/` | 26.3 权威 `javap` 转储（`OrderedSubmitNodeCollector.txt`、`ItemQuads.txt`、`BlockStateBase*.txt`、`ItemStackRenderState.txt`、`LayerRenderState.txt`、`CuboidItemModelWrapper.txt`、`GuiRenderer.txt`、`GuiItemAtlas.txt`、`Block.txt`） |
| `mods-old/` / `mods-new/` / `mods-deliv/`（71 jar 无探针）/ `game-*/` | 两套 A/B 环境 + 交付件本体回归（**一次性**，别 promote） |

---

## 7. 未尽事项 / 风险

1. **`BlockHelper.destroyBlockAs` / `FluidFillingBehaviour.canBeReplacedByFluid` 两处只做了静态修，
   没有专门的运行时验收**：前者要打碎方块走真实掉落（`destroyBlockAs` 是从 `destroyBlock` 的
   `Consumer` 重载进去的），后者要流体填进方块。两处都是**同一符号、同一 `isSolid()` 逐义替换**，
   且类级 `javap` 比对只有那 1 条指令变；但严格说它们的「行为」本轮没有像梯子那样被日志证明。
2. **`GuiItemAtlas` 的随机性**：三次新件 GUI 跑都命中 `GUI ITEM SEEN` → 图标确实进过图集。
   旧件在 `old-gui`（手持路径）与 `old-gui2/3`（图集路径）都崩，说明这个入口在本机是稳定可复现的，
   不是「碰巧没撞上」。
3. **Ponder / Flywheel 侧**：`CustomLayer` 是 Flywheel 的 `SpecialModelRenderer`，本轮 A/B 只覆盖了
   物品图标与讲台方块两条真实入口；Ponder 场景里的物品渲染仍受台账那条「几何体提交进 26.3 相位」
   未完成所限，不属于本族。
4. **不要用本轮成品替换 `mods-stable` 做「顺手验证」**——扫描还在跑；promote 由主代理在扫描结束后做。
