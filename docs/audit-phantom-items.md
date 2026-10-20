# 幻影物品审计（items 资源在、物品未注册）

> 2026-10-20 ｜ 输入：g119 item sweep 4811 = 4740 ok + 71 unknown + 0 rawkey
> 参考：`docs/audit-phantom-blocks.md`、`docs/lang-gap.md` §5。

## 71 unknown 分类

| 类别 | 数量 | 性质 | 处理 |
|---|---:|---|---|
| 嵌套模型部件 id | 32 | `simulated:creative_physics_staff/*`、`simulated:plunger_launcher/*`、`createframed:package/rigging/*` 是 **items 子目录里的模型部件**，不是物品 id；被真实 item model 引用 | **保留 assets**，从 `item_ids.json` 生成规则中排除（items/ 相对路径含 `/`） |
| 已删方块的残留 item | 16 | `createframed:framed_radon_lamp_*`（g117 已删 blockstate/items/models） | 从 `item_ids.json` 排除；staging 用 g117 件 |
| 真物品/方块物品缺口 | 19 | `simulated:*_portable_engine` 16 色 + `directional_gearshift` + `linked_typewriter` + `steering_wheel`：blockstate/item 资源都在，**BlockItem 未注册** | 新增 companion `sky262-audit-items` 注册 BlockItem |
| 真物品缺口 | 3 | `ends_delight:dragon_egg_shell` / `ender_sauce` / `liquid_dragon_egg_in_shell` | 同 companion 注册普通 Item |
| 流体桶残留 | 1 | `aeronautics:levitite_blend_bucket`（block 已删，保留 bucket 模型） | companion 注册普通 Item |
| 方块缺口 | 1 | `createaddition:accumulator`（g117 已删 blockstate/block model/item def） | 不再出现在 block_ids；无 item |

## 修复件

- `sky262-audit-items-0.1.0.jar`（id `sky262_audit_items`）：注册 19 个 BlockItem（仅当 item 不存在且 block 已注册）+ 4 个普通 Item；日志 `[sky262_audit_items] registered=N skipped=M`；
  - SHA-256 `f01e37c41ef276c76fc66bf2d2f249a2f4443b6b78d90fe9134d8b06acde19f7`，2,489 B；
- 列表重生成：`work/run26/port/g29/block_ids.json`（4212）、`item_ids.json`（4763，排除嵌套部件 + 已删 lamp）；
- staging：`g121/stage-final/mods-candidate`（live + g117 幻影方块删件 + companion）；
- 预期 sweep：block **4187/0 unknown**、item **4763/0 unknown**。

## 注意

- companion 只是注册层：portable engine 等仍无 BE/行为，仅让 give/创造栏可获取；后续功能另补；
- 嵌套模型部件绝不能当 item id 加入 sweep 清单（会被 `/give` 判 unknown）。