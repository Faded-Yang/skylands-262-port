# 物品功能（源码级）核查与修复 —— simulated / aeronautics

> 轮次 R449；基线 live aero `455B5824`（源码收口版）。

## 1. 注册表核对（源码 vs 上游 Simulated-Project vs 运行期 registry dump）

| 名称 | 上游（1.21.1 源码） | 当前源码 | 运行期注册 | 结论 |
|---|---|---|---|---|
| `simulated:contraption_diagram` | item（DiagramItem） | 已注册（excluded-wip/SimItems） | ✅ item | 已修：`DiagramEntity.defineSynchedData` 补 super + `updateFacingWithBoundingBox` 水平化；live 实测无 Validate 异常 |
| `simulated:honey_glue` | item（HoneyGlueItem）+ 实体 HoneyGlueEntity + 客户端 Handler | 已注册；Handler 由 `SimClickInteractions.HONEY_GLUE_MANAGER` 注册 | ✅ item | 代码链路完整（Alt+右键两次 → BINDING → `HoneyGlueSpawnPacket` → spawn 实体）；26.3 适配已做（`Minecraft.hasAltDown/hasControlDown`、`player.swing(hand,SwingAnimation.DEFAULT,false)`）。`HoneyGlueItem.canAttackBlock` 在 26.3 已无对应钩子（Item 无此方法）⇒ 该方法为死代码，不影响主链路 |
| `simulated:creative_physics_staff`（不是 `physics_staff`） | item（PhysicsStaffItem）+ ClientHandler | 已注册；`PHYSICS_STAFF_CLIENT_HANDLER` 已接线 | ✅ item | 无注册缺口 |
| `simulated:plunger_launcher` | item（PlungerLauncherItem）+ Renderer | 已注册；handler 接线 | ✅ item | 无注册缺口 |
| `simulated:spring` / `rope_coupling` / `gyroscopic_mechanism` / `engine_assembly` | item | 已注册 | ✅ | 无缺口 |
| `simulated:merging_glue` | **只有方块**（`MergingGlueBlock` + BE），上游 `REGISTRATE.block(...).register()` **没有 BlockItem** | 同上游：只有方块 | 方块 ✅ / **item ❌** | **真缺口**：创造栏/物品形态都没有 ⇒ 用户报「未注册」。修法：源码 `SimBlocks.MERGING_GLUE` 加 `.item().build()`，并补 `assets/simulated/items/merging_glue.json`（指向 `simulated:block/merging_glue/block`）+ `item.simulated.merging_glue` 中英 lang |
| `simulated:absorber` | 上游注册代码**整段被注释**（WIP） | 未注册 | ❌ | 不是缺口（上游有意未启用） |
| `simulated:extendo_grip` | **不属于 simulated**（上游只有 `ExtendoGripItemMixin`/`ExtendoGripRenderHandlerMixin` 两个 mixin，作用于 Create 的 `com.simibubi.create.content.equipment.extendoGrip.ExtendoGripItem`） | 只有 mixin | Create 侧 item | 不是缺口；要测的是 `create:extendo_grip` |

## 2. 资源缺口

- 源码树原先**没有** 26.3 的 `assets/<ns>/items/*.json`（物品定义）⇒ 源码构建会丢物品图标；已把 live 里的 145 个定义拷回源码资源（simulated 99 + aeronautics 46），源码构建现在可复现。
- `merging_glue` 新增物品定义（上面）——这是本轮唯一新增资源。

## 3. 本轮候选

| 项 | 值 |
|---|---|
| 候选 | `work/run26/port/g76/out/aeronautics-fabric-0.1.0-port.26.3-itemfunc-r6.jar` |
| size / SHA | 31,599,467 B / `0e94b691c035f7343d9e0cfcf4abc7134c46b874325d90d9fe23cb27c5167ce6` |
| base | live `455B5824` |
| changed | `dev/simulated_team/simulated/index/SimBlocks.class` + `assets/simulated/lang/{en_us,zh_cn}.json`（live lang 基础上仅加 1 key） |
| added | `assets/simulated/items/merging_glue.json` |
| staging | `work/run26/port/g76/stage/mods-itemfunc-r1` |

## 4. 待 probe 验证

1. `simulated:merging_glue` 物品存在（创造/搜索可见、名字「黏合胶 / Merging Glue」）、可放置为方块、方块可被使用（黏合行为）；
2. `simulated:honey_glue`：Alt+右键两次 → BINDING → 生成胶实体（0 crash）；
3. `simulated:creative_physics_staff`：右键/拖拽有反应（客户端 handler 生效）；
4. `simulated:plunger_launcher`：右键发射（0 crash）；
5. `simulated:contraption_diagram`：使用无异常（已在 live 验证，回归项）。

## 5. 已知遗留

- `HoneyGlueItem.canAttackBlock`：26.3 `Item` 无此钩子，等价行为需 `InteractCallback`/`BlockPlaceContext` 侧实现（客户端 handler 已接管 attack，实测为准）。
- `simulated:absorber`：上游未启用，不补。
- `create:extendo_grip`：Create 侧，若无效属 Create 移植问题，不属 simulated。
## 6. R453 · merging_glue 放置即消失（probe 反馈）修复

**根因**：`MergingGlueBlock extends DirectionalBlock`，但既没有覆盖 `getStateForPlacement`（vanilla `DirectionalBlock` 不提供），又未在注册时给默认朝向语义 ⇒ 放置后 `FACING=NORTH`，`canSurvive → canAttach(level,pos,getConnectedDirection=NORTH.getOpposite=SOUTH)` 检查的是**南边邻居**；平地上南边是空气 ⇒ `updateShape` 立刻返回 AIR（探针 `placed=1/1` 后即 air）。

**修法**（源码）：`MergingGlueBlock.getStateForPlacement` 返回 `defaultBlockState().setValue(FACING, context.getClickedFace())` ⇒ `getConnectedDirection()` 指向被点击的支撑方块内部，`canSurvive` 成立。

**候选 r7**：`g76/out/aeronautics-fabric-0.1.0-port.26.3-itemfunc-r7.jar`，31,599,574 B / `85cccbb33f7ab12bd1978d8934d5eb7b5a7e8bd28fbda4d5a7579e5e4277f4bb`，base `455B5824`；changed = `SimBlocks.class` + `MergingGlueBlock.class` + 2 个 lang（只加 1 key）；added = `assets/simulated/items/merging_glue.json`；staging `g76/stage/mods-itemfunc-r2`。

## 7. 程序化触发方法（给 probe）

### honey_glue（绕过 Alt 合成）
- 代码里 Alt 判定：`Minecraft.getInstance().hasAltDown()`（`HoneyGlueClientHandler.onUse` 内）；探针无法合成按键状态。
- **直接入口**：`dev.simulated_team.simulated.index.SimClickInteractions.HONEY_GLUE_MANAGER`（public static 字段，类型 `HoneyGlueClientHandler`）
  - 第 1 次：`selectPos(pos1, player, player.getItemInHand(InteractionHand.MAIN_HAND))` → `currentState=BINDING`、播放 HONEY_ADDED 音效、返回 true；
  - 第 2 次：`selectPos(pos2, ...)` → 走 `checkBBValidity`，通过则 `VeilPacketManager.server().sendPacket(new HoneyGlueSpawnPacket(pos1,pos2))` → 服务端 spawn `HoneyGlueEntity`，状态回 UNBOUND。
  - 选点需满足：两个面互相朝向（`invalid_directions.*` 校验）、不同 sublevel、范围内、有支撑。
  - 若第 2 次返回 false，日志/返回值即可判定是哪条校验失败（方法内每种失败都有对应 lang key 路径）。

### creative_physics_staff（需要拖拽，不是单击）
- `simulated:creative_physics_staff` 是「物理手杖」：`PhysicsStaffClientHandler` 的语义是 **按下右键 → startDraggingSubLevel/lockSubLevel → onMouseMove/setDistance/onScroll 拖拽 → 松开结束**；单击无观测行为属预期。
- 程序化入口：`SimulatedClient.PHYSICS_STAFF_CLIENT_HANDLER`（public static）→ `onUse(modifiers, GLFW_PRESS, rightKey)` 需要玩家准星对着 sublevel 方块；随后调用 `dragSubLevel()`/`setDistance(x)`/`onMouseMove(yaw,pitch)`，最后 `onUse(..., GLFW_RELEASE, ...)` 或 `onItemUsed(PhysicsStaffAction)`。
- 判据：出现选择框/光束（`onRender`）或 server drag session 变化。

### plunger_launcher（服务端动作）
- `PlungerLauncherItem.use` 只在 `!level.isClientSide()` 分支生成 `LaunchedPlunger`，客户端 `res=ok` 属预期；探针应在**服务端**调用或检查服务端实体列表。
- 潜行+右键 = 清空自己的 plunger（overlay 提示 `plunger_launcher.clear_plungers`），可作区分性验证。
