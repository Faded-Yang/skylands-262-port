# glue-viz —— 强力胶/蜂蜜胶「可视粘连范围」（用户新需求）

> **状态（2026-10-18 裁决）：sky262-glueviz 未采用 —— 蜂蜜胶的 tick 驱动已由 aeronautics g32 候选补上（§1.3）。**
> ⚠ **g32 仍是候选**（`g32/out/*-g32.jar`，未 promote、未 A/B）：**在它 promote 之前，当前交付件的蜂蜜胶仍然没有 tick**，
> 因此 glueviz 先**保留为兜底**、不删；若 g32 promote 成功则 glueviz 永久退场（两者禁止共存，否则 handler 双 tick）。
> 强力胶本来就有显示。**本 mod 只补 tick、不含任何 render**（render 走 create-fly 既有 Outliner，与 g32 无关，见 §1.4）。
> 本轮未启动游戏；**未改 mods-stable / watch / create-fly / sable**。

- 任务板：`task-21`（owner crashfix-26）
- 交付目录：`work/run26/port/g36/`（src / out / out/evidence / stage / 脚本）

---

## 0. 结论一句话

- **强力胶（create:super_glue）**：当前交付里**本来就有**完整实现（粘时选择框预览 + 粘后手持物品显示已粘范围），静态调用链完整（§1.1）。
- **蜂蜜胶（simulated:honey_glue）**：渲染代码**存在且已注册**（`HoneyGlueClientHandler` 在 `SimClickInteractions.HONEY_GLUE_MANAGER`），
  原交付里**每 tick 的驱动丢失**（`SimulatedCommonClientEvents.postClientTick` 在全部 71 jar 里零调用者，§1.2）。
- **该缺失已由 aeronautics g32 候选补上**（neo-auditor task-16）：`SimulatedFabricClient` 注册了
  `ClientTickEvents.START/END_CLIENT_TICK` → `preClientTick/postClientTick`，而 postClientTick 遍历
  `SimClickInteractions.CLICK_INTERACTION_ENTRIES`（含 `HONEY_GLUE_MANAGER`）逐条调 `clientTick` ⇒ 蜂蜜胶可视化恢复（§1.3）。
- 结论：**不需要 sky262-glueviz**（再加会 double-tick）；它只作为备选保留。

---

## 1. 现状调查（可复跑证据：`out/evidence/03_static_analysis.txt`）

### 1.1 强力胶：已具备（create-fly 内部）

| 环节 | 证据（javap） |
|---|---|
| 选择 handler 被 new 并挂到静态字段 | `Create.onInitializeClient`：`new SuperGlueSelectionHandler` → `putstatic Create.GLUE_HANDLER` |
| handler 每 tick 被调用 | client `MinecraftMixin.tickPost`（`Minecraft.tick()V` TAIL）调用 `SuperGlueSelectionHandler.tick(Minecraft)` |
| **已粘范围与选择框的渲染** | `SuperGlueSelectionHandler.tick` 里遍历 `SuperGlueEntity`，对每个实体调 `Outliner.showAABB(entity, entity.getBoundingBox())`（类里共 2 处 showAABB：选择框 + 已有胶盒；选中的高亮色 6866310 / 普通 5083490） |
| Outliner 的 actually-render | client `LevelRendererMixin` 在 `@Inject(method="submitFeatures(...)", at=INVOKE target="Lnet/minecraft/client/renderer/LevelRenderer;finalizeGizmoCollection()V")` 里 `Outliner.submitOutlines(...)`；26.3 的 `LevelRenderer.submitFeatures` 仍在偏移 96 调用 `finalizeGizmoCollection()` ⇒ 注入点存在 |

⇒ 手持 `create:super_glue`（主手/副手）时，**已粘范围**会画出来；右键选择过程中会画**预览框**。

### 1.2 蜂蜜胶：逻辑/注册都在，但 tick 驱动丢失

| 环节 | 证据 |
|---|---|
| handler 已注册 | `SimClickInteractions` 静态初始化：`new HoneyGlueClientHandler()` → `register(...)` → `putstatic HONEY_GLUE_MANAGER` |
| 渲染逻辑完整 | `HoneyGlueClientHandler.clientTick(Level, LocalPlayer)` 调 `renderSelection(...)`（选择预览）+ `renderHoneyGlue()`（已有 `HoneyGlueEntity` 的 AABB，`Outliner.showAABB/chaseAABB`，颜色 `SimColors.ACTIVE_YELLOW/PERCHANCE_ORANGE`，带 `HONEY_GLUE` 面纹理） |
| **驱动缺失** | 上游靠 `SimulatedCommonClientEvents.postClientTick` 遍历 `CLICK_INTERACTION_ENTRIES` 调每个 handler 的 `clientTick`。**全 71 jar 扫描：`preClientTick`/`postClientTick` 的 Methodref = 0**（只有该类自身与 Keyboard/Mouse mixin 引用这个类，但那两个 mixin 调的是输入类回调）；也没有 Fabric client-tick 事件注册 |

⇒ 这属于台账里反复出现的「**已有但没接上**」：渲染与注册都在，移植丢了一个 tick hook。

### 1.3 后续：aeronautics g32 候选已补上这组钩子（glueviz 因此冗余）

证据（可复跑：`out/evidence/05_g32_overlap.txt`；被检对象 `g32/out/aeronautics-fabric-0.1.0-port.26.3-g32.jar`，
SHA `e290f9db…5a940`）：

- g32 的 `SimulatedFabricClient.onInitializeClient` 里，`ClientTickEvents.START/END_CLIENT_TICK.register` 的
  lambda 实现方法（BootstrapMethods 的两条 `REF_invokeStatic` MethodHandle）正是
  `SimulatedCommonClientEvents.preClientTick` / `SimulatedCommonClientEvents.postClientTick`；
- g32 的 `AeronauticsFabricClient` 同时注册 START/END tick → `AeronauticsClientEvents.clientLevelTick`；
- 26.3 交付的 `SimulatedCommonClientEvents.postClientTick` 的字节码：遍历
  `SimClickInteractions.CLICK_INTERACTION_ENTRIES` → 对每个 `InteractCallback` 调
  `InteractCallback.clientTick:(Level, LocalPlayer)V`；而 `SimClickInteractions` 静态初始化把
  `HoneyGlueClientHandler` 注册成 `HONEY_GLUE_MANAGER` 放进这个集合。

⇒ **g32 单独就能每 tick 驱动蜂蜜胶 handler** ⇒ 蜂蜜胶"粘时预览 + 粘后手持查看"恢复；**sky262-glueviz 冗余，不 promote**。
（如果两者同时装：蜂蜜胶 handler 每 tick 被调两次 = 双份 Outliner 刷新 + handler 内部状态/音效副作用，禁止共存。）

**边界（重要）**：
- g32 目前**只是候选**（未 promote、未 A/B）。**在 g32 promote 之前，交付件里的蜂蜜胶依然没有 tick**；
  所以 glueviz 保留作兜底，等 g32 promote 后再退场。
- g32 覆盖的是 **tick 驱动**；本 mod 也**只有 tick 驱动**，没有任何世界渲染代码。两边的 render 都走
  create-fly 既有的 Outliner（§1.1 第 4 行，已在当前交付件里），**不依赖 g32**。

> **交叉记录**：neo-auditor 的 `docs/diag-physics.md` §3.3 末尾「联动（crashfix-26 交叉确认）」也记录本互斥关系
> （g32 未 promote 前 glueviz 兜底、promote 后永久退场；glue 的 render 走 create-fly 既有 Outliner、与 tick 无关），
> 并已撤回"glueviz 有 render 代码"的说法；`onServerTickEnd`（redstone magnet / docking connector）留在其 §6 同族缺口列表、由 lead 排期（与 glue 无关）。

### 1.4 tick 与 render 的分工（回应「render 部分是否要单独保留」）

| 部分 | 归属 | 当前交付件里是否存在 | 说明 |
|---|---|---|---|
| 世界渲染管线（把线框真正画出来） | **create-fly** client `LevelRendererMixin` → `Outliner.submitOutlines`（INVOKE 26.3 仍存在的 `LevelRenderer.finalizeGizmoCollection()`） | ✅ 已有（create-fly 已 promote 的 `64b68869…`） | 与 g32 无关；蜂蜜胶/强力胶共用 |
| 强力胶 tick + 已粘/选择框逻辑 | **create-fly** `SuperGlueSelectionHandler`（由 client `MinecraftMixin.tickPost` 驱动） | ✅ 已有 | 本来就有 |
| 蜂蜜胶 tick + 已粘/选择框逻辑 | **aeronautics** `HoneyGlueClientHandler`（由 `SimulatedCommonClientEvents.postClientTick` 驱动） | ❌ 原交付缺 tick（handler/渲染代码在） | g32 候选补上；未 promote 前可用 glueviz 兜底 |
| glueviz 自身 | 我们的客户端 mod | 只有 tick 驱动 | **没有 render 代码**，所以不存在「render 部分需要单独保留」的情况 |

---

## 2. 方案：客户端小 mod `sky262-glueviz`（**未采用**；仅备选，见 §1.3）

- `ClientModInitializer` 注册 Fabric `ClientTickEvents.END_CLIENT_TICK`；
- 每 tick（player/level 非空时）调用已经注册好的
  `SimClickInteractions.HONEY_GLUE_MANAGER.clientTick((Level) level, player)`；
- 只驱动**蜂蜜胶** handler（最小化）：不驱动其它同样丢失 tick 的 click-interaction handler（merging glue / rope / zipline / hold interaction …，见 §5.4）；
- 自身**不画任何东西**：渲染仍由 handler 走 create 的 `Outliner`（与强力胶同一条管线，已确认在 26.3 接通）；
- 健壮性：`try/catch (Throwable)` + 日志；handler 为 null 时 warn 一次；`client == null` 保护（冒烟里反射验证过）；
- 诊断日志（给探针）：初始化一行；之后每 200 tick 一行
  `[glueviz] alive ticks=N holdingHoneyGlue=... honeyGlueEntitiesNearby=...`。

---

## 3. 交付件

| 项 | 路径 | size | SHA-256 |
|---|---|---|---|
| **候选 mod** | `work/run26/port/g36/out/sky262-glueviz-1.0.0.jar` | 2,661 B | `64d9a4c540b4457bb34f2789bd44a38038dd78e9116788ede17abc34db080289` |

- jar 内容：`fabric.mod.json` + `skylands262/glueviz/GlueVizClient.class`（仅 2 entries，无 mixin、无 assets）。
- `fabric.mod.json`：id `sky262glueviz` / version `1.0.0` / environment `client` /
  entrypoint `client: ["skylands262.glueviz.GlueVizClient"]` / depends：`fabricloader >=0.15.0`、`fabric-lifecycle-events-v1`、`aeronautics`。
- staging（硬链接，mods-stable 未写）：
  - 基线：`work/run26/port/g36/stage/mods-baseline`（71 jar）
  - 候选：`work/run26/port/g36/stage/mods-glueviz`（72 jar = 71 + `sky262-glueviz-1.0.0.jar`）
- promote 方式：把该 jar 加进 mods-stable（71 → 72 jar），**不需要改任何现有 jar**。
- **裁决：不 promote**（被 aeronautics g32 覆盖，见 §1.3）。候选件保留在 `g36/out` 以便将来 g32 方案失效时启用；
  启用时必须同时移除 g32 的 ClientTick 钩子（否则蜂蜜胶 double-tick）。

---

## 4. 验证口径（给 lead/探针；本文件作者未启动游戏）

> **裁决后：蜂蜜胶可视化应在 r408 组合包（含 aeronautics g32）里验证，而不是用 mods-glueviz。**
> 推荐：同一组合包下（a）手持 `simulated:honey_glue` 看已粘范围是否出现（修复前没有）；（b）手持
> `create:super_glue` 看已粘范围（本来就有）。glueviz 的日志只在其被安装时出现，不作为判据。

1. （若单独测 glueviz 备选）用 `mods-glueviz` 启动进世界；日志应出现
   `[glueviz] init: client tick driver ...` 与周期性 `[glueviz] alive ticks=...`。
2. **强力胶（对照现有功能）**：两块相邻方块用 `create:super_glue` 粘好；之后**主手或副手持 super_glue** 对着该区域：
   应看到已粘范围的线框盒子（选中/未选中有两种颜色）；粘的过程中（右键选择）应看到预览框。
3. **蜂蜜胶（本修复）**：用 `simulated:honey_glue` 粘好方块；之后**手持 honey_glue** 应看到已粘范围盒子
   （修复前完全不显示）；选择/绑定时应看到预览框与悬停高亮。
4. **对照**：`mods-baseline`（71 jar）下蜂蜜胶**没有**这些线框（handler 不 tick）；强力胶两种都应该有。
5. 建议探针记录：截图 + `[glueviz]` 日志行 + 手持物品 id；可选反射 `Outliner.getInstance().getOutlines()` 的 key 数做量化
   （蜂蜜胶的 slot key 含 `"HoneyGlue"` / 实体 id）。

---

## 5. 风险 / 不确定（**必读**）

1. **未实测**：本轮只有静态链 + 类加载冒烟；A/B 由探针做（且改用 g32 组合包，见 §4）。
2. **强力胶「已具备」是静态结论**：调用链、注入点都核对到 26.3 现存方法；但若 A/B 发现强力胶也没显示，
   说明运行期 Mixin 注入被跳过（例如等级/插件过滤），下一步 = 在我们自己的 mod 里用同一 `Outliner` 直接画
   （或改用 26.3 `WorldRenderEvents`），需另开一轮。
3. 我们的驱动让蜂蜜胶 handler **每 tick 跑**（与上游一致）；若 handler 内部有其它未移植依赖，会被 try/catch 兜住并记日志，**不会崩客户端**。
4. **范围限制（glueviz 方案自身的）**：它只驱动蜂蜜胶 handler。其它 simulated click-interaction handler
   （merging glue / rope / zipline / hold interaction / physics staff …）本 mod 不碰——**g32 已整体接回 postClientTick**，
   因此这个限制在本轮裁决后不再有实际影响。
5. **double-tick 风险**：glueviz 与 g32 同时安装 ⇒ `HoneyGlueClientHandler.clientTick` 每 tick 跑两次
   （两次 Outliner 刷新，视觉上多半相同但重复工作）。**二者只能选一个**；本轮选 g32，glueviz 保持不装。
6. 依赖 `aeronautics`（HoneyGlue* 类）与 `fabric-lifecycle-events-v1`；当前交付件都包含，缺一个会启动报依赖错误。
7. 用户操作说明：需要在**主手/副手**持对应胶物品；蜂蜜胶的绑定交互按 mod 原有提示（alt/点击）——修复只是让已有提示重新可见。

---

## 6. 回滚

- 未修改 mods-stable；回滚 = 从 mods 目录删掉 `sky262-glueviz-1.0.0.jar` 即可，其它交付件不受影响。

---

## 7. 复跑命令（脚本都在 `work/run26/port/g36/`）

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g36
python _build.py            # 编译 + 打 jar + 冒烟（evidence 00/01/02）
python _static_analysis.py  # 现状调查证据（evidence 03）
python _mkstage.py          # staging（evidence 04）
```

---

## 8. 一句话

强力胶的可视范围**本来就有**（create-fly 的 Outliner 链完整）；蜂蜜胶的渲染与注册也都在，移植只是丢了
「每 tick 驱动」（原交付 `postClientTick` 零调用者）——**这组钩子已由 aeronautics g32 候选补上**（§1.3 有逐条字节码证据），
因此两种胶都应有「粘时预览 + 粘后手持查看已粘范围」，**sky262-glueviz 冗余、不 promote**（保留为备选；与 g32 禁止共存）。
**结论有静态证据，仍未实测——请用 r408 组合包验证（§4）。**
