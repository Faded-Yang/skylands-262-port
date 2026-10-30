# Sable 26.3 —— mixin 线（R348）：mixin 域编译错误清零报告

> 范围：**只动 `common/` 与 `fabric/`**；`neoforge/`、`_dropped*/`、`sublevel/render/**`、`render/**`、
> `mixin/sublevel_render/**`、`mixin/dynamic_directional_shading/**` 一个字节没动。
> 编译：`port26\compile-r4.log`（起点 **273**）→ `compile-mx4.log`（终点，见 §1）。
> 脚本：`port26\fix_mx.py` / `fix_mx2.py` / `fix_mx3.py` / `fix_mx4.py`（每处都是显式
> `(文件, old, new, 期望出现次数)` 三元组，**全部校验通过才落盘**）；
> JSON 校验：`port26\validate_mixins_json.py`；错误解析：`parse_mx3.py` / `show_mx3.py` / `ctx.py`。

---

## 1. 数字（实测）

| 口径 | 起点 `compile-r4.log` | 终点，我的 `compile-mx4.log` |
|---|---|---|
| javac 尾行总错误 | **273** | **4** |
| 去重 unique | 267 | 4 |
| **mixin 域（我的域）** | **142** | **0** |

起点 mixin 域按文件：

| 错误 | 文件 | 最终处置 |
|---|---|---|
| 15 | `mixin/particle/ParticleEngineMixin` | 删掉 `crack` 的 `@Redirect`（`ParticleEngine.crack` 在 26.3 已删） |
| 12 | `mixin/entity/teleport_players/ServerPlayerMixin` + `respawn_point/ServerPlayerMixin` | `RelativeMovement`→`Relative`；`RespawnConfig` 重写 |
| 9 | `mixin/clip_overwrite/BlockGetterMixin` | `ClipContext` 三字段转私有 → 走 `ClipContextExtension` 新访问器 |
| 7 | `mixin/AbstractSableMixinPlugin` | maven 版本区间换自带最小实现 |
| 6 | `mixin/entity/parrot/ParrotMixin` | 换包 `.animal.parrot.*`（**类没删**） |
| 6 | `mixin/entity/entity_rendering/EntityRendererMixin` | `noCulling`→`affectedByCulling`；`getBoundingBoxForCulling` 移回 `EntityRenderer` |
| 5 | `mixin/entity/entities_stick_sublevels/ClientPacketListenerMixin` | `Entity.lerpTo` → `moveOrInterpolateTo(Vec3,FF)` |
| 5 | `mixin/entity/entities_stick_sublevels/EntityRenderDispatcherMixin` | `renderHitbox` 已删 ⇒ 整段调试线框移除 |
| 其余 ~77 | 见 §2、§3 | —— |

> ⚠ 总错误数里有**其他线（api/network/storage/physics/fabric platform）的并行进度**，
> 所以「273 → 终点」不全是本线贡献；**mixin 域的 142 → 0 是本轮的成果**，可用文件级计数复核。

---

## 2. 机械替换（26.3 精确修法，语义不变）

| 1.21.x | 26.3 | 依据（javap 26.3.jar） | 落地点 |
|---|---|---|---|
| `world.entity.animal.Parrot` / `ShoulderRidingEntity` | `world.entity.animal.parrot.*` | 两类**都还在**，只是移入 `.parrot` 子包 | `ParrotMixin` |
| `world.entity.projectile.ThrownTrident` | `world.entity.projectile.arrow.ThrownTrident` | 同包改名 | `ThrownTridentMixin` |
| `world.entity.vehicle.AbstractMinecart` | `world.entity.vehicle.minecart.AbstractMinecart` | 移包 | `AbstractMinecartMixin` |
| `world.entity.projectile.windcharge.AbstractWindCharge` | `...projectile.hurtingprojectile.windcharge.*` | 移包 | `ExplosionMixin` |
| `net.minecraft.BlockUtil` | `net.minecraft.util.BlockUtil` | 移包 | `portal/EntityMixin` |
| `world.entity.RelativeMovement` | `world.entity.Relative` | 枚举改名 | `teleport_players/ServerPlayerMixin` |
| `EntityType.is(TagKey)` | （上一轮已修） | —— | —— |
| `Entity.kill()` | `Entity.kill(ServerLevel)` | javap 确认无参版删除 | `AbstractMinecartMixin` |
| `Entity.lerpTo(DDDFFI)V` | `Entity.moveOrInterpolateTo(Vec3,FF)V` / `moveOrInterpolateTo(FF)V` | 插值改 `InterpolationHandler`，**没有 int lerpSteps 参数** | `entities_stick_sublevels/ClientPacketListenerMixin` |
| `Entity.absMoveTo(DDDFF)` | `Entity.absSnapTo(DDDFF)` | 改名 | `entity_rotations_and_riding/ServerPlayerMixin` |
| `ClientboundPlayerPositionPacket(dddff,Set,int)` | `(int, PositionMoveRotation, Set<Relative>)` | record 化 | 同上 |
| `Minecraft.cameraEntity`（字段） | `Minecraft.getCameraEntity()` | 字段转私有 | `camera_zoom/CameraMixin`、`new_camera_types/GameRendererMixin` |
| `Minecraft.setScreen(x)` | `Minecraft.gui.setScreen(x)` | `Minecraft` 无该方法 | `options/OptionsScreenMixin` |
| `Minecraft.getToasts()` | `Minecraft.gui.toastManager()` | `Gui` 持有 `ToastManager` | `toast/IntegratedServerMixin` |
| `LocalPlayer.displayClientMessage(c,true)` | `LocalPlayer.sendOverlayMessage(c)` | javap 确认 | `new_camera_types/MinecraftMixin` |
| `Camera.getEntity()` | `Camera.entity()` | 改名 | `camera_rotation/GuiMixin` |
| `Camera.getPosition()` | `Camera.position()` | 改名 | —— |
| `GameRenderer.mainCamera()` 已有 | —— | —— | —— |
| `BlockState.blocksMotion()` | `BlockState.isSolid()` | `blocksMotion` 整类删除 | `stop_rain/LevelRenderMixin` |
| `BlockState.emissiveRendering(Level,BlockPos)` | `BlockState.emissiveRendering()` | 变无参 | `particle/ParticleMixin` |
| `ItemCooldowns.isOnCooldown(Item)` | `isOnCooldown(ItemStack)` | 形参改 ItemStack | `punching/MinecraftMixin` |
| `PathfinderMob.hasRestriction()/getRestrictCenter()` | `Mob.hasHome()/getHomePosition()` | 概念改名为 home | `entity_pathfinding/RandomPosMixin` |
| `Level.getMaxBuildHeight()` | `LevelHeightAccessor.getMaxY()` | 上一轮已确认 | `sublevels_block_sky/*` |
| `Level` 构造器（带 `Supplier<ProfilerFiller>`） | 去掉 profiler 参数 | javap 确认 | `particle/ClientLevelMixin` |
| `ClientChunkCache.Storage`（包私有） | 不可再命名 | javap 确认 package-private | `plot/ClientChunkCacheMixin`、`loaded_chunk_debug/ClientChunkCacheStorageAccessor` |
| `LevelChunk.replaceWithPacketData(FriendlyByteBuf,CompoundTag,Consumer)` | `replaceWithPacketData(int,int,ClientboundLevelChunkPacketData)` | 完全重写 | `plot/ClientChunkCacheMixin` |
| `ClientboundLevelChunkWithLightPacket.getX()/getZ()` | `.x()/.z()` | record 化 | `plot/lighting/ClientPacketListenerMixin` |
| `BlockStateBase.entityInside(Level,BlockPos,Entity)` | `(Level,BlockPos,Entity,InsideBlockEffectApplier,boolean)` | 新增两参 | `entities_in_blocks/EntityMixin` |
| `PoseStack.mulPose(Quaternionf)` | `mulPose(Matrix4fc)` / Quaternion 包装 | 只剩 Matrix4fc/Transformation | `entity_rendering/LevelRendererMixin`、`entities_stick_sublevels/EntityRenderDispatcherMixin` |
| `Entity.hasImpulse`（字段） | 删除 | javap 确认 | `entity_rotations_and_riding/LivingEntityMixin` |
| `Level.random`（protected） | 走 `getRandom()` | —— | （非 mixin） |
| `Connection.NETWORK_*_WORKER_GROUP`、`ServerConnectionListener.SERVER_*_GROUP` | `EventLoopGroupHolder.remote(bool)/local().eventLoopGroup()` | 静态 EventLoopGroup 全删 | `udp/ConnectionMixin`、`udp/ServerConnectionListenerMixin` |
| `MinecraftServer.isEpollEnabled()` | 删除，直接用 `Epoll.isAvailable()` | javap 确认无该 getter | `udp/ServerConnectionListenerMixin` |
| `ServerPlayer.server`（转私有） | `serverPlayer.level().getServer()` | `Level.getServer()` 仍 public | `udp/PlayerListMixin` |
| `Path`（26.3 变 **final**） | 必须 `(PathExtension)(Object) path` | final 类不能 cast 到无关接口 | `entity_pathfinding/PathNavigationMixin` |
| `Path` 的 `PathExtension` 同理 | —— | —— | —— |

---

## 3. 删除 / 摘条目（**成对执行**）

### 3.1 删掉的 14 个 mixin 类（全部同步摘 json）

| # | 文件 | 原因 |
|---|---|---|
| 1 | `camera/camera_rotation/CompassItemPropertyFunctionMixin` | 目标 `CompassItemPropertyFunction` 整类删除（26.3 物品属性函数改为 `CompassAngle`/`CompassAngleState`） |
| 2 | `entity/entity_rotations_and_riding/EntityRendererMixin` | 目标 `EntityRenderer.renderNameTag` 已删（改 `submitNameDisplay`/`extractNameTags`）；该 mixin 的唯一功能是名字牌朝向 |
| 3 | `loaded_chunk_debug/ClientChunkCacheStorageAccessor` | `ClientChunkCache$Storage` 转**包私有**，连 `@Mixin(X.class)` 都无法命名 |
| 4 | `compatibility/computercraft/WirelessNetworkMixin` | jar 不在 classpath（26.3 无该 mod 构建） |
| 5 | `compatibility/exposure/CameraPosesMixin` | 同上 |
| 6 | `compatibility/exposure/CameraStandEntityMixin` | 同上 |
| 7 | `compatibility/iris/ExtendedShaderMixin` | 同上（上一轮已降级为注释壳，本轮删净） |
| 8 | `compatibility/jade/BlockAccessorImplMixin` | 同上 |
| 9 | `compatibility/jade/RayTracingMixin` | 同上 |
| 10 | `compatibility/jadeaddons/CreatePluginMixin` | 同上 |
| 11 | `compatibility/vista/LODMixin` | 同上 |
| 12 | `compatibility/vista/ViewFinderAccessMixin` | 同上 |
| 13 | `compatibility/vista/ViewFinderControllerMixin` | 同上 |
| 14 | `fabric/mixin/compatibility/sodiumextras/EmbyToolsMixin` | 同上（**本就不在 json 里**，是遗留孤儿文件） |

> 全部移进 `src\_dropped_mixin\`（不 `rm`，可整体回滚），共 15 个文件（含 1 个上一轮遗留的 `.bak-render`）。
> **json 摘掉 13 条**（`sable.mixins.json`：client 4 条 / mixins 9 条）；`sable-fabric.mixins.json` 无需改（EmbyTools 未登记）。

### 3.2 加了 `require = 0` 的 7 处（目标消失 / 极可能消失，只告警不崩）

| 文件 | 注入 | 目标状态 |
|---|---|---|
| `entity/trident/ThrownTridentMixin` | `@Inject(tick → setNoPhysics)` | `Entity.setNoPhysics` 在 26.3 已删 |
| `entity/entities_stick_sublevels/ClientPacketListenerMixin` | `@WrapOperation(handleTeleportEntity)` | 26.3 的调用点是 `moveOrInterpolateTo`；`handleTeleportEntity` 若再变只告警 |
| 同上 | `@WrapOperation(handleMoveEntity)` | 同上（ordinal 0） |
| `entity/entities_stick_sublevels/packet_mixin/ClientboundTeleportEntityPacketMixin` | `@Inject(<init>(FriendlyByteBuf))` | 记录类改 `StreamCodec`，该构造器已无 |
| 同上 | `@Inject(write)` | `write` 方法已无 |
| `entity/entities_in_blocks/EntityMixin` | `@Inject(checkInsideBlocks)` | 26.3 只剩 `checkInsideBlocks(List, StepBasedCollector)`，无参版已删 |
| `entity/sublevels_block_sky/SubLevelsBlockSkyMixin` | `@WrapOperation(Level.canSeeSky)` | `canSeeSky(BlockPos)` 整类删除（`LevelReader` 只剩 `canSeeSkyFromBelowWater`） |

---

## 4. 降级清单（源码内都带 `// PORT(26.3):`，可用 `grep -rn "PORT(26.3)"` 回收）

| # | 文件 | 丢掉了什么 | 替代 |
|---|---|---|---|
| 1 | `mixin/AbstractSableMixinPlugin.java` | `org.apache.maven.artifact.versioning` 整包（26.3 classpath 上不存在，fabric-loader 不再传递 maven-artifact） | `sable$matchesRange(...)` 自带最小 Maven 区间实现（`1.0` / `[a,b)` / `(,b]` / `[a,)`），数字段按 BigInteger 比较。**编译期唯一的 `@MixinModVersionConstraint` 在 `neoforge/`（`(,6.0.11)`），不进本次编译**，行为无差异 |
| 2 | `mixin/plot/ClientChunkCacheMixin.sable$loadedChunks()` | `ClientChunkCache$Storage.chunks` 的枚举能力（Storage 包私有 + 无公开访问路径） | 返回 `List.of()`。**丢失：debug 渲染的「已加载区块」列表**（纯调试） |
| 3 | `mixin/respawn_point/ServerPlayerMixin` | `ServerPlayer.RespawnPosAngle`（转 **package-private**，无法命名）+ `findRespawnAndUseSpawnBlock`（签名改 `(ServerLevel, RespawnConfig, boolean)`） | 删掉 `@Redirect`。**丢失：在「子维度跟踪点」上重生的解析**——重生会退回原版出生点（NBT `RespawnPoint` 仍照常读写） |
| 4 | 同上 | 四个字段 `respawnPosition/respawnDimension/respawnAngle/respawnForced` 全并进 `RespawnConfig` 且转私有；`copyRespawnPosition` 的 `@Overwrite` 不再可行 | `@Overwrite` → `@Inject(TAIL)`，只同步 `sable$respawnPoint`；`setRespawnPosition` 的注入改为 `(RespawnConfig, boolean)` 形参。语义等价（原版自己会 copy 配置） |
| 5 | `mixin/entity/entities_stick_sublevels/packet_mixin/ClientboundTeleportEntityPacketMixin` | 传送包是 record + `StreamCodec`，「actuallyInSubLevel」这个**额外布尔位无法再上线** | 注入加 `require = 0`；`ClientPacketListenerMixin` 里改用 `((Object) packet) instanceof`。**丢失：客户端区分「真在子维度里」与「只是贴着子维度传输」**——该标志恒为 false，实体一律走 `setPos` 校正分支 |
| 6 | `mixin/entity/entities_in_blocks/EntityMixin` | `BlockState.entityInside` 的侧效执行器 | 传 `InsideBlockEffectApplier.NOOP` + `false`。**丢失：子维度内「方块内侧效」（营火/岩浆/蜂蜜等）的施加**（碰撞本身仍在） |
| 7 | `mixin/entity/entities_stick_sublevels/EntityRenderDispatcherMixin` | `EntityRenderDispatcher.renderHitbox`（整方法已删） | 整段移除（类变空 mixin）。**丢失：子维度实体的三条 debug 线框**（碰撞盒 / 上传位置 / 服务器插值目标） |
| 8 | `mixin/particle/TerrainParticleMixin` | `TerrainParticle.getLightColor` 已删，`LevelRenderer.getLightColor` 也搬去 `LightCoordsUtil` | 整类降级为空 mixin。**丢失：子维度地形粒子的光色缩放** |
| 9 | `mixin/particle/ParticleEngineMixin` | `ParticleEngine.crack` 整方法已删 | 移除该 `@Redirect`。**丢失：破坏方块裂纹粒子的子维度速度变换**（该方法本就不会被调用） |
| 10 | `mixin/entity/entity_rotations_and_riding/EntityRendererMixin` | `renderNameTag` 已删 | 删类。**丢失：子维度上名字牌的朝向修正** |
| 11 | `mixin/camera/camera_rotation/CompassItemPropertyFunctionMixin` | `CompassItemPropertyFunction` 整类已删 | 删类。**丢失：子维度内指南针/回溯指针的角度修正** |
| 12 | 10 个 `mixin/compatibility/**` + 1 个 fabric sodiumextras | 外部 mod 的编译依赖（classpath 无 jar，26.3 也无这些 mod 的构建） | 删类 + 摘 json。**丢失：ComputerCraft / Exposure / Iris / Jade / JadeAddons / Vista / SodiumExtras 的兼容钩子**（这些 mod 本身也装不上 26.3） |
| 13 | `mixin/entity/sublevels_block_sky/SubLevelsBlockSkyMixin` | `Level.canSeeSky(BlockPos)` | `require = 0`。**丢失：子维度遮挡天空的判断**（僵尸/幻翼在子维度内仍按主世界天空判定） |
| 14 | `mixin/udp/ConnectionMixin`、`udp/ServerConnectionListenerMixin` | 原版共享的静态 `EventLoopGroup`（全删） | 每次建连向 `EventLoopGroupHolder` 要一个 group。**副作用：UDP 通道各持一个 EventLoopGroup，不与原版共享**（连接数不大时可接受） |
| 15 | `mixin/entity/entity_rotations_and_riding/LivingEntityMixin` | `Entity.hasImpulse` 字段 | 删该赋值。**丢失：子维度骑乘时强制位置同步的那一位**（26.3 由插值系统接管） |

**没有降级的**：§2 的其余全部是等价替换（换包 / 改名 / 换个访问器），行为不变。

---

## 5. JSON 一致性校验（铁律验收）

```
> python validate_mixins_json.py
sable.mixins.json        entries=205
sable-fabric.mixins.json entries=9
TOTAL entries=214  missing=0
ORPHAN java files not in any mixins.json: 1
   dev.ryanhcode.sable.mixin.AbstractSableMixinPlugin
```

- **missing = 0**：214 条登记项**每一条**都能在源码里找到对应 `.java`（按 `package` + 条目名拼路径逐条 `os.path.isfile`）。
- 唯一「孤儿」是 `AbstractSableMixinPlugin` —— 它是 `"plugin"` 字段指向的**配置插件**，本来就不该出现在 mixins 列表里，属预期。
- 删掉的 14 个类与摘掉的 13 条 json **一一对应**（EmbyTools 本就没登记），因此不会出现 `MixinApplyError`。

---

## 6. 复现

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\sable-26\port26
$env:JAVA_HOME="$env:APPDATA\.minecraft\runtime\java-runtime-epsilon"
.\gradlew.bat compileJava --no-daemon          # -> compile-mx4.log

python validate_mixins_json.py                 # json 一致性
```

回滚单个文件：`Copy-Item <file>.bak-mx <file>`（**42 个**）。
整批回滚删除的 mixin：`Move-Item ..\src\_dropped_mixin\*.java ..\src\common\src\main\java\dev\ryanhcode\sable\mixin\...`（目录结构见 §3.1）。

---

## 7. 仍然不在本线范围（其余 4 条错误的归属）

`compile-mx4.log` 剩下的 4 条错误全在**别的域**，本轮未动（其他线同一时刻也在推进，数字会继续变化）：

| 域 | 文件 | 错误 |
|---|---|---|
| api | `EntitySubLevelUtil.java:76` | `Entity.moveTo(double,double,double)` 已删（改 `snapTo`/`absSnapTo`） |
| api | `SubLevelAssemblyHelper.java:407` | 上一轮的 `Clearable.tryClear(BlockEntity)`（26.3 该接口换签名） |
| network | `SableUDPServer.java:115` | UDP 服务端的符号缺失（`connection`/`server` 访问级别族，见下） |
| network | `SableUDPPacket.java:36` | `NoOpFrameEncoder`/`MonitorFrameDecoder` 移包（26.3 `Connection` 内部编解码器重写） |

> 本轮**已由其他线清掉**的同族项（记录以免误判为本线成果）：`SableUDPServer` 的
> `server`/`connection` 访问级别 3 条、`GameProfile`→`NameAndId`、`PhysicsChunkTicketManager`、
> `SubLevelEntityCollision.getNearest`、`Level.random`、`FragileBlockCallback.blocksMotion`、
> `SableCollisionContextImpl` / `SubLevelEntityCollisionContext` 的 collision-context 族、
> fabric 的 `Load.onChunkLoad` / `fabric_*Attachments*Nbt`。
