# TFMG（The Factory Must Grow）评估 + reduced batch1

> 日期：2026-10-20 凌晨 ｜ 角色：crashfix-26 ｜ 源：tfmg-1.2.0.jar（4.9 MB）

## 1. 规模/可行性

| 项 | 数值 |
|---|---|
| blockstates（方块） | **436** |
| item 模型 | 584（含 block item） |
| block 模型 / block 贴图 / item 贴图 / lang | 1595 / 572 / 188 / 10 |
| data json（recipe/loot/advancement/tags/worldgen） | 1747（全丢） |
| 类 | **671**（BlockEntity 92、fluid 37、worldgen 7、entity 94、recipe 77、renderer 49） |
| 跨命名空间资产 | assets/create 71、assets/minecraft 3（缺失仅 cosmetic；本批模型贴图缺失 0） |

**结论：可行**——assets 型 reduced，通用静态 Block/BlockItem，单默认 variant，无 data；机器/BE/流体方块退化为静态装饰。

## 2. 分批计划（累积件，ids 只增不减）

- 每批 **60** 方块（436 / 60 → 8 批左右；按 Lead 60–100 可调），每批 1 个累积 jar；
- batch1：前 60 个（`accumulator` … `brown_rebar_concrete`）；
- 后续批次继续追加 blockstates/items 与注册项，旧 ids 保留。

## 3. batch1 结果

| 项 | 结果 |
|---|---|
| 件 | `g70/out/sky262-tfmg-1.2.0-26.3-b1.jar`，**2,338,689 B，SHA256 `a05f8f6782916a42e1c1653501f5c19e22a820c1c7e12d5e8619fcabbb8a7f83`** |
| staging | `g70/stage/tfmg-b1-final`（base live **103** + 本件 = **104 jar**） |
| 规模 | 60 方块 + 60 BlockItem |
| 自检 | blockstates 60、items 60、**data 0**、missing block/item model **0**、跨命名空间贴图缺失 **0**、lang 合法 |
| 标题 | **TITLE_SCREEN_OK** |
| 进世界 | **WORLD_OK joined=true 44.8s**；0 crash |

## 4. 噪声/降级

- 机器/BE/流体方块无功能、无 BE；方块整块碰撞；
- 未恢复 recipe/loot/advancement/tags/worldgen 数据；模型复杂方块（多状态）合并为单默认 variant；
- 部分机器模型可能引用 create/neoforge loader（本批 0 缺失记录，后续批次继续统计）。

## 5. 给 probe 的 MCP 验收（batch1）

~~~powershell
node tools\mcp_fabric_client.mjs player.getState
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s tfmg:aluminum_block 1"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s tfmg:aluminum_bars 1"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/setblock ~ ~ ~ tfmg:accumulator"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/setblock ~ ~1 ~ tfmg:air_intake"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/setblock ~ ~2 ~ tfmg:aluminum_block"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/setblock ~ ~3 ~ tfmg:aluminum_bars"}'
node tools\mcp_fabric_client.mjs world.getBlock '{"x":0,"y":0,"z":0}'
node tools\mcp_fabric_client.mjs chat.get
node tools\mcp_fabric_client.mjs screenshot.take --out tfmg-shots
~~~
断言：give/setblock 不报 unknown；world.getBlock 读回一致；0 crash/0 registry；≥2 张 PNG。
## 6. batch2（加大到 94 新方块/批）

- 件：`g70/out/sky262-tfmg-1.2.0-26.3-b2.jar`，**2,384,529 B，SHA256 `d1ec84fde2233b7b158f3055dfb8d6a1794858395dc34030fa4a644fcb9c156b`**；
- 累积：**154 方块 + 154 BlockItem**（b1 60 + 新增 94）；
- staging：`g70/stage/tfmg-b2-final`（base live **104** + 本件 = **105 jar**）；
- 自检：blockstates 154、items 154、**data 0**、missing item model 0；block model 仅 `copycat_cable_block` 引用 `minecraft:block/air`（原包有意，非缺失）；跨命名空间贴图缺失 **0**；
- **TITLE_SCREEN_OK**；**WORLD_OK joined=true 43.0s**；0 crash；
- 后续：剩余 282 → **b3=248、b4=342、b5=436**（94/批，共 5 批收完）。

### batch2 给 probe 的抽样

~~~powershell
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s tfmg:fossilstone 1"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/give @s tfmg:flarestack 1"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/setblock ~ ~ ~ tfmg:fossilstone"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/setblock ~ ~1 ~ tfmg:flarestack"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/setblock ~ ~2 ~ tfmg:fireproof_chemical_vat"}'
node tools\mcp_fabric_client.mjs chat.send '{"message":"/setblock ~ ~3 ~ tfmg:aluminum_block"}'
node tools\mcp_fabric_client.mjs world.getBlock '{"x":0,"y":0,"z":0}'
node tools\mcp_fabric_client.mjs screenshot.take --out tfmg-b2-shots
~~~
断言：无 unknown id、0 crash/0 registry、读回一致、≥2 张 PNG。
## 7. batch3（累积 248 方块）

- 件：`g70/out/sky262-tfmg-1.2.0-26.3-b3.jar`，**2,431,962 B，SHA256 `0d2def8f92cfb8f0e5abc5d9113d65a7134a7824be8c74c41543de8f15f7d427`**；
- 累积：**248 方块 + 248 BlockItem**（b1 60 + b2 +94 + b3 +94）；
- staging：`g70/stage/tfmg-b3-final`（base live **106** + 本件 = **107 jar**）；
- 自检：blockstates/items 248、**data 0**、missing item model 0；block model 仅 `copycat_cable_block` 用 `minecraft:block/air`（原包有意）；跨命名空间贴图缺失 **0**；
- **TITLE_SCREEN_OK**；**WORLD_OK joined=true 42.8s**；0 crash；
- 后续：b4=342、b5=436（94/批，收满 436）。
## 8. batch4（累积 342 方块；staging 替换旧 tfmg jar）

- 件：`g70/out/sky262-tfmg-1.2.0-26.3-b4.jar`，**2,478,473 B，SHA256 `5bc1cc1f1060b02571739ed46e5f2a71702f4a1fa2f06226a060a4b22be81df4`**；
- 累积：**342 方块 + 342 BlockItem**；
- staging：`g70/stage/tfmg-b4-final`（base live **110**，**移除旧 b3 jar 后替换为 b4**，避免同 mod id 双 jar）；
- 自检：blockstates/items 342、**data 0**、missing item model 0；block model 仅 `copycat_cable_block` 用 `minecraft:block/air`（有意）；跨命名空间贴图缺失 **0**；
- **TITLE_SCREEN_OK**；**WORLD_OK joined=true 42.6s**；0 crash；
- 后续：b5=436（最后一批）+ TFMG zh_cn 补全。
## 9. batch5（最终：436/436 全量）+ TFMG zh_cn

- 件：`g70/out/sky262-tfmg-1.2.0-26.3-b5.jar`，**2,538,474 B，SHA256 `71b8f4388ae1ac73d21986ef1a24a12a5f24a3356fabff65bc2a51d7c5318565`**；
- staging：`g70/stage/tfmg-b5-final`（base live **110**；**移除旧 b3/b4 jar，只放 b5**，110 jar）；
- 规模：**436 方块 + 436 BlockItem（全量）**；
- 自检：blockstates/items **436/436**、**data 0**、missing model **0**（16 个无自有模型的方块使用 vanilla `minecraft:block/air` / `minecraft:item/barrier` 兜底）、跨命名空间贴图缺失 **0**；
- **TFMG zh_cn 同 jar 补齐**：`assets/tfmg/lang/zh_cn.json` 1299 键、相对 en_us **missing 0**；`lithium_torch`→锂火把、`aluminum_block`→铝块；`lang_audit` tfmg=缺0；
- **TITLE_SCREEN_OK**；**WORLD_OK joined=true 42.8s**；0 crash。
## 10. probe 复验（b5 final，PASS）

- `N_STAY` / WS ready；`Registry loading errors`=0；0 crash；
- give 中文：`tfmg:lithium_torch` → 锂火把、`tfmg:aluminum_block` → 铝块；
- setblock→readback 4/4 一致：zinc_frame / zinc_truss / machine_input / fossilstone；
- tfmg 域 Missing model=0；截图 `g33/mcp-shots/tfmg_final.png` / `mcp-1792440875416.png`；
- 判读：PASS，可 promote（110 jar，累积 436 方块，b5 覆盖 b1–b5）。