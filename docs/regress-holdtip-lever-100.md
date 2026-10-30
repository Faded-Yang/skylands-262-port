# 组装器/拉杆 视觉+进度条回归（R-hold）

> DOCS FIRST：`docs/fix-hold-all.md`（R429/R432 startHold 护栏）、`docs/fix-hold-ui.md`（HoldTip 垫片）、`docs/DELIVERY.md`（R422 拉杆渲染/R426 hold 提示/R427 进度条 blit→sprite/R429 按住重置/R432 startHold 加固）。

## 结论（根因）

**Fabric 客户端入口没有绑定 `postClientTick` / `renderOverlays` 两个事件**：

- `work/aero-port/aeronautics-26/src/fabric/java/dev/simulated_team/simulated/fabric/SimulatedFabricClient.java` 只调用 `SimulatedClient.init()`；
- 因此 `SimulatedCommonClientEvents.postClientTick()` 从不执行 ⇒ `HoldInteractionManager.tick()` 从不执行；
- `HoldInteractionManager.renderOverlay()` 也从不执行 ⇒ 进度条从不绘制。

## 逐项

| 现象 | live 是否有补丁 | 为何失效 | 26.3 管线 | 修法 |
|---|---|---|---|---|
| 物理组装器按住无进度条 | 有 `PhysicsAssemblerGUIHandler.renderOverlay`（R427 的 GUI fill 路径），类 hash 与 `.bak-r455/r464/r690/r740` 相同 | `SimulatedCommonClientEvents.renderOverlays` 无 Fabric HUD 订阅 ⇒ 方法不可达 | 26.3 用 `HudElementRegistry/HudElement`（`extractRenderState(GuiGraphicsExtractor, DeltaTracker)`） | 在 `SimulatedFabricClient` 注册 `HudElementRegistry.addLast` → `renderOverlays` |
| 组装器拉杆不实时变化 | 有 `activeTick` → `updateControlledByPlayer` → BE `playerAngle`/`visualAngle`；类 hash 相同 | `postClientTick` 无 Fabric tick 订阅 ⇒ `activeTick` 从不执行；只有 `activeOnMouseMove` 执行（音效正常、fraction 变），松手 `release()` 才直接设角度 ⇒ 瞬间拉满回弹 | 26.3 客户端 tick 用 `ClientTickEvents.END_CLIENT_TICK` | 注册 `END_CLIENT_TICK -> postClientTick` |
| 油门/动力拉杆位置实时但无进度条 | 其渲染/输入走自身 client grip，可能不依赖 HoldInteraction overlay | 同一 HUD 未绑定问题（overlay 不画） | 同上 | 同一 HUD 注册即可 |

## 候选

| 项 | 值 |
|---|---|
| 文件 | `work/run26/port/g139/out/aeronautics-fabric-0.1.0-port.26.3.jar` |
| 变化 | 仅 `dev/simulated_team/simulated/fabric/SimulatedFabricClient.class`（2624 B） |
| SHA-256 | `309e81b2a86502d530457dca1a76b746274f274da0d30aedfde1fa73cb15320e` |
| staging | `work/run26/port/g139/stage-final/mods-candidate`（115 jar，aero 同名替换） |

## 验证

- 起局放置 `simulated:physics_assembler`，按住右键上下拖：应出现右侧竖直进度条且 lever 实时转动；
- 松手应停止/回弹正常，无瞬间跳满；
- 油门杆同样有 overlay；0 crash、0 registry error。
