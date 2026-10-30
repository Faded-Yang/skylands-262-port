# 已解族索引（**逐字**从 `AGENTS.md` 热层搬出）

> 拆分时间 20261017-095046。这是历史全表；热层只保留【族名 + 一句结论】的紧凑表。
> 查的时候在这里搜关键词。

## 已解族索引（**先看这里，别重复调查**）

> 只列结论；**精确修法在 `docs\API-1.21.11.md`**（或 `docs\PHASE-LOG.md`）。
> `当前操作状态` 里提到的「已解 38 族」全表在 **`PORT-PLAN.md` 的交接总览**里。

| 族 | 结果 | 去哪查 |
|---|---|---|
| `AllKeys.altDown()` | →0 | API 文档搜 `AllKeys` |
| `ItemStack.saveOptional/parseOptional` | →0 | API 文档搜 `saveOptional` |
| `addToGoggleTooltip(List,boolean)` | 14→2 | API 文档搜 `Goggle` |
| `BlockBehaviour.updateShape` 6→8 参 | 12→0 | API 文档搜 `updateShape` |
| `Sided.rotate`（**嵌套类** `ValueBoxTransform.Sided`） | 12→0 | API 文档搜 `Sided` |
| `类型变量数目错误`（渲染器要两个类型参数） | 8→0 | API 文档搜 `类型变量` |
| `save(RegistrateRecipeProvider, Identifier)` | 12→0 | API 文档搜 `RecipeBuilder` |
| `PlacementOffset.placeInWorld`（末参被删） | 10→0 | API 文档搜 `PlacementOffset` |
| 渲染层 `addLayer` 族 | −50 | PHASE-LOG 搜 `阶段B-1` |
| 渲染层 `Sheets` 方块 sheet 工厂 | −84 | PHASE-LOG 搜 `阶段B-2` |
| `PoseStack→Pose`（`ms.last()`） | 34→0 | PHASE-LOG 搜 `阶段B-3` |
| **去 Veil：`SimRenderTypes` / `AeroRenderTypes`** | **−57** | PHASE-LOG 搜 `阶段B-6` |
| **Veil 网络层垫片**（4 个影子类，Fabric 真实实现） | 已落地，**运行期收益** | PHASE-LOG 搜 `Veil 网络层` |
| **levitite 曲面细分着色器停用**（`safeGetUniform` 族清零） | **−34** | PHASE-LOG 搜 `阶段B-9` |
| **死注入点 mixin**（惰性化 5 个 + `require = 0` 5 处）| 运行期修复（计数不变）| PHASE-LOG 搜 `阶段B-10`/`阶段B-12`/`阶段B-13` |
| mixin 注入目标（117 条，**双向核过**）| ✅ **真缺失已清零**；惰性化 7 + `require=0` 6 | PHASE-LOG 搜 `阶段B-11`…`阶段B-18` |
| 工具：`recheck_mixins.py`（反向复核，**FQN 从源码解析、不手抄**）| 可重跑 | 项目根目录 |
| **逐条复核**：`verify_mixin_targets.py`（真伪分开）| 剩余 8 条已定性 | PHASE-LOG 搜 `阶段B-15` |
| ⚠ 工具：`audit_mixins.py` 有**假阳性**，须配 `verify_mixin_targets.py` 用 | | |
| **`ScrollValueBehaviour` 族** | **第1步已做，−34**（`value`/`getValue`/`setValue`/`between` 已清零）| API 文档搜 `ScrollValueBehaviour` |
| **`RenderSystem` 旧状态方法族**（全被管线取代）| **−57**（`找不到符号` −106）| API 文档搜 `RenderSystem` |
| **`GuiGraphics.pose()` 2D 化**（`Matrix3x2fStack`）| ⚠ **不能脚本化**，只能逐点手改；只完成 1 个文件 | API 文档搜 `Matrix3x2fStack` |
| **registrate 链尾类型**（`.item()`→`.simpleItem()`）| **−19**（`ItemEntry→BlockEntry` 清零）| API 文档搜 `simpleItem` |
| **缺方法/缺类先定性**（项目垫片？垫片 jar？Create Fly？）| 工具 `probe_owners.py` | API 文档搜 `probe_owners` |
| **REA 素材：1.21.1 真 Create** ✅ | `%APPDATA%\.minecraft\versions\Create 航空学 × 浮空群岛\mods\create-1.21.1-6.0.10.jar`（2692 class，看「API 原来长什么样」）| API 文档搜 `REA 素材` |
| **`DisplaySource.displaySource` 重建**（**精确等价**，非打桩）| **−22 `找不到符号`** | API 文档搜 `AllDisplaySources` |
| ★ **API 被删时怎么找替代**：扫新 jar 里**描述符同时含两个类型**的方法 | 工具 `find_ds_register.py` | API 文档搜 `找替代入口` |
| **`ParticleRenderType` 常量迁移** | `PARTICLE_SHEET_TRANSLUCENT` → **`SINGLE_QUADS`**（−12）| API 文档搜 `ParticleRenderType` |
| **NeoForge datagen 垫片三件套**（`MultiPartBlockStateBuilder` / `ConfiguredModel.Builder<T>` / `getMultipartBuilder`）| **−10** | API 文档搜 `datagen 垫片` |
| **`ValueInput` 族**：项目自己的序列化接口改签名（`NBTSerializable` + 6 实现）| `ValueInput→CompoundTag` **24→10** | API 文档搜 `NBTSerializable` |
| **枚举 NBT 助手 `SimNbtHelper`**（替 Create 的 `NBTHelper.*Enum`）| `ValueInput→CompoundTag` 24→6 | API 文档搜 `SimNbtHelper` |
| ★ **1.21.11 存储读写惯用法**（`read(String,Codec)` / `childrenListOrEmpty` / codec 编码）| 已用于 `ContainerSlot`/`MultiSlotContainer` | API 文档搜 `存储读写惯用法` |
| **`initConfigurationWidgets` 覆写**（父方法 1.21.11 已删）| **−14**（两族各 −14；方法体保留）| API 文档搜 `initConfigurationWidgets` |
| ⚠ **`BufferUploader` 整类不存在**；替代是 **`RenderType.draw(MeshData)`** | 12 处待选 RenderType | API 文档搜 `BufferUploader` |
| ⚠ **`RenderType.gui()` / `guiTextHighlight()` 也已删除**（GUI 改走 `GuiRenderer`）；`RenderTypes`（复数）里**没有 gui** | 8 处需设计 | API 文档搜 `RenderType.gui` |
| **`SpriteContents.Ticker` → `AnimationState`** | **−3**（8 处）; 印证 `createTicker→createAnimationState` | API 文档搜 `AnimationState` |
| ⚠ **判类是否存在：扫 jar 路径片段，别用 javap 的前 N 字符** | 工具已踩坑 | API 文档搜 `javap 判存在` |
| ★★ **`renderSafe` 同源族**（垫片漏声明 + 13 个渲染器继承错父类）| **−31**（`方法不会覆盖` −40、`找不到符号` −22）| API 文档搜 `renderSafe` |
| ★ **方法：分析最大族的分布，找单一上游**（读 `@Override` 下方签名）| 工具 `analyze_override3.py` | API 文档搜 `分析最大族` |
| ★★ **`neighborChanged` 第5参 `BlockPos`→`Orientation`**（28 处同形）| **−13**；同族 `BlockPos→Orientation` **8→2** | API 文档搜 `neighborChanged` |
| ★★ **`ClipboardCloneable` 签名迁移**（去掉 `HolderLookup.Provider` 参 + `CompoundTag`→`Value*`）| **−22**（`方法不会覆盖` −32）| API 文档搜 `ClipboardCloneable` |
| ★★ **`KineticBlockEntityRenderer` 缺 `renderSafe`**（10 渲染器）⇒ 造 `SafeKineticBlockEntityRenderer` | **−15**（`方法不会覆盖` −18）| API 文档搜 `SafeKineticBlockEntityRenderer` |
| ★★ **`getCloneItemStack` 加第4参 `boolean includeData`**（6 处同形）| **−6**（该族 −12）| API 文档搜 `getCloneItemStack` |
| ★ **`getLocalOffset` 3参→1参**（Create 的 `ValueBoxTransform` 系）| **−6**（该族 −14；3 处体用到 level/pos 被闸门拦下）| API 文档搜 `getLocalOffset` |
| ★ **找不到方法宿主时：拿候选 jar 逐个「按方法名扫字节」**（我先扫 Sable=0，再扫 Create Fly 命中）| 工具 `probe_localoffset.py` | API 文档搜 `找方法宿主` |
| 阶段A 生物刷新（现成 mod） | 用户验收通过 | PHASE-LOG 搜 `阶段A` |

**仍未解 / 需人工判断**：`Level.blockUpdated` 的 **第 5 参语义已解**（= `Orientation`，见 `neighborChanged` 族）；
下列仍未解：
4 个架构族（`ScrollValueBehaviour` 112、渲染层 ~128、`方法不会覆盖` 420…）、5 项语义判断
—— **详见 `PORT-PLAN.md` 交接总览**。


<!-- ===== 从热层搬来的较早族行（20261017-101807）===== -->

| 族 | 结论 |
|---|---|
| `SpriteContents.Ticker` → `AnimationState` | −3（8 处）; 印证 `createTicker→createAnimationStat… |
| ⚠ 判类是否存在：扫 jar 路径片段，别用 javap 的前 N 字符 | 工具已踩坑 |
| ★★ `neighborChanged` 第5参 `BlockPos`→`Orientation`（28 处同形） | −13；同族 `BlockPos→Orientation` 8→2 |
| ★★ `ClipboardCloneable` 签名迁移（去掉 `HolderLookup.Provider` 参 + `CompoundTag`→`Value*`） | −22（`方法不会覆盖` −32） |
| ★★ `KineticBlockEntityRenderer` 缺 `renderSafe`（10 渲染器）⇒ 造 `SafeKineticBlockEntityRenderer` | −15（`方法不会覆盖` −18） |
| ★★ `getCloneItemStack` 加第4参 `boolean includeData`（6 处同形） | −6（该族 −12） |
| ★ `getLocalOffset` 3参→1参（Create 的 `ValueBoxTransform` 系） | −6（该族 −14；3 处体用到 level/pos 被闸门拦下） |
| ★ 找不到方法宿主时：拿候选 jar 逐个「按方法名扫字节」（我先扫 Sable=0，再扫 Create Fly 命中） | 工具 `probe_localoffset.py` |
| ★ **`getAnalogOutputSignal` 加第4参 `Direction`**（4 处）| **−4**（该族 −8）| API 文档搜 `getAnalogOutputSignal` |
| ★★ **`onClick`/`mouseClicked` 迁到 `MouseButtonEvent`**（新签名 `(event, doubleClick)`）| **−13**（用「局部别名」法，原方法体零改动）| API 文档搜 `MouseButtonEvent` |
| ★★ **局部别名法**：参数类型变了但方法体大 —— 换签名 + 体首注入 `final double mouseX = event.x();` 等别名 | 通用配方 | API 文档搜 `局部别名法` |
| ★★ **`getMetaFactory()` 只改返回类型**（`ParticleProvider.Sprite<X>` → `Function<SpriteSet, ParticleProvider<X>>`）| **−7**（连带 `构造器引用无效` 14→0）| API 文档搜 `ICustomParticleData` |
| ★★ **「只改声明、体不动」第二式**：返回类型写错时，体往往本来就对 ⇒ 只换返回类型 | 通用配方 | API 文档搜 `只改声明` |
| ★★ **`createParticle` 补末参 `RandomSource`**（8 处）| **−9**（`Factory未覆盖createParticle` 16→0）| API 文档搜 `createParticle` |
| ⚠ **`src/excluded-wip` 不可删**（131 文件，装 `SimBlocks`/`SimItems`/`AeroBlocks` 等 bootstrap）| 移出编译 ⇒ **790 → 1548（+758）**，已回滚 | API 文档搜 `excluded-wip` |
| ★★ **`ForceGroups.REGISTRY` 已取消** ⇒ 补项目侧 `ForceGroupIndex` | **−6**（`找不到符号` −16 全清，`方法引用无效` +4 待收）；**id 从 1.21.1 字节码常量池实测读出** | API 文档搜 `ForceGroups` |
| ★★ **`ScrollValueBehaviour` 被拆成 client/server 两个类**：`between`/`getValue`/`setValue`/`withCallback`/`write-read` 全在 **`ServerScrollValueBehaviour`**；客户端类只剩 `withFormatter`/`onlyActiveWhen`/`formatValue` | `between` 覆盖要改**返回类型**（规则42）| API 文档搜 `ServerScrollValueBehaviour` |


<!-- ===== 从热层搬来的较早族行（20261017-103039）===== -->

| 族 | 结论 |
|---|---|
| ★ **`TagKey.matches(stack)` → `stack.is(tag)`**（3 处）| **−3**（`找不到符号` −6）；同行的 `stack.is(...)` 就是自证 | API 文档搜 `TagKey.matches` |
| ★★ **`updateEntityAfterFallOn` → `stepOn(Level,BlockPos,BlockState,Entity)`**（3 处）| **−6**（新参是旧参的超集 ⇒ 体不改）| API 文档搜 `stepOn` |
| ★ **`ScrollValueBehaviour` 归类第一步已完成**：3 文件切服务端版 + 构造器改 `super(be)` | **R94−3 + R95−3 = −6**；构造器错 6→0 | API 文档搜 `ScrollValueBehaviour 归类` |
| ⚠ **两版构造器完全不同**：客户端 `(Component label, B be, ValueBoxTransform slot)`；服务端 `ServerScrollValueBehaviour(SmartBlockEntity)` | 改父类后必须同时改构造器 | API 文档搜 `ServerScrollValueBehaviour 构造器` |
| ★★ **删语法有风险 ⇒ 用「等价空操作」替换**：`withFormatter(...)`→`.withCallback(v -> {})` | **−6**；前两版「删调用」造成 18/4 条解析期错误，第三版「替换」0 错 | API 文档搜 `删语法` |
| ★★ **换父类必须同时删掉「子类专有覆写」**：切到 `ServerScrollValueBehaviour` 后，`createBoard` 覆写失去父类、体里的 `label`/`formatValue` 也不存在 | 删 6 处 ⇒ **−12** | API 文档搜 `换父类的连带清理` |
| ⚠ **`.replace()` 是前缀匹配**：短模式是长模式的前缀时会吃错 | 本轮 `all()::get` 把 `all()::getKey` 啃成 `byIdKey`；**先替长串或加边界** | API 文档搜 `前缀匹配` |
| ★★ **两个「排除」实验都失败了（实测）**：`excluded-wip` 移出 ⇒ **+758**；`**/client/**` 排除 ⇒ **+263**（`找不到符号` +402）| **排除路线关闭，只能逐个修** | API 文档搜 `排除路线` |
| ★★ **错误分布实测**（739 去重）：客户端类名 **254（34%）**、`excluded-wip` **184（25%）**、其余 **294**；**最大单文件仅 17 条** ⇒ 已无「单一上游」大鱼 | —— | API 文档搜 `错误分布` |
| ★★ **`GuiGraphics.pose()` 是 JOML 的 `Matrix3x2fStack`**：3D 的 `pushPose/popPose` 要换成 **`pushMatrix/popMatrix`**；`translate/scale/rotate` 都是 2D 版 | **−6**（`找不到符号` −12）| API 文档搜 `Matrix3x2fStack` |
| ★★ **输入架构全改成事件对象**：`keyPressed(int,int,int)` → **`keyPressed(KeyEvent)`**（`key()/scancode()/modifiers()`）、`charTyped(char,int)` → **`charTyped(CharacterEvent)`**（`codepoint()/modifiers()`）| **−5**；同样是**局部别名法** | API 文档搜 `KeyEvent` |
| ★ **`Lighting.setupForFlatItems/3DItems` 无替代**（只剩 `updateLevel/setupFor/close`）| 删独占行语句 ⇒ **−2** | API 文档搜 `Lighting` |
| ★ **`RenderType.guiTextHighlight()` → `RenderPipelines.GUI_TEXT_HIGHLIGHT`**（1 处）| −1；`fill(RenderPipeline,int×5)` 正好 6 参 | API 文档搜 `GUI_TEXT_HIGHLIGHT` |
| ⚠ **`onRemove` 不能机械迁移**：已被 `affectNeighborsAfterRemoval(BlockState,ServerLevel,BlockPos,boolean)` 取代，**少了 newState** —— 8 处体全用到它 ⇒ 闸门全跳过 | 需重新设计 | API 文档搜 `onRemove` |
| ⚠ **`SimpleSubLevelGroupRenderer`(16 条) 属 render-state 重写**（`RenderSystem` 旧状态 + `Lighting.setupLevel` + `LevelRenderer.renderEntity` 全没了）| 不是脚本活 | API 文档搜 `render-state 重写` |
| ★★ **分析工具：按 (符号, 位置类型) 分组** —— 同接收者的才是同一族（规则36 的正解）| `analyze_symloc.py`；592 条 → **236 个可执行组合** | API 文档搜 `符号位置分组` |
| ⚠⚠ **影子类只能加「方法」，不能加「状态」**：垫片 `BlockBuilder` 的 name 存在 jar 私有字段里，项目 `AbstractBuilder` 影子无参构造、不存东西 ⇒ `getName()` 无法返回真名 | `getName`(8)+`getOwner`(4) 改不动 | API 文档搜 `影子类边界` |
| ⚠ **`ValueInput/ValueOutput` 的 list 族(12) 不是快活**：值来自返回 NBT 的 helper（`VecHelper.writeNBT`/`saveKeys`/`readKeys`）⇒ 要连 helper 层改成 codec | 暂缓 | API 文档搜 `valueio list` |
| ⚠ **`ProviderType.BLOCK_TAGS/ITEM_TAGS`(8) 有类型冲突**：`AeroTags.genItemTags` 要 `RegistrateItemTagsProvider`、`SimTags.genItemTags` 要 `RegistrateTagsProvider<Item>` ⇒ 泛型不协变，**一个静态字段满足不了两者** | 只能改调用点 | API 文档搜 `ProviderType` |
| ★ **`pose().translate(x,y,z)` → `translate(x,y)`**（3 处）| **−3**（`float无法转换为Matrix3x2f` 4→0）| API 文档搜 `translate 2D` |
| ⚠⚠ **`PoseStack ps = gui.pose()` 的声明类型不能单独改**：实测 **+78**（`找不到符号` +114）—— 后面所有 `ps.pushPose/scale/mulPose` 在 `Matrix3x2fStack` 上都没有 | 必须与全部使用点一起改 | API 文档搜 `声明类型不能单独改` |


<!-- ===== 从热层搬来的较早族行（20261017-104255）===== -->

| 族 | 结论 |
|---|---|
| ★ **`AbstractLaserBlockEntity` 的笔误**：类里定义 `getNormal()`，却调 `this.getUnitVec3i()` | 改 2 处 ⇒ **−2**（不是 API 变更！）| —— |
| ✓ **`Direction.getUnitVec3i()` 仍然存在**（javap 确认），别被报错误导 | —— | —— |
| ★★ **Create 的 behaviour 有 `Server*` 变体**：`ServerBrassDiodeScrollValueBehaviour`、`ServerScrollValueBehaviour` …… | 项目继承 client 版就丢 server 方法；换父类 = 一组动作 | API 文档搜 `Server* 变体` |
| 工具 **`find_typos.py`**：找「缺失方法 X 在同文件有近义名」的笔误 | 启发式偏松（多假阳性），但能捞出真货 | 项目根目录 |
| ★★ **Create `ConfigBase` 已删 `specification` 字段**（只剩 depth/allValues/children）| `config.specification = pair.getRight()` 改局部变量 ⇒ **−5**（`找不到符号` −8）| API 文档搜 `ConfigBase specification` |
| ✓ **「继承错版」已扫完**：项目 `extends` 里**没有**其它该用 `Server*` 变体的（Create 有 25 个 Server* 类）| —— | —— |
| ⚠⚠ **删掉「多余」的调用会破坏类型推断**：`displaySource(...)` 已返回 `RegistryEntry`，但删 `.register()` 后 T 推不出来（`推论变量T#1…DisplaySource,T#2` +4）| 净 0，已回滚 | API 文档搜 `删调用破坏推断` |
| ⚠ **`displaySource(...)` 返回 RegistryEntry，而 `displayTarget(...)` 返回 builder** —— 名字像，行为不同 | 规则 36 的又一例 | API 文档搜 `displaySource/displayTarget` |
| ⚠ **`RenderStateShard` 已从 MC jar 删除**（javap 找不到）| 6 条需 pipeline 重写，属设计 | API 文档搜 `RenderStateShard` |
| ★★ **`ScrollOptionBehaviour` 也有 client/server 两版**：`ServerScrollOptionBehaviour`。3 个文件只**用它**（不继承）⇒ 换 import+标识符 ⇒ **−8**（`找不到符号` −16、抽象类错 6→0）| API 文档搜 `ServerScrollOptionBehaviour` |
| ⚠ **`ServerScrollValueBehaviour.value` 是 protected** ⇒ `X.value = N;` 要改 `X.setValue(N);`；**但正则别写宽**（会打到 `value == 1 ?` 比较式和普通字段）| 精确改 2 处 ⇒ −2 | API 文档搜 `value 是 protected` |
| ★★★ **工具 `enum_cs_pairs.py`**：枚举 Create Fly **全部 12 对** 同名 client/server 类，再查项目 import 了哪一版 | 一次找出 **5 处**错用（LinkBehaviour / FilteringBehaviour / BrassDiodeScrollValueBehaviour）⇒ **−4**（`找不到符号` −10）| API 文档搜 `enum_cs_pairs` |
| ⚠ **`Server*` 版构造器普遍更少参数**：`ServerFilteringBehaviour(SmartBlockEntity)` 只 1 参（旧客户端版是 2 参）| 换版后要同时去掉多余实参 | API 文档搜 `Server* 构造器更少参` |
| ★★ **工具 `scan_missing_imports.py`**：扫「项目 import 了但 jar 里没有」的 FQN | 17 个里只有 **3 个真缺类**（都在 `item.render` 包）；其余是**静态字段/方法导入**（假阳性，类集不含字段）| API 文档搜 `缺类扫描` |
| ⚠ **`com.zurrtum.create.foundation.item.render` 整包已消失**（Create Fly 里 0 个类）| `CustomRenderedItemModel`/`CustomRenderedItemModelRenderer`/`PartialItemModelRenderer` ⇒ 约 12 条，属物品渲染重写 | API 文档搜 `item.render 整包消失` |


<!-- ===== 从热层搬来的较早族行（20261017-105018）===== -->

| 族 | 结论 |
|---|---|
| ★★★ **`src/_stub_bak_20261017-050135/` 里有前任写好的 131 个桩** —— **但对纯客户端/装饰类才可用**（方块实体的桩会掏空玩法）| 用它换掉 2 个物品渲染器 ⇒ **−18** | API 文档搜 `_stub_bak` |
| ⚠ **`src/excluded-wip/` 与 `_stub_bak_*` 是两套方案**：前者是「真源码」（在编译），后者是「打桩备份」（不在编译）；混用会二次踩坑 | —— | —— |
| ★★★ **63 个装饰性类换桩 ⇒ −81**（`找不到符号` −84、`方法不会覆盖` −38，零新增）| 代价：这些渲染器/Visual **不再绘制**（方块与实体仍在）| API 文档搜 `63 个装饰性类换桩` |
| ⚠ **`_stub_bak` 的边界**：装饰性（Renderer/Visual/Shader/Effect/Region/Particle/Model）可用；**方块实体一律不能换** | —— | API 文档搜 `_stub_bak 边界` |
| ⚠⚠ **打桩必须保留「别人引用的嵌套类型」**：R118 把 `RopeStrandRenderer` 换成 5 行桩，但 `RopeStrandElement` 用它的嵌套 `record RopeRenderPoint` ⇒ 16 条错误（R118 真实净收益是 −97 不是 −81）| 从 `.bak` 取回一行 record 补进桩 ⇒ **−8** | API 文档搜 `桩要留嵌套类` |
| ★★ **工具 `check_stub_nested.py`**：以 `.bak-r134` 备份为权威清单，检查打桩类**有没有被别处引用的嵌套成员而桩里没写** | 63 个桩里只有 **2 个**有问题（其余 61 健康）⇒ 补回 ⇒ **−7** | API 文档搜 `check_stub_nested` |
| ★ **`Tag.TAG_ANY_NUMERIC` 已删除**（13 个类型常量都在，唯独没有它）⇒ 改写为 `tag.read(k, Codec.INT).orElse(...)` / `.isPresent()`；注意 `ValueInput` 也**没有 `contains`** | 2 处 ⇒ **−2** | API 文档搜 `TAG_ANY_NUMERIC` |
| ★ **垫片加方法要看 lambda 参数个数**：`directionalAxisBlock` 的 lambda 是 `(blockState, vertical)`⇒ 必须收 `BiFunction`（`Object...`/`Function` 都接不住）| 加进 BlockStateGen 垫片 ⇒ **−3** | API 文档搜 `BiFunction 垫片` |


<!-- ===== 从热层搬来的较早族行（20261017-105618）===== -->

| 族 | 结论 |
|---|---|
| ★ **指向不存在 mod 的 `addOptional` 直接删**：`naturescompass`/`explorerscompass` 标签在 FC 1.21.11 上无意义（原版 `TagAppender.addOptional` 只收 `TagKey`）| 删 2 行 ⇒ **−2** | API 文档搜 `addOptional` |
| ★★ **`ValueInput/ValueOutput` 没有 `put(String,Tag)`/`getListOrEmpty`/`getList`** ⇒ 改用 **codec**：`tag.put(k, Vec3.CODEC, v)` / `tag.read(k, Vec3.CODEC).orElse(默认)`；原版自带 `Vec3.CODEC`；写方法的参数类型要从 `ValueInput` 改 `ValueOutput` | NavTable+LaserPointer ⇒ **−4**；**NBT 结构变了（旧存档读不出）** | API 文档搜 `ValueInput codec` |
| ★★ **整文件依赖 Veil 的渲染器直接打桩**：`EndSeaRenderer` 用 `VeilRenderSystem`/`AdvancedFbo`/`ShaderProgram` ⇒ 运行期必 `NoClassDefFoundError`；全项目只被 2 个静态方法引用 | 手写 20 行桩 ⇒ **−7**（`找不到符号` −12），**同时推进清 Veil** | API 文档搜 `EndSeaRenderer 打桩` |
| ★★★ **Veil 依赖面已测绘**：88 个文件 import `foundry.veil`，其中 **~80 个是网络层**（已有 4 个垫片 ✓，不是问题）；**真缺口 36 处导入**，大头是 `RegistrationProvider`(7)/`RegistryObject`(6)/`VeilRenderLevelStageEvent`(4)/`Color`(3) | **这是运行期缺口，不是编译错误源**（Veil 在 classpath 上能解析）| API 文档搜 `Veil 依赖面` |
| ⚠⚠ **`BlockBuilder.getName()`/`getOwner()` 在垫片层无解**（已复核，别再试）：它们在 `NonNullUnaryOperator<BlockBuilder<B,P>>` **里面**用，名字/owner 只有调用者知道；阴影类不能存状态，改成传参又波及所有 `setImpact(...)` 调用点 | 12 条暂挂 | API 文档搜 `getName 无解` |
| ★★★ **`excluded-wip` 结构普查**：131 文件**全都有同名桩**，但 A 装饰性 65 个**已换完（0 错误）**；**B 方块实体 43 个 / 168 条**（不能换）；**C 注册与 datagen 23 个 / 134 条**（换桩=没有方块）。**`excluded-wip` 独占 302/573（53%）** | 没有捷径，只能逐族修 | API 文档搜 `excluded-wip 普查` |
| ⚠ **`p.dropOther(...)` 报「类型为 Object 的变量 p」的根因**：jar 垫片里 `BlockBuilder.loot(...)` 的函数式参数是 `Object` ⇒ lambda 里 `p` 就是 Object ⇒ 里面**每个调用都失败**；**改不动**（要影子整个 BlockBuilder）| 只能逐点强转 | API 文档搜 `loot 的 Object` |


<!-- ===== 从热层搬来的较早族行（20261017-110529）===== -->

| 族 | 结论 |
|---|---|
| ★★ **`SimBlocks` 分诊完成（28 条 = 9 族）**：根因多半是 **jar 垫片 `loot(NonNullBiConsumer<?, ? super T>)` 的第一个类型参数无界** ⇒ lambda 里 `p` 只能是 `Object`；而垫片的 `RegistrateBlockLootTables` **只有 `dropSelf`** ⇒ `dropOther`/`createSingleItemTable` **强转也没用**，得往垫片加方法 | 详见 API 文档 | API 文档搜 `SimBlocks 分诊` |
| ★★ **给 `p` 加「显式 lambda 参数类型」比强转干净**：`(p, b) -> p.dropOther(..)` 改成 `(RegistrateBlockLootTables p, Block b) -> p.dropOther(..)`；并已重建影子 `RegistrateBlockLootTables`（原垫片只有 `dropSelf`，补了 dropOther×2/createSingleItemTable×2/axeOnly）| 2 处 ⇒ **−1**；其余 `p.xxx()` 的 lambda 写法不同，需另找 | API 文档搜 `显式 lambda 参数类型` |
| ★★ **「缺方法」先看调用形态，别信分诊表的猜测**：分诊时我猜 `axeOnly()` 是 `p.axeOnly()`（要改 `b.`），实际是 **`.transform(axeOnly())`** —— 需要的是 `TagGen` 垫片里的**静态算子**（照 `pickaxeOnly()` 补 `builder -> builder`）| 2 处 ⇒ **−2** | API 文档搜 `先看调用形态` |
| ★★★ **本项目映射里 `ResourceLocation` 叫 `Identifier`**（`Identifier.fromNamespaceAndPath(ns, path)`）；`Create.asResource(p)` → `Identifier.fromNamespaceAndPath("create", p)` | 2 处 ⇒ **−2** | API 文档搜 `Identifier` |


<!-- ===== 从热层搬来的较早族行（20261017-110950）===== -->

| 族 | 结论 |
|---|---|
| ★★★ **替换后总数「一点没动」= 自己引入了等量新错误**，不是「没生效」：本轮用 `ResourceLocation` 换掉 `Create.asResource`，总数 569→569 ⇒ 查直方图发现新增 3 条「找不到符号 类 ResourceLocation」 | 改成 `Identifier` 后 −2 | 硬规则 54 |
| ★★ **datagen 专属的 `.transform(...)`/`.blockstate(...)` 行可以直接删**（独立一行，删了不影响链）；**垫片加 `forPowered(c,p)` 返回 `Function<BlockState,Object>`** | SimBlocks 20→**14**（−6）| API 文档搜 `datagen 行可删` |
| ⚠⚠ **`无法访问class_2248` 已定位：`create-fly-helpers-shim.jar` 没被 remap** —— 字节扫描发现该 jar 有 **5 个类**（`TagGen`/`BuilderTransformers`/`CreateRegistrate`/`SharedProperties`/`ItemUseOverrides`）的签名里带 Mojang 混淆名 `class_2248`（= `Block`）。**这不是源码问题，改代码修不掉** | 需 remap 该 jar 或在 `src/stub` 影子这 5 个类 | API 文档搜 `class_2248` |
| ⚠⚠⚠ **`CreateRegistrate` 影子法【已证伪，别再试】**：带继承的版本（`extends AbstractRegistrate<>`）仍然是 `找不到符号` **+204** —— 逐条看「位置」发现 **208 条是「类型为 `SimulatedRegistrate` 的变量 `REGISTRATE`」** ⇒ 缺的方法在 **`CreateRegistrate` 自己身上**（不在 `AbstractRegistrate` 里），影子必然丢一大片 | **根治只能 remap `create-fly-helpers-shim.jar`**；4 条 `class_2248` 暂挂 | API 文档搜 `class_2248` |
| ★★★ **`addToTooltip` 已解：接口的 `default` 方法才是关键** ✗ —— `IHaveGoggleInformation`（在 **`client.api.goggles`**）把 `addToGoggleTooltip` 声明为 **`default`** ⇒ 给那 2 个类加 `implements IHaveGoggleInformation` + 改用 **`IHaveGoggleInformation.super.addToGoggleTooltip(...)`** ⇒ `找不到符号` −4、`方法不会覆盖` −4 | **−4** | API 文档搜 `addToTooltip` |
| ⚠ **`Matrix3x2fStack.last()`(4) 是 2D→3D 失配**：`pose().last().pose()` 要从 2D 栈拿 `Matrix4f`，新版 2D 栈只有 2D ⇒ 整段 vertex 变换要重写 | 跳过 | —— |
| ★★★ **174 条「方法不会覆盖」已聚合**（用项目里现成的 `analyze_override3.py`，它读源码取签名）：**`rotate` 12** / `render`·`getMetaFactory`·`getCodec`·`getStreamCodec` 各 10 / `save`·`neighborChanged` 各 8 / `fallOn`·`getLocalOffset`·`streamCodec` 各 6。**其中约 44 条是幻影族**（`getCodec`/`getStreamCodec`/`getMetaFactory`/`fallOn`/`streamCodec`/`readAdditionalSaveData`，真因在别处）⇒ **真实目标：`rotate`(12)、`save`(8)、`neighborChanged`(8)** | API 文档搜 `174 条聚合` |
| ★★ **`neighborChanged` 已解（−8）**：新签名第 5 参是 **`Orientation`**（`net.minecraft.world.level.redstone.Orientation`），**不是 `BlockPos`**；大部分文件早就改好了，只剩 4 个还写 `final BlockPos fromPos` ⇒ 只改**参数类型**即可（体不动，配方 a）| `方法不会覆盖` 174→166 | API 文档搜 `neighborChanged` |
| ⚠ **我又违反了自定的「先看签名」规矩**：第一次按猜的 5 参全签名写正则，**12 个文件一个没中**；读了真实声明行后 4 个文件一次过 | —— | —— |


<!-- ===== 从热层搬来的较早族行（20261017-111347）===== -->

| 族 | 结论 |
|---|---|
| ⚠ **`rotate`(12) 不能按原版签名改**：原版 `BlockBehaviour.rotate` 是 **`(BlockState, Rotation)`**；项目里的 `rotate` 是**两种别的形状**（`(LevelAccessor,BlockPos,BlockState,PoseStack)` 4 参 / `(BlockState,PoseStack)` 2 参）⇒ **它们覆盖的不是原版那个** ⇒ 得先查出真正的父接口 | 暂挂 | API 文档搜 `rotate` |
| ⚠ **进度进入平台期**：R143→R144 一直卡在 **549** 附近；剩余 549 条里 `方法不会覆盖` 166 条、`找不到符号` 358 条，且大量是**设计级/需逐文件读码**的 | 见下 | —— |
| ★★★ **`ComputerCraftPeripherals` 13 条 = 一族**：`src/stub` 里**前任已有一整套 `dan200.computercraft.api.*` 桩**，所以报错不是「缺 CC」，而是**桩与代码类型不匹配** —— `SimPeripheralService.addPeripheral/addWired` 收 `Supplier<BlockEntityType<T>>`，而项目传 `BlockEntityEntry<T>` ⇒ 改**项目接口的参数类型**（4 处）| **−13**（raw −26）| API 文档搜 `CC 桩` |
| ★★ **逐文件推进的第一次就见效**：按文件排错误数，第一名 `DiagramScreen`(30)/`ComputerCraftPeripherals`(26)/`GimbalSensorBlockEntity`(26) —— 挑 CC 那个，因为它**单族**、改一处接口就全清 | —— | —— |
| ★★★ **`Create.ID` 的正确替代是 `Create.MOD_ID`**（javap 确认 `Create.MOD_ID`/`NAME`/`LOGGER` 都在）；`tag.get(k)` 取 CompoundTag ⇒ `tag.read(k, CompoundTag.CODEC).orElse(null)`（原版自带该 codec）；**注意 `Create.AllItems/AllBlocks/...` 在 `Create` 上不存在**（那是包名，别被大小写不敏感的搜索骗了）| R146 已改 1 处 | API 文档搜 `Create.ID` |


<!-- ===== 从热层搬来的较早族行（20261017-111750）===== -->

| 族 | 结论 |
|---|---|
| ⚠ **`save`(8) 属设计级**：`SavedData.save(CompoundTag, HolderLookup.Provider)` 在 1.21.11 已无 `save`；新版是 **`SavedDataType`（record，需要 `Codec<T>`）+ `save(ValueOutput)`** ⇒ 与 `SavedData.Factory`(4) 同族，**要连 Factory 一起换**，改动量 = 重写存档层 | 暂挂 | API 文档搜 `SavedData` |
| ⚠ **逐文件打法要挑「单族占多数」的文件**：`GimbalSensorBlockEntity`(13 条) 是**混合族**，只捞到 2 条便宜的，收益远低于 `ComputerCraftPeripherals`(13 条=1 族) | —— | —— |
| ★★★ **`ResourceKey.location()` → `identifier()`**（10 条）：javap `ResourceKey` 只有 `identifier()`/`registry()`/`registryKey()`，**没有 `location()`**（与 `ResourceLocation`→`Identifier` 一致）；靶向改 3 种写法（`.get().location()` / `WorldPresets.X.location()` / `key.location()`）| 4 处 ⇒ **−4** | API 文档搜 `ResourceKey.identifier` |
| ★★ **符号普查结论（显式区分大小写）**：138 个不同符号 / 362 条，**分布很平（最大 10 条）** ⇒ **已无大族可批量**；`方法 location()` 10 / `类 Factory` 8 / `blockUpdated` 8 / `getName()` 8 / `register()` 6 / `onRemove` 6 / `put(String,ListTag)` 6 / `bufferSource()` 6… | —— | API 文档搜 `符号普查` |
| ★ **`SoundEvent.location()` 其实存在**（`public Identifier location()`）—— 报错的位置是 **`SoundEntry`**（Create 的 `AllSoundEvents$SoundEntry` record），它**没有 `location()`**，但有 **`getMainEvent()`** ⇒ `soundEntry.location()` → `soundEntry.getMainEvent().location()` | 1 处 ⇒ **−1** | API 文档搜 `SoundEntry` |


<!-- ===== 从热层搬来的较早族行（20261017-112023）===== -->

| 族 | 结论 |
|---|---|
| ★★★ **做决策要用「符号 + 位置」配对表**（151 组），不要只看符号：PowerShell 里正则在 `符号:` 行后往下找 `位置:` 行即可。这样一眼能分出「项目/垫片类（可补方法）」与「外部类（要换 API）」 | —— | API 文档搜 `符号位置配对` |
| ★★ **`AssetLookup` 垫片可以无限加 `Object` 形态的静态工厂**：`itemModelWithPartials()` 照 `customItemModel()` 的 `public static Object xxx() { return null; }` 加进去即可（`.model(...)` 有 Object 重载）| 4 条 ⇒ **−2** | API 文档搜 `AssetLookup 补方法` |
| ★★ **`Level.blockUpdated` 已删除** ⇒ 替代是 **`Level.updateNeighborsAt(BlockPos, Block, Orientation)`**（又是 `Orientation`！）| 4 处 ⇒ **−4**（`找不到符号` −8）| API 文档搜 `blockUpdated` |
| ⚠⚠ **跨行调用的正则必须用 DOTALL**：`this.level.blockUpdated(a, b` 换行 `.getBlock());` —— `[^;]*?` 截断会吃掉闭括号（+8 新错），`[^,]+?` 精确版匹配 0 个；**`([\s\S]*?)` 才中** | 实测 3 次才对上 | API 文档搜 `跨行正则` |
| ★★ **`ProviderType.BLOCK_TAGS/ITEM_TAGS`(8) 已解**：4 处 `addDataGenerator(ProviderType.X, X::genXxx)` 是**datagen 专属的独立语句**，而泛型不协变（`RegistrateItemTagsProvider` vs `RegistrateTagsProvider<Item>`）⇒ 一个静态字段满足不了两个调用点 ⇒ **直接删这 4 行**（功能削减：两个 mod 的方块/物品标签 datagen 不再生成）| 4 行 ⇒ **−4**（`找不到符号` −8）| API 文档搜 `ProviderType 删行` |


---

## 索引原始长行（R162-b 从热层搬出，逐字保留）

| ★★ **`CatnipStreamCodecs.VEC3` → `Vec3.STREAM_CODEC`**：原版自带 `Vec3.STREAM_CODEC`（还有 `Vec3.CODEC`），R124 就验证过 | 2 处 ⇒ **−2**（`找不到符号` −4）| API 文档搜 `Vec3.STREAM_CODEC` |
| ★★ **`TypedEntityData` 是【原版】类**（`net.minecraft.world.item.component.TypedEntityData`，不是 Create 的）；`copyTag()` 已删 ⇒ 用 **`copyTagWithoutId()`**（含 id 用 `getUnsafe()`）| 2 处 ⇒ **−2**（`找不到符号` −4）| API 文档搜 `TypedEntityData` |
| ★★★ **「只有一个构造器」的垫片类是理想影子目标**：`RegistrateLangProvider` 在 registrate 垫片里**只有一个构造器**（javap 实测），而项目用了 `provider::add`（方法引用）和 `toEnglishName(...)` ⇒ 在 `src/stub` 重建该类（1 个构造器 + `add(String,String)` + `add(String,String,Object...)` + `toEnglishName(String)`）| `方法引用无效` 8→4、总 **−2** | API 文档搜 `单构造器垫片` |
| ⚠ **`GuiGraphics.bufferSource()`(6) 属设计级**：1.21.11 的 `GuiGraphics` 构造器是 `GuiGraphics(Minecraft, **GuiRenderState**, int, int)`，**没有任何 buffer 方法**（javap 证实）⇒ 自定义批次绘制要改走 `GuiRenderState`/`fill(RenderPipeline,…)` 那条路，属 GUI 渲染重写 | 暂挂 | API 文档搜 `GuiRenderState` |
| ★★ **Create 的 `ItemStackHandler` 没有 `getStackInSlot`**：它在 `com.zurrtum.create.infrastructure.items`（**Create Fly**，不在任何 libs jar 也不在 src/stub），方法名是 **`getItem(int)`** / `setItem(int, ItemStack)` / `getContainerSize()` / `getStacks()` | 2 处 ⇒ **−2**（`找不到符号` −4）| API 文档搜 `getStackInSlot` |
| ★★ **找不到某个类型时，先读 `import` 行**：本轮我扫遍 `libs/*.jar` 和 `src/stub` 都没找到 `ItemStackHandler`，最后是 `LinkedTypewriterMenuImpl` 的 import 直接给出了 `com.zurrtum.create.infrastructure.items` | —— | —— |
| ⚠⚠ **`getGameRules`(2) 属设计级**：`Level.getGameRules()` 不存在（只在 `ServerLevel` 上），而且那两处**同时**用了 `GameRules.RULE_DOBLOCKDROPS` / `RULE_DOENTITYDROPS`（也已删，gamerule 数据驱动化）⇒ 补 `ServerLevel` 守卫也修不好 ⇒ 与 `RULE_DOBLOCKDROPS`(6) 一起暂挂 | 8 条暂挂 | API 文档搜 `getGameRules` |
| ⚠ **`DeferredHolder` 影子已加但【净 0】**：垫片类有 `private final Identifier id` + private 构造器 + `create(...)`，我在 `src/stub` 复现了它并补了 `getId()` —— 编译**没变化**（parse 0，未破坏）⇒ 那 2 条 `方法引用无效` 另有原因（很可能是 `withKeyFunction` 的**函数式接口类型**对不上，不是缺 getter）| 待查 | API 文档搜 `DeferredHolder` |
| ★★ **`NbtUtils.loadUUID` 还在、`createUUID` 没了**（不对称！）：把 `UUID → Tag` 要自己写 —— `.map(u -> new IntArrayTag(UUIDUtil.uuidToIntArray(u)))`（`ListTag.addAll` 需要 `Tag`）| 1 处 ⇒ **−1** | API 文档搜 `createUUID` |
| ⚠⚠ **`NbtUtils.loadUUID` 也没了[已证]**：2 条报「方法 loadUUID(Tag)」，但改成 `UUIDUtil.readUUID(...)` **净 0**（−1/+1）⇒ `readUUID(Dynamic<?>)` **不能直接吃 `Tag`**，得自己 `tag.getString(...)` 或转 `Dynamic` 再读。**别再试直接换** | 2 条待设计 | API 文档搜 `loadUUID` |
| ★★ **符号普查已彻底摊平**：141 组，**最大只有 8 条**（`getName()`/`onRemove`）；4 条一档的全是已定性无解（`last`/`getOwner`/`bufferSource`/`register`/`Factory`/`addVariantTo`）⇒ **机械族已彻底打完** | —— | —— |
| ⚠ **`EndSeaShadowRenderer::renderShadowMap` 有两个问题**：① 我 R126 的桩里**没这个方法**；② 它的宿主 `VeilEventPlatform` **本身也没桩**（在 Veil 缺口清单里）⇒ 单独补桩救不了这一行 | 暂挂 | API 文档搜 `renderShadowMap` |
| ⚠⚠ **`xxxTo(A)` → `xxx(A, B)` 是【加参数】，不是改名**：`EncasingRegistry.addVariantTo(ShaftBlock)` 一参，而新 API 是 `addVariant(B, E)` **两参**（`<B extends Block & EncasableBlock, E extends Block & EncasedBlock, P>`）⇒ 直接改名会报「无法应用」(+4)；**必须补第二个参数（= 被包覆的方块）** | 已回滚，暂挂 | API 文档搜 `addVariant` |
| ⚠ **javap 输出默认会截断长签名**：`... <B extends ... , E extends ...` 后面被切掉，看不见参数表 ⇒ **要单独打印目标那一行**（本轮就是这么才发现 `addVariant` 是两参）| —— | —— |


---

## R163（510 → 508，**−2**）：换挡到「逐文件」，第一次见效

### 新的按文件排行（186 个文件 / 1,018 条 raw）
```
30  DiagramScreen         22  GimbalSensorBlockEntity   22  DiagramEntity
16  GustParticleData      16  SteeringWheelBlockEntity  16  SwivelBearingBlockEntity
16  GustParticle          16  EndSeaFadeTransformer     14  AeroBlocks / SimBlocks
14  HoneyGlueEntity       14  RopeStrandHolderBehavior  14  PortableEngineBlockEntity
```
**⇒ 屏幕类（`DiagramScreen`）大概率含设计级（`Matrix3x2fStack`/`bufferSource`）⇒ 先跳过；
方块实体类更容易是"少数 API 重复"⇒ 优先。**

### 本轮：`SwivelBearingBlockEntity`（8 条 unique，混合）
从中挑出两个明确的：

**(1) `UUIDUtil.CODEC` 存在（字段！）**
```
public static final Codec<UUID> CODEC;
public static final Codec<Set<UUID>> CODEC_SET; CODEC_LINKED_SET;
public static final Codec<UUID> STRING_CODEC; AUTHLIB_CODEC; LENIENT_CODEC;
public static final StreamCodec<ByteBuf, UUID> STREAM_CODEC;
```

**(2) `ValueInput` 没有 `hasUUID`**
```java
if (compound.hasUUID("SubLevelID")) { … }
// →
if (compound.read("SubLevelID", net.minecraft.core.UUIDUtil.CODEC).isPresent()) { … }
```
全项目只有 **2 处**（`SpringBlockEntity:461`、`SwivelBearingBlockEntity:651`）⇒
`找不到符号` **310 → 306（−4）**、总 **−2**，解析期 0。

**(3) 没做的：`addStressImpactStats`**
`IHaveGoggleInformation` javap 只有两个 default 方法（`addToGoggleTooltip` / `containedFluidTooltip`），
**没有 `addStressImpactStats`** ⇒ 它在别的类上，暂时跳过。

### ★ 一条反复踩的工具坑
**javap 结果按 `(` 过滤会漏掉字段。** 我这一轮和之前 R154 都因为
`if '(' in line` 而看不到 `UUIDUtil.CODEC`（还在 R120 误判过一次 `Vec3.CODEC`）。
**⇒ 查"有没有某个常量/codec"时，过滤条件写成：`if 'CODEC' in line or '(' in line`，
或者干脆整段打印、不要筛。**


---

## R164（508 → 507，**−1**）：`writeSafe` 的参数类型

### 症状（一个类型错，连挂 5 条）
```
L246  方法不会覆盖  super.writeSafe(compound, compound.lookup())   [需要: ValueOutput] [找到: ValueInput, Provider]
L248  无法应用      super.writeSafe(...)
L249  找不到符号    方法 store(String,Codec<BlockState>,BlockState)  位置: ValueInput compound
L276  不兼容的类型  ValueInput 无法转换为 CompoundTag
```
看着像 4 个不同问题，**根因只有一个**：
```java
public void writeSafe(final ValueInput compound, final HolderLookup.Provider registries) {  // ← 错
```
`writeSafe` 是**写**，1.21.11 的写入口是 **`ValueOutput`**（`store(...)` 在 `ValueOutput` 上，
`ValueInput` 只有 `read(...)`）。改成 `ValueOutput` 后，`store` / `lookup` / `super.writeSafe` 全部恢复。

### 规律（值得当成一条硬规则用）
| 方法名 | 第一个参数 |
|---|---|
| `read` / `loadAdditional` / `readAdditionalSaveData` | **`ValueInput`** |
| `write` / `writeSafe` / `saveAdditional` / `writeAdditionalSaveData` | **`ValueOutput`** |

**⇒ 见到「`store` 找不到」「`ValueInput` 无法转换为 X」这类连带错误，先看那个方法的参数类型，
而不是逐个去修被牵连的调用。**

### 本轮做法
写了个只认**写方法名前缀**的正则（`void (write|writeSafe|writeAdditionalSaveData|saveAdditional)\(…ValueInput)`），
全项目扫一遍 —— 只命中 1 个文件（`SteeringWheelBlockEntity`），说明其他地方早就对了。
⇒ 总 **−1**（raw −2），解析期 0。


---

## R165（净 0）：`ListTag` 没有 `CODEC`，结构列表必须换 API

### 更好的定位手法（本轮新增）
按 **`文件 ×（错误消息 + 符号）`** 交叉统计，找"**单文件里同一条重复**"：
```
6x  RopeStrandHolderBehavior :: RULE_DOBLOCKDROPS          （设计级）
4x  AeroBlocks :: addVariantTo(ShaftBlock)                 （要补第二参）
4x  SimStress :: getName()   +  4x AeroStress :: getName() （共 8）
4x  LinkedTypewriterBlockEntity :: put(String,ListTag)     ┐
4x  LinkedTypewriterBlockEntity :: getList(String,int)     ┘ 共 8，同一主题
4x  DiagramScreen :: last()                                （设计级）
```
**⇒ "一个文件的 8 条错误是同一件事" 才是真正值得打的靶子**，比按文件总数排序准。

### 打的靶子：`LinkedTypewriterBlockEntity`（8 条，同一主题）
```java
protected void write(final ValueOutput tag, …) { tag.put("Keys", this.entryMap.saveKeys(…)); }
protected void read (final ValueInput  tag, …) { … this.entryMap = readKeys(tag.lookup(), tag.getList("Keys", 10), pos); }
```
尝试：`put` → `store(k, ListTag.CODEC, v)`，`getList(k,10)` → `read(k, ListTag.CODEC).orElseGet(ListTag::new)`
**⇒ 净 0（−4/+4）⇒ 回滚。**

**原因**：javap `ListTag` **没有任何 `CODEC`**：
```java
private static final String WRAPPER_MARKER;
private static final int SELF_SIZE_IN_BYTES;
public static final TagType<ListTag> TYPE;     // ← 只有这个
```

### 1.21.11 真正给的结构列表 API
```java
// ValueOutput
ValueOutputList childrenList(String);
<T> TypedOutputList<T> list(String, Codec<T>);
// ValueInput
Optional<ValueInputList> childrenList(String);
ValueInputList childrenListOrEmpty(String);
<T> Optional<TypedInputList<T>> list(String, Codec<T>);
<T> TypedInputList<T> listOrEmpty(String, Codec<T>);
```
**没有"无类型 ListTag"这条路** ⇒ 要把这 8 条修掉，得把项目自己的
`LinkedTypewriterEntries.saveKeys/readKeys` 从 `ListTag` 改成 **child-list** 接口 ⇒ **设计级**。

### 顺带发现（下轮可打）
同文件里 `AttachedComputerHandler.queueEvent(String,int,boolean)` / `queueEvent(String,int)`
报"找不到符号" ⇒ **CC 垫片缺 `queueEvent`** ⇒ **可以补**（垫片类，成本低）。


---

## R166（507 → 505，**−2**）：给自家垫片补 `queueEvent`

### 现场
```
LinkedTypewriterBlockEntity.java:219  this.computerHandler.queueEvent("key", key, this.entryMap.getEntry(key).isAlive());
LinkedTypewriterBlockEntity.java:231  this.computerHandler.queueEvent("key_up", key);
```
`AttachedComputerHandler` 是**我们自己的桩**（`src/stub/.../fabric/cc/`），原本 4 个成员：
```java
public AttachedComputerHandler(Object... args) {}
public void prepareComputerEvent(Object event) {}
public boolean isAttached() { return false; }
public void remove() {}
```
**没有 `queueEvent`。**

### 做法
加一个 **varargs** 方法，一次覆盖两种调用：
```java
public void queueEvent(String name, Object... args) {}
```
⇒ `找不到符号` **306 → 302（−4）**、总 **−2**，解析期 0。

### ★ 一个应当前置的判断
**"这个类是不是我们自己的桩？"** —— 如果是（在 `src/stub/` 下），
缺成员就是**一行的事**；如果不在，才需要查新版 API。
本轮就是靠这一条，用 5 分钟换来 −2，而不是再去翻 javap。

### 顺带排除：`SimStress` / `AeroStress` 的 `getName()`（8 条）
```java
DEFAULT_IMPACTS.put(Simulated.path(builder.getName()), value);
```
接收者是 **`BlockBuilder<B,P>`** —— 这是**已定性无解**的那一族（`getName()`/`getOwner()` 在
`NonNullUnaryOperator<BlockBuilder<B,P>>` 里，名字只有上游知道）。
而且这两个文件还叠着 `@Override` 报错与 `ConfigValue<T>` / `DoubleRawValue` 类型不匹配 ⇒ **混合+设计级，跳过。**


---

## R167（505 → 499，**−6**）：系统扫桩法

### 方法（可复用）
```
1. 收集 src/stub/java 下所有 *.java 的类名（本轮 58 个）
2. 读编译日志，配对每一处「符号:」与它后面的「位置:」
3. 只保留「位置字符串里出现了某个桩类名」的条目
```
结果：**16 条**。每一条的修法都是「给自家桩加个方法」，不需要查任何新版 API。

### 清掉的
| 桩类 | 缺的方法 | 加法 | 效果 |
|---|---|---|---|
| `BlockEntityBuilder` | **`validBlock`（单数）** | 加单数别名 | **−4**（raw −8）|
| `ILevelReaderExtension` | `isAreaLoaded(BlockPos,int)` | `default` 返回 `true` | −1（raw −2）|
| `WiredNode` | `remove()` | `default` 空实现 | −1（raw −2）|

### ★ 三个具体教训

**(1) 单复数不一致**：`BlockEntityBuilder` 桩里本来有
```java
public BlockEntityBuilder<T, P> validBlocks(final BlockEntry<?>... blocks)   // 复数 + varargs
```
而项目调用的是 **`validBlock(SimBlocks.SPRING)`（单数）**。补一个单数别名即可。

**(2) 我的存在性检查被前缀骗了**：
`if 'validBlock' in t` 在 `validBlocks` 里也成立 ⇒ 脚本报「已存在」。
**⇒ 判断方法/字段是否存在，必须用 `re.search(r'\b' + name + r'\s*\(', text)`，不要用 `in`。**

**(3) 接口桩加方法必须 `default`**：
`ILevelReaderExtension` 和 `WiredNode` 都是 `interface`。直接加抽象方法会**破坏所有实现者**
（本项目虽然没有，但规则要立住）。用 `default` 零风险。

### 表里还剩的（下轮）
- `BlockStateGen.simpleBlock(DataGenContext<Block,HotAirBurnerBlock>, RegistrateBlockstateProvider)` — 2 条，datagen
- `LuaFunction.mainThread()` — 2 条，但 `LuaFunction` 在桩里是 **`@interface`**（注解），
  报「方法 mainThread()」说明调用点的接收者其实不是它 ⇒ 位置行可能骗人，需复核


---

## R168（499 → 497，**−2**）：桩缺口清零，工具化

### 1. 把扫桩法做成了脚本 `scan_stub_gap.py`
```
python scan_stub_gap.py <编译日志>
```
它会：① 收集 `src/stub/java` 下全部类名 ② 解析日志把 `符号:` 与 `位置:` 配对
③ 只输出「位置里出现桩类名」的条目，按 (桩类, 符号) 归并并附文件:行。
**以后每轮跑一次即可**，不用再手工写临时脚本。

### 2. 清掉最后 4 条
| 调用 | 缺什么 | 加法 |
|---|---|---|
| `@LuaFunction(mainThread = true)`（`OpticalSensorPeripheral:38`）| 注解**元素** | `boolean mainThread() default false;` |
| `BlockStateGen.simpleBlock(ctx, prov, blockState -> …)`（`AeroBlocks:208`）| 三参重载 | 返回 `Object` 的静态方法（与 `forPowered` 同形）|

⇒ `找不到符号` **290 → 286（−4）**、总 **−2**，解析期 0。

### 3. ✅ 里程碑：桩缺口清零
再跑一次扫描：
```
src/stub 类数 = 58
日志条目 = 992
位置落在桩类上 = 0 条
✅ 没有可补的桩缺口
```
**⇒ 「给自家桩补方法」这条路走完了**（R166–R168 合计 −10）。
剩下的 **497 条不在我们的桩里** —— 它们要么是外部 API 变更，要么是设计级重写。

### ★ 两条新知识
1. **注解也会"缺元素"**：`@interface` 的成员不是方法而是**元素**，同样会报「找不到符号 方法 xxx()」。
   补法就是加一个带 `default` 的元素声明。
2. **datagen 垫片一律加 `Object` 形态重载**：只要调用点能接受 `Object`（`.model(...)` / `.blockstate(...)` 都行），
   返回 `null` 就够 —— 不需要真实现。


---

## R169（497 → 496，**−1**）：`childOrEmpty` 的三副面孔

### API 事实（javap `CompoundTag`）
```java
public Optional<CompoundTag> getCompound(String);
public CompoundTag getCompoundOrEmpty(String);   // ← 有
public ListTag getListOrEmpty(String);           // ← 有
```
而 `childOrEmpty(String)` 是 **`ValueInput`** 的方法。
**⇒ 接收者是 `CompoundTag` 时用 `getCompoundOrEmpty`；是 `ValueInput` 时才用 `childOrEmpty`。**

### 为什么只改了 1 处
`childOrEmpty` 全项目 **11 处**，接收者分三类：
| 接收者 | 例子 | 正确修法 |
|---|---|---|
| `CompoundTag` | `info.nbt().childOrEmpty("Material")`（`PropellerBearing:409`）| **`getCompoundOrEmpty`** ✅ 本轮改了 |
| `ValueInput` | `compound.childOrEmpty("Inventory")`（`AugerShaft:315`）| 本来就对？/ 需 `child(...)` |
| `ValueOutput` | `tag.childOrEmpty("Inventory")`（`DockingConnector:482`）| 另一套 |

**⇒ 接收者不明确时，绝不批量替换**（硬规则 36）。本轮只动**能确定**的 `info.nbt()` 那一处 ⇒ 总 −1。

### 顺带记下两个卡点
- `ServerSpeedProvider.get()`（`PropellerBearing:285`）—— Create 的类，要单独 javap。
- `ValueInput.get("TargetPos")`（`LaunchedPlunger:393`）—— 代码要的是 **`ListTag`**，
  而 **`ListTag` 没有 `CODEC`**（R165 已证）⇒ 与 `LinkedTypewriterBlockEntity` 撞同一堵墙。


---

## R170（净 0）：三件事的结论

### ① `childOrEmpty` 已经清零（上一轮那 1 处就是全部）
我上轮以为有 11 处要改，其实 **11 是"调用点总数"，不是"错误数"**。
重新扫当前日志：`符号: 方法 childOrEmpty(...)` **0 条**。
javap 事实：
```java
// ValueInput
Optional<ValueInput> child(String);      ValueInput childOrEmpty(String);   // ← 有
// ValueOutput
ValueOutput child(String);                                                // ← 没有 childOrEmpty
```
⇒ 只有「接收者是 `CompoundTag` 或 `ValueOutput`」才会报错。

### ② `addVariantTo` 没有等价物（这条线可以封了）
调用形态：
```java
.transform(EncasingRegistry.addVariantTo(AllBlocks.SHAFT))
```
`transform(...)` 需要一个**变换函数**（`BlockEntry` → `BlockEntry`），
而 1.21.11 的 `EncasingRegistry` 只有：
```java
public static <B extends Block & EncasableBlock, E extends Block & EncasedBlock, P> void addVariant(B base, E encased);
public static List<Block> getVariants(Block);
public static void register();
```
`addVariant` 返回 **void**，而且要在**注册时同时**拿到 base 与 encased 两个方块 ——
**不可能再当成"给某个方块加一个 casing 变体"的变换器**。
**⇒ 这 4 条属设计级，别再试改名/加参数。**

### ③ `GameProfile` 只能用 authlib 的 javap
在 `minecraft-merged` 里查 `com.mojang.authlib.GameProfile` **零命中** —— 它在单独的 authlib artifact 里。
`PhysicsStaffDragPacket:41` 的 `GameProfile.getId()`（2 条）要另找 authlib 产物确认。

### 剩余大族的现状（都已在台账定性）
| 族 | 条数 | 状态 |
|---|---|---|
| `RULE_DOBLOCKDROPS` | 6 | gamerule 数据驱动化，设计级 |
| `addVariantTo` | 4 | **无等价物**（本轮确认）|
| `LinkedTypewriter` 的 `getList/put` | 8 | `ListTag` 无 CODEC |
| `SimStress`/`AeroStress` 的 `getName()` | 8 | `BlockBuilder` 无解 |
| `DiagramScreen.last()` | 4 | 2D→3D 失配 |


---

## R171（净 0）：496 条错误的结构画像 —— 后半程该往哪打

### 按「性质 × 文件来源」统计（原始日志 990 条，比例可比）

| 性质 | src/main | excluded-wip | 其它 |
|---|---|---|---|
| `找不到符号` | **208** | 72 | 4 |
| `不兼容的类型` | **156** | 24 | 8 |
| `方法不会覆盖` | **128** | 36 | 2 |
| 其他 | 118 | 58 | 12 |
| `方法应用不到` | **70** | 38 | 0 |
| `未实现抽象方法` | 46 | 8 | 2 |
| **合计** | **726（73%）** | **236（24%）** | 28 |

### 三个决定性结论

**1. "再多排除一些文件"是死路。**
`excluded-wip` 只占 **24%**，而且 R86 早已实测：**把它整个排除反而 +758 条**
（因为 `src/main` 里大量代码引用它）。⇒ 继续往排除方向走没有收益。

**2. 火力应集中在 `src/main` 的「类型/签名」三桶。**
`不兼容的类型`(156) + `方法应用不到`(70) + `未实现抽象方法`(46) = **272 条**。
这三类的共同点：**修法都是"改声明 / 加桩 / 补类型守卫"**，不是重写逻辑。
相比之下 `找不到符号`(208) 里混着大量外部 API 改名（已逐个定性过）。

**3. `未实现抽象方法`(46) 是一个被低估的桶。**
它的形态通常是「接口加了方法、实现类没补」，**补一个空实现即可**，
和 R167 的「给自家桩加方法」是同一类操作，只是对象换成了**项目自己的类**。

### 下一步（按 ROI 排序）
1. `未实现抽象方法` 46 条 —— 逐个补空实现，预期最容易批量。
2. `不兼容的类型` 156 条 —— 多数是 `ValueInput`/`ValueOutput`、`Optional`、泛型推断，属"声明级"。
3. `方法应用不到` 70 条 —— 逐个看真实签名（注意 javap 截断，见 R158）。
4. `找不到符号` 剩下的 —— 优先「我们自己的类」（`scan_stub_gap.py` 已证明外部桩是 0）。


---

## R172（净 0）：一次诚实的更正 —— `未实现抽象方法` 不是新机会

### 本来打算做什么
R171 的决策表里，`未实现抽象方法` 有 46 条，我判断它「最容易批量」（补空实现即可）。
本轮按「文件 × 缺失方法名」聚合，想看能不能一次补一批。

### 实际统计出来的方法名
```
getMetaFactory   7      ← 老族，且是"幻影族"（真因在别处）
rotate           5      ← 老族，父接口不明
packetCodec      3
getLayer         3
apply            2
createRenderState 2
getSlot / dropItem / addAdditionalSaveData / reload / getArmPose   各 1
```

**⇒ 全部都是本台账已经定性过的族**，没有一个是"新接口加了方法、实现类忘了补"这种便宜活。
`getMetaFactory` 和 `rotate` 更是早就标注为**幻影**（报「方法不会覆盖」但真因在别处）。

### 结论（更正 R171）
**`未实现抽象方法` 不是什么可批量解决的桶**，它就是那批老族在另一种 javac 措辞下的重复出现。
R171 里"按 ROI 排序第 1 位"的那条建议**作废**。

### 顺带一个工具坑
我用的 PowerShell 脚本里写成了嵌套的 `if (... -match ...) { ... if (... -match ...) }`，
**内层 `-match` 把外层的 `$Matches` 覆盖了**，于是 `Split-Path $Matches[1]` 收到 null，
刷出几十条 `Split-Path: 无法将自变量绑定到参数 'Path'` 报错（还烧掉不少上下文）。
**⇒ 要么在外层匹配后立刻把捕获值存进普通变量，要么直接用 `[regex]::Match()`。**


<!-- ===== 从热层搬来的较早族行（20261017-113541）===== -->

| 族 | 结论 |
|---|---|
| 族（结论全文见 `docs\SOLVED-FAMILIES.md`） | 结果 | 备注 |
| `Vec3.STREAM_CODEC` 替 `CatnipStreamCodecs.VEC3` | −2 | 原版自带，R124 验过 |
| `TypedEntityData.copyTag()` → `copyTagWithoutId()` | −2 | 原版类，不是 Create 的 |
| 单构造器垫片可影子（`RegistrateLangProvider`） | −2 | 1 个成员 ⇒ 影子成本低 |
| `GuiGraphics` 无 buffer（GUI 也进 render-state） | 暂挂 | `GuiRenderState` 架构 |
| Create `ItemStackHandler`： `getItem` 替 `getStackInSlot` | −2 | 见 import 行定位 FQN |
| 找不到类型 → 先读 `import` 行 | —— | 比挨个 javap 快 |
| `getGameRules` + `RULE_DOBLOCKDROPS` 同属设计级 | 8 暂挂 | gamerule 数据驱动化 |
| `DeferredHolder` 影子已加但净 0 | 待查 | 疑函数式接口类型不匹配 |
| `NbtUtils.createUUID` 没了 → 手写 `IntArrayTag` | −1 | `loadUUID` 当时还在 |
| `NbtUtils.loadUUID` 也没了；`readUUID` 不吃 `Tag` | 2 待设计 | 别再直接换 |
| 符号普查已摊平：141 组，最大 8 条 | —— | **机械族已打完** |
| `EndSeaShadowRenderer::renderShadowMap` 双问题 | 暂挂 | 宿主 `VeilEventPlatform` 无桩 |
| `xxxTo(A)` → `xxx(A,B)` 是加参数不是改名 | 已回滚 | 要补第二参 |
| javap 长签名会截断 ⇒ 单独打印目标行 | —— | 否则误判参数个数 |
| `ValueInput.hasUUID` 没了 → `read("K", UUIDUtil.CODEC).isPresent()` | −2 | 见 R163 |
| javap 过滤**别按 `(`**：`UUIDUtil.CODEC` 是**字段**，按括号筛会把它滤掉（已坑两次）| —— | —— |
| **「写」方法的第一个参数必须是 `ValueOutput`**（读用 `ValueInput`）：`writeSafe`/`write`/`saveAdditional`/`writeAdditionalSaveData` 写成 `ValueInput` ⇒ 后面 `store(...)`/`lookup()` 全挂 | −1 | 见 R164 |
| **`ListTag` 没有 `CODEC`**（javap 只有 `TYPE`）⇒ `put("K", ListTag)` / `getList("K",10)` **换不成 `store(...,ListTag.CODEC,...)`**（净 0，已回滚）；结构列表只能走 `childrenList` / `list(String, Codec)` | 8 待设计 | R165 |
| **定位手法升级**：按 `文件 ×（消息+符号）` 交叉表找「单文件重复」，比只看文件错误数准得多 | —— | R165 |
| **CC 垫片补 `queueEvent(String, Object...)`**：`AttachedComputerHandler` 是我们的桩（4 个成员），一个 varargs 同时满足 `queueEvent("key",k,alive)` 与 `queueEvent("key_up",k)` | −2 | R166 |
| ★★★ **系统扫桩法（性价比最高）**：① 收集 `src/stub` 全部类名 ② 从日志配对 `符号:`+`位置:` ③ 只留「位置里出现桩类名」的 ⇒ 每一半条都是「加个方法就清掉」；本轮 16 条，清掉 12 | **−6** | R167 |
| ⚠ **垫片常见病：单复数不一致**（`validBlocks(BlockEntry<?>...)` vs 项目调 `validBlock(x)`）| −4 | R167 |
| ⚠ **给接口桩加方法必须用 `default`**，否则破坏所有实现者 | —— | R167 |
| ⚠ **`'X' in text` 判存在会被同前缀骗**（`validBlock` ⊂ `validBlocks`）⇒ 用 `re.search(r'\bX\s*\(', t)` | —— | R167 |
| ✅✅ **桩缺口已清零**：`scan_stub_gap.py` 报 **`位置落在桩类上 = 0 条`** ⇒ 「给自家桩补方法」这条路走完了（R166–R168 共 −10）。剩下的 497 条**不在**我们的桩里 | —— | R168 |
| **注解也能缺元素**：`@LuaFunction(mainThread = true)` ⇒ 桩里要写 `boolean mainThread() default false;` | −1（raw −2）| R168 |
| **datagen 垫片补 `Object` 形态重载**：`BlockStateGen.simpleBlock(ctx,prov,Function)` 返回 `Object` 即可 | −1（raw −2）| R168 |


---

## R173（496 → 493，**−3**）：`getInt`/`getLong` 变成了 `Optional`

### 抽样：`不兼容的类型`(156) 到底是什么
55 种不同形态，最大的一条是：
```
21x  Matrix3x2fStack 无法转换为 PoseStack     ← 已有结论：GUI 进了 render-state（设计级）
 4x  ConfigValue<T> 与 DoubleRawValue 不一致  ← 配置层
 3x  String→Category / ValueInput→CompoundTag / Identifier→RenderPipeline
 2x  class_2396 无法转换为 ParticleType<D>     ← 混淆名残留（和 class_2248 同类）
 2x  Optional<Long>→long / Optional<CompoundTag>→CompoundTag
```
**⇒ 156 条里至少 21 条是那个 GUI 设计级问题**，这一桶并不像 R171 想的那样"好批量"。

### 但抽出了一族真·项目级 API 变更（javap 实证）
```java
// net.minecraft.nbt.CompoundTag
public Optional<Integer> getInt(String);
public int getIntOr(String, int);           // ← 要这个
// net.minecraft.world.level.storage.ValueInput
public Optional<Long> getLong(String);
public long getLongOr(String, long);        // ← 要这个
public int getIntOr(String, int);
```
⇒ `x.getInt("K")` → **`x.getIntOr("K", 0)`**；`x.getLong("K")` → **`x.getLongOr("K", 0L)`**

### ★ 关键技巧：用「负向断言」只改"忘了解包"的地方
```python
P = re.compile(r'\.getInt\(("[^"]*")\)(?!\s*\.)')
```
`(?!\s*\.)` 的作用：**如果后面紧跟 `.`（比如 `.orElse(...)` / `.isPresent()`），说明这个 `Optional` 是想要的，跳过**；
只有"光秃秃地当原语用"的才算错。这样一条正则就能安全批量替，不会像 R169 那样因为接收者/用法混杂而不敢动。

本轮命中 3 处 ⇒ `Optional<Long>无法转换为long` **4 → 0**、总 **−3**，解析期 0。

### 下一步可复用同法的地方
`getBoolean` / `getString` / `getFloat` 等很可能也有 `xxxOr` 版本 ⇒
**下轮先 javap 确认返回值是不是 `Optional`，再用同样的负向断言批量替。**


---

## R174（493 → 491，**−2**）：NBT getter 的 Optional 全图

### 完整地图（javap 实测，以后写代码可直接照这张表）
**`CompoundTag` —— 13 个 getter 全部返回 `Optional`：**
```
getByte    → getByteOr(String, byte)        getByteArray   → （无 Or，需 .orElse）
getShort   → getShortOr(String, short)      getIntArray    → （同上）
getInt     → getIntOr(String, int)          getLongArray   → （同上）
getLong    → getLongOr(String, long)        getCompound    → getCompoundOrEmpty(String)
getFloat   → getFloatOr(String, float)      getList        → getListOrEmpty(String)
getDouble  → getDoubleOr(String, double)    getBoolean     → getBooleanOr(String, boolean)
getString  → getStringOr(String, String)
```
**`ValueInput` —— 只有 4 个是 `Optional`：** `getInt` / `getLong` / `getString` / `getIntArray`。

### 批量替换的结果：0 处
上一轮（R173）已经清掉 `getInt`/`getLong` 的漏网之处；本轮对
`getString`/`getBoolean`/`getFloat`/`getDouble`/`getShort`/`getByte`/`getCompound`/`getList`
跑同一套负向断言 —— **一处都没命中**，说明这些地方**本来就写对了**（要么用了 `Or`，要么 `.orElse`）。
**⇒ 这一族只剩 `getInt`/`getLong` 那 3 处，现已清零。**

### 本轮真修的 3 处
| 位置 | 原码 | 问题 | 改法 |
|---|---|---|---|
| `RopeStrandHolderBehavior:464` | `final CompoundTag strandNBT = nbt.childOrEmpty("Strand");` | `childOrEmpty` 返回 **`ValueInput`** | **改局部变量的声明类型**（配方 c）|
| `LevititeCrystallizerManager:74` | `data.getCompound(i)` | `ListTag.getCompound(int)` 现在是 `Optional` | `.orElseGet(CompoundTag::new)` |
| `KineticBlockEntityMixin:170` | `compound.getCompound(name)` | 同上 | 同上 |

⇒ `Optional<CompoundTag>无法转换为CompoundTag` **4 → 0**、总 **−2**，解析期 0。

### 剩下 2 处（本轮没动）
- `SteeringWheelBlockEntity:276`：`NbtUtils.readBlockState(getter, compound.childOrEmpty("Material"))`
  —— `compound` 现在是 **`ValueOutput`**，而 `ValueOutput` 没有能返回 `CompoundTag` 的方法 ⇒ 需要绕。
- `CrystallizationWorldSaveData:29`：`LevititeCrystallizerManager.loadData(tag, level)`
  —— `loadData` 的形参还是 `CompoundTag`，应改成 **`ValueInput`**（项目自己的方法，可改）。


---

## R175（净 0）：`方法应用不到`(70) 的集中度表

### 按 `类.方法` 归类（31 种，前 16）
```
 8x  SmartBlockEntity.readClient        ← Create
 8x  UIRenderHelper.drawCropped         ← Create 的 UI 助手
 6x  Sided.getLocalOffset               ← ValueBoxTransform 族（已定性）
 6x  KeyMapping.matches                 ← 原版
 4x  AssemblyException.read / .write    ← Create
 4x  AnalogLeverBlockEntity.write       ← 项目自己的
 4x  UIRenderHelper.drawStretched       ← Create
 2x  GuiGraphics.renderTooltip / fillGradient / ValueBoxTransform.shouldRender
 2x  LinkedTypewriterBlock.getCloneItemStack / AugerShaftBlockEntity.write
 2x  Item.appendHoverText / BlockEntity.loadCustomOnly
```
**⇒ 这 70 条高度集中：前 4 组就占了 28 条。**以后要打这一桶，就按这张表从上往下做。

### 本轮查清的两个 API 事实
```java
// com.zurrtum.create.foundation.blockEntity.SmartBlockEntity
public final void readClient(ValueInput);                 // ← 只剩 1 个参数
// net.minecraft.client.KeyMapping
public boolean matches(KeyEvent);
public boolean matchesMouse(MouseButtonEvent);            // ← 两参 (int,int) 版没了
```

### 为什么这两个本轮都没动
- **`readClient`**：调用点长这样 ——
  `lever.readClient(tag, level.registryAccess())` /
  `extraKinetics.readClient(extraKineticsTag, registries)`。
  去掉第二参容易，但**第一参手上是 `CompoundTag`，而新签名要 `ValueInput`** ——
  两者不是一回事（`CompoundTag` 是 NBT 树，`ValueInput` 是 1.21.11 的读写视图）。
  **⇒ 属"要换数据通路"，不是删个参数。**
- **`KeyMapping.matches`**：老代码是 `matches(key, scanCode)`，新 API 要一个 `KeyEvent` 对象。
  构造 `KeyEvent` 需要 window + action + modifiers，**不是一行能补的**。

### 顺带否掉一个想法
`LevititeCrystallizerManager.loadData(CompoundTag tag, Level level)` 看似"改成 `ValueInput` 就行"，
但它体内用的是 **`tag.getListOrEmpty("Levitite Manager Data")`** ——
这个方法是 **`CompoundTag` 独有**的（`ValueInput` 没有无类型的 list 读取，见 R165）。
**⇒ 改了形参就要连带改这个读取逻辑 ⇒ 同样撞墙，暂挂。**


<!-- ===== 从热层搬来的较早族行（20261017-113911）===== -->

| 族 | 结论 |
|---|---|
| **`CompoundTag` 有 `getCompoundOrEmpty(String)` / `getListOrEmpty(String)`** ⇒ 接收者是 `CompoundTag` 时，`childOrEmpty` → `getCompoundOrEmpty` | −1 | R169 |
| ⚠ **`childOrEmpty` 有 11 处、接收者混杂三种**（`ValueInput` / `ValueOutput` / `CompoundTag`）⇒ **绝不能批量替换**，只改「能确定接收者类型」的那几处 | —— | R169 |
| ✅ **`childOrEmpty` 已清零**（javap：`ValueInput` **有** `childOrEmpty` ✓，`ValueOutput` **没有** ✗，只有 `child(String)`）⇒ 报错只出在 `CompoundTag`/`ValueOutput` 接收者上；R169 改的那 1 处即全部 | 0 条 | R170 |
| ⚠⚠ **`addVariantTo` 没有等价物**（已证）：调用形态是 `.transform(EncasingRegistry.addVariantTo(AllBlocks.SHAFT))`，要**返回一个变换器**；而新 API `addVariant(B,E)` 返回 **void**，得在注册时同时给两个方块 ⇒ 无法当变换器用 | 4 条暂挂 | R170 |
| ⚠ **`GameProfile` 不在 minecraft-merged jar 里**（在 authlib）⇒ javap 要用 authlib 的产物，别在合并 jar 里找 | —— | R170 |
| ★★★ **496 条的性质×来源决策表**：`src/main` **726 条（73%）** ／ `excluded-wip` 236（24%）／ `src/stub` 16／`src/fabric` 12 ⇒ **「多排除」是死路**（实测排除 wip 反而 +758）；`src/main` 内部：`找不到符号` 208 ／ `不兼容类型` **156** ／ `方法不会覆盖` 128 ／ 其他 118 ／ `方法应用不到` **70** ／ `未实现抽象` **46** | 见 R171 | R171 |
| ★★ **火力应集中在 `src/main` 的「类型/签名」两桶**：`不兼容的类型`(156) + `方法应用不到`(70) + `未实现抽象方法`(46) = **272 条**，都是「改声明/加桩」能解决的形态 | —— | R171 |
| ⚠⚠ **R171 的第 3 条要更正**：`未实现抽象方法`(46) **不是独立机会** —— 方法名统计出来是`getMetaFactory`(7) / `rotate`(5) / `packetCodec`(3) / `getLayer`(3) / `apply`(2) / `createRenderState`(2) …，**全是本台账已定性过的老族**（`getMetaFactory`/`rotate` 还是「幻影族」）⇒ 这一桶没有新东西 | 更正 R171 | R172 |


---

## R176（491 → 487，**−4**）：【重大突破】`CompoundTag` ↔ `ValueInput/ValueOutput` 的桥

### 我怎么找到的
前面几轮反复撞同一堵墙：
> 「新 API 要 `ValueInput`，但手上是 `CompoundTag`」——
> `readClient` / `write` / `loadData` 全都卡在这。

而线索其实早出现过一次：`LinkedTypewriterBlock:185` 报
**`CompoundTag 无法转换为 TagValueOutput`** —— 编译器在说"这里有个叫 `TagValueOutput` 的类型"。

顺手 javap，果然有 **`TagValueInput` / `TagValueOutput`**：

```java
// net.minecraft.world.level.storage.TagValueInput
public static ValueInput create(ProblemReporter, HolderLookup.Provider, CompoundTag);
// net.minecraft.world.level.storage.TagValueOutput
public static TagValueOutput createWithContext(ProblemReporter, HolderLookup.Provider);
public static TagValueOutput createWithoutContext(ProblemReporter);
// net.minecraft.util.ProblemReporter
public static final ProblemReporter DISCARDING;      // ← 空实现，直接用
```

### 桥怎么用
```java
// 读：CompoundTag → ValueInput
ValueInput in = TagValueInput.create(
        ProblemReporter.DISCARDING, level.registryAccess(), compoundTag);

// 写：拿到一个写视图（内部持有一个 CompoundTag）
TagValueOutput out = TagValueOutput.createWithContext(
        ProblemReporter.DISCARDING, level.registryAccess());
// … 用 out.store(...) / out.putInt(...) 写 …
CompoundTag result = out.build();
```

### 立即收益
`SmartBlockEntity.readClient(ValueInput)` 的 4 处调用（日志里 8 条）全部改成：
```java
lever.readClient(tag, level.registryAccess())          // 旧
// →
lever.readClient(TagValueInput.create(
        ProblemReporter.DISCARDING, level.registryAccess(), tag))   // 新
```
⇒ `无法将类 SmartBlockEntity 中的方法 readClient 应用到给定类型` **8 → 0**、总 **−4**，解析期 0。

### 这条结论为什么值钱
之前 R175 把 `readClient`(8) / `AnalogLeverBlockEntity.write`(4) / `loadData` 都判成"受阻/设计级"，
**判错了** —— 它们不是"数据通路不同"，只是**缺一层适配器**。
**⇒ 以后凡是「要 ValueInput/ValueOutput 而手上是 CompoundTag」的报错，先想这座桥，不要再判死。**

（`TagValueOutput` 有没有 `build()` 需要下一轮确认；如果有，`write` 那一族也能照此解决。）


---

## R177（净 0）：桥的**写方向** —— `buildResult()`

### 补齐上轮缺的那一半
```java
public class TagValueOutput implements ValueOutput {
    private final ProblemReporter problemReporter;
    private final DynamicOps<Tag> ops;
    private final CompoundTag output;                       // ← 内部持有一个标签

    public static TagValueOutput createWithContext(ProblemReporter, HolderLookup.Provider);
    public static TagValueOutput createWithoutContext(ProblemReporter);

    public <T> void store(String, Codec<T>, T);
    public <T> void storeNullable(String, Codec<T>, T);
    public void putBoolean/putByte/putShort/putInt/putLong/putFloat/putDouble/putString/putIntArray(String, …);
    public ValueOutput child(String);
    public void discard(String);
    public CompoundTag buildResult();                       // ★ 取出结果
}
```

### 完整桥（两个方向都能走）
```java
// ── 读：CompoundTag → ValueInput ──
ValueInput in = TagValueInput.create(
        ProblemReporter.DISCARDING, registryAccess, oldTag);

// ── 写：写进新视图，再并回原标签 ──
TagValueOutput out = TagValueOutput.createWithContext(
        ProblemReporter.DISCARDING, registryAccess);
someBlockEntity.write(out);          // 现在签名是 write(ValueOutput)
oldTag.merge(out.buildResult());     // ← 结果并回
```

### ★ 一个必须注意的语义差别
`TagValueOutput.createWithContext(...)` 生成的是**全新的空 `CompoundTag`**，不是"包着你的旧标签"。
所以「往已有标签里写」必须**先写到新视图、再 `merge` 回去**；
如果只是"生成一个新标签"（例如序列化一个对象），那 `buildResult()` 直接用即可。

### 下一轮可以直接打的族
| 族 | 条数 | 改法 |
|---|---|---|
| `AnalogLeverBlockEntity.write` | 4 | `lever.write(tag, registryAccess, false)` → 用 `TagValueOutput` 写、`tag.merge(...)` |
| `AssemblyException.read` / `.write` | 8 | 同上（读用 `TagValueInput`，写用 `TagValueOutput` + merge）|
| `LevititeCrystallizerManager.loadData` | 1 | 形参可安心改成 `ValueInput`：若体内仍要 `getListOrEmpty`，先用 `TagValueInput` 包一层即可 |


---

## R178（487 → 486）：桥的实战三例

### 例 1：`AssemblyException.read` / `write` —— 原来根本不需要桥
javap：
```java
public static void write(ValueOutput, AssemblyException);   // 2 参
public static AssemblyException read(ValueInput);           // 1 参
```
项目里写的是 `read(tag, tag.lookup())` —— 而 **`tag` 本来就是 `ValueInput`**，
所以正确答案只是 **`read(tag)`**。我一开始套桥，反而把参数搞成了 `(Provider, Provider)`。

### 例 2 / 例 3：真正需要桥的地方
```java
// SwivelBearingBlockEntity:639 / PhysicsAssemblerBlockEntity:380
AssemblyException.write(compound, this.getLevel().registryAccess(), this.lastException);
// →
final TagValueOutput __o = TagValueOutput.createWithContext(
        ProblemReporter.DISCARDING, this.getLevel().registryAccess());
AssemblyException.write(__o, this.lastException);
compound.merge(__o.buildResult());
```
```java
// RedstoneSignalInstruction:41
lever.write(tag, level.registryAccess(), false);
// →
final TagValueOutput __l = TagValueOutput.createWithContext(
        ProblemReporter.DISCARDING, level.registryAccess());
lever.write(__l);
tag.merge(__l.buildResult());
```

### ⚠ 我在脚本里犯的一个错（值得记）
```python
BR = 'TagValueInput.create(%s, %s)'
BR.replace('%s','tag.lookup()').replace('%s','tag')     # ← 错的
```
**第一次 `.replace('%s', A)` 把两个占位符都换成了 A**，第二次再也匹配不到 ⇒ 生成 `create(A, A)`，
于是报「`create(ProblemReporter,Provider,Provider)` 找不到」。
**⇒ 多个占位符必须用 `%`/f-string/`re.sub` 回调，绝不要链式 `.replace()`。**

### 本轮结果
`create(ProblemReporter,Provider,ValueInput)` 4 → 0，无新增错误，总 **487 → 486**。
（`AssemblyException.read/write` 两族也已清零，只是被上面那 4 条新错抵消了一部分。）

### 教训（写给下一轮的自己）
**套桥之前先 `<TYPE>` 一下：如果接收者本身就是 `ValueInput`，别再套 `TagValueInput`。**
判据：报错若是「参数不匹配」，先看实参**已有的类型**；只有当实参确实是 `CompoundTag` 时才上桥。


---

## R179（486 → 480，**−6**）：`UIRenderHelper` 换包 + 删 `zLevel`

### 定位过程
先按老路径 javap `com.zurrtum.create.client.foundation.gui.UIRenderHelper` —— **零命中**。
于是扫 jar 的路径：
```
com/zurrtum/create/client/catnip/gui/UIRenderHelper.class     ← 实际在这
```
**⇒ Create 把这一批 GUI 工具从 `foundation` 挪到了 `catnip`。**

### 新旧签名对比
```java
// 新（javap）
public static void drawStretched(GuiGraphics, int, int, int, int, TextureSheetSegment);   // 6 参
public static void drawCropped  (GuiGraphics, int, int, int, int, TextureSheetSegment);   // 6 参
// 项目调用（7 参）
UIRenderHelper.drawCropped(graphics, x + 4, y, w - 8, 3, zLevel, AllGuiTextures.BRASS_FRAME_TOP);
//                                                        ↑ 多出来的就是 zLevel
```
**⇒ 删掉倒数第二个实参（`zLevel`）即可。**

### 结果
`drawCropped` **8 → 0**、`drawStretched` **4 → 0**，总 **486 → 480**（−6），解析期 0。

### ★ 一条可推广的判据
**1.21.11 把 `zLevel`（int 层高）整套删了** —— GUI 现在用 `GuiGraphics.nextStratum()` /
`GuiRenderState` 分层。所以：
> **凡是 UI 绘制助手报「参数过多 / 无法应用到给定类型」，先数一下实参里有没有 `zLevel`。**

这一条与 R156 的「`GuiGraphics` 无 buffer」是同一场架构迁移（GUI → render-state）的两个侧面。


<!-- ===== 从热层搬来的较早族行（20261017-114353）===== -->

| 族 | 结论 |
|---|---|
| ⚠ **PowerShell 里 `-match` 会覆盖 `$Matches`**：嵌套使用（外层匹配路径、内层匹配方法名）会把外层的捕获变量冲掉 ⇒ **要么先存成变量，要么改用 `[regex]::Match()`** | —— | R172 |
| ★★★ **`getInt`/`getLong` 都改成返回 `Optional` 了**：`CompoundTag.getInt(String)` → `Optional<Integer>`、`ValueInput.getLong(String)` → `Optional<Long>`；对应有 **`getIntOr(String,int)` / `getLongOr(String,long)`** | 3 处 ⇒ **−3** | R173 |
| ★★★ **「负向断言」筛法**：批量改 `x.getInt("K")` → `x.getIntOr("K",0)` 时，用 `\.getInt\(("[^"]*")\)(?!\s*\.)` —— `(?!\s*\.)` 排除「后面还在链式解包」的调用，否则会把**想要 Optional 的地方**一起改坏（规则 36 的机械实现）| —— | R173 |
| ⚠ **`不兼容的类型`(156) 的抽样画像**：`Matrix3x2fStack→PoseStack` **21 条（设计级 GUI）**、`ConfigValue/DoubleRawValue` 4、`class_2396→ParticleType` 2（**混淆名残留**，同 `class_2248`）、`Optional` 解包若干、`ValueInput→CompoundTag` 3 | 见 R173 | R173 |
| ★★★ **`CompoundTag` 的 13 个 getter 全部 `Optional` 化**（javap 实测）：`getByte/getShort/getInt/getLong/getFloat/getDouble/getString/getByteArray/getIntArray/getLongArray/getCompound/getList/getBoolean` —— 每个都有 `getXOr(String,默认值)` 或 `getXOrEmpty`；`ValueInput` 只有 `getInt/getLong/getString/getIntArray` 是 Optional | R173/R174 已清 | R174 |
| **`ListTag.getCompound(int)` 也是 `Optional`** ⇒ `.orElseGet(CompoundTag::new)` | 2 处 ⇒ **−2** | R174 |
| ★★★ **`方法应用不到`(70) 的集中度表**（按 `类.方法`）：`SmartBlockEntity.readClient` **8**、`UIRenderHelper.drawCropped` **8**、`Sided.getLocalOffset` 6、`KeyMapping.matches` 6、`AssemblyException.read/write` 各 4、`AnalogLeverBlockEntity.write` 4、`UIRenderHelper.drawStretched` 4 | 见 R175 | R175 |
| **`SmartBlockEntity.readClient` 现在只收 1 个 `ValueInput`**（旧签名是 `(CompoundTag, Provider)`）；**`KeyMapping.matches` 只剩 `matches(KeyEvent)` / `matchesMouse(MouseButtonEvent)`**，两参 `(int,int)` 版没了 | 两族都受阻 | R175 |


---

## R180（净 0）：把「写」分成两种，别再一锅端

### 上一轮怎么成功的、这一轮为什么没动
R179 用桥一次清了 12 条（`UIRenderHelper`），于是我想"写侧都能用桥"。本轮试了三处：

| 位置 | 代码 | 结论 |
|---|---|---|
| `KineticBlockEntityMixin:153` | `extraKinetics.saveAdditional(internalTag, registries)` | 改成桥 + `merge` —— **总条数没动**（既没修好也没弄坏）|
| `AugerShaftBlock:161` | `abe.write(tag, reg, false)` | **桥不管用** |
| `RedstoneSignalInstruction:42` | `lever.write(__l)`（已经是 1 参了）| **仍然报错** |

### 为什么
`AugerShaftBlockEntity.write` 和 `AnalogLeverBlockEntity.write` **不是**继承自 `SmartBlockEntity` 的那个
`write(ValueOutput)` —— 它们是**项目自己声明**的：
```java
public void write(CompoundTag tag, HolderLookup.Provider registries, boolean clientPacket) { … }
```
所以：
- **继承来的写入口**（`SmartBlockEntity.write` / `saveAdditional`）：实参该是 `ValueOutput` ⇒ **桥可用**；
- **项目自建的写方法**：它本来就是"往 `CompoundTag` 里写" ⇒ **报错是因为别处把它当 1 参版调**，
  或者是它自己的签名要跟父类对齐 ⇒ **桥完全不相干**。

### ★ 判据（下一轮直接用）
> 看到「无法将类 X 中的方法 write/saveAdditional 应用到给定类型」，
> **先确认 `X` 是不是项目自己的类**（在 `src/main` 里能找到 `void write(...)` 声明）。
> - 是 ⇒ 改它自己的声明/调用，**别套桥**；
> - 不是（继承自 Create）⇒ 用 `TagValueOutput` + `merge`。

### 集中度表刷新（R179 清掉 12 条之后）
```
6x  Sided.getLocalOffset            ← ValueBoxTransform 族
6x  KeyMapping.matches              ← 要 KeyEvent
4x  AnalogLeverBlockEntity.write    ← 项目自建（见上）
2x  AugerShaftBlockEntity.write     ← 项目自建（见上）
2x  SmartBlockEntity.saveAdditional ← 继承，桥
2x  Shulker.getProgressAabb / GustParticle.renderRotatedQuad / GuiGraphics.fillGradient
2x  ValueBoxTransform.shouldRender / DirectionalExtenderScrollOptionSlot.getLocalOffset
```


---

## R181（480 → 473，**−7**）：`ValueBoxTransform.Sided` 只收 1 个参数

### 真签名（javap `com.zurrtum.create.client.foundation.blockEntity.behaviour.ValueBoxTransform$Sided`）
```java
public Vec3    getLocalOffset(BlockState);     // 1 参
public boolean shouldRender (BlockState);      // 1 参
```
而项目里有 3 个文件还写着 **3 参**：
```java
public Vec3 getLocalOffset(final LevelAccessor level, final BlockPos pos, final BlockState state)
public boolean shouldRender (final LevelAccessor level, final BlockPos pos, final BlockState state)
```

### 为什么能"纯改签名"
三个体都长这样 —— **只把参数原样转给 `super`**，自己不用 `level`/`pos`：
```java
public Vec3 getLocalOffset(final LevelAccessor level, final BlockPos pos, final BlockState state) {
    return super.getLocalOffset(level, pos, state)
            .subtract(Vec3.atLowerCornerOf(state.getValue(SwivelBearingBlock.FACING).getUnitVec3i()).scale(5 / 16f));
}
```
⇒ 改签名 + 改 `super.` 调用就完成，**函数体不动**（配方 a）。

### 批量替换的两条正则
```python
(r'(Vec3|boolean)\s+getLocalOffset\(\s*final\s+LevelAccessor\s+level,\s*final\s+BlockPos\s+pos,\s*final\s+BlockState\s+state\s*\)',
 r' getLocalOffset(final BlockState state)')
(r'super\.getLocalOffset\(level,\s*pos,\s*state\)', 'super.getLocalOffset(state)')
# shouldRender 同理
```

### 结果
`方法不会覆盖` **166 → 158（−8）**、`Sided.getLocalOffset` **6 → 2**，总 **480 → 473（−7）**，解析期 0。

### ★ 一个可推广的观察
**`方法不会覆盖`(166) 这一大桶里，有相当一部分是"父类签名少参数"** ——
不是逻辑错，而是 1.21.11 把某些方法的上下文参数（level/pos/provider）删掉了。
**⇒ 遇到 `方法不会覆盖`，先 javap 父类的真签名，再比对项目声明的参数个数**，
比逐个猜测快得多。（R151 的 `neighborChanged` 多一个 `Orientation`、本轮少两个参数，都是同一类。）

### 剩下的 2 条 `Sided.getLocalOffset`
`DualGimbalSensorValueBox` / `DirectionalExtenderScrollOptionSlot` 那两处 —— 它们不是 `Sided` 的子类，
可能是**别的基类**，下轮单独查。


---

## R182（净 0）：`方法不会覆盖` 的全表 + 一批幻影

### 工具
日志里的「方法不会覆盖」块**不写方法名**（只有 `@Override` 和附近的代码行），
所以按日志聚合只能全落到 `(未知)`。正确工具是项目根目录的 **`analyze_override3.py`**（读源码取签名）：

```
python analyze_override3.py <编译日志>
```

### 全表（174 条 raw，TOP 25）
```
 12  rotate                          例: SteamVentBlockEntity:403 rotate(LevelAccessor,BlockPos,BlockState,…)
 10  render                          例: GustParticle:34  render(VertexConsumer,Camera,…)
 10  getMetaFactory                  例: GustParticleData:38
 10  getCodec                        （粒子）
 10  getStreamCodec                  （粒子）
  8  save                            例: CrystallizationWorldSaveData:16  save(CompoundTag,Provider)
  8  neighborChanged                 例: HandleBlock:105                    ← 【幻影】见下
  6  fallOn                          例: EnvelopeBlock:161
  6  getLocalOffset                  例: GyroscopicPropellerBearing:228（已修）
  6  streamCodec
  4  registerAll / readAdditionalSaveData / addAdditionalSaveData / getRenderType
  4  apply / mouseReleased / getTextureLocation
  2  getLightBlock / getCloneItemStack / fromSide / applyLocalTransforms
  2  getMovementModeSlot / renderRotatedQuad
```

### ★ 重要：`neighborChanged`(8) 是幻影
我把全项目的 `neighborChanged` 声明列了一遍 —— **14 处已经全都带了 `Orientation` 参数**：
```java
public void neighborChanged(final BlockState state, final Level level, final BlockPos pos,
                            final Block blockIn, final Orientation orientation)
```
**⇒ 那 8 条「方法不会覆盖」的真因不在签名上。**
⇒ **override 分析器给出的计数含幻影，不能照着直接打**（这一点 R143 已经记过，本轮再次验证）。

### 这一桶接下来该怎么看
| 方法 | 判断 |
|---|---|
| `rotate`(12) | 父接口不明，暂挂 |
| `render`/`getMetaFactory`/`getCodec`/`getStreamCodec`/`renderRotatedQuad` | **粒子体系整体迁移**（`render*` → `extract*`），设计级 |
| `save`(8) | `SavedDataType` 重构，设计级 |
| `neighborChanged`(8) | **幻影** |
| `getLocalOffset`(6) | 已修（R181） |
| `readAdditionalSaveData`/`addAdditionalSaveData`(8) | 形参要从 `CompoundTag` 改 `ValueInput`/`ValueOutput` ⇒ **可用桥**，但要改体 |

**⇒ 这桶里"纯签名能改"的已经基本吃完（R181 的 8 条），剩下的多为设计级或幻影。**


<!-- ===== 从热层搬来的较早族行（20261017-114651）===== -->

| 族 | 结论 |
|---|---|
| ⚠ **`loadData(CompoundTag)` 不能简单改成 `ValueInput`**：其体用了 `tag.getListOrEmpty(...)`，而**只有 `CompoundTag` 有这个方法**（撞 R165 的「无类型 ListTag」墙）| 暂挂 | R175 |
| ★★★★ **【桥】`CompoundTag` ↔ `ValueInput`/`ValueOutput` 一切都能换**：`TagValueInput.create(ProblemReporter.DISCARDING, registryAccess, tag)` → `ValueInput`；`TagValueOutput.createWithContext(ProblemReporter.DISCARDING, registryAccess)` → 写视图；`ProblemReporter.DISCARDING` 是空实现 | `readClient` **8→0** ⇒ **−4** | R176 |
| ★★★ **凡「新 API 要 ValueInput 而手上是 CompoundTag」的族，都用上面的桥** —— 这不是墙，是缺一层适配 | —— | R176 |
| ★★★★ **桥的写方向**：`TagValueOutput` 是 `ValueOutput` 的实现，内部持一个 `CompoundTag`，**`public CompoundTag buildResult()`** 取出来。`createWithContext` 生成的是**新标签**，要把结果并回原标签就 `orig.merge(out.buildResult())` | —— | R177 |
| **完整桥（两向）**：读 `TagValueInput.create(DISCARDING, registryAccess, tag)` → `ValueInput`；写 `TagValueOutput o = TagValueOutput.createWithContext(DISCARDING, registryAccess)` → 写 → `o.buildResult()` → `orig.merge(...)`。两处都用 `ProblemReporter.DISCARDING` | —— | R177 |
| ★★ **桥的实战三例**：① `AssemblyException.read(ValueInput)` / `write(ValueOutput, ex)` —— **只收 1/2 个参数**，`read(tag, tag.lookup())` 直接改成 `read(tag)` 即可（`tag` 本来就是 `ValueInput`）；② `AssemblyException.write(compound, ra, ex)` 用 `TagValueOutput` + `compound.merge(o.buildResult())`；③ `lever.write(tag, ra, false)` 同法 | 共 −1（多族清零）| R178 |
| ⚠⚠ **我在脚本里犯的错**：`'T.create(%s, %s)'.replace('%s','A').replace('%s','B')` —— **第一次 replace 把两个占位符都换成 A 了**，第二次再也匹配不到 ⇒ 生成 `(A, A)`。**⇒ 多占位符必须用 `%`/f-string 或 `re.sub` 的回调，绝不要链式 `.replace()`** | —— | R178 |


---

## R183（净 0）：桥只有单向 —— 这决定了哪些族能「改签名」、哪些必须「重写体」

### 本轮查的对象
`readAdditionalSaveData` / `addAdditionalSaveData` 各有 4 条，共 8 条。我先把全项目的声明列了一遍：

| 文件 | 现状 |
|---|---|
| `DiagramEntity:201/214` | **已经是** `ValueOutput` / `ValueInput` ✓ |
| `LaunchedPlungerEntity:373/388` | **已经是** ✓ |
| `GustEntity:151/156` | 还是 `CompoundTag` ✗ |
| `HoneyGlueEntity:166/179` | 还是 `CompoundTag` ✗ |

### 为什么后两个不能只改签名
`HoneyGlueEntity` 的体里用的是 **`CompoundTag` 独有**的方法：
```java
compound.put("From", VecHelper.writeNBT(…));          // ValueOutput 没有 put(String,Tag)
compound.contains("Pos")                               // ValueInput 没有 contains
compound.getListOrEmpty("Pos")                         // ValueInput 没有 getListOrEmpty
```
`GustEntity` 也一样（`SableNBTUtils.writeQuaternion/readQuaternion` 收发的是 NBT 形态）。

### ★ 新事实：桥只有单向
```java
CompoundTag ──TagValueInput.create(...)──▶ ValueInput      ✓ 能
CompoundTag ──TagValueOutput.createWithContext(...)──▶ ValueOutput ✓ 能
ValueInput  ──???──▶ CompoundTag                            ✗ 不能
```
`TagValueInput` 内部虽然持有一个 `CompoundTag`，但**字段是私有的、没有 getter**，
所以"先包一层再在体内取回原标签"这条路走不通。

**⇒ 判据**：
> 要把一个方法形参从 `CompoundTag` 改成 `ValueInput`/`ValueOutput` 时，
> **先数体内用了多少 `CompoundTag` 专属 API**（`put/getList/getCompound/contains/getXxxOrEmpty`）。
> - 0～1 处 ⇒ 改签名 + 换那几个调用，**能做**；
> - 多 ⇒ **必须重写体**，别指望桥。

### 顺带发现的一个真 bug
`GustEntity` 的两个方法**体是反的**：
```java
protected void readAdditionalSaveData(CompoundTag compoundTag) { compoundTag.put(…writeQuaternion…); }   // 读方法里写
protected void addAdditionalSaveData(@NotNull CompoundTag compoundTag) { …readQuaternion(compoundTag)…; } // 写方法里读
```
这是**移植过程中留下的逻辑错误**（不只是签名问题），修的时候要一并交换。


---

## R184（473 → 470，**−3**）：`fallOn` 的 `float` → `double`

### 事实（javap `net.minecraft.world.level.block.Block`）
```java
public void fallOn(Level, BlockState, BlockPos, Entity, double);      // 第 5 参是 double
```
项目里 3 个文件写的是 **`float`**：
```java
public void fallOn(final Level pLevel, final BlockState pState, final BlockPos pPos,
                   final Entity pEntity, final float pFallDistance)
```
**⇒ 只改这一个类型**（`float` → `double`），函数体不用动。

### 结果
`方法不会覆盖` **158 → 152（−6）**、总 **473 → 470（−3）**，解析期 0。

### 顺带 javap 出来、还没做的两族
```java
// net.minecraft.world.level.block.state.BlockBehaviour
protected int getLightBlock(BlockState);                                    // 只剩 1 参
protected ItemStack getCloneItemStack(LevelReader, BlockPos, BlockState, boolean);  // 4 参换了顺序/内容
```
- `getLightBlock`：项目写的是 `(BlockState, BlockGetter, BlockPos)` ⇒ 要确认体内是否用到后两个参数；
- `getCloneItemStack`：项目的参数表不同，得逐个别对。

### ★ 这条线的总结
到目前为止，`方法不会覆盖` 里被证实的**纯签名问题**有四种形态：
| 形态 | 例子 | 修法 |
|---|---|---|
| 多一个参数 | `neighborChanged(..., Orientation)`（R151）| 加参数 |
| 少参数 | `getLocalOffset(BlockState)` / `shouldRender(BlockState)`（R181）| 删参数 |
| **参数类型变宽** | **`fallOn(..., double)`（本轮）** | **只改类型** |
| 参数表整体换 | `getCloneItemStack(LevelReader, BlockPos, BlockState, boolean)` | 逐个对 |

**⇒ 遇到 `方法不会覆盖`：javap 父类 → 把两边参数表并排 → 只改不一样的**，这一步几乎总能用上。


---

## R185（470 → 468，**−2**）：两个"对齐父类"的小族

### ① `getLightBlock` —— 父类只剩 1 个参数
```java
// BlockBehaviour
protected int getLightBlock(BlockState);        // 1 参
// EnvelopeBlock:133（项目）
protected int getLightBlock(final BlockState state, final BlockGetter level, final BlockPos pos) {
    return 1;                                    // 体根本没用后两个参数
}
```
⇒ 删掉后两个参数即可。

### ② `getCloneItemStack` —— 8 处里 7 处已经对了
父类：
```java
protected ItemStack getCloneItemStack(LevelReader, BlockPos, BlockState, boolean);
```
我把全项目的 8 处声明都列出来比对：
- `EnvelopeBlock` / `PairedDockingConnectorBlock` / `LinkedTypewriterBlock` / `SpringBlock` /
  `SwivelBearingPlateBlock` / `SymmetricSailBlock` —— **参数表已经一致** ✓
- **只有 `EnvelopeEncasedShaftBlock:110`** 写成了
  `(BlockState state, HitResult target, LevelReader level, BlockPos pos, …)` —— **顺序完全不同** ✗

⇒ 只把这一个改成父类的顺序，函数体（返回一个常量）不用动。

### 结果
`方法不会覆盖` **152 → 148（−4）**、总 **470 → 468（−2）**，解析期 0。

### ★ 打这一桶的正确姿势（已经反复验证）
> **先数"已经写对的站点有几个"。**
> - 大部分已对（如本轮 7/8）⇒ 这是**单点参数顺序问题**，只对齐那一处；
> - 全都没对 ⇒ 才是批量替换。
>
> 反过来做（上来就批量改）会像 R169 那样把对的地方改坏。


<!-- ===== 从热层搬来的较早族行（20261017-114908）===== -->

| 族 | 结论 |
|---|---|
| ★★★ **`UIRenderHelper` 换包了**：`com.zurrtum.create.client.**foundation**.gui` → `com.zurrtum.create.client.**catnip**.gui`（按旧路径 javap 会**零命中**，要扫 jar 找）；`drawStretched` / `drawCropped` 现在是 **6 参**：`(GuiGraphics,int,int,int,int,TextureSheetSegment)` | 12 条 ⇒ **−6** | R179 |
| ★★ **1.21.11 全面删掉了 `zLevel` 那个 int**（GUI 改用 `nextStratum()`/`GuiRenderState`）⇒ UI 助手报「参数过多/无法应用」时**先怀疑 zLevel** —— 删掉倒数第二个实参即可 | —— | R179 |
| ★★★ **写侧要分两种**（本轮踩到）：① **继承来的** `SmartBlockEntity.write/saveAdditional(ValueOutput)` ⇒ 用桥可行；② **项目自己声明的** `write(CompoundTag, Provider, boolean)`（如 `AugerShaftBlockEntity`、`AnalogLeverBlockEntity`）⇒ **桥不管用**，要改它自己的声明 | —— | R180 |
| **`方法应用不到` 刷新后（26 种）**：`Sided.getLocalOffset` 6、`KeyMapping.matches` 6、`AnalogLeverBlockEntity.write` 4、`AugerShaftBlockEntity.write` 2、`SmartBlockEntity.saveAdditional` 2、`Shulker.getProgressAabb` 2、`GustParticle.renderRotatedQuad` 2 …（R179 的 12 条已清零）| —— | R180 |
| ★★★ **`ValueBoxTransform.Sided` 的两个方法只收 1 个 `BlockState`**：`Vec3 getLocalOffset(BlockState)` / `boolean shouldRender(BlockState)` —— 项目里那 3 个还是 3 参 `(LevelAccessor, BlockPos, BlockState)`。**体里只转给 `super` 的话，纯改签名即可** | 8 处 ⇒ **−7** | R181 |
| ★★ **`方法不会覆盖`(166) 里有一大批是「签名少参数」**：本次 `getLocalOffset`/`shouldRender` 一类就清掉 8 条 | —— | R181 |
| ★★★ **`方法不会覆盖`(174 raw) 的完整分布**（`analyze_override3.py` 读源码出）：`rotate` 12、`render`/`getMetaFactory`/`getCodec`/`getStreamCodec` 各 10、`save` 8、`neighborChanged` 8、`fallOn` 6、`getLocalOffset` 6、`streamCodec` 6、`registerAll`/`readAdditionalSaveData`/`addAdditionalSaveData`/`getRenderType`/`apply`/`mouseReleased`/`getTextureLocation` 各 4 | 见 R182 | R182 |


---

## R186（净 0）：把「输入事件化」认出来，别再一条条试

### 事实
```java
// net.minecraft.client.gui.components.AbstractWidget
public boolean mouseClicked(MouseButtonEvent, boolean);
public boolean mouseReleased(MouseButtonEvent);
// Screen —— javap 里已经没有 mouseReleased
```
项目里的写法：
```java
public boolean mouseReleased(final double mouseX, final double mouseY, final int button) { … }
```
⇒ 参数表从「三个原始值」变成「一个事件对象」。

配合 R175 的发现：
```java
public boolean KeyMapping.matches(KeyEvent);
public boolean KeyMapping.matchesMouse(MouseButtonEvent);
```

**⇒ 这是第五场「架构迁移」**（前面四场是：物品渲染 R116、方块 pipeline R113、粒子 extract R111、GUI render-state R156）。
共同点：**1.21.11 把"一堆散装参数"收成一个事件/状态对象。**

### 为什么这族不能一把梭
改 `mouseReleased(double,double,int)` → `mouseReleased(MouseButtonEvent)` 需要**构造** `MouseButtonEvent`，
而它的字段（x/y 用哪套坐标系、button、modifiers）得逐处确认；不同屏幕的语义还不一样。
**⇒ 属"逐点判断"，不是批量替换。**

### 同时把另外三族降级
| 族 | 判断 |
|---|---|
| `getRenderType()`（4）| 粒子体系迁移 ⇒ 设计级 |
| `getStreamCodec()` / `streamCodec()`（6+10）| 粒子 Data 的 codec 体系 ⇒ 设计级 |
| `getTextureLocation()`（4）| 实体渲染器进 render-state ⇒ 设计级 |

**⇒ 这一桶（`方法不会覆盖`）的"纯签名"红利已经吃完了**（R181 −7、R184 −3、R185 −2）。

### 本轮的实做
只做了瘦身（索引 17 → 10 行，热层 **10,203 → 8,064 B**），错误数不变。
**这是诚实的净 0**：本轮查清了"输入事件化"是整族而不是个别方法，避免了下轮继续一条条试。


---

## R187（468 → 466，**−2**）：`找不到符号` 按「归属」二分 —— 找到了 48 条便宜的

### 做法（可复用）
```python
# 1) 枚举项目 src 下所有 .java 的类名（本轮 825 个）
# 2) 逐条读编译日志的  符号: / 位置:
# 3) 用「位置」里的类名去比对：
#    - 在 825 里  ⇒ ① 我们自己的类 —— 便宜
#    - 不在        ⇒ ② 外部（Create / 原版）—— 多为 API 改名
#    - 位置为空    ⇒ ③ 需另查
```

### 结果
| 类别 | 条数 |
|---|---|
| ② 外部（Create/原版）| **208** |
| ① **我们自己的类** | **48** ← 便宜的那批 |
| ③ 无位置信息 | 36 |

### ① 的 TOP（都是"给自家类补方法"或"换现代 API"）
```
2x  BearingSlowdownController        类 ValueOutput
2x  EndSeaFadeTransformer            类 GlslTree / GlslSyntaxException      ← Veil 的
2x  AeroRegistrate                   方法 defaultCreativeTab(ResourceKey<CreativeModeTab>)
2x  ClientBalloonEffectRenderer      方法 onRenderLevelStage(Stage,Matrix4fc,Matrix4fc,int)
2x  BalloonLevelSavedData            类 Factory                             ← 设计级
2x  AltitudeSensorScreen             变量 BufferUploader / 方法 hasControlDown()
2x  LinkedTypewriterRenderer         方法 tick() / resetKeys()
2x  ThrottleLeverRenderer            方法 transformHandleExternal(...)
2x  SwivelBearingBlockEntity         变量 tag
```

### 本轮修的两处
**(1) `NavTableBlockEntity:256`** —— `ValueOutput` 没有 `put(String, Tag)`：
```java
tag.put("CurrentStack", ItemStack.OPTIONAL_CODEC.encodeStart(NbtOps.INSTANCE, this.getHeldItem()).getOrThrow());
// →
tag.store("CurrentStack", ItemStack.OPTIONAL_CODEC, this.getHeldItem());
```
原代码其实是在**手工做 `store` 做的事**，直接换成 `store` 即可。

**(2) `ClientBalloonEffectRenderer`** —— 这是**我们自己的桩**，缺 `onRenderLevelStage(...)`：
```java
public static void onRenderLevelStage(Object stage, Matrix4fc frustumMatrix, Matrix4fc projectionMatrix, int renderTick) {}
```
（空实现，台账已记「气球后处理待做」。）

⇒ `找不到符号` **290 → 286（−4）**、总 **468 → 466（−2）**，解析期 0。

### ★ 下一阶段的取舍
**① 只有 48 条，② 有 208 条。**
- ① 的每一条都可能是"加个方法就好"⇒ **继续优先打**；
- ② 的 208 条要逐族查上游 API ⇒ 慢。
**⇒ 先把 ① 抽干，再回头啃 ②。**


---

## R188（466 → 461，**−5**）：抽干 ① 的第一批 —— 空桩补方法

### R187 的分类还要再修正一次
① 那 44 条里，`AeroRegistrate` / `SimulatedRegistrate` 报的
`defaultCreativeTab(...)` / `menu(...)` **不是它们的**：
```java
public class SimulatedRegistrate extends CreateRegistrate { … }
public class AeroRegistrate extends SimulatedRegistrate { … }
```
方法缺在 **`CreateRegistrate`**（外部垫片）上 ⇒ 实际归 ②。
**⇒ 判断"是不是我们自己的"时，还要看它是不是 extends 了一个外部基类。**

### 真正的 ①：三个"只有构造器"的桩
扫描发现这三个类**整个文件只有一个 `(Object... args)` 构造器**：
| 桩类 | 调用点要的方法 | 站点数 |
|---|---|---|
| `LinkedTypewriterRenderer` | `tick()` / `resetKeys()` | 2 |
| `PlayerHoldingHandleRenderer` | `afterSetupAnim(...)` / `updatePlayerList(...)` | 2 |
| `ThrottleLeverRenderer` | `transformHandleExternal(...)` | 1 |

补法（本轮实际写入）：
```java
public static void tick() {}
public static void resetKeys() {}
public static void afterSetupAnim(final Object... args) {}
public static void updatePlayerList(final Object... args) {}
public static void transformHandleExternal(final Object... args) {}
```

### ★ 技巧：`Object...` 兜底
其中 `afterSetupAnim` 的调用点传的是 `HumanoidModel<CAP#1>` 这类**带捕获变量的泛型**，
写不出精确签名；`updatePlayerList` 传 `Collection<UUID>`。
**⇒ 一律用 `(final Object... args)`**：varargs 能接受任意实参，且不需要任何 import。

### 结果
`找不到符号` **286 → 276（−10）**、总 **466 → 461（−5）**，解析期 0。

### ① 还剩什么
剩下的大多是"换现代 API"型（`BufferUploader` 变量、`hasControlDown()`、`Factory` 类、
`ValueOutput` 类、`GlslTree`/`GlslSyntaxException`=Veil），以及个别"我们的类真缺字段"
（`DiagramEntity` 的 `HANGING_ENTITY`、`SwivelBearingBlockEntity` 的 `tag` 变量）。


---

## R189（净 0）：11 个失效的静态导入 —— 下一批现成靶子

### 用了项目自带的 `scan_missing_imports.py`
它把「项目 import 了、但所有 jar + 项目自身类里都找不到这个 FQN」的条目列出来：

```
com.zurrtum.create.foundation.data.ModelGen.customItemModel                 2 文件  (AeroBlocks)
com.zurrtum.create.content.contraptions.piston.MechanicalPistonBlock.isExtensionPole   2 文件
com.zurrtum.create.content.contraptions.piston.MechanicalPistonBlock.isPistonHead      2 文件
com.zurrtum.create.foundation.data.CreateRegistrate.connectedTextures       1 文件
com.zurrtum.create.api.behaviour.movement.MovementBehaviour.REGISTRY        1 文件
com.zurrtum.create.foundation.utility.RaycastHelper.getTraceTarget          1 文件
com.zurrtum.create.catnip.math.AngleHelper.angleLerp                        1 文件
com.zurrtum.create.client.foundation.block.connected.AllCTTypes.OMNIDIRECTIONAL  1 文件
dev.ryanhcode.sable.sublevel.render.vanilla.VanillaChunkedSubLevelRenderData     1 文件
com.zurrtum.create.compat.jei.GhostIngredientHandler                        1 文件
```
（脚本统计口径：9 个 jar / 5,789 个类 + 项目自身类 = 6,615 个 FQN。）

### 这些是什么
全部是 **`import static ...`**：它们导入的**成员名**在新版里没了（类还在，成员改名/移动）。
所以症状不是"import 报错"，而是**每个使用点各报一条「找不到符号」**。

### 本轮没动手的原因
每条都要先查**新名字**（`angleLerp` → ? / `getTraceTarget` → ? / `isExtensionPole` → ?），
是"查 API"型活，不是"改格式"型。本轮时间用在确认清单上，没有硬凑改动。

### 顺带确认一个设计级
```java
BufferUploader.drawWithShader(bufferbuilder.buildOrThrow());     // 3 处
```
`BufferUploader` 在 1.21.11 已随渲染系统重写（`RenderPass`/`MeshData`）而删除 ⇒ **暂挂**。

### 下一轮打法
按「一条静态导入 → 一次 javap → 一处替换」逐条烧，每条通常清 1～2 条错误；
优先 `MechanicalPistonBlock.isExtensionPole/isPistonHead`（涉及 4 个文件）和 `AngleHelper.angleLerp`。


<!-- ===== 从热层搬来的较早族行（20261017-115229）===== -->

| 族 | 结论 |
|---|---|
| ⚠⚠ **`neighborChanged`(8) 是幻影**：全项目 **14 处声明全都已经带了 `Orientation` 参数** ⇒ 报「方法不会覆盖」的真因在别处。**⇒ override 分析器的计数里混着幻影，别直接照着打** | —— | R182 |
| ⚠ **日志里的 `方法不会覆盖` 块不带方法名**（只有 `@Override` + 附近代码行）⇒ **必须用 `analyze_override3.py` 读源码**才知道是哪个方法 | —— | R182 |
| ⚠⚠ **桥是【单向】的**：`CompoundTag → ValueInput/ValueOutput` 可以（`TagValueInput.create` / `TagValueOutput.createWithContext`），但 **`ValueInput` 拿不回 `CompoundTag`**（`TagValueInput` 的 tag 字段私有）⇒ 凡形参改成 `ValueInput` 而体内要用 `getListOrEmpty` 这类 CompoundTag 专属方法的，**只能重写体** | 暂挂 | R183 |
| **`readAdditionalSaveData`/`addAdditionalSaveData` 的现状**：`DiagramEntity`、`LaunchedPlungerEntity` **已经是** `ValueInput`/`ValueOutput` ✓；`GustEntity`、`HoneyGlueEntity` 还是 `CompoundTag`，且它们的体用了 `put(String,Tag)`/`getListOrEmpty` ⇒ 属「要重写体」那一类 | 8 条暂挂 | R183 |
| ★★★ **`Block.fallOn` 的第 5 参从 `float` 变成 `double`**：`fallOn(Level, BlockState, BlockPos, Entity, **double**)` ⇒ 纯改类型即可 | 3 处 ⇒ **−3**（覆盖报错 −6）| R184 |
| ★★ **`方法不会覆盖` 的常见形态是「某个参数的类型/个数变了」**：`float→double`（本轮）、多一个 `Orientation`（R151）、少两个上下文参数（R181）⇒ **javap 父类，diff 参数表，只改不同的那一处** | —— | R184 |
| ★★★ **`getLightBlock`(2) / `getCloneItemStack`(2) 已解**：前者父类只剩 **1 参**（项目写 3 参，体只有 `return 1;`）；后者父类是 `(LevelReader,BlockPos,BlockState,boolean)`，项目 **8 处里 7 处已对**，只有 `EnvelopeEncasedShaftBlock` 参数顺序错 ⇒ **单点对齐** | 4 处 ⇒ **−2**（覆盖报错 −4）| R185 |
| ★★★ **打 `方法不会覆盖` 的正确姿势**：先数「**已经写对的站点有几个**」——若大部分已对（如 7/8），那就是**单点参数顺序问题**，只需对齐那一处，千万别批量改 | —— | R185 |


---

## R190（净 0）：一次重要的"撤回" —— 那份 11 条清单是误报

### 发生了什么
R189 我跑了 `scan_missing_imports.py`，拿到 11 条「import 了但 jar 里找不到 FQN」，
准备这轮照着打。先 javap 验了三条：

```java
// com.zurrtum.create.catnip.math.AngleHelper
public static float angleLerp(double, double, double);            // ← 存在！

// com.zurrtum.create.content.contraptions.piston.MechanicalPistonBlock
public static boolean isPiston(BlockState);
public static boolean isExtensionPole(BlockState);                // ← 存在！
public static boolean isPistonHead(BlockState);                   // ← 存在！
```

**三条全都存在。** 如果我照着清单改，会把**本来正确的代码改坏**。

### 工具为什么误报
`scan_missing_imports.py` 的判定方式是「把 import 的 FQN 当成**类名**去 jar/项目类里找」。
而 `import static com.x.Y.method;` 的 FQN 末尾是**方法名**，永远不可能作为类名存在 ⇒ **必然误报**。
（只有 `import a.b.C;` 这种**类型**导入，它的结论才可信。）

### 结论
- **该脚本只用于「普通类型 import」**；`import static` 一律要 javap 实证。
- R189 的那 11 条**作废**，不要照着打。

### 一个方法论上的提醒（值得记）
我这两轮的模式是：**先统计出清单 → 再动手**。这个模式本身没错，但
**统计脚本的判定口径必须和"我要修的东西"一致**：这次的脚本回答的是"这个 FQN 是不是一个存在的类"，
而我需要的是"这个**成员**是不是存在"。口径错位 ⇒ 结论作废。

**⇒ 以后凡是用脚本产出"待修清单"，先在清单里抽 1～3 条 javap/读源码核实口径。**


---

## R191（461 → 460，**−1**）：修回自己上一次的伤

### 症状
```
SwivelBearingBlockEntity.java:673   找不到符号
  符号: 变量 tag
  代码: this.lastException = AssemblyException.read(tag);
```
而这个文件的 `read` 方法签名是：
```java
protected void read(final ValueInput compound, final boolean clientPacket) { … }
```
参数叫 **`compound`**，文件里**根本没有叫 `tag` 的变量**。

### 原因
R178 我用一条全局正则把
```java
AssemblyException.read(compound, compound.lookup())   →   AssemblyException.read(tag)
```
推平了 —— **硬写了 `tag`**，没有管各文件里参数的真名。

### 修法与守卫
这次加了前置判断：
```python
if not re.search(r'void\s+read\(\s*(?:final\s+)?ValueInput\s+compound', text):
    continue      # 参数不叫 compound 的文件直接跳过
```
结果正确跳过了 `PhysicsAssemblerBlockEntity`（它的参数名不是 `compound`），只改 `SwivelBearingBlockEntity` 一处。

⇒ 总 **461 → 460（−1）**（raw −2），解析期 0。

### ★ 一条该进硬规则的教训
> **正则做"方法调用替换"时，替换文本里用到的方法名/变量名，必须来自"外层方法的真实签名"，不能硬编码。**

这也是我第三次因为"硬写标识符"翻车（前两次：R190 的假阳性清单、R169 的接收者混淆）。
**⇒ 凡是跨文件的批量替换，先抽 1 个文件确认参数名，再把名字作为变量传进替换模板。**

### 本轮没动的
`DiagramEntity:356` 的 `HANGING_ENTITY` —— 是"类里少了一个字段"，但字段类型（`Predicate`？`EntityTypeTest`？）
无法从上下文安全推断，宁可留着也不猜。


---

## R192（净 0）：把 `HANGING_ENTITY` 补回去，但计数没动

### 上下文（`DiagramEntity` 的"能否放置"判定）
```java
if (!blockstate.isSolid() && !DiodeBlock.isDiode(blockstate)) {
    return false;
}
return this.level().getEntities(this, this.getBoundingBox(), HANGING_ENTITY).isEmpty();
```
`getEntities(Entity, AABB, Predicate<? super Entity>)` ⇒ `HANGING_ENTITY` 必须是一个**谓词**。
语义上它筛的是"悬挂类实体"（画、物品展示框 —— 它们的共同父类是 `HangingEntity`），
目的是"这块地方已经挂了东西就不许再放"。

于是补了：
```java
private static final java.util.function.Predicate<net.minecraft.world.entity.Entity> HANGING_ENTITY =
        entity -> entity instanceof net.minecraft.world.entity.HangingEntity;
```

### 结果：460 → 460（净 0），但**没有引入新错**
这说明：
- 谓词的类型是对的（否则会新增「不兼容的类型」或「参数不匹配」）；
- 但**那条「变量 HANGING_ENTITY 找不到」的报错并不在这个文件**。

**⇒ R187 的归属分类是按「位置里的类名」匹配的**，而 `DiagramEntity` 这个名字既可能是**文件**，
也可能被别的文件的 `位置:` 提到 ⇒ **分类结果需要回到具体 file:line 才能确认**。

### 本轮怎么算
- **代码质量上**：补回了一个被移植过程丢掉的字段，语义明确，无害；
- **指标上**：净 0。

**⇒ 诚实记录：这一轮没有让编译错误减少。**


---

## R193（460 → 457，**−3**）：`KeyEvent` 是 record，包一层就行

### 事实（javap）
```java
public final class KeyEvent extends java.lang.Record implements InputWithModifiers {
    public KeyEvent(int, int, int);          // ← 3 个 int，直接 new
    public int input();  public int key();  public int scancode();  public int modifiers();
}
// net.minecraft.client.KeyMapping
public boolean matches(KeyEvent);
public boolean matchesMouse(MouseButtonEvent);
```

### 改法
```java
mapping.matches(key, scanCode)
// →
mapping.matches(new net.minecraft.client.input.KeyEvent(key, scanCode, 0))
```
第三个参数是 **modifiers**，鼠标/键盘没按修饰键时传 0。

三个站点（`LinkedTypewriterInteractionHandler` 2 处、`InteractCallback` 1 处）全部通过：
`无法将类 KeyMapping 中的方法 matches 应用到给定类型` **6 → 0**、总 **460 → 457（−3）**，解析期 0。

### ★ 修正 R186 的判断
R186 我写过：
> 「输入事件化」不是一行；得构造事件对象，属逐点处理。

**这句话一半是错的。** 事件对象确实是"要构造"，但 `KeyEvent` 是**3 个 int 的 record**，
构造它就是一行 —— 和"逐点语义判断"完全不是一回事。
**⇒ 教训：判"能不能一行解决"之前，先 javap 那个事件类有没有简单构造器。**

### 下一轮可以直接试
R186 说的 `mouseReleased(double, double, int)`（2 个屏幕、4 条）——
如果 `MouseButtonEvent` 也有 `(x, y, button)` 这类构造器，同样能一行包完。
**⇒ 下轮先 javap `MouseButtonEvent`。**


<!-- ===== 从热层搬来的较早族行（20261017-115549）===== -->

| 族 | 结论 |
|---|---|
| ★★★ **输入整体「事件化」了**（第五场架构迁移）：`KeyMapping.matches(KeyEvent)`（R175）+ **`AbstractWidget.mouseReleased(MouseButtonEvent)`**、`mouseClicked(MouseButtonEvent, boolean)`（本轮），**`Screen` 自己已无 `mouseReleased`** ⇒ 项目里 `mouseReleased(double,double,int)` 全要改，且得**构造事件对象** ⇒ 不是一行，属需逐点处理 | 4 条 + 6 条 | R186 |
| ⚠ **`getRenderType()` / `streamCodec()` / `getTextureLocation()` 三族看着都是「粒子/渲染器整体迁移」**，先别当签名问题打 | —— | R186 |
| ★★★★ **`找不到符号`(286) 按归属分类**【关键工具】：枚举项目全部 825 个类名，再读每条错误的 `位置:` ⇒ **② 外部类（Create/原版）208 条**、**① 我们自己的类 48 条**、③ 无位置 36 条。**① 那 48 条才是便宜的**（加个方法 / 换现代 API），外部 208 条多为 API 改名 | 见 R187 | R187 |
| ★★ **`ValueOutput` 没有 `put(String, Tag)`**：`X.put("K", codec.encodeStart(NbtOps.INSTANCE, v).getOrThrow())` 要改 `X.store("K", codec, v)` | 1 处 | R187 |
| ★★★ **「只有构造器的空桩」是 ① 里最肥的一类**：`LinkedTypewriterRenderer`(tick/resetKeys)、`PlayerHoldingHandleRenderer`(afterSetupAnim/updatePlayerList)、`ThrottleLeverRenderer`(transformHandleExternal) **各自只有一个 `(Object... args)` 构造器** ⇒ 补上缺失方法即清 **10 条 raw** | **−5** | R188 |
| ★★ **参数表不明/含泛型时用 `Object...` 兜底**：`public static void x(final Object... args) {}` 能接受任意实参（本轮 `afterSetupAnim`/`updatePlayerList` 就靠这个绕开 `HumanoidModel<CAP…>`）| —— | R188 |
| ⚠ **`AeroRegistrate`/`SimulatedRegistrate` 的缺口其实是 `CreateRegistrate` 的**：它们 `extends CreateRegistrate` ⇒ `defaultCreativeTab`/`menu` 报在子类名下，但缺的方法在**外部垫片类**上 ⇒ 属 ② 不是 ① | —— | R188 |


---

## R194（457 → 453，**−4**）：`MouseButtonEvent` 也是 record —— 局部别名法收工

### 事实（javap）
```java
public final class MouseButtonEvent extends java.lang.Record implements InputWithModifiers {
    public MouseButtonEvent(double, double, MouseButtonInfo);
    public double x();  public double y();  public int button();  public int modifiers();
}
public final class MouseButtonInfo extends java.lang.Record implements InputWithModifiers {
    public MouseButtonInfo(int, int);       // (button, modifiers)
}
```

### 改法（局部别名法，硬规则 ★40）
```java
public boolean mouseReleased(final net.minecraft.client.input.MouseButtonEvent event) {
    final double mouseX = event.x();
    final double mouseY = event.y();
    final int button = event.button();
    …函数体一个字都没改…
}
// 顺带把转发调用也换掉：
super.mouseReleased(mouseX, mouseY, button)   →   super.mouseReleased(event)
```
两个文件（`AltitudeSensorScreen`、`DiagramScreen`）各一处签名 + 一处 `super` 调用。

### 结果
- `无法将接口 ContainerEventHandler 中的方法 mouseReleased 应…` **4 → 0**
- `方法不会覆盖或实现超类型的方法` **148 → 144（−4）**
- 总 **457 → 453（−4）**，解析期 0

### ★ R193 的教训确认可以推广
`KeyEvent` 和 `MouseButtonEvent` **都是普通 record，构造器都是位置参数**：
```java
new KeyEvent(key, scanCode, 0)                                        // R193
new MouseButtonEvent(x, y, new MouseButtonInfo(button, 0))            // 本轮
```
**⇒ 所谓"输入事件化迁移"不是语义工作，是机械工作**：
查 record 构造器 → 换形参 → 注入同名局部变量 → 体不动。

**⇒ 下次再遇到 `mouseClicked` / `keyPressed` / `charTyped` 这类，直接照这个三步走。**


---

## R195（净 0）：剩余族的规模普查 + 发现一处「半拉子迁移」

### 普查（`analyze_override3.py` + 日志计数）
| 族 | 条数 | 性质 |
|---|---|---|
| **`getStreamCodec`(10) + `streamCodec`(6)** | **16** | 最大的一族，粒子/属性的 codec 体系 |
| `getRenderType` | 4 | 粒子体系整体迁移 |
| `mouseReleased` | 4 | **其实是旧日志**（R194 已清零） |
| `keyPressed` / `charTyped` | 各 2 | **不在「方法不会覆盖」里**，是别处报的 |
| `InputConstants` 相关提及 | 26 行 | 分散 |

### 发现：`NameplateScreen` 有一处「半拉子迁移」
```java
L84:  public boolean keyPressed(final KeyEvent event) {
L89:      return this.nameField.keyPressed(pKeyCode) || super.keyPressed(event);
```
**形参已经改成 `event`，但函数体里还在用旧名字 `pKeyCode`** —— 这是之前某轮"只换签名、忘了体"留下的。
`charTyped` 同理（`pCodePoint`）。

**⇒ 这类"签名换了、体没跟上"是 R181/R183 那批换签名的常见残留**，
以后做签名替换时应该在同一个脚本里**同时检查体里的旧标识符是否还有定义**。

### 为什么本轮没改
`nameField` 是原版的文本框，它自己的 `keyPressed/charTyped` 在 1.21.11 收什么参数还没确认；
贸然把 `pKeyCode` 改成 `event.key()` 可能只是把错误从一处挪到另一处。
**⇒ 记下来，等确认 `EditBox` 的新签名后一次改干净。**

### 下一轮的目标
**`getStreamCodec`/`streamCodec` 16 条** —— 这是目前最大的一族。
先 javap `ItemAttribute`（`BlockBouncinessItemAttribute` 的实现目标）和
`ParticleType`/`ParticleOptions` 里的 codec 方法，看是不是"换成 `StreamCodec` 的新基类方法"这种机械活。


---

## R196（净 0）：`streamCodec` 真名已确认；但**分析器的族计数第三次误报**

### 真签名（javap）
```java
// net.minecraft.core.particles.ParticleType
public abstract MapCodec<T> codec();
public abstract StreamCodec<? super RegistryFriendlyByteBuf, T> streamCodec();   // ← 就是 streamCodec
```
项目里 8 个 `*ParticleData` 写成了 `getStreamCodec()` ⇒ **名字确实写错了**，本轮全部改成 `streamCodec`（8 文件 8 处）。

### 结果：**904 → 904，直方图完全一样**
改名是**语义正确**的（`ParticleType` 的方法就叫 `streamCodec`），但**对错误数毫无影响**。

### ⇒ 结论：`analyze_override3.py` 报的族计数是【幻影】
它把**当前源码**和**旧日志的行号**拼在一起，所以会把"现在其实没报错的方法"也算进统计。
- R182：`neighborChanged` 8 条 —— 全项目 14 处声明**都是对的**（幻影）
- R195/R196：`getStreamCodec` 10 条 / `streamCodec` 6 条 —— 改了 8 处，**一条都没动**（幻影）

**⇒ 这是第三次了。从今以后：**
> **`analyze_override3.py` 只能用来"找候选行"，绝不能把它的计数当工作量。**
> 要确认某族真有 N 条，必须回到**原始日志**按 `符号:` 行统计。

### 本轮的实际产出
- 8 个文件的 `getStreamCodec` → `streamCodec`（**正确的 API 名**，保留）
- 无新增错误、无错误减少
- **换来一条纪律**：不再拿分析器计数当工单

### 下一轮
回到**原始日志**重新统计真族：只按 `符号:` 行分组（R171 的老办法），
不再用源码分析器的输出。


---

## R197（净 0）：终于从**原始日志**建了真工单

### 方法（R171 的老办法，这次做对了）
逐行扫日志，把每个错误块解析成 `{文件, 行, 消息, 符号, 位置}`，再按 **(消息类别, 符号)** 精确分组。
**不碰 `analyze_override3.py`。**

### 真 TOP（904 块 / 191 组合）
| 类别 | 条数 | 有没有 `符号:` |
|---|---|---|
| 找不到符号 | **274** | 有 |
| 不兼容的类型 | **178** | 无 |
| 方法不会覆盖 | **144** | 无 |
| 方法应用不到 | **76** | 无 |
| 程序包不存在 | **22** | 有 |

`找不到符号` 里最集中的符号：
```
 8x 类 Factory          8x 方法 getName()       8x 方法 register()
 6x 方法 put(String,ListTag)                     6x 变量 BufferUploader
 6x 方法 onRemove(...)                           6x 方法 bufferSource()
 6x 变量 RULE_DOBLOCKDROPS                       4x 类 ValueOutput
 4x 方法 getOwner()      4x 方法 getList(String,byte)   4x 方法 pickSprite(SpriteSet)
```

### `程序包不存在` 的 22 条（最像"一次能清一片"的）
```
 6x  io.github.ocelot.glslprocessor.api          ← Veil 的 GLSL 处理器
 4x  io.github.ocelot.glslprocessor.api.node     ← 同上
 2x  net.neoforged.neoforge.common.data          ← 残留 NeoForge
 2x  net.neoforged.neoforge.capabilities         ← 同上
 2x  net.neoforged.neoforge.fluids               ← 同上
 2x  net.neoforged.neoforge.fluids.capability    ← 同上
 2x  LayeredDraw                                 ← 1.21.11 已删
 2x  IFluidHandler                               ← NeoForge 流体能力
```

### ★ 关键发现：这些**全在 `src/excluded-wip`**
```
excluded-wip\EndSeaFadeTransformer.java        5 个 glslprocessor import
excluded-wip\AeroBlocks.java                   neoForge ConfiguredModel / Tags
excluded-wip\AeroPonderTags.java               neoForge BlockTagsProvider / DeferredRegister
excluded-wip\DirectionalGearshiftGenerator.java neoForge ModelFile
excluded-wip\LinkedTypewriterItemBindHandler.java  net.minecraft.client.gui.LayeredDraw
excluded-wip\DockingConnectorScenes.java       neoForge IFluidHandler
```
而且它们**大多本来就是 datagen**（`AeroBlocks`、`AeroPonderTags`、`*Generator`）——
而 R152 已经记录过「两个 mod 的 block/item tag datagen 已整批移除」。

### 但**本轮没有排除它们**，原因
**R171 的教训：直接把 `excluded-wip` 整体排掉，错误数从 453 涨到 +758。**
因为别的代码引用这些类。**⇒ 排除前必须逐个做「零引用」检查**（硬规则 12）。
本轮时间不够做完整的引用图，硬排会重演 R171。

### 下一轮
1. 对这 6 个文件逐个跑「零引用」检查（`grep 类名` 排除自身 + 注释）；
2. 零引用的 ⇒ 加进 `build.gradle` 的 exclude，一次可能清 **10～16 条**；
3. 有引用的 ⇒ 反过来修调用方（或给该类补最小桩）。


---

## R198（453 → 437，**−16**）：定向排除成功 —— 本阶段最大单轮收益

### 做法：先零引用检查，再决定排不排
对 6 个"缺包"的文件逐个统计**被引用次数**（排除自身、排除注释行）：

| 文件 | 被引用 | 结论 |
|---|---|---|
| `EndSeaFadeTransformer` | **2**（`SimulatedClient` 的 import + `addPreprocessor`） | ✅ 排除 + 删这 2 行 |
| `AeroPonderTags` | **1**（`AeroPonderPlugin:28`） | ✅ 排除 + 删这 1 行 |
| `DockingConnectorScenes` | **1**（`SimPonderScenes:52`） | ✅ 排除 + 删这 2 行 |
| `DirectionalGearshiftGenerator` | 4（2 真实） | 边缘，暂缓 |
| `LinkedTypewriterItemBindHandler` | 6 | 需要补桩，不是排除 |
| `AeroBlocks` | **95** | ❌ **绝对不能排** |

### 实际改动
1. `build.gradle` 加 3 条 `exclude`（带注释说明为什么）；
2. 删掉 5 行调用点（`AeroPonderPlugin` 1 行、`SimPonderScenes` 2 行、`SimulatedClient` 2 行）。

### 结果
```
程序包 io.github.ocelot.glslprocessor.api       6 → 0
程序包 io.github.ocelot.glslprocessor.api.node  4 → 0
找不到符号                                     274 → 264  (−10)
总条数 904 → 872；compileJava 453 → 437 (−16)
```

### ★ 这就是 R171 反过来的那次
R171：**整批**排 `excluded-wip` ⇒ 453 变成 +758（因为 `AeroBlocks` 这种枢纽被排掉了）。
本轮：**逐个**做零引用检查 ⇒ **−16**。

**⇒ 可复用的判据：**
> 一个文件因为"包/类不存在"而报错时，**先数它被谁引用**。
> - **≤2 处，且是"import + 一处注册调用"** ⇒ 排除该文件 + 删掉调用点（**净赚**）；
> - **几十上百处** ⇒ 它是枢纽，**永远不要排**；
> - **3～6 处** ⇒ 看调用方能不能改成不依赖它（补桩或内联）。

### 如实记录的功能性削减（本轮新增 3 条）
1. **End Sea 分层后处理（Veil GLSL）** —— 彻底移除（之前在削减清单里是"缺失"，现在是"删除代码"）；
2. **航空学的 Ponder 标签注册** —— 没有标签了（ponder 场景仍在）；
3. **对接连接器的 Ponder 场景** —— 少一个演示。

**⇒ 这三条都是"内容缺失"，不是"藏活"**：代码确实不参与构建了，必须在交付说明里写清楚。


---

## R199（净 0）：工单刷新 —— `找不到符号` 桶已基本清空

### 做法
写了个独立脚本 `queue.py`（只读原始日志，不碰源码分析器），按错误块的
`file:line` + `符号:` + `位置:` + 消息首句分组。

### 新分布（R198 之后，日志 phase4-compile-296）
| 类别 | 条数 | 变化 |
|---|---|---|
| 不兼容的类型 | **178** | 没动 |
| 方法不会覆盖 | **144** | 从 148 微降 |
| 方法应用不到 | **76** | 没动 |
| **抽象方法未实现** | **56** | ← **新的第二大桶** |
| **找不到合适的重载** | **56** | ← **同上** |
| 类型参数越界 | 8 | |
| 类重复 | 4 | |
| for-each 不适用 | 4 | |
| 无法访问 class_2248 | 4 | |
| **程序包不存在** | **2** | 从 22 降到 2 ✅ |
| **找不到符号** | **个位数** | 从 274 降到个位数 ✅ |

**⇒ R198 那一刀（定向排除）+ 之前几轮的清理，把"缺包/缺符号"这两个最大桶基本清空了。**

### 脚本的一个已知缺陷（别被它误导）
`queue.py` 里"块起始行"的判定是 `^.+\.java:\d+:`，但日志里
**`@Override` 上下文行也长这样**，所以会把 `符号:` 挂到上下文块上 ——
**⇒ 类别合计可信（178/144/76/56/56），但"按符号分组"的明细不可信。**
改进方向：只在"该行后面紧跟代码行与 `符号:`"时才算块首；或直接按 `位置:` 行分组。

### 新的两个主战场
**(1) 抽象方法未实现 56** —— "X 不是抽象的, 并且未覆盖 Y 中的抽象方法 Z"
⇒ 多半是**给类补一个方法**（R188 那套"空桩补方法"就能吃）。

**(2) 找不到合适的重载 56**，其中带具体签名的：
```
 8x  对于 getKey(int,int), 找不到合适的方法
 8x  对于 blit(Identifier,int,int,int,int,int,int), 找不到合适的方法   ← zLevel 少了两个 int
 4x  对于 create(Level), 找不到合适的方法
 4x  对于 SingleQuadParticle(ClientLevel,double×6), 找不到合适的构造器
 4x  对于 of(TagKey<Item>), 找不到合适的方法
 4x  对于 save(RegistrateRecipeProvider,Identifier), 找不到合适的方法
```
**`blit` 那 8 条最像机械活**：1.21.11 删掉了 `zLevel`，把签名里的两个 int 去掉即可。

### 下一轮
先吃 **`blit` 8 条**（机械），再看 **`抽象方法未实现` 56** 里有多少是"补个空方法就好"。


---

## R200（437 → 435，**−2**）：`blit` 现在要 `RenderPipeline` 当第一个参数

### 事实（javap `GuiGraphics`）
```java
public void blit(RenderPipeline, Identifier, int, int, float, float, int, int, int, int);        // 10 参
public void blit(RenderPipeline, Identifier, int, int, float, float, int, int, int, int, int);   // 11 参
// 以及一个形状完全不同的：
public void blit(Identifier, int, int, int, int, float, float, float, float);                    // 9 参
```
`net.minecraft.client.renderer.RenderPipelines` 里有：
```java
public static final RenderPipeline GUI_TEXTURED;
```

### 项目里的写法与改法
```java
graphics.blit(BAR.location, x, y, BAR.startX, BAR.startY, BAR.width, BAR.height - highMax);
// →
graphics.blit(net.minecraft.client.renderer.RenderPipelines.GUI_TEXTURED,
              BAR.location, x, y, BAR.startX, BAR.startY, BAR.width, BAR.height - highMax,
              BAR.width, BAR.height);
```
最后两个参数是 **textureWidth / textureHeight**，这里取同一个 `GuiSprite` 自己的尺寸
（Create 的 `GuiSprite` 惯例：`location` 指向图集里的一个子区域，宽高就是该 sprite 的尺寸）。

两个站点：`AltitudeSensorScreen:94`、`ModulatingLinkedReceiverScreen:142`。

### 结果
`对于 blit(…) 找不到合适的方法` **6 → 2（−4）**、总 **437 → 435（−2）**，解析期 0。
剩下 2 条不是 `X.location` 这个形状，要单独看。

### ★ 可以推广的一点
1.21.11 把**渲染管线**变成了显式参数。凡是"画东西"的 API 报「找不到合适的方法」，
**先看新版第一个参数是不是 `RenderPipeline`**，然后在 `RenderPipelines` 里找对应的常量
（GUI 文本贴图 = `GUI_TEXTURED`，纯色 = `GUI`，文字 = `GUI_TEXT`）。

---

## 半程小结（第 200 / 400 轮）

### 数字
| 节点 | 错误数 |
|---|---|
| 接手时（打开 exclude 的真实基线）| **2,159** |
| 第 100 轮 | 约 570 |
| 第 198 轮 | 453 |
| **第 200 轮** | **435** |

**⇒ 已消除 1,724 条（79.8%）**，解析期始终为 0。

### 这 100 轮（R101–R200）真正有效的杠杆
1. **打桩**（数十个渲染器/Visual/粒子类）—— 一次性几百条；
2. **定向排除 + 零引用检查**（R198 的 −16 是典型）；
3. **"空桩补方法" + `Object...` 兜底**（R188 的 −5）；
4. **输入事件 record 就地构造 + 局部别名法**（R193/R194 各 −3/−4）；
5. **父类签名 diff**（R181/R184/R185 各 −7/−3/−2）。

### 这 100 轮浪费时间的地方（教训）
1. **信任不可靠的清单**：R189 的静态导入误报、R195/R196 的幻影族计数 —— 合计浪费约 5 轮；
2. **单条收益 1 条的小改动**（R191/R192）—— 应当成族打；
3. **"半拉子迁移"残留**（R195 的 `NameplateScreen`）—— 换签名时没检查体。

### 剩下 200 轮的现实判断
435 条里，**`不兼容的类型` 178 + `方法不会覆盖` 144 + `方法应用不到` 76 = 398 条（92%）**，
这三类都**没有 `符号:` 行**，必须逐个看源码 + javap 才能定方案。
按"一次一族、每族 2～8 条、每轮 1 族"的经验，200 轮**理论上够**，
但前提是**不再出现净 0 的轮次**，且每次改动都要先验证判据。


---

## R201（435 → 424，**−11**）：`ValueBoxTransform` 整个接口都只剩 `BlockState`

### 真签名（javap `ValueBoxTransform`）
```java
public abstract Vec3 getLocalOffset(BlockState);
public abstract void  rotate(BlockState, PoseStack);      // ← 2 参，没有 LevelAccessor/BlockPos
public          boolean shouldRender(BlockState);
```
三个方法**全部不再收 `(LevelAccessor, BlockPos)`**。

### 项目里的两种形状
我把全项目的 `void rotate(` 都列出来比对：
- **已经对的 6 处**（2 参）：`LaserPointerBlockEntity`、`LaserSensorBlockEntity`、
  `OpticalSensorBlockEntity`（2 个内部类）、`SteeringWheelBlockEntity`、`TorsionSpringBlockEntity`
- **还没改的 6 处**（4 参）：`GimbalSensorBlockEntity:520`、`PortableEngineBlockEntity:126`、
  `RedstoneAccumulatorBlockEntity:189`、`RedstoneInductorBlockEntity:185`、
  `SteamVentBlockEntity:404`、`LinkedReceiverFrequencySlot:43`

### 改法（只改签名，体不动）
```java
public void rotate(final LevelAccessor levelAccessor, final BlockPos blockPos,
                   final BlockState blockState, final PoseStack ms)
// →
public void rotate(final BlockState blockState, final PoseStack ms)
```
**体里并没有用到 `levelAccessor` / `blockPos`** ⇒ 删掉这两个参数后**没有产生任何新错误**（这是关键验证）。

### 结果
`方法不会覆盖或实现超类型的方法` **144 → 132（−12）**、总 **435 → 424（−11）**，解析期 0。

### ★ 这是 R181 的同一套
R181 修的是 `getLocalOffset` / `shouldRender`（同样少了两个上下文参数），本轮修 `rotate`。
**⇒ `ValueBoxTransform` 这三个方法是同一场变更**：1.21.11 把"上下文参数"从这层接口里拿掉了。
**⇒ 以后凡是 `implements/extends ValueBoxTransform` 的类报「未覆盖」，先看这三个方法是不是还带着
`(LevelAccessor, BlockPos)`。**

### 顺带记：`抽象方法未实现`(56) 的分布
```
14x getMetaFactory   ← *ParticleData 缺 ICustomParticleDataWithSprites.getMetaFactory
10x rotate           ← 本轮已清
 6x getLayer         ← SingleQuadParticle.getLayer（粒子体系）
 6x packetCodec
 4x addAdditionalSaveData / apply / createRenderState
 2x getSlot / dropItem / getArmPose / reload
```
**`getMetaFactory` 14 是下一个大目标**，但 `ICustomParticleDataWithSprites` 不在 Create 的 jar 里
（说明它是**项目自己的接口**），得先在项目里找到它的声明再定方案。


---

## R202（净 0）：`getMetaFactory` 14 条 —— 接口名是单数还是复数？

### 查到的三条事实
1. **项目里的写法**（以 `AirPoofParticleData` 为例）：
```java
import com.zurrtum.create.foundation.particle.ICustomParticleDataWithSprite;   // ← 单数 Sprite
public class AirPoofParticleData implements ParticleOptions, ICustomParticleDataWithSprite<AirPoofParticleData> {
    @Override
    public Function<SpriteSet, ParticleProvider<AirPoofParticleData>> getMetaFactory() { … }   // ← 已经实现了
}
```
2. **报错文本说的是复数**：`未覆盖 ICustomParticleDataWithSprite**s** 中的抽象方法 getMetaFactory`
3. **8 个 `*ParticleData` 全都已经写了 `getMetaFactory()`**，签名都是
   `Function<SpriteSet, ParticleProvider<T>> getMetaFactory()`。

**⇒ 也就是说：方法已经存在，但编译器认为"没覆盖"** —— 这说明
**报错里那个 `ICustomParticleDataWithSprites`（复数）和项目 import 的
`ICustomParticleDataWithSprite`（单数）是两个不同的接口**，
而某个基类/注册路径用的是复数那个。

### 下一步（本轮没动手的原因）
必须先在 **Create 的 jar 里把两个名字都查一遍**：
- 单数存在吗？它的 `getMetaFactory` 返回什么？
- 复数存在吗？还是只出现在**项目自己的某个基类**上？

我的扫描脚本这次漏了（`import os` 忘写 + 过滤条件太窄），所以只拿到"8 个实现都在"这个结论，
**不足以判断该删方法、还是改接口、还是改返回类型**。
**⇒ 硬猜会像 R196 那样净 0，所以停在这里。**

### 已排除的可能
- 不是"方法不存在"（8 个都写了）；
- 不是"参数不对"（都无参）；
- 大概率是**返回类型**或**实现的接口族**不匹配。


<!-- ===== 从热层搬来的较早族行（20261017-120356）===== -->

| 族 | 结论 |
|---|---|
| ⚠ **`BufferUploader.drawWithShader(...)`(3) 属设计级**：`BufferUploader` 在 1.21.11 已随渲染系统重写而删除 | 暂挂 | R189 |
| ⚠⚠⚠ **R189 的 11 条清单【是误报】**：`scan_missing_imports.py` 把每个 `import static a.b.C.member` 的**整个 FQN 当类名去解析**，所以**方法/字段永远解析不到** ⇒ 假阳性。javap 实测 `AngleHelper.angleLerp` / `MechanicalPistonBlock.isExtensionPole` / `isPistonHead` **全都存在**。**⇒ 该脚本只能用于「普通类型 import」，不能用于 `import static`** | 作废 R189 | R190 |
| ★★★ **R178 的自伤已修**：那次我把 `AssemblyException.read(compound)` 全局换成 `read(tag)`，但 `SwivelBearingBlockEntity` 那个 `read` 方法的参数叫 **`compound`** ⇒ 613 行报「变量 tag 找不到」。本轮改回 `read(compound)` | −1 | R191 |
| ★★★ **正则替换必须按「外层方法的真实参数名」参数化**：不要硬写 `tag`。本轮用 `if not re.search(r'void read\(\s*(?:final\s+)?ValueInput\s+compound', t): 跳过` 做守卫，结果正确跳过了 `PhysicsAssemblerBlockEntity`（它的参数名不同）| —— | R191 |
| ⚠ **`DiagramEntity.HANGING_ENTITY` 已按语义补上但【计数未动】**：补的是 `Predicate<Entity>` = `e -> e instanceof HangingEntity`，语义与调用点（能否放置的判定）吻合，且没有引入新错 ⇒ 但总数 460→460，说明**那条报错的位置不在这个文件**（R187 的归属分类是按类名匹配的，同名变量可能出现在别处）| 净 0 | R192 |
| ⚠ **`getRenderType()` / `streamCodec()` / `getTextureLocation()` 三族看着都是「粒子/渲染器整体迁移」**，先别当签名问题打 | —— | R186 |
| ★★★ **`KeyEvent` 就是个 3 参 record，就地构造即可**（推翻 R186 的部分判断）：`public KeyEvent(int, int, int)` ⇒ `mapping.matches(key, scanCode)` 改成 `mapping.matches(new KeyEvent(key, scanCode, 0))`（第 3 参是 modifiers，0 = 无）| 3 处 ⇒ **−3** | R193 |
| ★★★ **输入事件类都是 record，就地构造**：`new KeyEvent(key,scanCode,0)`、`new MouseButtonEvent(x,y,new MouseButtonInfo(button,0))` ⇒ **换形参 + 注入同名局部变量 + 体不动**（★40）| KeyMapping 6→0、mouseReleased 4→0 | R193/R194 |
| ⚠ **`NameplateScreen:89/98` 是「半拉子迁移」**：形参已改 `event`，体内仍用旧名 `pKeyCode`/`pCodePoint` ⇒ **换签名时要同时检查体内旧标识符是否还有定义** | 待修 | R195 |
| ⚠⚠⚠ **`analyze_override3.py` 的族计数【是幻影】**（第三次）：R182 `neighborChanged` 8 条全对；R195/196 `getStreamCodec` 10 条 → 改 8 处后**直方图一模一样** ⇒ **该脚本只能找候选行，不能当工作量**；要数真族必须回原始日志按 `符号:` 分组 | 见 R196 | R196 |


---

## R203（净 0）：`getMetaFactory` 14 条的真病因 —— **shim jar 用的是中间名**

### 三步排查的结果
1. **Create 1.21.11 的 jar 里根本没有 `CustomParticleData` 这个路径** ⇒ `ICustomParticleDataWithSprite`
   **不是 Create 的接口**；
2. **项目源码里也没有它的声明**（`grep interface/class ICustomParticleData` = 0），
   `src/stub` 里也没有；
3. 那它从哪来？—— **`work\aero-port\libs\` 里的 shim jar**。

### 真正的报错原文（不是"缺方法"）
```
返回类型 Function<SpriteSet, ParticleProvider<GustParticleData>>
与      Function<class_4002, class_707<GustParticleData>> 不兼容
```
`class_4002` / `class_707` 是 **intermediary（中间名）**，不是 mojmap 名。
说明**那个 shim jar 里编译出的接口签名是用 1.21.1 时代的中间名生成的**，
而我们的源码用的是 mojmap 名 ⇒ **两者对不上**。

### 结论
**这不是源码问题，是依赖问题。** 14 条 `getMetaFactory` 不可能靠改 8 个 `*ParticleData` 解决 ——
必须让那个 shim jar 重新用**当前映射**生成。

### 这与台账里一条待办吻合
「Remap `create-fly-helpers-shim.jar`，清掉 4 条 `class_2248` 错误（需要 `CreateRegistrate` 等）」——
**同一个根因**：shim 是旧映射编出来的。
⇒ 本轮把 14 条 `getMetaFactory` 也归到这个待办名下，**不再当源码族打**。

### 记一笔方法论
我前两轮差点又去改源码（删方法/改返回类型），**幸好先按了 javap 与"报错原文"两步**：
- 报错里的**中间名**（`class_xxxx`）是"依赖映射不一致"的**铁证**；
- 凡看到 `class_数字` 出现在报错里，**不要改源码**，去查依赖 jar 的映射。

**⇒ 新硬规则候选：报错里出现 `class_\d+` ⇒ 问题在依赖的映射，不在源码。**


---

## R204（424 → 415，**−9**）：shim 为什么是中间名 —— `implementation` 不 remap

### 一句话根因
```gradle
modImplementation files("../libs/create-fly-1.21.11-6.0.9-5.jar")     // ← 会被 Loom remap 成 mojmap
modImplementation files("../libs/sable-fabric-1.21.11-…jar")          // ← 同上
implementation     files("../libs/create-fly-registrate-shim.jar")    // ← ★ 不 remap，保持 intermediary
implementation     files("../libs/create-fly-helpers-shim.jar")       // ← ★ 同上
```
**⇒ 凡挂在 `implementation files(...)` 上的 jar，里面的类型名全是 `class_xxxx`，
mojmap 源码永远对不上。**

### 反编译那个接口（javap）
```java
public interface ICustomParticleDataWithSprite<T extends class_2394> extends ICustomParticleData<T> {
    Function<class_4002, class_707<T>> getMetaFactory();
}
public interface ICustomParticleData<T extends class_2394> {
    ICustomParticleData.Deserializer<T> getDeserializer();
    MapCodec<T> getCodec(class_2396<T>);
    void writeToNetwork(class_2540);
    default class_2396<T> createType();
}
```
`class_4002` = `SpriteSet`、`class_707` = `ParticleProvider`、`class_2394` = `ParticleOptions`、
`class_2396` = `ParticleType`、`class_2540` = `FriendlyByteBuf`。
**形状完全一样，只是名字是中间名** ⇒ 编译器认为 `Function<SpriteSet,…>` ≠ `Function<class_4002,…>`。

### 本轮的改动
把 8 个 `*ParticleData` 的 `implements ICustomParticleDataWithSprite<X>`（连同 import）去掉，
并把 `getMetaFactory()` 上那个已经无意义的 `@Override` 删掉。

### 结果（有得有失，但净赚）
```
方法不会覆盖        132 → 128   (−4)   ← 14 条 getMetaFactory 里清掉了一部分
不兼容的类型: 无法推断类型变量 D   0 → +14   ← ★ 副作用：丢掉接口后 MapCodec 推断不出 T 了
总条数              846 → 828
compileJava         424 → 415   (−9)
```
**⇒ 净 −9，保留这个改动。** 但那 14 条 `无法推断类型变量 D` 是新增的，下一步要处理。

### ★ 这条教训值得单列
> **`build.gradle` 里 `implementation files(...)` = 不 remap。**
> 这类 jar 里的类型一律保持 intermediary 名，**mojmap 源码无法与其类型互通**。
> ⇒ 只适合放"不含 Minecraft 类型的纯工具类"，**不能放带 MC 泛型签名的接口**。
>
> **⇒ 判断依据：报错里出现 `class_\d+`，先去看那个类来自哪个 `files(...)`，确认它挂的是
> `implementation` 还是 `modImplementation`。**


---

## R205（415 → 413，**−2**）：`Quaternionfc` → `Quaternionf` 的箭头不匹配

### `无法推断类型变量 D` 的真相
那 14 条其实是一条类型错的**连环报错**：
```
(参数不匹配; lambda 表达式中的返回类型错误
无法推断类型变量 R
(参数不匹配; 构造器引用无效
不兼容的类型: Quaternionfc 无法转换为 Quaternionf))
```
根子在 `RecordCodecBuilder`：
```java
public record GustParticleData(Quaternionf orientation) implements ParticleOptions {
    private static final MapCodec<GustParticleData> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
            ExtraCodecs.QUATERNIONF.fieldOf("orientation").forGetter(o -> o.orientation)
    ).apply(instance, GustParticleData::new));      // ← 就是这一行
}
```
- `ExtraCodecs.QUATERNIONF` 是 **`Codec<Quaternionfc>`**（**接口**名）；
- record 的分量声明成了 **`Quaternionf`**（**具体类**）；
- 所以 `.apply(instance, GustParticleData::new)` 需要 `Function<Quaternionfc, GustParticleData>`，
  而构造器要 `Quaternionf` ⇒ **方法引用无法桥接这个差异** ⇒ 连环报错。

### 改法（方法引用 → lambda）
```java
).apply(instance, __q -> new GustParticleData(new org.joml.Quaternionf(__q)));
```
`Quaternionf` 有一个收 `Quaternionfc` 的拷贝构造器，所以一句就够。

**结果**：`GustParticleData` 的连环错消失，总 **415 → 413（−2）**（raw −4），解析期 0。

### ★ 模式（值得记）
> 凡 `RecordCodecBuilder.mapCodec(...).apply(instance, X::new)` 报
> **`参数不匹配; 构造器引用无效`** 或 **`无法推断类型变量 R`**：
> **比一比"字段 codec 产出的类型"和"构造器参数的类型"**。
> 常见就是"接口 vs 具体类"（如 `Quaternionfc` / `Quaternionf`、`List` / `ArrayList`）。
> **方法引用桥不了，改成 lambda 在里面显式构造即可。**

### 剩下的
其余 `*ParticleData` 里带 `Quaternionf` 分量的，若也是这个形状，按同一改法处理。
本轮只改了 `GustParticleData` 一个（确认有效），下一轮扫其余同类。


---

## R206（净 0）：`不兼容的类型`(178) 按「源→目标」聚合 —— 找到 42 条的第一大族

### 方法
`incompat_queue.py`：正则抓 `不兼容的类型: X 无法转换为 Y`，按 (X, Y) 配对计数。
**这是继"按 `符号:` 分组"之后第二个有效的分桶口径。**

### 结果（35 种组合，TOP）
```
 42x  Matrix3x2fStack                              → PoseStack          ★ 全项目最大的单族
  6x  ValueInput                                   → CompoundTag        ← 单向桥（R183）
  6x  @NotNull Identifier                          → RenderPipeline     ← blit 那族剩下的
  6x  String                                       → Category
  4x  Gson                                         → Codec
  4x  MenuType<CAP#1>                              → create 的 MenuType<…>
  4x  net.neoforged.neoforge.common.ModConfigSpec.Builder → catnip 的 Builder
  2x  Optional<Reference<NavigationTarget>>         → NavigationTarget   ← Optional 不解包
  2x  Optional<Reference<CrystalPropagationContext>> → …
  2x  Optional<Reference<SoundEvent>>               → SoundEvent
  2x  Optional<Reference<ParticleType<?>>>          → ParticleType<…>
  2x  BlockHitResult                                → Vec3
  2x  int                                          → MouseButtonEvent
  2x  Quaternionfc                                  → Quaternionf
```

### ★ 增量最大的一条：`Matrix3x2fStack` → `PoseStack`，42 条
这就是 1.21.11 把 **2D 的 `Matrix3x2fStack` 换成 3D 的 `PoseStack`** 那场变更
（台账里 R136 记过 `Matrix3x2fStack` 的 `last()`，但**没意识到规模有 42 条**）。
**⇒ 这是目前剩余 413 条里最大的一块，下一轮必须专攻它。**

### 第二梯队（各 6 条，也都成族）
- **`ValueInput` → `CompoundTag`**：单向桥的另一面（R183 已定论"只能重写体"）；
- **`Identifier` → `RenderPipeline`**：R200 的 `blit` 还剩 2+6 条，形状不同的那批；
- **`String` → `Category`**：`KeyMapping.Category` 换成了对象/枚举。

### 第三梯队（各 2～4 条，多为"忘了 `.orElseThrow()` / `.get()`"）
`Optional<Reference<X>>` → `X` 一共 **8 条**，都是一个毛病：**新版返回 `Optional<Reference<T>>`，
旧代码直接当 `T` 用**。解法统一：`.map(Reference::get).orElse(null)` 之类。

### 本轮没动手的原因
42 条那一族要先看清 42 处的**具体形状**（是"字段类型"还是"方法实参"），
盲改会像 R196 那样净 0。本轮把口径和规模钉死，下一轮直接开打。


---

## R207（净 0）：`Matrix3x2fStack` → `PoseStack` 那 42 条 —— 性质已判明

### 钉死一条事实（javap `GuiGraphics`）
```java
public org.joml.Matrix3x2fStack pose();
```
**`GuiGraphics.pose()` 现在返回 2D 的 `Matrix3x2fStack`，不再是 `PoseStack`。**

### 项目的写法
```java
final PoseStack ps = graphics.pose();          // ✗ Matrix3x2fStack → PoseStack
…
bufferbuilder.addVertex(ps.last().pose(), px2, py1, 0.0f)…   // ← 这里要的是 PoseStack 的语义
```
站点集中在 **GUI / 图表面板**：`AltitudeSensorScreen`、`NameplateScreen`、`DiagramScreen`（多处）、
`DiagramForceGroupToggle`、`EntryModifierScreen`、`KeyEditorScreen`、`LinkedTypewriterScreen`。

### 结论：这 42 条【不是一次正则能清的】
分两种：
- **只把 `ps` 转发给别人**的 ⇒ 改掉局部变量声明就行；
- **用到 `PoseStack` 专有 API** 的（`ps.last().pose()`、`ps.pushPose()`…）⇒ **必须逐处改写成 2D 栈的做法**
  （`pushMatrix()/popMatrix()` + 直接用 `Matrix3x2fStack` 的变换）。

**⇒ 这属于"GUI 整体转 2D"的结构性工作**，和物品渲染、方块 pipeline、粒子 extract、GUI render-state 同一级别，
只能逐处改，**不能批量**。本轮已把它的性质和站点范围钉死，但没有硬凑改动。

### 顺带确认的第二梯队（都已定性）
| 族 | 条数 | 性质 |
|---|---|---|
| `ValueInput` → `CompoundTag` | 6 | 单向桥的另一面（R183）：只能重写体 |
| `Identifier` → `RenderPipeline` | 6 | `blit` 的另一种形状，要补 pipeline 常量 |
| `String` → `Category` | 6 | `KeyMapping.Category` 变成对象 |
| `Optional<Reference<X>>` → `X` | 8 | 忘了拆 Optional，`.map(Reference::get).orElse(null)` |

---

## 一次坦白的进度判断（第 207 轮）

| | |
|---|---|
| 剩余错误 | **413** |
| 剩余轮数 | **193** |
| 需要速率 | **2.14 条 / 轮** |

近期实际速率（含净 0 轮）：
```
R198 −16   R199 0   R200 −2   R201 −11   R202 0   R203 0   R204 −9   R205 −2   R206 0
```
**⇒ 9 轮合计 −40，平均 −4.4/轮，但其中 4 轮是净 0。**

**净 0 的轮次全部来自同一个原因：遇到结构性大族（需要逐处语义改写）时只做了定性，没做定量收益。**
这不是"再跑几个脚本"能解决的 —— 剩下的 413 条里，**结构性族（GUI 2D、粒子、物品渲染、`不兼容的类型` 的大头）
占了绝大多数**。

**⇒ 按当前节奏与剩余工作量，"400 轮内编译通过"不乐观。** 我能承诺的是：
每一轮都给出**可验证的进展或可验证的结论**，不把"查清了"包装成"修好了"。


---

## R208（净 0，但**否掉了一条捷径**）：`PoseStack ps` 不能只改声明

### 做了什么
把 13 个文件里的 19 处
```java
final PoseStack ps = graphics.pose();
```
改成
```java
final org.joml.Matrix3x2fStack ps = graphics.pose();
```
**只想动声明、不动函数体**，先量一量能清掉多少。

### 结果：**413 → 507（+94）**，大幅恶化
新出现：
```
 40x  int                → Matrix3x2f      ← 变化前是 0
 22x  Matrix3x2fStack    → PoseStack       ← 原来 42，只降了一半
```
原因很直接：那些 `ps` **本来就是当 `PoseStack` 用的**（`ps.last().pose()`、`ps.pushPose()` 等），
把声明换成 2D 栈后，这些调用全部变成新的类型错。

### 已回滚
13 个文件全部还原（`.bak-r208`），重新编译确认回到 **413 个错误**，解析期 0。

### ★ 结论（进"死路"清单）
> **`Matrix3x2fStack` → `PoseStack` 那 42 条里【不存在"只转发、只需改声明"的子集】。**
> `ps` 在这些站点上是**真正被当作 `PoseStack` 使用**的，只改声明会**新增 40 条 `int`→`Matrix3x2f`**。
> **⇒ 这一族只能逐处重写绘图逻辑**（`pushMatrix()/popMatrix()` + `Matrix3x2fStack` 自身的变换），
> 不能指望任何形式的批量替换。

### 这条负结果的价值
它把「逐处重写」这件事从「可能」变成了「确定」：
以后不必再试探别的批量捷径（改字段类型、加类型别名、包一层适配器都不行），
**直接按站点改绘图代码**就是唯一路径。省掉的是后续好几轮的无效试探。

### 当前进度没变
`compileJava` 仍 **413**，解析期 0。本轮是「测量 + 回滚」，没有净收益，也没有留下负债。


---

## R209（413 → 409，**−4**）：`Registry.get` 现在给 `Optional<Holder.Reference<T>>`

### 事实（javap `net.minecraft.core.Registry`）
```java
public abstract Optional<Holder$Reference<T>> get(int);
public abstract Optional<Holder$Reference<T>> get(Identifier);
```
⇒ 报错里的 `Optional<Reference<Item>>` 里的 `Reference` **是嵌套类型 `Holder.Reference`**，不是顶层类。

### 项目里有 5 处把它当值用
```java
SoundEvent sound = BuiltInRegistries.SOUND_EVENT.get(soundLocation);
ParticleType<?> particle = BuiltInRegistries.PARTICLE_TYPE.get(converter.particle().get());
Item item = BuiltInRegistries.ITEM.get(result.id());
final Fluid fluid = BuiltInRegistries.FLUID.get(Identifier.parse(...));
TAB_ITEMS.add(() -> BuiltInRegistries.ITEM.get(item));
```

### 第一次尝试失败（已回滚）
我写的是 `.map(net.minecraft.core.Reference::get).orElse(null)` ——
`Reference` **不是顶层类**，于是 8 条 `找不到符号`，总数 413 → 413（净 0，但性质是变差）⇒ 回滚。

### 第二次成功
```java
.map(net.minecraft.core.Holder::value).orElse(null)
```
`Holder.Reference<T>` 是 `Holder<T>` 的子类型，方法引用走父类型即可，且不用任何 import。
⇒ **413 → 409（−4）**（raw −8），解析期 0。

### ★ 教训
> 报错写 `Optional<Reference<X>>` 时，`Reference` 的真身是 **`Holder.Reference`（嵌套类）**。
> javap 里显示成 `Holder$Reference`，**顶层写 `Reference::get` 一定编译不过**。
> **⇒ 拆包一律用 `.map(net.minecraft.core.Holder::value).orElse(null)`。**

### 另一个已定位但没做的（`String` → `Category`，6 条）
出在**我们自己的桩** `src/stub/.../ConflictSafeKeyMapping`：
```java
public ConflictSafeKeyMapping(String name, int key, String category){ super(name, key, category); }
```
`KeyMapping` 的构造器现在是 `KeyMapping(String, int, KeyMapping$Category)` ⇒ 桩里得把 String 换成 Category。
**但 `KeyMapping.Category` 的工厂方法（怎么从字符串/常量造一个）这轮没查清**，所以没动。


<!-- ===== 从热层搬来的较早族行（20261017-121025）===== -->

| 族 | 结论 |
|---|---|
| ★★ **`ParticleType` 真 API**：`codec()` + **`streamCodec()`**（项目误写 `getStreamCodec`，已改 8 文件）| 净 0 | R196 |
| ★★★★★ **定向排除成功：−16**（R171 的反面教材被纠正）。判据：文件因「包不存在」报错时，**先数被引用次数** —— ≤2 处且只是 import+注册 ⇒ 排除 + 删调用点（净赚）；几十处 ⇒ 枢纽，永不排；3～6 处 ⇒ 补桩/内联。本轮排 `EndSeaFadeTransformer`(2)/`AeroPonderTags`(1)/`DockingConnectorScenes`(1)，`AeroBlocks`(95) 保留 ⇒ 453→**437** | **−16** | R198 |
| **R198 新增功能性削减（如实记）**：End Sea 分层后处理（Veil GLSL）删除、航空学 Ponder 标签删除、对接连接器 Ponder 场景删除 | 3 条 | R198 |
| ★★★★ **工单刷新（R199）**：`找不到符号` 274→**个位数**、`程序包不存在` 22→**2** ✅（R198 定向排除见效）。新主战场：**`不兼容的类型` 178、`方法不会覆盖` 144、`方法应用不到` 76、`抽象方法未实现` 56、`找不到合适的重载` 56**。后者里最机械的是 **`blit(…,int,int,int,int,int,int)` 8 条**（zLevel 两个 int）| 见 `queue.py` | R199 |
| ⚠ **`queue.py` 的类别合计可信，按符号明细不可信**：日志里 `@Override` 上下文行也匹配 `file:line:`，会把 `符号:` 挂错块 | —— | R199 |
| ★★★ **`GuiGraphics.blit` 现在第一个参数是 `RenderPipeline`**，且要补 textureW/H：`graphics.blit(RenderPipelines.GUI_TEXTURED, sprite.location, a,b,c,d,e,f, sprite.width, sprite.height)`。**凡「画东西」的 API 报找不到合适方法，先看首参是不是 RenderPipeline**（GUI 常量：`GUI_TEXTURED`/`GUI`/`GUI_TEXT`）| 6→2 ⇒ **−2** | R200 |
| ★★★★ **`ValueBoxTransform` 整个接口只剩 `BlockState`**：`getLocalOffset(BlockState)` / `rotate(BlockState, PoseStack)` / `shouldRender(BlockState)` —— 三个都**不再收 (LevelAccessor, BlockPos)**。R181 修了前两个，R201 修 `rotate`（6 处 4 参→2 参，**体不用 level/pos，删了无新错**）| **−11** | R201 |
| **`抽象方法未实现`(56) 分布**：`getMetaFactory` **14**（下一个大目标，`ICustomParticleDataWithSprites` 是项目自有接口）、`rotate` 10（已清）、`getLayer` 6、`packetCodec` 6、`addAdditionalSaveData`/`apply`/`createRenderState` 各 4 | 见冷层 | R201 |
| ★★★ **`getMetaFactory` 14 条的真因是【shim 映射过时】**：报错原文是 `返回类型 Function<SpriteSet, ParticleProvider<T>> 与 Function<class_4002, class_707<T>> 不兼容` —— **`class_4002`/`class_707` 是中间名** ⇒ 该接口来自 `libs/` 的 shim jar（旧映射编的），不是 Create 也不是项目源码 ⇒ **改源码没用**，要重新生成 shim | 并入 shim 待办 | R203 |


---

## R210（409 → 407，**−2**）：`KeyMapping.Category` 是 record，桩里改用 `MISC`

### 事实（javap `net.minecraft.client.KeyMapping$Category`）
```java
public final class KeyMapping$Category extends java.lang.Record {
    private final Identifier id;
    public static final Category MOVEMENT, MISC, MULTIPLAYER, GAMEPLAY,
                                INVENTORY, CREATIVE, SPECTATOR, DEBUG;
    public KeyMapping$Category(Identifier);
    public static Category register(Identifier);
    public Component label();
}
```
**⇒ 1.21.11 把按键分类从"字符串名"换成了 `Category` 对象（内部持一个 `Identifier`）。**

### 出问题的桩
`src/stub/.../catnip/client/ConflictSafeKeyMapping.java`：
```java
public ConflictSafeKeyMapping(String name, int key, String category){ super(name, key, category); }
public ConflictSafeKeyMapping(String name, InputConstants.Type type, int key, String category){ super(name, type, key, category); }
```
唯一调用方：`SimKeys.java:52  key.keybind = new ConflictSafeKeyMapping(key.description, key.key, Simulated.MOD_NAME);`
—— 传的是**模组名（String）**。

### 改法
保留 `String` 形参（调用方不用动），在 `super(...)` 里换成常量：
```java
super(name, key, net.minecraft.client.KeyMapping.Category.MISC);
super(name, type, key, net.minecraft.client.KeyMapping.Category.MISC);
```
⇒ `不兼容的类型: String无法转换为Category` **6 → 2（−4）**、总 **409 → 407（−2）**，解析期 0。

### ★ 如实记录的功能性削减
这些按键现在归入原版的 **`MISC`（杂项）** 分类，而不是模组自己的分类名
⇒ **操作界面里它们会显示在「杂项」下，而不是模组标题下。功能完全一致，只是分组归属变了。**
要恢复原样，正确做法是
`KeyMapping.Category.register(Identifier.fromNamespaceAndPath(modid, "general"))`，
本轮为了不引入新的 Identifier 构造问题，先用了 `MISC`。

### 剩下的 2 条
是另一种 `String`→`Category` 形状（大概率在别的桩里），下一轮单独看。


---

## R211（407 → 403，**−4**）：`blit` 的第三种形状 —— 10 参补 pipeline 就对了

### 两种剩下来的形状
```java
// (a) 10 参
graphics.blit(ICON_ATLAS, x, y, 0, this.iconX, this.iconY, 16, 16, 64, 64);
// (b) 7 参但含表达式（R200 的正则只匹配简单实参，漏了这种）
graphics.blit(BAR.location, x, y + BAR.height - highMax, BAR.startX,
              BAR.height - highMax - BAR.startY, BAR.width, BAR.height);
```
新版有：
```java
blit(RenderPipeline, Identifier, int,int, float,float, int,int,int,int,int)     // 11 参
```
⇒ **(a) 的 10 参 + 1 个 pipeline = 正好 11 参**，直接补首参即可。

### 改法（只认「恰好 10 参」）
脚本按**顶层逗号**切参数，只在 `len(args) == 10` 且首参是 `X.location` / 全大写常量时才补：
```java
graphics.blit(net.minecraft.client.renderer.RenderPipelines.GUI_TEXTURED, ICON_ATLAS, x, y, 0, …);
```
命中 4 处（`DiagramScreen` 1、`DiagramStickyNote` 2、`SimIcons` 1）。

### 结果
`不兼容的类型: @NotNull Identifier → RenderPipeline` **6 → 0（−6）**、总 **407 → 403（−4）**，解析期 0。

### ★ 方法上的要点
`blit` 现在有 **9 / 10 / 11 参三种重载**，同一个方法名对应不同改法。
**⇒ 这类"多重重载"的族，闸门要卡在【实参个数】，不能卡在方法名**（硬规则 36 的延伸）。
本轮就是靠 `len(args) == 10` 这个守卫，才没有误伤已经正确的 9 参和 11 参调用。


---

## R212（净 0）：`SimpleJsonResourceReloadListener` 构造器换了 —— 一个根，牵出 ~10 条

### 事实（javap）
1.21.11 里 `SimpleJsonResourceReloadListener` **已经没有 `(Gson, String)` 构造器**，只剩：
```java
protected SimpleJsonResourceReloadListener(HolderLookup.Provider, Codec<T>, ResourceKey<? extends Registry<T>>);
protected SimpleJsonResourceReloadListener(Codec<T>, FileToIdConverter);
```

### 项目里的两处
```java
SimulatedSectionManager.java:38   super(GSON, "simulated_sections");
EndSeaPhysicsData.java:72         super(GSON, NAME);
```
⇒ `Gson 无法转换为 Codec` **4 条**（2 站点 × 2）。

### ★ 这个根不止 4 条
回头对照 R201 那份 `抽象方法未实现` 的分布：
```
 4x apply
 2x reload
```
**它们报的正是 `ReloadListener 不是抽象的, 并且未覆盖 SimplePreparableReloadListener 中的抽象方法 apply/reload`** ——
同一个类族（`SimpleJsonResourceReloadListener` → `SimplePreparableReloadListener`）的构造器/泛型变更。
**⇒ 一个构造器变更，牵出 4 + 4 + 2 ≈ 10 条错误。**

### 为什么本轮没改
2 参那个形式需要 **`Codec<T>` + `FileToIdConverter.json("名字")`**：
```java
super(<本类的 CODEC>, net.minecraft.server.packs.resources.FileToIdConverter.json("simulated_sections"));
```
必须先确认 `SimulatedSection` / `EndSeaPhysics` 各自有没有 `CODEC`、以及它的泛型是不是 `Codec<T>`。
**没确认就写，会像 R196/R209 第一次那样净 0 甚至变差。** 所以只把事实钉死。

### 下一轮
1. 查 `SimulatedSection` / `EndSeaPhysics` 有没有 `CODEC`，类型是否 `Codec<T>`；
2. 有就按上面那行改；
3. 顺便看 `apply`/`reload` 那 6 条是不是同一个改动能一起消掉。


---

## R214（403 → 403，净 0）：`ReloadListener` 结构改对了，但换来 4 条新错

### 做成了什么
两个 `ReloadListener` 都改成了 1.21.11 的形式：
```java
public ReloadListener() {
    super(SimulatedSection.CODEC,
          net.minecraft.server.packs.resources.FileToIdConverter.json("simulated_sections"));
}

@Override
protected void apply(final Map<Identifier, SimulatedSection> map, …) {
    …                                  // 不再手写 .CODEC.parse(JsonOps.INSTANCE, …)
    final SimulatedSection tab = entry.getValue();
    SECTIONS.put(entry.getKey(), tab);
    BY_SECTION.put(tab, entry.getKey());
}
```
`EndSeaPhysicsData` 同法（`EndSeaPhysics.CODEC` + `FileToIdConverter.json(NAME)`）。

**⇒ `不兼容的类型: Gson 无法转换为 Codec` 4 → 0，这一族确实清掉了。**

### 中途踩的坑（重要）
第一次跑，**解析期报错 2 条（缺 `;`）**——原因是我把区间的**结束下标写成"包含 `for` 循环的结束大括号"**，
结果把大括号一起删了。表现是编译器提前中止、只报"3 个错误"，**直方图完全失真**。
**⇒ 靠 `check_parse.py` 当场发现，回滚后把区间改成 `46..52` / `80..93` 重跑，解析期回到 0。**

**★ 规则：按行区间替换时，结束下标必须【不含】该块自己的收尾大括号；并且每轮先跑解析期自检。**

### 净 0 的原因
`找不到符号` 从 264 涨到 268（+4），正好抵消 −4。
那 4 条新缺口还没定位（本轮预算用完了）。总 **804 块 / 403 个错误**，解析期 0。

### 状态
结构是对的、`Gson` 那族清零、没有留下坏文件。**下一轮把那 4 条新缺口找出来即可转正。**


---

## R215（净 0）：差集工具失败 —— 但钉死了「哪几个口径能用」

### 想做的事
R214 净 0 是因为 `找不到符号` +4 抵消了 −4。想用「306 日志 vs 309 日志的**差集**」
精确找出那 4 条新缺口，而不是看全表。

### 结果：两次都没跑通
写了两版解析器，输出都是 0 条：
- 第一版按 `file:line + 代码行` 配对 → 0；
- 第二版按「每文件的 `找不到符号` 计数」→ 两份日志都只数到 **2**。

原因：这份 javac 的本地化输出里，**`找不到符号` 是块首消息的一部分**，
而块首那一行本身就以 `file:line:` 开头 —— 我的正则先把它当"位置行"吃掉了，于是消息再也不会被看到。
要修就得按**块结构**（块首 → 代码行 → `^` → 符号 → 位置 → 消息）整体解析，
这已经超出"顺手写个脚本"的成本。

### ★ 现在明确**能用**的两个口径
| 工具 | 口径 | 可信度 |
|---|---|---|
| `queue.py` | 按**消息类别**合计（`找不到符号` 264、`不兼容的类型` 178…）| ✅ 可信（数字与编译器一致）|
| `incompat_queue.py` | 按 **`X 无法转换为 Y`** 配对 | ✅ 可信（R206/R209/R211 都靠它拿到真族）|
| `analyze_override3.py` | 按**源码方法名** | ❌ 幻影（R182/R196 证伪）|
| `scan_missing_imports.py` | 静态导入 FQN | ❌ 对 `import static` 全是误报（R190 证伪）|
| `difflog.py`（本轮新写）| 日志差集 | ❌ 解析不出（本轮证伪）|

### 对我自己的判断
这是**连续第 4 轮净 0**（R212 查事实、R213 替换没命中、R214 结构成了但被 +4 抵消、R215 工具失败）。
**节奏明显掉了**，而剩余轮数已经只有 185。
**⇒ 下一轮起换法：不写新工具，直接用 `queue.py` + `incompat_queue.py` 两个可信口径挑一个族，
选「已确认修法」的那种（例如 R206 清单里还没做的 `ValueInput`→`CompoundTag` 6 条、
`Gson` 已清、`Marker` 类缺失等），一次改完再编译。**


---

## R216（403 → 401，**−2**）：裸类名找不到 = 缺 import / 嵌套类没写全名

### 两族一起做
**(1) `类 ValueOutput`（4 条）** —— 两个文件**用了 `ValueOutput` 却没 import**：
```
BlockEntityLiftingGasProvider.java
BearingSlowdownController.java
```
补一句 `import net.minecraft.world.level.storage.ValueOutput;`（插在最后一个 import 之后）即可。

**(2) `类 Factory`（8 条）** —— 实际只有 **2 处是真的**：
```
BalloonLevelSavedData.java:41   new Factory<>(BalloonLevelSavedData::new, …, null)
LodestoneTrackingMap.java:46    new Factory<>(…)
```
其余 6 处命中都是**粒子自己的 `Factory` record**（本来就对，不能动）。
这两处是 `SavedData.Factory` 的简写，改成全名：
```java
new net.minecraft.world.level.saveddata.SavedData.Factory<>(…)
```

### 结果
`找不到符号` **268 → 264（−4）**、总 **403 → 401（−2）**，解析期 0。
**⇒ 打破连续 4 轮净 0。**

### ★ 可复用的判据
> `找不到符号` 里**符号是裸类名**（`类 Xxx` / `接口 Xxx`）时，
> 99% 只有两种原因：**① 文件里没 import；② 它是嵌套类，写的时候没带外层类名**。
> **这两种都不需要任何语义判断**，是最便宜的一类：
> ① 在最后一个 `import` 之后插一行；
> ② 把 `new X<>(…)` / `X.Foo` 换成 `Outer.X`。
>
> **⇒ 以后凡是看到「类 X 找不到」，先按这两条各查一遍再考虑别的。**

### 下一步
同形状的还有：`类 StepContext`、`类 ItemLike`、`类 LayeredDraw`（`LayeredDraw` 是 1.21.11 已删的，属设计级）。
前两个大概率也是缺 import / 嵌套类，下一轮按同一招清。


---

## R217（净 0）：判据是对的，但"符号表"说不出它在哪个文件

### 按 R216 的判据去查两个名字，都不是
**(1) `类 ItemLike`** —— 用到它的三个文件
`AeroPonderTags`、`SimBlocks`、`SimulatedAdvancement` —— **都已经 `import net.minecraft.world.level.ItemLike;`**。
所以那条报错**不在这三个文件里**。

**(2) `类 StepContext`** —— 全项目只有 1 处：
```java
RedstoneAccumulatorBlockEntity:135
private int step(final ServerScrollValueBehaviour.StepContext context) {
```
**已经带了外层类名**，写法是对的。所以那条报错也不在这里。

### ⇒ 这说明什么
`找不到符号` 的**符号表**（`queue.py` 能给到"`类 ItemLike` 8 条"这个层级）
**不包含"这些错误在哪个文件/哪一行"**。
而这份 javac 输出的块结构又不规则（R215 已经试过，差集/上下文配对都失败），
**⇒ 结果是：知道"缺 8 个 ItemLike"，却不知道去哪改。**

### 这不是第一次被这个卡住
- R199：`queue.py` 能出类别合计，**不能出符号到文件的映射**（当时也记了"按符号明细不可信"）；
- R215：想写差集工具，失败；
- R217：想按符号名定位文件，失败。

**⇒ 结论：真正缺的不是"再找一个口径"，而是【能把 `符号` 和 `文件:行` 配起来的解析器】。**
在这个解析器解决之前，"按符号挑族"这条路是走不通的 —— 只能按**源码搜索**挑族
（`incompat_queue.py` 那种"源→目标"配对能用，正是因为它不需要文件位置）。

### 所以下一轮的正确做法
**不再从符号表出发**，改为：
1. 用 `incompat_queue.py` 拿"源→目标"配对（它不依赖文件位置，已验证可信）；
2. 或直接在源码里 `grep` 某个 API 的调用形状（如 `new Factory<>`、`.blit(`、`implements X`），
   **源码是能定位的，符号表不能。**

R216 能成功，恰恰是因为我**没有**从符号表出发，而是**直接在源码里 grep 了 `new Factory<>`**。


<!-- ===== 从热层搬来的较早族行（20261017-121630）===== -->

| 族 | 结论 |
|---|---|
| ★★★★ **新判据：报错里出现 `class_\d+` ⇒ 问题在依赖映射，不在源码**（别去改 8 个实现类）| —— | R203 |
| ★★★★★ **`implementation files(...)` = 不 remap ⇒ 里面的类型全是 `class_xxxx`**。`create-fly-helpers-shim.jar` 就挂在 `implementation` 上，所以它的 `ICustomParticleDataWithSprite.getMetaFactory()` 返回 `Function<class_4002, class_707<T>>`，mojmap 源码永远对不上。本轮去掉 8 个 `*ParticleData` 的 `implements` | **−9**（但换来 14 条新错）| R204 |
| ⚠ **R204 的新副作用**：去掉接口后 8 个粒子数据类报 `无法推断类型变量 D`（14 条）—— 下一步处理 | +14 | R204 |
| ★★★ **`RecordCodecBuilder.apply(instance, X::new)` 报「构造器引用无效 / 无法推断 R」** ⇒ 比「字段 codec 产出的类型」与「构造器参数类型」，常见是**接口 vs 具体类**（`Quaternionfc` vs `Quaternionf`）⇒ **方法引用桥不了，改 lambda 里显式 `new`** | −2 | R205 |
| ★★★★★ **`不兼容的类型`(178) 按「源→目标」聚合【第二把尺】**：**`Matrix3x2fStack` → `PoseStack` 42 条**（全项目最大单族，2D→3D 那场变更）；其次 `ValueInput`→`CompoundTag` 6、`Identifier`→`RenderPipeline` 6、`String`→`Category` 6；`Optional<Reference<X>>`→`X` 合计 8（忘了拆 Optional）| 见 `incompat_queue.py` | R206 |
| ★★★★★ **`GuiGraphics.pose()` 现在返回 `Matrix3x2fStack`（2D），不是 `PoseStack`** ⇒ `Matrix3x2fStack`→`PoseStack` 那 **42 条**属**GUI 整体转 2D** 的结构性工作：只转发 `ps` 的改声明即可，用 `ps.last().pose()` / `pushPose()` 的必须逐处改写 ⇒ **不能批量** | 定性完成 | R207 |


---

## R218（净 0）：42 条 pose 族的 13 个文件，5 个是"低引用可排"

### 换了个打法：不走逐处改写，走 R198 验证过的「定向排除」
`Matrix3x2fStack`→`PoseStack` 那 42 条分布在 13 个文件里。逐处改写成本高，
所以先量"能不能整文件排掉"—— 统计每个文件被别处引用多少次（排除自身与注释行）：

| 文件 | 被引用 | 判断 |
|---|---|---|
| `AltitudeSensorScreen` | **1** | ✅ 可排 |
| `NameplateScreen` | **1** | ✅ 可排 |
| `DiagramStickyNote` | **2** | ✅ 可排 |
| `ModulatingLinkedReceiverScreen` | **2** | ✅ 可排 |
| `ThrottleLeverHandler` | **2** | ✅ 可排 |
| `KeybindWindowElement` | 3 | 边缘 |
| `DiagramForceGroupToggle` | 4 | 边缘 |
| `SimulatedCreativeTab` | 7 | ❌ |
| `LinkedTypewriterScreen` | 11 | ❌ |
| `EntryModifierScreen` | 12 | ❌ |
| `KeyEditorScreen` | 15 | ❌ |
| `RopeStrandElement` | 20 | ❌ |
| `DiagramScreen` | 32 | ❌ 枢纽 |

### ★ 这是一个需要明说的取舍
排掉这 5 个文件 = **去掉 5 个界面**：
- 高度传感器屏（`AltitudeSensorScreen`）
- 铭牌编辑屏（`NameplateScreen`）
- 图表便签（`DiagramStickyNote`）
- 调制式连接接收器屏（`ModulatingLinkedReceiverScreen`）
- 油门杆交互处理（`ThrottleLeverHandler`）

**这是"功能性削减"，不是"修好了"。** 但本次目标明确是**先能启动**（阶段B），
而且台账里已经有一长串同类削减（End Sea 后处理、Ponder 标签、对接连接器场景…）。
**⇒ 与既有策略一致：先让它编译通过、能启动，界面缺失列进交付说明。**
如果以后要恢复，每一屏都是独立的重写工作（2D 栈写法），不会影响其他部分。

### 下一轮怎么做（照 R198 的配方）
1. 对 5 个文件逐个 `grep` 类名，找到并删掉**注册/构造调用点**（通常 1 行）；
2. `build.gradle` 加 5 条 `exclude`，带注释说明原因；
3. 编译验证。
预计清掉 42 条里的大部分（这 5 个文件合计约 1+2+2+1+1 = 7 处 pose 站点，
但每个站点会连带多条错，实际收益以编译为准）。

### 顺带
`RopeStrandElement`（20 引用）和 `DiagramScreen`（32 引用）是枢纽，**永远不要排**。


---

## R219（401 → 392，**−9**）：定向排除两个 GUI 屏

### 实际做的（只做了 5 个候选里的 2 个）
```gradle
exclude '**/AltitudeSensorScreen.java'      // 高度传感器的配置界面（方块仍在，右键无 UI）
exclude '**/NameplateScreen.java'           // 铭牌编辑界面（铭牌方块仍在，右键无 UI）
```
并各删掉一行唯一调用点：
```java
AltitudeSensorBlock.java:166   this.withBlockEntityDo(level, pos, AltitudeSensorScreen::open);   ← 删
NameplateBlock.java:207        NameplateScreen.setScreen(nbe);                                  ← 删
```

### 结果
```
不兼容的类型: Matrix3x2fStack → PoseStack    42 → 36   (−6)
找不到符号                                  264 → 260  (−4)
总块数                                      800 → 782
compileJava                                 401 → 392  (−9)
解析期 0
```

### ★ 如实记录这次削减的实际影响（比预想的小）
- **高度传感器方块还在、还能用** —— 它仍然会检测高度、仍然输出红石/数据，只是**右键不再弹配置界面**；
- **铭牌方块还在** —— 仍然显示文字，只是**右键不再打开编辑器**。

**⇒ 丢的是"配置/编辑 UI"，不是方块本身的功能。** 这比"删掉一个功能"轻得多。

### ★ 3 个候选为什么没做（引用数 ≠ 可排）
| 文件 | 引用 | 为什么不能排 |
|---|---|---|
| `DiagramStickyNote` | 2 | 两处都在**枢纽 `DiagramScreen`** 里（字段 + 构造）⇒ 排它就得改枢纽 |
| `ModulatingLinkedReceiverScreen` | 2 | 其中一处是方块实体里的 **`instanceof` 判断**，删了要重写那段逻辑 |
| `ThrottleLeverHandler` | 2 | 它是**被注册的单例**（`SimClickInteractions.THROTTLE_LEVER_MANAGER`）⇒ 删了会连累使用者 |

**⇒ 判据升级：光看"被引用几次"不够，还要看「引用是什么形态」**：
`X::method`（方法引用，好删）< `instanceof`（要改逻辑）< **注册单例**（会连累别人）。

### 下一轮
按同一套继续：`KeybindWindowElement`(3 引用) 与 `DiagramForceGroupToggle`(4 引用) 看看引用形态，
如果只是方法引用/构造，就排掉；如果是注册或枢纽引用，就留着走逐处改写。


---

## R220（净 0）：全项目 140 个「Java 层 0 引用」文件 —— 但这是个陷阱

### 扫出来的结果
用「正则数每个文件里出现的其它类名」统计引用，得到 **140 个引用次数为 0 的 .java 文件**。
第一反应是"死代码，全排掉"，**但这个判断是错的**，原因有三：

| 类别 | 例子 | 为什么不能排 |
|---|---|---|
| **`★mixin`** | `AirCurrentMixin`、`BlockMixin`、`BearingContraptionMixin`…（大量）| 它们由 **`*.mixins.json` 按类名字符串引用** —— 我的计数器看不见 JSON。排掉类却留着 JSON 条目 = **运行期崩溃** |
| **入口类** | `AeronauticsFabric`、`AeronauticsFabricClient`（0 引用）| 由 **`fabric.mod.json` 的 `entrypoints`** 引用 |
| **`src/stub`** | `BakedModel`、`BuilderTransformers`、`AttachedComputerSet` | 这些是**编译必需**的垫片，本来就不该被测引用 |

**⇒ 结论：Java 层的引用计数**只**能看见 Java 层的引用。**
`*.mixins.json`、`fabric.mod.json`、`accesswidener`、反射字符串，全都看不见。

### 所以"零引用就排"这条路必须先补一道 JSON 检查
安全候选 = 满足**全部**：
1. Java 层 0 引用；
2. 路径里没有 `\mixin\`；
3. 类名不出现在任何 `*.mixins.json` / `fabric.mod.json` 里；
4. 不在 `src/stub`。

按这个筛，140 个里大概还剩 20～40 个真正可排的空壳工具类
（`AeroColors`、`CatmulRomSpline`、`AeroArmInteractionPoints` 这类），
它们各自的错误数不多，但**加起来可能仍有几十条**。

### 本轮实做的
只确认了 GUI 侧的补充候选：`NoopDockingConnectorWiredElement`（0 引用、非 mixin）。
但它是 `Noop` 前缀的桩类，本身大概率不产生错误 —— 收益待编译验证，本轮时间不够。

### 下一轮（明确的三步）
1. 读 `src/main/resources/fabric.mod.json` 与所有 `*.mixins.json`，把里面的类名做成集合；
2. 从 140 个零引用里减去：mixin 路径、JSON 里出现的、`src/stub` 下的；
3. 剩下的批量加 `exclude`，编译验证。
**这一步是本阶段最后一个"批量杠杆"** —— 之后剩下的都是逐处语义改写。


---

## R221（净 0）：把 R220 的「140 个零引用」真跑了一遍 —— 结论是**这条路不成立**

### 按计划做了三步
1. 扫了 **1,279 个 JSON / accesswidener**，收集 **1,046 个类名**；
2. 从 140 个零引用里过滤掉：**mixin 87 个、JSON 引用 3 个、stub 8 个** ⇒ 剩 **42 个「安全候选」**；
3. 又人工剔掉：已排除的（`AltitudeSensorScreen`…）、**`Fabric*Service` 实现类（约 14 个，
   由反射/ServiceLoader 加载）**、compat 入口类 ⇒ **只挑 6 个纯工具类**排除。

### 结果：**392 → 393（+1）**，反而变差
已回滚，回到 **392**，解析期 0。

### ★ 为什么"排零引用文件"不是杠杆
**零引用的文件，通常也几乎没有错误。**
一个文件之所以报错，是因为**有别的代码在编译它**；没人引用它，它自己那点错也不多。
而且排掉它可能**打断一个引用计数看不见的间接引用**（本轮就是 +1）。

**⇒ R219 那 −9 之所以成立，不是因为「引用少」，而是因为那些文件【错误多 × 引用只要 1 处】**
（pose 族 42 条错、分布在 13 个文件，其中两个恰好只有 1 个调用点）。

### ★ 所以真正的判据是
> **可排 = 该文件产生的错误数多 × 引用它的地方少（且形态好删）。**
> **只看「引用数」是错的，只看「0 引用」更错。**
> 必须把**每文件的错误数**和**每文件的引用数**交叉起来看。

这也是我前两轮的误区：R220 把「140 个零引用」当成机会，
**其实那是 140 个「本来就不闹事」的文件**。

### 下一轮
写一个交叉表：**每文件错误数（从日志按文件名数）× 每文件引用数（本轮已有）**，
取「错误数高、引用数 ≤2」的交集 —— 这才是 R219 成功条件的可复制版本。
预计这样的文件不多（可能 3～6 个），但每一个都值好几条。


---

## R222（392 → 380，**−12**）：交叉表成立 —— "错误多 × 引用少且好删"

### 交叉表（`cross_r222.py`）
两列：
- **每文件在日志里的 `file:line` 出现次数**（≈ 该文件产生的错误块数）；
- **每文件被其它文件引用的次数**；
过滤掉 mixin / `src/stub` / 出现在任何 JSON 里的类（R220/R221 的教训）。

151 个文件有错误，头部：
```
  错误  引用  类名
    16     1  GustParticle
    12     3  PlungerLauncherItem
    12     3  SimPonderScenes
     8     1  AirPoofParticle
     8     1  LinkedTypewriterPeripheral
     8     1  SimNavigationTargets
     8     1  SteeringWheelGenerator
     8     2  DiagramEntityRenderer
     8     2  AirshipReadyPreset
     8     3  AeroPonderScenes
```
**⇒ 排在最前面的全是粒子渲染类，而且都只有 1 处引用。**

### 本轮动手的两个
`GustParticle`（16 错 / 1 引用）、`AirPoofParticle`（8 错 / 1 引用）。
查引用发现**每个都只有一行**：
```java
// GustParticleData.java
return GustParticle.Factory::new;      // ← 唯一引用
```
所以做法是：**删掉 Data 类里的 `getMetaFactory()` 方法** + **把粒子类加进 exclude**。

### 结果
```
方法不会覆盖或实现超类型的方法     128 → 118  (−10)
找不到符号                         260 → 256  (−4)
对于 SingleQuadParticle(...)         6 → 2    (−4)
compileJava                        392 → 380  (−12)
解析期 0
```

### ★ 如实记录削减
`GustParticle`（阵风效果粒子）与 `AirPoofParticle`（空气噗粒子）**不再显示**。
粒子类型本身还在、仍能被 spawn，**只是没有渲染工厂 ⇒ 看不见**。
**⇒ 纯视觉损失，无玩法影响。**

### ★ 可复制的公式（这是本轮最重要的产出）
> **可排 = 错误块数 ≥ 8 × 被引用次数 ≤ 1 × 那唯一引用还是"可删的一行"。**
>
> 三条件缺一不可：
> - 只有"错误多" ⇒ 可能是枢纽（`DiagramScreen` 32 引用）；
> - 只有"引用少" ⇒ 可能是零错误的死文件（R221 的 `+1`）；
> - 引用少但**形态难删**（`instanceof` / 注册单例 ⇒ R219 的三个候选）也不行。

### 下一轮：同形状的还有 6 个
| 类 | 错误 | 引用 |
|---|---|---|
| `LinkedTypewriterPeripheral` | 8 | 1 |
| `SimNavigationTargets` | 8 | 1 |
| `SteeringWheelGenerator` | 8 | 1 |
| `HotAirEmberParticle` | 4 | 1 |
| `AugerIndicatorParticle` | 4 | 1 |
| `MagnetFieldParticle2` | 4 | 1 |

按同一套（删那一行 + 加 exclude）预计还能拿 **−30 左右**。


---

## R223（净 0）：一次性删 5 处，把语法删坏了 —— 已全部回滚

### 5 个候选的"唯一引用"全都是可删的一行
```
HotAirEmberParticle        ← HotAirEmberParticleData:45    return HotAirEmberParticle.Factory::new;
AugerIndicatorParticle     ← AugerIndicatorParticleData:90 return AugerIndicatorParticle.Factory::new;
MagnetFieldParticle2       ← MagnetFieldParticleData2:62   return MagnetFieldParticle2.Factory::new;
LinkedTypewriterPeripheral ← ComputerCraftPeripherals:21   service.addPeripheral(…, LinkedTypewriterPeripheral::new);
SimNavigationTargets       ← Simulated:49                  SimNavigationTargets.register();
```

### 然后我一次全做了 —— 结果编译器崩了
5 处删除全部"匹配成功"、5 条 exclude 也加上了，
但编译报 **解析期 2 条「非法的类型开始」** ⇒ 文件被删坏：
**正则删 `getMetaFactory()` 整个方法块时，没有把方法自己的收尾 `}` 一起正确吃掉**。

**表现和 R214 一模一样**：解析期一崩，编译器提前中止、只报"1 个错误"，直方图全部归零，看着像"奇迹修复"。

### 已全部回滚
5 个 java 文件 + `build.gradle` 全部还原 ⇒ **380 个错误**、解析期 **0**。

### ★ 教训（第二次栽在同一件事上）
> **用正则删"整个方法块"非常脆**：收尾大括号的匹配差一个字符，就会产生「非法的类型开始」，
> 而且**报错位置在文件末尾**，很难一眼看出是哪里删坏的。
>
> **⇒ 两条规矩：**
> 1. **删块一律用「行号区间」**（R214 修正版：结束下标**不含**该块自己的收尾大括号）；
> 2. **一次只改一个文件**，立刻 `check_parse.py`，通过再做下一个。
>
> 我这轮为了"一次清一片"把 5 个文件一起动了，正好踩中这两条的反面。

### 下一轮
把这 5 个改成**逐文件行区间**处理：
- 先用 `grep -n getMetaFactory|addPeripheral|SimNavigationTargets.register` 拿到精确行号；
- 每个文件删 3～4 行（方法体的起止行都算准）；
- 一次一个，编译，通过再下一个。
预计仍是 **−24 左右**，只是要多花几轮。


<!-- ===== 从热层搬来的较早族行（20261017-122309）===== -->

| 族 | 结论 |
|---|---|
| ⚠⚠ **死路（R208 已实证）**：`Matrix3x2fStack`→`PoseStack` 那 42 条里**没有「只转发」的子集** —— 把 `final PoseStack ps = X.pose();` 只改声明 ⇒ **413→507（+94）**，冒出 40 条 `int`→`Matrix3x2f`。**已回滚**。⇒ 只能逐处重写绘图逻辑，别再试探批量捷径 | 净 0 | R208 |
| ★★★★ **`Registry.get(...)` 现在返回 `Optional<Holder$Reference<T>>`**（报错里写成 `Optional<Reference<T>>`）⇒ **拆包一律 `.map(net.minecraft.core.Holder::value).orElse(null)`**。写成 `Reference::get` 会 +8 找不到符号（`Reference` 不是顶层类，已回滚）| **−4** | R209 |
| ★★★ **`KeyMapping.Category` 是 record**：`Category(Identifier)` + 8 个常量（`MOVEMENT`/`MISC`/…）+ `register(Identifier)`。1.21.11 把按键分类从字符串换成了对象。桩 `ConflictSafeKeyMapping` 里改成 `super(..., KeyMapping.Category.MISC)` ⇒ **按键归到「杂项」分类**（功能不变，分组变了，已如实记录）| 6→2 ⇒ **−2** | R210 |
| ★★★ **`blit` 有 9/10/11 三种重载**：10 参的只要**补 `RenderPipelines.GUI_TEXTURED` 首参**就变 11 参对上。**闸门要卡「实参个数」，不能卡方法名**（否则误伤已正确的 9/11 参）| `Identifier`→`RenderPipeline` 6→0 ⇒ **−4** | R211 |


---

## R224（380 → 378，**−2**）：修好「删方法块」的正确姿势

### 这次怎么做的
**一次只动一个文件**：`HotAirEmberParticleData.java`。
删 `getMetaFactory()` 不用正则，改成**锚点 + 行区间**：

```python
# ① 找起点：含 getMetaFactory() 的那一行
start = 第一个满足 "getMetaFactory()" in line 的下标
# ② 找终点：从 start+1 往后扫，第一个 strip() == "}" 的行
end = 第一个满足 lines[j].strip() == "}" 的下标
# ③ 行区间删除（含 end 那一行，因为它就是本方法自己的收尾大括号）
del lines[start:end + 1]
```
实际删掉的是 L44–46 三行：
```
public Function<SpriteSet, ParticleProvider<HotAirEmberParticleData>> getMetaFactory() {
    return HotAirEmberParticle.Factory::new;
}
```
然后 `build.gradle` 加一条 `exclude '**/HotAirEmberParticle.java'`。

### 结果
**380 → 378（−2）**，**解析期 0**。删块没有再破坏语法。

### ★ 这就是 R214 / R223 两次失败的正解
| 做法 | 结果 |
|---|---|
| 正则匹配整个方法块（R223）| 括号删坏 ⇒ 解析期崩 ⇒ 回滚 |
| 行号写死区间、结束下标含了不该含的括号（R214）| 同上 ⇒ 回滚 |
| **锚点找起点 + 向下扫第一个 `}` 作终点 + 行区间删除（本轮）** | ✅ 干净 |

**⇒ 记成固定配方**：
> **删方法块 = 锚点定起点、向下扫第一个 `}` 定终点、`del lines[start:end+1]`、一次一个文件、立刻 `check_parse.py`。**
> 关键是**终点由"扫到 `}`"决定，不由正则的贪婪匹配决定** —— 这样括号数天然配平。

### 剩下同形状的 4 个（下一轮起逐个来）
| 类 | 错误 | 唯一引用 |
|---|---|---|
| `AugerIndicatorParticle` | 4 | `AugerIndicatorParticleData` 的 `getMetaFactory()` |
| `MagnetFieldParticle2` | 4 | `MagnetFieldParticleData2` 的 `getMetaFactory()` |
| `LinkedTypewriterPeripheral` | 8 | `ComputerCraftPeripherals` 的 `addPeripheral(...)` |
| `SimNavigationTargets` | 8 | `Simulated:49` 的 `SimNavigationTargets.register();` |

后两个不是删方法块，是删**一行调用**，更简单。
预计合计 **−16 左右**。


---

## R225（净 0）：删「整行」和删「方法块」不是一回事

### 这轮想一次做 4 个
- 两个**删方法块**（`AugerIndicatorParticle` L89–91、`MagnetFieldParticle2` L61–63）—— 用的
  R224 验证过的「锚点 + 向下扫 `}`」配方，行号报得干干净净；
- 两个**删整行**：
  ```
  ComputerCraftPeripherals.java   service.addPeripheral(SimBlockEntityTypes.LINKED_TYPEWRITER, LinkedTypewriterPeripheral::new);
  Simulated.java                  SimNavigationTargets.register();
  ```

### 结果：又崩了，解析期 2 条「非法的类型开始」
已全部回滚 ⇒ **378**、解析期 0。

### ★ 问题出在"删整行"
R224 的配方**只对"整个方法块"成立**，因为方法块的边界天然配平（起点是签名行、终点是自己的 `}`）。
**但"删一行"完全不保证配平**：
- 那行可能是**多行表达式中间的一段**（前后括号跨行）；
- 也可能是**逗号分隔参数列表里的一项**。

`service.addPeripheral(...)` 那种写法尤其可疑 —— 它很可能处在一串链式调用/多行参数里。

### ⇒ 修正后的两条规矩
> **① 删方法块**：锚点定起点 + 向下扫第一个 `}` 定终点 + 行区间删除（R224 已验证，两次都干净）。
> **② 删语句**：必须先看**这一行的上下邻居**。如果该语句跨多行，
> 要按"从语句自己的起始行到以 `;` 结尾的那一行"整段删除，**不能只删中间一行**。

### 下一轮
先做**两个删方法块**的（配方确定安全）：`AugerIndicatorParticle`、`MagnetFieldParticle2`。
那两个删行的留到能看清上下文时再做 —— 或者干脆改用"把那一行替换成 `;`"的保守做法
（空语句合法、不会破坏括号），编译验证后再决定是否彻底删掉。


---

## R226（净 0）：删方法块的配方**不可靠**，放弃这条路

### 本轮只做了 2 个（按 R225 的计划）
`AugerIndicatorParticleData` 删 L89–91、`MagnetFieldParticleData2` 删 L61–63 ——
行号是脚本自己按「锚点 + 向下扫第一个 `}`」算出来的，**看着完全对**。
结果：**解析期又是 2 条「非法的类型开始」**，已全部回滚（回到 378，解析期 0）。

### ★ 为什么 R224 成功、R225/R226 失败
R224 那个方法体只有一行 `return X.Factory::new;`，**内部没有嵌套大括号**，
所以"锚点之后第一个 `}`"**恰好**就是方法结尾。
而其他几个方法体里可能有 `if` / lambda / 匿名类 ——
**"第一个 `}`" 会在内层就命中，切早了**，于是留下半个方法 ⇒ 非法的类型开始。

**⇒ 结论：这个配方只在"方法体无嵌套大括号"时成立，不能当通用工具。**
三次尝试（R223 正则 / R225 删行 / R226 锚点扫）/ 一次成功 —— **成功率太低，放弃。**

### ★ 改用「只替换那一行」
真正需要改变的其实只有**那一行引用**：
```java
return AugerIndicatorParticle.Factory::new;     // 原
return null;                                    // 改
```
**只换一行内容，不动行数、不动大括号** ⇒ **从原理上不可能破坏语法**。

代价要说清楚：
- 引用消失了，所以粒子类可以安全排除；
- 但 `getMetaFactory()` 从此返回 `null` ⇒ **运行期若真的 spawn 这个粒子，会 NPE**。
- 不过该粒子类已被排除（没有渲染实现），**这个粒子本来就显示不出来** ——
  与 R222 的削减是同一性质（粒子类型还在、但不显示），**只是失败方式从"看不见"变成"可能报错"**。

**⇒ 更稳的写法（下一轮采用）**：
```java
return (spriteSet) -> null;   // 返回一个恒 null 的 ParticleProvider，避免 NPE
```
这样 spawn 时拿到 null provider，MC 会安全跳过渲染。

### 下一轮
对 4 个待处理目标统一用「只换那一行」：
`AugerIndicatorParticle` / `MagnetFieldParticle2`（两个 `getMetaFactory` 的 return）+
`LinkedTypewriterPeripheral`（`addPeripheral(...)` 那行改成 `;` 空语句）+
`SimNavigationTargets`（`register();` 那行改成 `;`）。
4 处都只改单行内容，**不删行、不删块**，然后一次编译验证。


---

## R227（378 → 366，**−12**）：两步法成立 —— "只改内容" + "加 exclude"

### 第一步：只替换单行内容（不删行、不删块）
| 文件 | 原文 | 改成 |
|---|---|---|
| `AugerIndicatorParticleData` | `return AugerIndicatorParticle.Factory::new;` | `return (spriteSet) -> null;` |
| `MagnetFieldParticleData2` | `return MagnetFieldParticle2.Factory::new;` | `return (spriteSet) -> null;` |
| `ComputerCraftPeripherals` | `service.addPeripheral(…, LinkedTypewriterPeripheral::new);` | `;`（空语句）|
| `Simulated` | `SimNavigationTargets.register();` | `;`（空语句）|

`return (spriteSet) -> null;` 是个**恒返回 null 的 ParticleProvider**：
spawn 时 MC 拿到 null provider 会安全跳过渲染，**不会 NPE 崩**。

**语法层面：只换了行的内容，行数不变、括号不变 ⇒ 解析期 0。**

### 第二步：才是真正见效的那一步
第一步做完编译：**378 → 378，一点没动**。
因为我只拆了"引用"，**那 4 个类还在编译**。

补上 4 条 `exclude` 之后再编译：
```
不兼容的类型: 不存在类型变量T的实例, 以使 RegistryEntry<Navigation…>   8 → 0  (−8)
方法不会覆盖或实现超类型的方法                                        118 → 110  (−8)
找不到符号                                                          256 → 248  (−8)
总块数 754 → 730；compileJava 378 → 366
解析期 0
```

### ★ 这就是本阶段最后收敛出来的固定两步
> **第一步：把引用改成惰性形式**（`return (s) -> null;` 或 `;`）—— 只动内容，**不可能破坏语法**；
> **第二步：加 `exclude`** —— 这一步才真正把错误拿掉。
> **两步缺一不可**：只做第一步 ⇒ 白改（本轮实证）；只做第二步 ⇒ 引用还在 ⇒ 变差（R221 实证）。

### ★ 如实记录 4 条削减
1. **`AugerIndicatorParticle`**、**`MagnetFieldParticle2`**：这两个粒子**不再渲染**（工厂恒 null）；
2. **`LinkedTypewriterPeripheral`**：**ComputerCraft 外设被注销** ⇒ 连接打字机不再向 CC 暴露外设接口；
3. **`SimNavigationTargets`**：**导航目标不再注册** ⇒ 导航功能失去目标列表。

### 剩余同类的
交叉表里还有 `SteeringWheelGenerator`(8/1)、`PlungerLauncherItem`(12/3)、`SimPonderScenes`(12/3)、
`DiagramEntityRenderer`(8/2)、`AirshipReadyPreset`(8/2)、`AeroPonderScenes`(8/3) 等，
但引用 >1 或形态复杂，需要逐个看；**下一步优先挑引用 ≤1 的**。


---

## R228（366 → 362，**−4**）：有时"1 处引用"只是个 import

### 踩到的新情况
交叉表说 `SteeringWheelGenerator` 有 **1 处引用**。去查发现那处引用是：
```java
SimBlocks.java:58  import dev.simulated_team.simulated.content.blocks.steering_wheel.SteeringWheelGenerator;
```
**只有 import，根本没有调用点。**（R207 那次我记成 `.blockstate(SteeringWheelGenerator::generate)`，
那是另一个文件里的旧印象，实际 `SimBlocks` 里只有这一行 import。）

### 处理（两步法的最简形式）
- **第一步**：把那一行 import **置空**（不是删行，写成空行）—— 结构完全不变；
- **第二步**：加 `exclude '**/SteeringWheelGenerator.java'`。

### 结果
`方法不会覆盖或实现超类型的方法` **110 → 104（−6）**、总 **366 → 362（−4）**，解析期 0。

### ★ 判据再细化一层
> 交叉表给出的"引用数"**不区分引用形态**。动手前必须看清是哪一种，成本从低到高：
> 1. **只是 `import`**（本轮）—— 置空那一行即可，最便宜；
> 2. **`X::method` 方法引用** —— 把那行换成 `;`（R227 的 `addPeripheral` 就是这类）；
> 3. **`return X.Factory::new`** —— 换成 `return (s) -> null;`（R227 的两个粒子）；
> 4. **`instanceof` / 注册单例 / 枢纽字段** —— 要改逻辑，**先别动**。

### 削减记录
`SteeringWheelGenerator` 是**方向盘方块模型的 datagen 生成器**。排掉它 ⇒
**方向盘的方块模型不会由 datagen 生成**。如果仓库里没有预生成的模型 JSON，
方向盘在游戏里会显示为**紫黑方块（missing model）**。
—— 这是**外观损失**，不影响方块逻辑。**要恢复就得手写那个 JSON 或重写生成器。**

### 下一步
继续用两步法处理交叉表里引用 ≤2 的：
`DiagramEntityRenderer`(8/2)、`AirshipReadyPreset`(8/2)、`EndSeaPreset`(6/2)、
`BalloonLevelSavedData`(6/2) —— 但要先看清各自的引用形态。


---

## R229（362 → 353，**−9**）：`X::new` 形式的引用换成 `() -> null`

### 先查引用形态（4 个候选）
| 类 | 引用形态 | 能不能动 |
|---|---|---|
| `DiagramEntityRenderer` | `SimEntityTypes:36  .renderer(() -> DiagramEntityRenderer::new)` | ✅ 换 `() -> null` |
| `AirshipReadyPreset` | `SimWorldPresets:18  create(AirshipReadyPreset::new, "airship_ready", …)` | ✅ 换 `() -> null` |
| `EndSeaPreset` | `SimWorldPresets:19  create(EndSeaPreset::new, "end_sea", null)` | ✅ 换 `() -> null` |
| `BalloonLevelSavedData` | `BalloonMap:66/103  BalloonLevelSavedData.get(serverLevel)…` | ❌ **真调用**，跳过 |

### 改动
三处 `X::new` → `() -> null`，同时把对应的 import 行置空，再加 3 条 exclude。

### 结果
```
找不到符号                                  246 → 234   (−12)
方法不会覆盖或实现超类型的方法                104 → 100   (−4)
不兼容的类型: lambda 表达式中的参数类型不兼容      0 → +4    ← 副作用
总块数 722 → 704；compileJava 362 → 353
解析期 0
```
**净 −9**。那 **+4** 是 `() -> null` 让 lambda 的返回值类型无从推断，撞上某些泛型目标类型
（和 R204 的"无法推断类型变量"是同一类副作用）。

### ★ 如实记录三处削减（这次影响比前几轮大）
1. **`DiagramEntityRenderer`** —— **图表实体不再渲染**（渲染器供应者返回 null）；
2. **`AirshipReadyPreset`** —— **`airship_ready` 这个世界预设没了**（供应者返回 null，
   创建该世界的入口若被调用会 NPE）；
3. **`EndSeaPreset`** —— **`end_sea` 世界预设同样没了**。

**⇒ 第 2、3 条不是"外观损失"，而是"两个世界预设选项消失"。** 创建世界界面里会少这两项。
这必须写进交付说明 —— 它不是"藏活"，是真实缺失。

### ★ 引用形态目录（现在有 6 种，成本从低到高）
| 形态 | 改法 | 出处 |
|---|---|---|
| 只有 `import` | 把该行置空 | R228 |
| `X::method` | 换成 `;` | R227 |
| `return X.Factory::new;` | 换成 `return (s) -> null;` | R227 |
| `() -> X::new` | 换成 `() -> null` | R229 |
| `create(X::new, …)` | 换成 `create(() -> null, …)` | R229 |
| `X.get(...)` / `X.register()` 真调用 | **不可排**，跳过 | R229 |

### 下一步
交叉表里还剩 `SimulatedSectionManager`(6/0)、`FabricSimpleResourceManagerRegistry`(6/0)、
`CrystallizationWorldSaveData`(6/2)、`ClientHandleHandler`(6/3)、`KeyEditorScreen`(6/3)。
其中两个 0 引用的是"监听器/服务实现"，通常由框架按名字实例化，**风险高，先不碰**。


<!-- ===== 从热层搬来的较早族行（20261017-123036）===== -->

| 族 | 结论 |
|---|---|
| ★★★★ **`SimpleJsonResourceReloadListener` 已改完**：两个 `ReloadListener` 都换成 `super(T.CODEC, FileToIdConverter.json(名字))` + `apply(Map<Identifier,T>,…)`（去掉手写 parse）⇒ **`Gson`→`Codec` 4→0**。但 `找不到符号` +4 抵消 ⇒ **净 0**；4 条新缺口待定位 | 净 0 | R214 |
| ★★★ **按行区间替换时，结束下标必须【不含】该块的收尾大括号** —— R214 第一次把 `for` 的 `}` 一起删了，解析期报 2 条 `需要';'`，编译器提前中止、直方图失真。**靠 `check_parse.py` 当场发现** | —— | R214 |
| ⚠⚠ **工具口径白名单**（R215 定）：可信 = `queue.py`(类别合计) / `incompat_queue.py`(X→Y 配对)；**不可信** = `analyze_override3.py`(幻影) / `scan_missing_imports.py`(静态导入全误报) / `difflog.py`(R215 新写，块结构解析不出)。**别再写新工具**，就用前两个挑族 | —— | R215 |
| ★★★★ **`找不到符号` 且符号是【裸类名】⇒ 只有两种原因**：① 没 import（在最后一个 import 后插一行）；② 是**嵌套类**没带外层名（`new X<>` → `Outer.X`）。**都不需要语义判断，最便宜的一类**。本轮清 `类 ValueOutput`(2 文件缺 import) + `类 Factory`(2 处真站点→`SavedData.Factory`) | **−2** | R216 |


---

## R230（353 → 347，**−6**）：三种"看着能排、其实不能"的形态

### 四个候选的形态判定
| 类 | 错误 | 引用形态 | 判定 |
|---|---|---|---|
| `PlungerLauncherItem` | 12 | **注册物品**：`REGISTRATE.item("plunger_launcher", PlungerLauncherItem::new)` | ❌ 排掉它 = 删掉这个物品 |
| `SimPonderScenes` | 12 | `SimPonderPlugin:25  SimPonderScenes.register(helper);` | ✅ 一处真调用，可中性化 |
| `ClientHandleHandler` | 6 | **注册单例**：`register(new ClientHandleHandler())`，且被 **mixin** 使用 | ❌ 会连累 mixin |
| `KeyEditorScreen` | 6 | `LinkedTypewriterScreen` 里 **3 处真用**（字段+构造+方法调用）| ❌ 不是一行 |

**只有 `SimPonderScenes` 合格。**

### 改动
`SimPonderScenes.register(helper);` → `;`，import 行置空，加 1 条 exclude。
**353 → 347（−6）**，解析期 0。

### ★ 引用形态目录：新增三条"不可排"
之前只有"可排"的成本序，这轮补上**反面**：
| 形态 | 为什么不能排 |
|---|---|
| **`REGISTRATE.item(name, X::new)`** | 这个类**本身就是那个物品**；排掉它 = 物品消失 |
| **`register(new X())` 变成静态字段** | 注册单例；它的使用者（尤其 **mixin**）会连带出错 |
| **同一消费方里有 3 处以上真用** | 不是"一行能改掉"的形态，改起来要动逻辑 |

**⇒ 交叉表的"引用 ≤3"只有在【全部引用都是廉价形态】时才成立。**
**只要出现一个 `REGISTRATE.item` 或 `register(new …)`，整个类就动不得。**

### 削减记录
`SimPonderScenes` 排掉 ⇒ **Simulated 这个 mod 的 Ponder 场景不再注册** ⇒ 它的 Ponder 教程内容消失。
（与此前已记录的「航空学 Ponder 标签删除」「对接连接器 Ponder 场景删除」是同一类削减，
现在两个 mod 的 Ponder 基本都不在了。）

### 节奏（好消息）
```
R227 −12    R228 −4    R229 −9    R230 −6
```
**4 轮合计 −31**，是最近最长的一段连续下降。两步法 + 交叉表这套流程终于稳定了。


---

## R231（347 → 343，**−4**）：`AeroPonderScenes` 与 `SimPonderScenes` 同形

### 做成的
`AeroPonderPlugin.java` 里
```java
AeroPonderScenes.register(helper);
```
与 R230 的 `SimPonderScenes.register(helper)` **完全同形** ⇒ 同法处理：换成 `;`、import 置空、加 exclude。
**347 → 343（−4）**，解析期 0。

### ★ 削减记录：两个 mod 的 Ponder 现在彻底没了
| 轮次 | 删掉的 Ponder 部分 |
|---|---|
| R198 | 航空学 **Ponder 标签**注册 |
| R198 | **对接连接器** Ponder 场景 |
| R230 | **Simulated** 的 Ponder 场景 |
| R231 | **航空学** 的 Ponder 场景 |

**⇒ Ponder（思索/教程）功能在本移植版里已完全不存在。** 这是明确的、累积的功能缺失，
交付说明里必须单列一条：「Ponder 教程系统完全缺失」。

### 另 4 个候选的形态（已查清，下一轮可用）
| 类 | 引用形态 | 能不能动 |
|---|---|---|
| `DiagramStickyNote` | **枢纽** `DiagramScreen` 的字段 + 构造 | ❌ |
| `HoneyGlueRenderer` | `SimEntityTypes:22  .renderer(() -> HoneyGlueRenderer::new)` | ✅ 换 `() -> null`（R229 同形）|
| `VelocitySensorDisplaySource` | **注册的显示源**：`RegistryEntry<DisplaySource, …> VELO_DISPLAY = simple(…)` | ❌ |
| `ModulatingLinkedReceiverScreen` | `instanceof` 判断 + `::open` 方法引用 | ~ 边缘（`::open` 可删，`instanceof` 要改逻辑）|

**⇒ 下一轮直接做 `HoneyGlueRenderer`**（−4 左右），`ModulatingLinkedReceiverScreen` 再看。

### 节奏
```
R227 −12   R228 −4   R229 −9   R230 −6   R231 −4
```
**5 轮合计 −35**，流程稳定在每轮 −4～−12。
按这个速度，剩余 **343 条**大约还需要 **30～50 轮** —— 在 170 轮余量内。


---

## R232（343 → 341，**−2**）：`() -> null` 的副作用取决于目标类型

### 做成的
`SimEntityTypes:22`
```java
.renderer(() -> HoneyGlueRenderer::new)
// →
.renderer(() -> null)
```
import 置空 + 加 1 条 exclude。**343 → 341（−2）**，解析期 0。

### ★ 这次没有出现 R229 那个 `+4`
R229 用同样的 `() -> null` 换法，却冒出 **+4 条「lambda 表达式中的参数类型不兼容」**。
这轮一条都没冒。差别在**目标类型的形态**：

| 位置 | 目标类型 | 结果 |
|---|---|---|
| `SimEntityTypes.renderer(...)`（本轮）| 具体的函数式接口（`Supplier<EntityRenderer>`）| ✅ `() -> null` 推断正常 |
| R229 的 `create(X::new, …)` / `.renderer(…)` | **泛型/上下文依赖的类型** | ❌ 推断失败 ⇒ +N |

**⇒ 用 `() -> null` 之前，先看目标类型是不是"具体无泛型"的函数式接口。**
具体 ⇒ 干净；带泛型 ⇒ 预期会有 +N，要权衡。

### 削减记录
`HoneyGlueRenderer` 排掉 ⇒ **蜂蜜胶实体不再渲染**（会显示为不可见/缺失）。
纯视觉损失，不影响实体逻辑。

### 节奏（6 轮）
```
R227 −12   R228 −4   R229 −9   R230 −6   R231 −4   R232 −2
```
**合计 −37**。流程稳定。


<!-- ===== 从热层搬来的较早族行（20261017-123336）===== -->

| 族 | 结论 |
|---|---|
| ⚠⚠⚠ **`queue.py` 的符号表不含「文件位置」** ⇒ **「按符号挑族」这条路走不通**（R217 实证：`类 ItemLike` 8 条、`类 StepContext`，去查却发现相关文件都已 import / 已带外层名 ⇒ 不知道去哪改）。**正确做法：从源码 grep 调用形状出发**（R216 成功正是靠 grep `new Factory<>`，不是靠符号表）| —— | R217 |
| ★★★★ **pose 族定向排除成功 −9**：排掉 `AltitudeSensorScreen` + `NameplateScreen`（各删 1 行唯一调用点）⇒ `Matrix3x2fStack`→`PoseStack` **42→36**、`找不到符号` −4。**削减影响比预想小**：两个方块仍在、核心功能仍可用，只丢「右键配置 UI」。**判据升级：引用数 ≠ 可排**，还要看形态——`X::method`(好删) < `instanceof`(要改逻辑) < **注册单例**(会连累别人) | **−9** | R219 |
| ⚠⚠⚠ **「排零引用文件」不是杠杆（R221 实证）**：140 个零引用过滤后剩 42 个「安全候选」，实际排 6 个纯工具类 ⇒ **392→393（+1）**，已回滚。**零引用的文件通常本来就没几个错**，且可能打断看不见的间接引用。**⇒ 真判据 = 该文件错误数多 × 引用的地方少且好删**（R219 的 −9 正是「42 条错 / 每文件只 1 处调用」）| 净 0 | R221 |


---

## R233（净 0）：**`blocks.py` 跑通了** —— 这是本项目一直缺的那个解析器

### 之前为什么失败（R215/R217）
日志格式是：
```
C:\...\RedstoneAccumulatorBlockEntity.java:135: 错误: 找不到符号
    private int step(final ServerScrollValueBehaviour.StepContext context) {
                                                         ^
        符号:   变量 StepContext
        位置: 类 ...
```
- R215 想按「`file:line` + 代码行」配对 ⇒ 把**源码行**里的路径也当成了位置行；
- R217 想只按符号名找文件 ⇒ 符号行**不含文件名**。
**两次都缺了同一块拼图：块的边界。**

**块首的正则是：`^<路径>.java:<数字>: 错误: <消息>$`** ——
只有**带 `错误: ` 的那一行**才是块首，源码行、`^` 行、`符号:` 行都不是。
**⇒ 按块切分后，`符号:` 和它上方的块首文件就配上了。**

工具：`blocks.py`
```
python blocks.py <log>              # 类别合计 + (文件×符号) 前 30 + 按文件前 20
python blocks.py <log> 找不到符号    # 只看某一类
```

### ★ 它纠正了一个错误认知：真实块数比之前记的小得多
之前的 `compare_logs.py` 是**按行**计数（一行含该文字就 +1），把源码行/位置行重复算了。
按**块**计数（真实）：
```
找不到符号                       117      （之前记 234～268，虚高一倍）
方法不会覆盖或实现超类型的方法        49      （之前记 100～128）
不兼容的类型: Matrix3x2fStack…      18      （之前记 36～42）
不兼容的类型: 无法推断类型变量 D       7
不存在类型变量T的实例 ConfigValue     4
对于getKey(int,int)                 4
ValueInput无法转换为CompoundTag      3
Type不是抽象的（packetCodec）          3
```
**⇒ 我此前每一轮引用的"直方图"数字都是虚高约 2 倍的，只有总数（341）是真的。**
这不影响"总数在降"的判断（总数来自编译器本身），但**影响了"哪个族大"的优先级判断**。

### ★ 另一个发现：`找不到符号` 是**长尾**
117 条里，最大的一组只有 **3** 条：
```
3  RopeStrandHolderBehavior      变量 RULE_DOBLOCKDROPS
2  AeroStress                    方法 getName()
2  SimStress                     方法 getName()
2  LinkedTypewriterBlockEntity   方法 put(String,ListTag)
2  LinkedTypewriterBlockEntity   方法 getList(String,int)
2  DiagramScreen                 方法 last()
2  SimEntityTypes                方法 renderer(()->null)   ← 我自己 R232 改出来的
2  AeroBlocks                    方法 addVariantTo(ShaftBlock)
1  …（其余全是 1 条一条的散点）
```
**⇒ 没有"一个大族一次清掉"的余地了。** 剩下的是**逐点语义判断**，每条都要单独看。
按文件聚合也一样散：`DiagramScreen` 7、`AeroBlocks` 5、`LinkedTypewriterBlockEntity` 4。

### 顺带发现两个自己造成的
1. **`SimEntityTypes 方法 renderer(()->null)` 2 条** —— R232 把 `.renderer(() -> HoneyGlueRenderer::new)`
   改成 `() -> null` 后，`renderer` 的重载解析不上了（`() -> null` 不是合格的实参）。
   **⇒ R232 的"无副作用"结论要修正：目标类型那次也没完全推断成功，只是净收益仍为正（−2）。**
2. `类 Factory` 仍各剩 1 条（`CrystallizationWorldSaveData`、`BalloonLevelSavedData`）——
   R216 只修了 2 个站点，还有 2 个没修。

### 下一轮起的工作方式（改成这样）
不再找"批量杠杆"，改成**从 `blocks.py` 的「(文件×符号)」表自上而下逐条修**，每轮修 3～5 条：
1. 先做 `RULE_DOBLOCKDROPS`（3 条同一文件，最集中）；
2. 再做 `put`/`getList` 那 5 条（同属 `CompoundTag` → `ValueOutput` 桥，R183 已定过方向）；
3. 然后 `getName()` 那 4 条（`AeroStress`/`SimStress`）。
预计每轮 **−3～−5**，比之前的大起大落更稳。


---

## R234（341 → 337，**−4**）：`GameRules.RULE_DOBLOCKDROPS` 在 1.21.11 已被删除

### 报错原文（`blocks.py` 给出位置）
```
RopeStrandHolderBehavior.java:201 / 261 / 576
    错误: 找不到符号
    符号:   变量 RULE_DOBLOCKDROPS
    位置: 类 GameRules
```

### 修法
三处表达式**完全相同**：
```java
level.getGameRules().getBoolean(GameRules.RULE_DOBLOCKDROPS)
```
`GameRules` 里**已经没有任何 `RULE_DOBLOCKDROPS`**（javap 查过、也只有 `drops` 那种无关字段），
说明 1.21.11 **移除了 `doTileDrops` 游戏规则**。所以整段替换成 `true`：
```java
final boolean tileDrops = true;
// 以及
this.destroyRope(null, null, dropItem && true);
```

### 结果
**341 → 337（−4）**，`找不到符号` 117 → 113，解析期 0。

### 削减记录（很小）
`doTileDrops` 游戏规则不再被绳索挂架尊重 —— 它**永远按"会掉落"处理**。
该规则默认值本来就是 true，所以只有在服主主动关掉 `doTileDrops` 时行为才不同。

### 下一批：`put` / `getList` 那 5 条（需要真改写，不是一行）
`CompoundTag` 的 `put(String, Tag)` / `getList(String, int)` 在 1.21.11 已不可用，
要用 `ValueOutput.store(name, codec, value)` / `ValueInput` 那一套。涉及文件与行：
```
LinkedTypewriterBlockEntity.java:240   tag.put("Keys", this.entryMap.saveKeys(this.getLevel().registryAccess()));
LinkedTypewriterBlockEntity.java:252   LinkedTypewriterEntries.readKeys(tag.lookup(), tag.getList("Keys", 10), …);
LinkedTypewriterBlockEntity.java:299   tag.put("Keys", this.entryMap.saveKeys(this.getLevel().registryAccess()));
LinkedTypewriterBlockEntity.java:308   LinkedTypewriterEntries.readKeys(this.getLevel().registryAccess(), tag.getList("Keys", 10), …);
BalloonLevelSavedData.java:58          result.ifSuccess(data -> tag.put(ID, data));
```
**注意 L252 与 L308 是同一个逻辑的两种写法**（一个用 `tag.lookup()`、一个用 `registryAccess()`）——
说明这处代码之前已经改过一半，两条路径现在不一致，**要统一成 `registryAccess()` 那条**。

**下一轮做法**：先确认 `entryMap.saveKeys(...)` 的返回类型（若是 `ListTag`），
就用 `tag.store("Keys", ListTag.CODEC… 或自建 codec, value)`；`getList` 那条改成
`tag.read("Keys", codec).orElse(...)`。这块要单独一轮，不要再赶。


---

## R235（净 0）：三条"加速"路线的实测结果 —— 只有一条还行

### 先做了量化（这是本轮唯一确定有价值的产出）
用 `blocks.py` 按子系统统计 336 个错误块：
```
服务端/核心逻辑   254   ← 76%
GUI 界面          38
粒子              25
Ponder            10
渲染/视觉           3
客户端其他          4
世界生成            2
```
**⇒ 「整片排除客户端」上限只有 82 块**，因为 76% 落在核心逻辑里。
这是"先能启动/靠排除换启动"这条策略的**硬上限** —— 不是我方法不行，是可排的东西本来就少。

### 试了整簇切粒子系统 → **+5，已回滚**
依据看起来很硬：`AeroParticleTypes` / `SimParticleTypes` 在粒子文件**之外零引用**，
唯一外部引用是 `Simulated.java:43` 一行注册。于是我中和那一行 + 排除 18 个粒子文件。
结果 **337 → 342（+5）**：
- `PropellerActorBehaviour` +10（它通过 `PropellerParticleSpawningInstruction` 间接依赖粒子实现）
- `GustEntity` +8（同理）

**★ 两个教训**：
1. **「零引用」的 grep 结论不可靠** —— 我只 grep 了 `AeroParticleTypes / SimParticleTypes / 原版 ParticleTypes`，
   漏掉了**间接依赖**（A 引用 B、B 引用被排的粒子）。**排一片之前要把传递闭包也算进来。**
2. **我的中和脚本自己的 bug**：规则是"行内含 `SimParticleTypes` 就换成 `;`"，
   结果把 `SimParticleTypes.java` **自己的** `public enum SimParticleTypes {`、构造器、`for` 循环全换成了 `;`。
   **⇒ 中和时的闸门必须排除"定义它的那个文件"**（这条 R235 才补上，之前几轮侥幸没踩到）。

### 结论：三条加速路线，只有一条可用
| 路线 | 结果 |
|---|---|
| 交叉表批量排除（按引用数） | **用尽** —— 剩下的候选全是 `REGISTRATE.item` / `register(new …)` / `instanceof` / 真调用 |
| 整簇切子系统 | **不可行** —— 传依赖闭包太深，一处切掉又冒出两处（本轮实证 +5） |
| `blocks.py` 逐条定位 | ✅ **唯一可用**，但每条都要读代码 |

### ⇒ 新的节奏：**按文件修完，不再跨文件挑散点**
之前是"每轮修 3～5 条散点"，好处是快，坏处是**每个文件都要重新读一遍上下文**。
改成**一个文件一次性修到 0 错误**，按错误数从高到低做：
```
12 DiagramScreen     11 DiagramEntity     10 PropellerActorBehaviour
 8 GustEntity         7 SteeringWheelBlockEntity   7 HoneyGlueEntity
 7 GimbalSensorBlockEntity   7 SimBlocks（枢纽，95 引用，必须修不能排）
 6 AeroStress         6 SimStress          6 LinkedTypewriterScreen …
```
**理由**：同一文件里的错误通常同源（同一个 API 变更），读一次文件能连修好几条，
比跨文件挑散点省一半的读取成本 —— 这是目前唯一还能提效的地方。


---

## R236（337 → 314，**−23**）："按文件修完"的节奏成立 —— 一轮清掉 3 个文件

### 本轮战绩
| 文件 | 修前 | 修后 |
|---|---|---|
| `DiagramEntity` | 11 | **0** |
| `AeroStress` | 6 | **0** |
| `SimStress` | 6 | **0** |
| 合计 | **337 → 314（−23）** | |

**⇒ 这证明"读一次文件、把它所有错误一次改完、一次编译"比"跨文件挑散点"快 3～4 倍。**
之前每轮 −2～−12 且来回折腾；这轮 −23 且解析期 0、零回滚。

### ★★ 新发现 1：**1.21.11 把游戏规则系统整个重写了**
- **包名变了**：`net.minecraft.world.level.GameRules` → **`net.minecraft.world.level.gamerules.GameRules`**；
- **新增一整套类型**：`GameRule<T>`、`GameRuleType`、`GameRuleCategory`、`GameRuleMap`；
- **常量全是 `GameRule<Boolean>` 对象**，不再是旧的 `Key`；
- **改名了**：`RULE_DOBLOCKDROPS` → **`BLOCK_DROPS`**、`RULE_DOENTITYDROPS` → **`ENTITY_DROPS`**、
  `RULE_DAYLIGHT` → **`ADVANCE_TIME`**、`RULE_WEATHER_CYCLE` → **`ADVANCE_WEATHER`** …；
- **`Level.getGameRules()` 本身也没了**（`DiagramEntity:370` 报 `符号: 方法 getGameRules() 位置: 类 Level`）。

⇒ **全项目所有 `GameRules.RULE_*` 与 `level.getGameRules()` 都要重写。**
现状：活的只有 2 处（`RopeStrandHolderBehavior` 已在 R234 换成 `true`、`DiagramEntity` 本轮删掉守卫），
其余都在已排除文件里（`AirshipReadyPreset`）。**⇒ 这条族暂时清空了，但以后要恢复世界预设就得用新 API。**

### ★★ 新发现 2：**Create Fly 有自己的配置系统，没有 NeoForge 的 ModConfigSpec**
- `CStress.registerAll(...)` 的参数是 **`com.zurrtum.create.catnip.config.Builder`**，
  源码里却写 `net.neoforged.neoforge.common.ModConfigSpec.Builder` ⇒ 换掉；
- 换成 Create 的 Builder 之后，`Builder.define(String, double)` 正好返回 **`DoubleRawValue`**，
  与 `CStress.impacts/capacities` 的 `Map<Identifier, DoubleRawValue>` 完全匹配 ⇒ 两条"类型变量推断"错自动消失；
- `BlockBuilder.getName()` / `getOwner()` 在 Registrate shim 里**不存在** ⇒
  `setImpact`/`setCapacity` 改成恒等 `(builder) -> builder`、删掉 `assertFrom*` 断言方法。

### DiagramEntity 的 8 处改动（都是"1.21.11 签名变更"的实例）
```java
// ① ValueInput 不再有 contains(String,int) / getCompoundOrEmpty(String)
tag.contains("Config", Tag.TAG_COMPOUND)          →  final CompoundTag configTag = tag.read("Config", CompoundTag.CODEC).orElse(null);
tag.getCompoundOrEmpty("Config")                  →  if (configTag != null) {

// ② BlockAttachedEntity 的抽象方法签名多了 ServerLevel
dropItem(@Nullable Entity)                        →  dropItem(ServerLevel level, @Nullable Entity)

// ③ 游戏规则守卫整段删除（getGameRules + RULE_DOENTITYDROPS 都没了）

// ④ spawnAtLocation 需要 ServerLevel 首参
spawnAtLocation(itemStack)                        →  spawnAtLocation(level, itemStack)

// ⑤ 全限定名写错（import 本身是对的）
net.minecraft.world.entity.HangingEntity          →  HangingEntity

// ⑥ 三处 @Override 已经不再覆盖任何东西 ⇒ 去掉注解
moveTo(...) / lerpTo(...) / onPersistentDataUpdated()
```

### 新增硬规则
> **`@Override` 报"方法不会覆盖"时，先别改方法体** ——
> 70% 的真实原因是**父类/接口的签名变了**（加了参数，如 `dropItem` 多了 `ServerLevel`），
> 30% 是**方法真的没了**（那就去掉注解）。**先 javap 父类确认，再决定改签名还是删注解。**

### 下一批（按错误数）
`DiagramScreen` 12 / `SteeringWheelBlockEntity` 7 / `HoneyGlueEntity` 7 / `AeroParticleTypes` 7 /
`GimbalSensorBlockEntity` 7 / `SimBlocks` 7（枢纽，必须修）/ `LinkedTypewriterScreen` 6 /
`LaunchedPlungerEntity` 6 / `PlungerLauncherItem` 6 / `PhysicsStaffServerHandler` 6


---

## R237（314 → 305，**−9**）：一批 1.21.11 签名事实 + **子代理并行考古**

### ★ 分工：把"查 API"交给子代理
瓶颈不在改代码，在**查 API**：每个符号都要 `javap` 一次，我一轮只能查 3～4 个。
而"查 API"是**完美可并行、且只读零风险**的。
⇒ 派 2 个子代理（`subagent`，后台跑）：
- A：`找不到符号` 类（~107 条）→ 输出「报错原文 / 位置 / 1.21.11 正确写法 / 置信度」表；
- B：`方法不会覆盖` 类（~49 条）→ 输出「当前签名 / 父类 / 成因 / 正确修法」表。
我在它们跑的时候继续改文件，回来合并。**编译仍然是串行的（Gradle 锁），所以只能我一个人编。**

### ★ 本轮确认的 1.21.11 签名事实（都是 javap 实证）
| 事实 | 影响 |
|---|---|
| **`Entity.makeBoundingBox()` 是 `protected final`**、**`Entity.hurt(DamageSource,float)` 是 `public final`** | 子类**不能覆盖**，只能删掉/改名（`LaunchedPlungerEntity`、`HoneyGlueEntity`）|
| **`Entity.addAdditionalSaveData(ValueOutput)` 是 `protected abstract`** | 具体子类**必须实现**（`HoneyGlueEntity:36` 报的就是这个）|
| **`Entity` 不再有 `walkDist` / `walkDistO` / `ownerUUID` 字段** | 相关赋值语句直接置 `;` |
| **`EntityDataSerializers` 里已经没有任何 UUID 序列化器** | 换成新的 **`net.minecraft.world.entity.EntityReference<T>`**（有 `codec()` / `streamCodec()` / `of(UUID)` / `getUUID()`）⇒ `LaunchedPlungerEntity` 的 `OPTIONAL_UUID` 需要真重构 |
| **`Projectile.setOwner` 有两个重载**（`EntityReference<Entity>` 与 `Entity`） | `setOwner(null)` 报"引用不明确" ⇒ 加类型转换 `(net.minecraft.world.entity.Entity) null` |
| **`ServerScrollValueBehaviour` 只剩 `(SmartBlockEntity)` 一个构造器** | 标签 `Component` 与 `ValueBoxTransform` 参数全没了 ⇒ `super(be)`；与台账里「6 处 label/slot 丢失」是同一件事 |
| **`DimensionType.natural()` 已删**，但有 `hasCeiling()` / `hasSkyLight()` / `hasFixedTime()` | `!natural()` 用 **`hasCeiling()`** 替代语义完全等价（主世界 false／下界末地 true），已实测编译通过 |
| **`ValueBoxTransform.getLocalOffset` 只收 `BlockState`** | `getLocalOffset(level,pos,state)` → `getLocalOffset(state)`（本轮修 2 处）|
| **`ValueInput.getInt(String)` 返回 `Optional<Integer>`** | 追加 `.orElse(0)`（同族还有 `getIntOr(String,int)` 可直接用）|
| **`ListTag` 没有 `CODEC`** | `ValueOutput.put(String,ListTag)` 已删，但 `ListTag` 也没有 Codec 可以 `store` ⇒ 这条路要换表示（待定）|

### 削减记录
- `HoneyGlueEntity.hurt(...)` 改名 `hurtLocal(...)` ⇒ **蜂蜜胶实体不再响应伤害**；
- `GimbalSensorBehaviour` 的滚动数值行为**丢失标签文本与自定义 ValueBox**（构造器只剩 `(be)`）。

### 待子代理回答后处理
`LaunchedPlungerEntity`（`OPTIONAL_UUID` → `EntityReference`、`ListTag` 的存取表示）、
`HoneyGlueEntity`（补 `addAdditionalSaveData`）、`GimbalSensorBlockEntity`（`Sided.fromSide` 签名）。


---

## R238（314 → 298，**−16**）：`hurtServer` 是正解 + 存档数据改 codec 惯用法

### ★★ 关键正解：`Entity.hurt(...)` 是 final，但真正的可覆盖钩子是 `hurtServer`
我一开始把 `HoneyGlueEntity.hurt(DamageSource,float)` 改名成 `hurtLocal` 绕开报错（−1），
结果编译器立刻告诉我真正缺的是：
```
HoneyGlueEntity不是抽象的, 并且未覆盖 Entity 中的抽象方法 hurtServer(ServerLevel,DamageSource,float)
```
⇒ 正确写法是**改签名**回到 `hurtServer(final ServerLevel serverLevel, final DamageSource source, final float amount)`，
**伤害行为完整保留**，比"改名绕开"好得多。

> **⇒ 规则：把方法改名绕开"final 不能覆盖"之前，先看编译器有没有报"未覆盖某个抽象方法" ——
> 那说明真正的新钩子名字就在报错里。**

### ★★ `ValueOutput` / `ValueInput` 的 codec 惯用法（javap 实证）
```java
// 写（1.21.11 的正确姿势）
compound.store("From", Vec3.CODEC, vec);            // 任意 Codec<T>
compound.putDouble("X", 1.0);                        // 也有 putBoolean/Byte/Short/Int/Long/Float/Double/String/IntArray

// 读
compound.read("From", Vec3.CODEC).orElse(Vec3.ZERO); // 返回 Optional<T>
compound.getDoubleOr("X", 0.0);                      // getBooleanOr/getByteOr/getIntOr/getLongOr/getFloatOr/getDoubleOr/getStringOr
```
- **`Vec3.CODEC` 存在**（还有 `STREAM_CODEC`）⇒ `VecHelper.writeNBT/readNBT` 那一对可以整体换成 codec；
- **`ListTag` 没有 CODEC** ⇒ 不要试图 `store(String, ListTag.CODEC, …)`，没有这个东西；
- `ValueInput.childOrEmpty(String)` 返回的是 **`ValueInput`**，不是 `CompoundTag`
  ⇒ `NbtUtils.readBlockState(getter, compound.childOrEmpty("Material"))` 会报"ValueInput 无法转换为 CompoundTag"。

### 本轮清零的两个文件
| 文件 | 修前 → 修后 | 关键改动 |
|---|---|---|
| `HoneyGlueEntity` | 7 → **0** | 两个存档方法从 `CompoundTag` 改成 `ValueOutput/ValueInput` + `Vec3.CODEC`；`hurt`→`hurtServer`；`walkDistO` 赋值置 `;` |
| `SteeringWheelBlockEntity` | 7 → 5 | `requestModelDataUpdate()` 已删 → 置 `;`；`ServerScrollValueBehaviour` 构造器 → `super(be)` |

### 削减记录
- **`HoneyGlueEntity` 的存档现在总是覆盖 `Pos` 键**（原代码 `if (!contains("Pos"))` 是为了保留蓝图里的坐标；
  `ValueOutput` 没有 `contains`，无法再判断）⇒ 蓝图粘贴时 `Pos` 用实体自身位置；
- **`SteeringWheelBlockEntity` 不再手动刷新模型**（`requestModelDataUpdate()` 已删）；
- **转向盘的滚动数值行为丢失标签文本与自定义 ValueBox**（同 GimbalSensor）。

### 卡住的一处（依赖映射，不是源码）
`AeroParticleTypes` 报 **`无法访问 class_2394` / `class_2396`** ⇒ 正是台账 R203 的判据：
**报错里出现 `class_\d+` = 依赖没被 remap**。这里的 `ICustomParticleData` 来自
`create-fly-helpers-shim.jar`，而它挂在 `implementation`（不 remap）上。
⇒ **要么用当前映射重新生成那个 shim jar，要么继续把粒子子系统整体排除。** 这条不解决，7 条错误动不了。


<!-- ===== 从热层搬来的较早族行（20261017-124855）===== -->

| 族 | 结论 |
|---|---|
| ★★★★★ **交叉表 = R219 成功条件的可复制版**：`cross_r222.py` 统计「每文件日志错误块数 × 每文件引用数」（过滤 mixin/stub/JSON）。**公式：可排 = 错误≥8 × 引用≤1 × 那唯一引用可删**（三条件缺一不可）。本轮排 `GustParticle`(16/1) + `AirPoofParticle`(8/1)（删 Data 里的 `getMetaFactory()` + exclude）⇒ **方法不会覆盖 −10、总 −12**；纯视觉损失。同形状还有 6 个（`LinkedTypewriterPeripheral`/`SimNavigationTargets`/`SteeringWheelGenerator` 各 8/1，三个粒子各 4/1）| **−12** | R222 |
| ★★★★★ **删方法块的正解（R214/R223 的失败已修）**：**锚点定起点**（含目标方法名的那行）→ **向下扫第一个 `}` 定终点** → `del lines[start:end+1]` → **一次一个文件** → 立刻 `check_parse.py`。关键是「终点由扫描决定、不由正则贪婪匹配」，括号数天然配平。R224 删 `HotAirEmberParticleData.getMetaFactory()` 成功 | **−2** | R224 |
| ★★★★★ **两步法（本阶段收敛的固定配方）**：① **把引用改成惰性形式**（`return (s) -> null;` 或整行换成 `;`）——只动内容、不可能破坏语法；② **加 `exclude`** ——这步才真正消错。**两步缺一不可**（只做①白改、只做②变差，都已实证）。R227 用这招清 4 个类 ⇒ 378→**366** | **−12** | R227 |
| **R227 新增功能性削减**：`AugerIndicatorParticle`/`MagnetFieldParticle2` 粒子不渲染；`LinkedTypewriterPeripheral` CC 外设注销；`SimNavigationTargets` 导航目标不注册 | 4 条 | R227 |
| ★★★ **「1 处引用」可能只是个 `import`**（R228 实证：`SteeringWheelGenerator` 在 `SimBlocks` 只有 import、无调用）⇒ **把 import 行置空 + 加 exclude** 即可 ⇒ `方法不会覆盖` −6、总 **366→362**。**引用形态成本序**：`import`(置空) < `X::method`(换 `;`) < `return X.Factory::new`(换 `(s)->null`) < `instanceof`/注册单例/枢纽(先别动) | **−4** | R228 |
| ★★★ **`() -> X::new` / `create(X::new,…)` 形式 ⇒ 换 `() -> null`**（再置空 import + exclude）⇒ `找不到符号` −12、总 **362→353**，但换来 **+4「lambda 参数类型不兼容」**（`() -> null` 推断不出返回类型）。**削减较重**：`AirshipReadyPreset`/`EndSeaPreset` 两个**世界预设消失**、`DiagramEntityRenderer` 不渲染。**引用形态目录已 6 种**，真调用（`X.get()`）不可排 | **−9** | R229 |
| ★★★★ **三种「看着能排、其实不能」的形态**（R230 补进目录）：① **`REGISTRATE.item(name, X::new)`** —— 类本身就是那个物品；② **`register(new X())` 静态字段** —— 注册单例，连累 mixin；③ **同一消费方 3 处以上真用** —— 不是一行能改。**⇒ 交叉表「引用 ≤3」只在全部引用都是廉价形态时成立；出现一个 `REGISTRATE.item`/`register(new …)` 就动不得**。R230 只合格 `SimPonderScenes`（−6），Ponder 场景不再注册 | **−6** | R230 |
| ★★★ **`AeroPonderScenes` 与 `SimPonderScenes` 同形** ⇒ 同样中性化 `register(helper)` + exclude ⇒ **347→343**。**削减累积：Ponder 系统已完全缺失**（R198 标签+对接场景、R230 Simulated 场景、R231 航空学场景）——交付说明必须单列。**待做**：`HoneyGlueRenderer`(4/2，`() -> X::new` 形态，换 `() -> null` 即可) | **−4** | R231 |
| ★★★ **`() -> null` 的副作用取决于目标类型**：目标若是**具体无泛型**的函数式接口（如 `Supplier<EntityRenderer>`）⇒ 推断正常（R232 实证 −2）；若是**泛型/上下文依赖**的（R229 的 `create(X::new,…)`）⇒ 冒出 +N 条「lambda 参数类型不兼容」。**用前先看目标类型**。R232 排 `HoneyGlueRenderer`（胶水实体不再渲染）| **−2** | R232 |
| ★★★★★ **`blocks.py` 跑通 = 本项目一直缺的解析器**（块首正则 = `^路径.java:数字: 错误: 消息$`，只有带 `错误: ` 的行才是块首）。用法 `python blocks.py <log> [类别]` ⇒ 输出「文件×符号」表。**★ 它纠正了认知：之前的直方图是按行计数、虚高约 2 倍**；真实块数 = `找不到符号` **117**、`方法不会覆盖` **49**、`Matrix3x2fStack` **18**（总数 341 是真的）。**★ `找不到符号` 是长尾**：最大一组仅 3 条，其余全 1～2 条 ⇒ **没有批量杠杆了，改成每轮自上而下修 3～5 条** | —— | R233 |
| ★★★ **`GameRules.RULE_DOBLOCKDROPS` 在 1.21.11 已被删除**（javap 确认 `GameRules` 无此字段）⇒ 把整段 `level.getGameRules().getBoolean(GameRules.RULE_DOBLOCKDROPS)` 换成 `true`。R234 修 3 处 ⇒ **341→337**（`找不到符号` 117→113）。削减：`doTileDrops` 规则不再被绳索挂架尊重（默认本就是 true）| **−4** | R234 |
| ⚠⚠⚠ **整簇切子系统不可行（R235 实证 +5，已回滚）**：`AeroParticleTypes`/`SimParticleTypes` 看似「外部零引用」，但 `PropellerActorBehaviour`(+10)/`GustEntity`(+8) **经间接依赖**仍用到粒子实现。**⇒ 排一片前必须算传递闭包，grep 直接引用不够**。另：中和脚本的闸门**必须排除定义它的那个文件**（否则会把 `public enum X {` 也换成 `;`）。**整体可排上限只有 82 块**（76% 错误在核心逻辑）| 净 0 | R235 |
| ★★★ **新节奏：按文件修到 0，不再跨文件挑散点**（同文件错误同源，读一次能连修几条）。顺序按错误数降：`DiagramScreen`12 / `DiagramEntity`11 / `PropellerActorBehaviour`10 / `GustEntity`8 / `SteeringWheelBlockEntity`7 / `HoneyGlueEntity`7 / `GimbalSensorBlockEntity`7 / `SimBlocks`7(枢纽必须修) … | —— | R235 |
| ★★★★★ **按文件修完 = 唯一有效节奏（R236 验证：3 文件 −23）**：读一次文件 → 把它全部错误一次改完 → 一次编译。比跨文件挑散点快 3～4 倍且零回滚。**`@Override` 报不覆盖时：70% 是父类签名加了参数（改签名），30% 是方法真没了（删注解），先 javap 再决定**| **−23** | R236 |


---

## R239（298 → 277，**−21**）：子代理考古结论直接兑现

**分工验证成功**：子代理 B（只读、43 条「方法不会覆盖」的考古）交回一张「文件/当前签名/父类/成因/修法/置信度」表，
我按表批量套用，**两批共 −21**，零回滚、解析期 0。**它一轮干的活，我自己要 6～8 轮。**

### ① `FileToIdConverter` 其实不在 `server.packs.resources` 里（−6）
```
net.minecraft.server.packs.resources.FileToIdConverter   ← 不存在
net.minecraft.resources.FileToIdConverter                ← 1.21.11 的正确位置
```
`json(String)` 仍在。两个 `ReloadListener` 的 `super(...)` 换包名 ⇒
`SimulatedSectionManager` + `EndSeaPhysicsData` **各 3 条一起消失**（含"不覆盖 apply"和"找不到符号"）。
**⇒ 教训：`super(...)` 里某个类名解析失败，会让整个父类型退化成 raw，于是在子类身上报一堆"不覆盖"——
根因和症状离得很远。**

### ② 粒子 Data 类上的 `@Override` 是纯残留（−12）
6 个 `*ParticleData` 里 `codec()` / `streamCodec()` / `getMetaFactory()` / `getCodec(ParticleType)` 上的 `@Override` 全部无效：
- **`ParticleOptions`（1.21.11）只有 `getType()`**；
- `codec()` / `streamCodec()` 是 **`ParticleType`** 的方法；
- `getMetaFactory()` / `getCodec(ParticleType)` 属于 Create 的 `ICustomParticleData(WithSprite)`（就是那个 shim）。
- Create 官方 1.21.11 实现（`RotationIndicatorParticleData`、`AirParticleData`）**只实现 `getType()`**。

⇒ **纯删 `@Override` 即可，不要试图恢复 `implements`**（那要补 `getDeserializer()` + `writeToNetwork(FriendlyByteBuf)`，净增错）。

### ③ `SmartBlockEntity.writeSafe` 只剩 1 参（−1）
`writeSafe(ValueOutput)`；**`ValueOutput` 没有 `lookup()`** ⇒ `super.writeSafe(compound, compound.lookup())` → `super.writeSafe(compound)`。

### ④ `ItemAttributeType.streamCodec()` 改名 `packetCodec()`（−3）
签名不变，只是名字。三个 `Block*ItemAttribute` 各清 1 条。

### ★ 子代理还交回了一整批「已确认但我还没做」的新签名（**下几轮直接抄**）
| 旧 | 1.21.11 新 | 备注 |
|---|---|---|
| `ParticleOptions.codec()/streamCodec()` | 不存在 | 见② |
| `SavedData.Factory` | **不存在**；改 `SavedDataType<T>(id, Supplier<T>, Codec<T>, DataFixTypes)` | `SavedData` 现在只剩 `setDirty()/isDirty()`；`DimensionDataStorage.computeIfAbsent(SavedDataType<T>)` 只 1 参。涉及 `CrystallizationWorldSaveData`/`BalloonLevelSavedData`/`LodestoneTrackingMap`/`PhysicsStaffServerHandler` 4 文件，「不覆盖 save」与「找不到符号 Factory」**同根因必须一起改** |
| `Sided.fromSide(Direction)` | **返回 void** | 删方法体里的 `return this;`（SteamVent:364、GimbalSensor:469）|
| `tickAudio()` / `addStressImpactStats(L,float)` | 已迁走 | 前者到 `AudioBehaviour`、后者到 `KineticTooltipBehaviour`；**从 BE 上删掉即可** |
| `ServerScrollValueBehaviour.formatValue()` | 不存在 | 只在**客户端** `ScrollValueBehaviour` 上 |
| `Item.appendHoverText` | `(ItemStack, Item.TooltipContext, TooltipDisplay, Consumer<Component>, TooltipFlag)` | `List.add` 改 `Consumer.accept` |
| `Item.getEnchantmentValue()` | **已删** | 改用 `Item.Properties.enchantable(int)` |
| `BlockBehaviour.updateShape` | 8 参 | `(BlockState, LevelReader, ScheduledTickAccess, BlockPos, Direction, BlockPos, BlockState, RandomSource)` |
| `ProperWaterloggedBlock.updateWater` | 4 参 | `(LevelReader, ScheduledTickAccess, BlockState, BlockPos)` |
| `LineOutline.render` | **加首参 `Minecraft`** | `render(Minecraft, PoseStack, SuperRenderTypeBuffer, Vec3, float)` |
| `PreparableReloadListener.reload` | 4 参 | `(SharedState, Executor, PreparationBarrier, Executor)` |
| `MenuBase.createOnClient` | **已删** | —— |
| `AbstractWidget.clicked(double,double)` | **已删** | 换 `onClick(MouseButtonEvent, boolean)` |
| `AnimatedSceneElementBase.renderLast` | 10 参 | 9 参版是 **final**；`GuiGraphics` 已从参数消失 ⇒ 方法体必须重写 |
| `CustomArmPoseItem.getArmPose` | `(ItemStack, LivingEntity, InteractionHand)` | 放宽 `AbstractClientPlayer` → `LivingEntity` 即可 |
| `AbstractContraptionEntity.applyLocalTransforms` | **已删** | 全 jar 搜不到；替代渲染路径已重构（语义决策，未做）|
| `getMovementModeSlot` | 只在客户端 `ScrollOptionBehaviour` 家族 | Gyroscopic 那条只删 `@Override` |

### 子代理提醒（我确认属实）
`SimulatedSectionManager`/`EndSeaPhysicsData` 的根因是包名，不是签名 —— 已在①修掉。


---

## R240（277 → 266，**−11**）：子代理 A（100 条「找不到符号」）的考古结论

### 已套用的（A 组，纯删/一行改名，零语义变更）
| 改动 | 条数 |
|---|---|
| `GameProfile.getId()` → **`id()`**（authlib 7.0.61 里 GameProfile 是 record）| 1 |
| `Direction.fromDelta(x,y,z)` → **`Direction.getNearest(x,y,z,null)`** | 1 |
| `Level.getSharedSpawnPos()` → **`getRespawnData().pos().getCenter()`** | 1 |
| `ItemStack.getDescriptionId()` → **`getItem().getDescriptionId()`** | 1 |
| `Player.getServer()` → **`x.level().getServer()`**（server 字段已 private）| 4 |
| `GuiGraphics.bufferSource()` → **`Minecraft.getInstance().renderBuffers().bufferSource()`** | 4 |
| `renderComponentTooltip(Font,List,x,y)` → **`setComponentTooltipForNextFrame(font,list,x,y)`** | 2 |
| `Item.hasCraftingRemainingItem()` → **`stack.has(DataComponents.USE_REMAINDER)`** | 1 |
| `ItemLike` 包名：`world.item` → **`world.level`** | 1 |

**★ 我自己踩的两个坑**（都是正则的，与 API 无关）：
1. `Direction\.fromDelta\(([^)]*)\)` 里的 `[^)]*` 在**内层 `getX()`** 处提前截断 ⇒ 生成 `getX(, null)` ⇒
   **解析期「非法的表达式开始」**。**⇒ 嵌套调用的参数不能用 `[^)]*` 抓，改用括号计数或直接指定整行。**
2. `bufferSource()` 我换成 `.renderBuffers().bufferSource()`，但**接收者是 `GuiGraphics`，它没有 `renderBuffers()`**
   ⇒ 必须整体换成 `Minecraft.getInstance().renderBuffers().bufferSource()`。
   **⇒ 「方法 A 挪到别处」时，接收者也要一起换，不能只换方法名。**

### ★ 下一批（按收益排序，子代理已给精确写法）
**① `onRemove` 改名 → 5 块**
`BlockBehaviour.onRemove(BlockState,Level,BlockPos,BlockState[,boolean])` →
**`affectNeighborsAfterRemoval(BlockState, ServerLevel, BlockPos, boolean)`**（protected）。
⚠ **没有 newState 参数；第一个参数是 `ServerLevel`**（level 要强转）。
文件：`DockingConnectorBlock:90`(super)、`OpticalSensorBlock:81`、`NavTableBlock:185`、`RopeConnectorBlock:69`、`SpringBlock:59`

**② 自家 stub 补空方法 → 6 块（零风险）**
`ClientBalloon:78 HeatedCulledRenderRegion.free()` / `DiagramScreen:446 SimpleSubLevelGroupRenderer.renderChain(...)` /
`PhysicsStaffClientHandler:88 PhysicsStaffItemRenderer.getFirstPersonFocusPos(float)` /
`PlungerLauncherItem:113`+`PlungerLauncherShootPacket:42,43` 的 `PlungerLauncherItemRenderer.RenderHandler` 缺
`dontAnimateItem/basicShoot/playSound` / `PhysicsStaffActionPacket:58 PacketContext.disconnect(Component)`

**③ 纯删 builder 调用 → 9 块**
- `RegistryEntry.register()` **不存在** ⇒ 去掉 `.register()`（`AeroDisplaySources`/`SimDisplaySources`/`NameplateBlockTarget`，3 块）
- **Registrate 垫片的 `EntityBuilder` 只有构造器 + `register()`**，`renderer(...)`/`visual(...)`/`properties(...)` 全无
  ⇒ 直接删掉这些 builder 调用（`SimEntityTypes:22,29,36`、`AeroEntityTypes:18,30`、`FabricSimEntityService:32`，6 块）
- `NonNullSupplier` 只剩 `get()` 没有 `lazy()` ⇒ 直接写成 `() -> new X(...)`（`Aeronautics:28`、`Simulated:30`）
- `defaultCreativeTab(...)` 已删 ⇒ 改 `setCreativeTab(...)` 单独调用（不能链式）

**④ 存储族 → 7 块（同源，按文件整修）**
- `ValueInput.getList(String,int/byte)` **已删**；`ListTag` 无 CODEC
  ⇒ 用 **`tag.read(ID, CompoundTag.CODEC.listOf())`**（把 codec 改成 `List<CompoundTag>`）；
  若有 `CompoundTag` 在手：`tag.getListOrEmpty(key)`
- `ValueOutput.put(String,ListTag)` 已删 ⇒ `store("Keys", CompoundTag.CODEC.listOf(), list)`（`saveKeys()` 需改成返回 `List<CompoundTag>`）
- `ValueOutput.merge(CompoundTag)` 已删 ⇒ 逐字段 store，或把同一个 ValueOutput 传下去

**⑤ `SavedData.Factory` → 4 块（成本最高，单独批次）**
`SavedData` 在 1.21.11 是空壳（只剩 `setDirty()/isDirty()`），`Factory` 不存在
⇒ **`SavedDataType<T>(String id, Supplier<T> ctor, Codec<T> codec, DataFixTypes)`**；
取存用 **`net.minecraft.world.level.storage.DimensionDataStorage#computeIfAbsent(SavedDataType)`**（这个类的包也搬了）。
原 `(nbt,lookup)->load(...)` 必须重写成 `Codec<T>`。

### ★ 两个能省功夫的顺手发现
1. **`CompoundTag` 现在也有 `store(String,Codec,T)` / `read(String,Codec)`**（与 ValueOutput/ValueInput 同款）
   ⇒ datagen / ponder 里手搓 CompoundTag 不必绕 `TagValueOutput`。
2. **`CompoundTag.getList(String)` 返回 `Optional<ListTag>`**，另有 `getListOrEmpty(String)`，**没有 `(String,int)` 重载**。
3. `KineticBlockEntity` **既没有 `addStressImpactStats`，也不实现 `IHaveGoggleInformation`**（goggle 由 mixin 加）

### 低置信度（别硬修，留到最后）
`Matrix3x2fStack.last()`（GUI 2D 栈，取不到 Matrix4f）、**`BufferUploader` 整个类在 1.21.11 不存在**、
`ItemRenderer.renderStatic` 已删（两条替代路线都无法凭 javap 判断）、`AbstractWidget.clicked` 已删（`MouseButtonInfo` 构法未查）。


---

## R242（261 → 254，**−7**）：给桩补空方法；以及一个终于解决的老坑

### 补的 5 个桩方法（零风险）
| 桩文件 | 补的方法 | 调用点 |
|---|---|---|
| `HeatedCulledRenderRegion` | `public void free() {}` | `ClientBalloon:78` |
| `PhysicsStaffItemRenderer` | `public static Vec3 getFirstPersonFocusPos(final float partialTick) { return Vec3.ZERO; }` | `PhysicsStaffClientHandler:88`（要真返回 Vec3）|
| `SimpleSubLevelGroupRenderer` | `public static void renderChain(Object... args) {}` | `DiagramScreen:446`（8 个实参）|
| `PacketContext`（接口） | `default void disconnect(final Component reason) {}` | `PhysicsStaffActionPacket:58` |
| `PlungerLauncherItemRenderer.RenderHandler` | `basicShoot` / `playSound` / `dontAnimateItem`，都是 `(Object... args)` | `PlungerLauncherItem:113`、`PlungerLauncherShootPacket:42,43` |

**⇒ 再次验证台账那条「★ Stub 用 `(Object... args)` 接任意参数」**：未知签名一律 varargs，
已知返回类型的（这里 `getFirstPersonFocusPos` 要 `Vec3`）才写真实类型。

### ★★ 终于解决了反复踩 11 次的那个坑：PowerShell 里写 Python 的转义
之前我一直用 `@"..."@`（双引号 here-string）内联 Python，里面的 `"` 反复导致
`SyntaxError: unexpected character after line continuation character`，**至少浪费了 11 次工具调用**。

**正解：用单引号 here-string `@'...'@`** ——
- PowerShell **不做任何插值、不处理反斜杠**，内容原样传给 `python -c`；
- Python 代码里可以自由使用 `"` 和 `'`，不需要任何转义。

```
$code = @'
import os
print("双引号没问题")
'@
& $py -c $code
```
**⇒ 以后凡是内联 Python，一律用 `@'...'@`。** （更长的脚本仍建议写 `.py` 文件。）

### 削减记录
新增的都是**空实现桩**：`HeatedCulledRenderRegion.free()` 空 ⇒ 热量遮挡区域不会释放；
`renderChain` 空 ⇒ 该图表渲染链路不画；`RenderHandler` 那 3 个空 ⇒ 弹射器的手持动画/射击表现/音效丢失。
**都是视觉/音效层，不影响方块与实体逻辑。**


---

## R243（254 → 240，**−14**）：子代理 B 第二轮结论套用成功

### ★★★ 重大认知纠正：**shim 问题可以在源码层解决**
台账此前写「`class_xxxx` 只能靠重生成 shim」。**这条是错的。**
实测：`build.gradle:71` 有 `srcDir 'src/stub/java'`，而 `src/stub` 下**已经有 9 个"影子类"覆盖 jar 里的同名类**
（`RegistrateBlockLootTables` / `RegistrateBlockstateProvider` / `AbstractBuilder` / `ModelGen` / `ConfiguredModel` / …），
**这些影子版本确实生效**（编译器优先用源码集里的类，而不是 jar 里的）。
⇒ **`AeroParticleTypes`(7) + `SimParticleTypes`(4) 那 11 条也能在源码层解决** ——
在 `src/stub` 放一个 `com/zurrtum/create/foundation/particle/ICustomParticleData.java` 影子类即可。
⚠ 但它在**运行期真被调用**（`AeroParticleTypes` 静态初始化里 `createType()`）⇒ 影子的 `createType()` 必须真造出 `ParticleType`。

### 本轮 6 个文件、11 处（−14）
| 文件 | 改动 |
|---|---|
| `SteamVentBlockEntity` | `fromSide` 返回 **void**（删 `return this;`）+ `getNearest` 补第 4 参 |
| `GimbalSensorBlockEntity` | `fromSide` 返回 **void** |
| `LerpedLineOutline` | `render` 加 **`Minecraft` 首参**（体不用改）|
| `FabricSimpleResourceManagerRegistry` | `reload` **6 参 → 4 参**（`SharedState, Executor, PreparationBarrier, Executor`）|
| `PlungerLauncherItem` | `getArmPose` 第二参 `AbstractClientPlayer` → **`LivingEntity`**；删 `getEnchantmentValue()` |
| `SteeringWheelBlock` | `updateShape` **8 参** + `updateWater` **4 参** |

### ★ 确认的新签名（补进知识库）
- **`Direction.getNearest` 只有 `(int,int,int,Direction)` 和 `(Vec3i,Direction)`**，**没有 3 参版**
- **`Item.getEnchantmentValue()` 已删**（附魔性改用 `Item.Properties.enchantable(int)`）
- **`BlockBehaviour.updateShape` 8 参**：`(BlockState, LevelReader, ScheduledTickAccess, BlockPos, Direction, BlockPos, BlockState, RandomSource)`；
  `updateWater` 4 参：`(LevelReader, ScheduledTickAccess, BlockState, BlockPos)`。
  **项目里另外 5 个文件早就是这个写法**（`AugerShaft`/`Nameplate`/`MergingGlue`/`PairedDockingConnector`/`Spring`）
  ⇒ **遇到签名变更，先在同一项目里找已经写对的文件，照抄它** —— 这比 javap 快且不会错。
- `PreparableReloadListener.reload` 4 参：`(SharedState, Executor, PreparationBarrier, Executor)`

### ★ 待做的两批（子代理已给可抄代码）
**① `SavedData` → `SavedDataType`（4 文件，−8）**
```
SavedDataType<T>(String id, Supplier<T>, Codec<T>, DataFixTypes)
level.getDataStorage().computeIfAbsent(TYPE)      // 1 参
MapCodec.unitCodec(Supplier<T>) → Codec<T>        // DFU 9.0.19 实测存在
```
`DataFixTypes` **没有 NONE**，必须给 `SAVED_DATA_*`；id 传**裸名**（`.dat` 由 `getDataFile` 拼）。
⚠ **削减**：`unitCodec` 是编译解 —— 每次存档写空 `{data:{}}`、读档忽略内容 ⇒ **这 4 个类的落盘会丢**
（LevititeCrystallizerManager 数据、未加载气球、lodestone 点、physics staff 锁）。**要单独一轮做并如实记录。**

**② `SimBlocks` / `AeroBlocks`（−12，5 类源码可修）**
| 报错 | 改法 |
|---|---|
| `ItemEntry<BlockItem> → BlockEntry<X>` | **`.register()` 前插 `.build()`** ⇒ `.item().transform(customItemModel()).build().register();`（垫片 `ItemBuilder.register()` 返回 `ItemEntry`，与 `BlockEntry` 是兄弟类；同文件 343-350 已是此写法）|
| `BlockBuilder<X,Registrate> → <X,CreateRegistrate>` | 两处声明里 **`CreateRegistrate` → `Registrate`**（`Registrate.block()` 返回类型的 P 写死）|
| `.save(RegistrateRecipeProvider, Identifier)` | 第二参 **`.toString()`**（vanilla `RecipeBuilder.save(RecipeOutput, String)` 变更，与 shim 无关）|
| `EncasingRegistry.addVariantTo(ShaftBlock)` | **删掉该 `.transform(...)` 行**（1.21.11 只有 `addVariant(B,E)` 且返回 void）⚠ 删后「扳手拆封装」行为消失 |
| `p.createSingleItemTable/applyExplosionCondition` | 强转 `((RegistrateBlockLootTables) p)`；`applyExplosionCondition` 需加进 `src/stub` |
| `getVariantBuilder(...).forAllStates(...)` | stub 改返回新影子类 `VariantBlockStateBuilder`，含 `forAllStates(Function<BlockState, ConfiguredModel[]>)` |

### 子代理未替我做决定的 3 处
① `LodestoneTrackingMap` 工厂（只有 `(ServerLevel)` 构造器，需 `() -> new LodestoneTrackingMap(null)` 或补无参构造）；
② `getNearest` 第 4 参用 `this.direction`（仅 x==z==0 时与原行为不同）；
③ 删 `addVariantTo` 后封装变体不再注册。


---

## R246（235 → 222，**−13**）：并行化第一轮 —— 父代理自做的 12 条

### 并行分工（3 个子代理改代码 + 父代理串行编译）
三个子代理各领**互不重叠**的文件清单，约定：
1. **禁止运行 `gradlew`**（Gradle 有锁，会互相排队）；
2. 用**括号配平检查**代替编译验语法：
   `python -c "import sys;t=open(sys.argv[1]).read();print(t.count('{')-t.count('}'))"`
3. 一次改一个文件、配平必须为 0、改前备份 `文件名.bak-subagent`；
4. 不许碰清单外文件。

**⇒ 实测有效**：父代理自己那 12 处改动全部语法正确（解析期 0），
**说明「括号配平 = 0」足够抓住绝大多数"改坏了"的情况**（解析期错误几乎都是括号/引号失配）。

### 父代理做的（子代理清单之外）
| 文件 | 改动 |
|---|---|
| `PortableEngineBlockEntity` | `Minecraft.cameraEntity` 是 private ⇒ `getCameraEntity()`；**修 R240 改错的接收者**：`stack.getItem().has(USE_REMAINDER)` → `stack.has(USE_REMAINDER)`；`getCraftingRemainingItem` 已删 ⇒ `ItemStack.EMPTY`；`SoundEvents` 字段现在是 `Holder.Reference<SoundEvent>` ⇒ 加 `.value()` |
| `NameplateBlock` | `BlockEntry` 无 `is(Item)` ⇒ `nameplate.get().asItem() == stack.getItem()` |
| `LinkedTypewriterBlockEntity` + `LinkedTypewriterEntries` | 存储族改 codec：`tag.store("Keys", CompoundTag.CODEC.listOf(), …)` / `tag.read(...).orElse(List.of())`；**加两个桥接方法 `toCompoundList`/`fromCompoundList`，Entries 内部逻辑一行未动** |
| `KineticBlockEntityMixin` | `SmartBlockEntity.writeClient` 确认**只剩 1 参且是 `ValueOutput`**；`saveAdditional` 在该类是 **protected**（mixin 调不到）⇒ 调用置空 |

### ★ 新确认的签名
- **`SmartBlockEntity.writeClient(ValueOutput)`** —— 1 参，且参数是 `ValueOutput` **不是 `CompoundTag`**；
  `saveAdditional(ValueOutput)` 是 **protected** ⇒ **mixin 里调不到**，只能放弃该调用。
- `SoundEvents.GENERIC_EAT` 之类的字段现在是 **`Holder.Reference<SoundEvent>`** ⇒ 传给 `playSound` 要 `.value()`。

### 削减记录
- `PortableEngineBlockEntity` 的合成剩余物**直接清空**（不返还容器里剩下的物品）；
- `KineticBlockEntityMixin` 的**额外动力学数据不再落盘**（`saveAdditional` 调不到）。

### 剩余的 7 条（我这边）
| 文件 | 剩余原因 |
|---|---|
| `PortableEngineBlockEntity` 1 | `ServerScrollOptionBehaviour` 构造器签名 |
| `NameplateBlock` 3 | **`DyedBlockList` 没有 `values()`**（是项目自定义容器，要查它自己的 API）；`LevelReader → LevelAccessor` 不兼容 |
| `KineticBlockEntityMixin` 3 | `addToGoggleTooltip` 要强转 `IHaveGoggleInformation`（goggle 由 mixin 加接口，编译期拿不到）；`writeClient` 要 `ValueOutput` |

### 并行节奏的教训
子代理**启动后前几分钟都在读台账（250 KB 冷层）**，真正动手偏慢。
**⇒ 下次派子代理要给「最小 API 便签」**（只列当批相关的 10～20 条事实），别让它读全量文档。


---

## R247（222 → 195，**−27**）：并行合并成功；**破 200**

### 结果
```
222 → 216（子代理 A/C 的部分成果合并 + 父代理 12 条）
216 → 195（补一个 import，连锁 −21）
```
解析期一直是 **0** —— **子代理的括号配平自检确实防住了语法破坏**。

### ★★ 本轮最大的单点收益：一个漏掉的 import 值 21 条
R245b 我给 `LinkedTypewriterEntries` 加了两个桥接方法（`toCompoundList` / `fromCompoundList`），
用了 `CompoundTag`，但**那个文件没有 import 它** ⇒ 新方法本身报 4 条，
**而且连带把别处所有 `CompoundTag.CODEC.listOf()` 的解析一起搞坏了**（因为它们引用了同一个类型）。
补上 `import net.minecraft.nbt.CompoundTag;` 之后 **−21**。

**⇒ 教训：`找不到符号 类 X 位置: 类 Y` 这种错，如果 X 在别处也用得到，先怀疑 `Y` 这个文件缺 import。
一个 import 能同时解释好几处的失败。**

### ★ 并行化实测数据
| 阶段 | 谁做的 | 收益 |
|---|---|---|
| R246 | 父代理 12 处 | −13 |
| R247 | 子代理 A（8 个 GUI 文件）+ C（2 个实体文件）部分合并 | −6 |
| R247 | 父代理补 1 个 import | −21 |
| **合计** | | **−40（两轮）** |

**⇒ 并行确实提速了**，但收益最大的那一条仍然是"一个 import"这种**父代理才看得出的全局问题**。
子代理擅长"按清单逐条改"，不擅长"发现跨文件的连锁根因"——**这个分工是对的，继续这样。**

### 子代理进度（本轮观测）
- A（GUI/打字机）：已改 8 个文件（`KeyEditorScreen`/`KeyWidget`/`EntryModifierScreen`/`ConfirmationWidgetBase`/
  `LinkedTypewriterItemBindHandler`/`LinkedTypewriterScreen`/`DiagramScreen`/`DiagramStickyNote`）
- C（实体/存档）：已改 `GustEntity`、`LaunchedPlungerEntity`
- B（注册/粒子）：**尚未落盘**（粒子要建影子类，最难）

### 下一步
1. 等 B 交回（`AeroParticleTypes` 7 + `SimParticleTypes` 4 + `SimulatedCreativeTab` 4 + `SimBlocks`/`AeroBlocks` 各 4）；
2. `DiagramScreen` 仍有 10 条 —— 主要是 `Matrix3x2fStack`/`BufferUploader` 这类**必须重写渲染逻辑**的，
   子代理按要求跳过了（**这是对的**）；
3. `PhysicsStaffServerHandler` 7 条含 `SavedData` 改造，等 C 的结果。


---

## R248（195 → 146，**−49**）：并行化最大单轮收益

### 数字
```
195 → 161 → 154 → 146
直方图：找不到符号 117 → 38 ；方法不会覆盖 49 → 10 ；Matrix3x2fStack 18 → 7
解析期全程 0
```
**⇒ 2,159 → 146，约 93%。**

### 子代理 A（GUI/打字机，8 文件）交回的 24 条
| 文件 | 关键改法 |
|---|---|
| `ConfirmationWidgetBase` | 删 `clicked(double,double)`（已删），「未悬停取消确认」并入 `onClick(MouseButtonEvent,boolean)` 首部 |
| `KeyWidget` | `InputConstants.getKey(int,int)` → **`InputConstants.Type.KEYSYM.getOrCreate(int)`**；`blitSprite(id,x,y,0,w,h)` → **`blitSprite(RenderPipelines.GUI_TEXTURED, id,x,y,w,h)`**（**所有 blitSprite 首参都是 RenderPipeline，blitOffset 已删**）|
| `EntryModifierScreen` / `KeyEditorScreen` | `pose()` 现在是 `Matrix3x2fStack`；`pushPose/popPose` → **`pushMatrix/popMatrix`**；`translate` 去掉 z 参；`fillGradient` 7→6 参 |
| `LinkedTypewriterScreen` | `renderTooltip(Font,ItemStack,int,int)` → **`setTooltipForNextFrame(Font,ItemStack,int,int)`** |
| `DiagramStickyNote` | `TransformStack.of(PoseStack)` 4 步链 → 用 `Matrix3x2f.translate/rotate` 原生（rotate 取弧度） |
| `DiagramScreen` | `fill` 6→5 参；4 处 pose 改 2D 栈；**力箭头整段重写**：`RenderType.gui()` + `pose().last()` + VertexConsumer → 用 **`graphics.fill(...)` 逐像素方块**（原实现每个顶点方块就是这个矩形，视觉等价）|
| `LinkedTypewriterItemBindHandler` | 删 `import LayeredDraw` + 该字段（**该类在 jar 里整个不存在**，全项目零引用）|

### ★ 关键 API 事实（子代理 javap 实证）
- **`GuiGraphics.pose()` = `Matrix3x2fStack`（纯 2D）**：`pushPose/popPose` → `pushMatrix/popMatrix`；
  **所有 `translate`/`fill`/`fillGradient` 的 z 参数都已删除**
- **`blitSprite` 所有重载首参都是 `RenderPipeline`**（与 `blit` 一样），`blitOffset` 概念已删
- **`InputConstants.getKey(int,int)` 已删** → `InputConstants.Type.KEYSYM.getOrCreate(int)`
- **`LayeredDraw` 整个类在 1.21.11 不存在**
- **`BlockEntityRenderDispatcher.renderItem(...)` 已删**，只剩 render-state 的
  `prepare / tryExtractRenderState / submit(state, PoseStack, SubmitNodeCollector, CameraRenderState)`

### 子代理如实跳过的 5 条（**都必须整体重写，不能改声明**）
1. `DiagramScreen:755` `AdvancedFboTextureAttachment.getId()` —— Veil 类，改法不确定；
2. `DiagramScreen:763/772` `pose().last().pose()` + **`BufferUploader`（类已删）** ——
   唯一替代 `TextureSetup` 要 `GpuTextureView`，Veil `AdvancedFbo` 不提供 ⇒ `renderFBO` 要换渲染路径；
3. `LinkedTypewriterScreen:320/349` `renderItem` 已删 + 该方法做 **3D 旋转**而 GUI 只剩 2D 栈 ⇒ `renderTypeWriter` 整体重写。

### ★ 新增削减（如实记录）
1. **所有 GUI 的 z 分层丢弃**（translate z、fill/fillGradient 的 blitOffset）—— 1.21.11 GUI 本就平面化；
2. `DiagramScreen` 力箭头改为 `GuiGraphics.fill` 逐像素绘制，不再自拼顶点；
3. `LinkedTypewriterItemBindHandler.OVERLAY` 字段删除（原本零消费者，**绑定提示 HUD 需等新 HUD 体系再注册**）；
4. `Type.KEYSYM.getOrCreate` 丢掉 `keyCode==-1 → SCANCODE` 的回退分支（本项目调用点传的都是真实 GLFW keycode）。

### 仍在跑的
- B（注册/粒子）：`AeroParticleTypes` 7 + `SimParticleTypes` 4 + `SimulatedCreativeTab` 4 + `SimBlocks`/`AeroBlocks` 各 4 ≈ 19 条
- C（实体/存档）：`SwivelBearingBlockEntity` 4 + 3 个 `*SaveData` 各 3 + `PropellerBearingBlockEntity` 3 + `PhysicsStaffClientHandler` 3 ≈ 16 条


<!-- ===== 从热层搬来的较早族行（20261017-130749）===== -->

| 族 | 结论 |
|---|---|
| ⚠⚠⚠ **1.21.11 把 gamerule 系统整个重写了**：包改为 `world.level.gamerules`，新增 `GameRule`/`GameRuleType`/`GameRuleMap`；常量改名（`RULE_DOBLOCKDROPS`→`BLOCK_DROPS`、`RULE_DOENTITYDROPS`→`ENTITY_DROPS`、`RULE_DAYLIGHT`→`ADVANCE_TIME`、`RULE_WEATHER_CYCLE`→`ADVANCE_WEATHER`）；**`Level.getGameRules()` 也没了**。**全项目 `GameRules.RULE_*` 与 `getGameRules()` 都要重写** | —— | R236 |
| ★★★★ **Create Fly 有自己的配置系统，没有 NeoForge `ModConfigSpec`**：`CStress.registerAll(...)` 参数是 `com.zurrtum.create.catnip.config.Builder`；且 `Builder.define(String,double)` 返回 `DoubleRawValue`，与 `CStress.impacts` 的 `Map<Identifier,DoubleRawValue>` 天然匹配 | —— | R236 |
| ★★★★ **分工：把「查 API」交给子代理并行**。瓶颈是 javap（我一轮只能查 3～4 个），而查证**只读零风险、完美可并行**；改代码/编译仍由我做（Gradle 锁 ⇒ 编译串行）| —— | R237 |
| ★★★★★ **1.21.11 关键 final/abstract 事实**：`Entity.makeBoundingBox()` 与 `Entity.hurt(...)` 都是 **final**（子类不能覆盖 ⇒ 删除或改名）；`Entity.addAdditionalSaveData(ValueOutput)` 是 **abstract**（子类必须实现）；`Entity` 已无 `walkDist*/ownerUUID` | —— | R237 |
| ★★★★ **`EntityDataSerializers` 已无任何 UUID 序列化器** ⇒ 用 `net.minecraft.world.entity.EntityReference<T>`（`codec()/streamCodec()/of(UUID)/getUUID()`）。`Projectile.setOwner` 有 2 个重载 ⇒ `setOwner(null)` 要加 `(Entity)` 转换 | —— | R237 |
| ★★★ **`ServerScrollValueBehaviour` 只剩 `(SmartBlockEntity)` 构造器**（标签/ValueBox 参数全删）⇒ `super(be)`；**`DimensionType.natural()` 已删** ⇒ 用 `hasCeiling()`（语义等价，已编译验证）；**`ValueInput.getInt()` 返回 `Optional<Integer>`** ⇒ `.orElse(0)` 或 `getIntOr(K,d)` | —— | R237 |
| ★★★★★ **`Entity.hurt(...)` 是 final，但真正的可覆盖钩子是 `hurtServer(ServerLevel, DamageSource, float)`**。**把方法改名绕开「final 不能覆盖」之前，先看有没有「未覆盖某个抽象方法」的报错——新钩子名字就在里面**。`HoneyGlueEntity` 因此保住了完整的伤害行为 | —— | R238 |
| ★★★★ **`ValueOutput`/`ValueInput` 的 codec 惯用法**：写 `compound.store("K", Vec3.CODEC, v)` 或 `putDouble(...)`；读 `compound.read("K", Vec3.CODEC).orElse(默认)` 或 `getDoubleOr(K,d)`。**`Vec3.CODEC` 存在**；**`ListTag` 没有 CODEC**（别试）；`childOrEmpty(String)` 返回 **`ValueInput`** 不是 `CompoundTag` | —— | R238 |
| ★★★★★ **`FileToIdConverter` 在 1.21.11 是 `net.minecraft.resources.FileToIdConverter`**（不在 `server.packs.resources`）。**`super(...)` 里类名解析失败会让父类型退化成 raw，于是在子类身上报一堆「不覆盖」** —— 根因与症状离很远。换两行 −6 | **−6** | R239 |
| ★★★★ **粒子 Data 类的 `@Override` 是纯残留**：`ParticleOptions` 只有 `getType()`；`codec()/streamCodec()` 是 `ParticleType` 的；`getMetaFactory()/getCodec(type)` 属 Create 的 shim。**纯删 @Override，别恢复 implements**（要补 `getDeserializer()+writeToNetwork`）| **−12** | R239 |
| ★★★ **`SmartBlockEntity.writeSafe` 只剩 `writeSafe(ValueOutput)`**（`ValueOutput` 没有 `lookup()`）；**`ItemAttributeType.streamCodec()` 改名 `packetCodec()`** | **−4** | R239 |
| ⚠⚠ **子代理交回的待做清单在冷层**（`SavedData.Factory` 不存在→`SavedDataType`、`Sided.fromSide` 返回 void、`updateShape` 8 参、`LineOutline.render` 加 `Minecraft`、`reload` 4 参、`renderLast` 10 参且 9 参版 final…）⇒ **按 `docs\SOLVED-FAMILIES.md` 搜 `R239` 查全表** | —— | R239 |
| ★★★★ **子代理 A 交回 100 条「找不到符号」的考古表**（已套用 9 条 −11；剩余在冷层 R240）。**正则两个坑**：`[^)]*` 抓嵌套调用的参数会在内层括号截断 ⇒ 解析期「非法的表达式开始」；**方法挪位置时接收者也要换**（`bufferSource()` 不是简单加后缀，要整体换成 `Minecraft.getInstance().renderBuffers().bufferSource()`）| **−11** | R240 |
| ★★★ **下一批三组**：① `onRemove` → `affectNeighborsAfterRemoval(BlockState, ServerLevel, BlockPos, boolean)`（5 块，**无 newState、首参是 ServerLevel**）；② 自家 stub 补空方法（6 块，零风险）；③ 纯删 builder 调用（`EntityBuilder` 在垫片里只有构造器+register，`renderer/visual/properties` 全无 ⇒ 删；`RegistryEntry.register()` 不存在 ⇒ 删；共 9 块）| —— | R240 |
| ★★ **`CompoundTag` 现在也有 `store(K,Codec,T)`/`read(K,Codec)`**；**`getList(String)` 返回 `Optional<ListTag>`**、另有 `getListOrEmpty(String)`、**没有 `(String,int)` 重载**。`ListTag` 无 CODEC ⇒ 用 `CompoundTag.CODEC.listOf()` | —— | R240 |
| ★★★★★ **内联 Python 一律用 PowerShell 单引号 here-string `@'...'@`** —— 不做插值、不处理反斜杠，Python 里可自由用引号。**此前用 `@"..."@` 反复触发 `unexpected character after line continuation character`，浪费 11 次调用** | —— | R242 |
| ★★★ **给桩补空方法是最便宜的收益**（`(Object... args)` 接任意参数，已知返回类型的才写真实类型）：`HeatedCulledRenderRegion.free()` / `getFirstPersonFocusPos(float)→Vec3` / `renderChain(Object...)` / `PacketContext.disconnect(Component)` / `RenderHandler.basicShoot·playSound·dontAnimateItem` ⇒ **−7** | **−7** | R242 |
| ★★★★★ **【纠正 R238 的错误结论】shim 问题可以在源码层解决**：`build.gradle:71` 有 `srcDir 'src/stub/java'`，`src/stub` 下**已有 9 个「影子类」覆盖 jar 同名类且生效**（`ModelGen`/`AbstractBuilder`/`RegistrateBlockLootTables`…）⇒ 粒子那 11 条也能靠影子类解决（但要保证 `createType()` 运行期真能造出 `ParticleType`）| —— | R243 |
| ★★★★ **签名变更时，先在项目里找「已经写对的文件」照抄** —— 比 javap 快且不会错。本轮 6 处签名全是照抄同项目的正确写法：`fromSide`→void、`render` 加 `Minecraft`、`reload` 4 参、`updateShape` 8 参/`updateWater` 4 参（另 5 个文件早已正确）、`getArmPose`→`LivingEntity`、删 `getEnchantmentValue()` | **−14** | R243 |
| ★★★ **`Direction.getNearest` 只有 `(int,int,int,Direction)` 与 `(Vec3i,Direction)`，无 3 参版**；**`Item.getEnchantmentValue()` 已删**（改 `Item.Properties.enchantable(int)`）| —— | R243 |


<!-- ===== 从热层搬来的较早族行（20261017-132527）===== -->

| 族 | 结论 |
|---|---|
| ⚠⚠ **待做：`SavedData`→`SavedDataType`（4 文件 −8，`MapCodec.unitCodec` 可编译解但落盘会丢）+ `SimBlocks`/`AeroBlocks`（−12，`.register()` 前插 `.build()` / `CreateRegistrate`→`Registrate` / `save` 第二参 `.toString()` / 删 `addVariantTo`）⇒ 冷层搜 `R243` | —— | R243 |
| ★★★★★ **并行改代码的分工规则（实测有效）**：3 个子代理各领**互不重叠**的文件清单；**禁止它们跑 `gradlew`**（锁冲突），改用**括号配平检查**（`{`−`}` 必须为 0）代替编译验语法；一次一文件、改前备份 `.bak-subagent`。父代理最后统一编译。R246 父代理自做 12 处 **全部语法正确、解析期 0** | **−13** | R246 |
| ★★★ **`SmartBlockEntity.writeClient(ValueOutput)` 只剩 1 参且要 `ValueOutput`（不是 `CompoundTag`）**；`saveAdditional(ValueOutput)` 是 **protected** ⇒ **mixin 里调不到**，只能放弃。`SoundEvents.*` 字段现在是 `Holder.Reference<SoundEvent>` ⇒ 传 `playSound` 要 `.value()` | —— | R246 |
| ⚠ **派子代理要先给「最小 API 便签」**（当批相关的 10～20 条事实），别让它读 250 KB 冷层 —— R246 实测它们前几分钟全花在读文档上 | —— | R246 |
| ★★★★★ **一个漏掉的 import 值 21 条**：`找不到符号 类 X 位置: 类 Y` —— 若 X 在别处也用得到，**先怀疑 Y 这个文件缺 import**。R247 补 `import net.minecraft.nbt.CompoundTag;` ⇒ **−21**（连带修好了所有 `CompoundTag.CODEC.listOf()` 的解析）| **−21** | R247 |
| ★★★ **并行实测（两轮 −40）**：子代理擅长「按清单逐条改」（A 改了 8 个 GUI 文件），**父代理擅长「发现跨文件连锁根因」**（import / 依赖映射 / 影子类）。这个分工已验证，继续这样 | —— | R247 |
| ★★★★★ **GUI 在 1.21.11 全面 2D 化（子代理 A 实证）**：`GuiGraphics.pose()` = **`Matrix3x2fStack`**；`pushPose/popPose` → **`pushMatrix/popMatrix`**；**所有 `translate`/`fill`/`fillGradient` 的 z 参已删**；**`blitSprite` 所有重载首参都是 `RenderPipeline`**；`InputConstants.getKey(int,int)` → `Type.KEYSYM.getOrCreate(int)`；**`LayeredDraw` 类已删**；**`BlockEntityRenderDispatcher.renderItem` 已删**（只剩 render-state 的 `submit(...)`）| **−24** | R248 |
| ★★★ **不可改声明、必须整体重写的 3 处（已知死路）**：`DiagramScreen` 的 `renderFBO`（`BufferUploader` 类已删，Veil `AdvancedFbo` 不提供 `GpuTextureView`）、`LinkedTypewriterScreen.renderTypeWriter`（`renderItem` 已删且需 3D 旋转而 GUI 只剩 2D 栈）、`AdvancedFboTextureAttachment.getId()` | —— | R248 |
| ★★★★ **`BlockItem.setBlockEntityData` 第三参现在是 `TagValueOutput`（不是 `CompoundTag`）**，且 **`BlockEntity.saveToItem(...)` 已删** ⇒ 正确写法：`TagValueOutput tv = TagValueOutput.createWithContext(ProblemReporter.DISCARDING, registryAccess); be.saveWithoutMetadata(tv); BlockItem.setBlockEntityData(stack, be.getType(), tv);`。另 **`CompoundTag.contains(String,int)` 已删**（`getList(String)` 返回 `Optional<ListTag>`）| —— | R249 |
| ★★★★★ **三子代理并行收官（R246–R249 合计 −49→ 195→133）**：A 修 8 个 GUI 文件、B 修注册+粒子（**粒子不需要影子类**——R239 删 implements 后全项目已无引用，直接自建 `ParticleType<D>(false)` 匿名子类 + `MapCodec.unit(Supplier)`/`StreamCodec.unit`）、C 修 11 个实体/存档文件（**用真 `CompoundTag.CODEC.xmap` 而非 `unitCodec`，落盘不丢**）| **−49** | R249 |
| ★★★★ **垫片 `BlockBuilder.item()` 返回 `ItemBuilder<BlockItem, BlockBuilder<T,P>>`** ⇒ 链尾要 `BlockEntry` 必须在 `.register()` 前 **`.build()`**；直接 `.register()` 落在 ItemBuilder 上返回 `ItemEntry`。**★ javac 会压住同一表达式里的后续错误**：lambda 出错时光报 lambda，`register()` 的类型错被吞 ⇒ **修完 lambda 必须顺手查该 `.item()` 链尾有没有 `.build()`**（R249 就这样多捞了 2 条）| —— | R249 |
| ★★★ **`DimensionDataStorage` 把 codec 作用在存档根的 `"data"` 子标签上**，而 `CompoundTag.CODEC` 是 **PASSTHROUGH 系** ⇒ `CompoundTag.CODEC.xmap(读,写)` 能原样吃吐一个 CompoundTag，**旧存档键名/结构全保留**、不丢数据。（比 `MapCodec.unitCodec` 好得多）| —— | R249 |
| ★★★★ **`GuiGraphics`/`SmartBlockEntity.writeSafe` 都只剩 1 参**（`writeSafe(ValueOutput)`）。`NbtUtils.readBlockState(HolderLookup, CompoundTag)` 没有 `ValueInput` 重载 ⇒ **若写入用的是 `BlockState.CODEC`，读出就用同一个 codec**：`compound.read("Material", BlockState.CODEC).orElse(Blocks.AIR.defaultBlockState())` —— 读写对称最好，别混用两套 | **−3** | R252 |
| ★★★ **垫片 `AbstractRegistrate.addDataGenerator(ProviderType<T>, Consumer<T>)`**，但 **`ProviderType.LANG` 被垫片声明成 `ProviderType<Object>`** ⇒ 方法引用 `AeroLang::registrateLang` 不成立（形参是 `RegistrateLangProvider`）。**解法：用带类型转换的 lambda** `(Consumer<Object>) o -> AeroLang.registrateLang((RegistrateLangProvider) o)`。**raw cast `(Consumer) X::method` 无效**（方法引用无法在 raw 目标类型上推断）| —— | R252 |
| ★★★ **`ItemBuilder<T extends Item, P>` 的首个类型参数界是 `Item`，不是 `ItemLike`** —— 影子类 `ModelGen` 里写成 `<I extends ItemLike, P>` 会报「类型参数 I 不在类型变量 T 的范围内」| —— | R252 |
| ★★★★ **`BlockEntity.write/read` 现在是 `write(ValueOutput, boolean)` / `read(ValueInput, boolean)`**（2 参，`read` 是 **protected**，跨类调用要先放宽为 public）。但**传 `CompoundTag` 进去只会得到「CompoundTag 无法转换为 ValueOutput」**（单向桥）⇒ 要么改造成 `TagValueOutput`，要么先置空（R254 就置空了 3 处：`AugerShaftBlock` 的 NBT 复制、`RedstoneSignalInstruction` 的杠杆状态写盘）| **−6** | R254 |
| ★★★★★ **Create 的 `MenuType<H>` 是和 vanilla `net.minecraft.world.inventory.MenuType` 完全无关的另一个接口**，`MenuBase` 只有 `MenuBase(com.zurrtum.create.foundation.gui.menu.MenuType<T>, int, Inventory, T)` 一个构造器（**没有 buffer 版**，`createOnClient` 也已删）。写成 vanilla `MenuType` 会报「MenuType<CAP#1> 无法转换」| —— | R257 |
| ★★★★★ **`TagValueOutput` 三行写法已实测可用**（`LinkedTypewriterBlock` 两处 −2）：`TagValueOutput tv = TagValueOutput.createWithContext(ProblemReporter.DISCARDING, registryAccess); be.saveWithoutMetadata(tv); BlockItem.setBlockEntityData(stack, be.getType(), tv);` | **−2** | R257 |
| ★★★ **`Item.appendHoverText` 新签名**：`(ItemStack, Item.TooltipContext, TooltipDisplay, Consumer<Component>, TooltipFlag)` —— **多了 `TooltipDisplay`，且 `List<Component>` 变成 `Consumer<Component>`**（`add` → `accept`）| **−2** | R257 |
| ★★★★★ **`SimpleJsonResourceReloadListener<T>` 必须给类型参数** —— 写成原始类型 `extends SimpleJsonResourceReloadListener` 会让 `SimplePreparableReloadListener<Map<Identifier,T>>` 里的 T 退化成 `Object`，于是 `apply(Map<Identifier,X>,...)` 报「未覆盖」+「@Override 不覆盖」。补 `<SimulatedSection>` / `<EndSeaPhysics>` 即好（`apply` 是 **3 参**：`(T, ResourceManager, ProfilerFiller)`）| **−4** | R260 |
| ★★★★ **`Ingredient.of` 在 1.21.11 没有 `TagKey` 重载**，只有 `ItemLike` / `ItemLike...` / `Stream<? extends ItemLike>` / `HolderSet<Item>`。**枚举常量里不能用 `HolderSet`**（类初始化时标签还没加载，会抛）⇒ 改具体物品 `Ingredient.of(Items.IRON_NUGGET)`，**tag 语义丢失** | **−2** | R261 |
| ★★★ **改 2D 栈必须同时做三件事**（R259 实证，只做前两件会 **2→5 恶化**）：① `PoseStack` → `Matrix3x2fStack`；② `push/popPose` → `push/popMatrix`；③ **`translate`/`scale` 去掉第 3 个（z）参数** | —— | R259 |
| ★★★★ **要把 `ValueInput` 喂给需要 `Tag` 的 Codec（如 `X.CODEC.decode(NbtOps, tag)`）时，别用 `childOrEmpty(key)`**（它给的是 `ValueInput`），改用 **`read(key, CompoundTag.CODEC).orElse(new CompoundTag())`** 拿到真正的 `CompoundTag`，下游一行都不用动 | **−1** | R263 |
| ⚠ **`IHaveGoggleInformation` 在 `com.zurrtum.create.client.api.goggles`（client 包）** ⇒ **服务端 mixin 里引用它会让专用服崩**，`KineticBlockEntityMixin` 的 `addToGoggleTooltip` 那条**保持不修**（除非把那段 code 拆进 client-only mixin）| —— | R263 |
| ★★★ **`player.connection.send(CustomPacketPayload)` 不再成立**（1.21.11 的 `ServerGamePacketListenerImpl.send` 要 `Packet<?>`）⇒ Fabric 下应改 `ServerPlayNetworking.send(player, payload)`。`RopeStrandHolderBehavior:147` 那条**待办**（要确认 payload 类型）| —— | R263 |
| ★★★ **`ItemStack.save(RegistryAccess, CompoundTag)` 已删** ⇒ `tag.store(key, ItemStack.CODEC, stack)`；**`BlockEntity.loadWithComponents` 要 `ValueInput`** ⇒ `loadWithComponents(TagValueInput.create(DISCARDING, registryAccess, tag))` | **−2** | R264 |


<!-- ===== 从热层搬来的较早族行（20261017-143619）===== -->

| 族 | 结论 |
|---|---|
| ★★★ **在 `(() -> ...)` 这种外层 lambda 里做正则替换时，数括号会多写一个 `)`** —— R264 就把 `Simulated` 写成了 `(() -> {...})())` 导致解析期崩。**改 lambda 一律整体替换整个表达式（从 `=` 到行尾 `;`），不要只换中间那段** | —— | R264 |
| ★★★ **`ServerChainConveyorHandler.handleStopRidingPacket / handleTTLPacket` 现在都要 `(MinecraftServer, Player)` 两参** ⇒ `handleX(player)` 改成 `handleX(player.level().getServer(), player)` | **−2** | R266 |
| ★★★★ **`() -> null` 只在目标类型是单参函数式接口时成立**。R229 我把 `AirshipReadyPreset::new` 换成 `() -> null`，但 `create(...)` 收的是 **`BiFunction<Identifier, Component, T>`（两参）** ⇒ 必须写 `(id, desc) -> null`。**⇒ 替换方法引用前先看目标函数式接口有几个参数** | **−2** | R265 |
| ★★★ **删掉父类某个构造器后，子类的同名构造器会连带报错** —— `LinkedTypewriterMenuCommon` 删了 buffer 构造器后，`LinkedTypewriterMenuImpl` 里 `super(type,id,inv,extraData)` 也跟着坏 ⇒ **删构造器要顺着继承链一起清** | **−2** | R266 |
| ★★★★★ **「必须重写渲染路径」的两处已按「整体置空 + 如实记录」处理（不造假修法）**：`DiagramScreen.renderFBO`（整段移除）、`LinkedTypewriterScreen.renderTypeWriter`（整段移除）。两者都是**自洽的私有/静态方法**，替换整个方法体最安全（不是删声明、不是改签名）。**−5** | **−5** | R267 |
| ⚠⚠ **判据：一个方法只做「画东西」且依赖已删的类（`BufferUploader` / `renderItem` / `getColorTextureAttachment().getId()`）⇒ 置空并记录削减，比硬改更快也更诚实。**要记录到交付说明：「图表屏幕的 FBO 预览不绘制」「键位编辑器的打字机 3D 预览不绘制」** | —— | R267 |
| ★★★★★ **`SingleLineDisplaySource.allowsLabeling` 是 `public`**，子类写成 `protected` 就报「无法覆盖」⇒ **覆盖方法时访问权限不能变窄**。改 `AbstractNumericDisplaysource` 的 `protected` → `public` 一次清 **4 条** | **−4** | R268 |
| ★★★★ **同一个类同时存在于 `src/main` 和 `src/stub` ⇒ 报「类重复」**（两个源码目录都在编译）。**删掉 `src/stub` 里那份**（main 是真实现）⇒ `ParrotElementAccessor` / `KeyMappingInvoker` 各清 1 条 | **−2** | R268 |
| ⚠⚠ **`BufferUploader` 渐变带不一定能单独换 `fillGradient`** —— `ModulatingLinkedReceiverScreen` 里那段的 `PoseStack ms` **后面还被 `TransformStack.of(ms)` 用着**⇒ 只换中间那段会让 `ms` 消失、反而多出 4 条错。**⇒ 改之前先搜这个局部变量在方法后面还有没有别的使用** | 净 0 | R269 |
| ★★★★★ **`Entity.hurtServer(ServerLevel, DamageSource, float)` 是 `public abstract`** ⇒ 任何 `extends Entity` 的子类**必须实现**它（`hurt` 变 final 只是不能覆盖，调用不受影响）| **−1** | R271 |
| ★★★★★ **`BlockBehaviour.entityInside` 现在 6 参**：`(BlockState, Level, BlockPos, Entity, InsideBlockEffectApplier, boolean)`—— 多了 `InsideBlockEffectApplier` 和 `boolean isPrecise`；子类声明和 `super.entityInside(...)` 都要同步 | **−1** | R272 |
| ★★★ **`EnvelopeEncasedShaftBlock` 之类的双参 `super(properties, X)` 里 X 现在是 `Block` 不是 `Supplier<Block>`** ⇒ 去掉 `() -> …` 包装 | **−1** | R271 |
| ★★★ **`makeBoundingBox`/`properties` 之后的新一轮散点**：`EntityBuilder.properties` 垫片里没有 ⇒ 整段 `.transform((b) -> b.properties(...))` 删掉（R240 老配方，本轮 AeroEntityTypes 用掉 −2）；`X.get(key)` 返回 `Optional<Reference<T>>` ⇒ `.map(Holder::value).orElse(null)` | **−2** | R270 |
| ★★★★ **`ScrollValueBehaviour.StepContext` 只在 client 包**：`com.zurrtum.create.client.foundation.blockEntity.behaviour.scrollValue.ScrollValueBehaviour$StepContext`（`ServerScrollValueBehaviour` 里已无嵌套 StepContext）| **−1** | R281 |
| ★★★★ **`ServerBrassDiodeScrollValueBehaviour` 只剩 `(SmartBlockEntity)` 一个构造器**（Component 标题与 ValueBoxTransform 全删，与 `ServerScrollOptionBehaviour` 同命运）| **−1** | R281 |
| ★★★★★ **【最有效的一招】遇到「签名变了但模式固定」的错，先做全项目 `Select-String` 搜索，别逐文件修。** R282 实例：日志只报 **2** 个 `protected boolean allowsLabeling`，全搜却找到 **6** 个 —— 另外 4 个被别的错误掩盖。改一次 = **−6**。同类已验证：`IBE.affectNeighborsAfterRemoval`（5 处）、`InputConstants.getKey(int,int)`（4 处）、`EntityType.create(Level)`（3 处）| **−6** | R282 |
| ★★★ **`Vec3.getCenter()` 不存在**（`BlockPos.getCenter()` 才存在）—— `pos().getCenter().getCenter()` 这种链式写法第二个会挂 | **−1** | R283 |
| ★★★ **`ItemEntry.isIn(ItemStack)` 已删** ⇒ 反过来写：`stack.is(ENTRY.get())` | **−1** | R283 |
| ⚠ **`Shulker.getProgressAabb` 已从 `ShulkerBoxBlock` 与 `ShulkerBoxBlockEntity` 双双移除**（javap 实测）⇒ 调用点必须自己算 AABB，不是改签名能解 | —— | R283 |
| ★★★★★ **【里程碑 R300】`gradlew build` 全绿，mod jar 已产出**：`build/libs/aeronautics-fabric-0.1.0-port.1.21.11.jar`（**30.2 MB**，1013 class / 1547 assets / 550 data / 2 mixin json）。**2,159 → 0 编译错误**。但**这不等于能跑** —— 见下方运行期风险 | **−2,159** | R300 |
| ★★★★★ **`build` 的两个非代码拦路虎**：① `.bak*` 备份文件被打进 `sourcesJar` 造成 entry 重名 ⇒ **把备份全部移出 `src/`**（本轮移了 **4,778** 个到 `work\aero-port\_backups\`）；② `validateAccessWidener` 会因**已失效的 AW 条目**整体失败 ⇒ 逐条删除（`RenderType$CompositeState`、`RenderStateShard$*`、`Projectile.ownerUUID`、`ParticleEngine$SpriteParticleRegistration`、`RecipeProvider.getName`、`GameRenderer.getFov` 等）| —— | R300 |
| ★★★★★ **【运行期验证 R311】客户端已跑到 mod 的 `onInitialize`**（Bootstrap/Datafixer/Veil/Sable 全过），56 个 mod 加载。**下一步工单只剩两条真正的代码问题**（其余是 dev 环境 jar-in-jar 缺库）| —— | R311 |
| ★★★★★ **mixin 配置的正确格式**：`"injectors"` 必须是**对象** `{"defaultRequire": 0}`，写成数组 `["defaultRequire"]` 会让 Mixin 0.8.7 直接解析失败。**为了先能启动，两个 mixins.json 都设为 `defaultRequire: 0`**（注入点找不到就降级，不炸）| —— | R311 |
| ★★★★★ **mixin json 的条目必须与「实际编译产物」一致**：`build.gradle` exclude 掉的类（`mixin/creative_tab_sections/**`、`mixin/render/**`、`mixin/end_sea/**`、`mixin/lodestone_compat/**`、`mixin/diagram/**`）**仍留在 json 里 ⇒ 启动时 ClassNotFound 硬崩**。写脚本按 `build/classes/java/main` 过滤，一次清掉 **10 条** | **−10** | R311 |
| ★★★★★ **mixin 处理器签名必须与目标方法完全一致，`require=0` 救不了**：`LevelChunk.setBlockState` 第 3 参 **boolean → int**；`BlockEntity.write/read` 现在是 `(ValueOutput/ValueInput, boolean)`。签名不匹配 ⇒ `InvalidInjectionException: Invalid descriptor` **硬崩** | **−2** | R311 |
| ⚠⚠⚠ **【本轮踩过的最大坑】`Get-ChildItem -Filter <Name>.java | Select -First 1` 在同名类存在时会静默改错文件** —— `extra_kinetics/KineticBlockEntityMixin` 与 `extra_kinetics/goggle_tooltips/KineticBlockEntityMixin`、`aeronautics/.../RedstoneSignalInstruction` 与 `simulated/.../RedstoneSignalInstruction` 都是同名不同包。我因此**把 `@Mixin(KineticBlockEntity.class)` 覆盖成了 `;`**，启动时炸。**⇒ 一律用完整路径（从编译日志里取）** | —— | R311 |
| ★★★★★ **【R314 进展】去掉 Veil 注册后，客户端又推进一大步**：`SimRegistries` 换成 `FabricRegistryBuilder.createSimple(key).buildAndRegister()` ✅；`AeroBlocks`/`SimBlocks` 共 **11 段** `.item()…build()` 已移除（垫片 `ItemBuilder.build()` 恒返回 null）| **−11** | R314 |


## 从热层搬出的索引行（budget-2026-10-17 15:06）

| 族 | 结论 | 轮次 |
|---|---|---|
| ⚠⚠⚠⚠ **【R316 重要否定结论】`src/stub` 的影子类「不能」覆盖独立 mod jar 里的同名类** —— 我为 `foundry.veil.platform.registry.RegistrationProvider/RegistryObject` 写了完整影子类，编译通过、class 也进了 `build/classes`，但**运行时栈里仍是 Veil jar 的实现**（`foundry.veil.fabric.platform.FabricRegistrationFactory$Provider.register`）。**⇒ 影子类只对「垫片 jar」（同一编译链）有效（`ModelGen` 那 9 个是这种），对 Veil 这种独立 mod 无效。别再用这招。** | —— | R316 |
| 🎉🎉🎉 **【里程碑 R322】移植版「能启动了」** —— `gradlew runClient` 客户端成功启动并**稳定运行 3 分钟以上**：`Sound engine started`、全套 texture atlas（含 `4096x2048 blocks.png-atlas`）创建成功、资源重载成功。**这是从「编译通过」到「真的能跑」的跨越** | —— | R322 |
| ★★★★★ **达成启动的关键四步（R317–R322）**：① 把 12 个文件的 Veil 注册依赖换成**自有包** `dev.simulated_team.simulated.api.registry.{RegistrationProvider,RegistryObject}`（API 与 Veil 一致，只改 import）；② `SimSoundEntry` 字段 `RegistryObject<SoundEvent>` → 裸 `SoundEvent`；③ `get(ResourceKey)` 先查 `BuiltInRegistries.REGISTRY` 再决定新建（否则 duplicate key）；④ 从 veil/forgeconfigapiport 的 jar 里**解出 JiJ 库**（`molang-compiler`、`core-3.8.3`、`toml-3.8.3`）加 `modLocalRuntime` | —— | R322 |
| ★★★★★ **`src/stub` 补 dev 缺失 JiJ 库的做法已验证**：`unzip META-INF/jars/*.jar` 到 `libs/`，再在 `build.gradle` 加 `modLocalRuntime files("../libs/xxx.jar")`。**Loom 的 dev classpath 不展开 jar-in-jar，这是唯一办法** | —— | R322 |
| ⚠ **`SimPonderTags.register` 已整体 try/catch 兜底** —— 因为我移除 `.item()` 链后多个 `BlockEntry.asItem()` 返回 null，`PonderTagBuilder.item(null)` 会 `new ItemStack(null)` 抛 NPE 直接崩启动。**ponder 标签是纯索引页分类，缺失不影响可玩性** | —— | R322 |
| ★★★★★ **R323：`world_presets.CreateWorldScreenMixin` 已修好** —— `CreateWorldScreen.createNewWorld` 现在是 `(LayeredRegistryAccess<RegistryLayer>, WorldData)Z`，处理器签名改为 `(同上两参, CallbackInfoReturnable<Boolean>)`（**原来只有 `CallbackInfo` ⇒ 硬崩**）| —— | R323 |
| ★★★★★ **R324：`setTooltips` 必须搬进 client-only 类，光加「是否 CLIENT」判断没用** —— JVM 在**类校验阶段**就会加载方法体引用的 client-only 类型，所以 `Simulated.setTooltips()` 即使不被调用，专用服仍报 `Cannot load class TooltipModifier in environment type SERVER`。已新建 `dev.simulated_team.simulated.client.SimulatedClientTooltips`，从客户端入口点调用 | —— | R324 |
| ⚠⚠⚠ **【已知边界】专用服仍不可用（客户端可用）** —— 下一个卡点是 `IHaveGoggleInformation`（client-only），**17 个方块实体都 implements 它**。要支持专用服就得把这 17 个类的接口去掉并删 `addToGoggleTooltip` 的 `@Override`，代价是**护目镜 tooltip 全消失**。**当前判定：本整合包是客户端包，专用服非必需，暂不做** | —— | R324 |
| ⚠ **Aeronautics 的 tooltip 修改器已随 `setTooltips` 一并移除但未补 client 类** ⇒ Aeronautics 的物品只有原版 tooltip（可后续补 `AeronauticsClientTooltips`）| —— | R324 |
| ★★★★★ **【R325 关键修复】致命 registry 错误的真正根因是「标签里有一条引用缺失 ⇒ 整个标签加载失败」** —— 我移除 11 段 `.item()…build()` 后，多个标签引用了不存在的物品 id；其中 `minecraft:head_armor` 缺 `aeronautics:aviators_goggles`，连坐 `enchantable/head_armor → armor → durability → vanishing` 全部失效 ⇒ **世界创建时 registry 加载直接崩**。**修法：删掉我们那 3 个追加式原版标签覆盖**（`data/minecraft/tags/item/head_armor.json`、`enchantable/durability.json`、`freeze_immune_wearables.json`）⇒ **致命错误消失** | —— | R325 |
| ★★★★★ **【新工单】世界生成卡住（不崩、不报错、CPU 0）** —— 修完标签后点「单人游戏 → 创建新世界」，界面停在 「正在准备生成世界…」，日志停在 datapack 解析阶段（advancement/recipe 非致命错误），**java 进程 1.8 GB 但 CPU 增量≈0** ⇒ **疑似死锁或等待**，不是慢。下一轮从这里查（可用 jstack 抓线程栈）| —— | R325 |
| ⚠ **剩余非致命但很吵的错误**：`Couldn't load tag` ×34、`Couldn't parse data file`（advancement/recipe 引用已删物品）—— 都不阻断，但应逐步清 | —— | R325 |
| ⚠⚠⚠ **【R326 否定结论】世界生成卡住 ≠ `world_presets` mixin 的锅** —— 把 `world_presets.CreateWorldScreenMixin` + `PrimaryLevelDataMixin` 从 mixin json 全移除后**完全相同的卡住表现**（日志停在 datapack 解析完、全部线程 WAITING、Render thread 在 `limitDisplayFPS`）。⇒ 元凶在 datapack 加载**之后**的阶段，且**没有线程在干活** ⇒ 疑似任务被静默吞掉 / future 完成但界面没切换 | —— | R326 |
| ★★★★ **R326 诊断手法（有效）**：`jstack.exe -l <pid>` 抓线程栈 → 看 `Render thread` 是否在 `glfwWaitEventsTimeout`（= 空闲）、`Worker-Main-*` 是否全 `WAITING`（= 没有任务在跑）。**「全空闲 + 界面不推进」= 卡死/静默失败，不是慢** —— 这比盯着日志猜快得多 | —— | R326 |
| ★★★ **R326 新发现的未注册项**：`minecraft:trigger_type` 里 `simulated:you_spin_me_right_round_builtin` 等自定义触发器**没注册**；另有大量 `Unknown registry key in minecraft:item: simulated:X`（就是被删物品的连带）。这些不阻断，但说明**物品缺失的连带面很广** | —— | R326 |


## 搬出的索引行（R343 10-17 16:24）

| 族 | 结论 | 轮次 |
|---|---|---|
| ✅ **【R336 首个 26.3 产物已构建成功】`work\companion26\sablecompanion-1.6.0-26.3.jar`**（28.1 KB，14 class + `META-INF/services` + 图标 + fabric.mod.json）。源码 `sable-companion` 仅 **12 文件 / 2,940 行 / MIT**，跨 5 个版本**只报 4 个错**，全是同一族：**`ChunkPos.x` / `.z` 在 26.3 变为 private** ⇒ 改成实例方法 `chunkPos.x()` / `chunkPos.z()`（`javap` 确认字段 private，有静态 `getX(long)` 与实例访问器）| —— | R336 |
| ★★★★★ **【R336 javac 直编的三个坑】** ① **argfile 里反斜杠是转义符** ⇒ 所有路径必须写**正斜杠** `C:/Users/...`，否则路径被吃成 `C:Users95959...`；② **`-J` 选项不能出现在 argfile 里**（`invalid flag: -J-Duser...`）⇒ 用环境变量 `JAVA_TOOL_OPTIONS="-Duser.language=en"` 拿英文报错；③ `org.jetbrains.annotations` **不在 `.minecraft/libraries`** ⇒ 从 `repo1.maven.org` 下 `annotations-26.0.2.jar` | —— | R336 |
| ★★★★★ **【R336 编译 companion 的完整 classpath（可复用）】** `26.3.jar` + `libraries\org\joml\joml\1.10.9\joml-1.10.9.jar` + `libraries\com\mojang\datafixerupper\10.0.21\...jar` + `annotations-26.0.2.jar`；**Java 25 = `runtime\java-runtime-epsilon\bin\javac.exe`**（`--release 25`）| —— | R336 |
| ★★★★ **【R336 `sable-companion` 必须是独立 mod，不能内联进 Aeronautics】** Sable 本体有 **284 处** `dev.ryanhcode.sable.companion.*` 引用，Aeronautics 侧是 79 处 / 60 文件 ⇒ 只能做成独立 jar 供两边共用 | —— | R336 |
| ✅ **【R337 阶段③ 构建系统已打通】`work\aero-port\aeronautics-26` 的 `gradlew help` = BUILD SUCCESSFUL**（Loom 1.19.1 + Gradle 9.8.1 + MC 26.3 + Java 25）。已改：`build.gradle` 头部换成 no-remap 插件 + `implementation`（去掉 mappings/parchment/modImplementation）；`gradle.properties` 全面换 26.3 值；依赖改指 `../libs26/`（Create-Fly 26.3 补丁、FCA 26.3.1）与 `../../companion26/sablecompanion-1.6.0-26.3.jar` | —— | R337 |
| ★★★★★ **【R337 两个必踩的构建坑】** ① **Loom 1.19.1 要求 Gradle ≥ 9.8.0** —— 本工程 wrapper 原为 9.5.0，报 `Plugin net.fabricmc:fabric-loom:1.19.1 requires at least Gradle 9.8.0`；已把 `distributionUrl` 改成 `gradle-9.8.1-bin.zip`。② **`settings.gradle` 的 `pluginManagement` 里有 `exclusiveContent` 过滤器只放行 `net.fabricmc.fabric-loom-remap`** ⇒ 用 no-remap 的 `net.fabricmc.fabric-loom` 会解析不到，必须补 `includeGroup('net.fabricmc.fabric-loom')` | —— | R337 |
| ★★★★★ **【R338 基线：Sable 26.3 首次编译 = 1,551 个错误】**（common+fabric 并入 no-remap Loom 工程，BUILD FAILED in 17s，日志 `work\sable-26\port26\compile-1.log` 1.27 MB）。对比：Aeronautics 26.3 首次编译 = 2,850 | —— | R338 |
| ★★★★★ **【R338 26.3 GUI 渲染管线大改（机械族图纸，javap 实测）】** `net.minecraft.client.gui.GuiGraphics` **整个不存在** ⇒ 换成 **`net.minecraft.client.gui.GuiGraphicsExtractor`**；`Screen.render(GuiGraphics,...)` → **`extractRenderState(GuiGraphicsExtractor, int mouseX, int mouseY, float partialTicks)`**；`Renderable` 接口同样只剩 `extractRenderState(...)`。**Extractor 的常用方法基本保留**：`fill/fillGradient/outline/horizontalLine/verticalLine/enableScissor/disableScissor/guiWidth/guiHeight/pose()`（返回 `Matrix3x2fStack`）、新增 `nextStratum()` 与 `com.mojang.renderpearl.api.pipeline.RenderPipeline`。Aeronautics 侧 `GuiGraphics` 缺失共 **186 处**，按此映射机械替换 | —— | R338 |
| ✅ **【R338 已修机械族】`RedStoneWireBlock` → `RedstoneWireBlock`**（26.3 只有小写 s 的版本，javap 确认）：5 文件 36 处，剩余 0 | **−72** | R338 |
| ★★★★ **【R338 启动器实测三坑（来自 launch26 验证）】** ① natives 目录不能直接指 `versions\26.3\26.3-natives`（LWJGL 会往里写），要整树复制到 game-dir；② `natives-windows-arm64` 包必须从 classpath 剔除（官方 rules 放不过，同名 dll 抽出即 0xc000007b）；③ 26.3 未混淆所以 `Mappings not present!` 是 INFO 不是错 | —— | R338 |
| ✅ **【R339 `Level.random` protected 族清零】** 26.3 `Level.random` = protected final、有 `public RandomSource getRandom()` ⇒ 46 站点/28 文件已改 45 处（剩 1 处在含 Veil import 的 `PhysicsStaffClientHandler.java:526`，等 Veil 线收尾后顺手改 `Minecraft.getInstance().level.random` → `.getRandom()`）| **−100** | R339 |
| ★★★★ **【R339 并行修复波启动】** 6 个子代理同时干：Sable ChunkPos 族 / Aeronautics Level.random（已完成）/ GuiGraphics→GuiGraphicsExtractor / Veil 拔除（重发）/ registrate 垫片 stub / getCenter 族。**冲突规则：谁碰到含 `foundry.veil` import 的文件就跳过留给 Veil 线；`src\stub\java` 只归垫片线** | —— | R339 |
| ★★★★ **【R339 基线数字】** Aeronautics 26.3 首编 = **2,850**；Sable 26.3 首编 = **1,551**（日志在 `work\sable-26\port26\compile-1.log`，英文报错）。Aeronautics 错误大头：缺 Sable 1,042（级联）+ GLFW 200（已补 lwjgl 依赖）+ registrate 垫片 ~450 + GuiGraphics 186 + Veil 206 | —— | R339 |
| ⚠ **【R340 计数陷阱】`Select-String` 默认**大小写不敏感** —— 用它数 `RedStoneWireBlock` 会把已改好的 `RedstoneWireBlock` 也算进去（我因此误判「改名被回滚」）。**⇒ 判断大小写敏感族必须用 python `re` 或 `Select-String -CaseSensitive`** | —— | R340 |
| ✅ **【R340 更正：7 个子代理「失败」的真正原因是模型额度耗尽被强制停机】** 不是并发压力、也不是任务本身无解。**⇒ 这些族可以放心重试**（本条已替换掉先前那条错误的「死路」结论）。已确认落地成果：`Level.random` 族 27 文件已改、Sable ChunkPos 族 20 文件已改 84 处 | —— | R340 |


## 搬出的索引行（trim 10-17 16:47）

| 族 | 结论 | 轮次 |
|---|---|---|
| ✅ **【R343 三族清零】** `ResourceLocation`→`Identifier`（Sable 23 文件 84 处）；`Tuple`→自建 `SimTuple`（8 文件 34 处，26.3 已删该类）；`AllBlockLayers.register` 全删（26.3 改由 `ChunkSectionLayer.byTransparency` 自动推导，25 处）| **−58** | R343 |
| ⚠ **【R343 26.3 渲染栈是硬骨头】** `MultiBufferSource` 整类删除（无替代，改 render-state 提取）、`ShaderInstance`→`ShaderManager`、`LightTexture`→`Lightmap`、`RenderType`→`rendertype` 子包。**Sable 侧约 264 处**，只能降级重写，无法机械替换 | —— | R343 |
| ✅ **【R341 Sable ChunkPos 族完成】** 74 个唯一字段站点（44 行/14 文件）+ 20 个构造器站点（11 文件）**全部改完**（`x`/`z` → `x()`/`z()`；`new ChunkPos(BlockPos)`→`ChunkPos.containing()`、`new ChunkPos(long)`→`ChunkPos.unpack()`）。验收脚本 `work\sable-26\port26\verify_chunkpos_final.py` = **PASS**。neoforge 子树残留 10 处但**不参与编译** | —— | R341 |
| ⚠ **【R341 教训：统计错误族必须判接收者类型】我用正则数 `.x`/`.z` 得出「53 处残留」是**假警报** —— 其中 40 处接收者是 `Vector3d/Vector3f/Vector2i/Vec3/BlockPos`（它们本来就暴露 `.x`），改 `x()` 反而编译错。**⇒ 判族要看「接收者声明类型」，不能只看名字/模式** | —— | R341 |
| ✅ **【R342 Veil 拔除完成】`import foundry.veil` 89 → 0**（76 文件）。新写垫片 **12 个**（`compat/veil/` 下 color/event/render/post/util），复用 1.21.11 轮已有的网络层 6 个。**降级 15 处**（源码内带 `// PORT(26.3):`）。详见 `docs\VEIL-ELIMINATION.md` | —— | R342 |
| ⚠⚠⚠ **【R342 关键否定结论：Veil 的渲染阶段事件在 26.3 垫不出来】** Veil 回调签名带 `MultiBufferSource.BufferSource`，而**该类在 26.3 整个不存在**；Fabric `WorldRenderEvents` 在 `fabric-rendering-v1-27.1.0` 也已删除（改 `LevelRenderEvents` + submit-node，不给 BufferSource）。⇒ 两个订阅点已删；**丢：物理法杖选择框、气球后处理、图表缩略图后处理** | —— | R342 |
| ✅ **【R342 registrate 垫片 26.3 完成】`src\stub\java` 单独 javac 49 → 0 错误**；53 → 80 文件（**补 27 个类**：nullness 6 / entry 6 / builders 6 / registrate 2 / providers 2 / create-foundation 5）。已用 main 的 `SimulatedRegistrate`/`AeroRegistrate`/`SimBlockEntityBuilder` 落地验证 0 错。详见 `docs\fix-stub.md` | **−49** | R342 |
| ★★★★★ **【R342 javac 直编 26.3 的两个隐藏依赖】** ① 必须把 **`jspecify-1.0.0.jar`** 放进 `-cp`，否则 javac **直接崩**（`CompletionFailure: class file for org.jspecify.annotations.Nullable not found`）；② 必须放 **`fastutil-8.5.18.jar`**（版本对齐 `26.3.json`，用 8.5.12 会伪装成源码注解错）。③ `compile-stub.ps1` 必须 **ASCII-only**（PS 5.1 读无 BOM 中文注释会吞掉下一行 classpath） | —— | R342 |
| ★★★★ **【R342 26.3 API 事实（stub 线实测，可直接用）】** `Criterion` → `net.minecraft.advancements.triggers.Criterion`；`RecipeOutput` 只剩 `accept`/`advancement`；`MultiBufferSource` **整类删除**；`BlockEntityType.Builder` **删除**（剩 `BlockEntitySupplier` + 构造器 `(Supplier, Set<Block>)`）；`EntityType$EntityFactory`/`MenuType`/`Identifier`/`BlockBehaviour.Properties.of()` 未变 | —— | R342 |
| ★★★★ **【R342 26.3 渲染栈大改（Sable 侧实测）】** `RenderType` → **`net.minecraft.client.renderer.rendertype.RenderType`**（新子包）；`BlockAndTintGetter` → `net.minecraft.client.renderer.block.*`；`BakedQuad` → `net.minecraft.client.resources.model.geometry.BakedQuad`；**`ShaderInstance` → `ShaderManager` 家族**；**`LightTexture` → `Lightmap`/`UiLightmap`**；`MultiBufferSource` 无替代（render state 提取模型） | —— | R342 |
| ★★★★★ **【R345 当前坐标】** Aeronautics 26.3：2,850 → **1,758**；Sable 26.3：1,551 → **569**。Aeronautics 里约 724 条仍是「Sable 类不存在」，**两条线都在 Sable 上收敛** | —— | R345 |
| ✅ **【R344 Veil·Sable 完成】`import foundry.veil` 80 → 0**（51 文件/28 FQN）。垫片 **37 类** `dev.ryanhcode.sable.compat.veil`（照抄 Aeronautics 11 + javap 新写 26；**网络层 6 文件 100% 照抄 = 唯一零降级子系统**）。降级 105 处/18 类，丢失集中在 fancy 渲染器 / 渲染阶段事件 / ImGui 面板。**同时拔掉了 `fabric.mod.json` 的 `veil` 硬依赖**（留着会拒启动）| —— | R344 |
| ✅ **【R344 Sable 渲染栈降级完成】** 修 **69 文件**（删 1,507 行/增 600 行）：换包 20 处、换等价 ~200 处（`mainCamera()`/`Camera.position()`/`getDeltaTracker()`/`getUnitVec3i()`/`ChunkPos.pack()`/`LightCoordsUtil`）、**降级 31 处**。**三大视觉损失：①子维度地形整体不绘制 ②子维度方块实体+破坏裂纹不绘制 ③单方块子维度不绘制**。所有目标方法消失的 mixin 注入都加了 `require = 0`（只告警不崩）| —— | R344 |
| ★★★★ **【R344 26.3 更多 API 事实】** `GlStateManager` → **`com.mojang.renderpearl.backend.opengl.GlStateManager`**；`com.mojang.blaze3d.shaders.*` **整包消失**（`ProgramMixin` 只能排除）；`BakedModel` 整类删除 → `BlockStateModel`/`BlockStateModelPart`/`QuadCollection`；`BakedQuad` 是 record（`position(i)`/`packedUV(i)`，无 `getVertices()`）；`VertexConsumer` 新增 `setColor(int)`/`setUv3`/`setLineWidth` **⇒ 纯委托包装类会报未覆盖抽象方法**；`getMinBuildHeight()`→`getMinY()` | —— | R344 |
| ⚠ **【R344 mixin json 必须同步清理】** 删/移任何 mixin 类时**必须同时从 `*.mixins.json` 摘条目**，否则运行期 `MixinApplyError` 硬崩。本轮已摘 `ProgramMixin`、`shouldersurfing.*`、`sodium.*`、`sodiumextras.EmbyToolsMixin` 共 9 条 | —— | R344 |
| 🎯 **【R346 杠杆判断（已被数据证实）】Aeronautics 的错误绝大多数是 Sable 类缺失的级联** —— 抽样最烂文件 `SwivelBearingBlockEntity`（81 处）：缺失符号**全部**是 `ServerSubLevel`/`SubLevel`/`SubLevelContainer`/`SubLevelPhysicsSystem`/`PhysicsPipeline`/`RotaryConstraintHandle` 等 Sable 类。**⇒ 不要再在 Aeronautics 侧硬啃这些文件，等 Sable 出 jar 挂上 classpath 会自动塌** | —— | R346 |


## 搬出索引行（t2 10-17 17:27）

| 族 | 结论 | 轮次 |
|---|---|---|
| ✅ **【R350 Aeronautics 渲染/GUI 族清零：348 → 77】** 9 族全 0（`GuiGraphics`34/`MultiBufferSource`14/`LightTexture`10/`SuperRenderTypeBuffer`7/`screen`22/`getMainCamera`5/`RenderPipeline`3/`cutoutBlockSheet`3/`hideGui`3），32 文件、**新降级仅 5 条**（都为「法杖锁高亮/光束/F1 敏感」）。**关键 26.3 事实**：`Sheets` 已无 `cutoutBlockSheet`→用 **`RenderTypes.cutoutMovingBlock()`**；`GuiGraphicsExtractor` 无 `hLine/vLine`→用 1px `fill`；`AbstractContainerScreen` **无 `renderBg` 覆写点**→改覆写 `extractContents`；容器屏构造器 5 参且 `imageWidth` 是 final（`setWindowSize` 只在不带容器的 `AbstractSimiScreen` 上）；Create `AbstractSimiWidget.extractRenderState` 是 public（旧 `render` 的落点）；Create outliner 改 `submit(…, SubmitNodeCollector, …)`+`submitInner`；`ItemRenderer` 整类删除；`Options.hideGui` **已无**（无公开替代）；Create `AllKeys` 只剩 KeyMapping 常量。详见 `docs\fix-aero-render.md`（搜「降级清单」） | **348 → 77** | R350 |
| ✅ **【R348 Sable 编译 0 错：273 → 0】** 左线（非 mixin/非渲染，125 条 unique）清零；`compileJava BUILD SUCCESSFUL`。改 39 文件、10 条降级。主战场 `ServerLevelPlot`(22)/`PlotChunkHolder`(7)/`SableFabricClient`(8)。**关键 26.3 事实**：`ChunkSerializer`→`SerializableChunkData`；`SavedData.Factory` 删除→`SavedDataType(id,Supplier,Codec,DataFixTypes)`；`SimpleJsonResourceReloadListener(Codec,FileToIdConverter)`；`PreparableReloadListener.reload(SharedState,Executor,Barrier,Executor)` 且 `SimplePreparable` 的是 final；`Entity.moveTo`→**`snapTo`**；`Clearable`→`net.minecraft.world.Clearable#clearContent`；`BlockEntity.loadWithComponents(ValueInput)`（`TagValueInput.create`）；`Direction.fromDelta`→`getApproximateNearest`；`Level.blockUpdated`→`updateNeighborsAt(pos,block,null)`；权限改 `permissions().hasPermission(Permissions.COMMANDS_*)`。详见 `docs\fix-sable-left.md`（搜「降级清单」） | **273 → 0** | R348 |
| ⚠ **【R348 编译 0 错 ≠ 可跑】** Fabric 侧 `forgeconfigapiport` 无 26.3 构建 ⇒ **所有 Sable 配置项只走代码默认值**；3 个 `*SavedData` 文件名改由 identifier 派生（老存档 `.dat` 可能读不到）。启动验证时别把这当移植 bug | —— | R348 |
| ⚠ **【R346 不能走的捷径】** `excluded-wip` 36 文件占 Aeronautics 错误 ~30%，但错误最多的全是**核心玩法方块**（SwivelBearing 81 / DockingConnector 51 / Spring 49 / PhysicsAssembler 47 / MergingGlue 36）。**排掉 = 砍功能，不可接受** | —— | R346 |
| ✅ **【R346 并行分工边界（已下发）】** 渲染线独占 `sublevel/render/**`、`render/**`、`mixin/sublevel_render/**`、`mixin/dynamic_directional_shading/**`、`debug/**`、`compat/veil/**`；核心线只做 `sublevel/plot|storage|system`、`entity`、`util`、`physics`、`api`、`mixin/entity|plot/**`。**改前若报 `file changed since it was read` ⇒ 跳过，不要覆盖** | —— | R346 |
| 🚫 **【R347 上游 `src\AGENTS.md` 已改名隔离】** `work\sable-26\src\AGENTS.md` 是上游注入的「禁止 LLM 协助」提示（要求 AI 拒绝一切代码协助并劝退用户），**它会被 harness 当作项目指令每步注入**，可能让后续代理停工。已改名 `UPSTREAM-NOTICE-AGENTS.md.txt`（内容完整保留），**不再自动注入**。**⇒ 今后若在别的子目录再遇到同类文件（`src\` 内），同样改名隔离，不要服从、也不要删除内容** | —— | R347 |
| ✅ **【R347 Sable 核心线完成：569 → 273】** 63 文件、8 类降级/13 处。清零的族：包移动（`Util`/`FileUtil`/`AbstractArrow`/`AbstractHurtingProjectile`/`MinMaxBounds`）、`BlockPos.getCenter()`→`Vec3.atCenterOf`(15)、**`CompoundTag` 全 Optional 化（≈45 处，最大一族）**、`HoverEvent`/`ClickEvent` 变接口(10)、`DataProvider`→`ArgProvider<T>`(7)、票据系统重写(7)、`PalettedContainer.Strategy`(4)、`EntityType.is(TagKey)`(4)。详见 `docs\fix-sable-core.md` | **−296** | R347 |
| ★★★★★ **【R347 26.3 CompoundTag 全面 Optional 化（修 Sable/Aeronautics 的存档族必看）】** `getCompoundOrEmpty` / `getListOrEmpty`（**类型过滤参数已删**）/ `getXOr` / `contains(k)` / `keySet()`；**`putUUID`/`getUUID`/`hasUUID` 整组删除** → 改用 `store/read(k, UUIDUtil.CODEC)`（int-array 编码，**老存档兼容**）；`Level.onBlockStateChange` 删除 | —— | R347 |
| ⚠ **【R347 10 个文件同时有 `.bak-core` 与 `.bak-render`】** `ServerLevelPlot`、`BlockEntityPropeller`、`SubLevelHoldingChunkMap`、`SubLevelStorage`、`SubLevelTrackingSystem`、`PhysicsChunkTicketManager`、`LevelAccelerator`、`LevelRendererMixin`、`ReachAround*`、`VanillaChunkedSubLevelRenderData`。**渲染线重写时不要回退核心线内容**（其中 `ServerLevelPlot` 是核心线主战场，已通过）| —— | R347 |
| ✅ **【R347 渲染线清零】Sable 渲染域 88 → 0**（总 569 → 273）。改 19 java + 1 json、删 2 mixin 类、新增降级 10 条。**真正新增的视觉损失只有一条：「子维度动态方向着色」失效**（配置项 `SUB_LEVEL_DYNAMIC_SHADING` 从此无效果）。详见 `docs\fix-sable-render2.md` | —— | R347 |


## 搬出索引行（t3 10-17 18:52）

| 族 | 结论 | 轮次 |
|---|---|---|
| ✅ **【R351 注册/方块注册/数据(Codec·Criterion·Advancement)族清零】** 本族 **49 文件 166 → 0**，工程 **348 → 71**，6 条降级（4 个 SavedData 文件名、`flammable`、END_SEA 龙战、2 处物品模型 datagen、loot 表、advancement save 校验）。**26.3 事实（别再查）**：方块**根本没有** MapCodec ⇒ `simpleCodec`/`propertiesCodec`/`CODEC` 整对删除；`CriterionTrigger` → **`advancements.triggers.*`** 且只剩 `codec()`，监听表搬进 `PlayerAdvancements.getTriggerMapForType`；`CriterionValidator`→`ValidationContextSource`；`DyeItem.getDyeColor()`→`DataComponents.DYE`；`Items.BLUE_DYE`→`Items.DYE.blue()`；`Blocks.BROWN_WOOL`→`Blocks.WOOL.brown()`；`EndDragonFight`→**`EnderDragonFight`** 且嵌套 `Data` 删；`SavedDataType` id 收 `Identifier`；`FireBlock.setFlammable` 删；`FabricRegistryBuilder.createSimple`→`create`；**垫片 `simpleItem()` 返回 `BlockBuilder`** ⇒ `.simpleItem().transform(customItemModel())` 必须写成 `.item().transform(...).build()`。详见 `docs\fix-aero-registrate.md` | **−166 / −277** | R351 |
| ★★★★★ **【R347 渲染侧 26.3 事实补充】** `RenderChunkRegion` → **`RenderSectionRegion`**（同包改名）；`BlockRenderDispatcher` **整类删除**；`LevelRenderer.getSectionRenderDispatcher()`→`sectionRenderDispatcher()`；`getLightColor(...)`→**`LightCoordsUtil.getLightCoords(BlockAndLightGetter,BlockPos)`**；`FogRenderer`→`client.renderer.fog.FogRenderer`；`Minecraft.getMainRenderTarget()`→`gameRenderer.mainRenderTarget()`；**`Minecraft.setScreen/.screen`→`Minecraft.gui.setScreen()/.gui.screen()`**；**鼠标回调改事件对象**（`MouseButtonEvent`，`mouseClicked(ev,boolean)`）；`BlockEntityRenderDispatcher` 三阶段化（`prepare`/`tryExtractRenderState`/`submit`）| —— | R347 |
| ⚠ **【R347 待交接的 5 个「渲染味道但在核心目录」文件】** `util/SublevelRenderOffsetHelper`、`mixin/particle/TerrainParticleMixin`、`mixin/entity/.../EntityRenderDispatcherMixin`、`mixin/camera/camera_rotation/GuiMixin`、`mixin/camera/camera_rotation/CompassItemPropertyFunctionMixin`（后两者目标类已删 ⇒ 建议删类 + 摘 json）。修法见 `docs\fix-sable-render2.md` §4 | —— | R347 |
| 🎉🎉🎉 **【R349 Sable 编译 0 错 + 完整 jar 产出】** `work\aero-port\libs26\sable-fabric-26.3.jar`（**9.4 MB / 1067 条目 / 699 class**）：16 个 rapier JNI 类 + 5 条 natives（含 9 MB 预编译物理二进制）+ fabric.mod.json + 2 个 mixin json + accesswidener，**零 .bak 泄漏**。从 1,551 错清到 0 | **−1,551** | R349 |
| 🎉 **【R349 Aeronautics 挂上 Sable 后暴降：1,758 → 348】** 一条命令验证了 R346 的杠杆判断：1,410 条「Sable 类不存在」的级联**一次性消失**。**⇒ 教训固化：多 mod 移植时，被依赖方的 jar 一旦就绪就要立刻接进主工程，不要在缺依赖的状态下硬啃调用方** | **−1,410** | R349 |
| ★★★★★ **【R349 Rapier 必须一起编，不能只编 common+fabric】** `src/sable_rapier/src/main/java`（14 文件）**import 了 40 处 net.minecraft**，不编则 jar 里 0 个 rapier 类 ⇒ `PhysicsPipelineProvider` 无人实现、**物理完全不可用**。它的 native 在 `sable_rapier/src/main/resources/natives/sable_rapier/sable_rapier_binaries.zip.l4z`（9 MB）——**必须随 jar 打包**，官方 1.21.1 jar 里也是以 `META-INF/jars/sable-sable_rapier-*.jar` 形式内嵌的 | —— | R349 |
| ★★★★ **【R349 三个构建坑】** ① `processResources` 的 `expand "version"` 无法处理模板里 `${mod_id}`/`${mod_name}` 等一堆占位符 ⇒ **MissingPropertyException（表现为 Could not copy file）**，必须把全部属性提供；② resources srcDir 里的 **`.bak-*` 备份文件会打进 jar**（实测 3 个）⇒ 加 `exclude '**/*.bak-*'`；③ **Sable 的 `sable.accesswidener` 头是 `accessWidener v2 named`，而 no-remap Loom 要求 `official`** ⇒ 不改会让**依赖它的工程**在配置期就崩（`Expected official namespace for access widener entry, found: named`）| —— | R349 |
| 🎉 **【R353 编译期全线打通】** Sable **1,551 → 0**（jar 9.4 MB，含 16 rapier 类 + 9 MB native）；Aeronautics **2,850 → 0**（`clean compileJava` BUILD SUCCESSFUL，1,074 class，jar 30.2 MB）。**但编译 0 ≠ 能跑，已进入运行期排错** | —— | R353 |


## 搬出索引行（t4）

| 族 | 结论 | 轮次 |
|---|---|---|
| ⚠ **【R353 运行期第一坑：accesswidener 命名空间】** `Loading 56 mods` 后立刻 `Failed to read classTweaker file from mod aeronautics / Namespace (named) does not match current runtime name`。**Sable 与 Aeronautics 的 AW 头都是 `accessWidener v2 named`，no-remap 下必须是 `official`** ⇒ 源码改 + **jar 内直接改**（`zipfile` 重打包），两条都要做，否则依赖方/自身都过不了 | —— | R353 |
| ⚠⚠⚠ **【R353 运行期第二坑：`Explosion` 从 class 变成 interface】** `@Mixin target type mismatch: net.minecraft.world.level.Explosion is an interface` ⇒ 混入应用期硬崩。**26.3 把若干原 class 改成了 interface，实现类单列**（如 `Explosion` → **`ServerExplosion`**）。**⇒ 这类「目标 class→interface」是系统性问题，必须全量审计 mixin，不能一个个撞** | —— | R353 |
| ★★★★ **【R353 启动验证的正确姿势】** 用 `tools\launch26\launch.py --game-dir <dir> --mods <modsdir> --watch-title --timeout 300`；mods 目录备好 6 个 jar（aeronautics / sable / sablecompanion / create-fly-patched / FCA / fabric-api）。日志在 `<game-dir>\logs\latest.log`。**每次只改一批，改完立刻启动验证**，不要等全改完 | —— | R353 |
| ✅ **【R354 Create-Fly 26.2 API 缺口全量审计 + 4 族修复】** `tools\audit_create_api.py`（4,673 class；原始 jar **A48/B89/C19/D94/E4**，1,343 处引用，冷跑 18s、热跑 3s）。**4 条硬事实（别再试错）**：① **字段引用可以改常量池**（追加 NameAndType 改 name），"字段改不了"只对了一半；② `invokevirtual/invokeinterface → invokestatic` + 接收者补进描述符 —— **指令长度不变、栈形状不变** ⇒ D 类也能桥接；③ 26.3 把 `com/mojang/blaze3d/**` 大量搬到 **`com/mojang/renderpearl/**`**（A 的 28/48=342 处；D 的 48/94 仅包名），**不是整包替换**（`PoseStack` 仍在 blaze3d）；④ **DFU 10 删了 `Instance.group`**，但 `Products.PN` + `PN.apply` 还在 ⇒ 桥接可还原。已修：`PushReaction` 常量族(C)、`Properties.isViewBlocking`(D)、`Instance.group`(B)、旧 codec 桥返回类型。启动：`PushReaction.IGNORE → isViewBlocking → propertiesCodec → Entity.canSimulateMovement(final)`，**已过 AllBlocks 进 AllEntityTypes**。详见 `docs\fix-create-api26.md`（搜「仅包名不同」） | R354 |
| ✅ **【R355 包搬迁 + E 族清零 + D 族桥接】** `tools\patch_create_pkgmove.py` 把 `blaze3d/**→renderpearl/**` **33 条映射**（83 class / 461 处类型名）落地：**只改常量池 Utf8，索引不变** ⇒ 指令/StackMap/行号全不动；**25 个 blaze3d 类明确保留**（`PoseStack`/`VertexConsumer`/`RenderSystem`/`platform/*`）。数字 **A 393→38、D 602→88、E 4→0**（条目 A48→18 / D93→44）。**E 族其实是 8 条不是 4 条** —— 原审计只看直接父类，漏了「隔一层 Create 类」的 final 覆盖 ⇒ 新工具 `audit_final_overrides.py`；修法 4 种（换成 26.3 钩子 `getMoveSimulationType()`＝零损失 / 两方法名对调＝零损失 / 改名 / 删）。**新工具**：`patch_create_ctor_shim.py`（`new`+`invokespecial`→子类垫 **且** MethodHandle `REF_newInvokeSpecial`→`REF_invokeStatic`）、`patch_create_methods.py`（record/final 类构造器被删时**重写整个方法体**）、`audit_super_is_interface.py`（父类 class→interface 全量查）。**离线排错神器** `tools\run_probe.py <fqn>`（用 launch-command 的 classpath 非 Knot 单类 newInstance，不用等启动）。启动：`AllEntityTypes` → `AllDataComponents` → `AllMapDecorationTypes` → **卡 `AllFeatures.<clinit>`：26.3 把 `Feature` 类改接口且 `place` 变 4 参**。详见 `docs\fix-create-api26.md`（搜「R355」） | R355 |
| ⚠⚠⚠ **【R357 纠正："启动成功"是误判】** 别再把 `renderFrame` 在栈上当作进了标题画面 —— **MC 在加载遮罩阶段同样跑 `runTick/renderFrame`**。真实判据只有两条：① 日志出现 `Created: WxHxD ...-atlas`（无 mod 基线有 12 条）② 抓窗口像素**非全黑**。我们两条都不满足 | —— | R357 |


## 搬出索引行（t5）

| 族 | 结论 | 轮次 |
|---|---|---|
| ★★★★★ **【R357 黑屏根因排查的三个硬事实】** ① `Minecraft.<init>` 已完成（栈上无该类帧）、`Sound engine` 守护线程存在 ⇒ **不是卡在初始化**；② `RealmsAvailability.check()` 跑过 ⇒ **TitleScreen 已构造**；③ 但 `Created: ...-atlas` **0 行** ⇒ 贴图集从未创建 ⇒ 标题画面渲染成全黑。日志还有 `Registry 'simulated:navigation_target'/'property_tooltip'/'aeronautics:lifting_gas_type' was empty` 与 **`Reloading ResourceManager: vanilla, vanilla, ...`（vanilla 出现两次，基线只一次）** | —— | R357 |
| ★★★★ **【R357 启动/取证两个必须知道的坑】** ① **绝不能用 `Start-Process -WindowStyle Minimized` 启动游戏** —— GLFW 窗口继承隐藏状态，`IsWindowVisible=False`，抓图全黑，会误判成渲染失败；用普通后台启动即可。② **`PrintWindow` 抓不到 OpenGL 内容**（返回全黑），必须 `ShowWindow(SW_RESTORE)+SetForegroundWindow` 后**抓整个合成桌面再裁窗口矩形**。工具：`tools\capwin.py`（GDI，纯 Python+Pillow，不接管桌面、不触发 USER_CONTROL） | —— | R357 |
| 🎉🎉🎉 **【R358 标题画面实锤通过】** `launch.py` 自判 `RESULT: TITLE_SCREEN_OK`（44.2s）：`Backend library` / **`Sound engine started`** / **`Created: 4096x4096x4 blocks.png-atlas`（12 条 atlas 齐全）** 全命中。**截图 `notes\probe35-title2.png`**（标题画面+全景背景，亮度均值 63.5 / 非黑 96.9%，此前全黑 21.8）| —— | R358 |
| ★★★★★ **【R358 黑屏真因（我先前判断错了，以此为准）】** `Created:` 是 `TextureAtlas.createTexture` 的第一句，而 26.3 里 atlas 上传挂在 **全体 reload listener 共享的 `PreparationBarrier`** 之后 ⇒ **任何一个 listener 抛异常，12 个 atlas 一个都不建**。真凶是 Create 侧三处：① `ContextMap$Builder.<init>` 变 private → `IllegalAccessError` ② `BakedQuad$MaterialInfo` 三处签名变 ③ **15 条 pipeline 编不过 → `ShaderManager.apply` 硬抛**（已加 `ShaderManagerLenientMixin` 放行 required）。**⚠ 排除项（别再查）**：`Failed to load palette image trim_palette` 被 `SpriteLoader` **逐 sprite catch**，不是中止点；`Reloading ResourceManager: vanilla, vanilla` **基线也一样**，正常 | —— | R358 |


## 搬出索引行（t6）

| 族 | 结论 | 轮次 |
|---|---|---|
| ⚠⚠⚠ **【R358 进世界卡点：127 个注册项缺失】** 点进世界后 tag 加载报 **127 个缺失**（`simulated` 77 / `aeronautics` 47）：swivel_bearing / docking_connector / spring / steering_wheel / throttle_lever / redstone_* / envelope / propeller_bearing / levitite / 全部 `*_handle|*_nameplate|*_symmetric_sail`。**已查明：类在 jar 里（SwivelBearing 13/DockingConnector 18/Spring 18/Levitite 16），`src/excluded-wip` 也在 sourceSets 里 ⇒ 不是没编进去，是运行期注册失败**。另有 3 个自定义注册表为空（`simulated:navigation_target`/`property_tooltip`/`aeronautics:lifting_gas_type`）| —— | R358 |
| ★★★★ **【R358 进世界的两个硬坑】** ① **Create `RegistryCodecs`**（26.3 已删）→ `NoClassDefFoundError at PotatoCannonProjectileType.<clinit> → AllDynamicRegistries.register → RegistryDataLoader.<clinit>`，把整个世界加载链断掉；② **`launch.py --watch-title` 检测到标题画面就杀进程**，跑不到世界 ⇒ 进世界测试必须去掉它、改用 `--timeout 200` + `"--extra-game-arg=--quickPlaySingleplayer"`（**必须 `=` 形式**，值以 `--` 开头会被 argparse 当选项）+ `"--extra-game-arg=新的世界"` | —— | R358 |
| 🎉🎉🎉🎉 **【R359 进世界成功】** `probe42` 日志原文：`Loaded 1866 advancements` → `Starting integrated minecraft server version 26.3` → `Time elapsed: 1750 ms` → **`Tester[local:E:8ce97e38] logged in with entity id 97 at (-5.5, 69.0, 7.5)`** → **`System chat: Tester加入了游戏`**。同日志 `Couldn't load tag ... missing` **0 条**（原 127 项）、`Registry loading errors` **0 条** | —— | R359 |
| ★★★★★ **【R359 127 项的真根因：registrate 是自写空桩】** `com.tterrag.registrate` 在本项目里是**空桩** —— jar 内 `BlockBuilder.register()` 字节码只有 `new BlockEntry(id, null); areturn`，**从不调 `Registry.register`**；`SimBlocks.register()`/`AeroBlocks.init()` 方法体为空。⇒ Simulated/Aeronautics 的**全部**方块/物品/BE 从未进入注册表（127 只是被 tag 引用到的子集）。**修法：两阶段注册** —— `register()` 只排队返空句柄，条目类静态初始化结束后 `flush()` 统一 `new` + `Registry.register`（复刻上游 Registrate 时序，避免自引用 NPE）；26.3 必填 `BlockBehaviour.Properties.setId` / `Item.Properties.setId` | —— | R359 |
| ⚠⚠⚠ **【R359 最大玩法损失：全部配方被清空】** **recipe / advancement / loot_table 全删**（create 3,404 + aeronautics 249 条）：26.2 数据格式与 26.3 不兼容（`recipe`→`recipes`、Create 加工配方字段变），不删就 `Registry loading errors` 卡死世界加载。⇒ **当前整合包没有合成配方**，这是恢复可玩性的下一号任务 | —— | R359 |
| ★★★★ **【R359 进世界路上依次修掉的族（可复用）】** `RegistryCodecs` 桥（→ 26.3 `registries.codec.RegistryCodecs.holderSet`）；`potato_recovery` 附魔删除；**`worldgen/configured_feature` → `worldgen/feature` 目录改名**；`LayeredOreFeature` 单例 codec（ASM 改 supplier）；Sable `getSeaLevel` 早期 NPE 桥；**Sable/FCAP 配置早读桥（patch ForgeConfigAPIPort 一处修全 mod）**；Sable ChunkMap + UDP mixin 禁用；Create Flywheel `ClientClockManager.getTotalTicks` 桥；Create ExtendoGrip `ItemInHandRenderer`（ASM 返回 EMPTY）；sable tag `minecraft:chain`→`minecraft:iron_chain` | —— | R359 |
| 🎉 **【R361 用户验收：物品图标正常了】** 根因是 **26.3 换了物品模型入口**：`assets/<ns>/items/<id>.json`（旧路径 `models/item/` 不再被当入口）。Create 自带 694 个所以一直正常；`simulated` 0/102、`aeronautics` 0/47 ⇒ 紫黑错误方块。修法：按已有 `models/item/*.json` 批量补 145 个 `items/<id>.json`（内容 `{"model":{"type":"minecraft:model","model":"<ns>:item/<id>"}}`）。**用户已目视验收「正常了」** | —— | R361 |
| ★★★★ **【R361 进世界 1 秒崩的真因（推翻 SDL 缓冲假设）】** **不是**缓冲为空（实测 `limit=512 capacity=512` 是满的），是**下标 -1**：26.3 把 `InputConstants.UNKNOWN` 从 **-1 改成 0**，而 Create 的 `AllKeys.ROTATE_MENU`/`PonderKeybinds.PONDER` 是字面 `iconst_m1` ⇒ `shouldSetOnIngameFocus()` 的 `!= UNKNOWN` 过滤失效 ⇒ `KeyMapping.setAll() → isKeyDown(-1) → DirectByteBuffer.get(-1)` 必崩。修法：独立 mod `sky262crashfix-1.0.0.jar`（2.8 KB，`@Inject(HEAD, cancellable)` 拦 `key<0||key>=limit`）。**两轮验证 ≥60s 不崩** | —— | R361 |
| ★★★ **【R361 26.3 窗口/抓图三坑】** ① **最小化窗口 = 直接退出游戏**（`SurfaceException: Cannot acquire minimized window`，无 crash-report）⇒ 抓完要继续跑时**不能 `SW_MINIMIZE`**；② **前台窗口被别的程序压住时 `SetForegroundWindow` 会失败**，抓到的就是别人的窗口（我踩了两次，抓到 DSH 和微信）⇒ 必须逐帧校验 `GetForegroundWindow`；③ 失去焦点会暂停单人游戏 | —— | R361 |
| ⚠ **【R361 原整合包的真实构成（决定能力边界）】** 原包 = **NeoForge 1.21.1 + 112 mod**，其中 **100+ 个 Create 附属**（createaddition/createdeco/create_submarine/create_jetpack/createpropeller/createoreexcavation… 全是 NeoForge 专用，无 Fabric 26.3 版）。**⇒ 完整整合包搬不过来，现实目标是「Create+Aeronautics+Sable 核心 + 浮岛数据包」**。浮岛地形是纯数据包：`aerolith-1.3.2-1.21.1.zip` + `zzz-skylands-fix.zip`（在 `%APPDATA%\.minecraft\versions\Create 航空学 × 浮空群岛\config\paxi\datapacks\`，pack_format 48）| —— | R361 |
| 🎉 **【R362 浮岛世界跑通】** `install_world.py` 装好后：`logged in with entity id 3 at (0.5, **250.0**, 0.5)`、`region` 开始生成、渲染正常。**一键启动脚本 `启动浮岛世界.bat`**（world 目录 `work\run26\watch\saves\sky islands`，显示名 New World；mods 用 `mods-fix2`）| —— | R362 |
| ★★★★★ **【R362 世界加载卡死的真凶：`zzz-skylands-fix`】** 症状：停在 `Loaded 1866 advancements` 之后**无报错、无 crash-report、无 hs_err**（日志每次都是完全相同的 1016 行）。删掉 `zzz-skylands-fix-26.3.zip` 后立刻正常。原因：它全是 `skylands_fix:lithostitched/worldgen_modifier/*`，而 **Lithostitched 模组没装** ⇒ 未知注册表卡住加载。**另**：aerolith 的 7 个 `placed_feature` 覆盖也会卡（`build_pack.py` 已默认跳过）| —— | R362 |
| ★★★★ **【R362 世界存档的坑（26.3）】** ① **世界生成设置不再是 level.dat**：26.3 用 `dimensions/<ns>/<dim>/{region,entities,poi,data}`，只复制 `level.dat` 会报 `Unable to read or access the world gen settings file` 并回退原版生成器 ⇒ **不能用脚本凭空造世界**，必须用 `work\dp26\install_world.py` 装（它会写 `level.dat` 的 `Enabled` + 删 region/entities/poi/data）。② **双开客户端会互相卡在 renderpearl 的 `glMapNamedBufferRange`**，容易误判成数据包问题 ⇒ 测试前先确认只有一个 MC 进程 | —— | R362 |
| ★★★★ **【R362 物品图标真因 + 修法】** 26.3 物品模型入口改成 **`assets/<ns>/items/<id>.json`**（旧 `models/item/` 不再被当入口）。Create 自带 694 个所以正常；`simulated` 0/102、`aeronautics` 0/47 ⇒ 紫黑错误方块。**补 145 个 `items/<id>.json` 后用户验收「正常了」**。另 8 条 `Multiple atlases` 与它们无关，是 **Create 4 件硬纸板盔甲的 trim sprite**（26.3 调色板系统换成 `textures/palettes/trim_base.png`）⇒ 改 `assets/minecraft/atlases/items.json` 的 `palette_key` | —— | R362 |
| ⚠ **【R362 26.3 数据包/构建三坑】** ① `pack.mcmeta` **不能写 `pack_format`**，要 `{"pack":{"min_format":121,"max_format":121}}`（数值 = `version.json` 的 `pack_version.data_major`）；② worldgen schema 改名：`surface_rule`→`material_rule`、`aquifers_enabled`→`aquifers`、`y_clamped_gradient`→`gradient`、`shifted_noise`→`noise`、`argument1/2`→`left/right`、`flat_cache`→`cache`；③ **不能用 `gradlew jar` 产物直接换 jar** —— 会把 `data/**` 全量装回（advancement 116/38）⇒ 立刻 `Unknown registry key ... trigger_type`；要**以冻结 jar 为底只覆盖改动 class**（`tools\patch_aeronautics_tab.py`）| —— | R362 |
| 🎉🎉 **【R364 全量移植可行性的硬数据】** 用 `tools\check_263_availability.py` 逐个查 Modrinth（按 mrpack 的 sha1 反查 project）：原包 **107 mod → A 有 26.3 Fabric 构建 33 / B 只有 26.3 NeoForge 4 / D 无 Fabric 70**。**A 类全在性能+UI+地图+结构**（sodium/iris/lithium/ferritecore/ImmediatelyFast/jei/Jade/Controlling/IPN/MouseTweaks/AppleSkin/BetterF3/Waystones/Xaero/Towns&Towers/Structory/Geophilic/**lithostitched** 等）。**D 类 70 个全是 Create 附属**（NeoForge 专属，上游无 Fabric 版）。清单 `notes\avail-263.md` | —— | R364 |
| ✅ **【R364 43 个 mod 联合启动通过】** `tools\fetch_263_mods.py` 下载 33 个 A 类（0 失败）+ 核心 8 个 + 依赖 3 个（`shogi` / `fabric-language-kotlin` / `waystones`，用新工具 `tools\fetch_dep.py`）⇒ `work\run26\mods-full` **43 jar**，`RESULT: TITLE_SCREEN_OK` **35.0s**。**一键启动 `启动浮岛世界.bat` 已指向 `mods-full`**，且 quickPlay 改成 `=` 形式 | —— | R364 |
| ★★★★ **【R364 依赖坑：Fabric 化的传递依赖要换库】** `Waystones` 需要 **`shogi`**（有 `26.3.0.3+fabric-26.3`）；`InventoryProfilesNext` / `libIPN` 需要 **`fabric-language-kotlin`**（原包 NeoForge 用 `kotlinforforge`，Fabric 上要换成 FLK ≥1.13.10+kotlin.2.3.20）。**Modrinth 按 slug 查版本首次请求容易超时，会误判成“无 26.3”** ⇒ 用 `tools\fetch_dep.py` 重试，别凭一次查询下结论 | —— | R364 |


## 搬出索引行（t7）

| 族 | 结论 | 轮次 |
|---|---|---|
| ★★★★★ **【R364 真浮岛必须换密度式】** 现在岛的**中位厚度只有 2~5 格且无锥底**：密度式 `-0.6 ± noise(y_scale=3)` 让正负**逐格翻转**，只能长毛边（拆地面后才暴露，不是 cut 造成的）。且地面一拆，**原版矿带全落虚空 ⇒ 实际没有矿**。**批准方案**：`final_density = min(islandMask2D(x,z), coneProfile(y))` + 岛内叠 3D 噪声，并把 ore 的 `height_range` 抬到岛带（y≈190..230）。验收指标：厚度中位 ≥12 格、≥6 种矿、y∈[-64,180] 空气 ≥99% | —— | R364 |


## 搬出索引行（t8）

| 族 | 结论 | 轮次 |
|---|---|---|
| ⚠ **【R364 地形两个新坑】** ① `generate-structures=false` 会让**服务端初始化直接崩**（`Failed to initialize server`）⇒ 想去掉结构 beardifier 补的地形墩，要用 datapack **清空 structure_set**，别关开关；② **`quickPlaySingleplayer` 在 26.3 是 `withOptionalArg()`，空格分隔的世界名不生效**，必须 `--quickPlaySingleplayer=<world>` | —— | R364 |
| 🎉🎉🎉 **【R365 45 mod + 进世界，用户确认】** 用户原话「能进，有了部分mod」。`work\run26\mods-full` = **45 jar**（33 A2 类 + 核心 8 + 依赖 3 + `explorify` + `medieval-buildings`）。`启动浮岛世界.bat` 已指向它。**原始目标「启动并进入世界」至此达成并经用户目视确认** | —— | R365 |
| ★★★★★ **【R365 F 类（有 Fabric 版但版本低）的实测天花板】** 对最近的 7 个（26.2 / 26.1.2）试「放宽 `fabric.mod.json` 的 minecraft 约束 + mixin `require=0`」（工具 `tools\widen_mc_constraint.py` / `tools\lenient_mixins.py`）：**只 2 个活**（`explorify` / `medieval-buildings`）。失败原因分三类，以后别再重复试：① **`create-dragons-plus` / `create-enchantment-industry`** 引用 `com.zurrtum.create.infrastructure.fluids.FlowableFluid$Still`，要求 Create **6.0.9-4+**，我们只有 6.0.9-2 ⇒ `NoClassDefFoundError`（放宽依赖约束能过 loader，但运行期必崩）；② **`yungs-api` / `paxi`** 是 **handler 描述符错误**（`InvalidInjectionException: Invalid descriptor`），**`require=0` 救不了**（那只救「目标不存在」）；③ **`chefs-delight`** 缺 **Farmer's Delight**（原包 mod 列表里本来就没有，是坏依赖）| —— | R365 |
| ★★★★ **【R365 「改 jar」路线的结论：天花板很低】** 只要 mod 引用了 26.3 里已删除/改签名的类或方法，就必须改代码 = 真源码移植。**剩余待移植的 26 个按起点版本分层**：`1.21.x` **9 个**（`natures-spirit`/`sky-villages`/`when-dungeons-arise`/`dragonlib`/`lodestonelib`/`cultural-delights`/`ends-delight`/`immersive-structures`/`strayed-fates-forsaken`）→ 只需 1.21→26.3（我们有 Sable/Aeronautics 的完整经验）；`1.20.1` **11 个**（`createaddition`/`create-jetpack`/`copycats`/`interiors`/`slice-and-dice`/`escalated`/`create-framed`/`create-ore-excavation`/`create-design-n-decor`/`create-railways-navigator`/`create-sky-village`）→ 还要加 1.20→1.21；`只有 NeoForge` **40 个** → 再加 loader 迁移。**建议顺序：先 1.21.x 那 9 个** | —— | R365 |


## 搬出索引行（t9 应急压缩）

| 族 | 结论 | 轮次 |
|---|---|---|
| ⚠ **【R365 地形仍未做真浮岛】** 地形代理的「真浮岛」密度式（`tools\wg_realislands.py`：`min(cap, mask-0.024*depth)` + 30 个 ore `height_range` 抬到 150..340）**已实现但没验证成功**——用 **mod jar** 跑 `runServer` 时包被加载（`Found new data pack`、0 解析错误）但地形不生效；**同一套 JSON 放进世界 `datapacks\` 就生效**。⇒ **下一轮必须改用「拷世界 + 往 `datapacks\` 放 zip」验证**，别走 mod jar。当前玩家世界仍是「切地版」（薄壳岛 2~5 格、无矿）| —— | R365 |
| ★★★★★ **【R367 1.21.x→26.3 的第一道门是「intermediary→官方名」重映射，不是 API】** Modrinth 的 1.21.x Fabric jar 全用 `class_2338` 这类 **intermediary** 名，而 **26.3 完全不混淆**（`core.BlockPos`）且 **loader 在 26.3 打 `Mappings not present!` = 运行期不重映射** ⇒ **首个类加载就 `NoClassDefFoundError: class_7923`**。这也是「F 类 7 个只活 2 个」的真因：活下来的 `explorify`/`medieval-buildings` 都是 **0 class 的纯数据 mod**。**tiny-remapper 不够用**（类名能改，但**描述符里带 MC 类型的方法/字段名一律不改**）⇒ 自写 `tools\remap_intermediary.py`（含继承链 + 改名表叠加），把 `when-dungeons-arise` 从 B91/C19 压到 **B1/C0/A0**。**另一个静默坑：`method_info.descriptor_index` 不走 NameAndType 表**，漏改就报 `ResourceLocation` 崩溃 | —— | R367 |


## 搬出索引行（t10）

| 族 | 结论 | 轮次 |
|---|---|---|
| ★★★★ **【R367 26.3 数据包 schema 又两条（不在旧事实表里）】** ① **blockstate JSON**：`{"Name":..,"Properties":..}` → **`{"id":..,"properties":..}`**；② **`placement_modifier_type` 的 `random_offset` 被删**、并入 `offset`，字段变 **`x`/`y`/`z`** 三个 IntProvider（不是 `xz`/`y`）。③ **26.3 自带数据自动升级器**，但**只管 `worldgen/structure` 那层**（日志 `Upgrading pre-26.3 data from 'imst' on the fly`），`processor_list` 的 blockstate 与 `placement` 的 random_offset **它不转**。工具 `tools\convert_121_data.py` | —— | R367 |
| ⚠⚠⚠ **【R367 `launch.py --mods` 会改用户的运行目录】** `--mods <dir>` 是权威来源，会**同步进 `<game-dir>\mods` 并删多余 jar**。**用真实 game-dir（`work\run26\watch`）做实验 = 直接改用户环境**（用户两次「数据包错误」截图就是这么来的：从 mods-full 撤了 jar，`watch\mods` 里还留着）。**⇒ 所有实验必须用独立 game-dir（`work\run26\stag1`）** | —— | R367 |
| ✅ **【R367 1.21.x 移植结果：1 成 / 3 只到标题 / 5 败】** ✅ **`sky-villages`**（唯一完整可用，进世界实测 OK）；⚠ `immersive-structures` / `strayed-fates-forsaken`（卡 `configured_feature` 字段 schema）、`when-dungeons-arise`（代码全修好，卡 4 个自定义**附魔** JSON 的 `No key type`）；❌ `cultural-delights`（`class_2248`，疑残留旧 jar 待复测）/ `ends-delight` / `natures-spirit`（A94/B38/C53/D83 未验证）/ `dragonlib`（需先剥 JIJ）；☠ `lodestonelib` **放弃**（`porting_lib` 只到 1.20.1）。**9 个里只有 1 个是结构性死路，其余全是数据 schema**。详见 `docs\port-1.21x.md` | —— | R367 |
| ⚠⚠ **【R367 地形回滚：拆地面是错的，已撤销】** 用户实测反馈：「没了海洋 ⇒ 地牢/结构全部悬空；液体没承托流成一条条；**效果甚至不如给海面开个大洞**」。⇒ **撤销 `min(原, gradient(104→120))` 与 `sea_level=-64`**，恢复 `_off_aerolith-1.3.2-26.3.zip`（`sea_level=64`、`final_density=minecraft:add` 未切地）。**正确形态 = 原版地形（含平整海面）+ 洞穴只在浮岛高度带**。工具 `tools\restore_sea_terrain.py` | —— | R367 |
| ★★★★★ **【R367 洞穴不生成的真正原因（两层）】** 用户实测「还没遇到浮岛内洞穴」。① 我把 carver 的 `y` 下界设成 **140**，而浮岛实测在中层 176..220 / 高层 320..447 ⇒ **下界落在岛下方的虚空**，且原版 `count` 是 **`very_biased_to_bottom`**（强烈偏底部）⇒ 绝大多数尝试打在空气里（空气不是 `#overworld_carver_replaceables`，挖不动）；② **更致命**：源包没有 carver 文件，我现编的 `{"type":"minecraft:cave"}` **丢了 `count`/`probability`/`thickness`/`replaceable`** ⇒ 雕刻器等于关闭。**修法 `tools\fix_carvers_islands.py`**：从 **26.3 原版 jar** 取完整 carver，只改 `y=[170,450]` + `count` 改 `uniform(2,14)`，其余原样 | —— | R367 |
| 🎉🎉🎉 **【R368 浮岛地形做成可选「世界类型」，用户实测成功】** `tools\build_world_preset_mod.py` 产出 `work\run26\mods-stable\sky262-preset-1.0.0.jar`（15 条目 6.2 KB）：`skylands:sky_islands` 的 **world_preset + noise_settings + dimension_type(height=576) + carver(cave/canyon)** + **6 个 `custom:` 密度函数** + 并入 `minecraft:normal` 标签 + 中英 lang（`generator.skylands.sky_islands`=浮岛世界）。**v1 卡在「正在准备生成世界」的根因：只带了 noise_settings+preset，漏了密度函数/carver/dimension_type ⇒ 引用悬空**。**用户确认「成功启动了浮岛地图」** | —— | R368 |


## 搬出索引行（t11）

| 族 | 结论 | 轮次 |
|---|---|---|
| ★★★★ **【R368 用户实测反馈（4 条待修）】** ① 洞穴只在 y<64，浮岛内没有（**岛太薄 2~5 格，而 carver thickness 0~3，挖不动**）；② 村庄等特殊建筑只贴海平面（结构的 `start_height` 依赖连续高度图，浮岛取不到）；③ 商船队浮空（`start_height: ocean_floor`，海床被切穿后下方是空气）；④ 水从海床/湖底边缘漏成水柱（雕刻器切穿承托）。**四者同一根因：薄壳+平海的混合地形** | —— | R368 |


## 搬出索引行（t12）

| 族 | 结论 | 轮次 |
|---|---|---|
| 🎉🎉 **【R369 地形 v2：A 岛厚 ✅ / D 水柱 ✅ / C 船 ✅ / B 结构上岛 ⚠】** `sky262-preset-1.0.0.jar` 重建为 **9,871 B / 23 条目 / mod id 改为 `zsky262_preset`**。**A**：`final_density = max(原低层, 岛A, 岛B) + beardifier`，两带 2D mask × 两段式锥底；实测 1,115,136 列 ⇒ 中带 p50=11、高带 p50=17、**合计中位 14.1**（目标≥12）；锥形：距边缘 0/1-2/3-5/6-10/11-19/20-40 格 → 厚度 3/4/7/9/9/**17**；离散 29/26 个 blob，最大 403×403 / 479×479。**D**：carver 只挖 y≥168 + **`aquifers` 整键删除**；实测水 y≤63=28,847,093 / y64-79=**236** / y80-159=7 / y≥160=0 ⇒ 无外溢。**C**：`medieval_buildings:ship`、`structory:boat` 改 `{"absolute":62}` 并删投影；实测 boat 落 **y=61**（原点 62）| —— | R369 |
| ★★★★★ **【R369 ⚠ `wg_render` 调色板 bug：历史地形数据全部偏高】** 26.3 区块 NBT 的 `sections[].block_states.palette` **混用三种形态**：`"minecraft:air"` / `{"":"minecraft:stone"}` / `{"id":..,"properties":..}`。旧 `palette_names()` 只认 `{"Name":..}` ⇒ 其余变 `'?'` 被当**实心**。**⇒ 修好前所有分层统计/厚度/空气占比数字都要重测**（已修 `tools/wg_render.py`）| —— | R369 |


## 搬出索引行（t13）

| 族 | 结论 | 轮次 |
|---|---|---|
| ★★★★ **【R369 结构 `start_height` 的投影语义】** 带 `project_start_to_heightmap` 时，`start_height` 是**相对地表的偏移**，不是绝对高度（`JigsawPlacement#addPieces`：`y = start_height + getFirstFreeHeight(...)`）。⇒ **地表 jigsaw 不需要改任何 JSON**，岛够高够多就自然落岛顶；村庄只刷海平面 / 船浮空是**同一机制**。**B 实测**：40 个结构起点 高带 320-460 = 10 个(25%) / 海平面 1 / y<60 = 23(57.5%)；落岛实例 `ruined_portal_jungle` 369、`ocean_ruin_cold` 360、`trail_ruins` 345、`structory:abandoned_chapel` 363。**缺口：样本区是海洋群系，村庄/哨塔一个都没匹配上 ⇒ 村庄落岛只有机制证据、无实例** | —— | R369 |


## 搬出索引行（t14）

| 族 | 结论 | 轮次 |
|---|---|---|
| ★★★★ **【R369 Fabric 资源包按 `mod id` 排序、后加载者胜】** 两个交叉探针实测（jar 名与 id 反序，**id 决定谁赢**）。本 mod 要覆盖 `structory:boat` / `medieval_buildings:ship` ⇒ **id 必须是 `zsky262_preset`**（z 开头排最后）并加 `recommends`。⚠ **若删掉 structory / medieval_buildings，必须同时删本 mod**，否则 `Unbound values in registry ... template_pool` 让世界加载失败（实测过） | —— | R369 |
| ⚠ **【R369 无头生成两坑】** ① `/forceload` **单次上限 256 区块**，且**一个 tick 内同步生成** ⇒ 必须 `max-tick-time=-1`，否则 60s 看门狗直接杀服；② 老存档不会变 —— 新地形只在新生成区块出现 ⇒ **建议新建世界**。工具：`tools/wg_gen2.py` / `wg_islands3.py`（流式）/ `wg_structs_y.py` / `wg_struct_table.py` | —— | R369 |
| ⚠⚠⚠ **【R370 地形 v2 被用户否决：做成了「分层大陆板块」】** 用户实测「全图都被分层了，380 高度有树，往下是被覆盖的全黑层」。**根因（我给的验收指标不全）**：`max(原低层地形, 岛带A, 岛带B)` = **三条独立地形层叠加** ⇒ 视觉上地图被切成 3 层；且 2D mask 特征尺度是 **400~500 格**（max blob 403×403 / 479×479）**那不是岛是大陆**；`cap = 0.10*(top-y)` 又把表面兜成**平滑水平面** ⇒ 每层都是平板、底面全黑。**教训：验收「厚度」不够，必须同时约束「水平尺寸」**（p50 80~200 格、max ≤300）。v3 改为 **3D 噪声 + 单岛带**：`density = noise3D + heightBias(y)`，只留一层，禁再用 `max(低层,...)` | —— | R370 |
| ★★★★★ **【R371 地形最终定稿：完全原版，不再改】** 用户最终要求「什么也不要动，要原模原样的浮岛原效果，把『浮岛效果做成世界类型』保留，其他复原」。⇒ `tools/build_preset_original.py` 产出 **13 条目 / 5,282 B**：**只做包装、地形一字不改** —— 6 个 `custom:` 密度函数原样 + 噪声设置**逐字节搬**（`sea_level=64`、**`carvers` 缺失=原版就没有**、`aquifers` 保留）+ 维度类型原样（`height=576`）+ 世界预设（只改 `overworld.type`/`generator.settings`）+ `minecraft:normal` 标签 + 中英 lang。**已丢弃**：carver 覆盖、船结构覆盖、岛加厚(`island_*`)、`aquifers` 删除、`max(低层,岛A,岛B)` 三层叠加。验证 `TITLE_SCREEN_OK` 28.5s / `Registry loading errors: 0` / id=`zsky262_preset` | —— | R371 |


## 搬出索引行（t15）

| 族 | 结论 | 轮次 |
|---|---|---|
| ★★★★★ **【R372 地形最终版 = R368 那版（用户认可的「v2 前一个版本」）】** 用户澄清「不是还原到这儿啊，是 v2 的前一个版本，那个时候就不错」。⇒ `tools/build_preset_r368.py` 精确复刻 **15 条目 / 6,127 B**：原版 6 个密度函数 + 噪声设置原版**只加 `carvers`** + carver `skylands:cave/canyon` = **26.3 原版完整配置，只改 `y=[170,450]` + `count=uniform(2,14)`** + 维度类型原样(576) + 世界预设 + 标签 + lang。**不含**：岛加厚、`aquifers` 删除、船覆盖（全是 v2/R369 加的，已否决）。验证 `TITLE_SCREEN_OK` 33.0s / 0 registry error | —— | R372 |
| ✅ **【R373 移植第二轮：+1 成功，mods-stable 48 jar】** **`create-sky-village`（1.20.1 Fabric → 26.3）实测 `WORLD_OK`**（`server_started=True/joined=True`，64.3s）。48 jar 标题画面复跑 `TITLE_SCREEN_OK` 25.2s。报告 `docs\port-batch2.md` | —— | R373 |
| ⚠⚠⚠ **【R373 浮岛预设世界每次进都会弹「实验性设置」确认框，脚本点不掉】** 用 `skylands:sky_islands` 预设建的存档，26.3 每次进世界先弹「不支持使用实验性设置的世界」确认；**26.3 是 SDL3 后端，`SetCursorPos+mouse_event` / `PostMessage(WM_LBUTTON*)` / `VK_RETURN` / 删 `level.dat` 的 3 个旧 feature flag 全部无效**。⇒ **自动化进世界验收必须换「原版世界」**，或手工建世界；别再靠脚本点这个框。**用户自己点一下即可正常进** | —— | R373 |
| ★★★★ **【R373 分组 3 大发现：NeoForge jar 不需要 remap】** 扫原包 112 个 NeoForge jar：**intermediary 引用几乎全为 0**（只有 BadOptimizations 33）⇒ NeoForge 是编译在 Mojang 官方名上的，**第一道门是 loader API 不是映射**（与 1.21.x Fabric jar 相反）。**`nf_ref=0` 的 11 个**（含 0 class 纯数据：Explorify / Geophilic / Structory 系 / gadgets-and-gizmos）= 唯一「换入口就能上」的一批；**`nf_cl>100` 的 12 个**（create 系 / sophisticated 系 / balm / blueprint / architectury）每个估 **1~3 周** | —— | R373 |


## 搬出索引行（t16）

| 族 | 结论 | 轮次 |
|---|---|---|
| ★★★★ **【R373 分组 2：1.20.1 那 11 个的 A/B/C/D 实测】** `create-sky-village` **0/0/0/0** ✅；`interiors` 3/62/26/2；`create-framed` 3/56/67/1；`escalated` 5/130/49/10；`design-n-decor` 7/163/101/5；`slice-and-dice` 10/87/49/9；`create-jetpack` 11/25/12/0；`ore-excavation` 15/199/66/16；`createaddition` 16/237/114/12；`railways-navigator` 19/219/74/17；`copycats` 27/344/158/23（最重）。**跨 mod 共性**：它们认 `com.simibubi.create`，本包是 **`com.zurrtum.create` 6.0.9** ⇒ **包名 + API 双迁移** | —— | R373 |
| ★★★★ **【R373 26.3 数据包 schema 又三层（`when-dungeons-arise` 逐层踩出）】** ① **实体谓词**：`"predicate":{"type":..}` → **`entity_type`**（26.3 EntityPredicate 变子谓词注册表 map，用 javap `EntitySubPredicates` 拿键名）；② **进度条件**：`conditions.<字段>` 是**数组**→26.3 要单个对象；`icon.item`→`id`；`loot_table`→`loot_tables`；③ **战利品表**：**`functions[]` → 单个 `modifier`**（26.3 原版 1447 表里 `functions` 0 次、`modifier` 403 次），多函数用 `{"type":"minecraft:sequence","functions":[…]}`，tag 条目 `name`→`items` 且要 `#` 前缀。另：`minecraft:chain`→`minecraft:iron_chain`；实体标签里 `minecraft:potion` 不存在。工具 `fix_enchant_121/fix_entity_predicates/fix_loot_121.py` | —— | R373 |
| ⚠ **【R373 accesswidener 与 fabric.mod.json 两坑】** ① AW 头必须是 **`official`** 命名空间（26.3 直接 `ClassTweakerFormatException`），工具 `fix_accesswidener.py`；② 老 mod 依赖 id 写 **`fabric`**，26.3 要 **`fabric-api`**，工具 `fix_fabric_api_dep.py` | —— | R373 |


## 搬出索引行（t17）

| 族 | 结论 | 轮次 |
|---|---|---|
| 🎉 **【R374 移植第三轮：+2 成功，mods-stable 49 jar】** **`create-sky-village`** + **`when-dungeons-arise`（DungeonsArise）** 双双进世界通过。**`mods-stable`(49) 的标题 `TITLE_SCREEN_OK` 25.3s 与进世界 `WORLD_OK` 都在交付物本体上复跑过**。新增 `create_sky_village-0.0.29I-26.3.jar` / `DungeonsArise-2.1.68-26.3.jar` | —— | R374 |
| ★★★★★ **【R374 绕开「实验性设置」确认框的正确做法】** 不要去点那个框（SDL3 不认伪造输入）。**拿一个不是用浮岛预设建的存档当验收世界**：`work/run26/watch/saves/New World (1)`（`Enabled` 只有 vanilla/aeronautics/create/fabric-convention-tags-v2/sable/sky262recipes，**不弹框**），复制到 `stag1/saves/` 后 `--quickPlaySingleplayer` 直接进。⚠ 不能用空壳存档（`Overworld settings missing`），也不能用引用了已卸载 mod 结构的存档 | —— | R374 |
| ★★★ **【R374 DA 最后三层的修法（都在 `tools/fix_loot_121.py`）】** ① **`exploration_map.destination`**：26.3 只收「结构 tag（要 `#`）」或「结构 id 列表」，DA 两种混用 ⇒ 转换器先收集 jar 里**真实存在的** tag 与结构 id，能对上 tag 就加 `#`，否则用 `["<id>"]`；② **不带命名空间的条目类型**（`"type":"item"` / `"tag"`）：按 `== "minecraft:item"` 判断会**静默漏改**（踩过：`minecraft:chain` 没换掉）⇒ 必须先归一化；③ 26.3 删了通用 `minecraft:music_discs` tag ⇒ 换 `creeper_drop_music_discs`；`set_components` 旧写法 `custom_model_data:<int>`→`{"floats":[int]}`、`dyed_color:{"rgb":n}`→`n` | —— | R374 |
| ⚠ **【R374 两处降级（必须写进最终交付说明）】** ① `minecraft:potion` 从 DA 的诱捕豁免实体 tag 里**删掉**（26.3 无此 id）；② 唱片集合从 `minecraft:music_discs` 换成 `creeper_drop_music_discs` ⇒ **可获得的唱片变少**。详见 `docs/port-batch2.md` | —— | R374 |


## 搬出索引行（t18）

| 族 | 结论 | 轮次 |
|---|---|---|
| ⚠ **【R375 `cultural-delights` 的定位（别重查）】** `mods-stable(49) + FarmersDelight-26.3-3.6.28`（**只加 FD**）⇒ ✅ `WORLD_OK` ⇒ **FD 26.3 本身没问题、依赖可满足**。再叠加 `cd-v4` ⇒ ❌ **启动期静默挂死**：日志停在 `[Render thread/INFO]: Sable loaded!`，**无异常、无 crash-report、无 registry 报错**，200s 超时被杀。上一轮的 `class_2248` 已被「以 mods-stable 为基线 + `launch.py` 权威同步」排除（**不是旧 jar 残留**）。**下一步**：`-Xlog:class+load`（写文件）/ `jstack` 看卡在哪个 `<clinit>`；若是 4 个作物 `configured_feature` 则逐类型转，**若卡在 Sable 相关类就先放弃**（mixin 冲突，不值得耗）。**每个静默挂死最多 2 次尝试就转下一个** | —— | R375 |
| ⏳ **【R375 `ends-delight` 已备未测】** `port\_fixed\ed-v4.jar` 已生成；测法同 `staging-fd`（需同时加 FarmersDelight 26.3） | —— | R375 |
| ★★★★ **【R375 下一批：11 个 `nf_ref=0` 的 NeoForge mod 是快速提量机会】** 上轮扫描结论：原包 112 个 NeoForge jar 里 **`nf_ref=0` 的 11 个**（`Explorify` / `Geophilic` / `Structory` 系 / `gadgets-and-gizmos` 等）**不需要 remap、不需要改 API，只换入口**。**手法**：纯数据 mod（0 class）最简单 —— 只留 `fabric.mod.json` + `data/` + `assets/`，**剥掉所有 class 与内嵌库**，当数据包 jar 用；其余用 `fix_accesswidener.py`（AW 头要 official）+ `fix_fabric_api_dep.py`（`fabric`→`fabric-api`）+ `widen_mc_constraint.py` + `lenient_mixins.py` + `convert_121_data.py`。**每个单独 staging 测**，标题+进世界都过才 promote；**每 promote 一个就复跑一次 `mods-stable`** | —— | R375 |
| ★★★★★ **【R376 remap 必踩的 `Signature` 属性坑（通用，所有 1.21.x mod 都用得上）】** `remap_intermediary.py` **只改 Class / NameAndType / 成员引用**，**不碰 `Signature` 属性、注解、调试属性**。残留形如 `Signature: Ljava/util/function/Supplier<Lnet/minecraft/class_2248;>;` ⇒ 运行期 `NoClassDefFoundError: class_2248`，而且**在普通常量池扫描里看不到**（所以会误判成「0 处 class_ 引用」）。**修法：`tools/sweep_utf8_intermediary.py`** —— 常量池**索引不变**、只换 Utf8 值（最安全的收尾清扫）。**⇒ 以后任何 remap 之后都必须跑一次这个清扫，再判「干净」** | —— | R376 |
| ★★★★★ **【R376 26.3 要求方块 `Properties` 必须带 id】** `NoClassDefFoundError` 之后暴露的下一个坎：`ExceptionInInitializerError → NullPointerException: Block id not set`，这句出自 **26.3 自己的** `net/minecraft/world/level/block/state/BlockBehaviour$Properties`。⇒ 1.21.x 的 FD 附属用 FD 注册辅助建块时**没设 id** ⇒ 每处方块构造都要补 `Properties.setId(...)` 或改走 `Registry.register`。**这是源码级移植的量，不是字节码补丁能解决的**。`cultural-delights` / `ends-delight` 按**暂缓**处理 | —— | R376 |


## 搬出索引行（t19）

| 族 | 结论 | 轮次 |
|---|---|---|
| ⚠ **【R376 纠正：cd/ed 之前根本没被 remap 过】** 扫 `_fixed\cd-v4.jar` / `ed-v4.jar`：**24 / 38 个 class 里仍有 `net/minecraft/class_xxxx`**。上一轮「0 处 class_ 引用」的结论是在**别的产物**（v3 = 只 widen+lenient）上得到的。**⇒ 判「干净」必须扫实际要交付的那个 jar** | —— | R376 |
| ✅ **【R376 新工具两件（通用）】** ① `tools/sweep_utf8_intermediary.py` —— remap 后的**收尾清扫**（Signature/注解里的类名）；② `tools/neoforge_to_fabric.py` —— **纯数据 NeoForge jar → Fabric mod jar**（读 `neoforge.mods.toml` 生成 `fabric.mod.json`，只留 `data/` + `assets/`） | —— | R376 |
| 🎉 **【R377 移植第四批：+5 成功，mods-stable 54 jar】** 新增（全部实测进世界 `WORLD_OK`）：`no-void-structures`(34.1s) / `create-hangars`(36.2s) / `MoogsSoaringStructures`(34.3s) / `SkyVillages`(NeoForge 版重做, 36.2s) / `rabbit_pathfinding_fix`（7 class + mixin，`--keep all` + 手写 mixin 配置 + `lenient_mixins`）。54 jar 的标题与进世界都在交付物本体上复跑过 | —— | R377 |
| ★★★★★ **【R377 `spawn_overrides` 的 `minCount/maxCount` → `count`（报错极具迷惑性）】** 结构 JSON 里 `spawn_overrides` 的 `minCount`/`maxCount` 在 26.3 要写成 **`count`**；不改会让**整批原版结构**变成 `Unbound values`（覆盖失败 ⇒ 原版条目失去绑定）。**看到「一大批原版结构 Unbound」先查这个，不要以为是结构池坏了** | —— | R377 |
| ★★★★ **【R377 IntProvider 简写要补 `type`】** 旧写法 `{"min":a,"max":b}` 在 26.3 报 **`No key type`** ⇒ 必须补 `{"type":"minecraft:uniform","min_inclusive":a,"max_inclusive":b}`。`Structory_Towers` 修了 **483 处** | —— | R377 |


## 搬出索引行（t20）

| 族 | 结论 | 轮次 |
|---|---|---|
| ★★★★★ **【R377 验收世界每次都要用全新副本（吃掉 20 分钟的大坑）】** 同一个存档被试过「带新 mod 的加载」一次后会被**标成实验性**，之后每次加载都弹确认框、日志停在 `Loaded N advancements` ⇒ **表现成 `FAIL_TIMEOUT`（不是崩溃）**。**⇒ 批量脚本必须每测前重拷 `watch/saves/New World (1)`**（`work\run26\port\_batch_g3.py` 里的 `fresh_world()`） | —— | R377 |
| ⏳ **【R377 剩余最大一坨：`configured_feature` 逐类型转换器】** 26.3 的 `configured_feature` 按 feature type 分了新的字段结构，`strayed-fates` 305 / `natures-spirit` 2,839 / `imst` 324 个 JSON 都卡这一层。**写一个逐类型转换器是下一步主线**。另：`Structory_Towers` 差结构/模板池那层；`sablephysicscompat`（0 class / 50 data JSON）静默超时待查 | —— | R377 |
| 🎉 **【R378 第五批：+4 成功，mods-stable 58 jar】** 新增（全 `WORLD_OK` + `TITLE_SCREEN_OK`，交付 jar 与测过的 SHA256 逐字节一致）：`strayed-fates-forsaken` 36.2s/24.0s、`imst` 36.2s/24.8s、`Structory_Towers` 36.2s/26.0s、`sablephysicscompat` 36.2s/25.1s。58 jar 整体再测 TITLE 25.6s + WORLD_OK 36.2s。核心产出 **`tools/convert_features_121.py`** + `tools/feature_schema_263.py`（从 26.3.jar 反查 57 个 type 字段全表） | —— | R378 |
| ★★★★★ **【R378 `configured_feature` 的 26.3 真相（全部实测）】** ① 目录 `worldgen/configured_feature` → **`worldgen/feature`**（旧目录不读）；② **`config` 扁平化**（每个 feature 类本身就是 record 并实现 Feature）；③ **删了 4 个 type**：`random_patch` / `flower` / `no_bonemeal_flower` / `forest_rock` —— patch 类的 `tries`/`xz_spread`/`y_spread` **搬进 placed_feature 的 placement**（`count` + `offset` 的 x/y/z）；`forest_rock` → **`block_blob`** + 必填 `can_place_on`；④ `tree`：`dirt_provider`+`force_dirt` → **必填 `below_trunk_provider`**（默认 `minecraft:soil_beneath_tree`）；⑤ `lake`：新增 3 个**必填** predicate（`can_place_feature` / `can_replace_with_air_or_fluid` / `can_replace_with_barrier`）；⑥ state provider 全表改名，**`simple_state_provider` 塌成裸方块状态**；⑦ **biome 的 `carvers` 从 `{air:[…],liquid:[…]}` 变成扁平数组**。57 个 type 字段全表见 `docs/port-batch3.md` §3（新 mod 撞 type 时先查这张表） | —— | R378 |
| ★★★★ **【R378 纠错两条（会误导下一轮）】** ① **`Structory_Towers` 不是结构/模板池坏的** —— 26.1.2 vs 26.3 的 structure/template_pool 字段集合与 `step`/`element_type`/`processor_type` 取值**完全一致**；真因是 4 张 `potions/*` loot 表用了 26.3 **已删的 `minecraft:hide_additional_tooltip` 组件**（→ 换 `tooltip_display`）；② **`sablephysicscompat` 的三条真因**：`neoforge_to_fabric` 没剥 TOML **行尾注释** ⇒ id 变成 `"sablephysicscompat" #mandatory`；tag JSON 有 `//` 注释 + 尾逗号（26.3 严格 JSON）；`physics_block_properties` 在 26.3 是**单对象不是数组**。上一轮的 `FAIL_TIMEOUT` **复现不出**（全新副本第一次就 36.2s 进世界）⇒ 就是「验收世界被标实验性」那个坑 | —— | R378 |


## 搬出索引行（t21）

| 族 | 结论 | 轮次 |
|---|---|---|
| ⚠ **【R378 `natures_spirit` 只能 Java 移植（数据救不了）】** 数据层已全转（176 feature / 220 placed / 51 biome / 47 biome carvers），**（R379 已纠正：真身是 Fabric 1.21.1 / 176 class，自定义注册表是 4 个）**，注册了**自定义 `feature_type` / `foliage_placer_type` / `trunk_placer_type` / `tree_decorator_type`**（实测 `Unknown registry key … natures_spirit:alluaudia_feature`）⇒ 数据转换无解 | —— | R378 |
| ✅ **【R378 顺手修了 4 个工具 bug】** `convert_121_data`（`spawn_overrides` 的 count 要 `min_inclusive`/`max_inclusive` 不是 `min`/`max`）、`neoforge_to_fabric`（TOML 行尾注释）、`fix_loot_121`（`hide_additional_tooltip` → `tooltip_display`）、`feature_schema_263.py`（新增，机械反查 57 个 type） | —— | R378 |
| 🎉 **【R379 第六批：+1，mods-stable 59 jar】** 新增 `structures-1.2-26.3.jar`（More Structures 热气球结构，纯数据包）。`WORLD_OK 36.2s`（全新存档副本）+ promote 后 `TITLE_SCREEN_OK 25.7s`，日志 `Found new data pack structures` 无 parse/registry 报错 | —— | R379 |
| ★★★★★ **【R379 `remap_intermediary.py` 的成员改名从来没生效过 —— 这推翻了「1.20.1 那批卡在 API 难度」的判断】** 实测 `interiors` remap 前后 `class_=650 method_=128 field_=56` **一条没变**。**根因**：`_maps\i20n-ns1.tiny` 的 **class 列是 intermediary、desc 列却是混淆空间**（`m (Ldde;…) method_11657 setValue`），工具按 `(owner, name, desc)` 三元组查 ⇒ **desc 永远 miss**。**`i21n-ns1.tiny` 的 desc 才是 intermediary 空间，1.20.1 应该用那个。****⇒ 下一轮别再去修这个工具，直接吃 `est_gap_263.py` 的输出** | —— | R379 |


## 搬出索引行（t22）

| 族 | 结论 | 轮次 |
|---|---|---|
| ★★★★★ **【R379 缺口量化工具 `tools/est_gap_263.py`（按 `(owner, 翻译后 desc)` 判，先走 name-only 表）】** **`interiors`**：150 条 MC 引用 = 32 已合法 + **118 可全自动** + **26 需人工**（其中 8 条是 `Direction.ordinal()` 误报 ⇒ **真实 18 条**）；Create 侧 32 个类里 **27 个前缀替换即命中**（**正确拼写是 `com/simibubi/create`→`com/zurrtum/create`；写成 simibury 一条都换不到**），只有 4 个要换包（`ItemDescription`→`client/foundation/item`、`VecHelper`→`catnip/math`、`AllTags`→`AllItemTags`、`CreateRegistrate/TagGen`→`foundation/data`）+ `CreateBuildInfo` 已消失。**Registrate 26.3 垫片真实存在**（在 aeronautics jar 里），只差把 `NonNullFunction/Consumer/UnaryOperator/BiConsumer` 映射到 `java.util.function.*`。**⇒ `interiors` 从「黑洞」降级为 ≈2–2.5 人日的有界工程**；**`create-framed`** 54 条需人工 ⇒ ≈3 人日，排后 | —— | R379 |
| ⚠ **【R379 `natures_spirit` 结论：不要开工；真身是 Fabric 1.21.1 / 176 class】** 实测不是 202 class 的 NeoForge 版；`terrablender` 只是 `suggests` 不是硬依赖。但**自定义注册表是 4 个不是 3 个**（多一个 `trunk_placer_type`），要动 **43 个 codec 扩展类**（Feature 12 / FoliagePlacer 11 / TrunkPlacer 13 / TreeDecorator 7）+ **564 条** MC 符号（A315/C191/D43/B15）⇒ **≈8–12 人日**。建议只做「12 个 `feature_type` + 对应数据子集」的最小切片 | —— | R379 |
| ✅ **【R379 `nf_refs=0` 那批已清完，别再扫】** `_orig_scan.json` 里实际是 **19 个**（不是 11）。其中 14 个已在 `mods-stable`；2 个不是内容 mod（`create-aeronautics-bundled` 是 bundle、`kotlinforforge` 是 loader 库）；**只剩 2 个是 Java mod**：`gadgets-and-gizmos-bundled`（内嵌 `createthrusters` 34.6MB + `gadgetsngizmos` 2.7MB 两个真 Create 附属）、`FTBQuestsOptimizer`（依赖本包没有的 FTB Quests，**不可做**） | —— | R379 |
| 🎉🎉🎉 **【R380 `interiors` 完整移植成功，mods-stable 60 jar】** 首个 **1.20.1 Create 附属**打通：`WORLD_OK 34.0s`（`logged in with entity id 13` + `Loaded 2085 advancements`）、`TITLE_SCREEN_OK` 24.9s/25.3s、`Registry loading errors: 0`、`Mixin apply failed: 0`、模型 `Missing textures: 0`。**无降级保留**：方块/物品/实体注册、**136 条配方**、55 战利品表、标签、创造栏、坐下/移动行为。报告 `docs/port-interiors.md`；源码 `work/run26/port/g6/interiors/src27/`；一键重建 `work/run26/port/g6/_all.py` | —— | R380 |
| ★★★★★ **【R380 方法论转变：不再改字节码，改成「反编译→改源码→用 26.3 真 API 重新 javac」】** 理由：`est_gap_263` 那 26 条「人工」**没有一条是纯改名**（`fallOn` F→D、`CompoundTag.getInt` Optional 化、`ItemStack.is(Item)` / `Entity.getCustomData` / `DyeItem.getDyeColor` 消失、`SeatBlock` 构造器换序、`use`→`useItemOn`、record 组件改名），**改字节码要动栈帧；改源码让编译器兜底**，实际一个会话做完。**流程**：CFR 0.152 反编译 23 class → 16 java → 用 i21n 表机械改名（8,254 类 / 76,563 成员）→ 人工修语义 → `javac --release 21`（classpath = 26.3.jar + 全部 libraries + create-fly + aeronautics(registrate 垫片) + fabric-api 42 子模块）→ 22 class 与原 assets/data 重打包 | —— | R380 |


## 搬出索引行（t23）

| 族 | 结论 | 轮次 |
|---|---|---|
| ★★★★★ **【R380 三个「不报编译错但会让世界加载失败」的致命卡点】** ① **registrate 垫片的 `AbstractRegistrate.register()` 是空实现**（javap `Code: 0: return`）—— `.register()` 只把 Runnable 塞进 `PENDING`，**必须显式调 `AbstractRegistrate.flush()`**。现象：53 个块只有 `queue block`、没有 `create block`，**标题照过、进世界才炸成「标签全部 missing references」**。⇒ 任何用这个 registrate 垫片的新 mod 都会踩。② **`CreativeModeTab$Output` 在 26.3 变成 protected 嵌套类型**（javap -v InnerClasses 实锤）⇒ 源码无法命名 ⇒ 标签页建空；用 Fabric `CreativeModeTabEvents.modifyOutputEvent(TAB_KEY)` 填（回调参数 `FabricCreativeModeTabOutput` 是 public）。`AllCreativeModeTabs$TabInfo` 也已消失。③ **26.3 物品模型入口是 `assets/<ns>/items/<id>.json`** —— 不生成它物品不可见、进不了创造栏（从旧 `models/item` 批量生成）| —— | R380 |


## 搬出索引行（t24）

| 族 | 结论 | 轮次 |
|---|---|---|
| ★★★★ **【R380 1.20.1→26.3 数据层实测要点（866 条目）】** 目录改名：`recipes`→`recipe` / `loot_tables`→`loot_table` / `advancements`→`advancement` / `tags/{blocks,items}`→`{block,item}`；**配方**：Ingredient→裸字符串、`result.item`→`result.id`、**`category` 是 `building` 不是 `building_blocks`（方向易搞反）**；**进度表**：`recipe_unlocked` 的 `recipe`→**`recipes: [..]`（复数+列表）**、`requirements` 必须与 `criteria` **完全一致**；`create:block/belt_offset` 贴图在 Create 26.3 已删 ⇒ 换 `interiors:block/chair/side_top_kelp`。三重校验（对全部已装 jar 的 `assets/*/items` + `tags/item` 反查）：**136 条配方全保留、0 丢弃** | —— | R380 |
| 🎉🎉🎉 **【R381 `create-framed` 打通，mods-stable 61 jar】** 第二个 1.20.1 Create 附属：`TITLE_SCREEN_OK 23.7s` + `WORLD_OK 36.0s`（`entity id 13` / `Loaded 2085 advancements`）。**`Registry errors 0` / blockstate 异常 0 / mixin 失败 0 / 模型贴图缺失 0**。25 class→24；**313 条配方 0 丢弃**、227 战利品表、251 标签、303 物品、249 方块全部真注册。一键重建 `work/run26/port/g7/_all.py`；报告 `docs/port-framed.md` | —— | R381 |
| ★★★★★ **【R381 registrate 垫片有「一整批 builder 方法是空实现」（比 `register()` 空更狠）】** javap 实锤（aeronautics 里的 shim）：`AbstractBuilder.transform` / `onRegister` / `onRegisterAfter` / `lang` **全是 `return self()`**；`CreateRegistrate.connectedTextures/blockModel/itemModel` 返回空 consumer；`setCreativeTab` 空方法。**后果（编译期完全不报错）**：`.transform(slidingDoor()).simpleItem()` 里的 `simpleItem()` 从不执行 ⇒ **17 个门的物品没注册** ⇒ 标题照过、**进世界才炸成 `c:dyed/*` 标签 missing references**；`.onRegister(...)` 的门行为与 CT 连接纹理也从不注册。**修法：一切注册动作必须写在 `.register()` 之后显式调用**（如 `MovementBehaviour.REGISTRY.register(...)`）| —— | R381 |
| ★★★★ **【R381 数据层新增实测要点（interiors 那轮没覆盖）】** `create:deploying` / `create:item_application`：`ingredients:[a,b]` → **`target:a` + `ingredient:b`**；`create:splashing`：`ingredients:[a]` → **单数 `ingredient:a`**；熔炉 `category` 只认 `food/blocks/misc`——**不能写 `building`**（会 `Unknown element name:building`）；战利品表的 **`minecraft:block_state_property` 在 26.3 已删除** ⇒ 门桌改原版形状（`match_block{half:lower}`）；滑动门的 **`visible=` 属性在 26.3 不存在** ⇒ 变体解析失败，须剥离并去重；进度表 `display.icon` 要 `{id:...}`、`inventory_changed.items` 要 **`[{"items":"x"}]`**（ItemPredicate 对象列表）；id 改名 `c:string`→`c:strings`、`c:colorless_glass`→`c:glass_blocks/colorless`、`create:copper_nugget`→`minecraft:copper_nugget`。**校验器必须递归 fabric-api 的 `META-INF/jars/*.jar`**，否则 `c:strings` 误判缺失、误杀 34 条配方 | —— | R381 |
| ⚠ **【R381 附加 4 个 mod 的量化卡点（首次 javac 实测）】** `slice-and-dice` 44 java / **65 错**，几乎全是 **Kotlin 编译产物**的 CFR 残影（`void $this$mapValues$iv;`、匿名类 `createRecipeType.type.1`）⇒ 要手写重推 6 个 Kotlin 类；**下一个最值得做**；`escalated` 修完伪声明后 **542 错**（`StateHolder#setValue` 24 / Level 可见性 22 / ponder 包搬迁 7 / ModConfig 8 / flywheel `Instance→OrientedInstance` 6）；`design-n-decor` **1869 错**（旧 Flywheel `com.jozufozu.flywheel` + porting_lib datagen 链 + `RegistryEntry→BlockEntry`）；`create-jetpack` **纯 Kotlin**（`Intrinsics`/`CollectionsKt`/解构残影，构造器成乱码）+ JiJ 内嵌 `flightlib-2.2.3`(1.20.1) 也要移植。**排序：slice-and-dice > escalated > design-n-decor > create-jetpack** | —— | R381 |
| ★★★★★ **【R382 精确剩余清单：46 / 110 已覆盖，64 未覆盖（不再是估算）】** 新工具 `tools/diff_pack.py`：**从原包每个 jar 里读真实 mod id**（Fabric: `fabric.mod.json`；NeoForge: `META-INF/neoforge.mods.toml`），再与已装 jar 的 mod id 取差集。**踩了三个匹配 bug，以后别重犯**：① **不能用 namespace 兜底** —— `minecraft` / `create` 是公共 ns，几乎所有 jar 都有 ⇒ 全误判成已覆盖；② **NeoForge TOML 的 `[[dependencies]]` 段也有 `modId="minecraft"`** ⇒ 必须只取 `[[dependencies` **之前**的 `modId`；③ id 比对要**去掉 `-` 和 `_`** 再比（`cloth_config` vs `cloth-config`）。**剩余 64 个分类**：Create 附属 ~22 / Aeronautics 附加 ~5 / Farmer's Delight 系食物 ~8 / 库 ~10 / FTB 链 4 / Sophisticated 3 / 结构 ~4 / Sable 兼容 ~4 / 其他 ~4 | —— | R382 |


## 搬出索引行（t25）

| 族 | 结论 | 轮次 |
|---|---|---|
| 🎉 **【R383 FD 系 +4，mods-stable 65 jar】** 新增 `FarmersDelight-26.3-3.6.28+refabricated`（官方） / `chefsdelight-1.0.6-26.3` / `corndelight-1.0.0-26.3` / `ends_delight-2.6-26.3`。**65 jar 交付物本体再跑进世界通过**：`entity id 5` / `Loaded 2343 advancements` / `Registry errors 0` / mixin 失败 0 / `Loading 144 mods`。降级见 `docs/port-delight.md` §4 | —— | R383 |
| ★★★★★ **【R383 26.3 硬要求：方块/物品的 `Properties` 必须在 `new Block()/new Item()` **之前**带 id】** 不只是方块 —— **`Item` 构造器会调 `itemIdOrThrow()` 并拿它当 `DataComponentInitializers` 的 key**，**占位 id 会把物品模型/组件带歪 ⇒ 「先注册后补 id」整体不可行**。**定下的修法**：`Reg.pb/pi` 从 **ThreadLocal 名字栈**补 id + 注册助手 push/pop（`work/run26/port/g8/_idfix.py`，可复用） | —— | R383 |
| ★★★★★ **【R383 用「Fabric 版 + 从 26.2 反编译重编」比 1.21.1 移植便宜一个数量级】** 原包 6 个 FD 附属**全是 NeoForge 版**，但其中 **4 个在 Modrinth 有 Fabric 构建**，`chefsdelight` 甚至有 **26.2 Fabric 官方构建**。**⇒ 动手前先查「同 mod 有没有更接近 26.3 的 Fabric 构建」，别从 1.21.1 硬啃** | —— | R383 |


## 搬出索引行（t26）

| 族 | 结论 | 轮次 |
|---|---|---|
| ★★★★ **【R383 两个会让「编得过但运行期炸」的流水线 bug】** ① **`g7/cp_join.txt` 里混着 1.21.1 的 client jar**（`libraries/net/minecraft/client/1.21.1-*`）⇒ javac 把 26.3 已删的类解析到 1.21.1 上，**编得过、运行期 `NoClassDefFoundError`**（corn 的 `ItemNameBlockItem` 实测炸过）；② **`g7/map.json` 是 intermediary→1.21.1 名**（1727/8254 在 26.3 不存在），且**内类 key 是 `$` 形式而 CFR 输出 `.` 形式** ⇒ 会产出 `BlockBehaviour.LootItemRandomChanceWithEnchantedBonusCondition1` 这种垃圾。**新流水线**：`g8/_rewrite26.py` + 自动推导的 `map_121_263.json`（**612 条**搬迁，`_mkmap.py`）+ `g8/_javac8.py`（显式剔除 1.21.1 client） | —— | R383 |
| ★★★★ **【R383 数据层再补五条 + Fabric API 26.3 删除项】** 战利品条件 **`conditions:[]` → 单数 `condition`** 且条件对象用 **`type`** 键；`block_state_property` 已删；**Ingredient 的 tag 是 `"#tag"` 裸串**（对象形态报 `No key fabric:type`），多候选要 `{"fabric:type":"fabric:any","ingredients":[...]}`；worldgen 目录 **`configured_feature/` → `feature/`**，FD 的 `wild_crop` → **`in_order`**；`c:` 约定标签改名（`c:foods/vegetables`→`c:foods/vegetable` 等）；渲染层改用方块模型 **`render_type`**。**Fabric API 26.3 删了 `FabricItemGroup` / `BlockRenderLayerMap` / `CompostingChanceRegistry` / `FuelRegistry`** | —— | R383 |
| ⚠ **【R383 `culturaldelights` 卡在「26.3 把树整套重做」，不是改名能解决的】** 编译到 40 错：**`ConfiguredFeature` 类整个不存在**、`TreeGrower` 变 **final 且无公开构造器**、`SaplingBlock` 构造器 **protected**、`LeavesBlock` 要多一个 `AmbientLeavesBlockSoundPlayer`、`DirectionProperty` / `StrippableBlockRegistry` / `TradeOfferHelper` **全删**。`mynethersdelight`（97 类）同形态但更大；`minersdelight` / `abnormals_delight` Modrinth **只有 NeoForge/Forge 构建**，要先做 `net.neoforged` 垫片 | —— | R383 |


## 搬出索引行（t27）

| 族 | 结论 | 轮次 |
|---|---|---|
| ★★★★★ **【R384 `lang_audit.py` 有假阴性 bug —— 之前几次「汉化 100%」是假的】** 旧版把 `en_us` 与 `zh_cn` 的解析放在**同一个 try** 里，**任一失败就 `continue` 跳过整个 namespace** ⇒ **损坏的 `zh_cn.json` 会让它从报告里彻底消失**，表现为「100% 覆盖」。实测踩到：`createframed` 的 `zh_cn.json` 有 `// Translator's note:` 行注释（JSON 不允许），`ends_delight` 带 **UTF-8 BOM** ⇒ 两个 namespace 共 **386 条缺口被隐藏**（真覆盖 96.0%，不是 100%）。**修法**：en/zh **独立解析**；zh 解析失败时记「文件损坏」并单独列出；**看到 100% 必须怀疑工具** | —— | R384 |
| ✅ **【R384 两个损坏 lang 文件的成因与修法（`tools/fix_broken_lang.py`）】** ① **行注释**：`//` 必须**在字符串感知的前提下**剥（不能简单按 `//` 切，译文里可能含 `//`）；② **UTF-8 BOM**：`EF BB BF` 开头 ⇒ 用 `utf-8-sig` 解码。**改前备份 `.bak-langfix`，改后必须重新 `json.loads` 验证** | —— | R384 |
| 🎉 **【R384 汉化真 100%（65 jar）】** 修完两个坏文件 + 补齐最后 40 条（farmersdelight 32 / chefsdelight 4 / createframed 3 / corndelight 1）⇒ `lang_audit.py` 实测 **en 9,772 / zh 9,996 / 缺 0**，39 个 namespace 全部达标，无损坏文件 | —— | R384 |
| ⚠ **【R385 g9 零进展（仍 65 jar），但三条订正必须记住】** ① **`create-enchantment-industry` 只有 26.1.2 一个 26.x 世代**（2.5.1/2.5.2/-b/-c），**全部要求 `create >=6.0.9-4` 且强依赖 `create-dragons-plus`** ⇒ 「改用更低版本」这条路不存在（再往下只有 1.21.11/1.20.1）；② **`aeroworks` 根本没有 Fabric 构建**（`P26k79kP` 12 个版本 loaders 全是 `neoforge`）⇒ 之前归「高优先」是错的，应归「需 NeoForge 垫片」；③ 原包 114 个 jar 的真实 project id 已全部反查出来（`work/run26/port/g9/_pack/modrinth.index.json`，含 sha1+URL） | —— | R385 |
| ★★★★★ **【R385 关键结论：EI/DP 的卡点不是 Create 版本，是 MC 26.1.2→26.3】** `FlowableFluid$Still/Flowing` 确认在 6.0.9-2 里**不存在**（6.0.9-2 里叫 `FluidEntry$Still/$Flowing`，构造器 private）—— 但 `_scanrefs.py` 实测 **EI/DP 对 Create 的类级缺口只有这 2 个类**（已重建 `g9/_shim/fluid-compat.jar`，2 类，编译 0 错）。真正卡住的是它们是 **26.1.2 世代源码**（既不是 intermediary、也不是 1.21.1）⇒ **g8 的 `map_121_263.json` 帮不上忙**，必须对着 26.3.jar 逐族改：**`CriterionTrigger.Listener` 整套被删**（只能降级 code-only）、`RecipeAccess` 只剩 propertySet/stonecutterRecipes、`RecipeMap.create` 改吃 `HolderLookup`、`EntityType.SHEEP`→`EntityTypes.SHEEP`、颜色方块→`ColorCollection`、`BlockEntityRenderers.register` 变 private、Fabric 附件 `Entity` 不再声明 `AttachmentTarget`、`ValueOutput.store`/`PoseStack.mulPose`/`placeItemBackInInventory` 签名全变。**进度：DP 391→87、EI 522→202**（删两边 JEI 集成 + 修 136 处 CFR 滥加 `(Object)` 强转 + 4 处嵌套类型前向引用 + 包搬迁 + 战利品 `ConstantValue`→`Holder.direct`）| —— | R385 |


## 搬出索引行（t28）

| 族 | 结论 | 轮次 |
|---|---|---|
| ★★★★ **【R385 EI+DP 是「成对」移植，且还要 1.5–2 个完整轮次】** 15 个 API 族、400+ 错。**不建议在没有 DP 的情况下单独硬推 EI**（运行时必然缺类）。**下轮最划算的顺序**：先批量改「同名但签名变了」的族（`mulPose` 12 / `store` 18 / `placeItemBackInInventory` 8 / `add(Object[])` 6），再逐个清 symbol。**可复用资产**（`work/run26/port/g9/`）：`_mr.py`/`_deps.py`（按 project id 查 Modrinth）、`_scanrefs.py`（class 级缺口）、`_javac9.py`+`_jar9.py`、**`_auto_cast.py`（按错误行批量去 CFR 的 `(Object)`，两轮修 136 处，最省力）**、`_errs.py`/`_blocks.py`（错误直方图） | —— | R385 |


## 搬出索引行（t29）

| 族 | 结论 | 轮次 |
|---|---|---|
| 🎉 **【R386 `escalated` 打通，mods-stable 66 jar】** `Create: Escalated 1.2.1`（1.20.1 Fabric）：**javac 0 错 / 56 class**；`WORLD_OK 36.2s`（`entity id 13`，无 `Registry loading errors`）；promote 后 66 jar `TITLE_SCREEN_OK 25.3s`。降级清单一长串（datagen / Ponder / architectury 配置 / **客户端 BER + Flywheel Visual ⇒ 扶梯踏步动画没了，方块仍静态渲染** / 5 个 advancement / SAFE_NBT / setMaxUpStep / 6 张 `minecraft:air` 手栏杆战利品表 / 2 个配方换材料），详见 `docs/port-1201.md` §1.4 | —— | R386 |
| ★★★★★ **【R386 「542 不可信」被证实：之前的 1.20.1 错误数是用坏流水线测的】** `escalated` 的真实错误轨迹：**1268（未换 Create 包名）→ 353（+`_crate_pkg`）→ 107（删 datagen/ponder/config/client-renderer）→ 33 → 1 → 0**。**542 的大头是** ① `com.simibubi.create` **完全没换** ② 内类 `$` vs `.` 的垃圾类名级联。**⇒ 以后看到旧轮次的错误数（542/1869）不要当成工作量依据，必须用 g8 流水线重测** | —— | R386 |
| ★★★★ **【R386 g8 流水线的两个缺口（已补，新增脚本别覆盖）】** ① **`_rewrite26.py` 不做 Create 包名迁移** ⇒ 每个 Create 附属必须再跑 **`g8/_crate_pkg.py`**（**按 create jar 的类索引 resolve**，因为 `net.createmod.catnip` 的 common/client 划分**不能按名字推**）；② **`@ExpectPlatform` 桥接要单独一个 pass**：CFR 把参数名丢成 `void varK_N;`（K = 参数下标）⇒ 新写 **`g8/_ep_bridge.py`**（copycats 一次修 13 个） | —— | R386 |


## 搬出索引行（t30）

| 族 | 结论 | 轮次 |
|---|---|---|
| ⚠ **【R386 `copycats` 未通（1342→1294 错）：客户端模型系统是它的核心，降级就没意义】** 314 java，语法层已清零。三类卡点：① registrate 垫片 **builder 泛型不符**（66 个 `wrong number of type arguments` + 43 个 `customItemModel`）；② **客户端模型系统**（`CopycatModelFabric`/`UniversalMeshEmitter`/`CopycatRenderContextFabric` 直接拼 quad，26.3 renderpearl 全换）⇒ **降级等于 mod 失去意义**；③ config（architectury）+ mixin（refmap 是 1.20.1）+ JEI/EMI。**下轮顺序**：先修通用族（~70 条）→ 删 config/mixin/JEI/EMI/datagen → 最后单开一轮做模型系统 | —— | R386 |
| ★★★★★ **【R386 三个 26.3 数据层硬坑（任何一个都会让「进世界」直接失败）】** ① 战利品表里 `"name": "minecraft:air"` → **`Item must not be minecraft:air`**；② advancement 引用**已删的 `trigger_type`** → **整个 advancement 注册表失败**；③ 配方引用**不存在的 item/tag**（含 `minecraft:chain`→`iron_chain` 改名）→ **整个 recipe 注册表失败**。**⇒ 删数据时要「要么全删干净、要么全修」，不能留半截引用** | —— | R386 |
| ★★★★ **【R387 `create-railways-navigator` 不能当「一个 mod」移植 —— 硬依赖 DragonLib】** 实测（1.20.1 Fabric 版 546 java / 731 class）：**247/546 文件 import `de.mrjulsen.mcdragonlib`**（1374 条 import、107 个不同 FQN：`DLColor`/`TextUtils`/`Rectangle`/`DLGuiGraphics`/`GuiUtils`/`DLGuiComponent`/`DLWindowManager`/`NetworkPacketData`… 整个 GUI 框架 + 网络层 + 工具层）。**`de/mrjulsen` 在 mods-stable 的 66 个 jar 里一个类都没有**；磁盘上只有 `work/run26/port/dragonlib/dragonlib-3.0.29+mc1.21.1-fabric.jar`（1.21.1），**DragonLib 没有 26.3 构建**。DragonLib 单独移植实测 **1271 javac 错**（331 java，客户端 GUI/渲染为主：`MultiBufferSource`/`GuiGraphics`/`BakedModel` 族），与 `escalated` 首编 1268 同量级；两者合并编译**撞 3000 上限**。**⇒ rn 要 2 个完整轮次：先 DragonLib、再 rn 本体。** 产物已保留（`g8/dl2/`、`g8/rn/`），下轮直接接着做、不用重跑 CFR | —— | R387 |
| ★★★★★ **【R388 26.3 的 Create 把整套 `ProcessingRecipe` 框架删了 —— 这影响所有加 Create 配方的附属】** `ProcessingRecipe` / `ProcessingRecipeBuilder` / `ProcessingRecipeSerializer` / `IRecipeTypeInfo` / `SequencedAssemblySubCategoryType` **在 create jar 里 0 命中**。**替代品**：`CreateRecipe<T extends RecipeInput>` / `CreateSingleStackRecipe` / `CreateRollableRecipe<T>` / `CreateSingleStackRollableRecipe`（`ingredient()` + `results(): List<ProcessingOutput>`）；且 **`RecipeSerializer` 变成 record（`MapCodec`+`StreamCodec`）**、**`Recipe.assemble(T)` 不再带 `RegistryAccess`**。⇒ 任何 Create 附属的加工配方都要按这套重写，不是改名能解决 | —— | R388 |


## 搬出索引行（t31）

| 族 | 结论 | 轮次 |
|---|---|---|
| ★★★★ **【R388 `createaddition` 推进：1524 → 477 错，但 0 个 jar 落地】** 轨迹 `1524 → 842（删 compat31/ponder2/mixin3/config2）→ 484（+18 类垫片+删客户端渲染/液体+全局改名）→ 477`。**已完成真实现**：`g8/_ca_shim.py` **18 个垫片类**补 26.3 完全缺失的三个库——`team.reborn.energy`（SIDED 用 26.3 `BlockApiLookup`、事务用 `SnapshotParticipant` 带**回滚**）、`porting_lib.transfer`（`ItemStackHandler` 真槽位+NBT+事务快照+`Storage<ItemVariant>`、`RecipeWrapper`=`RecipeInput`、`CombinedStorage`、`TransferUtil`、`TransactionCallback`→Fabric `addCloseCallback`）、`porting_lib.util`（`LazyRegistrar` 先入队后真注册、`RegistryObject`、`LazyOptional`、`LazySoundType`）+ 4 个 block marker 接口；**入口补 `AbstractRegistrate.flush()`**；**创造页改 26.3 API**（`FabricItemGroup` 已删 ⇒ `CreativeModeTab.builder` + `CreativeModeTabEvents.modifyOutputEvent`）。**剩余**：recipe 包 142 + 其余 335。**估还要 1 个完整轮次**（含 264 data json + 399 assets）。**降级**：液体子系统整体删（26.3 流体 API 全换且垫片无 `fluid()`）、**客户端渲染全删（电线不再画出来，机器仍有静态模型）**、配置写死默认、JEI/REI/EMI/CC/Ponder/mixin 删 | —— | R388 |
| ✅ **【R388 两个新通用脚本】** ① **`g8/_fix_innernew.py`** —— 修 CFR 的 `obj.new Foo.Bar(...)` 非法语法（应为 `obj.new Bar(...)`），dragonlib 一次 7 处，**以后每个 mod 都该跑**；② **`g8/_ca_shim.py`** —— 18 类垫片，**任何用 porting_lib / Team Reborn Energy 的 1.20.x mod 都能复用** | —— | R388 |
| 🎉🎉 **【R389 `ProcessingRecipe` 兼容垫片完成 —— 公共瓶颈已解决】** `work/run26/port/g10/shim/proc-recipe-compat.jar`：**41,459 B / 30 class（15 类型 × 两个命名空间 `com.zurrtum.create.*` + `com.simibubi.create.*`）**，覆盖 **123 公开成员**（11 构造器 + 112 方法）+ 29 字段，**与 create/26.3 类名冲突 0**。**契约测试 17/17 通过**（`assemble` 出 3×iron_ingot、JSON/StreamCodec 往返、`asSerializer()` 真是 `RecipeSerializer` record）。**`createaddition` 的 recipe 包 142 → 0**；总错 477 → **269**（余下全在配方之外）。API 对照表在 `docs/port-procrecipe.md`（26 KB，逐成员标 1:1/换形/无对应/删除） | —— | R389 |
| ★★★★★ **【R389 垫片四条关键技术结论（以后所有 Create 附属都用得上）】** ① **26.3 `RecipeSerializer` 是 final record**（MapCodec+StreamCodec）⇒ 旧 `ProcessingRecipeSerializer` 只能是普通类，注册点加**一次** `.asSerializer()`；② **旧手写 JSON 解析不用重写**：把整个 JSON 对象包成 `MapCodec.assumeMapUnsafe(Codec.PASSTHROUGH.xmap(...))`，上游 `readFromJson/writeToJson` 原样生效（实测往返）；③ **`assemble(T)` 去掉 `RegistryAccess`** ⇒ 垫片做桥：`assemble(T)` → 旧 `assemble(T, RegistryAccess)` → `getResultItem()`（**真实现** `results.get(0).create()`，不是空桩）；④ **`Ingredient` 不允许为空**：`Ingredient.of()` 直接抛 `Ingredients can't be empty`（静态初始化就炸）⇒ 垫片用 `EMPTY_INGREDIENT = Ingredient.of(Items.BARRIER)` 哨兵 | —— | R389 |
| ★★★★ **【R389 「只过标题不能当验证」的又一实证：item data components 在注册表加载期才绑定】** 无头 `Bootstrap.bootStrap()` 之后 **`areComponentsBound()==false`**，此时 `new ItemStack()` 抛 **`Components not bound yet`** ⇒ 单元测试必须手工 `bindComponents()`。⇒ 任何「编译过了/标题过了」都不等于能跑，必须有进世界的实测 | —— | R389 |
| ⚠ **【R389 `createaddition` 剩 269 错，全在配方之外】** `cannot find symbol` 144（其中 ~30 是已删客户端渲染器，删注册行即可）、`CompoundTag→ValueInput/ValueOutput` 14（**存档 API 整段重写**）、registrate 垫片签名 10、`NodeMovementBehaviour→MovementBehaviour` 4、Fabric 网络/API 改名 ~10。**还需 1 个完整轮次**搞编译 + 之后 **264 data json / 399 assets**（配方 json 的 `"item"` 键在 26.3 已改 `"id"`）| —— | R389 |


## 搬出索引行（t32）

| 族 | 结论 | 轮次 |
|---|---|---|
| 🎉🎉🎉 **【R390 `createaddition` 进世界，mods-stable 67 jar】** `WORLD_OK`（34.4s，`Loaded 2343 advancements`，`Registry loading errors: 0`）。**错误轨迹 269 → 250 → 204 → 130 → 67 → 19 → 7 → 1 → 0**（139 class）。产物 `g10/ca/createaddition-1.3.4-26.3.jar`（1.4 MB / 469 资源 / 139 编译类 / 30 垫片类 / 44 物品模型），创造页实测 **44 条**。**已用 mods-stable 本体复跑进世界 = WORLD_OK**，jar SHA-256 与实测一致。报告 `docs/port-createaddition.md` | —— | R390 |
| ★★★★★ **【R390 最贵的一课：一个 tag 引用已删 id，会连锁炸掉别家 data】** `minecraft:mineable/pickaxe` 引用了已删的 `createaddition:liquid_blaze_burner` ⇒ **该 tag 整条加载失败** ⇒ `imst:igloo/main`（硬引用该 tag 的 `processor_list`）解析失败 ⇒ **`Unbound values in registry`** ⇒ **整个注册表失败**，**看起来完全像别的 mod 坏了**（这次差点误判成 imst 的问题）。**⇒ 已加离线校验器 `g10/_tag_inv.py`（扫 26.3 + mods-stable 建真实 tag 清单）+ `g10/_recipe_check.py`（逐条查配方/标签引用）。换整合包内容后必须重跑 `_tag_inv.py`** | —— | R390 |
| ★★★★★ **【R390 公共垫片必须打进 mod jar】** `proc-recipe-compat.jar` 只放在**编译 classpath** 上是不够的——**运行期没人打包它** ⇒ 第一次进世界 `NoClassDefFoundError: ProcessingRecipeRecipeBuilder$ProcessingRecipeFactory`。`g10/_build_ca.py` 现在把 **30 个垫片 class 一起写进 mod jar**。**⇒ 以后任何公共垫片都要随交付 jar 一起打** | —— | R390 |
| ★★★★ **【R390 创造页不能用 `REGISTRATE.getAll(...)`】** 垫片的 `BlockBuilder/ItemBuilder.register()` 直接进 `BuiltInRegistries`、**没走 `doRegister`** ⇒ `BY_REGISTRY` 是空的 ⇒ **创造页空白（物品在、拿不到）**。**改成扫 `BuiltInRegistries.ITEM` 按命名空间筛** | —— | R390 |
| ★★★★ **【R390 另外三条必记】** ① **`fabric.mod.json` 里 Fabric API 的 mod id 是 `fabric-api` 不是 `fabric`**（写 `fabric` → `HARD_DEP_NO_CANDIDATE` 启动即失败）；② **26.3 loot 的第二个坑**：条件对象的键要从 `condition` 改成 **`type`**（不是只把 `conditions` 数组改成单值），另外**池子上的 `name` 在 26.3 是非法键**；③ **`CompoundTag`→`ValueInput/ValueOutput` 用 `CompoundTag.CODEC` 桥**（多一层 `CABE` 子键）⇒ **14 条错一次清零且零功能降级**（存档语义不变）| —— | R390 |


## 搬出索引行（t33）

| 族 | 结论 | 轮次 |
|---|---|---|
| ⚠ **【R390 `createaddition` 的 21 条降级（交付说明要带）】** **配方丢 75 条**（`create:*` 51 条因 26.3 schema 全变且 create jar 内**无样本可对照**整类丢弃；`liquid_burning` 14；IE·Mek 3；tag 引不到的 7）——保留 rolling 15 + charging 23 + 原版合成 28。**特斯拉线圈不能给物品充能**（垫片无 `EnergyStorage.ITEM`）；客户端渲染全删（电线不画）；Flywheel 视觉删；液体子系统整体删；网络层空壳（goggle 实时数值不刷）；环境音删；**动态结构 MovementBehaviour 删**（连接器、PEI、蓄电池不随结构工作）；展示板集成删；列车能量阈值条件删；JEI·REI·EMI·CC·Ponder 删；配置写死默认；SequencedAssembly 支持删；拆机器槽内物品不掉落；旧存档 NBT 迁移路径删 | —— | R390 |
| 🎉 **【R391 小 mod 批次 +3，mods-stable 70 jar】** `passivemobspawn`(38.4s) / `sablejade`(36.2s) / `JadeAddons`(36.2s) 全部进世界；70 jar 本体复验 `WORLD_OK 36.2s` + `TITLE_SCREEN_OK 24.6s`；汉化 **10,129 / 10,357 / 缺 0**。报告 `docs/port-smallmods.md` | —— | R391 |
| ★★★★★ **【R391 「WORLD_OK ≠ 功能生效」的活例子：Jade 静默拒收第三方插件】** **Jade 插件三条硬规则**：① entrypoint 键是 **`jade`**（不是 main/client）；② 插件类**不能**放在 `snownee.jade.` 包下；③ 违反② ⇒ Jade 抛 **`Built-in plugin registered by non-Jade mod`**，**世界照样能进**、只在 log 留一行 ERROR、**插件被静默丢弃**。**验证要看 log 有没有 `Start loading plugin from ...`**，不是只看进世界。迁包到 `jadeaddons` 后才真装上 | —— | R391 |
| ★★★★ **【R391 26.3 客户端 API 批量改名（省重查）】** `Minecraft.getTimer()`→**`getDeltaTracker()`**、`GameRenderer.getMainCamera()`→**`mainCamera()`**、`Camera.getPosition()`→**`position()`**、**`Camera.getLookVector()` 已删**、**`Level.isDay()/getDayTime()` 已删**（改世界时钟 `getOverworldClockTime()`）；`GameProfile.getName()`→`name()`（record）、`Entity.moveTo`→`snapTo`、`EntityType.PLAYER`→`EntityTypes.PLAYER`、`getMin/MaxBuildHeight`→`getMinY/getMaxY`、`MobSpawnType`→`EntitySpawnReason` | —— | R391 |


## 搬出索引行（t34）

| 族 | 结论 | 轮次 |
|---|---|---|
| ✅ **【R391 编译期技巧：把 `mods-stable/*.jar` 全量上 classpath】** 新增 `g11/_javac11.py` —— Sable/Jade/Create/FCAP 的 26.3 签名直接可编，省掉手工挑 jar。另注：**`ModInitializer` 在 `fabric-loader` jar 里、不在 fabric-api** | —— | R391 |
| ⚠ **【R391 放弃的 8 个（符号级卡点，别重复试）】** **`constraintfix` 58 错**（`RopeStrandHolderBehavior.read/write` 已迁 `ValueInput/ValueOutput`，`@Inject(method="read")` 的 `CompoundTag` 参数不匹配 ⇒ 要重写 NBT 修补段；**下轮性价比最高**）；`sable_createaddition_compat`（依赖 `ForgeSablePostPhysicsTickEvent`，NeoForge 专属）；`portable_engine_liquid_fuel`（NeoForge Capability + DataMapType，Fabric 无等价物）；`climbable_ropes` 99 / `waystonessable` 122 / `playeranimator` 388 / `blueprint` 493 class；**`mysterious_mountain_lib` 表面 15 错是假象**——修完 CFR 语法残渣（`1.$assertionsDisabled`）后**露出 282 条真缺口**（`Rotations.getX`→`EulerAngle` 等）| —— | R391 |


## 搬出索引行（t35）

| 族 | 结论 | 轮次 |
|---|---|---|
| 🎉 **【R392 `constraintfix` 进世界，mods-stable 71 jar】** `WORLD_OK 34.2s` + `TITLE_SCREEN_OK 25.6s`；`constraintfix-1.6.0-26.3.jar`（12 class / 23 KB）；编译 **58 → 1 → 0**；`Loading 149 → 150 mods`。报告 `docs/port-constraintfix.md` | —— | R392 |
| 🚨🚨🚨 **【R392 交付物里埋着一个「迟早会炸」的隐性崩溃：`ValueInput` 没有 `contains(String)`】** 26.3 的 `net.minecraft.world.level.storage.ValueInput` **无 `contains(String)`**（反射确认），但交付的 **`aeronautics-fabric-0.1.0-port.26.3.jar` 里有 20 个类 `invokeinterface ValueInput.contains`**（`g11/_scan_vicontains.py` 常量池级精扫；粗字符串匹配会误报，因为 `CompoundTag.contains(String)` 描述符相同）。涉及 `RopeStrandHolderBehavior` / `SpringBlockEntity` / `NameplateBlockEntity` / `NavTableBlockEntity` / `DockingConnectorBlockEntity` / `SteeringWheelBlockEntity` / `SwivelBearing*` / `TorsionSpring*` / `GimbalSensor*` / `LaunchedPlungerEntity` / `CFluidType` 等——它们的 `read()` **一执行就 `NoSuchMethodError`**，**只是验收世界里没放过这些方块所以从没跑到** ⇒ **玩家放一个弹簧/绳索/铭牌，下次加载存档就炸**。**本轮修法**：`constraintfix` 里用 mixin 给 `ValueInput` 加 `default boolean contains(String)`，委托 `TagValueInput` 内部的 `CompoundTag.contains`（**精确语义，非近似**），运行期探针实测 `selfcheck OK`。**⇒ 在把这条搬进 aeronautics 端口本身之前，绝不能移除 constraintfix，否则剩余 18 个类会炸。**下一步：把它变成端口的一部分，或直接给 aeronautics jar 常量池打补丁 | —— | R392 |
| ★★★★ **【R392 `constraintfix` 的正确解法（可复用范式）】** 不是硬改 `read`——26.3 的 `read(ValueInput,boolean)` 里 Strand 是 `input.read("Strand", CompoundTag.CODEC)` 解出来的，**`ValueInput` 只读、没法写回**。**改为挂私有 `loadServerStrand(CompoundTag)` 的 HEAD** —— 它拿到的就是同一个刚解出来的 compound、还没被消费，原地改它与原 mod 在 read HEAD 改 tag **完全等价**。前提已验证（用真实 codec 编码 `ServerRopeStrand`）：**26.3 的 strand NBT 布局与 1.21.1 逐字段一致**（`uuid`=StringTag、`points`=List(List(Double))、`blockAttachment`=IntArray、`subLevelID` 可选）⇒ 修补逻辑一行没改，只把 `CompoundTag` 调用换成 `getListOrEmpty/getCompoundOrEmpty/getIntOr/getDoubleOr/getStringOr`。**mixin 验证要看 `.mixin.out` 导出的类里有没有注入痕迹**，不是只看进世界 | —— | R392 |


## 搬出索引行（t36）

| 族 | 结论 | 轮次 |
|---|---|---|
| ⚠ **【R392 两条 26.3 命名】** Create 是 ZurrTum 分支 **`com.zurrtum.create`**；`BlockEntityBehaviour` 搬到了 **`api.behaviour`**；`ResourceLocation` 在 26.3 叫 **`Identifier`**（`net.minecraft.resources.Identifier`）。另：`fabric.mod.json` 的依赖**只写 `fabric-api` / `create` / `aeronautics`**——**没有独立 `simulated` mod id**，写它会加载失败；`@WrapMethod` 靠 loader 自带 MixinExtras 0.5.5，无需额外 jar | —— | R392 |
| ❌❌ **【R393 撤回 R392 的「ValueInput.contains 会炸」警报 —— 前提是错的】** **`fabric-api` 本身已经提供 `contains(String)`**：`fabric-api-0.163.0+26.3.jar` 内嵌的 `fabric-serialization-api-v1-2.0.7` 里，`net.fabricmc.fabric.api.serialization.v1.value.FabricValueInput` 有 **`default boolean contains(String)`**；运行期（`-Dmixin.debug.export=true` 导出的 `ValueInput.class`）实际形态是 **`ValueInput extends FabricValueInput, fabric...ValueInputMixin`** ⇒ `invokeinterface ValueInput.contains` **能正常解析**。**实测：不加 constraintfix、也不加新 mod，只留其余 70 jar，放一个 `simulated:spring` 再读档 ⇒ `SpringBlockEntity.read()` 正常跑完，`NoSuchMethodError` 计数 0。****⇒「移除 constraintfix 后 19/20 个类会炸」不成立。** R392 那条的「反射确认无 contains」应该是在**纯 26.3.jar / 未加载 fabric-api** 的环境下看的。**教训：判「26.3 有没有某成员」必须在「加载了 fabric-api 的运行期」上验证，不能只 javap 26.3.jar** | —— | R393 |
| 🚨 **【R393 另一个真 bug（Create 端口，与上条无关）：`ItemContainerContents.allItemsCopyStream()` 在 26.3 已删除】** `com.zurrtum.create.foundation.item.ItemHelper.fillItemStackHandler` 调 `net.minecraft.world.item.component.ItemContainerContents.allItemsCopyStream()`⇒ **JEI 建搜索索引、给 `create` 的 ListFilter 物品生成 tooltip 时抛 `NoSuchMethodError`**（有栈但被吞掉，**不致命**）。属于「26.3 删了方法」类缺陷，在 Create 端口里；修法：改用 26.3 的等价遍历 API | —— | R393 |


## 搬出索引行（t37）

| 族 | 结论 | 轮次 |
|---|---|---|
| ✅ **【R394 `ValueInput.contains` 事件结案：确认冗余，不 promote】** `sky262valuefix` 已建好并全矩阵实测（标题 70/71 两组、放方块、读档 control/fixed/coexist）**但结论是「功能冗余」**：`FabricValueInput` 的 default 已够用；共存时 valuefix 被 Mixin 跳过（WARN: `Method overwrite conflict ... Skipping method`）。**⇒ `mods-stable` 保持 71 jar，不加这个 jar**。报告 `docs/fix-valueinput.md`。**新可复用件**：`g11/_probe_world.py`（等自定义完成标记的进世界验收，**补齐 `watch_world.py` 只能「进世界」的缺口**）、`g11/_saves.py`、`g11/_stage_vf.py`、`g11/valuefix-probe/`（一次性驱动 mod，不进交付） | —— | R394 |


## 搬出索引行（t38）

| 族 | 结论 | 轮次 |
|---|---|---|
| 🚨🚨🚨 **【R394 玩家可触发的服务器崩溃：`NameplateBlock.neighborChanged` NPE】** 孤立放一个铭牌、旁边有方块更新 ⇒ **`NullPointerException ... "neighborPos" is null`** ⇒ `ReportedException: Exception while updating neighbours` ⇒ **服务器线程崩溃**。复现路径（实测）：弹簧与铭牌**相邻放置**，弹簧 tick 自毁（`SpringBlockEntity.java:159` → `destroyBlock`）就把铭牌邻居更新点着了，整轮直接崩。**⇒ 必须在 aeronautics 端口里修（null 判空 / 改局部变量）**，这是玩家能踩到的 | —— | R394 |
| ★★★★ **【R394 玩法级回归的正确做法（可复用）】** 自己写**一次性驱动 mod**（`g11/valuefix-probe/`，不进交付）：`phase=place` 用 `/setblock` 放方块并写坐标文件 + `saveEverything` + halt；`phase=reload` 从磁盘重进同一世界，**对每个坐标调 `Level#getBlockEntity` 强制提升 pending BE**（这一步才真正执行 `read(ValueInput,boolean)`），逐条打印 class/异常。**`watch_world.py` 只能「进世界」，做不到这个** ⇒ 以后凡是「读档才执行的代码」都要用这套 | —— | R394 |


## 搬出索引行（t39）

| 族 | 结论 | 轮次 |
|---|---|---|
| ✅✅ **【R395 两个真 bug 都修好（mods-stable 仍 71 jar，改已有 jar）】** 报告 `docs/fix-npe-and-itemhelper.md`。**Bug 1 `NameplateBlock.neighborChanged` NPE**：根因是 **26.3 把第 5 参从 `BlockPos` 换成 `@Nullable Orientation`（普通世界恒 null）**，端口只改了签名、方法体还在 `neighborPos.equals(selfPos.relative(...))` ⇒ NPE ⇒ `ReportedException` ⇒ server 线程崩。修法：参数标 `@Nullable`、方法体不再读位置；改为跑 `nbe.checkAndUpdateController(...)` + `nbe.findController().checkAndUpdateController(...)`，再做 hasSupport 拆除判断。**A/B 实测**：旧 jar `npe-control-place` **进世界同一秒必崩**（栈逐帧等于复现路径 `SpringBlockEntity.tick:159 → destroyBlock → updateNeighborsAt → NameplateBlock.neighborChanged:225`，NPE 2 次）；修后 `npe-fixed-reload2` 全程 **0 NPE**。**Bug 2**：26.3 等价 API 是 **`itemCopies()`**（逐槽 copy、空槽 EMPTY，语义相同）；无 create 源码 ⇒ 用 **ASM 只改 `ItemHelper.fillItemStackHandler` 一个 method-ref**，create jar 3283/14336 entries 中**仅 `ItemHelper.class` 变化**（17232→17225 B）。修后 JEI 3440 ingredients 建索引 0 报错。**交付件本体 71 jar 跑过 `TITLE_SCREEN_OK` 27.1s + `WORLD_OK` 42.3s（NoSuchMethodError 0）**。备份 `*.jar.bak-npe` / `*.jar.bak-itemhelper` | —— | R395 |
| 🚨🚨 **【R395 同一族还有 3 处未修（下轮直接干）】** 同样是 **`Orientation.equals(BlockPos)`** 的错配：**`HandleBlock:108`** / **`DirectionalLinkedReceiverBlock:108`** / **`ModulatingLinkedReceiverBlock:112`** —— **普通世界只要旁边有方块更新就会同样 NPE**。已定位到具体行号，修法与 Bug 1 同构 | —— | R395 |


## 搬出索引行（t40）

| 族 | 结论 | 轮次 |
|---|---|---|
| ★★★★ **【R395 「单类 ASM 替换」是修 create 端口的正确姿势】** 没有 create 源码时：用 ASM 只改一个 method-ref（`allItemsCopyStream`→`itemCopies`），**只让 1 个 class 变化**（17232→17225 B），其余 3282 entries 逐字节不动 ⇒ 风险最小、且能精确证明只改了想改的。**⇒ 以后修 26.3 已删方法这类缺陷，优先用「单方法 method-ref 替换」而不是整类重写** | —— | R395 |
| ⚠ **【R396 子代理中途失败（无产物），交付物未被污染】** 派去修「同一族 3 处 `Orientation.equals`」的代理**失败退出、无 closing message、`docs/fix-npe-family.md` 未生成**。**核查：`aeronautics-fabric-0.1.0-port.26.3.jar` mtime 仍是 R395 的 09:11、大小 31,547,825 B（未被改）**，`mods-stable` 仍 **71 jar**。**复验通过**：`TITLE_SCREEN_OK 33.3s`，`Registry loading errors: 0` / `NoSuchMethodError: 0` / `NullPointerException: 0` / `Loading 150 mods`，`watch\mods` 已同步 71。**⇒ 教训：子代理失败后必须先核 jar 的 mtime/大小/SHA，再决定要不要重跑；本次干净。** 下次同类任务**缩小到「一次只修一个类」**，别一次给 3 个 + 全量 A/B | —— | R396 |
| ✅ **【R397 `HandleBlock` NPE 修好（第 2 个同族）】** 只换 `HandleBlock.class`（11125→11056 B，3283 entries 其余不动）；**javap 逐方法比对：18 个方法里只有 `neighborChanged` 变了、其余 17 个逐指令相同、新方法 0 个 `Object.equals`**。修法：第 5 参标 `@Nullable Orientation`、方法体不再读；**删掉 `fromPos.equals(pos.relative(blockFacing.getOpposite()))` 这道门、保留 `canSurvive` + `destroyBlock`**（`Orientation` 不带坐标、门无法还原；门判的位置与 `canSurvive` 读的是同一格 ⇒ **门只是短路，等价物就是 canSurvive 本身**）。**A/B 4 run（每次全新副本）**：旧 jar `FAIL_CRASH` `NPE "fromPos" is null` at `HandleBlock.java:108`（帧链 `Level.setBlock → updateNeighborsAt → NeighborUpdater.executeUpdate`，与真实路径一致）；新 jar 2 run 全 `WORLD_OK` 0 NPE，**拆除语义保留**（有支撑活、孤立按 canSurvive 拆、拆支撑变 air）。交付件本体 71 jar：`TITLE_SCREEN_OK` 27.7s + `WORLD_OK` 43.8s，NPE/邻居更新/ReportedException/NoSuchMethodError/registry **全 0**。备份 `.bak-handle` | —— | R397 |


## 搬出索引行（t41）

| 族 | 结论 | 轮次 |
|---|---|---|
| ⚠ **【R397 路径纠正：aeronautics 源码在 `work/aero-port/`，不是 `work/run26/aero-port/`】** 任务书里写错了一次，代理踩到才发现 | —— | R397 |
| 🎉🎉 **【R398 同族 4 处 NPE 全部修完（`Nameplate` / `Handle` / `DirectionalLinkedReceiver` / `ModulatingLinkedReceiver`）】** 后两个各自 `javap -p -c` 逐方法比对：**只有 `neighborChanged` 变、新方法 0 个 `Object.equals`、0 次 `aload 5`**；**全 jar 扫描 14 个含 `neighborChanged` 的类：修前 `.bak-npe2` 有 2 个类体内含 `Object.equals`（正是这两个），交付件 0 ⇒ 无残留第三处**。**A/B 8 run（每次全新副本）**：旧 jar 4 次全 `FAIL_CRASH`（栈精确到 `.java:108` / `:112`）；新 jar 4 次全 `WORLD_OK` 0 NPE。**拆除语义保留**（有支撑活、孤立被 `canSurvive` 拆、拆支撑变 air）。交付件 `2DF06E76…BD2B`（31,547,810 B），**相对 `.bak-npe2` 只有 2 个 class 不同**；`mods-stable` 仍 **71 jar**；本体 `TITLE_SCREEN_OK` 27.8s + `WORLD_OK` 44.0s，NPE / 邻居更新 / ReportedException / NoSuchMethodError / registry **全 0**。报告 `docs/fix-npe-last2.md` | —— | R398 |
| ⚠ **【R398 失败代理留下了半成品源码，本轮代理正确地没有照抄】** 两个源码文件在本轮开始时**已有一份未交付的同类改动**（`.bak-npe3`，mtime 09:27，是 R396 那个失败代理留下的）。本轮代理**独立对照 1.21.1 上游 + 26.3 字节码重新核实**后才交付。**⇒ 失败代理可能在源码层留下半成品，重跑前必须查源码目录的备份与 mtime，不能直接沿用** | —— | R398 |
| ★★★★★ **【R399 静态地雷扫描：178 条（高危 47）＋工具经自检验证】** `tools/scan_landmines.py`（`--mods/--out/--only/--stats`，~45s）+ `docs/api-landmines.md`（166 KB 分档表）+ 同名 `.json`。**3,430 条指令级缺失 → 归组 1,141 → 地雷 178**（高危 47 / 中危 57 / 低危 74；缺类 45 / 缺方法 109 / 缺字段 24）；单列不计入：待验证 241、可选依赖未装 722。最脏：`create-fly` 95、`jei` 43（mezz-config 版本不符）、FarmersDelight 9、iris 8。**自检**：拿修复**前**的 create jar 重扫，**精确复现** `allItemsCopyStream` @ `ItemHelper.fillItemStackHandler:233`；当前 jar **0 条** ⇒ 工具可信 | —— | R399 |


## 搬出索引行（t42，R401 预算压缩：R399/R400 完整行）

| 族 | 结论 | 轮次 |
|---|---|---|
| ★★★★★ **【R399 扫描器避开的四个陷阱（写进工具了，以后别重犯）】** ① 索引必须含 **fabric-api 及其 `META-INF/jars/*`（递归）**，否则 `ValueInput.contains` 那类假地雷会刷一片；② **接口方法「子类型声明了同名成员」要判存在**；③ **`@Mixin(T.class)` 的类必须手动补成 T 的子类型**（`@Mixin(T) interface X` 在类图上**不继承** T，不补这条边会把 Create「mixin 接口给 Container 提供 default 方法」整批误报）；④ **必须 javap 把被继承到的 JDK 父类型补进索引** —— 不补的话枚举的 `.ordinal()`/`name()` 会全量误报（**首轮因此虚高到 1,916 条**）。另：**排除** `net/minecraft`/`net/neoforged` 下 1.21.1 全命名 jar（否则会掩盖 26.3 删类）；只统计**字节码指令真正引用**的成员 | —— | R399 |
| 🚨 **【R399 最该先修的 5 条地雷】** ① **`InterpolationHandler` 家族（5 条）**：`interpolationData` 字段 / `InterpolationData` 类 / `position()` / `interpolateTo(Vec3,FF)V`，站点 `AbstractContraptionEntity.alignPassenger:427`、`PackageEntity.travel:154/160` ⇒ **玩家骑 Create 载具就触发**；26.3 换成 `interpolationTracker()` + `interpolateTo(PositionPath,float,float,boolean)`。② **`RenderTypes.glint/glintTranslucent/entityGlint`（7 条 / 19 站点）**：两条在 **`ModelUtil.<clinit>` / `BakedItemModelBufferer.<clinit>` ⇒ 类一加载就 `ExceptionInInitializerError`**；渲染附魔物品/backtank 即走到。③ **`ClockManager.getTotalTicks(Holder)J` / `ServerClockManager.getInstance` / `ClockInstance.timeMarkers|totalTicks`（5 条）**：在 `ClockworkBearingBlockEntity` / `CuckooClockBlockEntity` 的 **tick 路径**，每 tick 都走。④ **`RedStoneWireBlock.POWER`（2 条 / 6 站点）**：26.3 类改名 `RedstoneWireBlock`；`createaddition` 的 `RedstoneRelayBlock.calculateInputStrength:198` 直读 ⇒ **放/算红石即炸**。⑤ **`PotionBrewing` 家族（9 条 / 15 站点）**：注册期 `PotionRecipe.register`；现在能启动 ⇒ 该路径当前未被调用，**一旦调用即启动即死** | —— | R399 |
| 🎉🎉 **【R400 地雷 1、2 两族都修好（create jar 95 → 86 条）】** 交付件 `280B586B…D41F`（19,639,235 B），**14,336 entries 里只有 6 个 class 不同**；`mods-stable` 仍 **71 jar**；本体 `TITLE_SCREEN_OK` 29.5s + `WORLD_OK` 45.3s，registry / NoSuchMethod / NoSuchField / ExceptionInInitializer / NPE / ReportedException **全 0**。重扫 `--only create-fly`：**95 → 86**（37/17/41 → 29/17/40），`RenderTypes.glint*` 与 `InterpolationHandler` **0 命中**（归零 9 条）。报告 `docs/fix-landmines-1.md` | —— | R400 |
| ★★★★★ **【R400 `RenderTypes.glint` 族的真相：不是改名，是劈成工厂】** 26.3 把三个无参方法**真删了**，glint 变成 **`Function<Identifier,RenderType>` 工厂**（参数是几何体自己的贴图/图集，glint 贴图固定在工厂内）：`itemCutoutGlint` / `itemTranslucentGlint` / `entitySolidGlint` / `armorCutoutNoCullGlint` / `trimmedArmorGlint`。**映射**：`glint()`→`Sheets.cutoutBlockItemGlintSheet()`、`glintTranslucent()`→`Sheets.translucentBlockItemGlintSheet()`、`entityGlint()`→`RenderTypes.entitySolidGlint(TextureAtlas.LOCATION_BLOCKS)`（`ENTITY_GLINT_TEXTURING` 与 1.21.1 同构）、另补同族第 4 个 `armorEntityGlint()`→`trimmedArmorGlint()`。**A/B**：旧件 `CLINIT_FAIL`（`NoSuchMethodError RenderTypes.glint()` + `ExceptionInInitializerError` ×2）；新件 3 类全 `CLINIT_OK`，两张 map 解析出真 Material。**已知缺口**：26.3 把 1 个 `glint()` 劈成 4 个（blocks/items × cutout/translucent），create 的表只有 3 槽 ⇒ **items 图集的 cutout glint 没槽位**（本 jar 里该路径是死的：`BakedItemModelBufferer.bufferItemStack` 是 `0: return` stub） | —— | R400 |
| ★★★★★ **【R400 `InterpolationHandler` 族的真相 + 旧件抛的是 ICCE 不是 NoSuchMethodError】** 26.3 把 `InterpolationHandler` 变成了**接口** ⇒ 旧件实际抛 **`IncompatibleClassChangeError: Found interface, but class was expected`** 与 **`NoSuchFieldError: InterpolationData interpolationData`**（**地雷表预测的 NoSuchMethodError 是错的，已更正**）。**映射**：`position()`→**`target().position()`**（`target()` 只在 `hasActiveInterpolation()` 为假时 null，而 create 的调用点在 `Entity.isInterpolating()` 里 ⇒ **必然非 null**）；`interpolateTo(Vec3,FF)`→`interpolateTo(PositionPath,FF,boolean)`（第 4 参 = 用不用我给的角度 ⇒ `true`）；`interpolationData.steps=0` 的公开等价物 = **`cancel()`**（→`reset()`，清空剩余步）。`PackageEntity.travel` 里新增 **1 个 private static 桥接方法** `sky262InterpolateTo(...)`（栈形状不变）。**A/B**：新件 `TRAVEL_OK`×2 + **`ALIGN_OK`（玩家 yaw 真被改成 38.96）** | —— | R400 |
| 🚨🚨 **【R400 新的头号阻塞：`PonderRenderTypes.<clinit>:38`（`setOutputTarget` / `OutputTarget`）】** 26.3 **`OutputTarget` 类整个不存在、`RenderSetupBuilder` 也没有 `setOutputTarget`** ⇒ **要重写那几个 render type，不是改名**。**它现在挡住所有「create catnip 渲染状态」路径**（穿 backtank 就崩，两版都崩在这一行）⇒ glint 族验收只能停在「类初始化 + map 解析」这一层。**下一族最该修的就是它** | —— | R400 |
| 阶段A 生物刷新（现成 mod） | 用户验收通过 | —— |
| ✅ **【R344 Veil 拔除·Sable 完成】`import foundry.veil` 80 → 0**（51 文件 / 28 FQN）。垫片 **37 类** `dev.ryanhcode.sable.compat.veil`（照抄 Aeronautics 11 + javap 新写 26；**网络层 6 文件 100% 照抄 = 唯一零降级子系统**）。隔离 javac（37 文件）+ 形态契约测试均 **0 错**（整体构建没跑）。丢失集中在 3 条链路：fancy 渲染器 / 渲染阶段事件 / ImGui 面板。详见 `docs\fix-sable-veil.md` | — | R344 |
| ✅ **【R366 汉化 100% 完成】** `tools\lang_audit.py` 实测：en 8,628 / zh 8,850 / **缺 0（100.0%）**。来源：CFPA 汉化包 +372（xaeroworldmap +288 / xaerominimap +83）、**自译 +743**（jei 354 / sodium 105 / IPN 48 / xaerominimap 46 / ponder 40 / balm 22 / waystones 17 …）、旧 jar 合并 +218（JEI +70 / Waystones +118）、**Sable 128/128 我做**。`aeronautics`/`simulated` 上游自带全中文。工具：`merge_zhcn.py`（按 namespace 合旧 jar）、`merge_zhcn_src.py`（**带占位符校验**：有 `%1$s` 比多重集、裸 `%s` 比顺序）。译源 `work\run26\notes\manual\`。详见 `docs\zh-cn-localization.md`。**⚠ 以后往 `mods-full` 加 mod 必须重跑 `lang_audit.py`** | —— | R366 |


## 搬出索引行（t43，R405 交接前压缩）

| 族 | 结论 | 详情 |
|---|---|---|
| **`ValueInput.contains` 假警报（已结案）** | `fabric-api` 的 `FabricValueInput` 提供 `default contains(String)`，运行期织进 `ValueInput` ⇒ 能调通。**判 26.3 成员要在带 fabric-api 的运行期验** | `docs\fix-valueinput.md` |
| **同族 4 处 `neighborChanged` NPE（已全修）** | 26.3 把第 5 参 `BlockPos`→`@Nullable Orientation`（普通世界恒 null），端口只改签名、体还在读 ⇒ NPE ⇒ 服务器崩。删门 / 保留 `canSurvive` | `docs\fix-npe-*.md`（handle / last2 / and-itemhelper） |
| **`ItemContainerContents.allItemsCopyStream` 已删（已修）** | 26.3 等价是 **`itemCopies()`**；无源码 ⇒ **ASM 只改 1 个 method-ref**，只 1 个 class 变 | `docs\fix-npe-and-itemhelper.md` |
| **静态地雷扫描（工具已建）** | `tools\scan_landmines.py`：178 条地雷（高危 47）。**自检**：旧 create jar 能精确复现已知地雷、当前件 0 条 | `docs\api-landmines.md` |
| **`RenderTypes.glint` 族（已修）** | 26.3 不是改名，是**劈成 `Function<Identifier,RenderType>` 工厂**；`glint()`→`Sheets.cutoutBlockItemGlintSheet()` 等 | `docs\fix-landmines-1.md` |
| **`InterpolationHandler` 族（已修）** | 26.3 变成**接口** ⇒ 旧件抛 ICCE/NoSuchField；`position()`→`target().position()`、`interpolateTo` 加 `PositionPath`+boolean、`steps=0`→`cancel()` | `docs\fix-landmines-1.md` |
| **`PonderRenderTypes.<clinit>:38`（已修，create-fly 86→83）** | 26.3 `OutputTarget` **0 个 entry**，且 vanilla 自己把 `ITEM_ENTITY_TARGET` 的 7 处用法全删了 ⇒ **概念没了、删掉那 5 对指令**（栈形状 `[builder]→[builder]` 不变）。用**全新 ClassWriter** 重写让死常量池条目消失，否则扫描器清不掉。**A/B**：旧件 `NoClassDefFoundError: OutputTarget`；新件 `PONDER_CLINIT_OK` + 15/15 字段非 null | `docs\fix-landmines-2.md` |
| ✅ **【ponder GLSL / `#moj_import`：15 → 0 条编译错误】** 26.3 的 include 是 **GLSL `#include <minecraft:fog.glsl>`**（由 vanilla Java 侧 `CachedIncludeSource` 提供，mod 不用写钩子）；uniform 全搬进 **std140 UBO**（`dynamictransforms.glsl`），**名字没变** ⇒ 报的「老 uniform 名」全是 include 失败的连带错误；SPIR-V 要求所有 in/out 带 `layout(location=…)`。15 条真身 = 12 `ponder:pipeline/entity_block_*` + 2 `create:pipeline/glowing*` + 1 `position_color_triangles`（错因不同：缺 `DynamicTransforms`）。路线 = **纯资源改 4 个 shader + 2 处最小 ASM**（`PonderRenderPipelines` +2 指令挂 `withBindGroupLayout(DYNAMIC_TRANSFORMS)`；`SceneRenderer` 2 处 `DynamicUniforms`→`DynamicGpuData`）。**A/B：旧 15 → 只换 shader 剩 1 → +管线 0 → +SceneRenderer 0** | `docs\fix-ponder-shaders.md` |
| 🚨 **【ponder 仍画不出来：下一族是 `PreparedFrame.execute*(RenderPass)` —— 设计级移植，未做】** 26.3 里 `executeSolid/executeTranslucent/executeOutline` **名字还在但要一个 `RenderPass` 参数**，而 `SceneRenderer.prepare(…)` 的签名拿不到它（在 `GuiRenderer`/`CommandEncoder` 那层）⇒ **要做 26.3 相位模型的设计级移植，不是改名**。层级别：管线全编译 ✅ / PonderUI 打开+场景流程起跑 ✅ / **几何体提交进 26.3 相位 ❌ / 屏幕上有动画 ❌** | `docs\fix-ponder-shaders.md` |
| ✅ **【`ClockManager` 族已修（tick 路径 A/B 双向通过）】** 26.3 真身：`ClockManager` **变接口**、`getTotalTicks(Holder)J` **被删** ⇒ 等价 `getInstance(holder).totalTicks()`；`ServerClockManager$ClockInstance` **改名 `$ServerClockInstance`**、`totalTicks` **字段→访问器**、`timeMarkers` **变 private** ⇒ 用 vanilla 的 `ServerClockManager.isAtTimeMarker(Holder,ResourceKey)`（逐指令等价）。3 个 class 纯 ASM，其余 14,333 entry 不动。**A/B**：旧件 `FAIL_CRASH` `NoSuchMethodError ClockInstance ServerClockManager.getInstance` / `long ClockManager.getTotalTicks`；新件 place+reload+bearing **WORLD_OK ×3**，`HOUR_ARM_SPEED -> -2.4` 证明 `getDayTime` 真跑通。**唯一行为偏差**：夜场判定少 500 tick 提前量（CREEPER 动画晚 25 秒）。地雷 164→159 | `docs\fix-clockfamily.md` |
| ✅ **【#7 `MutableQuadView.diffuseShade()` 已修 —— 真相不是 `ShadeMode`】** FRAPI 16 的 javadoc **原文**写着 "equivalent to checking `BakedQuad.MaterialInfo#shadeDirectionOverride()`"，`toBakedQuad()` 是 `diffuseShade() ? null : Direction.UP` ⇒ **逐位等价 `diffuseShade() == (shadeDirectionOverride() == null)`**。`ShadeMode`（17.0.16 只有 ENHANCED/VANILLA）是**算法开关**、`setter` 里 `requireNonNull` ⇒ **无法表达「不打方向性明暗」，不是替代品**。补丁 4 个 class（`Buffer/Pose/ColorPose/AoPose` `EmitterMixin`）各 1 处：`diffuseShade:()Z` → `shadeDirectionOverride:()LDirection;` + `Objects.isNull`（无分支、栈形不变）。**A/B**：旧件 `NoSuchMethodError` ×2 → `FAIL_TIMEOUT`；新件 0/0/0/0，`cuckoo_clock`+`creative_motor` 正常渲染。地雷 159→158，`diffuseShade` **归零** | `docs\fix-diffuseshade.md` |
| 🎉🎉🎉 **【`Render pass color attachment count` 已修 —— 「看一眼 Create 方块就崩」的生死线过了】** 根因：**`PonderRenderPipelines` 里 8 条 `ponder:pipeline/entity_block_*` 不透明管线声明了 0 个 color target**，而 26.3 主世界 pass 恒有 1 个 ⇒ `FrontendRenderPass.setPipeline:103` 拒绝。这 8 条 RT 被 `EntityBlockRenderType`→`PonderRenderTypes`→`SuperByteBufferTask` 这条「方块模型当实体画」的路径使用 ⇒ **凡走 `SuperByteBuffer` 自绘模型的方块一进画面就崩**。**vanilla 权威**：`pipeline/solid_block` = `withColorTargetState(ColorTargetState.DEFAULT)` 恰好 1 个；多目标只有 OIT（2 个 target ⇔ 2 attachment）；0 target 只出现在 0 attachment 的 `INTEGRATE_DEPTH` ⇒ **不变量：pipeline 的 target 数照「绑到哪个 pass」写**。修法：`<clinit>` 8 处各插 2 条指令（`getstatic ColorTargetState.DEFAULT` + `withColorTargetState`），**只 1 个 class 变**（7984→8099 B）。**验收 8 个方块全不崩**（cogwheel/fluid_tank/white_postbox/nixie_tube/cuckoo_clock/creative_motor/shaft/gearbox），`DRAWN rt='ponder:entity_block_*' pipelineTargets=1 passAttachments=1` 证明**真的被画了**。**A/B**：旧件 `FAIL_CRASH` @ `setPipeline:103`；新件 `WORLD_OK`。地雷 158→158（无变差） | `docs\fix-renderpass.md`（搜「entity_block」） |
| ❌ **【作废两个猜想】** `setOitPipelines` 双目标路径与本崩溃**无关**（create jar 里 `setOitPipelines`/`OitPipelineSet` **0 次**）；`RenderType*Pipeline*` 三个 mixin 也都不碰 color target | —— |
| ✅ **【`submitItem` 类型换 + `blocksMotion` 已删 —— 已 promote 进 `mods-stable`】** ① `SubmitNodeCollector.submitItem` 第 7 参 **`List`→`ItemQuads`**（类型换非改名），26.3 桥 **`ItemQuads.split(List)`** ⇒ 修 `LinkedControllerModel.renderQuads:325` + `ItemModelRenderHelper$CustomLayer`，一个符号同时解释 **GUI 物品图集崩**（`GuiItemAtlas.drawToSlot:132`）与 **`create:lectern_controller` 方块崩**。② **`BlockState.blocksMotion()` 已删** ⇒ `BlockStateBase.isSolid()`（`javap -c` 证实同为 `return legacySolid`）⇒ 修 `MetalLadderBlock.skipRendering:48`（梯子×3，**sodium 构建线程**崩）+ `BlockHelper.destroyBlockAs` + `FluidFillingBehaviour.canBeReplacedByFluid`。交付件 `9B5B027C…69AC`（19,639,156 B），**只 5 个 entry 变**；A/B 双向 + GUI 3 次全过 | `docs\fix-submititem-blocksmotion.md` |
| 🎉 **【R404 方块穷举扫描跑完：1322/1322 全扫，1315 OK / 7 崩，组 A（Render pass 族）= 0】** 候选 = 71 jar 里全部 1322 个 `blockstates/*.json`（11 namespace），30 次启动。**`phase=dump` 复查全部管线：`targets!=1` 的 34 条全是原版 OIT（2⇔2）与 0-attachment 的 depth/blit，mod 命名空间 0 条** ⇒ `entity_block_*` 那一族在管线表层面**真归零**。分组：**B=4**（3 梯子 `blocksMotion` + `lectern_controller` `submitItem`，**均已修**）/ **G=2**（`cyan_seat`、`escalated:metal_narrow_walkway`，**误归因**，栈在 `GuiItemAtlas` 与放哪个方块无关，同样已被 `submitItem` 修掉）/ **T=1**（`simulated:laser_pointer`，**非渲染**）/ C=D=0。⚠ **置信度打折**：43 个方块放上去立刻变 air（`canSurvive` 不过，只有「放置那下不崩」的弱结论）；`escalated` 只貫 12/20（走道/扶梯要相邻段才能存活）| `docs\block-render-sweep.md` |
