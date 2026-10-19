# fix-landmines-1 —— 修 `InterpolationHandler` 家族 与 `RenderTypes.glint` 家族（create-fly jar，纯 ASM）

> **结论：两族都修好了，且两族都做了旧件必炸 / 新件不炸的 A/B（不是「能进世界」当完成）。**
>
> | 族 | 状态 | 交付改动 | A/B |
> |---|---|---|---|
> | **地雷 2 `RenderTypes.glint` 家族**（4 个成员 / 8 站点） | ✅ 已修，**类初始化级 A/B**：旧件 `Class.forName` 即 `ExceptionInInitializerError`，新件 3 个类全 `CLINIT_OK`，两张表全部解析出真 Material / 层号 | create jar 内换 **4 个 class** | ✅ 旧件 4 条 `NoSuchMethodError` + 2 条 `ExceptionInInitializerError` / 新件 **0** |
> | **地雷 1 `InterpolationHandler` 家族**（5 个成员 / 3 站点） | ✅ 已修，**方法级 A/B**：旧件 `travel()` 两次调用分别 `IncompatibleClassChangeError`、`alignPassenger()` `NoSuchFieldError`；新件三次调用全 OK（玩家 yaw 真的被改写） | create jar 内换 **2 个 class**（`PackageEntity` 多 1 个 private static 桥接方法） | ✅ 旧件 2×ICCE + 1×NoSuchFieldError / 新件 `TRAVEL_OK`×2 + `ALIGN_OK` |
>
> `mods-stable` 仍 **71 jar**（改的是已有 jar，没有加新 jar）。
> 交付件本体（71 jar）跑过 **`TITLE_SCREEN_OK` 29.5s + `WORLD_OK` 45.3s**，`NoSuchMethodError` / `NoSuchFieldError` /
> `ExceptionInInitializerError` / `NullPointerException` / `ReportedException` / registry 错误 **全 0**。
> 交付件相对**原始件只有 6 个 class 不同**（14,336 entries 其余逐字节不动）。
> 重扫：`create-fly` 地雷 **95 → 86**（两族共 9 条归零）。
>
> ⚠ 两族的**玩法级**验证各缺一半，如实写在 §6：`backtank` 路径被**另一族地雷**（`PonderRenderTypes.<clinit>`）挡在更早处；
> 本次靠「类初始化 + 表解析」证明 glint 族。`alignPassenger` 用**客户端直接构造载具实体**驱动（不是真骑上去），
> 因为本 jar 里 `/summon create:carriage_contraption` 不可能成功（缺 train 数据）。

---

## 0. 本轮用的目录（`work/run26/watch` 全程未读写）

```
work/run26/port/g15/
  asm/PatchLandmines.java     一次性 ASM 工具（mode=glint / mode=interp）
  asm/out/                    它的 class
  oldcls/ newcls/             glint 族：改前/改后 4 个 class
  oldcls2/ newcls2/           interp 族：改前/改后 2 个 class
  bridge/src/bridge/PackageEntityBridge.java   桥接方法源码（编译后整方法拷进 PackageEntity）
  probe/src/                 一次性驱动 mod（sky262lm-probe.jar，**不进交付**）
  out-jar/                    只修 glint 的 create jar
  out-jar2/                   修 glint + interp 的 create jar（= 交付件）
  mods-control / mods-fixed              硬链接 71 jar + probe，create 分别是旧件/glint 件
  mods-interp-control / mods-interp-fixed 同上，create 分别是原始件/交付件
  game-*/ saves 模板来自 work/run26/vfix-saves/placed（**每次全新副本**，跑过就换名字）
  final/                      交付件本体跑标题 + 进世界
  evidence/                   每次的 latest.log / console.log 留档
  scan_before.md / scan_after.md
```

`work/run26/stag1` 只作为 `options.txt / config / defaultconfigs` 的来源读取；
`mods-full` / `mods-fix2` / `mods-crashfix` / `work/sable-26` / `work/build26` / `g6`-`g14` 未改动。

---

## 1. 地雷 2：`RenderTypes.glint` 家族

### 1.1 26.3 到底长什么样（javap 现查，不是照抄地雷表）

```powershell
& "$env:APPDATA\.minecraft\runtime\java-runtime-epsilon\bin\javap.exe" -p -c `
  -cp "$env:APPDATA\.minecraft\versions\26.3\26.3.jar" `
  net.minecraft.client.renderer.rendertype.RenderTypes
```

**结论 1：三个无参方法真的没了，且不是「改名」。** 26.3 的 glint 全部变成
**`Function<Identifier, RenderType>` 工厂，并把「glint 合成到 base 同一趟 pass 里」**：

| 26.3 工厂 | 签名 | lambda 体（`javap -c` 原文摘要） |
|---|---|---|
| `itemCutoutGlint` | `(Identifier)→RenderType` | `RenderPipelines.ITEM_CUTOUT_GLINT` + `withTexture("Sampler0", <参数>)` + `withTexture("GlintSampler", ItemFeatureRenderer.ENCHANTED_GLINT_ITEM)` + `setTextureTransform(GLINT_TEXTURING)` |
| `itemTranslucentGlint` | 同上 | `ITEM_TRANSLUCENT_GLINT` + Sampler0=参数 + GlintSampler=ENCHANTED_GLINT_ITEM + GLINT_TEXTURING |
| `entitySolidGlint` | 同上 | `ENTITY_SOLID_GLINT` + Sampler0=参数 + GlintSampler=ENCHANTED_GLINT_ITEM + **ENTITY_GLINT_TEXTURING** |
| `armorCutoutNoCullGlint` | 同上 | `ARMOR_CUTOUT_NO_CULL_GLINT` + Sampler0=参数 + GlintSampler=**ENCHANTED_GLINT_ARMOR** + ARMOR_ENTITY_GLINT_TEXTURING |
| `patternedShieldGlint` | `()→RenderType` | `RenderPipelines.GLINT` + Sampler0=ENCHANTED_GLINT_ITEM + ENTITY_GLINT_TEXTURING + `withForcedSolidModelPhase()` |
| `trimmedArmorGlint` | `()→RenderType` | `RenderPipelines.GLINT` + Sampler0=ENCHANTED_GLINT_ARMOR + ARMOR_ENTITY_GLINT_TEXTURING + VIEW_OFFSET_Z 分层 |

⇒ **参数 `Identifier` = 这块几何体本身用的贴图/图集**（`Sampler0`），glint 贴图是每个工厂内固定的。

**结论 2：`Sheets` 里已经有现成常量**（vanilla 自己的 `RenderTypes` 初始化就写死了这四个组合）：

```
CUTOUT_BLOCK_ITEM_GLINT_SHEET      = RenderTypes.itemCutoutGlint(TextureAtlas.LOCATION_BLOCKS)
TRANSLUCENT_BLOCK_ITEM_GLINT_SHEET = RenderTypes.itemTranslucentGlint(TextureAtlas.LOCATION_BLOCKS)
CUTOUT_ITEM_GLINT_SHEET            = RenderTypes.itemCutoutGlint(TextureAtlas.LOCATION_ITEMS)
TRANSLUCENT_ITEM_GLINT_SHEET       = RenderTypes.itemTranslucentGlint(TextureAtlas.LOCATION_ITEMS)
```
访问器 `Sheets.cutoutBlockItemGlintSheet()` / `translucentBlockItemGlintSheet()` 都是 `public static`；
`TextureAtlas.LOCATION_BLOCKS/LOCATION_ITEMS` 是 `public static final Identifier`（都 javap 核过）。

### 1.2 站点语义判定 ⇒ 映射

| 1.21.1 调用 | 26.3 替代 | 为什么是它（不是「换个名字」） |
|---|---|---|
| `RenderTypes.glint()` | `Sheets.cutoutBlockItemGlintSheet()` | = `itemCutoutGlint(blocks 图集)`：26.3 渲染**方块图集附魔物品**时用的**就是这一个实例**；glint 贴图仍 `enchanted_glint_item`、变换仍 `GLINT_TEXTURING` |
| `RenderTypes.glintTranslucent()` | `Sheets.translucentBlockItemGlintSheet()` | = `itemTranslucentGlint(blocks)`，半透明管线 |
| `RenderTypes.entityGlint()` | `RenderTypes.entitySolidGlint(TextureAtlas.LOCATION_BLOCKS)` | 26.3 的实体 glint 用 **ENTITY_GLINT_TEXTURING**（与 1.21.1 `entity_glint_direct` 逐项同构）；backtank 的几何体是方块模型 ⇒ base 贴图 = blocks 图集 |
| `RenderTypes.armorEntityGlint()`（同族第 4 个成员，扫到的 LOW 条目） | `RenderTypes.trimmedArmorGlint()` | 唯一「纯护甲 glint 叠加」静态件：`ENCHANTED_GLINT_ARMOR` + `ARMOR_ENTITY_GLINT_TEXTURING` + `RenderPipelines.GLINT`（depth EQUAL / GLINT 混合），与 1.21.1 `armorEntityGlint` 同形；**无参→无参**，改完指令数不变 |

**为什么不是 `patternedShieldGlint()`**：它确实是「纯 glint 叠加 + Sampler0=glint 贴图」，但带了
`withForcedSolidModelPhase()`（把这一趟强制塞进 solid model phase），对 create 的「先画 backtank 再叠加 glint」
两趟结构来说是没验证过的相位改动；`entitySolidGlint` 是 `entitySolid` 的 base+glint 版本，cull/混合都不变，
只多画一遍底贴图（无害 overdraw）。⇒ 选后者，理由写在 §6.1。

### 1.3 修法：4 个 class、6 条 method-ref（ASM，只改 ref）

`asm/PatchLandmines.java mode=glint`，`ClassWriter(COMPUTE_MAXS)` + 原有 `FrameNode` 原样复制，
只把调用点换成新的静态调用（`entityGlint` 那个多插一条 `getstatic TextureAtlas.LOCATION_BLOCKS`）。

工具实际输出的站点（= 全部 8 条）：

```
ModelUtil.class
  [<clinit>()V]  RenderTypes.glint()            -> Sheets.cutoutBlockItemGlintSheet()
  [<clinit>()V]  RenderTypes.glintTranslucent() -> Sheets.translucentBlockItemGlintSheet()
  [<clinit>()V]  RenderTypes.entityGlint()      -> RenderTypes.entitySolidGlint(TextureAtlas.LOCATION_BLOCKS)
BakedItemModelBufferer.class
  [<clinit>()V]  RenderTypes.glint()            -> Sheets.cutoutBlockItemGlintSheet()
  [<clinit>()V]  RenderTypes.glintTranslucent() -> Sheets.translucentBlockItemGlintSheet()
  [<clinit>()V]  RenderTypes.entityGlint()      -> RenderTypes.entitySolidGlint(TextureAtlas.LOCATION_BLOCKS)
BacktankFeatureRenderer.class
  [submit(...)V] RenderTypes.entityGlint()      -> RenderTypes.entitySolidGlint(TextureAtlas.LOCATION_BLOCKS)
HumanoidArmorLayerMixin.class
  [renderArmorPiece(...)V] RenderTypes.armorEntityGlint() -> RenderTypes.trimmedArmorGlint()
```

### 1.4 每类逐一验证（`_javap_cmp.py`；常量池编号 `#nnn` 归一化后比对）

| class | 大小 | 成员清单 | 逐方法比对 |
|---|---|---|---|
| `ModelUtil` | 9650 → 9888 B | **17 行完全一致** | 15 个方法里 **14 个逐指令相同**，只有 `<clinit>` 变 |
| `BakedItemModelBufferer` | 4267 → 4526 B | **9 行完全一致** | 7 个里 6 个相同，只有 `<clinit>` 变 |
| `BacktankFeatureRenderer` | 6364 → 6531 B | **5 行完全一致** | 3 个里 2 个相同，只有 `submit(PoseStack,SubmitNodeCollector,int,S,float,float)` 变 |
| `HumanoidArmorLayerMixin` | 4532 → 4533 B | **4 行完全一致** | 2 个里 1 个相同，只有 `renderArmorPiece` 变，且**只有一条 invokestatic 换了 owner.name，偏移全不变** |

`ModelUtil.<clinit>` 的 diff（就是预期的那 3 条，偏移 364/379/394 后各加了 3 字节）：

```
- 364: invokestatic  RenderTypes.glint:()LRenderType;
+ 364: invokestatic  Sheets.cutoutBlockItemGlintSheet:()LRenderType;
- 379: invokestatic  RenderTypes.glintTranslucent:()LRenderType;
+ 379: invokestatic  Sheets.translucentBlockItemGlintSheet:()LRenderType;
- 394: invokestatic  RenderTypes.entityGlint:()LRenderType;
+ 394: getstatic     TextureAtlas.LOCATION_BLOCKS:Lnet/minecraft/resources/Identifier;
+ 397: invokestatic  RenderTypes.entitySolidGlint:(LIdentifier;)LRenderType;
   400: getstatic     Materials.GLINT_ENTITY
   403: invokeinterface Map.put
```

`BacktankFeatureRenderer.submit` 同样：`249: ifeq 290 → 293`（多一条指令）、`252: getstatic LOCATION_BLOCKS` +
`255: invokestatic entitySolidGlint`，其余三个 `submit(RenderType, pose, collector)` 调用点逐个相同。

### 1.5 jar 级证明

```
entries: A=14336 B=14336      (仅修 glint 时)
differing entries (4):
  .../BacktankFeatureRenderer.class      A=6531  B=6364
  .../ModelUtil.class                    A=9888  B=9650
  .../BakedItemModelBufferer.class        A=4526  B=4267
  .../HumanoidArmorLayerMixin.class       A=4533  B=4532
```

### 1.6 A/B（旧件 vs 新件，各自**全新存档副本**）

**控制组（原始件，`evidence/glint-control-latest.log`）**

```
[sky262lm] phase=glint
[sky262lm] CLINIT_FAIL com.zurrtum.create.client.flywheel.lib.model.ModelUtil
           -> java.lang.NoSuchMethodError: 'net.minecraft.client.renderer.rendertype.RenderType
              net.minecraft.client.renderer.rendertype.RenderTypes.glint()'
[sky262lm] CLINIT_FAIL com...model.baked.BakedItemModelBufferer
           -> java.lang.NoSuchMethodError: '...RenderTypes.glint()'
[sky262lm] CLINIT_OK   com...equipment.armor.BacktankFeatureRenderer     <- 它的 <clinit> 里没有 glint 引用
[sky262lm] ITEMMATERIAL_FAIL
           Caused by: java.lang.ExceptionInInitializerError: Exception java.lang.NoSuchMethodError:
             '...RenderTypes.glint()' [in thread "Render thread"]
[sky262lm] CHUNKLAYERS_FAIL
           Caused by: java.lang.ExceptionInInitializerError: ...
```
计数：`NoSuchMethodError 4` / `ExceptionInInitializerError 2` / `NullPointerException 0`。

**修复组（`evidence/glint-fixed-latest.log`）**

```
[sky262lm] CLINIT_OK com...model.ModelUtil
[sky262lm] CLINIT_OK com...model.baked.BakedItemModelBufferer
[sky262lm] CLINIT_OK com...equipment.armor.BacktankFeatureRenderer
[sky262lm] ITEMMATERIAL base=SimpleMaterial@64c58382 glint=SimpleMaterial@d12ec94
           glintTranslucent=SimpleMaterial@d12ec94 entityGlint=SimpleMaterial@2422ad32 armorGlint=null
[sky262lm] CHUNKLAYERS size=5
           keys=[item_cutout=0, item_translucent=1, item_cutout_glint=2,
                 item_translucent_glint=3, entity_solid_glint=4]
[sky262lm] RESOLVE glint=RenderType[item_cutout_glint ... Sampler0=atlas/blocks.png ...]
           glintTranslucent=RenderType[item_translucent_glint ...]
           entityGlint=RenderType[entity_solid_glint ... textureTransform=entity_glint_texturing ...]
           armorGlint=RenderType[trimmed_armor_glint ... Sampler0=enchanted_glint_armor.png ...]
[sky262lm] RESOLVE id-equality glint==itemCutoutGlint(blocks)=true
           entityGlint==entitySolidGlint(blocks)=true
```
计数：四个错误计数**全 0**；`ITEMMATERIAL` 里 glint / glintTranslucent 都落到 `Materials.GLINT`（create 自己的表就是这么写的），
entityGlint 落到 `Materials.GLINT_ENTITY`——**不是 null**，说明两张表真的建起来了。
（`armorGlint=null` 是**预期**：`armorEntityGlint` 从来不在 `ITEM_CHUNK_MATERIALS` 里，它只用于 mixin 的直接 submit。）

### 1.7 附：真的「穿带附魔 backtank」跑了，但先撞到**另一族**地雷

`phase=backtank`：切第三人称 + `/item replace entity <p> armor.chest with
create:copper_backtank[enchantment_glint_override=true]`（`ItemStack.hasFoil()` 在 26.3 先读
`DataComponents.ENCHANTMENT_GLINT_OVERRIDE`，javap 核过），日志确认
`BACKTANK tick=20 chest=1 create:copper_backtank foil=true`（附魔物品确实穿上了），
然后**两版都以同一行崩掉**：

```
[sky262lm] BACKTANK tick=30 chest=1 create:copper_backtank foil=true
net.minecraft.ReportedException: Rendering entity in world
	at knot//com.zurrtum.create.client.catnip.render.PonderRenderTypes.<clinit>(PonderRenderTypes.java:38)
```

`PonderRenderTypes` 属于**地雷表第 1 号**（`RenderSetup$RenderSetupBuilder.setOutputTarget` + `OutputTarget.ITEM_ENTITY_TARGET`，
5 站点）。javap 核实：**26.3 里 `OutputTarget` 类整个不存在，`RenderSetupBuilder` 也没有 `setOutputTarget`**
⇒ 不是改名、是整体模型换掉（改成 pipeline + `withTexture`/sampler），要**重写**这几个 render type，超出本轮范围。
所以 backtank 这条玩法路径**不能**作为 glint 族的 A/B（两版一起崩在更早处），见 §6.2。

---

## 2. 地雷 1：`InterpolationHandler` 家族

### 2.1 26.3 到底长什么样（javap 现查）

```
public interface net.minecraft.world.entity.InterpolationHandler {
  InterpolationHandler NO_OP;
  default InterpolationTracker interpolationTracker();
  PositionAndRotation target();
  boolean interpolateTo(PositionPath, float, float, boolean);
  void interpolate();
  void applyPredictedMovement(Vec3);
  boolean hasActiveInterpolation();
  void cancel();
}
```
（1.21.1 它是**类**，有 `interpolationData` 字段 / `InterpolationData` 类 / `position()` / `interpolateTo(Vec3,FF)V`。）

关键旁证（都在 `AbstractInterpolationHandler` / `Entity` 里 javap 读到）：

* `AbstractInterpolationHandler.target()`：`hasActiveInterpolation() ? interpolationData().immutable() : null`
  ⇒ **只有没在插值时才返回 null**；而 `Entity.isInterpolating()` 的实现就是
  `interpolationHandler.hasActiveInterpolation()` ⇒ **`PackageEntity.travel` 的
  `if (isInterpolating()) { ...getInterpolation()... }` 分支里 `target()` 必然非 null**（这就是不写 null 检查的依据）。
* `interpolateTo(PositionPath,FFZ)` 的第 4 个参数：字节码是
  `iload 4; ifeq → 用传进来的 fload_2/fload_3，否则用 positionAndRotation 的 yRot/xRot`
  ⇒ 语义 = **「用不用我给的角度」**，旧 3 参版本恒等于「用」⇒ 传 `true`。
* `interpolationData.steps = 0` 的等价物：26.3 里只剩
  `AbstractInterpolationHandler.interpolationSteps`（**protected**，create 同包都用不了）和
  `SteppedInterpolationHandler$InterpolationData`（包私有，且没有 `steps` 字段）。
  **公开的等价动作是 `cancel()`**：`SteppedInterpolationHandler.cancel()` → `interpolationData.reset()`
  （清空 remainingSteps），也就是 1.21.1 `cancel()` 的 `interpolationSteps = 0`。

### 2.2 站点语义判定 ⇒ 映射

| 站点 | 1.21.1 | 26.3 | 判定 |
|---|---|---|---|
| `AbstractContraptionEntity.alignPassenger:427` | `handler.interpolationData.steps = 0` | `handler.cancel()` | **同义**：都是「立刻停掉插值」。差别：`cancel()` 还会 reset 起点/步长状态，比只清零步数更彻底（不会改变可见行为，只是更干净） |
| `PackageEntity.travel:154` | `getInterpolation().position()` | `getInterpolation().target().position()` | 同上语义（`position()` 在 1.21.1 返回**插值目标点**）；null 风险已被 `isInterpolating()` 挡住（§2.1） |
| `PackageEntity.travel:160` | `interpolateTo(Vec3,yRot,xRot)` | `interpolateTo(PositionPath.of(vec),yRot,xRot,true)` | 参数形状变了 ⇒ **写桥接方法**（不能只改名） |

### 2.3 修法

**(a) `AbstractContraptionEntity.alignPassenger` —— 纯指令替换，不加方法**

```
- 105: getfield      InterpolationHandler.interpolationData:...InterpolationData;
- 108: iconst_0
- 109: putfield      ...InterpolationData.steps:I
+ 105: invokeinterface InterpolationHandler.cancel:()V
```
栈净效果不变（`getfield` 吃掉 handler 引用推 value，改成 `cancel()` 直接吃掉引用），
后续分支目标 112→110、148→146 自动跟着挪。

**(b) `PackageEntity.travel` —— 1 处改成 2 条 invokeinterface，1 处换成桥接**

```
- 120: invokevirtual InterpolationHandler.position:()LVec3;
+ 121: invokeinterface InterpolationHandler.target:()LPositionAndRotation;
+ 126: invokeinterface PositionAndRotation.position:()LVec3;
      131: invokestatic VecHelper.lerp:(FLVec3;LVec3;)LVec3;     <- 原样保留
...
- 178: invokevirtual InterpolationHandler.interpolateTo:(LVec3;FF)V
+ 186: invokestatic  PackageEntity.sky262InterpolateTo:(LInterpolationHandler;LVec3;FF)V
```

桥接方法（源码 `g15/bridge/src/bridge/PackageEntityBridge.java`，**编译后整方法拷进 PackageEntity**，
只加 **1 个 private static 方法**，没加 class）：

```java
private static void sky262InterpolateTo(InterpolationHandler handler, Vec3 pos, float yRot, float xRot) {
    if (handler == null || pos == null) {
        return;
    }
    handler.interpolateTo(PositionPath.of(pos), yRot, xRot, true);   // ← 旧 3 参语义
}
```

> 为什么能用「1 换 1」：调用点当时的操作数栈正好是 `[handler, vec3, yRot, xRot]`，
> 与桥接方法的形参表一一对应 ⇒ `invokevirtual` 换 `invokestatic` **不动栈、不动 max_stack、不动 StackMapFrame**。

交付件里的桥接字节码（javap）：

```
private static void sky262InterpolateTo(InterpolationHandler, Vec3, float, float);
   0: aload_0
   1: ifnull        8
   4: aload_1
   5: ifnonnull     9
   8: return
   9: aload_0
  10: aload_1
  11: invokestatic  PositionPath.of:(LVec3;)LPositionPath;
  14: fload_2
  15: fload_3
  16: iconst_1
  17: invokeinterface InterpolationHandler.interpolateTo:(LPositionPath;FFZ)Z
  22: pop
  23: return
```

### 2.4 每类逐一验证

| class | 大小 | 成员清单 | 逐方法比对 |
|---|---|---|---|
| `AbstractContraptionEntity` | 41640 → 41512 B | **98 行完全一致** | 96 个方法里 **94 个逐指令相同**；变的是 `alignPassenger`（预期）+ `positionRider` 里一处 `ldc`→`ldc_w`（常量池越过 255 后的编码差异，同一个 float 常量，语义不变） |
| `PackageEntity` | 23774 → 24328 B | 原 49 行 **全部保留** + **新增 1 行** `private static void sky262InterpolateTo(...)` | 51 个方法里 **48 个逐指令相同**；`travel` 变（预期）、`getMoveSimulationType` 只是比对脚本把类尾 `}` 归到最后一个方法的显示差异 |

> 两处「非预期」差异都只是 **同一个常量的 `ldc`→`ldc_w`**（ASM 因为常量池变长而换了短/长编码），
> 指令语义、栈效果、帧完全相同 —— 在报告里明写，不当作「没变」。

### 2.5 jar 级证明（最终交付件 vs 原始件）

```
entries: A=14336 B=14336
differing entries (6):
  .../client/content/equipment/armor/BacktankFeatureRenderer.class   A=6531  B=6364
  .../client/flywheel/lib/model/ModelUtil.class                      A=9888  B=9650
  .../client/flywheel/lib/model/baked/BakedItemModelBufferer.class    A=4526  B=4267
  .../client/mixin/HumanoidArmorLayerMixin.class                     A=4533  B=4532
  .../content/contraptions/AbstractContraptionEntity.class           A=41512 B=41640
  .../content/logistics/box/PackageEntity.class                      A=24328 B=23774
```

### 2.6 A/B（旧件 vs 新件，各自全新存档副本）

**控制组（原始件，`evidence/interp-control3-latest.log`）**

```
[sky262lm] PACKAGE constructed tickCount=0 client=true
           handler=net.minecraft.world.entity.SteppedInterpolationHandler isInterpolating=false
[sky262lm] TRAVEL_FAIL call1 (interpolateTo site)
           -> java.lang.IncompatibleClassChangeError: Found interface
              net.minecraft.world.entity.InterpolationHandler, but class was expected
[sky262lm] interpolateTo(PositionPath,...) -> true active=true      <- 探针用 26.3 API 激活插值
[sky262lm] TRAVEL_FAIL call2 (position site)
           -> java.lang.IncompatibleClassChangeError: Found interface ...
[sky262lm] client contraption OrientedContraptionEntity constructed
[sky262lm] prevPosInvalid cleared via AbstractContraptionEntity
[sky262lm] contraption placed at (-320.5, 71.0, -41.5)
[sky262lm] ALIGN_FAIL -> java.lang.reflect.InvocationTargetException
           <- java.lang.NoSuchFieldError: Class net.minecraft.world.entity.InterpolationHandler
              does not have member field
              'net.minecraft.world.entity.InterpolationHandler$InterpolationData interpolationData'
```

**修复组（`evidence/interp-fixed3-latest.log`）**

```
[sky262lm] TRAVEL_OK call1 (interpolateTo site) pos=(-323.5, 74.58725999609247, -41.5) isInterpolating=true
[sky262lm] interpolateTo(PositionPath,...) -> true active=true
[sky262lm] TRAVEL_OK call2 (position site) pos=(-323.5, 74.17451999218494, -41.5)
[sky262lm] ALIGN_OK after alignPassenger(player) playerYRot=38.95573
[sky262lm] PHASE_DONE phase=interp ticks=96
```
⇒ 三次调用全过；`ALIGN_OK` 里玩家 yaw 真被改成 38.96（证明 `alignPassenger` 的**方法体真的跑完了**，
不是「提前 return」）；四个错误计数全 0。

> 注意：**旧件的实际抛错是 `IncompatibleClassChangeError` / `NoSuchFieldError`，不是地雷表里预测的 `NoSuchMethodError`。**
> 原因是 26.3 把 `InterpolationHandler` 从类变成了**接口**：`invokevirtual` 打到接口上 ⇒ ICCE；`getfield` 打接口字段 ⇒ ICCE
> （这里先被判成 `NoSuchFieldError`，因为字段本身也不存在）。地雷表只写了「会炸」，具体异常类型本报告更正。

---

## 3. 交付物状态

### 3.1 `mods-stable` = 71 jar（未增未减）

| 文件 | 备份 | 原 SHA-256 | 新 SHA-256 |
|---|---|---|---|
| `create-fly-26.2-6.0.9-2-26.3-patched.jar` | `.bak-landmine`（19,639,091 B，原始件）<br>`.bak-landmine-glint`（19,639,255 B，只修 glint 的中间态） | `BBCBC18710D31708EDFD132D0F471FD375660D48E7DB99F3F7632DB9119F81B0`（原始件） | `280B586B3C348C4783D35539C307A88A99FAA490D6B6B6B5CCA487E6703AD41F`（19,639,235 B） |

两个备份都在 `mods-stable` 里、扩展名不是 `.jar` ⇒ Fabric 不会加载。

### 3.2 交付件本体的回归（`--mods mods-stable`，71 jar）

| 项 | 命令 | 结果 |
|---|---|---|
| 标题 | `python tools/launch26/launch.py --game-dir g15/final --mods mods-stable --watch-title --timeout 300` | **`RESULT: TITLE_SCREEN_OK`**（29.5s，三标记全中） |
| 进世界 | `python g15/_run_world.py --game-dir g15/final --mods mods-stable --world lm-final --marker "logged in with entity id" --tag final-world --timeout 300` | **`RESULT: WORLD_OK`**（45.3s） |

交付件日志计数（`evidence/final-world-latest.log`）：

```
Loading 150 mods:                       1
Loaded 2343 advancements
Registry loading errors                 0
NoSuchMethodError                       0
NoSuchFieldError                        0
ExceptionInInitializerError             0
NullPointerException                    0
ReportedException                       0
Exception while updating neighbours     0
```

### 3.3 重扫前后对比（`tools/scan_landmines.py --only create-fly`）

| 指标 | 改前（`scan_before.md`） | 改后（`scan_after.md`） |
|---|---|---|
| 原始指令级发现 | 1147 | 1134 |
| 去重归组 | 287 | 278 |
| **地雷总数** | **95** | **86** |
| 高危 / 中危 / 低危 | 37 / 17 / 41 | **29** / 17 / **40** |
| 缺类 / 缺方法 / 缺字段（组） | 22 / 57 / 16 | 21 / **51** / **14** |

`scan_after.md` 里 `RenderTypes.(glint|glintTranslucent|entityGlint|armorEntityGlint)` 与 `InterpolationHandler`
**一次都不再出现**（`Select-String` 0 命中）。归零 9 条 = glint 族 4 条 + interp 族 5 条。

---

## 4. 复现命令（可直接照抄）

```powershell
$base = "C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
$g15  = "$base\work\run26\port\g15"
$jar  = "$base\work\run26\mods-stable\create-fly-26.2-6.0.9-2-26.3-patched.jar"
$asm  = "$env:APPDATA\.minecraft\libraries\org\ow2\asm\asm\9.10.1\asm-9.10.1.jar"
$javac= "$env:APPDATA\.minecraft\runtime\java-runtime-epsilon\bin\javac.exe"
$java = "$env:APPDATA\.minecraft\runtime\java-runtime-epsilon\bin\java.exe"

# 1) 编译 ASM 工具
& $javac -cp $asm -d "$g15\asm\out" "$g15\asm\PatchLandmines.java"

# 2) 取要改的 class（原始件里取）
python -c "import zipfile,pathlib; z=zipfile.ZipFile(r'$jar'); ..."   # 见 §0 的 oldcls/

# 3) 改
& $java -cp "$g15\asm\out;$asm" PatchLandmines glint  "$g15\oldcls\...\ModelUtil.class" "$g15\newcls\...\ModelUtil.class"
& $java -cp "$g15\asm\out;$asm" PatchLandmines interp "$g15\oldcls2\...\PackageEntity.class" "$g15\newcls2\...\PackageEntity.class" "$g15\out_bridge\bridge\PackageEntityBridge.class"

# 4) 逐类比对
python "$g15\_javap_cmp.py" "$g15\oldcls" "$g15\newcls"  com/zurrtum/create/client/flywheel/lib/model/ModelUtil.class ...
python "$g15\_javap_cmp.py" "$g15\oldcls2" "$g15\newcls2" com/zurrtum/create/content/logistics/box/PackageEntity.class

# 5) 换 entry + 看 jar diff
python "$g15\_patch_jar.py" $jar "$g15\out-jar2\<同名>.jar" "com/...=...class" ...
python "$g15\_jar_diff.py"   "$g15\out-jar2\<同名>.jar"    $jar

# 6) A/B（每次都是存档模板的全新副本）
python "$g15\_mkmods.py"  "$jar.bak-landmine" "$g15\mods-interp-control"
python "$g15\_mkmods.py"  "$g15\out-jar2\<同名>.jar" "$g15\mods-interp-fixed"
python "$g15\_mkworld.py" --game "$g15\game-interp-control" --template "$base\work\run26\vfix-saves\placed" --name lm-interp-control3 --phase interp
python "$g15\_run_world.py" --game-dir "$g15\game-interp-control" --mods "$g15\mods-interp-control" --world lm-interp-control3 --tag interp-control3 --timeout 300

# 7) 交付（先备份，再删除+重写，避免写穿硬链接）
python "$g15\_deliver.py" "$g15\out-jar2\<同名>.jar" ".bak-landmine-glint"
```

---

## 5. 本轮新增的一次性工具

| 文件 | 作用 |
|---|---|
| `g15/asm/PatchLandmines.java` | `mode=glint` / `mode=interp` 的 ASM 工具；带**断言**（意外的指令序列直接抛错），打印每次改写与丢弃的指令 |
| `g15/bridge/src/bridge/PackageEntityBridge.java` | 桥接方法源码（编译后整方法拷入 `PackageEntity`） |
| `g15/_javap_cmp.py` | 两个 class 树的成员清单 + 逐方法字节码比对（归一化 `#nnn` 常量池编号与列宽） |
| `g15/_mkmods.py` | 硬链接 71 jar + 探针，替换指定 create jar |
| `g15/_deliver.py` | 备份 + 「删除再写」交付（不会写穿 `g15/mods-*` 的硬链接），打印前后 SHA/大小/jar 数 |
| `g15/_run_world.py` / `_mkworld.py` | 由 g12/g14 改名而来，marker 改成 `[sky262lm] PHASE_DONE`，计数改成 `NoSuchMethodError / NoSuchFieldError / ExceptionInInitializerError / NPE` |
| `g15/probe/` | 一次性驱动 mod `sky262lm-probe.jar`（**不进交付**，`mods-stable` 里没有它） |

---

## 6. 没做到的 / 已知限制（**别当成「都验完了」**）

### 6.1 glint 族：26.3 把 1 个 glint 劈成 4 个（按图集 × cutout/translucent）

1.21.1 只有**一个** `RenderTypes.glint()`，26.3 有 4 个 item glint（blocks/items × cutout/translucent）。
create 的 `ITEM_CHUNK_MATERIALS` / `CHUNK_LAYERS` **只有 3 个 glint 槽**（1.21.1 的形状），所以只能塞
blocks-cutout / blocks-translucent / entity 三个。**items 图集的 cutout glint（`Sheets.cutoutItemGlintSheet()`）没有对应槽位**
—— 如果将来有代码把这种 RenderType 交给 `ModelUtil.getItemMaterial`，会拿到 `null`。
在这个 jar 里这条路径**是死的**：`BakedItemModelBufferer.bufferItemStack` 的方法体是 `0: return`（早前移植时被 stub 掉了），
`ItemModels.bakeModel` 因此只能拿到空层表。要真正补齐，得再加 2 个 map 槽 + 改 `CHUNK_LAYERS` 的构造，
那已经不是「改 method-ref」了，**本轮没做**。

### 6.2 glint 族的「玩家穿 backtank」路径：**未能作为 A/B**（被另一族地雷挡住）

`phase=backtank` 两版都以同一行崩溃在同一处：

```
net.minecraft.ReportedException: Rendering entity in world
	at ...catnip.render.PonderRenderTypes.<clinit>(PonderRenderTypes.java:38)
```

`PonderRenderTypes` 是地雷表**第 1 号**（`setOutputTarget` / `OutputTarget.ITEM_ENTITY_TARGET`，5 站点）。
javap 核实 26.3 **没有 `OutputTarget` 类、`RenderSetupBuilder` 也没有 `setOutputTarget`** ⇒ 需要重写这几个 render type
（pipeline + `withTexture`/sampler 模型），不是本轮范围。
⇒ **glint 族的验收停在「类初始化 + 两张表 + 四个替代件解析」这一层**，这是本轮能拿到的最强证据；
backtank 的**可见发光效果**没有在屏幕上确认过（也没有截图）。

### 6.3 interp 族：`alignPassenger` 是「构造实体 + 反射直调」，不是真骑上去

- 本 jar 里 `/summon create:carriage_contraption` **必失败**：
  `CarriageContraptionEntity.readAdditional:509` → `Optional.orElseThrow()` → `NoSuchElementException: No value present`
  （车厢实体离不开 train 数据，这不是 bug）。`/summon` 这条路还会连带 `ReportedException: Loading entity NBT` 把整轮打崩。
- 所以探针改成**在客户端直接 `EntityType.create(level, COMMAND)`** 造一个 `OrientedContraptionEntity`（就是
  `create:contraption`，`AbstractContraptionEntity` 的子类），反射把 `prevPosInvalid` 清掉（这个 protected 字段只由 `tick()` 清，
  而实体没进世界），把位置挪到玩家东侧 3 格（`getPrevPositionVec()` 还是 (0,0,0) ⇒ `getContactPointMotion` 非 0，
  否则 `alignPassenger` 会提前 return），然后反射调用 `alignPassenger(player)`。
- 也就是说：**被改的那段方法体确实整段执行了**（玩家 yaw 被改成 38.96、旧件抛 `NoSuchFieldError`），
  但**「玩家真的坐在 Create 载具上」这个场景没有跑**（载具需要 train/contraption 数据，本环境造不出来）。

### 6.4 其它

* 没有重跑 107 mod 全量矩阵；只跑 `mods-stable` 71 jar。
* 没有重编整个 create 工程（有意为之：交付件是字节码补丁出来的，整包重编会覆盖掉 26.3 资源路径/垫片）。
* `g15/probe/sky262lm-probe.jar` 是**一次性验收驱动，不是交付物**。
* 本轮**没有**顺手修 `PonderRenderTypes` 那族 —— 它需要重写，且属于另一族。
