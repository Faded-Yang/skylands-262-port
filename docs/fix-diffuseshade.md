# 修 `MutableQuadView.diffuseShade()`（地雷 #7）—— FRAPI 17 的等价是 `shadeDirectionOverride()`

> **结论**：`diffuseShade()` 确实被删了，但它**不是改名**，也没有被 `ShadeMode` 取代。
> FRAPI 17 保留的是**同一个属性的另一种表示**：`shadeDirectionOverride()`（可空 `Direction`）。
> 逐位等价是
>
> ```java
> diffuseShade()  ==  (quad.shadeDirectionOverride() == null)
> ```
>
> 4 个 class、每个 class **1 条 `invokeinterface` 被换成 2 条无分支指令**；jar 里其余 14,332 个 entry 内容逐字节不动。
> A/B：旧交付件 `NoSuchMethodError: '...diffuseShade()'`（2 行）+ `FAIL_TIMEOUT`；新件 **0 行**。
>
> **但「方块放眼前不崩」这条验收只被 2 个方块满足，不是全部** —— 修掉本族后，
> 带半透明部分或 flywheel visual 的 Create 方块会撞**另一个独立缺陷**
> （`IllegalStateException: Render pass color attachment count must match pipeline color target state count`）。
> 已用「把 boolean 硬写成常量 `true`」的对照件证明该崩溃与本补丁无关，详见 §8。

---

## 0. 并行冲突：开工人 / 交付时的 `create-fly` 基线

上一轮两个代理同时改同一个 jar 撞过基线，所以先声明。

| 时点 | SHA-256 | 大小 | mtime |
|---|---|---|---|
| **开工时**（15:49 读） | `3943433B3BF87D295E309E70D0E41BF07266F3186D8AEA814641A638BBF20423` | 19,639,085 B | 2026-10-18 15:37:41 |
| **中途复核**（16:02） | 同上（未变） | 同上 | 同上 |
| **交付前复核**（见 §11） | 同上（未变） | 同上 | 同上 |

⇒ 本轮**没有**并行代理改动这个 jar，补丁基于唯一基线 `3943433B…0423`。
备份名用 `.bak-diffuseshade`（没有碰别人的 `.bak-clock` / `.bak-shader` / `.bak-ponder`）。

台账里记的 `6DD6B46F…ED9B` 是**旧基线**（对应 `.bak-clockfamily`），已被更晚的修复取代；以本表为准。

---

## 1. 旧语义（这个 jar 是对着 FRAPI **16** 编的）

证据不是回忆，是 **Maven 上的源码 jar**：
`net.fabricmc.fabric-api:fabric-renderer-api-v1:16.0.0+bca5816925-sources.jar`
（下载自 `https://maven.fabricmc.net/`，解包在 `g19/_fapi/src16/`）。

`MutableQuadView.java`（16.0.0）：

```java
/**
 * Controls whether vertex colors should be modified for diffuse shading.
 *
 * <p>The default value is {@code true}.
 *
 * <p>This property is guaranteed to be respected in block contexts. ...
 */
MutableQuadView diffuseShade(boolean shade);
```

`QuadView.java`（16.0.0）—— **getter 的 javadoc 直接给出了等价关系**：

```java
/**
 * This method is equivalent to checking {@link BakedQuad.MaterialInfo#shadeDirectionOverride()}.
 *
 * @see MutableQuadView#diffuseShade(boolean)
 */
boolean diffuseShade();
```

同一份 `QuadView.java` 的 `toBakedQuad()`（API 自己的编码方向，等价关系的**符号**在这里定下来）：

```java
Direction shadeDirectionOverride = diffuseShade() ? null : Direction.UP;
```

⇒ **`diffuseShade()==true` ⟺ `shadeDirectionOverride == null`**；`false` ⟺ 被钉成 `Direction.UP`
（UP 的漫反射系数是 1.0 ⇒ 视觉上等于「不打方向性明暗」）。

调用点确实是**读**这个属性（不是设）：4 个 mixin 的 `lambda$quadEmitter$0` 里都是
`invokeinterface MutableQuadView.diffuseShade:()Z`，返回值直接当 `getBuffer(...)` 的 `shade` 形参：

```
jshell> javap -p -c BufferPoseEmitterMixin
  7: invokeinterface MutableQuadView.diffuseShade:()Z
 12: invokeinterface MutableQuadView.chunkLayer:()LChunkSectionLayer;
 18: invokeinterface getBuffer:(ZLChunkSectionLayer;)LVertexConsumer;
```

全 jar 只有这 4 处引用，**没有任何一处调用 setter** `diffuseShade(Z)` ⇒ 运行期该值恒等于默认值 `true`。

---

## 2. FRAPI 17 的真身（26.3 运行期）

`fabric-renderer-api-v1-17.0.16+79385d0b5d`（`fabric-api-0.163.0+26.3.jar` 内嵌，见 `g19/_fapi/`）：

```text
$ javap -p net.fabricmc.fabric.api.client.renderer.v1.mesh.MutableQuadView
  ...
  MutableQuadView emissive(boolean);
  MutableQuadView shadeDirectionOverride(net.minecraft.core.Direction);
  MutableQuadView ambientOcclusion(TriState);
  MutableQuadView shadeMode(ShadeMode);
  ...
  （没有 diffuseShade，也没有 diffuseShade(Z)）
```

`QuadView` 里的对应 getter：

```text
  Direction lightFace();
  Direction nominalFace();
  boolean emissive();
  Direction shadeDirectionOverride();     // @Nullable
  TriState ambientOcclusion();
  ShadeMode shadeMode();
```

### `ShadeMode` 是什么

`ShadeMode.java`（17.0.16 源码，`g19/_fapi/src17/...`）—— **只有两个常量**：

```java
/**
 * A hint to the renderer about how the quad is intended to be shaded, for example through ambient
 * occlusion and diffuse shading. The renderer is free to ignore this hint.
 */
public enum ShadeMode {
    /** shading 一致、无边缘 case、视觉好看（给 vanilla 造不出来的 quad 用） */
    ENHANCED,
    /** shading 模仿 vanilla 结果（保住资源包改模型产生的观感） */
    VANILLA;
}
```

`MutableQuadView.shadeMode` 的 javadoc：**`The default value is ShadeMode.ENHANCED`**，而且
`MutableQuadViewImpl.shadeMode(...)` 第一句就是 `Objects.requireNonNull(mode, "ShadeMode may not be null")`
⇒ **`shadeMode` 永远非 null，它无法表达「不参与方向性明暗」**。

### 所以 `shadeMode` 不是替代品

Indigo 17 自己的用法把两者分得很清楚（`g19/_fapi/isrc/.../render/AltModelBlockRendererImpl.java:126`）：

```java
shadeQuad((MutableQuadViewImpl) quad, ao, quad.emissive(), quad.shadeMode() == ShadeMode.VANILLA);
```

`shadeMode` 只选**算法**（vanilla 式 / enhanced 式），真正决定「用哪个方向算亮度」的是
`shadeDirectionOverride`（`isrc/.../aocalc/FlatLighter.java:48-58`）：

```java
final Direction shadeDirectionOverride = quad.shadeDirectionOverride();
if (shadeDirectionOverride != null) {
    final float directionalBrightness = cardinalLighting.byFace(shadeDirectionOverride);
    ...scale every vertex color...
}
```

这正是 FRAPI 16 里 `if (!quad.diffuseShade()) { ...byFace(Direction.UP)... }` 的**同一条分支**
（16 的 indigo `FlatLighter.java:49` 就是 `if (!quad.diffuseShade()) {`）。
在 26.2 里 `diffuseShade=false` 被编码成 `shadeDirectionOverride=UP`，26.3 只是把中间那层 boolean 删了。

### 26.3 vanilla 自己的写法（权威背书）

vanilla 26.3 的 `BakedQuad$MaterialInfo` 已经是 record，字段就叫 `shadeDirectionOverride`：

```text
$ javap -p -classpath .../versions/26.3/26.3.jar net.minecraft...BakedQuad$MaterialInfo
  private final net.minecraft.core.Direction shadeDirectionOverride;
  public net.minecraft.core.Direction shadeDirectionOverride();
```

`BlockModelLighter.getDirectionalBrightness`（字节码等价源码）：

```java
Direction d = quad.materialInfo().shadeDirectionOverride();
return cardinalLighting.byFace(d != null ? d : quad.direction());
```

**vanilla 也是「非空 ⇒ 用这个方向；null ⇒ 用 quad 自己的方向」**，与 Indigo 17 一致。

而 FRAPI 17 自己的 vanilla 模型编码器（**就是崩栈上那一个 class**）
`VanillaBlockModelPartEncoder.emitQuads`（`src17/.../VanillaBlockModelPartEncoder.java:55-58`）：

```java
emitter.cullFace(cullFace);
emitter.fromBakedQuad(q);            // ← 这里把 materialInfo.shadeDirectionOverride() 原样抄进 quad
emitter.ambientOcclusion(ao);
emitter.shadeMode(ShadeMode.VANILLA);   // vanilla 模型走 VANILLA 档
emitter.emit();
```

`MutableQuadViewImpl.fromBakedQuad`（indigo 17，`isrc/.../mesh/MutableQuadViewImpl.java:340`）：

```java
tintIndex(materialInfo.tintIndex());
shadeDirectionOverride(materialInfo.shadeDirectionOverride());
emissive(lightEmission == 15);
```

⇒ 本补丁执行的那一刻，`shadeDirectionOverride()` 里装的就是 vanilla `BakedQuad` 的
`MaterialInfo.shadeDirectionOverride`，与 FRAPI 16 里 `diffuseShade()` 的来源**是同一个字段**。

**选档结论**：不选 `ShadeMode` 的任何一个档（它是算法开关，不是本属性的替代）；
本属性用 `shadeDirectionOverride() == null` 还原，`ShadeMode` 保持 `fromBakedQuad` 之后的默认
（vanilla 模型 = `VANILLA`，mod 自建 quad = `ENHANCED`）—— 与 16 时代行为一致。

---

## 3. 补丁（单方法指令替換，纯 ASM）

工具：`g19/asm/PatchDiffuseShade.java`（ASM 9.10.1，`new ClassWriter(0)` 全新常量池）。

```
invokeinterface MutableQuadView.diffuseShade:()Z
  ↓
invokeinterface MutableQuadView.shadeDirectionOverride:()Lnet/minecraft/core/Direction;
invokestatic    java/util/Objects.isNull:(Ljava/lang/Object;)Z
```

为什么安全：

* 两条指令的**栈形状**与原来一致（吃掉 receiver、留下一个 `int`），所以 `maxStack` / `maxLocals` 都不用重算；
* **不新增分支** ⇒ 不需要重算 stack map frame（`ClassWriter(0)` 直接沿用原帧）；
* 用**全新 ClassWriter**（而不是 `new ClassWriter(reader, 0)`）⇒ 死掉的 `diffuseShade` 常量池条目不会残留；
* `Objects.isNull` 是 JDK7+ 的 `obj == null`，与 `== null` 语义完全相同。

改动清单（4 个 class，每类恰好 1 处，ASM 工具内部断言 `patched==1 && residual==0`）：

```
BufferEmitterMixin.class           patched=1  in=2389 out=2497  residual=0
BufferPoseEmitterMixin.class       patched=1  in=2932 out=3040  residual=0
BufferColorPoseEmitterMixin.class  patched=1  in=3135 out=3243  residual=0
BufferAoPoseEmitterMixin.class     patched=1  in=3229 out=3343  residual=0
```

---

## 4. 逐方法 `javap -p -c` 比对（`g19/_clsdiff.py`，归一化掉常量池序号与指令偏移）

```
== BufferEmitterMixin.class
   members: old=3 new=3 SAME
   changed methods: 1 / 3
   --- private void lambda$quadEmitter$0(MutableQuadView);
       -invokeinterface #, 1 // InterfaceMethod MutableQuadView.diffuseShade:()Z
       +invokeinterface #, 1 // InterfaceMethod MutableQuadView.shadeDirectionOverride:()Lnet/minecraft/core/Direction;
       +invokestatic # // Method java/util/Objects.isNull:(Ljava/lang/Object;)Z
== BufferPoseEmitterMixin.class
   members: old=3 new=3 SAME
   changed methods: 1 / 3        （同上）
== BufferColorPoseEmitterMixin.class
   members: old=3 new=3 SAME
   changed methods: 1 / 3        （同上）
== BufferAoPoseEmitterMixin.class
   members: old=4 new=4 SAME
   changed methods: 1 / 4
       同上 + `ifnonnull 33 -> 36`（插入 3 字节后跳转目标整体后移，是偏移不是语义）
```

⇒ **除了目标 lambda 的那一条指令，4 个 class 的每个方法都逐指令相同。**

---

## 5. jar 级：只有这 4 个 entry 变（`g19/_entry_diff.py`）

```
entries: old=14336 new=14336  order+set SAME
entries with different content: 4
  com/zurrtum/create/client/mixin/BufferAoPoseEmitterMixin.class     3229 -> 3343
  com/zurrtum/create/client/mixin/BufferColorPoseEmitterMixin.class  3135 -> 3243
  com/zurrtum/create/client/mixin/BufferEmitterMixin.class           2389 -> 2497
  com/zurrtum/create/client/mixin/BufferPoseEmitterMixin.class       2932 -> 3040
```

其余 **14,332** 个 entry 解压后内容逐字节相同（entry 顺序、时间戳、属性也沿用原件）。
jar 大小 19,639,085 → **19,639,235 B**（+150 B）。

---

## 6. 验收脚手架（g19 新建，没碰 `watch`）

`work/run26/port/g19/` 复用了 g17 的 `_mkmods.py` / `_mkworld.py` / `_run_world.py`（原样拷贝，
路径全部按脚本自身目录推导），只改**探针 mod** `probe/src/skylands262/clockprobe/ClockProbe.java`：

* `phase=visible`：把方块摆在**相机正前方 5 格**，然后 `/gamemode spectator @a` + `/tp` 到
  已知机位（后方 6 格、上方 3 格）**正对**方块 ⇒ "方块有没有进画面"不再是变量；
* **一次一个方块**（wt=10 原版箱子作对照 → wt=20 布谷鸟钟 → wt=30 创意马达 → …），
  崩了就能从"最后一条 placing"直接读出凶手；
* 世界模板：`g18/final/saves/lm-final`（上一轮交付验收的 26.3 干净世界），**每次跑都重新拷贝**
  （`_mkworld.py` 只读模板，`session.lock` 会删）。

> 探针永远只进一次性 `g19/mods-*`，**不会**进 `mods-stable`。

---

## 7. A/B（同一份探针、同一个世界模板、全新副本）

### 7.1 旧件（当前交付件 `3943433B…0423`）—— 应该崩

`g19/evidence/run-ctrl2-visible.txt`

```
[run] title markers: ALL 3 HIT
[run] server_started=True joined=True marker_seen=False in 200.6s
[run] NoSuchMethodError lines: 2
[mc] step0-vanilla-chest   ... ChestBlockEntity
[mc] step1-cuckoo          ... CuckooClockBlockEntity
[mc] step2-motor           ... CreativeMotorBlockEntity
[mc] step3-fluid-tank      ... FluidTankBlockEntity
[mc] step4-postbox         ... PostboxBlockEntity
[mc] com.google.common.util.concurrent.ExecutionError: java.lang.NoSuchMethodError:
     'boolean net.fabricmc.fabric.api.client.renderer.v1.mesh.MutableQuadView.diffuseShade()'
[run] RESULT: FAIL_TIMEOUT
```

崩栈与地雷表一致（`g17` 已有同款证据，本轮独立复现）：

```
SuperByteBufferCache.get -> CachedBuffers.partialFacing -> CuckooClockRenderer.extractRenderState:55
Caused by: NoSuchMethodError: ... MutableQuadView.diffuseShade()
   at BufferPoseEmitter...lambda$quadEmitter$0$0
   at SodiumRenderer$1.emitDirectly
   at VanillaBlockModelPartEncoder.emitQuads
```

### 7.2 新件 —— `diffuseShade` 归零

`g19/evidence/run-fixed2-visible.txt` / `run-fixed3-visible.txt` / `run-const-visible.txt` 全部：

```
[run] NoSuchMethodError lines: 0
[run] NoSuchFieldError lines: 0
```

布谷鸟钟、创意马达在画面里正常渲染（它们各自在场景里活了 ≥1 s、多帧），
**`diffuseShade` 这条链彻底不再报错**。

### 7.3 但"方块放眼前不崩"没有全部达成（如实记）

修掉本族之后，**下一层**缺陷露出来了（见 §8）：`create:cogwheel` / `create:fluid_tank` /
`create:white_postbox` / `create:nixie_tube` 一进画面就崩；`create:cuckoo_clock` /
`create:creative_motor` 不崩。

⇒ 本族（`diffuseShade`）**已修好并验证**；但"凡走 SuperByteBufferCache 的方块看一眼都不崩"这个
**更大**的目标仍被 §8 的独立缺陷挡住。时钟那两个方块（任务点名的两个渲染器）已经安全。

---

## 8. 独立缺陷（**不属于本族**，本轮只测量、不修）

```
java.lang.IllegalStateException: Render pass color attachment count must match pipeline color
target state count.
  at com.mojang.renderpearl.frontend.FrontendRenderPass.setPipeline(FrontendRenderPass.java:103)
  at net.minecraft.client.renderer.rendertype.PreparedRenderType.draw(...)
  at ...FeatureRenderDispatcher$PreparedFrame.executeSolid(FeatureRenderDispatcher.java:142)
  at net.minecraft.client.renderer.LevelRenderer.executeSolid(LevelRenderer.java:520)
```

测量（全部 `phase=visible`，一次放一个方块）：

| 方块 | 结果 |
|---|---|
| `minecraft:chest`（对照） | 正常 |
| `create:cuckoo_clock` | **正常**（本补丁要救的那个） |
| `create:creative_motor` | **正常** |
| `create:cogwheel` | 崩（`BracketedKineticBlockEntityVisual` 一路，flywheel visual） |
| `create:fluid_tank` | 崩 |
| `create:white_postbox` | 崩 |
| `create:nixie_tube` | 崩 |

**为什么能断定与本补丁无关**：另做了一份**对照件**——同样 4 个 class、同样 4 处站点，
但把 boolean 换成**常量 `true`**（`g19/asm/PatchDiffuseShadeConst.java`，栈形状仍是 1 个值）。
常量 `true` 正是 FRAPI 16 对所有原版模型 quad 的默认返回值，所以「值取错」这条路被排除：

`g19/evidence/run-const-visible.txt`：

```
[run] NoSuchMethodError lines: 0
[mc] step1-cuckoo  ok   step2-motor  ok   step3-postbox ...
[run] crash line: net.minecraft.ReportedException: Render Frame
```

⇒ 常量 `true` 也一样死在 postbox 上，**崩溃与 `diffuseShade` 的取值无关**。

**下一步该查什么（给接手的代理）**：
`AllRenderPipelines` 的 5 条自建 pipeline（ADDITIVE / ADDITIVE2 / GLOWING / GLOWING_TRANSLUCENT /
CUBE）都用 `withColorTargetState(...)` 建了一条 color target；`CreateRenderTypes` 用它们做
`RenderSetup`。26.3 的 `FrontendRenderPass.setPipeline` 会拿 pass 的 attachment 数去对
pipeline 的 color target 数。可疑点：

1. 带半透明部分的方块（fluid_tank 的玻璃窗、postbox）走 `CreateRenderTypes.translucent()`；
2. `RenderSetupBuilder.setOitPipelines(OitPipelineSet)`（26.3 的 OIT 双目标路径）是否被错误地
   挂到了主 pass 上；
3. `create.client.mixins.json` 里的 `RenderTypeFeatureRendererGroupMixin` / `RenderTypeMixin` /
   `RenderPipelineMixin` 是否改了 vanilla pipeline 的 color target。

---

## 9. 交付件的回归（71 jar 本体）

交付后**立即**拿 `work/run26/mods-stable`（71 jar，无探针）跑：

| 项 | 结果 | 证据 |
|---|---|---|
| 标题画面 | **`TITLE_SCREEN_OK`**，27.0 s（三标记全命中） | `g19/evidence/final-title.txt` |
| 进世界 | **`WORLD_OK`**，43.8 s（`joined=True`，`Loading 150 mods` 一路正常） | `g19/evidence/final-world.txt` |
| NoSuchMethodError / NoSuchFieldError / ExceptionInInitializerError / NullPointerException | **0 / 0 / 0 / 0** | 同上 |

（`launch.py` 必须带 `--watch-title` 才会在命中三标记后自己收工；第一次忘带，跑到 150 s 超时
但三标记在 46 s 就全命中了，重跑即 `TITLE_SCREEN_OK`。）

---

## 10. 重扫（`tools/scan_landmines.py`）

```
python tools/scan_landmines.py --mods work/run26/mods-stable --out work/run26/port/g19/scan-after.md
```

| 指标 | 修前（台账记录的 159） | 修后 |
|---|---|---|
| **地雷总数** | 159 | **158** |
| 高危 / 中危 / 低危 | — / — / — | **32 / 54 / 72** |
| `diffuseShade` 相关条目 | **1 条（4 个站点）** | **0**（`Select-String diffuseShade` 命中 0 行） |
| 缺类 / 缺方法 / 缺字段 | — | 41 / 98 / 19 |
| 待验证 | — | 240 |

`diffuseShade` **归零**。总数只少 1（该条目是"同成员 4 站点算 1 条"）。

---

## 11. 交付记录

| 项 | 值 |
|---|---|
| 交付文件 | `work/run26/mods-stable/create-fly-26.2-6.0.9-2-26.3-patched.jar` |
| 旧 SHA / 大小 | `3943433B3BF87D295E309E70D0E41BF07266F3186D8AEA814641A638BBF20423` / 19,639,085 B |
| **新 SHA / 大小** | **`DA3E5A9F4C85E1175375BAD572A586987E28B235D0E45D6B70979D2F1A466EC9` / 19,639,235 B** |
| 备份 | `...jar.bak-diffuseshade`（19,639,085 B，= 旧件本体） |
| entries | 14,336（与旧件完全一致，只 4 个 class 内容变） |
| `mods-stable` jar 数 | **71** |
| 交付前 `create-fly` 复核 | `3943433B…0423`（未变 ⇒ 无并行冲突，补丁基于唯一基线） |

### 复现用资产（都在 `work/run26/port/g19/`）

| 文件 | 用途 |
|---|---|
| `asm/PatchDiffuseShade.java` | 正式补丁（`shadeDirectionOverride()==null`） |
| `asm/PatchDiffuseShadeConst.java` | 对照件（常量 `true`），只用来证明 §8 与本补丁无关 |
| `_patch4.py` / `_rebuild_jar.py` / `_entry_diff.py` / `_clsdiff.py` | 打补丁 / 重打包 / entry 级差异 / 逐方法 javap 比对 |
| `probe/src/.../ClockProbe.java` | `phase=visible` 探针（相机机位 + 一次一个方块） |
| `_mkmods.py` / `_mkworld.py` / `_run_world.py` | A/B 脚手架（从 g17 原样拷贝） |
| `evidence/run-*.txt` | 6 次 A/B 的原始输出 |
| `scan-after.md` / `scan-after.json` | 重扫结果 |
| `_fapi/src16` `_fapi/src17` `_fapi/isrc` | 从 maven 拉的 FRAPI 源码（语义证据） |

### 一句话交接

> `diffuseShade` 已按语义修好（`shadeDirectionOverride()==null`），4 class / 1 指令，A/B 双向通过，
> 重扫归零；**下一族**是 `Render pass color attachment count must match pipeline color target
> state count`（`CreateRenderTypes` / `AllRenderPipelines` 的 pipeline 与 26.3 pass 的 color target 数），
> 它才是"看一眼 Create 方块就崩"现在剩下的主因。
