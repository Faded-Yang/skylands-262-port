# Transmission & Linkage 最小移植（aeronautics_utility_objects）

| 项 | 值 |
|---|---|
| 来源 | 原包 `create_aeronautics_transmission_linkage-0.2.8.jar`（734,744 B，131 class，99 java 反编译到 `g70/src/transmission`） |
| 候选 | `g70/out/sky262-transmission-linkage-0.2.8.jar` |
| size | **70,317 B** |
| SHA-256 | `70e787ef16c4ac967b5bbbd5a72f56796360be57c6fc3893cc14a5e438480b37` |
| base | 75 jar（aero `455B5824`、create `17FD0C33`；构建脚本断言 aero） |
| 内容 | 8 方块（universal_joint/brass_universal_joint/damping_stress_bearing/hydraulic_connection_head/hydraulic_hinge_head/brass_hydraulic_hinge_head/hydraulic_hinge_link/hydraulic_regulator）+ 12 物品（7 方块物品 + 5 杆件）+ 自建创造栏；原 models/textures/lang 全部带入 |
| TODO | 关节/液压联动/动力学/菜单/渲染行为全部未移植（先广度） |
| 验证 | PASS（`g70/out/_static_verify_trans.txt`，-Xverify:all SMOKE_OK） |
| staging | `g70/stage_trans/mods-baseline`(75) / `mods-candidate`(76) |

## toolgun 行为层评估

- `MagneticGunItem`/`StructureToolItem` 本身只有 `use/useOn` 空壳（consume / 反射调 `ClientStructureToolHandler`）；
- 真正行为在 `ClientToolState`、`ClientHooks`、`network/*Payload`、`client/render/*`、`blueprint/*`（316 class）⇒ 需要独立批次（网络 + 客户端 UI/渲染 + 蓝图子系统），不适合作为单步行为层；
- 当前 toolgun 广度件物品是普通 Item（无 consume），仅注册/创造栏可见，行为待专门批次。
