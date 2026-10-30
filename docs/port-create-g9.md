# g9 —— Create 附属（26.3 Fabric）移植诊断报告

> 轮次：g9（接 g6 interiors / g7 create-framed / g8 delights 的流水线）
> **结论先说：本轮 0 个 mod 进入 `mods-stable`（仍是 65 jar）。**
> 唯一「离 26.3 最近」的目标 `create-enchantment-industry` 2.5.2（26.1.2 构建）**不是改改名能过的**，
> 它牵出两个 26.1.2 世代的 mod（自身 261 类 + 依赖 `create-dragons-plus` 150 类），
> 卡点是 **MC 26.1.2 → 26.3 的一批 API 重构**（不是 Create 版本）。
> 本轮已把两个 mod 从 **391 / 522 错**压到 **88 / 201 错**，并留下可复现的工具链与逐族修法。
> **没有把「只过标题」说成完成**：本轮一个都没启动过游戏（没有 staging 测试，因为没到能测的程度）。

---

## 0. 结论速览

| mod（真实 slug / project id） | 最近的 Fabric 构建 | 本轮结果 | 卡点 |
|---|---|---|---|
| **create-enchantment-industry**（`JWGBpFUP`） | **26.1.2**（`2.5.2-c`，文件名 `create-enchantment-industry-fly-26.1.2-2.5.2-c.jar`） | ❌ 未完成（**201 错**，522 起） | 见 §2：MC 26.1.2→26.3 重构；另需 `create-dragons-plus` |
| **create-dragons-plus**（`dzb1a5WV`，**EI 的强依赖**） | 26.1.2（`1.11.8`） | ❌ 未完成（**88 错**，391 起） | 同上；成对移植，单靠 EI 无法运行 |
| **create-aeroworks**（`P26k79kP`） | **没有 Fabric 构建**（12 个版本全是 NeoForge） | ⛔ 不做 | 任务表里的「1.21.1 Fabric」**是错的**，同「需 NeoForge 垫片」那一档 |
| createaddition（`kU1G12Nn`） | 1.20.1（`fabric-1.20.1-1.3.4`） | ⏳ 未开始 | 1.20.1→26.3，跨 Create 0.5→6.0 |
| copycats（`UT2M39wf`） | 1.20.1（`3.0.10+mc.1.20.1-fabric`） | ⏳ 未开始 | 同上 |
| escalated（`LyOBYG8Q`） | 1.20.1（`1.2.1`） | ⏳ 未开始 | 同上（台账记 542 错） |
| create-jetpack（`UbFnAd4l`） | 1.20.1（`4.4.2-fabric`） | ⏳ 未开始 | 纯 Kotlin（要 fabric-language-kotlin，已在 stable）+ 1.20.1 |
| create-railways-navigator（`Dq3STxps`） | 1.20.1（`0.10.0-C6`） | ⏳ 未开始 | 同上，另需 railways 库 |
| create-connected / power-loader / mechanical-extruder / central-kitchen | 无 Fabric | ⛔ 不做 | 需 NeoForge 垫片 |

**交付物 `work/run26/mods-stable`：65 jar → 65 jar（无变化，未 promote 任何东西）**
`work/run26/watch` 全程只读，未同步、未改动；`mods-stable` 里没有任何 jar 被改（也没有新增 `.bak`）。

---

## 1. 任务表的三处订正（都实测）

1. **`create-enchantment-industry` 的 26.1.2 构建是 ZurrTum「-fly」变体**
   （`fabric.mod.json` 里 `depends.create = ">=6.0.9-4 <6.1.0"`、`depends.create_dragons_plus = "1.11.4-p1"`），
   所以它**必须**配 `create-dragons-plus`；而 DP 的所有 26.x 构建同样要求 `create-fly >= 6.0.9-4`。
2. **所有 26.x 构建都要求 Create 6.0.9-4+**（2.5.1 / 2.5.2 / 2.5.2-b / 2.5.2-c 四个版本都一样）
   ⇒ 任务里说的「改用更低版本」**不存在**；再往下只有 1.21.11 / 1.20.1 构建。
3. **`aeroworks` 没有 Fabric 构建**（`P26k79kP` 的 12 个版本 loaders 全是 `neoforge`）
   ⇒ 「高优先」这一档实际为空。

另外：任务里报「项目不存在」的那批 slug，真实 project id 已从原包 `modrinth.index.json` 反查出来，见
`work/run26/port/g9/_pack/modrinth.index.json`（114 files，含每个 jar 的 sha1 + 下载 URL）。
本次用到的映射：`createdeco=sMvUb4Rb`、`createpropulsion=ApkoHNO9`、`createdieselgenerators=ZM3tt6p1`、
`createliquidfuel=sH9tXU9f`、`createoreexcavation=ResbpANg`、`aerocopycats=wjpmYU1u`、
`mechanicals=ProvjTA7`、`tfmg=USgVjXsk`、`create-submarine=mva5q4qZ`、`sliceanddice=GmjmRQ0A`、
`design-n-decor=x49wilh8`。
（`g9/_mr.py` 与 `g9/_deps.py` 都是按 **project id** 查，不再靠 slug 猜。）

---

## 2. `create-enchantment-industry` 的真实卡点

### 2.1 `FlowableFluid$Still` 确实不存在（任务里那个已知障碍，已确认）

```
javap -p -cp create-fly-26.2-6.0.9-2-26.3-patched.jar \
      com.zurrtum.create.infrastructure.fluids.FlowableFluid
→ public abstract class FlowableFluid extends WaterFluid   // 没有 entry 字段、没有嵌套 Still/Flowing
```
6.0.9-2 里同样的东西叫 `FluidEntry$Still` / `FluidEntry$Flowing`（**private 内部类，构造器 private**），
6.0.9-4 才把它们搬到 `FlowableFluid` 名下并公开。EI 的 `CEIFluids` 直接
`new FlowableFluid.Still(fluidEntry)` / `new FlowableFluid.Flowing(fluidEntry)`。

**已做的垫片（可用，2 类、编译 0 错）**：
`g9/shim/src/com/zurrtum/create/infrastructure/fluids/FlowableFluid$Still.java` / `...$Flowing.java`
—— 按 6.0.9-2 的 `FluidEntry$Still/$Flowing` 反编译结果（`g9/_dec/out/.../FluidEntry.java`）原样重建，
类名故意写成 `FlowableFluid$Still` 让 **binary name 与 6.0.9-4 一致**，构造器改 public。
产物：`g9/_shim/fluid-compat.jar`（可作独立 mod jar 放进 staging，不必改 create）。

> 检查过：EI / DP 对 Create 的**类级**缺口只有这 2 个类
> （`g9/_scanrefs.py` 能一次扫出来；把 create + 自身 + DP 都放进依赖集后 MISSING=2）。
> 也就是说 **Create 版本不是主要矛盾** —— 主要矛盾是下面这条。

### 2.2 主要矛盾：MC 26.1.2 → 26.3 的 API 重构

两个 mod 的源码是 **26.1.2 官方名**（不是 intermediary，也不是 1.21.1），
所以 `g8/_rewrite26.py` + `map_121_263.json`（1.21.1→26.3）**帮不上忙**，只能对着 26.3.jar 逐族改。

实测错误轨迹：

| mod | 首次 javac | 去 JEI + 机械修正后 | 当前 |
|---|---|---|---|
| create-dragons-plus 1.11.8 | **391** | 173 | **87** |
| create-enchantment-industry 2.5.2-c | **522** | 242 | **202** |

**已解决/已绕开的族（可复用，脚本都在 `g9/`）**：

| 族 | 26.1.2 | 26.3 | 修法 |
|---|---|---|---|
| 进度触发器 | `advancements.CriterionTrigger` + `CriterionTrigger.Listener` + `PlayerAdvancements#addPlayerListener` | `advancements.triggers.CriterionTrigger<T>` **只剩 `codec()` + `createCriterion(T)`**；监听改成 `PlayerAdvancements#getTriggerMapForType` | **降级为 codec-only**（仍注册、JSON 仍能解析，触发不再派发）。`CDP/CEI` 的 `StatTrigger`/`BuiltinTrigger` 已重写 |
| 进度条件类 | `advancements.Criterion` / `criterion.MinMaxBounds` | `advancements.triggers.Criterion` / `advancements.predicates.MinMaxBounds` | 改 import（`_fix_dp.py`） |
| 战利品数字 | `providers.number.NumberProvider` / `ConstantValue.exactly(float)` | 拆成 `ints/floats` 的 `ContextIntProvider`；`LootPool.Builder#setRolls` 吃 `Holder<ContextIntProvider>` | `setRolls(Holder.direct(new ConstantValue(1)))` |
| 实体类型常量 | `EntityType.SHEEP` | **`EntityTypes.SHEEP`**（新类） | 改引用（`_fix_dp2.py`） |
| 颜色方块/染料 | `Items.RED_WOOL` / `Blocks.LIME_CONCRETE` / `Items.LIME_DYE` | **`ColorCollection`**：`Items.WOOL.red()` / `Blocks.CONCRETE.lime()` / `Items.DYE.lime()` | 改引用 |
| `BlockPos#getBottomCenter` | 有 | 删 | `Vec3.atBottomCenterOf(pos)` |
| `Block#item` | 公开字段 | private | `asItem()` |
| 方块实体渲染器 | `BlockEntityRenderers.register(...)`（public） | **private** | 用 Fabric `BlockEntityRendererRegistry.register(type, provider)` |
| Fabric 附件 | `LivingEntity#getAttached/setAttached`（Entity 直接实现 `AttachmentTarget`） | `Entity` **不再声明** `AttachmentTarget`（运行期由 mixin 注入） | 编译期要 `((AttachmentTarget) entity).getAttached(...)` |
| 配方访问 | `level.recipeAccess().getSynchronizedRecipes()` | `RecipeAccess` 只剩 `propertySet`/`stonecutterRecipes`；`RecipeMap.create` 改吃 `HolderLookup<Recipe<?>>` | **尚未定案**（见 §2.3） |
| 网络码流 | `StreamCodec<RegistryFriendlyByteBuf, T>` 泛型 | CFR 丢泛型后 `Object` 传参 | `_auto_cast.py` 批量去 `(Object)` |
| JetBrains 注解 | `org.jetbrains.annotations.*` | 不在 classpath | `g9/anno` 编译期垫片 → `_shim/anno-stub.jar`（CLASS 保留，运行期缺席无影响，不打包） |

**`g9/_auto_cast.py` 是这轮最省力的工具**：CFR 在类型推断失败时会保守插 `(Object)`/`(Comparable)`，
反而让重载解析失败；脚本按 javac 错误行把它们删掉，两轮共修掉 **136 处**（DP 64 + EI 95/41）。

### 2.3 还剩的（EI 201 / DP 88）——按族

EI（201）：
- `cannot find symbol` 56：一半是**嵌套类前向引用**（见下）、一半是 26.1.2 里还有的类在 26.3 被搬走
  （`advancements.Criterion`、`ValueOutput.store` 家族）
- `mulPose(Quaternionfc)` 12 —— `PoseStack` 的姿态 API 变了（要查 26.3 的 `PoseStack`）
- `inference variable R has incompatible bounds` 11 —— CFR 泛型丢失 + mixin 签名
- `placeItemBackInInventory(ItemStack)` 8 —— 26.3 改了签名（要吃 `ServerPlayer`/`ItemStack`？待查）
- `add(Object[])` 6、`SnapshotParticipant` 构造器 3、`ExperienceOrb.count` private 3
- **嵌套类型前向引用**（EI 3 处 / DP 1 处，已修）：CFR 把嵌套 `record/class` 放在文件末尾，
  而 **`implements I<Inner>` 子句不在类体作用域内**，非限定 `Inner` 会报 `cannot find symbol`。
  实测最小复现：`class B implements I<PD> { static class PD {} }` **不通过**，
  `class B implements I<B.PD> { ... }` 通过（`g9/_t/a/B.java` 与 `A.java`）。
  **修法**：写全限定名（`g9/_fix_fwd.py` 已自动做掉这 4 处）。

DP（88）：
- 上面那些 EI 族的大部分都有少量（`ParticleData`、`Output`/`TabVisibility` protected、`CDPFluidEntry` 泛型、
  `CDPPonderScenes` 的 `List<BucketItem>→List<Item>`、ponder 的 `Instance→TransformedInstance` 已定位为
  **`stealInstance((Instance)head)` 的 `(Instance)` 强转多余**，去掉即可 5 处）
- `CauldronInteractions.newDispatcher(String)` private（create 6.0.9-2 与 6.0.9-4 的 API 差异，唯一一处
  非 MC 的硬缺口）
- `FeaturesConfig` 的 "flexible constructors"（Java 25 预览特性；CFR 把 `super(...)` 放到了语句之后）
- `RecipeAccess` / `RecipeMap.create`（同上）

**结论：EI+DP 是「一个 400+ 错、跨 15 个 API 族的成对移植」，不是一个下午能收尾的量；
按 g8 的节奏（单 mod 39 处语义修改 ≈ 一个完整轮次）估，**再要 1.5–2 个完整轮次**才可能到能进世界。

---

## 3. 本轮产出的可复用资产（下一轮直接接）

```
work/run26/port/g9/
  _pack/modrinth.index.json   原包 114 个 jar 的 sha1/URL（真实 slug 靠它反查）
  _mr.py                      Modrinth：按 project id 列 fabric 构建 / 下载指定 game_version
  _deps.py                    打印某构建的精确依赖（含 project 名）
  _scanrefs.py                <target.jar> <dep.jar>... 列出 class 级缺失（判「缺口多大」）
  _imports.py                 <srcdir> --mod x：列出 import 了但 classpath 没有的 FQN + 候选新位置
  _javac9.py  _jar9.py        26.3 classpath 编译（已剔 1.21.1 client）/ 打 jar
  _errs.py  _blocks.py        错误直方图 / 压平成一行一条（通读用）
  _auto_cast.py               按错误行去 CFR 滥加的 (Object)/(Comparable)
  _fix_dp.py  _fix_dp2.py     DP 的包搬迁 + 颜色/实体类搬迁
  anno/src                    org.jetbrains.annotations 编译期垫片
  shim/src                    FlowableFluid$Still/$Flowing（6.0.9-4 兼容垫片）
  _shim/anno-stub.jar  _shim/fluid-compat.jar
  ei/  dp/                    各自 orig/mod.jar + src（已部分修过）
  javac_ei.log / javac_dp.log / ei_err.txt / dp_err.txt   当前错误清单（一行一条）
```

复现：

```powershell
cd work\run26\port\g9
python _javac9.py dp            # 87 错
python _javac9.py ei            # 202 错（cp_ei.txt 里挂的是 DP 原包；DP 修好后改成 out_dp）
python _errs.py javac_ei.log
```

---

## 4. 降级清单（本轮已确定、写进交付说明时要用）

| mod | 降级 | 原因 |
|---|---|---|
| create-dragons-plus | **JEI 集成整包删除**（`client/compat/jei/**` 9 类 + `jei_mod_plugin` 入口） | 26.3 的 JEI API 与 26.1.2 不同；纯展示 |
| create-enchantment-industry | **JEI 集成整包删除**（`integration/jei/**` 14 类 + `jei_mod_plugin` 入口） | 同上 |
| create-dragons-plus | `StatTrigger` / `BuiltinTrigger` 降级为 **codec-only**（进度不再自动完成） | 26.3 删了 `CriterionTrigger.Listener` + `PlayerAdvancements#addPlayerListener` |
| create-dragons-plus | 猫/狼领巾染色（`Cat/Wolf#setCollarColor` 已 private） | 需 accessor/mixin，性价比低 |
| create-dragons-plus | 接触染色记忆（Fabric 附件） | `Entity` 运行期才实现 `AttachmentTarget`，编译期要强转 + 行为待验证 |

---

## 5. 下一步建议（按性价比排序）

1. **先清「同名但签名变了」的族**（`mulPose(Quaternionfc)` 12、`placeItemBackInInventory(ItemStack)` 8、
   `add(Object[])` 6、`ValueOutput.store` 18）：查一次 26.3.jar 的对应类就能批量改，是当前最大的一块。
2. 再清 `cannot find symbol` 里剩下的（EI 56）——逐个查 26.3.jar，多数是类/方法搬家。
3. `RecipeAccess` / `RecipeMap` / `CauldronInteractions` / `FeaturesConfig` 四处**单点**，各需 10–20 分钟。
4. 两 mod 都 0 错之后：`_build9.py`（照抄 `g8/_build8.py`，把 `dp`/`ei` 配进去，删 `jei_mod_plugin`
   entrypoint、把 `depends.minecraft` 改 `>=26.1- <26.4-`、把 `create` 约束改 `>=6.0.9-2`、
   `create_dragons_plus` 改 `>=1.11.4`）→ 打包 → staging（**65 + dp + ei + fluid-compat**）
   → `TITLE_SCREEN_OK` → **全新存档副本** → `WORLD_OK` → promote → 复跑标题。
5. 数据层**不用转**：EI/DP 的 26.1.2 jar 已经是 26.3 目录/格式（`recipe/`、`loot_table/`、`advancement/`、
   `assets/*/items/`），这是 26.1.2 相比 1.21.1 最大的一处便宜。

---

## 6. 本轮明确**没有**做的事

- 没有启动游戏（EI/DP 都没到能编译的程度，测了也是白测）。
- 没有改 `mods-stable`、没有 promote、没有动 `work/run26/watch`。
- 没有碰 `mods-full` / `mods-fix2` / `mods-crashfix` / `work/sable-26` / `work/build26` / `g6` / `g7` / `g8`。
- 没有对 5 个 1.20.1 目标动手（本轮预算全花在「最近的那一个」上，符合「离 26.3 最近优先」）。
