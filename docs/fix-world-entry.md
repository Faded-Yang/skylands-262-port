# 进世界打通报告（R359）

> 任务：`Create Aeronautics + Simulated + Sable` 在 **MC 26.3 + Fabric** 上点「开始游戏」→ 真正进入世界。
> 结论写在最前面，证据在最后。

---

## 0. 结论：世界能进，客户端第一帧后崩

**世界加载链已全部打通**，日志实锤（`work\run26\probe42\logs\latest.log`，最后一轮 22:02）：

```
[22:02:14] [Worker-Main-22/INFO]: Loaded 1866 advancements
[22:02:18] [Server thread/INFO]: Starting integrated minecraft server version 26.3
[22:02:20] [Server thread/INFO]: Time elapsed: 1750 ms          ← 出生区生成完成
[22:02:21] [Server thread/INFO]: Tester[local:E:8ce97e38] logged in with entity id 97 at (-5.5, 69.0, 7.5)
[22:02:21] [Server thread/INFO]: System chat: Tester加入了游戏
```

同一份日志里：

- `Couldn't load tag ... missing following references`：**0 条**（修复前 20 条、127 个唯一方块 ID）
- `Registry loading errors`：**0 条**
- `was empty after loading`：**2 条**（`simulated:navigation_target` 的注册类 `SimNavigationTargets.java` 在 build.gradle 里被 exclude；`aeronautics:lifting_gas_type` 的条目类在跑但注册表为空，见 §7）

**但**客户端在进入世界约 1 秒后崩在渲染/输入链：

```
java.lang.IndexOutOfBoundsException
  at java.nio.DirectByteBuffer.get
  at com.mojang.blaze3d.platform.InputConstants.isKeyDown(InputConstants.java:626)
  at net.minecraft.client.KeyMapping.setAll
  at net.minecraft.client.MouseHandler.grabMouse
  at net.minecraft.client.gui.Gui.setScreen
  at net.minecraft.client.gui.screens.LevelLoadingScreen.onClose   ← 加载界面关闭、真正接管世界的那一刻
```

- 这是 **26.3 原生 `InputConstants`** 的 SDL 键盘状态缓冲（`DirectByteBuffer`）越界，不是我们的 mod 代码。
- 触发点正好是「加载界面关闭 → 抓鼠标」；此时若窗口被别的全屏程序抢走焦点/最小化，SDL 键盘状态缓冲会是空/过短 → 越界。
- 本机当时**用户正在另一个全屏程序里**（抓屏抓到的是用户自己的微信/游戏窗口），所以这一条**没有排除环境因素**，也没有拿到游戏内截图。

### 能不能进世界？

**能。** 判据三条：

| 判据 | 结果 |
|---|---|
| ① 日志出现出生区完成 / 时间统计 | ✅ `Time elapsed: 1750 ms`、`Loaded 1866 advancements` |
| ② 没有 `ReportedException` / `NoClassDefFoundError`（世界加载阶段） | ✅ 世界加载/服务器启动阶段零异常；只在进入后 render/input 崩 |
| ③ 截图非全黑且是游戏内视角 | ❌ **未取得**（用户占用桌面；见 §6） |

---

## 1. 127 个注册项缺失：根因（带证据）

### 1.1 结论一句话

**`com.tterrag.registrate` 在本项目里是自写的「空桩」：`BlockBuilder.register()` 只 `new BlockEntry(id, null)`，从不调用 `Registry.register`；`SimBlocks.register()` / `AeroBlocks.init()` 体内是空的。**
所以 Simulated/Aeronautics 的**全部**方块、物品、方块实体从未进游戏注册表 —— 127 只是「数据包 tag 恰好引用到的那个子集」。

### 1.2 证据

1. **jar 里 `BlockBuilder.register()` 的字节码**（`javap -c`）：
   ```
   new BlockEntry
   dup
   aload_0; getfield owner; aload_0; getfield name
   invokevirtual AbstractRegistrate.makeId
   aconst_null                    ← 值就是 null
   invokespecial BlockEntry.<init>(Identifier, Block)
   areturn
   ```
   全类没有任何 `net/minecraft/core/Registry.register` 引用。

2. **`SimBlocks.register()` / `AeroBlocks.init()` 在 jar 里都是 `return`**（本报告已把它们改成 `flush()`）。

3. **只有 aeronautics 的 jar 带 `com.tterrag.registrate`**（46 个类），create-fly / sable 的 jar 里一个都没有 ⇒ 运行期没有「真 Registrate」可用，空桩就是唯一实现。

4. 直接后果：`simulated:navigation_target` / `simulated:property_tooltip` / `aeronautics:lifting_gas_type` 三个自定义注册表为空（`Registry ... was empty after loading`）；点进世界时 tag 加载报 127 个 `Couldn't load tag ... missing following references`。

### 1.3 修法（真注册垫片 + 两阶段）

改动都在 `work\aero-port\aeronautics-26\src\stub\java\com\tterrag\registrate\`：

| 文件 | 改动 |
|---|---|
| `AbstractRegistrate` | 新增 `defer()/flush()` 队列；`simple()/accept()` 真写注册表；`getAll()` 真收集（codec 反查要用）；`registryFor(key)` 从 `BuiltInRegistries.REGISTRY` 取表 |
| `Registrate` | `registerVanilla/get/getAll` 真实现 |
| `builders/BlockBuilder` | 攒 `BlockBehaviour.Properties`；`register()` 排队 → `flush` 时 `new` 方块、`Registry.register(BLOCK)`、按需建 `BlockItem` 注册进 `ITEM` |
| `builders/ItemBuilder` | 攒 `Item.Properties`，`register()` 同样两阶段 |
| `builders/BlockEntityBuilder` | `validBlocks` 收集 `BlockEntry`，flush 时 `new BlockEntityType<>(supplier, set)` 并注册（26.3 没有 `Builder` 内部类） |
| `builders/EntityBuilder` | `EntityType.Builder.of(...).build(key)` + 注册 |
| `util/entry/RegistryEntry` | 值改为可回填（`setValue`）；`get()` 空值时兜底 `flush()` |

**为什么必须两阶段而不是当场注册**：很多方块构造器会引用**同一批静态字段**，例如
`SwivelBearingBlock.<clinit>` 里的 `SimBlocks.SWIVEL_BEARING::has`、
`AeroBlocks.ENVELOPE_ENCASED_SHAFTS`（DyedBlockList）。边建边注册会在字段还没赋值时读到 null 直接 NPE
（第一次尝试就是这么崩的）。所以 `register()` 只建「空句柄 + 排队」，等这个条目类静态初始化**结束**后由
`flush()` 统一建对象 —— 与上游 Registrate「收集 builder → RegisterEvent 统一建」同构。

**flush 调用点**（8 个条目类的 `register()` / `init()` 末尾，各加一行
`com.tterrag.registrate.AbstractRegistrate.flush();`）：
`SimBlocks`、`AeroBlocks`、`SimItems`、`AeroItems`、`SimBlockEntityTypes`、`AeroBlockEntityTypes`、`SimEntityTypes`、`AeroEntityTypes`。

### 1.4 26.3 的另外两个坑（不修就 NPE/崩）

- `BlockBehaviour.Properties` 必须 `setId(ResourceKey<Block>)`，否则 `Block.<init>` 里
  `effectiveDrops()` 抛 `NullPointerException: Block id not set`。
- `Item.Properties` 必须 `setId(ResourceKey<Item>)`，否则 `Item.<init>` 抛 `Item id not set`。

### 1.5 127 → 0 的剩余部分

修完注册后还剩 51 个「缺引用」，根因是**旧降级注释把物品形态删了**：
`AeroBlocks` 的 envelope（32）与 `SimBlocks` 的 nameplate（16）、`AeroBlocks` 的 levitite（2）在
`PORT(1.21.11) 削减：垫片 ItemBuilder.build() 返回 null …` 注释处把 `.item().build()` 整段删了。
现在垫片会真建 `BlockItem`，把 6 处 `.item().build()` 恢复即可（`AeroBlocks:111/153/182/375/393`、
`SimBlocks:822`）。

另：`sable` 的两个 block tag 引用 `minecraft:chain`，26.3 已改名 `minecraft:iron_chain`（`Blocks.IRON_CHAIN`）
⇒ jar 内 `data/sable/tags/block/{super_light,quarter_volume}.json` 替换（源码不动）。

---

## 2. 卡点 1：Create 的 `RegistryCodecs`

26.3 把 `net.minecraft.core.RegistryCodecs` **搬到**
`net.minecraft.core.registries.codec.RegistryCodecs`，且 `homogeneousList` 改名/改型为 `holderSet`。

- 全 create jar 只有 1 个引用点：`PotatoCannonProjectileType.<clinit>` 的
  `RegistryCodecs.homogeneousList(Registries.ITEM)`，字段类型是 `HolderSet<Item>`。
- 修法：在 aeronautics jar 里新增桥类 `net/minecraft/core/RegistryCodecs`
  （`src/stub/java/net/minecraft/core/RegistryCodecs.java`），把 `homogeneousList(key)` 转发到
  26.3 的 `RegistryCodecs.holderSet(key)`。**不改 create 字节码**。
- 验证：`probe42` 的日志里 `PotatoCannonProjectileType` 的 `NoClassDefFoundError` 不再出现，世界加载链走通。

---

## 3. 世界加载路上依次暴露的卡点（修完注册之后）

> 顺序就是日志里实际撞到的顺序；每条都给了修法。前 4 条是**数据/注册表**，后 5 条是 **Sable/Create 26.3 运行期 API**。

| # | 报错 | 根因 | 修法 |
|---|---|---|---|
| 1 | `Failed to parse create:potato_recovery`（附 `No key type ...`） | 26.2 的 enchantment 数据格式（`requirements.condition`）26.3 不收；且 `data/minecraft/tags/enchantment/*` 仍引用它 | 删 `data/create/enchantment/potato_recovery.json`；把 `in_enchanting_table/non_treasure` 两个 tag 里的该条目删掉 |
| 2 | `Unbound values in registry minecraft:worldgen/feature: [create:zinc_ore, striated_ores_*]` | 26.3 把数据目录 `worldgen/configured_feature/` **改名** `worldgen/feature/` | jar 内重命名这 3 个文件 |
| 3 | `Adding duplicate value LayeredOreFeature@... to registry` | Create 的 `LayeredOreFeature.codec()` 是 `MapCodec.unit(this)`（单例）；26.3 `MappedRegistry` 按 identity 查重，两个 ore feature 撞车 | ASM 把 `codec()` 改成 `MapCodec.unit(new LayeredOreFeatureSupplier())`（每次解码 new 一个；新类 `com/zurrtum/create/infrastructure/worldgen/LayeredOreFeatureSupplier`） |
| 4 | 1344 条 `Failed to parse ... from pack create/aeronautics` | 26.2 的 recipe / recipe-unlock advancement 格式与 26.3 不兼容：`recipe_unlocked` 的 `recipe`→`recipes`；Create 加工配方 `ingredients`/`target` 字段变化 | 先把 advancement 的 `"recipe":` 批量改成 `"recipes":`；仍失败的 189 个文件删除；最后**清空** `recipe/advancement/loot_table` 三个数据目录（见 §4 降级） |
| 5 | `NullPointerException: chunkSource is null`（`ServerLevel.getSeaLevel`） | Sable `DimensionPhysics.createDefault` 在 `ServerLevel.<init>` 早期（chunkSource 未赋值）调 `getSeaLevel()` | 桥 `dev.eriksonn.aeronautics.compat.SableLevelBridge.getSeaLevel(Level)`：chunkSource 为空返回 64；用 `tools/patch_create_bridge.py` + `tools/sable_sea_bridge.json` 改 sable jar 的 2 个调用点 |
| 6 | `Cannot get config value before config is loaded`（`PhysicsConfigData.updateFromConfig`） | ForgeConfigAPIPort 的配置还没 load，Sable 就在 `ServerLevel.<init>` 里读 | 桥 `ConfigIntBridge.getAsInt(IntValue)`：失败退回 `getDefault()` |
| 7 | 同上（`ServerConnectionListener.startMemoryChannel`） | 同上 | 桥 `ConfigRawBridge.getRaw(ConfigValue)`：失败退回 `getDefault()`；用 `tools/fcap_config_bridge.json` **直接改 ForgeConfigAPIPort jar** 的 9 个调用点（一次修全所有 mod 的早读） |
| 8 | `MixinApplyError: plot.ChunkMapMixin ... Invalid descriptor` | 26.3 `ChunkMap.saveChunkIfNeeded` 签名变了（少了一个 `long`） | `sable.mixins.json` 里移除 3 个 `*ChunkMapMixin`（含 `plot.serialization`，见降级） |
| 9 | `IoHandle of type LocalServerChannel$LocalServerUnsafe not supported` | Sable 的 UDP 子系统把 `LocalServerChannel` 注册到 NIO handler；Netty 4.2 要求 `LocalIoHandler` | `sable.mixins.json` 移除 4 个 `udp.*` mixin（单机不需要 UDP 通道） |
| 10 | `NoSuchMethodError: ClientClockManager.getTotalTicks(Holder)` | Create 的 Flywheel 渲染钩子（`LevelRenderStateMixin`）用 26.2 签名 | 桥 `ClientClockBridge.getTotalTicks(manager, holder)` → `getInstance(holder).totalTicks()`；patch create jar 1 个调用点 |
| 11 | `NoSuchMethodError: EntityRenderDispatcher.getItemInHandRenderer()` | 26.3 删了 `ItemInHandRenderer` 整个类 | ASM 把 `ExtendoGripRenderHandler.getRendered{Main,Off}HandStack` 重写成 `return ItemStack.EMPTY`（ExtendoGrip 的手部渲染降级） |
| 12 | `IndexOutOfBoundsException at InputConstants.isKeyDown` | 26.3 原生 SDL 键盘状态缓冲；加载界面关闭抓鼠标时窗口被别的全屏程序占用 ⇒ 缓冲为空/过短 | **未修**（见 §6：环境因素未排除） |

---

## 4. 降级清单（必须写进交付说明）

本轮为了让世界**能加载**，对 create / aeronautics 两个 jar 做了以下**数据/行为削减**（均已备份 `.bak-world`）：

1. **全部配方 / 配方解锁 advancement / 战利品表被清空**
   （`data/*/recipe/**`、`data/*/advancement/**`、`data/*/loot_table/**`，create 3,404 条 + aeronautics 249 条）。
   ⇒ 创造模式能放方块、能飞；**生存模式没有合成、方块无掉落**。
   根因是 26.2 配方/进度数据格式与 26.3 不兼容（字段改名 + 结构变化），逐条修需要重写数据生成。
2. **`create:potato_recovery` 附魔删除**（26.2 格式不兼容；`create:capacity` 保留）。
3. **Sable 的 3 个 ChunkMap mixin + 4 个 UDP mixin 禁用** ⇒ 子世界（plot）区块的保存路径与 UDP 网络不可用；单机基础物理仍在。
4. **ExtendoGrip 手部渲染降级**（不显示手持物品）。
5. **Envelope/Nameplate/Levitite 的物品形态恢复**（本轮修好，不算降级）。

---

## 5. 复现（命令）

```powershell
# 1) 重建垫片 + 8 个条目类（javac.args 见 build/）
#    编译产物已直接写进 work\run26\mods-aero\aeronautics-…jar
python tools\launch26\launch.py --game-dir work\run26\probe42 --mods work\run26\mods-aero `
  --timeout 300 "--extra-game-arg=--quickPlaySingleplayer" "--extra-game-arg=newtest"
```

- 世界存档：`work\run26\probe42\saves\newtest`（从用户存档复制并升级；原件未动）。
- 新增工具：
  - `tools/sable_sea_bridge.json`、`tools/sable_config_bridge.json`、`tools/fcap_config_bridge.json`、`tools/create_clock_bridge.json`
  - `work/run26/probe_src/PatchLayeredOre.java`（ASM：单例 codec → supplier）
  - `work/run26/probe_src/PatchReturnEmpty.java`（ASM：方法体替换为 `return ItemStack.EMPTY`）
  - `tools/run_capture_world.py`（启动 + 前台化 + 抓屏）

---

## 6. 证据与限制

### 6.1 日志（`work\run26\probe42\logs\latest.log`）

世界加载链（R359 最后一轮，22:02）：

```
[22:02:14] [Worker-Main-22/INFO]: Loaded 1866 advancements
[22:02:18] [Server thread/INFO]: Starting integrated minecraft server version 26.3
[22:02:18] [Server thread/INFO]: Creating physics pipeline for ... minecraft:overworld using StaticPhysicsPipelineProvider
[22:02:20] [Server thread/INFO]: 准备生成区域中：16%
[22:02:20] [Server thread/INFO]: Time elapsed: 1750 ms
[22:02:21] [Server thread/INFO]: Tester[local:E:8ce97e38] logged in with entity id 97 at (-5.5, 69.0, 7.5)
[22:02:21] [Server thread/INFO]: System chat: Tester加入了游戏
[22:02:22] [Render thread/ERROR]: Unreported exception thrown! (InputConstants.isKeyDown)
```

### 6.2 截图：**未取得游戏内画面**

- 抓屏工具 `tools/capdesk.py` 能抓到「窗口矩形」，但**用户当时正在用这台电脑**：
  - 第一次抓屏（`notes\probe42-1.png`）抓到的是用户的另一个全屏游戏；
  - 最后尝试（`notes\probe42-world.png`）抓到的是用户的微信聊天窗口（亮度均值 **239.9**、非黑 **99.5%**，但**不是 Minecraft**）。
- 这两张图恰好证明「桌面被用户占用」，`capdesk` 的 `ShowWindow+SetForegroundWindow` 之后窗口又被抢回前台。
- 因此**没有「游戏内视角」截图**；按约束没有继续反复抢焦点。

### 6.3 下一步（给接手的人）

1. 先修 `InputConstants.isKeyDown`：给 26.3 的这个调用做 mixin/桥（`SDL_GetKeyboardState` 返回空缓冲时 fallback 到 `false`），或在用户不占用桌面时复跑 —— 世界已能加载，只差这一帧。
2. 若要恢复玩法：按 26.3 的 recipe/advancement 格式重生成数据（Create 的 datagen 已有 26.3 运行环境，可改 `RecipeProvider` 后用 `runDatagen`），而不是手改 3,000+ JSON。

---

## 7. 仍然存在 / 未修的问题

1. **`aeronautics:lifting_gas_type` 仍为空**（非阻断）。
   `AeroLiftingGasTypes` 两个字段 `REGISTRATE.liftingGasType("default"/"steam", ...)` 会走
   `AbstractRegistrate.simple(...)` → `doRegister(...)`；推测是 `Aeronautics.init()` 的调用顺序
   （`AeroLiftingGasTypes.init()` 在 `AeroRegistries.init()` 之前）让注册表还没建好；
   需要把 `AeroRegistries.init()` 提前，或给 `AeroRegistries.Keys.*` 做静态前置。
   **注意**：`Grep` 可见 `AeroRegistries` 的自定义表由 `RegistrationProvider.get` 创建，而 `init()` 里是 no-op；
   实际创建发生在 `AeroRegistrate.liftingGasType` 首次访问 `AeroRegistries.Keys` 时 —— 需要在下轮用离线探针确认。
2. **`simulated:navigation_target` 为空**（设计内降级）。
   `build.gradle` 里 `exclude '**/SimNavigationTargets.java'`，导航目标注册类根本没进编译。
3. **`simulated:property_tooltip` 已恢复**（修复前为空，现在有内容）。
4. **客户端进入世界后 1 秒崩在 `InputConstants.isKeyDown`**（见 §0/§6.2）—— 世界加载已完成，这是渲染/输入帧的问题。
5. **ExtendoGrip 手持渲染、Sable plot 保存、Sable UDP 网络** 为已知降级（§4）。

---

## 8. 一句话总结

**127 项缺失的根因不是「方块类缺失」，而是 Registrate 垫片是空桩（`BlockBuilder.register()` 从不调用 `Registry.register`），整个 Simulated/Aeronautics 内容从未注册；把垫片改成「两阶段真注册」后 127 归零、世界能加载、玩家能登录，最后一帧卡在 26.3 原生 SDL 键盘状态越界。**

---
---

# R360：进世界 ~1 秒崩（`InputConstants.isKeyDown`）已修 —— 并拿到游戏内截图

> R359 结束时最后一道墙是「进世界约 1 秒后 Render thread 崩在 `InputConstants.isKeyDown`」。
> 本章把它修掉，并给出「进世界后稳定停留 60 秒以上」的日志 + 截图 + `/give` 三重证据。
> **同时纠正 R359 的一个错误假设**：那不是「窗口被抢焦点 ⇒ SDL 键盘缓冲为空」，缓冲一直是满的 512 字节。

## 9.0 结论速览

| 项目 | 结论 |
|---|---|
| **崩因** | 26.3 把 `InputConstants.UNKNOWN` 的取值从 **-1 改成 0**（SDL scancode 0）。`KeyMapping.shouldSetOnIngameFocus()` 靠「`key.getValue() != UNKNOWN.getValue()`」过滤未绑定键位 ⇒ Create 用 **-1** 注册的空闲键位不再被过滤，`KeyMapping.setAll()` 把 `-1` 传进 `isKeyDown`，`ByteBuffer.get(-1)` 抛 `IndexOutOfBoundsException` |
| **不是** | ❌ 不是 SDL 缓冲为空/未就绪（实测 `limit=512 capacity=512`）；❌ 不是环境因素（窗口焦点无关，有焦点也照崩） |
| **修法** | 新增独立 mod **`sky262crashfix-1.0.0.jar`（2.8 KB）**：`@Mixin(InputConstants.class)` + `@Inject(method="isKeyDown", at=@At("HEAD"), cancellable=true)`，越界（`key<0 || key>=limit`）/空缓冲/SDL 抛异常 ⇒ `return false`。**不碰任何现有 jar** |
| **能稳定停留 ≥60 秒？** | ✅ **能**。probe46：进世界 35.2 s、停留 **73.9 s**、进程存活、`IndexOutOfBounds` **0**、`Unreported exception` **0**、crash-report **0**；probe45 独立复现：停留 **79.6 s** 同样零崩 |
| **游戏内截图** | `notes\probe46-world-1.png`（亮度均值 **111.2** / 非黑 **99.1%**）、`notes\probe46-world-2.png`（**90.5** / **84.1%**，+62 s 时仍在世界内） |
| **方块/物品注册** | ✅ `/give @s simulated:spring 3` 成功。服务端日志原文 `System chat: [Tester: 已将3个[弹簧]给予Tester]`，快捷栏/手持出现该物品 |

## 9.1 崩因：javap 证据链（4 步）

**① `InputConstants.isKeyDown(int)` 只判 null，不判边界**（`javap -p -c`，26.3.jar）：

```
0: invokestatic  SDLKeyboard.SDL_GetKeyboardState:()Ljava/nio/ByteBuffer;
3: astore_1
4: aload_1
5: ifnull        20                       ← 只挡 null
8: aload_1
9: iload_0                                ← key
10: invokevirtual java/nio/ByteBuffer.get:(I)B   ← key=-1 时抛 IndexOutOfBoundsException
```

**② 调用方 `KeyMapping.setAll()` 会遍历所有键位**（`grabMouse` → `setAll`）：

```
41: invokevirtual KeyMapping.shouldSetOnIngameFocus:()Z
44: ifeq 61
49: getfield      KeyMapping.key
52: invokevirtual InputConstants$Key.getValue:()I
55: invokestatic  InputConstants.isKeyDown:(I)Z
```

**③ 过滤器 `shouldSetOnIngameFocus()` 是「类型 == KEYBOARD 且值 != UNKNOWN.value」**：

```
 4: invokevirtual Key.getValue:()I
20: getstatic     InputConstants.UNKNOWN
23: invokevirtual Key.getValue:()I
26: if_icmpeq     33        ← 等于 UNKNOWN 就跳过
```

**④ 26.3 的 `InputConstants.UNKNOWN` 已经不是 -1 了**：

```
static {}:
 6: getstatic  InputConstants$Type.KEYBOARD
 9: iconst_0                       ← 0，不是 iconst_m1
10: invokevirtual Type.getOrCreate:(I)Key
13: putstatic  InputConstants.UNKNOWN
```

而 Create 侧两个键位是**字面 -1**：

- `com/zurrtum/create/client/AllKeys.<clinit>`：`47: iconst_m1` → `register(String, int)` → `new KeyMapping(name, -1, CATEGORY)`（`ROTATE_MENU`）
- `com/zurrtum/create/client/ponder/enums/PonderKeybinds`：`10: iconst_m1` → `new KeyMapping(name, -1, CATEGORY)`，`defaultKey = Type.getOrCreate(-1)`（`PONDER`）

⇒ 1.21.11 里 `UNKNOWN == -1`，这两个键位被 `shouldSetOnIngameFocus` 过滤掉，永远到不了 `get(-1)`；
26.3 把 `UNKNOWN` 改成 0 之后，`-1 != 0` ⇒ **过滤失效** ⇒ 进世界抓鼠标那一刻（`LevelLoadingScreen.onClose → Gui.setScreen → MouseHandler.grabMouse → KeyMapping.setAll`）必崩。

**运行期实锤**（`probe45/46` 日志，修复用的守卫打出来的）：

```
[crashfix] InputConstants.isKeyDown out-of-range suppressed: key=-1 limit=512 capacity=512 total=1
```

`limit=512` ⇒ **缓冲是满的**；越界的是**下标**（-1），不是缓冲长度。R359 §0 里「缓冲为空/窗口被占」的判断是错的。

## 9.2 修法（独立 mod，不动任何现有 jar）

新增文件：

| 路径 | 作用 |
|---|---|
| `work\run26\crashfix\src\skylands262\crashfix\mixin\InputConstantsGuardMixin.java` | `@Mixin(InputConstants.class)`；`@Inject(method="isKeyDown", at=@At("HEAD"), cancellable=true, require=1)`；HEAD 处取 `SDL_GetKeyboardState()`，`key<0 \|\| key>=limit` / 缓冲 null / SDL 抛异常 ⇒ `cir.setReturnValue(false)`，**否则完全不干预**（正常路径仍走原方法） |
| `work\run26\crashfix\src\skylands262\crashfix\CrashFixSupport.java` | 日志+计数（故意放在 mixin 类外面：避免 mixin 把静态字段合并进 `InputConstants`） |
| `work\run26\crashfix\src\fabric.mod.json` / `sky262crashfix.mixins.json` | 独立 mod 元数据；mixin 配置 `required:true`、`injectors.defaultRequire=1`（注入失败会**响**，不会静默） |
| `tools\build_crashfix_mixin.py` | javac（`--release 21`）+ 打包 + 自检（mixin 配置里的类必须真在 jar 里） |
| 产物 `work\run26\mods-aero\sky262crashfix-1.0.0.jar` | 2.8 KB；放进 mods 目录即生效，删掉即还原 |

```powershell
python tools\build_crashfix_mixin.py      # 编译 + 打包 + 自检
```

`javac` 的 classpath 用 `26.3.jar` + `sponge-mixin-0.17.4` + `lwjgl-sdl-3.4.3` + `slf4j-api`（全在
`%APPDATA%\.minecraft\` 下，脚本里写死版本）。运行期不需要 refmap：本项目的运行时命名空间就是
Mojang 名，mixin 里的 `InputConstants` / `isKeyDown` 直接命中。

**为什么用 HEAD 守卫而不是 `@Overwrite`**：`@Overwrite` 要抄整段方法体（26.3 一改就静默失配），
HEAD+cancellable 只在异常条件上短路，正常路径与官方逐字节同行为。

**为什么不改 Create 的 `-1`**：那是「更根治」的一条（把 `iconst_m1` 改成 0，或让 Create 用
`InputConstants.UNKNOWN`），但只治 Create；任何别的 mod 用 -1 注册键位还会崩。守卫是通用的，
两者以后可以都做。

## 9.3 验证（两轮独立 probe）

| | probe45 | probe46 |
|---|---|---|
| mods | `work\run26\mods-crashfix`（= R359 已知可进世界的 6 jar + crashfix） | 同上 |
| 进世界（`logged in`） | 91.9 s | **35.2 s** |
| 进世界后停留 | **79.6 s** | **73.9 s** |
| 进程存活到收尾 | ✅ | ✅ |
| `IndexOutOfBoundsException` | 0 | **0** |
| `Unreported exception` / crash-report | 0 / 0 | **0 / 0** |
| `Cannot acquire minimized window` | 0 | 0 |
| 守卫命中次数（`key=-1`） | 5 | **5**（含 +62 s 那次重新抓鼠标） |
| 截图 | world-1 均值 75.6 / 83.6%（world-2 因用户窗口挡在前台，**作废**） | world-1 **111.2 / 99.1%**、world-2 **90.5 / 84.1%** |

probe46 完整时间线（`work\run26\probe46\logs\latest.log`）：

```
[22:16:30] [Server thread/INFO]: Starting integrated minecraft server version 26.3
[22:16:32] [Server thread/INFO]: Time elapsed: 1170 ms
[22:16:32] [Server thread/INFO]: Tester[local:E:0746e39d] logged in with entity id 62 at (-50.8, 84.0, -31.0)
[22:16:33] [crashfix] isKeyDown out-of-range suppressed: key=-1 limit=512 capacity=512 total=1   ← 原来这里崩
[22:16:35] [Server thread/INFO]: System chat: [Tester: 已将minecraft:overworld调至时间标记minecraft:day的时刻]
[22:16:38] [Server thread/INFO]: System chat: [Tester: 已将3个[弹簧]给予Tester]
[22:17:23] [crashfix] ... total=5                                                              ← +62s 再次抓鼠标，仍不崩
[22:17:42] [Server thread/INFO]: Saving and pausing game...                                    ← 收尾（我们降下窗口）时正常存档
```

## 9.4 截图内容（我实际看到的）

`notes\probe46-world-1.png`（1302×776，亮度均值 111.2，非黑 99.1%）

- **恶地/平顶山（badlands）地貌**：大片橙色陶瓦 + 红沙台地，中间一条**蓝色河流/海湾**，上方**蓝天**；远处有台地分层条纹
- **准星**在屏幕正中央；右上角是原版教学 toast「用 W、A、S、D 来移动 / 用空格来跳跃」
- **底部快捷栏 9 格都有物品**（旧存档带过来的物品：圆形装置×4、红白拐杖糖、弯钩状金属件、护目镜、红黑装置；图标**正常**——因为它们是 Create 物品，Create 的 jar 有 694 个 `items/*.json`）；当前选中第 7 格，右下角是它的第一人称手持模型
- **聊天栏两行**：`已将minecraft:overworld调至时间标记minecraft:day的时刻`、`已将3个[弹簧]给予Tester`
- 窗口标题 `Minecraft* 26.3 - 单人游戏`
- 快捷栏 3× 放大图另存：`notes\probe46-hotbar-zoom.png`

`notes\probe46-world-2.png`（+62 s 抓的第二张，亮度 90.5，非黑 84.1%）

- 同一世界的恶地地面视角：红沙 + 橙色陶瓦 + **枯灌木/仙人掌**，左上角台地条纹
- **手持 `simulated:spring`**（紫黑格 = 缺模型贴图，见 §9.6.2）；快捷栏第 2 格是该物品
- 画面底部有一条像素是从后面窗口漏进来的（用户桌面上的 DSH 窗口有一条边被 BitBlt 抓到），**主体 95% 是游戏画面**

## 9.5 本轮新踩的坑（已写进工具，别再重踩）

1. **26.3 最小化窗口 = 直接自杀**（不是黑屏，是退出）：
   `SurfaceException: Cannot acquire minimized window` @ `GlSurface.acquireNextTexture ← Minecraft.renderFrame`，
   没有 crash-report，`launch.py` 报 `RESULT: FAILED (exit=4294967295)`。
   ⇒ 需要「抓完继续跑」时**绝不能 `SW_MINIMIZE`**；用 `capdesk.py --no-minimize`，
   之后把窗口 `SetWindowPos(HWND_BOTTOM)` + `SetForegroundWindow(原来的前台)` 还给用户。
2. **抓图必须校验前台窗口**：probe45 的第二张抓到的是**用户桌面上的 DSH 聊天窗**（亮度 249.7 全白），
   而当时 `capdesk` 自己的 `SetForegroundWindow` 早返回了。
   ⇒ `capdesk.py --require-foreground`：**每一帧 BitBlt 之前**重新查 `GetForegroundWindow()`，不是目标窗口就跳过该帧；
   一帧都没取到就返回 4，由调用方重试（probe46 第 2 张重试 5 次才拿到干净帧）。
3. **失去焦点会暂停单人游戏**（截图会拍到「游戏菜单」）：靠日志里的 `Saving and pausing game...` **计数增量**
   判断是否暂停，暂停了才发一次 `Esc` 恢复（不要无脑发，未暂停时 Esc 会打开菜单）。
   probe46 把窗口降到底部后**没有**暂停（`pauseOnLostFocus:false` 生效），所以 73.9 s 里世界一直在跑。
4. **并发冲突**：做本轮时 `work\run26\mods-aero\aeronautics-*.jar` 正在被另一个会话改（recipe 恢复），
   导致 22:07 那轮一进世界就 `ReportedException: Registry Loading`。
   ⇒ 取证要用**冻结集**：`work\run26\mods-crashfix\`（R359 的 6 个 jar + crashfix，aeronautics SHA256 `D3EC481C…`）。

## 9.6 剩余问题（本轮不修）

### 9.6.1 全部 recipe / advancement / loot_table 仍被清空（**最大玩法损失**，一号任务）

`data/*/recipe/**`、`data/*/advancement/**`、`data/*/loot_table/**` 仍在删掉的状态 ⇒ **没有任何合成配方、方块无掉落**。
26.3 把 **recipe 变成了动态注册表**（`RegistryDataLoader` 加载）⇒ 任何一条解析不过的配方都**不是「跳过」而是整个世界加载失败**
（`IllegalStateException: Failed to load registries due to errors`），所以「先塞回去再逐条修」这条路走不通，
只能在**离线**把 3,000+ 条数据转成 26.3 格式（Create/Aeronautics 的 datagen 是最现实的路径）。
参考：本轮 22:08 那次 `mods-aero` 里被塞回 263 条 recipe，世界立刻崩在
`create:white_sail` / `aeronautics:wooden_propeller_from_andesite` / `simulated:yellow_handle` 等条目上
（`List is too short: 0, expected range [1-9]`、`No key fabric:type`）。

### 9.6.2 Simulated / Aeronautics 的**物品图标全是紫黑格**（缺 26.3 的 item definition）

- 26.3（自 1.21.4 起）物品模型入口是 **`assets/<ns>/items/<id>.json`**（item model definition），
  `assets/<ns>/models/item/*.json` 只是被它引用的模型。
- 实测：`simulated` **items_defs = 0 / item_models = 102**，`aeronautics` **0 / 47**；
  而 Create 的 jar 已有 **694** 个 `assets/create/items/*.json`（所以 Create 物品图标正常）。
- ⇒ `/give @s simulated:spring` 拿到的物品**能拿、能放、名字正确**，但图标/手持是**紫黑缺模型**（见 §9.4 第二张图）。
- 修法（未做）：为 102 + 47 个物品各生成一个
  `{"model":{"type":"minecraft:model","model":"<ns>:item/<id>"}}`，塞进 jar 的 `assets/<ns>/items/`。

### 9.6.3 其它（沿用 R359 清单）

1. `aeronautics:lifting_gas_type` 注册表仍空（非阻断）。
2. `simulated:navigation_target` 仍按设计 exclude。
3. ExtendoGrip 手部渲染、Sable plot 保存、Sable UDP 网络 仍是降级项（见 §4）。
4. 用户自己的 `work\run26\play` 实例（22:07 启动）崩在 `Registry Loading`（= 9.6.1，不是输入崩），
   说明**这个实例里的 aeronautics jar 带着旧 recipe**；要给它换成清过 recipe 的 jar。

## 9.7 复现命令

```powershell
# 1) 构建 crashfix（幂等）
python tools\build_crashfix_mixin.py

# 2) 冻结的已知可进世界 jar 集（R359 的 6 个 jar + crashfix）
#    work\run26\mods-crashfix\

# 3) 一键：启动 → 进世界 → /time set day → /give → 抓图 → 停留 62s → 再抓图 → 收尾
python tools\run_verify_world.py `
  --game-dir work\run26\probe46 --mods work\run26\mods-crashfix `
  --world 新的世界 --save-src work\run26\probe40\saves\新的世界 `
  --prefix notes/probe46 --hold 62
```

输出：`notes\probe46-world-1.png` / `-world-2.png` / `notes\probe46-verify.json`。

## 9.8 一句话总结

**「进世界 1 秒崩」不是 SDL 缓冲的环境问题，而是 26.3 把 `InputConstants.UNKNOWN` 从 -1 改成 0，
让 Create 用 -1 注册的空闲键位漏过了 `shouldSetOnIngameFocus` 过滤器；一个 2.8 KB 的 HEAD 守卫 mixin 之后，
进世界 74 秒不崩、`/give simulated:spring` 成功、拿到了恶地地貌的游戏内截图 —— 剩下最大的坑是「没有任何合成配方」，
以及 Simulated/Aeronautics 物品缺 26.3 的 `items/*.json` 定义（图标紫黑）。**
