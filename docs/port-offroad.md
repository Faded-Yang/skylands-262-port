# offroad 最小移植（26.3 Fabric）—— port-offroad

> 背景：`FEATURE-GAP.md` 发现原包 `create-aeronautics-bundled-1.21.1-1.3.2.jar` 内嵌 3 个 jar（aeronautics / simulated / **offroad**），前两者注册表 0 缺失，**offroad 整块缺失**（3 方块、7 物品、49 lang、borehead 实体）。本文件记录最小移植。

## 1. 来源与产物

| 项 | 值 |
|---|---|
| 原包 | `%APPDATA%\.minecraft\versions\Create 航空学 × 浮空群岛\mods\create-aeronautics-bundled-1.21.1-1.3.2.jar` 内嵌 `META-INF/jarjar/dev.ryanhcode.offroad.offroad-neoforge-1.21.1-1.3.2.jar`（830,487 B，325 entries） |
| 候选 jar | `work\run26\port\g67\out\sky262-offroad-1.0.0.jar` |
| size | **54,590 B** |
| SHA-256 | `4d7d003bc6a80060562ca5861c78545f170b4a3c7894c91041daa92487ea3a11` |
| base | live aero `1BED71C9`（独立 jar，**不改 aeronautics 任何字节**） |
| 验证 | `g67/out/_static_verify.txt` PASS（jar 结构/资源齐全 + `-Xverify:all` SMOKE_OK） |
| staging | `g67/stage/mods-baseline`（71 jar）/ `mods-candidate`（+ offroad = 72 jar）；aero 仍 `1BED71C9` |

## 2. 注册内容（最小广度）

### 方块（3）
- `offroad:wheel_mount`：`HorizontalDirectionalBlock`（FACING 四向），cube 模型，贴图 `offroad:block/suspension_0`；
- `offroad:rockcutting_wheel`：同上，贴图 `offroad:block/rockcutting_wheel`；
- `offroad:borehead_bearing`：同上，贴图 `offroad:block/borehead_bearing_side`；
- 全部 `setId()` 前置、`MapColor.METAL`、`strength(2.0)`、`SoundType.METAL`；BlockItem 用 `useBlockDescriptionPrefix()`。

### 物品（7）
- 3 个 BlockItem（wheel_mount / rockcutting_wheel / borehead_bearing）；
- 4 个普通 Item：`tire` / `small_tire` / `large_tire` / `monstrous_tire`。

### 创造栏
- 自建 `offroad:offroad` CreativeModeTab，icon=wheel_mount；
- `CreativeModeTabEvents.modifyOutputEvent(TAB).register(...)` 填入 7 个 item（26.3 Fabric 的 `CreativeModeTab.Output` 不可直接 lambda，必须走事件）。

### 资源
- blockstates：3 个（facing 四向 → cube 模型）；
- models：`block/simple/<id>.json`（cube_all）+ `item/<id>.json`（item/generated）；
- `assets/offroad/items/<id>.json`：26.3 新 item model 入口（7 个）；
- 全部原版贴图（textures/block/**）与 lang（en_us 49 keys + 其它语言）照抄；
- loot_table/blocks 3 个照抄原文件。

## 3. 明确 TODO（未移植）

| 项 | 原因 |
|---|---|
| 车轮/轮胎物理行为、悬挂、载具交互 | 原 `offroad` 是 NeoForge 1.21.1，行为层依赖 Create 1.21 API/Sable；本轮只做注册/放置广度 |
| `borehead_contraption_entity` | 实体 + 钻头 contraption 行为复杂；本轮未注册 |
| `rockcutting_wheel` 的 .obj/.mtl 模型 | 26.3 无原自定义 OBJ loader；用 cube 模型占位 |
| recipes / advancements / tags | 1.21 数据 schema 与 26.3 不同；为避免数据加载错误，未打入（后续可转换） |
| 原方块形状/BE | 用普通 Block 占位；原 BE（若有）未移植 |

## 4. 验证要求（待 probe）

1. 标题画面 → Mods 列表出现 `offroad`（Create Offroad (minimal 26.3 port)）；
2. 进世界后 `Registry loading errors: 0`、0 crash；
3. 创造栏出现 offroad 标签页，7 个物品可见；
4. 放置 3 个方块（wheel_mount / rockcutting_wheel / borehead_bearing）成功、有模型、可破坏；
5. 4 个轮胎物品在背包/创造栏可见。

## 5. 回滚

- 独立 jar：从 `mods-stable` 删除 `sky262-offroad-1.0.0.jar` 即完全回滚；aeronautics 未改。
