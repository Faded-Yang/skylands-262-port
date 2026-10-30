# aeronauticscompat 最小移植（data-only）

| 项 | 值 |
|---|---|
| 来源 | `aeronauticscompat-1.1.3.jar`（43,764 B）：10 个其他 mod 的 mixin（bitsnbobs/citadel/cobblemon/etched/pneumaticcraft/sable/simulated/storagedrawers/thickair/waterframes）+ SableBridge/SubLevelRayTrace 等 + 2 个 data tag |
| 候选 | `g70/out/sky262-aeronauticscompat-1.1.3.jar` |
| size | **2,366 B** |
| SHA-256 | `14cf9829c5babe02ea0571222f3b5d8fc832b975fab4acc26258204f5a10ab66` |
| base | 75 jar（aero `455B5824`、create `17FD0C33`；构建脚本断言 aero） |
| 内容 | `data/create/tags/block/seats.json`、`data/sable/tags/entity_type/retain_in_sub_level.json`、lang；`fabric.mod.json` id=`aeronauticscompat`、无 entrypoint/mixin |
| TODO | Java 兼容层：`SableBridge`/`SubLevelRayTrace`/`SableAssemblyFlag`/`DeferredSoundQueue`，以及 10 个目标 mod 的 mixin。这些目标 mod 当前**都未装**，装了才需要逐个移植 |
| 验证 | `g70/out/_static_verify_ac`（本次未写文件，控制台 PASS） |
| staging | `g70/stage_ac/mods-baseline`(75) / `mods-candidate`(76) |
