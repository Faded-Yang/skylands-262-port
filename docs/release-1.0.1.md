# skylands-262 1.0.1 发布说明（2026-10-21）

> 状态：**已 promote 到 live（115 jar，distinct mod id 115）**；本轮全部修复均经真实客户端验证（mcpfabric + 旧 probe）。
> 上一版：1.0.0（114 jar，2026-10-20）。

## 1. 本轮修了什么

| # | 问题 | 根因 | 修法 | 验证 |
|---|---|---|---|---|
| 1 | **飞岛世界「只加载一个区块」/世界进不去** | 存档 datapack `aerolith-1.3.2-26.3.zip` 的 `pack.mcmeta` 用 `min_format/max_format=121`，26.3 拒载 => 浮岛生成器不生效、区块全空；另有存档的 `zzz-skylands-fix` 引用 5 个不存在结构 => registry Unbound | 新工具 `tools/repair_skylands_world.py`：修 mcmeta 为 pack_format 81、替换过滤后的 fix pack、清空 region 重生成、自动备份 | 重生成后 y≈80 草方块岛屿 / y≈164 浮岛；用户已确认区块加载正常 |
| 2 | 大量 `Exception loading blockstate definition`（5257 条） | dndecor/createdeco 的 reduced 件用通用 Block，但 blockstate 仍带 `axis/size/half` 多状态 | 改为单默认 variant（dndecor 63、createdeco 9 door） | g172 启动日志 **0 条** |
| 3 | 大量 `Missing textures in model` / 1 条 `Multiple atlases` | 模型引用了被裁剪的贴图/跨图集 | 逐模型修复 + 补贴图（corndelight/createaddition/ends_delight/create_connected/dndecor/tfmg/createdeco） | 启动日志 0 条 `Unable to bake item_model` / `Multiple atlases` |
| 4 | `Unknown tag: sable:*`（12 个物理 tag，52 行） | sable 的 loader 用 `getTagOrEmpty` 判断 tag 是否存在，**空 tag 不会出现在 getTagOrEmpty** => 补空 JSON 无效 | 改 sable 源码 `PhysicsBlockPropertiesDefinitionLoader`：`BuiltInRegistries.BLOCK.get(tagKey).isPresent()` | g175 日志 `Unknown tag: sable:` **= 0** |
| 5 | 部分 modded 双半门破坏后另一半残留 | 门方块分布在 4 个 mod（107 门，89 双半），原版逻辑只处理 DoorBlock | 新件 `sky262-doorfix-0.1.0.jar`：mixin `Block.playerWillDestroy` 破坏同坐标另一半（`@Mixin(Block)` + `CallbackInfoReturnable<BlockState>`） | **129 door-like / failures=0** |
| 6 | Create 冲压机不工作（历史 #4 回归） | 上一轮误判为缺 `c:` 标签；实为 `data merge` 写 depot `Inventory` 不触发压制 | 测试方法修正：必须真实右键投料（press 压 depot 的 HeldItem） | live 真实右键：`Running=1, Ticks=106, Finished=1`，4 铜锭 -> `create:copper_sheet` |
| 7 | 物理组装器「坏了」 | 实测 live 上组装器功能正常；用户遇到的多半是坏世界/松手过早 | 无代码改动 | probe phase H（120 ticks）：fraction 0.004 -> **1.000**、`sub0=ServerSubLevel`、forced=false、0 crash |
| 8 | Create 中后期内容卡死（`precision_mechanism`/`sturdy_sheet`/`track` 不可得） | `create:sequenced_assembly` 静态 0 条（上游 3 条，此前因 schema 解析失败被整体删除） | 3 条配方转 26.3 schema + create-fly `SequencedAssemblyRecipeMapCodec` 的 Optional->Float cast 修复（候选 `27222486`） | 进行中：数据键名 `item`->`id` 修好后入 1.0.2 |

## 2. 升级方式
1. 用 `work/run26/mods-stable`（115 jar）替换 mods 目录；
2. **旧世界**先运行 `python tools/repair_skylands_world.py --world "<存档路径>"`（自动备份），否则空区块/registry 问题仍在；
3. 首次进入若弹「不支持使用实验性设置的世界」，点「我知道我在做什么」（自定义 dimension_type 的固有提示）。

## 3. 已知限制
- `sequenced_assembly` 3 条配方尚未进 live（等 1.0.2）；
- 少数 mod 的空 tag 类日志警告仍可能出现（不影响玩法）；
- 首次加载世界偶发卡住（已知偶发，重启客户端可恢复）；
- 列车/控制、CEI 部分副产物链仍待动态矩阵补完。

## 4. 验证产物
- 截图：`work/run26/port/g33/lab-shots/`（门/图标/press/组装器）
- 报告：`docs/lab-report-100.md`、`docs/audit-doors-equipment-100.md`、`docs/diag-create-unusable-100.md`、`docs/regress-assembler-100.md`
- 台账：`docs/LEDGER-FULL.md` R910/R915/R920
