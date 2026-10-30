# 27 条 custom advancement trigger 移植（aeronautics/simulated `*_builtin`）

> 参考 `docs/fix-aero-registrate.md`（14 条 trigger 的 26.3 API 事实）、`docs/fix-aero-data.md`（27 条 trigger 导致 advancement 跳过）。

## 结论

- 1.21.1 `aeronautics-bundled` 里**没有每个 trigger 的独立类**；只有 `SimpleSimulatedTrigger` + `SimulatedCriterionTriggerBase`（已移植到源码）；
- 每个 advancement 在构造时调用 `AeroAdvancementTriggers.addSimple` / `SimAdvancementTriggers.addSimple` 生成 `SimpleSimulatedTrigger`；
- live jar 的问题是 **register() 从未被调用**（且 advancement 静态初始化未触发），所以 27 个 `*_builtin` 未注册。

## 代码修复

- 新增 `dev.simulated_team.simulated.data.advancements.Sky262CustomTriggers`：显式注册 27 个 `SimpleSimulatedTrigger`（7 aeronautics + 20 simulated，ID 从 1.21 advancement JSON 提取）；
- `Simulated.init()` 末尾调用 `Sky262CustomTriggers.register()`；
- 基于 server-safe aero `608f038b` 重建；仅新增 1 class + 改 `Simulated.class`；
- aero SHA `7d877f79dcafb4d1d0e75afa4179b15d3ecb301ab8d1a62a3fce2711d0534293`。

## 数据修复

- 从 1.21.1 aeronautics/simulated jar 取回 27 条 `*_builtin` advancement JSON，放入 aero-recipes 1.0.7；
- 这些 JSON 的 criteria 形态（`conditions` 为 trigger id 字符串）与 `SimpleSimulatedTrigger` 的 `Identifier.CODEC` 兼容；
- aero-recipes SHA `e8bdf2413fedcc2856abf750a30dec211927bd50fcff07d41bcb14371989542e`。

## 验证

- server26 实测：`Done (2.616s)!`，无 `Registry loading errors`（27 条 advancement 全部加载）；
- 仅剩 sable 对缺失 mod 的 `Unknown block/tag` 日志，不影响；
- 客户端进世界/trigger 实机触发待 probe。

## staging

- `g173/stage-final/mods-candidate`：117 jar = live 117；
- 替换：aero `7d877f79`、aero-recipes `e8bdf241`、toolgun `773fcbd9`、createframed `c4db59d2`、jetpack `11a738db`。

## 追加：`simulated:what_goes_down`（g174-final 反馈）

- g182 发现 2 条新 advancement (`simulated:must_come_up` / `simulated:rewind_time`) 的 parent `simulated:what_goes_down` 缺失；
- 从 1.21.1 simulated jar 取回 `data/simulated/advancement/what_goes_down.json`，加入 aero-recipes 1.0.8（parent `simulated:get_a_grip`，trigger `minecraft:inventory_changed`）；
- server26 实测 `Done (1.807s)`，上述 2 条不再报错；仅剩 dungeons_arise 2 条历史缺失（非本包）。

### 1.0.8

- SHA `612dd4e0a4cbac1b57ddf5b993e56eb24ebf68c968cbe3bb6e8a1a0c751bf5d6`；
- staging：`g175/stage-final/mods-candidate`（117 jar，替换 aero-recipes）。
