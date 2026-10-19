# 削减清单（26.3 移植）—— 必须逐条写进最终交付说明

> 原则：每一项都要写「丢了什么」+「为什么必须丢」+「能不能修回来」。

## 一、依赖层（26.3 上不存在，只能替代或砍）
| 组件 | 处理 | 丢了什么 | 可修回？ |
|---|---|---|---|
| **Veil**（foundry.veil） | **已彻底拔除**（`import foundry.veil` 89 → 0）：网络层复用自有垫片，渲染/杂项新写 12 个垫片文件，**15 处降级** | 渲染阶段事件（含物理法杖选择框、气球后处理）、后处理管线（PostPipeline/PostProcessingManager）、AdvancedFbo、透视渲染状态、GLSL 预处理器 | 逐条见 `docs\VEIL-ELIMINATION.md`（§4 有完整 15 条 + 可修回条件） |
| **glslprocessor**（io.github.ocelot） | 4 个着色器预处理器改**直通** | 动态方向光照着色、动态天空光阴影、水面遮挡着色、fancy sublevel 着色器改写 | 需重写 GLSL AST 逻辑 |
| **Create** | Create-Fly 26.2 + 版本约束补丁 | 26.3 未经上游验证，mixin 目标可能失效 | 等上游 26.3 分支 |
| **sable-companion** | 自行 javac 编 26.3 版 | 无（源码 MIT，功能完整） | — |

## 二、可选兼容（目标 mod 不存在，整体排除）
| 组件 | 处理 | 丢了什么 |
|---|---|---|
| Shoulder Surfing（6 文件） | 移出 `_dropped_compat/` + 删 6 条 mixin 条目 | 肩部冲浪视角下子关卡渲染联动 |
| Sodium（2 文件 + 1 条 mixin） | 移出 | 钠渲染器下的子关卡渲染路径（回退 vanilla 路径） |

## 三、GUI 渲染管线：`GuiGraphics` → `GuiGraphicsExtractor`（R341）
> 全表/修法见 `docs\fix-guigraphics.md`（115 → 0 非 Veil 残留；19 文件 / 56 处）。

| 位置 | 处理 | 丢了什么 | 可修回？ |
|---|---|---|---|
| `DiagramButton` 悬停 tooltip | `DiagramScreen.renderTooltip` 调用**注释掉** | 图纸界面按钮的悬停 tooltip 不显示（按钮本身正常） | ✅ Veil 线把 `DiagramScreen.renderTooltip` 形参改成 `GuiGraphicsExtractor` 后恢复注释的两行 |
| `mixin\physics_staff\GuiGraphicsMixin` | **整类降级为不注入**（`@Mixin(GuiGraphicsExtractor.class)`，删失效 `@WrapMethod`） | 物理手杖在物品栏槽位的 16×16 裁剪高亮（该效果 1.21.11 阶段就已不绘制） | ⚠️ 需按 26.3 `item(LivingEntity,ItemStack,III)` 重写；该类未登记进 `simulated.mixins.json`，0 运行期影响 |
| `SimGUITextures.render(…, Color)` | 方法体仍是空壳 | 带颜色贴图染色重绘不绘制 | ⚠️ 需 `TextureSetup.singleTexture` 重写（**既有降级**，非本次引入） |

## 四、Veil 拔除（R341）—— **15 处降级**，全表见 `docs\VEIL-ELIMINATION.md`
> `import foundry.veil`：**89 → 0**（76 文件）；新写垫片 **12** 文件；复用网络层垫片 6 文件。

| 组 | 降级点 | 丢了什么（一句话） |
|---|---|---|
| 事件订阅 | `VeilEventPlatform.onVeilAddShaderProcessors` / `onVeilRegisterBlockLayers` / `onVeilRegisterFixedBuffers`（3 条） | GLSL 预处理器挂载、区块渲染层注册、固定缓冲刷出 —— 26.3 三者都无对应入口 |
| 渲染阶段 | `AeronauticsClient` 订阅删除、`SimulatedClient` 订阅删除、`VeilRenderLevelStageEvent` 只剩枚举（3 条） | 气球热空气后处理、物理法杖选择框/悬停框、Veil 的全部 11 个渲染阶段回调（`MultiBufferSource` 在 26.3 已不存在） |
| 渲染工具 | `AdvancedFbo`、`VeilLevelPerspectiveRenderer`、`VeilRenderSystem`、`MatrixStack`（4 条） | 离屏 FBO 不分配 GPU 资源（`getId()` 是假负数）、透视渲染恒 false、渲染门面 60+ API 未提供、变换栈无事件源 |
| 后处理 | `getPipeline` 恒 null、`runPipeline` 空、`Context.setFramebuffer` 空、`ShaderUniformAccess` 全空（4 条） | 图表/便签的线条描边、配色分级、淡出整体消失 |
| 着色器预处理 | `EndSeaFadeTransformer` 去掉 `implements ShaderPreProcessor`（1 条） | End Sea 分层雾气着色（该文件本就不参与编译；`glslprocessor` 无 26.3 构建） |

**垫不掉的 3 条**：`ShaderPreProcessor`（依赖 glslprocessor）、Veil 渲染阶段事件签名（`MultiBufferSource` 已删）、
`VeilRenderSystem` 的 GL 能力探测族（工程零调用，不留空方法）。

## 五、垫片层：`src\stub\java`（registrate + create-foundation，R342）
> 全表/修法见 `docs\fix-stub.md`（49 错误 → **0**，53 → 80 文件，补 27 类）。

| 位置 | 丢了什么 | 可修回？ |
|---|---|---|
| `AbstractRegistrate.simple/accept/register` | **不接管注册表事件** —— 直接持有上游已 new 出的对象，`register()` 空操作。值是对的，注册动作没发生 | 需接 Fabric `Registry.register` / NeoForge `DeferredRegister` |
| `BlockBuilder`/`ItemBuilder`/`BlockEntityBuilder`/`EntityBuilder.register()` | 只 new 一个持有 **null** 的句柄，**不创建** Block/Item/BlockEntityType | 26.3 已无 `BlockEntityType.Builder`，需手写 `new BlockEntityType(supplier, blocks)` |
| `SharedProperties.softMetal/stone/wooden` | 只给裸 `BlockBehaviour.Properties.of()`，**没套** Create 的强度/音色/材质数值 | 需按 Create 源码补数值 |
| `addDataGenerator` / `ProviderType` / 各 datagen 钩子 | datagen 全空操作（只在 gradle datagen 任务里跑，运行期不需要） | 需真接 `DataProvider` |
| `CreateRegistrate.setTooltipModifierFactory` | 存不用 ⇒ **Create 的物品 tooltip 注入链没接** | 需接 `TooltipModifier` 注册表 |
| `SafeBlockEntityRenderer.renderSafe` / `SafeKineticBlockEntityRenderer.renderSafe` | 钩子**没接进**父类渲染流程（不出图）；buffer 形参已从 `MultiBufferSource`（26.3 已删）换成 `SubmitNodeCollector` | 需按 26.3 render-state 流程重写 |
| `MenuBuilder` / `RegistrateTagsProvider` / `SpecialBlockStateGen` / `ISyncPersistentData` | 空壳（javap 实测垫片原版即如此，主工程零引用） | 需要时再补 |

## 六、渲染/GUI 族（R350）—— 348 → 77 错，**新降级 5 条**
> 全表/修法见 `docs\fix-aero-render.md`（9 族全清零，32 文件）。

| 位置 | 处理 | 丢了什么 | 可修回？ |
|---|---|---|---|
| `PhysicsStaffRenderHandler.renderAllLocks` | **整方法删除** | 物理法杖「锁」的贴图方块高亮不再绘制 | ⚠️ 需按 26.3 `LevelRenderEvents` 拿 `SubmitNodeCollector` 重写 |
| `PhysicsStaffClientHandler.onRender` + `PhysicsBeam.render` | 空实现 / 删除 | 物理法杖**光束折线**不再绘制（节点抖动模拟保留） | ⚠️ 同上；`line.submit(mc, ms, collector, camera, pt)` 即可复活 |
| `PhysicsStaffRenderHandler.renderSelectionBox` | `options.hideGui` 分支删除 | 按 F1 隐藏 GUI 时法杖选择框不再跟着隐藏 | ❌ `Options.hideGui` 26.3 已无（无公开替代） |
| `HoldInteractionManager.renderOverlay` | `hideGui` → 常量 `false` | 按 F1 时按住交互的进度条/提示仍显示 | ❌ 同上 |
| `LinkedTypewriterItemBindHandler.renderOverlay`（excluded-wip） | `hideGui` 分支删除 | 按 F1 时键位绑定提示仍显示 | ❌ 同上 |

**同族的 5 条零损失清理**（删的都是已不可用的空壳/空刷，不计视觉削减）：
`SimIcons.render(PoseStack,MultiBufferSource,int)`、`RenderableNavigationTarget` 的 buffer 形参与 `ItemRenderer`、
`RopeStrandElement.renderLast`、`DiagramStickyNote` 的 `endBatch()`、`SimulatedCommonClientEvents.onRenderLevelStage` 的 buffer 形参。
**等价改写**（不是降级）：`hLine/vLine`→1px `fill`、`setWindowSize`→构造器尺寸、`Sheets.cutoutBlockSheet`→`RenderTypes.cutoutMovingBlock()`。

## 七、注册 / 方块注册 / 数据族（R351）—— 本族 166 → 0，工程 348 → 71，**新降级 6 条**
> 全表/修法见 `docs\fix-aero-registrate.md`（49 文件；含 26.3 的 `simpleCodec` / `CriterionTrigger` / `DyeColor` 事实表）。

| 位置 | 处理 | 丢了什么 | 可修回？ |
|---|---|---|---|
| 4 个 `SavedDataType` 的 id（Crystallization / BalloonLevel / LodestoneTracking / PhysicsStaff） | String → `Identifier.fromNamespaceAndPath(...)` | **存档文件名变化** ⇒ 老存档的 `.dat` 读不到 | 需 `SavedDataStorage` 侧做旧名迁移 |
| `AeroBlocks.flammable(...)` | `FireBlock.setFlammable` 26.3 整方法删除 ⇒ 返回恒等算子 | 这些方块**不再被火点燃** | 需按数据驱动的可燃性表重写 |
| `CreateWorldScreenMixin` 的 `END_SEA` 分支 | 删除（`EndDragonFight.Data` 与 `level.dat` 字段都已删） | END_SEA 世界**不再预置“龙已击杀”**，正常开局 | 需在 ServerLevel 初始化后改 `EnderDragonFight` 这份 SavedData |
| `SimItems` 两处 `.model(AssetLookup.itemModelWithPartials())` | 删除（垫片返回 `Object`，`ItemBuilder.model` 只收强类型 `BiConsumer`） | 创造法杖 / 活塞发射器的**物品模型 datagen** | 给垫片补 `Object...` 兜底重载 |
| `AeroBlocks` 自定义 loot 表（1 处） | 删除（`LootPool.setRolls` 全面 Holder 化，且垫片 `loot()` 本就空操作） | 该方块战利品表 datagen | 需按 `Holder<ContextIntProvider>` 重写 |
| `SimulatedAdvancement.save(Consumer)` | 改 `builder.build(id)` + 回调，不走 `BootstrapContext` 版 `save` | 进度**跨 mod 查重 / 判据校验** | 改成真 `BootstrapContext` 注入 |

**同族零损失等价改写**：18 个方块的 `CODEC`/`codec()` 删除（26.3 方块根本没有 MapCodec 序列化）、
`simpleItem→item().build()`(30 处)、`setCapacity→withCapacity`、`displayClientMessage→sendOverlayMessage`、
`placeItemBackInInventory(+Prediction)`、`SignText.asMutable()`、`Vec3.STREAM_CODEC`、`FabricRegistryBuilder.create`、
`DyeItem.getDyeColor()→DataComponents.DYE`、`Items.DYE.blue()|pick()`、`Blocks.WOOL.brown()` / `CONCRETE.white()`、
`Blocks/Items.COPPER_BLOCK.weathering().unaffected()`、`AllBlocks.SAIL→AllItems.SAIL`。

## 八、编译收尾（R352）—— 71 → **0 错**，`compileJava` BUILD SUCCESSFUL，**新降级 4 条 + 语义微调 2 条**
> 全表/修法/26.3 事实见 `docs\fix-aero-final.md`（39 文件；日志 `notes\aero26-final.log`）。

| 位置 | 处理 | 丢了什么 | 可修回？ |
|---|---|---|---|
| `ClientHandleHandler`（手柄持握的第一人称挥臂） | 三行 `swingTime/swinging/swingingArm` → 每 tick 一次 `swing(MAIN_HAND, DEFAULT, false)` | **恒定循环挥臂**变成「挥一次」——三字段已并入 private `LivingEntity$SwingState`，26.3 无公开复位入口 | 需给 `LivingEntity` 加 accessor mixin 读 `swingState`；或给超长 duration 的 `SwingAnimation` 近似 |
| `ValueSettingsClient.tick`（按住右键编辑值） | 写 `LocalPlayer.swinging` 的 5 字节 → **5×NOP**（R407） | 长按期间不再强制取消挥臂动画（手臂自然挥一次）；交互/发包/开屏不变 | 同上一行（`SwingState` 无公开取消 API） |
| `ValueSettingsScreen.setCursor` / `StockKeeperRequestScreen` / `ControlsUtil` 的 4 处 GLFW 调用 | owner 改到 `skylands262/compat/SdlCompat`（SDL 实现，R407） | `glfwSetInputMode`（拖动存储仓列表时隐藏/恢复鼠标）→ **no-op**：拖动时鼠标不再隐藏（纯视觉） | 26.3 `CursorType` 只公开 `DEFAULT`，无安全的 hide/show 入口 |
| `PonderSceneMixin.onCameraSet` | `getValue(pt)` → `getValue()` | 相机旋转的**亚 tick 插值**（高帧率下略阶梯）。原代码的 `pt` 本就**不在作用域**（这 2 条正是编译错误本身） | ✅ 用 MixinExtras `@Local(argsOnly = true) float partialTick` 接回，1 行 |
| `AeroRenderTypes.make` | 删 `.bufferSize(RenderType.TRANSIENT_BUFFER_SIZE)` | `RenderSetupBuilder#bufferSize(int)` 26.3 已删 ⇒ 用默认缓冲大小（**只影响缓冲增长策略，不影响画面**） | 等 26.3 提供等价设置 |
| `SimAssemblyHelper`（拆解时搬胶水/悬挂实体） | 内部 `entityManager.sectionStorage` 逐 section → 按 plot chunk 列 `getEntities(null, columnBox, e->true)` | 覆盖集合等价（原实现就是遍历这些 chunk 的全部实体）；区别是多了 AABB 相交判断、不再区分 loaded section | 无需修（语义等价）；在意性能可改成一次全局包围盒查询 |

**语义微调（不算损失）**：① `HoneyGlueEntity.interact` / `DiagramEntity.interact` 由 `interactAt` 并入 `interact` 后，
同时接管「精确命中」与「普通右键」两条路径（原来只接管精确命中）；② `DisplayLinkScreenMixin` 的 `ChatFormatting.GRAY.getColor()`
→ 硬编码 `0xAAAAAA`（数值与原版一致，零视觉差异）。

**同族零损失等价改写**：`swing(+SwingAnimation.DEFAULT,false)`、`sendOverlayMessage`/`sendSystemMessage`、
`placeItemBackInInventory(+Prediction.SERVER_ONLY)`、`PushReaction.IGNORE_ENTITY|PUSH`、`ChunkPos.containing`、`ChunkPos.pack()`、
`LightCoordsUtil.getLightCoords`、`builtInRegistryHolder().is`、`Type.KEYBOARD`、`InputConstants.isKeyDown(int)`、
`ForceGroups.XXX.get()`、`DataComponentPatch.split()`、`ItemContainerContents.itemCopies()`、`Vec3.atCenterOf/atBottomCenterOf`、
`ItemStackTemplate.fromStack`、`getLightDampening`、`resetFlyingTicks()`、`Gui.hud.setOverlayMessage`、`SimTuple.setA/setB`。

## 九、待补充（随修随记）
- （暂无）

## 十、Create-Fly 26.2 字节码移植（R354→R355）

> 这一层不是「改源码」，是**直接改 jar 内字节码**（Create 没有 26.3 源码）。
> 修法/工具见 `docs\fix-create-api26.md`（搜「R355」）。
> 结论：A 393→38 处、D 602→88 处、E 4→0，**启动从 `AllEntityTypes` 推进到 `AllFeatures`**。

### 10.1 E 族「覆盖 26.3 final 方法」—— 8 条，其中 2 条真正有损失

| # | 位置 | 处理 | 丢了什么 | 可修回？ |
|---|---|---|---|---|
| 1 | `content/logistics/box/PackageEntity.canSimulateMovement()` | **换成 26.3 钩子** `getMoveSimulationType()→SERVER_AND_CLIENT`（新增方法） | **无** | — |
| 2 | `content/trains/entity/CarriageContraptionEntity.isLocalInstanceAuthoritative()` | 同上 | **无** | — |
| 3 | `client/catnip/gui/widget/AbstractSimiWidget.extractRenderState` | 与 `extractWidgetRenderState` **名字对调** + 自调用重指 | **无**（hover/tooltip/wasHovered 全保留） | — |
| 4 | `client/foundation/gui/widget/Indicator.extractRenderState` | 改名 `extractWidgetRenderState` | **无**（它本来就是绘制体） | — |
| 5 | `content/logistics/depot/EjectorItemEntity.moveOrInterpolateTo` | 删（原体是空 `return`） | **无** | — |
| 6 | `content/equipment/blueprint/BlueprintEntity.moveOrInterpolateTo` | 删 | **蓝图实体的位置吸附（snap 到整块坐标）没了**，改为 26.3 的插值移动（视觉上是「更平滑」而不是「错」） | ⚠️ 26.3 该方法是 final，三个重载全 final，**没有钩子**；要在 26.3 恢复只能在 `setPos`/`PositionPath` 侧动手 |
| 7 | `content/contraptions/ControlledContraptionEntity.moveOrInterpolateTo` | 删 | 原来**空体 = 忽略位置更新**；现在 26.3 的插值会生效（装置实体可能跟随 tick 插值） | ⚠️ 同上，无法保留「忽略」语义 |
| 8 | `content/contraptions/gantry/GantryContraptionEntity.moveOrInterpolateTo` | 删 | 同 #7 | ⚠️ 同上 |

> #6/#7/#8 是**放弃定制**：26.3 把 `Entity.moveOrInterpolateTo` 的三个重载全部 final，
> 且它们直接改内部插值状态，没有可覆盖的钩子。

### 10.2 `MapDecorationType`（record）构造器缩水 —— 1 处，**值靠推断**

26.3：`MapDecorationType(Identifier assetId, boolean showOnItemFrame, boolean trackCount)`；
26.2：五参（多了 `int mapColor` 与第 5 个 boolean）。`AllMapDecorationTypes.register`
整个方法体被重写成 3 参调用：

| 处理 | 丢了什么 | 可修回？ |
|---|---|---|
| `trackCount` 硬编码为 **`false`**（= 26.2 记录的第 4 个分量，即 Create 传的 `p4`） | 地图上 Create 站点装饰的**「计数徽章」不显示**（`mapColor` 在 26.3 也已删除，颜色一并不可控） | ✅ 把这 1 个 `iconst_0` 改成 `iconst_1` 即可（`tools\patch_create_methods.py` 里一行）；**若实测发现站点标记行为异常，先试这个开关** |

> Create 的 `MapItemSavedDataMixin` 会读 `trackCount()`，所以这个值**有实际语义**，
> 是「26.2 记录字段顺序」推断出来的，属**已知不确定项**。

### 10.3 已修但**没有**损失的（记录在案，便于交付说明）

- **包搬迁**：`blaze3d/** → renderpearl/**` 33 条映射（461 处类型名 / 83 个 class），
  只改常量池 Utf8，`PoseStack` 等 25 个仍在 blaze3d 的类明确保留 ⇒ **零语义变化**。
- **`PoseStack.mulPose(Quaternionfc)` → `rotate`**（240 处）：桥接类直接转调，**零语义变化**。
- **`Inventory.placeItemBackInInventory(ItemStack)`**（64 处）：桥到 `(ItemStack, Prediction.PREDICTED)`。
  ⚠️ 与 Aeronautics **源码侧**已改的 `Prediction.SERVER_ONLY`（见 §八）**口径不一致**：
  源码侧是「只在服务端做」，Create 字节码这侧是「立刻做并允许服务端纠正」。
  两者都不会丢物品，但**客户端预测表现可能不同**；要统一就把 `InventoryBridge` 里的 `PREDICTED` 改 `SERVER_ONLY`。
- **`BlockPos(Vec3i)` 构造器**（7 处 `new` + 3 处 `BlockPos::new` 方法引用）：垫成 `BlockPosShim extends BlockPos`
  （`Vec3i.equals` 用 `instanceof` + 坐标比较，`hashCode`/`compareTo` 只看坐标 ⇒ 不破坏 `Map<BlockPos,?>`）。

### 10.4 当前**未修**的硬骨头（阻断启动）

| 阻断点 | 原因 | 状态 |
|---|---|---|
| `com.zurrtum.create.infrastructure.worldgen.LayeredOreFeature` | 26.3 把 `Feature` 从 class 改成 **interface**，且 `place()` 从 `(FeaturePlaceContext)` 改成 4 参；`FeaturePlaceContext` / `FeatureConfiguration` **整个类在 26.3 不存在** | ⛔ **阻断**：这是第一个「必须写语义、且要改结构（加字段）」的地方，见 `docs\fix-create-api26.md` §8 |
| `ConfigPlacementFilter` | `PlacementFilter` 也变 interface，但 `shouldPlace` 签名没变 | 🔧 **可机械修**（未做）：`super_class`→Object + 加 `implements` + nop 掉 `super()` 那 5 字节 |

## 十一、Create-Fly 字节码移植（R356）—— 新降级 6 条

> 承接 §十。修法见 `docs\fix-create-api26.md`（搜「R356」）。
> 本轮把 A/B/C/D 从 **158 条 / 341 处** 压到 **112 条 / 204 处**，启动推进到**渲染主循环**（`Minecraft.runTick`）。

### 11.1 `LayeredOreFeature`：**层状矿不生成**（世界生成特性，已按“不许崩”处理）

26.3 的 `Feature` 变 interface、`place` 变 4 参、`FeaturePlaceContext`/`FeatureConfiguration` 整个类不存在。
本轮把 `LayeredOreFeature` 改造成合法实现，但 `place(...)` 体是 **`return false`**：

| 处理 | 丢了什么 | 可修回？ |
|---|---|---|
| `place` 直接返回 `false`；注册进 `BuiltInRegistries.FEATURE_TYPE` 的 codec 是 `MapCodec.unit(this)`（**忽略 config**） | **Create 的锌矿 / 分层矿（`striated_ores_*`）不再生成**；`data/create/worldgen/configured_feature/*.json` 的配置字段被忽略 | ✅ 算法本身还在字节码里（`canPlaceOre`/`shouldSkipAirCheck`/`LayeredOreFeature$TemporaryLayerEntry` 全保留）。要恢复需：给类**加 3 个实例字段**（layerPatterns/size/discardChance）、写 `codec()` 解 JSON、`place` 按 4 参重写（`config` 从字段取），再把 `LayerPattern$Layer` 的 `OreConfiguration$TargetBlockState` 换成 26.3 的 `BlockReplacement`（`state`/`target` 字段 → `state()`/`target()` 方法） |

> **不修的理由**：这是世界生成，标题画面不需要；而“改结构 + 重写 1000 字节带分支/异常表的方法体”
> 在 `patch_create_methods.py` 的能力边界之外（它只允许无分支、无异常表的方法改长度）。

### 11.2 26.2 `Container` 搬运 API：**语义是重建的，不是原版**（39 成员 / 102 处）

26.3 把整套 API 删了且**没有任何 *Util 接班**（全库扫描 0 命中）。`ContainerBridge` 按
「方法名 + 描述符 + 调用点用法」重建，**偏差如下（按影响排序）**：

| # | 偏差 | 影响 | 可修回？ |
|---|---|---|---|
| 1 | 所有 `Direction` 参数**被忽略**（26.3 没有 per-face 槽位 API） | 面限定的插入/抽取会变成**全槽位**（比原版宽松；不会少物品，可能多塞） | ⚠️ 需要 26.2 的 `Container` 源码才能精确对齐 |
| 2 | `count(Predicate,int)` / `preciseCount(Predicate,int)` 返回 **peek 副本（不改容器）** | 若原版是“数完就取”，这里会**少取**（不会多取） | 同上 |
| 3 | `insert/extract/countSpace` 的 `int` 参数统一按**数量上限 limit** 解释 | 若原版是“槽位号”或“每槽上限”，行为会偏移 | 同上 |
| 4 | `insert(List,int,int)` / `countSpace(List,int,int)` 的两个 int **含义不明**，按「忽略 / 整表可放」保守处理 | 特殊调用点可能少插 | 同上 |
| 5 | `update(predicate, function)` 对每个匹配槽 apply 一次（原版可能合并） | 无（结果一致） | — |

> 所有写操作都走 26.3 的 `Container.setItem` + `setChanged()`；**不复制、不吞物品**是设计目标。

### 11.3 `RenderSystem.outputColorTextureOverride` / `outputDepthTextureOverride`：**重定向失效**（12 处 / 3 类）

26.3 把这两个**全局输出纹理覆盖**字段删了（改成显式传 `RenderTarget`）。桥接静态字段
（`RenderBitsBridge`）只接住读写，**不会真的改变渲染输出**：

| 处理 | 丢了什么 | 可修回？ |
|---|---|---|
| 读写落到 `RenderBitsBridge` 的同名静态字段 | 「临时把渲染导向另一个 target 的离屏 pass」失效 ⇒ 相关效果**画到主 target** 或该 pass 变空（装置/传送带的部分特写渲染可能异常） | ⚠️ 26.3 无等价全局钩子；要在**每个调用点**改成显式 RenderTarget 参数（属重写渲染代码，不是桥接） |

### 11.4 `ComposterBlock.COMPOSTABLES`：**Create 物品不可堆肥**（1 处）

26.3 把堆肥概率搬进了 `DataComponents.COMPOSTABLE`，静态表 `COMPOSTABLES` 已删。
桥接给的是**空表** ⇒ Create 往表里注册的概率全部丢失：

| 处理 | 丢了什么 | 可修回？ |
|---|---|---|
| `ComposterBlock.COMPOSTABLES` → `ContainerBridge.COMPOSTABLES`（空 `Object2FloatMap`） | Create 的物品（树皮、种子类等）**不能放进堆肥桶** | ✅ 改成在 26.3 用 data component 注册（要按 26.3 的 `Compostable` 组件重写注册代码） |

### 11.5 `AllConfiguredFeatures`：configured-feature 键改用 `Registries.FEATURE`（datagen 漂移）

`Registries.CONFIGURED_FEATURE` 在 26.3 不存在（`ConfiguredFeature` 类也没了）。三个 `ResourceKey`
改成 `Registries.FEATURE` 下同 id 的键：

| 处理 | 丢了什么 | 可修回？ |
|---|---|---|
| `register(String)` 用 `Registries.FEATURE` | `AllConfiguredFeatures.ZINC_ORE` 等**不再指向 26.2 的 configured-feature 注册表**；datagen/数据包路径会漂移（配合 §11.1：矿本来就不生成） | ✅ 与 §11.1 一起修 |

### 11.6 ⚠ **Sable 的 `fix_bundle_packet.ClientPlayNetworkAddonMixin` 被禁用**（不属于 Create，但阻断启动）

`@WrapOperation` 目标是 `Minecraft.execute(Runnable)`，而 **Fabric API 0.163.0+26.3 的
`ClientPlayNetworkAddon.receive(...)` 已经不再调它**（改成直接调 handler）⇒ Mixin 报
`Critical injection failure ... (0/1) succeeded. Scanned 0 target(s)`，**整个客户端启动失败**。
处理：把该 mixin 从 `sable-fabric-26.3.jar` 内的 `sable-fabric.mixins.json` 的 `client` 数组里**删掉**
（同组的 `ClientPacketListenerMixin` 是 `@WrapMethod handleBundlePacket`，目标还在，保留）。

| 丢了什么 | 影响 | 可修回？ |
|---|---|---|
| Sable 对 Fabric 打包包（bundle packet）的**主线程调度修正** | 收到 bundle 包时的线程调度按 26.3/Fabric 原样；**Sable 原本要修的那个 bug 在这版 Fabric 上本来就不存在**（它改的那行代码没了） | ✅ 实际上**应当删除**（上游已修）；要恢复只需改 Sable 源码删掉这个 mixin |

> 备份：`work\run26\mods-aero\sable-fabric-26.3.jar.bak-r356`。
> ⚠ 这条是**跨项目**的：改的是 `mods-aero` 里的成品 jar，没有动 `work\sable-26\` 源码树。

### 11.7 ⚠ **15 条 Create/Ponder 渲染管线缺席**（黑屏修复的代价，见 `docs\fix-blackscreen.md`）

26.3 的管线走 **GLSL→SPIR-V**，而 Create 26.2 的 shader 一条都不满足新要求
（`#moj_import <...>` 未被展开、缺显式 `layout(location=N)`、`ProjMat`/`ModelViewMat`/
`fog_*`/`sample_lightmap` 在 26.3 变成 snippet）。`ShaderManager.apply` 对「required 管线
编译失败」是**硬抛**，会打断整次资源 reload（连带 atlas 一个都不建 ⇒ 全黑）。
处理：`ShaderManagerLenientMixin` 只把 required 那处 `isEmpty` 改成 true，让失败降级成沉默跳过。

| 丢了什么 | 影响 | 可修回？ |
|---|---|---|
| `create:pipeline/glowing`、`create:pipeline/glowing_translucent`、`ponder:pipeline/entity_block_{solid,cutout,translucent}`、`ponder:pipeline/entity_block_light_*`、`ponder:pipeline/nether_entity_block_*`、`ponder:pipeline/position_color_triangles`（共 15 条） | 用到它们的**实际绘制**会报错/被跳过：Create 的「发光」效果、Ponder 场景里的实体方块与光照渲染。**标题画面、普通方块/物品/GUI 不受影响**（已验证 12/12 atlas + 标题画面正常） | ✅ 真修 = 按 26.3 重写这批 shader（加 `layout(location)`、把矩阵/雾/lightmap 改成 snippet 引用、`#moj_import` 换成 26.3 的 include 机制）。属独立工作量 |

> 备份：`work\run26\mods-aero\create-fly-26.2-6.0.9-2-26.3-patched.jar.bak-black`
> （改前原始 jar）。补丁脚本：`tools\patch_create_shaderlenient.py`。

### 11.8 ⚠ **Create 的 120 个 trim 调色板失败**（纯外观）

Create 26.2 自带 `assets/minecraft/atlases/items.json` + `armor_trims.json`（**覆盖**原版同名文件），
里面写的是 `palette_key: minecraft:trims/color_palettes/trim_palette` / `minecraft:trims/color_palettes/<色>`。
26.3 把这套改名成 `minecraft:trim_base` / `minecraft:trim/<色>`，且 `26.3.jar` 里
`color_palettes` 条目数为 **0** ⇒ 每次 reload 打 120 条
`Failed to load palette image minecraft:trims/color_palettes/trim_palette`。

| 丢了什么 | 影响 | 可修回？ |
|---|---|---|
| `create:trims/items/card_*_trim_*` 的调色板 | Create 的纸板甲饰纹**丢颜色变体**（物品仍在，贴图缺 paletted 变体） | ✅ 把 Create 那份 `minecraft:atlases/items.json` 与 26.3 原版**合并**（别整体覆盖，否则会丢 26.3 新增的 sprite 源），再把调色板路径改到 `minecraft:trim_base` / `minecraft:trim/<色>` |

> **这条不是黑屏原因**：修完三个中止点后，同样的 120 条 ERROR 仍在，但 12/12 atlas 照建
> （异常被 `SpriteLoader` 逐 sprite catch）。本轮故意没动它 —— 改 atlas JSON 有打乱
> items atlas 的风险，而收益只是外观。

### 11.9 `BakedQuad$MaterialInfo.shade()` 的语义近似

26.3 的 `MaterialInfo` 没有「关闭方向性明暗」的哨兵值，`shade` 布尔换成了
`Direction shadeDirectionOverride`。垫片 `MaterialInfoBridge`：

| 处理 | 丢了什么 | 可修回？ |
|---|---|---|
| `of(..., boolean shade, ...)` → `of(..., (Direction) null, ...)`；`shade()` → `shadeDirectionOverride() == null` | `shade=false` 的 OBJ 模型**仍按默认方向明暗**（少数 Create OBJ 模型明暗与 26.2 略有差异）；glint 渲染类型按图集/layer 推断 | ⚠ 26.3 无等价表达；除非 26.3 另有「flat shading」开关（未发现） |

## 四、第五批（port-batch3，`configured_feature` 转换器那一批）

| mod | 位置 | 丢了什么 | 为什么 | 可修回？ |
|---|---|---|---|---|
| `Structory_Towers` 1.0.17 | `data/structory_towers/loot_table/potions/*.json`（4 张） | 物品组件 `minecraft:hide_additional_tooltip` → `minecraft:tooltip_display{hide_tooltip:true}`：**连物品名一起隐藏**（原先只隐藏附加信息） | 26.3 删了这个组件类型（`No component with type: 'minecraft:hide_additional_tooltip'`），最近的是 `tooltip_display` | ✅ 若以后确认 26.3 有「只隐藏附加行」的写法，替换这 4 个文件即可（纯展示层，无功能影响） |
| `natures_spirit` 相关（未交付） | `configured_feature` 的 `no_bonemeal_flower` | 转换器按普通 patch（`simple_block`）处理 ⇒ **允许骨粉** | 26.3 没有 `no_bonemeal_flower` 类型，也没有对应字段；该 mod 本身还未交付 | ⛔ 需要 Java 层另做「不可骨粉」判断 |
