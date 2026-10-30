# regress-assembler-100 —— 物理组装器回归静态定位

> 只读静态审计 + 最小 A/B staging；未改 live。DOCS FIRST 参考：docs/diag-aero-physics.md、docs/DELIVERY.md R408/R409/R414/R415、docs/api-landmines.md。

## 1. 组装器链路（当前 live）

| 环节 | 类 / 事件 | live 位置 |
|---|---|---|
| 方块/交互 | PhysicsAssemblerBlockEntity (extends com.zurrtum.create.foundation.blockEntity.SmartBlockEntity) | aeronautics-fabric-0.1.0-port.26.3.jar |
| 客户端 GUI/hold | PhysicsAssemblerGUIHandler、HandHoldInteraction / SimClickInteractions | aeronautics jar |
| 服务端包 | AssemblePacket | aeronautics jar |
| 组装核心 | SimAssemblyHelper.assembleFromSingleBlock | aeronautics jar |
| Sable 组装 | SubLevelAssemblyHelper.assembleBlocks | sable-fabric-26.3.jar |
| 容器/物理 | SubLevelContainer、SubLevelPhysicsSystem、SubLevelTrackingSystem | sable jar |
| 组装器子级查询 | PhysicsAssemblerBlockEntity.getSubLevel -> Sable.HELPER.getContaining(this) | aeronautics jar |

当前版本：
- aeronautics = ee6aab8bf075500148e208f5b0fed9d74f722a8aa4e2f78a7bc176d1c4f3f2fa（31,603,055 B）；比 docs R414/R415 的 clean 件更新，需重点对照。
- sable = 2dfc53a6629d0a6d226e58af31a51d41e7fb829f079e6c8191dd21a5cd21e7d0（9,375,013 B），与 docs 记录核心 SHA 2DFC53A6 相同。
- crashfix = 1.0.5（8f8b6b08...），后装，包含 SmartBlockEntityClientInitMixin。

## 2. mixin/ASM 静态扫描（只列相关目标）

| 来源 | 目标 | 类型 | 与组装器关系 |
|---|---|---|---|
| crashfix 1.0.5 | BlockEntity（setLevel） | Inject | 父类级：PhysicsAssemblerBlockEntity 也走 setLevel -> initialize |
| crashfix 1.0.5 | SmartBlockEntity（initialize） | Inject（经 setLevel 调 initialize） | 直接调 assembler 的 initialize 覆盖 |
| aeronautics | SubLevelAssemblyHelper（balloon.SubLevelAssemblyHelperMixin） | Inject | 直接改 sable 组装入口 |
| aeronautics | ServerSubLevel（assembly_preventer.ServerSubLevelMixin） | Inject | primaryAssembler 防重复组装 |
| aeronautics | SimAssemblyHelper（balloon.SimAssemblyHelperMixin） | Inject | 组装核心 |
| CEI | SmartBlockEntity | Inject | 父类级间接影响 assembler initialize |
| constraintfix | SmartBlockEntity（ropefix） | Inject | 父类级间接 |
| DP | BasinOperatingBlockEntity / BlockEntityBehaviour | Inject/Redirect | 主要影响 Create 机器，不直接 assembler |
| createframed/interiors | Create 门/座位 | Inject | 不直接 assembler |

结论：没有后续 Create mod 直接给 PhysicsAssemblerBlockEntity/SimAssemblyHelper 注入；但 crashfix 的 setLevel->initialize 是父类级，会实际调用 assembler 的 initialize 覆盖。这是当前最强静态嫌疑。

## 3. 可疑点

### P0（最高）crashfix SmartBlockEntityClientInitMixin 提前调用 assembler.initialize()
- 证据：
  - crashfix 1.0.5 在 BlockEntity.setLevel TAIL（client）调 SmartBlockEntity.initialize()；
  - PhysicsAssemblerBlockEntity overrides initialize()：先 super.initialize()，若 primaryAssembler 则 setParent(level)，再 initializeLeverPosition()/getSubLevel() 设置 holdTip；
  - 该 initialize 在 setLevel 时被提前调用，可能发生在 NBT/primaryAssembler/子级状态就绪之前；会提前 flick lever、设置 holdTip、甚至 setParent，导致后续按住/释放逻辑状态错乱。
- 复现：装 live + crashfix 1.0.5（有 mixin）vs 同 live + crashfix noinit（见 A/B），同一位置放 assembler 并按住右键组装，比较是否响应/是否创建 sublevel/是否崩。
- 修法：
  1. 最小：noinit A/B 确认后，给 crashfix 加白名单，只对 mixer/whistle/cuckoo 等 renderer 需要的 BE 提前 initialize，排除 PhysicsAssemblerBlockEntity；
  2. 或延迟 initialize 到首 tick 前但先 readClient（保持 renderer 首帧有 behaviour）。
- 优先级：P0（用户明确说昨晚修好后装别的 mod 又坏；crashfix 是后装项）。

### P1（高）aeronautics ee6aab8b 比 R414/R415 clean 件更新
- 证据：
  - live aero 31,603,055 B / ee6aab8b，与 docs 审计里替换件一致，但比 R408/R414 基线更新；
  - 当前 aero 含 assembly_preventer.ServerSubLevelMixin（PrimaryAssemblerExtension）与 balloon.SubLevelAssemblyHelperMixin；若新版本要求 primaryAssembler 设置而旧 SimAssemblyHelper 路径未同步，组装器可能判定非 primary/无法组装。
- 复现：A/B 替换为 R414/R415 的 aero clean 件（若备份存在）或只回退 assembly_preventer 相关类，比较 assembler 是否能创建 sublevel。
- 修法：对比 ee6aab8b 与 R414 clean 的 SimAssemblyHelper/PrimaryAssembler 字节码差异；必要时回退新版 assembly_preventer 或补 primary 设置。
- 优先级：P1（若 P0 noinit 仍失败，优先查这条）。

### P2（中）CEI/constraintfix 对 SmartBlockEntity 的注入叠加
- 证据：CEI 和 constraintfix 都向 SmartBlockEntity 注入；assembler 是 SmartBlockEntity 子类，initialize/behaviour 顺序可能受影响。
- 复现：base+Create+crashfix，逐个移除 CEI/constraintfix，比较 assembler。
- 修法：确认注入优先级/是否与 crashfix 提前 initialize 叠加；必要时调整 crashfix 白名单（同 P0）。
- 优先级：中（间接）。

### P3（低）sable 版本/物理后端
- sable live SHA 与 docs 核心一致（2dfc53a6），不是新版本；但仍需看 Sable.HELPER.getContaining 与 SubLevelContainer 是否被其它 mixin 改（静态扫描无第三方直接目标）。
- 若组装后没有 sublevel，检查 Sable.Rapier/Static 日志与 SubLevelContainer.getAllSubLevels。
- 优先级：低（版本未变）。

### P4（低）createfix / create-recipes / mechanicals
- 这些不直接注入 assembler；createfix 只跳过 modded wood cutting；create-recipes 是数据；mechanicals 无 mixin。
- 不是首要嫌疑，但可作为 A/B 的对照。

## 4. 最小 A/B staging

A 臂（对照）：live 114（crashfix 1.0.5）。
B 臂（noinit）：
- 件：g70/out/sky262crashfix-1.0.5-ab-noinit.jar
  - SHA-256 = f2f747526eb6ee3491d2eecbf7dd9829a46bf63d87f8a884bdcd4a759c575770（8,505 B）
  - 只从 mixins client 列表移除 SmartBlockEntityClientInitMixin（类保留，便于回滚），保留 InputConstants bridge / mixer renderer guard / BlockEntity guard。
- staging：g70/stage/assembler-ab-noinit（base live 114，替换 crashfix；114 jar）。

判据：
- 放 assembler，按住右键拖拽/释放 -> 是否发出 AssemblePacket、是否创建 sublevel（比 SubLevelContainer.getAllSubLevels 数量）、0 crash；
- 若 B 臂恢复正常而 A 臂坏 -> P0 实锤，按 P0 白名单修；
- 若两臂都坏 -> 查 P1（aero 新版）/P2（CEI/constraintfix）。

## 5. 结论先行（A/B 后修订）
- live 臂旧 probe phase H：H_TRIGGER Success、fraction 0.004→1.000、H_RESULT sub0=ServerSubLevel@x-339.50,y76.79,z-37.50、forced=false、0 crash、0 crash-report ⇒ **live 上组装器可用**；
- 之前静态排的 crashfix 提前 initialize / aero 新版 / CEI 父类注入，均未获得实测支持，不再作为回归根因；
- 用户报告的“组装器坏了”更可能是坏世界/松手太早（世界已修）；noinit staging 仅留回归对照，不作 promote。


## 6. A/B 撤销（2026-10-21 Lead 实测）
- 旧 probe phase H（h-ticks=120）在 live 臂：H_TRIGGER Success、fraction 0.004 -> 1.000、H_RESULT sub0=ServerSubLevel@x-339.50,y76.79,z-37.50、forced=false、0 crash、0 crash-report。
- 结论：**live 上组装器可用**，不需要 noinit 对比；用户“组装器坏了”更可能是坏世界/松手太早（世界已修）。
- 本轮的 noinit staging 仅留作未来回归对照，不作为 promote 候选。
- 参考旧 probe 证据：g33/evidence（H 场景）。
