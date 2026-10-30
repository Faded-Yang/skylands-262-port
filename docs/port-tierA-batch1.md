# Tier A 小件重写 · 批 1（aerocopycats / throwable rope connector）

base = live 74 jar（aero `1BED71C9`、sable `1088C4FE`、create `0E9B26D3`；完整 74 个 SHA 见 `g68/out/*.meta.json` 的 `base_jars`）。

## 1. aerocopycats 1.1.1（纯数据，最简单）

| 项 | 值 |
|---|---|
| 原 jar | `aerocopycats-1.1.1.jar`（14,702 B）：assets/aerocopycats/lang + data/copycats/physics_block_properties（26 条）+ 2 个空 @Mod 类 |
| 候选 | `g68/out/sky262-aerocopycats-1.1.1.jar` |
| size | **9,185 B** |
| SHA-256 | `fdc13b8245aa20d54deef0a026e3f1f41b6d1ce09912379033daa573b28f2899` |
| 内容 | 原 assets/lang + `data/copycats/physics_block_properties/*.json` 原样复制；`fabric.mod.json` id=`aerocopycats`、无 entrypoints |
| 说明 | 原 Java 只有 `HELLO FROM COMMON SETUP`，真正数据是给 **copycats** 的 physics properties；copycats 目前未移植 ⇒ 本 jar 先保证 mod 列表/数据加载 0 错误，等 copycats 移植后自动生效 |

## 2. create_aeronautics_throwable_rope_connector 0.4.3（最小广度）

- 上游源码已找到并作规格参考：GitHub `sprocketaudio/Create-Aeronautics-Throwable-Rope-Connector`（README + `src/main/java` 的 item/entity/launcher/BE 源码）。
- 原 jar：187,714 B；方块 `mounted_rope_launcher`（facing/axis_along_first/half 24 variants）、物品 `throwable_rope_connector` / `rope_connector_launcher`、实体 `throwable_rope_connector_projectile` + `mounted_rope_launcher_seat`（未移植）。

| 项 | 值 |
|---|---|
| 候选 | `g68/out/sky262-throwable-rope-connector-0.4.3.jar` |
| size | **26,024 B** |
| SHA-256 | `2d34ae53350ce91114b19541f845fe931f48693a9a03136fd911c67a2034d90` |
| 内容 | `mounted_rope_launcher` 方块（FacingBlock，4 向）、3 个物品（方块物品 + throwable + launcher）、自建创造栏；原 textures/models/lang/loot_table 原样带入；gen 26.3 blockstate/items 定义 |
| 行为 | **TODO**：投掷物/launcher 发射/seat 骑乘/客户端渲染/网络包；本轮只保证注册/放置/创造栏/0 错误 |

## 3. 验证（待 probe）

1. 标题 + 进世界；Mods 列表出现 `aerocopycats 1.1.1` 与 `Create Aeronautics: Throwable Rope Connector (minimal 26.3 port)`；
2. `Registry loading errors: 0`、0 crash；
3. 创造栏出现 rope 模组的 tab（3 物品）；`mounted_rope_launcher` 可放置；
4. aerocopycats 无 tab/物品，只验 datapack 加载不报错。

## 4. 回滚

- 删除 `sky262-aerocopycats-1.1.1.jar` / `sky262-throwable-rope-connector-0.4.3.jar` 即完全回滚；不改核心 4 jar。

## 5. 源码版升级：throwable rope connector（反编译 → 移植）

- 已用 `tools/decompile.py` 反编译原 jar 到 `port/g70/src/throwable_rope/`（30 java）；上游 repo `sprocketaudio/Create-Aeronautics-Throwable-Rope-Connector` 同时作为规格；
- 本版升级 `throwable_rope_connector` 物品行为（源：`ThrowableRopeConnectorItem` + `ThrowableRopeConnectorPlacement`）：服务端 raycast（10 格）→ 校验目标面 sturdy / 放置位可替换 -> 放置 `simulated:rope_connector` 方块 -> 给 `simulated:rope_coupling`（尝试写 `simulated:rope_first_connection` 组件）-> 消耗物品 + 10 tick cooldown + 音效；
- 仍未做：投掷物实体（`ThrowableRopeConnectorProjectile`）、launcher/seat/网络/客户端渲染；
- 新候选：`g68/out/sky262-throwable-rope-connector-0.4.3.jar`，SHA `dd3c4ce19176342b101e9d2956f4782c4b3dce7899560658b6ebadb3785f0369`，29,540 B；验证 PASS；staging 已更新。

## 6. 基线更新（live 72 jar，aero 64926763）

- 按 72 jar 重建后（确定性 zip 时间戳），候选 SHA 更新：
- aerocopycats: `91e15f97c8ad7824442e8aebf9dc3d154a26f4317f83f4de82baf60f14f6d5dc`（9185 B）
- throwable rope connector: `0cf5bdf96692efb499dd039463b405326196cbe82bb62c714ce577d83780ad84`（29540 B）
- staging g68: baseline 72 / candidate 74。
