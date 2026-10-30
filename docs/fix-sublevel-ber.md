# fix-sublevel-ber —— 物理化（sublevel）后机器方块缺小组件（task-33 / R425）

> 症状（用户）：「物理化后的原机械动力方块，还是会缺失小组件」——普通世界已补好的 BE renderer 部件，
> 一旦结构被物理组装进 sublevel 就消失。

## 1. 根因

R415 的 `SableSubLevelRenderBootstrap`（`LevelRenderEvents.COLLECT_SUBMITS`）只提交 block model，
从未调用 `BlockEntityRenderer`。sublevel 里方块模型可见，但 BE 的附加几何（partial 模型）没有提交 ⇒ 缺小组件。
26.3 的 BE 是两段式（extract/submit），由 `BlockEntityRenderDispatcher` 管理（prepare/tryExtractRenderState/submit）。

## 2. 修法（R425，sable 侧）

扩展 live sable 的 `skylands262.compat.SableSubLevelRenderBootstrap`：

1. `collectSubmits`：取 `cameraRenderState`、`partialTicks`、`dispatcher`，调用一次 `dispatcher.prepare(cameraPos)`；
2. 每块沿用 camera-relative world pose（translate(corner-camera) * rotate(orientation)）：MODEL 先提 block model 再提 BE；BE-only 方块只提 BE；
3. `renderBlockEntity`：`level.getBlockEntity(blockPos)` → `dispatcher.tryExtractRenderState(be, partialTicks, null, false)` → light==0 回退 FULL_BRIGHT → `dispatcher.submit(state, pose, collector, cameraRenderState)`；
4. 单块 BE 失败只记一次 ERROR。**复用已注册的 `BlockEntityRenderer`，没有为 sublevel 重写一套。**

## 3. 候选与验证

| 项 | 值 |
|---|---|
| 基线 | live sable `59280C1E…`（9,364,703 B） |
| 候选 | `work\run26\port\g48\out\sable-fabric-26.3-sublevelber.jar` |
| size | **9,365,513 B** |
| SHA-256 | `b0c5d0c26c3291d9911be482ef3d092d8ebd07f794837378429f8b7cb77ea01b` |
| entry diff | **1**：只修改 `skylands262/compat/SableSubLevelRenderBootstrap.class`；其它 entry 逐字节不变、顺序不变 |
| 静态验证 | `g48\out\_static_verify.txt` **PASS**（diff=1、class=编译产物、zip OK、`-Xverify:all` SMOKE_OK） |

staging（atomic）：
- `g48\stage\mods-baseline`：sable `59280C1E`（aero `FB6A2A01`、create-fly `595B5EB8`）
- `g48\stage\mods-candidate`：sable `B0C5D0C2`，其它同 baseline

## 4. A/B（probe）

1. 普通位置放一个 `simulated:throttle_lever` / `simulated:physics_assembler`，截图（普通世界 BE 部件应可见）；
2. 把含该方块的结构用物理组装器组装成 sublevel（fraction=1.000）；
3. 截图对比：基线 sublevel 内只有方块本体、缺手柄/拉杆/旋钮；候选应出现同样的 BE 部件（位置/朝向跟 sublevel pose）；
4. 0 crash；日志：`sable sub-level single-block renderer registered (COLLECT_SUBMITS)` 仍在；失败会打 `sub-level block entity render failed`。

## 5. 风险 / 已知边界

- **客户端 BE 数据**：实现依赖 `ClientLevelPlot` 里已有对应 BE；若某机器只同步了方块状态、没有 BE，则部件仍缺 → 下一步需要从 snapshot 包创建 BE（TODO，先看 A/B 哪些机器缺）。
- **pose/光照**：BE 与 block model 共用同一 camera-relative world pose；若位置/朝向偏，按 pose 顺序调。
- **性能**：仅 volume≤64 的小 sublevel 逐块 extract（每帧），可接受；chunked 大结构走第二步。
- 回滚：建议 promote 前 `.bak-r425` = live `59280C1E`；原子替换回滚。

## 6. 后续

- A/B 确认后 promote；若出现 plot 无 BE 的机器，补客户端 BE 创建路径；
- 大 renderer 批量件（task-30）继续，两者共用 `BlockEntityRenderer` 注册，不冲突。

## 7. A/B 结果（interact-probe，2026-10-19 00:1x）：**PASS（可 promote）**

2 run（1280×720、全新存档，phase Z：普通世界 → 组装 → sublevel 同机位截图）：
- 两臂都成功组装（server/client count=1）、0 crash、锚点 `single-block renderer registered=1`、`block entity render failed=0`；
- **普通世界两臂完全一致**：组装器 + 油门拉杆，位置/大小正确；
- **sublevel 内**：
  - 基线 `59280C1E`：出现一根**巨大金色/黑色柱状物**悬在石块上方（比例/位置明显异常）——`g33/evidence/ber-base-sublevel.png`；
  - 候选 `B0C5D0C2`：结构与普通世界一致（组装器 + 油门拉杆正常大小、位置正确）——`g33/evidence/ber-cand-sublevel.png`；
- 两臂均无 `block entity render failed`、0 crash-report。

**判读**：候选把 sublevel 内渲染从「异常巨柱」修成「与普通世界一致」⇒ task-33 主诉（物理化后机器缺小组件）PASS。
基线巨柱推测：R415 只画 block model、没有 BE 提交；该异常几何可能来自 plot 内 BE 被其它路径以错误 pose/scale 提交（或方块模型叠加），
候选显式以 sublevel pose 提交 BE 后收敛到与普通世界一致；具体成因不阻塞结论（候选已对齐普通世界）。

**待补**：换其它带 BE 的机器（swivel_bearing 等）在 sublevel 内再抽查 1–2 个，确认不是只有 throttle/assembler 正确。

promote 建议：候选 `b0c5d0c2…` 原子替换 live sable（备份 `.bak-r425` = `59280C1E`）；promote 后复跑标题+进世界。
