# 幻影方块审计（有 blockstate、无注册）

> 2026-10-20 ｜ 输入：mcpfabric 全量 4212 blockstate 放置 = 4187 成功 + **25 Unknown block type** ｜ 处理：删资源（reduced 无代码注册）
> 参考：`docs/block-render-sweep.md`、`docs/port-tfmg.md` §4（静态广度降级惯例）。

## 结论

25 个 id **全部是上游/旧 jar 残留 assets，没有对应注册代码**；无 recipe/tag 引用（仅 lang/模型自引用）。处理：**删除 blockstate + block/item 模型/定义**，保留仍有效的 bucket 物品模型（createaddition/aeronautics）。

| namespace | id 数 | 来源 jar | 性质 | 处理 |
|---|---:|---|---|---|
| createframed | 16 | `createframed-1.7.3-26.3.jar` | `framed_radon_lamp_*` 16 色 assets；jar 内 class 无 `radon` 字符串，Create radon lamp 功能未移植/未注册 | 删 blockstate+items+models |
| createaddition | 6 | `createaddition-1.3.4-26.3.jar` | `accumulator`（class 存在但注册未生效）、`bioethanol`/`seed_oil`/`liquid_blaze_burner`（流体方块，Fabric 流体未移植）、`connector_old`（旧资源）、`copper_wire_casing`（仅模型） | 删 blockstate+block 模型（+accumulator item def）；**保留 bucket 物品模型** |
| natures_spirit | 2 | `natures_spirit-...-nsB2.jar` | `framed_sugi_door`/`framed_sugi_trapdoor` assets；NS reduced 只注册普通方块，门/活板门未注册 | 删 blockstate+models |
| aeronautics | 1 | `aeronautics-fabric-...jar` | `levitite_blend` 流体方块 assets；无注册 | 删 blockstate+block 模型；保留 bucket 模型 |

## 修复件（base live 114）

| jar | 删除 entries | 旧 entries → 新 entries | 新 SHA-256 |
|---|---:|---:|---|
| createframed | 64（16×4） | 2798 → 2734 | `9f97a75774a93295add194b9c6d660c4d988b1fafb57b8e487b17321cb87e102` |
| createaddition | 10 | 857 → 847 | `a6878ebf19eeaa03cab17b8d0c987653b64fe18140fd32f9943405634e20b9cc` |
| natures_spirit | 15 | 8002 → 7987 | `53a01a18f341f286543a20cdcad1d4364c28e424d47ab21897bb3741f7b7b1db` |
| aeronautics | 2 | 3293 → 3291 | `ee6aab8bf075500148e208f5b0fed9d74f722a8aa4e2f78a7bc176d1c4f3f2fa` |

staging：`g117/stage-final/mods-candidate`（114/114）。

## 后续断言

- 全量 blockstate 数应为 **4187**；
- 全量放置应「4187 成功 / 0 Unknown block type」；
- 0 crash、registry 0。

## 备注

- createframed radon lamp 若未来上游 Create 提供 radon lamp 功能，可再用 reduced 生成器补注册，不要只靠 assets；
- createaddition accumulator 若后续移植 BE/能量系统，再单独注册（当前删资源避免空壳）。