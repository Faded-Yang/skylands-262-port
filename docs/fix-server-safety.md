# server-safety 完整收口 + aero datapack schema

## 1. aeronautics main entrypoint

- `Simulated.init()` 的 `SimSpriteShifts.init()`（客户端 sprite shift）移到 `SimulatedClient.init()`；
- `SimPacketManager.init()` 只注册 serverbound，新增 `initClientbound()` 由客户端调用；
- 改动：`Simulated.class`、`SimulatedClient.class`、`SimPacketManager.class`；
- SHA `608f038bfdf08efe17c020a59fc74b88f56ffca049ab4d037ff629adb0de5ced`。

## 2. toolgun main entrypoint

- `PortableStructurePrinterBlock26.useWithoutItem` 不再直接 `Minecraft/Screen`，改调 `ToolgunClientHooks.openPrinterScreen`；
- 新增 `ToolgunClientHooks`（client-only）；主类/服务端 class 无 `Screen` 引用；
- 重建自 `g70/src_toolgun` 源码；SHA `773fcbd94626f80292c9f12946791fee222a6d9756599b5a7680bc11dc68ddc6`。

## 3. createframed

- 该 jar 的 `CreateFramedBlocks` 构造器直接引用 `CTSpriteShiftEntry/HorizontalCTBehaviour`（客户端类型），无源码可拆；
- 数据侧将 `fabric.mod.json.environment` 改为 `client`，服务端不加载 createframed；
- **降级**：服务端无 createframed 方块（客户端有）；如需联机完整内容，需后续按源码拆 client init。
- SHA `c4db59d2225ef9458de06469466b34946f598edc228e078f7c9d5a2637b33266`。

## 4. aero-recipes 1.0.6 datapack schema

修 8 处：
1. 4 个 advancement：`criteria.conditions.location` → `{"type":"minecraft:match_block","blocks":"simulated:..."}`；
2. loot `simulated:blocks/merging_glue`：`minecraft:air` → `simulated:merging_glue`；
3. filling `simulated:filling/honey_glue`：`fluid_tag` → `#c:honey`；
4. mixing `aeronautics:mixing/levitite_blend`：该 build 的 `create:mixing` codec 不认 `fluid_results`；改为 item `results` 产出 `aeronautics:levitite_blend_bucket`（**降级**：不再产流体，需后续 codec/数据专项）；
5. seqassembly `simulated:sequenced_assembly/engine_assembly`：cutting step 补 `"processing_time": 50`。

SHA `f5452f28975cf5a9264e2d7acfa6e01aa6693b072c9135d8dcfddd7a2a3af757`（1.0.6）。

## 5. server26 实测

- 使用上述 aero/toolgun/createframed + aero-recipes 1.0.6；
- 日志：`Done (17.502s)!`，0 registry loading error；
- 仍有 sable 对缺失 mod 的 `Unknown block/tag` 日志（copycats:copycat_step、quark 等），不影响启动。

## 6. staging

- `g169/stage-final/mods-candidate`（117 jar = live 116 + aero-recipes 1.0.6；4 个同名替换）；
- 客户端回归：aero 608f038b 需 probe 验进世界/机器。
