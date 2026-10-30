# skylands-262 1.0.6 发布说明（2026-10-21）

> 状态：**已 promote 到 live（117 jar / 117 个不同 mod id）**。
> 本轮 = 用户新参考安装 + 全 mod 重构第一/二轮 + server-safe。

## 1. 参考安装（不改交付，只作参考）
- `work/refs/jars/`：Create Fabric 6.0.8.1 (1.20.1，内嵌 22 库 jar)、Create Aeronautics 1.3.2 bundled (1.21.1，内嵌 aeronautics/simulated/offroad)，已解包；
- `work/refs/repos/`：fabric-docs、neoforged-documentation、create-wiki、yan-mc-mod-dev、fabricators-create-old（主仓库 codeload 404，用 Old 仓库替代）；
- 索引 `docs/refs-index.md`；说明：github git 协议不可达，统一 codeload。

## 2. 全 mod 重构第一轮：API 审计
- 新工具 `tools/scan_icce.py`、`tools/scan_super.py`；
- 全库 117 jar / 32016 class：ICCE 隐患仅 2 处 latent（create-fly worldgen 死引用），super/interface 错配 0；
- 结论：API 层没有大面积系统性错误，问题集中在**数据缺失**与**行为差异**。

## 3. 第二轮：aeronautics/simulated/offroad 数据补全
| 类别 | 修复前 | 1.0.6 |
|---|---:|---:|
| recipes | 88（旧 `sky262-recipes`，仅合成） | **124**（+36 条机器配方：deploying/crushing/mixing/filling/splashing/mechanical_crafting/sequenced_assembly） |
| loot_table | 0（aero/sim） | **137**（aero40/sim94/offroad3，26.3 单数 `condition` 形式） |
| advancements | 0 | **107**（跳过 31：27 条 custom trigger 未移植 + 4 条 parent 缺失） |
- 新件：`sky262-aero-recipes-1.0.6.jar`（`f5452f28`）；删除旧 `sky262-recipes-1.0.0.jar`（新件为 recipe 超集）；
- 另有 `sky262-offroad-lootfix-1.0.0.jar`（`41a5ded2`）修正 offroad 3 张 loot 的 26.3 条件形式；
- 终验：`Registry loading errors`=0、3 条 `recipe give` 成功、破坏 aero/offroad 方块正常掉落、0 crash。

## 4. server-safe（新）
- 修复：aeronautics `Simulated/SimulatedClient/SimPacketManager` 拆 client init；toolgun 移除 main 里的 `Screen` 引用（新增 client-only hooks）；createframed 标记 `environment=client`；
- 验证：Fabric 26.3 专用服务器（`work/run26/server26`）**启动到 `Done (17.502s)`**、0 registry loading error；
- 降级：createframed 服务端不加载（联机时无 createframed 方块）；levitite blend 因当前 create:mixing codec 不认 `fluid_results`，改为产出 `aeronautics:levitite_blend_bucket`（不产流体）。

## 5. item 图标第二轮
- 补 38 个真实可见物品的 item 定义（createdeco 13 / createdieselgenerators 19 / dndecor 5 / waystones 1）；
- item 定义缺失 365 → 327（余量：MC 183、无资源技术件 65、createframed stale key 35、无贴图 32、模型部件 12）；
- 图标抽查：`createdieselgenerators:canister`、`waystones:bound_scroll`、`createdeco:brass_coinstack` 正常；
- 注：`createdeco:*_coin`、`dndecor:belt` 在构建里**不是物品**（只有 coinstack / block 形式），item-defs 为其生成的资源是无害冗余。

## 6. 升级方式
1. 用 `work/run26/mods-stable`（**117 jar**）替换 mods 目录；**删除旧的 `sky262-recipes-1.0.0.jar`**（如果手工升级）；
2. 旧世界跑 `python tools/repair_skylands_world.py --world "<存档>"`；
3. 首次进世界点「我知道我在做什么」。

## 7. 已知限制
- 27 条 advancements 的 custom trigger 未移植；
- createframed 服务端不加载；levitite 不产流体；
- 首次加载世界偶发卡住；
- belt/crafter/deployer/controls 的完整功能断言仍受自动化交互限制。

## 8. 验证产物
- 截图：`lab-shots/g177/`、`lab-shots/g149/`、`lab-shots/matrix2/`
- 报告：`docs/refs-index.md`、`docs/refactor-100.md`、`docs/fix-aero-data.md`、`docs/fix-server-safety.md`、`docs/audit-item-models-wearables-100.md`、`docs/lab-report-100.md`
- 台账：`LEDGER-FULL.md` R970/R565/R566/R601/R602
