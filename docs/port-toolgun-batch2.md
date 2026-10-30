# toolgun 批次 2：蓝图捕获/放置最小链路

| 项 | 值 |
|---|---|
| 候选 | `g70/out/sky262-toolgun-1.0.0.jar`（替换 live 同名 jar） |
| size | **125,358 B** |
| SHA-256 | `398fe7c9177d02462b006ad09cc9f9cbcf36c2ccd0c581e0be9f804399be6826` |
| base | 77 jar（aero `455B5824`、sable `2DFC53A6`、create `17FD0C33`；构建断言 aero） |
| staging | `g70/stage_toolgun3/mods-baseline`(77) / `mods-candidate`(77，替换同名) |
| 验证 | PASS（jar/资源/`-Xverify:all` SMOKE_OK） |

## 行为（最小链路，非原版完整蓝图）

- `action=1`（structure_tool 右键方块）：捕获以点击方块为中心的 **5×5×5** 非空气方块，写入 `game-dir/sky262_toolgun_captures/<uuid>-<millis>.json`；
- `action=2`（structure_tool 右键空气）：把最近一次捕获按相对坐标放到玩家视线命中面旁（可替换位置才放）；
- 日志：`[sky262toolgun] capture player=... center=... blocks=N file=...` / `[sky262toolgun] place player=... target=... blocks=N file=...`；
- 不做原版的连通 sublevel 捕获、蓝图编码/压缩、预览/回滚、菜单；批次 3 再补渲染/BE。
