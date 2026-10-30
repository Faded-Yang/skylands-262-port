# Sable 26.3 —— 渲染线第二轮（R347）：残余渲染族清零 + 降级清单

> 范围：**只动 `common/` 与 `fabric/`**；`neoforge/`、`_dropped*/` 一个字节没动（期间误建的 3 个 `.bak-render2` 已删除）。
> 分支边界（R346 台账）：渲染线独占 `sublevel/render/**`、`render/**`、`mixin/sublevel_render/**`、
> `mixin/dynamic_directional_shading/**`、`debug/**`、`compat/veil/**`；其余目录归核心线。
>
> 编译口径：`port26\compile-*.log` 里 javac 尾行的 `N errors`（日志每行错误会出现两遍，脚本按
> `(file,line,msg)` 去重后得 unique 数）。
> 本轮脚本：`an_r.py`（去重+分类）、`dom.py`（按域统计）、`det.py`（按文件看详情）、`jr.py`（javap 直读 26.3.jar）。

---

## 1. 数字

| 口径 | 起点（compile-5.log） | 我的终点（compile-r3.log） | 复验（compile-r4.log，核心线又修了一批） |
|---|---|---|---|
| javac 尾行总错误 | **569** | **297** | **273** |
| 去重 unique 总数 | 551 | 291 | 267 |
| **渲染域（我的域）** | **88** | **0** | **0** |
| 非渲染（核心线） | 463 | 291 | 267 |

渲染域逐轮收敛：

| 日志 | unique | 我的域 | 分域明细 |
|---|---|---|---|
| compile-5（起点） | 551 | **88** | sublevel/render 57 · debug 14 · dynamic_directional_shading 10 · render 5 · mixin/sublevel_render 2 |
| compile-r1 | 484 | 71 | sublevel/render 43 · debug 14 · dds 7 · render 5 · mixin/sublevel_render 2 |
| compile-r2 | 341 | 23 | debug 14 · dds 7 · sublevel/render 1 · mixin/sublevel_render 1 |
| compile-r3 | 291 | **0** | — |

> 期间核心线同时在改非渲染族，所以「总错误 569→297」不全是本人的贡献；**渲染域的 88→0 是本轮成果**。

规模：**改 19 个 java + 改 1 个 mixin json + 删 2 个 mixin 类**；每个被改文件都有 `.bak-render2` 原件
（例外：`ModelBlockRendererMixin` 的原件是上轮留下的 `.bak-render`）。

---

## 2. 换包 / 换等价（机械替换，语义不变）

| 1.21.1 | 26.3 | 依据（javap 26.3.jar） | 落地点 |
|---|---|---|---|
| `client.renderer.chunk.RenderChunkRegion` | `client.renderer.chunk.RenderSectionRegion` | `RenderSectionRegion implements BlockAndTintGetter`，字段 `private final ClientLevel level` | 4 文件 9 处：`RenderChunkRegionMixin`(目标+shadow)、`SubLevelMeshBuilder`、`FancySubLevelTaskScheduler`、`fabric/…/SectionCompilerMixin` |
| `client.renderer.block.BlockRenderDispatcher` | **整类删除** | `client.renderer.block` 只剩 `BlockModelResolver` / `ModelBlockRenderer` / `BlockQuadOutput` / `BlockStateModelSet` … | 从 `SubLevelMeshBuilder`、`FancySubLevelSectionCompiler` 的字段/构造器里**整个参数删掉**（`compile()` 早已降级，该字段无使用点） |
| `RenderType`（`client.renderer.*` 通配 import） | `client.renderer.rendertype.RenderType` | 子包搬迁 | `SubLevelMeshBuilder` 3 处补 import |
| `SectionBufferBuilderPack.buffer(RenderType)` | `buffer(ChunkSectionLayer)` | `Map<ChunkSectionLayer, ByteBufferBuilder>` | `SubLevelMeshBuilder.getOrBeginQuadLayer` 换键类型 |
| `BlockEntityRenderer.shouldRenderOffScreen(E)` | `shouldRenderOffScreen()` | 26.3 无参 | `SubLevelMeshBuilder`、`VanillaSingleSubLevelRenderData` |
| `Minecraft.useAmbientOcclusion()` | `Minecraft.getInstance().options.ambientOcclusion().get()` | `Minecraft` 已无该静态方法；`Options.ambientOcclusion()` 返回 `OptionInstance<Boolean>` | `SubLevelMeshBuilder.getFaceAO` |
| `RenderSystem.enableDepthTest/depthMask/glBindBuffer/glDeleteBuffers` | `com.mojang.renderpearl.backend.opengl.GlStateManager._enableDepthTest/_depthMask/_glBindBuffer/_glDeleteBuffers` | GL 门面整类搬家且**方法名带下划线前缀** | `WaterOcclusionRenderer`、`BucketRenderBuffer`（6 处） |
| `client.renderer.FogRenderer` | `client.renderer.fog.FogRenderer` | 子包搬迁 | `mixin/water_occlusion/FogRendererMixin` |
| `Camera.getPosition()` / `getBlockPosition()` | `Camera.position()` / `blockPosition()` | javap 确认 | `WaterOcclusionRenderer`、`FancySubLevelRenderData`、`SableClientGizmoHandler` |
| `Minecraft.getMainRenderTarget()` | `Minecraft.gameRenderer.mainRenderTarget()` | `Minecraft` 无该 getter | `WaterOcclusionRenderer` |
| `LevelRenderer.getSectionRenderDispatcher()` | `LevelRenderer.sectionRenderDispatcher()` | javap 确认 | `VanillaSubLevelRenderDispatcher` |
| `Minecraft.setScreen(x)` / `Minecraft.screen` | `Minecraft.gui.setScreen(x)` / `Minecraft.gui.screen()` | `Minecraft` 已无该字段/方法；`Gui` 持有当前屏 | `SableClientGizmoHandler.start/stop` |
| `Screen.render(GuiGraphics,…)` | `Screen.extractRenderState(GuiGraphicsExtractor,…)` | `GuiGraphics` 整类改名 `GuiGraphicsExtractor` | `debug/GizmoScreen` |
| `mouseClicked(double,double,int)` / `mouseReleased(double,double,int)` / `mouseDragged(double,double,int,double,double)` | `mouseClicked(MouseButtonEvent,boolean)` / `mouseReleased(MouseButtonEvent)` / `mouseDragged(MouseButtonEvent,double,double)` | 事件对象化（`MouseButtonEvent.x()/y()`） | `debug/GizmoScreen` |
| `PoseStack.mulPose(Quaternionfc)` | `PoseStack.mulPose(Matrix4fc)`（需 `new Matrix4f().rotation(q)`） | 只剩 `mulPose(Matrix4fc)`/`mulPose(Transformation)` | `fabric/…/block_outline_render/LevelRendererMixin` |
| `RenderRegionCache.createRegion(Level, SectionPos)` | `createRegion(ClientLevel, long)` | 要 `SectionPos.asLong()` | `FancySubLevelRenderData` |
| `LevelHeightAccessor.getMinBuildHeight()` | `getMinY()` | R344 已确认，本轮补漏 | `SingleBlockSubLevelWrapper` |

---

## 3. 本轮新增降级（**逐条：文件 + 方法 + 丢了什么**）

> 统一约定：方法签名/调用关系保留，方法体不画；每条都带 `PORT(26.3)` 注释。
> **不伪造任何 26.3 类**。

| # | 文件 | 方法/成员 | 26.3 断点 | 丢什么 |
|---|---|---|---|---|
| 1 | `sublevel/render/vanilla/VanillaChunkedSubLevelRenderData.java` | `resize()` / `rebuild()` / `compileSections()` / `isSectionCompiled()` / `setDirty()` / `close()` / `getRenderSection()` 共 7 个方法改为 shell | `RenderSection` 构造器改 `(SectionRenderDispatcher,int,long)`；`isDirty/setDirty/getCompiled/setCompiled/releaseBuffers/updateGlobalBlockEntities/getOrigin/getBuffer` 全删；section 几何改 `CompiledSectionMesh`/`SectionMesh`；`Minecraft.getProfiler()` 删除 | **子维度 section 的脏标记、重编译调度、越界释放、section→方块实体索引**全部消失（地形本就不绘制，见 §4.1 第一轮 R344 的 `renderChunkedSubLevel`）。`isSectionCompiled` 恒 true，避免调用方无意义重试 |
| 2 | `sublevel/render/dispatcher/ReachAroundSubLevelRenderDispatcher.java` | `createRenderData()` / `preRenderChunks()` | `SectionRenderDispatcher` 构造器改 `(TracingExecutor, RenderBuffers, SectionCompiler, Consumer<RenderSection>)`；`setLevel/bufferPool/blockUntilClear/setCamera/uploadAllPendingUploads` 全删；`Minecraft.renderBuffers()/getBlockRenderer()` 删除 | ReachAround（Sodium 直通）**不再自建 SectionRenderDispatcher**，改复用 `LevelRenderer.sectionRenderDispatcher()`。**不新增视觉损失**（该渲染器绘制早已为空） |
| 3 | `sublevel/render/dispatcher/VanillaSubLevelRenderDispatcher.java` | `renderBlockEntities()` 的 `VanillaChunkedSubLevelRenderData` 分支 | `SectionRenderDispatcher.RenderSection.getCompiled()` 删除；`BlockEntityRenderer.renderBlockEntities(List,PoseStack,…)` 不存在（改 createRenderState/extract/submit） | **子维度 section 内方块实体的批量绘制** —— 与 R344 §4.2 同一处损失，不新增 |
| 4 | `sublevel/render/vanilla/VanillaSingleSubLevelRenderData.java` | `removeBlockEntity()` | `LevelRenderer.updateGlobalBlockEntities(Set,Set)` 删除（26.3 无「全局方块实体」注册表） | 单方块子维度方块实体的**全局列表登记/注销**（该方块实体本身已因 `renderSingleBlock` 降级而不绘制） |
| 5 | `render/water_occlusion/WaterOcclusionRenderer.java` | `preRenderTranslucent()` 里的 `RenderSystem.setShaderColor(...)` | 无全局 shader 颜色槽位 | 水遮挡预渲染的着色重置（预渲染本就在 `SimpleCulledRenderRegion` 降级为空） |
| 6 | `mixin/dynamic_directional_shading/ModelBlockRendererMixin.java` | 整类清空（保留 `@Mixin`） | 目标方法 `putQuadData` / `renderModelFaceFlat` 不存在；`@Shadow CACHE`(ThreadLocal) 删除；`BlockAndTintGetter.getShade` 删除 | **子维度「动态方向着色」失效**：子维度方块面的明暗不再被强制为 1.0，也不再把面法线强制竖直；配置项 `SUB_LEVEL_DYNAMIC_SHADING` 从此无效果 |
| 7 | `fabric/…/dynamic_directional_shading/SectionCompilerMixin.java` | 整类清空（保留 `@Mixin`） | `ModelBlockRenderer.Cache` 删除；`SectionCompiler.compile` 形参改 `RenderSectionRegion` | 配合 #6：子维度编译期的「onSubLevel」标志置位消失（同一处损失） |
| 8 | `mixin/dynamic_directional_shading/AmbientOcclusionFaceMixin.java` | **删除文件 + 摘 `sable.mixins.json` 条目** | 目标 `ModelBlockRenderer.AmbientOcclusionFace` 整类删除 | 子维度 AO 面的方向性明暗抑制（同一处损失） |
| 9 | `mixin/dynamic_directional_shading/ModelBlockRendererCacheMixin.java` | **删除文件 + 摘 `sable.mixins.json` 条目** | 目标 `ModelBlockRenderer.Cache` 整类删除 | `sable$onSubLevel` 标志的载体消失（同一处损失） |
| 10 | `mixin/sublevel_render/BlockEntityRenderDispatcherMixin.java` | `@Redirect setupAndRender` / `@ModifyArg render` 两条注入删除（保留 `sable$cameraPos` 字段与 `BlockEntityRenderDispatcherExtension` 实现） | 目标方法 `setupAndRender` / `render` 均删除（改 `prepare`→`tryExtractRenderState`→`submit`）；`LevelRenderer.getLightColor` 搬到 `LightCoordsUtil.getLightCoords` | **子维度方块实体的光色缩放**（`SubLevel.scaleLightColor`）与**「按 Sable 相机位置判断可见性」**失效（与 §4.2 同一处损失） |

**合计：新增降级 10 条 / 涉及 8 个文件（2 个删除）**。其中 #3/#4/#10 是 R344 §4.2 同一处视觉损失的
连带清理，#1/#2 是已在 §4.1 判死的地形渲染的连带清理；**真正新增的视觉损失只有一条：#6/#7/#8/#9 的
「子维度动态方向着色」**（子维度方块面明暗不再被强制平坦/竖直法线）。

---

## 4. 交接给核心线（**渲染味道但不属于渲染域目录**，按 R346 边界未动）

> 这四个文件在 `util/`、`mixin/particle/`、`mixin/entity/`、`mixin/camera/` 下，属核心线；
> 修法都是机械替换，直接照 §2 表即可。

| 文件 | 错误 | 改法 |
|---|---|---|
| `util/SublevelRenderOffsetHelper.java` | 2 | `mainCamera().getPosition()`→`.position()`；`ps.mulPose(new Quaternionf(o))`→`ps.mulPose(new Matrix4f().rotation(new Quaternionf(o)))` |
| `mixin/particle/TerrainParticleMixin.java` | 2 | `LevelRenderer.getLightColor`→`LightCoordsUtil.getLightCoords`；**且 26.3 的 `TerrainParticle` 已无 `getLightColor` 方法**，`@Redirect` 目标失效 ⇒ 建议整类降级为空 mixin（丢：子维度地形粒子的光色缩放） |
| `mixin/entity/entities_stick_sublevels/EntityRenderDispatcherMixin.java` | 5 | `mulPose(Quaternionf)` 包裹；`LevelRenderer.renderLineBox(...)` 已删除（26.3 线框改 gizmo/`ShapeRenderer`）⇒ 三条 debug 线框要么降级要么换 API；`Camera.getPosition()`→`position()` |
| `mixin/camera/camera_rotation/GuiMixin.java` | 3 | `camera.getEntity()`→`camera.entity()` |
| `mixin/camera/camera_rotation/CompassItemPropertyFunctionMixin.java` | 2 | 目标类 `client.renderer.item.CompassItemPropertyFunction` 26.3 已删（物品属性函数体系整体重构）⇒ 只能摘 json 条目 + 删类 |

---

## 5. 运行期风险（编译 0 错 ≠ 能跑）

1. **`sable.mixins.json` 已同步摘掉 2 条**（`AmbientOcclusionFaceMixin`、`ModelBlockRendererCacheMixin`），
   否则 `MixinApplyError` 会在启动时硬崩。
2. `ModelBlockRendererMixin` / `fabric SectionCompilerMixin` 现在是**空 mixin**（只有 `@Mixin`），
   加载不会报错，也不会做事。
3. `RenderChunkRegionMixin` 现在 shadow `RenderSectionRegion.level`（`private final ClientLevel`）——
   字段名与描述符都对得上 26.3。
4. `BlockEntityRenderDispatcherMixin` 仍实现 `BlockEntityRenderDispatcherExtension`，
   `VanillaSubLevelRenderDispatcher` 会调 `sable$setCameraPosition(...)` —— 现在只写字段，无消费者。
5. 所有降级点用 `grep -rn "PORT(26.3)"` 可回收。
