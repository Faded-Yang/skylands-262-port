# portable_engine_liquid_fuel / createliquidfuel —— 现实核查与兼容壳（reduced v0）

> 日期：2026-10-20 凌晨 ｜ 角色：crashfix-26

## 1. 核心发现（重要）

这两个 mod **不是方块/物品内容包，而是纯行为 addon**：

| mod | 条目 | 内容 |
|---|---|---|
| `portable_engine_liquid_fuel` 2.0.0 | 41 | 10 classes（`EngineFuelData`/`DatapackRegister`/`RegisterDataMaps` + 2 mixin 进 simulated 的 PortableEngine LavaTank/Inventory）+ `data_maps/fluid/engine_fuel.json`（`#minecraft:lava` burn_time 20000）/`super_engine_fuel.json`；**无 blockstates/models/model items** |
| `createliquidfuel` 3.0.0 | 30 | 13 classes（`LiquidFuels`/`LiquidBurnerFuelJsonLoader`/`BurnerStomachHandler` + 2 mixin 进 Create BlazeBurner）+ `data_maps/fluid/liquid_fuel.json`（lava/createaddition 油等）；**无 assets/** |

⇒ 「assets + 手写方块/物品注册」路线**没有内容可注册**；硬门槛「方块/物品可放置可获取」对这两件不适用。

## 2. 已完成的 v0（兼容壳）

- `sky262-portable_engine_liquid_fuel-2.0.0-26.3-shell.jar`：1,342 B，SHA256 `544a08177e3988c9ed45de980a4722d71837f0f8b4d41016c65baa41c5ef3561`；
- `sky262-createliquidfuel-3.0.0-26.3-shell.jar`：1,165 B，SHA256 `f2a44bd0d13f7f0f1aaddbfe62c158aa5b844b76760a0dfeef1b4e7252c77869`；
- 内容：正确 fabric.mod.json（id/版本/名称/描述/依赖），mod 列表可识别，**无行为**；
- staging：`g70/stage/fuel-final`（base live **100** + 2 = **102 jar**）；
- 自测：**TITLE_SCREEN_OK**；**WORLD_OK joined=true 42.4s**；0 crash。

## 3. 行为移植（待决策）

- portable_engine：需要 mixin 26.3 simulated 的 PortableEngine 熔岩罐（burn_time 数据），或 Fabric 侧替换 data map；
- createliquidfuel：需要 mixin 26.3 create-fly 的 BlazeBurnerTileEntity + 流体接入（Create 的 FluidHandler/管道 API），并把 `liquid_fuel.json` 表硬编码；
- 两项均为 mixin/行为层，不是 assets 注册；每项估计 **2+ 轮**（含 API 差异调试），且 probe 无法用 give/setblock 直接验证，需要功能测试（管道注入/燃烧）。

## 4. 给 probe 的 v0 验收（仅加载）

~~~powershell
node tools\mcp_fabric_client.mjs player.getState
node tools\mcp_fabric_client.mjs screenshot.take --out fuel-shots
~~~
断言：世界可进、0 crash、mod 列表含 `portable_engine_liquid_fuel` 与 `createliquidfuel`（无方块/物品可给）。

## 5. 建议
- 先按 v0 兼容壳收口（补齐 mod 列表/依赖关系），行为移植单列 TODO；
- 若要行为，需接受 probe 以「管道注入 lava 后引擎/燃烧室行为」做功能验证，不是 give/setblock。
## 6. probe 复验（PASS，仅加载判据）

- 前两次启动 JVM 在 GL/注册阶段异常退出（无 crash report，`FAIL_NO_JOIN`，环境 flaky）；第三次正常；
- `Loading 183 mods` → `N_STAY` / WS ready；`Registry loading errors`=0；0 crash；
- mod 列表确认：`createliquidfuel 3.0.0-26.3-shell`、`portable_engine_liquid_fuel 2.0.0-26.3-shell`；
- 截图：`g33/mcp-shots/fuel_shells.png` / `mcp-1792438875114.png`；
- 判读：加载 PASS，可 promote（102）；功能（燃料兼容行为）待补，不做判定。