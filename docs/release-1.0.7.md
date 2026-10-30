# skylands-262 1.0.7 发布说明（2026-10-21）

> 状态：**已 promote 到 live（118 jar / 118 个不同 mod id）**。
> 本轮继续「全 mod 重构」：custom trigger 移植、aero 数据补全到 138 advancement、Create 配方补 23 条、机器矩阵 round 3。

## 1. 27 条 custom advancement trigger 移植
- 根因：1.21.1 参考件没有独立 trigger 类，只有通用 `SimpleSimulatedTrigger`，且 `register()` 从未调用 ⇒ 27 个 `aeronautics:*_builtin` / `simulated:*_builtin` 未注册，31 条 advancements 被跳过；
- 修复：新增 `Sky262CustomTriggers`（27 个 trigger 显式注册），`Simulated.init()` 调用；aeronautics `7d877f79`；
- 数据：`sky262-aero-recipes-1.0.8`（`2c8fe78f`）补回 138 条 advancements（含 `what_goes_down`/`must_come_up`/`rewind_time`/`nearsighted`/`stuck_together`/`song_of_the_sky`），parent 闭包 0 缺失；
- 验证：registry=0、`advancement grant` 实测 `for_every_action`/`must_come_up`/`rewind_time` 成功；`Couldn't load advancements` 只剩历史 5 条（createframed 3 + dungeons_arise 2，非本包）。

## 2. Create 配方补 23 条（对 1.20.1 参考件 diff）
- `sky262-create-extra-recipes-1.0.1`（`5e04690e`）：22 条 stonecutting（brass/copper/copycat/framed/tiled/industrial/weathered）+ 1 条 `crafting/materials/copper_ingot`；
- 验证：3 条 `recipe give` 成功、registry=0。

## 3. 机器矩阵 round 3（`docs/audit-create-machines-100.md` §6.7）
| 机器 | 结果 |
|---|---|
| belt | **PASS**：belt_connector 两次右键绑定 shaft → 5 格带；funnel 投料 → 铁锭传送 ≈3.6 格 |
| mechanical crafter | 建网 PASS（cogwheel 啮合 ±16、Network 5/4；不能直连轴） |
| deployer | 建网+插料 PASS（facing=down、hitLocation>0.75、HeldItem=oak_planks）；产出待查 |
| controls | standalone 无 BE（需装到列车/contraption，属正常设计） |

### 工具修正（重要）
- `players.teleport` 是 RPC 方法（之前误用 command ⇒ 玩家从未真正传送，导致大量 aim 失败）；
- `players.give` 后必须扫 `player.getInventory` 选槽；
- `interact.placeBlock({x,y,z,face})` 是最可靠的真实交互（自带 reach + 显式 face）。

## 4. 升级方式
1. 用 `work/run26/mods-stable`（**118 jar**）替换 mods；手工升级时删 `sky262-aero-recipes-1.0.6.jar`、加 `1.0.8` 与 `sky262-create-extra-recipes-1.0.1.jar`；
2. 旧世界跑 `python tools/repair_skylands_world.py --world "<存档>"`；
3. 首次进世界点「我知道我在做什么」。

## 5. 已知限制
- createframed 3 条 + dungeons_arise 2 条历史 advancement 失败（与 aero 数据无关）；
- deployer 产出未确认（下一轮查 `DeployerBlockEntity` Mode/depot 处理）；
- controls 需列车组装；
- createframed 服务端不加载；levitite 不产流体。

## 6. 验证产物
- 截图：`lab-shots/matrix3/`、`lab-shots/g183/`
- 报告：`docs/fix-aero-triggers.md`、`docs/fix-aero-data.md`、`docs/fix-create-extra-recipes.md`、`docs/audit-create-machines-100.md`
- 台账：`LEDGER-FULL.md` R604/R605/R567/R568
