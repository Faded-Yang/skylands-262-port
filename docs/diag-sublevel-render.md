# diag-sublevel-render —— 物理组装出的 sublevel 方块"隐形但有碰撞"（task-29 / R413）

> **性质：纯静态诊断（未改任何 jar、未启动游戏）。**
> 对象：live `sable-fabric-26.3.jar`（9,361,559 B，SHA `4f8f7d3b78b3ffeed299fe65da3d2496d38319290770faefb4c9f48bdb5b1053`）
> 与 `aeronautics-fabric-0.1.0-port.26.3.jar`（31,552,983 B，`bf7509e5fef8bba02d0623b23f172bf2e3d398628109f43d7025a24f7d30b4cc`）。
> 工作目录 `work\run26\port\g45\`（脚本见 §7）。

---

## 0. 结论（一句话）

**sublevel 的方块渲染整条链路在 26.3 移植里被"降级成空函数"，不只是漏注册**：
① 唯一调用渲染分发器的那两个 `LevelRendererMixin` 因 26.3 删掉了 `renderLevel/renderSectionLayer/setupRender/isSectionCompiled` 被移入
`src\_dropped_mixin26\`（未恢复）；
② 分发器 `SubLevelRenderDispatcher` 的所有 draw 方法（`renderSectionLayer/renderAfterSections/renderBlockEntities/preRenderChunks`）
在 live jar 里**方法体就是 `return`**；
③ 真正画几何的 `VanillaChunkedSubLevelRenderData.renderChunkedSubLevel()` 与
`VanillaSingleSubLevelRenderData.renderSingleBlock()` 也**都是 `return`**，`getRenderSection()` 直接 `aconst_null`；
④ 原本可作替代入口的 Veil 事件垫片 `VeilEventPlatform` 五个注册方法**全部 no-op**（只打 debug 日志）。

⇒ 物理/碰撞在服务端 + Rapier，完全正常；客户端**没有任何代码把 sublevel 的方块几何提交到 26.3 的渲染管线** ⇒ 方块不可见。
用户看到的"实体碰撞"来自 `SubLevelEntityCollision`/Rapier 碰撞体（与渲染无关）。
**这不是 1~2 行注册能修的，需要按 26.3 的 submit/帧图架构重写绘制层。**

---

## 1. 证据链（类 + 方法 + 字节码）

### 1.1 调用链断了：没有调用者
对两个 jar 做常量池扫描（`_render_callsites.py`）：

| 方法 | sable 内引用者 | aeronautics 内引用者 |
|---|---|---|
| `renderSectionLayer` | 仅 3 个 dispatcher 实现类自身 | 0 |
| `renderAfterSections` | 仅 dispatcher 自身 | 0 |
| `updateCulling` | 仅 dispatcher 自身 | 0 |

⇒ **没有任何类在渲染时调用分发器**；原调用点在 26.3 被删的入口里：

- `_dropped_mixin26\MANIFEST.md`：
  - `sublevel_render.LevelRendererMixin`：**"LevelRenderer 无 level/allChanged/renderLevel（26.3 改 submit 两段式）"**
  - `sublevel_render.impl.vanilla.LevelRendererMixin`：**"LevelRenderer 无 level/minecraft 字段；setupRender/isSectionCompiled/renderSectionLayer 全删"**
- 被移走的源码里明确写着：`// PORT(26.3): require = 0 —— LevelRenderer.renderSectionLayer 在 26.3 已删除（改 submit-node）`，
  原来这些注入点里调用的是
  `SubLevelRenderDispatcher.get().renderSectionLayer(sublevels, renderType, x, y, z, modelView, projection, partialTick)`
  与 `renderAfterSections(...)`（见 `getSubLevels/getSublevels` 两处原实现）。

### 1.2 分发器本身是空壳（最致命）
`javap -p -c`（live jar）：

| 类 | 方法 | 字节码 |
|---|---|---|
| `VanillaSubLevelRenderDispatcher` | `renderSectionLayer` | `0: return` |
| 同上 | `renderAfterSections` | 只 `singleBlockLayers.clear(); return` |
| 同上 | `renderBlockEntities` / `preRenderChunks` | `return` |
| `FancySubLevelRenderDispatcher` | `renderSectionLayer/renderAfterSections/renderBlockEntities` / `free` | 全部 `return` |
| `ReachAroundSubLevelRenderDispatcher`（**sodium 在场时实际选中的**，extends Vanilla） | 继承上述空实现；只有 `createRenderData` 是真实实现 | — |

### 1.3 渲染数据层也是空壳
| 类 | 方法 | 字节码 |
|---|---|---|
| `VanillaChunkedSubLevelRenderData` | `renderChunkedSubLevel(RenderType, Matrix4f, double,double,double)` | `0: return` |
| 同上 | `getRenderSection(SectionPos)` | `aconst_null; areturn` |
| 同上 | `compileSections/rebuild/resize` | 有真实实现（用 26.3 的 `SectionRenderDispatcher.RenderSection`） |
| `VanillaSingleSubLevelRenderData` | `renderSingleBlock(RenderType, VertexConsumer, Matrix4f, double,double,double)` | `0: return` |
| 同上 | `rebuild` | 真实（能取到 singleBlockState/BlockEntity） |

⇒ 数据/分块编译层可能还是好的（`ReachAround.createRenderData` 会 new `VanillaChunkedSubLevelRenderData(sublevel, SectionRenderDispatcher)`），
**但"把编译结果画出来"这一步被整体置空**。

### 1.4 选择器与入口（不是这里的问题）
- `SubLevelRenderer.<clinit>`：遍历 `SelectedRenderer.values()` 取第一个 `isSupported()`：
  - `VANILLA`：`!SodiumCompat.isLoaded()` ⇒ 创建 `VanillaSubLevelRenderDispatcher`
  - `SODIUM_REACHAROUND`：`SodiumCompat.isLoaded()` ⇒ 创建 `ReachAroundSubLevelRenderDispatcher`
  - 本包有 sodium ⇒ 实际是 **SODIUM_REACHAROUND**（仍继承空实现）。
- `SubLevelRenderer.getDispatcher()` 懒创建，`SableClientConfig` 会 `setImpl(SELECTED_RENDERER)` ⇒ dispatcher 对象存在。
- `SableFabricClient.onInitializeClient()` 只注册了：`SableClient.init()`、`ClientPlayConnectionEvents.DISCONNECT`、一个资源 reload listener（`sub_level_renderer`）；
  **没有任何渲染事件注册**。
- `SableClient.init()` 里唯一的渲染注册是 `VeilEventPlatform.INSTANCE.onVeilRenderLevelStage(SableSkyLightShadows::renderShadowMap)`
  ⇒ 走 no-op 垫片（见下）。

### 1.5 Veil 垫片把替代入口也堵死了
`dev.ryanhcode.sable.compat.veil.platform.VeilEventPlatform$1`（live jar，javap）：

```text
onVeilRendererAvailable       -> LOGGER.debug("[VeilShim] onVeilRendererAvailable ignored (no Veil renderer in 26.3)")
onVeilAddShaderProcessors     -> ... ignored (no GLSL preprocessor hook in 26.3)
onVeilRenderLevelStage        -> ... ignored (no level-render stage hook in 26.3)
onVeilRegisterBlockLayers     -> ... ignored (chunk layers are not registrable in 26.3)
onVeilRegisterFixedBuffers    -> ... ignored (no fixed-buffer concept in 26.3)
```

⇒ fancy 渲染器需要的 block layer/fixed buffer/shader processor 全没注册；天空光阴影（`SableSkyLightShadows`）与 gizmo 也一起没了（次要）。
`AeronauticsClient` / `SimulatedClient` 里对 `onVeilRegisterBlockLayers/fixedBuffers` 的注册同样落在 no-op 上。

---

## 2. 为什么"只有方块看不见、玩家/实体站得住"

- 碰撞：服务端 `ServerSubLevel` + Rapier 碰撞体（`SubLevelEntityCollision$CollisionInfo` 等）独立于渲染 ⇒ 正常。
- 实体渲染：`mixin.entity.entity_rendering.LevelRendererMixin` 等仍在（26.3 还保留 `renderEntity` 类入口），
  所以站在 sublevel 上的玩家/生物能画出来。
- 方块几何：唯一入口在 1.1 的已删 `LevelRenderer` 方法里 ⇒ 从未提交 ⇒ 隐形。完全对得上用户描述。

---

## 3. 26.3 可用的新接入点（修法依据，javap 实测）

### 3.1 Fabric API（`fabric-rendering-v1-27.1.0`）已有 level 渲染事件
`net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderEvents` 回调族（26.3 官方）：

- `START_MAIN` / `AFTER_OPAQUE_TERRAIN` / `BEFORE_TRANSLUCENT_TERRAIN` / `AFTER_TRANSLUCENT_TERRAIN` /
  `AFTER_SOLID_FEATURES` / `AFTER_TRANSLUCENT_FEATURES` / `BEFORE_BLOCK_OUTLINE` / `BEFORE_GIZMOS` / `END_MAIN`
- `COLLECT_SUBMITS`（`collectSubmits(LevelRenderContext)`）
- `LevelRenderContext`：`submitNodeCollector()` + `poseStack()`（外加 terrain 上下文的 `LevelTerrainRenderContext.sectionsToRender(): ChunkSectionsToRender`）

### 3.2 vanilla 26.3 两段式
`LevelRenderer` 现在有：`render(...)` / `submitFeatures(LevelRenderState, SubmitNodeCollector, boolean)` /
`prepareChunkRenders(Matrix4fc, boolean)` / `compileSections(CameraRenderState)` / `executeSolid/executeOit/...`
⇒ sublevel 的几何要么走 **submit 节点**（`SubmitNodeCollector`），要么复用 **`ChunkSectionsToRender`** 的分块绘制路径。

---

## 4. 修复方案（建议拆两步，先拿到"可见"）

### PRIME（先做，目标是"能看见方块"）
1. **入口**：新增一个 client entrypoint（sable jar 内新类 + `fabric.mod.json` entrypoints.client 加一项；不改现有类），
   注册 `LevelRenderEvents`：
   - `START_MAIN`/`AFTER_OPAQUE_TERRAIN`：取 `ClientLevel` 的 plot 容器（`SubLevelContainerHolder.sable$getPlotContainer()`，
     mixin 已注册）→ `SubLevelRenderer.getDispatcher()`；
   - `AFTER_OPAQUE_TERRAIN`（或 AFTER_TRANSLUCENT_TERRAIN）：按 chunk layer 调
     `dispatcher.renderSectionLayer(sublevels, layer, camX,camY,camZ, pose.matrix, projection, partialTick)`；
   - `COLLECT_SUBMITS`：对没走分块路径的 render data 用 `submitNodeCollector()` 提交方块状态几何。
2. **实现 draw**（当前空实现）：
   - `VanillaSubLevelRenderDispatcher.renderSectionLayer/renderAfterSections/preRenderChunks` 补回；
   - `VanillaChunkedSubLevelRenderData.renderChunkedSubLevel`：26.3 里不能再 `RenderType.draw`，建议
     用 `LevelTerrainRenderContext.sectionsToRender()` 的 `ChunkSectionsToRender` 手法（把 sublevel 的 RenderSection 当 chunk section 画）
     或改用 `SubmitNodeCollector`（见 §3.2）；需要把 `MatrixStack/PoseStack` 与相机偏移传进去；
   - `VanillaSingleSubLevelRenderData.renderSingleBlock`：**用户这次的组装很可能落在 `isSingleBlock` 分支**
     （ReachAround.createRenderData 会优先返回 `VanillaSingleSubLevelRenderData`），补它性价比最高：
     用 `SubmitNodeCollector`/`BlockModelResolver` 提交单方块（含 BlockEntity 走 `submitBlockEntity`）。
3. **保底**：`SableSkyLightShadows` 等 Veil 事件相关可先不管（只影响阴影/特效，不影响可见性）。

### 之后再补
- Fancy 渲染器（block layers/fixed buffers/shader processors）——需要按 26.3 RenderPipeline/GpuDevice 重写，工作量最大；
- 水遮挡/同步/光照等细节。

**工作量估计**：PRIME 1–2 天（单方块路径 + 一个 level-render 事件入口；可以先只让 `isSingleBlock` 的组装可见），
完整分块路径 +2–4 天；风险高（26.3 渲染状态/帧图 API 需要实测迭代）。**本轮不出候选**（满足你的"静态定方向"要求）。

---

## 5. 与"普通 contraption 渲染"的关系

Create 的 contraption 走 **create-fly 自己的渲染器**（`com.zurrtum.create…` + flywheel），
不经过 sable 的 `SubLevelRenderDispatcher` ⇒ 静态上与这个 bug **无关**，普通轴承/活塞 contraption 应正常（R407 的旋转实测也见过正常渲染）。
需要探针用「同一世界：Create contraption 可见 + sable 物理组装不可见」做对照确认。

---

## 6. 给探针的对照实验（下一轮）

1. 基线（live）：物理组装器组装一个 **单方块** 子世界 → 截图（预期：方块隐形、站上去有碰撞）；
2. 同样操作再组装一个 **多方块**（2×2×2）→ 截图（预期：同样隐形；若某边角可见说明部分路径 work，需要记录）；
3. 对照：Create 轴承 contraption → 截图（预期：可见）；
4. 记录 `latest.log` 里是否出现 `[VeilShim] … ignored`（基线会，证明垫片 no-op 生效）。

---

## 7. 复现命令（只读）

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g45

python _render_hook_recon.py        # 渲染相关类/配置/render data 清单
python _client_hook_recon.py        # SableFabricClient/Veil 垫片字节码
python _render_callsites.py         # 证明 renderSectionLayer/renderAfterSections/updateCulling 0 调用者
python _hook_api2.py                # dispatcher 空实现 + 26.3 LevelRenderer/Fabric 事件 API
python _dispatcher_state.py         # 三个 dispatcher 的方法体 + 选择器
python _dispatch_init.py            # SubLevelRenderer.<clinit>/getDispatcher 懒创建
python _fallback_api.py             # 单方块/分块渲染数据 API + LevelTerrainRenderContext
```

关键证据文件：`g45\_dropped_manifest_excerpt.txt`（MANIFEST 摘录）、`g45\_evidence.md`（本次结论 raw 输出摘录，待补）。


---

## 8. R415 PRIME 候选：单方块 sublevel 渲染恢复（g45）

> ⚠ **基线漂移记录**：本任务开始时 live sable = `4F8F7D3B…`（Lead 给的基线），
> 构建期间被别人改了两次：`4F8F7D3B → 83B6BEE5（21:41）→ 3828A3A7（21:47）`；
> 两次 diff 都只有 `dev/ryanhcode/sable/physics/impl/rapier/RapierPhysicsPipeline.class`（物理走子，非渲染）。
> 因此候选以 **最新 live `3828A3A7…` 为基线**重打（本补丁只加 entrypoint + 1 个 class，**与基线内容无关**，
> 换基线时新增 class 字节完全一致）。staging 里的 sable 是**快照 copy**（不是 hardlink），避免 live 继续漂移。

| 项 | 值 |
|---|---|
| 文件 | `work\run26\port\g45\out\sable-fabric-26.3-sublevelrender.jar` |
| size | **9,364,712 B**（基线 9,359,690 B） |
| SHA-256 | `2189a3acc150329a4cd573b1fc8a81d3dcb1fdfc2d2943f1afabe338a876f7e9`（v5） |
| 基线 | live `3828a3a7089b230148b525be63490b74b20d6a3b0a58cc68a2895cea78f6cdcf`（备份 `g45\backup\sable-fabric-26.3.3828a3a7.jar`） |
| 相对基线 | 改 `fabric.mod.json`（entrypoints.client +1）+ 新增 `skylands262/compat/SableSubLevelRenderBootstrap.class`；其它 1050 entry 逐字节不变、顺序不变 |

### 8.1 实现（PRIME 只做单方块）

新增 client entrypoint `skylands262.compat.SableSubLevelRenderBootstrap`：
- `onInitializeClient()` 注册 Fabric 26.3 `LevelRenderEvents.COLLECT_SUBMITS`；
- 回调里取 `Minecraft.level` → `SubLevelContainerHolder.sable$getPlotContainer()` → `ClientSubLevelContainer.getAllSubLevels()`；
- 处理 **小体量** sublevel：`volume = (dx*dy*dz) ≤ 64` 就逐块提交（单方块只是 volume==1 的特例；
  探针实测组装出的 sublevel bounds 是 `y=126..127` 两格高、用户报的也是「物理方块 + 下面石块」⇒ 只放单方块会漏；
  体积 >64 的 chunked sublevel 留给第二步）：
  - 取 `blockState = sublevel.getLevel().getBlockState(pos)`，跳过 air / `RenderShape != MODEL`；
  - **transform 数学逐行照抄** pre-26.3 的 `VanillaSingleSubLevelRenderData.renderSingleBlock`：
    `rotationPoint - blockPos → 旋转 → 取反 + renderPos → translate(-camera) → rotate(orientation)`，
    再 `pose = context.poseStack()(=identity) * transform` ⇒ 只留 `translate(renderCOR-cam) * rotate(orientation)`。
    这是 **camera-relative world pose**，不是旧 modelView：javap 证实 `submitFeatures` 开头 `new PoseStack()` 是 identity、
    `COLLECT_SUBMITS` 在其 TAIL 触发；26.3 的相机旋转由后续 feature 阶段（`CameraRenderState.viewRotationMatrix`）应用
    （neo-auditor 复核确认）⇒ **不要**乘旧 modelView / `Camera.getViewRotationMatrix()`（v2 曾误乘，v3 已回退）；
  - 用 26.3 正常管线提交：`BlockModelResolver.update(state, blockState, BlockDisplayContext.create())` →
    `BlockModelRenderState.blockLightCoords = LightCoordsUtil.getLightCoords(level,pos)` →
    `state.submit(pose, context.submitNodeCollector(), light, OverlayTexture.NO_OVERLAY, 0)`；
- camera 位置与 `submitFeatures` 对齐：优先 `context.levelState().cameraRenderState.pos`，为空才回退 `mainCamera().position()`；
- sublevel 列表先 `new ArrayList<>(...)` 快照再遍历（容器在 client main thread 会增删，避免 CME）；
- 整个回调 try/catch，失败只记一次 ERROR（不崩客户端）；日志锚点
  `[skylands262] sable sub-level single-block renderer registered (COLLECT_SUBMITS)`；
- 光照：`LightCoordsUtil.getLightCoords(level, pos)` 在 plot global 坐标上多半返回 0（客户端 plot 光照尚未接）⇒ **0 时回退 `LightCoordsUtil.FULL_BRIGHT`**（v5 修黑箱）；
- 一次性 debug（A/B 用）：`[skylands262] sublevel-render probe: bounds=…, volume=…, rendered=…, renderPos=…, rotationPoint=…, camera=…, firstCorner=…`
  ——v4 实测 `rendered=2`（提交已发生），v5 补光照并用这四个数反推 offset（若仍有位置/朝向偏差，拿这行 + 截图对）。

### 8.2 静态证据

`python work\run26\port\g45\_verify.py` → `out/_static_verify.txt` **PASS**：
entry 顺序保留 + 1 追加；唯一改的 entry = `fabric.mod.json`（entrypoints.client 只多了我们的类）；
新增 class 字节 == 编译产物（sha `4460f45b832dd205…`）；zip CRC OK；类加载冒烟（真实 launch classpath，375 项）
加载出 `ClientModInitializer` + 3 个方法，无 VerifyError。

### 8.3 A/B（探针）

staging（sable 为快照 copy，aeronautics = live `6D435F98`，未混 wakefix2 以外的件）：
- baseline：`g45\stage\mods-baseline`（sable = `3828A3A7`）
- candidate：`g45\stage\mods-candidate`（sable = `002A8146`）
- 重建：`python work\run26\port\g45\_mkstage.py baseline|candidate <dir>`

步骤（**必须用单方块组装**，PRIME 只覆盖这个分支）：
1. 同世界先放一个 Create 轴承/活塞 contraption 截图（对照，应正常）；
2. 用物理组装器组装 **一块** 方块 → 截图（基线：隐形但有碰撞；候选：应能看到这块方块，位置/朝向跟随 sublevel pose）；
3. 抓 `latest.log`：候选应有 `registered (COLLECT_SUBMITS)`；若出现
   `sub-level single-block render failed` ⇒ 把栈发回；
4. 记录失败形态：完全不可见 / 位置偏移 / 朝向错 / 亮度不对 —— 分别对应 transform 约定、相机偏移、pose 乘法顺序、light 参数，下一轮据此调。

**诚实预期**：这是「先能看见」的最小版本；多方块（chunked）仍不可见（需 §4 的第二步）。


### 8.4 v5 A/B 结果：**PASS**（interact-probe，2026-10-18 22:1x）

staging：baseline sable `3828A3A7` / candidate `2189A3AC`（g45 staging，全新存档）；场景同 slr5（2 格结构：组装器+石块）。

- 有效性：fraction=1.000 松手、**serverSubCount=1 / clientSubLevelCount=1**、0 crash-report；
- 候选日志（完整）：
```
  [skylands262] sable sub-level single-block renderer registered (COLLECT_SUBMITS)
  [skylands262] sublevel-render probe: bounds=(20481032,126,20481032)-(20481032,127,20481032), volume=2, rendered=2, renderPos=(-3.395E+2 7.679E+1 -3.750E+1), rotationPoint=(2.048E+7 1.268E+2 2.048E+7), camera=(-337.3,78.1,-37.5), firstCorner=(-3.400E+2 7.600E+1 -3.800E+1)
```
- 截图（`g33/slr-cand-v5-t1.png` / `slr-cand-v5-t55.png` vs 基线 `slr-base-t1/t55.png`）：
  - 基线：只有两块灰色悬浮石块（客户端残留），无机器/黑箱；
  - 候选 v5：**黑箱消失**，可见灰色石块 + 带棕色面的 physics_assembler（都有贴图/光照），t1→t55 稳定；
  - 位置：`firstCorner=(-340,76,-38)` 与 `renderPos=(-339.5,76.79,-37.5)` 差 <0.8 格（组装后 pose 与残留方块 0.5~1 格属正常）；
- 判读：**可见 PASS，无亮度问题、无黑箱、无明显 offset/朝向错误**（石块/组装器比残留略靠前 ~0.5 格，属预期差）。

### 8.5 promote 建议（Lead 操作）

| 项 | 值 |
|---|---|
| 候选 | `work\run26\port\g45\out\sable-fabric-26.3-sublevelrender.jar`（SHA `2189a3acc150329a4cd573b1fc8a81d3dcb1fdfc2d2943f1afabe338a876f7e9`，9,364,712 B） |
| 备份链 | sable .bak-r415 = 现行 `3828A3A7`（保留 .bak-r414 = `4F8F7D3B`） |
| 改名 | 覆盖为 `mods-stable\sable-fabric-26.3.jar` |
| promote 后 | 立刻复跑标题 + 进世界（三级门槛）；确认日志两行锚点仍在 |
| 回滚 | 用 `.bak-r415` 覆盖回去即可（补丁只加 entrypoint+class，回滚无残留） |

### 8.6 已知边界（PRIME 的“能看见”，不是完整渲染）

- 只覆盖 **volume ≤ 64** 的小 sublevel（含单方块特例）；多方块大 sublevel 走 chunked 第二步（`ChunkSectionsToRender` / 真 section renderer）；
- 光照是 **plot 光照接上前的 full-bright fallback**（仅当 `getLightCoords()==0` 时用 `FULL_BRIGHT`）；后续接 plot 光照会自然恢复明暗；
- 方块实体（BE）单独渲染暂未接（单/小体量 PRIME 只交地形几何）；BlockEntity 特例在第二步一起做；
- debug 日志只在回调首次成功时打一行（INFO），无每帧开销。


### 8.7 R416：物理基线必须 wakefix2（render 补丁重打）

> **教训（Lead 2026-10-18）**：wakefix3（sable `3828A3A7`）下探针实测 **200 tick 仍不下落**（±5.0 冲量对把唤醒/积分搞坏）；wakefix2（`83B6BEE5`）此前 20–45 tick 就落。
> ⇒ **sublevel 渲染 A/B 的物理基线必须是 wakefix2**；渲染补丁本身与基线无关（只加 entrypoint+class，换基线下新增 class 字节一致）。

| 项 | 值 |
|---|---|
| 基线 | `work\run26\port\g39\out\sable-fabric-26.3-g39-wakefix2.jar` = `83B6BEE5…`（9,359,681 B） |
| 候选 | `work\run26\port\g45\out\sable-fabric-26.3-sublevelrender-wf2.jar` |
| size | **9,364,703 B** |
| SHA-256 | `59280c1ea4e924fe4732fcd0dc6bc375404475698caf66b31df89f334ad25232` |
| 相对基线 entry diff | **2 个**：`fabric.mod.json`（entrypoints.client +1）+ 新增 `skylands262/compat/SableSubLevelRenderBootstrap.class`；其它 1050 entry 逐字节不变、顺序不变 |
| 静态验证 | `out/_static_verify_wf2.txt` **PASS**（entry diff=2、class=编译产物、zip OK、SMOKE_LOAD_OK） |

staging（atomic 写：temp + `os.replace`，不原地覆盖）：
- `g45\stage\mods-baseline-wf2`（sable = `83B6BEE5`、aeronautics = `6D435F98`、create-fly = `43C4A441`）
- `g45\stage\mods-candidate-wf2`（sable = `59280C1E`，其余同上）
- 重建：`python work\run26\port\g45\_mkstage_wf2.py baseline-wf2|candidate-wf2 <dir>`

promote 建议（Lead）：
- 现行 live sable = `2189A3AC`（render-on-wakefix3）⇒ 用 `59280C1E`（render-on-wakefix2）替换；
- 备份链：**`.bak-r416` = `2189A3AC`**（保留 `.bak-r415` = `3828A3A7`、`.bak-r414` = `4F8F7D3B`）；
- **必须 temp + `os.replace` 原子替换**，不要 `copy2` 覆盖 live（会穿透 hardlink 把 staging 一起改掉）；
- promote 后复跑「标题 + 进世界」；A/B 判据：① 组装后 sublevel 20–60 tick 内下落（wakefix2 行为）；② 方块可见（沿用 §8.4 的 render 证据，同一 class）。


### 8.8 R416 A/B 结果（interact-probe）：渲染 PASS；物理异常但与本补丁无关

- 候选 `59280C1E`（render-on-wakefix2）截图/日志：两臂 sublevel count=1、0 crash；候选 `rendered=2`、石块+physics_assembler 有贴图光照 ⇒ **渲染 PASS**（同 R415 结论）。
- **物理**：两臂（base wakefix2 `83B6BEE5` / cand `59280C1E`）200 tick 都不落、`javaVel=(0,0,0)`；本轮探针每 5 tick 做 native getPose/getLinearVelocity 只读采样。
- **独立性证据**：候选相对基线只差 2 个 entry（`fabric.mod.json` 的 **client** entrypoints +1、新增 `SableSubLevelRenderBootstrap.class`）；该类只注册 `LevelRenderEvents.COLLECT_SUBMITS`、只读数据（不写 pose、不调 pipeline、无 mixin、无服务端代码）⇒ 对物理零影响；且基线单独跑也不落。
- 与 R414b（wakefix2 PASS）差异：那次是离地场景（y 76.79→64.79，60 tick 落地）；本轮 pose 仍 76.79，可能贴地/被支撑或 body 仍 asleep。
- 判定实验（交给 probe/neo-auditor）：① 冲量后看 nativeVel 是否变化（变了 ⇒ step 正常、重力唤醒没生效；不变 ⇒ body/step 路径）；② 抬高 3–5 格再组装看是否下落（⇒ 本轮只是贴地）；③ 读 body `isSleeping`/collider 数（resync `mass=3.0` 说明 collider 在）。
- 结论：**render 侧可 promote `59280C1E`**；物理基线（wakefix2 vs wakefix3）等复核结果，render 补丁不参与该选择。


### 8.9 promote 状态（2026-10-18 22:13，Lead）

- Lead 用 **原子替换（temp + `os.replace`）** promote 了 R416：live sable = `59280C1E`（9,364,703 B），标题回归 30.7 s 通过；
- 备份链：`.bak-r416` = `2189A3AC`（render-on-wakefix3）、`.bak-r415` = `3828A3A7`（wakefix3）、`.bak-r414` = `4F8F7D3B`；
- 物理定性测试（冲量/离地/body 状态）进行中，物理基线（wakefix2 vs wakefix3）待定；render 补丁可随时按新基线重打（只加 entrypoint+class，与基线无关）。
