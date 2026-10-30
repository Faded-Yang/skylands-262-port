# Veil 拔除报告（MC 26.3 + Fabric）

> 目标：**把 `foundry.veil` 这个硬依赖从 Aeronautics 工程里彻底拔掉**，改由本工程自有的
> `dev.simulated_team.simulated.compat.veil` 垫片实现。
>
> 根因：Veil 在 26.x 上**根本不存在**（Modrinth 上 109 个版本全是 1.21.1）。工程的
> `fabric.mod.json` 也从未声明它，所以 1.21.1 那份 jar 只是「编译期能过、运行期必炸」。
>
> 工程根：`work/aero-port/aeronautics-26/src`
> 生成时间：2026-10-17（R341 波次）

---

## 0. 三个数字（验收口径）

| 指标 | 数值 |
|---|---|
| **`import foundry.veil`（python `re`，区分大小写）** | **89 → 0** |
| **新写垫片文件数** | **12**（另有 6 个网络层垫片文件是**复用** 1.21.11 轮已写好的） |
| **降级处数** | **15**（逐条见 §4） |

---

## 1. 怎么复核

```powershell
# 用 python 数 import（不要用 Select-String：它大小写不敏感）
& "C:\Users\95959\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" -c `
  "import os,re;r=r'C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\aero-port\aeronautics-26\src';n=0;[n:=n+len(re.findall(r'^import\s+foundry\.veil',open(os.path.join(dp,f),encoding='utf-8',errors='replace').read(),re.M)) for dp,dn,fn in os.walk(r) for f in fn if f.endswith('.java')];print(n)"
```

复核结果（本次实测）：

- `import foundry.veil` = **0**（76 个 .java 文件的 89 条 import 全部改写）
- 全工程（`src` 下，排除 `*.bak-*`）搜字符串 `foundry.veil` = **0**（连注释里的旧 FQN 也清了，
  免得后人误以为还依赖 Veil）
- `.bak-veil2` 备份 = **76** 个（与改动文件一一对应）

> ⚠ 工作区里另有 **`src.bak-veil/`（上一次尝试的整树备份）** 和一批 `*.bak-rNNN` 历史备份，
> 它们**不在编译源集里**，仍含 `foundry.veil` 字样。**不要**把它们算进「残留」，也不要删
> （是回滚依据）。

---

## 2. 符号清单（17 个符号 / 89 条 import / 76 个文件）

「工程实际调用面」= 全量 grep 后**真的被调用到**的成员；没列出的成员垫片**故意不提供**
（少一个符号就少一处版本风险）。

| # | Veil 符号 | import 数 | 文件数 | 工程实际调用面 | 垫片落点 | 性质 |
|---|---|---|---|---|---|---|
| 1 | `api.network.VeilPacketManager` | 29 | 29 | `create`、`server()`、`player(ServerPlayer)`、`tracking(Entity/BlockEntity)`、`all(MinecraftServer)`；`PacketHandler.handlePacket`（方法引用）、`PacketSink.sendPacket` | `compat.veil.VeilPacketManager` | ✅ **复用**（保真） |
| 2 | `api.network.handler.ServerPacketContext` | 20 | 20 | `player()`、`level()` | `compat.veil.handler.ServerPacketContext` | ✅ 复用 |
| 3 | `api.network.handler.ClientPacketContext` | 9 | 9 | `player()`、`level()` | `compat.veil.handler.ClientPacketContext` | ✅ 复用 |
| 4 | `api.network.handler.PacketContext` | 8 | 8 | 作形参基类型；`player()`、`level()` | `compat.veil.handler.PacketContext` | ✅ 复用 |
| 5 | `api.event.VeilRenderLevelStageEvent` | 4 | 4 | `.Stage` 常量（`AFTER_*` 共 5 个值）+ 形参类型 | `compat.veil.event.VeilRenderLevelStageEvent` | ⚠️ **降级**（只剩枚举） |
| 6 | `api.client.color.Color` | 3 | 3 | `new Color(int,boolean)`、`new Color(float×4)`、`new Color()`、`ARGB_INT_CODEC` | `compat.veil.color.Color` | ✅ 保真（纯数学） |
| 7 | `api.client.color.Colorc` | 2 | 2 | `argb()`、`darken(float, Color)` | `compat.veil.color.Colorc` | ✅ 保真 |
| 8 | `platform.VeilEventPlatform` | 2 | 2 | `INSTANCE.onVeilAddShaderProcessors`、`onVeilRegisterBlockLayers`、`onVeilRegisterFixedBuffers` | `compat.veil.event.VeilEventPlatform` | ⚠️ **降级**（3 个 no-op） |
| 9 | `api.client.render.VeilLevelPerspectiveRenderer` | 2 | 2 | `isRenderingPerspective()` | `compat.veil.render.VeilLevelPerspectiveRenderer` | ⚠️ **降级**（恒 false） |
| 10 | `api.client.render.framebuffer.AdvancedFbo` | 2 | 2 | `withSize/addColorTextureBuffer/setDepthTextureBuffer/build/free`、`bind/bindRead/clear`、静态 `unbind` | `compat.veil.render.framebuffer.AdvancedFbo` | ⚠️ **降级**（无 GPU 资源） |
| 11 | `api.client.render.MatrixStack` | 2 | 2 | `matrixPush/matrixPop/translate(double×3)/pose()/toPoseStack()` | `compat.veil.render.MatrixStack` | ⚠️ 适配器可用，但**无事件源** ⇒ 调用方不可达 |
| 12 | `api.client.render.shader.processor.ShaderPreProcessor` | 1 | 1 | `implements`（无实例化） | **无垫片**（见 §5） | ❌ 垫不掉 |
| 13 | `api.CodecReloadListener` | 1 | 1 | `extends` + `super(Codec, FileToIdConverter)` + `apply(...)` 覆写 | `compat.veil.CodecReloadListener` | ✅ 保真 |
| 14 | `api.util.CodecUtil` | 1 | 1 | `VECTOR3D_CODEC`（`ServerRopeStrand` 顶点序列化） | `compat.veil.util.CodecUtil` | ✅ 保真 |
| 15 | `api.client.render.VeilRenderSystem` | 1 | 1 | `renderer().getPostProcessingManager()` | `compat.veil.render.VeilRenderSystem` | ⚠️ **降级**（只留这一条链） |
| 16 | `api.client.render.post.PostPipeline` | 1 | 1 | `getUniformSafe(name).setVector/setFloat`、作变量类型 | `compat.veil.render.post.PostPipeline` | ⚠️ **降级**（恒 NOOP） |
| 17 | `api.client.render.post.PostProcessingManager` | 1 | 1 | `getPipeline(id)`、`getPostPipelineContext().setFramebuffer(...)`、`runPipeline(p,false)` | `compat.veil.render.post.PostProcessingManager` | ⚠️ **降级**（空实现） |

**16 个可垫 + 1 个垫不掉**（`ShaderPreProcessor`）。

> 76 个被改文件里，**3 个本来就不参与编译**（`build.gradle` 的 `exclude` 命中）：
> `excluded-wip/EndSeaFadeTransformer.java`、`AltitudeSensorScreen.java`、`NameplateScreen.java`。
> 其余 **73 个参与编译**。

---

## 3. 垫片清单

### 3.1 复用（6 个文件，1.21.11 轮已写好，本次只改 import 指向）

`src/main/java/dev/simulated_team/simulated/compat/veil/`

| 文件 | 说明 |
|---|---|
| `VeilPacketManager.java` | 接口 + `create/server/player/tracking/all`；签名按 Veil 4.5.0 jar `javap` 逐条核对 |
| `FabricVeilPacketManager.java` | `PayloadTypeRegistry` + `ServerPlayNetworking/ClientPlayNetworking` 映射 |
| `VeilClientSide.java` | 只在物理客户端加载的薄壳（避免专用服务端 linkage error） |
| `handler/PacketContext.java` | 基接口（**自己声明 `player()/level()`**，不是空标记接口） |
| `handler/ServerPacketContext.java` | 协变收窄到 `ServerPlayer/ServerLevel` |
| `handler/ClientPacketContext.java` | 协变收窄到 `LocalPlayer/ClientLevel` |

> 这 6 个文件里的网络层是**唯一「完全非降级」的一族**：Veil 在 Fabric 上的包管理本来就是
> Fabric Networking API 的一层薄包装，垫片按同样映射重写，功能等价。

### 3.2 新写（12 个文件）

| 文件 | 对应 | 保真度 | 关键实现点 |
|---|---|---|---|
| `CodecReloadListener.java` | `api.CodecReloadListener` | ✅ 等价 | `SimplePreparableReloadListener<Map<Identifier,T>>` + `FileToIdConverter.listMatchingResources` + `JsonParser.parseString` + `Codec.parse(JsonOps)`；`javap` 确认 26.3 这三样都在 |
| `color/Colorc.java` | `api.client.color.Colorc` | ✅ 等价 | `red/green/blue/alpha` + `rgb/argb/redInt…` + `lighten/darken/lerp/mix`；纯数学 |
| `color/Color.java` | `api.client.color.Color` | ✅ 等价 | float 分量存储；4 个用到的构造器 + `RGB/ARGB_INT_CODEC`、`RGB/ARGB_CODEC` |
| `util/CodecUtil.java` | `api.util.CodecUtil` | ✅ 等价 | `VECTOR3D_CODEC` = `Codec.DOUBLE.listOf()` 长度 3 的 `comapFlatMap`（+ 对称的 VECTOR3F） |
| `render/MatrixStack.java` | `api.client.render.MatrixStack` | ⚠️ 可用但无源 | `final class` 包 `PoseStack`；提供 `matrixPush/Pop`、`translate(float/double)`、`pose()→PoseStack.Pose`、`toPoseStack()` 等 5 个实际用到的方法 |
| `render/VeilLevelPerspectiveRenderer.java` | 同名 | ⚠️ 降级 | `isRenderingPerspective()` 恒 `false` |
| `render/VeilRenderSystem.java` | 同名 | ⚠️ 降级 | `renderer()` → 内置 `VeilRenderer.getPostProcessingManager()`；其余 60+ API 未提供 |
| `render/framebuffer/AdvancedFbo.java` | 同名 | ⚠️ 降级 | 纯描述对象（宽高/附件数/调试名），不分配 GPU 资源；`Builder` 链式 API 形状保留 |
| `render/post/PostPipeline.java` | 同名（含 `Context`、`ShaderUniformAccess`） | ⚠️ 降级 | 接口 + `getUniformSafe` 恒返回 `ShaderUniformAccess.NOOP` |
| `render/post/PostProcessingManager.java` | 同名 | ⚠️ 降级 | `getPipeline` 恒 `null`；`runPipeline/add/remove/endFrame/free` 全 no-op |
| `event/VeilRenderLevelStageEvent.java` | 同名 | ⚠️ 降级 | **只保留 11 个 `Stage` 常量**（+`getName()`）；无回调方法 |
| `event/VeilEventPlatform.java` | `platform.VeilEventPlatform` | ⚠️ 降级 | `INSTANCE` + 3 个注册方法全 no-op（带 `debug` 日志） |

---

## 4. 降级削减清单（**15 条 · 完整**）

> 每条都在源码里带 `// PORT(26.3): ...` 注释，说明丢了什么、为什么丢。
> 「可修回？」= 需要什么条件才能恢复。

| # | 位置 | 丢了什么效果 | 为什么必须丢 | 可修回？ |
|---|---|---|---|---|
| **1** | `event/VeilEventPlatform.java` `onVeilAddShaderProcessors` | 把 GLSL 预处理器挂到着色器编译链上。工程里该订阅的 lambda 体**本来就是空的**（`SimulatedClient:43`） | 26.3 的着色器走 `com.mojang.renderpearl` 的 `RenderPipeline`，没有「按源码字符串改 GLSL」的公开入口 | ❌ 需 26.3 侧的着色器源码钩子（当前不存在） |
| **2** | 同上 `onVeilRegisterBlockLayers` | 把 `AeroRenderTypes.levitite()` / `levititeGhosts()` 注册成「区块渲染层」 | 26.3 的区块层由原版 `RenderType.chunkBufferLayers()` + 提交管线决定，**没有外部注册入口**（`javap` 实测） | ⚠️ 需改 `RenderType` 的层枚举方式；若 levitite 在区块里不显示，要单独接 |
| **3** | 同上 `onVeilRegisterFixedBuffers` | 把 `laser`/`lens`/`staffOverlay`/`levitite*` 固定到 `AFTER_PARTICLES`/`AFTER_TRANSLUCENT_BLOCKS`/`AFTER_LEVEL`/`AFTER_BLOCK_ENTITIES`/`AFTER_WEATHER` 刷出 | 「固定缓冲」是 Veil 自家渲染管线的概念；26.3 提交管线自己负责批次排序，无对应物 | ❌ 概念不存在；渲染类型本身仍可用 |
| **4** | `event/VeilRenderLevelStageEvent.java` | 渲染阶段**事件回调**（原方法 10 个参数，含 `MultiBufferSource.BufferSource`） | **`MultiBufferSource` 这个类在 26.3 已整个不存在**（`jar tf 26.3.jar \| grep MultiBufferSource` = 0），签名垫不出来；Fabric 的 `WorldRenderEvents` 也被 `LevelRenderEvents` + submit-node 取代 | ❌ 要按 26.3 提交管线重写（不是垫片能做的） |
| **5** | `AeronauticsClient.registerEvents`（原 L27–38，已删） | 气球热空气的**屏幕后处理**钩子 `ClientBalloonEffectRenderer.onRenderLevelStage(stage, frustumMatrix, projectionMatrix, renderTick)` 不再触发 | 依赖 #4；且该渲染器在本轮移植里**本来就是编译桩**（`ClientBalloonEffectRenderer` 方法体为空） | ⚠️ 与 #4 同条件；恢复后需真实现 |
| **6** | `SimulatedClient.init`（原 L45，已删） | **物理法杖的选择框 / 悬停框**不再绘制（`SimulatedCommonClientEvents.onRenderLevelStage` → `PhysicsStaffRenderHandler.renderSelectionBox` 整条链路变不可达） | 依赖 #4；且该链路还卡在 `MultiBufferSource`（26.3 无此类型），本轮**本来就编不过** | ⚠️ 需按 submit-node 重写 `renderSelectionBox`，再接 26.3 的 `LevelRenderEvents.AFTER_TRANSLUCENT_TERRAIN` **或** `SubmitNodeCollector` |
| **7** | `render/framebuffer/AdvancedFbo.java` | 真正的离屏渲染目标：`create/bind/bindRead/clear/free/unbind*` 全部 no-op；`getId()` 返回**负数的假 id** | 26.3 把 GL 直调换成 `renderpearl` 的 `GpuTexture/RenderPass`；`RenderTarget` 只剩 `getColorTexture()` 与 `blitAndBlendToTexture(...)`，没有可平移的 bind/clear 入口 | ⚠️ 需用 `GpuTexture` + `RenderPass` 重写 |
| **8** | `render/VeilLevelPerspectiveRenderer.java` | 子维度「透视渲染」状态：`isRenderingPerspective()` **恒 false** ⇒ 图表屏幕的「正在渲染透视预览」分支永远走不到 | Veil 的 `LevelPerspectiveCamera` 与可绑定 FBO 都不存在（依赖 #7） | ⚠️ 与 #7 同条件 |
| **9** | `render/VeilRenderSystem.java` | 渲染系统门面：GL 能力探测、着色器块绑定、`setShader/drawScreenQuad/renderPost/beginFrame/...` 60+ API **未提供** | 26.3 对应 `GpuDevice/GpuCapabilities`；工程零调用，**按需再写**而非空实现 | ⚠️ 用到哪个补哪个 |
| **10** | `render/MatrixStack.java` | 变换栈本身是真实现（可包 `PoseStack`），但**唯一构造它的地方是 #4 的事件回调** ⇒ 当前没有任何运行路径会创建它 | 事件源消失（#4） | ✅ 一旦 #6 的重写落地，直接 `MatrixStack.wrap(poseStack)` 就能用 |
| **11** | `render/post/PostProcessingManager.java` `getPipeline` | **恒返回 `null`** ⇒ 调用方的 `if (pipeline != null)` 整块被跳过（`LineColor/InSize/PaletteOffset/FadeScale` 四个 uniform 不再设置） | 26.3 没有「按 JSON 组装后处理链」的加载器 | ❌ 需自研后处理链（或等上游） |
| **12** | 同上 `runPipeline` | 图表屏幕的**后处理（线条描边 / 配色分级 / 淡出）整体不执行** | 同上 | ❌ 同上 |
| **13** | `render/post/PostPipeline.java` `Context.setFramebuffer` | 把命名 FBO 暴露给 pipeline 的 stage —— **no-op** | 依赖 #7（没有真 FBO） | ❌ 同上 |
| **14** | 同上 `getUniformSafe` / `ShaderUniformAccess` | uniform 写入全部 no-op（`setVector/setFloat/setInt`） | 没有真实着色器程序可写 | ❌ 同上 |
| **15** | `excluded-wip/EndSeaFadeTransformer.java` | End Sea 的分层雾气着色：注入 `EndSeaCameraY`、改写 `vertexColor.rgb` | 依赖 Veil `ShaderPreProcessor` **与** `io.github.ocelot.glslprocessor`（26.3 都没有；后者也没有 26.3 构建） | ❌ 需按 26.3 渲染管线重写；**该文件本就被 `build.gradle` 排除，不参与编译** |

**汇总（观感层面）：**

1. 图表 / 便签屏幕里的**子维度缩略图**与**后处理**完全消失（数据与交互不受影响）。
2. 物理法杖的**选择框 / 悬停框**消失。
3. 气球热空气的**屏幕后处理**不再触发（本来就是空实现）。
4. levitite / laser / lens / staffOverlay 的**渲染时机**改由 26.3 提交管线排序（类型本身还在）。

> ⚠ **既有降级（不是本次引入，别记在本账上）**：`handler/PacketContext.disconnect()` 在
> 1.21.11 轮就改成了「只打日志、不断开」（26.3 的 `ServerGamePacketListenerImpl` 没有
> `disconnect(Component)` 重载）。

---

## 5. 垫不掉的（3 条）

### 5.1 `ShaderPreProcessor`（`api.client.render.shader.processor`）

- 接口签名里带 `io.github.ocelot.glslprocessor.api.node.GlslTree`、`GlslSyntaxException`、
  `anarres.cpp.LexerException`。**26.3 没有这个库，也没有 26.3 构建**（`docs/DEPS-26.3.md`）。
- 唯一实现者 `EndSeaFadeTransformer` 本来就被 `build.gradle` 排除，不参与编译。
- 处理方式：删掉 import，类声明去掉 `implements`，加文件级说明「整体不参与编译、仅作重写参考」。
- **不写空接口冒充可用** —— 写了也挡不住它下面对 `GlslTree` 的方法调用。

### 5.2 Veil 的「渲染阶段事件」签名

- 参数第 3 个是 `MultiBufferSource.BufferSource`。**该类在 26.3 不存在**（`javap` / `jar tf` 双证）。
- Fabric API 的 `WorldRenderEvents` 在 `fabric-rendering-v1-27.1.0`（26.3）里**已被删除**，
  取而代之的是 `LevelRenderEvents`（`START_MAIN/AFTER_OPAQUE_TERRAIN/AFTER_TRANSLUCENT_TERRAIN/END_MAIN/...`）
  与 `LevelRenderContext`（提供 `poseStack()`/`submitNodeCollector()`/`levelRenderer()`/`levelState()`），
  **不再提供 `MultiBufferSource`**。
- 结论：不是「没找到钩子」，而是**钩子的数据模型换了**。硬桥接 = 把整个回调按 submit-node 重写，
  那属于渲染族的重写工作，不属于「拔 Veil」。

### 5.3 `VeilRenderSystem` 的 GL 能力探测族

- 原类有 60+ 方法（`tessellationSupported/computeSupported/maxSamples/bindTextures/writeToBuffer/...`）。
- 工程**零调用**，全部不提供。**没有留空方法** —— 留了会让人以为可用。
  需要时按 `renderpearl` 的 `GpuDevice` 现写。

---

## 6. 验证证据

### 6.1 签名来源（不靠记忆）

`javap` 对 `work/aero-port/libs/veil-fabric-1.21.1-4.5.0.jar` 逐类核对（该 jar 是
intermediary 名，已按 `class_761=LevelRenderer` 等映射回 26.3 名）：

- `VeilRenderLevelStageEvent` / `$Stage`（11 个常量）
- `VeilEventPlatform`（3 个用到的注册方法）
- `Color`（4 个用到的构造器 + 4 个 Codec 常量 + `red/green/blue/alpha`）
- `Colorc`（`argb/rgb/darken/lighten/lerp`…）
- `MatrixStack`（`matrixPush/matrixPop/translate/pose/toPoseStack`）
- `VeilLevelPerspectiveRenderer`、`VeilRenderSystem`、`AdvancedFbo`(+`Builder`)、
  `PostPipeline`(+`Context`)、`PostProcessingManager`、`CodecReloadListener`、`CodecUtil`
- 26.3 侧同时 `javap` 核对了落点 API：`SimplePreparableReloadListener`、`FileToIdConverter`、
  `Resource.readAllAsString/openAsReader`、`PoseStack`、`RenderType`、`Identifier`、
  `RenderTarget`（确认没有可平移的 bind/clear）。

### 6.2 独立编译（**只编垫片，不编工程**）

按要求**没有跑 `gradlew compileJava`**（其他族未修完）。改为把 12 个新垫片文件**单独**用
javac 直编，classpath = `26.3.jar` + `datafixerupper-10.0.21` + `gson-2.14.0` +
`slf4j-api-2.0.17` + `joml-1.10.9`：

```
javac --release 25 -d <temp>/out @args.txt     →  EXIT=0（12 文件全过）
```

再补两个**调用点探针**（不进工程，只验证签名够用）：

- `CallSiteProbe.java` —— 把 12 个符号的调用表达式**原样抄一遍**
  （`Color.ARGB_INT_CODEC.xmap(...)`、`CodecUtil.VECTOR3D_CODEC.listOf().fieldOf(...)`、
  `AdvancedFbo.withSize(...).addColorTextureBuffer().setDepthBuffer().build(true)`、
  `VeilRenderSystem.renderer().getPostProcessingManager().getPipeline(id)`、
  `pipeline.getUniformSafe("x").setVector(...)`、`VeilEventPlatform.INSTANCE.onVeilRegister*`、
  `ps.matrixPush()/translate(double,double,double)/pose()/toPoseStack()` 等）
- `ResourceManagerProbe.java` —— 验证 `SimpleResourceManager<T>` 的
  `extends CodecReloadListener<T>` + `super(codec, FileToIdConverter.json(path))` +
  `@Override apply(Map<Identifier,T>, ResourceManager, ProfilerFiller)` 形状一致

```
javac --release 25 -d <temp>/probeout -cp <shims>+<26.3> CallSiteProbe.java ResourceManagerProbe.java
→  EXIT=0
```

**已知的、本轮不负责的编译障碍**：`MultiBufferSource` 在 26.3 不存在（GUI/渲染族），
`GuiGraphics` 不存在（GUI 族，另一个代理在改）。这两族修完之前工程不可能整体编译，
与 Veil 无关。

### 6.3 改动面审计

- 76 个 `.bak-veil2` 备份与改动文件一一对应；
- 逐文件 diff 审计：**71 个文件只改了 import 行**；5 个有额外改动 =
  `AeronauticsClient`（删订阅）、`SimulatedClient`（删订阅+注释）、`EndSeaFadeTransformer`
  （去 `implements`+文件头说明）、`AeroPacketManager`/`SimPacketManager`（恢复了一处被正则吃掉的空行）；
- 所有 `import dev.simulated_team.simulated.compat.veil.*` 的落点文件**都存在**（脚本校验）；
- **没有重复 import**；**没有改过任何含 `GuiGraphics` 的行**（与并行代理的边界）。

---

## 7. 回滚

```powershell
# 单文件
Copy-Item <file>.java.bak-veil2 <file>.java -Force
# 全部（76 个）
Get-ChildItem -Recurse -Filter *.java.bak-veil2 | ForEach-Object { Copy-Item $_.FullName ($_.FullName -replace '\.bak-veil2$','') -Force }
```

新增的 12 个垫片文件没有 `.bak`（它们是新文件），回滚时删掉
`src/main/java/dev/simulated_team/simulated/compat/veil/` 下 §3.2 那 12 个即可 ——
**但注意 **`compat/veil/` 里那 6 个网络层文件是 1.21.11 轮的成果，不要删**。

---

## 8. 给后续的注意事项

1. **别再把 Veil 加回来**。`build.gradle` 里已无 Veil 依赖（R339 前就删了），
   `fabric.mod.json` 也从未声明过。
2. **`SimulatedCommonClientEvents.onRenderLevelStage` / `PhysicsStaffRenderHandler.renderSelectionBox`
   现在是「有方法、无订阅」**。谁要修物理法杖选择框，走的是 #6：按 26.3 的
   `SubmitNodeCollector` 重写，**不是**把 Veil 事件找回来。
3. **`AdvancedFbo` 的 `getId()` 是负数假 id**。若哪天有人拿它去 `blit` 纹理，会静默画不出东西 ——
   这不是 bug，是记录的降级（#7）。
4. **`PostProcessingManager.getPipeline` 恒 null**。调用点的 `if (pipeline != null)` 是**保命判空**，
   别删。
5. `MatrixStack` 是适配器：一旦有人重新拿到 `PoseStack` 的渲染期钩子，
   `MatrixStack.wrap(poseStack)` 就能复活 #10。
6. 本文件与 `docs/DEGRADATIONS.md`「一、依赖层 → Veil」一行对应；两处要一起维护。
