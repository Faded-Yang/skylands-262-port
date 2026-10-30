# 物品功能性审计（task-36）

base live aero = `1BED71C9`；本文件记录 item 行为入口、已定位问题与修法。

## 1. 物品清单与行为入口

| 物品 | 类 | 行为入口 | 现状 |
|---|---|---|---|
| `create:super_glue` | Create `SuperGlueItem` | Create 的 `MinecraftMixin.doItemUse` | **崩**：26.3 删 `LocalPlayer.swing(InteractionHand)`；ponder P0 修 create 件，**不归 aeronautics** |
| `simulated:honey_glue` | `HoneyGlueItem`（无 Item 方法） | `HoneyGlueClientHandler`（Alt+右键，click-interactions） + `HoneyGlueSpawnPacket` | 代码路径存在、mixin 已注册；**普通右键无行为是设计**（需 Alt） |
| `simulated:merging_glue` | block + `MergingGlueItemHandler`（客户端预览） | 放置 block / 绑定两端 sublevel | block/BE 在，item handler 注册待验 |
| `simulated:spring` | `SpringItem` | `useOn` + `SpringItemHandler` | useOn 已实现 |
| `simulated:rope_coupling` | `RopeItem` | `useOn` + `ZiplineClientManager` | useOn 已实现 |
| `simulated:contraption_diagram` | `DiagramItem` | `useOn` | 已实现 |
| `simulated:plunger_launcher` | `PlungerLauncherItem` | `use`/`useOn` + arm pose | 已实现 |
| `simulated:physics_staff` | `PhysicsStaffItem`（无 Item 方法） | `PhysicsStaffClientHandler` | 客户端 handler |
| `aeronautics:aviators_goggles` | `AviatorsGogglesItem`（无 Item 方法） | 装备/渲染 mixin | 已实现 |
| Create `wrench`/`extendo_grip` | Create 物品 | Create 逻辑 + simulated `ExtendoGripItemMixin` | 非本 mod 物品 |

## 2. super_glue 崩溃

根因链：`MinecraftMixin.doItemUse` → `LocalPlayer.swing(InteractionHand)`（26.3 已删）→ NoSuchMethodError。
**修法在 create 件（ponder 已出 P0）**；aeronautics 侧没有 super glue 类，无需改。

## 3. honey_glue 无功能

原版机制：**Alt+右键**选第一个方块（BINDING，播放 HONEY_ADDED/ITEM_FRAME_ADD_ITEM），再 Alt+右键第二个方块 → 发 `HoneyGlueSpawnPacket` 生成 HoneyGlueEntity；Shift+右键清除；**普通右键本来就不触发**。

代码链路（静态检查）：
- `SimClickInteractions.HONEY_GLUE_MANAGER` 已注册；
- `MouseHandlerMixin` 已调用 `SimulatedCommonClientEvents.onBeforeMouseInput/onMouseScroll`；
- `FabricVeilPacketManager` 负责注册 payload；
=> 若 probe 用普通右键测「无功能」，属预期；需用 **Alt+右键两次** 测实体 spawn/NBT。

## 4. 待探针验证

- honey_glue：Alt+右键 A 方块 → 再 Alt+右键 B 方块 → 检查 `HoneyGlueEntity` 是否生成、NBT bounds、声音、0 crash；
- merging_glue：手持 merging glue 右键 sublevel 两端 → 检查 block/BE/绑定；
- spring/rope_coupling/diagram/plunger_launcher：各自右键方块/空气，检查预期效果与 0 crash；
- super_glue：等 ponder 的 create 修复件 promote 后测右键方块。

## 5. 结论

- 当前没有需要 aeronautics 代码改动的「空实现」item；honey_glue 是**用法**问题（Alt），super_glue 是 create 件问题（ponder）；
- 下一步按探针结果决定是否要补 handler 注册/兼容。
