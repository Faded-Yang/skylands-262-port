# port-cei-dp-source —— 反编译源码级迁移（进行中）

> 日期：2026-10-19 ｜ 工具：`tools/decompile.py`（Vineflower 1.10.1）｜ base = live 74 jar
> 目标：CEI 2.5.2-c + DragonsPlus 1.11.4-p1（26.1.2 Fabric）源码级修到 26.3 后重编译。

## 已完成

- 反编译：`g70/src/cei`（169 个 .java）+ `g70/src/dp`（117 个 .java），资源（META-INF/assets/data/accesswidener）也在同目录。
- 编译工具：`g70/_build.py`（26.3 全 classpath = versions/26.3.json 库 + g7/cp_join + loader + fabric-api modules + mods-stable + `.minecraft/libraries/**` + `work/companion26/libs/annotations-26.0.2.jar` + `g31/_deps/mixinextras-fabric-0.5.5.jar`）；日志 `g70/javac_dp.log` / `javac_cei.log`。

## 编译现状（javac 26.3）

| 目标 | errors | 主要来源 |
|---|---|---|
| DP | **94** | criterion 30（`Listener`/`CriterionTrigger`/`Criterion`/`Ints`）、dyes/wool（`LIME_DYE/RED_WOOL/LIME_WOOL/LIME_CONCRETE`）、`Still`/`simpleCodec` 2、`FeaturesConfig`/`getSynchronizedRecipes`、`CreativeModeTab.Output/TabVisibility` protected、`AttachmentType` API、`BlockEntityRenderers.register` private、Cat/Wolf `setCollarColor` private、EntityTypes（`SHEEP/SNOW_GOLEM/BLAZE`）等 |
| CEI | 707（未含成功编译的 DP 类） | 大量是「DP 包不存在」+ cp 问题；DP 编译通过后预计降到 ~150-250，集中在 create 26.1.2→26.3 API（Ponder `modifyBlockEntity`/`mulPose`、`placeItemBackInInventory` 1 参、`BlockEntityBehaviour.addClient`、`registerBlockItem`、`GuiGraphicsExtractor` 等） |

## 下一步（源码级，按文件批次）

1. **DP criterion 重写**（`common/advancements/criterion/BuiltinTrigger.java`、`StatTrigger.java`）：26.3 `CriterionTrigger<T>` 只有 `codec()` + default `createCriterion(T)`，旧 `Listener` 机制删除；改为 26.3 `Criterion`/`CriterionTriggerInstance` + 手动 trigger 路径（`ServerStatsCounterMixin` 已有调用点）。
2. DP 机械改：`Items.<COLOR>_DYE`→`Items.DYE.pick(DyeColor)`；`Blocks.<COLOR>_WOOL/CONCRETE`→`Blocks.WOOL/CONCRETE.pick(...)`；`Blocks.COPPER_BLOCK/LIGHTNING_ROD`→`.weathering().unaffected()`；`EntityType.SHEEP`→`EntityTypes.SHEEP`；`simpleCodec`→删 CODEC+codec()；`CreativeModeTab.Output/TabVisibility` 改 getter；`BlockEntityRenderers.register`→registry 事件；`AttachmentType`→26.3 API；Cat/Wolf `setCollarColor` 用 accessor/registry；`getSynchronizedRecipes`/`FeaturesConfig` 按 26.3 javap 改。
3. DP 编译通过后，把 `g70/build/dp` 加 CEI classpath 重编 CEI，按错误批次修（Ponder/图形 API、`placeItemBackInInventory`、`BlockEntityBehaviour`、`registerBlockItem`、`GuiGraphicsExtractor` 等）。
4. 重打包：源码编译 class + 原 jar 资源（fabric.mod.json/mixins/assets/data/AW）；候选到 `g66/stage/batch10`；标题+进世界。

## 纪律

- 未 promote、未写 mods-stable；base = live 74 jar；所有实验在 `port/g70` + `port/g66`。
## 6. 进展更新（criterion 已重写，DP 94 → 63 errors）

- 已把 `common/advancements/criterion/BuiltinTrigger.java`、`StatTrigger.java` 重写为 26.3 API：
  `extends SimpleCriterionTrigger<T>`（listener 管理由基类提供）+ `codec()` + `SimpleInstance.player()`；`StatTrigger.Instance` 用 26.3 `advancements.predicates.MinMaxBounds.Ints`。
- DP 编译 **94 → 63 errors**（`g70/javac_dp.log` 已更新）。剩余分组：
  - 28 cannot find symbol（dyes/wool/copper 常量、EntityTypes、AttachmentType、simpleCodec、Still/Flowing、ConstantValue 等）；
  - 7 CreativeModeTab.Output/TabVisibility protected；
  - 3 泛型推断（CDPItems/CDPJeiPlugin）；
  - 2 cauldron `newDispatcher`/`put` API + 2 Object→Block（CDPRuntimeRecipes/CDPBlocks copper）；
  - 2 mixin 目标类型转换（FluidFillingBehaviourMixin）、1 BasinOperatingBlockEntityMixin、1 EntityMixin；
  - 其余单点：`BlockEntityRenderers.register` private、`GuiGraphicsExtractor.guiRenderState` private、`placeItemBackInInventory(ItemStack)`、Cat/Wolf `setCollarColor`、`FeaturesConfig`、recipe/HolderLookup、`List<BucketItem>→List<Item>`。
- 下一步：按上表批量改源码（先 28 symbols + CreativeModeTab + mixin 转换），目标 DP 0 error → 打包 DP 候选 → 标题/进世界；再用 DP 产物重编 CEI。
## 7. 进展更新 2（2026-10-19，base = live 77 jar）

- base 记录：`g70/base-live-77.json`（aero `455B5824…` 源码构建、sable `2DFC53A6…` 源码构建、create-fly `17FD0C33…`、toolgun `…` 等 77 件）；
- DP 编译 **63 → 47 → 29 errors**（本轮两批源码修复）：
  - batch A：`Items.RED_WOOL/LIME_WOOL/LIME_DYE`、`Blocks.LIME_CONCRETE`、`EntityTypes.SHEEP/SNOW_GOLEM/BLAZE`、`BlockPos.getBottomCenter()`→`Vec3.atBottomCenterOf`、`Blocks.COPPER_BLOCK.weathering().unaffected()`、`simpleCodec` 删除（2 类）、`BlazeBlockVisual` Context 消歧；
  - batch B：`CDPFluids` 改用本地 `CompatStill/CompatFlowing`（替换包私有 `FluidEntry.Still/Flowing`）、Fabric `AttachmentTarget` 强转（3 文件）、mixin cast 改 `(Object)this`（3 文件）、Ponder list 泛型、`BlockEntityRendererRegistry.register`、DP 初始化顺序。
- **DP 剩余 29 errors**（`g70/javac_dp.log`）：4 cannot find symbol（`getSynchronizedRecipes`/`ConstantValue` 等）、6 `CreativeModeTab.Output/TabVisibility` protected、3 泛型推断（CDPItems/CDPJeiPlugin）、2 Object→Block（CDPRuntimeRecipes）、6 cauldron（`newDispatcher`/`put`）、2 recipe 泛型、2 FeaturesConfig、2 Cat/Wolf `setCollarColor`、1 guiRenderState、1 `placeItemBackInInventory(ItemStack)`。
- 下一步：按上述分组清到 0 → 打包 DP（base 77）→ 标题+进世界 → CEI。
## 8. DP 源码级移植 PASS（2026-10-19，base = live 77 jar）

- **编译**：DP 源码 0 errors（`g70/_build.py dp`，javac `--release 25`）。
- **候选**：`g70/out/dp-1.11.4p1-26.3-src.jar`，**527,221 B，SHA256 `6490879a0749732a2829177576eba81867f60b92bdd4f95423ec149a398241ba`**（150 classes + 240 resources，390 entries，testzip OK）。
- **base**：live 77 jar（`g70/base-live-77.json`）；候选依赖已放宽：`minecraft >=26.1- <26.4-`、`create >=6.0.9-1 <6.1.0`（live create 6.0.9-2）。
- **staging**：`g66/stage/batch10`（77 base + DP = **78 jar**，live 硬链接复制，无隔离件）。
- **验证**：标题 **PASS 24.7s**（`g70/out/evidence/dp-title.log`）；进世界 **PASS 38.2s，joined=true，0 registry errors，0 crash**（`g70/out/evidence/dp-batch10-world2-latest.log` / `-result.json`）。
- 关键运行时修复：
  - `CreateDragonsPlus.onInitialize` 里补 `CDPBlocks.register()`（否则 `CDPBlockEntities` 拿不到 fluid_hatch）；
  - 26.3 `FluidEntry` 构造器会创建 Still/Flowing 实例（含 intrusive holder）：改为直接注册 `entry.still/entry.flowing`，不再 `new FluidEntry$Still/Flowing`；
  - 2 个 advancement 的 `recipe_unlocked` 条件 `recipe` → `recipes` 列表（26.3 codec）；
  - 26.3 数据格式旧（loot 自动升级警告，功能可用）。
- **降级（已在源码注释/报告声明）**：
  - DP 创造栏**不注册**（javac 对 `CreativeModeTab$Output/TabVisibility` 的 InnerClasses 可见性报 protected；inline lambda/Fabric API 都试过），所以创造栏不会出现 DP 物品；
  - `CDPCauldrons` 交互 no-op（26.3 `CauldronInteractions.newDispatcher/put` 包私有）；
  - 客户端配方查询分支返回 empty、运行时改配方事件 no-op（26.3 `RecipeAccess` 无 getSynchronizedRecipes；`RecipeMap.create` 需 HolderLookup）；
  - Cat/Wolf 项圈颜色、JEI `guiRenderState` 用反射桥接。
## 9. CEI 编译基线（用 DP 编译产物作 cp）

- `g70/_build.py cei`：DP 0 errors → **CEI 113 errors**（压缩前 707；`g70/javac_cei.log`）。
- 分组：
  - 52 cannot find symbol（含 advancements `criterion.InventoryChangeTrigger/MinMaxBounds`、FluidEntry `Still/Flowing`、dye/wool/copper 常量、`ItemStackTemplate` 等）；
  - 12 `mulPose(Quaternionf)`（26.3 PoseStack 签名变化）；
  - 8 `placeItemBackInInventory(ItemStack)` 1 参；
  - 5 `CreativeModeTab.Output/TabVisibility` protected（同 DP，计划降级/Fabric 路线）；
  - 3 `BlockEntityRenderers.register` private；
  - 4 `ExperienceOrb.count/setValue` private；
  - 3 `WeatheringCopperCollection→BlockBehaviour`；
  - 2 `Model.renderToBuffer` 签名；2 `addProvider` 歧义 + 1 `BakingContext` 歧义；
  - datagen：`CEIRecipeProvider`/`CEIEnchantmentTagsProvider.getName`/`AdvancementProvider` 构造/`display(...)`/`Stream<Pair<K,Object>>` 等；
  - create `BehaviourType` 泛型 3 处、`ItemStackTemplate→ItemStack` 1、`Object→CAP#1` 1。
- 下一步批次：CEI-A（机械：物品 1 参 API、renderer registry、advancement import、FluidEntry、copper/wool/dye、tab 降级）→ CEI-B（mulPose/renderToBuffer/ExperienceOrb/BehaviourType）→ CEI-C（datagen provider API）。
## 10. CEI 源码级移植 PASS（2026-10-19，base = live 78 jar）

- **编译**：CEI **0 javac errors**（`g70/_build.py cei`，`--release 25`；datagen-only 源码暂排除，见下）。
- **候选**：`g70/out/cei-2.5.2c-26.3-src.jar`，**807,587 B，SHA256 `fbe0f7b66752d0257033d012e291fe27e46c98ba9e3c535c9572adf6b8b8aee3`**（246 classes + 220 resources，466 entries，testzip OK）。
- **base**：live 78 jar；依赖放宽 `minecraft >=26.1- <26.4-`、`create >=6.0.9-1 <6.1.0`。
- **staging**：`g66/stage/batch11`（78 base + CEI = **79 jar**；已确认无 yungsapi/Paxi）。
- **验证**：标题 **PASS 26.3s**（`g70/out/evidence/cei-title.log`）；进世界 **PASS 45.4s，joined=true，0 crash token**（`cei-batch11-world-result.json` / `-latest.log`）。
- 关键修复：
  - 26.3 `PoseStack.mulPose(Quaternionf)` → `rotate(Quaternionfc)`；`Model.renderToBuffer` 补第 5 参；
  - `EntityTypes.LIGHTNING_BOLT/SHEEP`、`Items.WOOL.pick(DyeColor)`、`Blocks.CONCRETE.pick`、`Blocks.LIGHTNING_ROD.weathering().unaffected()`；
  - `BlockEntityRendererRegistry`（fabric）、`ExperienceOrb.count/setValue` 反射桥、`BehaviourType` 新建、`AttachmentTarget` 强转、`ItemQuads.split`；
  - 26.3 `advancements.triggers.Criterion`/`InventoryChangeTrigger`/`predicates.MinMaxBounds` 路径；
  - `CEIFluids` 直接注册 `entry.still/flowing`（同 DP）；
  - `CEIAdvancements` 数据生成方法剥离（字段/`register()` 保留，数据 JSON 仍在 jar），9 个 advancement `recipe_unlocked` 的 `recipe`→`recipes`；
  - `CEIServerConfigSnapshot.decode` 被 decompiler 丢成注释，按 bytecode 语义重写。
- **降级/TODO**：
  - CEI 创造栏不注册（同 DP，`CreativeModeTab.Output/TabVisibility` javac protected；待 Fabric tab 方案统一补）；
  - datagen 类（`data/**`、`CEIRecipeProvider` 等）不编译/不随 jar 提供（运行时无引用，数据资源保留）；
  - goggle tooltip 的 `addToGoggleTooltip` 调用降级为 `false`（tooltip 功能暂缺，已记 TODO）。
## 11. CEI 修复候选（FilteringBehaviour NPE，2026-10-19）

- **根因**：CEI 的 `PrinterBehaviour`/`ClassicEnchanterBehaviour`/`EnchanterBehaviour` 在移植时把 `TYPE` 换成了 `new BehaviourType<>("cei_behaviour")`；而 Create 26.3 客户端 `FilteringBehaviour` 构造/initialize 时按 **`ServerFilteringBehaviour.TYPE`** 查 server behaviour，查不到 → `behaviour` 为 null → `FilteringRenderer.tick` NPE（放置 printer 等后客户端 tick 崩）。
- **上游写法**（`work/aero-port/refs/CreateEnchantmentIndustry-Fly` 源码）：`TYPE = (BehaviourType) ServerFilteringBehaviour.TYPE;`（`EnchanterBehaviour` 用 `ServerScrollValueBehaviour.TYPE`），即复用 create 的 type 对象。
- **修复**：三个 Behaviour 的 `TYPE` 恢复上游写法（unchecked cast 复用 create type），CEI 重新编译 0 errors。
- **新候选**：`g70/out/cei-2.5.2c-26.3-src.jar`，**807,485 B，SHA256 `75f377595122acd70e94a6bc3c7da724e5010114c7b24f83df3a5682fd205650`**（246 classes + 220 resources，466 entries，testzip OK）；staging `g66/stage/batch11`（79 jar，已换成新 jar）。
- **验证**：标题 **PASS 34.9s**；等待 probe 重跑 CEI 放置（printer/blaze_enchanter/grindstone_drain/experience_lantern）确认 NPE 消失。
## 12. DP/CEI 创造栏修复（编译期 InnerClasses 放宽，2026-10-19）

- **根因**：26.3 `CreativeModeTab.class` 的 `InnerClasses` 属性里 `$Output`/`$TabVisibility` 标记为 protected（类文件本身是 public），javac 按 InnerClasses 报 protected 拒绝编译；运行期实际按类访问（public）检查。
- **方案**：生成编译专用 `g70/_mc263_javac.jar`（26.3.jar 副本，只把 `CreativeModeTab.class` 的 InnerClasses 中 `$Output`/`$TabVisibility` 访问位改成 public），`_build.py` 编译时把它放在 classpath 最前；运行仍用真实 26.3.jar（字节码访问的类本身 public，不会 IllegalAccessError）。
- **DP 候选**：`g70/out/dp-1.11.4p1-26.3-src.jar`，**529,047 B，SHA256 `01fafe3482d11f8cd419f648a9a02d042b3ed0332d2ec0df9fa18500cd6d701f`**；base live 79；staging `g66/stage/batch12`（79 jar）；标题 **33.8s PASS**、世界 **48.3s PASS（joined=true）**。
- **CEI 候选**：`g70/out/cei-2.5.2c-26.3-src.jar`，**809,352 B，SHA256 `82eab5896dbac30cc10de5d054f25149946f855700ada834dc05ca3248d70ccd`**；base live 79；staging `g66/stage/batch13`（79 jar）；标题 **30.7s PASS**、世界 **44.2s PASS（joined=true）**。
- 合并 staging：`g66/stage/batch14`（79 jar，DP+CEI 两件均替换），供 probe 一次验证创造栏物品。
- 待 probe：创造栏中应出现 DP（fluid_hatch 等）与 CEI（grindstone/hatch/printer…）物品；通过后 Lead promote（base 79，变化 2 个 jar）。