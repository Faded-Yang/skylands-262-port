# port-smallmods —— 小体积 mod 批量移植（26.3 Fabric，第 11 组 `g11`）

> 日期：2026-10-18 ｜ 目标：MC **26.3** + Fabric Loader 0.19.5 + Java 25
> 验收口径：**`WORLD_OK` = `logged in with entity id`**（`tools/watch_world.py`，每次都用 `watch/saves/New World (1)` 的**全新副本**）
> ＋ promote 后**在交付物本体 `mods-stable` 上复跑标题**（`launch.py --watch-title` 三条标记全命中）。
> 工作目录：`work/run26/port/g11/`（新流水线，**没有**用 g7）。

---

## 0. 结论

| 项 | 结果 |
|---|---|
| `mods-stable` | **67 → 70 jar**（+3）；本体复验 `WORLD_OK 36.2 s` + `TITLE_SCREEN_OK`（见 §1.4） |
| 新成功（以**进世界**为准） | **3 个**：`passivemobspawn` / `sablejade` / `jadeaddons` |
| 明确放弃（有具体卡点，不占用轮次） | 8 个：见 §2 |
| 工具 | 新增 `g11/_dec.py`（CFR 反编译）/`_jp.py`（26.3 javap）/`_javac11.py`/`_build11.py`/`_stage.py`/`_fix_sablejade.py` |

先查过 Modrinth Fabric 构建（`tools/probe_fabric_builds.py`）：这批 11 个 slug 里**只有 `playeranimator` 有 Fabric 构建**（最新 1.21.7）；
`waystones-sable` / `blueprint` 明确「无任何 Fabric 构建」，其余 slug 在 Modrinth 上**不存在**（原包里的 jar 名与 slug 不同）。
⇒ 这批**没有「更接近 26.3 的 Fabric 版本」可捡**，全部只能走「1.21.1 NeoForge 反编译 → 26.3 Fabric 重写」。

---

## 1. 三个成功的

### 1.1 ✅ `passivemobspawn` 1.0.0（空岛友好：草方块上刷被动生物）

| 项 | 值 |
|---|---|
| 原始 | `passivemobspawn-1.0.0.jar`（NeoForge，7 class） |
| 产物 | `work/run26/port/g11/pm/passivemobspawn-1.0.0-26.3.jar`（13 KB / 7 class） |
| 进世界 | **`WORLD_OK 38.4 s`**（测试标签 `pm1`） |
| promote 后标题 | **`TITLE_SCREEN_OK 24.8 s`**（68 jar） |
| 运行期证据 | `[PassiveMobSpawn] initialised (fabric 26.3 port)`（entrypoint 真执行） |

改法（编译 0 错一次过，`src` 重写 3 个类）：
* `@Mod` 构造器 → `ModInitializer`；NeoForge `ServerTickEvent.Post` → `ServerTickEvents.END_SERVER_TICK`
* `ResourceLocation` → `Identifier`；`MobSpawnType` → `EntitySpawnReason`；
  `getMinBuildHeight/getMaxBuildHeight` → `getMinY/getMaxY`；
  `EntityType.create(Level)` → `create(Level, EntitySpawnReason)`；
  `addFreshEntityWithPassengers` → `tryAddFreshEntityWithPassengers`；
  `EntityType.PLAYER` → `EntityTypes.PLAYER`；`BlockPos.getCenter()` → `Vec3.atCenterOf`；
  `Entity.moveTo(d,d,d,f,f)` → `snapTo(...)`；`GameProfile.getName()` → `name()`（26.3 里是 record）；`level.random` → `level.getRandom()`

降级（如实记）：
* **配置文件整条删除**（原版 `ModConfigSpec`：debug / spawnCheckDelaySeconds / passiveMobs）⇒ 写死默认值（`debug=false`、`60 s`、5 种动物各 100 权重）。
* 原版那个「启动时修补 config 里缺失的 `spawning.debug`」逻辑随配置一起删除。
* 白天判定：26.3 的 `Level` **已经没有 `isDay()/getDayTime()`**（改成世界时钟）⇒ 用 `getOverworldClockTime() % 24000 < 12000`。
* **未做**「肉眼看见动物刷出来」的行为验证：默认 60 s 一次检查，验收窗口 38 s 内不保证触发；能证的是「mod 加载 + entrypoint 执行 + 进世界」。

### 1.2 ✅ `sablejade` 1.3.0（Sable × Jade：子世界方块 tooltip + 射线重定位）

| 项 | 值 |
|---|---|
| 原始 | `sablejade-1.3.0.jar`（NeoForge，15 class，client-only，无 mixin） |
| 产物 | `work/run26/port/g11/sablejade/sablejade-1.3.0-26.3.jar`（296 KB / 14 class + 原 assets） |
| 进世界 | **`WORLD_OK 36.2 s`**（`sj1`） |
| promote 后标题 | **`TITLE_SCREEN_OK 25.7 s`**（69 jar） |
| 运行期证据 | `Loading sablejade` + **`Start loading plugin from Sable: Jade: dev.mgcode.sablejade.SableJadePlugin`**（Jade 真把插件装上了） |

依赖面实测（都在 `mods-stable` 里，且签名一致，**这是它能一次过的原因**）：
`dev.ryanhcode.sable.Sable.HELPER`（`ActiveSableCompanion.getContaining/projectOutOfSubLevel`）、
`LevelPoseProviderExtension.sable$pushPoseSupplier(Function<SubLevel,Pose3dc>)`、
`ClientSubLevel.renderPose(float)`、`Pose3dc`（在 `sablecompanion-1.6.0-26.3.jar` 里）、Jade `IBlockComponentProvider/ITooltip/IWailaClientRegistration`。

改法：
* `ResourceLocation` → `Identifier`（`Identifier.fromNamespaceAndPath` 在 26.3 仍存在，**不用**改调用形态）
* `net.neoforged.fml.ModList.get().isLoaded(x)` → `FabricLoader.getInstance().isModLoaded(x)`
* `SableJadeConfig`（NeoForge `ModConfigSpec`、EnumValue/BooleanValue）→ 写死默认值（`WITH_GOGGLES` / `onlyInSubLevels=true`）
* `@Mod` → `ModInitializer`（只打一行 log）
* 客户端 API：`Minecraft.getTimer()` → `getDeltaTracker()`；`GameRenderer.getMainCamera()` → **`mainCamera()`**；
  `Camera.getPosition()` → **`position()`**；`Camera.getLookVector()` **26.3 已删** ⇒ 改用 `player.getViewVector(partialTick)`（长度退化时给 `(0,0,1)` 兜底）
* 入口：`fabric.mod.json` 里用 Jade 的**自定义 entrypoint 键 `jade`**（不是 main/client）

降级：
* 配置项 `tooltipInfoMode` / `tooltipInfoOnlyInSubLevels` 不能改（写死默认）
* 只用**反射**的可选集成（Create 护目镜 / Simulated 的 `BlockPropertiesTooltip` / `HoldInteractionManager`）**原样保留**：
  反射不到就返回 null/false，不会崩 —— 这部分**零降级**

### 1.3 ✅ `jadeaddons`（Jade Addons 6.1.2）

| 项 | 值 |
|---|---|
| 原始 | `JadeAddons-1.21.1-NeoForge-6.1.2.jar`（NeoForge，32 class + 3 mixin + 23 个 target_modifier JSON） |
| 产物 | `work/run26/port/g11/jadeaddons/JadeAddons-6.1.2-26.3.jar`（20 KB / **4 class** + 原 assets） |
| 进世界 | `WORLD_OK 34.3 s`（`ja1`，插件被拒）→ **`WORLD_OK 36.2 s`（`ja2`，插件装上）** → `WORLD_OK 38.2 s`（`ja3`，加计数日志的终版） |
| promote 后 | `WORLD_OK 36.2 s`（70 jar 本体）+ `TITLE_SCREEN_OK 26.0 s`；补 `zh_cn` 后**又重测一遍**（见 1.4） |
| 运行期证据 | `Start loading plugin from Jade Addons: jadeaddons.JadeAddonsBase` + `Scanned 23 jade target modifier files, loaded 0 replacements` |

**两个真坑（都会导致「进世界了但功能没生效」——正是任务书说的那种假完成）**：
1. **Jade 拒绝 `snownee.jade.*` 包下的第三方插件**。Jade `Jade.loadPlugins` 里有硬判断：
   `clazz.startsWith("snownee.jade.") && !entrypoint.modId().equals("jade")` ⇒ 抛
   `IllegalStateException: Built-in plugin registered by non-Jade mod`。
   第一次（`ja1`）**世界照样进得去**，只有一行 ERROR，插件被丢掉。**修法：把包名从 `snownee.jade.addon` 挪到 `jadeaddons`**。
   （这是「进世界 ≠ 功能生效」的活例子，不能只看 `WORLD_OK`。）
2. **26.3 的 `SimpleJsonResourceReloadListener` 只剩 `(Codec, FileToIdConverter)` 构造器**，没有 `(Gson, String)` 了
   ⇒ `TargetModifierLoader` 改成自己 `ResourceManager.listResources("jade/target_modifier", …)` + Gson 解析。

改法：
* `@Mod` → `ClientModInitializer`；`IWailaPlugin` 原样实现（Jade 接口 26.3 与 1.21.1 基本一致，只有 `ResourceLocation→Identifier`）
* `NeoForge.EVENT_BUS.addListener(TagsUpdatedEvent(CLIENT_PACKET_RECEIVED))` → `ClientPlayConnectionEvents.JOIN`（进世界时载一次）

降级（**这次降得比较狠，必须写进交付说明**）：
* **只保留 `general` 插件（target_modifier 伪装/隐藏）**；`create` / `enderio` / `computercraft` / `lootr` / `oritech` 五个插件**整块删除**（32 → 4 class）。
  本包里这些 mod 只有 create 装了，但 Create 插件要吃 26.3 全变的 `com.zurrtum.create` API，本轮不做。
* 三个 mixin（`BacktankBlockEntityAccess` / `BlueprintOverlayRendererAccess` / `FilterItemAccess`，全是为 create 插件服务的）删除
* `remove_elements`（按 tag 删 tooltip 行）删除，只保留 `replace`
* `equipment_requirement` 配置项 + Curios 集成删除
* **本包内实际生效条数 = 0**：23 个 JSON 里 `replace` 只有 2 条（aether/artifacts 的 mimic），这两个 mod 没装；
  `create/package.json` 与 supplementaries 那批是 `remove_elements`（已删）。⇒ **功能在本整合包内「可运行但无可作用对象」**，这点必须如实说。
* **汉化补丁（否则破坏「缺 0」交付指标）**：原 jar 只有 `en_us`（41 键）+ ko/pt/ru/tr，**没有 zh_cn**。
  已自译 `assets/jadeaddons/lang/zh_cn.json`（41/41 键，`_build11.py` 的 `extra` 写进 jar），并在**补完之后重跑了世界 + 标题**（§1.4）。

### 1.4 交付物本体复验（改 jar 就重测）

| 轮次 | 内容 | 结果 |
|---|---|---|
| `stable70` | 70 jar（zh 补丁**之前**的 jadeaddons） | **`WORLD_OK 36.2 s`** |
| `stable70zh` | 70 jar（**加了 zh_cn 的终版** jadeaddons） | **`WORLD_OK 36.2 s`** + **`TITLE_SCREEN_OK 24.6 s`**（交付物本体） |

> `mods-stable` 里保留了 `.bak-nozh`（旧 jar 的备份，扩展名不是 `.jar`，Fabric 不会加载）。

### 1.5 交付清单（三个 jar 的 SHA-256，交付物体内实测的就是这三份）

| jar | 字节 | SHA-256 |
|---|---|---|
| `passivemobspawn-1.0.0-26.3.jar` | 13,182 | `86E1DE160FB916434E6EC509556CDE11DAF6228FB6A10987E8201AA459F1D0C0` |
| `sablejade-1.3.0-26.3.jar` | 296,234 | `A33F6B4ADFC1AFDC98488837BD6D075DF9039B53A2A4AA1DDC2B5F40572CA1B9` |
| `JadeAddons-6.1.2-26.3.jar` | 21,548 | `ED3DC4942012468A52BCB437DD6520F6B98F7C63B33CE347E3A19FF598F204B2` |

jar 名单快照：`work/run26/mods-stable.jar-list.bak-r391-smallmods.txt`（70 行）。

**汉化没被破坏**：`python tools/lang_audit.py work/run26/mods-stable` ⇒
`en_us 10,129 / zh_cn 10,357 / 缺失 0（100.0%）`；`jadeaddons en=41 zh=41 缺 0`，`passivemobspawn`/`sablejade` 无 lang（不参与统计）。


---

## 2. 没做 / 放弃的 8 个（卡点都是实测出来的，不是猜）

| mod | 卡点（具体到符号/类） | 判定 |
|---|---|---|
| `constraintfix`（`ropefix`） | 6 个 mixin 打 `dev.simulated_team.simulated...rope`。目标类**都在** `aeronautics-*.jar` 里，但 `RopeStrandHolderBehavior` 的 **`read(ValueInput, boolean)` / `write(ValueOutput, boolean)`** 已从 `read(CompoundTag, HolderLookup.Provider, boolean)` 迁走 ⇒ `@Inject(method="read")` 的 `CompoundTag` 参数根本不匹配，得按 `ValueInput`（只读）重写整段 NBT 修补逻辑。**≥1 轮**，本轮不做 | 放弃（有明确修法，下轮） |
| `sable_createaddition_compat` | ① 依赖 **`dev.ryanhcode.sable.neoforge.event.ForgeSablePostPhysicsTickEvent`**（NeoForge 专属，我们的 sable 26.3 端口没有 neoforge 事件桥）；② 客户端是 26.3 **render state 之前的旧渲染 API**（`MultiBufferSource` / `BlockEntityRenderDispatcher` / `VanillaSubLevelBlockEntityRenderer`）；③ 5 个 mixin 打 createaddition + create(`com.simibubi.create`→`com.zurrtum.create`) | 放弃（≈1–1.5 轮） |
| `portable_engine_liquid_fuel` | 核心是 **NeoForge Capability + `DataMapType` 注册表**（`RegisterDataMaps`/`ILavaTankProvider`/`PortableEngineCapabilityHandler`）；Fabric 没有 capability 系统，datamap 也没有等价物 ⇒ 要么写垫片，要么整个「液体燃料」语义丢失 | 放弃（垫片量级） |
| `climbable_ropes` | 23 个文件里 18 个是客户端：`MovementInputUpdateEvent` / `RenderPlayerEvent` / `RegisterKeyMappingsEvent` / `ConfigurationScreen` + 自定义 KeyMapping + 2 个 mixin（`PlayerSkyhookRenderer`）。26.3 的输入与玩家渲染都变了 | 放弃（≈1–2 轮） |
| `waystonessable` | 40 class，NeoForge **`RegisterPayloadHandlersEvent`/`PayloadRegistrar`** 网络层 + `FakePlayerFactory` + `RegisterCommandsEvent` + gametest 6 个 + 7 个 mixin | 放弃 |
| `mysterious_mountain_lib` | 73 class 的库：bedrock 模型/POJO 加载、container、客户端 model/particle，几乎全是客户端渲染资产管线 | 放弃 |
| `playeranimator` | 98 文件，Architectury 注入的 `PlatformMethods` + 127 class + mixin + 网络 + 玩家动画层 | 放弃（唯一有 Fabric 构建，但只到 1.21.7） |
| `blueprint` | **493 class**（TeamAbnormals 库，含整套客户端 screen/renderer/texture atlas） | 放弃（量级不符） |

> 这 8 个都**没有开工成半成品**：一行代码都没往 `mods-stable` 里放。

### 2.1 首编基线（同一套 26.3 classpath 下**原样编译**的 javac 错误数，给下轮排序用）

| mod | 首编错误 | 说明 |
|---|---|---|
| `constraintfix` | **58** | 全是 mixin 侧：`read/write(ValueInput/ValueOutput)`、`com.simibubi.create`→`com.zurrtum.create`、`@WrapMethod` 目标签名。**最少的一批** |
| `climbable_ropes` | **99** | 客户端事件 + KeyMapping + 玩家渲染 |
| `waystonessable` | **122** | NeoForge 网络层 + FakePlayer + gametest |
| `mysterious_mountain_lib` | 15 → **282** | 15 条是 CFR 语法残渣（`1.$assertionsDisabled`，已用 `_fix_mmlib.py` 修掉），修完**才露出 282 条真缺口**（`Rotations.getX()` 在 26.3 变 `EulerAngle`、bedrock 模型渲染管线等）⇒ 别被「15 错」骗了 |
| `playeranimator` | **388** | Architectury 平台层 + 127 class 动画栈 |
| `blueprint` | 未编（493 class，量级不符，直接不排） | |

---

## 3. 本批新增工具（`work/run26/port/g11/`）

| 工具 | 作用 |
|---|---|
| `_dec.py <jar> <outdir>` | CFR 0.152 反编译（NeoForge jar 直出官方名，不用 intermediary） |
| `_jp.py <fqcn> [子串]` | 用 `26.3.jar` 的 `javap -p` 查成员（**查 26.3 真签名，不靠 1.21.11 记忆**） |
| `_javac11.py <mod>` | 编译。classpath = `g7/cp_join.txt`（**已剔 1.21.1 client**）+ `fabric-loader 0.19.5`（`ModInitializer` 在这里，**不在 fabric-api**）+ `g6/_fab/*.jar` + **`mods-stable/*.jar`（全部 26.3 已交付物）** |
| `_build11.py <mod>` | 用「原 jar 的 data/assets + 新编译 class」重打包，`CONFIG` 里配 prefix / drop / fabric.mod.json 覆盖 |
| `_stage.py <dst> [extra...]` | 用**硬链接**把 `mods-stable` 的 jar 铺成 staging mods 目录 + 塞候选 jar（零拷贝，70 个 jar 秒级） |
| `_fix_sablejade.py` | sablejade 的可复现迁移脚本（含 Camera/DeltaTracker 那一组改动） |

---

## 4. 复现命令（三个成功件）

```powershell
# passivemobspawn
python work\run26\port\g11\_javac11.py pm
python work\run26\port\g11\_build11.py pm
python work\run26\port\g11\_stage.py work/run26/modset-g11 pm/passivemobspawn-1.0.0-26.3.jar
python work\run26\port\g8\_testworld.py work/run26/modset-g11 pm1 --world "New World (1)"

# sablejade（先 _fix_sablejade.py 生成 sablejade/src）
python work\run26\port\g11\_fix_sablejade.py
python work\run26\port\g11\_javac11.py sablejade
python work\run26\port\g11\_build11.py sablejade

# jadeaddons（源码在 g11/jadeaddons/src，已从 snownee.jade 迁包到 jadeaddons）
python work\run26\port\g11\_javac11.py jadeaddons
python work\run26\port\g11\_build11.py jadeaddons

# 每次 promote 后在交付物本体复跑标题
python tools\launch26\launch.py --game-dir work\run26\stag1 --mods work\run26\mods-stable --watch-title --timeout 240
```

---

## 5. 给下一轮的提示

1. **`mods-stable/*.jar` 全量上 classpath** 这招很好用（`_javac11.py`）：Sable / Jade / Create / FCAP / Waystones 的 26.3 签名直接可查可编，
   不用手工挑 jar。代价是编译稍慢，但省掉「找不到符号 → 猜包名」的往返。
2. **`ForgeConfigAPIPort` 里真的有 `net/neoforged/neoforge/common/ModConfigSpec`**（还有 `net.neoforged.fml.config.ModConfig`），
   所以「只想让 config 类编过」时**不必**重写成静态字段；但 `ModConfigEvent` / `ModContainer` / `@Mod` 不在里面，事件注册还是得换。
   本批为了少一个运行期依赖面，选了「写死默认值」。
3. **Jade 插件三条硬规则**：① entrypoint 键是 **`jade`**；② 插件类**不能**在 `snownee.jade.` 包下；
   ③ 插件被拒**不会**让世界进不去（只在 log 里一行 ERROR）⇒ 必须去 log 里搜 `Start loading plugin from`。
4. **26.3 客户端时间/相机 API**：`Minecraft.getDeltaTracker()`、`GameRenderer.mainCamera()`、`Camera.position()`、`Camera.getLookVector()` 已删。
5. 下一个性价比最高的是 **`constraintfix`**（卡点已定位到 `read(ValueInput,…)`，方法体是纯 NBT 算术，重写不难）。
