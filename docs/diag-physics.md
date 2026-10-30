# 物理组装器不可用 + 缺拉杆 + 航空学物理缺失 —— 诊断与候选修复（G32）

> **性质**：静态诊断 + 两个候选 jar。**未启动游戏、未改 mods-stable、未碰 watch**。
> **基线**：work/run26/mods-stable 71 jar；aeronautics = 35BA4148…A800BAF5（31,550,019 B）、sable = 54ADAAE1…F03E229B（9,358,963 B）。
> **候选件**：work/run26/port/g32/out/sable-fabric-26.3-g32.jar、…/aeronautics-fabric-0.1.0-port.26.3-g32.jar（文件名不同，不会覆盖交付件）。

---

## 0. 一句话结论（三个现象 = 三个独立根因）

1. **物理没生效**：sable jar 里的 **ServiceLoader 清单只登记了 StaticPhysicsPipelineProvider**（无物理的空管线）。Rapier 物理实现（RapierPhysicsPipeline / 36 KB）和 native 全都在 jar 里，只是**没被登记** ⇒ Sable 从世界加载起就用空管线。**修法 = 清单加 1 行**（候选已做，隔离测试已证明选择结果从 Static 变 Rapier）。
2. **物理组装器只是普通方块**：NeoForge→Fabric 移植丢了 **客户端 tick / HUD 渲染** 钩子。SimulatedCommonClientEvents.preClientTick/postClientTick/renderOverlays 在 Fabric 版**零调用方** ⇒ HoldInteractionManager.tick 不跑 ⇒ PhysicsAssemblerGUIHandler.activeTick 不跑 ⇒ lastAnimatedValue 永远是 0 ⇒ 松手时 **AssemblePacket 永远不会发**（所以完全不能组装）；同时 HoldTipManager.tick 不跑 ⇒ **没有「按住并拖拽以组装」提示**；renderOverlays 不跑 ⇒ 没有进度条 overlay。**修法 = 补 3 个 Fabric 客户端钩子**（候选已做）。
3. **缺拉杆**：两层缺失：① **Registrate 垫片的 BlockEntityBuilder.renderer() 是空实现**（字节码：return this），build() 返回 null ⇒ 所有模拟/航空学 BE 的 renderer **根本没有注册**；② 52 个 Renderer class **全部是编译桩**（433–1168 B；PhysicsAssemblerRenderer 只有 485 B，仅一个 Object... 构造器）。上游 renderer 是 55 行：SmartBlockEntityRenderer + CachedBuffers.partial(SimPartialModels.ASSEMBLER_LEVER) + 按 visualAngle 旋转。26.3 渲染改成「提取 → 提交节点」，这份 renderer 必须重写。**本轮只写方案**（第 4 节）。

> 结论：**先把 1+2 的候选件 A/B 掉**，用户就能「按住拖拽组装 + 看到物理」。拉杆是独立的美术缺口，且是全 52 个 renderer 的系统性问题，不应顺手修。

---

## 1. 现象 → 根因 → 证据

| # | 用户现象 | 根因（一句话） | 关键证据 |
|---|---|---|---|
| 1 | 航空学物理用不了 | sable 只注册 Static（无物理）管线 | 见第 2 节 |
| 2 | 组装器只是普通方块、没有按住提示 | 客户端 tick/HUD 钩子在 Fabric 版未接线 | 见第 3 节 |
| 3 | 少了个拉杆 | Registrate renderer() 空实现 + 52 个 renderer 全是桩 | 见第 4 节 |

---

## 2. 物理缺失：Sable 的物理管线被 ServiceLoader 换成了空实现

### 2.1 证据链（全部可复现）

1. **jar 内 service 清单只有空实现**：META-INF/services/dev.ryanhcode.sable.api.physics.PhysicsPipelineProvider 只有一行
   dev.ryanhcode.sable.physics.impl.none.StaticPhysicsPipelineProvider
   而 dev/ryanhcode/sable/physics/impl/rapier/RapierPhysicsPipelineProvider.class（36 KB 的 RapierPhysicsPipeline、Rapier3D JNI、碰撞体、约束、绳索全在）存在但未被登记。

2. **上游是两个模块各带一份 service 文件**（work/sable-26/src）：
   - common/src/main/resources/META-INF/services/…PhysicsPipelineProvider → StaticPhysicsPipelineProvider
   - sable_rapier/src/main/resources/META-INF/services/…PhysicsPipelineProvider → RapierPhysicsPipelineProvider
   我们的重打 jar 只合并了 common 的那份 ⇒ 清单缺 Rapier 行（**构建合并问题，不是代码缺失**）。

3. **选择规则**（PhysicsPipelineProvider 静态初始化，javap）：ServiceLoader.load(...).stream().max(comparingInt(类上的 @LoadPriority，缺省 1000))
   - StaticPhysicsPipelineProvider：@LoadPriority(value=900)
   - RapierPhysicsPipelineProvider：**无注解 ⇒ 1000**
   ⇒ 只要两行都在清单里，Rapier 自动胜出，Static 保留为回退。

4. **隔离验证（不需要启动游戏）**：写了一个只读 PhysicsPipelineProvider.INSTANCE 的 Java 测试，classpath = sable jar + MC 26.3 jar + lz4 + slf4j：
   - 原 jar：SELECTED: …physics.impl.none.StaticPhysicsPipelineProvider
   - 候选 jar：SELECTED: …physics.impl.rapier.RapierPhysicsPipelineProvider

5. **native 可用性（真机验证）**：natives/sable_rapier/sable_rapier_binaries.zip.l4z 是标准 LZ4 frame（首 4 字节 04 22 4d 18），内含 6 个平台的库，本机目标 = sable_rapier_x86_64_windows.dll（1,658,368 B）；用 at.yawk.lz4:lz4-java:1.10.1 解压 + System.load(...) 实测 **LOADED OK**；lz4-java 本来就在 **26.3 的启动库清单**里（versions/26.3/26.3.json 的 at.yawk.lz4:lz4-java:1.10.1）⇒ Rapier3D.loadLibrary() 的 LZ4FrameInputStream 依赖运行期满足。

6. **物理确实会 tick**：sable.mixins.json 的 plot.ServerLevelMixin 在 ServerLevel tick 里调 plotContainer.tick() → SubLevelContainer.tick()（line 147）遍历 observers → SubLevelPhysicsSystem.tick(container)（implements SubLevelObserver）→ this.pipeline.tick()（line 231）。也就是说 **只差「选中 Rapier 管线」这一步**。

### 2.2 候选修复（已做）：sable-fabric-26.3-g32.jar

service 文件改成两行（保持 Static 作为回退）：
```
dev.ryanhcode.sable.physics.impl.none.StaticPhysicsPipelineProvider
dev.ryanhcode.sable.physics.impl.rapier.RapierPhysicsPipelineProvider
```

- entry diff：**1 / 1048**（只有该 service 文件变化，其余 entry 内容逐字节一致；testzip 通过）。
- 预期效果：世界加载时日志出现 Rapier 管线（不再是 using StaticPhysicsPipelineProvider）；sublevel 会真正受重力/碰撞/约束驱动。
- **必须实测**：native 符号解析（JNI 懒解析）、.sable/natives/ 写盘、世界加载是否成功。失败会以 CrashReport: Sable linking with Rapier natives 结束（不会静默回退）。

---

## 3. 组装器交互：Fabric 版丢了客户端 tick / HUD 钩子

### 3.1 证据

上游 NeoForge 的接线在 work/aero-port/Simulated-Project/simulated/neoforge/.../SimNeoForgeClientEvents.java（以及 aeronautics 的 AeroNeoForgeClientEvents）。对照我们的 Fabric 源码：

| 上游 NeoForge 钩子 | 作用 | Fabric 版现状 |
|---|---|---|
| ClientTickEvent.Pre → SimulatedCommonClientEvents.preClientTick | 前置客户端 tick | **无调用方**（全树 grep preClientTick 只有定义） |
| ClientTickEvent.Post → postClientTick | 后置客户端 tick：HoldInteractionManager/HoldTipManager/物理法杖/绳索… | **无调用方** |
| RenderGuiEvent.Post → renderOverlays(graphics, partialTick) | 按住交互进度条 overlay | **无调用方** |
| RegisterKeyMappingsEvent → SimKeys.registerTo | 注册 Tab/scroll 键 | **无调用方**（SimKeys.registerTo 全树 0 调用） |
| ClientTickEvent.Pre/Post（aeronautics）→ AeronauticsClientEvents.clientLevelTick | 气球图/levitite shader tick | **无调用方** |
| ItemTooltipEvent → appendTooltip | 方块属性 tooltip | 未验证（可能由 mixin 覆盖） |
| PlayerInteractEvent.RightClickBlock → onRightClickBlock | 按住交互时取消普通右键 | 端口有 quiet_use.MultiPlayerGameModeMixin（未逐行核实） |
| RegisterGuiLayersEvent（LinkedTypewriter overlay） | 打字机绑定提示 | 仍缺（与本任务无关） |

SimulatedFabricClient.onInitializeClient()（基线 391 B）只做 SimulatedClientTooltips.apply() + SimulatedClient.init()；AeronauticsFabricClient 只做 AeronauticsClient.init()。**没有任何 Fabric 生命周期/渲染 API 调用**。

### 3.2 因果链（为什么表现为「普通方块」）

```
右键（客户端）→ PhysicsAssemblerBlock.useWithoutItem → PHYSICS_ASSEMBLER_MANAGER.startHold
   → HoldInteractionManager.active = handler（只此一步生效）
但 HoldInteractionManager.tick() 从不被调用（缺 END_CLIENT_TICK）
   → PhysicsAssemblerGUIHandler.activeTick() 从不执行
   → lastAnimatedValue 永远 0、be.updateControlledByPlayer 不调用
松手 → MouseHandlerMixin → BlockHoldInteraction.onUse(RELEASE) → release()
   → 判断条件依赖 lastAnimatedValue > 1-PULLED_THRESHOLD ⇒ 永远不成立
   → AssemblePacket 永远不发送 ⇒ 服务端 assembleOrDisassemble() 永远不执行
同时 HoldTipManager.tick() 从不执行 ⇒ 没有「按住并拖拽以组装」提示
同时 renderOverlays() 从不执行 ⇒ 没有右侧进度条
```

（注：PhysicsAssemblerBlock、PhysicsAssemblerBlockEntity、GUIHandler、SimClickInteractions、hold_interaction mixins **都在 jar 里且是真实现**，不是桩 —— 缺的只是 tick/render 接线。）

### 3.3 候选修复（已做）：aeronautics-fabric-0.1.0-port.26.3-g32.jar

替换 **2 个类**（其余 entry 内容逐字节不变；entry diff = 2 / 3284）：

- SimulatedFabricClient：
  - ClientTickEvents.START_CLIENT_TICK → preClientTick
  - ClientTickEvents.END_CLIENT_TICK → postClientTick
  - HudElementRegistry.addLast(Simulated.path("interaction_overlays"), (g, dt) -> renderOverlays(g, 0f))
  - SimKeys.registerTo(KeyMappingHelper::registerKeyMapping)
- AeronauticsFabricClient：START/END tick → AeronauticsClientEvents.clientLevelTick(false/true)

API 均已从包内 fabric-api-0.163.0+26.3 的嵌套模块 javap 核实：ClientTickEvents$StartTick.onStartTick(Minecraft)、HudElement/HudElementRegistry.addLast(Identifier, HudElement)、KeyMappingHelper.registerKeyMapping(KeyMapping)。
（renderOverlays 的 float pt 当前实现未使用，传 0 不影响。）

> **联动（crashfix-26 交叉确认，2026-10-18）**：`postClientTick` 是**同一份 tick** 驱动 `SimClickInteractions.CLICK_INTERACTION_ENTRIES` 的全部 handler（HONEY_GLUE_MANAGER / PHYSICS_ASSEMBLER_MANAGER / 手柄 / 拉杆 / 滑索 …）⇒ 与 crashfix-26 的 `sky262-glueviz` **互斥，禁止共存**（否则这些 handler 双跑，有重复 Outliner 刷新与状态/音效副作用）；g32 promote 后 glueviz 永久退场。另：蜂蜜胶的**渲染**不依赖本 tick（它走 create-fly 既有的 `LevelRendererMixin` → `Outliner.submitOutlines`，已 promote），本轮不改。

---

## 4. 缺拉杆：两层缺失（本轮只给方案）

1. **注册层**：Registrate 垫片 com.tterrag.registrate.builders.BlockEntityBuilder 的字节码里：
   - renderer(Supplier<? extends RendererFactory<? super T>>) → **直接 return this**（空实现）
   - visual(...) → 同样 return this；build() → return null
   ⇒ SimBlockEntityTypes.PHYSICS_ASSEMBLER.renderer(() -> PhysicsAssemblerRenderer::new) 这句话**没有任何效果**。
2. **实现层**：PhysicsAssemblerRenderer.class = 485 B，只有 PhysicsAssemblerRenderer(Object...) {}（编译桩）。全 jar 52 个 Renderer 全是 433–1168 B 的桩；**不是只有拉杆缺，是所有模拟/航空学 BER 视觉都缺**。

上游 renderer（55 行，Simulated-Project/simulated/common/.../PhysicsAssemblerRenderer.java）：SmartBlockEntityRenderer.renderSafe 里用 CachedBuffers.partial(SimPartialModels.ASSEMBLER_LEVER, blockState)，按 getRenderAngle(be, partialTicks) 绕 Direction.EAST 旋转（0–45°）。模型 assets/simulated/models/block/physics_assembler/lever.json（knob + lever 两个 element）和 block.json 都在 jar 里；SimPartialModels.ASSEMBLER_LEVER 也存在 —— **只差渲染代码 + 注册**。

**两个选项**：

- **A（快，视觉正确性打折）**：把 lever.json 的两个 element 合并进 block.json（静态拉杆，永远指向装配状态）。只改 1 个资源 entry，无代码。缺点：不随拉动旋转、与真实状态不同步。
- **B（正解，M 体量）**：按 26.3「提取 → 提交节点」重写 renderer（参考 create-fly 里真实的 BearingRenderer/StickerRenderer 的 *RenderState + submit 写法，SuperByteBuffer/CachedBuffers 在 26.3 仍存在），并在 SimulatedClient.init() 用 BlockEntityRenderers.register(SimBlockEntityTypes.PHYSICS_ASSEMBLER.get(), PhysicsAssemblerRenderer::new) 显式注册（因为垫片不再注册）。再做同族的 51 个 renderer 属于另一轮。

---

## 5. 候选件与 A/B 方法

| 候选 | 路径 | 大小 | SHA-256 | entry diff |
|---|---|---:|---|---|
| sable（物理） | work/run26/port/g32/out/sable-fabric-26.3-g32.jar | 9,358,979 | 031F57056A58D92B9CEC9A30234AC81C8137DF4AE3C7FD62C5C9D808A4451C78 | 1 / 1048 |
| aeronautics（交互） | work/run26/port/g32/out/aeronautics-fabric-0.1.0-port.26.3-g32.jar | 31,551,335 | E290F9DBB7AD6D1BE3E5E8307D201300784707A97F2B49DFCDE302F2CCD5A940 | 2 / 3284 |

**A/B 步骤（交给 verifier；按现有 g21/g23v 流程）**

1. 自建 mods 目录（硬链接复制 mods-stable，**不要动 mods-stable/watch**），用两个候选替换同名 jar；
2. **必须用全新存档副本**（模板 template/lm-final）；
3. 基线：原两 jar → 放 simulated:physics_assembler → 按住右键：无提示、无 overlay、松手不组装；日志出现 using StaticPhysicsPipelineProvider；
4. PRIME：候选两 jar → 同一操作：应看到「按住并拖拽以组装」提示 + 右侧进度条；拉到底松手应生成 sublevel 并能推动/受重力（物理候选生效的标志）；
5. 若 PRIME 在**世界加载**就崩：看是否 Sable linking with Rapier natives（native 问题）⇒ 先单独只换 sable 候选复现；
6. 回归：TITLE_SCREEN_OK + WORLD_OK + scan_landmines 不得变差。

---

## 6. 未修 / 未验证 / 风险

- **未验证（需要实测）**：Rapier native 在真实 Fabric classloader + 游戏目录下的加载；第一次进世界时 .sable/natives/ 解压；物理驱动的 sublevel 渲染/碰撞是否完整；客户端预测物理是否也走 Rapier（未查）。
- **Rapier 失败不回退**：Rapier3D.loadLibrary() 失败会抛 ReportedException（crash report 终止），不会回退 Static。若实测高风险，可改为「清单只写 Static + 显式按平台选」或给 provider 加 try/catch（需要重打 sable，M 体量）。
- **sable 配置未注册**：SableFabric.onInitialize 里 NeoForgeConfigRegistry.register(SableConfig.SPEC/SableServerConfig.SPEC) 被注释（注释说「FCAP 没有 26.3 构建」，但**包里其实有** ForgeConfigAPIPort-v26.3.1-mc26.3.x-Fabric.jar）⇒ 配置文件的值全被忽略，用默认值（substeps_per_tick=2 等）。不影响物理能否跑，但影响可调性；可用 FCAP v5 API 补（S）。
- **同族还缺的 common 钩子**：SimulatedCommonEvents.onServerTickEnd（redstone magnet / docking connector 的 global tick）在 Fabric 版同样零调用方；onPlayerLoggedIn/onChunkLoad 等 NeoForge 回调也需对照。本轮未修（与组装器无关，但会影响磁铁/对接等）。crashfix-26 已确认此项**与蜂蜜胶无关**、不在 task-21 范围，留此列表由 lead 排期。
- **拉杆**：未实现（第 4 节方案）。
- 候选 jar 是用 **javac 直接编译 2 个类 + 重打 jar** 生成的（没有跑 gradle），编译 classpath 取 aeronautics-26/build/javac.args + fabric-api 全部嵌套模块；若将来 gradle 全量重建，应把同样的钩子加进 src/fabric/... 源码，避免候选件被重建覆盖。

---

## 7. 下一步（按「成本 × 崩面」排序）

1. **P0 实测两个候选**（verifier）：物理 + 组装器交互；这是用户最直接的痛点。
2. **P1 拉杆方案 A**（静态模型，1 个资源 entry）如果用户只是「要看到拉杆」；否则排 B。
3. **P1 把候选源码改动回灌** work/aero-port/aeronautics-26/src/fabric/...（两文件），保证下次 gradle 重建不丢；同时把 sable 的 service 合并修进 sable 的重打脚本（找 sable 打包脚本/README，避免下次又只合并 common）。
4. **P2 注册 sable 配置**（FCAP v5）+ 补 onServerTickEnd 接线。
5. **P3 系统性补 BER**（52 个 renderer + 注册机制），这是「航空学视觉完全体」的长期项。

---

## 8. 复跑 / 构建命令（本机）

```powershell
cd C:/Users/95959/OneDrive/Desktop/Work/skylands-262/work/run26/port/g32
# 1) 验证候选件 entry diff（重打脚本会打印 changed 列表）
python _tmp/repack.py
# 2) 验证 sable 管线选择（不需要启动游戏）
#    classpath = 候选 sable + 26.3.jar + lz4 + slf4j，运行 TestProvider
# 3) A/B 实测按 verifier 的 g21/g23v 流程
```

- 编译候选类用的 argfile：g32/_tmp/javac_g32.args（classpath = aeronautics 的 javac 编译类路径 + g32/_tmp/fapimods/*.jar）。
- 候选源码（便于回灌）：g32/src/dev/simulated_team/simulated/fabric/SimulatedFabricClient.java、g32/src/dev/eriksonn/aeronautics/fabric/AeronauticsFabricClient.java。

---

## 9. 基线校验和

| 项 | SHA-256 |
|---|---|
| aeronautics-fabric-0.1.0-port.26.3.jar（当前） | 35BA4148210E7EA5A45B6FC63CF699177FE0D87BB22BE7F7BFEDBE74A800BAF5 |
| sable-fabric-26.3.jar（当前） | 54ADAAE12517E4B36DB2D424B9086102048137966D99745B4BE73B52F03E229B |
| 候选 sable | 031F57056A58D92B9CEC9A30234AC81C8137DF4AE3C7FD62C5C9D808A4451C78 |
| 候选 aeronautics | E290F9DBB7AD6D1BE3E5E8307D201300784707A97F2B49DFCDE302F2CCD5A940 |
