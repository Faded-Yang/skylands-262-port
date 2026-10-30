# fix-aero-render —— Aeronautics 26.3 渲染/GUI 族清零

> 族：**渲染 / GUI**（`GuiGraphics` · `MultiBufferSource` · `SuperRenderTypeBuffer` · `LightTexture` ·
> `getMainCamera` · `RenderPipeline` · `cutoutBlockSheet` · `screen` · `hideGui`）
> 执行：R350 子代理（渲染/GUI 线）
> 工程：`work/aero-port/aeronautics-26`　日志：`notes/aero26-compile-9.log` → `notes/aero26-compile-14.log`

---

## 一、验收数字（编译实测）

| 指标 | 数值 |
|---|---|
| **起始**（`aero26-compile-9.log`） | **348 错** |
| 第 1 轮后（`-10`） | 218 |
| 第 2 轮后（`-11`） | 136 |
| **终点**（`aero26-compile-14.log`） | **77 错** |
| **净减** | **−271（−77.9%）** |
| 本线 9 个符号族残留 | **0**（`node dump_fam.cjs notes/aero26-compile-14.log` 输出为空） |

复现：

```powershell
cd work\aero-port\aeronautics-26
$env:JAVA_HOME="$env:APPDATA\.minecraft\runtime\java-runtime-epsilon"
.\gradlew.bat compileJava --no-daemon
# 解析（去重：本日志每条错误出现两次）
node parse_err.cjs C:\...\notes\aero26-compile-14.log
node dump_fam.cjs  C:\...\notes\aero26-compile-14.log   # 按本线符号分组，应为空
```

### 各族起始 → 终点

| 符号 | 起始（去重后） | 终点 | 修法 |
|---|---|---|---|
| `GuiGraphics` | 34 | **0** | → `GuiGraphicsExtractor`；`drawString`→`text`、`renderWidget`→`extractWidgetRenderState`、旧 `render(...)`→`extractRenderState(...)` |
| `MultiBufferSource` | 14 | **0** | 整类删除、无替代 ⇒ 逐点降级（见 §四） |
| `LightTexture` | 10 | **0** | → `net.minecraft.util.LightCoordsUtil.FULL_BRIGHT` |
| `SuperRenderTypeBuffer` | 7 | **0** | Create 26.3 整族删除 ⇒ 降级 |
| `getMainCamera` | 5 | **0** | → `gameRenderer.mainCamera()` |
| `RenderPipeline` | 3 | **0** | 包移动 → `com.mojang.renderpearl.api.pipeline.RenderPipeline` |
| `cutoutBlockSheet` | 3 | **0** | → `RenderTypes.cutoutMovingBlock()` |
| `screen`（`Minecraft.screen` / `setScreen`） | 22 | **0** | → `minecraft.gui.screen()` / `minecraft.gui.setScreen(...)` |
| `hideGui` | 3 | **0** | `Options` 无替代 ⇒ 降级为「总是显示」 |
| `setWindowSize`（连带） | 2 | **0** | 尺寸改由 `AbstractSimiContainerScreen` 5 参构造器固定 |
| （附带）`AllKeys`/`Type.KEYSYM`/`scancode` | 7 | **0** | 见 §二 #14–#16 |

**改动面：32 个文件 / 约 110 个站点。**

> ⚠ **口径**：`77` 是本线收尾时 `notes\aero26-compile-14.log` 的**实测快照**。同一时段还有别的线在
> 并行改 `src\stub\java\**`、`SimBlocks`、`AeroBlocks` 等（本线**一律没碰**），所以总数会随他们的提交继续变化；
> 判本线的唯一指标是 **9 族残留 = 0**（`node dump_fam.cjs <最新日志>` 输出为空）。

---

## 二、javap 核实的 26.3 事实（本次动工依据，全部实测，勿凭记忆）

jar：`~\.minecraft\versions\26.3\26.3.jar`；Create：`work\aero-port\libs26\create-fly-26.2-6.0.9-2-26.3-patched.jar`
javap：`~\.minecraft\runtime\java-runtime-epsilon\bin\javap.exe`

| # | 事实 | 依据 |
|---|---|---|
| 1 | `Sheets` **只剩 12 个 item-sheet 工厂**（`cutoutBlockItemSheet` / `translucentItemSheet` / …），**没有** `cutoutBlockSheet()` / `solidBlockSheet()` | `javap -p Sheets` |
| 2 | 方块图集 + cutout 的落点是 **`RenderTypes.cutoutMovingBlock()`**（`solidMovingBlock()` 对应 solid） | `javap -c RenderTypes` → `createMovingBlockSetup` 用 `TextureAtlas.LOCATION_BLOCKS` + `useLightmap()` |
| 3 | `GuiGraphicsExtractor` **没有** `hLine`/`vLine`（只有 `fill`/`outline`/`blit`/`text`/`item`/`pose`） | `javap -p GuiGraphicsExtractor` |
| 4 | `Options`（512 行全量 dump）**没有** `hideGui`；`Minecraft`/`Gui`/`GameRenderer` 也没有 | `javap -p`；解包后全量 grep 只在 `ScreenEffectRenderer` 命中（它是 `submit(..., boolean hideGui)` 的形参名，非字段） |
| 5 | 26.3 的 F1 状态没有公开读取口：只在内部作为 boolean 传给 `ScreenEffectRenderer#submit(float, SubmitNodeCollector, PlayerRenderState, CameraRenderState, boolean)` | 同上 |
| 6 | `AbstractSimiContainerScreen` 构造器 = `(T, Inventory, Component, int imageWidth, int imageHeight)`；`setWindowSize` **只在** `AbstractSimiScreen`（非容器）上；`imageWidth/imageHeight` 是 `final` | `javap -p/-c` |
| 7 | `AbstractContainerScreen` **没有 `renderBg` 覆写点**，也没有背景贴图字段；背景/槽位都在 `extractContents(...)` 里 | `javap -p AbstractContainerScreen` + 反编译 `extractContents` |
| 8 | `AbstractSimiWidget.extractRenderState(GuiGraphicsExtractor,int,int,float)` 是 **public**，是 1.21.11 `render(...)` 的直接落点（`extractWidgetRenderState` 是 protected） | `javap -p AbstractSimiWidget` |
| 9 | Create 的 outliner 换成提交模型：`LineOutline.submit(Minecraft, PoseStack, SubmitNodeCollector, Vec3, float)`，几何下沉到 `protected submitInner(PoseStack, SubmitNodeCollector, Vec3, float, Vector3d, Vector3d, float, int color, int lightmap, boolean)` | `javap -c LineOutline`（`submit` 只是转发到 `submitInner`） |
| 10 | `com.zurrtum.create.client.catnip.render.SuperRenderTypeBuffer` / `DefaultSuperRenderTypeBuffer` **整族不存在**（换成 `SuperByteBufferRenderState` + `SuperNodeCollector`） | `jar tf` 全量，无该类 |
| 11 | `net.minecraft.client.renderer.entity.ItemRenderer` **整类删除**（只剩 `ThrownItemRenderer`/`OversizedItemRenderer`），`Minecraft.getItemRenderer()` 一并消失 | `jar tf` |
| 12 | `net.minecraft.client.Minecraft`：`public final Gui gui`；`Gui.screen()` / `Gui.setScreen(Screen)` | `javap -p` |
| 13 | `GameRenderer.mainCamera()`；`LightCoordsUtil.FULL_BRIGHT`（`net.minecraft.util`，不是 renderer 包） | `javap -p` |
| 14 | Create 的 `AllKeys` 26.3 **只剩 `KeyMapping` 常量**：`isKeyDown` / `isMouseButtonDown` / `hasControlDown` / `hasShiftDown` 全删 | `javap -p com.zurrtum.create.client.AllKeys` |
| 15 | 替代：`InputConstants.isKeyDown(int)`、`Minecraft.hasControlDown()/hasShiftDown()`、`MouseHandler.isLeftPressed()`；`Minecraft.mouseHandler` 仍是 public 字段 | `javap -p` |
| 16 | `InputConstants.Type.KEYSYM` → **`Type.KEYBOARD`**；`KeyEvent.scancode()` → **`KeyEvent.keycode()`**（record = `(key, keycode, modifiers)`） | `javap -p InputConstants$Type / KeyEvent`，且 `InputConstants.getKey(KeyEvent)` 内部用 `KeyEvent.key()` |

---

## 三、逐文件改动（32 文件）

| # | 文件（相对 `src`） | 改了什么 |
|---|---|---|
| 1 | `main\…\ponder\outliners\LerpedLineOutline.java` | **重写**：`render(...)`+`renderInner(...)` → 单个 `submitInner(...)`（把插值后的两端点传给 `super`）。**观感与 1.21.11 等价，无降级** |
| 2 | `excluded-wip\SimRenderTypes.java` | `Sheets.cutoutBlockSheet()`→`RenderTypes.cutoutMovingBlock()`（3 处）、`Sheets.solidBlockSheet()`→`solidMovingBlock()`（1 处） |
| 3 | `main\…\physics_staff\PhysicsStaffRenderHandler.java` | 去 `MultiBufferSource`/`LightTexture`/`VertexConsumer` import；`renderSelectionBox` 去 bufferSource 形参；`options.hideGui` 分支删除；`renderAllLocks(...)` 整方法删除 |
| 4 | `main\…\physics_staff\PhysicsStaffClientHandler.java` | `getMainCamera()`→`mainCamera()`（2）；`onRender` 空实现；`PhysicsBeam.render(...)` 删除；`level.random`→`level.getRandom()` |
| 5 | `main\…\events\SimulatedCommonClientEvents.java` | 4× `.screen`→`.gui.screen()`；`renderOverlays(GuiGraphicsExtractor)`；`onRenderLevelStage` 去 bufferSource 形参 |
| 6 | `main\…\diagram\screen\DiagramScreen.java` | 去 `MultiBufferSource` import；`minecraft.setScreen`→`minecraft.gui.setScreen`；`widget.render`→`extractWidgetRenderState`；`drawString`→`text`；**`hLine`/`vLine`→1px `fill`**（4 处） |
| 7 | `main\…\diagram\screen\DiagramStickyNote.java` | `renderWidget`→`extractWidgetRenderState`；去 `MultiBufferSource` import；删 `renderBuffers().bufferSource().endBatch()` |
| 8 | `main\…\linked_typewriter\screen\LinkedTypewriterScreen.java` | 9 处：`GuiGraphics`→Extractor；**`render`→`extractRenderState`**；**`renderBg`→`extractContents`**（26.3 无 renderBg 覆写点）；`setWindowSize`×2 删除（尺寸进构造器）；3 个 widget 的 `.render`→`.extractRenderState`；`drawString`→`text`；`KeyRow.render` 形参 |
| 9 | `main\…\index\SimIcons.java` | 删 `render(PoseStack, MultiBufferSource, int)` + `vertex(...)`（零调用）；清 9 个 import |
| 10 | `main\…\linked_typewriter\screen\EntryModifierScreen.java` | import + 2 个签名 + 3 个 widget `.render`→`.extractRenderState` |
| 11 | `main\…\linked_typewriter\screen\KeyEditorScreen.java` | `Type.KEYSYM`→`KEYBOARD`；`AllKeys.isMouseButtonDown(0)`→`Minecraft.getInstance().mouseHandler.isLeftPressed()`；去 AllKeys import |
| 12 | `main\…\linked_typewriter\screen\widgets\PromptWidget.java` | `Type.KEYSYM`→`KEYBOARD`；`event.scancode()`→`event.keycode()` |
| 13 | `main\…\modulating_receiver\ModulatingLinkedReceiverScreen.java` | import + 2 个签名 + `drawString`→`text` |
| 14 | `main\…\registrate\simulated_tab\SimulatedCreativeTab.java` | import + 2 个签名 + `drawString`→`text`（2） |
| 15 | `main\…\steering_wheel\SteeringWheelHandler.java` | import + 签名 + `drawString`→`text`（2） |
| 16 | `main\…\throttle_lever\ThrottleLeverHandler.java` | import + 签名 + `drawString`→`text` |
| 17 | `main\…\physics_assembler\PhysicsAssemblerGUIHandler.java` | import + 签名 |
| 18 | `main\…\client\BlockPropertiesTooltip.java` | `Minecraft.screen`→`.gui.screen()`；`AllKeys.isKeyDown`→`InputConstants.isKeyDown` |
| 19 | `main\…\contraption_diagram\DiagramDataPacket.java` | `minecraft.screen`→`minecraft.gui.screen()` |
| 20 | `main\…\RopeItem\ClientRopeItemHandler.java` | `.screen`→`.gui.screen()` |
| 21 | `main\…\mixin\hold_interaction\KeyboardHandlerMixin.java` | `this.minecraft.screen`→`.gui.screen()` |
| 22 | `main\…\linked_typewriter\LinkedTypewriterInteractionHandler.java` | `.screen`→`.gui.screen()`；`setScreen(null)`→`gui.setScreen(null)` |
| 23 | `excluded-wip\ModulatingLinkedReceiverBlockEntity.java` | `.screen`→`.gui.screen()` |
| 24 | `excluded-wip\LinkedTypewriterItemBindHandler.java` | `GuiGraphics`→Extractor；`options.hideGui` 分支删除 |
| 25 | `main\…\util\hold_interaction\HoldInteractionManager.java` | `options.hideGui`→`false` |
| 26 | `main\…\navigation_target\RenderableNavigationTarget.java` | 重写：去 `MultiBufferSource`/`ItemRenderer` 形参（零调用） |
| 27 | `main\…\ponder\elements\rope\RopeStrandElement.java` | 删 `renderLast(...)`（空壳）+ 2 个 import |
| 28 | `excluded-wip\AeroRenderTypes.java` | `RenderPipeline` import 换成 `com.mojang.renderpearl.api.pipeline.RenderPipeline` |
| 29 | `main\…\honey_glue\HoneyGlueClientHandler.java` | `AllKeys.hasControlDown()/hasShiftDown()`→`Minecraft.getInstance().has*Down()`；去 AllKeys import |
| 30 | `main\…\hot_air\sound\BalloonBurnerSoundInstance.java` | `getMainCamera()`→`mainCamera()`（2） |
| 31 | `main\…\blocks\handle\ClientHandleHandler.java` | `getMainCamera()`→`mainCamera()` |
| 32 | `main\…\mixin\ponder\PonderSceneMixin.java` | 去无用 `SuperRenderTypeBuffer` import |

---

## 四、降级清单（**丢了什么 / 为什么 / 能否修回**）

> 每条源码里都带 `// PORT(26.3): ...` 注释。

### 4.1 有视觉损失的新降级（5 条）

| # | 位置 | 丢了什么效果 | 为什么必须丢 | 可修回？ |
|---|---|---|---|---|
| **1** | `PhysicsStaffRenderHandler.renderAllLocks`（整方法删除） | **物理法杖「锁」的贴图方块高亮不再绘制**（每把锁位置那个 lock 贴图四边形） | ① `MultiBufferSource.BufferSource.getBuffer(RenderType)` —— `MultiBufferSource` 在 26.3 整类删除；② 即时顶点提交只有 `SubmitNodeCollector.submitCustomGeometry(PoseStack, RenderType, …)`，而本方法拿不到 collector（它原本挂的 Veil 渲染阶段事件已被拔除） | ⚠️ 需按 26.3 `LevelRenderEvents` 拿到 `SubmitNodeCollector` 后重写（与 Veil 线 DEGRADATIONS #6 同条件） |
| **2** | `PhysicsStaffClientHandler.onRender`（空实现）+ `PhysicsBeam.render(...)`（删除） | **物理法杖光束的折线不再绘制**（带抖动的物理束）；节点抖动模拟 `update()` 仍保留 | ① `SuperRenderTypeBuffer`/`DefaultSuperRenderTypeBuffer` 在 26.3 Create 里整族删除；② `LineOutline.render(…, SuperRenderTypeBuffer, …)` → `submit(…, SubmitNodeCollector, …)`，本类拿不到 collector | ⚠️ 同上：拿到 collector 后 `line.submit(mc, ms, collector, camera, pt)` 即可复活 |
| **3** | `PhysicsStaffRenderHandler.renderSelectionBox` | **按 F1 隐藏 GUI 时，法杖选择框不再跟着隐藏** | `Options.hideGui` 在 26.3 已不存在（`Options` 512 行全量 javap + `Minecraft`/`Gui`/`GameRenderer` 均无；26.3 只在内部把该 boolean 传给 `ScreenEffectRenderer#submit(...)`，**无公开读取口**） | ❌ 需 Mixin `ScreenEffectRenderer` 抓那个 boolean，或等上游公开 getter |
| **4** | `HoldInteractionManager.renderOverlay` | **按 F1 时，按住交互的进度条/提示仍会画在屏幕上** | 同上（`options.hideGui` 无替代），改传常量 `false` | ❌ 同上 |
| **5** | `LinkedTypewriterItemBindHandler.renderOverlay`（`excluded-wip`） | **按 F1 时，键位绑定的物品提示仍会显示** | 同上 | ❌ 同上 |

### 4.2 零损失降级（**只是删掉已不可用的空壳/空刷**，不是视觉削减）

| # | 位置 | 删了什么 | 为什么零损失 |
|---|---|---|---|
| 6 | `SimIcons.render(PoseStack, MultiBufferSource, int)` + `vertex(...)` | 世界空间刷图标四边形的旧接口 | **工程内零调用**；GUI 侧统一走 `render(GuiGraphicsExtractor,int,int)` |
| 7 | `RenderableNavigationTarget.renderInNavTable` 的 `MultiBufferSource buffer` 形参与 `ItemRenderer` 局部量 | 两个 26.3 已删除的类型 | **零调用点**；方法体自 1.21.11 起就是空壳 |
| 8 | `RopeStrandElement.renderLast(...)` | 整个方法 | 方法体自 1.21.11 起就是空壳（绳子在 ponder 场景里早已不绘制） |
| 9 | `DiagramStickyNote` 的 `renderBuffers().bufferSource().endBatch()` | 一次手动刷批 | 26.3 无 `renderBuffers()`、无 `MultiBufferSource`；提交改由 collector 在帧末统一完成 |
| 10 | `SimulatedCommonClientEvents.onRenderLevelStage` 的 `MultiBufferSource.BufferSource` 形参 | 一个形参 | 26.3 无该类；本方法**当前无订阅方**（Veil 渲染阶段事件已拔除） |

> ⚠️ `src\stub\java`、`SimBlocks.java`、`AeroBlocks.java`、`SimulatedCriterionTriggerBase.java`、
> `SimulatedAdvancement.java` **完全没碰**（归别的线）。

---

## 五、等价改写（**不是**降级，别记进 DEGRADATIONS）

| 位置 | 改写 | 为什么等价 |
|---|---|---|
| `DiagramScreen.renderMagnificationHighlight` | `hLine(x1,x2,y,c)` → `fill(x1,y,x2,y+1,c)`；`vLine(x,y1,y2,c)` → `fill(x,y1,x+1,y2,c)` | 26.3 只删了便捷线函数，`fill` 的像素覆盖范围完全一致（1px） |
| `LinkedTypewriterScreen` | `setWindowSize(w,h)`（init + rescaleWindow） → 构造器传 `width/height` | 26.3 的尺寸在构造期固定（`imageWidth/Height` 是 final），两个调用点原本传的就是同一对常量 |
| `SimRenderTypes` | `Sheets.cutoutBlockSheet()` → `RenderTypes.cutoutMovingBlock()` | 同一张方块图集（`TextureAtlas.LOCATION_BLOCKS`）+ cutout + lightmap，语义最近的现存 RenderType |
| `LerpedLineOutline` | `renderInner` → `submitInner` 覆写 | 26.3 的 `submitInner` 直接接收两端点，插值逻辑原样保留 |

---

## 六、回滚

```powershell
# 9 个主文件有 .bak-rgui（动工前原样）
Get-ChildItem -Recurse -Filter *.java.bak-rgui | ForEach-Object {
    Copy-Item $_.FullName ($_.FullName -replace '\.bak-rgui$','') -Force
}
```

> ⚠️ **其余 23 个文件没有 `.bak-rgui`**（本线失误，如实记录）。回滚靠三份「可逆脚本」：
> `work\aero-port\aeronautics-26\batch_gui.cjs` / `batch_gui2.cjs` / `batch_gui3.cjs` ——
> 里面每条都是 `[from, to]` 精确字符串对，把两者对调即可还原（脚本本身就是改动清单）。
> 另：`src.bak-veil\` 是 R344 拔 Veil 前的整树快照，早于本线，**不能**当本线的回滚点。

---

## 七、交接：剩下的 77 错里有 0 条属于本线

本线 9 族全 0。剩余错误按族归别人（供后续分工参考）：

| 剩余族（实测 `-14` 的前几名） | 建议归属 |
|---|---|
| `ForceGroups.GRAVITY_VALUE` 等 7 个常量（`ForceGroupIndex` 7） | 力系统/核心线 |
| `swing(...)` 重载 / `LocalPlayer.swingTime/swinging`（`ZiplineClientManager` 6、`ClientHandleHandler` 5、`HoneyGlueEntity` 3） | 实体/动画线 |
| `SimAssemblyHelper` 4 / `SceneScheduler` 3 / `GirderBlockMixin` 2 / `PropellerBearingBlockEntity` 2 / `PropellerAirParticle` 2 | 各自文件归属线 |
| 其余零散 1 错文件（`ItemInfoWrapper`、`EnvelopeBlock`、`GustEntity`、`LevititeClientCatalyzerHandler`…） | 各自文件归属线 |

> **本线未做**：未跑运行期验证（`tools\launch26\launch.py`）。「0 编译错 ≠ 能跑」仍成立：
> 本线新增的 `extractRenderState`/`extractContents` 覆写点、`@Override` 的 mixin 注入器都只在运行期解析。
