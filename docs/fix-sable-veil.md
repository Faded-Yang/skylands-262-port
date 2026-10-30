# Sable 26.3 —— 拔掉 `foundry.veil`（垫片方案）

> 族名：`veil-elimination`（Sable 侧）。做法与 Aeronautics 的 R342 完全一致：
> 在工程自己的包下重建垫片，全部 import 改指向垫片，**不再依赖 Veil 的 jar**。
>
> 承接：`docs\VEIL-ELIMINATION.md`（那是 **Aeronautics** 的 R342 记录，本次是 Sable）。
> 只动 `src\common\` 与 `src\fabric\`，**`neoforge/` 一个字节没碰**。

---

## 1. 结论数字

| 指标 | 值 |
|---|---|
| 原 `import foundry.veil` | **80 行 / 51 文件 / 28 个不同 FQN** |
| 现 `import foundry.veil`（common+fabric） | **0** ✅ |
| 垫片包 | `dev.ryanhcode.sable.compat.veil`（**37 个类**） |
| 其中**照抄 AerO 垫片** | **11 个**（6 个网络层 100% 照抄 + 5 个沿用骨架并补方法） |
| 其中**按 Veil jar 的 javap **新写** | **26 个** |
| 降级标注 `// PORT(26.3)`（垫片内） | **105 处 / 18 个类** |
| Sable 侧因 veil 改动的签名 | **1 处**（`SableSkyLightShadows.renderShadowMap` 去掉 `BufferSource` 参数） |
| **构建依赖也拔干净** | `veil-common` / `veil-fabric` / `fabric.mod.json` 的 `"veil"` 三条声明全部删除（见 §7.2） |
| 改前备份 | 51 个 `*.java.bak-sableveil` ＋ `fabric.mod.json.bak-sableveil` |

包名 **不与 Aeronautics 撞 FQN**：那边是 `dev.simulated_team.simulated.compat.veil`，
这边是 `dev.ryanhcode.sable.compat.veil`，两个 jar 可同时在场。

---

## 2. 符号清单（28 个 FQN → 落点 → 状态）

`import foundry.veil.X` 全部按 **`foundry.veil` → `dev.ryanhcode.sable.compat.veil` 逐字替换**
（包内子路径保持不变），因此映射是机械的、没有手写对照表。

| 原 FQN（省略 `foundry.veil.`） | 文件数 | 垫片类 | 状态 |
|---|---:|---|---|
| `api.network.handler.PacketContext` | 18 | `api/network/handler/PacketContext` | ✅ 真实（`level()`/`player()`） |
| `api.client.render.VeilRenderSystem` | 9 | `api/client/render/VeilRenderSystem` | ⚠ 部分降级（见 §4） |
| `api.network.VeilPacketManager` | 6 | `api/network/VeilPacketManager` | ✅ **完全非降级** |
| `api.client.render.CullFrustum` | 5 | `api/client/render/CullFrustum` | ✅ 真实（薄转发 `Frustum`） |
| `api.client.render.MatrixStack` | 4 | `api/client/render/MatrixStack` | ✅ 真实（包 `PoseStack`） |
| `api.client.render.VeilRenderBridge` | 4 | `api/client/render/VeilRenderBridge` | ✅ 只实现用到的 2 个 `create` |
| `api.client.render.shader.processor.ShaderPreProcessor` | 5 | `.../shader/processor/ShaderPreProcessor` | ⚠ `GlslTree`/`Context` 为占位类型 |
| `platform.VeilEventPlatform` | 2 | `platform/VeilEventPlatform` | ⛔ 4 个注册方法全 no-op |
| `Veil` | 2 | `compat/veil/Veil` | ✅ `platform().isModLoaded/isDevelopmentEnvironment` |
| `platform.registry.RegistrationProvider` | 2 | `platform/registry/RegistrationProvider` | ✅ 真实（`MappedRegistry`） |
| `platform.registry.RegistryObject` | 2 | `platform/registry/RegistryObject` | ✅ 真实 |
| `api.event.VeilRenderLevelStageEvent` | 2 | `api/event/VeilRenderLevelStageEvent` | ⛔ 事件永不触发 + 少 `BufferSource` 参数 |
| `api.compat.SodiumCompat` | 2 | `api/compat/SodiumCompat` | ✅ `isLoaded()` |
| `api.client.render.framebuffer.AdvancedFbo` | 2 | `.../framebuffer/AdvancedFbo` | ⛔ 无 GPU 资源（纯描述） |
| `api.client.render.shader.program.ShaderProgram` | 2 | `.../shader/program/ShaderProgram` | ⛔ 只产「无效程序」 |
| `api.client.render.vertex.VertexArray` | 2 | `.../vertex/VertexArray` | ⛔ 不调 GL |
| `api.client.editor.EditorManager` | 1 | `api/client/editor/EditorManager` | ⛔ 只当登记簿 |
| `api.client.render.rendertype.VeilRenderType` | 1 | `.../rendertype/VeilRenderType` | ⚠ 嵌套类改成**接口** |
| `api.client.render.VeilLevelPerspectiveRenderer` | 1 | `.../VeilLevelPerspectiveRenderer` | ⛔ `render` 空实现 |
| `api.client.render.shader.uniform.ShaderUniform` | 1 | `.../shader/uniform/ShaderUniform` | ⛔ 永不实例化 |
| `api.client.render.vertex.VertexArrayBuilder` | 1 | `.../vertex/VertexArrayBuilder` | ⛔ 只记参数 |
| `impl.client.render.dynamicbuffer.VanillaShaderCompiler` | 1 | `impl/.../VanillaShaderCompiler` | ⛔ 全 no-op |
| `api.client.render.shader.block.DynamicShaderBlock` | 1 | `.../shader/block/DynamicShaderBlock` | ⚠ CPU 侧真实现，无 GPU 上传 |
| `api.client.render.shader.block.ShaderBlock` | 1 | `.../shader/block/ShaderBlock` | ⚠ 同上 |
| `api.client.render.profiler.RenderProfilerCounter` | 1 | `.../profiler/RenderProfilerCounter` | ⛔ 纯常量 |
| `api.client.render.profiler.VeilRenderProfiler` | 1 | `.../profiler/VeilRenderProfiler` | ⛔ 全 no-op |
| `api.compat.IrisCompat` | 1 | `api/compat/IrisCompat` | ✅ `isLoaded()` |
| `api.client.editor.SingleWindowInspector` | 1 | `api/client/editor/SingleWindowInspector` | ⛔ 渲染为空 |

> 验收脚本看到的 28 个 FQN **全部落地**；`dev.ryanhcode.sable.compat.veil` 的
> 每个 import 都能解析到实际文件（89 条 import / 33 个 distintos，无法解析 = 0）。

---

## 3. 抄了哪些（复用 Aeronautics 垫片）

源目录：`work\aero-port\aeronautics-26\src\main\java\dev\simulated_team\simulated\compat\veil\`

**100% 照抄（只换包名）：6 个 —— 网络层整层**

| Aeronautics 文件 | Sable 落点 | 备注 |
|---|---|---|
| `VeilPacketManager.java` | `api/network/VeilPacketManager.java` | Veil→Fabric 映射表原样保留 |
| `FabricVeilPacketManager.java` | `api/network/FabricVeilPacketManager.java` | 同上 |
| `VeilClientSide.java` | `api/network/VeilClientSide.java` | 物理客户端隔离 |
| `handler/PacketContext.java` | `api/network/handler/PacketContext.java` | 已自带 `level()`，Sable 正好需要 |
| `handler/ClientPacketContext.java` | `api/network/handler/ClientPacketContext.java` | |
| `handler/ServerPacketContext.java` | `api/network/handler/ServerPacketContext.java` | |

网络层是这一轮**唯一完全不降级**的子系统：Sable 的 18 个包、5 个 `PacketSink` 类型全部原样工作。

**沿用骨架 + 按 Sable 调用面补方法：5 个**

| Aeronautics 文件 | 补了什么（为什么） |
|---|---|
| `render/MatrixStack.java` | 补 `clear()`：Sable `VanillaSubLevelRenderDispatcher:237` 每轮调；**26.3 的 `PoseStack` 已删 `clear()`**，改成 `while(!isEmpty()) popPose()` |
| `render/VeilLevelPerspectiveRenderer.java` | 补 `render(AdvancedFbo, Matrix4fc×2, Vector3dc, Quaternionfc, float, DeltaTracker, boolean)`（Aeronautics 零调用，Sable `SableSkyLightShadows:82` 要）＋ 把「恒 false」改成带状态标志 |
| `render/framebuffer/AdvancedFbo.java` | 补 `clear(r,g,b,a,depth,mask)`、`getClearMask()`、`getDepthTextureAttachment()`（`WaterOcclusionRenderer:114/160/161`） |
| `event/VeilEventPlatform.java` | 补 `onVeilRendererAvailable(Consumer<VeilRenderer>)` 与 `onVeilRenderLevelStage(Listener)`；`ShaderProcessorCallback` 的 registry 由 `Object` 收窄为 `ShaderProcessorRegistry`（Sable 要调 `.addPreprocessor(...)`） |
| `event/VeilRenderLevelStageEvent.java` | 补 `Listener` 函数接口（9 参，去掉 `BufferSource`） |

**没有搬的**：`color/Color`、`color/Colorc`、`util/CodecUtil`、`CodecReloadListener`、
`render/post/PostPipeline`、`render/post/PostProcessingManager`、`render/VeilRenderSystem`。
原因：Sable **一次都没 import 它们**（`import foundry.veil` 清单里没有），
少一个类就少一处版本风险。`VeilRenderSystem` 是重写的（Sable 要 11 个方法，
Aeronautics 只要 1 条链 `renderer().getPostProcessingManager()`）。

---

## 4. 新写的 26 个（按 Veil 4.5.0 jar 的 `javap` 补签名）

`javap -cp veil-fabric-1.21.1-4.5.0.jar` 逐个核对，不凭记忆：

```
Veil.java                                   platform/VeilPlatform.java
platform/registry/RegistrationProvider.java platform/registry/RegistryObject.java
api/compat/{SodiumCompat,IrisCompat}.java
api/client/render/{VeilRenderSystem,VeilRenderBridge,CullFrustum}.java
api/client/render/framebuffer/FramebufferManager.java
api/client/render/rendertype/VeilRenderType.java
api/client/render/profiler/{VeilRenderProfiler,RenderProfilerCounter}.java
api/client/render/shader/{ShaderManager,ShaderDefinitions}.java
api/client/render/shader/program/ShaderProgram.java
api/client/render/shader/uniform/ShaderUniform.java
api/client/render/shader/processor/ShaderPreProcessor.java
api/client/render/shader/block/{ShaderBlock,DynamicShaderBlock}.java
api/client/render/vertex/{VertexArray,VertexArrayBuilder}.java
api/client/editor/{Inspector,SingleWindowInspector,EditorManager}.java
impl/client/render/dynamicbuffer/VanillaShaderCompiler.java
```

其中 **3 个是「真实现」而不是空壳**（26.3 有等价能力）：

- `RegistrationProvider` / `RegistryObject` —— 用 26.3 的
  `new MappedRegistry<>(key, Lifecycle.stable())` + `register(ResourceKey, T, RegistrationInfo.BUILT_IN)`；
  两个自由注册表（`sable:force_groups`、`sable:physics_block_properties`）照常工作。
- `CullFrustum` —— 26.3 的 `Frustum` 公开了 `isVisible(AABB)` / `pointInFrustum` /
  `getCamX|Y|Z`，直接薄转发（球形剔除退化为外接盒，属更宽松的一侧）。
- `VeilRenderSystem.directStateAccessSupported()` —— 真查
  `GL.getCapabilities().OpenGL45 || GL_ARB_direct_state_access`（`StagingBuffer` 用它选 DSA/ARB）。

---

## 5. 降级清单（逐条：丢了什么）

### 5.1 功能级丢失（会被人看见的）

| # | 丢失的东西 | 根因 | 位置 |
|---|---|---|---|
| 1 | **子维度天空光阴影贴图不渲染** | 渲染阶段事件垫不出来（`BufferSource` 类已删除 + 无阶段钩子） | `SableSkyLightShadows.renderShadowMap` 保留但永不回调 |
| 2 | **调试 Gizmo 线框不绘制** | 同上（且 `DebugRenderer.renderFilledBox(...)` 在 26.3 已删除） | `SableClientGizmoHandler.onRenderStage` |
| 3 | **子维度占用图 ImGui 面板消失** | imgui-mc 不存在 ⇒ `hasImGui()` 恒 false、`EditorManager` 不渲染 | `SubLevelContainerInspector` |
| 4 | **水遮挡 close/far 深度缓冲无效果** | `AdvancedFbo` 不分配 GPU 资源 | `WaterOcclusionRenderer` |
| 5 | **Fancy 渲染路径整体关闭** | `ShaderManager.createDynamicProgram` 只返回「无效程序」 ⇒ `program.isValid()==false` 提前返回 | `FancySubLevelRenderDispatcher` |
| 6 | **4 个 GLSL 预处理器不生效** | `io.github.ocelot.glslprocessor` 不存在（且它们本来就已是直通） | `Sable*PreProcessor` / `FancySubLevelShaderProcessor` |
| 7 | **F3 剖析图里没有 `sublevel_render` 节点** | `VeilRenderProfiler` 全 no-op | `VanillaSubLevelRenderDispatcher` |
| 8 | **切设置后不再强制重建全世界的区块 mesh** | `LevelRenderer.allChanged()` 在 26.3 已删除 | `VeilRenderSystem.rebuildChunks()` |
| 9 | **`renderThreadExecutor()` 不再切线程** | 26.3 无公开的渲染线程执行器句柄 ⇒ 直接当前线程跑（两处调用都是 `free()`，安全） | `FancySubLevelSectionCompiler` / `RenderSectionMixin` |
| 10 | **顶点/索引数据永不进显存** | `VertexArray` 不调 GL | `FancySubLevelRenderDispatcher` 构造器 |
| 11 | **UBO/SSBO 永不绑定** | 26.3 无「按名字绑 shader 块」入口 | `SubLevelTextureCache`（`SableSprites` 块） |
| 12 | **精灵图集数据只在 CPU 侧打包** | 同上（`ShaderBlock` 保留全部 CPU 语义，只丢 `glBufferSubData`） | 同上 |
| 13 | **Veil 的 RenderType 包装/分层分支永不命中** | 嵌套类改成了接口 | `impl/vanilla/LevelRendererMixin.sable$renderSubLevelLayers` |
| 14 | **多个子维度 section 不再出现在 F3 计数** | 同 #7 | —— |

> #5 + #10 + #11 + #12 是**同一条链**（fancy 渲染器），#1/#2 同一条（阶段事件）。
> 也就是说实际「体感」丢失 = **3 条链路**：fancy 渲染器、阶段事件、ImGui 编辑器面板。

### 5.2 签名级改动

| 位置 | 改动 | 为什么 |
|---|---|---|
| `SableSkyLightShadows.renderShadowMap(...)` | **删掉 `MultiBufferSource.BufferSource` 参数**（连带删 import） | 该类在 26.3 **整个不存在**（`jar tf 26.3.jar \| grep MultiBufferSource` = 0），回调签名里没有任何类型能顶上；这也是 R342 对 Aeronautics 下的否定结论 |
| `VeilRenderType.RenderTypeWrapper/LayeredRenderType` | `class` → `interface` | 原类 `extends RenderType`；26.3 的 `RenderType` 已迁包并改构造，无法在外部继承。做成**接口**后 `renderType instanceof X` 才合法（两个不相关的类 javac 会判 `inconvertible types`） |
| `ShaderProgram.setDefaultUniforms` | 第一参 `VertexFormat.Mode` → `Object` | 26.3 的 `VertexFormat` 迁到 `com.mojang.renderpearl.api.vertex` 且**没有 `Mode`**（换成 `pipeline.PrimitiveTopology`）；本方法体为空，放宽成 `Object` 就不会和「渲染栈」那条线的重命名打架 |
| `VeilPacketManager.player/tracking/all` | 参数写死 `ServerPlayer`/`Entity`/`BlockEntity`（同 Aeronautics） | 与原 Veil 一致 |
| `VanillaShaderCompiler.reload/getActiveDynamicBuffers` | 参数 `Object` / `Collection<?>` | 原签名用 `ShaderInstance`（26.3 包路径属另一族），垫片刻意不耦合 |

### 5.3 行为级近似

- `CullFrustum.testSphere` 用**球的外接立方体**代替真球-平面判定（更宽松：可能多画，不会漏画）。
- `FramebufferManager.getFramebuffer(name)` 原实现只认资源包里声明的帧缓冲（**Sable 从来没写过声明文件**，
  1.21.11 轮也一样），所以原行为其实是返回 `null`；垫片改成**按名字惰性自建**一个无 GPU 资源的描述对象
  ——好处是 `SableSkyLightShadows.bindShadowMapTexture` 不会 NPE。
- `EditorManager.setEnabled(...)` 记录但恒 false。

---

## 6. 验证（未跑整体构建 —— 别的族还在修）

1. **`import foundry.veil` = 0**：python `re`，扫 `common/` + `fabric/` 全部 `.java`，
   正则 `^\s*import\s+(?:static\s+)?foundry\.veil` → 命中 **0**（改前 80）。
   残留的 `foundry.veil` 字面量 33 处**全部在垫片自己的 javadoc `{@code ...}` 里**（描述原 FQN），没有代码引用。
2. **垫片包隔离 javac 编译 = 0 错**：37 个文件，classpath =
   `26.3.jar` + `fabric-loader-0.19.5` + `fabric-networking-api-v1-6.3.10`（从 fabric-api 大 jar 里解出来）
   + `fabric-api-base` + joml 1.10.9 + fastutil 8.5.18 + slf4j + jspecify + annotations + datafixerupper + brigadier + lwjgl。
3. **契约测试 `= 0 错`**：另写了一个**不进仓库**的 `VeilShimContract.java`（临时目录），
   把 51 个调用点的形态逐条复刻（`ShaderBlock.dynamic` 的 lambda 目标类型推断、
   `VertexArray` 链式 builder、`thenApplyAsync(..., Minecraft)`、两种 `onVeilRenderLevelStage`
   方法引用、`RegistrationProvider` 泛型、`registerClientbound/serverbound` 的方法引用、
   `instanceof VeilRenderType.*` 的 while 循环…），javac 通过。
   —— 这一步才是「垫片形状对不对」的真正证据，因为整体构建跑不了。
4. **import 可解析性**：89 条 `dev.ryanhcode.sable.compat.veil.*` import（33 个不同）逐个映射到文件，
   无法解析 = **0**。

---

## 7. 顺带修的（同文件、非 veil 族，已确认属于 26.3 API 变化）

### 7.1 Registry API 3 处

| 文件 | 改动 | 原因 |
|---|---|---|
| `api/physics/force/ForceGroups.java` | `REGISTRY.size()` → `VANILLA_PROVIDER.getEntries().size()` | 26.3 的 `Registry` 接口**没有 `size()`**（`javap` 实测） |
| `physics/config/block_properties/PhysicsBlockPropertyTypes.java` | 同上 ×2；`REGISTRY.get(id)` → `REGISTRY.getOptional(id).orElse(null)` ×2 | 26.3 的 `Registry.get(Identifier)` 返回 `Optional<Holder.Reference<T>>`，不再是 `T` |
| `sublevel/render/fancy/FancySubLevelCommandBuilder.java` | 删 3 个**完全未使用**的 veil import | 死 import |
| `render/sky_light_shadow/SableSkyLightShadows.java` | 删 `MultiBufferSource` import + 参数 | 见 §5.2 |

### 7.2 构建依赖（任务要求「拔掉依赖」的一部分）

| 文件 | 原内容 | 处理 |
|---|---|---|
| `src/common/build.gradle` | `implementation("foundry.veil:veil-common-...")` | 删（留注释说明原行） |
| `src/fabric/build.gradle` | `include(modApi("foundry.veil:veil-fabric-..."))` | 删（留注释）——不再 jar-in-jar 打包 Veil |
| `src/fabric/src/main/resources/fabric.mod.json` | `depends` 里的 `"veil": ">=${veil_version}"` | 删 ——**这一条最要紧**：它是**运行期硬依赖**，留着会让 loader 在没装 Veil 时拒绝启动 Sable |

> 注：真正用于 26.3 编译的是 `work\sable-26\port26\build.gradle`，它**本来就没有 veil 依赖**
> （依赖走 `libs\expanded\*` + 3 个显式 jar），所以上面三条属于「仓库里的声明也一起拔干净」，
> 对现有构建无影响，只防止以后按上游布局构建时又把 Veil 拉回来。
> `gradle.properties` 的 `veil_version=4.3.2` 与 `buildSrc\...\multiloader-common.gradle` 的传递行
> **保留**（现在已无消费者；删除会牵动 `buildSrc`，收益为零）。

---

## 8. 刻意没碰的（不参与编译，按硬约束「只动 common/ 与 fabric/」）

| 路径 | 情况 |
|---|---|
| `src/neoforge/**` | **一个字节没动**（不是本工程的编译目标） |
| `src/_dropped_compat/**` | 已废弃的兼容 mixin 目录（sodium / shouldersurfing / perspective），端口构建的 `sourceSets` 里**没有它** ⇒ 不参与编译。其中 `SodiumWorldRendererMixin.java` 仍有 2 条 `import foundry.veil.…`（`VeilRenderBridge`、`VeilRenderType`），**故意不动**：它在 common/fabric 之外。若将来要复活这个文件，把那 2 条 import 改成 `dev.ryanhcode.sable.compat.veil.…` 即可（垫片里两个类都在） |

---

## 9. 留给别的族（不是 veil，别在这里找）

- `MultiBufferSource` / `DebugRenderer.renderFilledBox` —— 渲染栈族（已由 R343 那条线处理）。
- `com.mojang.blaze3d.vertex.VertexFormat` → `com.mojang.renderpearl.api.vertex.VertexFormat`，
  `VertexFormat.Mode` → `pipeline.PrimitiveTopology`。
- `net.minecraft.client.renderer.ShaderInstance` 的落点（26.3 已不在该包）。
- `imgui.*`（`SableClientConfig` 之外的 ImGui 家族）—— `SubLevelContainerInspector` 仍 import
  `imgui.ImGui/ImDrawList/ImVec2`，属于另一条线。
- `BakedQuad` 迁包（`SubLevelTextureCache` 仍 import 旧路径）。

---

## 10. 操作要点（复现）

```powershell
# 1) 全部 import 机械替换（同时留备份）
#    foundry.veil  ->  dev.ryanhcode.sable.compat.veil
#    改动前对 51 个文件各留一份 <file>.java.bak-sableveil
# 2) 垫片源码在：
#    work\sable-26\src\common\src\main\java\dev\ryanhcode\sable\compat\veil\
# 3) 验收：
#    python -c "扫 common+fabric，re '^import foundry.veil' == 0"
```

回滚：51 个文件都有 `.bak-sableveil`；垫片目录是纯新增，删掉目录即可。
