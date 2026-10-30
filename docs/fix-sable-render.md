# Sable 26.3 —— 渲染栈移植（降级清单 + 映射表）

> 范围：**只动 `common/` 与 `fabric/`**，`neoforge/` 一字未改。**未编译**（按约定由主控统一编）。
> 每一次「改不动」都写成了源码里的 `// PORT(26.3): not implemented — …`，没有伪造任何 26.3 类。
>
> 取证方式：`javap` 直接读 `versions\26.3\26.3.jar`（26.3 未混淆），不依赖 1.21.11 的记忆。
> 工作脚本留在 `work\sable-26\port26\`（`_famsites.py` 抽站点、`apply_*.py` 落地、`verify_render.py` 验收）。

---

## 1. 验收计数（族残留）

脚本：`work\sable-26\port26\verify_render.py`（去掉注释与字符串后统计真实使用）

| 族 | 改前（compile-3.log 去重后） | 改后 | 说明 |
|---|---|---|---|
| `MultiBufferSource` | 35 | **0**（仅注释） | 整类在 26.3 删除，无替代 |
| `ShaderInstance` | 37 | **0**（仅注释） | 换 `ShaderManager` 后无「拿当前 shader 写 uniform」入口 |
| `LightTexture` | 28 | **0**（仅注释） | 静态辅助 → `LightCoordsUtil` / `Lightmap` |
| `getMainCamera()` | 38 | **0** | → `gameRenderer.mainCamera()` |
| `getTimer()` | 24 | **0** | → `getDeltaTracker()` |
| `getNormal()` | 22 | **0** | → `Direction.getUnitVec3i()` |
| `toLong()` / `asLong(int,int)` | 24 + 14 | **0** | → `ChunkPos.pack()` |
| `Uniform` | 22 | **0** | `com.mojang.blaze3d.shaders` 整包删除 |
| `RenderType`（剩余） | 37 | **0 处编译错误**（见 §5） | 换包 + `RenderTypes`/`ChunkSectionLayer` |
| `BakedQuad` | 14 | **0** | 换包 + record 访问器重写 |
| `BlockAndTintGetter` | 12 | **0** | 换包 → `net.minecraft.client.renderer.block` |
| `ImGui` | 26 | **0** | 面板降级为空 |
| `getPosition()`（Camera） | 41 | **0** | → `Camera.position()`，`SubLevelCamera` 重写 |

规模：**69 个文件**（每个都有 `.bak-render` 原件），删除 1,503 行 / 新增 571 行。

---

## 2. 换包（同一语义，只是搬家）

| 1.21.1 | 26.3 | 落地点 |
|---|---|---|
| `net.minecraft.client.renderer.RenderType` | `…renderer.rendertype.RenderType` | 13 文件（早已批量改过，本次补齐） |
| `…renderer.block.model.BakedQuad` | `…client.resources.model.geometry.BakedQuad` | `SubLevelVertexConsumer`、`SubLevelTextureCache`、`SubLevelMeshBuilder` |
| `net.minecraft.world.level.BlockAndTintGetter` | `net.minecraft.client.renderer.block.BlockAndTintGetter` | 7 文件（AO/粒子/方块实体/网格构建） |
| `com.mojang.blaze3d.vertex.VertexFormat` | `com.mojang.renderpearl.api.vertex.VertexFormat` | `SimpleCulledRenderRegion`、`WaterOcclusionRenderRegion` |
| （新）`net.minecraft.client.renderer.chunk.ChunkSectionLayer` | 替代 `RenderType.chunkBufferLayers()` 的「3 层」概念 | `FancySubLevelSectionCompiler` |

---

## 3. 换等价（签名改名，行为一致）

| 1.21.1 | 26.3 | 依据 |
|---|---|---|
| `Camera.getPosition()` | `Camera.position()` | javap：`public Vec3 position()` |
| `Camera.getBlockPosition()` | `Camera.blockPosition()` | 同上 |
| `Camera.getXRot()/getYRot()` | `Camera.xRot()/yRot()` | 同上 |
| `Camera.getEntity()` | `Camera.entity()` | 同上 |
| `Camera.getLookVector()/getUpVector()/getLeftVector()` | `forwardVector()/upVector()/leftVector()`，返回 **`Vector3fc`（只读）** | `SubLevelCamera` 改为自持三个 `Vector3f` 并覆盖访问器 |
| `Camera.getPartialTickTime()` | **删除**（26.3 无此方法） | `SubLevelCamera` 去掉该覆盖 |
| `Minecraft.gameRenderer.getMainCamera()` | `gameRenderer.mainCamera()` | javap：`public Camera mainCamera()` |
| `Minecraft.getTimer()` | `Minecraft.getDeltaTracker()` | `getGameTimeDeltaPartialTick(boolean)` 仍在 `DeltaTracker` 上 |
| `Direction.getNormal()` | `Direction.getUnitVec3i()` | javap：`getUnitVec3i()`，字段 `normal` 已私有 |
| `ChunkPos.toLong()` / `ChunkPos.asLong(x,z)` | `ChunkPos.pack()` / `ChunkPos.pack(x,z)` | javap：`public long pack()` + `static long pack(int,int)` |
| `BlockPos.getCenter()` | `Vec3.atCenterOf(pos)` | `getCenter()` 已从 `BlockPos` 移除 |
| `PoseStack.mulPose(Quaternionf)` | `poseStack.mulPose(new Matrix4f().rotation(q))` | 重载只剩 `mulPose(Matrix4fc)` / `mulPose(Transformation)` |
| `LightTexture.pack/block/sky/FULL_BRIGHT` | `LightCoordsUtil.pack/block/sky/FULL_BRIGHT` | javap：`net.minecraft.util.LightCoordsUtil`，方法名一一对应 |
| `LightTexture.getBrightness(DimensionType,int)` | `Lightmap.getBrightness(DimensionType,int)` | javap：`net.minecraft.client.renderer.Lightmap` |
| `BakedQuad.getVertices()[i*8+4/5]` 取 UV | `BakedQuad.packedUV(i)` 解包（低 32 位 u / 高 32 位 v） | `BakedQuad` 已改为 record，见 `SubLevelTextureCache` |
| `VertexConsumer.putBulkData(Pose,BakedQuad,float[],…)` | `VertexConsumer.putBakedQuad(Pose,BakedQuad,QuadInstance)` | 见 `SubLevelVertexConsumer` |
| `BlockAndTintGetter.getShade(Direction, boolean)` | `BlockAndTintGetter.cardinalLighting()` → `CardinalLighting.byFace(Direction)` | 26.3 的方向性明暗改成 record；`SingleBlockSubLevelWrapper` 已补 `cardinalLighting()` |
| `LevelReader.getMaxLightLevel()` | 常量 `15` | 该类方法在 26.3 删除（`SingleBlockSubLevelWrapper`） |
| `LevelHeightAccessor.getMinBuildHeight()` | `getMinY()` | 同上；另有 `getMaxBuildHeight()` → `getMaxY()` |
| `VertexConsumer` 新增抽象方法 | `setColor(int)` / `setUv3(float,float)` / `setLineWidth(float)` | 纯委托包装类必须补实现（`SubLevelVertexConsumer`） |

---

## 4. 降级清单（**逐条：文件 + 方法 + 丢了什么视觉**）

> 统一约定：方法签名/调用关系保留，方法体不画；注入类保留注解并加 **`require = 0`**
> （26.3 目标方法不存在时**只告警、不让游戏崩**）。

### 4.1 子维度地形本体（最重的一条）

| 文件 | 方法 | 丢什么 |
|---|---|---|
| `sublevel/render/dispatcher/VanillaSubLevelRenderDispatcher.java` | `renderSectionLayer(...)`（并删掉 `setupDynamicEffects`） | **子维度 chunked 地形整体不绘制**。原逻辑：改 `FOG_SHAPE`、写 `SableEnableNormalLighting / SableEnableSkyLightShadows / SableSkyLightScale` 三个 uniform、逐子维度调 `renderChunkedSubLevel` 用 VertexBuffer 画 |
| 同上 | `renderAfterSections(...)` | **单方块子维度不绘制**。原用 `Tesselator.begin(QUADS, BLOCK)` 收集几何 + `layer.setupRenderState()/draw(meshData)` |
| `sublevel/render/vanilla/VanillaChunkedSubLevelRenderData.java` | `renderChunkedSubLevel(...)` | 子维度地形的**雾色 / 天光缩放 / 区块偏移 uniform** 与逐 section 的 `VertexBuffer.draw()` |

> 这三条是同一件事：26.3 把「立即模式 + VertexBuffer」换成「extract → submit-node」，
> Sable 的自建渲染器没有可机械迁移的等价物。**结论：26.3 下子维度地形不可见。**

### 4.2 实体 / 方块实体 / 阴影

| 文件 | 方法 | 丢什么 |
|---|---|---|
| `mixinhelpers/sublevel_render/vanilla/VanillaSubLevelBlockEntityRenderer.java` | `renderSingleBE(...)` | **子维度内方块实体渲染**（箱子/熔炉/告示牌模型与文字）+ **方块破坏裂纹叠加**（`SheetedDecalTextureGenerator` + `VertexMultiConsumer`） |
| `mixin/sublevel_render/block_entity_render/LevelRendererMixin.java` | `sable$renderBlockEntities(...)` / `sable$preRenderBEs(...)` | 子维度方块实体的**注入钩子**（去 `MultiBufferSource`/`LightTexture` 参数，`require = 0`） |
| `mixin/entity/entity_rendering/LevelRendererMixin.java` | `renderEntityOnSubLevel(...)` / `renderEntity(...)` | 实体在子维度上的**位置变换与绕点旋转**（`EntityRenderDispatcher.render` 已改为 `extractEntity`+`submit`） |
| `mixin/entity/entity_rotations_and_riding/EntityRenderDispatcherMixin.java` | `sable$rotateEntity` / `sable$popPose1` / `sable$popPose2` | **骑乘/乘坐实体的朝向随子维度旋转** |
| `mixin/entity/entity_rendering/shadows/EntityRenderDispatcherMixin.java` | `sable$renderShadowsOnSubLevels(...)` | **子维度上的实体阴影**（`renderShadow` 已删除） |
| `mixin/respawn_point/sleeping/LivingEntityRendererMixin.java` | `sable$setupRotations(...)` | 在床上睡觉的实体**朝向随子维度** |
| `mixin/conduit/ConduitRendererMixin.java` | `sable$reorientEye(...)` | **导管「眼睛」朝向修正** |

### 4.3 调试 / 线框 / Gizmo

| 文件 | 方法 | 丢什么 |
|---|---|---|
| `mixin/debug_render/DebugRendererMixin.java` | 整个 `@Overwrite renderFilledBox` **删除** | 子维度内**所有调试方块盒**（F3+B 碰撞箱、方块事件、蜂巢/袭击 debug）的朝向修正 |
| `mixin/debug_render/LevelRendererMixin.java` | 整条注入**删除** | **子维度包围盒线框**、子维度原点十字框、**快照插值包围盒（青色）线框** |
| `mixinhelpers/loaded_chunk_debug/SableChunkDebugRenderer.java` | `render(...)` | `DEBUG_DRAW_LOADED_CHUNKS` 的全部效果：已加载区块柱状线框、所在 chunk 黄框、分层高度蓝框 |
| `mixin/loaded_chunk_debug/ChunkBorderRendererMixin.java` | `render(...)` | 同上（取消原版 ChunkBorder 的入口） |
| `debug/SableClientGizmoHandler.java` | `onRenderStage(...)` / `updateMouseDir(...)` | 子维度 gizmo 的**手柄盒**；鼠标射线改用单位投影矩阵 ⇒ **拾取方向不再准确** |

### 4.4 着色器 / uniform / 后处理

| 文件 | 方法 | 丢什么 |
|---|---|---|
| `render/sky_light_shadow/SableSkyLightShadows.java` | `bindShadowMapTexture(...)` | **天空光阴影**的 uniform 与深度贴图绑定 ⇒ 子维度投下的软阴影消失（`renderShadowMap` 体仍依赖 Veil FBO） |
| `render/water_occlusion/WaterOcclusionRenderer.java` | `setupTranslucentShader(...)` | **水中遮挡**的 `ENABLE`/`ScreenSize` uniform 与两张深度采样 |
| `render/region/SimpleCulledRenderRegion.java` | `render/build/free` | 水遮挡的**深度预渲染几何**（`Tesselator`+`VertexBuffer` 全删）；保留 origin 纯数学 |
| `mixin/sublevel_render/impl/vanilla/water_occlusion/LevelRendererMixin.java` | 两条注入**删除** | 水遮挡后处理的**挂载点**（`renderLevel` / `renderSectionLayer` 均不存在） |
| `mixin/sublevel_render/impl/vanilla/LevelRendererMixin.java` | `sable$renderSubLevels` / `sable$renderSubLevelLayers` | **Veil 分层 RenderType** 下子维度的逐层渲染（`layer.setupRenderState/shader.apply` 全删） |
| `compatibility/SableIrisCompat.java` | 整类空壳 | Iris 光影下的**法线矩阵修正** |
| `mixin/compatibility/iris/ExtendedShaderMixin.java` | 整类空 mixin | `ExtendedShader` 的 **model-view 逆矩阵 / 法线矩阵重算** |
| `mixin/config/GameRendererAccessor.java` + `SableClientConfig.java` | 访问器删除 + 调用点注释 | 改配置时的 **shader 热重载**（需重进世界） |
| `sublevel/render/dispatcher/SubLevelRenderDispatcher.java` | 接口方法去 `ShaderInstance` 参数 | 契约变化：调用方不再传「当前 shader」 |
| `sublevel/render/dispatcher/FancySubLevelRenderDispatcher.java` | 整类**空壳** | **Fancy 渲染器**（StagingBuffer + 自建 VAO + 动态 UBO/SSBO）。注：`SelectedRenderer` 只有 `VANILLA`/`SODIUM_REACHAROUND`，本类在 26.3 构建里**没有实例化点**（原本就是未启用路径） |

### 4.5 网格构建 / 单方块 / 调试 UI

| 文件 | 方法 | 丢什么 |
|---|---|---|
| `sublevel/render/fancy/SubLevelMeshBuilder.java` | `compile(...)`、`isAxisAligned(...)` | Fancy 的**逐方块六面打包**（`BakedModel.getQuads` + packed int 面数据）；保留 `Results`/`QuadMesh` 供上层编译 |
| `platform/SableSubLevelRenderPlatform.java` + `fabric/…/SableSubLevelRenderPlatformImpl.java` | 删 `tesselateBlock` / `getRenderLayers` | 单方块子维度的**模型细分与 render layer 推导**（`BakedModel`/`ItemBlockRenderTypes` 均删） |
| `sublevel/render/vanilla/VanillaSingleSubLevelRenderData.java` | `renderSingleBlock(...)` | **单方块子维度的渲染** |
| `render/dynamic_shade/SubLevelVertexConsumer.java` | `putBulkData` → `putBakedQuad` | dynamic_shade 的「不参与着色的面强制竖直法线」特判（26.3 的 `BakedQuad` 无 `isShade()`） |
| `render/dynamic_biome/DynamicBiomeTintRenderTypes.java` | 整类空壳 | 无（原本就是注释掉的实验代码，无人引用） |
| `sublevel/storage/debug/SubLevelContainerInspector.java` | `renderComponents()` | **子维度容器检查器 ImGui 面板**（占用热力图）—— 无 imgui-mc 依赖 |

---

## 5. 需要主控知道的遗留（**不属于我这 13 个族**）

1. **fancy 子树还有 4 个非本族错误**（`GlStateManager` / `Program` 都已从 26.3 删除）：
   `sublevel/render/fancy/BucketRenderBuffer.java`、
   `sublevel/render/fancy/FancySubLevelCommandBuilder.java`、
   `sublevel/render/staging/DSAStagingBuffer.java`、
   `mixin/sublevel_render/fancy/ProgramMixin.java`（`@Mixin(com.mojang.blaze3d.shaders.Program.class)` 目标类不存在）。
   这 4 个文件现在**只被已降级的 Fancy 路径引用**，两种收尾都可以：
   ① 各自降级为空壳；② 在 `build.gradle` 里把 fancy 子树 `exclude` 掉（同时从 mixin json 摘掉 `ProgramMixin`）。
2. **`RenderType` 的「换等价」只做到可编译**：26.3 的 `RenderType` 变成「一份 `RenderSetup` + pipeline」，
   静态工厂迁到 `net.minecraft.client.renderer.rendertype.RenderTypes`（`RenderTypes.lines()`、
   `RenderTypes.translucentMovingBlock()` …）。代码里凡是要「按 RenderType 取 chunk 层」的地方，
   26.3 的正确类型是 `ChunkSectionLayer`（`SOLID/CUTOUT/TRANSLUCENT`，`byTransparency(...)`）。
   本次只把 `chunkBufferLayers()` 换成 `ChunkSectionLayer.values().length`，**没有做 RenderType→ChunkSectionLayer 的语义迁移**
   （那属于 §4.1 的重写，不是机械替换）。
3. **`require = 0` 的注入点**（§4.2/4.3 里列的那些）：编译通过，但运行期会打
   `Cannot locate method / injection point` 警告。**这是有意的** —— 比整段删掉留证据强，
   也比默认 `require = 1` 直接崩游戏强。真正的重挂要等 26.3 的 submit-node 模型吃透。
4. **Veil 线已完成（R344，import `foundry.veil` 80 → 0）**，我的改动与之有交叠（`SableSkyLightShadows`、
   `FancySubLevelRenderDispatcher`、`WaterOcclusionRenderer` 等）。若后续 rebase，**以本文件的降级语义为准**，
   Veil 垫片只提供「类存在」，不提供「能画」。
5. **没有做的事**：没有重写任何渲染管线去对接 `SubmitNodeCollector` / `RenderState`。
   那是「让子维度重新可见」的唯一正路，工作量远大于本轮（需要按 26.3 的 extract 阶段重新组织
   子维度几何与材质），不在「编译通过 + 逻辑保留」的目标内。

---

## 6. 运行期风险提示（编译 0 错 ≠ 能跑）

- §4.1 的两处 no-op 意味着**子维度看不见**，但**不会崩**。
- `FancySubLevelRenderDispatcher.createRenderData` 现在抛 `UnsupportedOperationException`；因该类
  无实例化点，正常流程不会触达。
- `SableSubLevelRenderPlatform.INSTANCE` 现在只剩 `tryAddFlywheelVisual`（原本就是 no-op），
  接口缩窄后 fabric 实现同步缩窄，`SablePlatformUtil.load` 反射按接口方法名匹配，不会因方法减少而失败。
- 所有降级点都用 `// PORT(26.3):` 标注，便于后续按 `grep -rn "PORT(26.3)"` 逐一回收。
