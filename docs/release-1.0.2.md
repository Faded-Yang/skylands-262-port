# skylands-262 1.0.2 发布说明（2026-10-21）

> 状态：**已 promote 到 live（116 jar，distinct mod id 116）**；关键修复经真实客户端/probe 验证。
> 上一版：1.0.1（115 jar）。

## 1. 本轮修复（对应用户反馈）

### 1.1 物理组装器 / 拉杆「没有进度条、拉杆不动、松手才跳满」
- **根因**：aeronautics 的 Fabric 客户端入口 `SimulatedFabricClient.onInitializeClient()` 只调了 `SimulatedClient.init()`，**没有注册** `ClientTickEvents.END_CLIENT_TICK` 与 HUD `renderOverlays`；
- 后果链：`postClientTick` 不执行 → `HoldInteractionManager.tick` 不执行 → `PhysicsAssemblerGUIHandler.activeTick` 不执行 → `updateControlledByPlayer` 不调用、`visualAngle` 恒 0；`renderOverlays` 不执行 → 进度条从不绘制；`activeOnMouseMove` 仍经输入 mixin 执行 → 音效/ fraction 变但视觉死；`release()` 直接设角度 → 松手瞬间拉满回弹；
- **修复**：注册 `END_CLIENT_TICK -> SimulatedCommonClientEvents.postClientTick` + `HudElementRegistry.addLast("aeronautics:hold_interaction_overlay", ...renderOverlays...)`（aeronautics `489bda3f`）；
- **验证（probe phase H，120 ticks）**：`visualAngle = animatedValue*45`：0.169° → 2.387° → 7.308° → 17.449° → 32.722° → 40.588° → 44.195°（不再恒 0）；fraction 1.000 松手不跳满；创建 `ServerSubLevel`；HUD 进度条截图可见；0 crash。

### 1.2 物品栏图标异常（方块贴图破碎 / 显示成纹路图集）
- 静态扫描：item 模型 parent 缺失 **46→0**、真实 item 贴图缺失 **47→0**、block 贴图缺失 **11→0**、blockstate 缺失模型 **1→0**、item 定义缺失 **799→365**（生成 434）；
- `create_jetpack` 图标根因：live 的 32×32 `textures/item/jetpack.png` 与上游 3D 模型 UV 皮肤 SHA 相同 → 显示成纹路图集；已换 16×16 fallback 图标；
- create_connected 45 个 item 模型改指实际存在的 block 模型（物品栏显示 3D 方块图）；
- 验证：启动日志 `Unable to bake item_model`=0、`Exception loading blockstate`=0，`Missing textures in model` 30→20（余量为故意占位/未强造资源）；图标截图：jetpack 16×16、create_connected 3 个 3D、nachos 正常。

### 1.3 可穿戴件实测
- ✅ 可穿：`create:goggles`（HEAD）、`create:copper_backtank`（CHEST，空气条）、cardboard 四件、copper/netherite diving 头盔/靴（实测 `item replace` 全部成功）；
- ⚠ `create_jetpack`：reduced port 里是普通 `Item`（无 EQUIPPABLE），**不能穿**，只能手持右键推进（THRUST 60 tick）；如需穿戴需再加装备槽代码；
- ⚠ `aeronautics:aviators_goggles`：当前无 EQUIPPABLE 组件，不能穿。

### 1.4 客户端崩溃：natures_spirit 自定义树叶 NPE
- 崩溃：`LeavesBlock.animateTick` NPE（`ambientLeavesBlockSoundPlayer` 为 null）——26.3 `LeavesBlock` 构造要求 `AmbientLeavesBlockSoundPlayer`；
- 修复：ns 的 `VinesLeavesBlock`/`ParticleLeavesBlock`/`ProjectileLeavesBlock` 构造传 `AmbientLeavesBlockSoundPlayer.noAmbientSound()`（仅 3 个 class 变化，`abd15661`）；
- 验证：aspen/blue_wisteria/cedar/coconut 放置 + 30s + 破坏，0 crash；全库扫描仅这 3 个 `extends LeavesBlock`，其它 112 mod 无同类。

### 1.5 Create 中后期内容：sequenced_assembly 3 条配方
- 数据：`precision_mechanism`/`sturdy_sheet`/track（拆 `track_from_iron`/`track_from_zinc`）按 26.3 schema 写入 `sky262-create-seqassembly-1.0.3.jar`（`87035537`）；
- create-fly codec 修复 4 关：Optional→Float cast、Holder→Recipe cast、空 components 走 ComponentsIngredient、ingredient 数组 schema（`72614a35`）；
- 验证：`Registry loading errors`=0（3 条配方解析通过）、世界正常加载、0 crash；注：Create 的 sequenced_assembly 不是 recipe-book 条目，`/recipe give` 不适用（vanilla 对照可）。

## 2. 升级方式
1. 用 `work/run26/mods-stable`（**116 jar**）替换 mods 目录；
2. 旧世界先跑 `python tools/repair_skylands_world.py --world "<存档路径>"`（自动备份）；
3. 首次进世界若弹「不支持使用实验性设置的世界」，点「我知道我在做什么」。

## 3. 已知限制
- `create:jetpack` 不能穿戴（reduced port 缺口）；`createaddition:metal_girder` 无独立物品（仅方块模型部件）；
- 365 个 item 定义缺失（crop/potted/wall_sign/隐藏物品，未强造）；`Missing textures in model` 余 20 条（占位/降级）；
- 首次加载世界偶发卡住；列车/控制、CEI 副产物链、机器矩阵仍待补完。

## 4. 验证产物
- 截图：`work/run26/port/g33/lab-shots/`（`asmvis/`、`itemfix/`、`leaves/`、`v101-press.png`）
- 报告：`docs/lab-report-100.md`、`docs/audit-item-models-wearables-100.md`、`docs/fix-ns-leaves-npe.md`、`docs/regress-holdtip-lever-100.md`、`docs/audit-doors-equipment-100.md`、`docs/diag-create-unusable-100.md`
- 台账：`docs/LEDGER-FULL.md` R910/R915/R920/R930 + R556
