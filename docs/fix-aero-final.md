# fix-aero-final —— Aeronautics 26.3 收尾：**71 → 0**，`compileJava` BUILD SUCCESSFUL

> 任务：把 Aeronautics 26.3 最后 **71 个编译错误**清零。本文是这一轮的逐族修法、降级清单与 26.3 新事实。
> 起始 `notes\aero26-compile-14.log`（71 行 / 70 unique）→ 终点 `notes\aero26-final.log`（**0 错 / BUILD SUCCESSFUL**）。

---

## 1. 数字

| 指标 | 值 |
|---|---|
| 起始 | **71** 行（去重 70）—— `aero26-compile-14.log` |
| 终点 | **0** —— `aero26-final.log`（`clean compileJava`，1,074 个 class） |
| 改动源文件 | **39**（全部有 `.bak-final` 备份） |
| 修掉错误 | **71**（每处一行对照，见 §3） |
| 新降级 | **4 条**（§4：1 视觉动画 / 1 渲染插值 / 1 性能 / 1 实现方式），另有 **2 条语义微调**（§4.2） |
| 复现 | `cd work\aero-port\aeronautics-26; .\gradlew.bat clean compileJava --no-daemon` |

三个日志都在 `notes\`：

```
aero26-compile-14.log   71 错（起点）
aero26-final-1.log       0 错 增量编译（首次过关）
aero26-final.log         0 错 clean 全量（验收用）
```

---

## 2. 26.3 新事实（**javap 现查，可直接复用，别再查一遍**）

| 1.21.11 | 26.3 | 依据 |
|---|---|---|
| `LivingEntity.swing(InteractionHand)` | **`boolean swing(InteractionHand, SwingAnimation, boolean)`**（第 3 参 = `sendToSelf`）。**没有 2 参重载** ⇒ `swing(h)` ≡ `swing(h, SwingAnimation.DEFAULT, false)` | javap `LivingEntity`；`SwingAnimation` 是 record(`SwingAnimationType`, int)，有 `DEFAULT` |
| `LivingEntity.swingTime / swinging / swingingArm`（public 字段） | **全删**，改 `private final SwingState swingState` + `SwingState.startIfAble(hand, anim, duration)`。**无法再逐 tick 复位**（`startIfAble` 对正在进行的挥动返回 false） | javap `-p LivingEntity` |
| `Player.displayClientMessage(Component, boolean)` | **`sendOverlayMessage(Component)`**（`true`）/ **`sendSystemMessage(Component)`**（`false`） | javap `Player` |
| `Gui.setOverlayMessage(Component, boolean)` | 方法搬到 **`Gui.hud`**（`net.minecraft.client.gui.Hud#setOverlayMessage(Component, boolean)` 原样存在） | javap `Gui`（只有 `hud` 字段）/ `Hud` |
| `Inventory.placeItemBackInInventory(ItemStack)` | `(ItemStack, Prediction)` / `(ItemStack, boolean, Prediction)`，`Prediction.PREDICTED`\|`SERVER_ONLY` | javap `Inventory` / `Prediction` |
| `PushReaction.IGNORE / PUSH_ONLY` | `IGNORE_ENTITY` / `PUSH`（枚举只剩 PUSH_PULL/PUSH/POPPED/IMMOVEABLE/IGNORE_ENTITY） | javap `PushReaction` |
| `new ChunkPos(BlockPos)` | **`ChunkPos.containing(BlockPos)`**；`ChunkPos.toLong()` → **`pack()`**（26.3 是 record） | javap `ChunkPos` |
| `BlockPos.getCenter() / getBottomCenter()` | **删** ⇒ `Vec3.atCenterOf(Vec3i)` / `Vec3.atBottomCenterOf(Vec3i)` | javap `BlockPos`（无这两个方法）/ `Vec3` |
| `net.minecraft.world.level.BlockAndTintGetter` | 接口搬到 **`net.minecraft.client.renderer.block.BlockAndTintGetter`**；但 **`GirderBlock.isConnected` 的首参在 26.3 是 `BlockAndLightGetter`**（mixin 必须用这个，否则运行期描述符不匹配） | javap 两处；见 §4.2-D5 |
| `LevelRenderer.getLightColor(ClientLevel, BlockPos)` | **`net.minecraft.util.LightCoordsUtil.getLightCoords(BlockAndLightGetter, BlockPos)`**（`LightCoordsUtil` 在 `util` 包，不是 `client.renderer`） | jar 类表 + javap |
| `EntityType.is(TagKey)`（1.21.11 有 `is` 便利方法） | 类上**没有** `is` ⇒ `type.builtInRegistryHolder().is(tag)`（`Holder.Reference` 有 `is(TagKey)`） | javap `EntityType` / `Holder$Reference` |
| `InputConstants.Type.KEYSYM` | **`Type.KEYBOARD`**（枚举只剩 `KEYBOARD`/`MOUSE`）；`getOrCreate(int)` 仍在 | javap `InputConstants$Type` |
| `InputConstants.isKeyDown(long window, int key)` | **`isKeyDown(int)`**（窗口参数删除） | javap `InputConstants` |
| `AllKeys.isKeyDown(int)`（Create） | **删**（Create 26.3 的 `AllKeys` 只剩 3 个 `KeyMapping` + `ALL`） | javap `com.zurrtum.create.client.AllKeys` |
| `Entity.interact(Player, InteractionHand)` + `interactAt(Player, Vec3, InteractionHand)` | **合并为一个**：`InteractionResult interact(Player, InteractionHand, Vec3)`（`interactAt` 不存在） | javap `Entity` |
| `BlockBehaviour.getLightBlock(BlockState)` | **`getLightDampening(BlockState)`** | javap `BlockBehaviour`（全表无 getLightBlock） |
| `HangingEntity.recalculateBoundingBox()` public? | **`protected`**；但 **`BlockAttachedEntity.setPos(double,double,double)` 内部就调它** ⇒ 外部再调是冗余 | javap `-c BlockAttachedEntity` |
| `ServerLevel.entityManager` / `PersistentEntitySectionManager.sectionStorage` | **都是 private**（26.3 无 accesswidener 可用）⇒ 只能走公开的 `Level#getEntities(Entity, AABB, Predicate)` / `ServerLevel#getAllEntities()` | javap `-p` 两者 |
| `DataComponentPatch.entrySet()` | **删**。公开 API 只剩 `get/size/isEmpty/forget/split`；**`split()` → `SplitResult{DataComponentMap added(); Set<...> removed()}`**（就是原来的 entrySet 拆两半） | javap |
| `ItemContainerContents.stream()` | **`itemCopies()`** / `nonEmptyItemCopyStream()` / `nonEmptyItems()` | javap |
| `ChatFormatting.getColor()` | **删**（只剩 `values/valueOf/toString/stripFormatting/getByCode`）⇒ 颜色只能自己写常量（GRAY=`0xAAAAAA`） | javap |
| `ProjectileDeflection.deflect(Projectile, Entity, RandomSource)` | 形参 4 个：**`deflect(Projectile, Entity, RandomSource, Vec3)`**（lambda 也要 4 参） | javap |
| `RenderSetupBuilder.bufferSize(int)` | **删**（全表 13 个方法，无 bufferSize）⇒ 用默认缓冲大小 | javap `RenderSetup$RenderSetupBuilder` |
| `ServerGamePacketListenerImpl.aboveGroundTickCount/aboveGroundVehicleTickCount` | **private** ⇒ **`resetFlyingTicks()`**（javap 字节码证实：正是把这两个字段置 0） | javap `-c` |
| `ForceGroups.GRAVITY_VALUE` … `MAGNETIC_FORCE_VALUE`（Sable 1.21.1） | 26.3 Sable 只剩 **`RegistryObject<ForceGroup> GRAVITY/DRAG/...`**（`get()` 直接返回字段，不抛异常） | javap `ForceGroups` / `RegistryObject` |
| `LerpedFloat.getValue(float)` | `getValue()`（无插值）也还在 | javap `LerpedFloat` |

---

## 3. 逐族修法（71 错 → 0）

| # | 族 | 条数 | 修法 | 文件 |
|---|---|---|---|---|
| 1 | `LivingEntity.swing` 签名 | **11** | `swing(h)` → `swing(h, SwingAnimation.DEFAULT, false)`（`DEFAULT` = 原版默认挥动长度；`false` = 不给自己发包，与旧的 1 参便利方法同义） | Spring×2 / Zipline×3 / HoneyGlueClient×2 / ClientHandle×1 / LevititeCatalyzer×1 / LevititePacket×1 / MergingGlue×1 |
| 2 | `displayClientMessage` | **7** | `(c, true)` → `sendOverlayMessage(c)`（4 处）；`(c, false)` → `sendSystemMessage(c)`（3 处，SceneScheduler） | Zipline×2 / DiagramEntity / PlungerLauncher / SceneScheduler×3 |
| 3 | `placeItemBackInInventory` | **4** | 补第 2 参 `Prediction.SERVER_ONLY` | EnvelopeEncasedShaft / MountedPotatoCannon / PortableEngine / RopeStrandHolderBehavior |
| 4 | `PushReaction.IGNORE / PUSH_ONLY` | **4** | → `IGNORE_ENTITY`（2）/ `PUSH`（2，`PUSH_ONLY` 已不存在，`PUSH` 最接近） | GustEntity / HoneyGlueEntity / SimAssemblyContraption×2 |
| 5 | `@Override` 失效 | **3** | 父类签名变了：`getLightBlock`→`getLightDampening`；`interact(Player,InteractionHand)`→`interact(Player,InteractionHand,Vec3)`；`interactAt(Player,Vec3,InteractionHand)`→同上合并形态 | EnvelopeBlock / HoneyGlueEntity / DiagramEntity |
| 6 | `ChunkPos` 构造器 | **3** | `new ChunkPos(pos)` → `ChunkPos.containing(pos)` | ClientHandleHandler / RopeStrandHolderBehavior / PhysicsStaffActionPacket |
| 7 | `BlockAndTintGetter` | **2** | **不是搬包**：`GirderBlock.isConnected` 首参在 26.3 是 `BlockAndLightGetter`，mixin 处理器必须同型 ⇒ 换 import + 换形参 | GirderBlockMixin |
| 8 | `getLightColor` | **2** | → `LightCoordsUtil.getLightCoords(this.level, blockpos)` | PropellerAirParticle / MagnetFieldParticle |
| 9 | `EntityType.is(TagKey)` | **2** | `e.getType().builtInRegistryHolder().is(tag)` | LaserBehaviour / ArmorStandItemMixin |
| 10 | `KEYSYM` / `AllKeys` | **3** | `Type.KEYSYM`→`Type.KEYBOARD`（2）；`AllKeys.isKeyDown(k)`→`InputConstants.isKeyDown(k)`（1） | KeyWidget / LinkedTypewriterItemBindHandler / SimKeys |
| 11 | 客户端挥臂三字段 | **3** | `swingTime/swinging/swingingArm` 三行 → 一行 `swing(MAIN_HAND, DEFAULT, false)`（**降级 D1**） | ClientHandleHandler |
| 12 | `ForceGroups.XXX_VALUE` | **7** | → `ForceGroups.XXX.get()` | ForceGroupIndex |
| 13 | `SimAssemblyHelper` | **4** | `entityManager`+`sectionStorage`+`toLong()` 三连 → 按 plot chunk 列 `ServerLevel#getEntities(null, columnBox, e->true)`；`chunk.getPos().toLong()` 不再需要；`recalculateBoundingBox()` 调用删除（`setPos` 内部已调） | SimAssemblyHelper |
| 14 | `DataComponentPatch` 无迭代 | **1** | `entrySet()` → `split().added()`（`TypedDataComponent` 逐个 `builder.set`）+ `split().removed()`（`builder.remove`） | ItemInfoWrapper |
| 15 | 散点（逐个 javap） | **17** | 见下表 | — |

**散点（15）逐条**：

| 位置 | 错 | 修法 |
|---|---|---|
| `SimTuple.setA/setB`（×2） | 替身类没有 setter（1.21.1 `Tuple` 是可变的） | 给 `SimTuple` 补 `setA/setB` 并把字段去掉 `final` |
| `SwivelBearingBlockEntity:587` | `BlockPos.getCenter()` 已删 | `Vec3.atCenterOf(...)` |
| `KineticScenes:838` | `BlockPos.getBottomCenter()` 已删 | `Vec3.atBottomCenterOf(...)` |
| `LinkedTypewriterInteractionHandler:228` | `ItemContainerContents.stream()` 已删 | `.itemCopies()` |
| `DisplayLinkScreenMixin:29` | `ChatFormatting.getColor()` 已删 | 常量 `0xAAAAAA`（GRAY）+ 注释 |
| `LaunchedPlungerEntity:85` | `ProjectileDeflection` lambda 少一参 | 补第 4 参 `Vec3` |
| `PonderSceneMixin:109`（×2 行） | 局部变量 `pt` 根本不在作用域（**移植期就坏的，不是这次引入**） | `getValue()`（无 partialTick）+ 注释（**降级 D2**） |
| `RopeRidingPacket:32,33`（×2） | 两个 `aboveGround*TickCount` 已 private | `player.connection.resetFlyingTicks()`（字节码等价） |
| `EnvelopeBlock:132` | `getLightBlock` 改名 | `getLightDampening` |
| `HoneyGlueEntity:128` | `ItemParticleOption(ParticleType, ItemStack)` 已删 | `ItemStackTemplate.fromStack(stack)` |
| `HoneyGlueEntity:243` / `DiagramEntity:412` | 见族 5 | `interact(Player, InteractionHand, Vec3)` |
| `AeroRenderTypes:53` | `RenderSetupBuilder.bufferSize(int)` 已删 | 删掉该调用，用默认缓冲（**降级 D3**） |
| `ClientHandleHandler:56` | 见族 6 | — |

---

## 4. 降级清单（逐条：丢了什么 / 为什么 / 可修回？）

### 4.1 真降级（**4 条**）

| # | 位置 | 丢了什么 | 为什么必须丢 | 可修回？ |
|---|---|---|---|---|
| **D1** | `ClientHandleHandler`（手柄第一人称「恒定挥臂」） | 原来每 tick 把 `swingTime` 置 0 强制**循环**挥臂；现在每 tick 调 `swing()`，但 `SwingState.startIfAble` 对进行中的挥动返回 false ⇒ **只挥一次**，不再无限循环 | 三个字段并入 private `SwingState`，26.3 无任何公开复位入口，且 accesswidener 在 no-remap Loom 下不可用（见 §5） | 需给 `LivingEntity` 加 accessor mixin（读 `swingState` 字段）后写回 `SwingState`；或 `SwingAnimation` 给一个超长 duration 的动画近似 |
| **D2** | `PonderSceneMixin.onCameraSet` | 相机旋转的**亚 tick 插值**（`getValue(pt)` → `getValue()`）；高帧率下旋转略「阶梯」 | 原代码引用的 `pt` 在该 `@Redirect` 里**从来不在作用域**（这就是那 2 条编译错误本身） | 把 `pt` 用 `@Local(argsOnly = true) float partialTick`（MixinExtras）接回来即可，1 行；本轮为了「不再引入新依赖」没做 |
| **D3** | `AeroRenderTypes.make` | `RenderType` 的显式 `bufferSize(TRANSIENT_BUFFER_SIZE)` | `RenderSetupBuilder#bufferSize` 26.3 已删（13 个方法全表无） | 等 26.3 提供等价设置；**只影响缓冲增长策略，不影响画面** |
| **D4** | `SimAssemblyHelper`（拆解时搬胶水/悬挂实体） | 实现由「内部 section storage 逐 section」改为「按 plot chunk 列的 AABB 查询」——**覆盖集合等价**（原实现就是遍历这些 chunk 的全部实体），但多了一次 AABB 相交判断，且不再区分 loaded section | `entityManager` / `sectionStorage` 双 private，`ChunkPos.toLong()` 已删 | 语义无需修；若要在意性能，改成一次 `getEntities(null, 全局包围盒, e->true)` |

> D4 的「悬挂实体包围盒重算」**不算降级**：`BlockAttachedEntity#setPos` 内部就调 `recalculateBoundingBox()`（javap 字节码证实），原代码那行是冗余调用。

### 4.2 语义微调（**2 条，不算损失但要记录**）

| # | 位置 | 变化 |
|---|---|---|
| **S1** | `HoneyGlueEntity.interact` / `DiagramEntity.interact` | `interactAt(...)` 并入 `interact(...)` 后，这两个重写**同时**接管「精确命中」与「普通右键」两条路径（原来只接管精确命中）。行为上都是「玩家与实体交互」，实际无可见差异 |
| **S2** | `DisplayLinkScreenMixin` | `ChatFormatting.GRAY.getColor()` → 硬编码 `0xAAAAAA`。数值与原版常量一致（零视觉差异），但若原版改色调需同步 |

### 4.3 零损失等价改写（不计降级）

`swing(+SwingAnimation.DEFAULT,false)`、`sendOverlayMessage`/`sendSystemMessage`、`placeItemBackInInventory(+Prediction.SERVER_ONLY)`、
`PushReaction.IGNORE_ENTITY`/`PUSH`、`ChunkPos.containing`、`LightCoordsUtil.getLightCoords`、
`builtInRegistryHolder().is`、`Type.KEYBOARD`、`InputConstants.isKeyDown(int)`、`ForceGroups.XXX.get()`、
`DataComponentPatch.split()`、`ItemContainerContents.itemCopies()`、`Vec3.atCenterOf/atBottomCenterOf`、
`ItemStackTemplate.fromStack`、`getLightDampening`、`resetFlyingTicks()`、`Gui.hud.setOverlayMessage`、
`ProjectileDeflection` 第 4 参、`Entity.collideBoundingBox((Entity) null, …)`（显式转型解决重载歧义）、
`SimTuple.setA/setB`（补回 1.21.1 `Tuple` 的可变性）。

---

## 5. 为什么没动 accesswidener

`LivingEntity.swingState` / `ServerLevel.entityManager` 这类 private 成员，理论上可用 AW 打开。
但本工程是 **no-remap Loom**，而 AW 要求 `official` 命名空间（R349 已记：Sable 的 `named` 头会让依赖工程在配置期就崩）。
因此本轮统一走**公开 API 替代**（D1/D4），不引入 AW。

---

## 6. 备份与回滚

* **39 个源文件**的**本轮改前快照** = `<文件>.bak-r352`（`tools\make-bak-r352.cjs` 生成，见下）。
  回滚单文件：`Copy-Item <f>.bak-r352 <f>`。
* ⚠ **诚实记录**：`tools\fix-batch.cjs` 的备份策略是「`.bak-final` 不存在才创建」，而这 39 个文件**全都已经带了
  更早轮次的 `.bak-final`（05:52–17:24，属于 R344/R350/R351 等线）**，所以它**没有**生成新备份 ——
  那些 `.bak-final` 不是本轮改前的状态。为补上这一点，本轮另写了 `tools\make-bak-r352.cjs`：
  **把 table-batch1/2 的替换表反向套用到当前文件**，重建出改前快照 `.bak-r352`（39 个，已核对：无一与当前文件相同）。
  代价是它依赖「替换表完全覆盖本轮改动」这一前提（本轮改动确实全部来自这两张表 + GirderBlockMixin 的 1 处手工改动，
  后者与 SimTuple 的备份是直接写出的原文）。
* 文件里还并存更早的 `.bak-veil2` / `.bak-final` 等历史备份 —— 回滚时**认准 `.bak-r352`**。
* 本轮的三个批处理脚本可重放（幂等：找不到原文就跳过该文件）：
  `tools\fix-batch.cjs`（执行器）+ `tools\table-batch1.cjs` / `tools\table-batch2.cjs`（对照表）。

---

## 7. 复现 / 验收

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\aero-port\aeronautics-26
$env:JAVA_HOME="$env:APPDATA\.minecraft\runtime\java-runtime-epsilon"
.\gradlew.bat clean compileJava --no-daemon --console=plain   # → BUILD SUCCESSFUL，0 错 0 警告
```

日志：`notes\aero26-final.log`（clean 全量，1,074 个 class）。
错误解析器：`node tools\parse-aero-errors.cjs notes\aero26-final.log --by=symbol`（0 组）。

---

## 8. 交接：`compileJava 0 错 ≠ 能跑`

上一线（R349/R350/R351）已经反复踩过：**mixin 的 `@Inject/@Redirect/@Shadow` 全是运行期解析**。
本轮只验证了编译；以下运行期点最可能在启动时炸，按顺序验：

1. `GirderBlockMixin`：`@Inject(method="isConnected")` 已确认 26.3 目标存在且首参 `BlockAndLightGetter`（javap 实测）；
2. `PonderSceneMixin`：`@Redirect` 目标 `PonderScene$SceneCamera.set(FF)` 存在（javap 实测）；
3. `DisplayLinkScreenMixin`：`DisplayTarget.getLineOptionText(I)` 存在（javap 实测）；
4. `ArmorStandItemMixin`：`WrapOperation` 目标 `List.isEmpty()` 仍在 `useOn` 里（未复核，需启动验）；
5. `ForceGroupIndex` 静态块会调 `ForceGroups.XXX.get()` —— `RegistryObject.get()` 直接返回字段（无异常），
   但若 `ForceGroups` 尚未初始化就会拿到 null；`ForceGroupIndex` 只有在首次使用时才建表，需在启动后确认 `ids()` 非空。
6. 全量启动验证仍走 `tools\launch26\launch.py`（见 `docs\DEPS-26.3.md`）。

---

## 9. 本轮的 26.3 事实增量（供其它线复用）

本轮新增了 §2 里带 **★** 的条目，其中最容易再踩的三个：

* **`GirderBlock.isConnected` 用 `BlockAndLightGetter`**（不是搬家的 `BlockAndTintGetter`）——编译器两个都能过，
  但 **mixin 运行期只认前者**。
* **`ChatFormatting.getColor()` 整方法删除** —— 影响所有「用格式色取 RGB」的地方。
* **`DataComponentPatch` 没有任何公开迭代入口** —— 只能 `split()`；`entrySet()/patchMap()` 这类写法全要改。
