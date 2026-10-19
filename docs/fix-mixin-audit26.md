# fix-mixin-audit26 —— MC 26.3 全量 mixin 审计与修复

> 目标：把 `Sable`（common + fabric）与 `Aeronautics/Simulated` 的 **4 个 mixins.json 共 306 条**全部审计一遍，
> 找出所有会在 **26.3 运行期**（prepare / apply 阶段）炸掉的条目并修掉，直到启动进入标题画面或撞到第一个非 mixin 错误。
>
> 工具：`tools\audit_mixins26.py`（审计，可复跑）、`tools\fix_mixins26.py`（按审计结果成对摘除 / 补 `require=0`）。
> 备份：所有改过的 json / java 旁边都有 `*.bak-mxaudit`；被摘的类在 `<src>\_dropped_mixin26\`，带 `MANIFEST.md`。

---

## 1. 结论

| 指标 | 数值 |
|---|---|
| 审计条目（初始） | **306** |
| 摘除条目（json + 源文件成对） | **17** |
| 修复后条目 | **289** |
| 最终审计 FATAL | **0** |
| 最终审计「需打补丁」 | **0** |
| 仅告警（require/defaultRequire=0） | **31** |
| `--validate`（json 条目 ↔ 源文件） | 289 / 289，bad=0 |
| 启动结果 | **mixin 零错误**；撞到第一个非 mixin 错误：Create-Fly 的 `NoSuchMethodError: Block.simpleCodec(...)`（Bootstrap 阶段），见 §7 |

`289 = 306 - 17`；`--validate` 证明**没有任何一条 json 指向被移走的文件**，也没有孤儿条目。

---

## 2. 工具与复跑方式

```powershell
$PY = "C:\Users\95959\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"

# 全量审计 + 打表（首跑 16s，复跑 <3s；javap 结果按类缓存）
& $PY tools\audit_mixins26.py --json tools\.cache\mixinaudit26\report.json

# 只要坏条目
& $PY tools\audit_mixins26.py --bad-only

# 只校验 json ↔ 源文件成对
& $PY tools\audit_mixins26.py --validate
```

### 它检查什么

1. 4 个配置的全部条目 → `点号 → 路径.java`；
2. `@Mixin(Xxx.class)` / `@Mixin({...})` / `@Mixin(targets="...")` 的目标（含嵌套类 `Outer.Inner` → `Outer$Inner`）；
3. 目标类在 26.3 **是否存在 / 是 class 还是 interface**（javap 一次批量查 30 个类，8 线程）；
4. `@Shadow` / `@Accessor` / `@Invoker` / `@Overwrite` 的成员名 **+ JVM 描述符**
   （源码 Java 类型 → 描述符：泛型擦除、数组、varargs、内部类 `$`、常见 JDK/joml 类型）；
5. `@Inject` 回调 handler 的**参数前缀**是否与目标方法参数一致（Mixin 允许省略尾部参数，但类型/顺序不能错）；
6. handler 与目标方法的**静态性**是否一致（26.3 有实例方法变 static）；
7. `@Inject/@Redirect/@WrapOperation/...` 的 `method=` 名字是否存在，并按 `require` / `defaultRequire`
   区分「会崩」与「已安全（只告警）」。

> 关键教训：**Mixin 是按 `name + descriptor` 精确匹配的**。第一版只比名字，把
> `canFallAtLeast(DDF)Z` vs `(DDD)Z`、`kill()V` vs `kill(ServerLevel)V` 都判成 OK，
> 到运行期才炸。描述符校验补上后一次抓出 7 条同类。

---

## 3. 按问题类型分组

> 同一 mixin 可能同时命中多类，所以下面的数字是「问题条目数」，不是互斥总和。

| 类型 | 条目数 | 处置 |
|---|---|---|
| 目标类不存在（可选 compat `etched`） | 1 | 摘条目 + 移走类 |
| 目标 **class → interface**（`Explosion`） | 1 | 摘（`ServerExplosion` 字段/注入点全变，非机械 retarget） |
| `@Shadow/@Accessor` 成员不存在（渲染族 / 数据族） | 12 | 摘条目 + 移走类 |
| `@Shadow` 方法/字段**描述符**不符 | 7 | 机械改声明类型 / 补参数 |
| `@Inject` handler **参数描述符**不符 | 10 | 改 9（`CompoundTag→ValueInput/ValueOutput` 等）、摘 1（PonderUI） |
| handler **静态性**不符 | 3 | 机械加/去 `static` |
| 注入点方法名缺失（sable 原 `defaultRequire=1`） | 21 | 补 `require = 0`（29 处注解） |
| 已安全（aero/simulated 原 `defaultRequire=0`） | 12 | 不动 |

---

## 4. 摘除清单（17 条，json + 源文件成对）

目录：`work\sable-26\src\_dropped_mixin26\`、`work\aero-port\aeronautics-26\src\_dropped_mixin26\`
（每个目录里有 `MANIFEST.md`，逐条写了原因）。

| # | 配置 | 条目 | 原因（26.3 事实） |
|---|---|---|---|
| 1 | sable | `explosion.ExplosionMixin` | `Explosion` 变 interface；实现类 `ServerExplosion` 只有 `center:Vec3`、`level:ServerLevel`，`explode` 的方块循环搬去 `interactWithBlocks` —— retarget 是重写 |
| 2 | sable | `entity.entity_leashing.LeashableMixin` | `@Overwrite` 的 `legacyElasticRangeLeashBehaviour` 删除（换成 `onElasticLeashPull`/`checkElasticInteractions`，语义不同） |
| 3 | sable | `entity.entities_stick_sublevels.LivingEntityMixin` | `lerpSteps/lerpYRot/lerpXRot` 删除，换成 `lerpHeadSteps/lerpYHeadRot`（头部而非身体插值） |
| 4 | sable | `sign_interaction.SignBlockEntityMixin` | `isFacingFrontText(Player)` → `getSlotPlayerIsFacing(Player)->SignTextSlot`（返回类型/语义都变） |
| 5 | sable | `world_border.LevelMixin` | `Level` 无 `worldBorder` 字段（也无 `getWorldBorder`） |
| 6 | sable | `block_decal_render.LevelRendererMixin` | `LevelRenderer` 无 `level` 字段（26.3 渲染改 submit 两段式） |
| 7 | sable | `particle.LevelRendererMixin` | 同上；`addParticleInternal` 签名也变了 |
| 8 | sable | `sublevel_render.LevelRendererMixin` | `level` / `allChanged` / `renderLevel` 全删 |
| 9 | sable | `sublevel_render.RenderSectionMixin` | `RenderSection` 重写，无 `dirty`/`getDistToPlayerSqr`/`setDirty` |
| 10 | sable | `sublevel_render.RenderSectionAccessor` | 无 `globalBlockEntities`（唯一引用处 `VanillaChunkedSubLevelRenderData` 的 import 已删） |
| 11 | sable | `sublevel_render.block_entity_render.LevelRendererMixin` | `level`/`destructionProgress` 删除，BE 渲染三阶段化 |
| 12 | sable | `sublevel_render.impl.vanilla.LevelRendererMixin` | `level`/`minecraft` 删除，`setupRender/isSectionCompiled/renderSectionLayer` 全删 |
| 13 | sable | `entity.entity_rotations_and_riding.EntityRenderDispatcherMixin` | `EntityRenderDispatcher` 无 `level` 字段，`render(...)` 三阶段化 |
| 14 | sable | `compatibility.etched.StopListeningSoundMixin` | 目标 `gg.moonflower.etched...`：运行环境没装 Etched |
| 15 | sable-fabric | `block_outline_render.LevelRendererMixin` | `LevelRenderer` 无 `level`；`renderLevel` 删除 |
| 16 | simulated | `accessor.CreateBlockEntityBuilderAccessor` | `CreateBlockEntityBuilder` 在 create-fly 里不存在（aero 自带 stub 无 `visualFactory/renderNormally`），`@Accessor` 应用期必失败 |
| 17 | simulated | `ponder.PonderUIMixin` | `PonderUI.renderScene` 参数改成 `(GuiGraphicsExtractor,int,int,float,float)`，scene index 不再是参数，handler 无法对齐 |

---

## 5. 机械修复清单（未摘，保留功能）

### 5.1 `@Shadow` 描述符 / 静态性

| mixin | 26.3 实际 | 修法 |
|---|---|---|
| `entity.entities_stick_sublevels.EntityMixin` | `Entity.moveTo` → `snapTo` | 改 shadow 名 + 调用点 |
| `entity.entity_sublevel_collision.EntityMixin` | `kill()` → `kill(ServerLevel)` | 改 shadow + `instanceof ServerLevel` 守卫 |
| `respawn_point.sleeping.LivingEntityMixin` | `setPosToBed(BlockPos)V` → `(BlockPos)Z` | 改返回类型，`return true` |
| `entity.arrows_hit_blocks.AbstractArrowMixin` | 字段 `inGround` → `isInGround()` | 字段 shadow 改方法 shadow |
| `entity.entity_sublevel_collision.PlayerMixin` | `bob` 字段删除（且原代码没用） | 删 shadow |
| `camera.new_camera_types.MinecraftMixin` | 字段 `cameraEntity` → `getCameraEntity()` | 改方法 shadow（类改 abstract） |
| `entity.entity_rotations_and_riding.EntityMixin` | `newDoubleList` 删除 | 本地 `@Unique sable$newDoubleList` 替代 |
| `entity.entity_pathfinding.RandomPosMixin` | 参数 `int` → `double` | 改签名 + `(int)` 转型 |
| `camera.camera_zoom.CameraMixin`、`entity.entity_swimming.CameraMixin`、`water_occlusion.CameraMixin` | `Camera.level` 类型是 `Level` 不是 `BlockGetter` | 改字段类型 |
| `entity.entity_swimming.CameraMixin` | `getNearPlane(float)` | 补参数 |
| sable-fabric `camera_rotation.CameraMixin` | `FORWARDS/UP/LEFT` 是 `Vector3fc` | 改类型 |
| `camera.camera_rotation.EntityMixin` | `calculateViewVector` 变 **static** | 改挂实例方法 `getViewVector`（行为等价） |
| `entity.tamed_teleport.TamableAnimalMixin` | 目标 `maybeTeleportTo` 是实例方法 | handler 去掉 `static` |
| `linked_controller_binding.LinkedControllerItemMixin` | 目标 `onItemUseFirst` 变 **static** | handler 加 `static` |
| `explosion.ServerLevelMixin` | `ServerLevel.explode(...)` 返回 **void**，且多一个 `WeightedList<ExplosionParticleInfo>` 参数 | `@WrapMethod` handler 改 void + 补参数 + `Operation<Void>` |
| `plot.lighting.BlockAndTintGetterMixin` | `getBrightness/getRawBrightness/getLightEngine` 都声明在父接口 `BlockAndLightGetter`；Mixin 的 `@Shadow/@Overwrite` **不查接口继承** | 目标改标 `BlockAndLightGetter`，`getLightEngine()` 改显式 cast |
| `assembly.AbstractFurnaceBlockEntityMixin` | `recipesUsed` 是 `Reference2IntOpenHashMap<ResourceKey<Recipe<?>>>`（不是 `Object2IntOpenHashMap<Identifier>`） | 改字段类型 |

### 5.2 `@Inject` handler 参数

| mixin | 26.3 实际参数 | 修法 |
|---|---|---|
| `tracking_points.EntityMixin` | `load(ValueInput)` | 改参数 + `read(...).ifPresent`；`ValueInput` 只读，去掉 `remove("RootVehicle")` |
| `respawn_point.ServerPlayerMixin` | `addAdditionalSaveData(ValueOutput)` | 改参数 + `output.store(...)` |
| `camera.new_camera_types.GameRendererMixin` | `renderLevel()` 无参 | handler 去掉 `DeltaTracker` |
| `entity.entities_turn_with_sub_levels.GameRendererMixin` | 同上 | 同上 |
| `water_occlusion.GameRendererMixin` | `render()` 无参 | handler 去掉 `DeltaTracker, boolean` |
| aero `steam_vent.BoilerDataMixin` | `read(ValueInput,int)` / `write(ValueOutput)` | 改 handler + `Codec.INT` 读写 |
| simulated `hold_interaction.GoggleOverlayRendererMixin` | `renderOverlay(Minecraft, GuiGraphicsExtractor, DeltaTracker)` | 补 `Minecraft` 首参 |
| simulated `world_presets.PrimaryLevelDataMixin` | `setTagData(CompoundTag, UUID)` | 改 handler 参数 |
| `game_test.TestCommandMixin` | `resetGameTestInfo(CommandSourceStack, GameTestInfo)` | 补首参 |
| `plot.LevelChunkMixin` | `setBlockState(BlockPos, BlockState, int)` | 第三参 `boolean`→`int`（两个注入点） |
| `udp.ConnectionMixin` | `connect(InetSocketAddress, EventLoopGroupHolder, Connection)` | 第二参 `boolean`→`EventLoopGroupHolder` |
| simulated `world_presets.CreateWorldScreenMixin` | `createNewWorld(LayeredRegistryAccess, WorldDataAndGenSettings, Optional)` | 改参数 + `worldDataGenSettings.data()` |
| simulated `world_presets.PrimaryLevelDataMixin`（parse） | `parse(Dynamic, LevelSettings, SpecialWorldProperty, Lifecycle)` | 去掉多出来的 `WorldOptions` |

### 5.3 `require = 0`（29 处 / 21 条目）

主要是 26.3 改名/搬家的方法：`method_*`（intermediary 残留）、`renderLevel`、`setup`、`renderCrosshair`、
`getLightColor`、`canSpreadTo`、`isNaturalSpawningAllowed`、`tickNonPaused`、`setDirty`、`addToGoggleTooltip` 等。
逐条见 `tools\.cache\mixinaudit26\report.json` 的 `problems`。

> **另外**：`sable.mixins.json` 的 `injectors.defaultRequire` 由 `1` 改为 `0`（与 aero/simulated 对齐）。
> 原因：`@At` 注入点目标缺失（如 `entity.entity_rotations_and_riding.PlayerMixin` 的 Redirect 0/1）
> 无法在纯静态审计里 100% 覆盖，`require=0` 让它只告警。**这是有意的降级**（见 §8）。

---

## 6. 成对性校验（硬约束）

```
$ python tools\audit_mixins26.py --validate
=== sable: sable.mixins.json  entries=191 pkg=dev.ryanhcode.sable.mixin
=== sable-fabric: sable-fabric.mixins.json  entries=8 ...
=== aeronautics: aeronautics.mixins.json  entries=21 ...
=== simulated: simulated.mixins.json  entries=69 ...

TOTAL entries=289 bad=0
```

被移走的 17 个类全部在 `_dropped_mixin26\`，**没有任何 json 条目指向它们**；
也没有「移了类但 json 没摘」的组合。

---

## 7. 启动验证

最终一轮：`work\run26\probe7`（6 个 jar：aeronautics / sable / sablecompanion / create-fly-patched / ForgeConfigAPIPort / fabric-api）。
（`probe6` 与 `probe7` 结果完全一致；probe7 用的是清掉 `.bak-mxaudit` 后的最终 jar。）

### 7.1 到了哪一步（`latest.log` 原文）

```
[18:31:49] [main/INFO]: SpongePowered MIXIN Subsystem Version=0.8.7 ...
[18:31:51] [main/INFO]: Initializing MixinExtras via ... (version=0.5.5).
[18:31:54] [Datafixer Bootstrap #0/INFO]: 307 Datafixer optimizations took 1015 milliseconds
```

**`latest.log` 里 `Mixin apply ... failed` / `InvalidMixinException` / `InvalidInjectionException` 出现 0 次。**
（对比：第一轮在 `Loading 56 mods` 后 1 秒就 `Mixin prepare ... ExplosionMixin` 崩。）

### 7.2 撞到第一个**非 mixin** 错误（本任务终点）

进程退出码 -1，崩溃报告 `work\run26\probe7\crash-reports\crash-2026-10-17_18.32.05-client.txt`：

```
Description: Bootstrap

java.lang.NoSuchMethodError: 'com.mojang.serialization.MapCodec
  com.zurrtum.create.content.kinetics.steamEngine.SteamEngineBlock.simpleCodec(java.util.function.Function)'
	at knot//com.zurrtum.create.content.kinetics.steamEngine.SteamEngineBlock.<clinit>(SteamEngineBlock.java:56)
	at knot//net.minecraft.world.level.block.Blocks.register(Blocks.java:1186)
	at knot//com.zurrtum.create.AllBlocks.<clinit>(AllBlocks.java:194)
	...
	at knot//net.minecraft.server.Bootstrap.bootStrap(Bootstrap.java:58)
```

**判定：这是 Create-Fly（`com.zurrtum.create`）自己的 26.2→26.3 API 缺口，不是 mixin 配置问题。**
26.3 删掉了 `Block.simpleCodec(...)`（方块不再有 MapCodec，见 `docs\fix-aero-registrate.md`），
而 create-fly 的 `SteamEngineBlock` 仍在调用它。属于**下一个族**，需要改 Create-Fly 的 jar/字节码或源码。

> 也就是说：**mixin 审计的终点已达** —— 启动过程不再因任何 `@Mixin/@Shadow/@Inject` 失败，
> 直到 Bootstrap 阶段被 Create 的 `NoSuchMethodError` 拦住。

---

## 8. 降级清单（必须进交付说明）

1. **爆炸对子维度的影响失效**（`ExplosionMixin` 摘除）—— 26.3 `Explosion` 接口化，`ServerExplosion`
   的字段/注入点全部不同；重写不是本次审计范围。
2. **子维度渲染整族降级**（7 个 LevelRenderer/RenderSection/EntityRenderDispatcher mixin 摘除）——
   与 `docs\fix-sable-render.md` 里「子维度分块地形不绘制」的既有降级一致。
3. **拴绳弹性 / 睡眠插值 / 告示牌朝向 / 世界边界** 4 条行为降级（目标方法语义变了，无法机械替换）。
4. **传送包的 `actuallyInSubLevel` 标记恒为 false**（`ClientboundTeleportEntityPacketMixin` 两个注入点删除，
   保留 extension 实现以免 cast 崩）。
5. **载入存档时不再强制下车**（`ValueInput` 只读，`remove("RootVehicle")` 无等价物）。
6. **sable 全部注入器改为「找不到只告警」**（`defaultRequire: 0`）—— 换取启动不被零散 `@At` 失败拦住；
   代价是后续 26.3 改动不会在启动时立刻暴露。建议进世界后逐项回归。
7. **ponder 阴影偏移/淡出**（`ponder.PonderUIMixin` 摘除）—— 纯视觉。
8. **`sable` 的 `defaultRequire` 改成 0** —— 所有注入点缺失只告警（见 §5.3）。

---

## 9. 下一族（非 mixin，已交接）

`Create-Fly` 的 `com.zurrtum.create.content.kinetics.steamEngine.SteamEngineBlock` 在 `<clinit>` 调用
26.3 已删除的 `Block.simpleCodec(Function)` → `NoSuchMethodError`（Bootstrap 阶段）。
同理可预期 Create 里其它 `simpleCodec/propertiesCodec` 调用会继续炸；需要按
`docs\fix-aero-registrate.md` 的同一修法处理 Create-Fly 的字节码/jar（本任务未动 Create）。
