# Farmer's Delight 系食物 mod → MC 26.3 Fabric 移植报告

> 轮次：g8（承接 g6 interiors / g7 create-framed 的流水线）
> 验收口径：**进世界为完成**（`tools/watch_world.py` 的 `WORLD_OK`），推进 `mods-stable` 后再复跑标题。
> 存档：每测前从 `work/run26/watch/saves/New World (1)` 重拷一份全新副本到 `work/run26/stag1/saves/`。

---

## 0. 结论速览

| mod | mod id | 来源 | 结果 | 卡点/修法 |
|---|---|---|---|---|
| **FarmersDelight** | `farmersdelight` | 官方 26.3 构建 `26.3-3.6.28` | ✅ **WORLD_OK**（基线） | 无需移植，直接装 |
| **Chef's Delight** | `chefsdelight` | 官方 **26.2 Fabric** 构建（Modrinth `1.0.6-fabric-26.2`） | ✅ **WORLD_OK** | 26.2→26.3 只有 3 处差异：`Int2ObjectMap.entry/ofEntries`（CFR 静态导入残影）、`StructureTemplatePool` 私有字段、`NumberProvider` 重构的 datagen |
| **Corn Delight** | `corndelight` | 官方 **1.21.1 Fabric** 构建（Modrinth `corn-delight-fabric 1.21-1.0.0`） | ✅ **WORLD_OK** | 1.21.1→26.3：方块/物品 id、食物效果→Consumable、`ItemInteractionResult`、标签与配方格式 |
| **End's Delight** | `ends_delight` | 官方 **1.21.1 Fabric**（refabricated 2.6） | ✅ **WORLD_OK** | 1.21.1→26.3：`Consumable`、`ToolMaterial`、`updateShape`、创造标签页、数据层（smithing/fabric:any/战利品条件） |
| **Cultural Delights** | `culturaldelights` | Fabric 0.17.7 | ❌ 未完成 | 编译到 40 错：世界生成/tree/leaves/strip 体系在 26.3 全部重构 |
| **My Nether's Delight** | `mynethersdelight` | Fabric refabricated 2.0.4 | ⏳ 未开始 | 与 CD 同类，规模更大（97 类） |
| **Miner's Delight** | `minersdelight` | **只有 NeoForge 构建** | ⏳ 未开始 | 需要 NeoForge API 垫片（DeferredRegister/IEventBus） |
| **Abnormals Delight** | `abnormals_delight` | **只有 NeoForge 构建**（依赖 blueprint） | ⏳ 未开始 | 同上 + Team Abnormals 的 blueprint 库 |

**交付物 `work/run26/mods-stable`：61 jar → 65 jar**
（+FarmersDelight 26.3 官方、+chefsdelight 1.0.6-26.3、+corndelight 1.0.0-26.3、+ends_delight 2.6-26.3）。

**最终验收（都在交付物本体上复跑过）**：

| 集合 | 标题 | 进世界 |
|---|---|---|
| 61 + FarmersDelight（62） | 隐含于下次 | ✅ `WORLD_OK 38.1s` |
| 63（+chefsdelight） | ✅ `TITLE_SCREEN_OK 23.9s` | —— |
| 64（+corndelight） | ✅ `TITLE_SCREEN_OK 22.6s` | —— |
| **65（+ends_delight，交付物本体）** | ✅ `TITLE_SCREEN_OK 22.9s` | ✅ **`WORLD_OK`** |

交付集本体的进世界证据（`work/run26/port/g8/_world_stable65.log`）：
`logged in with entity id 5` / `Loaded 2343 advancements` / **`Registry loading errors: 0`** /
**mixin 失败 0** / `Loading 144 mods`。

---

## 1. 26.3 的硬门槛（本轮实测，按踩坑顺序）

### 1.1 方块/物品 id 必须**在构造之前**设好（本轮最大的坑）

26.3 里：

* `BlockBehaviour(Properties)` 构造器第一件事就是 `properties.effectiveDescriptionId()`
  ⇒ id 为 null 当场 NPE：`Block id not set`
* `Item(Properties)` 构造器调用 `itemIdOrThrow()`，并拿这个 key 去登记
  `DataComponentInitializers` ⇒ 同样必须在 `new Item(...)` **之前**

所以「先注册、后补 id」整体不可行（占位 id 会把物品模型/组件一起带歪）。
上一轮 cultural/ends 卡在 `Block id not set` 就是这个原因。

**本轮定下的修法（`work/run26/port/g8/_idfix.py`，全 mod 复用）**

1. 把 `BlockBehaviour.Properties.of/copy/...` 与 `new Item.Properties(...)` **整条链**
   包成 `Reg.pb(...)` / `Reg.pi(...)`；
2. `Reg.pb/pi` 从 **ThreadLocal 名字栈**里取当前注册名，调
   `setId(ResourceKey.create(Registries.BLOCK/ITEM, id(name)))`；
3. 注册助手在 `supplier.get()` 前后 `Reg.push(name)` / `Reg.pop()`；
   对「立即构造」的 mod（corn），把 `registerX("name", EXPR)` 机械改写成
   `registerX("name", Reg.with("name", () -> EXPR))`。

> ⚠ **名字栈必须是栈**：物品构造里会触发方块类初始化（嵌套注册），
> 单个 ThreadLocal 会被内层 `pop()` 清空 ⇒ 外层取不到名字（实测第一次跑就 NPE 在这）。

### 1.2 26.3 的 `Properties` 工厂认的是**26.3 名**，i21n 表只到 1.21.1 名

`work/run26/port/g7/map.json` 是 **intermediary → 1.21.1 官方名**，不是 26.3 名：

* 8254 条里 **1727 条**在 26.3.jar 里根本不存在（如 `ResourceLocation` 已改名 `Identifier`）
* 内类 key 是 `class_4970$class_2251`，而 CFR 反编译写的是 `class_4970.class_2251`（点号）
  ⇒ g7 的 `_rewrite_src.py` 会漏改长 key、再用短 key 顶替，产出
  `BlockBehaviour.LootItemRandomChanceWithEnchantedBonusCondition1` 这种垃圾

**本轮修法**：新写 `_rewrite26.py`（点号形式也建 key、按长度降序替换），
再叠一张 **自动推导的 1.21.1→26.3 类改名表** `map_121_263.json`
（`_mkmap.py`：拿 `libraries/.../client-1.21.1-srg.jar` 的类名当 1.21.1 官方名，
对「26.3 没有」的类按简单名唯一匹配回填，得到 **612 条**搬迁映射，
例如 `advancements.critereon.*` → `advancements.predicates.*`）。

### 1.3 javac classpath 里混着 **1.21.1 的 client jar**（危险的假成功）

`g7/cp_join.txt` 里有
`libraries/net/minecraft/client/1.21.1-.../client-1.21.1-...-srg.jar`。
留着它，javac 会把 26.3 已删的类解析到 1.21.1 上：**编得过、运行期 `NoClassDefFoundError`**
（实测 corn 的 `ItemNameBlockItem` 就是这样炸的）。

⇒ `_javac8.py` 现在显式剔除 `libraries/net/minecraft/client/**`，只留 `26.3.jar`。

### 1.4 数据层（26.3 与 1.21.1 的实际差异，全部实测）

| 项 | 1.21.1 | 26.3 |
|---|---|---|
| 目录 | `recipes/` `loot_tables/` `advancements/` `tags/{blocks,items}` `worldgen/configured_feature` | `recipe/` `loot_table/` `advancement/` `tags/{block,item}` **`worldgen/feature`** |
| 配方成分 | `{item:x}` / `{tag:t}` / `[a,b]` | **`"x"` / `"#t"`** / `{"fabric:type":"fabric:any","ingredients":[...]}` |
| 配方结果 | `{item, count}` | `{id, count}` |
| 熔炉类 category | 任意 | 只认 `food/blocks/misc` |
| 战利品条件 | `"conditions": [..]`，条件对象用 `"condition"` 键 | **`"condition"`（单数）**，条件对象用 **`"type"`** 键 |
| `minecraft:block_state_property` | 有 | **已删除** ⇒ 整条条件剥掉 |
| 进度表 | `recipe_unlocked` 的 `recipe` | **`recipes: [..]`** |
| 物品模型入口 | `assets/<ns>/models/item/*.json` | **`assets/<ns>/items/<id>.json`**（不生成物品不可见） |
| 渲染层 | Fabric `BlockRenderLayerMap` | **方块模型里的 `"render_type": "minecraft:cutout"`** |
| `c:` 约定标签 | `c:foods/vegetables` `c:foods/milk` `c:foods/cooked_pork` `c:seeds/corn` | `c:foods/vegetable` `c:drinks/milk` `c:foods/cooked_meat` `c:seeds` |
| 世界生成特性 | FD `farmersdelight:wild_crop` | FD `farmersdelight:in_order`（`features[]` 数组） |

转换器：`work/run26/port/g8/_convert_dl.py`（含**标签存在性校验**：
引用缺失标签的配方直接丢弃并记账，避免整个数据包 parse 失败）。

### 1.5 Fabric API 在 26.3 侧的搬迁

* `itemgroup.v1.FabricItemGroup` → **消失**：用原版 `CreativeModeTab.builder(Row.TOP, 0)` 注册，
  再用 `net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents.modifyOutputEvent(key)` 填物品
* `blockrenderlayer.v1.BlockRenderLayerMap` → **消失**：改成方块模型 `render_type`
* `registry.CompostingChanceRegistry` / `FuelRegistry` → **消失**（改成物品组件 / 数据驱动）

---

## 2. 逐 mod 详情

### 2.1 FarmersDelight 26.3（✅ 基线）

官方构建 `FarmersDelight-26.3-3.6.28+refabricated.jar` 直接放进 staging：
`mods-stable(61) + FD` ⇒ `WORLD_OK 38.1s`。promote 后 `63 jar` ⇒ `TITLE_SCREEN_OK 23.9s`。

### 2.2 Chef's Delight（✅）

原包给的是 NeoForge `chefsdelight-1.0.6.jar`，但 Modrinth 有 **Fabric 26.2** 构建
（`1.0.6-fabric-26.2`，作者 Redstone Games）。26.2→26.3 只差一代，比从 1.21.1 移植便宜得多：

1. 反编译（CFR 0.152）后**直接对着 26.3.jar 重编**（不经过 i21n）；
2. 17 类里 3 个是纯 datagen（`ChefsDelightDataGenerator` / `ModVillagerTrades` /
   `ModVillagerTradeTags`）⇒ 删掉、`entrypoints` 去掉 `fabric-datagen`；
3. `ModTradeSets` 只留 `ResourceKey<TradeSet>` 常量（内容在数据包，不在代码）；
4. `Int2ObjectMap.entry/ofEntries` 是 **CFR 静态导入残影**，真名在 `Int2ObjectMaps`，
   而且 `ofEntries` 根本不存在 ⇒ 换成自写 `trades(...)` 助手；
5. `VillageStructures` 要改 `StructureTemplatePool.templates/rawTemplates`
   （26.3 是 **private final**）⇒ 反射拿列表引用**原地改**；
   `rawTemplates` 还可能塞的是**不可变 List**（`ImmutableCollections`）⇒ 必须反射**换引用**
   （`Field.set`，仅实例 final，Java 25 可用）；
6. `fabric.mod.json` 的 `minecraft` 约束 `~26.2` → `>=26.1- <26.4-`。

结果：`WORLD_OK 36.1s`；日志只有一条自愈提示
`Upgrading pre-26.3 data from 'chefsdelight' ... (loot_table chests/cooker)`（仍能用）。

### 2.3 Corn Delight（✅）

原包是 NeoForge `corn_delight-1.2.10`，改用 Modrinth 的
**`corn-delight-fabric 1.21-1.0.0`**（同名 fabric 移植，mod id 是 `corndelight`，
内容比 1.2.10 少一些，见 §4）。

编译：14 java → 删 datagen 6 类 → 9 类 0 错。除 §1 的通项外，这个 mod 特有的点：

* `ItemNameBlockItem` 26.3 已删 ⇒ 用 `BlockItem`（名称走 lang，不再取方块名）
* `ComposterBlock.COMPOSTABLES` 已删 ⇒ **堆肥概率不复刻**（降级）
* `Blocks.WHITE_WOOL` → `Blocks.WOOL.white()`（彩色方块统一成 `ColorCollection`）
* `MobEffects.DAMAGE_BOOST` → `STRENGTH`
* `BonemealableBlock` 三个方法都多一个 `BonemealSource`
* 数据：35 配方 / 22 进度 / 5 战利品表 / 24 物品模型 / 1 世界生成特性
  （`wild_crop` → `in_order` + `count:64`），**0 丢弃**

结果：`WORLD_OK`。踩过的 5 个数据层坑全部记在 §1.4。

### 2.4 End's Delight（✅）

原包 NeoForge，改用 Fabric `ends_delight-2.6+refabricated.1.21.1`。
35 java → 30 类 0 错。代码层修法：

* 食物效果/进食速度 → `Consumable`（46 个 `_FX` 常量）
* `Tier` → `ToolMaterial`；`ToolMaterial` 是 **record**，1.21.1 那种匿名 `new Tier(){}` 不可能
  ⇒ 4 个自定义材料**降级**成原版常量（NETHERITE/STONE/IRON/DIAMOND），刀的数值变，功能不变
* `DrinkableItem` / `PopsicleItem` / `HotCocoaItem` 在 FD 26.3 已删 ⇒ 改挂 `ConsumableItem`
* `updateShape` 新签名（多 `ScheduledTickAccess` + `neighborPos` + `RandomSource`）
* 方块 codec（`simpleCodec`/`codec()`）在 26.3 已整体移除 ⇒ 删字段
* `BlockEntityType.Builder` 删了 ⇒ `FabricBlockEntityTypeBuilder`
* `PushReaction.DESTROY` → `POPPED`
* `ItemCooldowns.addCooldown` 现在吃 `ItemStack`
* `Player.displayClientMessage(C,bool)` → `sendSystemMessage(C)`
* `Level#isClientSide` 字段 → `isClientSide()`；`getMinBuildHeight` → `getMinY`

**降级（本轮明确摘除）**：

1. **战利品注入**（`loot/EDLootModificationEvents` + `ItemAdditionModifier`）：
   26.3 把 `NumberProvider` 重构成 `ResolvableFloat/ResolvableInt`，`LootPoolSingletonContainer` 已删
   ⇒ 末影人掉龙牙、龙鳞等注入全没了
2. **紫颂多肉的自然生成**（`ChorusSucculentFeature` + `ModBiomeFeatures` + `ModBiomeModifiers`）：
   `Feature<CountConfiguration>` / `FeaturePlaceContext` 体系重构
3. **炉子的自定义渲染器**（`EndStoveRenderer`）：`BlockEntityRenderer` 换成
   `createRenderState/extractRenderState/submit` + `SubmitNodeCollector`，且 `MultiBufferSource` 已删
4. **龙牙刀对末地生物的额外伤害**（`LivingEntityMixin`）：`actuallyHurt` 的注入点不匹配
   （`Critical injection failure: ... setHealthMixin ... (0/1) succeed`）

**数据层收尾踩到的 4 个坑**（都已写进 `_convert_dl.py`，其余 mod 复用）：

1. `block_state_property` 条件在 26.3 已删 ⇒ 整条剥掉；但剥完不能留下残缺条件
   （`{"type":"minecraft:inverted"}` 没有 `term` 会 parse 失败）⇒ 连带把父条件也剥掉
2. 上游把配方 id 写成 `minecraft:corn`（少命名空间）⇒ 26.3 直接报
   `Unbound values in registry minecraft:recipe`；修法：若该名字在本包里有同名配方，补上本 mod 命名空间
3. `fabric:any` 是 1.21.1 就用的形态，但里面仍写 `{item:...}`，要**递归**转成裸串
4. `minecraft:smithing_transform` 的 `template` / `base` / `addition` 也是 Ingredient，漏转就 parse 失败

结果：`WORLD_OK`（65 jar 交付集上复跑）。

### 2.5 Cultural Delights（未完成，卡点已定位）

Fabric 版 `culturaldelights-0.17.7`。25 java → 编译到 **40 错**。
已修：食物 → Consumable（47 个 `_FX`）、`ItemNameBlockItem`、`ItemInteractionResult`、
JetBrains 注解、`isClientSide`、`getMinBuildHeight`、创造标签页。

**真正的卡点（26.3 把「树」整套重做了，不是签名变化）**：

* `ConfiguredFeature` **类整个不存在**了（`Registries.CONFIGURED_FEATURE` 还在，但没有这个类）
* `TreeGrower` 变成 **final**，只暴露 `OAK/SPRUCE/...` 常量，**没有公开构造器**
  ⇒ 自定义树（牛油果）在代码里根本造不出来，只能走 26.3 的数据驱动形态
* `SaplingBlock(TreeGrower, Properties)` 构造器变成 **protected**
* `LeavesBlock` 构造器现在要多一个 `AmbientLeavesBlockSoundPlayer`
* `DirectionProperty` / `StrippableBlockRegistry` / `TradeOfferHelper` 也都已删

结论：CD 要打通必须**按 26.3 的数据驱动重写「树/叶/去皮/世界生成」这一层**
（不是机械改名）。本轮预算内不做。
建议下一步：先只保留「方块+物品+食物」并把牛油果树叶/树苗**降级成普通方块**，
再单独用 26.3 的 `worldgen/feature` JSON 重做树；`strippable` 用数据标签或 `AxeItem` 映射替代。

### 2.6 My Nether's Delight / Miner's Delight / Abnormals Delight（未开始）

* `mynethersdelight`：Fabric refabricated 2.0.4（97 类），与 CD 同形态（世界生成 + 交易 + 大量方块）
* `minersdelight`、`abnormals_delight`：Modrinth 上**只有 NeoForge/Forge 构建**
  ⇒ 需要先做一套 `net.neoforged` 垫片（`DeferredRegister` / `DeferredHolder` / `IEventBus` /
  `@Mod` 构造器），再叠 §1 的 id 修补；abnormals 还多一个 `blueprint` 库依赖

---

## 3. 复现方式（g8 流水线）

```
work/run26/port/g8/
  _inventory.py      8 个原包的类/资源/依赖清点
  _mkmap.py          1.21.1 srg → 26.3 的类改名表（→ map_121_263.json）
  _rewrite26.py      CFR 源码 → 26.3 名（修好内类点号 + 包搬迁）
  _idfix.py          26.3 的 Properties id 修补（Reg.pb/pi + 名字栈 + Reg.with）
  _javac8.py         26.3 classpath 编译（已剔除 1.21.1 client jar）
  _build8.py         编译产物 + 原 assets/data 重新打包
  _convert_dl.py     数据层转换 + 标签校验 + 物品模型定义 + 世界生成改名
  _edfood.py         FoodProperties.Builder → FoodProperties + Consumable
  _fix_chefs.py / _fix_corn.py / _fix_ed.py / _fix_cd.py   逐 mod 语义修复
```

单个 mod 的重建顺序（以 corn 为例）：

```powershell
python _rewrite26.py corn\src corn\src26
python _fix_corn.py                 # 内部会调 _idfix.py
python _javac8.py corn src27
python _build8.py corn
python _convert_dl.py corn\corndelight-1.0.0-26.3.jar corn\corndelight-1.0.0-26.3-data.jar corndelight \
    --ver 1.0.0-26.3 --cutout "corn_crop,wild_corn,popcorn_box" --drop-ep "client,fabric-datagen" \
    --tags "..\g6\_fab\*.jar;..\_deps\orig\FarmersDelight-26.3-3.6.28+refabricated.jar"
```

验收：

```powershell
# 每测前重拷全新存档副本
Copy-Item "work\run26\watch\saves\New World (1)" "work\run26\stag1\saves\New World (1)" -Recurse -Force
python tools\watch_world.py --game-dir work\run26\stag1 --mods work\run26\modset-dl --world "New World (1)"
```

---

## 4. 降级清单（进交付说明时必须写）

| mod | 降级 | 原因 |
|---|---|---|
| corndelight | 堆肥概率（3 条） | `ComposterBlock.COMPOSTABLES` 已删，26.3 改成物品组件 |
| corndelight | 内容版本取 1.21 的 fabric 移植（1.0.0），非 NeoForge 1.2.10 | 后者无 Fabric 构建 |
| chefsdelight | 数据包仍是 pre-26.3 格式（26.3 自动升级，日志有 WARN） | 改写成 26.3 格式成本高于收益 |
| chefsdelight | datagen 类（含村民交易 datagen）全部摘除 | 只影响数据生成，不影响运行 |
| ends_delight | 战利品注入（末影人掉龙牙等） | `NumberProvider`→`ResolvableFloat` 重构 + `LootPoolSingletonContainer` 删除 |
| ends_delight | 紫颂多肉自然生成 | `Feature<CountConfiguration>` 体系重构 |
| ends_delight | 炉子物品展示渲染 | `BlockEntityRenderer` 换成 submit/state 新体系 |
| ends_delight | 龙牙刀对末地生物额外伤害 | mixin 注入点 `actuallyHurt` 不匹配 |
| ends_delight | 4 个刀的材质（耐久/挖速/附魔度） | `ToolMaterial` 是 record，不能自定义 |
