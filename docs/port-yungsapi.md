# port-yungsapi —— yungsapi 26.3 源码级移植（暂停中，路线 A）

> 2026-10-19 建档。Lead 决策：**路线 A（全源码移植）**，B（二进制止血）否决（`StructureProcessorType` 泛型 flip 的 ctor 重定向易再 ICCE）。
> 时间窗原因：本轮不启动大批量改动，恢复后按批次推进。yungsapi/Paxi 期间保持隔离（`port/g72/quarantine/`）。

## 0. 产物与基线

- 原始 jar：`work/run26/port/g72/quarantine/yungsapi-patched4.jar`（1,303,055 B）；
- 反编译产物：`work/run26/port/g70/src/yungsapi`（**167 java**，Vineflower via `tools/decompile.py`）；
- 编译命令：`python work/run26/port/g70/_build.py yungsapi`；日志 `g70/javac_yungsapi.log`；
- **编译基线：131 errors**。

## 1. 错误分组（基线 131）

| # | 组 | 数量 | 说明 |
|---|---|---|---|
| G1 | `StructureProcessor` / `StructureProcessorType` 类型翻转 | ~10 | 26.3 `StructureProcessor` class→interface；`StructureProcessorType<T>` 泛型 class→非泛型 interface；`StructureEntityProcessor extends StructureProcessor`；`StructureProcessorType` 使用处去泛型；`Registry.register(STRUCTURE_PROCESSOR, id, ...)` 目标类型变化 |
| G2 | `DensityFunction` / `DensityFunctions` 包迁移 | 5 | 26.3 移到 `worldgen.density` 子包（新路径名以 26.3 javap 为准） |
| G3 | `cannot find symbol` 杂项 | 81 | 含 `EntityType` 构造/`EntitySpawnReason`→`EntitySpawnRequest`、`StateHolder.setValue` 签名、`MetadataSection`/DataPackResources、Fabric API 小项、reflections 依赖等 |
| G4 | Fabric API 迁移 | 3 | `FabricPotionBrewingBuilder`、`CompostableRegistry` 等模块/类型路径变化 |
| G5 | reflections 依赖（`org.reflections.*`） | 4 | yungsapi 自带反射扫描依赖；需决定 shade/版本或删除相关 auto-register 功能 |
| G6 | 其它 | 剩余 | `StructureProcessor cannot be converted to StructureEntityProcessor`（3，checkcast 链）、`EntityType` ctor、`apply(Instance<Piece...>)` 泛型、mixin cast（NoiseChunkMixin）等 |

## 2. 批次计划（恢复后按序）

### 批次 Y1：StructureProcessor/Type 类型链（核心崩溃）
- 文件：`com/yungnickyoung/minecraft/yungsapi/world/processor/StructureEntityProcessor.java`、`api/world/structure/processor/StructureEntityProcessorBuilder.java`、`mixin/EntityProcessorMixinFabric.java`、`module/StructureProcessorTypeModuleFabric.java`、`services/FabricStructureProcessorHelper.java`、`world/structure/jigsaw/element/{YungJigsawSinglePoolElement,MaxCountSinglePoolElement,MaxCountLegacySinglePoolElement}.java`；
- 改法：`extends StructureProcessor`→`implements StructureProcessor`；所有子类补 `codec()`（或保持 abstract 由具体类实现）；`StructureProcessorType<T>` 全部去泛型、`StructureProcessorType` 注册改用 26.3 的 `Registry<MapCodec<? extends StructureProcessor>>` 语义；checkcast `StructureProcessor→StructureEntityProcessor` 保持运行期语义（必要时 `(Object)` 中转）；
- 验收：javac 通过 + 世界生成 processor 加载冒烟。

### 批次 Y2：DensityFunction 包迁移
- 按 26.3 javap 找新包（`net.minecraft.world.level.levelgen.density.*` 等），全局 import/类型替换；
- 验收：javac 通过。

### 批次 Y3：杂项 API/反射/Fabric
- `EntitySpawnReason`→`EntitySpawnRequest`、`EntityType` ctor、`StateHolder.setValue`、`MetadataSection`/DataPackResources、`EntityProcessorMixinFabric` 等；
- reflections：优先找 26.3 兼容版本或本地 shade；若 auto-register 不需要可临时禁用相关类（记录降级）；
- Fabric API：`FabricPotionBrewingBuilder`/`CompostableRegistry` 路径按 26.3 fabric-api 模块修正；
- 验收：javac 0 errors。

### 批次 Y4：打包 + 验证
- 按 CEI/DP 方式打包（原 jar 资源 + 编译 classes；mixin refmap 去除；AW namespace 校验；`minecraft >=26.1- <26.4-`）；
- staging：`g66/stage/`（base = promote 时的 live）；标题+进世界；**结构生成专项**（worldgen/structure processor 路径）由 probe 验证；
- 若世界生成仍 ICCE，先查所有直接 extends `StructureProcessor`/`StructureProcessorType` 的类是否都已切 interface。

## 3. 风险 / 备注

- `StructureProcessorType` 26.3 无泛型、无抽象方法（interface）；yungsapi 的注册 API 需要按 26.3 `MapCodec` 体系重写；
- 反射依赖（reflections）可能引入额外类加载失败，优先级低于处理器链；
- 期间 yungsapi/Paxi 保持隔离，不进入任何 staging/候选；
- 本文件为暂停期交接，恢复后按 Y1→Y4 继续。
## 4. 进展（2026-10-19）

### Y1 ✅（131 → 112 errors）
- `StructureEntityProcessor implements StructureProcessor`；
- 自定义 processor 类型改 26.3 `MapCodec<? extends StructureProcessor>`（手写 MapEncoder/MapDecoder unit codec，补齐 compressor/keys）；
- `StructureEntityProcessorBuilder.build()` 返回 MapCodec；修复 F 泛型；`EntityTypes.ARMOR_STAND/ITEM_FRAME`；
- `StructureProcessorTypeModuleFabric` 注册改为 `MapCodec`；
- G1（StructureProcessor/Type）错误清零。

### Y2a ✅（112 → 99 errors，降级）
- 禁用 `BeardifierMixin` / `NoiseChunkMixin` / `EnhancedBeardifierHelper`（26.3 `FunctionContext`/`ContextProvider`→`SamplerContext`、`BeardifierOrMarker` 删除，暂不迁移）；
- 效果：beardifier 增强失效（服务 YUNG's Better*，未安装）；
- 混合包中已从 mixin config 移除这两个 mixin。

### hybrid 冒烟件（仅冒烟，不交付）
- `g70/out/yungsapi-hybrid-y1.jar`：原 `yungsapi-patched4.jar` + 仅替换 **Y1 的 5 个源文件（14 个 class）**；SHA256 `9069da54dd909439a82549f63feeed7b4d7e62e4b62afb0977a7fbe3bf3a474f`（1,300,158 B）；
- staging：`g66/stage/yungsapi-hybrid`（**80 jar** = 当前 live 79 + hybrid yungsapi）；
- 目标：证明 `StructureEntityProcessor` 的 `IncompatibleClassChangeError` 消失（结构生成 smoke）；不代表 yungsapi 整体可交付。

### 下一步
- Y3：79 cannot find symbol（EntitySpawnReason→EntitySpawnRequest、StateHolder.setValue、MetadataSection/DataPackResources、Fabric API、reflections 等）→ 目标 0 errors；
- Y4：全量打包（base=当时 live）+ 标题/进世界 + 结构生成专项 probe。
## 5. Y3 分析（99 errors，2026-10-19）

26.3 worldgen API 有**结构性重命名/删除**，不是简单移包：
- `FeaturePlaceContext`、`BasaltColumnsFeature`、`ConfiguredFeature`、`NoneFeatureConfiguration`、`BasaltColumnsFeature` 等类在 26.3.jar 中不存在（需按新 API 重写/替代）；
- `PlacementModifierType` → `PlacementModifierTypes`（复数类）；`StructurePlacementType` → `StructurePlacements`；
- `DeltaFeatureConfiguration`/`UnderwaterMagmaConfiguration` 类名变化（26.3 有 `DeltaFeature`/`UnderwaterMagmaFeature`，config 名需查）；
- `EntitySpawnReason` 仍在，但 26.3 新增 `EntitySpawnRequest`（`EntityType`/`finalizeSpawn` 参数改用它）；
- `StructureProcessorType` 相关（Y1 已改 MapCodec）。

Y3 建议再分：
- **Y3a 低风险**：CriterionTrigger 路径（`advancements.triggers`）、EntitySpawnRequest、StateHolder.setValue、MetadataSection/DataPackResources、Fabric API（FabricPotionBrewingBuilder/CompostableRegistry）、reflections（jar 在 `src/yungsapi/META-INF/jars/reflections-0.10.2.jar`，可加 cp）；
- **Y3b 中风险**：feature/placement/structure 类型重命名迁移（FeaturePlaceContext、BasaltColumnsFeature、ConfiguredFeature、PlacementModifierTypes、StructurePlacements 等，需逐个查 26.3 新类）；
- **Y3c 大**：`YungJigsawStructure`/jigsaw assembler 的 `JigsawStructure` 字段/构造变化（16+7 errors，startPool/startJigsawName/maxDepth/... 字段在 26.3 可能改 record/参数）；
- **Y3d 杂项**：mixin 目标类迁移（NoDeltas/NoMagma/NoVines 对应 feature 类名）、BLACK_WALL_BANNER→`Blocks.WALL_BANNER.pick(DyeColor.BLACK)`、BuildCallback、AutoRegisterEntityType 等。

当前 99 errors；hybrid `9069da54` 待 probe 结构生成 smoke 结果。
## 6. Y3a + Y3b 完成（99 → 32 errors，2026-10-19）

### Y3a（99 → 64）
- reflections：`src/yungsapi/META-INF/jars/reflections-0.10.2.jar` 加入编译 cp；
- `CriterionTrigger` → `advancements.triggers.CriterionTrigger`（2 文件）；
- `FabricAutoRegisterHelper`：`registerBrewingRecipe`/`addCompostableItem` 降级 no-op（26.3 Fabric API 无对应类）；
- `EntityType.create(..., EntitySpawnRequest)`；`StateHolder.setValue` raw cast（2 文件）；`LocateReplacerDataPackResources` 降级 no-op Source（Pack.ResourcesSupplier 重构）。

### Y3b（64 → 32）
- 禁用 4 个 feature-removal mixin（NoDeltas/NoMagma/NoVines/NoBasalt；26.3 已无对应 feature 类）；
- `PlacementModifierTypeModuleFabric` 注册改 `MapCodec`；`AutoRegisterFieldRouter` 的 `instanceof` 改 `MapCodec`；
- `JigsawBlockInfo` 访问器：`.info().pos()`→`.pos()`、`.info().state()`→`.state()`（26.3 record 直接字段）；
- `Blocks.BLACK_WALL_BANNER`→`Blocks.WALL_BANNER.pick(DyeColor.BLACK)`；`MaxCountFeaturePoolElement.toString` 简化；`ServerLevelMixin` raw `Either.left()` cast。

### 映射依据（refs/mc26.3）
- `net/minecraft/world/level/levelgen/placement/PlacementModifierTypes.java:7-8`：interface + `bootstrap(Registry<MapCodec<? extends PlacementModifier>>)` 返回 MapCodec；
- `net/minecraft/world/level/levelgen/placement/PlacementModifier.java:11-16`：`codec()` 取代旧类型注册；
- `net/minecraft/world/level/levelgen/structure/placement/StructurePlacement.java:11-28`：`codec()`；
- `net/minecraft/world/level/levelgen/structure/templatesystem/StructureTemplate.java:772-793`：`JigsawBlockInfo` record 字段 `pos/state/...`；
- `net/minecraft/world/level/levelgen/RandomState.java:107,126`：`samplersWithContext`/climate sampler；
- 26.3 refs 与 26.3.jar 均无 `FeaturePlaceContext`/`ConfiguredFeature`/`BasaltColumnsFeature`/`NoneFeatureConfiguration`/`DeltaFeatureConfiguration`/`UnderwaterMagmaConfiguration`。

### 剩余 32 errors
- **Y3c（~18）**：`YungJigsawStructure` 的 `JigsawStructure` 字段/构造（startPool/startJigsawName/maxDepth/startHeight/xOffsetInChunk/...）与 `settingsCodec`；
- 单点 ~14：`MaxCountFeaturePoolElement` 仍引用 ConfiguredFeature（toString 简化后仍有一处 import/类型需清）、`ModResourcePackCreatorMixinFabric` 的 `@Nullable` 类型注解位置、`AutoRegisterEntityType` 构造、`PieceInRangeCondition`/`PieceInHorizontalDirectionCondition` codec（record 字段访问 + MapCodec apply）、`BiomeCondition` `RandomState.sampler()`、`ServerLevelMixin` 方法引用、`EntityTypeModuleFabric`/`FeatureModuleFabric` 注册、`YungJigsawSinglePoolElement` modifiers/codec、`YungJigsawFeatureElement` `StructureBlockInfo.of`、`FabricBlockEntityTypeHelper`、`MixinUtils` `getStartForStructure`。
- 等 hybrid `9069da54` probe 结果后再开 Y3c（Lead 指示）。
## 7. Y3c + Y4 完成（0 errors → 全量候选，2026-10-19）

### Y3c（24 → 0 errors 的关键）
- 根因是 decompile 后 `RecordCodecBuilder.mapCodec` 的类型推断丢失：`builder` 被推断成 `Instance<Object>`，导致 `settingsCodec` 与所有字段 `forGetter` 报错；
- 修复：显式类型见证 `RecordCodecBuilder.<YungJigsawStructure>mapCodec(...)`（同理 `YungJigsawSinglePoolElement`、`PieceInRangeCondition`、`PieceInHorizontalDirectionCondition`）；
- `PieceInHorizontalDirectionCondition` 构造 lambda 参数修正为 `(pieces, range, rotation)`；
- 其余单点：`EntityType` 26.3 构造器（`TagKey<Block> immuneTo` + `trackDeltas`）、`BiomeSource.getNoiseBiome` 改用 `createCachingResolver(randomState)`、`FabricDefaultAttributeRegistry.register` 泛型 cast、`StructureModifier` 包名、`StructureManager.getStartForStructure(structure, chunk)`、`JigsawBlockInfo.parse`、`BuiltInRegistries.FEATURE_TYPE` + `Feature.codec()`、`RandomState.createClimateSampler` 等。

### Y4：全量候选
- jar：`g70/out/yungsapi-26.3-src.jar`，**1,273,188 B，SHA256 `d0b664eea313fef1530a7422dc116f1350378e09e0c4e55b9049de71378b23d2`**（207 classes + 25 resources，232 entries，testzip OK）；
- base：live 79 jar；staging `g66/stage/batch15`（**80 jar** = 79 + yungsapi）；
- 依赖放宽 `minecraft >=26.1- <26.4-`；mixin config 移除 6 个已禁用 mixin（Beardifier/NoiseChunk/NoDeltas/NoMagma/NoVines/NoBasalt），refmap 去除；
- 验证：标题 **PASS 51.3s**；进世界 **PASS 40.3s，joined=true，0 crash**。

### 降级清单（yungsapi）
- beardifier 增强（2 mixin）停用；结构内去 feature（4 mixin）停用；
- Fabric 酿造/堆肥自动注册 no-op；locate replacer 数据包 no-op；
- AutoRegisterEntityType：`immuneTo` 传 null、`trackDeltas=false`（自定义实体免疫/跟踪细节丢失）；
- 其余 API 均为 26.3 等价迁移。

### 待 probe
- 结构生成专项（同 hybrid 的 10 次传送/320 tick 方法）在 **全量候选** 上复测，确认 ICCE 仍为 0；通过后再 promote（79→80，只 +yungsapi）。