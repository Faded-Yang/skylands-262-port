# 特性缺口审计（代码侧）—— FEATURE-GAP-code

> 目标：对手工移植的三个 jar（create-fly / aeronautics / sable）做「未实现特性」清单，
> 与 wiki/注册表侧清单（aero-fixer + probe）合并成用户可对照的完整特性表。

## 1. 已知的「未实现」形态（先分类，便于对照）

| 形态 | 例子（已确认） | 后果 |
|---|---|---|
| 渲染器桩（class 只有构造器/空 render） | `PhysicsAssemblerRenderer`(485B)、`AbstractLaserRenderer`(454B)、`LaserPointerRenderer`(479B)、`OpticalSensorRenderer`(484B) | 方块本体可见但部件/透镜/光束缺失 |
| registrate 垫片空实现 | `BlockBuilder.renderer()` 空实现 | 大量 BE renderer 从未注册（R422/R423 系列根因） |
| shim 空方法 | `CreateClient$ValueSettingsHandler.showHoverTip` 只 return（R426 已修） | 提示/UI 永不显示 |
| 数据引用 26.3 已删内容 | advancement icon 引用未注册方块（R431 已修 4 条） | <clinit> 崩溃或图标空 |
| Methodref 指向 26.3 已删 API | `LocalPlayer.swing(InteractionHand)`（swingfix2 已修） | 右键使用崩溃 |
| mixin 选择器失效（defaultRequire=0） | hold_interaction 四个 mixin（R428 已修） | 静默失效：交互不响应 |

## 2. 扫描方法与当前状态

计划：逐 class 解析方法 Code 属性 → 标记「空方法（仅 return/throw）」「只返回默认值」→ 输出 模块/类/方法/调用方。

当前状态（**未完成，工具需修**）：
- 第一版 Python 解析器已能统计方法总数（create-fly 33,961 / aeronautics 7,889 / sable 4,231），
  但「空方法」启发式**误报为 0**（与已知桩 `PhysicsAssemblerRenderer` 等矛盾）⇒ 判定逻辑有 bug，结论**不采用**；
- 26.3 已删 API 的 Methodref 扫描第一版（MC 方法表映射）也只解析出 1 个 MC class，同样作废。

下一步（下一轮）：
1. 用 **Java + ASM** 写扫描器（与 MixinTargetCheck 同套 classpath），逐方法读取 InsnList：判断是否只有 RETURN/ACONST_NULL/IRETURN 等，
   同时识别 `throw new UnsupportedOperationException` 与字符串常量中的 `TODO`/`not implemented`；
2. Methodref 解析改为「用 ASM 加载 26.3 jar 建立 ClassNode 方法表」后扫描三个目标 jar，输出 owner.name+desc 缺失清单；
3. 结果写入本文件 §3（模块/类/方法/现状/调用方/优先级/修复成本）与 §4（已注册但运行期无实现的方块/物品单独表）。

## 3. 模块/类/方法缺口表（待 ASM 扫描填充）

| 模块 | 类 | 方法 | 现状 | 调用方 | 优先级 | 修复成本 |
|---|---|---|---|---|---|---|
| aeronautics | AbstractLaserRenderer / LaserPointerRenderer / OpticalSensorRenderer | render* | 桩 | BlockEntityRenderer 注册 | P1（视觉） | 中（需从零 BER） |
| aeronautics | PhysicsAssemblerRenderer | render* | 桩（已被 PhysicsAssemblerLeverRenderer 取代，R422） | — | 已完成 | — |
| create-fly | 大量 *Renderer（registrate 垫片未注册） | render* | 桩 | 由 R422/R423/R433 批量补 | P0→P1 | 每项小 |
| sable | Vanilla*/Fancy* SubLevel render dispatcher | render* | 空壳（R415 部分修复） | LevelRenderEvents | P1 | 中 |

## 4. 已注册但运行期无实现的方块/物品（待补）

（待 ASM 扫描 + 注册表侧清单合并；已知候选：laser_sensor/optical_sensor 的透镜面、portable_engine filtering/发光层、text 类方块）

## 5. 已修族索引（避免重复审计）

- R422/R423/R433：BE renderer 批量补齐（17 表项 + assembler/throttle/docking）；
- R426：hold tip shim；R427：进度条；R428：hold 输入 mixin；R429/R432：hold 防重入；
- R431：advancement 空 icon；R434/R436：sublevel 交互双端映射；R439：ABC8 + laser 透镜 asset。
## 6. ASM 扫描器 v2 结果（2026-10-19）

工具：`work/run26/port/g31/helper/src4/FeatureGapScan.java`（ASM ClassNode；26.3 jar 建方法表 + 继承链 BFS）。
输入：create-fly `0E9B26D3` / aeronautics `1BED71C9` / sable `1088C4FE`。

### 6.1 桩方法分布（top 类，均含『仅 return/默认值』方法）

| 类 | 桩方法数 | 说明 |
|---|---|---|
| create/catnip/levelWrappers/SchematicChunkSource$EmptierChunk$DummyLevel | 24 | 虚拟世界占位（合理） |
| create/client/flywheel/lib/vertex/DefaultVertexList | 22 | flywheel 占位（合理） |
| sable/physics/impl/none/StaticPhysicsPipeline | 19 | no-op 物理后端（合理） |
| create/client/foundation/virtualWorld/VirtualChunk / ponder/foundation/level/PonderChunk | 18 / 18 | 虚拟世界占位（合理） |
| create/api/behaviour/BlockEntityBehaviour / MovementBehaviour | 10 / 8 | 可选重写（合理） |
| sable/sublevel/render/dispatcher/FancySubLevelRenderDispatcher | 7 | **未实现渲染**（R415 部分修） |
| simulated/compat/veil/render/post/PostProcessingManager | 7 | Veil 后处理占位 |
| simulated/content/entities/honey_glue/HoneyGlueEntity | 6 | **蜂蜜胶功能缺口候选** |
| simulated/content/items/plunger_launcher/PlungerLauncherItemRenderer$RenderHandler | 6 | 渲染占位 |
| simulated/fabric/service/FabricSimInventoryService | 6 | 背包桥占位 |

结论：多数桩是虚拟世界/可选重写（无害）；**需关注** = `FancySubLevelRenderDispatcher`、`HoneyGlueEntity`、`PlungerLauncherItemRenderer$RenderHandler`、`PostProcessingManager`。

### 6.2 引用 26.3 缺失成员（继承链感知，已剔除大部分泛型/枚举误报）

| 缺失引用 | 次数 | 判读 |
|---|---|---|
| `ClientPlayer.swing(InteractionHand)`（经 mixin 运行期补回） | 4 | 已由 create-fly swingfix2（R440）修复，扫描器静态看不到 mixin 方法 |
| `ServerPlayer.swing(InteractionHand, Z)` | 2 | **真缺失**，若被调用会 NoSuchMethodError；需确认调用方是否可达 |
| `Inventory.insert(ItemStack,III)` | 1 | **真缺失**（26.3 Inventory 改签名），见 `AllHandle`；同类问题可致丢物品/崩溃 |
| `BlockItem.updateCustomBlockEntityTag(BlockPos,...)` | 7 | **真缺失**，方块物品放置时 BE 数据可能不下发 |
| `GuiGraphicsExtractor.textWithWordWrap/tooltip(...)` | 6 / 3 | **真缺失**，渲染路径改动 ⇒ 文本/Tooltip 可能静默不显示 |
| `Level.fuelValues()` / `FuelValues.isFuel` | 5 / 1 | **真缺失**，燃料判定可能失效 |
| `ValueInput.contains/forEach/iterator` | 30/21/10 | 26.3 数据层改 API，配置/NBT 读取路径需核对 |
| `BlockState.isViewBlocking(BlockGetter,BlockPos)` | 9 | 可能真缺失（渲染遮挡判定） |
| `Direction.ordinal()` 等枚举方法 | 218+ | **误报**（java.lang.Enum 继承，扫描器只走 MC 继承链） |
| `ListTag.add/forEach` | 33/5 | **误报**（java.util 继承，同上） |

### 6.3 下一步（优先级）

1. 扫描器补 JDK 继承（Enum/Iterable/Collection）消除误报；
2. 对「真缺失」逐条确认调用方是否可达（用 MethodInsn 调用图），可达的按 P0 修（同 swingfix 模式：mixin 补方法或 CP 适配）；
3. 物品功能缺口（probe 已验）：`create:super_glue` 右键不崩（R440）；`simulated:merging_glue/physics_staff/extendo_grip` **未注册**（需查注册表/移植是否遗漏）；`simulated:contraption_diagram` 使用抛 synched data 8（候选 `ca9ba885` 已 staging 待验）；`simulated:honey_glue` 功能待专测。
