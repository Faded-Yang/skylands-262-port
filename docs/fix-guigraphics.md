# fix-guigraphics —— 裸 `GuiGraphics` → 26.3 `GuiGraphicsExtractor`

> 族：**GUI 渲染管线改名**（26.3 `net.minecraft.client.gui.GuiGraphics` 整个类不存在）
> 执行：R341 子代理（GuiGraphicsExtractor 线）
> 约束：含 `foundry.veil` 的文件**整文件跳过**（归 Veil 线）；`src\stub\java` 不动；**未编译**（本线不跑编译）

---

## 一、结果（验收数字）

| 指标 | 数字 |
|---|---|
| 动工前：裸 `GuiGraphics` 站点 | **115 处 / 32 文件** |
| ↳ 其中含 `foundry.veil`、整文件跳过 | **59 处 / 13 文件** |
| ↳ 本线实际修 | **56 处 / 19 文件** |
| 动工后：**非 Veil 文件残留** | **0**（python `\bGuiGraphics\b` + 排除含 Extractor 的行复核） |
| 动工后：Veil 文件残留（按约定留给 Veil 线） | 59 处 / 13 文件（清单见第五节） |

> ⚠ **口径说明（重要，别被 197 误导）**：任务书写「197 处」。本次用任务书给的同一条 python 规则实测，
> 全 `src`（含 `excluded-wip`、`stub`、`_stub_bak_*`）**只有 115 行命中**，且每行恰好 1 个匹配
> （**行数 = 出现次数 = 115**）。`src.bak-veil`（Veil 线动工前的整库快照）也是 115/32，可复现。
> 台账 R338 记的「186 处」与本任务书的「197」都不是按这条规则在当前源码上数出来的（应为早期口径/含别的计数）。
> **以本文件的 115 → 0（非 Veil）为准。**

复现命令（python 3）：

```python
import os,re
root=r"...\aeronautics-26\src"; pat=re.compile(r"\bGuiGraphics\b")
for dp,dn,fn in os.walk(root):
    for f in fn:
        if not f.endswith(".java"): continue
        p=os.path.join(dp,f); t=open(p,encoding="utf-8",errors="replace").read()
        hits=[l for l in t.split("\n") if pat.search(l) and "GuiGraphicsExtractor" not in l]
        if hits: print(len(hits), ("VEIL " if "foundry.veil" in t else "     ")+os.path.relpath(p,root))
```

每个被改文件都有备份：`<文件名>.java.bak-guigraphics2`（**19 个**，`src` 树内，Gradle 不会编译它们）。

---

## 二、javap 核实的 26.3 事实（本次动工依据）

`javap -p -cp minecraft-merged-deobf-26.3.jar …`（jar：`~\.gradle\caches\fabric-loom\minecraftMaven\net\minecraft\minecraft-merged-deobf\26.3\`）

| 旧（1.21.x） | 26.3 | 依据 |
|---|---|---|
| `net.minecraft.client.gui.GuiGraphics` | **不存在**，换 `net.minecraft.client.gui.GuiGraphicsExtractor` | javap 找不到 GuiGraphics |
| `Renderable.render(GuiGraphics,int,int,float)` | `extractRenderState(GuiGraphicsExtractor,int,int,float)` | `Renderable` 只剩这一个抽象方法 |
| `Screen.render(...)` | `extractRenderState(...)` / `extractRenderStateWithTooltipAndSubtitles(...)` | `Screen` javap |
| `AbstractWidget.renderWidget(GuiGraphics,int,int,float)` | **`extractWidgetRenderState(GuiGraphicsExtractor,int,int,float)`**（抽象） | `AbstractWidget` javap；`AbstractWidget.render` 也不存在，只有 `final extractRenderState` |
| `GuiGraphics.drawString(Font,…,boolean)` | **`text(Font, String/Component/FormattedCharSequence, int,int,int[,boolean])`** | `GuiGraphicsExtractor` |
| `drawCenteredString(...)` | **`centeredText(Font, …, int,int,int)`** | 同上（本工程未用到） |
| `renderItem(ItemStack,int,int[,int])` / `renderItem(LivingEntity,ItemStack,int,int,int)` | **`item(ItemStack,int,int[,int])` / `item(LivingEntity, ItemStack, int,int,int)`** | 同上 |
| `renderTooltip(...)` | `setTooltipForNextFrame(...)` / `setComponentTooltipForNextFrame(...)` | 同上 |
| `blit(Identifier,int x,int y,int u,int v,int w,int h,int texW,int texH)` | **`blit(RenderPipeline, Identifier, int x,int y, float u,float v, int w,int h, int texW,int texH)`**（首参 pipeline，u/v 变 float） | 10 参重载反编译：内部转成 (x,y,u,v,w,h,uWidth=w,vHeight=h,texW,texH) |
| `fill/fillGradient/outline/horizontalLine/verticalLine/enableScissor/disableScissor/containsPointInScissor/guiWidth()/guiHeight()/pose()` | **全部保留**（`pose()` 返回 `Matrix3x2fStack`） | 同上 |
| — | 新增 `nextStratum()` / `blurBeforeThisStratum()` / `requestCursor(CursorType)` | 同上 |

**第三方（Create-Fly 26.3 补丁 jar）同样已换到 Extractor**（这决定了本篇的「方法到底叫什么」）：
- `catnip…ScreenElement.render(GuiGraphicsExtractor,int,int)` → `SimGUITextures`/`SimIcons` 的 `render` **名字不变**
- `catnip…AbstractSimiWidget`：`extractRenderState` / `extractWidgetRenderState` / `doRender` / `renderTooltip` 全是 Extractor；**`doRender` 名字不变**
- `foundation…IconButton.doRender(GuiGraphicsExtractor,int,int,float)`
- `GuiGameElement$GuiItemRenderBuilder.render(GuiGraphicsExtractor)`
- `GoggleOverlayRenderer.renderOverlay(Minecraft, GuiGraphicsExtractor, DeltaTracker)`
- `PonderUI.renderScene(GuiGraphicsExtractor,int,int,float,float)`、`TextWindowElement.render(PonderScene,PonderUI,GuiGraphicsExtractor,float,float)`

---

## 三、逐文件改动（19 文件 / 56 处）

| # | 文件（相对 `src\main\java`） | 裸引用 | 具体改动 |
|---|---|---|---|
| 1 | `dev\eriksonn\aeronautics\mixin\levitite\PonderUIMixin.java` | 2 | import + `renderScene` 注入器形参 |
| 2 | `…\linked_typewriter\screen\KeyEditorScreen.java` | 9 | import；8 个 `render*`/`doRender` 签名；5 处 `widget.render→extractRenderState`；`drawString→text` |
| 3 | `…\linked_typewriter\screen\widgets\ConfirmationWidgetBase.java` | 3 | import；`doRender`、`renderHoveredText` 形参（`setComponentTooltipForNextFrame` 保留） |
| 4 | `…\linked_typewriter\screen\widgets\KeyWidget.java` | 5 | import；`render` 形参；**`renderWidget`→`extractWidgetRenderState`**；`this.render→this.extractRenderState`；`renderItem→item`×2；`drawString→text` |
| 5 | `…\linked_typewriter\screen\widgets\PromptWidget.java` | 2 | import；`doRender` 形参；`drawString→text` |
| 6 | `…\diagram\screen\DiagramButton.java` | 2 | import；**`renderWidget`→`extractWidgetRenderState`**；**tooltip 调用降级（见第四节）** |
| 7 | `…\diagram\screen\DiagramForceGroupToggle.java` | 3 | import；`renderTab` 形参；**`renderWidget`→`extractWidgetRenderState`**；`drawString→text`×6 |
| 8 | `…\index\SimGUITextures.java` | 4 | import；3 个 `render` 形参；2 处 `blit` 加 `RenderPipelines.GUI_TEXTURED` 首参 |
| 9 | `…\index\SimIcons.java` | 2 | import；`render` 形参；**修正原先错位的 11 参 blit → 10 参**（u=iconX, v=iconY, 16×16, 64×64） |
| 10 | `…\mixin\creative_tab_sections\CreativeModeInventoryScreenMixin.java` | 2 | import + 注入器形参（该文件被 `compileJava` exclude，仍清零） |
| 11 | `…\mixin\hold_interaction\GoggleOverlayRendererMixin.java` | 2 | import + `@Inject` 形参 |
| 12 | `…\mixin\physics_staff\GuiGraphicsMixin.java` | 2 | **整类降级**：`@Mixin(GuiGraphicsExtractor.class)` + 删掉失效 `@WrapMethod`（见第四节） |
| 13 | `…\mixin\ponder\PonderSceneMixin.java` | 2 | import + `@Redirect` 注入器形参（target 本身仍是 1.21.1 旧包名，见第五节告警） |
| 14 | `…\mixin\ponder\PonderUIMixin.java` | 3 | import + `@ModifyConstant`/`@Inject` 两个注入器形参 |
| 15 | `…\mixin\ponder\TextWindowElementMixin.java` | 5 | import；2 个 `@WrapOperation` 的 **target 描述符** `L…GuiGraphics;fillGradient(IIIIIII)V` → `L…GuiGraphicsExtractor;…`；2 个注入器形参 |
| 16 | `…\ponder\elements\KeybindWindowElement.java` | 2 | import；`render` 形参；`drawString→text` |
| 17 | `…\ponder\elements\rope\RopeStrandElement.java` | 2 | import + `renderLast` 形参（方法体本就是空壳） |
| 18 | `…\util\hold_interaction\BlockHoldInteraction.java` | 2 | import + `renderOverlay` 形参 |
| 19 | `…\util\hold_interaction\HoldInteractionManager.java` | 2 | import + `renderOverlay` 形参 |

### 改动类型统计

| 类型 | 处数 |
|---|---|
| 类型名替换（import + 形参/字段/签名里的 `GuiGraphics`） | **56** |
| 方法签名重打（因类型变化） | **34** |
| 方法改名（`renderWidget` → `extractWidgetRenderState`） | **3**（KeyWidget / DiagramButton / DiagramForceGroupToggle） |
| 方法改名（`@Mixin` 目标类 → `GuiGraphicsExtractor`） | 1（physics_staff.GuiGraphicsMixin） |
| 调用点改写 | **21**：`drawString→text` 10、`renderItem→item` 2、`widget.render→extractRenderState` 6、`blit` 补 pipeline 首参 3 |
| 删除/注释掉的调用（降级） | **2**（DiagramButton 的 tooltip 调用、physics_staff 的 `@WrapMethod`） |

> 说明：`Screen/Renderable` 的 `render→extractRenderState` 在本工程**没有直接命中**——
> 这里没有自己 `extends Screen` 并覆写 `render` 的类（自定义屏走 Create 的 `AbstractSimiWidget` / ponder 体系）。
> 唯一相关的 `renderWidget` 覆写 3 处已按 26.3 改名为 `extractWidgetRenderState`。

---

## 四、降级清单（**丢了什么效果**）

| # | 位置 | 方法/调用 | 丢了什么效果 | 原因 | 可修回？ |
|---|---|---|---|---|---|
| 1 | `DiagramButton.extractWidgetRenderState` | `DiagramScreen.renderTooltip(guiGraphics, …)` → **注释掉** | **图纸界面上按钮的鼠标悬停 tooltip 不再显示**（按钮本身、图标、点击都正常） | `DiagramScreen.renderTooltip` 的形参仍是 `GuiGraphics`，而 `DiagramScreen` 含 `foundry.veil`、按约定整文件不动 ⇒ 跨文件类型不兼容，本线无法调用 | ✅ 能：Veil 线把 `DiagramScreen.renderTooltip` 形参改成 `GuiGraphicsExtractor`（第 1048 行）后，把 `DiagramButton` 里注释的两行恢复即可 |
| 2 | `physics_staff.GuiGraphicsMixin` | 整个 `@Mixin(GuiGraphics.class)` + `@WrapMethod(renderItem(LivingEntity,Level,ItemStack,IIII)V)` → **类体清空** | 物理手杖在物品栏/容器槽位里的 **16×16 裁剪高亮**（scissor 方块）不再注入 | ① 目标类 `GuiGraphics` 不存在；② 注入点 `renderItem(LivingEntity,Level,ItemStack,IIII)V` 在 26.3 变成 `item(LivingEntity,ItemStack,III)`，无同签名可迁；③ 该注入体在 1.21.11 阶段**就已是空壳**（`RenderSystem.enableScissor/disableScissor` 被删，全部绘制语句早已注释） | ⚠️ 要修回得重写：`@WrapMethod(method="item(Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/world/item/ItemStack;III)V")` + 用 `enableScissor` 替代 `RenderSystem`。**该类当前未列入 `simulated.mixins.json`，所以 0 运行期影响** |
| 3 | `SimGUITextures.render(GuiGraphicsExtractor,int,int,Color)` | 方法体仍是空壳（`;`） | 带颜色的贴图染色重绘（`drawColoredTexture`）不绘制 | **非本次引入**：26.3 的 `drawColoredTexture` 需要 `TextureSetup` 首参，Color 版本无对应；1.21.11 阶段已降级，本次只把形参类型跟上 | ⚠️ 需按 `TextureSetup.singleTexture(view,sampler)` 重写 |
| 4 | `KeyWidget` 的图标染色 | `RenderSystem.setShaderColor` 三处早已注释 | 键帽图标在绑定/未绑定时的棕色/深棕色染色 | **非本次引入**（1.21.11 阶段已降级） | ⚠️ 需 RenderPipeline 的 color 位或 `blit(..., color)` 重载 |

> 只有 **#1 和 #2** 是本次新产生的降级；#3 #4 是既有降级，本次仅随类型改名一起带过。

---

## 五、跳过文件（含 `foundry.veil`，**整文件未动**）与留给 Veil 线的跨文件耦合

### 5.1 未动的 Veil 文件（59 处 / 13 文件）

| 处数 | 文件（相对 `src`） |
|---|---|
| 15 | `main\java\…\content\entities\diagram\screen\DiagramScreen.java` |
| 8 | `main\java\…\content\blocks\redstone\linked_typewriter\screen\LinkedTypewriterScreen.java` |
| 6 | `main\java\…\content\blocks\nameplate\NameplateScreen.java` |
| 6 | `main\java\…\registrate\simulated_tab\SimulatedCreativeTab.java` |
| 4 | `main\java\…\content\entities\diagram\screen\DiagramStickyNote.java` |
| 3 | `main\java\…\content\blocks\altitude_sensor\AltitudeSensorScreen.java` |
| 3 | `main\java\…\content\blocks\redstone\linked_typewriter\screen\EntryModifierScreen.java` |
| 3 | `main\java\…\content\blocks\redstone\modulating_receiver\ModulatingLinkedReceiverScreen.java` |
| 3 | `excluded-wip\LinkedTypewriterItemBindHandler.java` |
| 2 | `main\java\…\content\blocks\physics_assembler\PhysicsAssemblerGUIHandler.java` |
| 2 | `main\java\…\content\blocks\steering_wheel\SteeringWheelHandler.java` |
| 2 | `main\java\…\content\blocks\throttle_lever\ThrottleLeverHandler.java` |
| 2 | `main\java\…\events\SimulatedCommonClientEvents.java` |

> `AltitudeSensorScreen` / `NameplateScreen` 另被 `build.gradle` 的 `compileJava` exclude（整屏已削减），改不改都不影响编译，但仍算 Veil 线。

### 5.2 ⚠ 跨文件耦合：Veil 线收尾时必须一起改的调用点

本线把**公共方法签名**改成 Extractor 后，下列 **Veil 文件里的调用点/覆写**会类型不匹配，必须由 Veil 线同步：

| 被本线改了签名的方法 | 在哪被 Veil 文件调用/覆写 |
|---|---|
| `SimGUITextures.render(GuiGraphicsExtractor,…)` ×3 | `DiagramScreen`、`DiagramStickyNote`、`AltitudeSensorScreen`、`PhysicsAssemblerGUIHandler`、`EntryModifierScreen`、`ModulatingLinkedReceiverScreen`、`LinkedTypewriterScreen`（都是 `SimGUITextures.XXX.render(guiGraphics,…)`） |
| `SimIcons.render(GuiGraphicsExtractor,int,int)` | `LinkedTypewriterScreen`、`KeyEditorScreen`（后者已改） |
| `KeyEditorScreen.render/renderBG` 系列 | `LinkedTypewriterScreen`（`this.keyEditorScreen.render(guiGraphics,…)`、`.renderBG(...)`） |
| `DiagramForceGroupToggle.renderTab(GuiGraphicsExtractor,…)` | `DiagramScreen` |
| `DiagramButton.extractWidgetRenderState` 的 tooltip（见第四节 #1） | `DiagramScreen.renderTooltip` |
| `HoldInteractionManager.renderOverlay(GuiGraphicsExtractor,…)` | `SimulatedCommonClientEvents.renderOverlays(GuiGraphics,…)`（第 139/143 行） |
| `BlockHoldInteraction.renderOverlay(GuiGraphicsExtractor,…)` | 子类覆写：`ThrottleLeverHandler`、`SteeringWheelHandler`、`PhysicsAssemblerGUIHandler`（都是 `public void renderOverlay(final GuiGraphics …)`） |
| `KeyWidget.render(GuiGraphicsExtractor,int,int,int,int,float,boolean)` | `LinkedTypewriterScreen` |
| `physics_staff.GuiGraphicsMixin` 目标类换掉 | `simulated.mixins.json` **没有**登记该类（只有 `.bak-r304/r307` 里的旧版本登记过）⇒ 无运行期影响 |

### 5.3 ⚠ 与本线无关、但同一个文件里仍是坏的（**请 ponder/Veil 线接手**）

`mixin\ponder\PonderSceneMixin.java` 的 `@Redirect`：

```java
@Redirect(remap=false, method="renderScene",
          at=@At(value="INVOKE", target="Lnet/createmod/ponder/foundation/PonderScene$SceneCamera;set(FF)V"))
```

- target 里 `Lnet/createmod/...` 是 **1.21.1 的旧包名**（现在是 `com.zurrtum.create.client.ponder...`），
- 且 `PonderScene.SceneCamera` / `PonderScene.SceneTransform` 在 26.3 的 Create-Fly 里**已不存在**（javap 无此嵌套类）。
- 本线只把注入器形参的 `GuiGraphics` 改成了 `GuiGraphicsExtractor`；**这个 `@Redirect` 依然会在 mixin 应用期报错**（该类已登记在 `simulated.mixins.json` 的 client 列表里）。
- 后果：ponder 相机跟随的 override 本来是死代码；现在需要整条重写或直接删掉该 `@Redirect`（属 ponder 族，不属本族）。

---

## 六、未做 / 边界

- **未编译**（任务书要求）。本文件的正确性依据是 javap 的 26.3 + Create-Fly 26.3 签名，不是编译器。
- 未改 `src\stub\java`（它的 GuiGraphics 计数本来就是 0）。
- 未改 `.java.bak-guigraphics2` 备份；它们不参与 Gradle 编译。
- 未改 `build.gradle`（无需新 exclude：`renderWidget` 没有残留，physics_staff mixin 本来就未登记）。
- `excluded-wip` 里的 `LinkedTypewriterItemBindHandler.java` 含 Veil import ⇒ 跳过（3 处）。
