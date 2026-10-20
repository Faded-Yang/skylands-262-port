# create-fly getOrDefault + checkcast 风险清单（静态扫描，2026-10-20）

> 背景：FluidStack.getMaxAmount() 实测 getOrDefault 返回 Optional 导致 (Integer) cast CCE（g130）。
> 本清单由 ASM 扫描 live create-fly（17FD0C33…）全部 class 生成：invoke getOrDefault(DataComponentType,...) 后 6 条指令内出现 checkcast。

## 汇总

- 站点总数：99
- 按 receiver owner：
  - net/minecraft/world/item/ItemStack：72
  - net/minecraft/core/component/DataComponentMap：22
  - com/zurrtum/create/infrastructure/fluids/FluidStack：3
  - net/minecraft/core/component/DataComponentGetter：2
- 按 cast 目标（Top 15）：
  - net/minecraft/network/chat/Component：16
  - java/lang/Boolean：15
  - java/lang/Integer：12
  - net/minecraft/world/item/alchemy/PotionContents：8
  - com/zurrtum/create/infrastructure/component/ClipboardContent：6
  - com/zurrtum/create/infrastructure/component/BottleType：6
  - net/minecraft/world/item/component/ItemContainerContents：5
  - com/zurrtum/create/infrastructure/component/TerrainTools：4
  - com/zurrtum/create/infrastructure/component/TerrainBrushes：3
  - com/zurrtum/create/infrastructure/component/PlacementOptions：3
  - java/lang/String：3
  - java/util/List：3
  - com/zurrtum/create/infrastructure/component/AttributeFilterWhitelistMode：2
  - com/zurrtum/create/infrastructure/component/PlacementPatterns：2
  - net/minecraft/world/item/component/CustomData：2

## 已修

- FluidStack.getMaxAmount / getName（3 站点）：create-fly 31ff67d0… 已用 FluidFix.unwrap/max 处理（g132 PASS）。

## 判定与建议

- ItemStack.getOrDefault / DataComponentMap.getOrDefault / DataComponentGetter.getOrDefault 在 26.3 反编译源码中返回 T（非 Optional），理论安全；
- 但 FluidStack 实测返回 Optional，说明组件值本身被存成 Optional 的运行期路径存在；若其它机器/工具出现同类 ClassCastException，可套用 FluidFix.unwrap 模式（ASM 在 checkcast 前插 invokestatic）；
- 本清单不逐点改：避免无证据的 99 处改动放大回归面。

## 全量站点

```
com/zurrtum/create/content/equipment/armor/BacktankBlock.class :: lambda$setPlacedBy$0 -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Integer
com/zurrtum/create/content/equipment/armor/BacktankBlockEntity.class :: getDefaultName -> owner=net/minecraft/core/component/DataComponentMap checkcast net/minecraft/network/chat/Component
com/zurrtum/create/content/equipment/armor/BacktankBlockEntity.class :: getDefaultName -> owner=net/minecraft/core/component/DataComponentMap checkcast net/minecraft/network/chat/Component
com/zurrtum/create/content/equipment/armor/BacktankBlockEntity.class :: applyImplicitComponents -> owner=net/minecraft/core/component/DataComponentGetter checkcast java/lang/Integer
com/zurrtum/create/content/equipment/armor/BacktankItem.class :: getRemainingAir -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Integer
com/zurrtum/create/content/equipment/armor/BacktankUtil.class :: getAir -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Integer
com/zurrtum/create/content/equipment/blueprint/BlueprintEntity$BlueprintSection.class :: getDisplayName -> owner=net/minecraft/core/component/DataComponentMap checkcast net/minecraft/network/chat/Component
com/zurrtum/create/content/equipment/blueprint/BlueprintMenu.class :: setItem -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Boolean
com/zurrtum/create/content/equipment/clipboard/ClipboardBlockEntity.class :: read -> owner=net/minecraft/core/component/DataComponentMap checkcast com/zurrtum/create/infrastructure/component/ClipboardContent
com/zurrtum/create/content/equipment/clipboard/ClipboardBlockItem.class :: use -> owner=net/minecraft/world/item/ItemStack checkcast com/zurrtum/create/infrastructure/component/ClipboardContent
com/zurrtum/create/content/equipment/clipboard/ClipboardValueSettingsHandler.class :: interact -> owner=net/minecraft/world/item/ItemStack checkcast com/zurrtum/create/infrastructure/component/ClipboardContent
com/zurrtum/create/content/equipment/potatoCannon/AllPotatoProjectileEntityHitActions$SuspiciousStew.class :: execute -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/world/item/component/SuspiciousStewEffects
com/zurrtum/create/content/equipment/symmetryWand/SymmetryWandItem.class :: isEnabled -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Boolean
com/zurrtum/create/content/equipment/symmetryWand/SymmetryWandItem.class :: isEnabled -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Boolean
com/zurrtum/create/content/equipment/zapper/terrainzapper/WorldshaperItem.class :: canActivateWithoutSelectedBlock -> owner=net/minecraft/world/item/ItemStack checkcast com/zurrtum/create/infrastructure/component/TerrainTools
com/zurrtum/create/content/equipment/zapper/terrainzapper/WorldshaperItem.class :: activate -> owner=net/minecraft/world/item/ItemStack checkcast com/zurrtum/create/infrastructure/component/TerrainBrushes
com/zurrtum/create/content/equipment/zapper/terrainzapper/WorldshaperItem.class :: activate -> owner=net/minecraft/world/item/ItemStack checkcast com/zurrtum/create/infrastructure/component/PlacementOptions
com/zurrtum/create/content/equipment/zapper/terrainzapper/WorldshaperItem.class :: activate -> owner=net/minecraft/world/item/ItemStack checkcast com/zurrtum/create/infrastructure/component/TerrainTools
com/zurrtum/create/content/fluids/potion/PotionFluidHandler.class :: getFluidFromPotionItem -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/world/item/alchemy/PotionContents
com/zurrtum/create/content/fluids/potion/PotionFluidHandler.class :: fillBottle -> owner=com/zurrtum/create/infrastructure/fluids/FluidStack checkcast com/zurrtum/create/infrastructure/component/BottleType
com/zurrtum/create/content/kinetics/belt/transport/ItemHandlerBeltSegment.class :: getMaxStackSize -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Integer
com/zurrtum/create/content/kinetics/deployer/DeployerHandler.class :: activate -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/world/item/component/ItemAttributeModifiers
com/zurrtum/create/content/kinetics/deployer/DeployerItemHandler.class :: getMaxStackSize -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Integer
com/zurrtum/create/content/kinetics/deployer/DeployerMovementBehaviour.class :: activateAsSchematicPrinter -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Boolean
com/zurrtum/create/content/logistics/box/PackageItem.class :: getAddress -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/String
com/zurrtum/create/content/logistics/box/PackageItem.class :: getContents -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/world/item/component/ItemContainerContents
com/zurrtum/create/content/logistics/chute/ChuteItemHandler.class :: getMaxStackSize -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Integer
com/zurrtum/create/content/logistics/crate/CreativeCrateMountedStorage.class :: <init> -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Integer
com/zurrtum/create/content/logistics/filter/AttributeFilterItem.class :: makeSummary -> owner=net/minecraft/world/item/ItemStack checkcast java/util/List
com/zurrtum/create/content/logistics/filter/AttributeFilterItem.class :: getFilterItems -> owner=net/minecraft/world/item/ItemStack checkcast java/util/List
com/zurrtum/create/content/logistics/filter/AttributeFilterMenu.class :: initAndReadInventory -> owner=net/minecraft/world/item/ItemStack checkcast com/zurrtum/create/infrastructure/component/AttributeFilterWhitelistMode
com/zurrtum/create/content/logistics/filter/AttributeFilterMenu.class :: initAndReadInventory -> owner=net/minecraft/world/item/ItemStack checkcast java/util/List
com/zurrtum/create/content/logistics/filter/FilterItem.class :: getDisplayName -> owner=net/minecraft/core/component/DataComponentMap checkcast net/minecraft/network/chat/Component
com/zurrtum/create/content/logistics/filter/FilterItemStack$AttributeFilterItemStack.class :: <init> -> owner=net/minecraft/world/item/ItemStack checkcast com/zurrtum/create/infrastructure/component/AttributeFilterWhitelistMode
com/zurrtum/create/content/logistics/filter/FilterItemStack$ListFilterItemStack.class :: <init> -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Boolean
com/zurrtum/create/content/logistics/filter/FilterItemStack$ListFilterItemStack.class :: <init> -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Boolean
com/zurrtum/create/content/logistics/filter/FilterMenu.class :: initAndReadInventory -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Boolean
com/zurrtum/create/content/logistics/filter/FilterMenu.class :: initAndReadInventory -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Boolean
com/zurrtum/create/content/logistics/filter/ListFilterItem.class :: makeSummary -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Boolean
com/zurrtum/create/content/logistics/filter/ListFilterItem.class :: getFilterItemHandler -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/world/item/component/ItemContainerContents
com/zurrtum/create/content/logistics/filter/ListFilterItem.class :: getFilterItems -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Boolean
com/zurrtum/create/content/logistics/filter/PackageFilterMenu.class :: initAndReadInventory -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/String
com/zurrtum/create/content/logistics/item/filter/attribute/attributes/ItemNameAttribute.class :: extractCustomName -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/network/chat/Component
com/zurrtum/create/content/logistics/item/filter/attribute/attributes/ShulkerFillLevelAttribute$ShulkerLevels.class :: canApply -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/world/item/component/ItemContainerContents
com/zurrtum/create/content/logistics/packagePort/PackagePortBlockEntity.class :: addAddressToClipboard -> owner=net/minecraft/world/item/ItemStack checkcast com/zurrtum/create/infrastructure/component/ClipboardContent
com/zurrtum/create/content/logistics/tableCloth/ShoppingListItem.class :: getAddress -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/String
com/zurrtum/create/content/processing/basin/BasinBlock.class :: getAnalogOutputSignal -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Integer
com/zurrtum/create/content/redstone/displayLink/target/LecternDisplayTarget.class :: acceptText -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/world/item/component/WrittenBookContent
com/zurrtum/create/content/redstone/link/controller/LecternControllerBlockEntity.class :: setController -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/world/item/component/ItemContainerContents
com/zurrtum/create/content/redstone/link/controller/LinkedControllerItem.class :: getFrequencyItems -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/world/item/component/ItemContainerContents
com/zurrtum/create/content/redstone/link/controller/LinkedControllerItem.class :: getDisplayName -> owner=net/minecraft/core/component/DataComponentMap checkcast net/minecraft/network/chat/Component
com/zurrtum/create/content/redstone/nixieTube/NixieTubeBlock.class :: useItemOn -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/network/chat/Component
com/zurrtum/create/content/redstone/nixieTube/NixieTubeBlock.class :: useItemOn -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/network/chat/Component
com/zurrtum/create/content/schematics/SchematicInstances.class :: getHash -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Integer
com/zurrtum/create/content/schematics/SchematicItem.class :: getSettings -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/world/level/block/Rotation
com/zurrtum/create/content/schematics/SchematicItem.class :: getSettings -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/world/level/block/Mirror
com/zurrtum/create/content/schematics/cannon/MaterialChecklist.class :: lambda$createWrittenClipboard$0 -> owner=net/minecraft/core/component/DataComponentMap checkcast net/minecraft/network/chat/Component
com/zurrtum/create/content/schematics/cannon/MaterialChecklist.class :: lambda$createWrittenClipboard$0 -> owner=net/minecraft/core/component/DataComponentMap checkcast net/minecraft/network/chat/Component
com/zurrtum/create/content/schematics/cannon/MaterialChecklist.class :: lambda$createWrittenBook$0 -> owner=net/minecraft/core/component/DataComponentMap checkcast net/minecraft/network/chat/Component
com/zurrtum/create/content/schematics/cannon/MaterialChecklist.class :: lambda$createWrittenBook$0 -> owner=net/minecraft/core/component/DataComponentMap checkcast net/minecraft/network/chat/Component
com/zurrtum/create/content/schematics/cannon/SchematicannonBlockEntity.class :: initializePrinter -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Boolean
com/zurrtum/create/content/schematics/cannon/SchematicannonBlockEntity.class :: applyImplicitComponents -> owner=net/minecraft/core/component/DataComponentGetter checkcast com/zurrtum/create/infrastructure/component/SchematicannonOptions
com/zurrtum/create/content/trains/schedule/ScheduleItem.class :: getDisplayName -> owner=net/minecraft/core/component/DataComponentMap checkcast net/minecraft/network/chat/Component
com/zurrtum/create/content/trains/track/TrackBlockItem.class :: useOn -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Boolean
com/zurrtum/create/content/trains/track/TrackTargetingBlockItem.class :: useOn -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Boolean
com/zurrtum/create/foundation/recipe/IngredientTextContent.class :: findName -> owner=net/minecraft/core/component/DataComponentMap checkcast net/minecraft/network/chat/Component
com/zurrtum/create/impl/effect/PotionEffectHandler.class :: getContents -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/world/item/alchemy/PotionContents
com/zurrtum/create/infrastructure/component/ClipboardEntry.class :: getLastViewedEntries -> owner=net/minecraft/world/item/ItemStack checkcast com/zurrtum/create/infrastructure/component/ClipboardContent
com/zurrtum/create/infrastructure/component/PlacementPatterns.class :: applyPattern -> owner=net/minecraft/world/item/ItemStack checkcast com/zurrtum/create/infrastructure/component/PlacementPatterns
com/zurrtum/create/infrastructure/fluids/FluidStack.class :: getName -> owner=com/zurrtum/create/infrastructure/fluids/FluidStack checkcast net/minecraft/world/item/alchemy/PotionContents
com/zurrtum/create/infrastructure/fluids/FluidStack.class :: getName -> owner=com/zurrtum/create/infrastructure/fluids/FluidStack checkcast com/zurrtum/create/infrastructure/component/BottleType
com/zurrtum/create/infrastructure/transfer/InventoryWrapper.class :: extractAnyMax -> owner=net/minecraft/core/component/DataComponentMap checkcast java/lang/Integer
com/zurrtum/create/infrastructure/transfer/InventoryWrapper.class :: extractMax -> owner=net/minecraft/core/component/DataComponentMap checkcast java/lang/Integer
com/zurrtum/create/client/compat/jei/category/SequencedAssemblyCategory$FillingRenderer.class :: lambda$getSequenceName$1 -> owner=net/minecraft/core/component/DataComponentMap checkcast net/minecraft/world/item/alchemy/PotionContents
com/zurrtum/create/client/compat/jei/category/SequencedAssemblyCategory$FillingRenderer.class :: lambda$getSequenceName$1 -> owner=net/minecraft/core/component/DataComponentMap checkcast com/zurrtum/create/infrastructure/component/BottleType
com/zurrtum/create/client/compat/jei/category/SpoutFillingCategory.class :: lambda$getRecipes$1 -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/world/item/alchemy/PotionContents
com/zurrtum/create/client/compat/jei/widget/PotionTooltip.class :: lambda$onRichTooltip$0 -> owner=net/minecraft/core/component/DataComponentMap checkcast net/minecraft/world/item/alchemy/PotionContents
com/zurrtum/create/client/compat/jei/widget/PotionTooltip.class :: lambda$onRichTooltip$0 -> owner=net/minecraft/core/component/DataComponentMap checkcast com/zurrtum/create/infrastructure/component/BottleType
com/zurrtum/create/client/compat/jei/widget/PotionTooltip.class :: lambda$onRichTooltip$0 -> owner=net/minecraft/core/component/DataComponentMap checkcast java/lang/Float
com/zurrtum/create/client/compat/rrv/CreateView.class :: createSlot -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/world/item/component/CustomData
com/zurrtum/create/client/compat/rrv/CreateView.class :: createSlot -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/world/item/component/CustomData
com/zurrtum/create/client/compat/rrv/CreateView.class :: updatePotionName -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/world/item/alchemy/PotionContents
com/zurrtum/create/client/compat/rrv/CreateView.class :: updatePotionName -> owner=net/minecraft/world/item/ItemStack checkcast com/zurrtum/create/infrastructure/component/BottleType
com/zurrtum/create/client/compat/rrv/view/SequencedAssemblyView$FillingRenderer.class :: getSequenceName -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/world/item/alchemy/PotionContents
com/zurrtum/create/client/compat/rrv/view/SequencedAssemblyView$FillingRenderer.class :: getSequenceName -> owner=net/minecraft/world/item/ItemStack checkcast com/zurrtum/create/infrastructure/component/BottleType
com/zurrtum/create/client/content/equipment/clipboard/ClipboardScreen.class :: <init> -> owner=net/minecraft/core/component/DataComponentMap checkcast com/zurrtum/create/infrastructure/component/ClipboardContent
com/zurrtum/create/client/content/equipment/zapper/ZapperScreen.class :: <init> -> owner=net/minecraft/world/item/ItemStack checkcast com/zurrtum/create/infrastructure/component/PlacementPatterns
com/zurrtum/create/client/content/equipment/zapper/ZapperScreen.class :: init -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/world/level/block/state/BlockState
com/zurrtum/create/client/content/equipment/zapper/terrainzapper/WorldshaperRenderHandler.class :: createBrushOutline -> owner=net/minecraft/world/item/ItemStack checkcast com/zurrtum/create/infrastructure/component/TerrainBrushes
com/zurrtum/create/client/content/equipment/zapper/terrainzapper/WorldshaperRenderHandler.class :: createBrushOutline -> owner=net/minecraft/world/item/ItemStack checkcast com/zurrtum/create/infrastructure/component/PlacementOptions
com/zurrtum/create/client/content/equipment/zapper/terrainzapper/WorldshaperRenderHandler.class :: createBrushOutline -> owner=net/minecraft/world/item/ItemStack checkcast com/zurrtum/create/infrastructure/component/TerrainTools
com/zurrtum/create/client/content/equipment/zapper/terrainzapper/WorldshaperScreen.class :: <init> -> owner=net/minecraft/world/item/ItemStack checkcast com/zurrtum/create/infrastructure/component/TerrainBrushes
com/zurrtum/create/client/content/equipment/zapper/terrainzapper/WorldshaperScreen.class :: <init> -> owner=net/minecraft/world/item/ItemStack checkcast com/zurrtum/create/infrastructure/component/TerrainTools
com/zurrtum/create/client/content/equipment/zapper/terrainzapper/WorldshaperScreen.class :: <init> -> owner=net/minecraft/world/item/ItemStack checkcast com/zurrtum/create/infrastructure/component/PlacementOptions
com/zurrtum/create/client/content/schematics/cannon/SchematicannonScreen.class :: getFuelLevelTooltip -> owner=net/minecraft/core/component/DataComponentMap checkcast net/minecraft/network/chat/Component
com/zurrtum/create/client/content/schematics/client/SchematicHandler.class :: loadSettings -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Boolean
com/zurrtum/create/client/content/schematics/client/SchematicHandler.class :: loadSettings -> owner=net/minecraft/world/item/ItemStack checkcast net/minecraft/core/BlockPos
com/zurrtum/create/client/content/trains/track/TrackTargetingClient.class :: clientTick -> owner=net/minecraft/world/item/ItemStack checkcast java/lang/Boolean
com/zurrtum/create/client/ponder/foundation/ui/PonderUI.class :: getBreadcrumbTitle -> owner=net/minecraft/core/component/DataComponentMap checkcast net/minecraft/network/chat/Component
```