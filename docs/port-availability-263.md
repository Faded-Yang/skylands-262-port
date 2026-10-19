# port-availability-263 —— 缺失 49 件「是否有 26.x Fabric 构建」全量核查

> 日期：2026-10-19 ｜ 数据源：`work/run26/port/p1/_probe_missing.py` 重跑（Modrinth `/project/<slug>/version?loaders=["fabric"]`，逐项目取最新 Fabric 版本）
> 结果落盘：`work/run26/port/g66/out/evidence/fabric-availability-263.json`（含 slug/best 版本）
> 判读规则（已由 dragonlib 实测验证）：**26.x Fabric 构建 = named，可直接放宽 minecraft 版本试装；1.21.x 及更早 = intermediary（class_xxx），启动必挂，直接跳过**（见 `docs/port-dragonlib.md` §1）。

---

## 1. 结论：49 个缺口里只有 5 个有 26.x Fabric 构建（其中 2 个已装）

| jar | Modrinth slug | 最新 Fabric 版本 | 状态 |
|---|---|---|---|
| `Paxi-1.21.1-NeoForge-5.1.3.jar` | paxi | **26.1.2** | ✅ 已装（批 1） |
| `YungsApi-1.21.1-NeoForge-5.1.9.jar` | yungs-api | **26.1.2** | ✅ 已装（批 1） |
| `natures_spirit-2.2.6-1.21.1.jar` | natures-spirit | **26.1.2** | 🔶 已下 2.3.0-26.1.2 并试装（首错 dye 字段，见 `docs/port-natures-spirit.md`） |
| `create-enchantment-industry-2.5.4b.jar` | create-enchantment-industry | **26.1.2** | 🔶 部分（第 2 断点 fluid builder，`docs/port-deps-batch2.md`） |
| `CreateDragonsPlus-1.11.9.jar` | create-dragons-plus | **26.1.2** | 🔶 部分（与 CEI 同断点） |

---

## 2. 只有 1.21.x Fabric（intermediary → 跳过）

| jar | slug | 最新 Fabric |
|---|---|---|
| culturaldelights-1.21.1-0.19.2 | cultural-delights | 1.21.1 |
| dragonlib-3.0.29 | dragonlib | 1.21.1（已实测失败，`docs/port-dragonlib.md`） |
| lodestone-1.21.1-1.8.2 | lodestonelib | 1.21.1 |
| modernfix 5.27.26 | modernfix | 24w14a（1.21 快照） |
| player-animation-lib 2.0.4 | playeranimator | 23w13a_or_b（1.21 快照） |

## 3. 只有 1.20.x 或更旧（距离 26.3 太远 → 跳过）

| jar | slug | 最新 Fabric |
|---|---|---|
| copycats-3.0.9 | copycats | 1.20.1 |
| create_jetpack-5.2.1 | create-jetpack | 1.20.1 |
| createoreexcavation-1.6.8 | create-ore-excavation | 1.20.1 |
| createrailwaysnavigator 0.10.0-C6 | create-railways-navigator | 1.20.1 |
| Design-n-Decor-2.2b | create-design-n-decor | 1.20.1 |
| sliceanddice-4.3.4 | slice-and-dice | 1.20.1 |

## 4. 无任何 Fabric 构建（33 件，含 NeoForge 专属/工具/bundle）

`abnormals_delight`、`aerocopycats`、`aeronauticscompat`、`aeroworks`、`awakened_islands`、`blueprint`、`climbable_ropes`、`create-central-kitchen`、`create_aeronautics_throwable_rope_connector`、`create_aeronautics_toolgun`、`create_aeronautics_transmission_linkage`、`create_connected`、`create_mechanical_extruder`、`create_power_loader`、`create_submarine`、`createdieselgenerators`、`createliquidfuel`、`createpropulsion`、`mechanicals`、`minersdelight`、`MyNethersDelight`、`mysterious_mountain_lib`、`portable_engine_liquid_fuel`、`sophisticatedbackpacks`、`sophisticatedcore`、`sophisticatedstorage`、`tfmg`、`waystonessable`（28 条；其余 5 条为 `createdeco`（项目不存在）/ FTB 三件 + FTBQuestsOptimizer（Modrinth 无此项目））。

---

## 5. 给 Lead 的排批建议

- **只剩 3 个可做的 26.x 件**：`natures_spirit`（做 PASS 最有希望）、`CEI`、`DragonsPlus`。其余 44 件要么 intermediary/1.20、要么无 Fabric 构建 ⇒ **不要再排轮次试装**。
- 优先顺序：NS（独立、无 create API）→ CEI/DP（必须先改 fluid builder，跨轮）。
- 后续若用户坚持要 NeoForge-only 内容，只能走「decompile→改源码→javac 26.3」重写路线（`docs/SOLVED-FAMILIES.md` R380 方法论），成本远高于放宽版本试装。
