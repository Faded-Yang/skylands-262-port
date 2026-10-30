# fix-aero-registrate —— Aeronautics/Simulated 26.3「registrate / 方块注册 / 数据(Codec·Criterion·Advancement)」族

> **结论：本族（49 个文件）166 错误 → 0。**
> 工程总错误：**348 → 71**（`notes\aero26-compile-9.log` → `notes\aero26-compile-14.log`）。
> ⚠ 其中 348 → 77 这一段里有渲染线（R350）的并行贡献；**77 → 71 是我在渲染线收工后的继续**。
> 归属可核对的数字是：**我这 49 个文件 166 → 0**（见 §7 复现命令）。

---

## 1. 数字

| 指标 | 值 |
|---|---|
| 起始（compile-9） | **348**（去重后 345 unique） |
| 终点（compile-14） | **71**（去重后 70 unique） |
| 本族文件集 | 49 个 → **166 错 → 0 错** |
| 改过的源文件 | **49**（35 个有 `.bak-rreg`，见 §8） |
| 修掉的错误 | **166** |
| 新增降级/削减 | **6 条**（§6，其中 2 条是真损失：SavedData 文件名、可燃性） |
| 零损失等价改写 | 其余全部 |

起始日志里本族的分布（去重后）：

```
 36  18 个方块的 CODEC=simpleCodec(...) + @Override codec()        ← 一族两条
 34  src\excluded-wip\SimBlocks.java          （registrate 链式 + dye + PushReaction + recipe）
 14  SimulatedCriterionTriggerBase.java       （Listener / CriterionTrigger 包移动）
 12  SimulatedAdvancement.java                （criterion / display / save）
 11  src\excluded-wip\AeroBlocks.java         （simpleItem 链 + LootPool + FireBlock.setFlammable）
 14  dye 族（BLUE_DYE 5 / getDyeColor 5 / RED_DYE 1 / WHITE_CONCRETE 1 / ItemStack(ColorCollection) 1 …）
  7  EndDragonFight（包改名 End→Ender + 嵌套 Data 删除）
  4  SavedData 的 id: String→Identifier
  其余  ≈  RegistrationProvider / SimRegistries / SimItems / SimEntityDataSerializers / SignText …
```

---

## 2. 26.3 实测事实（javap 现查，**可直接复用，别再查一遍**）

| 1.21.11 | 26.3 | 依据 |
|---|---|---|
| `BlockBehaviour.simpleCodec(...)` / `propertiesCodec()`（`protected static`，子类可直接裸调） | **两个都删了**。26.3 的方块**根本没有 MapCodec 序列化**：vanilla `LadderBlock` 零 `CODEC` 字段，`BlockBehaviour` 全表零 codec 方法 | javap `LadderBlock` / `BlockBehaviour`；扫 jar 内 `world/level/block/*.class`：只有 14 个非方块类提到 `MapCodec` |
| 每个方块 `public static final MapCodec<X> CODEC = simpleCodec(X::new);` + `@Override protected MapCodec<? extends Y> codec()` | **整对删除**（不是改名） | 同上 |
| `net.minecraft.advancements.CriterionTrigger` | **`net.minecraft.advancements.triggers.CriterionTrigger`**（整个 criterion 包搬到 `triggers`，`ItemPredicate`/`BlockPredicate` 等搬到 `advancements.predicates`） | javap 包清单 |
| `CriterionTrigger` 有 `addPlayerListener` / `removePlayerListener` / `removePlayerListeners` + 嵌套 `Listener<T>` | **全删**。接口只剩 `Codec<T> codec()` + `default Criterion<T> createCriterion(T)`；监听表搬进 `PlayerAdvancements.getTriggerMapForType(CriterionTrigger<T>)` → `Map<TriggerInstanceKey, T>` | javap `CriterionTrigger` / `PlayerAdvancements` |
| `Listener.trigger()` 回调式 | 拉取式：`playerAdvancements.getTriggerMapForType(this).forEach((key,inst) -> if (pred) playerAdvancements.award(key.advancement(), key.criterion()))` | javap `PlayerAdvancements$TriggerInstanceKey`（record，`advancement()` / `criterion()`） |
| `CriterionTriggerInstance.validate(CriterionValidator)` | **`validate(net.minecraft.world.level.storage.loot.ValidationContextSource)`**（`CriterionValidator` 类不存在） | javap |
| `Criterion`（1.21.11 是 record `(trigger, instance)`） | 同形态，但在 `advancements.triggers.Criterion`；工厂方法直接返回它：`InventoryChangeTrigger.TriggerInstance.hasItems(ItemLike...)` / `ItemUsedOnLocationTrigger.TriggerInstance.placedBlock(...)` | javap |
| `ItemUsedOnLocationTrigger.TriggerInstance.placedBlock(Block)` | **删**；剩 `placedBlock(HolderGetter<Block>, Block)` 与 `placedBlock(LootItemCondition.Builder)` | javap |
| `LootItemBlockStatePropertyCondition` | **整类不存在**（26.3 loot 条件大改，`MatchBlock.blockMatches(BlockPredicate.Builder)`） | jar 类表零命中 |
| `Advancement.Builder.display(ItemStack, …, Identifier background, …)` | `display(ItemStackTemplate/Item, …, 无 background)` + **`rootDisplay(…, Identifier background, …)` 只给根节点** | javap `Advancement$Builder` |
| `Advancement.Builder.save(Consumer<AdvancementHolder>, String)` | **`save(BootstrapContext<Advancement>, String)`**；仍有 `AdvancementHolder build(Identifier)` | javap |
| `DyeColor.BLUE_DYE` 之类 `ItemLike` 常量 / `Items.BLUE_DYE` / `Items.RED_DYE` | **全删**。`Items.DYE` 变成 `ColorCollection<Item>`：`Items.DYE.blue()` / `.pick(DyeColor)`；`Blocks.WOOL` / `Blocks.CONCRETE` 同理：`Blocks.WOOL.brown()`、`Blocks.CONCRETE.white()` | javap `Items` / `Blocks` / `ColorCollection` |
| `DyeItem.getDyeColor()` / `DyeItem.byColor(DyeColor)` | **删**；颜色在组件里：`stack.get(DataComponents.DYE)`（可为 null）、`stack.getOrDefault(DataComponents.DYE, …)`；按颜色取染料物品 = `Items.DYE.pick(color)` | javap `DyeItem` / `DataComponents` |
| `PushReaction.BLOCK` / `.IGNORE` / `.PUSH_ONLY` | 只剩 `PUSH_PULL / PUSH / POPPED / IMMOVEABLE / IGNORE_ENTITY` ⇒ `BLOCK`→`IMMOVEABLE`，`IGNORE`→`IGNORE_ENTITY`，`PUSH_ONLY`→`PUSH`（**注意语义：`PUSH_ONLY` 消失了，`PUSH` 最接近**） | javap `PushReaction` |
| `EndDragonFight`（`world.level.dimension.end`） | **`EnderDragonFight`**（End→Ender）；**嵌套 `Data` 删除**，改为独立 `SavedData`（`SavedDataType TYPE` + `createDefault()`），构造器 9 参 | javap `EnderDragonFight`（无 `$Data` 类） |
| `PrimaryLevelData.endDragonFightData` | **删**（连带 `PrimaryLevelData.parse` 不再收 `WorldOptions`） | javap `PrimaryLevelData` |
| `new SavedDataType<>(String id, Supplier, Codec, DataFixTypes)` | **`SavedDataType(Identifier id, …)`** ⇒ `Identifier.fromNamespaceAndPath(modid, ID)` | javap `SavedDataType` |
| `LootPool.Builder.setRolls(NumberProvider)` | **`setRolls(Holder<ContextIntProvider>)`** —— 26.3 loot 数值/条件全面 Holder 化；`ConstantValue` 搬到 `…providers.number.floats.ConstantValue` | javap `LootPool$Builder` / `ConstantValue` |
| `FireBlock.setFlammable(Block,int,int)`（public） | **整个方法删除**（可燃性改数据驱动）；`FireBlock` 只剩 `bootStrap()` | javap |
| `Blocks.COPPER_BLOCK`（Block） | **`WeatheringCopperCollection<Block>`**：`Blocks.COPPER_BLOCK.weathering().unaffected()`；`Items.COPPER_BLOCK` 同理 | javap `WeatheringCopperCollection` / `Blocks` |
| `Inventory.placeItemBackInInventory(ItemStack)` | **`placeItemBackInInventory(ItemStack, Prediction)`**（`Prediction.SERVER_ONLY`） | javap `Inventory` |
| `Player.displayClientMessage(Component, boolean)` | **`sendOverlayMessage(Component)`**（action bar）/ `sendSystemMessage(Component)`（聊天） | javap `Player` |
| `SignBlockEntity.getFrontText()` / `setText(SignText, boolean)` | **`getText(SignTextSlot.FRONT)` / `setText(SignText, SignTextSlot)`** | javap `SignBlockEntity` |
| `SignText.setMessage(int,Component)` / `setColor` / `setHasGlowingText`（可变） | `SignText` 不可变；改走 `asMutable()` → `setLine(int,Component)` / `setColor(DyeColor)` / `setTextGlowing(boolean)` → `asImmutable()` | javap `SignText$Mutable` |
| `SignApplicator.canApplyToSign(SignText, Player)` / `tryApplyToSign(Level,SignBlockEntity,boolean,Player)` | `canApplyToSign(SignText, ItemStack, Player)` / `tryApplyToSign(Level, SignBlockEntity, SignTextSlot, ItemStack, Player)` | javap `SignApplicator` |
| `ItemParticleOption(ParticleType, ItemStack)` | `(ParticleType, ItemStackTemplate)` ⇒ `ItemStackTemplate.fromStack(stack)` | javap |
| `RegistryFriendlyByteBuf.readVec3()/writeVec3(Vec3)` | **删** ⇒ `Vec3.STREAM_CODEC` | javap `Vec3` / `FriendlyByteBuf` |
| `FabricRegistryBuilder.createSimple(key)` | **`create(key)`**（fabric-registry-sync 8.0.3，类在 `META-INF/jars/` 里） | javap 拆嵌套 jar |
| `Block.playerDestroy(Level, Player, …)` | **`playerDestroy(ServerLevel, ServerPlayer, …)`** | javap `Block` |

---

## 3. 修法：`SimBlocks`(34) —— 不是「垫片缺一个 API」的纯级联

拆开看是 **5 个互不相干的族**，逐一处理：

### 3.1 `.simpleItem().transform(customItemModel(...))` ×22（最大项）
* **根因**：垫片 `BlockBuilder.simpleItem()` 返回 `BlockBuilder`（上游返回 `ItemBuilder`），而
  `AbstractBuilder.transform()` 只收 `NonNullUnaryOperator<S>`。上游能过，是因为垫片原版有个
  `transform(Object...)` 兜底重载（`src\stub` 那轮按「主工程几乎不用」把它省了 —— 实测 `excluded-wip`
  里用了 30 次，**那个判断是错的**）。
* **修法（零损失，不动 stub）**：把链改成
  ```java
  .item()                       // 返回 ItemBuilder<BlockItem, BlockBuilder<T,P>>
  .transform(customItemModel()) // S = ItemBuilder，匹配 NonNullUnaryOperator<ItemBuilder<I,P>>
  .build()                      // ItemBuilder.build() 返回 parent = BlockBuilder<T,P>
  ```
  即 `.simpleItem().transform(X)` → `.item().transform(X).build()`，共 30 处（SimBlocks 22 / AeroBlocks 8）。
  只有 `SimBlocks:733` 这种中间夹 `.tag(...)` 的，把 `.build()` 拼在 `transform` 之后。

### 3.2 无参 `.onRegister()` ×2（SimBlocks 581 / 855）
垫片 `onRegister(Object...)` 允许零参；强类型版要求 1 参 ⇒ **删掉这个空调用**（上游这么写也编译不过）。

### 3.3 `SimStress.setCapacity(double)` 与父类同名冲突
`CStress` 已有 `static <T> Consumer<T> setCapacity(double)`，`SimStress` 用同签名不同返回类型再声明 ⇒
`对setCapacity的引用不明确`。**改名 `withCapacity(double)`**（4 个调用点；`AeroStress` 同病，一起改；它零调用点）。
> 顺带记录：这两个方法体本来就是 `builder -> builder`（空实现），**压力值从来没被记录**（既有降级，非本次引入）。

### 3.4 染料/颜色集合（见 §5）
`DyeItem.byColor(color)` → `Items.DYE.pick(color)`；`PushReaction.BLOCK`→`IMMOVEABLE`；
`AllBlocks.SAIL`（已是 `ColorCollection<SailBlock>`）→ `AllItems.SAIL`（普通帆物品，3 处）。

---

## 4. 修法：`AeroBlocks`(11)

* 8 处 `.simpleItem().transform(customItemModel())` → 同 §3.1。
* `new ItemStack(Items.COPPER_BLOCK)` / `.define('C', Blocks.COPPER_BLOCK)` → 加 `.weathering().unaffected()`。
* **自定义 loot 表整段删除**（1 处）：`LootPool.Builder.setRolls` 只收 `Holder<ContextIntProvider>`，且垫片
  `BlockBuilder.loot(...)` 本来就是空操作 ⇒ 删掉，注释写明。
* `flammable(...)` 变恒等算子（`FireBlock.setFlammable` 删除），**见 §6 降级 2**。
* 删 `import …foundation.block.ItemUseOverrides`（26.3 Create 里没这个类，且工程零使用）。

---

## 5. 修法：Criterion / Advancement（14 + 12 + 3 + 2 = 31）

### 5.1 `SimulatedCriterionTriggerBase` 重写（14）
监听表整个删掉，改拉取式（javap 出的 26.3 形态）：

```java
protected void trigger(ServerPlayer player, @Nullable List<Supplier<Object>> suppliers) {
    final PlayerAdvancements pa = player.getAdvancements();
    pa.getTriggerMapForType(this).forEach((key, instance) -> {
        if (instance.test(suppliers)) pa.award(key.advancement(), key.criterion());
    });
}
```
`Instance` 仍是 `CriterionTriggerInstance`；`addPlayerListener/removePlayerListener*` 全部删除（vanilla 也没了）。

### 5.2 `SimpleSimulatedTrigger`（3）
`validate(CriterionValidator)` → `validate(ValidationContextSource)`；`codec()` 保持（`@Override` 现在合法）。

### 5.3 `SimulatedAdvancement`（12）
* import：`advancements.criterion.{InventoryChangeTrigger,ItemUsedOnLocationTrigger}` → `advancements.triggers.*`；
  补 `advancements.triggers.Criterion`；删无用的 `ItemPredicate`。
* `display(...)` 拆成 `rootDisplay(..., background, ...)`（`id.equals("root")`）与 `display(...)`，
  图标参数 `ItemStackTemplate.fromStack(t.icon)`。
* `save(Consumer)`：改 `builder.build(Identifier)` + `t.accept(...)`（不再走 `BootstrapContext` 版 save；
  datagen 输出 JSON 不变，少的是注册期查重/校验）。
* `placedBlock(block)` → `placedBlock(BuiltInRegistries.BLOCK, block)`（`Registry` 本身是 `HolderGetter`）。

### 5.4 触发器的注册（2）
`Registry.register(BuiltInRegistries.TRIGGER_TYPES, …)` 原本没报别的错 —— 那 2 条是
`SimulatedCriterionTriggerBase` 编译失败导致的**类型推断级联**，父类修好后自动消失。

---

## 6. 降级清单（逐条，**6 条**）

| # | 位置 | 丢了什么 | 可修回？ |
|---|---|---|---|
| **1** | `CrystallizationWorldSaveData` / `BalloonLevelSavedData` / `LodestoneTrackingMap` / `PhysicsStaffServerHandler` 的 `SavedDataType` id | String→Identifier ⇒ **存档文件名变化**（老存档的 `.dat` 读不到） | 需在 `SavedDataStorage` 侧做旧文件名迁移；或保留旧名做别名 |
| **2** | `AeroBlocks.flammable(encouragement, flamability)` | `FireBlock.setFlammable` 整方法删除 ⇒ 现在**返回恒等算子**，这些方块不会被火点燃 | 需按 26.3 数据驱动的可燃性注册表重写（datapack/data map） |
| **3** | `CreateWorldScreenMixin` 的 `END_SEA` 分支 | 原来给 END_SEA 预设预置「末影龙已击杀」（`EndDragonFight.Data`）；26.3 里 `Data` 与 `level.dat` 字段都删了 ⇒ **END_SEA 世界会正常开局（有龙战）** | 需在 `ServerLevel` 初始化后改 `EnderDragonFight` 这份独立 SavedData |
| **4** | `SimItems` 两处 `.model(AssetLookup.itemModelWithPartials())` | 创造法杖 / 活塞发射器的**物品模型 datagen** 不再生成（垫片 `AssetLookup` 返回 `Object`，`ItemBuilder.model` 只收强类型 `BiConsumer`） | 给垫片补 `Object...` 兜底重载，或让 `AssetLookup` 返回真类型 |
| **5** | `AeroBlocks` 自定义 loot 表（1 处，`loot(...)` 段） | 该方块的战利品表 datagen（垫片 `loot()` 本来就是空操作 ⇒ 实际输出本来也没有） | 需按 `Holder<ContextIntProvider>` 重写 |
| **6** | `SimulatedAdvancement.save(Consumer)` | 不再经过 `BootstrapContext` 版 `save` ⇒ 少了「跨 mod 进度查重 + 判据校验」 | 改成真 `BootstrapContext` 注入后恢复 |

**零损失等价改写（不计降级）**：18 个方块的 `CODEC`/`codec()` 删除（26.3 方块无 codec）、
`simpleItem→item().build()`、`SimStress/AeroStress.setCapacity→withCapacity`、`displayClientMessage→sendOverlayMessage`、
`Inventory.placeItemBackInInventory(+Prediction.SERVER_ONLY)`、`ItemParticleOption(ItemStackTemplate)`、
`SignText.asMutable()`、`SignApplicator` 新签名、`Vec3.STREAM_CODEC`、`FabricRegistryBuilder.create`、
`AllBlocks.SAIL→AllItems.SAIL`、`Blocks.WOOL.brown()` / `Blocks.CONCRETE.white()` / `Items.DYE.blue()|pick()`、
`stack.get(DataComponents.DYE)`、`WeatheringCopperCollection.weathering().unaffected()`。

---

## 7. 复现 / 验收

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\aero-port\aeronautics-26
$env:JAVA_HOME="$env:APPDATA\.minecraft\runtime\java-runtime-epsilon"
.\gradlew.bat compileJava --no-daemon
```

日志：`notes\aero26-compile-9.log`（348，起始） → `notes\aero26-compile-14.log`（**71**，我的终点）。

**本族 49 个文件的核对命令**（`tools\parse-aero-errors.cjs` 是本轮写的解析器，能处理中文 javac 输出并去重）：

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262
node tools\parse-aero-errors.cjs notes\aero26-compile-14.log --by=file --top=60   # 我的 49 个文件 0 命中
```

我的 6 个符号也都已清零（在同一条命令上加 `--sym=`）：

```
simpleCodec 0 │ BLUE_DYE 0 │ getDyeColor 0 │ CriterionTrigger 0 │ EndDragonFight 0 │ Listener 0
```

---

## 8. 备份与回滚

* **35 个主文件**改前已备份为 `<文件>.bak-rreg`（SimBlocks / AeroBlocks / 18 个方块 / 数据 4 件套 / 触发器 5 件 / dye 6 件 …）。
* ⚠ **诚实记录**：后一批 14 个文件（`RegistrationProvider`、`SimRegistries`、`SimItems`、`AugerShaftScenes`、
  `RopeScenes`、`SimPonderTags`、`SimEntityDataSerializers`、`AeroStress`、`SimBlockStateGen`、
  `LinkedTypewriterBlockEntity`、`CrystallizationWorldSaveData`、`BalloonLevelSavedData`、
  `LodestoneTrackingMap`、`PhysicsStaffServerHandler`）**没来得及在改前建 `.bak-rreg`**。
  它们的改动都很小，且全部是老→新一行对照（原文都在本文 §2/§5 的表格里），可据此手工回滚；
  其中若干文件还留有大轮次的 `.bak-r314` 之类旧备份。
* **没有动 `src\stub\java` 的任何一行**（垫片那轮成果原样保留）。

---

## 9. 本轮留下的、**不属于本族**的错误（交接索引，`compile-14` 共 71 条）

| 族 | 条数 | 典型位置 | 26.3 事实（若要接手） |
|---|---|---|---|
| `LivingEntity.swing` 签名 | 11 | `SpringItemHandler` / `ZiplineClientManager` / `HoneyGlueClientHandler` | 现在要 `swing(InteractionHand, SwingAnimation, boolean)` |
| `displayClientMessage` | 7 | `DiagramEntity` / `SceneScheduler` / 蜂蜜胶 | → `sendOverlayMessage(Component)` / `sendSystemMessage` |
| `placeItemBackInInventory` | 4 | `EnvelopeBlock` / `MountedPotatoCannonBlock` / `RopeStrandHolderBehavior` / `PortableEngineBlock` | 补 `Prediction.SERVER_ONLY` |
| `@Override` 失效 | 3 | `EnvelopeBlock:132` / `HoneyGlueEntity:243` / `DiagramEntity:412` | 父类签名变了，需逐条 javap |
| `ChunkPos` 构造器 | 3 | `ClientHandleHandler` / `RopeStrandHolderBehavior` / `PhysicsStaffActionPacket` | 26.3 `ChunkPos` 构造器只收长/int,int? 需 javap |
| `BlockAndTintGetter` | 2 | `mixin\auger_shaft\GirderBlockMixin` | 类改名/移位（javap） |
| `PushReaction.IGNORE` / `PUSH_ONLY` | 4 | `GustEntity` / `HoneyGlueEntity` / `SimAssemblyContraption` | → `IGNORE_ENTITY` / `PUSH`（**本轮已知修法，机械替换即可**） |
| `getLightColor` | 2 | 粒子 | → `LightCoordsUtil.getLightCoords(...)`（R347 已记） |
| `EntityType.is(TagKey)` | 2 | `LaserBehaviour` / `ArmorStandItemMixin` | 需 `builtInRegistryHolder().is(tag)` |
| `KEYSYM` / `AllKeys.isKeyDown` | 3 | `KeyWidget` / `PromptWidget` / `SimKeys` | `AllKeys` 只剩 KeyMapping 常量（R350 已记） |
| `ForceGroupIndex` (7)、`SimAssemblyHelper` (4)、`SceneScheduler` (3) 等 | 其余 | — | 各自独立小族 |
