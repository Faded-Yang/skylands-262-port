# net.neoforged 垫片普查 × 定时炸弹审计（skylands-262 / MC 26.3 + Fabric Loader 0.19.5）

> **性质**：纯静态审计。**没有启动游戏、没有改任何 jar、没有碰 mods-stable / watch**。
> **基线**：`work\run26\mods-stable` 71 个 jar。审计主基线 = **R405 之前**的 aeronautics（SHA-256 `2DF06E76…BD2B`，现为 `…jar.bak-laserpointer`）；**当前交付件已含 R405 修复**（`B0A9383F…`，见第 0 节与第 4.2 节）。
> **产物**：本文（人读）+ `work/run26/port/g23a/census.json`（机读，每类型一行）+ `tweaker.json`（classtweaker 可行性核算）+ `generated.classtweaker` + 全部脚本（见第 10 节）。

---

## 0. 一句话结论

**全包只有 1 个「跑到必炸」的 net.neoforged 定时炸弹，就是已知的 `ILevelReaderExtension`（`simulated:laser_pointer`）。**

> **R405 之后复核（当前 `mods-stable`，aeronautics `B0A9383F…`）**：全量重跑 `census.py` 结果为 **BOMB = 0 / RISK = 5 / SAFE = 50**。`ILevelReaderExtension` 已由新 mixin 类 `LevelILevelReaderExtensionMixin` 声明实现，且垫片体已从 `return true` 改成 `hasChunksAt` 真语义 ⇒ **本审计的 BOMB 结论是「修复前基线」的结论**，现作为系统性风险图谱保留（第 4.2 节记录差异）。
`sable` 的 21 个引用 class **全部**只用到 ForgeConfigAPIPort（FCAP）的 `ModConfigSpec` 配置家族——那是真移植，**0 炸弹**；`aeronautics` 其余引用集中在 datagen 模型生成器 / `Tags` / 注解 / 配置桥上，也都不构成炸弹。
5 个「类型缺失」RISK **全部集中在一个死类** `FarmersDelight` 的 `LaunchpadClientEvents`（NeoForge 事件总线回调类，Fabric 上无人加载）。

NeoForge **26.3.x** 的 `injected-interfaces.json` 共 115 个目标 / 116 条映射（其中 113 条指向 `net.neoforged`）。本包 classpath 上只存在 **1** 个对应接口 ⇒ 过滤后的 classtweaker **只需 1 行**就能覆盖 **1 / 1** 现有 BOMB。
⚠ **不能**把 115 条整份注入：其中 110 条映射的接口类在本包根本不存在，注入不存在的 superinterface 会让目标类加载时 `NoClassDefFoundError`。

---

## 1. 背景与范围

`simulated:laser_pointer` 的根因（`docs\block-render-sweep.md` F3，已实测）：
`SimLevelUtil.isAreaActuallyLoaded` 对 `Level` 做无保护强转 `(ILevelReaderExtension)`，而该接口是 **aeronautics jar 自带的垫片**，全包没有任何类实现它 ⇒ `ClassCastException` ⇒ `Ticking block entity`。
本审计要回答：**这套「声明了但没人实现」的形态在全包还有几处？** 以及（Lead 追加）**能不能用一份 Fabric class tweaker 批量兜底？**

审计对象（`census.py`）：

- 71 个 jar（含嵌套 jar，最多 3 层）全部 class 的**类头**（super / interfaces / flags / 方法表），共 19,233（R405 前）/ 19,234（当前）个 class 定义；
- 常量池里真正出现 `net/neoforged` 的 class 逐一声明式解析：`checkcast` / `instanceof` / `new` / `anewarray` / `invoke*` / 字段读写 / `ldc` / `invokedynamic`（lambda 目标）/ 方法·字段描述符 / 注解；
- 每个引用点的**行号**（LineNumberTable）与 **pc**，便于和崩栈对行；
- mixin 配置（`*.mixins.json` 等）与 `@Mixin` 的 targets，用于判断「mixin 类声明 implements」算不算实现者。

口径对照：台账写「aeronautics 36 个 class、sable 21 个 class 引用 net.neoforged」——**粗口径（常量池含该字节串）复现为 108 个 class**：FCAP 50 / aeronautics 36 / sable 21 / FarmersDelight 1。本审计的细口径（真正解析出 net.neoforged 类型引用，排除纯字符串）为 **103 个 class**：FCAP 47 / aeronautics 34 / sable 21 / FarmersDelight 1（R405 后 aeronautics +1 个 mixin class ⇒ 104；两组计数都在 `census.json.meta` 与 `census-pre-r405.json.meta`）。

---

## 2. 判定口径（每一类的规则）

| 判定 | 条件（静态） | 运行时表现 |
|---|---|---|
| **BOMB** | ① 类型是接口/抽象类，**传递闭包内 0 个具体实现者**，也没有「已配置的 mixin 类声明 implements」、没有 lambda 目标；且 ② 存在**未受 `instanceof` 保护**的 `checkcast`（或具体类从未被 `new`/无子类却有无保护强转） | 执行到那一行 → `ClassCastException`（就是 laser_pointer） |
| **RISK** | ① 类型**完全未定义**于任何 jar（首个解析/执行 → `NoClassDefFoundError`）；② 引用的**成员**在垫片里找不到（`NoSuchMethodError/NoSuchFieldError`，本次 0 例）；③ 零实现者但存在未受保护的 `invokeinterface`；④ 零实现者但仅有类型引用 | 只在走到该路径时炸；需要判断可达性 |
| **SAFE** | 有具体实现者 / 有 lambda 目标 / 强转由 `instanceof` 守卫 / 注解类型 / 只有静态调用且定义齐全 | 不构成该类型的转炸 |

「受保护强转」的静态启发（`guard_for`）：同一方法内、该 `checkcast` 之前存在同类型的 `instanceof`，且满足其一：① 与强转在同一源码行；② 二者之间有条件跳转，且跳转目标越过该强转（`if (x instanceof T) { ((T)x)... }` 的典型形态）。`laser_pointer` 的强转**没有任何 instanceof**，因此判 BOMB；FCAP 的 `TranslatableEnum` 强转有同类型 instanceof 守卫，因此从初版的 BOMB 降为 SAFE（见第 8 节置信度）。

---

## 3. 结论总表（55 个被触达的 net.neoforged 类型）

> 下表按 **R405 之前**的 `mods-stable` 判定（原始产物 `census-pre-r405.json`）；R405 之后唯一变化是第 1 行的 BOMB → SAFE，其余 54 行不变（见第 4.2 节）。

> 「定义在」缩写：aeronautics = `aeronautics-fabric-0.1.0-port.26.3.jar`，FCAP = `ForgeConfigAPIPort-v26.3.1-mc26.3.x-Fabric.jar`。
> 「常量池引用 class 数」含类型自身的 class 文件（注解描述符/自身泛型签名可能自引用）；BOMB 那一行的**外部**引用者只有 `SimLevelUtil` 一个。

| # | 判定 | 类型 | 定义在 | 形态 | 方法(抽象/default) | 具体实现者 | 常量池引用 class 数 |
|---|---|---|---|---|---|---|---|
| 1 | **BOMB → 现 SAFE** | `net/neoforged/neoforge/common/extensions/ILevelReaderExtension` | aeronautics | interface | 0/1 | 1（mixin） | 2→3 |
| 2 | RISK | `net/neoforged/bus/api/SubscribeEvent` | **缺失** | MISSING | -/- | 0 | 1 |
| 3 | RISK | `net/neoforged/fml/common/EventBusSubscriber` | **缺失** | MISSING | -/- | 0 | 1 |
| 4 | RISK | `net/neoforged/neoforge/client/event/RegisterGuiLayersEvent` | **缺失** | MISSING | -/- | 0 | 1 |
| 5 | RISK | `net/neoforged/neoforge/client/gui/GuiLayer` | **缺失** | MISSING | -/- | 0 | 1 |
| 6 | RISK | `net/neoforged/neoforge/client/gui/VanillaGuiLayers` | **缺失** | MISSING | -/- | 0 | 1 |
| 7 | SAFE | `net/neoforged/api/distmarker/Dist` | aeronautics | enum | 0/0 | 0 | 5 |
| 8 | SAFE | `net/neoforged/api/distmarker/OnlyIn` | aeronautics | annotation | 1/0 | 0 | 4 |
| 9 | SAFE | `net/neoforged/fml/config/ConfigTracker` | FCAP | class | 0/0 | 0 | 8 |
| 10 | SAFE | `net/neoforged/fml/config/ConfigWatcher` | FCAP | class | 0/0 | 0 | 2 |
| 11 | SAFE | `net/neoforged/fml/config/IConfigSpec` | FCAP | interface | 4/0 | 2 | 14 |
| 12 | SAFE | `net/neoforged/fml/config/IConfigSpec$ILoadedConfig` | FCAP | interface | 2/0 | 1 | 8 |
| 13 | SAFE | `net/neoforged/fml/config/LoadedConfig` | FCAP | class | 0/0 | 0 | 3 |
| 14 | SAFE | `net/neoforged/fml/config/ModConfig` | FCAP | class | 0/0 | 0 | 20 |
| 15 | SAFE | `net/neoforged/fml/config/ModConfig$Type` | FCAP | enum | 0/0 | 0 | 15 |
| 16 | SAFE | `net/neoforged/fml/config/ModConfigs` | FCAP | class | 0/0 | 0 | 6 |
| 17 | SAFE | `net/neoforged/neoforge/client/gui/ConfigurationScreen` | FCAP | class | 0/0 | 0 | 14 |
| 18 | SAFE | `net/neoforged/neoforge/client/gui/ConfigurationScreen$1` | FCAP | class | 0/0 | 0 | 2 |
| 19 | SAFE | `net/neoforged/neoforge/client/gui/ConfigurationScreen$ConfigurationListScreen` | FCAP | class | 0/0 | 0 | 4 |
| 20 | SAFE | `net/neoforged/neoforge/client/gui/ConfigurationScreen$ConfigurationListScreen$ListLabelWidget` | FCAP | class | 0/0 | 0 | 3 |
| 21 | SAFE | `net/neoforged/neoforge/client/gui/ConfigurationScreen$ConfigurationSectionScreen` | FCAP | class | 0/0 | 1 | 7 |
| 22 | SAFE | `net/neoforged/neoforge/client/gui/ConfigurationScreen$ConfigurationSectionScreen$Context` | FCAP | class | 0/0 | 0 | 5 |
| 23 | SAFE | `net/neoforged/neoforge/client/gui/ConfigurationScreen$ConfigurationSectionScreen$Custom` | FCAP | class | 0/0 | 0 | 3 |
| 24 | SAFE | `net/neoforged/neoforge/client/gui/ConfigurationScreen$ConfigurationSectionScreen$Element` | FCAP | class | 0/0 | 0 | 5 |
| 25 | SAFE | `net/neoforged/neoforge/client/gui/ConfigurationScreen$ConfigurationSectionScreen$Filter` | FCAP | interface | 1/0 | 0 | 4 |
| 26 | SAFE | `net/neoforged/neoforge/client/gui/ConfigurationScreen$TooltipConfirmScreen` | FCAP | class | 0/0 | 0 | 2 |
| 27 | SAFE | `net/neoforged/neoforge/client/gui/ConfigurationScreen$TranslationChecker` | FCAP | class | 0/0 | 0 | 3 |
| 28 | SAFE | `net/neoforged/neoforge/client/gui/ConfigurationScreen$UndoManager` | FCAP | class | 0/0 | 0 | 5 |
| 29 | SAFE | `net/neoforged/neoforge/client/gui/ConfigurationScreen$UndoManager$Step` | FCAP | class | 0/0 | 0 | 4 |
| 30 | SAFE | `net/neoforged/neoforge/client/model/generators/ConfiguredModel` | aeronautics | class | 0/0 | 0 | 7 |
| 31 | SAFE | `net/neoforged/neoforge/client/model/generators/ConfiguredModel$Builder` | aeronautics | class | 0/0 | 0 | 6 |
| 32 | SAFE | `net/neoforged/neoforge/client/model/generators/ModelFile` | aeronautics | class | 0/0 | 0 | 9 |
| 33 | SAFE | `net/neoforged/neoforge/client/model/generators/MultiPartBlockStateBuilder` | aeronautics | class | 0/0 | 0 | 5 |
| 34 | SAFE | `net/neoforged/neoforge/client/model/generators/MultiPartBlockStateBuilder$PartBuilder` | aeronautics | class | 0/0 | 0 | 4 |
| 35 | SAFE | `net/neoforged/neoforge/client/model/generators/VariantBlockStateBuilder` | aeronautics | class | 0/0 | 0 | 3 |
| 36 | SAFE | `net/neoforged/neoforge/common/ModConfigSpec` | FCAP | class | 0/0 | 0 | 46 |
| 37 | SAFE | `net/neoforged/neoforge/common/ModConfigSpec$BooleanValue` | FCAP | class | 0/0 | 0 | 17 |
| 38 | SAFE | `net/neoforged/neoforge/common/ModConfigSpec$Builder` | FCAP | class | 0/0 | 0 | 13 |
| 39 | SAFE | `net/neoforged/neoforge/common/ModConfigSpec$Builder$1` | FCAP | class | 0/0 | 0 | 3 |
| 40 | SAFE | `net/neoforged/neoforge/common/ModConfigSpec$BuilderContext` | FCAP | class | 0/0 | 0 | 6 |
| 41 | SAFE | `net/neoforged/neoforge/common/ModConfigSpec$ConfigValue` | FCAP | class | 0/0 | 5 | 13 |
| 42 | SAFE | `net/neoforged/neoforge/common/ModConfigSpec$DoubleValue` | FCAP | class | 0/0 | 0 | 12 |
| 43 | SAFE | `net/neoforged/neoforge/common/ModConfigSpec$EnumValue` | FCAP | class | 0/0 | 0 | 5 |
| 44 | SAFE | `net/neoforged/neoforge/common/ModConfigSpec$IntValue` | FCAP | class | 0/0 | 0 | 11 |
| 45 | SAFE | `net/neoforged/neoforge/common/ModConfigSpec$ListValueSpec` | FCAP | class | 0/0 | 1 | 7 |
| 46 | SAFE | `net/neoforged/neoforge/common/ModConfigSpec$LongValue` | FCAP | class | 0/0 | 0 | 4 |
| 47 | SAFE | `net/neoforged/neoforge/common/ModConfigSpec$Range` | FCAP | class | 0/0 | 0 | 11 |
| 48 | SAFE | `net/neoforged/neoforge/common/ModConfigSpec$RestartType` | FCAP | enum | 0/0 | 0 | 11 |
| 49 | SAFE | `net/neoforged/neoforge/common/ModConfigSpec$ValueSpec` | FCAP | class | 0/0 | 2 | 9 |
| 50 | SAFE | `net/neoforged/neoforge/common/Tags` | aeronautics | class | 0/0 | 0 | 7 |
| 51 | SAFE | `net/neoforged/neoforge/common/Tags$Blocks` | aeronautics | class | 0/0 | 0 | 3 |
| 52 | SAFE | `net/neoforged/neoforge/common/Tags$Items` | aeronautics | class | 0/0 | 0 | 5 |
| 53 | SAFE | `net/neoforged/neoforge/common/TranslatableEnum` | FCAP | interface | 0/1 | 0 | 2 |
| 54 | SAFE | `net/neoforged/neoforge/entity/IEntityWithComplexSpawn` | aeronautics | interface | 2/0 | 1 | 2 |
| 55 | SAFE | `net/neoforged/neoforge/registries/DeferredHolder` | aeronautics | class | 0/0 | 0 | 1 |

---

## 4. BOMB 清单（R405 前 1 个；当前 0 个）

### 4.1 `net/neoforged/neoforge/common/extensions/ILevelReaderExtension`

| 项 | 内容 |
|---|---|
| 定义在 | `aeronautics-fabric-0.1.0-port.26.3.jar`（**垫片**，不是 FCAP） |
| 形态 | `public interface`，无父接口；**唯一方法** `default boolean isAreaLoaded(BlockPos,int)`，方法体经字节码摘要确认是 `return true`（`iconst_1; ireturn`） |
| 实现者 | **0**（全 71 jar 的 super/interfaces 闭包；无 mixin 类声明它；无 lambda 目标） |
| 引用站点（唯一外部） | `dev/simulated_team/simulated/util/SimLevelUtil#isAreaActuallyLoaded(Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;I)Z`：`SimLevelUtil.java:16`，`pc=14 checkcast` → `pc=19 invokeinterface isAreaLoaded(BlockPos,I)Z`；**没有 instanceof 守卫** |
| 触发条件（已实测，`docs\block-render-sweep.md` F3） | 放下 `simulated:laser_pointer` → `LaserPointerBlockEntity.tick:70` → 本方法 → `ClassCastException: ServerLevel cannot be cast to ILevelReaderExtension` → `ReportedException: Ticking block entity` → 服务器停、客户端退（组 T，不进画面也崩） |
| 为什么静态可判死 | 接口零实现者 + 强转无守卫 ⇒ 只要执行到 `pc=14` 必抛；与实测崩溃栈完全吻合 |

**修法（按推荐度）：**

**A. classtweaker（推荐，见第 7 节）**：一行

```
classTweaker v1 official
transitive-inject-interface net/minecraft/world/level/LevelReader net/neoforged/neoforge/common/extensions/ILevelReaderExtension
```

`LevelReader` 在 26.3 是接口，且 `ServerLevel → Level → LevelAccessor → CommonLevelAccessor → LevelReader`、`ClientLevel → Level → …`（已用 26.3.jar 类头逐级核对），**注入接口本身即可让全部实现者继承它**，无保护强转立即合法。零字节码改动，还能覆盖未来所有对 `LevelReader` 的同类强转。

**B. mixin（等效备选，aero-fixer 正在做）**：`@Mixin(Level.class) … implements ILevelReaderExtension {}` + 挂进 `simulated.mixins.json`。需要改 class + mixin 配置；只覆盖 `Level` 及其子类（`ServerLevel/ClientLevel` 够用，但不覆盖别的 `LevelReader` 实现者）。

**C. 纯字节码（不推荐）**：改 `SimLevelUtil` 的 5 条指令为 `goto`（等价恒 true），只修一个调用点。

**⚠ 语义修正（可选，但建议同轮做）**：NeoForge 26.3.x 真身（`ILevelReaderExtension.java:19-20`）是
`return self().hasChunksAt(center.offset(-r,-r,-r), center.offset(r,r,r));`，
我们垫片是 `return true`。A/B 修完后不再崩，但仍会「相信未加载区块已加载」。若要语义对齐，把垫片方法体改成上面的 `hasChunksAt`（26.3 的 `LevelReader` 确认有 `hasChunkAt`/`hasChunksAt` 共 5 个 default 重载（含 `hasChunksAt(BlockPos,BlockPos)Z`））；否则接受「恒 true」并在交付说明标注。
来源：<https://raw.githubusercontent.com/neoforged/NeoForge/26.3.x/src/main/java/net/neoforged/neoforge/common/extensions/ILevelReaderExtension.java>

### 4.2 R405 后的复核（当前 `mods-stable`）

Lead 已用**两条一起**修掉（见台账 R405 / `docs\fix-laser-pointer.md`）：

1. 新增 mixin 类 `dev/simulated_team/simulated/mixin/level/LevelILevelReaderExtensionMixin`，class 头声明 `implements ILevelReaderExtension`（本审计按「mixin 类声明实现」识别为实现者，登记在 `census.json` 的 `implementers.mixin_classes`）；
2. 垫片 `isAreaLoaded` 方法体从 `return true` 改为 `hasChunksAt(...)`（本审计方法体摘要：`return true` → `returns-value(calls)`，与 NeoForge 26.3.x 源码一致）。

重跑结果（`census.json` 当前版）：**BOMB 0 / RISK 5 / SAFE 50**；`ILevelReaderExtension` 判定变为 SAFE（理由：有已配置的 mixin 实现者），`SimLevelUtil` 的 `checkcast` 仍在（现在合法）。本节的修法 A/B/C 仍有价值：A（tweaker）是不依赖 mixin 的**系统性**路线，可在未来新垫片接口上复用。

---

## 5. RISK 清单（5 个，全部集中在同一个死类）

| 类型 | 缺失成员/用法 | 引用 class | 可达性 |
|---|---|---|---|
| `net/neoforged/bus/api/SubscribeEvent` | 仅**注解** | `vectorwing/farmersdelight/integration/launchpad/LaunchpadClientEvents` | **不可达**（见下） |
| `net/neoforged/fml/common/EventBusSubscriber` | 仅**注解** | 同上 | 不可达 |
| `net/neoforged/neoforge/client/event/RegisterGuiLayersEvent` | `registerAbove(Identifier,Identifier,GuiLayer)V` ×2（:16/:17） | 同上 | 不可达 |
| `net/neoforged/neoforge/client/gui/GuiLayer` | 方法描述符 + lambda 目标（`registerAbove` 的第 3 参） | 同上 | 不可达 |
| `net/neoforged/neoforge/client/gui/VanillaGuiLayers` | `getstatic PLAYER_HEALTH/FOOD_LEVEL`（:16/:17） | 同上 | 不可达 |

**为什么判「不可达」（静态证据）：**

1. 扫描 71 jar 全部 class 的常量池：出现 `LaunchpadClientEvents` 这个名字的**只有它自己的 class 文件**（self-reference），没有任何别的类引用它；
2. 不在 `FarmersDelight/fabric.mod.json` 的 entrypoints 里（main/client/datagen/jei/rei/…都没有它），也不在 `farmersdelight.mixins.json` 的 mixins/client 列表里；
3. 该 jar 内**资源文件**（json/其它）没有出现该类名；唯一提到 "launchpad" 的是 `fabric.mod.json`；
4. 它是 NeoForge 事件总线风格的回调类（`@EventBusSubscriber`/`@SubscribeEvent`），Fabric 端没有对应扫描器 ⇒ 不会被动加载。

⇒ 当前是死代码；只有反射/将来恢复 NeoForge 事件系统时才会炸。**不阻塞交付，低优先**（建议：删除该类，或补 5 个 no-op stub；但不要为此引入 NeoForge GUI 语义）。

---

## 6. 分 jar 视角

| jar | 引用 net.neoforged 的 class（细口径） | 自己定义的 net.neoforged 类型 | 结论 |
|---|---:|---:|---|
| ForgeConfigAPIPort（FCAP） | 47 | 36 | 真移植：`ModConfigSpec` 家族 / `ConfigTracker` / `ConfigurationScreen` / `TranslatableEnum`。成员解析 **0 缺失**，全 SAFE |
| aeronautics | 34（R405 前）/ 35（当前，新增 1 个 mixin class） | 14（全部垫片） | 只有 `ILevelReaderExtension` 是 BOMB；其余是 datagen 模型生成器（4 个类型，仅被 datagen 类引用）、`Tags/Tags$Blocks/Tags$Items`、`Dist/OnlyIn` 注解、`DeferredHolder`（无外部引用）、`IEntityWithComplexSpawn`（1 个实现者 `GustEntity`） |
| sable | **21** | **0** | 21 个 class **全部**只引用 FCAP 的 `ModConfigSpec`（+ `$BooleanValue/$DoubleValue/$IntValue/$EnumValue/$Range/$ValueSpec/$Builder`）⇒ **0 炸弹**；sable 自己不带任何 net.neoforged 垫片 |
| FarmersDelight | 1 | 0 | 死类 `LaunchpadClientEvents` ⇒ 第 5 节的 5 个 RISK |

**sable 的 21 个 class（核对用）**：`SableClientConfig`、`SableConfig`、`SableServerConfig`、`SubLevelSettingsScreen`、`ServerSubLevelContainer`、`ChunkBorderRendererMixin`、`ServerConnectionListenerMixin`、`ClientboundSableUDPActivationPacket`、`SableUDPServer`、`ServerSubLevel`、`SubLevelHoldingChunkMap`、`SubLevelStorage`、`PhysicsChunkTicketManager`、`MouseHandlerMixin`、`ClientSableInterpolationState`、`ServerboundPunchSubLevelPacket`、`SubLevelSerializer`、`SubLevelTrackingSystem`、`PhysicsConfigData`、`SubLevelHeatMapManager`、`SubLevelPhysicsSystem`。

---

## 7. 扩展接口 × NeoForge `injected-interfaces.json` × classtweaker 可行性

### 7.1 我们 jar 里实际「声明」的 net.neoforged 接口（6 个）

| 接口 | 定义在 | 方法（抽象/default） | 具体实现者 | 说明 |
|---|---|---|---:|---|
| `fml/config/IConfigSpec` | FCAP | 4 / 0 | 2 | 配置 API 契约，FCAP 自带实现 |
| `fml/config/IConfigSpec$ILoadedConfig` | FCAP | 2 / 0 | 1 | 同上 |
| `neoforge/client/gui/ConfigurationScreen$…$Filter` | FCAP | 1 / 0 | 0 | 函数式接口，由 lambda 实现（`invokedynamic` 目标） |
| `neoforge/common/TranslatableEnum` | FCAP | 0 / 1 | 0 | 枚举翻译 key 接口；FCAP 内部强转有 `instanceof` 守卫 ⇒ SAFE |
| `neoforge/common/extensions/ILevelReaderExtension` | aeronautics | 0 / 1 | 0 | **唯一 BOMB**；唯一方法是 default，体 = `return true` |
| `neoforge/entity/IEntityWithComplexSpawn` | aeronautics | 2 / 0 | 1（`GustEntity`） | 抽象方法已被实现；调用语义在 Fabric 上是否生效未判（不崩） |

> 另外 `distmarker/OnlyIn`、`distmarker/Dist` 是注解/枚举（不是扩展接口）。

### 7.2 能对上 NeoForge 官方注入清单吗？——**能，但本包只有 1 条有效**

NeoForge 用 `META-INF/injected-interfaces.json` 在运行时把「原版类 → 扩展接口」注入。**26.3.x 分支**（不是 1.21.x，数字更准）实测：

- **115** 个 target、**116** 条映射；其中 **113** 条指向 `net/neoforged`（另 3 条是 vanilla→vanilla）；
- 115 个 target 里 **113** 个在 MC 26.3.jar 中存在；**2** 个缺失（`IntrinsicHolderTagsProvider$IntrinsicTagAppender`、`DeadBushBlock`，26.3 已改名/删除）；
- **本包 classpath 上只存在 1 个** 被映射的 NeoForge 接口：`ILevelReaderExtension`；
- 它对应的映射正是 `net/minecraft/world/level/LevelReader → ILevelReaderExtension`（`generated.classtweaker` 已生成）。

**估算收益**：R405 前 1 个 BOMB → 1 条 tweaker **全覆盖（1/1，100%）**；R405 后当前 BOMB = 0，tweaker 的价值转为「防止未来同类垫片接口复发 + 为剩余 39 个待移植 mod 兜底」。
**不能盲注全量**：其余 **110** 条映射的接口类在本包不存在。Fabric 的 `InterfaceInjectionClassVisitor` 会把这些接口名写进目标类的 interfaces 数组；JVM 加载该类时要解析 superinterface ⇒ **`NoClassDefFoundError`**，等于把一个炸弹换成一排炸弹。Kilt 能整份注入是因为它自己打包了整套 `net.neoforged` 类；我们不是。

Kilt 先例（可直接参考，注意它是 dev 用的 `named` 命名空间）：
- <https://github.com/KiltMC/Kilt/blob/version/1.21.1/tweakers/injections/neoforge.classtweaker>（文件头注释写明 *automatically generated from their injected-interfaces.json*，其中就有 `transitive-inject-interface net/minecraft/world/level/LevelReader net/neoforged/neoforge/common/extensions/ILevelReaderExtension`）
- Kilt 的 `fabric.mod.json` 用 `"accessWidener": "kilt.classtweaker"` 声明（class tweaker 沿用 accessWidener 这个键）。

### 7.3 本环境可行性核对（都已实测，不是推断）

| 项 | 结论 | 证据 |
|---|---|---|
| Fabric Loader 版本门槛 | **满足**：0.18.0+ 才支持 class tweaker；本包 loader **0.19.5** | `work/aero-port/libs26/fabric-loader-0.19.5.jar` 内含 `impl/lib/classtweaker/{api,reader,classvisitor}`，`ClassTweakerReaderImpl` 字符串表含 `classTweaker`、`inject-interface`、`transitive-inject-interface`、`accessWidener` |
| 命名空间 | 用 **`official`** | aeronautics 自带的 `aeronautics-fabric.accesswidener` 头就是 `accessWidener v2 official`，且该 jar 正常运行；launcher 也传 `-Dfabric.development=false` |
| target 可注入性 | `LevelReader` 是 vanilla 接口（vanilla class 才允许作为 target） | 26.3.jar 类头 `access=0x0601` |
| 注入后可达性 | `ServerLevel → Level → LevelAccessor → CommonLevelAccessor → LevelReader`（`ClientLevel` 同理） | 26.3.jar 逐级类头解析（`hierarchy.py`/`chain.py`） |
| 接口在 classpath | ✓ `ILevelReaderExtension` 在 aeronautics jar 内 | `census.json` |
| Loom ≥1.12 | 只影响 **开发期** 编译/验证；我们是**重打生产 jar**，不经过 Loom | Fabric 官方文档 |

### 7.4 落地建议

**推荐：独立小 mod 承载 tweaker（不动 aeronautics 一个字节）**

```
sky262-neosupport.jar
├─ fabric.mod.json
│   {
│     "schemaVersion": 1,
│     "id": "sky262_neosupport",
│     "version": "1.0.0",
│     "name": "Skylands 26.3 NeoForge interface tweaks",
│     "environment": "*",
│     "accessWidener": "sky262-neosupport.classtweaker"
│   }
└─ sky262-neosupport.classtweaker     ← 就是 g23a/generated.classtweaker（当前 1 行）
```

- 优点：aeronautics 保持原 SHA；不依赖 mixin 配置；后续每移植一个带 NeoForge 垫片接口的 mod，重跑生成器往这个文件里加行即可。
- 代价：mods-stable 从 **71 → 72** jar（交付台账要同步）。

**备选：塞进 aeronautics 现有 AW**：一个 mod 只能声明一个 `accessWidener`，所以只能把 `aeronautics-fabric.accesswidener` 的头从 `accessWidener v2 official` 改成 `classTweaker v1 official` 再追加 1 行（class tweaker v1 是 v2 的超集，loader 两者都解析；但这条路径要重验该文件里所有原有 directive）。**不推荐**：改动面比 A 大，收益一样。

**风险清单（做 tweaker 前必须知道）**

1. **loader 版本**：<0.18 会不认 `classTweaker` 头 ⇒ 本包 0.19.5 没问题；若将来降级 loader 要回退到 mixin。
2. **命名空间写错**（写成 `named`/`intermediary`）⇒ 启动期抛解析/重映射错误。本包用 `official`。
3. **接口必须在 classpath**：生成器必须按「本包已定义的类」过滤（`gen_classtweaker.py` 已实现）；**绝不**直接拷 NeoForge 整份 JSON。
4. **target 必须存在且是 vanilla**：生成器已按 26.3.jar 过滤（当前丢掉 2 条不存在的 target）；缺失 target 默认被 loader 忽略，但白写。
5. **重复注入**：若同时上 mixin `implements` 方案，二者都生效（冗余但通常无害）；建议**二选一**，A/B 时只带一个。
6. **行为语义**：注入只让强转合法，`isAreaLoaded` 仍返回 `true`（垫片体）⇒ 见第 4 节语义修正。
7. **验证**：先放 stage 副本跑标题（看 loader 日志里 class tweaker 有无 `Ignoring …`/解析报错），再按 verifier 的 A/B 流程验 laser_pointer；**不要**直接改 mods-stable。
8. **生成物要随包重生成**：新移植的 mod 若自带 `net.neoforged` 扩展接口，重跑生成器即可；输出应只有「接口真实存在」的行。

**生成器**：`work/run26/port/g23a/gen_classtweaker.py`（本审计新增，已跑通）

```
python gen_classtweaker.py                 # 默认 26.3.x JSON + mods-stable + 26.3.jar
#   -> generated.classtweaker（当前 kept 1 / 113）
#   dropped: 110 接口不在本包 classpath / 2 target 不在 26.3 / 3 非 net.neoforged
```

---

## 8. 方法学与置信度

**静态判了什么（可复现）**

1. **定义**：71 jar（含嵌套 jar ≤3 层）全部 class 头 → `{name, super, interfaces, flags, methods}`；`net/neoforged` 类型共 50 个有定义（FCAP 36 / aeronautics 14），5 个只被引用、无定义。
2. **实现者**：以 `super/interfaces` 为边求**传递闭包**，区分「具体实现者（非接口、非抽象）」/「mixin 类（按 `*.mixins.json` 的 package+类名与 `@Mixin(targets/value)` 确认）」。
3. **引用站点**：逐方法 walk 字节码（完整 opcode 长度表，含 `tableswitch/lookupswitch/wide`），记录 `checkcast/instanceof/new/anewarray/invokestatic/invokevirtual/invokespecial/invokeinterface/get*/put*/ldc`，并用 `LineNumberTable` 映射行号。
4. **守卫判定**：同方法内同类型 `instanceof` + 同行或「条件跳转越过强转」⇒ 视为受保护（解决 `TranslatableEnum` 这类先 `instanceof` 后 `checkcast` 的假阳性）。
5. **lambda**：`invokedynamic` 调用点描述符返回类型为接口 ⇒ 视为 LambdaMetafactory 生成的实现者（解决 `Filter` 这类函数式接口的假阳性）。
6. **成员解析**：对每个 `invoke*/field` 引用点，在该垫片类及其继承链里按 `name+desc` 查；链尾到 `java/lang/Object` 时按 Object 成员表判定。**本次全部 55 个类型 0 个成员缺失**。
7. **注解**：解析 `RuntimeVisibleAnnotations`；注解类型另作「仅注解」处理。

**没判什么（不要把结论当实测）**

- **没有运行期验证**：BOMB 的「必炸」是静态推断（但与 `docs\block-render-sweep.md` F3 的实测崩溃栈逐行吻合，置信度极高）；RISK 的「不可达」是静态可达性推断（无 CP/entrypoint/mixin/资源引用），反射/未来入口不在覆盖内——**这是 RISK 而不是 SAFE 的原因**。
- **mixin 实际是否应用**未验（只看配置里有没有声明）；被 mixin 织入的接口实现按「声明即算」处理，已单独标注 `mixin_classes`。
- **Fabric API 的 mixin 织法**、运行期动态代理、`Class.forName` 字符串加载、`ServiceLoader` 未覆盖。
- **注解 retention** 未区分（`@SubscribeEvent` 这类若为 RUNTIME 且有人反射扫，会提前炸）。
- **多版本 jar**（`META-INF/versions/`）跳过；嵌套 jar 只到 3 层（本包未发现更深）。
- 只扫 `mods-stable` 71 jar；Minecraft/Fabric API/loader 的类不在「定义」搜索面内（`net.neoforged` 不会在那里，但成员解析遇到 MC 父类时返回 unknown）。
- 本审计只覆盖「**类型级**」炸弹；**扩展方法调用在 MC 类上的站点**（如 `level.xxx()` 这类 owner 是 MC 类、方法来自 extension interface 的调用）属于成员级地雷，归 `tools/scan_landmines.py` / `docs/api-landmines.md` 管，本次未合并。

---

## 9. 下一步建议（按「成本 × 崩面」排序）

| 优先 | 动作 | 成本 | 覆盖 | 备注 |
|---|---|---|---|---|
| **P0（R405 前）** | 加 1 行 classtweaker（`LevelReader → ILevelReaderExtension`），放独立小 mod | 极低（1 文件 + 1 mod） | R405 前 BOMB **1/1**；作为不依赖 mixin 的系统性兜底 | R405 的 mixin 修法已实测通过；tweaker 与它**二选一**即可（第 7.4 节风险 5），若走 tweaker 需重新 A/B |
| P1 | （可选）把垫片 `isAreaLoaded` 体改成 `hasChunksAt(...)` 对齐 NeoForge 语义 | 低（改 aeronautics 1 个方法体） | 行为正确性 | 不改也不崩；台账已记「恒 true ⇒ 可能读未加载区块」的隐患 |
| P1 | 若不想引入 loader 特性：走 mixin（aero-fixer 任务） | 低 | `Level` 及其子类 | 与 P0 二选一 |
| P2 | 把 `gen_classtweaker.py` 固化进移植流程：每新增含 net.neoforged 垫片的 mod 后重生成，并**按 classpath 过滤** | 低（脚本已有） | 未来同类炸弹 | 不要用整份 113 条 |
| P3 | 清掉 FD 死类 `LaunchpadClientEvents`（或补 5 个 no-op stub） | 低 | 5 个 RISK 归零 | 当前不可达，不阻塞 |
| P4 | 把「成员级」extension 调用（owner 是 MC 类）纳入下一轮扫描口径，与 `scan_landmines` 结果合并 | 中 | 未覆盖的隐性地雷 | 本次 0 个成员缺失只代表「已触达的 net.neoforged 类型」 |

---

## 10. 复现

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g23a

python census.py             # 全量静态普查 -> census.json（约 30 s，纯 python，不需要 java）
python tweaker_analysis.py   # 对照 NeoForge 26.3.x 注入清单 -> tweaker.json
python gen_classtweaker.py   # 生成 class tweaker（按本包 classpath 过滤）-> generated.classtweaker
python summary.py            # 人读总表（stdout）
```

- 输入：`work\run26\mods-stable`（71 jar）；`work/run26/port/g23a/injected-interfaces-neoforge-26.3.x.json`（从 NeoForge `26.3.x` 分支下载，见第 11 节）；`%APPDATA%\.minecraft\versions\26.3\26.3.jar`（仅用于「target 是否存在」与继承链核对）。
- 输出：`census.json`（55 行/类型，含定义、形态、方法表、实现者、引用站点、判定与理由）、`tweaker.json`、`generated.classtweaker`。
- 脚本清单：`census.py`（主解析器）、`tweaker_analysis.py`、`gen_classtweaker.py`、`summary.py`/`make_snippets.py`（展示），以及一次性核对脚本 `hierarchy.py`、`chain.py`、`check_loader.py`、`reader_tokens.py`、`aw_check.py`、`fd_refs.py`、`per_jar_counts.py`。

---

## 11. 附件与校验和（本审计基线）

| 项 | SHA-256 |
|---|---|
| `aeronautics-fabric-0.1.0-port.26.3.jar`（当前，R405 后） | `B0A9383FF012EA452C0CDECD693D9F821075C21C362731CD98F9E98E9BABECD6` |
| `aeronautics-fabric-0.1.0-port.26.3.jar.bak-laserpointer`（**审计主基线**，R405 前） | `2DF06E769FC15210BD6DD4E907F5ECCB15175CA8FF88560E3A05256E6D28BD2B` |
| `sable-fabric-26.3.jar` | `54ADAAE12517E4B36DB2D424B9086102048137966D99745B4BE73B52F03E229B` |
| `ForgeConfigAPIPort-v26.3.1-mc26.3.x-Fabric.jar` | `9D0CA9DC75C0A191D12B013DC85E8A27915DA08B63B5730B490075542AEE0B09` |
| `FarmersDelight-26.3-3.6.28+refabricated.jar` | `791A94B47211D75EC956BFBCD49FC503938A92C075A0D75782A7ADE05C48CA24` |
| `injected-interfaces-neoforge-26.3.x.json` | `45E0A6D5FABB16E9719F75501929F87F543CC26B601B404FA80226C0DD9140E0` |
| `census.json`（生成物，当前 R405 后） | `57AAD32950A992E840C24CA80486F853838AB67AEB995FEBA28FAA4B911BF254` |
| `census-pre-r405.json`（生成物，审计主基线） | `7EACEDE1F7DD85D5A73C95B018FFACDF78AC996959B9D23AA099F916FE9718B8` |
| `tweaker.json`（生成物，当前） | `9CBB8678BB25E04E1487B499988B7561FB91EFE052074F7AA92C521DF4FB95C3` |
| `generated.classtweaker`（生成物） | `3FFFAE8EB6689AE98C936BEEB0013C2A76DEBCEB8CD058BD5BBCE6E3C6F0B6D6` |

`injected-interfaces-neoforge-26.3.x.json` 来源：
`https://raw.githubusercontent.com/neoforged/NeoForge/26.3.x/src/main/resources/META-INF/injected-interfaces.json`

参考：
- Fabric 官方 class tweaker 文档：<https://docs.fabricmc.net/develop/class-tweakers/>
- NeoForge 26.3.x `ILevelReaderExtension.java`：<https://github.com/neoforged/NeoForge/blob/26.3.x/src/main/java/net/neoforged/neoforge/common/extensions/ILevelReaderExtension.java>
- Kilt 生成物：<https://github.com/KiltMC/Kilt/blob/version/1.21.1/tweakers/injections/neoforge.classtweaker>
