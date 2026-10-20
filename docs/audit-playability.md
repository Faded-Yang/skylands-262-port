# 可玩性审计（mcpfabric，2026-10-20 18:00 起）

> **post-promote 收尾（Lead 实测，可直接引用）**：staging g123（live+quests）上 `sweep_blocks` = **placed 4187 / failures 0 / unknown 0**、`sweep_items` = **ok 4763 / unknown 0 / rawkey 0 / error 0**，日志 `work/run26/port/g29/g123_{blocks,items}.log`。

> 工具：mcpfabric 0.8.0+26.3（bridge 127.0.0.1:25599）+ `tools/mcpfabric_client.mjs`、`tools/mcp_prep.mjs`、`tools/sweep_blocks.mjs`、`tools/sweep_items.mjs`。
> 测试局：`work/run26/port/g33/game-g119fab`（g119 staging + mcpfabric）、`game-g122`（g122 staging + mcpfabric）。
> 纪律：mcpfabric 只用于验证局，不进 `mods-stable`；测试语言固定 `lang:zh_cn`。

## 1. 全量放置 / 物品 sweep（g119 staging）

### block sweep（`sweep_blocks.mjs`）
```
{ "placed": 4187, "failures": 0, "unknown": 25 }
```
- placed 4187 = 期望 blockstate 总数；0 failure、0 crash。
- unknown 25：**24 个是 `block_ids.json` 里的旧版残留 id**（当前 jar 无 blockstate/model）：createframed framed_radon_lamp×16、natures_spirit×2、aeronautics:levitite_blend、createaddition:bioethanol/connector_old/copper_wire_casing/liquid_blaze_burner/seed_oil；
- **1 个真实缺口**：`createaddition:accumulator`（models/item 存在，方块未注册）。
- 结论：**PASS（放置 4187/0 fail）**，unknown 属清单过期 + 1 注册缺口（R590 已处理，g117 件应清零，待新清单复跑）。

### item sweep（`sweep_items.mjs`）
```
{ "ok": 4740, "unknown": 71, "rawkey": 0, "error": 0 }
```
- **rawkey=0 PASS**（本轮 lang 修复生效）；
- unknown 71 分类（按 staging jar 资源核对）：
  - 资源存在但未注册 **55**：simulated×32（portable_engine 16 色 / directional_gearshift / linked_typewriter / creative_physics_staff/* 等）、createframed×19、ends_delight×3、aeronautics:levitite_blend_bucket×1；
  - 过期 id 16（createframed framed_radon_lamp×16）。
- 结论：R591 已由 `sky262-audit-items 0.1.0`（g121/g122）补注册 19 BlockItem+4 Item 并重生成 item_ids=4763，**待 g122 新清单复跑期望 4763/0**。

## 2. 任务书 GUI（g122 staging，quests `29f01fb7`）

- `/questbook open`（chat.send，客户端命令）→ `screen.get`：`other / "Quest Book"` 427x240 ✅

## 6. CEI ponder nbt palette 迁移

- 根因：CEI 的 15 个 ponder 场景结构 nbt 仍是旧 `Name/Properties` palette，26.3 的 palette 解析失败 ⇒ 场景只有空平台/缺方块；
- 修复：CEI 15 个 ponder nbt palette 迁移 = **`3070dc03`**（与 create 的 178 个同 R421 方案）；场景几何恢复已实测（`blaze_enchanter` / `super_experience_nugget` / `create:cogwheel` 截图见 `g33/final-audit/`）。