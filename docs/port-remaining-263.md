# port-remaining-263 —— 剩余缺口清单（原整合包 vs live）

> 生成：2026-10-20｜原包 mods（112 jar）id 扫描 vs work/run26/mods-stable（100 jar）fabric/toml id；逐 jar 统计 class 数量与 data/worldgen/create/fluid/BE 标记。
> 去重后未覆盖 33 个 jar（含 2 个容器）；多数已归类为「已出件 / live 已有 / bundle / 不建议」。

## Top-10（可快速 reduced，按轮次再按规模排序）

| # | jar | mod id | 规模 | 26.x Fabric? | reduced 可行 | 依赖 | 轮次 | 备注 |
|---|---|---|---|---|---|---|---|---|
| 1 | create-hangars-V1.0.0.jar | ? | 0 cls / 37 wg | 1.21 only | 是（纯数据，0 class） | 无 | 1 | 首选；37 worldgen + 64 data 结构包 |
| 2 | sable_createaddition_compat-0.1.13.jar | sable_createaddition_compat | 11 cls / 0 wg | 1.21 only | 是（11 class） | sable/create | 1 | 次选；薄兼容层 |
| 3 | portable_engine_liquid_fuel-2.0.0-neoforge-1.21.1.jar | portable_engine_liquid_fuel | 10 cls / 0 wg | 1.21 only | 是（10 class） | create/fluid/BE | 2 | 可做；便携引擎燃料 |
| 4 | createliquidfuel-3.0.0-1.21.1.jar | createliquidfuel | 13 cls / 0 wg | 1.21 only | 是（13 class） | create/fluid/BE | 2 | 可做；液体燃料 |
| 5 | climbable_ropes-2.1.4.jar | climbable_ropes | 34 cls / 0 wg | 1.21 only | 部分（34 class mixin） | 无 | 2 | 可做（风险中）；26.3 映射核 mixin |
| 6 | waystonessable-1.0.7.jar | waystonessable | 40 cls / 0 wg | 1.21 only | 是（40 class） | create/waystones | 2 | 可做；依赖均在 live |
| 7 | mysterious_mountain_lib-1.2.15-1.21.1.jar | mysterious_mountain_lib | 73 cls / 0 wg | 1.21 only | 部分（73 class 库） | create | 2 | 可做（低价值）；无独立内容 |
| 8 | player-animation-lib-forge-2.0.4+1.21.1.jar | playeranimator | 127 cls / 0 wg | 1.21 only | 部分（127 class） | 无 | 2-3 | 可做（mixin 库）；动画库 |
| 9 | dragonlib-3.0.29+mc1.21.1-neoforge.jar | dragonlib | 588 cls / 0 wg | 1.21 intermediary | 否 | 无 | - | 不可做；实测失败 |

## 全量未覆盖清单

| jar | mod id | loader | cls | data/worldgen | 状态 | 26.x Fabric | reduced | 依赖 | 轮次 |
|---|---|---|---|---|---|---|---|---|---|
| awakened_islands-1.0.0.jar | awakened_islands | neoforge | 2 | 0 | 已出件（staging） | 无(neoforge) | 是（2 class 源码移植） | sable | 0 |
| blueprint-1.21.1-8.2.0.jar | blueprint | neoforge | 493 | 3 | 不推荐 | 1.21 only | 否（493 class） | create | - |
| climbable_ropes-2.1.4.jar | climbable_ropes | neoforge | 34 | 0 | 可做（风险中） | 1.21 only | 部分（34 class mixin） | 无 | 2 |
| cloth-config-15.0.140-neoforge.jar | cloth_config | neoforge | 633 | 0 | live 已有 fabric 版 | 26.3 fabric | - | 无 | 0 |
| copycats-3.0.9+mc.1.21.1-neoforge.jar | copycats | neoforge | 393 | 0 | 不推荐 | 1.20 only | 否 | create/BE/fluid | - |
| corn_delight-1.2.10-1.21.1.jar | corn_delight | neoforge | 22 | 5 | live 已有（corndelight） | 26.3 | - | 无 | 0 |
| create-aeronautics-bundled-1.21.1-1.3.2.jar | aeronautics_bundled | neoforge | 0 | 0 | bundle 占位 | - | - | 无 | 0 |
| create-hangars-V1.0.0.jar | ? | neoforge | 0 | 37 | 首选 | 1.21 only | 是（纯数据，0 class） | 无 | 1 |
| create_connected-1.3.3-mc1.21.1.jar | create_connected | neoforge | 401 | 0 | 不推荐 | 1.21 only | 否 | create/BE/fluid | - |
| create_submarine-3.3.0.jar | create_abyss,create_high_seas,create_submarine | neoforge | 420 | 7 | 不推荐 | 1.21 only | 否 | create/BE/fluid/wg | - |
| createliquidfuel-3.0.0-1.21.1.jar | createliquidfuel | neoforge | 13 | 0 | 可做 | 1.21 only | 是（13 class） | create/fluid/BE | 2 |
| createpropulsion-1.1.5.jar | createpropulsion | neoforge | 344 | 11 | 不推荐 | 1.21 only | 否 | create/BE/fluid/wg | - |
| createrailwaysnavigator-neoforge-1.21.1-beta-0.10.0-C6.jar | createrailwaysnavigator | neoforge | 724 | 0 | 不推荐 | 1.21 only | 否（724 class GUI） | create/BE | - |
| dragonlib-3.0.29+mc1.21.1-neoforge.jar | dragonlib | neoforge | 588 | 0 | 不可做 | 1.21 intermediary | 否 | 无 | - |
| ftb-library-neoforge-2101.1.37.jar | ftblibrary | neoforge | 403 | 0 | 不建议（自研 quests 替代） | 1.21 only | 否 | 无 | - |
| ftb-quests-neoforge-2101.1.36.jar | ftbquests | neoforge | 476 | 0 | 不建议（自研 quests 替代） | 1.21 only | 否 | 无 | - |
| ftb-teams-neoforge-2101.1.11.jar | ftbteams | neoforge | 134 | 0 | 不建议（自研替代） | 1.21 only | 否 | 无 | - |
| FTBQuestsOptimizer-neoforge-3.2.0-1.21.1.jar | ftbqopt | neoforge | 10 | 0 | 不建议 | 1.21 only | 否 | 无 | - |
| gadgets-and-gizmos-bundled-2.0-pre-release-2.jar | createthrusters_bundled | neoforge | 0 | 0 | bundle 占位 | - | - | create | 0 |
| kotlinforforge-5.12.0-all.jar | ? | ? | 0 | 0 | 跳过 | neoforge | 否 | 无 | - |
| lodestone-1.21.1-1.8.2.jar | lodestone | neoforge | 419 | 0 | 不推荐 | 1.21 only | 否（419 class） | create | - |
| modernfix-neoforge-5.27.26+mc1.21.1.jar | modernfix | neoforge | 314 | 0 | 不建议 | 快照 only | 否 | 无 | - |
| MoogsSoaringStructures-universal-1.21-2.2.0.jar | mss | fabric | 0 | 217 | live 已有 26.3 版 | 26.3 | - | 无 | 0 |
| mysterious_mountain_lib-1.2.15-1.21.1.jar | mysterious_mountain_lib | neoforge | 73 | 0 | 可做（低价值） | 1.21 only | 部分（73 class 库） | create | 2 |
| no-void-structures-2.0.1.jar | mr_no_voidstructures | fabric | 0 | 23 | 已出件（staging） | fabric 数据包 | 是（纯数据） | lithostitched | 0 |
| player-animation-lib-forge-2.0.4+1.21.1.jar | playeranimator | neoforge | 127 | 0 | 可做（mixin 库） | 1.21 only | 部分（127 class） | 无 | 2-3 |
| portable_engine_liquid_fuel-2.0.0-neoforge-1.21.1.jar | portable_engine_liquid_fuel | neoforge | 10 | 0 | 可做 | 1.21 only | 是（10 class） | create/fluid/BE | 2 |
| sable_createaddition_compat-0.1.13.jar | sable_createaddition_compat | neoforge | 11 | 0 | 次选 | 1.21 only | 是（11 class） | sable/create | 1 |
| sophisticatedbackpacks-1.21.1-3.26.12.2208.jar | sophisticatedbackpacks | neoforge | 379 | 0 | 不推荐 | 1.21 only | 否 | sophisticatedcore | - |
| sophisticatedcore-1.21.1-1.5.13.2404.jar | sophisticatedcore | neoforge | 843 | 0 | 不推荐 | 1.21 only | 否（843 class GUI） | fluid/BE | - |
| sophisticatedstorage-1.21.1-1.6.7.2184.jar | sophisticatedstorage | neoforge | 403 | 0 | 不推荐 | 1.21 only | 否 | sophisticatedcore | - |
| tfmg-1.2.0.jar | tfmg | neoforge | 671 | 17 | 不推荐 | 1.21 only | 否（671 class + 1828 data） | create/fluid/BE | - |
| waystonessable-1.0.7.jar | waystonessable | neoforge | 40 | 0 | 可做 | 1.21 only | 是（40 class） | create/waystones | 2 |

## 说明与并行派活
- 已出件待验：awakened_islands（g86/stage/mods-awakened-final）、No Void b3（g86/stage/mods-novoid-b3-final）；
- live 已有/别名（diff 判定差异，无需再动）：MoogsSoaringStructures、cloth-config、corn_delight、create-aeronautics-bundled、gadgets-and-gizmos-bundled；
- FTB 系不再移植（自研 sky262-quests 已覆盖）；dragonlib 已失败；modernfix/kotlinforforge 跳过；
- create 重依赖件只列不做：copycats / create_connected / create_submarine / createpropulsion / railwaysnavigator / tfmg / sophisticated*；
- 派活建议：ponder = create-hangars（1 轮，数据包 schema 转换）+ sable_createaddition_compat（1 轮）；crashfix = portable_engine_liquid_fuel / createliquidfuel（2 轮）；aero = climbable_ropes + waystonessable（各 2 轮）；每件出 -final staging，probe 硬门槛=标题+世界+0 registry，细节押后。
