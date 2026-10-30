# 游戏内视觉取证（2026-10-22，子代理 visual-probe）

## 已验证事实

- **26.3 的 `BackupConfirmScreen` 继承 `Screen` 而不是 `ConfirmScreen`**（`work/refs/mc26.3/net/minecraft/client/gui/screens/BackupConfirmScreen.java:13`），
  而 mcpfabric 的 `UiHandlers.requireAllowed()` 白名单只放行 `ConfirmScreen`/`AlertScreen`/Pause/Title/Options/Advancements/Stats/AbstractContainerScreen
  => `ui.widgets`/`ui.click` 对它一律 `ui_refused`。实验性存档弹窗**无法用 ui.* 点掉**，只能外部键鼠注入或换存档。
- 存档 `sky islands` 的 `level.dat` **没有** `enabledFeatures`、没有 `removed_features`（dataVersion 5023, WasModded=1）。
  实验性判定来自 `WorldOpenFlows.java:541` `unstable = worldGenSettingsLifecycle() != Lifecycle.stable()`，
  其值来自 `LevelStorageSource.java:170` `dimensions.lifecycle().add(registryAccess.allRegistriesLifecycle())`
  => 是 **mod 自带 datapack 世界生成数据**被判实验性，改 level.dat 无效。quickPlay 进该存档必卡在弹窗；验证要用干净存档（如 `vis1`）。
- 本整合包的创造栏是 **EMI 风格自定义界面**（左 9x5 物品格 + 右侧 1/137 物品浏览面板 + 顶部 7 个 tab + `2/5` 翻页），
  不是原版 195x136 `CreativeModeInventoryScreen`；但槽位仍用原版 slot.png（#373737/#FFFFFF/#8B8B8B, 18px pitch）。
  Lead 扫 35 个 tab / 1121 格：missing 0。**物品图标不是问题所在**。
- 世界内玩家 hotbar 每格上的紫色小图形是**资源包的槽位装饰**，不是破损物品（别误判）。
  EMI 创造界面 hotbar 行确实出现过 1 个品红黑棋盘 item（missing texture），已在 `shots/page2-0-0.png`。
- 日志已有 render 级证据：`IllegalArgumentException: Cannot compute translucency out of bounds: [17,23,19,25] in 16x16 image`
  （`SpriteContents.computeTransparency`/`FaceBakery.computeMaterialTransparency`）= UV 越界导致模型烘焙失败；
  以及大量 `Missing texture references in model interiors:block/...: #missing` / `createdeco:...: particle`。

## 死路（不要重试）

- 用 mcpfabric `ui.click` 关实验性存档确认框：见上，类不在白名单，永久 `ui_refused`（不是配置问题）。
- 用 Windows MCP（mcp__windows__Click）注入到游戏窗口：桌面控制受 **用户空闲** 门控（`ControlStatus.state=user` 时返回 `USER_CONTROL`），
  用户正在聊天时不可用；且点击前需 `WScript.Shell.AppActivate('Minecraft')` 把窗口置前，否则点击只起聚焦作用。
- `players.teleport` 等 server 方法在本实例不可靠（`info` 里 `serverPresent:false`），用 `command.run "tp @a ..."`。

## 方块渲染审计脚手架（可复用）

- 脚本：`scratch/vis/block_audit.py`（bridge 直连 + Pillow 判定，自带标定与 CSV/MD 报告）。
- 世界几何：平台 `y=100` smooth_stone（x -7..9, z -3..9），方块放 `y=101`（顶面 y=102）；
  相机 **旁观模式**（无重力，坐标稳定）`tp @a 0.5 112.38 2.5 0 90`（眼高 114）。
- 标定：把平台铺 4 块彩色混凝土（红/蓝/绿/黄），由饱和度投影定位平台矩形、按色相归位四角，
  再解 4 点单应 `world(x,z)->screen`；实测 `cell_px≈37.7`（x/z 一致才算成功），残差 0。
- 判定：顶面按单应投影成四边形取内缩 20% 采样，品红 `r,b>=170 & g<=100` 占比 >=5% => MISSING；
  另用 `world.getBlock` 权威核查是否真的放下（NOT_PLACED 不算破损）。
- 速度：45 个/批 ≈ 1.4s（含 45 次 getBlock）。
