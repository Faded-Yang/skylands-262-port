# create_power_loader 2.0.5 移植评估 + reduced v1

原包：`%APPDATA%\.minecraft\versions\Create 航空学 × 浮空群岛\mods\create_power_loader-2.0.5-mc1.21.1.jar`（442,369 B）
反编译：`work/refs/power-loader`（**52 java**；jar 189 entries：4 blockstates / 28 models / 13 textures / 11 lang / 11 ponder / loot 6 / recipe 3 / tags 3+5）

## 0. 内容
- 4 个方块（`empty_andesite/empty_brass/andesite/brass_chunk_loader`）+ 4 BE + 3 renderer；
- 核心行为：机械动力的区块加载器，kinetic 驱动时强制加载周围区块；
- 另有：commands、ponder、trains 集成（station/train chunk loader）、4 个 mixin、NeoForge 配置。

## 1. 依赖与阻塞点
- 必需 create 6.0.0+（我们的 fork OK）；**NeoForge 专属**：`ChunkLoadManager` 用 `RegisterTicketControllersEvent` / `TicketController` / `TicketHelper` / `LevelTickEvent.Pre`。
- **替代方案（已确认可行）**：26.3 原版 `ServerLevel#setChunkForced(int,int,boolean)` 存在 ⇒ 用强制区块重写管理器（语义简化，非引用计数）。
- FD/其它 mod 无依赖；`SableCompat` 引用 sable（可选，v1 不做）。

## 2. reduced v1（已实现）
- 手写注册（Fabric）：4 blocks + 4 BlockItems + 4 BlockEntityType；`BlockItem` 用 `useBlockDescriptionPrefix()` 复用 `block.*` lang 键；
- 4 个 BlockEntity：`Empty`（kinetic 占位）、`Andesite`（range 1）、`Brass`（range 2，原版是 scroll value 配置，v1 固定 2）；
- 强制加载：每 20 tick 检查 `isOverStressed() || |getSpeed()|<=1e-3`，active 时 `setChunkForced` 自己周围 (2r+1)^2，停转/移除时释放；
- 资源：原包 assets/data 全搬 + 生成 26.3 `assets/create_power_loader/items/*.json`（指向已有 `item/*` 模型）；
- 不做（TODO）：3 个 BER renderer（核心盘/传动动画）、ponder 插件、commands、trains/station 集成、4 个 mixin、NeoForge 配置（range 固定）、Empty loader 的“装上 station”物品行为。

## 3. 候选
- `g79/out/sky262-power-loader-2.0.5-beta-port.1.jar`：72,099 B / `fe576214…`，80 entries（12 classes），staging `g79/stage/mods-power-loader-r1`；`-Xverify:all` 6 类 PASS。

## 4. 降级说明
- 强制区块非引用计数 ⇒ 若别的系统也 force 同一区块，停转时会被解除（TODO：改用 26.3 Ticket API / 引用计数）；
- 无 BER ⇒ 方块只有静态模型，核心盘旋转/激活发光缺失（外观降级）；
- brass 的 range 不可调（固定 2）；Empty loader 不能由物品转成 station loader。
