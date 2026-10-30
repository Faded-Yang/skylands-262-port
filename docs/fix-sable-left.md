# Sable 26.3 移植 —— 左线（非 mixin / 非渲染）残余清零报告

> 范围：**只动 `src/common/src/main/java` 与 `src/fabric/src/main/java`**。
> 未碰 `neoforge/`、`_dropped*/`、`sublevel/render/**`、`render/**`、`mixin/**`（`mixinhelpers/` 是普通 helper 包，不是 mixin 类）。
> 编译：`port26\gradlew.bat compileJava --no-daemon`，日志 `compile-l3.log`。

---

## 1. 数字（实测）

| 口径 | 起点 `compile-r4.log` | 我的 l1 | 我的 l2 | 终点 `compile-l3.log` |
|---|---|---|---|---|
| javac 尾行错误 | **273** | 206 | 4 | **0（BUILD SUCCESSFUL）** |
| 去重 unique（脚本 `an_left.cjs`） | 267 | 199 | 4 | 0 |
| 其中**非 mixin 域**（我的域） | **125** | ~57 | 4 | **0** |

> ⚠ `compile-r4 → l2` 的下降**不全是我做的**：另一条线（mixins）在同期并行改 `mixin/**`。
> 归因：l1 时 mixin 文件仍在报错（`ParticleEngineMixin` 15 条等），说明 273→206 里 29 条是我的两个主战场
> （`ServerLevelPlot` 22 + `PlotChunkHolder` 7）；206→4 中约 **165 条由 mixin 线并行清掉**，我只贡献 ~35 条。
> **族级复核**：`compile-r4.log` 里所有「路径不含 `\mixin\`」的 125 条 unique 错误，在本轮结束时**全部为 0**。

---

## 2. 我改的文件（39 个）

| 类别 | 文件 |
|---|---|
| 有修改前备份 `.bak-left`（17） | `ServerLevelPlot`、`PlotChunkHolder`、`EmbeddedPlotLevelAccessor`、`util/SublevelRenderOffsetHelper`、`SubLevelOccupancySavedData`、`SubLevelTicketsSavedData`、`SubLevelTrackingPointSavedData`、`SubLevelHoldingChunkMap`、`PhysicsBlockPropertiesDefinitionLoader`、`DimensionPhysicsData`、`FloatingBlockMaterialDataHandler`、`DimensionPhysics`、`fabric/client/SableFabricClient`、`fabric/ResourceReloadDelegate`、`fabric/SableFabric`、`ServerSubLevel`、`SubLevelTrackingSystem` |
| 就地修改（22，无 pre-edit 备份） | `MovingSoundInstanceDelegate`、`command/SableCommand`、`api/entity/EntitySubLevelUtil`、`util/LevelAccelerator`、`sublevel/plot/SubLevelPlayerChunkSender`、`sublevel/storage/serialization/SubLevelSerializer`、`network/client/ClientSubLevelPunchHelper`、`network/packets/tcp/ServerboundGizmoMoveSubLevelPacket`、`network/packets/tcp/ServerboundPunchSubLevelPacket`、`command/SableStorageCommands`、`network/udp/SableUDPPacket`、`network/udp/SableUDPServer`、`api/SubLevelAssemblyHelper`、`mixinhelpers/.../TheFasterEntityCollisionContext`、`physics/impl/SubLevelEntityCollisionContext`、`physics/impl/SableCollisionContextImpl`、`sublevel/entity_collision/SubLevelEntityCollision`、`command/argument/selector/SubLevelTargetSelector`、`physics/callback/FragileBlockCallback`、`sublevel/system/ticket/PhysicsChunkTicketManager`、`fabric/platform/SableChunkEventPlatformImpl`、`fabric/platform/SablePlotPlatformImpl` |

> 就地修改的 22 个：每处都带 `// PORT(26.3): ...` 注释，且 §3 的表里给了「旧 → 新」精确表达式，
> 可用 `grep -rn "PORT(26.3)"` 定位后逐条反向替换。**这是本轮流程上的欠账**（应改前备份）。

---

## 3. 已清零的族（26.3 精确修法）

### 3.1 `ServerLevelPlot`（22 → 0）

| 断点 | 修法 |
|---|---|
| `ChunkSerializer` 整类删除 | → **`SerializableChunkData`**（同包）；`ChunkSerializer.ChunkReadException` → `SerializableChunkData.ChunkReadException` |
| `LevelLightEngine.blockEngine/skyEngine` 转私有、无 accessor | `new LevelLightEngine(chunkSource, **true**, level.dimensionType().hasSkyLight())`；sky/block 判定同法（Level 恒有 block engine，sky 只在有天空光的维度存在） |
| `ChunkMap.updatingChunkMap` / `modified` 私有 | 两处（remove + put）降级为注释（§4.1） |
| `ChunkMap.onFullChunkStatusChange` 变包私有 | 降级注释（§4.2） |
| `ServerLevel.entityManager` 私有、无 accessor | `updateChunkStatus` 两处降级注释（§4.2） |
| `PersistentEntitySectionManager.sectionStorage` 私有 | `kickAllEntities` 改 `level.getEntitiesOfClass(Entity.class, chunkAABB)`（§4.3） |
| `Entity.levelCallback` 私有 | 改用公开 `entity.setLevelCallback(EntityInLevelCallback.NULL)`（§4.3） |
| `new LevelChunkSection(Registry<Biome>)` 删除 | → `new LevelChunkSection(level.palettedContainerFactory())`（`PalettedContainerFactory` 是 26.3 新区块容器工厂） |
| `ChunkAccess.TicksToSave` → `ChunkAccess.PackedTicks`；`getTicksForSerialization()` 新增 `long gameTime` 参数 | 用 `SavedTick.codec(BuiltInRegistries.BLOCK.byNameCodec()).listOf()` 编解码（与 vanilla 区块序列化同格式） |
| `LevelChunkTicks.load(ListTag, Function, ChunkPos)` 删除 | → `new LevelChunkTicks<>(codec.parse(...).result().orElse(List.of()))` |
| `BlockEntity.getPosFromTag(CompoundTag)` 签名变更 | → `BlockEntity.getPosFromTag(global, blockEntityTag)` |

### 3.2 `PlotChunkHolder`（7 → 0）

| 断点 | 修法 |
|---|---|
| `ChunkLevel.ENTITY_TICKING_LEVEL` 私有 | → `ChunkLevel.byStatus(FullChunkStatus.ENTITY_TICKING)` |
| `ChunkHolder.ticking/entityTicking/fullChunkFuture` 私有 | 不写字段，**改为重写三个公开 getter**，返回 `CompletableFuture.completedFuture(ChunkResult.of(chunk))`（语义不变，无反射） |
| `ChunkHolder.blockChanged` 返回 boolean | `protected/void` → `public boolean` |
| `rescheduleChunkTask(ChunkMap, ChunkStatus)` 删除 | 删掉该 override（原本就是空实现） |

### 3.3 `SableFabricClient` / `SableFabric` / `ResourceReloadDelegate`（12 → 0）

- `PreparableReloadListener#reload` 改为 **`reload(SharedState, Executor, PreparationBarrier, Executor)`**，且
  `SimplePreparableReloadListener#reload` 变成 `final` ⇒ 委托类改为转发新签名。
- `fuzs.forgeconfigapiport.fabric.api.neoforge.v4.*` 在 26.3 **不存在** ⇒ 三条 `NeoForgeConfigRegistry.INSTANCE.register(...)` 与两条 `NeoForgeModConfigEvents.{loading,reloading}` 全部降级注释（§4.4）。
- `player.connection.send(CustomPacketPayload)` 类型错误 ⇒ 包一层 **`new ClientboundCustomPayloadPacket(payload)`**（`send` 收 `Packet<?>`）。共 3 处（`SableFabric` / `ServerSubLevel` / `SubLevelTrackingSystem`）。

### 3.4 SavedData 三件套（`Factory` 整类删除）

26.3：`SavedData` 变 Codec 驱动，`SavedData.Factory` 删除，入口改为 `getDataStorage().computeIfAbsent(SavedDataType<T>)`，
`SavedDataType` = record `(Identifier id, Supplier<T> ctor, Codec<T> codec, DataFixTypes)`。修法：

```java
private static final Map<ServerLevel, SavedDataType<X>> TYPES = new WeakHashMap<>();
private static SavedDataType<X> typeFor(ServerLevel level) { ... new SavedDataType<>(
        Sable.sablePath(FILE_ID), () -> new X(level),
        CompoundTag.CODEC.xmap(tag -> X.load(level, tag), X::saveNow), DataFixTypes.LEVEL) ... }
public static X getOrLoad(ServerLevel level) { return level.getDataStorage().computeIfAbsent(typeFor(level)); }
```

`save(CompoundTag, Provider)` → `private CompoundTag saveNow()`（自建 tag）。**NBT payload 一个字节没变**（仍是原来的手写字段），
但 **外层文件名改由 identifier 派生**（`sable:sable_sub_level_occupancy` 之类）—— 老存档里同名的 `.dat` 不会再被自动读到（§5.1）。

### 3.5 三个 `SimpleJsonResourceReloadListener`（`PhysicsBlockPropertiesDefinitionLoader` / `DimensionPhysicsData.ReloadListener` / `FloatingBlockMaterialDataHandler.ReloadListener`）

26.3 基类变 `SimpleJsonResourceReloadListener<T>`，构造器 `(Codec<T>, FileToIdConverter)`，`apply(Map<Identifier, T>, ResourceManager, ProfilerFiller)`。
⇒ 泛型化 + `super(X.CODEC, FileToIdConverter.json(NAME))`，`apply` 里**删掉手写 `JsonOps` 解析**（基类已做，错误日志由基类打印），只保留业务装载与排序。

### 3.6 杂项（逐条）

| 旧 | 26.3 |
|---|---|
| `Camera.getPosition()` | `position()`（`util/SublevelRenderOffsetHelper`） |
| `PoseStack.mulPose(Quaternionf)` | `mulPose(new Matrix4f().rotation(q))` |
| `SoundInstance.getLocation()/resolve(SM)` | `getIdentifier()/getOrResolve(SM)`，并补 `getSoundEvent()`（`MovingSoundInstanceDelegate`） |
| `LevelReader.environmentAttributes()` 新增抽象 | `EmbeddedPlotLevelAccessor` 委托 `level.environmentAttributes()`（返回 `EnvironmentAttributeReader`） |
| `BlockAndTintGetter.getShade` 删除 | 删 `getShade` override |
| `Level.getCurrentDifficultyAt` | 下沉到 **`ServerLevel`** ⇒ `getLevel().getCurrentDifficultyAt(pos)` |
| `LevelAccessor.playSound/levelEvent(Player, …)` | 形参改 **`Entity`** |
| `Direction.fromDelta(int,int,int)` | `Direction.getApproximateNearest(x,y,z)`（单位轴向量等价） |
| `Direction.getNearest(int,int,int)` | `getApproximateNearest(...)` |
| `Level.random`（protected） | `getRandom()` |
| `Level.blockUpdated(pos, block)` | `updateNeighborsAt(pos, block, null)` |
| `Entity.moveTo(x,y,z)` | **`snapTo(x,y,z)`**（26.3 改名） |
| `Item.canAttackBlock(state, level, pos, player)` | `Item.canDestroyBlock(stack, state, level, pos, livingEntity)` |
| `ItemCooldowns.isOnCooldown(Item)` / `addCooldown(Item,int)` | 改收 **`ItemStack`** |
| `Player.hasPermissions(int)` | `permissions().hasPermission(Permissions.COMMANDS_*)`（1→MODERATOR，2→GAMEMASTER） |
| `CommandSourceStack.hasPermission(int)` | `permissions().hasPermission(Permissions.COMMANDS_GAMEMASTER)` |
| `GameProfile.getName()` | `name()`（authlib record） |
| `new ClickEvent(Action,…)` / `new HoverEvent(Action,…)` | `new ClickEvent.CopyToClipboard(s)` / `new HoverEvent.ShowText(c)` |
| `CompoundTag.getString(k)` 用于三元表达式 | `getStringOr(k, default)`（`SableStorageCommands` ×2） |
| `NbtUtils.createUUID(uuid)` | `UUIDUtil.CODEC.encodeStart(NbtOps.INSTANCE, uuid).getOrThrow()`（`SubLevelSerializer`，并补 `NbtOps` import） |
| `EntityCollisionContext(boolean,double,ItemStack,Predicate,Entity)` | `(boolean isDescending, boolean alwaysCollideWithFluid, double, ItemStack, boolean isPlacement, Entity)`；`EntityCollisionContext(Entity)` → `(Entity, isDescending, false)` |
| `CollisionContext.getCollisionShape/alwaysCollideWithFluid` 新增抽象 | `SableCollisionContextImpl` 补实现（空形状 / false） |
| `BlockState.blocksMotion()` | `isSolid()`（`FragileBlockCallback`） |
| `Registry.getTag(TagKey)` | `getTagOrEmpty(TagKey)`（返回 Iterable，非 Optional） |
| `DefaultedRegistry.get(Identifier)` | `getValue(Identifier)`（`PhysicsBlockPropertiesDefinitionLoader`） |
| `DimensionType.natural()` | `hasSkyLight()`（近似，§4.5） |
| `ExtraCodecs.VECTOR3F`/`ByteBufCodecs.VECTOR3F` 变 `Vector3fc` | 记录仍存 `Vector3f`，在 codec/streamcodec 处 `.map(Vector3f::new)` / `.map(v -> (Vector3fc) v)`；`RecordCodecBuilder` 的 `DimensionPhysics::new` 改显式 lambda |
| `DebugPackets.sendPoiPacketsForChunk` | 整类删除 ⇒ 空实现（§4.6） |
| `Clearable.tryClear(BlockEntity)`（整类搬包 + 方法删） | `if (be instanceof net.minecraft.world.Clearable c) c.clearContent()` |
| `HangingEntity.calculateSupportBox()` 变 protected | 一律随动（§4.7） |
| `BlockEntity.loadWithComponents(CompoundTag, Provider)` | `loadWithComponents(TagValueInput.create(ProblemReporter.DISCARDING, registries, tag))` |
| `NoOpFrameEncoder` / `NoOpFrameDecoder` / `MonitorFrameDecoder` 删除 | Netty 直通 `ChannelOutboundHandlerAdapter`/`ChannelInboundHandlerAdapter`；monitor 分支用 `Varint21FrameDecoder(monitor)` |
| Fabric `ServerChunkEvents.Load#onChunkLoad` 新增 boolean | 传 `false`（plot chunk 不是新生成） |
| Fabric `AttachmentTargetImpl#fabric_read/writeAttachmentsFromNbt` 改 `ValueInput/ValueOutput` | `TagValueInput.create(...)` / `TagValueOutput.createWithContext(...)` 再 `buildResult()` 合并回 tag |
| `ServerPlayer.server` 私有 / `isSingleplayerOwner(NameAndId)` | `this.server` + `new NameAndId(player.getGameProfile())` |
| `ServerCommonPacketListenerImpl.connection` 变 protected | UDP 认证表改以 **`SocketAddress`**（`player.connection.getRemoteAddress()`）为键，`isConnected` 改查在线玩家列表（§4.8） |

---

## 4. 降级清单（逐条，源码内都带 `// PORT(26.3):`）

| # | 文件:位置 | 26.3 断点 | 丢掉了什么 | 替代 |
|---|---|---|---|---|
| 4.1 | `ServerLevelPlot:167/252` | `ChunkMap.updatingChunkMap`、`modified` 私有 | **plot chunk 不再注入/摘出父 `ChunkMap`**。父 chunk map 不再感知 plot chunk（影响：父级 chunk 级联保存/实体跟踪的「登记」，不再有） | 注释掉；区块数据仍由 `SubLevelPlayerChunkSender` 显式发送 |
| 4.2 | `ServerLevelPlot:189/271` | `ServerLevel.entityManager` 私有 + `ChunkMap.onFullChunkStatusChange` 包私有 | plot chunk 的 **full-chunk-status 不再推给父实体管理器**（`INACCESSIBLE` / `ENTITY_TICKING` 两次都不推） | 注释掉 |
| 4.3 | `ServerLevelPlot:290`（`kickAllEntities`） | `PersistentEntitySectionManager.sectionStorage` 私有；`Entity.levelCallback` 私有 | 不再按 **section** 精确遍历（改按 chunk AABB 查询，边界上的实体会被多算一次/漏算极少数）；不再调用 `section.remove(entity)`；脱离旧 chunk 改用 `setLevelCallback(NULL)`（旧 section 会短暂持有陈旧引用） | `level.getEntitiesOfClass(Entity.class, chunkAABB)` + `setLevelCallback(EntityInLevelCallback.NULL)` |
| 4.4 | `SableFabric`（2 处）/ `SableFabricClient`（3 处） | `fuzs.forgeconfigapiport` 无 26.3 构建 | **Fabric 侧不再注册任何 NeoForge `ModConfigSpec`**，也没有 `loading/reloading` 回调 ⇒ `SableConfig` / `SableServerConfig` / `SableClientConfig` 全部只能取**代码默认值**，用户改配置文件不生效（服务端/客户端都是） | 全部注释掉，保留 SPEC 对象 |
| 4.5 | `DimensionPhysics:104` | `DimensionType#natural()` 删除（维度属性系统重写） | `magnetic_north` 的默认值不再按「自然维度」判定 | 用 `hasSkyLight()` 近似 |
| 4.6 | `SubLevelPlayerChunkSender:24` | `DebugPackets` 整类删除 | plot chunk 载入时**不再推送 POI 调试广播**（原本就是调试用途） | 方法体空实现 |
| 4.7 | `SubLevelAssemblyHelper:313` | `HangingEntity#calculateSupportBox()` 变 protected | 悬挂实体（画/物品框）**不再精确判「是否挂在被移动的方块上」**，凡在装配区域内的悬挂实体一律随动 | `moveEntity = true` |
| 4.8 | `SableUDPServer`（5 处） | `ServerCommonPacketListenerImpl#connection` 变 protected（无 getter） | 认证表键由 `Connection` 改为 **`SocketAddress`**；存活判定由 `Connection#isConnected()` 改为「玩家列表里还有没有这个远端地址」⇒ **同一 IP 多开时可能误判存活**（WeakHashMap 键的弱引用语义也随地址对象变化） | 见 §3.6 末两行 |
| 4.9 | `ServerLevelPlot` tick 存档 | `LevelChunkTicks.load` 删除 | 方块 tick 的 NBT 形状改由 `SavedTick.codec` 决定。若与旧手写 `ListTag` 结构不同，**老存档 plot 内的待定 tick 会静默丢弃**（`result().orElse(List.of())`）；新存档自洽 | `SavedTick` codec + `new LevelChunkTicks<>` |
| 4.10 | 三个 `*SavedData` | `SavedData.Factory` 删除、改为 identifier 化 | **数据文件名由 identifier 派生**，老存档 `world/data/<FILE_ID>.dat` 可能不再被自动读取（内容格式本身未变） | `SavedType(CompoundTag.CODEC.xmap(...))`；如需兼容，把旧 `.dat` 按新名改一份即可 |

**没有降级的**：§3 其余全部为等价替换（含 `LevelLightEngine` 引擎判定、`LevelChunkSection` 工厂、`snapTo`、权限集、声音接口、`ValueInput/ValueOutput`、`getStringOr`、`NameAndId` 等）。

---

## 5. 运行期风险（编译 0 错 ≠ 能跑）

1. **4.4 的配置降级**意味着 Fabric 上所有 Sable 配置项走默认值 —— 启动验证时不要因为「配置不生效」误判为移植 bug。
2. **4.10 的 SavedData 文件名变化**：进老存档时先备份 `world/data/sable_*`，观察是否重新生成了新的 `.dat`（= 数据被当成初次加载）。
3. `EntityCollisionContext` 六参构造器的**布尔位序**是按 26.3 签名推断的（`isDescending, alwaysCollideWithFluid, y, stack, isPlacement, entity`）。两个子类都重写了 `isDescending/isAbove`，影响面小，但首次进世界应验证实体碰撞。
4. `SableCollisionContextImpl.getCollisionShape` 返回空形状 —— 若物理管线依赖它取客户端预测碰撞，会出现「穿模」；原实现根本没有这个方法，26.3 才变抽象。
5. `4.1/4.2` 的 chunk map 解链会让 **plot chunk 的卸载完全依赖 Sable 自己的 `queuedUnloads`**；若出现「子维度区块残留/内存涨」，先查这里。
6. 用 `grep -rn "PORT(26.3)" src/common src/fabric` 可回收全部降级点。

---

## 6. 复现 & 脚本

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\sable-26\port26
$env:JAVA_HOME="$env:APPDATA\.minecraft\runtime\java-runtime-epsilon"
.\gradlew.bat compileJava --no-daemon
```

- `an_left.cjs` —— 日志去重 + 按文件/符号/明细归类（**注意**：javac 输出两遍，第二遍带 2 空格缩进，
  脚本已 `trimStart` 后再匹配，否则去重失效、数字会翻倍）。
- `jp.py <类名> [正则...]` —— javap 26.3.jar 并缓存到 `jpcache/`，`$` 内部类用 PowerShell 单引号传。
- 回滚单个文件：`Copy-Item <file>.bak-left <file>`（仅 §2 前 17 个文件有此备份）。
