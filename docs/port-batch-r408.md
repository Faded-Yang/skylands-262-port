# port-batch-r408 —— 未移植 mod 批次：可移植性评估 + 首批落地（Paxi / YungsApi）+ 附魔工业可行性

> 日期：2026-10-18 ｜ 目标：MC **26.3** + Fabric Loader 0.19.5 + Java 25
> 验收口径：**标题 = launch.py --watch-title 三条标记全中**；**进世界 = `logged in with entity id`（全新存档副本）**。
> 本批全部实验在 `work/run26/port/p1/`，**未改 `mods-stable`**、未碰 `watch`。promote 由 Lead 做。

---

## 0. 结论

| 项 | 结果 |
|---|---|
| 剩余真实缺口 | **~52 jar**（`diff_pack.py` 出 54；其中 `MoogsSoaringStructures`/`no-void-structures` 是 **mod id 变更误报**，两者已在交付件里）。52 里 **bundle 2 + loader 库 1** 不产生新内容 ⇒ 真正要移植的约 **49（库/前置 10、内容 39）** |
| ★ 关键更正 | **`notes/avail-263.md` 的「完全没有 Fabric 构建」有 5 条误判**：CEI / DragonsPlus / natures_spirit / Paxi / YungsApi 实测都有 **26.1.2 Fabric 构建**（§2） |
| ✅ 已实做并达标 | **Paxi 26.1.2-Fabric-6.1.0 + YungsApi 26.1.2-Fabric-6.1.3（3 类、9 处补丁）**：`TITLE_SCREEN_OK 39.6 s` + `WORLD_OK 72.9 s`，**0 crash-report、0 Mixin apply failed** |
| 🔶 附魔工业（用户点名） | **可做，跨轮（预计 2–4 轮）**。上游有 26.1.2 Fabric 构建（2.5.2-c）＋必需前置 DragonsPlus 26.1.2；本轮已下载、放宽依赖、真启动并拿到首错（`NoClassDefFoundError: …FlowableFluid$Still`，实为改名 `FluidEntry$Still`）；静态扫描把 CEI+DP 缺口分成 **8 类 78 处**（§4） |
| ❌ 不建议本轮做 | 只有 NeoForge 构建的 ~40 个（sophisticated 3 / tfmg / create_submarine / copycats / central_kitchen / mechanical_extruder / power_loader / connected / 各种 Create 附属）—— 要「NeoForge→Fabric + 1.21→26.3」两层 |

---

## 1. 剩余缺口重新核算（可复算）

```
python tools\diff_pack.py            # 54 条「未覆盖」
python p1/_inventory.py              # 按 mod id + jar 名相似度重算，标出 id 变更误报
python p1/_probe_missing.py          # 对每条重查 Modrinth 最新 Fabric 构建
```

- `diff_pack.py` 只按 **mod id** 比对 ⇒ 旧 jar 的 id 与新 Fabric 件不同时会误报。
- 实测两处：`MoogsSoaringStructures-universal-1.21`（旧 id `mss`）已装为 `MoogsSoaringStructures-2.2.0-26.3.jar`；`no-void-structures-2.0.1` 已装为 `no_void_structures-2.0.1-26.3.jar`。
- 剔除后 **52**；再把 `create-aeronautics-bundled`（内含的 aeronautics/sable 已按本体移植）、`gadgets-and-gizmos-bundled`（内含 2 个真 Java mod，优先级 2）、`kotlinforforge`（loader 库，已用 fabric-language-kotlin）排除，**真正要动约 49 个**。

### 1.1 缺口总表（名字 / 类型 / 最新 Fabric / 差距 / 规模 / 预判）

> 「差距」= 最新 Fabric 与 26.3 的距离；class/nf_ref/data 来自 `work/run26/port/_orig_scan.json`（原 1.21.1 jar）。

| jar | 类型 | Modrinth slug | 最新 Fabric | 差距 | class | nf_ref | data | 预判 |
|---|---|---|---|---|---|---|---|---|
| `create-enchantment-industry-2.5.4b.jar` | 内容★用户点名 | create-enchantment-industry | 26.1.2 | 26.1.x | 464 | 379 | 158 | M/L（见 §4） |
| `CreateDragonsPlus-1.11.9.jar` | 库(CEI 前置) | create-dragons-plus | 26.1.2 | 26.1.x | 388 | 295 | 305 | M/L（与 CEI 同步） |
| `natures_spirit-2.2.6-1.21.1.jar` | 内容(大) | natures-spirit | 26.1.2 | 26.1.x | 202 | 105 | 2839 | S/M（放宽→实测；数据面大） |
| `YungsApi-1.21.1-NeoForge-5.1.9.jar` | 库 | yungs-api | 26.1.2 | 26.1.x | 191 | 47 | 4 | **已落地**（§3） |
| `Paxi-1.21.1-NeoForge-5.1.3.jar` | 工具(数据包/世界预设) | paxi | 26.1.2 | 26.1.x | 15 | 21 | 0 | **已落地**（§3） |
| `dragonlib-3.0.29+mc1.21.1-neoforge.jar` | 库 | dragonlib | 1.21.1 | 1.21.x | 588 | 104 | 0 | L/XL |
| `lodestone-1.21.1-1.8.2.jar` | 库 | lodestonelib | 1.21.1 | 1.21.x | 419 | 176 | 34 | L/XL |
| `modernfix-neoforge-5.27.26+mc1.21.1.jar` | 优化器 | modernfix | 24w14a(快照) | 1.21.x | 314 | 112 | 0 | L/XL |
| `player-animation-lib-forge-2.0.4+1.21.1.jar` | 库 | playeranimator | 23w13a_or_b | 1.21.x | 127 | 4 | 0 | L（两层） |
| `culturaldelights-1.21.1-0.19.2.jar` | 内容 | cultural-delights | 1.21.1 | 1.21.x | 111 | 127 | 471 | L（两层） |
| `createrailwaysnavigator-…` | 内容 | create-railways-navigator | 1.20.1 | 1.20.x | 724 | 117 | 29 | XL（三层） |
| `copycats-3.0.9+mc.1.21.1-neoforge.jar` | 内容 | copycats | 1.20.1 | 1.20.x | 393 | 120 | 246 | XL |
| `Design-n-Decor-1.21.1-2.2b.jar` | 内容 | create-design-n-decor | 1.20.1 | 1.20.x | 166 | 88 | 3127 | XL |
| `createoreexcavation-1.21-1.6.8.jar` | 内容 | create-ore-excavation | 1.20.1 | 1.20.x | 145 | 96 | 54 | XL |
| `sliceanddice-4.3.4-neoforge.jar` | 内容 | slice-and-dice | 1.20.1 | 1.20.x | 122 | 93 | 33 | XL |
| `create_jetpack-forge-5.2.1.jar` | 内容 | create-jetpack | 1.20.1 | 1.20.x | 26 | 41 | 11 | XL |
| `sophisticatedcore` / `sophisticatedbackpacks` / `sophisticatedstorage` | 库+内容 | sophisticated-* | 无 | 无Fabric | 843/379/403 | 471/395/356 | 6/244/754 | XL（只有 26.3 NeoForge 构建） |
| `tfmg-1.2.0.jar` | 内容 | create-tfmg | 无 | 无Fabric | 671 | 492 | 1747 | XL |
| `create_aeronautics_toolgun-0.3.6.jar` | 内容 | create-aeronautics-toolgun | 无 | 无Fabric | 496 | 174 | 3 | XL |
| `blueprint-1.21.1-8.2.0.jar` | 库 | blueprint | 无 | 无Fabric | 493 | 285 | 53 | XL |
| `ftb-quests` / `ftb-library` / `ftb-teams` | 内容(任务)+库 | ftbquests/ftblibrary/ftbteams | 无 | 无Fabric | 476/403/134 | 42/12/2 | 17/0/0 | XL（价值低） |
| `create_submarine-3.3.0.jar` | 内容 | create-deep-seas | 无 | 无Fabric | 420 | 529 | 103 | XL |
| `create_connected` | 内容 | create-connected | 无 | 无Fabric | 401 | 235 | 634 | XL |
| `createpropulsion` | 内容 | create-propulsion-simulated | 无 | 无Fabric | 344 | 356 | 189 | XL |
| `aeroworks` | 内容 | create-aeroworks | 无 | 无Fabric | 241 | 110 | 66 | XL |
| `createdieselgenerators` | 内容 | create-diesel-generators | 无 | 无Fabric | 239 | 345 | 212 | XL |
| `create-central-kitchen` | 内容 | create-central-kitchen | 无 | 无Fabric | 236 | 165 | 3 | XL |
| `create_aeronautics_transmission_linkage` | 内容 | create-aeronautics-transmission-linkage | 无 | 无Fabric | 131 | 107 | 19 | XL |
| `MyNethersDelight` | 内容 | my-nethers-delight | 无 | 无Fabric | 131 | 142 | 440 | XL |
| `mechanicals` | 库 | mechanicals-lib | 无 | 无Fabric | 106 | 45 | 1 | XL |
| `mysterious_mountain_lib` | 库 | mmlib | 无 | 无Fabric | 73 | 48 | 3 | XL |
| `minersdelight` | 内容 | miners-delight | 无 | 无Fabric | 69 | 110 | 199 | XL |
| `create_power_loader` | 内容 | create-power-loader | 无 | 无Fabric | 65 | 28 | 11 | XL |
| `createdeco` | 内容 | createdeco（slug 不存在） | 无 | 无Fabric | 62 | 24 | 3869 | XL（数据巨大） |
| `create_mechanical_extruder` | 内容 | create-mechanical-extruder | 无 | 无Fabric | 49 | 36 | 46 | XL |
| `waystonessable` | 兼容 | waystones-sable | 无 | 无Fabric | 40 | 14 | 0 | XL |
| `abnormals_delight` | 内容 | abnormals-delight | 无 | 无Fabric | 35 | 67 | 392 | XL |
| `create_aeronautics_throwable_rope_connector` | 内容 | create-aeronautics-throwable-rope-connector | 无 | 无Fabric | 35 | 76 | 5 | XL |
| `climbable_ropes` | 内容 | create-aeronautics-climbable-rope | 无 | 无Fabric | 34 | 61 | 0 | XL |
| `aeronauticscompat` | 兼容 | create-aeronautics-compatability | 无 | 无Fabric | 25 | 6 | 2 | M（小 Java） |
| `createliquidfuel` | 内容 | create-liquid-fuel | 无 | 无Fabric | 13 | 15 | 1 | M（小 Java） |
| `FTBQuestsOptimizer` | 工具 | ftbqopt | 无 | 无Fabric | 10 | 0 | 0 | M（依赖 FTBQ，装了也没意义） |
| `portable_engine_liquid_fuel` | 内容 | create-aeronautics-portable-engine-liquid-fuel | 无 | 无Fabric | 10 | 24 | 2 | M（小 Java） |
| `aerocopycats` | 内容(需 copycats) | copycats-plus-aeronautics-weight | 无 | 无Fabric | 2 | 5 | 27 | S（纯数据，但依赖 copycats，本轮做不了） |
| `awakened_islands` | 内容 | awakened-islands | 无 | 无Fabric | 2 | 12 | 0 | M（2 class，需反编译看语义） |
| bundle/loader 3 件 | bundle / loader | — | — | — | 0 | 0 | 0 | 不是内容 mod（§1） |

---

## 2. 关键更正：`avail-263.md` 的 D 类有 5 条误判

`notes/avail-263.md`（2026-10-17）把 CEI 等判成「完全没有 Fabric 构建」。今天用 `probe_fabric_builds.py` 重查，**5 条实际是 26.1.2 Fabric**：

| 项目 | 今天实测最新 Fabric | 旧判定 |
|---|---|---|
| create-enchantment-industry | **26.1.2** | D 无 Fabric ❌ |
| create-dragons-plus | **26.1.2** | D ❌ |
| natures-spirit | **26.1.2** | D ❌ |
| paxi | **26.1.2** | D ❌ |
| yungs-api | **26.1.2** | D ❌ |

⇒ **「完全没有 Fabric 构建」必须当天重跑**（Modrinth 的 `loaders=[fabric]` 查询会超时返回空）。这直接把两个候选从「XL 重写」降成「M/L 改名/补丁」。

---

## 3. 已落地：Paxi + YungsApi（TITLE_OK + WORLD_OK）

### 3.1 候选件

| 件 | 来源 | 大小 | SHA-256 |
|---|---|---|---|
| Paxi 26.1.2-Fabric-6.1.0 | Modrinth `paxi`（**未改字节**） | 231,173 B | `09591c50d39b510a775e54bb25634e282f7241888a8fc957bd677ddc0e730222` |
| YungsApi 26.1.2-Fabric-6.1.3 | Modrinth `yungs-api` | 1,305,783 B | 原始 `8a856193e92cfe7d5da022618ef3dc1b9ebff7f02ca45471319d762e3b8165e9` |
| YungsApi **patched4（交付候选）** | 3 类补丁，见 §3.2 | 1,303,055 B | `53d7ed9ee4fcb8b90a55d5dc6633b7d8ed3926a4c6243671d9262273240aee5b` |

> **Paxi 一条字节都不用改**：它的 `depends.minecraft` 是 `>=26.1`（天然接受 26.3），依赖只有 `yungsapi` / `fabric-api` / cloth-config（都已满足）。

### 3.2 YungsApi 的 3 类补丁（每类都验证「其它 entry 逐字节不变」）

| # | 补丁 | 原因（26.3 实测） | 影响 |
|---|---|---|---|
| 1 | 删 mixin：`NoBasaltColumnsInStructuresMixin` / `NoDeltasInStructuresMixin` / `NoMagmaInStructuresMixin` / `NoVinesInStructuresMixin`（`yungsapi.mixins.json`） | 它们的 `\@Inject` 目标 `Feature.place(FeaturePlaceContext)Z` 在 26.3 已变 ⇒ `InvalidInjectionException`，**启动期 fatal** | 失去「结构内不刷玄武岩/三角洲/岩浆/藤蔓」的世界生成微调 |
| 2 | 删类：`module/StructurePlacementTypeModule`、`StructurePlacementTypeModuleFabric`、`world/structure/placement/EnhancedRandomSpread`；**补一个同签名 no-op 类** `StructurePlacementTypeModuleFabric.processEntries()` | 26.3 **删除了 `net.minecraft…StructurePlacementType`**（换成 `StructurePlacements` 注册表）；`AutoRegister` 扫描到该静态字段 ⇒ `NoClassDefFoundError` | 自定义放置类型 `EnhancedRandomSpread` 不再注册（Paxi 不用它） |
| 3 | 删 mixin：`mixin/locate/ModResourcePackCreatorMixinFabric`（`yungsapi_fabric.mixins.json`）；删 mixin：`BeardifierMixin`、`NoiseChunkMixin`、`accessor.NoiseChunkAccessor`、`locate.ChunkGeneratorMixin`、`locate.LocateCommandMixin`、`locate.ServerLevelMixin` | ① `AbstractPackResources` 被 26.3 重做（`AbstractPackMetadataResources`/`PackResources`）⇒ 世界加载期 `ClassNotFoundException`；② `Beardifier`/`NoiseChunk` 的 `\@Shadow`/`\@Inject` 在 26.3 世界生成里找不到 ⇒ **区块生成期 crash-report**（世界还能进，但刷 48 条 ERROR + 写 crash-report） | 失去「locate-replacer 数据包」与结构地形融合微调；**Paxi 自己的全局数据包功能不受影响**（它的 2 个 mixin 与 yungsapi 的这几条无关） |

工具：`p1/_drop_mixin.py`（改 mixin JSON）、`p1/_drop_entries.py`（删类）、`p1/_add_entry.py`（补 no-op 类），全部「只改目标条目、其余 entry 逐字节不变、打印 old/new sha256」。

### 3.3 实测（73 jar = 71 stable + YungsApi + Paxi；每次全新存档）

| 测试 | 结果 | 证据 |
|---|---|---|
| 标题 | **TITLE_OK 39.6 s** | `p1/logs/paxi-title-final-result.json`；launch.py 三条标记全中 |
| 进世界 | **WORLD_OK 72.9 s** | `p1/logs/paxi-world8-result.json`；`[Server thread/INFO]: Tester[…] logged in with entity id 64 at (-323.5, 71.0, -41.5)` |
| 稳定性 | **0 crash-report、`Mixin apply for mod` 失败 0 条、`Game crashed` 0 条** | `p1/game-paxi4/crash-reports` 不存在；`p1/logs/paxi-world8-latest.log` |
| 残留 | 无 Paxi/YungsApi 专属 WARN（只有与基线一致的 Create mixin target / rabbit_pathfinding_fix / Realms 噪声） | 同上 |

**降级清单（如实记）**：① EnhancedRandomSpread 放置类型不注册；② 四条「结构内不刷 X」微调、Beardifier/NoiseChunk 地形融合、locate-replacer 数据包 全部关闭；③ **Paxi 的全局数据包加载功能未做玩法级验证**（只证了「模组加载 + 标题 + 进世界」）。

---

## 4. 附魔工业（create-enchantment-industry）：可做，跨轮

### 4.1 为什么「可做」

- 上游有 **Create: Enchantment Industry - Fly 2.5.2-c（Fabric 26.1.2）**，**必需前置 Create: Dragons Plus 1.11.4-p1（Fabric 26.1.2）** 也有。
- 我方 Create 是 **26.2 / 6.0.9-2**（`com.zurrtum.create`），CEI/DP 的 `depends.create` 是 `>=6.0.9-4 <6.1.0` ⇒ 只需放宽到 `>=6.0.9-1`。
- 本轮已完成：下载两件 → `_relax_deps.py` 只改 `fabric.mod.json`（`minecraft: >=26.1- <26.4-`、`create: >=6.0.9-1 <6.1.0`；其它 597/491 个 entry 逐字节不变）→ 组 73-jar 测试集 → 真启动。

| 件 | 原始 SHA-256 | 放宽后 SHA-256 | 大小 |
|---|---|---|---|
| CEI 2.5.2-c | `55f1747ee900afbe5b94486a595edefecab08f5806db0b44b29f9fc9be116203` | `463714f7027e410eebbfa0cd1770fdce2e8a90197dfd6321e13891cbc87760f5` | 882,274 → 872,709 B |
| DP 1.11.4-p1 | `ddc62cc0e2add435f108cbe7a25480fdbf57f9f5c58cb6e9e307906ddf98de9b` | `dead361de2b7a16fb073cfab0a202181ed64439ef2008e55488de6411ad8ab05` | 551,793 → 543,927 B |

### 4.2 首启动结果（真启动，18.7 s 崩在 Bootstrap）

```
java.lang.NoClassDefFoundError: com/zurrtum/create/infrastructure/fluids/FlowableFluid$Still
  at plus.dragons.createdragonsplus.registry.CDPFluids.registerPair(CDPFluids.java:63)
  at plus.dragons.createdragonsplus.registry.CDPFluids.register(CDPFluids.java:51)
  at …CreateRegisterPlugin.registerFluid(CreateRegisterPlugin.java:50)
  at net.minecraft.world.level.material.Fluids.<clinit>(Fluids.java:19)
Caused by: ClassNotFoundException: com.zurrtum.create.infrastructure.fluids.FlowableFluid$Still
```

**根因（已核实）**：我方 create-fly 26.2 的 fluids 包里 `FlowableFluid` 还在，但 **`FlowableFluid$Still`/`$Flowing` 已改名成 `FluidEntry$Still`/`$Flowing`**（`jar tf` 实证：`com/zurrtum/create/infrastructure/fluids/FluidEntry$Still.class` 存在）。⇒ **不是缺实现，是改名**，走项目已有的「常量池 Utf8 就地改名」范式即可（R407 GLFW 同款修法），**下一轮第一步**。

### 4.3 静态错误分类（`scan_landmines.py --mods p1/mods-cei`，CEI/DP 共 78 处）

- 整包：地雷 **157 → 205**（高危 **32 → 46**）—— CEI+DP 自己带来 **48 条**（高危 +14）。
- 按修法分 8 类（站点数来自 78 行表）：

| # | 类别 | 站点 | 代表（原文） | 触发 | 优先级 |
|---|---|---|---|---|---|
| 1 | **Create 内部流体类改名** | 4 | `FlowableFluid$Still.<init>(FluidEntry)` / `$Flowing` ← `CEIFluids.register:60/61`、`CDPFluids.registerPair:63/64` | 注册期（**首错**） | **P0 fatal** |
| 2 | **`simpleCodec(Function)->MapCodec` 消失** | 7 | 5 个 CEI 方块 + 2 个 DP 方块 `<clinit>`（`ExperienceHatchBlock:62`、`PrinterBlock:48`、`BlazeEnchanterBlock:38`…） | 类第一次加载（注册期几乎必然）→ NoSuchMethodError | **P0 fatal** |
| 3 | **战利品 API 重做**（26.3） | 8+ | `LootItem.lootTableItem(ItemLike)`（同名异签名）、`ConstantValue.exactly(F)`、`LootPoolSingletonContainer$Builder`、`NumberProvider`、`Criterion` 类不存在 | 方块掉落/生成时 | P1 |
| 4 | `RegistrySetBuilder.add(ResourceKey, RegistryBootstrap)` 签名变 | 2 | 26.3 改 `MultiRegistryBootstrap` | 注册期 | P1 |
| 5 | Fabric Attachment API 换代 | 5 | `AreaEffectCloud.setAttached/getAttached(AttachmentType,Object)` | 龙息汽化 | P1 |
| 6 | Create 配方/输出 API | 1+ | `ProcessingOutput.<init>(ItemStackTemplate)` | 配方加载 | P1 |
| 7 | 客户端渲染 / Ponder 场景（低优先） | 11 | `Items.RED_WOOL/PINK_WOOL/LIME_WOOL/WHITE_BANNER` 字段、`BookModel.renderToBuffer(PoseStack,VertexConsumer,II)`、`CDPPonderScenesImpl` | 打开 Ponder/渲染物品 | P2（Ponder 已损） |
| 8 | **datagen-only（可以不理）** | 24 | `AdvancementProvider.<init>(PackOutput,…)`、`AdvancementSubProvider.createPlaceholder`、`ShapedRecipeBuilder.unlockedBy`、`CEIRecipeProvider$Provider.has` | 只有 `fabric-datagen` 入口跑；游玩不进 | P3（最后） |

### 4.4 下一轮从哪继续（可直接照做）

1. **P0-①**：对 CEI+DP 两个 jar 做常量池改名
   `com/zurrtum/create/infrastructure/fluids/FlowableFluid$Still` → `…/FluidEntry$Still`、`$Flowing` → `…/FluidEntry$Flowing`；改完 `javap` 核对构造器签名（`(FluidEntry;)V` 是否一致）。复用 `tools/patch_create_pkgmove.py` 的「只改 CP Utf8 + 2 字节长度」Pass B 逻辑。
2. **P0-②**：`javap` 26.3 的对应类，找 `simpleCodec` 的替代（26.3 可能是 `simpleCodec(Function, Function)` 或换到 `BlockBehaviour`/Create builder），先做一个站点跑通再批量 7 处。
3. 重新 `_launch.py --mode world`（≈20–70 s）→ 拿到下一个 fatal，继续；P1 类按「战利品 → RegistrySetBuilder → Attachment → ProcessingOutput」顺序修。
4. 数据面：CEI 158 / DP 305 个 json 用 `tools/convert_121_data.py` 预检（26.1.2 数据未必需要转换，先跑一遍看报告）。
5. 预期 **2–4 轮**，每轮 30–60 min；每轮只需「真启动一次」就能暴露下一层。

### 4.5 依赖风险

- CEI 2.5.2-c 要求 `create_dragons_plus = 1.11.4-p1`（**精确匹配**）；我们已用同版本，**不要**换成 1.11.8。
- 我方 create-fly 6.0.9-2（CEI 原始要求 ≥6.0.9-4）：已放宽；若后续出现 Create 内部 API 差异，按「CP 改名 + 垫片」补。
- 若用户只要「标签页不再缺失」的**可见**效果，可先只做 DP（它提供 blaze 升级模板/标签页），CEI 稍后 —— 但 CEI 的标签页是用户点名项，建议一起做。

---

## 5. 工具与复现（全部在 `p1/`，可复算）

| 脚本 | 作用 |
|---|---|
| `_inventory.py` | 按 mod id + jar 名相似度重算真实缺口（inventory.json） |
| `_probe_missing.py` | 对每条重查 Modrinth 最新 Fabric（probe-missing.json） |
| `_classify.py` | 生成 §1.1 表（classify.json） |
| `_fetch.py <slug> [--game 26.1.2] [--ver x]` | 下载指定 Fabric 构建 + 校验 sha512 |
| `_relax_deps.py <in> <out> --set depends.minecraft=...` | **只改 fabric.mod.json**，其余 entry 逐字节不变 |
| `_drop_mixin.py <in> <out> <config.json> <SimpleName,…>` | 删失败 mixin（JSON 条目） |
| `_drop_entries.py` / `_add_entry.py` | 删类 / 补 no-op 类 |
| `_jarmeta.py` / `_jarread.py` / `_jarls.py` / `_scanref.py` | 读元数据 / 读条目 / 列条目 / 扫常量池引用 |
| `_mkmods.py <dir> <extra.jar…>` | mods-stable 硬链接 + 候选复制（manifest + SHA） |
| `_launch.py --mods <dir> --game <dir> --tag x --mode world|title` | 全新存档 + 真启动 + 判定 |
| `_summarize.py` | 统计 results-*.jsonl |

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262

# 复现「已落地」候选（Paxi + YungsApi）
python work\run26\port\p1\_mkmods.py work\run26\port\p1\mods-paxi ^
  work\run26\port\p1\work\yungsapi-patched4.jar ^
  work\run26\port\p1\in\Paxi-26.1.2-Fabric-6.1.0.jar
python work\run26\port\p1\_launch.py --mods work\run26\port\p1\mods-paxi ^
  --game work\run26\port\p1\game-paxi4 --tag paxi-world8 --mode world --timeout 200
python work\run26\port\p1\_launch.py --mods work\run26\port\p1\mods-paxi ^
  --game work\run26\port\p1\game-paxi4 --tag paxi-title-final --mode title --timeout 200

# 复现 CEI 首错
python work\run26\port\p1\_mkmods.py work\run26\port\p1\mods-cei ^
  work\run26\port\p1\work\cei-2.5.2c-26.3.jar work\run26\port\p1\work\dp-1.11.4p1-26.3.jar
python work\run26\port\p1\_launch.py --mods work\run26\port\p1\mods-cei ^
  --game work\run26\port\p1\game-cei --tag cei-world --mode world --timeout 200
```

---

## 6. 限制 / 未覆盖（不要当成已验）

1. **Paxi/YungsApi 只到「标题 + 进世界」**：Paxi 全局数据包加载未做玩法级验证；YungsApi 的降级清单见 §3.2。
2. **CEI 本轮没有通过**：只完成「环境 + 首错 + 静态分类 + 下一步」。§4.3 的 P0 两条没修（下一轮第一件事）。
3. **未动 `mods-stable`**：全程硬链接 + p1 内复制（manifest 有每个候选 SHA）。**promote 由 Lead 执行**；建议先 promote Paxi+YungsApi（已达标），CEI 继续作跨轮主线。
4. 每次验收都是**全新存档副本**（`g21/template/lm-final` 拷贝 + 删 session.lock）；未做 long soak。
5. 未测 `gadgets-and-gizmos-bundled` 内嵌的两个真 Java mod（createthrusters 34.6 MB + gadgetsngizmos 2.7 MB），属优先级 2。
