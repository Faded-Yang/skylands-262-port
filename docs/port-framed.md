# create-framed（Create 附属）1.20.1 Fabric → MC 26.3 Fabric 移植报告

> 轮次：R381（2026-10-18）｜交付物：`work/run26/mods-stable/createframed-1.7.3-26.3.jar`
> 结论：**标题画面 + 进世界都实测通过**；`mods-stable` 从 **60 → 61 jar**。
> 流水线照抄 `interiors`（`work/run26/port/g6/_all.py`），新脚本在 `work/run26/port/g7/`。

---

## 0. 一句话结论

`create-framed` 用「CFR 反编译 → i21n 机械改名 → 人工修语义 → javac --release 21 → 与原 assets/data 重打包」
跑通：25 个 class → 24 个 class（新增 `TiledGlassBlock`，删掉 1 个 render-state 渲染器），
**313 条配方 0 丢弃**、227 张战利品表、303 个物品模型入口、249 个方块/物品全部真注册。

| 验收项 | 结果 | 证据 |
|---|---|---|
| 标题画面（`mods-stable` 61 jar） | **TITLE_SCREEN_OK 23.7s** | `g7/framed/title_stable.log` |
| 进世界（全新存档副本，`mods-stable` 本体） | **WORLD_OK 36.0s**（`server_started=True joined=True`） | `g7/framed/world_stable.log` |
| 注册表错误 | **0**（`Registry loading errors` 一条没有） | 同上 |
| 方块状态解析失败 | **0**（第 5 轮前是 17 个门的 1024 个变体） | 同上 |
| mixin 应用失败 | **0** | 同上 |
| 模型/贴图缺失 | **0**（`createframed` 相关 Missing 零） | 同上 |
| 进度表加载 | **2085** | `world_stable.log` |

---

## 1. 流水线（与 interiors 同构，只是换了 mod）

```
原 jar（named 类名 / intermediary 成员）
  │ CFR 0.152（_tools/cfr-0.152.jar）
  ▼
23 个 .java（25 class，2 个内部类合并）
  │ _rewrite_src.py：i21n 表（8,254 类 / 76,563 成员）+ Create 包搬迁
  ▼
src26（机械改名）→ src27（_fix_framed.py 人工修语义）
  │ javac --release 21，classpath = 26.3.jar + libraries + create-fly + aeronautics(registrate 垫片) + fabric-api
  ▼
24 个 .class + 原 assets/data → 数据层转换 → 三重校验
```

一键重建（本轮已验证可复现，产物字节数与交付一致）：

```powershell
$py = "C:\Users\95959\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
cd work\run26\port\g7
& $py _all.py          # 反编译(缺省跳过) -> 改名 -> 修语义 -> javac -> 打包 -> 数据转换 -> 校验
```

---

## 2. 代码侧修法（逐条）

### 2.1 MC 26.3 侧

| # | 1.20.1 | 26.3 | 修法 |
|---|---|---|---|
| 1 | `new Identifier(ns, path)` | 构造器变 private | `Identifier.fromNamespaceAndPath(ns, path)` |
| 2 | `Level.random`（字段） | 变 protected | `level.getRandom()` |
| 3 | `CompoundTag.getBoolean` | 返回 `Optional<Boolean>` | `getBooleanOr(key, false)` |
| 4 | `Direction.getNormal()` | 删除 | `getUnitVec3i()` |
| 5 | `Direction.getNearest(d,d,d)` | 删除 | `getApproximateNearest(Vec3)` |
| 6 | `Block#propagatesSkylightDown(state,getter,pos)` | 单参 | `propagatesSkylightDown(BlockState)` |
| 7 | `Block#getLightBlock(...)` + `getter.getMaxLightLevel()` | 合并 | `getLightDampening(BlockState)` 返回 15 |
| 8 | `GlassBlock` | **删除**（1.21.2 并入 `TransparentBlock`，构造器 protected） | 自建 `TiledGlassBlock extends TransparentBlock` |
| 9 | `Blocks.RED_STAINED_GLASS` 等 16 个 | 变成 `ColorCollection<Block>` | `Blocks.STAINED_GLASS.pick(DyeColor.X)` |
| 10 | `Blocks.RED_TERRACOTTA` 等 19 个 | 变成 `ColorCollection<Block>` | `Blocks.DYED_TERRACOTTA.pick(DyeColor.X)` |
| 11 | `Blocks.COPPER_BLOCK` | 变成 `WeatheringCopperCollection<Block>` | `Blocks.COPPER_BLOCK.weathering().unaffected()` |
| 12 | `TrainTrapdoorBlock(Properties, BlockSetType)` | 参数换序 | `super(BlockSetType, Properties)` |
| 13 | `SlidingDoorBlockEntity(BlockEntityType, BlockPos, BlockState)` | 去掉 type | `super(pos, state)` |
| 14 | `SlidingDoorBlockEntity#isVisible/showBlockModel/shouldRenderSpecial` | 删除（渲染改 render-state） | 整段删掉；`animation` 已是父类 public 字段 |
| 15 | `BlockEntityRenderer#renderSafe` | 26.3 改成 `extractRenderState/submit` 两段式 | **删掉自定义渲染器**，复用 Create 的 `SlidingDoorRenderer`（见降级 3） |
| 16 | `BlockBehaviour.Properties#isValidSpawn/isViewBlocking` | 泛型谓词（`AABB` / `EntityType`） | 三个 `never()` 重载按签名分开 |
| 17 | `CreativeModeTab$Output` | 变 protected 嵌套类型；`AllCreativeModeTabs$TabInfo` 删除 | Fabric `FabricCreativeModeTab.builder()` + `CreativeModeTabEvents.modifyOutputEvent(TAB_KEY)` |
| 18 | `ItemDescription` 之外无 | — | 本 mod 没用到 |

### 2.2 Create 26.3 侧

| 1.20.1 | 26.3 | 备注 |
|---|---|---|
| `com/simibubi/create/**` | `com/zurrtum/create/**` | 前缀替换（拼写 `simibubi`） |
| `.../foundation/block/connected/*`（AllCTTypes/CTSpriteShifter/CTType/各种 CTBehaviour） | `.../client/foundation/block/connected/*` | 搬进 client |
| `.../content/decoration/TrapdoorCTBehaviour` | `.../client/content/decoration/TrapdoorCTBehaviour` | 同上 |
| `.../AllPartialModels` | `.../client/AllPartialModels` | 同上 |
| `net/createmod/catnip/render/*`、`.../lang/*` | `com/zurrtum/create/client/catnip/*` | client |
| `net/createmod/catnip/{animation,data,math}/*` | `com/zurrtum/create/catnip/*` | 非 client |
| `dev/engine_room/flywheel/lib/model/baked/PartialModel` | `com/zurrtum/create/client/flywheel/lib/model/baked/PartialModel` | flywheel 被 Create 内联 |
| `MovementBehaviour` | **接口 → 抽象类** | `implements` → `extends` |
| `Contraption#getBlockEntityClientSide(BlockPos)` | 删除 | `AllClientHandle.INSTANCE.getBlockEntityClientSide(contraption, pos)` |
| `CardboardBlockItem` | 删除 | 用原版 `BlockItem::new`（构造器签名一致） |
| `Create.asResource(String)` | 删除 | `Identifier.fromNamespaceAndPath("create", path)` |
| `AllCreativeModeTabs.PALETTES_CREATIVE_TAB.key()` | 删除 | `AllCreativeModeTabs.PALETTES_GROUPS` → 实际字段名 `PALETTES_GROUP` |
| `BuilderTransformers.trapdoor(boolean)` | 垫片里只有 `copycat()` | 去掉该 transform（数据已烘进 jar） |
| `MovementBehaviour.movementBehaviour(x)` / `MovingInteractionBehaviour.interactionBehaviour(x)` | 删除 | `REGISTRY.register(block, x)` |

### 2.3 ★ 本轮最关键的新发现：registrate 垫片里**一整批 builder 方法是空实现**

`interiors` 只发现了 `AbstractRegistrate.register()` 是 `Code: 0: return`。本轮 javap 逐个核对后确认
**`AbstractBuilder` 的这批方法全是 `return self()`**：

```
transform(NonNullUnaryOperator)      -> 直接 return self()   // 传进去的 lambda 从不执行
onRegister(NonNullConsumer)          -> 直接 return self()
onRegisterAfter(...)                 -> 直接 return self()
lang(String)                         -> 直接 return self()
```
`CreateRegistrate.connectedTextures/blockModel/itemModel` 返回的 consumer 也是空 lambda（`Code: 0: return`），
`CreateRegistrate.setCreativeTab(...)` 同样是空方法。

**后果（编译期完全不报错）**：
1. `.transform(slidingDoor(type))` 里的 `.simpleItem()` 不执行 ⇒ **17 个门的物品一个都没注册**，
   而 `data/c/tags/item/dyed/*` 引用了它们 ⇒ 进世界时 `Couldn't load tag c:dyed/... missing references`
   ⇒ `Failed to load registries due to errors`。**标题画面照过。**
2. `.onRegister(...)` 不执行 ⇒ 门的移动/交互行为从未注册（滑门在 contraption 上不会开）。
3. `.onRegister(CreateRegistrate.connectedTextures(...))` 不执行 + consumer 本身是空的 ⇒ 连接纹理**没有注册**（见降级 1）。

**修法**：一切「注册动作」都必须在 `.register()` 之后显式写：
```java
BlockEntry<FramedGlassSlidingDoorBlock> entry = REGISTRATE.block(...)
        .initialProperties(...).properties(...).simpleItem().register();
MovingInteractionBehaviour.REGISTRY.register(entry.get(), new FramedDoorMovingInteraction());
MovementBehaviour.REGISTRY.register(entry.get(), new FramedSlidingDoorMovementBehaviour());
```
`simpleItem()` 本身不是空实现：它只把 `itemRequested=true` 打在同一个 BlockBuilder 上，
物品真正注册发生在 `BlockBuilder.register()` 里（`if (itemRequested) Registry.register(ITEM, id, BlockItem)`）。
所以「链尾有 `.register()`」时 `simpleItem()` 有效 —— **但如果 `simpleItem()` 写在 `.transform()` 的 lambda 里就永远不生效**。

> 判据：`[REGDBG] queue block createframed:*` 与 `create block createframed:*` 计数必须相等（本轮 249/249）。
> 物品没有 REGDBG 日志，只能靠「标签能不能解析」反查 —— 这就是为什么必须进世界。

---

## 3. 数据层（1.20.1 → 26.3，本轮实测）

`create-framed` 的资源条目 2699 个（assets 1722 / data 940），代码只有 25 个 class。

| 项 | 1.20.1 | 26.3 | 数量 |
|---|---|---|---|
| 目录 | `recipes/` `loot_tables/` `advancements/` `tags/blocks` `tags/items` | `recipe/` `loot_table/` `advancement/` `tags/block` `tags/item` | 313+227+3+251 |
| Ingredient | `{"item":x}` / `{"tag":t}` | 裸字符串 `"x"` / `"#t"` | 313 条配方 |
| result | `{"item":...}` | `{"id":...}` | 同上 |
| **`create:deploying` / `create:item_application`** | `ingredients:[a,b]` | **`target: a` + `ingredient: b`**（26.3 的 `ItemApplicationRecipe` 是 record(results, keepHeldItem, target, ingredient)） | 19 |
| **`create:splashing`** | `ingredients:[a]` | **`ingredient: a`**（单数） | 12 |
| **`category: blocks`（熔炉）** | `blocks` | 烹饪只认 `food/blocks/misc`（**不能**写 `building`） | 16 |
| `category: building_blocks` | — | `building`（锻造/合成仍用 `building`） | — |
| **战利品表 `minecraft:block_state_property`** | 门的下半判定 | **26.3 已删除该 loot condition** ⇒ 整表改成原版门形状（`pool.condition=survives_explosion` + `entry.condition=match_block{half:lower}`） | 17 |
| **方块状态 `visible=...`** | Create 1.20.1 的滑动门有 VISIBLE 属性 | **26.3 的 `SlidingDoorBlock` 没有该属性** ⇒ 变体解析失败 | 17 门 ×1024 变体 → 去重后 32 |
| **进度表 `display.icon`** | `{"item":x}` | `{"id":x}`（ItemStack） | 3 |
| **进度表 `inventory_changed.items`** | `[{"item":x}] / [{"tag":t}]` | **`[{"items":"x"}] / [{"items":"#t"}]`**（ItemPredicate 对象列表） | 3 |
| 进度表 `requirements` | 可缺省 | **必须与 criteria 完全一致** | 3 |
| 物品定义 | 无 | `assets/createframed/items/*.json`（从 `models/item` 批量生成） | 303 |
| **约定标签改名** | `c:string` / `c:colorless_glass` | **`c:strings` / `c:glass_blocks/colorless`**（fabric-convention-tags-v2） | 39 |
| **物品改名** | `create:copper_nugget` | **`minecraft:copper_nugget`**（1.21 起是原版物品） | 1 |
| `pack.mcmeta` | pack_format 9 | 丢弃 | 1 |

### 3.1 三重校验（`_validate_framed.py`）

* 物品清单 = 所有已装 jar 的 `assets/<ns>/items/*.json`（2900 个，含 fabric-api 伞 jar **嵌套子模块**递归）
* 标签清单 = `data/<ns>/tags/{item,block}/*.json`（item 722 / block 640）
* 逐条校验 `type / category / 每个 ingredient / target / result / results`
* 实测：**313 条配方全部保留、0 丢弃**

> 教训：校验器一开始只扫 `mods-stable` 顶层 jar，于是 `c:strings`（在 fabric-api 的
> `META-INF/jars/fabric-convention-tags-v2-*.jar` 里）被判成「missing tag」，误杀 34 条配方。
> **校验器必须递归一层嵌套 jar**，否则会把「运行时其实存在」的东西当缺失。

---

## 4. 迭代实录（5 轮进世界）

| 轮 | 结果 | 卡在哪 | 修法 |
|---|---|---|---|
| 1 | TITLE_SCREEN_OK 23.8s | —（249 方块全部 queue+create，flush 正常） | — |
| 2 | `FAIL_REGISTRY` | ① 3 张进度表 `display.icon` 用 `{item:}`；② `c:dyed/*` 标签引用 17 个门物品，**门物品根本没注册** | ① icon→`{id}`；② 门改用显式 `simpleItem()`+显式注册行为 |
| 3 | `FAIL_REGISTRY` | ① 17 张门战利品表用了已删除的 `block_state_property`；② 熔炉 `category: building` 非法；③ `create:deploying/item_application` 要 `target`+`ingredient`；④ `create:splashing` 要单数 `ingredient` | 逐类转换（见 3 节） |
| 4 | `WORLD_OK` 36.1s | （但方块状态仍在报错：`visible` 属性不存在） | 去掉 `visible=...` 并去重变体 |
| 5 | **WORLD_OK 36.0s + 0 注册表错误 + 0 blockstate 异常**，promote 后 `TITLE_SCREEN_OK 23.7s` | — | — |

---

## 5. 降级清单（必须写进交付说明）

| # | 降级 | 影响 | 原因 |
|---|---|---|---|
| 1 | **连接纹理（CT）没有注册** | 染色 framed glass / window 的「相邻玻璃自动连纹理」不会生效，视觉上是普通贴图 | 垫片的 `CreateRegistrate.connectedTextures` 返回空 consumer、`onRegister` 是空实现；26.3 侧没有等价的公开注册入口可调 |
| 2 | **`setCreativeTab` 无效果** | 物品不进 Create 的 palette 标签页，只进本 mod 自己的 `create_framed` 标签页（该标签页已实测可用） | 垫片 `CreateRegistrate.setCreativeTab` 是空方法 |
| 3 | **滑动门渲染器改用 Create 自带的 `SlidingDoorRenderer`** | 门在 contraption 上滑动时由 Create 渲染器画（同一套动画语义）；原先自定义渲染器里的「folding door 分支」对本 mod 的门本来就是死代码（`isFoldingDoor()==false`） | 26.3 的 BER 改成 `extractRenderState/submit` 两段式 + render state 体系，重写成本高、收益近零 |
| 4 | **创造栏改由 Fabric 事件填充** | 功能等价 | `CreativeModeTab$Output` 变 protected；`AllCreativeModeTabs$TabInfo` 删除 |
| 5 | **karpboard 方块不再作为燃料**（原 4000/8000 tick） | 丢进熔炉不燃烧 | 26.3 Fabric API 已移除 `FuelRegistry`（燃料改数据驱动），没有等价注册入口 |
| 6 | **datagen 入口删除** | 以后不能跑这个 mod 的数据生成；现有数据已烘进 jar | 原 `fabric-datagen` entrypoint 依赖 porting_lib 的生成器，26.3 不存在 |
| 7 | 门/活板门的物品模型直接由 `models/item` 生成 | 与原版视觉一致（已实测 0 Missing） | — |

**没有降级的**：全部 249 个方块 + 物品注册、313 条配方、227 张战利品表、251 个标签、
创造标签页、门/活板门/窗/玻璃/纸板/背包（package）的方块类与方块实体。

---

## 6. 复现 / 验证命令

```powershell
$py = "C:\Users\95959\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262

# 1) 重建（反编译→改名→修语义→javac→打包→数据→校验）
cd work\run26\port\g7; & $py _all.py

# 2) 标题（交付目录本体）
& $py tools\launch26\launch.py --game-dir work\run26\stag1 --mods work\run26\mods-stable --watch-title --timeout 240

# 3) 进世界（★ 每次必须先重拷全新存档，否则「实验性设置」弹框会伪装成超时）
Remove-Item -Recurse -Force "work\run26\stag1\saves\New World (1)"
Copy-Item -Recurse "work\run26\watch\saves\New World (1)" "work\run26\stag1\saves\New World (1)"
& $py tools\watch_world.py --game-dir work\run26\stag1 --mods work\run26\mods-stable --world "New World (1)" --timeout 260
```

## 7. 文件索引

| 用途 | 路径 |
|---|---|
| 交付 jar | `work/run26/mods-stable/createframed-1.7.3-26.3.jar` |
| 构建产物 | `work/run26/port/g7/framed/createframed-1.7.3-26.3-final.jar` |
| 反编译源码 | `g7/framed/src/`（23 java） |
| 机械改名后 | `g7/framed/src26/` |
| 最终源码（编译用） | `g7/framed/src27/`（24 class） |
| 一键重建 | `g7/_all.py` |
| 脚本 | `g7/{_rewrite_src,_fix_framed,_javac,_build_jar,_convert_framed,_validate_framed}.py` |
| 日志 | `g7/framed/{title_stable,world_stable}.log` |

---

## 8. 附加任务（后续 4 个 mod）的实测结论 —— **均未打通**

按缺口从小到大推进，逐个做到「机械改名 + 首次 javac」并记录卡点（这是排期最有效的一步：
一次 javac 就能把「1.20.1 API 差异」和「Kotlin/框架级重写」分开）。

| mod | class | 首次 javac 错误 | 判定 | 卡在哪（根因） |
|---|---|---|---|---|
| `design-n-decor` 0.4.0b | 135（107 java） | **1869** | ❌ 不做 | 三类硬伤叠加：① 依赖**旧 Flywheel**（`com.jozufozu.flywheel.api/core`，32+ 条 `package does not exist`），26.3 的 flywheel 被 Create 内联且 API 全换；② `porting_lib.models.generators` 的整条 datagen 链（`RegistrateItemModelProvider`/`LootTable.Builder`）在 26.3 不存在；③ 大量 `RegistryEntry → BlockEntry` 的垫片返回值差异。即使砍掉渲染（468 错）+datagen（66 错），core 仍有 **1155** 错 ⇒ 保守估计 3–5 个会话 |
| `slice-and-dice` 3.6.0 | 58（44 java） | **65** | ⚠ 最值得下一个做 | 错误几乎全是 CFR 对 **Kotlin 编译产物**的恢复失败：`void $this$mapValues$iv;` 之类伪声明（55 处）、匿名内部类被写成 `createRecipeType.type.1`（方法签名非法）。需要把 6 个 Kotlin 风格的类（`Content`/`RecipeInjection`/`SlicerBlockEntity`/`PonderScenes`）按语义重写，规模约等于 2–3 个 framed |
| `create-jetpack` 4.4.2 | 17（12 java） | 9 → 之后暴露 Kotlin | ❌ 短期不做 | 整个 mod 是 **Kotlin**：CFR 输出里满是 `Intrinsics`/`CollectionsKt`/`Function0`/destructuring 残影；`JetpackItem` 构造器被还原成 `void $this$map$iv` 的乱码。要靠手写反推 Kotlin 语义（喷射物理 + 控制层 HUD）。另外它 JiJ 内嵌 `flightlib-2.2.3`（1.20.1 构建），飞行库本身也要移植 |
| `escalated` 1.2.1 | 78（64 java） | 5 → 修完后 **542** | ⚠ 次选 | 5 个错误只是 `void varN;` 伪声明（已修）；把 `@ExpectPlatform`（architectury 构建期注解，运行时 jar 里没有）剥掉后掉到 542。剩余：`StateHolder#setValue` 签名（24）、`Level.isClientSide/random` 可见性（22）、`net.createmod.ponder.api.registration`（7，ponder 包在 26.3 搬到 `com.zurrtum.create.client.ponder`）、`ModConfig`（8，architectury config 未随 jar 分发）、`Instance → OrientedInstance`（6，flywheel）等 |

> 结论排序（下一轮建议）：**slice-and-dice（65）> escalated（542）> design-n-decor（1869）> create-jetpack（Kotlin 重写）**。
> 注意：`slice-and-dice` / `create-jetpack` 的「错误数少」是假象 —— 少是因为 CFK 在**语法阶段**就停下了，
> 真实的 26.3 API 缺口要等 Kotlin 残影清完才会暴露。真正可比的是 `design-n-decor`/`escalated` 这种
> 「语法通过、只有 API 缺口」的数字。
