# fix-landmines-2 —— 修 `PonderRenderTypes.<clinit>` 家族（`setOutputTarget` / `OutputTarget.ITEM_ENTITY_TARGET`，create-fly jar，纯 ASM）

> **结论：这一族修好了。`PonderRenderTypes` 的 `<clinit>` 现在能跑完，穿 backtank 的那条路径不再崩在这一行**
> —— 它往前推进了整整一层，撞上**表里另一族**地雷（`MutableQuadView.diffuseShade()`，现 #7）。
>
> | 项 | 结果 |
> |---|---|
> | 类初始化 A/B | 旧件 `PonderRenderTypes` → **`NoClassDefFoundError: .../OutputTarget`**（`PONDER_CLINIT_FAIL`）；新件 → **`PONDER_CLINIT_OK`**，15/15 静态字段非 null，15 个工厂全非 null，`EntityBlockRenderType` 6/6 解析出真 RenderType |
> | **玩法级（穿 backtank）A/B** | 旧件：`ReportedException` → **`PonderRenderTypes.<clinit>(PonderRenderTypes.java:38)`**；新件：**这一处不再出现**，同一调用栈推进到 `MutableQuadView.diffuseShade()`（另一族） |
> | 交付件改动 | jar 内**只换 1 个 class**（9201 → 8824 B，14336 entries 其余逐字节不动） |
> | `mods-stable` | 仍 **71 jar**（改已有 jar，未加新 jar） |
> | 交付件本体回归 | **`TITLE_SCREEN_OK` 27.8 s** + **`WORLD_OK` 45.4 s**；`Registry loading errors` / `NoSuchMethodError` / `NoSuchFieldError` / `ExceptionInInitializerError` / `NPE` / `ReportedException` / `neighbours` **全 0** |
> | 重扫 | `create-fly` 地雷 **86 → 83**（高危 29→27 / 中危 17→16 / 低危 40→40），`OutputTarget` 三组**全部归零**（0 命中） |
>
> ⚠ **没有判定为「需要产品决策」**：这一族是「概念整个没了 ⇒ 去掉那一步」，不是猜语义（理由见 §2.3）。
> ⚠ 但 backtank 的**可见画面**仍未验到（被 #7 挡在更深处，见 §6.3），且 ponder 的 GLSL 在 26.3 编译失败
> （**改前/改后都失败**，独立既有问题，见 §6.4、§9.2）。

---

## 0. 本轮用的目录（`work/run26/watch` 全程未读写）

```
work/run26/port/g16/
  asm/PatchPonder.java          一次性 ASM 工具（mode 只有一个：drop-setOutputTarget）
  oldcls/ newcls/               改前 / 改后 的 PonderRenderTypes.class（包路径完整）
  dump_old.txt / dump_new.txt   javap -p -c 全量
  _javap_cmp.py(借 g15) / _instr_cmp.py   逐方法、逐指令（去偏移）比对
  _mkmods.py / _mkworld.py / _run_world.py / _deliver.py / _jar_diff.py / _patch_jar.py   由 g15 改名而来
  _javac_npe.py / _build_probe.py          探针 mod 编译与打包
  probe/                        一次性驱动 mod（sky262lm-probe.jar，**不进交付**）
  mods-control / mods-fixed     各 70 硬链接 jar + create（旧件/新件）+ 探针 = 72 文件
  game-ponder-control / game-ponder-fixed / game-bt-control / game-bt-fixed / final
                                **每次都是存档模板的全新副本**（用一次就换名字）
  evidence/                     每次的 latest.log / console.log
  scan_after.md / scan_after.json
```

`work/run26/stag1` 只作为 `options.txt / config / defaultconfigs` 的来源读取；
`mods-full` / `mods-fix2` / `mods-crashfix` / `work/sable-26` / `work/build26` / `g6`–`g15` 未改动。

---

## 1. `PonderRenderTypes.<clinit>` 到底在建什么

`javap -p -c` 全量（`dump_old.txt`）：类里只有 **15 个 `private static final` 字段 + 13 个 public getter +
2 个合成 lambda + 1 个 `createLayerName`**。`<clinit>` 一次性把 15 个字段全建出来，顺序固定：

| # | 字段 | pipeline | 额外步骤 |
|---|---|---|---|
| 1 | `ENTITY_BLOCK_SOLID` | `PonderRenderPipelines.ENTITY_BLOCK_SOLID` | `withTexture("Sampler0", TextureAtlas.LOCATION_BLOCKS)` + `useLightmap` + `affectsCrumbling` + `setOutline(AFFECTS_OUTLINE)` + **`CustomRenderType.markPriority(...)`** |
| 2 | `ENTITY_BLOCK_CUTOUT` | `…ENTITY_BLOCK_CUTOUT` | 同上（无 markPriority） |
| 3 | `ENTITY_BLOCK_TRANSLUCENT` | `…ENTITY_BLOCK_TRANSLUCENT` | `withTexture` + **`setOutputTarget(ITEM_ENTITY_TARGET)`** + `useLightmap` + `affectsCrumbling` + `sortOnUpload` + `setOutline` |
| 4–6 | `ENTITY_BLOCK_LIGHT_{SOLID,CUTOUT,TRANSLUCENT}` | `…ENTITY_BLOCK_LIGHT_*` | 与 1–3 同形（第 6 个带 `setOutputTarget`） |
| 7–12 | `NETHER_ENTITY_BLOCK_*` / `NETHER_ENTITY_BLOCK_LIGHT_*` | `…NETHER_ENTITY_*` | 与 1–6 逐项同形（第 9、12 个带 `setOutputTarget`） |
| 13 | `GUI` | `PonderRenderPipelines.GUI` | 无纹理，只 `setLayeringTransform(new LayeringTransform("view_offset_z_layering_gui", RenderSystem.getProjectionType()::applyLayeringTransform))` |
| 14 | `OUTLINE_SOLID` | `RenderPipelines.ENTITY_SOLID` | `Sampler0 = PonderSpecialTextures.BLANK.getLocation()` + lightmap + overlay + `setOutline(IS_OUTLINE)` |
| 15 | `OUTLINE_TRANSLUCENT` | —— | `Util.memoize(BiFunction<Identifier,Boolean,RenderType>)`，body 是 `lambda$static$1` |

`lambda$static$1(id, cull)`：`createLayerName("outline_translucent" + (cull ? "_cull" : ""))` +
`(cull ? PonderRenderPipelines.ENTITY_TRANSLUCENT_CULL : …ENTITY_TRANSLUCENT)` + `Sampler0 = <参数>` +
`sortOnUpload` + `useLightmap` + `useOverlay` + **`setOutputTarget(ITEM_ENTITY_TARGET)`** + `setOutline(IS_OUTLINE)`。

### 1.1 五个站点（就是地雷表第 1 号的全部 5 处）

```
<clinit>       102: getstatic OutputTarget.ITEM_ENTITY_TARGET    <- ENTITY_BLOCK_TRANSLUCENT
               105: invokevirtual RenderSetupBuilder.setOutputTarget
<clinit>       234/237                                            <- ENTITY_BLOCK_LIGHT_TRANSLUCENT
<clinit>       366/369                                            <- NETHER_ENTITY_BLOCK_TRANSLUCENT
<clinit>       498/501                                            <- NETHER_ENTITY_BLOCK_LIGHT_TRANSLUCENT
lambda$static$1 56/59                                             <- OUTLINE_TRANSLUCENT（第 5 处）
```

**语义判定**：这一对指令的栈形状是「消耗 `[builder]` → 产出 `[builder]`」，纯副作用；
它把「这个 RenderType 画到哪个 framebuffer」记进 `RenderSetup`。
4 个带它的都是 **translucent**（半透明要单独凑一批、按深度排序后再合成），第 5 个是 **outline translucent**
—— 和 vanilla 自己的 `item_translucent` / `glint_translucent` / `entity_translucent_cull_item_target`
用的是同一个 target，属于从 vanilla 抄过来的写法。

---

## 2. 26.3 里这个「输出目标」概念还剩什么（javap 现查）

### 2.1 26.3：类没了、方法没了、字段也没了

| 检查 | 26.1.2 | 26.3 |
|---|---|---|
| `net/minecraft/client/renderer/rendertype/OutputTarget` | **有**（4 个常量） | **0 个 entry**（整个 jar 里没有这个类） |
| `RenderSetupBuilder.setOutputTarget(OutputTarget)` | 有 | **没有**（builder 只有 13 个方法，见下） |
| `RenderType.outputTarget()` | 有（`public OutputTarget outputTarget()`） | **没有** |
| `RenderSetup` 字段 | 含 `outputTarget` | `pipeline / oitPipelineSet / textures / textureTransform / outlineProperty / outlineTextureName / useLightmap / useOverlay / affectsCrumbling / sortOnUpload / layeringTransform / forceSolidModelPhase` |
| `LevelRenderer.getItemEntityTarget()` | 有（`OutputTarget.ITEM_ENTITY_TARGET` 的 supplier 指向它） | **没有**（换成 `LevelTargetBundle` + `executeOit`） |

26.1.2 的 `OutputTarget` 四个常量（`javap -c` 原文）：
`MAIN_TARGET → Minecraft.getMainRenderTarget()`、
`OUTLINE_TARGET → levelRenderer.entityOutlineTarget()`、
`WEATHER_TARGET → levelRenderer.getWeatherTarget()`、
**`ITEM_ENTITY_TARGET → levelRenderer.getItemEntityTarget()`**。
—— 它就是「这一批几何体写进 item entity 的那张离屏图，主画面再合成」。

26.3 的 `RenderSetupBuilder` 全量：`withTexture(String,Identifier)` / `withTexture(String,Identifier,Supplier)` /
`useLightmap` / `useOverlay` / `affectsCrumbling` / `sortOnUpload` / `setLayeringTransform` /
`setTextureTransform` / `setOutline(OutlineProperty)` / `setOutline(OutlineProperty,String)` /
**`setOitPipelines(OitPipelineSet)`** / `withForcedSolidModelPhase` / `createRenderSetup`。

### 2.2 vanilla 自己怎么改的（这才是判「等价物」的依据）

26.1.2 的 `RenderTypes` 里有 7 处 `ITEM_ENTITY_TARGET`，26.3 的 `RenderTypes` 里 **0 处**。逐项对照：

| 26.1.2 用法 | 26.3 同形方法怎么处理 |
|---|---|
| `createMovingBlockSetup(pipeline, true)`（半透明移动方块） | 26.3 的 `solid/cutout/translucent_moving_block`：**没有 target** |
| `lambda$static$9` = **`entity_translucent_cull_item_target`** | 该方法在 26.3 **仍然叫这个名字**（`String entity_translucent_cull_item_target`），但 builder 链里**没有 target、也没有 OIT** |
| `lambda$static$11` = **`item_translucent`** | 26.3 的 `item_translucent`：`withTexture` → `useLightmap` → `useOverlay` → `affectsCrumbling` → `sortOnUpload` → `setOutline` → `createRenderSetup`，**没有 target** |
| `<clinit>` 的 `glint_translucent` | 26.3 同样**没有 target** |
| `<clinit>` 的 `lines` / `lines_translucent` / `secondary_block_outline` | 26.3 **改成 `setOitPipelines(RenderPipelines.OIT_LINES_TRANSLUCENT)`**（并且多了 `lines_translucent_no_depth_write` / `lines_translucent_depth_bias` 两个带 OIT 的新变体） |

⇒ 26.3 把原来一个 `outputTarget` 概念**拆成两条互斥的去向**：
**半透明的 item/entity/glint 类**——彻底不要 target（由调用它的那一趟 pass 决定）；
**lines/debug/自定义透明**——挂一个 `OitPipelineSet`（`LevelRenderer.executeOit` 那套 OIT 合成）。
「item entity target」这张离屏图本身在 26.3 没有了：`LevelRenderer` 只剩 `entityOutlineTarget` +
`LevelTargetBundle` + `OIT_*` 一堆 target。

### 2.3 所以这一族是「概念整个没了 ⇒ 去掉那一步」，不是猜语义

- 没有任何 26.3 API 能表达「画进 item entity target」——那张图不存在，`RenderType` 也不再携带它。
- Ponder 的这 5 个 RenderType 是**在 ponder 自己的 GUI 场景里画**的（`SceneRenderer` 直接提交几何体），
  不在 `LevelRenderer.executeOit` 那一趟里；挂 `setOitPipelines` 会让它指向**这一趟永远不会绑定的**
  OIT 管线与 target，是**引入**一个未验证的相位改动，不是等价替换。而且 create 的
  `PonderRenderPipelines` 里**没有**任何 `OitPipelineSet` 常量（javap 核过：19 个 `RenderPipeline` + 2 个 snippet）。
- vanilla 对**同形**的 `item_translucent` / `glint_translucent` / `entity_translucent_cull_item_target`
  就是「什么都不挂」⇒ 我们照做。

**⇒ 修法 = 删掉那 5 对指令**（`getstatic OutputTarget.ITEM_ENTITY_TARGET` + `invokevirtual setOutputTarget`），
builder 链的接收者原样保留，其余一个字节不动。

---

## 3. 修法实现（`g16/asm/PatchPonder.java`）

1. `ClassReader.accept(cv, 0)`：所有 StackMapTable 帧都以 `FrameNode` 形式到达并原样回写。
2. 在 `visitFieldInsn` 里把 `GETSTATIC OutputTarget.ITEM_ENTITY_TARGET` **缓冲**起来；
   若紧随其后的是 `INVOKEVIRTUAL RenderSetupBuilder.setOutputTarget(OutputTarget)RenderSetupBuilder`
   ⇒ **两条一起丢掉**；否则原样 flush 并计数（本轮 0 次）。
   两者之间偶尔会有 `Label` / `LineNumber`（第 5 个站点就是：`56: getstatic` 后面隔着一个 label 才是
   `59: invokevirtual`）⇒ 这些**没有指令的标记**先存起来、删除后再按原顺序补写，所以
   **分支目标不会移动**。
3. **`ClassWriter` 用「全新的」而不是 `new ClassWriter(reader, …)`**：这样被删掉之后不再被引用的常量池
   条目（`OutputTarget` 的 Class 常量、`ITEM_ENTITY_TARGET` 的 Fieldref、`setOutputTarget` 的 Methodref
   与描述符）会**一并消失**。这一点不是洁癖：`tools/scan_landmines.py` 的「缺类」判定读的是
   **常量池里的 Class 常量**，留着死条目就还会报一条 `类 OutputTarget 不存在`（地雷表 #18）。
4. `COMPUTE_MAXS` + 保留原帧：只删直线代码，帧与 `max_stack`（只会变小）都合法。
5. 工具自带**断言**：`dropped==5`、`unmatchedGetstatic==0`、`otherOutputTargetRefs==0`、
   输出字节里 `OutputTarget` 出现 **0** 次；任一不满足直接抛错不写文件。

实际运行输出：

```
  [com/zurrtum/.../PonderRenderTypes] dropped GETSTATIC ...OutputTarget.ITEM_ENTITY_TARGET + ...setOutputTarget   ×5
dropped=5 unmatchedGetstatic=0 otherOutputTargetRefs=0
bytes: in=9201 out=8824 residual 'OutputTarget' strings=0
```

> 为什么不用「换成 NOP」：NOP 能保住偏移，但会留下死的常量池引用 ⇒ 地雷表的「缺类」那一条清不掉，
> 而且类里会明显留下 10 条空指令。删除 + 重写常量池是同一风险等级下更干净的等价物。

### 3.1 静态初始化顺序：没动

15 个字段的赋值**顺序、数量、右值**全部照旧（§1 的表逐行相同）；变的只是 5 条 builder 链里少了一步
`setOutputTarget`。也就是说：**任何依赖这些静态字段的类（5 个）拿到的对象不变**，
差别只在 `RenderSetup` 少了一个 26.3 根本不存在的字段。

---

## 4. 逐类验证：只有预期的那两个方法变了

### 4.1 成员清单（`_javap_cmp.py`，常量池编号归一化后比对）

```
com/zurrtum/create/client/catnip/render/PonderRenderTypes.class
  member list: IDENTICAL (37 lines)     <- 15 字段 + 1 构造器 + 13 getter + 2 lambda + createLayerName + <clinit>（含空行）
  methods bytecode-identical: 33        <- 该计数把字段行也算进去了，见 §4.2 的纯方法口径
  methods DIFFERENT: 2
    != static {};
    != private static RenderType lambda$static$1(Identifier, Boolean);
```

### 4.2 指令级（`_instr_cmp.py`，去掉偏移与 `#nnn` 后逐行 diff）

类里一共 **20 个方法**（构造器 + 13 getter + `outlineSolid` + `outlineTranslucent` + `createLayerName` + 2 个 lambda + `<clinit>`）：**18 个逐指令相同，2 个不同**，差异只有下面这些——

| 方法 | 结果 |
|---|---|
| 18 个方法（13 个 getter、`outlineSolid`、`outlineTranslucent`、构造器、`lambda$static$0`、`createLayerName`） | **逐指令相同** |
| `lambda$static$1` | **只少 2 行**：`getstatic OutputTarget.ITEM_ENTITY_TARGET` + `invokevirtual setOutputTarget` |
| `<clinit>` | **只少 8 行** = 4 对同样的指令；**没有任何 `+` 行**（新增指令 0 条） |

### 4.3 字节码校验器

```
java -cp asm-util-9.10.1.jar:asm-analysis-9.10.1.jar org.objectweb.asm.util.CheckClassAdapter <class>
  old: (无输出)      new: (无输出)
```

两次都通过（`CheckClassAdapter` 会跑 `SimpleVerifier` 数据流分析，帧/栈错会直接报）。新类
**单独**（classpath = 26.3 + 交付 jar）也通过。

### 4.4 类大小与残留

`9201 → 8824 B`；输出里 `OutputTarget` / `ITEM_ENTITY_TARGET` / `setOutputTarget` **0 次**。

---

## 5. jar 级证明

```
entries: A=14336 B=14336
only in A (0):   only in B (0):
differing entries (1):
  com/zurrtum/create/client/catnip/render/PonderRenderTypes.class   A=8824  B=9201
```

（A = 新交付件，B = 改前的 `280B586B…`）

---

## 6. A/B（旧件 = 改前交付件 `280B586B…`，新件 = 本次交付件；每次都是全新存档副本）

探针 `g16/probe/sky262lm-probe.jar`（一次性，**不进交付**）两个 phase：

### 6.1 类初始化级：`phase=ponder`

**控制组**（`evidence/ponder-control1-latest.log`）

```
[sky262lm] phase=ponder
[sky262lm] PONDER_CLINIT_FAIL com.zurrtum.create.client.catnip.render.PonderRenderTypes
           -> java.lang.NoClassDefFoundError: net/minecraft/client/renderer/rendertype/OutputTarget
              <- java.lang.ClassNotFoundException: net.minecraft.client.renderer.rendertype.OutputTarget
[sky262lm] PHASE_DONE phase=ponder ticks=84
```

**修复组**（`evidence/ponder-fixed1-latest.log`）

```
[sky262lm] PONDER_CLINIT_OK com.zurrtum.create.client.catnip.render.PonderRenderTypes
[sky262lm] PONDER_FIELD ENTITY_BLOCK_SOLID = RenderType[ponder:entity_block_solid:RenderSetup[...
              textures={Sampler0=…minecraft:textures/atlas/blocks.png …}, outlineProperty=affects_outline,
              useLightmap=true, useOverlay=false]]
  …（15 条，全部非 null；OUTLINE_TRANSLUCENT = memoize/2[function=…$$Lambda…]，也是真对象）
[sky262lm] PONDER_FIELDS total=15 nulls=0
[sky262lm] PONDER_FACTORY getEntityBlockSolid -> RenderType[ponder:entity_block_solid:…]
  …（13 个 getter 全部非 null）
[sky262lm] PONDER_FACTORY outlineSolid -> RenderType[ponder:outline_solid:… Sampler0=ponder:textures/special/blank.png …]
[sky262lm] PONDER_FACTORY outlineTranslucent(cull=true)  -> RenderType[ponder:outline_translucent_cull:… Sampler0=minecraft:block/stone …]
[sky262lm] PONDER_FACTORY outlineTranslucent(cull=false) -> RenderType[ponder:outline_translucent:…]
[sky262lm] PONDER_FACTORIES factoryGaps=0
[sky262lm] ENTITYBLOCK_RT SOLID type=RenderType[item_cutout:…] lightType=RenderType[solid_moving_block:…]
  …（6 个常量 × type/lightType 全部非 null）
[sky262lm] ENTITYBLOCK_RT_OK constants=6
[sky262lm] GLINT_STILL_OK glint=SimpleMaterial@1e6df74d entityGlint=SimpleMaterial@25db2cc   <- 上一轮修的 glint 族没被碰坏
[sky262lm] PONDER_RESULT fields=15 fieldNulls=0 factoryGaps=0
```

`outlineTranslucent` 是**第 5 个站点**所在的工厂（`lambda$static$1`），它返回的两个 RenderType
名字分别带 `_cull` 和不带，说明 `BiFunction` 真的被调用并建出了对象。

### 6.2 玩法级：`phase=backtank`（真的穿附魔 backtank）

两版都做了：切第三人称 + `/item replace entity <p> armor.chest with
create:copper_backtank[enchantment_glint_override=true]`，日志确认
`BACKTANK tick=20 chest=1 create:copper_backtank foil=true`（**附魔物品确实穿上了**），然后渲染线程画本地玩家模型。

**控制组**（`evidence/bt-control1-latest.log`）—— 与上一轮报告里那一行**逐字一致**：

```
net.minecraft.ReportedException: Rendering entity in world
	…
Caused by: com.google.common.util.concurrent.ExecutionError: java.lang.NoClassDefFoundError:
           net/minecraft/client/renderer/rendertype/OutputTarget
	at …SuperByteBufferCache.get(SuperByteBufferCache.java:43)
	at …CachedBuffers.block(CachedBuffers.java:84)
	at …CachedBuffers.block(CachedBuffers.java:71)
	at …BacktankFeatureRenderer.submit(BacktankFeatureRenderer.java:40)
	at …BacktankFeatureRenderer.submit(BacktankFeatureRenderer.java:21)
	at …LivingEntityRenderer.submit / EntityRenderDispatcher.submit / LevelRenderer.submitEntities / …
	at …PonderRenderTypes.<clinit>(PonderRenderTypes.java:38)
```

**修复组**（`evidence/bt-fixed1-latest.log`）—— **前 10 帧完全相同**，`PonderRenderTypes.<clinit>` 这一帧
**没有了**，栈往深处多了一层，撞上**另一族**：

```
net.minecraft.ReportedException: Rendering entity in world
Caused by: com.google.common.util.concurrent.ExecutionError: java.lang.NoSuchMethodError:
           'boolean net.fabricmc.fabric.api.client.renderer.v1.mesh.MutableQuadView.diffuseShade()'
	at …SuperByteBufferCache.get(SuperByteBufferCache.java:43)      <- 与控制组同一帧
	at …CachedBuffers.block(CachedBuffers.java:84)                  <- 同一帧
	at …CachedBuffers.block(CachedBuffers.java:71)                  <- 同一帧
	at …BacktankFeatureRenderer.submit(BacktankFeatureRenderer.java:40)  <- 同一帧
	at …BacktankFeatureRenderer.submit(BacktankFeatureRenderer.java:21)  <- 同一帧
	…
	at …BufferEmitter.mddcd39d$create$lambda$quadEmitter$0$0(BufferEmitter.java:523)   <- 新增的一层
	at …SodiumRenderer$1.emitDirectly / MutableQuadViewWrapper.transformAndEmit / emit
	at …SimpleModelPart.emitQuads(SimpleModelPart.java:540)
	at …SingleVariant.emitQuads / NonTerrainBlockRenderContext.tesselateBlock
	at …ModelRenderHelper$Consumer…tesselateBlock(ModelRenderHelperMixin.java:96)
	at …SuperBufferFactory.createForBlock(SuperBufferFactory.java:41)   <- 与控制组同一帧
```

⇒ 「**渲染状态构建**」（`PonderRenderTypes` + `EntityBlockRenderType` 这一层）**已经通了**；
现在崩的是**把 quad 送进 emitter**时的 fabric-api 签名不匹配（`diffuseShade()` 在 FRAPI 17 里被删，
换成了 `ShadeMode`）。它是地雷表里的**另一条**（现 #7，LOW，4 站点），不是本轮范围。

### 6.3 backtank 验到哪一层（如实）

- ✅ 走到 `BacktankFeatureRenderer.submit` 的第 4 行、`CachedBuffers.block`、`PonderRenderTypes.<clinit>`
  全部跑完（`EntityBlockRenderType.<clinit>` 也从这些静态字段建出了真 RenderType）。
- ❌ **没有看到屏幕上的 backtank 发光**：quad 在到达 GPU 之前就死在新地雷 #7 上，所以「肉眼可见」这一级
  **未验证**；也没有截图。
- 本轮**不能**把 #7 一起修（见 §9.1），所以这条玩法路径的**完整**验收仍然欠一层。

### 6.4 一个**改前改后都一样**的既有问题（别记到本轮账上）

四次 A/B 运行 + 交付件本体运行，**每一次**都有 15 条：

```
[Worker-Main-6/ERROR]: Couldn't compile pipeline (ponder:pipeline/entity_block_translucent):
com.mojang.renderpearl.util.ShaderCompileException: Couldn't parse GLSL:
  ponder:entity_block:3: error: '#' : invalid directive: moj_import
  … 'location' : SPIR-V requires location for user input/output
  … 'ProjMat' / 'ModelViewMat' : undeclared identifier
  … 'fog_spherical_distance' / 'sample_lightmap' : no matching overloaded function found
```

以及 `Failed to load optional shader programs: - ponder:pipeline/… - create:pipeline/glowing …`。
这是 **ponder 管线的 GLSL 源还是 26.2 写法**（`#moj_import` + 老 uniform 名），与 `PonderRenderTypes`
无关（它发生在 `PonderRenderPipelines` 的管线注册，改前就是 15 条、改后还是 15 条）。
⇒ **修复组即使绕过 #7，ponder 场景也还是会因为管线编译失败而画不出来**。这是**第三族**（shader 源移植）。

---

## 7. 交付

### 7.1 `mods-stable` = 71 jar（未增未减）

| 文件 | 备份 | 原 SHA-256 | 新 SHA-256 |
|---|---|---|---|
| `create-fly-26.2-6.0.9-2-26.3-patched.jar` | `.bak-ponder`（19,639,235 B） | `280B586B3C348C4783D35539C307A88A99FAA490D6B6B6B5CCA487E6703AD41F` | **`F950B9529AAF732BEADC2A626D7B916773518BC3B7A8053C0226343A234F6E0E`**（19,639,144 B / 14336 entries） |

`.bak-landmine`（原始件）、`.bak-landmine-glint`、`.bak-itemhelper` 均**未覆盖**。

### 7.2 交付件本体回归（`--mods mods-stable`，71 jar，全新存档副本）

| 项 | 命令 | 结果 |
|---|---|---|
| 标题 | `python tools/launch26/launch.py --game-dir g16/final --mods mods-stable --watch-title --timeout 300` | **`RESULT: TITLE_SCREEN_OK`**（27.8 s，三标记全中） |
| 进世界 | `python g16/_run_world.py --game-dir g16/final --mods mods-stable --world lm-final --marker "logged in with entity id" --tag final-world --timeout 300` | **`RESULT: WORLD_OK`**（45.4 s） |

`evidence/final-world-latest.log` 计数：

```
Loading 150 mods:                        1
Loaded 2343 advancements                 （+ 34 client）
Registry loading errors                  0
NoSuchMethodError                        0
NoSuchFieldError                         0
ExceptionInInitializerError              0
NullPointerException                     0
ReportedException                        0
Exception while updating neighbours      0
Couldn't compile pipeline                15   <- §6.4，改前就有，与本轮无关
```

---

## 8. 重扫（`python tools/scan_landmines.py --only create-fly`）

| 指标 | 改前（`g15/scan_after.md`，= 上一轮交付件） | 改后（`g16/scan_after.md`） |
|---|---|---|
| 原始指令级发现 | 1134 | **1123** |
| 去重归组 | 278 | **275** |
| **地雷总数** | **86** | **83** |
| 高危 / 中危 / 低危 | 29 / 17 / 40 | **27 / 16 / 40** |
| 缺类 / 缺方法 / 缺字段（组） | 21 / 51 / 14 | **20 / 50 / 13** |

归零 3 条 = `setOutputTarget` + `ITEM_ENTITY_TARGET` + `类 OutputTarget`；`Select-String OutputTarget`
在新报告里 **0 命中**。上一轮修的 `RenderTypes.glint*` / `InterpolationHandler` 仍然 **0 命中**（没被碰坏）。
新报告的第一优先级现在是 `ClockManager.getTotalTicks(Holder)`（2 站点）。

---

## 9. 已知限制 / 下一步

### 9.1 下一族（建议顺序）

1. **`MutableQuadView.diffuseShade()Z`**（现 #7，LOW，4 站点：`BufferAoPoseEmitterMixin` /
   `BufferColorPoseEmitterMixin` / `BufferEmitter` 等）——它现在**直接挡住穿 backtank 的画面**，
   也是「ponder/backtank 视觉验收」的最后一道。26.3 的 FRAPI 17 里 `QuadView`/`MutableQuadView`
   **都没有** `diffuseShade`（我把 `fabric-renderer-api-v1-17.0.16` 从 fabric-api 的内嵌 jar 里扒出来核过），
   换成了 `ShadeMode`；这需要判「哪一档 `ShadeMode` 等价于 `diffuseShade=true`」，属于**要读语义**的修，
   不是本轮这种「概念没了就删一步」。
2. **ponder/`create:pipeline/glowing` 的 GLSL 源**（§6.4）——`#moj_import` 与老 uniform 名在 26.3 的
   renderpearl 编译器下直接编译失败。这一族比 #7 更大（要改 `.vsh/.fsh` 资源），但**不修它 ponder 场景永远画不出来**。

### 9.2 本轮**没有**判定为「需要产品决策」的理由

这一族不是「语义不确定」，而是「26.3 把这个概念连同承载它的类一起删了，vanilla 对同形 RenderType
的处理就是不要它」——删掉那一步是**唯一**不需要发明新语义的做法，而且 §5 证明 jar 里只变 1 个 entry、
§4 证明类里只少 10 条指令。风险可控。

### 9.3 其它

- 没有重跑 107 mod 全量矩阵；只跑 `mods-stable` 71 jar + 4 次 A/B。
- 没有重编 create 工程（交付件是字节码补丁，整包重编会覆盖掉 26.3 资源路径/垫片）。
- `g16/probe/sky262lm-probe.jar` 是**一次性验收驱动，不是交付物**（`mods-stable` 里没有它）。
- `phase=ponder` 的 `outlineTranslucent` 传的是 `minecraft:block/stone` 这个**不存在的纹理 id**，
  只为证明工厂能返回对象；真正渲染会走 `PonderSpecialTextures`/方块图集。

---

## 10. 复现命令

```powershell
$base = "C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
$g16  = "$base\work\run26\port\g16"
$name = "create-fly-26.2-6.0.9-2-26.3-patched.jar"
$jar  = "$base\work\run26\mods-stable\$name"
$asm  = "$env:APPDATA\.minecraft\libraries\org\ow2\asm\asm\9.10.1\asm-9.10.1.jar"
$javac= "$env:APPDATA\.minecraft\runtime\java-runtime-epsilon\bin\javac.exe"
$java = "$env:APPDATA\.minecraft\runtime\java-runtime-epsilon\bin\java.exe"

# 1) 取类（原始件 / 改前交付件都行；本轮从 .bak-ponder 等价件取）
python -c "import zipfile,pathlib; ..."   # 见 §0 的 oldcls/

# 2) 编译 + 改
& $javac -cp $asm -d "$g16\asm\out" "$g16\asm\PatchPonder.java"
& $java -cp "$g16\asm\out;$asm" PatchPonder "$g16\oldcls\com\zurrtum\create\client\catnip\render\PonderRenderTypes.class" `
                                        "$g16\newcls\com\zurrtum\create\client\catnip\render\PonderRenderTypes.class"

# 3) 逐方法 / 逐指令比对
python "$base\work\run26\port\g15\_javap_cmp.py" "$g16\oldcls" "$g16\newcls" com/zurrtum/create/client/catnip/render/PonderRenderTypes.class
python "$g16\_instr_cmp.py" "$g16\dump_old.txt" "$g16\dump_new.txt"

# 4) 换 entry + jar diff
#    源 jar = **改前**的交付件：交付前是 $jar 本身，交付后等价物是 $jar.bak-ponder
python "$g16\_patch_jar.py" "$jar" "$g16\out-jar\$name" `
  "com/zurrtum/create/client/catnip/render/PonderRenderTypes.class=$g16\newcls\com\zurrtum\create\client\catnip\render\PonderRenderTypes.class"
python "$g16\_jar_diff.py" "$g16\out-jar\$name" "$jar.bak-ponder"

# 5) A/B（每次全新存档副本）
python "$g16\_mkmods.py" "$jar.bak-ponder"        "$g16\mods-control"      # 旧件（改前交付件）
python "$g16\_mkmods.py" "$g16\out-jar\$name"    "$g16\mods-fixed"
python "$g16\_mkworld.py" --game "$g16\game-ponder-fixed" --template "$base\work\run26\vfix-saves\placed" --name lm-ponder-fixed1 --phase ponder
python "$g16\_run_world.py" --game-dir "$g16\game-ponder-fixed" --mods "$g16\mods-fixed" --world lm-ponder-fixed1 --tag ponder-fixed1 --timeout 240

# 6) 交付（备份 + 删除再写，不写穿硬链接）
python "$g16\_deliver.py" "$g16\out-jar\$name" ".bak-ponder"

# 7) 重扫
python "$base\tools\scan_landmines.py" --only create-fly --out "$g16\scan_after.md" --json "$g16\scan_after.json"
```
