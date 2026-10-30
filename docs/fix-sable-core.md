# Sable 26.3 核心线（非渲染）修复报告

> 对象：`work\sable-26`（common + fabric）。
> 边界：渲染线独占 `sublevel/render/**`、`render/**`、`mixin/sublevel_render/**`、
> `mixin/dynamic_directional_shading/**`、`debug/**`、`compat/veil/**`；本报告全部落在**核心线**范围。
> 日志：`port26\compile-5.log`（起点 569）→ `port26\compile-11.log`（终点 273）。
> 复现脚本：`port26\fix_a.py` … `fix_h.py`（每处都是显式 `(文件, old, new)` 三元组，dry-run 通过才 `--apply`）。
> 备份：每个被改文件留 `<file>.bak-core`（**63 个**）。

---

## 1. 结论（实测）

| 项 | 数 |
|---|---|
| 起点错误数（compile-5） | **569** |
| 本线终点错误数（compile-11） | **273** |
| 总下降 | **−296** |
| 我的编译轮次 | 6 轮（569→504→414→335→298→284→273） |
| 改的文件 | **63**（`.bak-core` 计数） |
| 明确降级点 | **8 类 / 13 处**（见 §4） |

> ⚠ 中间几轮（335）包含了**渲染线的并行进度**：两条线同一工程同时编译，总数是共同结果。
> 但每个族的清零都由本线单轮驱动，可用族级计数复核（§3）。

---

## 2. 已清零的族（26.3 精确修法）

### 2.1 包移动 / 类删除（机械替换）

| 族 | 起点 | 修法 | 影响文件 |
|---|---|---|---|
| `net.minecraft.Util` | 9 | → **`net.minecraft.util.Util`**（`pauseInIde`/`getMillis`/`backgroundExecutor` 都还在） | 4 |
| `net.minecraft.FileUtil` | 3 | → **`net.minecraft.util.FileUtil`** | 1 |
| `AbstractArrow` | 6 | → **`...entity.projectile.arrow.AbstractArrow`** | 2 |
| `AbstractHurtingProjectile` | 2 | → **`...projectile.hurtingprojectile.AbstractHurtingProjectile`** | 1 |
| `MinMaxBounds` | 5 | → **`net.minecraft.advancements.predicates.MinMaxBounds`**（`Doubles.fromReader` 未变） | 2 |
| `BlockPos.getCenter()` | 15 | → **`Vec3.atCenterOf(blockPos)`** | 14 |
| `Level.getMaxBuildHeight()` | 5 | → **`getMaxY()`** | 5 |
| `Level.getMinBuildHeight()` | 3 | → **`getMinY()`** | 3 |
| `getMinSection()` / `getMaxSection()` | 5 | → **`getMinSectionY()` / `getMaxSectionY()`** | 3 |
| `ResourceKey.location()` | 6 | → **`identifier()`** | 5 |
| `GameProfile.getId()` | 4 | → **`id()`**（authlib 6 是 record） | 4 |
| `PalettedContainer.Strategy` | 4 | → **`net.minecraft.world.level.chunk.Strategy`**：`Strategy.createForBlockStates(IdMap)` / `createForBiomes(IdMap)`；`new PalettedContainer(idMap, def, strategy)` → `new PalettedContainer<>(def, strategy)`；`codecRW(idMap, codec, strategy, def)` → `codecRW(codec, strategy, def)` | 2 |
| `EntityType.is(TagKey)` | 4 | → **`type.builtInRegistryHolder().is(tag)`** | 4 |
| `Direction.getNearest(d,d,d)` | 3 | → **`Direction.getApproximateNearest(d,d,d)`** | 2 |
| `new BlockPos(BlockPos)` | 3 | → 直接用原 `BlockPos`（`floodfill.getFirst()` / `index` 本来就是 `BlockPos`） | 1 |
| `LevelChunk.setBlockState(...,boolean)` | 3 | → 第 3 参是 **int 更新标志**，用 `3`（UPDATE_ALL） | 2 |
| `Player` 构造器 | 4 | `Player(Level, BlockPos, float, GameProfile)` → **`Player(Level, GameProfile)`** | 4 |
| `Level` 构造器 | 4 | 去掉 **DimensionType `Supplier`** / **`profiler`** 参数 | 4 |
| `Level.onBlockStateChange` | 3 | → **`sendBlockUpdated(pos,old,new,3)` + `updatePOIOnBlockStateChange(pos,old,new)`**（降级，见 §4.5） | 1 |

### 2.2 `CompoundTag` 全面 Optional 化（**最大一族，−45 左右**）

26.3 的 `CompoundTag` 所有 getter 改返回 `Optional`，并新增 `*Or` / `*OrEmpty` 变体：

```
getCompound(k)                 -> Optional<CompoundTag>   ; 用 getCompoundOrEmpty(k)
getList(k, type)               -> 只剩 getList(k):Optional ; 用 getListOrEmpty(k)（**类型过滤参数已删除**）
getInt/getString/getBoolean/
getDouble/getLongArray/
getIntArray/getByteArray       -> Optional<...>            ; 用 getXOr(k, default) 或 .orElse(...)
contains(k, type)              -> 只剩 contains(k)
getAllKeys()                   -> keySet()
putUUID(k,v)/getUUID(k)/hasUUID(k) --> 整组删除
```

修法：
- `getCompound` → `getCompoundOrEmpty`（22 处）
- `getList(k, TAG_X)` → `getListOrEmpty(k)`（6 处）
- `contains(k, TAG_X)` → `contains(k)`（3 处）
- `getInt/getString/getBoolean/getDouble` → `getXOr(k, 0 / "" / false / 0.0)`（12 处）
- `getLongArray/getIntArray` → `.orElse(new long[0])` / `.orElse(new int[0])`（3 处）
- `getByteArray` → `.orElseThrow()`（2 处，调用点已在外层 `contains` 判定内）
- `getAllKeys()` → `keySet()`（5 处）
- **UUID**：`putUUID(k,v)` → `tag.store(k, UUIDUtil.CODEC, v)`；`getUUID(k)` → `tag.read(k, UUIDUtil.CODEC).orElse(null)`；
  `hasUUID(k)` → `contains(k)`。`UUIDUtil.CODEC` 就是 int-array 编码，**NBT 格式与旧版一致**，老存档可读。
- `NbtUtils.loadUUID(Tag)` 已删除 → `UUIDUtil.CODEC.parse(NbtOps.INSTANCE, tag).getOrThrow()`

受影响文件 7 个（`ServerLevelPlot` / `SubLevelSerializer` / `SubLevelTicketsSavedData` /
`SubLevelTrackingPointSavedData` / `SableNBTUtils` / `SubLevelOccupancySavedData` / `SubLevelHoldingChunk`）。

### 2.3 聊天组件改为 record 子类型

`HoverEvent` / `ClickEvent` 现在是 **接口**，`action()` 之外没有成员，**不能 `new`**：

```
new HoverEvent(HoverEvent.Action.SHOW_TEXT, c)      -> new HoverEvent.ShowText(c)
new ClickEvent(ClickEvent.Action.COPY_TO_CLIPBOARD, s) -> new ClickEvent.CopyToClipboard(s)
new ClickEvent(ClickEvent.Action.SUGGEST_COMMAND, s)   -> new ClickEvent.SuggestCommand(s)
```
10 处 / 2 文件。

### 2.4 `DataCommands.DataProvider` → `ArgProvider<T>`

- `DataCommands.DataProvider` 整类换成泛型 **`net.minecraft.server.commands.ArgProvider<T>`**
  （成员不变：`access(CommandContext)` / `wrap(ArgumentBuilder, Function)`）。
- 原来的 `Function<String, DataProvider>` 换成单抽象方法接口 **`ArgProvider.Factory<T>`**（方法名 `create(String)`）。
- 桌面清单变成 `DataCommands.ALL_PROVIDERS: List<ArgProvider.Factory<DataAccessor>>`。
7 处 / 2 文件（`SubLevelDataAccessor` / `DataCommandsMixin`）。

### 2.5 区块票据系统重写（`Ticket` / `TicketType`）

26.3：
- `Ticket` **不再泛型、不再携带 value**：`new Ticket(TicketType, int level)`；
- `TicketType` 变成 **record `(long timeout, int flags)`**，`TicketType.create(name, comparator)` 删除；
- `DistanceManager` 的 `addTicket/removeTicket/tickingTicketsTracker` **全部消失**，
  票据改由 `TicketStorage` 持有，对外唯一入口是 `ServerChunkCache.addTicket(Ticket, ChunkPos)` /
  `addTicketWithRadius(TicketType, ChunkPos, int)` / `removeTicketWithRadius(...)`；
- `ChunkProgressListener` **整类删除**（`server.level.progress` 包改成 `LevelLoadListener` 家族），
  `ChunkMap` / `ServerChunkCache` 的构造器签名随之改变（`TicketStorage` 顶替原 `ChunkProgressListener`）。
7 处 / 3 文件，含 3 处降级（§4.1–4.3）。

### 2.6 其它

- `getProfiler()`：`Level#getProfiler()` / `Minecraft#getProfiler()` 全部删除 →
  **`Profiler.get()`**（`net.minecraft.util.profiling.Profiler`，ThreadLocal 活动 filler）。
- `registryAccess().registryOrThrow(...)` → **`lookupOrThrow(...)`**（4 处）。
- `Registry.getHolderOrThrow(ResourceKey)` → **`wrapAsHolder(getValueOrThrow(key))`**（3 处）。

---

## 3. 逐轮记录（可用于归因）

| 轮 | 脚本 | 内容 | 编译后 |
|---|---|---|---|
| 起点 | — | — | 569 |
| A | `fix_a.py` | Util/FileUtil 包、AbstractArrow、getCenter、getMaxBuildHeight/getMinSection、getAllKeys、location→identifier | **504** |
| B | `fix_b.py` | CompoundTag Optional 全家（53 处 / 7 文件） | — |
| C | `fix_c.py` | UUID codec、Profiler.get、MinMaxBounds 包、lookupOrThrow | **414** |
| D | `fix_d.py` | HoverEvent/ClickEvent record、PalettedContainer.Strategy、GameProfile.id、FileUtil、AbstractHurtingProjectile | — |
| E | `fix_e.py` | Ticket/TicketType/TicketStorage + ChunkProgressListener 的 `<init>` 签名 | **335** |
| F | `fix_f.py` | ArgProvider、ChunkProgressListener 清理、EntityType.is(TagKey) | **298** |
| G | `fix_g.py` | BlockPos.of、getApproximateNearest、setBlockState flags、onBlockStateChange、SableAttributes 降级 | **284** |
| H | `fix_h.py` | Player/Level 构造器签名 | **273** |

---

## 4. 降级清单（逐条，源码内都带 `// PORT(26.3):`）

| # | 文件 | 丢掉了什么 | 替代 |
|---|---|---|---|
| 4.1 | `sublevel/system/ticket/PhysicsChunkTicketManager.java:42` | 自定义 **具名** `TicketType`（`TicketType.create("sable_sub_level_loaded", UUID::compareTo)`）随工厂一起消失 | `new TicketType(TicketType.NO_TIMEOUT, FLAG_PERSIST \| FLAG_LOADING)`。**丢掉名字**（调试字符串里看不到 "sable_sub_level_loaded"），保留「不过期 + 持久 + 会加载区块」的语义 |
| 4.2 | 同上 `:237` | `DistanceManager.addTicket(long, Ticket)` 已移到 `TicketStorage`，`DistanceManager` 不再对外暴露 | `level.getChunkSource().addTicket(ticket, ChunkPos.unpack(chunkLong))`。语义等价 |
| 4.3 | 同上 `:300` | `tickingTicketsTracker.removeTicket(...)` 与**按 Ticket 实例**移除的能力都没了 | `level.getChunkSource().removeTicketWithRadius(SUB_LEVEL_LOADED_TICKET_TYPE, pos, 0)`。**区别：会移除该区块上所有 Sable 子维度票据**，不只是当前这一张。同一区块有多个子维度时会提前掉票 |
| 4.4 | `mixin/plot/ServerChunkCacheMixin.java:167` | 注入目标 `ServerChunkCache.addRegionTicket(TicketType,ChunkPos,int,T)` 整方法删除 | 改注入后继方法 `addTicketWithRadius(TicketType,ChunkPos,int)`，并加 **`require = 0`**（目标再变只告警不崩）。**丢掉**：只按 type 判断，无法再区分 value |
| 4.5 | `api/SubLevelAssemblyHelper.java`（3 处）、`util/LevelAccelerator.java`（1 处） | `Level.onBlockStateChange(BlockPos,BlockState,BlockState)` 删除 | `sendBlockUpdated(pos,old,new,3)` + `updatePOIOnBlockStateChange(pos,old,new)`。**丢掉旧 hook 里附带的 light-engine / 高度图侧效** |
| 4.6 | `index/SableAttributes.java` | `AttributeSupplier` 变成**不可变**（`private final instances`，无 accessor），无法再把 `PUNCH_STRENGTH` / `PUNCH_COOLDOWN` 注入 **PLAYER 默认属性表** | `register()` **置空**；`getPushCooldownTicks()` 在属性缺失时**回退固定 10 tick**。**丢掉**：玩家默认不再自带这两个属性，拳击力度/冷却走默认值 |
| 4.7 | `api/SubLevelAssemblyHelper.java`、`util/LevelAccelerator.java` | `LevelChunk.setBlockState(..., boolean moved)` 的布尔语义 | 第 3 参改 int 标志位，统一传 `3`（UPDATE_ALL）。**丢掉**「静默放置」与「正常放置」的区分 |
| 4.8 | `sublevel/storage/**`（3 文件） | `getUUID` 缺失时抛错的行为 | `read(...).orElse(null)`：坏存档下静默得到 `null`，由调用方判空（原逻辑本来就判空） |

**没有降级的**：§2 的其余全部是等价替换，行为不变。

---

## 5. 因边界让给渲染线而未处理

渲染线明确独占后，以下**已经改过但不再跟进**（渲染线已整体重写覆盖，我不回滚、不再碰）：

| 文件 | 我改过什么 | 处置 |
|---|---|---|
| `sublevel/render/dispatcher/ReachAroundSubLevelRenderDispatcher.java` | `import net.minecraft.Util` 换包 + `getProfiler()`→`Profiler.get()` | 归渲染线 |
| `sublevel/render/vanilla/VanillaChunkedSubLevelRenderData.java` | `getProfiler()`→`Profiler.get()` | 归渲染线 |
| `mixin/sublevel_render/impl/vanilla/LevelRendererMixin.java` | `getProfiler()`→`Profiler.get()` | 归渲染线 |
| `api/block/propeller/BlockEntityPropeller.java` | `getCenter()`→`Vec3.atCenterOf` | **核心线内容，但文件有 `.bak-render`**：若渲染线重写该文件，这 2 处需要重放 |
| `sublevel/plot/ServerLevelPlot.java` | CompoundTag Optional 全家 + Strategy + `entityManager` 相关 | **核心线主战场**，同有 `.bak-render`。已在 compile-11 通过，暂未冲突 |
| `sublevel/storage/holding/SubLevelHoldingChunkMap.java` | `dimension().location()`→`identifier()` | 同上 |
| `sublevel/storage/serialization/SubLevelStorage.java` | `FileUtil` 换包 | 同上 |
| `sublevel/system/SubLevelTrackingSystem.java` | `GameProfile.getId()`→`id()` | 同上 |
| `sublevel/system/ticket/PhysicsChunkTicketManager.java` | 票据系统全家 | 同上 |
| `util/LevelAccelerator.java` | `getMinY/getMaxY/getMinSectionY` + setBlockState flags | 同上 |

> 合计 **10 个文件同时有 `.bak-core` 和 `.bak-render`**。核心线内容如需保留，请渲染线在重写时不要回退这几处。

---

## 6. 未处理（留给后续 / 渲染线）

核心线范围内**还留着**的族（我判断代价 > 收益或需要新 mixin 访问器）：

- `ClipContext` 的 `block`/`fluid`/`collisionContext` 字段**转私有**且无 getter（9 条）——
  需要新增一个 `@Accessor` mixin 并登记 `mixins.json`，本轮没做。当前 `BlockGetterMixin` 靠重建
  `ClipContext` 做子维度射线投影，**这段现在是编译错误状态**。
- `ServerLevel.entityManager` 转私有（3 条）——无公开等代 API，需 accessor mixin。
- `ReloadListener` 由 Gson 改 Codec（3 条）——要重写两个配置 loader。
- `CustomPacketPayload`→`Packet<?>`（3 条）——需改走 `ServerPlayNetworking.send`。
- `ShoulderRidingEntity` 整类删除（3 条，parrot）——`Parrot` 已移包，mixin 结构要重做。
- `ServerPlayer.RespawnPosAngle` 转私有（3 条）。
- `Entity.lerpTo(double,double,double,float,float,int)` 删除（3 条）。
- `org.apache.maven.artifact.versioning` 整包缺失（4 条，版本比较）。
- 16 条「method does not override」散点，需要逐个对 26.3 父类签名。

---

## 7. 复现

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\sable-26\port26
$env:JAVA_HOME="$env:APPDATA\.minecraft\runtime\java-runtime-epsilon"
.\gradlew.bat compileJava --no-daemon
```

回滚单个文件：`Copy-Item <file>.bak-core <file>`。
