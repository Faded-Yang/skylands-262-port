# skylands-262 1.0.3 发布说明（2026-10-21）

> 状态：**已 promote 到 live（116 jar）**；1.0.2 修复 + 可穿戴/剪贴板/数码管/atlas 补全。

## 1. 本轮新增修复

### 1.1 可穿戴装备（用户要求「真穿身上」）
- `create:jetpack` / `create_jetpack:netherite_jetpack`：`Item.Properties` 加 `EQUIPPABLE` CHEST（asset、swappable、damageOnHurt=false）+ equipment 资源；**实测可穿胸槽**，手持右键推进保留（1.5s 上升 ~11 格）；
- `aeronautics:aviators_goggles`：加 `EQUIPPABLE` HEAD + equipment 资源；**实测可戴头**；
- 已可穿（前一轮验证）：`create:goggles`、`copper_backtank`（带空气条）、cardboard 四件、铜/下界合金潜水头盔+靴。

### 1.2 剪贴板 GUI 崩溃（blocks 扫到 224 命中）
- 根因：`ClipboardScreen.removed()/send()` 在 `content == null` 时仍调用 `setPreviouslyOpenedPage`/`setPages` → NPE；
- 修复：ASM 在 live 原类 `removed()`/`send()` 入口插 `if (content == null) return;`（`COMPUTE_FRAMES` 重算，避免上次整类重编译的 VerifyError）；
- 实测：打开/关闭 ×3 正常，无 VerifyError/NPE。

### 1.3 数码管（Nixie Tube）右键崩服务端（P0）
- 根因：`create-fly DynamicComponent.getCommandSource` 仍用 1.21 的 9 参 `CommandSourceStack` 构造；26.3 改为 7 参 → `NoSuchMethodError` 打崩 server tick；
- 修复：改用 26.3 7 参构造（`PermissionSet` + server + entity）；
- 实测：手持剪贴板右键数码管 ×3 全部 Success，服务端不崩。

### 1.4 剩余 20 条 `Missing textures in model` → 0
- 17 条 TFMG 流体 block model particle：`tfmg:block/*` 指向 `tfmg:fluid/*_still`，但 `textures/fluid` 不在 blocks atlas 自动扫描目录；新增 `assets/minecraft/atlases/blocks.json`（49 个 fluid still/flow single sources）；
- 3 条 simulated diagram：在 aeronautics 的 atlas 配置追加 3 个 `simulated:entity/diagram_*` sources；
- 终验：**`Missing textures in model` = 0**。

### 1.5 blocks 全量扫描发现并修复的其它问题（前两轮）
- natures_spirit 树叶 `LeavesBlock.animateTick` NPE（客户端崩溃）：3 个树叶类构造改 `AmbientLeavesBlockSoundPlayer.noAmbientSound()`；
- 组装器/拉杆无进度条、拉杆不动、松手跳满：aeronautics 注册 `END_CLIENT_TICK` + HUD `renderOverlays`；
- 物品图标破损/图集（jetpack 等）：item 模型 parent 46→0、item 贴图 47→0、block 贴图 11→0；
- seqassembly 3 条配方 + 4 个 codec bug 修复。

## 2. 升级方式
1. 用 `work/run26/mods-stable`（116 jar）替换 mods；
2. 旧世界跑 `python tools/repair_skylands_world.py --world "<存档>"`；
3. 首次进世界点「我知道我在做什么」。

## 3. 已知限制
- jetpack 穿戴后**空手右键不触发推进**（推进仍在手持 jetpack 时生效；如需穿戴即推需另加输入/mixin）；
- `createaddition:metal_girder` 不是物品（仅方块模型部件）；
- blocks 全量扫描在 3000-3200 段出现服务端挂起（非 crash），正在二分定位；
- 首次加载世界偶发卡住；列车/控制、CEI 副产物链、机器矩阵待补。

## 4. 验证产物
- 截图：`lab-shots/v103/`、`lab-shots/g149/`、`lab-shots/g146/`、`lab-shots/asmvis/`、`lab-shots/v102/`
- 报告：`docs/lab-report-100.md`、`docs/fix-wearables-100.md`、`docs/fix-clipboard-screen-npe.md`、`docs/fix-nixie-tube-command-source.md`、`docs/audit-item-models-wearables-100.md`
- 台账：`docs/LEDGER-FULL.md` R930/R940 + R556/R557/R558/R559/R596
