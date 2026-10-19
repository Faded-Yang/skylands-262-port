# 26.3 API 地雷清单（静态扫描）

> 由 `tools/scan_landmines.py` 生成；**只读扫描**，没有改动任何 jar。
> 复跑：`python tools/scan_landmines.py --mods work/run26/mods-stable --out docs/api-landmines.md`

## 0. 结论

| 指标 | 数值 |
|---|---|
| 扫描目标 jar | **71** |
| 索引来源 jar（含内嵌） | 331 |
| 索引里可解析的 class | **77241** |
| 索引里的 方法 / 字段 | 843221 / 280750 |
| 被识别为 mixin target 的类 | 969 |
| 原始「指令级引用了但索引里没有」 | 3393 |
| 被「织入放宽」判为存在的接口方法（不进表） | 30 |
| 去重归组后的全部条目 | 1120 |
| — 其中「可选依赖根本没装」（**不计入地雷**） | 722 |
| — 其中「只随包了一个桩」（**不计入地雷**） | 0 |
| — 待验证（见 §4.1） | 240 |
| **地雷总数** | **158** |
| ↳ **高危 / 中危 / 低危** | **32 / 54 / 72** |
| ↳ 其中「owner 类整个不存在」 | 106 |
| 缺类 / 缺方法 / 缺字段（组数） | 41 / 98 / 19 |

**一条「地雷」= 一个 `(目标成员, 描述符)`。** 同一个缺失成员被 N 处引用只算 1 条，但会列全部站点 —— 触发点越多，玩家越容易撞上。

### 0.1 建议先修哪几条

排序依据：**高危** + owner 在 `net/minecraft`（= 26.3 直接改的）+ 引用站点最多。站点多 = 碰撞概率高。

| 优先 | 缺失成员 | 站点 | 在哪里 |
|---|---|---|---|

---

## 1. 高危 —— 方块/实体/物品的 read·write·tick·neighborChanged·use，以及注册期静态初始化

排序：**判定置信度 → 危险级别 → `net/minecraft` 优先 → 被引用 jar 数 → 站点数**。

| # | 缺失成员 | 所属 jar | 类.方法:行 | 什么情况下会炸 | 站点 |
|---|---|---|---|---|---|
| 1 | `com/zurrtum/create/client/compat/rrv/RecipeButton.active : Z` | `create-fly-26.2-6.0.9-2-26.3-patched` | RecipeButton.init:34 / RecipeButton.init:35 | 走到 init() 这条路径时 → NoSuchFieldError | 2 |
| 2 | `com/zurrtum/create/client/compat/rrv/RecipeButton.onPress : Lnet/minecraft/client/gui/components/Button$OnPress;` | `create-fly-26.2-6.0.9-2-26.3-patched` | RecipeButton.init:34 | 走到 init() 这条路径时 → NoSuchFieldError | 1 |
| 3 | `com/zurrtum/create/client/compat/rrv/RecipeButton.tooltip : Lnet/minecraft/client/gui/components/WidgetTooltipHolder;` | `create-fly-26.2-6.0.9-2-26.3-patched` | RecipeButton.init:35 | 走到 init() 这条路径时 → NoSuchFieldError | 1 |
| 4 | `com/zurrtum/create/client/compat/rrv/RecipeButton.visible : Z` | `create-fly-26.2-6.0.9-2-26.3-patched` | RecipeButton.init:35 | 走到 init() 这条路径时 → NoSuchFieldError | 1 |
| 5 | `net/minecraft/world/level/block/RedStoneWireBlock.POWER : Lnet/minecraft/world/level/block/state/properties/IntegerProperty;` | `createaddition-1.3.4-26.3` | RedstoneRelayBlock.calculateInputStrength:198 / RedstoneRelayBlock.calculateInputStrength:198 …(+3) | 该方块/实体被操作时 → NoSuchFieldError | 5 |
| 6 | `net/minecraft/world/item/alchemy/PotionBrewing$Mix.from()Lnet/minecraft/core/Holder;` | `create-fly-26.2-6.0.9-2-26.3-patched` | PotionRecipe.register:79 / PotionRecipe.register:93 | 注册期（启动时） → NoSuchMethodError | 2 |
| 7 | `net/minecraft/world/item/alchemy/PotionBrewing$Mix.to()Lnet/minecraft/core/Holder;` | `create-fly-26.2-6.0.9-2-26.3-patched` | PotionRecipe.register:84 / PotionRecipe.register:97 | 注册期（启动时） → NoSuchMethodError | 2 |
| 8 | `net/minecraft/world/item/alchemy/PotionBrewing$Mix.ingredient()Lnet/minecraft/world/item/crafting/Ingredient;` | `create-fly-26.2-6.0.9-2-26.3-patched` | PotionRecipe.register:89 / PotionRecipe.register:103 | 注册期（启动时） → NoSuchMethodError | 2 |
| 9 | `net/minecraft/world/item/alchemy/PotionBrewing.bootstrap(Lnet/minecraft/world/flag/FeatureFlagSet;)Lnet/minecraft/world/item/alchemy/PotionBrewing;` | `create-fly-26.2-6.0.9-2-26.3-patched` | PotionRecipe.register:64 | 注册期（启动时） → NoSuchMethodError | 1 |
| 10 | `net/minecraft/world/item/alchemy/PotionBrewing.containers : Ljava/util/List;` | `create-fly-26.2-6.0.9-2-26.3-patched` | PotionRecipe.register:67 | 注册期（启动时） → NoSuchFieldError | 1 |
| 11 | `net/minecraft/world/item/alchemy/PotionBrewing.potionMixes : Ljava/util/List;` | `create-fly-26.2-6.0.9-2-26.3-patched` | PotionRecipe.register:77 | 注册期（启动时） → NoSuchFieldError | 1 |
| 12 | `net/minecraft/world/item/alchemy/PotionBrewing.containerMixes : Ljava/util/List;` | `create-fly-26.2-6.0.9-2-26.3-patched` | PotionRecipe.register:92 | 注册期（启动时） → NoSuchFieldError | 1 |
| 13 | 类 `net/minecraft/world/level/block/RedStoneWireBlock` → 疑似改名 `RedstoneWireBlock` | `createaddition-1.3.4-26.3` | RedstoneRelayBlock | 该方块/实体被操作时 → NoClassDefFoundError | 1 |
| 14 | 类 `net/minecraft/world/entity/animal/Rabbit$RabbitJumpControl` | `rabbit_pathfinding_fix-1.0.5-26.3` | RabbitEntityRabbitMoveControlMixin | 该方块/实体被操作时 → NoClassDefFoundError | 1 |
| 15 | `net/minecraft/world/entity/animal/Rabbit$RabbitJumpControl.wantJump()Z` | `rabbit_pathfinding_fix-1.0.5-26.3` | RabbitEntityRabbitMoveControlMixin.tickRespectJumping:33 | 该方块/实体被操作时 → NoSuchMethodError | 1 |
| 16 | `dan200/computercraft/api/lua/LuaException.<init>(Ljava/lang/String;)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | ComputerUtil.deepEquals:69 / ComputerUtil.deepEquals:74 …(+49) | 走到 parse() 这条路径时 → NoSuchMethodError | 51 |
| 17 | 类 `dan200/computercraft/api/lua/LuaException` | `create-fly-26.2-6.0.9-2-26.3-patched` | ComputerUtil / ComputerUtil$Collection …(+16) | 走到 该类() 这条路径时 → NoClassDefFoundError | 18 |
| 18 | `dan200/computercraft/api/detail/VanillaDetailRegistries.ITEM_STACK : Ldan200/computercraft/api/detail/DetailRegistry;` | `create-fly-26.2-6.0.9-2-26.3-patched` | AllComputerPeripherals.register:54 / ComputerUtil.bigItemStackToLuaTableFilter:22 …(+13) | 注册期（启动时） → NoSuchFieldError | 15 |
| 19 | `dan200/computercraft/api/detail/DetailRegistry.getDetails(Lnet/minecraft/core/HolderLookup$Provider;Ljava/lang/Object;)Ljava/util/Map;` | `create-fly-26.2-6.0.9-2-26.3-patched` | ComputerUtil.bigItemStackToLuaTableFilter:22 / ComputerUtil.getItemDetail:353 …(+8) | 走到 bigItemStackToLuaTableFilter() 这条路径时 → NoSuchMethodError | 10 |
| 20 | 类 `dan200/computercraft/api/detail/DetailRegistry` | `create-fly-26.2-6.0.9-2-26.3-patched` | AllComputerPeripherals / ComputerUtil …(+6) | 走到 该类() 这条路径时 → NoClassDefFoundError | 8 |
| 21 | 类 `dan200/computercraft/api/detail/VanillaDetailRegistries` | `create-fly-26.2-6.0.9-2-26.3-patched` | AllComputerPeripherals / ComputerUtil …(+6) | 走到 该类() 这条路径时 → NoClassDefFoundError | 8 |
| 22 | 类 `dan200/computercraft/api/lua/IArguments` | `create-fly-26.2-6.0.9-2-26.3-patched` | DisplayLinkPeripheral / NixieTubePeripheral …(+5) | 走到 该类() 这条路径时 → NoClassDefFoundError | 7 |
| 23 | `dan200/computercraft/api/lua/IArguments.get(I)Ljava/lang/Object;` | `create-fly-26.2-6.0.9-2-26.3-patched` | DisplayLinkPeripheral.writeBytes:65 / RedstoneRequesterPeripheral.generateOrder:120 …(+3) | 走到 writeBytes() 这条路径时 → NoSuchMethodError | 5 |
| 24 | `dan200/computercraft/api/detail/DetailRegistry.getBasicDetails(Lnet/minecraft/core/HolderLookup$Provider;Ljava/lang/Object;)Ljava/util/Map;` | `create-fly-26.2-6.0.9-2-26.3-patched` | ComputerUtil.list:334 / PackageOrderLuaObject.list:68 …(+2) | 走到 list() 这条路径时 → NoSuchMethodError | 4 |
| 25 | `dan200/computercraft/api/lua/IArguments.count()I` | `create-fly-26.2-6.0.9-2-26.3-patched` | SequencedGearshiftPeripheral.runInstruction:33 / StockTickerPeripheral.requestFiltered:58 | 走到 runInstruction() 这条路径时 → NoSuchMethodError | 2 |
| 26 | `net/neoforged/neoforge/client/event/RegisterGuiLayersEvent.registerAbove(Lnet/minecraft/resources/Identifier;Lnet/minecraft/resources/Identifier;Lnet/neoforged/neoforge/client/gui/GuiLayer;)V` | `FarmersDelight-26.3-3.6.28+refabricated` | LaunchpadClientEvents.register:16 / LaunchpadClientEvents.register:17 | 注册期（启动时） → NoSuchMethodError | 2 |
| 27 | `dan200/computercraft/api/detail/DetailRegistry.addProvider(Ljava/util/function/BiConsumer;)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | AllComputerPeripherals.register:54 | 注册期（启动时） → NoSuchMethodError | 1 |
| 28 | `net/neoforged/neoforge/client/gui/VanillaGuiLayers.PLAYER_HEALTH : Lnet/minecraft/resources/Identifier;` | `FarmersDelight-26.3-3.6.28+refabricated` | LaunchpadClientEvents.register:16 | 注册期（启动时） → NoSuchFieldError | 1 |
| 29 | `net/neoforged/neoforge/client/gui/VanillaGuiLayers.FOOD_LEVEL : Lnet/minecraft/resources/Identifier;` | `FarmersDelight-26.3-3.6.28+refabricated` | LaunchpadClientEvents.register:17 | 注册期（启动时） → NoSuchFieldError | 1 |
| 30 | `net/mezzdev/config/gui/api/ConfigValueEditorType.create(Ljava/lang/String;Ljava/lang/String;)Lnet/mezzdev/config/gui/api/ConfigValueEditorType;` | `jei-26.3-fabric-31.15.0.79` | AlignmentConfigValueGuiAdapter.<clinit>:22 | 类第一次被加载时（注册期几乎必然） → NoSuchMethodError | 1 |
| 31 | `net/mezzdev/config/gui/api/IConfigGuiRegistration.registerValueEditor(Lnet/mezzdev/config/gui/api/ConfigValueEditorType;Lnet/mezzdev/config/gui/api/IConfigValueEditorFactory;)V` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin.register:57 | 注册期（启动时） → NoSuchMethodError | 1 |
| 32 | `net/mezzdev/config/gui/api/IConfigGuiRegistration.configureScreen(Ljava/util/function/Consumer;)V` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin.register:58 | 注册期（启动时） → NoSuchMethodError | 1 |

## 2. 中危 —— GUI/渲染、配方匹配、tooltip、网络包

| # | 缺失成员 | 所属 jar | 类.方法:行 | 什么情况下会炸 | 站点 |
|---|---|---|---|---|---|
| 1 | `net/minecraft/client/renderer/state/level/FirstPersonHandsAndItemsRenderState.clearExtraData()V` | `fabric-api-0.163.0+26.3`, `sodium-fabric-0.9.3-beta.1+mc26.3` | PlayerRenderStateMixin.clearExtraRenderData:40 / PlayerRenderStateMixin.clearExtraRenderData:40 | 走到 clearExtraRenderData() 这条路径时 → NoSuchMethodError | 2 |
| 2 | `net/minecraft/client/renderer/SubmitNodeCollector.submitItem(Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/world/item/ItemDisplayContext;III[ILjava/util/List;Lnet/minecraft/client/renderer/item/ItemStackRenderState$FoilType;)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | ItemModelRenderHelper$CustomLayer.submit:89 / LinkedControllerModel.renderQuads:325 | 走到 submit() 这条路径时 → NoSuchMethodError | 2 |
| 3 | `net/minecraft/util/Util$OS.openFile(Ljava/io/File;)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | SchematicTableScreen.lambda$init$1:144 | 走到 lambda$init$1() 这条路径时 → NoSuchMethodError | 1 |
| 4 | `net/minecraft/server/packs/resources/ResourceManager.listResources(Ljava/lang/String;Ljava/util/function/Predicate;)Ljava/util/Map;` ⚠同名异签名: `(Ljava/lang/String;Lnet/minecraft/server/packs/resources` | `create-fly-26.2-6.0.9-2-26.3-patched` | ShaderSources.<init>:28 | 构造这个对象时 → NoSuchMethodError | 1 |
| 5 | `net/minecraft/client/renderer/feature/FeatureRenderDispatcher$PreparedFrame.executeSolid()V` ⚠同名异签名: `(Lcom/mojang/renderpearl/api/commands/RenderPass;)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | SceneRenderer.prepare:83 | 走到 prepare() 这条路径时 → NoSuchMethodError | 1 |
| 6 | `net/minecraft/client/renderer/feature/FeatureRenderDispatcher$PreparedFrame.executeTranslucent()V` ⚠同名异签名: `(Lcom/mojang/renderpearl/api/commands/RenderPass;)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | SceneRenderer.prepare:84 | 走到 prepare() 这条路径时 → NoSuchMethodError | 1 |
| 7 | `net/minecraft/client/renderer/feature/FeatureRenderDispatcher$PreparedFrame.executeOutline()V` ⚠同名异签名: `(Lcom/mojang/renderpearl/api/commands/RenderPass;)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | SceneRenderer.prepare:85 | 走到 prepare() 这条路径时 → NoSuchMethodError | 1 |
| 8 | `net/minecraft/client/renderer/feature/FeatureRenderDispatcher$PreparedFrame.executeTranslucentAfterTerrain()V` ⚠同名异签名: `(Lcom/mojang/renderpearl/api/commands/RenderPass;)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | SceneRenderer.prepare:86 | 走到 prepare() 这条路径时 → NoSuchMethodError | 1 |
| 9 | `net/minecraft/client/renderer/feature/FeatureRenderDispatcher$PreparedFrame.executeAlwaysOnTop()V` ⚠同名异签名: `(Lcom/mojang/renderpearl/api/commands/RenderPass;)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | SceneRenderer.prepare:87 | 走到 prepare() 这条路径时 → NoSuchMethodError | 1 |
| 10 | `com/mojang/math/Axis.of(Lorg/joml/Vector3f;)Lcom/mojang/math/Axis;` ⚠同名异签名: `(Lorg/joml/Vector3fc;)Lcom/mojang/math/Axis;` | `create-fly-26.2-6.0.9-2-26.3-patched` | BearingVisual.<init>:40 / StabilizedBearingMovementRenderBehaviour.getRenderState:62 …(+3) | 构造这个对象时 → NoSuchMethodError | 5 |
| 11 | `com/mojang/blaze3d/platform/ClipboardManager.setClipboard(Lcom/mojang/blaze3d/platform/Window;Ljava/lang/String;)V` ⚠同名异签名: `(Ljava/lang/String;)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | PonderUI.mouseClicked:955 / PonderUI.mouseClicked:964 …(+1) | 走到 mouseClicked() 这条路径时 → NoSuchMethodError | 3 |
| 12 | `com/zurrtum/create/client/compat/rrv/RecipeButton.setTooltip(Lnet/minecraft/client/gui/components/Tooltip;)V` ⚠同名异签名: `(Lnet/minecraft/network/chat/Component;)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | RecipeButton.setTooltip:39 / RecipeButton.updateMissing:44 | 走到 setTooltip() 这条路径时 → NoSuchMethodError | 2 |
| 13 | `dev/architectury/hooks/client/fluid/fabric/ClientFluidStackHooksImpl.getStillTexture(Lnet/minecraft/world/level/BlockAndLightGetter;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/material/FluidState;)Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;` ⚠同名异签名: `(Ldev/architectury/fluid/FluidStack;)Lnet/minecraft/clie` / `(Lnet/minecraft/client/renderer/block/BlockAndTintGetter` | `architectury-fabric-22.0.5` | ClientFluidStackHooks.getStillTexture | 走到 getStillTexture() 这条路径时 → NoSuchMethodError | 1 |
| 14 | `dev/architectury/hooks/client/fluid/fabric/ClientFluidStackHooksImpl.getFlowingTexture(Lnet/minecraft/world/level/BlockAndLightGetter;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/material/FluidState;)Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;` ⚠同名异签名: `(Ldev/architectury/fluid/FluidStack;)Lnet/minecraft/clie` / `(Lnet/minecraft/client/renderer/block/BlockAndTintGetter` | `architectury-fabric-22.0.5` | ClientFluidStackHooks.getFlowingTexture | 走到 getFlowingTexture() 这条路径时 → NoSuchMethodError | 1 |
| 15 | `com/zurrtum/create/client/foundation/entity/behaviour/CarriageAudioBehaviour$LoopingSound.resolve(Lnet/minecraft/client/sounds/SoundManager;)Lnet/minecraft/client/sounds/WeighedSoundEvents;` | `create-fly-26.2-6.0.9-2-26.3-patched` | CarriageAudioBehaviour$LoopingSound.<init>:349 | 构造这个对象时 → NoSuchMethodError | 1 |
| 16 | 类 `net/minecraft/world/item/alchemy/PotionBrewing` | `create-fly-26.2-6.0.9-2-26.3-patched` | SchematicChunkSource$EmptierChunk$DummyLevel / WrappedLevel …(+2) | 走到 该类() 这条路径时 → NoClassDefFoundError | 4 |
| 17 | 类 `net/minecraft/world/item/alchemy/PotionBrewing$Mix` | `create-fly-26.2-6.0.9-2-26.3-patched` | PotionRecipe | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 18 | `net/mezzdev/config/gui/api/IConfigScreenCategoryBuilder.addValue(Lnet/mezzdev/config/api/value/IConfigValue;)Lnet/mezzdev/config/gui/api/IConfigScreenCategoryBuilder;` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin.configureSearchValues:74 / JeiConfigGuiPlugin.configureCategories:107 …(+7) | 走到 configureSearchValues() 这条路径时 → NoSuchMethodError | 9 |
| 19 | `net/mezzdev/config/gui/api/IConfigScreenCategoryBuilder.addValues(Ljava/util/Collection;)Lnet/mezzdev/config/gui/api/IConfigScreenCategoryBuilder;` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin.configureSearchValues:76 / JeiConfigGuiPlugin.configureSearchValues:83 …(+7) | 走到 configureSearchValues() 这条路径时 → NoSuchMethodError | 9 |
| 20 | `net/mezzdev/config/gui/api/IConfigScreenBuilder.addCategory(Ljava/lang/String;)Lnet/mezzdev/config/gui/api/IConfigScreenCategoryBuilder;` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin.configureCategories:104 / JeiConfigGuiPlugin.configureCategories:128 …(+6) | 走到 configureCategories() 这条路径时 → NoSuchMethodError | 8 |
| 21 | 类 `net/mezzdev/config/gui/api/IConfigScreenValue` | `jei-26.3-fabric-31.15.0.79` | AlignmentConfigValueEditor / AlignmentConfigValueGuiAdapter …(+2) | 走到 该类() 这条路径时 → NoClassDefFoundError | 4 |
| 22 | 类 `net/mezzdev/config/gui/api/ConfigValueEditorType` | `jei-26.3-fabric-31.15.0.79` | AlignmentConfigValueGuiAdapter / AlignmentConfigValueGuiAdapter$AlignmentSerializer …(+1) | 走到 该类() 这条路径时 → NoClassDefFoundError | 3 |
| 23 | `net/mezzdev/config/gui/api/IConfigScreenCategoryBuilder.addScreenValue(Lnet/mezzdev/config/gui/api/IConfigScreenValue;)Lnet/mezzdev/config/gui/api/IConfigScreenCategoryBuilder;` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin.configureGridValues:201 / JeiConfigGuiPlugin.configureRuntimeToggleValues:216 …(+1) | 走到 configureGridValues() 这条路径时 → NoSuchMethodError | 3 |
| 24 | `net/mezzdev/config/gui/api/IConfigScreenCategoryBuilder.addStringSortingConfig(Ljava/lang/String;Ljava/lang/String;Lnet/mezzdev/config/api/sorting/ISortingConfig;Ljava/util/Collection;)Lnet/mezzdev/config/gui/api/ISortingConfigGuiBuilder;` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin.configureSortingOrderCategories:262 / JeiConfigGuiPlugin.configureSortingOrderCategories:273 …(+1) | 走到 configureSortingOrderCategories() 这条路径时 → NoSuchMethodError | 3 |
| 25 | `net/mezzdev/config/gui/api/ISortingConfigGuiBuilder.setValueName(Ljava/util/function/Function;)Lnet/mezzdev/config/gui/api/ISortingConfigGuiBuilder;` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin.configureSortingOrderCategories:268 / JeiConfigGuiPlugin.configureSortingOrderCategories:279 …(+1) | 走到 configureSortingOrderCategories() 这条路径时 → NoSuchMethodError | 3 |
| 26 | `net/mezzdev/config/gui/api/ISortingConfigGuiBuilder.setValueDescription(Ljava/util/function/Function;)Lnet/mezzdev/config/gui/api/ISortingConfigGuiBuilder;` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin.configureSortingOrderCategories:269 / JeiConfigGuiPlugin.configureSortingOrderCategories:280 …(+1) | 走到 configureSortingOrderCategories() 这条路径时 → NoSuchMethodError | 3 |
| 27 | `net/mezzdev/config/gui/api/ISortingConfigGuiBuilder.setValueIcon(Ljava/util/function/Function;)Lnet/mezzdev/config/gui/api/ISortingConfigGuiBuilder;` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin.configureSortingOrderCategories:270 / JeiConfigGuiPlugin.configureSortingOrderCategories:281 …(+1) | 走到 configureSortingOrderCategories() 这条路径时 → NoSuchMethodError | 3 |
| 28 | 类 `net/mezzdev/config/gui/api/IConfigValueEditor` | `jei-26.3-fabric-31.15.0.79` | AlignmentConfigValueEditor / JeiConfigGuiPlugin | 走到 该类() 这条路径时 → NoClassDefFoundError | 2 |
| 29 | 类 `net/mezzdev/config/gui/api/IConfigValueEditorSerializer` | `jei-26.3-fabric-31.15.0.79` | AlignmentConfigValueGuiAdapter / AlignmentConfigValueGuiAdapter$AlignmentSerializer | 走到 该类() 这条路径时 → NoClassDefFoundError | 2 |
| 30 | 类 `net/mezzdev/config/gui/api/ConfigValueApplyMode` | `jei-26.3-fabric-31.15.0.79` | AlignmentConfigValueGuiAdapter / RuntimeToggleScreenValue | 走到 该类() 这条路径时 → NoClassDefFoundError | 2 |
| 31 | `net/mezzdev/config/gui/api/ConfigValueApplyMode.IMMEDIATE : Lnet/mezzdev/config/gui/api/ConfigValueApplyMode;` | `jei-26.3-fabric-31.15.0.79` | AlignmentConfigValueGuiAdapter.getApplyMode:84 / RuntimeToggleScreenValue.getApplyMode:77 | 走到 getApplyMode() 这条路径时 → NoSuchFieldError | 2 |
| 32 | 类 `net/mezzdev/config/gui/api/IConfigScreenCategoryBuilder` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin / JeiConfigGuiPlugin$ConfigScreenCategories | 走到 该类() 这条路径时 → NoClassDefFoundError | 2 |
| 33 | `net/mezzdev/config/gui/api/IConfigScreenCategoryBuilder.addValueByName(Ljava/lang/String;)Lnet/mezzdev/config/gui/api/IConfigScreenCategoryBuilder;` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin.configureSearchValues:97 / JeiConfigGuiPlugin.configureCategories:159 | 走到 configureSearchValues() 这条路径时 → NoSuchMethodError | 2 |
| 34 | `net/mezzdev/config/gui/api/IConfigScreenCategoryBuilder.addCategory(Ljava/lang/String;)Lnet/mezzdev/config/gui/api/IConfigScreenCategoryBuilder;` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin.lambda$configureCategories$0:176 / JeiConfigGuiPlugin.addNestedCategory:300 | 走到 addNestedCategory() 这条路径时 → NoSuchMethodError | 2 |
| 35 | `net/mezzdev/config/gui/api/IConfigScreenCategoryBuilder.setTitle(Lnet/minecraft/network/chat/Component;)Lnet/mezzdev/config/gui/api/IConfigScreenCategoryBuilder;` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin.lambda$configureCategories$0:177 / JeiConfigGuiPlugin.addNestedCategory:301 | 走到 addNestedCategory() 这条路径时 → NoSuchMethodError | 2 |
| 36 | 类 `net/neoforged/neoforge/client/gui/GuiLayer` | `FarmersDelight-26.3-3.6.28+refabricated` | LaunchpadClientEvents | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 37 | 类 `net/neoforged/neoforge/client/gui/VanillaGuiLayers` | `FarmersDelight-26.3-3.6.28+refabricated` | LaunchpadClientEvents | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 38 | 类 `net/neoforged/neoforge/client/event/RegisterGuiLayersEvent` | `FarmersDelight-26.3-3.6.28+refabricated` | LaunchpadClientEvents | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 39 | 类 `net/mezzdev/config/gui/api/ISortingConfigGuiBuilder` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 40 | 类 `net/mezzdev/config/gui/api/IConfigGuiPlugin` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 41 | 类 `net/mezzdev/config/gui/api/IConfigGuiRegistration` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 42 | 类 `net/mezzdev/config/gui/api/IConfigScreenBuilder` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 43 | 类 `net/mezzdev/config/gui/api/IConfigScreenFactory` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 44 | 类 `net/mezzdev/config/gui/api/IConfigValueEditorFactory` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 45 | 类 `net/mezzdev/config/gui/api/IConfigScreenValueBuilder` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 46 | `net/mezzdev/config/gui/api/IConfigScreenFactory.create(Lnet/minecraft/client/gui/screens/Screen;)Lnet/minecraft/client/gui/screens/Screen;` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin.createScreen:47 | 走到 createScreen() 这条路径时 → NoSuchMethodError | 1 |
| 47 | `net/mezzdev/config/gui/api/IConfigScreenCategoryBuilder.clearDefaultValues()Lnet/mezzdev/config/gui/api/IConfigScreenCategoryBuilder;` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin.configureCategories:162 | 走到 configureCategories() 这条路径时 → NoSuchMethodError | 1 |
| 48 | `net/mezzdev/config/gui/api/IConfigScreenCategoryBuilder.getValueBuilder(Lnet/mezzdev/config/api/value/IConfigValue;)Lnet/mezzdev/config/gui/api/IConfigScreenValueBuilder;` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin.configureRuntimeToggleValues:227 | 走到 configureRuntimeToggleValues() 这条路径时 → NoSuchMethodError | 1 |
| 49 | `net/mezzdev/config/gui/api/IConfigScreenValueBuilder.insertBefore(Lnet/mezzdev/config/gui/api/IConfigScreenValue;)Lnet/mezzdev/config/gui/api/IConfigScreenValueBuilder;` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin.configureRuntimeToggleValues:228 | 走到 configureRuntimeToggleValues() 这条路径时 → NoSuchMethodError | 1 |
| 50 | `net/mezzdev/config/gui/api/IConfigScreenCategoryBuilder.setDescription(Lnet/minecraft/network/chat/Component;)Lnet/mezzdev/config/gui/api/IConfigScreenCategoryBuilder;` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin.addNestedCategory:302 | 走到 addNestedCategory() 这条路径时 → NoSuchMethodError | 1 |
| 51 | `net/mezzdev/config/gui/api/IConfigScreenCategoryBuilder.addKeyMappings(Ljava/util/Collection;)Lnet/mezzdev/config/gui/api/IConfigScreenCategoryBuilder;` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin.lambda$configureCategories$0:178 | 走到 lambda$configureCategories$0() 这条路径时 → NoSuchMethodError | 1 |
| 52 | `net/mezzdev/config/gui/api/IConfigScreenBuilder.setTitle(Lnet/minecraft/network/chat/Component;)Lnet/mezzdev/config/gui/api/IConfigScreenBuilder;` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin.lambda$register$1:59 | 走到 lambda$register$1() 这条路径时 → NoSuchMethodError | 1 |
| 53 | `net/mezzdev/config/gui/api/IConfigScreenBuilder.clearDefaultCategories()Lnet/mezzdev/config/gui/api/IConfigScreenBuilder;` | `jei-26.3-fabric-31.15.0.79` | JeiConfigGuiPlugin.lambda$register$1:60 | 走到 lambda$register$1() 这条路径时 → NoSuchMethodError | 1 |
| 54 | `net/blay09/mods/unbreakables/api/UnbreakablesAPI.shogiScope()Lnet/blay09/mods/shogi/scope/ShogiScope;` | `waystones-fabric-26.3-26.3.0.1` | UnbreakablesIntegration.<init>:12 | 构造这个对象时 → NoSuchMethodError | 1 |

## 3. 低危 —— 只在特定交互/调试路径

| # | 缺失成员 | 所属 jar | 类.方法:行 | 什么情况下会炸 | 站点 |
|---|---|---|---|---|---|
| 1 | `net/minecraft/client/renderer/state/GameRenderState.useShaderTransparency()Z` | `create-fly-26.2-6.0.9-2-26.3-patched` | OitFramebuffer.prepare:57 / OitFramebuffer.composite:190 | 走到 prepare() 这条路径时 → NoSuchMethodError | 2 |
| 2 | `net/minecraft/world/level/block/ComposterBlock.COMPOSTABLES : Lit/unimi/dsi/fastutil/objects/Object2FloatMap;` | `create-fly-26.2-6.0.9-2-26.3-patched` | AllItemAttributeTypes.lambda$static$10:84 | 走到 lambda$static$10() 这条路径时 → NoSuchFieldError | 1 |
| 3 | `net/minecraft/world/level/block/BonemealableBlock.performBonemeal(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/util/RandomSource;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;)V` ⚠同名异签名: `(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/` | `create-fly-26.2-6.0.9-2-26.3-patched` | TreeFertilizerItem.useOn:50 | 走到 useOn() 这条路径时 → NoSuchMethodError | 1 |
| 4 | `net/minecraft/core/component/DataComponentPatch.entrySet()Ljava/util/Set;` | `create-fly-26.2-6.0.9-2-26.3-patched` | ComponentsIngredient.test:75 | 走到 test() 这条路径时 → NoSuchMethodError | 1 |
| 5 | `net/minecraft/client/renderer/SubmitNodeCollector.submitBreakingBlockModel(Lcom/mojang/blaze3d/vertex/PoseStack;Ljava/util/List;I)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | WorldSectionElementImpl.renderFirst:379 | 走到 renderFirst() 这条路径时 → NoSuchMethodError | 1 |
| 6 | `net/minecraft/world/level/levelgen/structure/templatesystem/RuleTest.test(Lnet/minecraft/world/level/block/state/BlockState;Lnet/minecraft/util/RandomSource;)Z` ⚠同名异签名: `(Lnet/minecraft/world/level/block/state/BlockState;Lnet/` | `create-fly-26.2-6.0.9-2-26.3-patched` | LayeredOreFeature.canPlaceOre:220 | 走到 canPlaceOre() 这条路径时 → NoSuchMethodError | 1 |
| 7 | `net/minecraft/world/level/block/JigsawBlock.canAttach(Lnet/minecraft/world/level/levelgen/structure/templatesystem/StructureTemplate$StructureBlockInfo;Lnet/minecraft/world/level/levelgen/structure/templatesystem/StructureTemplate$StructureBlockInfo;)Z` ⚠同名异签名: `(Lnet/minecraft/world/level/levelgen/structure/templates` | `DungeonsArise-2.1.68-26.3` | ModifiedStructurePoolBasedGenerator$StructurePoolGenerator.generatePiece:312 | 走到 generatePiece() 这条路径时 → NoSuchMethodError | 1 |
| 8 | `net/minecraft/world/level/ChunkPos.<init>(Lnet/minecraft/core/BlockPos;)V` ⚠同名异签名: `(II)V` | `DungeonsArise-2.1.68-26.3` | ModifiedStructurePoolBasedGenerator.generate:162 | 走到 generate() 这条路径时 → NoSuchMethodError | 1 |
| 9 | `net/minecraft/world/level/levelgen/structure/Structure$GenerationContext.<init>(Lnet/minecraft/core/RegistryAccess;Lnet/minecraft/world/level/chunk/ChunkGenerator;Lnet/minecraft/world/level/biome/BiomeSource;Lnet/minecraft/world/level/levelgen/RandomState;Lnet/minecraft/world/level/levelgen/structure/templatesystem/StructureTemplateManager;JLnet/minecraft/world/level/ChunkPos;Lnet/minecraft/world/level/LevelHeightAccessor;Ljava/util/function/Predicate;)V` ⚠同名异签名: `(Lnet/minecraft/core/RegistryAccess;Lnet/minecraft/world` / `(Lnet/minecraft/core/RegistryAccess;Lnet/minecraft/world` | `DungeonsArise-2.1.68-26.3` | ModifiedStructurePoolBasedGenerator.generate:162 | 走到 generate() 这条路径时 → NoSuchMethodError | 1 |
| 10 | `xaero/lib/client/compat/prometheus/FixedNumberBoxListEntry.getText()Ljava/lang/String;` | `xaerominimap-fabric-26.3-26.6.0`, `xaeroworldmap-fabric-26.3-1.47.0` | FixedNumberBoxListEntry.getLongValue:27 / FixedNumberBoxListEntry.getByteValue:35 …(+2) | 走到 getLongValue() 这条路径时 → NoSuchMethodError | 4 |
| 11 | `xaero/lib/client/compat/prometheus/FixedNumberBoxListEntry.text : Ljava/lang/String;` | `xaerominimap-fabric-26.3-26.6.0`, `xaeroworldmap-fabric-26.3-1.47.0` | FixedNumberBoxListEntry.setText:22 / FixedNumberBoxListEntry.setText:22 | 走到 setText() 这条路径时 → NoSuchFieldError | 2 |
| 12 | `xaero/lib/client/compat/prometheus/FixedNumberBoxListEntry.getIntValue()Ljava/util/OptionalInt;` | `xaerominimap-fabric-26.3-26.6.0`, `xaeroworldmap-fabric-26.3-1.47.0` | PrometheusOptionDisplay.saveNumberEntry:138 / PrometheusOptionDisplay.saveNumberEntry:138 | 走到 saveNumberEntry() 这条路径时 → NoSuchMethodError | 2 |
| 13 | `xaero/lib/client/compat/prometheus/FixedNumberBoxListEntry.getDoubleValue()Ljava/util/OptionalDouble;` | `xaerominimap-fabric-26.3-26.6.0`, `xaeroworldmap-fabric-26.3-1.47.0` | PrometheusOptionDisplay.saveNumberEntry:144 / PrometheusOptionDisplay.saveNumberEntry:144 | 走到 saveNumberEntry() 这条路径时 → NoSuchMethodError | 2 |
| 14 | `joptsimple/OptionParser.acceptsAll(Ljava/util/Collection;Ljava/lang/String;)Ljoptsimple/OptionSpecBuilder;` ⚠同名异签名: `(Ljava/util/List;)Ljoptsimple/OptionSpecBuilder;` / `(Ljava/util/List;Ljava/lang/String;)Ljoptsimple/OptionSp` | `iris-fabric-1.11.7+mc26.3` | Main.run:60 / Main.run:64 …(+6) | 走到 run() 这条路径时 → NoSuchMethodError | 8 |
| 15 | `org/anarres/cpp/CppTask.fileCopyMap : Ljava/util/Hashtable;` | `iris-fabric-1.11.7+mc26.3` | CppTask.doFileOperations:163 / CppTask.doFileOperations:164 …(+3) | 走到 doFileOperations() 这条路径时 → NoSuchFieldError | 5 |
| 16 | `org/spongepowered/asm/mixin/injection/struct/InjectionInfo.getContext()Lorg/spongepowered/asm/mixin/refmap/IMixinContext;` | `MoogsStructureLib-fabric-26.3-3.4.2` | MixinVersionImpl_v0_8.getMixin:25 / MixinVersionImpl_v0_8.parseMemberInfo:56 …(+1) | 走到 getMixin() 这条路径时 → NoSuchMethodError | 3 |
| 17 | `vectorwing/farmersdelight/integration/rei/display/CookingPotDisplay.getInputEntries()Ljava/util/List;` | `FarmersDelight-26.3-3.6.28+refabricated` | CookingPotCategory.setupDisplay:75 / CookingPotCategory.setupDisplay:91 | 走到 setupDisplay() 这条路径时 → NoSuchMethodError | 2 |
| 18 | `org/anarres/cpp/CppTask.log(Ljava/lang/String;)V` | `iris-fabric-1.11.7+mc26.3` | CppTask.doFileOperations:164 / CppTask$Listener.print:39 | 走到 print() 这条路径时 → NoSuchMethodError | 2 |
| 19 | `org/anarres/cpp/CppTask.getProject()Lorg/apache/tools/ant/Project;` | `iris-fabric-1.11.7+mc26.3` | CppTask.addSystemincludepath:76 / CppTask.addLocalincludepath:82 | 走到 addSystemincludepath() 这条路径时 → NoSuchMethodError | 2 |
| 20 | `org/anarres/cpp/CppTask.verbosity : I` | `iris-fabric-1.11.7+mc26.3` | CppTask.doFileOperations:176 / CppTask.doFileOperations:181 | 走到 doFileOperations() 这条路径时 → NoSuchFieldError | 2 |
| 21 | `org/anarres/cpp/CppTask.log(Ljava/lang/String;I)V` | `iris-fabric-1.11.7+mc26.3` | CppTask.doFileOperations:176 / CppTask.doFileOperations:181 | 走到 doFileOperations() 这条路径时 → NoSuchMethodError | 2 |
| 22 | `dan200/computercraft/api/peripheral/IComputerAccess.getAttachmentName()Ljava/lang/String;` | `create-fly-26.2-6.0.9-2-26.3-patched` | SyncedPeripheral.queueEvent:76 | 走到 queueEvent() 这条路径时 → NoSuchMethodError | 1 |
| 23 | `dan200/computercraft/api/peripheral/IComputerAccess.queueEvent(Ljava/lang/String;[Ljava/lang/Object;)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | SyncedPeripheral.queueEvent:77 | 走到 queueEvent() 这条路径时 → NoSuchMethodError | 1 |
| 24 | `net/aurelj/dungeons_arise/structures/WDAGenericStructures.method_42697(Lcom/mojang/serialization/codecs/RecordCodecBuilder$Instance;)Lcom/mojang/serialization/codecs/RecordCodecBuilder;` | `DungeonsArise-2.1.68-26.3` | WDAGenericStructures.lambda$static$8:33 | 走到 lambda$static$8() 这条路径时 → NoSuchMethodError | 1 |
| 25 | `vectorwing/farmersdelight/integration/rei/display/CookingPotDisplay.getOutputEntries()Ljava/util/List;` | `FarmersDelight-26.3-3.6.28+refabricated` | CookingPotCategory.setupDisplay:76 | 走到 setupDisplay() 这条路径时 → NoSuchMethodError | 1 |
| 26 | `vectorwing/farmersdelight/integration/rei/display/CuttingDisplay.getInputEntries()Ljava/util/List;` | `FarmersDelight-26.3-3.6.28+refabricated` | CuttingCategory.setupDisplay:65 | 走到 setupDisplay() 这条路径时 → NoSuchMethodError | 1 |
| 27 | `org/anarres/cpp/CppTask.destDir : Ljava/io/File;` | `iris-fabric-1.11.7+mc26.3` | CppTask.doFileOperations:165 | 走到 doFileOperations() 这条路径时 → NoSuchFieldError | 1 |
| 28 | `org/anarres/cpp/CppTask.getLocation()Lorg/apache/tools/ant/Location;` | `iris-fabric-1.11.7+mc26.3` | CppTask.doFileOperations:207 | 走到 doFileOperations() 这条路径时 → NoSuchMethodError | 1 |
| 29 | `org/spongepowered/asm/mixin/injection/throwables/InvalidInjectionException.<init>(Lorg/spongepowered/asm/mixin/injection/struct/InjectionInfo;Ljava/lang/String;)V` ⚠同名异签名: `(Lorg/spongepowered/asm/mixin/injection/selectors/ISelec` / `(Lorg/spongepowered/asm/mixin/injection/selectors/ISelec` | `MoogsStructureLib-fabric-26.3-3.4.2` | MixinVersionImpl_v0_8.makeInvalidInjectionException:20 | 走到 makeInvalidInjectionException() 这条路径时 → NoSuchMethodError | 1 |
| 30 | `org/spongepowered/asm/mixin/injection/modify/LocalVariableDiscriminator$Context.<init>(Lorg/objectweb/asm/Type;ZLorg/spongepowered/asm/mixin/injection/struct/Target;Lorg/objectweb/asm/tree/AbstractInsnNode;)V` ⚠同名异签名: `(Lorg/spongepowered/asm/mixin/injection/struct/Injection` | `MoogsStructureLib-fabric-26.3-3.4.2` | MixinVersionImpl_v0_8.makeLvtContext:30 | 走到 makeLvtContext() 这条路径时 → NoSuchMethodError | 1 |
| 31 | `org/spongepowered/asm/mixin/injection/struct/InjectionInfo.getAnnotation()Lorg/objectweb/asm/tree/AnnotationNode;` | `MoogsStructureLib-fabric-26.3-3.4.2` | MixinVersionImpl_v0_8.getAnnotation:40 | 走到 getAnnotation() 这条路径时 → NoSuchMethodError | 1 |
| 32 | `org/spongepowered/asm/mixin/injection/struct/InjectionInfo.getTargets()Ljava/util/Collection;` | `MoogsStructureLib-fabric-26.3-3.4.2` | MixinVersionImpl_v0_8.getTargets:51 | 走到 getTargets() 这条路径时 → NoSuchMethodError | 1 |
| 33 | `org/spongepowered/asm/mixin/injection/struct/MemberInfo.parse(Ljava/lang/String;Lorg/spongepowered/asm/mixin/refmap/IReferenceMapper;Ljava/lang/String;)Lorg/spongepowered/asm/mixin/injection/struct/MemberInfo;` ⚠同名异签名: `(Ljava/lang/String;Lorg/spongepowered/asm/mixin/injectio` | `MoogsStructureLib-fabric-26.3-3.4.2` | MixinVersionImpl_v0_8.parseMemberInfo:56 | 走到 parseMemberInfo() 这条路径时 → NoSuchMethodError | 1 |
| 34 | 类 `net/minecraft/world/level/levelgen/feature/configurations/OreConfiguration$TargetBlockState` | `create-fly-26.2-6.0.9-2-26.3-patched` | LayerPattern$Layer / LayerPattern$Layer$Builder …(+1) | 走到 该类() 这条路径时 → NoClassDefFoundError | 3 |
| 35 | `net/minecraft/world/level/levelgen/feature/configurations/OreConfiguration.target(Lnet/minecraft/world/level/levelgen/structure/templatesystem/RuleTest;Lnet/minecraft/world/level/block/state/BlockState;)Lnet/minecraft/world/level/levelgen/feature/configurations/OreConfiguration$TargetBlockState;` | `create-fly-26.2-6.0.9-2-26.3-patched` | LayerPattern$Layer$Builder.block:129 / LayerPattern$Layer$Builder.blocks:151 …(+1) | 走到 block() 这条路径时 → NoSuchMethodError | 3 |
| 36 | 类 `net/minecraft/world/level/levelgen/placement/PlacementModifierType` | `create-fly-26.2-6.0.9-2-26.3-patched` | AllPlacementModifiers / ConfigPlacementFilter | 走到 该类() 这条路径时 → NoClassDefFoundError | 2 |
| 37 | 类 `net/minecraft/world/item/AxeItem` | `create-fly-26.2-6.0.9-2-26.3-patched` | SandPaperItem | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 38 | `net/minecraft/world/item/AxeItem.getStripped(Lnet/minecraft/world/level/block/state/BlockState;)Ljava/util/Optional;` | `create-fly-26.2-6.0.9-2-26.3-patched` | SandPaperItem.useOn:199 | 走到 useOn() 这条路径时 → NoSuchMethodError | 1 |
| 39 | 类 `net/minecraft/world/level/levelgen/feature/configurations/OreConfiguration` | `create-fly-26.2-6.0.9-2-26.3-patched` | LayerPattern$Layer$Builder | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 40 | `net/minecraft/world/level/levelgen/feature/configurations/OreConfiguration$TargetBlockState.CODEC : Lcom/mojang/serialization/Codec;` | `create-fly-26.2-6.0.9-2-26.3-patched` | LayerPattern$Layer.lambda$static$0:81 | 走到 lambda$static$0() 这条路径时 → NoSuchFieldError | 1 |
| 41 | 类 `net/minecraft/world/level/block/entity/FuelValues$Builder` | `create-fly-26.2-6.0.9-2-26.3-patched` | FuelValuesMixin | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 42 | 类 `net/minecraft/world/level/levelgen/feature/FeaturePlaceContext` | `create-fly-26.2-6.0.9-2-26.3-patched` | LayeredOreFeature | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 43 | 类 `net/minecraft/world/level/levelgen/feature/configurations/FeatureConfiguration` | `create-fly-26.2-6.0.9-2-26.3-patched` | LayeredOreFeature | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 44 | `net/minecraft/world/level/levelgen/feature/configurations/OreConfiguration$TargetBlockState.target : Lnet/minecraft/world/level/levelgen/structure/templatesystem/RuleTest;` | `create-fly-26.2-6.0.9-2-26.3-patched` | LayeredOreFeature.canPlaceOre:220 | 走到 canPlaceOre() 这条路径时 → NoSuchFieldError | 1 |
| 45 | `dan200/computercraft/api/lua/LuaValues.getType(Ljava/lang/Object;)Ljava/lang/String;` | `create-fly-26.2-6.0.9-2-26.3-patched` | CreateLuaTable.getBoolean:26 / CreateLuaTable.getString:36 …(+5) | 走到 getBoolean() 这条路径时 → NoSuchMethodError | 7 |
| 46 | `dan200/computercraft/api/lua/LuaValues.badField(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Ldan200/computercraft/api/lua/LuaException;` | `create-fly-26.2-6.0.9-2-26.3-patched` | CreateLuaTable.getBoolean:26 / CreateLuaTable.getString:36 …(+3) | 走到 getBoolean() 这条路径时 → NoSuchMethodError | 5 |
| 47 | `dan200/computercraft/api/lua/IArguments.getTable(I)Ljava/util/Map;` | `create-fly-26.2-6.0.9-2-26.3-patched` | NixieTubePeripheral.setSignal:126 / NixieTubePeripheral.setSignal:129 …(+2) | 走到 setSignal() 这条路径时 → NoSuchMethodError | 4 |
| 48 | `dan200/computercraft/api/lua/MethodResult.of([Ljava/lang/Object;)Ldan200/computercraft/api/lua/MethodResult;` | `create-fly-26.2-6.0.9-2-26.3-patched` | StationPeripheral.canTrainReach:232 / StationPeripheral.canTrainReach:234 …(+2) | 走到 canTrainReach() 这条路径时 → NoSuchMethodError | 4 |
| 49 | 类 `dan200/computercraft/api/lua/LuaValues` | `create-fly-26.2-6.0.9-2-26.3-patched` | CreateLuaTable / DisplayLinkPeripheral …(+1) | 走到 该类() 这条路径时 → NoClassDefFoundError | 3 |
| 50 | `dan200/computercraft/api/lua/IArguments.getInt(I)I` | `create-fly-26.2-6.0.9-2-26.3-patched` | RedstoneRequesterPeripheral.setCraftingRequest:42 / SequencedGearshiftPeripheral.runInstruction:33 …(+1) | 走到 setCraftingRequest() 这条路径时 → NoSuchMethodError | 3 |
| 51 | 类 `net/mezzdev/config/gui/api/IConfigValueIcon` | `jei-26.3-fabric-31.15.0.79` | DrawableConfigValueIcon / SortingOrderConfigValues …(+1) | 走到 该类() 这条路径时 → NoClassDefFoundError | 3 |
| 52 | `dan200/computercraft/api/lua/LuaValues.checkEnum(ILjava/lang/Class;Ljava/lang/String;)Ljava/lang/Enum;` | `create-fly-26.2-6.0.9-2-26.3-patched` | NixieTubePeripheral.setText:80 / NixieTubePeripheral.setTextColour:93 | 走到 setText() 这条路径时 → NoSuchMethodError | 2 |
| 53 | `dan200/computercraft/api/lua/IArguments.optTable(I)Ljava/util/Optional;` | `create-fly-26.2-6.0.9-2-26.3-patched` | NixieTubePeripheral.setSignal:125 / NixieTubePeripheral.setSignal:128 | 走到 setSignal() 这条路径时 → NoSuchMethodError | 2 |
| 54 | 类 `dan200/computercraft/api/peripheral/PeripheralLookup` | `create-fly-26.2-6.0.9-2-26.3-patched` | AllComputerPeripherals | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 55 | `dan200/computercraft/api/peripheral/PeripheralLookup.get()Lnet/fabricmc/fabric/api/lookup/v1/block/BlockApiLookup;` | `create-fly-26.2-6.0.9-2-26.3-patched` | AllComputerPeripherals.registerPeripheral:22 | 走到 registerPeripheral() 这条路径时 → NoSuchMethodError | 1 |
| 56 | 类 `dan200/computercraft/api/lua/LuaTable` | `create-fly-26.2-6.0.9-2-26.3-patched` | CreateLuaTable | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 57 | 类 `dan200/computercraft/api/lua/ObjectLuaTable` | `create-fly-26.2-6.0.9-2-26.3-patched` | DisplayLinkPeripheral | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 58 | `dan200/computercraft/api/lua/ObjectLuaTable.<init>(Ljava/util/Map;)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | DisplayLinkPeripheral.writeBytes:70 | 走到 writeBytes() 这条路径时 → NoSuchMethodError | 1 |
| 59 | `dan200/computercraft/api/lua/ObjectLuaTable.length()I` | `create-fly-26.2-6.0.9-2-26.3-patched` | DisplayLinkPeripheral.writeBytes:71 | 走到 writeBytes() 这条路径时 → NoSuchMethodError | 1 |
| 60 | `dan200/computercraft/api/lua/ObjectLuaTable.getInt(I)I` | `create-fly-26.2-6.0.9-2-26.3-patched` | DisplayLinkPeripheral.writeBytes:73 | 走到 writeBytes() 这条路径时 → NoSuchMethodError | 1 |
| 61 | `dan200/computercraft/api/lua/LuaValues.badArgumentOf(Ldan200/computercraft/api/lua/IArguments;ILjava/lang/String;)Ldan200/computercraft/api/lua/LuaException;` | `create-fly-26.2-6.0.9-2-26.3-patched` | DisplayLinkPeripheral.writeBytes:76 | 走到 writeBytes() 这条路径时 → NoSuchMethodError | 1 |
| 62 | `dan200/computercraft/api/lua/IArguments.getString(I)Ljava/lang/String;` | `create-fly-26.2-6.0.9-2-26.3-patched` | NixieTubePeripheral.setText:72 | 走到 setText() 这条路径时 → NoSuchMethodError | 1 |
| 63 | `dan200/computercraft/api/lua/IArguments.optString(ILjava/lang/String;)Ljava/lang/String;` | `create-fly-26.2-6.0.9-2-26.3-patched` | NixieTubePeripheral.setText:75 | 走到 setText() 这条路径时 → NoSuchMethodError | 1 |
| 64 | `dan200/computercraft/api/lua/IArguments.drop(I)Ldan200/computercraft/api/lua/IArguments;` | `create-fly-26.2-6.0.9-2-26.3-patched` | RedstoneRequesterPeripheral.setCraftingRequest:43 | 走到 setCraftingRequest() 这条路径时 → NoSuchMethodError | 1 |
| 65 | 类 `dan200/computercraft/api/lua/MethodResult` | `create-fly-26.2-6.0.9-2-26.3-patched` | StationPeripheral | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 66 | 类 `net/mezzdev/config/gui/api/ConfigInfo` | `jei-26.3-fabric-31.15.0.79` | AlignmentConfigValueEditor | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 67 | 类 `net/mezzdev/config/gui/api/ConfigValueLocalization` | `jei-26.3-fabric-31.15.0.79` | AlignmentConfigValueEditor | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 68 | `net/mezzdev/config/gui/api/ConfigValueLocalization.getName(Lnet/mezzdev/config/gui/api/IConfigScreenValue;)Lnet/minecraft/network/chat/Component;` | `jei-26.3-fabric-31.15.0.79` | AlignmentConfigValueEditor.getTooltipInfo:56 | 走到 getTooltipInfo() 这条路径时 → NoSuchMethodError | 1 |
| 69 | `net/mezzdev/config/gui/api/ConfigValueLocalization.getValueName(Lnet/mezzdev/config/gui/api/IConfigScreenValue;Ljava/lang/Object;)Lnet/minecraft/network/chat/Component;` | `jei-26.3-fabric-31.15.0.79` | AlignmentConfigValueEditor.getTooltipInfo:57 | 走到 getTooltipInfo() 这条路径时 → NoSuchMethodError | 1 |
| 70 | `net/mezzdev/config/gui/api/ConfigInfo.<init>(Lnet/minecraft/network/chat/Component;Lnet/minecraft/network/chat/Component;)V` | `jei-26.3-fabric-31.15.0.79` | AlignmentConfigValueEditor.getTooltipInfo:57 | 走到 getTooltipInfo() 这条路径时 → NoSuchMethodError | 1 |
| 71 | 类 `net/mezzdev/config/gui/api/IConfigValuePopup` | `jei-26.3-fabric-31.15.0.79` | AlignmentSelectorPopup | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |
| 72 | 类 `net/blay09/mods/unbreakables/api/UnbreakablesAPI` | `waystones-fabric-26.3-26.3.0.1` | UnbreakablesIntegration | 走到 该类() 这条路径时 → NoClassDefFoundError | 1 |

## 4. 不能当实证的三类（单列，**不计入上面的地雷数**）

### 4.1 待验证：拿不准的三种情况（240 条）

这些成员在索引里确实找不到，但存在一种**可能是假的**理由，所以不敢当成实证：

| 理由 | 含义 |
|---|---|
| `mixin-target` | 该类被某个 `@Mixin(...)` 认领 —— 那个 mixin **可能**把缺失成员织了进去 |
| `woven-subtype` | 它的某个子类型声明了同名同描述符的成员 —— 可能是 mixin 接口注入的 default 方法 |
| `jdk-unknown` | 继承链上碰到一个没建模的 JDK 类型（该 JRE 里没有 / javap 拿不到） → 无法判定 |

本工具**既不**据此判定它存在，**也不**判定它不存在。表里最后一列会标出具体是哪种理由。

要证实/证伪：在 dev 环境 `javap -p` 看**织入后**的类；或读对应 mixin 类的 `@Inject`/`@Shadow` 里的成员名；或直接写一个像 `fix-npe-and-itemhelper.md` 里那样的行为级探针跑一次。

| # | 缺失成员 | 所属 jar | 类.方法:行 | 什么情况下会炸 | 站点 |
|---|---|---|---|---|---|
| 1 | `net/minecraft/world/item/ItemStack.getCraftingRemainder()Lnet/minecraft/world/item/ItemStackTemplate;` | `FarmersDelight-26.3-3.6.28+refabricated`, `balm-fabric-26.3-26.3.0.3` +1 | AbstractStoveBlock.tryToExtinguish:119 / FeastBlock.takeServing:125 …(+19) | 走到 getCraftingRemainingItem() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 21 |
| 2 | `net/minecraft/world/entity/Entity.spawnReason()Lnet/minecraft/world/entity/EntitySpawnReason;` | `fabric-api-0.163.0+26.3`, `modmenu-21.0.0` +1 | PersistentEntitySectionManagerMixin.beforeAddEntity:39 / PersistentEntitySectionManagerMixin.beforeAddEntity:39 …(+1) | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 3 |
| 3 | `net/minecraft/server/network/ServerConfigurationPacketListenerImpl.addTask(Lnet/minecraft/server/network/ConfigurationTask;)V` | `ForgeConfigAPIPort-v26.3.1-mc26.3.x-Fabric`, `fabric-api-0.163.0+26.3` | ForgeConfigAPIPortFabric.lambda$registerEventHandlers$0:35 / AttachmentSync.lambda$onInitialize$0:130 …(+4) | 走到 lambda$onInitialize$0() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 6 |
| 4 | `net/minecraft/client/renderer/block/BlockStateModelSet.getParticleMaterial(Lnet/minecraft/world/level/block/state/BlockState;Lnet/minecraft/client/renderer/block/BlockAndTintGetter;Lnet/minecraft/core/BlockPos;)Lnet/minecraft/client/resources/model/sprite/Material$Baked;` ⚠同名异签名: `(Lnet/minecraft/world/level/block/state/BlockState;)Lnet` | `fabric-api-0.163.0+26.3`, `sodium-fabric-0.9.3-beta.1+mc26.3` | BlockMarkerMixin.getParticleMaterialProxy:34 / LevelExtractorMixin.getParticleMaterialProxy:46 …(+4) | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 6 |
| 5 | `net/minecraft/world/level/block/entity/BlockEntity.getRenderData()Ljava/lang/Object;` | `fabric-api-0.163.0+26.3`, `sodium-fabric-0.9.3-beta.1+mc26.3` | FabricBlockGetter.getBlockEntityRenderData:70 / RenderRegionCacheMixin.mapChunk:108 …(+3) | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 5 |
| 6 | `net/minecraft/core/DefaultedRegistry.addAlias(Lnet/minecraft/resources/Identifier;Lnet/minecraft/resources/Identifier;)V` | `FarmersDelight-26.3-3.6.28+refabricated`, `balm-fabric-26.3-26.3.0.3` | RegistryAliases.addBlockAlias:21 / RegistryAliases.addItemAlias:25 …(+1) | 走到 enableMilkFluid() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 3 |
| 7 | `net/minecraft/world/level/block/Block.getProvidedEnchantmentPower(Lnet/minecraft/world/level/block/state/BlockState;Lnet/minecraft/world/level/BlockGetter;Lnet/minecraft/core/BlockPos;)F` | `Jade-mc26.3-Fabric-26.3.5`, `fabric-api-0.163.0+26.3` | ClientProxy.getEnchantPowerBonus:286 / FabricBlockState.getProvidedEnchantmentPower:65 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 8 | `net/minecraft/client/renderer/block/BlockModelRenderState.setupMesh(Lorg/joml/Matrix4fc;Z)Lnet/fabricmc/fabric/api/client/renderer/v1/mesh/QuadEmitter;` | `fabric-api-0.163.0+26.3`, `sodium-fabric-0.9.3-beta.1+mc26.3` | BlockStateModelWrapperMixin.update:53 / BlockStateModelWrapperMixin.update:53 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 9 | `net/minecraft/world/level/storage/ValueInput.contains(Ljava/lang/String;)Z` | `aeronautics-fabric-0.1.0-port.26.3` | DockingConnectorBlockEntity.read:472 / DockingConnectorBlockEntity.read:478 …(+28) | 从存档/网络读这个对象时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 30 |
| 10 | 类 `net/minecraft/world/level/block/entity/FuelValues` | `create-fly-26.2-6.0.9-2-26.3-patched` | AllItemAttributeTypes / SchematicChunkSource$EmptierChunk$DummyLevel …(+5) | 走到 该类() 这条路径时 → NoClassDefFoundError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 7 |
| 11 | `net/minecraft/data/tags/TagAppender.getBuilder()Lnet/minecraft/tags/TagBuilder;` | `fabric-api-0.163.0+26.3` | BlockItemTagAppenderMixin.setReplace:47 / BlockItemTagAppenderMixin.forceAddTag:53 …(+5) | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 7 |
| 12 | `net/minecraft/tags/TagBuilder.removeElement(Lnet/minecraft/resources/Identifier;)Lnet/minecraft/tags/TagBuilder;` | `fabric-api-0.163.0+26.3` | BlockItemTagAppenderMixin.remove:62 / BlockItemTagAppenderMixin.lambda$remove$0:68 …(+5) | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 7 |
| 13 | `net/minecraft/world/level/Level.fuelValues()Lnet/minecraft/world/level/block/entity/FuelValues;` | `create-fly-26.2-6.0.9-2-26.3-patched` | AllItemAttributeTypes.lambda$static$5:60 / WrappedLevel.fuelValues:314 …(+3) | 走到 lambda$static$5() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 5 |
| 14 | `net/minecraft/client/renderer/feature/FeatureRenderDispatcher.renderAllFeatures(Lnet/minecraft/client/renderer/SubmitNodeStorage;)V` ⚠同名异签名: `(Lcom/mojang/renderpearl/api/commands/RenderPass;Lnet/mi` | `create-fly-26.2-6.0.9-2-26.3-patched` | BlockTransformElementRenderer.prepare:81 / EntityBlockRenderer.prepare:105 …(+3) | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 5 |
| 15 | `net/minecraft/server/network/ServerConfigurationPacketListenerImpl.completeTask(Lnet/minecraft/server/network/ConfigurationTask$Type;)V` | `fabric-api-0.163.0+26.3` | AttachmentSync.lambda$onInitialize$1:143 / CommonPacketsImpl.lambda$init$0:50 …(+3) | 走到 lambda$onInitialize$1() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 5 |
| 16 | `net/minecraft/client/player/LocalPlayer.swing(Lnet/minecraft/world/InteractionHand;)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | ChainConveyorConnectionHandler.onItemUsedOnBlock:91 / CurvedTrackInteraction.clientTick:76 …(+2) | 走到 onItemUsedOnBlock() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 4 |
| 17 | `net/minecraft/server/network/ServerConfigurationPacketListenerImpl.getPacketContext()Lnet/fabricmc/fabric/api/networking/v1/context/PacketContext;` | `fabric-api-0.163.0+26.3` | ServerConfigurationNetworking$Context.packetContext:301 / AttachmentSync.lambda$onInitialize$1:141 …(+2) | 走到 lambda$onInitialize$1() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 4 |
| 18 | `net/minecraft/world/level/block/state/BlockState.blocksMotion()Z` | `create-fly-26.2-6.0.9-2-26.3-patched` | MetalLadderBlock.skipRendering:48 / FluidFillingBehaviour.canBeReplacedByFluid:320 …(+1) | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 3 |
| 19 | `net/minecraft/data/tags/BlockItemTagAppender.forceAddTag(Lnet/minecraft/tags/TagKey;)Lnet/minecraft/data/tags/TagAppender;` | `FarmersDelight-26.3-3.6.28+refabricated` | BlockTags$RefabricatedTagBuilder.addTag:448 / ItemTags$RefabricatedTagBuilder.addTags:421 …(+1) | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 3 |
| 20 | 类 `net/minecraft/world/entity/animal/Rabbit` | `rabbit_pathfinding_fix-1.0.5-26.3` | RabbitEntityEatCarrotCropGoalMixin / RabbitEntityMixin …(+1) | 该方块/实体被操作时 → NoClassDefFoundError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 3 |
| 21 | `net/minecraft/world/entity/item/ItemEntity.getAttachedOrElse(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;Ljava/lang/Object;)Ljava/lang/Object;` | `architectury-fabric-22.0.5` | ItemEntityHooksImpl$1.getAsInt:47 / MixinItemEntity.architectury$modifyLifespan:66 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 22 | `net/minecraft/world/level/block/entity/SignText.getMessages(Z)[Lnet/minecraft/network/chat/Component;` ⚠同名异签名: `(Z)Ljava/util/List;` | `create-fly-26.2-6.0.9-2-26.3-patched` | NBTProcessors.lambda$static$0:49 / PackagerBlockEntity.getSign:650 | 走到 lambda$static$0() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 23 | `net/minecraft/world/entity/player/Player.drop(Lnet/minecraft/world/item/ItemStack;Z)Lnet/minecraft/world/entity/item/ItemEntity;` | `create-fly-26.2-6.0.9-2-26.3-patched` | ManualApplicationHelper.manualApplicationRecipesApplyInWorld:103 / BlazeBurnerBlock.useItemOn:163 | 走到 manualApplicationRecipesApplyInWorld() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 24 | `net/minecraft/world/level/block/entity/FuelValues.burnDuration(Lnet/minecraft/world/item/ItemStack;)I` | `create-fly-26.2-6.0.9-2-26.3-patched` | BlazeBurnerBlockEntity.tryUpdateFuel:207 / Train.lambda$burnFuel$0:1237 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 25 | `net/minecraft/tags/TagBuilder.removeTag(Lnet/minecraft/resources/Identifier;)Lnet/minecraft/tags/TagBuilder;` | `fabric-api-0.163.0+26.3` | BlockItemTagAppenderMixin.removeTag:86 / TagAppenderMixin$TagAppender1Mixin.removeTag:85 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 26 | `net/minecraft/core/particles/BlockParticleOption.getBlockPos()Lnet/minecraft/core/BlockPos;` | `fabric-api-0.163.0+26.3` | ExtendedBlockParticleOptionStreamCodec.encode:50 / TerrainParticleMixin.constructTerrainParticle:64 | 发包时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 27 | `net/minecraft/world/level/block/state/BlockBehaviour$Properties.blockIdOrThrow()Lnet/minecraft/resources/ResourceKey;` | `FarmersDelight-26.3-3.6.28+refabricated` | LaunchpadFenceGateBlockMixin.fdrf$modifyOpenSound:16 / LaunchpadFenceGateBlockMixin.fdrf$modifyCloseSound:24 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 28 | `net/minecraft/world/entity/animal/Rabbit.jumping : Z` | `rabbit_pathfinding_fix-1.0.5-26.3` | RabbitEntityEatCarrotCropGoalMixin.tickWaitUntilRabbitHasCompletedJump:98 / RabbitEntityRabbitMoveControlMixin.tickRespectJumping:31 | 该方块/实体被操作时 → NoSuchFieldError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 29 | `net/minecraft/world/entity/item/ItemEntity.setAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;Ljava/lang/Object;)Ljava/lang/Object;` | `architectury-fabric-22.0.5` | ItemEntityHooksImpl$1.accept:42 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 30 | `net/minecraft/client/resources/model/ModelManager.getModel(Lnet/fabricmc/fabric/api/client/model/loading/v1/ExtraModelKey;)Ljava/lang/Object;` | `balm-fabric-26.3-26.3.0.3` | FabricBalmBlockStateModelRegistrar$FabricDeferredBlockStateModel.asBlockStateModel:40 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 31 | `net/minecraft/world/entity/LivingEntity.randomTeleport(DDDZ)Z` ⚠同名异签名: `(DDDZLjava/util/function/Predicate;)Z` / `(DDDZLnet/minecraft/tags/TagKey;)Z` | `create-fly-26.2-6.0.9-2-26.3-patched` | AllPotatoProjectileEntityHitActions$ChorusTeleport.execute:172 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 32 | `net/minecraft/server/level/ServerPlayer.drop(Lnet/minecraft/world/item/ItemStack;ZZ)Lnet/minecraft/world/entity/item/ItemEntity;` ⚠同名异签名: `(Lnet/minecraft/world/item/ItemStack;ZLnet/minecraft/uti` / `(Z)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | DeployerBlockEntity.lambda$discardPlayer$0:505 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 33 | `net/minecraft/world/level/block/entity/HopperBlockEntity.insertExist(Lnet/minecraft/world/item/ItemStack;)I` | `create-fly-26.2-6.0.9-2-26.3-patched` | DrillBlockEntity.optimiseCobbleGen:84 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 34 | `net/minecraft/world/level/block/entity/SignBlockEntity.getText(Z)Lnet/minecraft/world/level/block/entity/SignText;` ⚠同名异签名: `(Lnet/minecraft/world/level/block/entity/SignTextSlot;)L` | `create-fly-26.2-6.0.9-2-26.3-patched` | PackagerBlockEntity.getSign:648 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 35 | `net/minecraft/client/renderer/entity/EntityRenderer.shouldRender(Lnet/minecraft/world/entity/Entity;Lnet/minecraft/client/renderer/culling/Frustum;DDD)Z` ⚠同名异签名: `(Lnet/minecraft/world/entity/Entity;Lnet/minecraft/clien` | `create-fly-26.2-6.0.9-2-26.3-patched` | ContraptionEntityRenderer.shouldRender:139 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 36 | `net/minecraft/client/renderer/entity/EntityRenderer.getBoundingBoxForCulling(Lnet/minecraft/world/entity/Entity;)Lnet/minecraft/world/phys/AABB;` ⚠同名异签名: `(Lnet/minecraft/world/entity/Entity;F)Lnet/minecraft/wor` | `create-fly-26.2-6.0.9-2-26.3-patched` | EntityVisibilityTester.check:46 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 37 | `net/minecraft/client/player/LocalPlayer.swinging : Z` | `create-fly-26.2-6.0.9-2-26.3-patched` | ValueSettingsClient.tick:101 | 每 tick 更新时（世界里一直跑） → NoSuchFieldError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 38 | `net/minecraft/world/level/block/Block.getAppearance(Lnet/minecraft/world/level/block/state/BlockState;Lnet/minecraft/world/level/BlockAndLightGetter;Lnet/minecraft/core/BlockPos;Lnet/minecraft/core/Direction;Lnet/minecraft/world/level/block/state/BlockState;Lnet/minecraft/core/BlockPos;)Lnet/minecraft/world/level/block/state/BlockState;` | `fabric-api-0.163.0+26.3` | FabricBlockState.getAppearance:47 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 39 | `net/minecraft/commands/arguments/selector/EntitySelectorParser.getCustomFlag(Lnet/minecraft/resources/Identifier;)Z` | `fabric-api-0.163.0+26.3` | EntitySelectorOptionRegistry.lambda$registerNonRepeatable$1:82 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 40 | `net/minecraft/commands/arguments/selector/EntitySelectorParser.setCustomFlag(Lnet/minecraft/resources/Identifier;Z)V` | `fabric-api-0.163.0+26.3` | EntitySelectorOptionRegistry.lambda$registerNonRepeatable$0:81 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 41 | `net/minecraft/client/gui/screens/recipebook/SearchRecipeBookCategory.FARMERSDELIGHT_COOKING : Lnet/minecraft/client/gui/screens/recipebook/SearchRecipeBookCategory;` | `FarmersDelight-26.3-3.6.28+refabricated` | CookingPotRecipeBookComponent.<clinit>:28 | 类第一次被加载时（注册期几乎必然） → NoSuchFieldError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 42 | `net/minecraft/world/level/block/entity/BlockEntityType.addValidBlock(Lnet/minecraft/world/level/block/Block;)V` | `FarmersDelight-26.3-3.6.28+refabricated` | ModBlockEntityTypes.addSupportedBlocks:45 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 43 | `net/minecraft/world/inventory/RecipeBookType.FARMERSDELIGHT_COOKING : Lnet/minecraft/world/inventory/RecipeBookType;` | `FarmersDelight-26.3-3.6.28+refabricated` | FDRecipeBookTypes.<clinit>:6 | 类第一次被加载时（注册期几乎必然） → NoSuchFieldError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 44 | `net/minecraft/world/level/block/state/BlockState.is(Lnet/minecraft/world/level/block/Block;)Z` | `rabbit_pathfinding_fix-1.0.5-26.3` | RabbitEntityEatCarrotCropGoalMixin.isTargetPosDoNotAbortWhenHavingTarget:136 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 45 | `net/minecraft/world/entity/animal/Rabbit.onGround()Z` | `rabbit_pathfinding_fix-1.0.5-26.3` | RabbitEntityRabbitMoveControlMixin.tickRespectJumping:31 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 46 | `net/minecraft/world/entity/animal/Rabbit.jumpControl : Lnet/minecraft/world/entity/ai/control/JumpControl;` | `rabbit_pathfinding_fix-1.0.5-26.3` | RabbitEntityRabbitMoveControlMixin.tickRespectJumping:31 | 该方块/实体被操作时 → NoSuchFieldError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 47 | `net/minecraft/world/entity/animal/Rabbit.getNavigation()Lnet/minecraft/world/entity/ai/navigation/PathNavigation;` | `rabbit_pathfinding_fix-1.0.5-26.3` | RabbitEntityRabbitMoveControlMixin.setSpeedToRabbit:56 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 48 | `net/minecraft/world/entity/animal/Rabbit.setSpeedModifier(D)V` | `rabbit_pathfinding_fix-1.0.5-26.3` | RabbitEntityRabbitMoveControlMixin.setSpeedToRabbit:58 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 49 | 类 `cc/cassian/rrv/common/recipe/inventory/RecipeViewScreen` | `FarmersDelight-26.3-3.6.28+refabricated`, `create-fly-26.2-6.0.9-2-26.3-patched` | CookingPotClientRecipe / DecompositionClientRecipe …(+23) | 走到 该类() 这条路径时 → NoClassDefFoundError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 25 |
| 50 | `com/mojang/blaze3d/platform/InputConstants.isKeyDown(Lcom/mojang/blaze3d/platform/Window;I)Z` ⚠同名异签名: `(I)Z` | `create-fly-26.2-6.0.9-2-26.3-patched` | ControlsHandler.tick:83 / LinkedControllerClientHandler.tick:165 …(+5) | 每 tick 更新时（世界里一直跑） → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 7 |
| 51 | `com/zurrtum/create/content/logistics/vault/ItemVaultBlockEntity$ItemVaultHandler.extract(Lnet/minecraft/world/item/ItemStack;)I` | `create-fly-26.2-6.0.9-2-26.3-patched` | ItemVaultBlockEntity$ConnectedItemVaultHandler.extract:611 / ItemVaultBlockEntity$ConnectedItemVaultHandler.extract:652 …(+3) | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 5 |
| 52 | `com/zurrtum/create/content/processing/recipe/ProcessingInventory.insert(Lnet/minecraft/world/item/ItemStack;)I` | `create-fly-26.2-6.0.9-2-26.3-patched` | BeltCrusherInteractionHandler.checkForCrushers:60 / SawBlockEntity.insertItem:444 | 走到 checkForCrushers() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 2 |
| 53 | `com/zurrtum/create/content/kinetics/millstone/MillstoneBlockEntity$MillstoneInventoryHandler.insert(Lnet/minecraft/world/item/ItemStack;)I` | `create-fly-26.2-6.0.9-2-26.3-patched` | MillstoneBlock.onEntityMovement:117 / MillstoneBlockEntity.process:146 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 2 |
| 54 | `com/zurrtum/create/api/contraption/storage/item/MountedItemStorageWrapper.extract(Ljava/util/function/Predicate;I)Lnet/minecraft/world/item/ItemStack;` | `create-fly-26.2-6.0.9-2-26.3-patched` | OrientedContraptionEntity.powerFurnaceCartWithFuelFromStorage:453 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 55 | `com/zurrtum/create/content/kinetics/base/KineticBlock.playerDestroy(Lnet/minecraft/world/level/Level;Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;Lnet/minecraft/world/level/block/entity/BlockEntity;Lnet/minecraft/world/item/ItemStack;)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | ChainConveyorBlock.playerDestroy:92 | 玩家挖掉这个方块时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 56 | `com/zurrtum/create/content/kinetics/crafter/MechanicalCrafterBlockEntity$CrafterItemHandler.matches(Lnet/minecraft/world/item/ItemStack;Lnet/minecraft/world/item/ItemStack;)Z` | `create-fly-26.2-6.0.9-2-26.3-patched` | MechanicalCrafterBlock.useItemOn:262 | 玩家右键这个方块时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 57 | `com/zurrtum/create/content/kinetics/crafter/MechanicalCrafterBlockEntity$CrafterItemHandler.removeMaxSize(Lnet/minecraft/world/item/ItemStack;Ljava/util/Optional;)Lnet/minecraft/world/item/ItemStack;` | `create-fly-26.2-6.0.9-2-26.3-patched` | MechanicalCrafterBlockEntity$CrafterItemHandler.onExtract:72 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 58 | `com/zurrtum/create/content/kinetics/crafter/MechanicalCrafterBlockEntity$CrafterItemHandler.setMaxSize(Lnet/minecraft/world/item/ItemStack;Ljava/util/Optional;)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | MechanicalCrafterBlockEntity$CrafterItemHandler.setStack:127 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 59 | `com/zurrtum/create/content/kinetics/millstone/MillstoneBlockEntity$MillstoneInventoryHandler.insert(Ljava/util/List;)Ljava/util/List;` | `create-fly-26.2-6.0.9-2-26.3-patched` | MillstoneBlockEntity.process:144 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 60 | `com/zurrtum/create/content/processing/recipe/ProcessingInventory.insert(Ljava/util/List;)Ljava/util/List;` | `create-fly-26.2-6.0.9-2-26.3-patched` | SawBlockEntity.applyRecipe:325 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 61 | `com/zurrtum/create/content/logistics/packagerLink/LogisticallyLinkedBlockItem.updateCustomBlockEntityTag(Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/Level;Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/item/ItemStack;Lnet/minecraft/world/level/block/state/BlockState;)Z` | `create-fly-26.2-6.0.9-2-26.3-patched` | FactoryPanelBlockItem.updateCustomBlockEntityTag:56 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 62 | `com/zurrtum/create/content/logistics/packagePort/PackagePortBlockEntity$PackagePortInventory.insert(Lnet/minecraft/world/item/ItemStack;I)I` | `create-fly-26.2-6.0.9-2-26.3-patched` | FrogportBlockEntity.tick:185 | 每 tick 更新时（世界里一直跑） → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 63 | `com/zurrtum/create/content/logistics/packagePort/PackagePortBlockEntity$PackagePortInventory.extractAny()Lnet/minecraft/world/item/ItemStack;` | `create-fly-26.2-6.0.9-2-26.3-patched` | FrogportBlockEntity.tryPullingFromOwnAndAdjacentInventories:303 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 64 | `com/zurrtum/create/content/logistics/vault/ItemVaultBlockEntity$ItemVaultHandler.insert(Lnet/minecraft/world/item/ItemStack;)I` | `create-fly-26.2-6.0.9-2-26.3-patched` | ItemVaultBlockEntity$ConnectedItemVaultHandler.insert:584 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 65 | `com/zurrtum/create/content/logistics/vault/ItemVaultBlockEntity$ItemVaultHandler.extract(Ljava/util/function/Predicate;I)Lnet/minecraft/world/item/ItemStack;` | `create-fly-26.2-6.0.9-2-26.3-patched` | ItemVaultBlockEntity$ConnectedItemVaultHandler.extract:636 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 66 | `com/zurrtum/create/content/logistics/vault/ItemVaultBlockEntity$ItemVaultHandler.count(Ljava/util/function/Predicate;I)Lnet/minecraft/world/item/ItemStack;` | `create-fly-26.2-6.0.9-2-26.3-patched` | ItemVaultBlockEntity$ConnectedItemVaultHandler.preciseExtract:676 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 67 | `com/zurrtum/create/content/logistics/vault/ItemVaultBlockEntity$ItemVaultHandler.count(Lnet/minecraft/world/item/ItemStack;I)I` | `create-fly-26.2-6.0.9-2-26.3-patched` | ItemVaultBlockEntity$ConnectedItemVaultHandler.preciseExtract:693 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 68 | `com/zurrtum/create/content/processing/basin/BasinInventory.insert(Lnet/minecraft/world/item/ItemStack;)I` | `create-fly-26.2-6.0.9-2-26.3-patched` | BasinBlock.lambda$onEntityMovement$0:203 | 该方块/实体被操作时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 69 | `net/minecraft/world/item/ItemStack.canBeEnchantedWith(Lnet/minecraft/core/Holder;Lnet/fabricmc/fabric/api/item/v1/EnchantingContext;)Z` | `fabric-api-0.163.0+26.3`, `jei-26.3-fabric-31.15.0.79` | AnvilMenuMixin.callAllowEnchantingEvent:51 / EnchantCommandMixin.callAllowEnchantingEvent:41 …(+3) | 走到 callAllowEnchantingEvent() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 5 |
| 70 | `net/minecraft/client/model/Model.copyTransforms(Lnet/minecraft/client/model/Model;)V` | `fabric-api-0.163.0+26.3`, `sodium-fabric-0.9.3-beta.1+mc26.3` | TransformCopyingModel.setupAnim:60 / TransformCopyingModel.copyTransforms:78 …(+2) | 走到 setupAnim() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 4 |
| 71 | `net/minecraft/client/resources/model/sprite/MaterialBaker.spriteFinder(Lnet/fabricmc/fabric/api/client/renderer/v1/mesh/QuadAtlas;)Lnet/fabricmc/fabric/api/client/renderer/v1/sprite/SpriteFinder;` | `fabric-api-0.163.0+26.3`, `sodium-fabric-0.9.3-beta.1+mc26.3` | SimpleUnbakedExtraModel.lambda$bakeResolved$0:118 / SimpleModelWrapperMixin.lambda$analyzeMesh$0:85 …(+1) | 走到 lambda$bakeResolved$0() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 3 |
| 72 | `net/minecraft/client/renderer/item/ItemStackRenderState$LayerRenderState.emitter()Lnet/fabricmc/fabric/api/client/renderer/v1/mesh/QuadEmitter;` | `fabric-api-0.163.0+26.3`, `sodium-fabric-0.9.3-beta.1+mc26.3` | CuboidItemModelWrapperMixin.onReturnUpdate:63 / CuboidItemModelWrapperMixin.onReturnUpdate:63 | 走到 onReturnUpdate() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 73 | `net/minecraft/client/model/Model.getChildPart(Ljava/lang/String;)Lnet/minecraft/client/model/geom/ModelPart;` | `fabric-api-0.163.0+26.3`, `sodium-fabric-0.9.3-beta.1+mc26.3` | TransformCopyingModel.getChildPart:73 / TransformCopyingModel.getChildPart:73 | 走到 getChildPart() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 74 | `net/minecraft/client/renderer/state/level/CameraRenderState.clearExtraData()V` | `fabric-api-0.163.0+26.3`, `sodium-fabric-0.9.3-beta.1+mc26.3` | LevelRenderStateMixin.clearExtraRenderData:38 / LevelRenderStateMixin.clearExtraRenderData:38 | 走到 clearExtraRenderData() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 75 | `net/minecraft/network/Connection.getPacketContext()Lnet/fabricmc/fabric/api/networking/v1/context/PacketContext;` | `fabric-api-0.163.0+26.3` | ServerCommonPacketListenerImplMixin.getPacketContext:82 / ServerHandshakePacketListenerImplMixin.getPacketContext:37 …(+7) | 走到 getPacketContext() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 9 |
| 76 | `net/minecraft/client/gui/GuiGraphicsExtractor.textWithWordWrap(Lnet/minecraft/client/gui/Font;Lnet/minecraft/network/chat/FormattedText;IIIIZ)V` ⚠同名异签名: `(Lnet/minecraft/client/gui/Font;Lnet/minecraft/network/c` / `(Lnet/minecraft/client/gui/Font;Lnet/minecraft/network/c` | `create-fly-26.2-6.0.9-2-26.3-patched` | ComputerScreen.renderWindow:115 / AssemblyScreen.renderWindow:162 …(+4) | 走到 renderWindow() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 6 |
| 77 | `net/minecraft/world/item/crafting/Ingredient.requiresTesting()Z` | `fabric-api-0.163.0+26.3` | CombinedIngredient.requiresTesting:51 / DifferenceIngredient.requiresTesting:62 …(+2) | 走到 requiresTesting() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 4 |
| 78 | `net/minecraft/world/Container.ITEM_STACK_HASH_STRATEGY : Lit/unimi/dsi/fastutil/Hash$Strategy;` | `create-fly-26.2-6.0.9-2-26.3-patched` | RecipeApplier.applyRecipeOn:70 / BlueprintPreviewPacket.createMap:38 …(+1) | 走到 applyRecipeOn() 这条路径时 → NoSuchFieldError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 3 |
| 79 | `net/minecraft/client/gui/GuiGraphicsExtractor.tooltip(Lnet/minecraft/client/gui/Font;Ljava/util/List;IILnet/minecraft/client/gui/screens/inventory/tooltip/ClientTooltipPositioner;Lnet/minecraft/resources/Identifier;)V` ⚠同名异签名: `(Lnet/minecraft/client/gui/Font;Ljava/util/List;IILnet/m` | `create-fly-26.2-6.0.9-2-26.3-patched` | BlueprintOverlayRenderer.renderOverlay:331 / GoggleConfigScreen.renderWindow:105 …(+1) | 走到 renderOverlay() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 3 |
| 80 | 类 `net/minecraft/client/renderer/ItemInHandRenderer` | `create-fly-26.2-6.0.9-2-26.3-patched` | ExtendoGripRenderHandler / ShootableGadgetRenderHandler …(+1) | 走到 该类() 这条路径时 → NoClassDefFoundError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 3 |
| 81 | `net/minecraft/client/gui/screens/inventory/CreativeModeInventoryScreen.getCurrentPage()I` | `fabric-api-0.163.0+26.3` | FabricCreativeGuiComponents$CreativeModeTabButton.extractContents:72 / FabricCreativeGuiComponents$Type.lambda$static$0:78 …(+1) | 走到 extractContents() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 3 |
| 82 | `net/minecraft/world/item/crafting/Ingredient.getCustomIngredient()Lnet/fabricmc/fabric/api/recipe/v1/ingredient/CustomIngredient;` | `fabric-api-0.163.0+26.3` | CustomIngredientStreamCodec.encode:63 / OptionalCustomIngredientStreamCodec.encode:64 …(+1) | 发包时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 3 |
| 83 | `net/minecraft/world/level/Level.potionBrewing()Lnet/minecraft/world/item/alchemy/PotionBrewing;` | `create-fly-26.2-6.0.9-2-26.3-patched` | WrappedLevel.potionBrewing:309 / VirtualRenderWorld.potionBrewing:403 | 走到 potionBrewing() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 84 | `net/minecraft/client/renderer/entity/EntityRenderDispatcher.getPlayerRenderer(Lnet/minecraft/client/player/AbstractClientPlayer;)Lnet/minecraft/client/renderer/entity/player/AvatarRenderer;` | `create-fly-26.2-6.0.9-2-26.3-patched` | ExtendoGripRenderHandler.onRenderPlayerHand:96 / ShootableGadgetRenderHandler.onRenderPlayerHand:88 | 走到 onRenderPlayerHand() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 85 | `net/minecraft/client/multiplayer/ClientPacketListener.getPacketContext()Lnet/fabricmc/fabric/api/networking/v1/context/PacketContext;` | `fabric-api-0.163.0+26.3` | ClientPlayNetworking$Context.packetContext:304 / LocalPlayerMixin.getPacketContext:37 | 走到 packetContext() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 86 | `net/minecraft/tags/TagFile.remove()Ljava/util/List;` | `fabric-api-0.163.0+26.3` | ClientTagsLoader.loadTag:71 / TagLoaderMixin.loadRemoveEntries:56 | 走到 loadRemoveEntries() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 87 | `net/minecraft/network/FriendlyByteBuf.readCollection(Ljava/util/function/IntFunction;Lnet/minecraft/network/codec/StreamDecoder;)Ljava/util/Collection;` | `create-fly-26.2-6.0.9-2-26.3-patched` | CatnipStreamCodecs$2.decode:47 | 收包时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 88 | `net/minecraft/network/FriendlyByteBuf.writeCollection(Ljava/util/Collection;Lnet/minecraft/network/codec/StreamEncoder;)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | CatnipStreamCodecs$2.encode:52 | 发包时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 89 | `net/minecraft/client/renderer/ItemInHandRenderer.renderItem(Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/world/item/ItemStack;Lnet/minecraft/world/item/ItemDisplayContext;Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/SubmitNodeCollector;I)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | ShootableGadgetRenderHandler.onRenderPlayerHand:148 | 走到 onRenderPlayerHand() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 90 | `net/minecraft/client/renderer/item/ItemStackRenderState$LayerRenderState.prepareQuadList()Ljava/util/List;` | `create-fly-26.2-6.0.9-2-26.3-patched` | ItemModelRenderHelper.submitQuads:38 | 走到 submitQuads() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 91 | `net/minecraft/world/level/block/state/BlockState.getProvidedEnchantmentPower(Lnet/minecraft/world/level/BlockGetter;Lnet/minecraft/core/BlockPos;)F` | `fabric-api-0.163.0+26.3` | EnchantmentMenuMixin.addEnchantingPower:38 | 走到 addEnchantingPower() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 92 | `net/minecraft/client/gui/screens/inventory/CreativeModeInventoryScreen.hasAdditionalPages()Z` | `fabric-api-0.163.0+26.3` | FabricCreativeGuiComponents$CreativeModeTabButton.extractContents:61 | 走到 extractContents() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 93 | `net/minecraft/client/gui/screens/inventory/CreativeModeInventoryScreen.getPageCount()I` | `fabric-api-0.163.0+26.3` | FabricCreativeGuiComponents$Type.lambda$static$0:78 | 走到 lambda$static$0() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 94 | `net/minecraft/client/multiplayer/ClientConfigurationPacketListenerImpl.getPacketContext()Lnet/fabricmc/fabric/api/networking/v1/context/PacketContext;` | `fabric-api-0.163.0+26.3` | ClientConfigurationNetworking$Context.packetContext:297 | 走到 packetContext() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 95 | `net/minecraft/client/multiplayer/ClientRecipeContainer.getSynchronizedRecipes()Lnet/fabricmc/fabric/api/recipe/v1/sync/SynchronizedRecipes;` | `fabric-api-0.163.0+26.3` | ClientPacketListenerMixin.copyPreviousRecipes:42 | 走到 copyPreviousRecipes() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 96 | `net/minecraft/world/item/crafting/RecipeAccess.getSynchronizedRecipes()Lnet/fabricmc/fabric/api/recipe/v1/sync/SynchronizedRecipes;` | `FarmersDelight-26.3-3.6.28+refabricated` | FDRecipes.<init>:23 | 构造这个对象时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 97 | `net/minecraft/client/renderer/rendertype/RenderType.iris$getPipeline()Lcom/mojang/renderpearl/api/pipeline/RenderPipeline;` | `iris-fabric-1.11.7+mc26.3` | OuterWrappedRenderType.iris$getPipeline:82 | 走到 iris$getPipeline() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 98 | `net/minecraft/client/renderer/rendertype/RenderType.iris$getRenderTarget()Lcom/mojang/blaze3d/pipeline/RenderTarget;` | `iris-fabric-1.11.7+mc26.3` | OuterWrappedRenderType.iris$getRenderTarget:87 | 走到 iris$getRenderTarget() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 99 | `net/minecraft/tags/TagKey.getName()Lnet/minecraft/network/chat/Component;` | `jei-26.3-fabric-31.15.0.79` | RenderHelper.getName:133 | 走到 getName() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 100 | `com/zurrtum/create/mixin/WorldlyContainerMixin.directCopy(Lnet/minecraft/world/item/ItemStack;I)Lnet/minecraft/world/item/ItemStack;` | `create-fly-26.2-6.0.9-2-26.3-patched` | WorldlyContainerMixin.count:64 / WorldlyContainerMixin.count:85 …(+29) | 走到 count() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 31 |
| 101 | `com/zurrtum/create/mixin/WorldlyContainerMixin.onExtract(Lnet/minecraft/world/item/ItemStack;)Lnet/minecraft/world/item/ItemStack;` | `create-fly-26.2-6.0.9-2-26.3-patched` | WorldlyContainerMixin.count:64 / WorldlyContainerMixin.count:85 …(+27) | 走到 count() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 29 |
| 102 | `com/zurrtum/create/mixin/WorldlyContainerMixin.matches(Lnet/minecraft/world/item/ItemStack;Lnet/minecraft/world/item/ItemStack;)Z` | `create-fly-26.2-6.0.9-2-26.3-patched` | WorldlyContainerMixin.count:45 / WorldlyContainerMixin.count:93 …(+21) | 走到 count() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 23 |
| 103 | `com/zurrtum/create/infrastructure/transfer/InventoryWrapper.directCopy(Lnet/minecraft/world/item/ItemStack;I)Lnet/minecraft/world/item/ItemStack;` | `create-fly-26.2-6.0.9-2-26.3-patched` | InventoryWrapper.count:94 / InventoryWrapper.count:118 …(+16) | 走到 count() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 18 |
| 104 | `com/zurrtum/create/mixin/WorldlyContainerMixin.ITEM_STACK_HASH_STRATEGY : Lit/unimi/dsi/fastutil/Hash$Strategy;` | `create-fly-26.2-6.0.9-2-26.3-patched` | WorldlyContainerMixin.countSpace:297 / WorldlyContainerMixin.countSpace:365 …(+4) | 走到 countSpace() 这条路径时 → NoSuchFieldError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 6 |
| 105 | `com/zurrtum/create/infrastructure/transfer/InventoryWrapper.ITEM_STACK_HASH_STRATEGY : Lit/unimi/dsi/fastutil/Hash$Strategy;` | `create-fly-26.2-6.0.9-2-26.3-patched` | InventoryWrapper.countSpace:247 / InventoryWrapper.extract:375 …(+2) | 走到 countSpace() 这条路径时 → NoSuchFieldError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 4 |
| 106 | `cc/cassian/rrv/api/recipe/ReliableClientRecipeType.getSlotCount()I` | `create-fly-26.2-6.0.9-2-26.3-patched` | CreateView.placeSlots:59 / CreateView.bindSlots:66 …(+2) | 走到 placeSlots() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 4 |
| 107 | `com/mojang/renderpearl/api/commands/RenderPass.iris$setCustomPass(Lnet/irisshaders/iris/mixinterface/CustomPass;)V` | `iris-fabric-1.11.7+mc26.3` | CenterDepthSampler.sampleCenterDepth:103 / ColorSpaceFragmentConverter.process:110 …(+2) | 走到 sampleCenterDepth() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 4 |
| 108 | `cc/cassian/rrv/api/recipe/ReliableClientRecipe.bindSlots(Lcc/cassian/rrv/common/recipe/inventory/RecipeViewMenu$SlotFillContext;)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | BlueprintTransferHandler.handle:35 / StockKeeperTransferHandler.handle:71 | 走到 handle() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 2 |
| 109 | 类 `cc/cassian/rrv/common/recipe/inventory/RecipeViewMenu` | `create-fly-26.2-6.0.9-2-26.3-patched` | RecipeButton / RrvRecipeViewScreenMixin | 走到 该类() 这条路径时 → NoClassDefFoundError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 110 | `cc/cassian/rrv/common/recipe/inventory/RecipeViewMenu.getClientRecipeType()Lcc/cassian/rrv/api/recipe/ReliableClientRecipeType;` | `create-fly-26.2-6.0.9-2-26.3-patched` | RecipeButton.renderInvalidSlots:58 / RrvRecipeViewScreenMixin.initHandler:47 | 走到 renderInvalidSlots() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 111 | `com/mojang/renderpearl/api/device/GpuDevice.backend : Lcom/mojang/renderpearl/backend/api/GpuDeviceBackend;` | `create-fly-26.2-6.0.9-2-26.3-patched` | MaterialRenderState.setupFrameBuffer:185 / OitFramebuffer.composite:184 | 走到 setupFrameBuffer() 这条路径时 → NoSuchFieldError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 2 |
| 112 | `cc/cassian/rrv/common/recipe/inventory/RecipeViewMenu.getParentScreen()Lnet/minecraft/client/gui/screens/Screen;` | `create-fly-26.2-6.0.9-2-26.3-patched` | RrvRecipeViewScreenMixin.initHandler:46 / RrvRecipeViewScreenMixin.createButton:80 | 走到 initHandler() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 113 | `com/seibel/distanthorizons/api/methods/events/abstractEvents/DhApiBeforeTextureClearEvent.<init>()V` | `iris-fabric-1.11.7+mc26.3` | LodRendererEvents$10.<init>:195 / LodRendererEvents$3.<init>:100 | 构造这个对象时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 2 |
| 114 | `com/seibel/distanthorizons/api/methods/events/abstractEvents/DhApiBeforeRenderEvent.<init>()V` | `iris-fabric-1.11.7+mc26.3` | LodRendererEvents$2.<init>:85 / LodRendererEvents$7.<init>:156 | 构造这个对象时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 2 |
| 115 | `com/mojang/blaze3d/pipeline/RenderTarget.iris$bindFramebuffer()V` | `iris-fabric-1.11.7+mc26.3` | MixinCompiledShaderProgram.iris$unlockDepthColorState:132 / IrisRenderingPipeline.beginLevelRendering:1001 | 走到 iris$unlockDepthColorState() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 116 | `cc/cassian/rrv/common/recipe/inventory/RecipeViewMenu.guiOffsetLeft()I` | `create-fly-26.2-6.0.9-2-26.3-patched` | RecipeButton.renderInvalidSlots:56 | 走到 renderInvalidSlots() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 117 | `cc/cassian/rrv/common/recipe/inventory/RecipeViewMenu.guiOffsetTop(I)I` | `create-fly-26.2-6.0.9-2-26.3-patched` | RecipeButton.renderInvalidSlots:57 | 走到 renderInvalidSlots() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 118 | `cc/cassian/rrv/common/recipe/inventory/RecipeViewMenu.getSlot(I)Lnet/minecraft/world/inventory/Slot;` | `create-fly-26.2-6.0.9-2-26.3-patched` | RecipeButton.renderInvalidSlots:60 | 走到 renderInvalidSlots() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 119 | `cc/cassian/rrv/api/recipe/ReliableClientRecipe.getId()Lnet/minecraft/resources/Identifier;` | `create-fly-26.2-6.0.9-2-26.3-patched` | StockKeeperTransferHandler.handle:51 | 走到 handle() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 120 | `cc/cassian/rrv/api/recipe/ReliableClientRecipe.getIngredients()Ljava/util/List;` | `create-fly-26.2-6.0.9-2-26.3-patched` | StockKeeperTransferHandler.handle:95 | 走到 handle() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 121 | `cc/cassian/rrv/api/recipe/ReliableClientRecipe.getResults()Ljava/util/List;` | `create-fly-26.2-6.0.9-2-26.3-patched` | StockKeeperTransferHandler.handle:122 | 走到 handle() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 122 | `com/mojang/blaze3d/pipeline/RenderTarget.useDepth : Z` | `create-fly-26.2-6.0.9-2-26.3-patched` | MaterialRenderState.setupFrameBuffer:189 | 走到 setupFrameBuffer() 这条路径时 → NoSuchFieldError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 123 | `com/seibel/distanthorizons/api/methods/events/abstractEvents/DhApiAfterDhInitEvent.<init>()V` | `iris-fabric-1.11.7+mc26.3` | LodRendererEvents$1.<init>:54 | 构造这个对象时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 124 | `com/seibel/distanthorizons/api/methods/events/abstractEvents/DhApiBeforeBufferRenderEvent.<init>()V` | `iris-fabric-1.11.7+mc26.3` | LodRendererEvents$11.<init>:213 | 构造这个对象时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 125 | `com/seibel/distanthorizons/api/methods/events/abstractEvents/DhApiBeforeRenderSetupEvent.<init>()V` | `iris-fabric-1.11.7+mc26.3` | LodRendererEvents$12.<init>:237 | 构造这个对象时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 126 | `com/seibel/distanthorizons/api/methods/events/abstractEvents/DhApiBeforeRenderPassEvent.<init>()V` | `iris-fabric-1.11.7+mc26.3` | LodRendererEvents$13.<init>:266 | 构造这个对象时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 127 | `com/seibel/distanthorizons/api/methods/events/abstractEvents/DhApiBeforeApplyShaderRenderEvent.<init>()V` | `iris-fabric-1.11.7+mc26.3` | LodRendererEvents$14.<init>:366 | 构造这个对象时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 128 | `com/seibel/distanthorizons/api/methods/events/abstractEvents/DhApiBeforeGenericRenderSetupEvent.<init>()V` | `iris-fabric-1.11.7+mc26.3` | LodRendererEvents$4.<init>:115 | 构造这个对象时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 129 | `com/seibel/distanthorizons/api/methods/events/abstractEvents/DhApiBeforeGenericObjectRenderEvent.<init>()V` | `iris-fabric-1.11.7+mc26.3` | LodRendererEvents$5.<init>:124 | 构造这个对象时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 130 | `com/seibel/distanthorizons/api/methods/events/abstractEvents/DhApiColorDepthTextureCreatedEvent.<init>()V` | `iris-fabric-1.11.7+mc26.3` | LodRendererEvents$6.<init>:144 | 构造这个对象时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 131 | `com/seibel/distanthorizons/api/methods/events/abstractEvents/DhApiBeforeDeferredRenderEvent.<init>()V` | `iris-fabric-1.11.7+mc26.3` | LodRendererEvents$8.<init>:164 | 构造这个对象时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 132 | `com/seibel/distanthorizons/api/methods/events/abstractEvents/DhApiBeforeRenderCleanupEvent.<init>()V` | `iris-fabric-1.11.7+mc26.3` | LodRendererEvents$9.<init>:178 | 构造这个对象时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 133 | `org/apache/tools/ant/taskdefs/Copy.<init>()V` | `iris-fabric-1.11.7+mc26.3` | CppTask.<init>:33 | 构造这个对象时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 134 | `net/mezzdev/config/gui/api/IConfigValueEditorSerializer.isValid(Ljava/lang/Object;)Z` | `jei-26.3-fabric-31.15.0.79` | AlignmentConfigValueGuiAdapter.set:64 | 走到 set() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 135 | `org/dynmap/DynmapCommonAPIListener.<init>()V` | `waystones-fabric-26.3-26.3.0.1` | DynmapIntegration.<init>:31 | 构造这个对象时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 136 | `net/minecraft/client/renderer/texture/SpriteLoader$Preparations.spriteFinder()Lnet/fabricmc/fabric/api/client/renderer/v1/sprite/SpriteFinder;` | `fabric-api-0.163.0+26.3`, `sodium-fabric-0.9.3-beta.1+mc26.3` | MaterialBakerMixin.spriteFinder:50 / MaterialBakerMixin.spriteFinder:52 …(+2) | 走到 spriteFinder() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 4 |
| 137 | `net/minecraft/world/item/Item.getCraftingRemainder(Lnet/minecraft/world/item/ItemStack;)Lnet/minecraft/world/item/ItemStackTemplate;` ⚠同名异签名: `()Lnet/minecraft/world/item/ItemStackTemplate;` | `architectury-fabric-22.0.5`, `fabric-api-0.163.0+26.3` | ItemStackHooksImpl.getCraftingRemainingItem:31 / FabricItemStack.getCraftingRemainder:44 | 走到 getCraftingRemainingItem() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 138 | `net/minecraft/world/item/Item.getCreatorNamespace(Lnet/minecraft/world/item/ItemStack;)Ljava/lang/String;` | `Jade-mc26.3-Fabric-26.3.5`, `fabric-api-0.163.0+26.3` | CommonProxy.getModIdFromItem:126 / FabricItemStack.getCreatorNamespace:87 | 走到 getCreatorNamespace() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 139 | `net/minecraft/world/item/Item.canBeEnchantedWith(Lnet/minecraft/world/item/ItemStack;Lnet/minecraft/core/Holder;Lnet/fabricmc/fabric/api/item/v1/EnchantingContext;)Z` | `FarmersDelight-26.3-3.6.28+refabricated`, `fabric-api-0.163.0+26.3` | KnifeItem.canBeEnchantedWith:73 / FabricItemStack.lambda$canBeEnchantedWith$0:65 | 走到 lambda$canBeEnchantedWith$0() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 140 | `net/minecraft/advancements/Advancement$Builder.save(Ljava/util/function/Consumer;Lnet/minecraft/resources/Identifier;)Lnet/minecraft/advancements/AdvancementHolder;` ⚠同名异签名: `(Lnet/minecraft/data/worldgen/BootstrapContext;Ljava/lan` | `FarmersDelight-26.3-3.6.28+refabricated` | FDAdvancementGenerator.generateAdvancement:54 / FDAdvancementGenerator.generateAdvancement:65 …(+19) | 走到 generateAdvancement() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 21 |
| 141 | `net/minecraft/world/level/storage/loot/LootPool$Builder.add(Lnet/minecraft/world/level/storage/loot/entries/LootPoolEntryContainer;)Lnet/minecraft/world/level/storage/loot/LootPool$Builder;` ⚠同名异签名: `(Lnet/minecraft/world/level/storage/loot/entries/LootPoo` | `FarmersDelight-26.3-3.6.28+refabricated` | LootModificationEvents.chestLoot:102 / LootModificationEvents.chestLoot:105 …(+12) | 走到 chestLoot() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 14 |
| 142 | `net/minecraft/world/level/block/state/BlockState.isViewBlocking(Lnet/minecraft/world/level/BlockGetter;Lnet/minecraft/core/BlockPos;)Z` | `create-fly-26.2-6.0.9-2-26.3-patched` | AoFaceData.compute:104 / AoFaceData.compute:118 …(+7) | 走到 compute() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 9 |
| 143 | `net/minecraft/world/item/BlockItem.updateCustomBlockEntityTag(Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/Level;Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/item/ItemStack;Lnet/minecraft/world/level/block/state/BlockState;)Z` ⚠同名异签名: `(Lnet/minecraft/world/level/Level;Lnet/minecraft/world/e` | `create-fly-26.2-6.0.9-2-26.3-patched` | FluidTankItem.updateCustomBlockEntityTag:77 / VerticalGearboxItem.updateCustomBlockEntityTag:61 …(+5) | 走到 updateCustomBlockEntityTag() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 7 |
| 144 | `net/minecraft/server/network/ServerGamePacketListenerImpl.getPacketContext()Lnet/fabricmc/fabric/api/networking/v1/context/PacketContext;` | `fabric-api-0.163.0+26.3` | ServerPlayNetworking$Context.packetContext:368 / AttachmentSync.trySync:76 …(+3) | 走到 trySync() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 5 |
| 145 | `net/minecraft/server/packs/resources/Resource.getFabricPackSource()Lnet/minecraft/server/packs/repository/PackSource;` | `fabric-api-0.163.0+26.3` | AdvancementUtil.determineSource:70 / ResourceUtil.determineSource:29 …(+1) | 走到 determineSource() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 3 |
| 146 | `net/minecraft/commands/CommandSourceStack.<init>(Lnet/minecraft/commands/CommandSource;Lnet/minecraft/world/phys/Vec3;Lnet/minecraft/world/phys/Vec2;Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/server/permissions/PermissionSet;Ljava/lang/String;Lnet/minecraft/network/chat/Component;Lnet/minecraft/server/MinecraftServer;Lnet/minecraft/world/entity/Entity;)V` ⚠同名异签名: `(Lnet/minecraft/commands/CommandSource;Lnet/minecraft/wo` / `(Lnet/minecraft/commands/CommandSource;Lnet/minecraft/wo` | `create-fly-26.2-6.0.9-2-26.3-patched` | FlwCommands.lambda$createDebugCommand$0:163 / DynamicComponent.getCommandSource:42 | 走到 getCommandSource() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 147 | `net/minecraft/client/renderer/LevelRenderer.itemEntityTarget()Lcom/mojang/blaze3d/pipeline/RenderTarget;` | `create-fly-26.2-6.0.9-2-26.3-patched` | OitFramebuffer.prepare:58 / OitFramebuffer.composite:191 | 走到 prepare() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 148 | `net/minecraft/nbt/CompoundTag.getString(Ljava/lang/String;)Ljava/lang/String;` ⚠同名异签名: `(Ljava/lang/String;)Ljava/util/Optional;` | `DungeonsArise-2.1.68-26.3` | ModifiedStructurePoolBasedGenerator.findStartingJigsawPos:136 / ModifiedStructurePoolBasedGenerator$StructurePoolGenerator.lookupPool:387 | 走到 lookupPool() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 149 | `net/minecraft/tags/TagKey.getTranslationKey()Ljava/lang/String;` | `fabric-api-0.163.0+26.3` | FabricLanguageProvider$TranslationBuilder.add:302 / TranslationConventionLogWarnings.lambda$setupUntranslatedItemTagWarning$1:88 | 走到 lambda$setupUntranslatedItemTagWarning$1() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 150 | `net/minecraft/server/MinecraftServer.globalAttachments()Lnet/fabricmc/fabric/api/attachment/v1/GlobalAttachments;` | `fabric-api-0.163.0+26.3` | AttachmentSavedData.codec:57 / ServerLevelMixin.globalAttachments:102 | 走到 codec() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 151 | `net/minecraft/world/item/Item.allowComponentsUpdateAnimation(Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/InteractionHand;Lnet/minecraft/world/item/ItemStack;Lnet/minecraft/world/item/ItemStack;)Z` | `fabric-api-0.163.0+26.3` | FirstPersonHandsAndItemsMixin.modifyProgressAnimation:49 / FirstPersonHandsAndItemsMixin.modifyProgressAnimation:58 | 走到 modifyProgressAnimation() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 152 | `net/minecraft/world/level/storage/loot/LootTable$Builder.modifyPools(Ljava/util/function/Consumer;)Lnet/minecraft/world/level/storage/loot/LootTable$Builder;` | `FarmersDelight-26.3-3.6.28+refabricated` | LootModificationEvents.scavengingLoot:185 / LootModificationEvents.pastrySlicing:273 | 走到 scavengingLoot() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 2 |
| 153 | `net/minecraft/world/level/material/Fluid.arch$registryName()Lnet/minecraft/resources/Identifier;` | `architectury-fabric-22.0.5` | SimpleArchitecturyFluidAttributes.lambda$new$0:71 | 走到 lambda$new$0() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 154 | `net/minecraft/world/entity/player/Player.getAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Ljava/lang/Object;` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.get:21 | 走到 get() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 155 | `net/minecraft/world/entity/player/Player.getAttachedOrCreate(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Ljava/lang/Object;` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.getOrCreate:26 | 走到 getOrCreate() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 156 | `net/minecraft/world/entity/player/Player.hasAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Z` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.has:31 | 走到 has() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 157 | `net/minecraft/world/entity/player/Player.removeAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Ljava/lang/Object;` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.remove:36 | 走到 remove() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 158 | `net/minecraft/world/entity/player/Player.setAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;Ljava/lang/Object;)Ljava/lang/Object;` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.update:41 | 走到 update() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 159 | `net/minecraft/world/level/Level.getAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Ljava/lang/Object;` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.get:46 | 走到 get() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 160 | `net/minecraft/world/level/Level.getAttachedOrCreate(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Ljava/lang/Object;` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.getOrCreate:51 | 走到 getOrCreate() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 161 | `net/minecraft/world/level/Level.hasAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Z` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.has:56 | 走到 has() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 162 | `net/minecraft/world/level/Level.removeAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Ljava/lang/Object;` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.remove:61 | 走到 remove() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 163 | `net/minecraft/world/level/Level.setAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;Ljava/lang/Object;)Ljava/lang/Object;` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.update:66 | 走到 update() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 164 | `net/minecraft/world/entity/Entity.getAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Ljava/lang/Object;` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.get:71 | 走到 get() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 165 | `net/minecraft/world/entity/Entity.getAttachedOrCreate(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Ljava/lang/Object;` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.getOrCreate:76 | 走到 getOrCreate() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 166 | `net/minecraft/world/entity/Entity.hasAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Z` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.has:81 | 走到 has() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 167 | `net/minecraft/world/entity/Entity.removeAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Ljava/lang/Object;` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.remove:86 | 走到 remove() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 168 | `net/minecraft/world/entity/Entity.setAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;Ljava/lang/Object;)Ljava/lang/Object;` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.update:91 | 走到 update() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 169 | `net/minecraft/world/level/block/entity/BlockEntity.getAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Ljava/lang/Object;` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.get:96 | 走到 get() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 170 | `net/minecraft/world/level/block/entity/BlockEntity.getAttachedOrCreate(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Ljava/lang/Object;` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.getOrCreate:101 | 走到 getOrCreate() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 171 | `net/minecraft/world/level/block/entity/BlockEntity.hasAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Z` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.has:106 | 走到 has() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 172 | `net/minecraft/world/level/block/entity/BlockEntity.removeAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Ljava/lang/Object;` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.remove:111 | 走到 remove() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 173 | `net/minecraft/world/level/block/entity/BlockEntity.setAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;Ljava/lang/Object;)Ljava/lang/Object;` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.update:116 | 走到 update() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 174 | `net/minecraft/world/level/chunk/ChunkAccess.getAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Ljava/lang/Object;` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.get:121 | 走到 get() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 175 | `net/minecraft/world/level/chunk/ChunkAccess.getAttachedOrCreate(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Ljava/lang/Object;` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.getOrCreate:126 | 走到 getOrCreate() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 176 | `net/minecraft/world/level/chunk/ChunkAccess.hasAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Z` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.has:131 | 走到 has() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 177 | `net/minecraft/world/level/chunk/ChunkAccess.removeAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Ljava/lang/Object;` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.remove:136 | 走到 remove() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 178 | `net/minecraft/world/level/chunk/ChunkAccess.setAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;Ljava/lang/Object;)Ljava/lang/Object;` | `balm-fabric-26.3-26.3.0.3` | FabricDataAttachmentLookup.update:141 | 走到 update() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 179 | `net/minecraft/server/level/ServerPlayer.swing(Lnet/minecraft/world/InteractionHand;Z)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | AllHandle.onContraptionInteraction:1126 | 走到 onContraptionInteraction() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 180 | `net/minecraft/world/entity/player/Inventory.insert(Lnet/minecraft/world/item/ItemStack;III)I` | `create-fly-26.2-6.0.9-2-26.3-patched` | AllHandle.lambda$onToolboxEquip$0:1470 | 走到 lambda$onToolboxEquip$0() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 181 | `net/minecraft/world/level/block/entity/FuelValues.isFuel(Lnet/minecraft/world/item/ItemStack;)Z` | `create-fly-26.2-6.0.9-2-26.3-patched` | AllItemAttributeTypes.lambda$static$5:60 | 走到 lambda$static$5() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 182 | `net/minecraft/server/level/ServerPlayer.drop(Lnet/minecraft/world/item/ItemStack;Z)Lnet/minecraft/world/entity/item/ItemEntity;` ⚠同名异签名: `(Lnet/minecraft/world/item/ItemStack;ZLnet/minecraft/uti` / `(Z)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | BeltDeployerCallbacks.activate:184 | 走到 activate() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 183 | `net/minecraft/world/level/block/entity/SignText.setMessage(ILnet/minecraft/network/chat/Component;)Lnet/minecraft/world/level/block/entity/SignText;` | `create-fly-26.2-6.0.9-2-26.3-patched` | SignDisplayTarget.lambda$acceptText$0:37 | 走到 lambda$acceptText$0() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 184 | `net/minecraft/world/entity/player/Inventory.extract(Lnet/minecraft/world/item/ItemStack;)I` | `create-fly-26.2-6.0.9-2-26.3-patched` | ServerFilteringBehaviour.readFromClipboard:275 | 走到 readFromClipboard() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 185 | `net/minecraft/world/entity/player/Inventory.extract(Ljava/util/function/Predicate;I)Lnet/minecraft/world/item/ItemStack;` | `create-fly-26.2-6.0.9-2-26.3-patched` | ServerFilteringBehaviour.readFromClipboard:275 | 走到 readFromClipboard() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 186 | `net/minecraft/world/entity/player/Inventory.count(Lnet/minecraft/world/item/ItemStack;I)I` | `create-fly-26.2-6.0.9-2-26.3-patched` | ServerFilteringBehaviour.onShortInteract:318 | 走到 onShortInteract() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 187 | `net/minecraft/client/renderer/state/level/SkyRenderState.skyColor : I` ⚠同名异签名: `Lorg/joml/Vector3fc;` | `create-fly-26.2-6.0.9-2-26.3-patched` | LevelUniforms.update:45 | 走到 update() 这条路径时 → NoSuchFieldError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 188 | `net/minecraft/client/renderer/fog/environment/WaterFogEnvironment.getBaseColor(Lnet/minecraft/client/multiplayer/ClientLevel;Lnet/minecraft/client/Camera;IF)I` ⚠同名异签名: `(Lnet/minecraft/client/multiplayer/ClientLevel;Lnet/mine` | `create-fly-26.2-6.0.9-2-26.3-patched` | FluidFogModifier.getBaseColor:48 | 走到 getBaseColor() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 189 | `net/minecraft/nbt/CompoundTag.getInt(Ljava/lang/String;)I` ⚠同名异签名: `(Ljava/lang/String;)Ljava/util/Optional;` | `DungeonsArise-2.1.68-26.3` | ModifiedStructurePoolBasedGenerator$StructurePoolGenerator.generatePiece:254 | 走到 generatePiece() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 190 | `net/minecraft/server/level/ServerLevel.globalAttachments()Lnet/fabricmc/fabric/api/attachment/v1/GlobalAttachments;` | `fabric-api-0.163.0+26.3` | AttachmentSync.lambda$onInitialize$2:153 | 走到 lambda$onInitialize$2() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 191 | `net/minecraft/world/level/Level.globalAttachments()Lnet/fabricmc/fabric/api/attachment/v1/GlobalAttachments;` | `fabric-api-0.163.0+26.3` | AttachmentTargetInfo$GlobalTarget.getTarget:215 | 走到 getTarget() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 192 | `net/minecraft/world/level/chunk/LevelChunk.getAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Ljava/lang/Object;` | `fabric-api-0.163.0+26.3` | ImposterProtoChunkMixin.getAttached:48 | 走到 getAttached() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 193 | `net/minecraft/world/level/chunk/LevelChunk.setAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;Ljava/lang/Object;)Ljava/lang/Object;` | `fabric-api-0.163.0+26.3` | ImposterProtoChunkMixin.setAttached:54 | 走到 setAttached() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 194 | `net/minecraft/world/level/chunk/LevelChunk.hasAttached(Lnet/fabricmc/fabric/api/attachment/v1/AttachmentType;)Z` | `fabric-api-0.163.0+26.3` | ImposterProtoChunkMixin.hasAttached:59 | 走到 hasAttached() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 195 | `net/minecraft/tags/TagBuilder.getRemovals()Ljava/util/List;` | `fabric-api-0.163.0+26.3` | TagsProviderMixin.addRemove:62 | 走到 addRemove() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 196 | `net/minecraft/world/effect/MobEffect.onEffectRemoved(Lnet/minecraft/world/effect/MobEffectInstance;Lnet/minecraft/world/entity/LivingEntity;)V` | `fabric-api-0.163.0+26.3` | ServerMobEffectEvents.lambda$static$14:157 | 走到 lambda$static$14() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 197 | `net/minecraft/world/effect/MobEffect.onEffectStarted(Lnet/minecraft/world/effect/MobEffectInstance;Lnet/minecraft/world/entity/LivingEntity;)V` ⚠同名异签名: `(Lnet/minecraft/world/entity/LivingEntity;I)V` | `fabric-api-0.163.0+26.3` | ServerMobEffectEvents.lambda$static$13:154 | 走到 lambda$static$13() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 198 | `net/minecraft/world/effect/MobEffect.onEffectAdded(Lnet/minecraft/world/effect/MobEffectInstance;Lnet/minecraft/world/entity/LivingEntity;)V` ⚠同名异签名: `(Lnet/minecraft/world/entity/LivingEntity;I)V` | `fabric-api-0.163.0+26.3` | ServerMobEffectEvents.lambda$static$12:151 | 走到 lambda$static$12() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 199 | `net/minecraft/core/component/DataComponentMap$Builder.get(Lnet/minecraft/core/component/DataComponentType;)Ljava/lang/Object;` | `fabric-api-0.163.0+26.3` | FabricItem$Properties.lambda$modifyComponent$0:184 | 走到 lambda$modifyComponent$0() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 200 | `net/minecraft/world/item/Item.allowContinuingBlockBreaking(Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/item/ItemStack;Lnet/minecraft/world/item/ItemStack;)Z` | `fabric-api-0.163.0+26.3` | MultiPlayerGameModeMixin.fabricItemContinueBlockBreakingInject:60 | 走到 fabricItemContinueBlockBreakingInject() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 201 | `net/minecraft/world/level/storage/loot/LootPool$Builder.add(Ljava/util/Collection;)Lnet/minecraft/world/level/storage/loot/LootPool$Builder;` ⚠同名异签名: `(Lnet/minecraft/world/level/storage/loot/entries/LootPoo` | `fabric-api-0.163.0+26.3` | FabricLootPoolBuilder.copyOf:109 | 走到 copyOf() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 202 | `net/minecraft/world/level/storage/loot/LootTable$Builder.pools(Ljava/util/Collection;)Lnet/minecraft/world/level/storage/loot/LootTable$Builder;` ⚠同名异签名: `Lcom/google/common/collect/ImmutableList$Builder;` | `fabric-api-0.163.0+26.3` | FabricLootTableBuilder.copyOf:106 | 走到 copyOf() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 203 | `net/minecraft/world/MenuProvider.shouldCloseCurrentScreen()Z` | `fabric-api-0.163.0+26.3` | ServerPlayerMixin.fabric_closeContainerScreenIfAllowed:60 | 走到 fabric_closeContainerScreenIfAllowed() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 204 | `net/minecraft/core/component/DataComponentMap$Builder.getOrCreate(Lnet/minecraft/core/component/DataComponentType;Ljava/util/function/Supplier;)Ljava/lang/Object;` | `FarmersDelight-26.3-3.6.28+refabricated` | CommonModBusEvents.addVanillaSoupEffect:62 | 走到 addVanillaSoupEffect() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 205 | `net/minecraft/world/item/BlockItem.allowComponentsUpdateAnimation(Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/InteractionHand;Lnet/minecraft/world/item/ItemStack;Lnet/minecraft/world/item/ItemStack;)Z` | `FarmersDelight-26.3-3.6.28+refabricated` | SkilletItem.allowComponentsUpdateAnimation:82 | 走到 allowComponentsUpdateAnimation() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 206 | `net/minecraft/world/item/BlockItem.canBeEnchantedWith(Lnet/minecraft/world/item/ItemStack;Lnet/minecraft/core/Holder;Lnet/fabricmc/fabric/api/item/v1/EnchantingContext;)Z` | `FarmersDelight-26.3-3.6.28+refabricated` | SkilletItem.canBeEnchantedWith:287 | 走到 canBeEnchantedWith() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 207 | `net/minecraft/world/level/storage/loot/LootTable$Builder.pool(Lnet/minecraft/world/level/storage/loot/LootPool;)Lnet/minecraft/world/level/storage/loot/LootTable$Builder;` | `FarmersDelight-26.3-3.6.28+refabricated` | LootModificationEvents.scavengingLoot:192 | 走到 scavengingLoot() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 208 | `net/minecraft/world/level/storage/loot/LootPool$Builder.when(Lnet/minecraft/world/level/storage/loot/predicates/LootItemCondition;)Lnet/minecraft/world/level/storage/loot/LootPool$Builder;` ⚠同名异签名: `(Lnet/minecraft/core/Holder;)Lnet/minecraft/world/level/` / `(Lnet/minecraft/core/Holder;)Lnet/minecraft/world/level/` | `FarmersDelight-26.3-3.6.28+refabricated` | LootModificationEvents.lambda$scavengingLoot$0:186 | 走到 lambda$scavengingLoot$0() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 209 | `net/minecraft/core/component/DataComponentMap$Builder.contains(Lnet/minecraft/core/component/DataComponentType;)Z` | `Jade-mc26.3-Fabric-26.3.5` | CommonProxy.hasComponent:181 | 走到 hasComponent() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 210 | `net/minecraft/world/item/ItemStack.getCreatorNamespace()Ljava/lang/String;` | `jei-26.3-fabric-31.15.0.79` | ItemStackHelper.getCreatorModId:64 | 走到 getCreatorModId() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 211 | `com/zurrtum/create/content/kinetics/crafter/MechanicalCrafterBlockEntity$CrafterItemHandler.insert(Lnet/minecraft/world/item/ItemStack;)I` | `create-fly-26.2-6.0.9-2-26.3-patched` | ArmScenes.lambda$filtering$0:317 / ArmScenes.lambda$filtering$1:340 …(+22) | 走到 lambda$filtering$1() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 24 |
| 212 | `com/zurrtum/create/infrastructure/transfer/InventoryWrapper$Slotted.directCopy(Lnet/minecraft/world/item/ItemStack;I)Lnet/minecraft/world/item/ItemStack;` | `create-fly-26.2-6.0.9-2-26.3-patched` | InventoryWrapper$Slotted.insert:1757 / InventoryWrapper$Slotted.insert:1776 …(+4) | 走到 insert() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 6 |
| 213 | `com/zurrtum/create/content/equipment/toolbox/ToolboxInventory.directCopy(Lnet/minecraft/world/item/ItemStack;I)Lnet/minecraft/world/item/ItemStack;` | `create-fly-26.2-6.0.9-2-26.3-patched` | ToolboxInventory.distributeToCompartment:130 / ToolboxInventory.takeFromCompartment:165 …(+3) | 走到 distributeToCompartment() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 5 |
| 214 | `cc/cassian/rrv/common/recipe/inventory/RecipeViewScreen.getFont()Lnet/minecraft/client/gui/Font;` | `create-fly-26.2-6.0.9-2-26.3-patched` | CompactingView.renderRecipe:161 / MechanicalCraftingView.renderRecipe:123 …(+3) | 走到 renderRecipe() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 5 |
| 215 | `com/zurrtum/create/infrastructure/transfer/InventoryWrapper$Slotted.ITEM_STACK_HASH_STRATEGY : Lit/unimi/dsi/fastutil/Hash$Strategy;` | `create-fly-26.2-6.0.9-2-26.3-patched` | InventoryWrapper$Slotted.countSpace:1680 / InventoryWrapper$Slotted.insert:1759 …(+1) | 走到 countSpace() 这条路径时 → NoSuchFieldError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 3 |
| 216 | `com/mojang/renderpearl/backend/opengl/GlRenderPass.iris$getCustomPass()Lnet/irisshaders/iris/mixinterface/CustomPass;` | `iris-fabric-1.11.7+mc26.3` | MixinGlCommandEncoder.iris$bypassSetup:125 / MixinGlCommandEncoder.iris$bypassSetup:129 …(+1) | 走到 iris$bypassSetup() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 3 |
| 217 | `com/mrcrayfish/configured/api/IConfigEntry.getValue()Lcom/mrcrayfish/configured/api/IConfigValue;` | `appleskin-fabric-mc26.3-3.0.10` | ConfiguredConfigProvider$ConfiguredModConfig.update:80 / ConfiguredConfigProvider$ConfiguredModConfig.startEditing:121 | 走到 update() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 2 |
| 218 | `com/zurrtum/create/client/compat/rrv/CreateView.getType()Lcc/cassian/rrv/api/recipe/ReliableClientRecipeType;` | `create-fly-26.2-6.0.9-2-26.3-patched` | CreateView.placeSlots:59 / CreateView.bindSlots:66 | 走到 placeSlots() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 2 |
| 219 | `com/mrcrayfish/configured/api/IConfigEntry.getChildren()Ljava/util/List;` | `appleskin-fabric-mc26.3-3.0.10` | ConfiguredConfigProvider$ConfiguredModConfig.update:78 | 走到 update() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 220 | `com/mrcrayfish/configured/api/IConfigValue.get()Ljava/lang/Object;` | `appleskin-fabric-mc26.3-3.0.10` | ConfiguredConfigProvider$ConfiguredModConfig.update:82 | 走到 update() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 221 | `com/mrcrayfish/configured/api/IConfigValue.getName()Ljava/lang/String;` | `appleskin-fabric-mc26.3-3.0.10` | ConfiguredConfigProvider$ConfiguredModConfig.update:85 | 走到 update() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 222 | `com/mrcrayfish/configured/api/IConfigValue.cleanCache()V` | `appleskin-fabric-mc26.3-3.0.10` | ConfiguredConfigProvider$ConfiguredModConfig.startEditing:123 | 走到 startEditing() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 223 | `com/zurrtum/create/content/equipment/toolbox/ToolboxInventory.insertExist(Lnet/minecraft/world/item/ItemStack;I)I` | `create-fly-26.2-6.0.9-2-26.3-patched` | AllHandle.lambda$onToolboxDisposeAll$0:1533 | 走到 lambda$onToolboxDisposeAll$0() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 224 | `com/zurrtum/create/content/equipment/toolbox/ToolboxInventory.insertExist(Lnet/minecraft/world/item/ItemStack;)I` | `create-fly-26.2-6.0.9-2-26.3-patched` | AllHandle.lambda$onToolboxEquip$0:1467 | 走到 lambda$onToolboxEquip$0() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 225 | `com/zurrtum/create/infrastructure/items/CombinedInvWrapper.insert(Lnet/minecraft/world/item/ItemStack;)I` ⚠同名异签名: `(Lnet/minecraft/world/item/ItemStack;ILnet/minecraft/cor` | `create-fly-26.2-6.0.9-2-26.3-patched` | MovementBehaviour.collectOrDropItem:73 | 走到 collectOrDropItem() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 226 | `com/zurrtum/create/api/contraption/storage/item/MountedItemStorage.insert(Lnet/minecraft/world/item/ItemStack;)I` | `create-fly-26.2-6.0.9-2-26.3-patched` | MountedDispenseBehavior.placeItemInInventory:76 | 走到 placeItemInInventory() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 227 | `com/zurrtum/create/content/kinetics/crafter/ConnectedInputHandler$ConnectedInventory.removeMaxSize(Lnet/minecraft/world/item/ItemStack;Ljava/util/Optional;)Lnet/minecraft/world/item/ItemStack;` | `create-fly-26.2-6.0.9-2-26.3-patched` | ConnectedInputHandler$ConnectedInventory.onExtract:267 | 走到 onExtract() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 228 | `com/zurrtum/create/infrastructure/items/CombinedInvWrapper.extract(Ljava/util/function/Predicate;I)Lnet/minecraft/world/item/ItemStack;` ⚠同名异签名: `(Ljava/util/function/Predicate;ILnet/minecraft/core/Dire` / `(Lnet/minecraft/world/item/ItemStack;ILnet/minecraft/cor` | `create-fly-26.2-6.0.9-2-26.3-patched` | DeployerMovementBehaviour.tryGrabbingItem:271 | 走到 tryGrabbingItem() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 229 | `com/zurrtum/create/content/logistics/depot/DepotBehaviour$DepotOutputHandler.insert(Ljava/util/List;)Ljava/util/List;` | `create-fly-26.2-6.0.9-2-26.3-patched` | DepotBehaviour.applyToAllItems:444 | 走到 applyToAllItems() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 230 | `com/zurrtum/create/content/processing/recipe/ProcessingInventory.removeMaxSize(Lnet/minecraft/world/item/ItemStack;Ljava/util/Optional;)Lnet/minecraft/world/item/ItemStack;` | `create-fly-26.2-6.0.9-2-26.3-patched` | ProcessingInventory.onExtract:80 | 走到 onExtract() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 231 | `com/zurrtum/create/content/processing/recipe/ProcessingInventory.setMaxSize(Lnet/minecraft/world/item/ItemStack;Ljava/util/Optional;)V` | `create-fly-26.2-6.0.9-2-26.3-patched` | ProcessingInventory.setItem:99 | 走到 setItem() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 232 | `com/zurrtum/create/content/kinetics/crafter/MechanicalCrafterBlockEntity$CrafterItemHandler.countSpace(Lnet/minecraft/world/item/ItemStack;I)I` | `create-fly-26.2-6.0.9-2-26.3-patched` | CrafterUnpackingHandler.unpack:70 | 走到 unpack() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 233 | `com/zurrtum/create/content/kinetics/crafter/MechanicalCrafterBlockEntity$CrafterItemHandler.insert(Lnet/minecraft/world/item/ItemStack;I)I` | `create-fly-26.2-6.0.9-2-26.3-patched` | CrafterUnpackingHandler.unpack:72 | 走到 unpack() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 234 | `com/zurrtum/create/client/compat/rrv/CreateCategory.getIcon()Lnet/minecraft/world/item/ItemStack;` | `create-fly-26.2-6.0.9-2-26.3-patched` | CreateCategory.renderIcon:39 | 走到 renderIcon() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 235 | `com/zurrtum/create/client/compat/rrv/CreateCategory.getSlotCount()I` | `create-fly-26.2-6.0.9-2-26.3-patched` | CreateCategory.placeSlots:63 | 走到 placeSlots() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 236 | `com/zurrtum/create/client/compat/rrv/CreateView.getIngredients()Ljava/util/List;` | `create-fly-26.2-6.0.9-2-26.3-patched` | CreateView.redirectsAsIngredient:91 | 走到 redirectsAsIngredient() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 237 | `com/zurrtum/create/client/compat/rrv/CreateView.getResults()Ljava/util/List;` | `create-fly-26.2-6.0.9-2-26.3-patched` | CreateView.redirectsAsResult:98 | 走到 redirectsAsResult() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |
| 238 | `cc/cassian/rrv/common/recipe/inventory/RecipeViewScreen.hoveredSlot : Lnet/minecraft/world/inventory/Slot;` | `create-fly-26.2-6.0.9-2-26.3-patched` | SequencedAssemblyView.renderRecipe:188 | 走到 renderRecipe() 这条路径时 → NoSuchFieldError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 239 | `com/mojang/blaze3d/platform/NativeImage.read(Lcom/mojang/blaze3d/platform/NativeImage$Format;Ljava/io/InputStream;)Lcom/mojang/blaze3d/platform/NativeImage;` ⚠同名异签名: `(Ljava/io/InputStream;)Lcom/mojang/blaze3d/platform/Nati` / `(Ljava/nio/ByteBuffer;)Lcom/mojang/blaze3d/platform/Nati` | `create-fly-26.2-6.0.9-2-26.3-patched` | NoiseTextures.reload:35 | 走到 reload() 这条路径时 → NoSuchMethodError 〔待验证：该类被某个 @Mixin 认领，成员可能被织入〕 | 1 |
| 240 | `com/zurrtum/create/infrastructure/worldgen/LayeredOreFeature.isAdjacentToAir(Ljava/util/function/Function;Lnet/minecraft/core/BlockPos;)Z` | `create-fly-26.2-6.0.9-2-26.3-patched` | LayeredOreFeature.canPlaceOre:227 | 走到 canPlaceOre() 这条路径时 → NoSuchMethodError 〔待验证：某子类型声明了同名成员，可能是 mixin 织入〕 | 1 |

### 4.2 可选依赖根本没装（722 条，**不是地雷**）

这些引用的 owner **连所在包名的前三段都不在索引里** —— 说明那个库/模组根本没装，而不是 26.3 把它删了。mod 里这类代码几乎都包在 `if (FabricLoader.isModLoaded("xxx"))` 里，那个分支进不去。

**但如果清单里出现了你本以为装着的库 → 那才是真问题**（版本不对 / 没同步进 `mods-stable`）。

| 未安装的包（前三段） | 引用条目数 | 举例（jar） |
|---|---|---|
| `com/seibel/distanthorizons` | 98 | `iris-fabric-1.11.7+mc26.3.jar` |
| `me/shedaniel/rei` | 92 | `FarmersDelight-26.3-3.6.28+refabricated.jar` |
| `cc/cassian/rrv` | 84 | `FarmersDelight-26.3-3.6.28+refabricated.jar` |
| `dev/isxander/yacl3` | 70 | `FarmersDelight-26.3-3.6.28+refabricated.jar` |
| `xaero/pac/client` | 56 | `xaerominimap-fabric-26.3-26.6.0.jar` |
| `xaero/pac/common` | 49 | `xaerominimap-fabric-26.3-26.6.0.jar` |
| `journeymap/api/v2` | 31 | `waystones-fabric-26.3-26.3.0.1.jar` |
| `net/luckperms/api` | 28 | `xaerominimap-fabric-26.3-26.6.0.jar` |
| `de/bluecolored/bluemap` | 26 | `waystones-fabric-26.3-26.3.0.1.jar` |
| `org/quiltmc/loader` | 25 | `modmenu-21.0.0.jar` |
| `earth/terrarium/prometheus` | 23 | `xaerominimap-fabric-26.3-26.6.0.jar` |
| `dev/ftb/mods` | 23 | `xaerominimap-fabric-26.3-26.6.0.jar` |
| `mcp/mobius/waila` | 19 | `balm-fabric-26.3-26.3.0.3.jar` |
| `com/mrcrayfish/configured` | 16 | `appleskin-fabric-mc26.3-3.0.10.jar` |
| `eu/pb4/trinkets` | 11 | `create-fly-26.2-6.0.9-2-26.3-patched.jar` |
| `org/apache/tools` | 10 | `iris-fabric-1.11.7+mc26.3.jar` |
| `org/dynmap/markers` | 10 | `waystones-fabric-26.3-26.3.0.1.jar` |
| `earth/terrarium/argonauts` | 8 | `xaerominimap-fabric-26.3-26.6.0.jar` |
| `com/teamresourceful/resourcefullib` | 7 | `xaerominimap-fabric-26.3-26.6.0.jar` |
| `dan200/computercraft/shared` | 6 | `create-fly-26.2-6.0.9-2-26.3-patched.jar` |
| `de/siphalor/amecs` | 5 | `xaerominimap-fabric-26.3-26.6.0.jar` |
| `snownee/jade/test` | 4 | `Jade-mc26.3-Fabric-26.3.5.jar` |
| `org/vivecraft/api` | 3 | `balm-fabric-26.3-26.3.0.3.jar` |
| `carpet/api/settings` | 3 | `InventoryProfilesNext-fabric-26.3-2.3.8.jar` |
| `org/embeddedt/modernfix` | 3 | `moreculling-fabric-26.3-1.9.0.jar` |
| `org/dynmap/DynmapCommonAPIListener` | 2 | `waystones-fabric-26.3-26.3.0.1.jar` |
| `com/github/zafarkhaja` | 2 | `iris-fabric-1.11.7+mc26.3.jar` |
| `org/dynmap/DynmapCommonAPI` | 2 | `waystones-fabric-26.3-26.3.0.1.jar` |
| `dev/isxander/controlify` | 2 | `InventoryProfilesNext-fabric-26.3-2.3.8.jar` |
| `carpet/settings/SettingsManager` | 2 | `InventoryProfilesNext-fabric-26.3-2.3.8.jar` |
| `carpet/CarpetServer` | 2 | `InventoryProfilesNext-fabric-26.3-2.3.8.jar` |

### 4.3 只随包了「桩」的命名空间（0 条，**不是地雷**）

这些 owner 类不存在，但该命名空间里**只剩零星几个类**（≤8）—— 典型是「为了能编译，随包了一个空壳 API」。只有真的装了对应 mod 才会走到，而那时提供的是真类。

| 桩命名空间 | 条目数 | 举例（jar） |
|---|---|---|

## 5. 按缺失成员聚合：最普遍的洞

| 缺失成员 | 级别 | 判定 | 站点数 | jar 数 |
|---|---|---|---|---|
| `dan200/computercraft/api/lua/LuaException.<init>(Ljava/lang/String;)V` | HIGH | 实证·缺类 | 51 | 1 |
| 类 `dan200/computercraft/api/lua/LuaException` | HIGH | 实证·缺类 | 18 | 1 |
| `dan200/computercraft/api/detail/VanillaDetailRegistries.ITEM_STACK : Ldan200/computercraft/api/detail/DetailRegistry;` | HIGH | 实证·缺类 | 15 | 1 |
| `dan200/computercraft/api/detail/DetailRegistry.getDetails(Lnet/minecraft/core/HolderLookup$Provider;Ljava/lang/Object;)Ljava/util/Map;` | HIGH | 实证·缺类 | 10 | 1 |
| `net/mezzdev/config/gui/api/IConfigScreenCategoryBuilder.addValue(Lnet/mezzdev/config/api/value/IConfigValue;)Lnet/mezzdev/config/gui/api/IConfigScreenCategoryBuilder;` | MED | 实证·缺类 | 9 | 1 |
| `net/mezzdev/config/gui/api/IConfigScreenCategoryBuilder.addValues(Ljava/util/Collection;)Lnet/mezzdev/config/gui/api/IConfigScreenCategoryBuilder;` | MED | 实证·缺类 | 9 | 1 |
| 类 `dan200/computercraft/api/detail/DetailRegistry` | HIGH | 实证·缺类 | 8 | 1 |
| 类 `dan200/computercraft/api/detail/VanillaDetailRegistries` | HIGH | 实证·缺类 | 8 | 1 |
| `net/mezzdev/config/gui/api/IConfigScreenBuilder.addCategory(Ljava/lang/String;)Lnet/mezzdev/config/gui/api/IConfigScreenCategoryBuilder;` | MED | 实证·缺类 | 8 | 1 |
| `joptsimple/OptionParser.acceptsAll(Ljava/util/Collection;Ljava/lang/String;)Ljoptsimple/OptionSpecBuilder;` ⚠同名异签名: `(Ljava/util/List;)Ljoptsimple/OptionSpecBuilder;` / `(Ljava/util/List;Ljava/lang/String;)Ljoptsimple/OptionSp` | LOW | 实证 | 8 | 1 |
| 类 `dan200/computercraft/api/lua/IArguments` | HIGH | 实证·缺类 | 7 | 1 |
| `dan200/computercraft/api/lua/LuaValues.getType(Ljava/lang/Object;)Ljava/lang/String;` | LOW | 实证·缺类 | 7 | 1 |
| `net/minecraft/world/level/block/RedStoneWireBlock.POWER : Lnet/minecraft/world/level/block/state/properties/IntegerProperty;` | HIGH | 实证·缺类 | 5 | 1 |
| `dan200/computercraft/api/lua/IArguments.get(I)Ljava/lang/Object;` | HIGH | 实证·缺类 | 5 | 1 |
| `com/mojang/math/Axis.of(Lorg/joml/Vector3f;)Lcom/mojang/math/Axis;` ⚠同名异签名: `(Lorg/joml/Vector3fc;)Lcom/mojang/math/Axis;` | MED | 实证 | 5 | 1 |
| `org/anarres/cpp/CppTask.fileCopyMap : Ljava/util/Hashtable;` | LOW | 实证 | 5 | 1 |
| `dan200/computercraft/api/lua/LuaValues.badField(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Ldan200/computercraft/api/lua/LuaException;` | LOW | 实证·缺类 | 5 | 1 |
| `xaero/lib/client/compat/prometheus/FixedNumberBoxListEntry.getText()Ljava/lang/String;` | LOW | 实证 | 4 | 2 |
| `dan200/computercraft/api/detail/DetailRegistry.getBasicDetails(Lnet/minecraft/core/HolderLookup$Provider;Ljava/lang/Object;)Ljava/util/Map;` | HIGH | 实证·缺类 | 4 | 1 |
| 类 `net/minecraft/world/item/alchemy/PotionBrewing` | MED | 实证·缺类 | 4 | 1 |
| 类 `net/mezzdev/config/gui/api/IConfigScreenValue` | MED | 实证·缺类 | 4 | 1 |
| `dan200/computercraft/api/lua/IArguments.getTable(I)Ljava/util/Map;` | LOW | 实证·缺类 | 4 | 1 |
| `dan200/computercraft/api/lua/MethodResult.of([Ljava/lang/Object;)Ldan200/computercraft/api/lua/MethodResult;` | LOW | 实证·缺类 | 4 | 1 |
| `com/mojang/blaze3d/platform/ClipboardManager.setClipboard(Lcom/mojang/blaze3d/platform/Window;Ljava/lang/String;)V` ⚠同名异签名: `(Ljava/lang/String;)V` | MED | 实证 | 3 | 1 |
| 类 `net/mezzdev/config/gui/api/ConfigValueEditorType` | MED | 实证·缺类 | 3 | 1 |
| `net/mezzdev/config/gui/api/IConfigScreenCategoryBuilder.addScreenValue(Lnet/mezzdev/config/gui/api/IConfigScreenValue;)Lnet/mezzdev/config/gui/api/IConfigScreenCategoryBuilder;` | MED | 实证·缺类 | 3 | 1 |
| `net/mezzdev/config/gui/api/IConfigScreenCategoryBuilder.addStringSortingConfig(Ljava/lang/String;Ljava/lang/String;Lnet/mezzdev/config/api/sorting/ISortingConfig;Ljava/util/Collection;)Lnet/mezzdev/config/gui/api/ISortingConfigGuiBuilder;` | MED | 实证·缺类 | 3 | 1 |
| `net/mezzdev/config/gui/api/ISortingConfigGuiBuilder.setValueName(Ljava/util/function/Function;)Lnet/mezzdev/config/gui/api/ISortingConfigGuiBuilder;` | MED | 实证·缺类 | 3 | 1 |
| `net/mezzdev/config/gui/api/ISortingConfigGuiBuilder.setValueDescription(Ljava/util/function/Function;)Lnet/mezzdev/config/gui/api/ISortingConfigGuiBuilder;` | MED | 实证·缺类 | 3 | 1 |
| `net/mezzdev/config/gui/api/ISortingConfigGuiBuilder.setValueIcon(Ljava/util/function/Function;)Lnet/mezzdev/config/gui/api/ISortingConfigGuiBuilder;` | MED | 实证·缺类 | 3 | 1 |
| `org/spongepowered/asm/mixin/injection/struct/InjectionInfo.getContext()Lorg/spongepowered/asm/mixin/refmap/IMixinContext;` | LOW | 实证 | 3 | 1 |
| 类 `net/minecraft/world/level/levelgen/feature/configurations/OreConfiguration$TargetBlockState` | LOW | 实证·缺类 | 3 | 1 |
| `net/minecraft/world/level/levelgen/feature/configurations/OreConfiguration.target(Lnet/minecraft/world/level/levelgen/structure/templatesystem/RuleTest;Lnet/minecraft/world/level/block/state/BlockState;)Lnet/minecraft/world/level/levelgen/feature/configurations/OreConfiguration$TargetBlockState;` | LOW | 实证·缺类 | 3 | 1 |
| 类 `dan200/computercraft/api/lua/LuaValues` | LOW | 实证·缺类 | 3 | 1 |
| `dan200/computercraft/api/lua/IArguments.getInt(I)I` | LOW | 实证·缺类 | 3 | 1 |
| 类 `net/mezzdev/config/gui/api/IConfigValueIcon` | LOW | 实证·缺类 | 3 | 1 |
| `net/minecraft/client/renderer/state/level/FirstPersonHandsAndItemsRenderState.clearExtraData()V` | MED | 实证 | 2 | 2 |
| `xaero/lib/client/compat/prometheus/FixedNumberBoxListEntry.text : Ljava/lang/String;` | LOW | 实证 | 2 | 2 |
| `xaero/lib/client/compat/prometheus/FixedNumberBoxListEntry.getIntValue()Ljava/util/OptionalInt;` | LOW | 实证 | 2 | 2 |
| `xaero/lib/client/compat/prometheus/FixedNumberBoxListEntry.getDoubleValue()Ljava/util/OptionalDouble;` | LOW | 实证 | 2 | 2 |

> ⚠ 这张表按**站点数**排，所以**可选集成**（`dan200/computercraft/*` 33 条 / 173 站点、`net/mezzdev/config/*` 43 条 / 91 站点）会挤在前排 —— 它们站点多、但**触发概率低**（对应 mod 没装，或那段 GUI 插件在 Fabric 上不注册）。**要按触发概率看，请用 §1–§3。**

## 6. 按 jar 统计（哪个 jar 最脏）

| jar | 地雷组数 | 其中实证高危 |
|---|---|---|
| `create-fly-26.2-6.0.9-2-26.3-patched.jar` | 75 | 22 |
| `jei-26.3-fabric-31.15.0.79.jar` | 43 | 3 |
| `FarmersDelight-26.3-3.6.28+refabricated.jar` | 9 | 3 |
| `iris-fabric-1.11.7+mc26.3.jar` | 8 | 0 |
| `MoogsStructureLib-fabric-26.3-3.4.2.jar` | 6 | 0 |
| `DungeonsArise-2.1.68-26.3.jar` | 4 | 0 |
| `xaerominimap-fabric-26.3-26.6.0.jar` | 4 | 0 |
| `xaeroworldmap-fabric-26.3-1.47.0.jar` | 4 | 0 |
| `createaddition-1.3.4-26.3.jar` | 2 | 2 |
| `rabbit_pathfinding_fix-1.0.5-26.3.jar` | 2 | 2 |
| `architectury-fabric-22.0.5.jar` | 2 | 0 |
| `waystones-fabric-26.3-26.3.0.1.jar` | 2 | 0 |
| `fabric-api-0.163.0+26.3.jar` | 1 | 0 |
| `sodium-fabric-0.9.3-beta.1+mc26.3.jar` | 1 | 0 |

---

## 7. 扫描方法（可复现）

### 7.1 步骤

1. **建索引**：把下面每个 jar 里**每个 class** 解析出 `(owner, name, descriptor)`：
   - `versions/26.3/26.3.jar`（MC 本体，77241 个 class 进了索引）
   - `fabric-api-0.163.0+26.3.jar` **及其 `META-INF/jars/*.jar` 内嵌模块（递归 4 层）**
   - `mods-stable` 里**全部 71 个 jar**（含各自内嵌 jar）⇒ 跨 jar 依赖
   - `.minecraft/libraries/**/*.jar`（fabric-loader / mixin / joml / fastutil / gson / lwjgl / guava / asm …；**排除** `net/minecraft/`、`net/neoforged/neoforge/` 下的 jar ——那里的 1.21.1 全命名 jar 会把 26.3 已删的类**掩盖**成存在）
   - JDK（`java.*` / `javax.*` / `jdk.*` / `sun.*`）：**本身不审计**，但为了能正确解析「继承来的成员」，用 `javap -p -s` 把**索引里出现过的 JDK 父类型（递归）** 补进索引（本次补了 420 个）。不补的后果很具体：枚举的 `ordinal()`/`name()` 声明在 `java/lang/Enum`，首轮扫描把**每一个** `.ordinal()` 都报成了 NoSuchMethodError。
   - 另外把 `@Mixin(T.class)` 的 **mixin 类手动当成 T 的子类型**：`@Mixin(T.class) interface X`里 X **不继承** T，类图上没有 X→T 这条边，但 X 声明的方法会被织进 T。不补这条边，Create 那种「mixin 接口给 `Container` 提供 default 方法」会被整批误报。
2. **读目标字节码**：每个目标 class 的常量池 + 字段/方法表 + 每条 `Code` 属性：
   - `getstatic/putstatic/getfield/putfield` → Fieldref
   - `invokevirtual/invokespecial/invokestatic/invokeinterface` → Methodref / InterfaceMethodref
   - `new/anewarray/checkcast/instanceof/multianewarray/ldc<class>` → Class
   - 另外收 super / interfaces / 字段与方法描述符 / 异常表 `catch_type` 里的类型
   - **不算**常量池里没有被任何指令引用的残留条目（那些运行期不会被解析）
3. **比对**：沿「自身 → 父类 → 全部父接口」BFS 解析成员；解析不到 ⇒ 再过两道放宽（织入/混入，§7.2），仍解析不到才记一条。
4. **去重归组**：按 `(目标成员, 描述符)` 聚合。
5. **分档**：先判「能不能当实证」，再按**外层方法名**与**外层类名**判危险级别（§7.3）。判定为「不能当实证」的三种情况直接单列，**不计入地雷数**：
   - `待验证`：owner 被 `@Mixin` 认领 / 某子类型声明了同名成员 / 继承链碰到没建模的 JDK 类型；
   - `非地雷·桩`：owner 类不存在，而它所在包只剩 ≤8 个类（随包的空壳 API）；
   - `非地雷·未安装`：owner 包名的前三段压根不在索引里（这个库没装）。

### 7.2 ⚠ 关键：为什么「`26.3.jar` 里没有」≠「运行时没有」

fabric-api 会**往 MC 的接口/类上织方法**。实测反例：

| 项 | 值 |
|---|---|
| 引用 | `ValueInput.contains(String)` |
| `26.3.jar` 的 `javap` | **看不到这个成员** |
| 实际提供者 | `fabric-api` 内嵌 `fabric-serialization-api-v1` 的 `FabricValueInput`：`default boolean contains(String)` |
| 织物 | `ValueInputMixin` 把该 default 方法织进 `ValueInput` |
| 运行期 | **能调通 ⇒ 不是地雷** |

本工具为此有三层防护：

1. **索引含 fabric-api 的内嵌模块**（递归解开 `META-INF/jars/*.jar`）。
2. **织入放宽**：解析失败的**接口方法** `I.m(desc)`，若索引里 **I 的某个实现类**声明了同名同描述符的方法 ⇒ 判「很可能由 mixin 织入」⇒ **不进地雷表**（本次共放过 30 个）。
3. **mixin target 标记**：解析失败的成员若 owner 在某个 `@Mixin(...)` 的 target 里 ⇒ **降级为「待验证」**而不是「实证」，并单列在 §4。

### 7.3 危险级别 = 玩家触发概率（**不是后果严重度**）

| 级别 | 触发条件（任一） | 为什么 |
|---|---|---|
| **高危** | 外层方法 `<clinit>` | 类一加载就执行，注册期几乎必然 |
| | 外层方法 ∈ {`read`,`write`,`tick`,`neighborChanged`,`use`,`onPlace`,`updateShape`,`getStateForPlacement`,`randomTick`,`saveAdditional`,`loadAdditional`,`register*` …} | 放/拆/存/读/每 tick 都走 |
| | 外层类是 `*Block`/`*BlockEntity`/`*Entity`/`*Item` 且方法为 `<init>` | 注册期就构造 |
| **中危** | 外层类名含 `Screen`/`Menu`/`Render*`/`Widget`/`Gui`/`Model`/`Recipe`/`Packet`/`Client` | 开界面 / 匹配方 / 收包才走 |
| | 外层方法 ∈ {`render`,`draw`,`getTooltip`,`matches`,`assemble`,`encode`,`decode`,`handle` …} | 同上 |
| **低危** | 其余 | 只在特定交互或调试路径 |

> 任何一条一旦触发都是崩溃；级别只回答「多容易被碰到」。

### 7.4 误报/漏报来源（**读表前必看**）

| # | 来源 | 方向 | 本工具的处理 |
|---|---|---|---|
| 1 | **mixin 织入**（fabric-api 或 mod 自己往 MC 类上补 default 方法 / 接口） | 误报 | 索引含 fabric-api 内嵌 + 实现类放宽 + mixin target 降级（§7.2）。**仍可能误报**：注入的成员不存在于任何实现类、且 target 是靠 `targets="..."` 字符串写的 |
| 2 | **Access Widener / AT** 只改可见性，不产生新成员 | 不影响 | 本工具只查存在性，不查可见性 |
| 3 | **第三方库没随包**（`net/neoforged/**` 等） | 真缺但未必是 26.3 删的 | 若库既不在 `libraries` 也不在 71 jar 里就报「缺类」。这类要人工判断是「26.3 删了」还是「这包本来就没装」 |
| 4 | **多版本库共存**（`libraries` 里 guava 20/32/33、fastutil 8.5.12/8.5.18、lwjgl 3.3.3/3.4.1/3.4.3） | **漏报** | 索引取并集 ⇒ 只在旧版存在的方法被当成存在。本工具**偏保守**：宁可漏报不误报 |
| 5 | **StackMapTable 里的类型**未纳索引 | 漏报 | 极少见；只出现在 StackMapTable 的缺类会漏 |
| 6 | **反射 / 字符串拼出来的成员名**（`Class.forName("...")`、mixin `@Shadow`） | 漏报 | 字节码里没有 Methodref ⇒ 扫不到。mixin 那一层另有 `tools/audit_mixins26.py` |
| 7 | **`invokedynamic` 的 bootstrap 目标** | 漏报 | 只解析 `ldc` 的 Class 常量，不展开 MethodHandle |
| 8 | **死代码 / 不可达分支** | 误报 | 不做可达性分析 ⇒ 引用了就算。所以「低危」里可能混着永远不执行的 |
| 9 | **记录类 / 密封类 / 编译器合成桥方法** | 漏报 | 合成成员本就在 class 文件里声明，不影响 |

### 7.5 已知的、已修过的（**不在本清单里**）

| 位置 | 问题 | 状态 |
|---|---|---|
| `NameplateBlock` / `HandleBlock` / `DirectionalLinkedReceiverBlock` / `ModulatingLinkedReceiverBlock` | `Orientation.equals(...)` 传了 `null` ⇒ NPE。**成员本身存在**，是「参数语义变了」不是「成员没了」 | ✅ 已修，`aeronautics` SHA `2DF06E76…BD2B`，见 `docs/fix-npe-last2.md` |
| `ItemHelper.fillItemStackHandler` | 调 `ItemContainerContents.allItemsCopyStream()`（26.3 已删）| ✅ 已改用 `itemCopies()`，见 `docs/fix-npe-and-itemhelper.md` |

> ⚠ 「成员还在、只是**签名/语义变了**」这一类（→ NPE / CCE）**不在本工具的能力边界内**。那类只能靠 A/B 实跑（`tools/launch26/launch.py`）。

### 7.6 自检：能不能抓到**已知的真地雷**

拿修复**前**的 create jar（`create-fly-….jar.bak-itemhelper`）原封不动复制成 `work/run26/_lmcheck/create-OLD.jar` 再跑同一扫描器：

```
python tools/scan_landmines.py --mods work/run26/_lmcheck \
    --universe-extra work/run26/mods-stable \
    --out work/run26/_lmcheck/gt.md
```

| | 结果 |
|---|---|
| 修复前的 jar | **1 条 1 站点**：`ItemContainerContents.allItemsCopyStream()Ljava/util/stream/Stream;` @ `ItemHelper.fillItemStackHandler:233` ⇒ 判 `实证` |
| 当前交付 jar | **0 条**（已改用 `itemCopies()` ⇒ 扫描器看不到它了） |

⇒ 这就是「已知真地雷能被同名工具复现」的对照。同一轮里 `Orientation.equals(null)` 那种「成员还在、语义变了」的 NPE **不会**出现在本清单里 —— 那不在本工具的能力边界内。

### 7.7 本工具明确**不**做的事

- 不检查**可见性**（`private` 方法被外部调用是 `IllegalAccessError`，另一类问题）。
- 不检查**方法签名语义兼容**（参数变少/变多但描述符恰好匹配的情况不存在；描述符变了会被本工具抓到，其中「旧参数被当成新参数用」导致的 NPE 抓不到）。
- 不检查 **mixin 的 `@Shadow` 目标**（那是 `tools/audit_mixins26.py` 的活）。
- 不检查 **资源/数据包/模型 json**。
