# fix-create-data（Create jar 配方/loot 数据缺失）

> 冲压机 P0（task-37）根因；create-fly jar 只发目录、几乎不发数据。

## 根因
- `create-fly-26.2-6.0.9-2-26.3-patched.jar` 内 `data/create/recipe/**/*.json` 数量 **0**（只有目录项）；live 的 `sky262-recipes` 只有 1 条 `create:white_sail`；
- 机械冲压机 press：`Speed=-16`、`Source=shaft` 但 `Running=0`，因为 `PressingBehaviour` 找不到任何 pressing 配方；depot 铜锭永远不变。

## 修复
- 从 Create-Fly 26.2 源码（GitHub `ZurrTum/Create-Fly`，branch 26.2）提取：
  - `data/create/recipe/` **1610** 条（保留 1607；整个 `sequenced_assembly/` 删除，26.2 schema 在 26.3 解析失败）；
  - `data/create/tags/` 缺的 6 条附魔 tag；
  - `data/create/loot_table/` **632** 条，按 NS 转换器转成 26.3 schema（`condition`→`type`、`functions`→`modifier`、`block_state_property`→`match_block` 等）；
- 打成独立 data-only mod `sky262-create-recipes-6.0.9-2-26.3.jar`（id `sky262-create-recipes`），不改 create-fly jar。

## 件
- 当前：`g70/out/sky262-create-recipes-6.0.9-2-26.3.jar`，**800,309 B，SHA256 `50b5fd2c6131b8f540900224f23c60a436d7aa1f9bf38246e88ae659b6f74f51`**；
- staging：`g70/stage/p0-create-data-final`（live 113 + 本件 = 114 jar）。

## 自测
- press：铜锭 → `create:copper_sheet`；press `Running=1b` → `Finished=1b`；截图 `g70/press-shots/mcp-1792470744101.png`；
- loot：待测（`/loot give` 三表 + 实际挖方块）。

## 数据缺口统计（source 26.2 vs live jar）
| 目录 | source | live | 缺 |
|---|---:|---:|---:|
| recipe | 1610 | 0 | 1610（已补） |
| advancement | 1150 | 0 | 1150（低优先） |
| loot_table | 632 | 0 | 632（已补） |
| enchantment | 2 | 0 | 2（待看） |
| tags | 91 | 85 | 6（已补） |
| damage_type / worldgen / potato_projectile | 9/6/25 | 9/6/25 | 0 |

## 已知降级
- `sequenced_assembly` 全部剔除（precision_mechanism/sturdy_sheet/track 等；26.2 schema 与 26.3 不兼容），需后续单独按 26.3 schema 转换；
- advancement 1150 暂未补（成就树缺失）；enchantment 2 待确认。
## DOCS FIRST 对照（2026-10-20 用户要求）
- 参考 `docs/API-263-data-schema.md §7`：源码构建 jar 会比发布 jar 少数千条 data，数据应从原发布 jar 取；
- 现状冲突：本地所有 `create-fly*` 副本 `data/create/recipe/**/*.json` 均为 0；Create-Fly 最新 release 仅 26.1.2，**不存在 26.3 发布 jar**（live 是 26.3 源码 patched 构建）⇒ 无法照 §7 取发布 jar 数据；
- 采用 26.2 source 数据 + 26.3 schema 转换（loot），并剔除 26.2 不兼容的 `sequenced_assembly`；此偏差已报 Lead。
- 另参考 `docs/DELIVERY.md`：createadddition 曾因 schema 丢 51 条配方；本件为同族缺口补齐。
## enchantment 2（probe PASS）
- 件：`sky262-create-recipes-6.0.9-2-26.3.jar`，**801,486 B，SHA256 `ba7eb2a32b9d4ff9f6f1d923cc40f4c3d0ac7f14cdd554336d003aa5be529e7d`**；staging `g70/stage/p0-create-ench-final`（114）；
- 内容：`create:capacity`、`create:potato_recovery`（effect requirement 的旧 `condition` 键已递归转 `type`），tags 补 `pressurized_air_sources`；
- probe：registry 0、0 crash；`/enchant @s create:capacity` / `potato_recovery` 返回“钻石镐不支持此魔咒”（非“未知”），证明注册表存在；截图 `g33/mcp-shots/ench.png`；可 promote。