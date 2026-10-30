# fix-assembler-lever —— 物理组装器缺「拉杆」渲染（task-29 / R421）

> 现象（用户截图）：放下 `simulated:physics_assembler` 后**没有应有拉杆**，且“右键没反应”。
> 本轮只修**缺拉杆**；交互另附静态确认（§4）。

---

## 1. 根因（静态证据）

1. **BE renderer 是桩**：live `aeronautics-fabric-0.1.0-port.26.3.jar`（`6D435F98…`）里
   `dev/simulated_team/simulated/content/blocks/physics_assembler/PhysicsAssemblerRenderer.class` 只有 485 B：
   `public PhysicsAssemblerRenderer(Object... args)` 仅调 `Object.<init>`，**没有实现 BlockEntityRenderer、没有绘制代码**。
2. **注册路径也断了**：`SimBlockEntityTypes` 的 `PHYSICS_ASSEMBLER` 确实调了
   `BlockEntityBuilder.renderer(Supplier)` → 工厂 lambda new `PhysicsAssemblerRenderer(Object[])`，
   但移植的 registrate 垫片 `BlockEntityBuilder.renderer(...)` 是**空实现** ⇒ 从未进 `BlockEntityRenderers`。
3. **资源和数据都在**：`assets/simulated/models/block/physics_assembler/lever.json`（knob + lever 两元素）、
   `SimPartialModels.ASSEMBLER_LEVER`（PartialModel 字段）、`PhysicsAssemblerBlockEntity.getClientAngle(float)`（public，返回 visualAngle 插值角度）都在。
4. 原始实现可参考：`work/aero-port/_backups/excluded-wip/PhysicsAssemblerRenderer.java.bak-r87`（Create `SmartBlockEntityRenderer` + `CachedBuffers.partial(ASSEMBLER_LEVER)` + `rotateCentered` 变换）。

---

## 2. 修法（26.3 extract/submit 重写）

新增 3 个 class 到 aeronautics jar：

| class | 作用 |
|---|---|
| `skylands262.compat.PhysicsAssemblerLeverRenderer` | 实现 `BlockEntityRenderer<PhysicsAssemblerBlockEntity, LeverRenderState>` |
| `skylands262.compat.PhysicsAssemblerLeverRenderer$LeverRenderState` | extends `BlockEntityRenderState`，字段 `blockState` / `SuperByteBufferRenderState handle` |
| `skylands262.compat.PhysicsAssemblerRenderBootstrap` | `ClientModInitializer`，`BlockEntityRendererRegistry.register(SimBlockEntityTypes.PHYSICS_ASSEMBLER.get(), PhysicsAssemblerLeverRenderer::new)` |

绘制逻辑（照抄原始公式，换成 26.3 的 extract/submit 两段式）：
- `extractRenderState`：`SmartBlockEntityRenderer.extractBase(be, state, crumbling)` 取 Level →
  `getCardinalLighting(level)` → `CachedBuffers.partial(SimPartialModels.ASSEMBLER_LEVER, state.blockState)
   .cardinalLighting(cl).light(state.lightCoords)` →
  `transform(handle, state.blockState)`（`rotateCentered`：FACING→UP 轴、FACE：floor 0 / wall 90 / ceiling 180→EAST 轴）→
  `translate(.5, 7/16, .5).rotate(angle, Direction.EAST).translate(-.5, -7/16, -.5)` →
  `handle.extractRenderState()` 存进 render state；`angle = toRadians(be.getClientAngle(partialTick))`。
- `submit`：`state.handle.submit(poseStack, collector)`（Fabric/26.3 的 submit 管线）。
- 注册用 **Fabric API** `BlockEntityRendererRegistry`（26.3 的 vanilla `BlockEntityRenderers.register` 已是 private；fabric-rendering-v1 提供公开入口）。

---

## 3. 候选与验证

| 项 | 值 |
|---|---|
| 基线 | live `aeronautics-fabric-0.1.0-port.26.3.jar` = `6D435F98…`（31,554,422 B） |
| 候选 | `work\run26\port\g46\out\aeronautics-fabric-0.1.0-port.26.3-assemblerlever.jar` |
| size | **31,558,749 B** |
| SHA-256 | `e62355e1b590aa175420d5d4b2cd12cf764ab327651bab462d3196429dbbc8ed` |
| entry diff | **4 个**：`fabric.mod.json`（entrypoints.client +1）+ 3 个新增 class；其它 entry 逐字节不变、顺序不变 |
| 静态验证 | `g46\out\_static_verify.txt` **PASS**（entry diff=4、3 class=编译产物、entrypoints 只加 bootstrap、javap 接口正确、`-Xverify:all` 冒烟 SMOKE_OK） |

staging（atomic：temp + `os.replace`；改的件 copy、未改件 hardlink）：
- `g46\stage\mods-baseline`：aeronautics = `6D435F98`（live 71 jar）
- `g46\stage\mods-candidate`：aeronautics = `E62355E1`；sable=`59280C1E`、create-fly=`595B5EB8`
- 重建：`python work\run26\port\g46\_mkstage.py baseline|candidate <dir>`

A/B（probe）：
1. 两臂各放一个 `simulated:physics_assembler`（创造物品栏或 give；**等物品同步**后放置）；
2. 截图（同一机位/朝向）：基线应**没有拉杆**（只有方块本体）；候选应出现 **knob+lever 杆**，朝向随 FACE/FACING；
3. 按住右键拖拽（或让组装器进入 hold/flick 状态）→ 候选拉杆角度应随 `getClientAngle` 变化（动画）；基线无变化；
4. 抓日志：候选应有 `[skylands262] physics_assembler lever renderer registered (fabric BlockEntityRendererRegistry)`；
5. 0 crash-report、其它方块 BE 渲染无回归。

风险/注意：
- 我们只补 renderer + 显式注册；**stub `PhysicsAssemblerRenderer` 保留原样**（未删，避免动 SimBlockEntityTypes 的 lambda）。
  若以后 registrate 垫片 `renderer()` 被真正实现，可能与我们的显式注册**重复**（BlockEntityRenderers 重复注册会抛异常）——届时删掉 bootstrap 里那行或实现 shim 时合并。
- 拉杆变换是从 1.21 原始公式直译（rotateCentered 的轴/顺序）；若 A/B 看到拉杆**位置/朝向偏**，按截图调 transform 顺序即可（模型 `lever.json` 是 32×32 贴图、原点 8,7,8）。

---

## 4. 交互（“右键没反应”）静态确认

- live aeronautics `6D435F98` 的 `dev.simulated_team.simulated.fabric.SimulatedFabricClient` 仍注册
  `ClientTickEvents.START_CLIENT_TICK` / `END_CLIENT_TICK`；class 扫描显示 `SimulatedFabricClient` 与
  `SimulatedCommonClientEvents` 仍引用 `preClientTick`/`postClientTick` ⇒ **交互钩子没丢**。
- 结合 R409/task-22：组装器是**按住右键拖拽**（hold_tip「按住并拖拽以组装」，进度 0→1.000 才发 assemble 包）；
  **单击右键**不会触发组装 ⇒ 用户“右键没反应”很可能就是单击 vs 按住拖拽的差异（另见 task-29 分工：交互逻辑本身探针已 PASS）。
- 探针可顺手对照：单击（应无进度）/ 按住拖拽到 fraction=1.000（应有进度并组装）。


---

## 5. A/B 结果（interact-probe，2026-10-18 23:0x）：**PASS（可 promote）**

staging：base aero `6D435F98` / cand `E62355E1`；sable `59280C1E`、create-fly `595B5EB8`；全新存档。
探针 phase L：同场景放 3 个物理组装器（floor/wall/ceiling, facing=north），相机对准 floor。

| 项 | 基线 | 候选 |
|---|---|---|
| 日志 `physics_assembler lever renderer registered` | 0 | **1** ✓ |
| 拉杆可视 | 方块本体，无 lever/knob | **knob + 木质拉杆可见**（截图对比明显） |
| 角度随进度 | — | 单击时竖直；hold30（fraction≈0.388）明显倾斜；按住到 1.000 release 后 `getClientAngle` 生效 ✓ |
| 单击（不拖拽） | managerActive=true，fraction 恒 **0.000** | 同左（单击无进度）|
| 按住拖拽 | 0.053→0.162→0.388→0.727→0.902→0.982→**1.000** 后释放 | 同左 |
| crash / RAPIER | 0 / ×3 | 0 / ×3 |

截图（整窗 + 裁剪）：`g33/lever-base.png`、`lever-base-zoom.png`（无拉杆）；
`g33/lever-cand-click.png`、`lever-cand-hold30.png`、`lever-cand-*-zoom.png`（有拉杆，两张角度不同）。

**唯一未做**：wall/ceiling 的**朝向**视觉对比（三块都放置成功，L_STATE 记录 `face=wall/ceiling`，但本轮相机只对准 floor）。
⇒ 已请 probe 补一轮专门对 wall/ceiling 的截图（可指定相机方位）；若朝向有偏，按 FACE/FACING 的 rotateCentered 顺序微调。

**交互侧**：本轮同时证实「单击 fraction 恒 0 / 按住拖拽才到 1.000」⇒ 用户“右键没反应”就是单击 vs 长按拖拽，**不是 bug**。


---

## 6. promote 状态（2026-10-18 23:00，Lead）

- Lead 用原子替换 promote：live aeronautics = `E62355E1`（31,558,749 B，mtime 23:00:27）；
- 备份链：**.bak-r422 = `6D435F98`**（promote 前的 wakefix live）；
- 标题回归通过（Lead 记录）；task-29 标记完成；
- 用户可见效果：放置 `simulated:physics_assembler` 后**出现 knob+木质拉杆**；按住右键拖拽时拉杆角度随进度变化；单击不组装（要按住拖拽到 fraction=1.000 再松手）——这是正常交互，不是 bug。
- 仍待补（不阻塞）：wall/ceiling 的拉杆**朝向**视觉对比（floor 已 PASS；若朝向偏按 FACE/FACING 的 rotateCentered 顺序微调）。


---

## 7. wall / ceiling 朝向补测（interact-probe，2026-10-18 23:1x）：**三分支全部正常**

- **ceiling**：组装器吊在石块下方，lever/knob **朝下伸出**、贴合 face=ceiling，无穿模 → `g33/lever-ceiling.png`；
- **wall**：组装器贴石块侧面，knob+拉杆**从墙面朝外（north）伸出**、贴合 face=wall+facing=north，无朝侧面/穿模 → `g33/lever-wall.png`；
  （第一轮相机打进树叶是废片 `lever-wall-badcam.png`，改从北侧 (2,1.5,-2.5) 看后正常。）
- 结论：FACE=floor/wall/ceiling 三分支的拉杆朝向都符合预期，**`rotateCentered` 顺序不需要调**；task-29 全部收口（floor + wall + ceiling + 角度动画 + 注册锚点）。
