# 修 `IllegalStateException: Render pass color attachment count must match pipeline color target state count`

> **结论**：出事的不是 `AllRenderPipelines` 那 5 条，也不是 `RenderSetup` / `setOitPipelines` / 任何 mixin ——
> 是 **`PonderRenderPipelines` 里 8 条 `ponder:pipeline/entity_block_*` 不透明管线，声明了 0 个 color target**，
> 而 26.3 主世界 pass 恒有 **1** 个 color attachment，`FrontendRenderPass.setPipeline` 直接拒绝绑定。
>
> 这 8 条管线被 **`EntityBlockRenderType` → `PonderRenderTypes` → `SuperByteBufferTask`** 这条“把方块模型当实体画”
> 的路径使用 ⇒ **凡走 `SuperByteBuffer` 自绘模型的 Create 方块，一进画面就崩**（`cogwheel` / `fluid_tank` /
> `white_postbox` / `nixie_tube`），而 `cuckoo_clock` / `creative_motor` 用自己的 renderer，走不到这里。
>
> 修法 = **单类 ASM**：在 `PonderRenderPipelines.<clinit>` 里给这 8 条链各插 2 条指令
> `getstatic ColorTargetState.DEFAULT` + `invokevirtual withColorTargetState`（**vanilla 自己的
> `pipeline/solid_block` 就是这么写的**）。**只 1 个 class 变，其余 14,335 个 entry 逐字节不动。**
>
> A/B：旧件 `FAIL_CRASH`（`FrontendRenderPass.setPipeline:103` ← `executeSolid`）；新件 **8 个 Create 方块
> 全摆在眼前不崩**、`WORLD_OK`、`Render pass color attachment` / `IllegalStateException` / `NoSuchMethodError`
> / `FAIL_TIMEOUT` 全 0；重扫地雷 **158 → 158**（无变化）。

---

## 0. 并行冲突：开工与交付时的 `create-fly` 基线

| 时点 | SHA-256 | 大小 | mtime |
|---|---|---|---|
| **开工时**（16:20 读） | `DA3E5A9F4C85E1175375BAD572A586987E28B235D0E45D6B70979D2F1A466EC9` | 19,639,235 B | 2026-10-18 15:55:45 |
| **中途复核**（16:33，删旧件前） | 同上（未变） | 同上 | 同上 |
| **交付时**（16:38 替换前打印） | 同上（未变） | 同上 | 同上 |
| **交付后新件** | `B6B1FD1840B845523B18F6DBCE938076187B001C0A046186470BFB45BDCB8888` | 19,639,253 B | 2026-10-18 16:38 |

⇒ 本轮**没有**并行代理改动这个 jar，补丁基于唯一基线 `DA3E5A9F…66EC9`（= 上一轮 `docs/fix-diffuseshade.md`
§11 交付的那一件）。备份名 `.bak-rastpass`（未使用 `.bak-clock` / `.bak-shader` / `.bak-ponder` /
`.bak-diffuseshade`）。

`mods-stable` 开工与交付时都是 **71 jar**。

---

## 1. 先定位：到底是哪条 pipeline 出事

异常消息里**既没有 pipeline 名字也没有两个数字**，所以必须把它抓出来。做法是在
`work/run26/port/g20/probe/`（一次性探针，**永不进 `mods-stable`**）里加两个 **mixin**：

| mixin | 目标 | 作用 |
|---|---|---|
| `FrontendRenderPassMixin` | `com.mojang.renderpearl.frontend.FrontendRenderPass#setPipeline` | HEAD 处反射读 `this.colorAttachments.size()` 与 pipeline 的 `colorTargetStates().size()`，不相等就打印；**不 cancel**（非本路径的崩溃保持原样） |
| `PreparedRenderTypeMixin` | `net.minecraft.client.renderer.rendertype.PreparedRenderType#draw` | HEAD 处同样比较并打印 **render type 名字 + pipeline 名字 + 两个数字 + colorTarget 列表**；默认 **cancel**，这样一次运行能把**所有**违规者列出来而不是死在第一个上 |

另外探针还在进世界时把 `RenderPipelines.PIPELINES_BY_LOCATION`（`AllRenderPipelines.register` /
`PonderRenderPipelines.register` 都往这里写）整个 dump 一遍，列出所有 `targets != 1` 的管线。

### 1.1 抓到的东西（`g20/evidence/diag1-latest.log`）

```
[sky262rast] pipelines registered: 213
[sky262rast] PIPELINE-DUMP loc=ponder:pipeline/entity_block_solid targets=0 wantsDepth=true
[sky262rast] PIPELINE-DUMP loc=ponder:pipeline/entity_block_cutout targets=0 wantsDepth=true
[sky262rast] PIPELINE-DUMP loc=ponder:pipeline/entity_block_light_solid targets=0 wantsDepth=true
[sky262rast] PIPELINE-DUMP loc=ponder:pipeline/entity_block_light_cutout targets=0 wantsDepth=true
[sky262rast] PIPELINE-DUMP loc=ponder:pipeline/nether_entity_block_solid targets=0 wantsDepth=true
[sky262rast] PIPELINE-DUMP loc=ponder:pipeline/nether_entity_block_cutout targets=0 wantsDepth=true
[sky262rast] PIPELINE-DUMP loc=ponder:pipeline/nether_entity_block_light_solid targets=0 wantsDepth=true
[sky262rast] PIPELINE-DUMP loc=ponder:pipeline/nether_entity_block_light_cutout targets=0 wantsDepth=true
...
[sky262rast] PIPELINE-DUMP pipelines with targets!=1: 42
...
[sky262rast] MISMATCH rt='ponder:entity_block_solid'  pipeline=ponder:pipeline/entity_block_solid  pipelineTargets=0 passAttachments=1 targets=[] first=1
[sky262rast] MISMATCH rt='ponder:entity_block_cutout' pipeline=ponder:pipeline/entity_block_cutout pipelineTargets=0 passAttachments=1 targets=[] first=1
```

**42 条的构成**（全部列在 `diag1-latest.log` 里）：

| 类别 | 条数 | targets | 是否真缺陷 |
|---|---|---|---|
| `minecraft:pipeline/oit_transmittance_*` | 31 | 2 | 否 —— 它们只绑 OIT transmittance pass（见 §2.4） |
| `minecraft:pipeline/integrate_depth`、`blit_depth`、`oit_water_mask` | 3 | 0 | 否 —— 只绑“无 color attachment”的 pass |
| **`ponder:pipeline/*_entity_block_*`（8 条）** | **8** | **0** | **是** —— 却绑在主世界 pass 上 |

被实测崩的方块，其 render type 正是这 8 条管线做的 RT。**一次运行里违规的 render type 只有
`ponder:entity_block_solid` / `ponder:entity_block_cutout` 两个**（`..._translucent` 系列本来就有
color target，所以不违规）。

另：`FrontendRenderPassMixin` 那一侧（覆盖**所有** `setPipeline` 调用点、而且**不 cancel**）在整次运行里
**一次都没报** ⇒ 违规只发生在 `PreparedRenderType.draw` 这条路上，没有第二个调用点参与。

### 1.2 为什么恰好是那 4 个方块崩

```
EntityBlockRenderType.SOLID/CUTOUT/...      (com.zurrtum.create.client.catnip.render)
  ├─ 字段 type      = Sheets.cutoutBlockItemSheet()      // 非主世界/下界时用
  ├─ 字段 overworld = PonderRenderTypes.getEntityBlockSolid()   → RT ponder:entity_block_solid
  └─ 字段 nether    = PonderRenderTypes.getNetherEntityBlockSolid()
        ↓  EntityBlockLayer / EntityBlockLightLayer 调 getRenderType(int)
        ↓  EntityBlockSbbBuilder / EntityBlockTemplateMesh / SuperByteBufferTask
      凡是用 SuperByteBuffer 自绘自己模型的 Create 方块
```

`SuperByteBufferTask` / `EntityBlockSbbBuilder` 是 `CachedBuffers` / `SuperByteBufferCache` 的落点，
所以 **`cogwheel`（flywheel visual 也走 `BracketedKineticBlockEntityVisual` → 方块模型）、`fluid_tank`、
`white_postbox`、`nixie_tube` 全军覆没；`cuckoo_clock`、`creative_motor` 用各自的 BlockEntityRenderer +
`CreateRenderTypes`（管线是自建但**声明了 1 个** target）所以安全** —— 与实测完全一致。

---

## 2. 26.3 的对应 API（javap 实测，`26.3.jar`）

### 2.1 `FrontendRenderPass.setPipeline` 的校验

```
public void setPipeline(CompiledRenderPipeline);
   25: aload_2
   26: invokevirtual FrontendRenderPipeline.colorTargetStates:()Ljava/util/List;
   29: astore_3
   30: aload_3
   31: invokeinterface List.size:()I
   36: aload_0
   37: getfield      Field colorAttachments:Ljava/util/List;
   40: invokeinterface List.size:()I
   45: if_icmpeq     58
   48: new           java/lang/IllegalStateException
   52: ldc           "Render pass color attachment count must match pipeline color target state count."
   57: athrow
```

⇒ 之后还逐 target 比 **format**（`ColorTargetState.format()` vs `textureView.texture().getFormat()`），
所以“数量对、格式不对”会报另一条消息；本轮遇到的只有数量这一条。

### 2.2 pipeline 的 target 数怎么来的

`RenderPipeline$Builder`：

```
private final ColorTargetState[] colorTargetStates;
private int activeColorTargetStateCount;

withColorTargetState(int, ColorTargetState)      // colorTargetStates[i]=s; activeCount=max(activeCount,i+1)
withColorTargetState(ColorTargetState)           // == withColorTargetState(0, s)     ← 单参重载写死 index 0
withColorTargetStates(int from, int to, Supplier) // 批量，OIT 用
withUnusedColorTargetState(int)                  // 占位 null，仍计进 activeCount

build():
   if (activeColorTargetStateCount != 0)
       colorTargetStates = Arrays.copyOf(colorTargetStates, activeColorTargetStateCount);
   else
       colorTargetStates = new ColorTargetState[0];      // ← 一个都没写 = 0 个 target
```

⇒ **`PonderRenderPipelines` 那 8 条链从头到尾没调过 `withColorTargetState`，所以编译出来就是 0 个 target 的
pipeline；`targets=[]` 是字面意义上的空数组**，不是打印失败。

`FrontendRenderPipeline`（record）把 `getColorTargetStates()` 原样存进 `colorTargetStates` 字段，
编译期不补任何默认值 —— 所以问题在**声明**侧，不在 pass 侧。

### 2.3 主世界 pass 恒为 1 个 color attachment

`LevelRenderer.lambda$addMainPass$0`（字节码等价源码）：

```java
RenderPass pass = device.createCommandEncoder().createRenderPass(
        () -> solid ? "Solid" : "Main",
        renderTarget.getColorTextureView(),      // 唯一一个 color attachment
        Optional.empty(),
        renderTarget.getDepthTextureView(),
        OptionalDouble.empty());
executeSolid(chunkSections, preparedFrame, pass);   // ← 崩栈上的那一条
```

`CommandEncoder.createRenderPass(label, colorView, clear, depthView, clearDepth)` 的 default 实现就是

```java
RenderPassDescriptor.builder(label)
    .withColorAttachment(colorView, clear)       // 恰好一次
    ...withDepthAttachment...
```

⇒ **pass 侧没得改，也不该改**；变的是 pipeline。

### 2.4 vanilla 自己的权威写法

**(a) 不透明、进主 pass 的管线 —— 恰好 1 个 target，用 `ColorTargetState.DEFAULT`**

```
$ javap -p -c net.minecraft.client.renderer.RenderPipelines   (静态初始化里)
  ldc "pipeline/solid_block"
  invokevirtual RenderPipeline$Builder.withLocation
  getstatic     ColorTargetState.DEFAULT
  invokevirtual RenderPipeline$Builder.withColorTargetState(ColorTargetState)
  invokevirtual RenderPipeline$Builder.build
  invokestatic  RenderPipelines.register
```

`ColorTargetState.DEFAULT` 的静态初始化（权威定义“不混合”）：

```
new ColorTargetState(Optional.empty() /* blend = 无 */, GpuFormat.RGBA8_UNORM, 15 /* WRITE_ALL */)
```

**(b) 多目标例子的唯一用法是 OIT，而且 target 数由同一个常量决定**

```
OIT_TRANSMITTANCE_SNIPPET = OIT_SNIPPET + withColorTargetStates(0, 1, supplier)   ⇒ 2 个 target

OitRenderPassProvider.createTransmittancePass(...):
  builder.withDepthAttachment(depth, empty);
  for (int i = 0; i < LevelRenderer.OIT_TRANSMITTANCE_TARGET_COUNT; i++)
      builder.withColorAttachment(transmittanceTargetViews[i], empty);          ⇒ 同一个常量个 attachment
```

**(c) 0 个 target 的管线只出现在 0 个 color attachment 的 pass 里**

```
LevelRenderer.executeAlwaysOnTop(...):
  RenderPassDescriptor.builder(() -> "Integrate always on top depth")
      .withDepthAttachment(depth)                 // 没有 color attachment
  ... setPipeline(RenderPipelines.INTEGRATE_DEPTH) // 而 INTEGRATE_DEPTH 声明 0 个 target
```

⇒ **不变量（vanilla 三条例子一起给的）**：*pipeline 的 color target 数量是照“它要被绑到哪个 pass”写的，
pass 有几个 attachment，pipeline 就必须声明几个*。这 8 条 ponder 管线要绑的是主 pass（1 个），所以它们
**少声明了 1 个**。

### 2.5 `setOitPipelines` 在 26.3 的语义（本轮已排除，但记下来）

`RenderSetup$RenderSetupBuilder#setOitPipelines(OitPipelineSet)` **仍然存在**，语义没变：它给 RenderType
挂上 depthBounds / transmittance / accumulate 三条 OIT 变体，`PreparedRenderType.drawFromBufferOit` 才用得到。
`OitPipelineSet.builder(locationSuffix, baseSnippet)` 会从 base snippet 派生 3 条管线。
**但 create jar 里 `setOitPipelines` / `OitPipelineSet` 出现 0 次**（全 14,336 entry 扫过），
`CreateRenderTypes` 的 `translucent()` 用的是 `RenderPipelines.TRANSLUCENT_BLOCK` 且不挂 OIT
⇒ **OIT 双目标路径与本次崩溃无关**，`docs/fix-diffuseshade.md` §8 的第 2 条猜想可以划掉。

同理 `RenderTypeFeatureRendererGroupMixin` / `RenderTypeMixin` / `RenderPipelineMixin` 只做
“priority 排序 / solidBlend 标记 / 跳过 blend 检查”，**都不碰 color target**（`withColorTargetState`
在整个 create jar 里只出现在 `AllRenderPipelines` 和 `PonderRenderPipelines` 两个类中，各 1 处调用点族）。

---

## 3. 判断：是「pipeline 声明少了 1 个」，不是「pass 挂少了」

| 假设 | 证据 | 判定 |
|---|---|---|
| pass 该挂 2 个却没挂 | 主 pass 由 `createRenderPass(label, color, …, depth, …)` 建，唯一 color attachment；vanilla 的 `pipeline/solid_block` 就是 1 个 target，chest 等原版方块正常 | ✗ |
| pipeline 声明多了（OIT 双目标） | 8 条 ponder 管线是 **0** 个 target，不是 2；create 里没有 `setOitPipelines` | ✗ |
| **pipeline 声明少了 1 个** | `targets=[]`（空数组）+ `passAttachments=1`；vanilla 同类管线写 `withColorTargetState(ColorTargetState.DEFAULT)` | ✓ |

---

## 4. 修法：单类 ASM，8 处 × 2 条指令

工具 `g20/asm/PatchPonderColorTarget.java`（ASM 9.10.1，`new ClassWriter(reader, COMPUTE_MAXS)`）。

在 `PonderRenderPipelines.<clinit>` 里，对每个
`invokestatic PonderRenderPipelines.register(String, RenderPipeline$Builder)`，如果它的 builder 链
（从最近一个 `RenderPipeline.builder(...)` 起）里**没有** `withColorTargetState`，就在 `register` 前插入：

```
getstatic     com/mojang/renderpearl/api/pipeline/ColorTargetState.DEFAULT
invokevirtual com/mojang/renderpearl/api/pipeline/RenderPipeline$Builder.withColorTargetState(L.../ColorTargetState;)L.../RenderPipeline$Builder;
```

**为什么安全**

* 栈形状 `[builder] → [builder]`，不新增分支 ⇒ 不需要重算 stack map frame；
* `ColorTargetState.DEFAULT` 恰好是“不混合 + RGBA8 + 写全通道”，与这 8 条管线在 26.2 时代的行为一致
  （它们本来就是不透明 `solid` / `cutout` 变体；`translucent` 变体原本就写了 `BlendFunction.TRANSLUCENT`）；
* **范围用名字白名单钉死**（`entity_block_solid/cutout`、`entity_block_light_solid/cutout`、
  `nether_entity_block_*` 共 8 条），因为 18 条 builder 链里有 11 条没写 `withColorTargetState`，
  其中 **3 条（`gui`、`triangle_fan`、`position_color_strip`）是从它们合并的 vanilla snippet 继承到
  1 个 target 的** —— 对它们再插一条会**覆盖** snippet 的 blend 语义（视觉回归）。清单见 `_ponder_chains.py`。

**唯一需要声明的不确定性**：这 8 条 RT 也用在 Ponder 场景里。但按台账，`ponder` 的几何体提交到 26.3 相位
（`PreparedFrame.execute*(RenderPass)`）**本来就还没做**、屏幕上没有动画 ⇒ 这条路径本轮不可能被“弄坏一个本来能用的东西”；
而 `ColorTargetState.DEFAULT` 的格式 `RGBA8_UNORM` 与 Ponder 目标的格式一致。真要接 Ponder 时，若发现它的 pass
attach 的不是 1 个 color，用 `g20/probe` 的 `phase=pipelines` + 日志里那条 `MISMATCH` 立刻能看出来。

**改动清单**

```
PonderRenderPipelines.class   patched entity_block_solid
                              patched entity_block_cutout
                              patched entity_block_light_solid
                              patched entity_block_light_cutout
                              patched nether_entity_block_solid
                              patched nether_entity_block_cutout
                              patched nether_entity_block_light_solid
                              patched nether_entity_block_light_cutout
                              chains=18 inserted=8
                              7984 B -> 8099 B
```

---

## 5. 逐方法 `javap -p -c` 比对（`g20/_clsdiff.py`，归一化掉常量池序号与指令偏移）

```
== PonderRenderPipelines.class
   members: old=25 new=25 SAME
   changed methods: 1 / 25
   --- static {};
       @@ -66,0 +67,2 @@
       +getstatic # // Field ColorTargetState.DEFAULT:L.../ColorTargetState;
       +invokevirtual # // Method RenderPipeline$Builder.withColorTargetState:(L.../ColorTargetState;)L.../RenderPipeline$Builder;
       @@ -81,0 +84,2 @@     （同上）
       @@ -111,0 +116,2 @@   （同上）
       @@ -124,0 +131,2 @@   （同上）
       @@ -154,0 +163,2 @@   （同上）
       @@ -169,0 +180,2 @@   （同上）
       @@ -201,0 +214,2 @@   （同上）
       @@ -216,0 +231,2 @@   （同上）
```

⇒ **除了这 8 处、每处恰好 2 条指令，25 个方法逐指令相同。**

**jar 级**（`g20/_entry_diff.py`）：

```
entries: old=14336 new=14336  order+set SAME
entries with different content: 1
  com/zurrtum/create/client/catnip/render/PonderRenderPipelines.class   7984 -> 8099  a9830186375bd443 -> 53c8d97dc8652226
```

其余 **14,335** 个 entry 解压后逐字节相同。

---

## 6. A/B（同一份探针、同一个世界模板、每次全新副本）

脚手架：`g20/probe/`（探针 mod，**永不进 `mods-stable`**）+ `g20/_mkmods.py` / `_mkworld.py` /
`_run_world.py`（从 g19 原样拷贝，`_mkmods.py` 多一个 probe 参数、`_mkworld.py` 多写一份
`sky262rast.cfg`）。世界模板 `g18/final/saves/lm-final`，**每次跑都重新拷贝**（`session.lock` 会删）。

探针 `phase=visible`：spectator 机位（方块前 6 格、高 3 格，正对）+ **一次放一个方块**，
布局是 **4 宽 × 2 高**的网格（单排 8 个会把第 5–8 个放到视锥外，“放了但没画”就没意义了）：

```
step0  minecraft:chest（对照）
step1  create:cogwheel[axis=y]            step5 create:cuckoo_clock[facing=north]
step2  create:fluid_tank                  step6 create:creative_motor[facing=up]
step3  create:white_postbox[facing=north] step7 create:shaft[axis=y]
step4  create:nixie_tube[...]             step8 create:gearbox[axis=y]
```

### 6.1 旧件（`DA3E5A9F…66EC9`，19,639,235 B）—— 崩

`g20/evidence/run-A2-old-visible.txt`

```
[run] title markers: ALL 3 HIT
[run] server_started=True joined=True marker_seen=False in 49.3s
[run] crash line: net.minecraft.ReportedException: Render Frame
[run] NoSuchMethodError lines: 0   NoSuchFieldError lines: 0
[run] RESULT: FAIL_CRASH
```

`g20/evidence/A2-old-visible-latest.log`

```
[sky262rast] step1-cogwheel  placing create:cogwheel[axis=y] at -325, 72, -37
[sky262rast] step2-fluid-tank placing create:fluid_tank at -326, 72, -37
[sky262rast] step3-white-postbox placing create:white_postbox[facing=north] at -327, 72, -37
Caused by: java.lang.IllegalStateException: Render pass color attachment count must match pipeline
 target color state count.
	at com.mojang.renderpearl.frontend.FrontendRenderPass.setPipeline(FrontendRenderPass.java:103)
	at net.minecraft.client.renderer.rendertype.PreparedRenderType.draw(PreparedRenderType.java)
	at net.minecraft.client.renderer.rendertype.PreparedRenderType.drawFromBuffer(PreparedRenderType.java:29)
	at net.minecraft.client.renderer.feature.RenderTypeFeatureRenderer.executeGroup(...)
	at net.minecraft.client.renderer.feature.FeatureRenderDispatcher$PreparedFrame.executeSolid(...)
	at net.minecraft.client.renderer.LevelRenderer.executeSolid(LevelRenderer.java:520)
```

（`run-A-old-visible.txt` 是更早一次、换布局前的旧件复现，同样 `FAIL_CRASH`；两次都是旧件崩。）

### 6.2 新件（`B6B1FD18…8888`，19,639,253 B）—— 不崩

`g20/evidence/run-B-new-visible.txt`（无 mixin 的探针，纯“能不能活”）

```
[run] title markers: ALL 3 HIT
[run] server_started=True joined=True marker_seen=True in 58.9s
[run] NoSuchMethodError 0 / NoSuchFieldError 0 / ExceptionInInitializerError 0 / NullPointerException 0
[run] RESULT: WORLD_OK
```

### 6.3 新件 + 只记日志的诊断探针（**证明 8 个方块真的被画了、且 0 次不匹配**）

`g20/evidence/run-B2-new-logonly.txt`（`-Dsky262rast.logonly=true`：不 cancel，任何不匹配都会照原样崩）

```
[run] server_started=True joined=True marker_seen=True in 69.4s
[run] RESULT: WORLD_OK
```

`g20/evidence/B2-new-logonly-latest.log`

```
[sky262rast] step1-cogwheel placing create:cogwheel[axis=y] at -325, 72, -37
...（8 条 placing 全在）...
[sky262rast] step8-gearbox placing create:gearbox[axis=y] at -328, 73, -37
[sky262rast] PHASE_DONE phase=visible wt=400 (8 create blocks placed)

[sky262rast] DRAWN rt='ponder:entity_block_solid'     pipelineTargets=1 passAttachments=1
[sky262rast] DRAWN rt='ponder:entity_block_cutout'    pipelineTargets=1 passAttachments=1
[sky262rast] DRAWN rt='ponder:entity_block_translucent' pipelineTargets=1 passAttachments=1
```

```
MISMATCH 行         : 0
"Render pass color attachment" : 0
IllegalStateException          : 0
```

`DRAWN` 行是本轮加进探针的“反证”：它由 `PreparedRenderType.draw` 的 HEAD 打出，**只有该 render type
真的被提交进帧才会出现**，所以这 8 个方块不是“放了没画”。

### 6.4 验收口径逐条对

| 口径 | 结果 |
|---|---|
| ≥8 个 Create 方块放眼前不崩 | **8 个全放（见上表），`WORLD_OK`** |
| `IllegalStateException` / `Render pass color attachment` / `NoSuchMethodError` / `FAIL_TIMEOUT` = 0 | **0 / 0 / 0 / 0**（B 与 B2 两份日志都 0） |
| A/B 方向 | 旧件 `FAIL_CRASH` → 新件 `WORLD_OK` |

---

## 7. 交付件本体回归（`mods-stable` **71 jar**，不带任何探针）

| 项 | 结果 | 证据 |
|---|---|---|
| 标题画面 | **`TITLE_SCREEN_OK`**，30.3 s（三标记全命中） | `g20/evidence/final-title.txt` |
| 进世界 | **`WORLD_OK`**，64.9 s（`joined=True`，`Loading 150 mods`，`Loaded 2343 advancements`） | `g20/evidence/final-world.txt` |
| `IllegalStateException` / `Render pass color attachment` / `NoSuchMethodError` / `NoSuchFieldError` / `ReportedException` / `FAIL_TIMEOUT` | **0 / 0 / 0 / 0 / 0 / 0** | `final-world-latest.log` |

> 第一次跑交付件时用的是上一个标题画面测试**用过的** `game-final` 目录，`quickPlaySingleplayer`
> 没生效、`FAIL_NO_JOIN`（241 s，日志停在标题画面）。换**全新** `game-final2` 目录 + 全新世界副本后一次
> `WORLD_OK` —— 与台账那条“每次用全新存档副本”一致，记录在此以免被误读成回归。
>
> 日志里有一条 `Couldn't load advancements: [createframed:…, dungeons_arise:…]`：旧件（`diag1`/`A2`）
> 与新件（`B2`）**逐字相同**，属既有数据问题，与本补丁无关。

---

## 8. 重扫（`tools/scan_landmines.py`）

```
python tools/scan_landmines.py --mods work/run26/mods-stable \
    --out work/run26/port/g20/scan-before.md --json .../scan-before.json     # 旧件在 mods-stable 时
python tools/scan_landmines.py --mods work/run26/mods-stable \
    --out work/run26/port/g20/scan-after.md  --json .../scan-after.json      # 交付新件后
```

| 指标 | 修前 | 修后 |
|---|---|---|
| **地雷总数** | **158** | **158** |
| 高危 / 中危 / 低危 | 32 / 54 / 72 | **32 / 54 / 72** |
| groups | 1120 | 1120 |
| 指令级原始命中 | 3393 | 3393 |
| 待验证 | 240 | 240 |

⇒ **没有变差**（本轮只加了两条对 `ColorTargetState.DEFAULT` / `withColorTargetState` 的
**已存在**成员引用，不引入任何新的缺类/缺方法/缺字段）。

---

## 9. 交付记录

| 项 | 值 |
|---|---|
| 交付文件 | `work/run26/mods-stable/create-fly-26.2-6.0.9-2-26.3-patched.jar` |
| 旧 SHA / 大小 | `DA3E5A9F4C85E1175375BAD572A586987E28B235D0E45D6B70979D2F1A466EC9` / 19,639,235 B |
| **新 SHA / 大小** | **`B6B1FD1840B845523B18F6DBCE938076187B001C0A046186470BFB45BDCB8888` / 19,639,253 B**（+18 B） |
| 备份 | `...jar.bak-rastpass`（19,639,235 B = 旧件本体） |
| entries | 14,336（与旧件完全一致，只有 1 个 class 内容变） |
| `mods-stable` jar 数 | **71** |
| 只在 1 个 class 里改动 | `com/zurrtum/create/client/catnip/render/PonderRenderPipelines.class` |

### 复现用资产（都在 `work/run26/port/g20/`）

| 文件 | 用途 |
|---|---|
| `asm/PatchPonderColorTarget.java` | 正式补丁（8 处 × 2 指令，名字白名单，内部断言 `inserted==8`） |
| `_patch_ponder.py` / `_rebuild_jar.py` / `_entry_diff.py` / `_clsdiff.py` | 打补丁 / 重打包 / entry 级差异 / 逐方法 javap 比对 |
| `_ponder_chains.py` | 列出 18 条 builder 链及“是否自带 color target”（说明白名单为什么必须是白名单） |
| `probe/`（`sky262rast-probe.jar` / `-nomixin.jar`） | `phase=visible` 探针；带 mixin 版做诊断，`-nomixin` 版做纯 A/B |
| `_mkmods.py` / `_mkworld.py` / `_run_world.py` | A/B 与交付验收脚手架 |
| `evidence/` | `diag1`、`run-A*`、`run-B*`、`final-title`、`final-world` 全部原始日志 |
| `scan-before.*` / `scan-after.*` | 重扫前后 |
| `_x/` | `javap -p -c` 的 26.3 权威转储（`RenderPipelines.txt`、`Oit.txt`、`RenderTypes.txt`、`PonderPipelines.txt`…） |

### 一句话交接

> **`ponder:pipeline/entity_block_{solid,cutout}` 等 8 条不透明管线声明了 0 个 color target，而 26.3 主 pass
> 恒有 1 个** ⇒ `setPipeline` 拒绝绑定 ⇒ 凡走 `SuperByteBuffer` / `EntityBlockRenderType` 的 Create 方块
> 一进画面就崩。补 = 逐条插 `withColorTargetState(ColorTargetState.DEFAULT)`（vanilla `pipeline/solid_block`
> 的写法），单 class / 8 处 / 16 条指令。旧件崩、新件 8 方块不崩，标题 + 进世界通过，地雷 158 不变。
> **下一个同类风险**：任何“管线没声明 color target 却要进主 pass”的第三方 jar —— 用
> `g20/probe` 的 `phase=pipelines`（dump `PIPELINES_BY_LOCATION` 里 targets!=1 的项）一跑就能列出来。
