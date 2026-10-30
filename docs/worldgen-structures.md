# 结构枚举表（26.3 原版 + mods-stable 45 个 jar）

生成器：`tools/wg_struct_table.py`（扫 `data/*/worldgen/structure/*.json`，跳过 `tags/`）。
共 **155** 个 structure 定义。

**关键语义（反编译 `JigsawPlacement#addPieces` 得出）**：
有 `project_start_to_heightmap` 时，结构起点 `y = start_height + 该列高度图值`
⇒ `start_height` 是**相对地表的偏移**，不是绝对高度。没有投影时它才是绝对 y。

| namespace | 结构 id | type | start_height | 投影 | 地形适配 |
|---|---|---|---|---|---|
| explorify | `badlands_pyramid` | jigsaw | `{"type":"uniform","min_inclusive":{"absolute":-12},"max_inclu...` | WORLD_SURFACE_WG | none |
| explorify | `black_spiral` | jigsaw | `{"absolute":32}` | - | none |
| explorify | `campsite` | jigsaw | `{"absolute":0}` | WORLD_SURFACE | beard_thin |
| explorify | `dark_forest_settlement` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| explorify | `desert_shrine` | jigsaw | `{"type":"uniform","min_inclusive":{"absolute":-10},"max_inclu...` | WORLD_SURFACE_WG | none |
| explorify | `end_shipwreck` | jigsaw | `{"type":"uniform","min_inclusive":{"absolute":-7},"max_inclus...` | WORLD_SURFACE_WG | none |
| explorify | `farmstead` | jigsaw | `{"absolute":0}` | MOTION_BLOCKING_NO_LEAVES | beard_thin |
| explorify | `guide_post_cold` | jigsaw | `{"absolute":-11}` | WORLD_SURFACE_WG | none |
| explorify | `guide_post_warm` | jigsaw | `{"absolute":-11}` | WORLD_SURFACE_WG | none |
| explorify | `mangrove_hut` | jigsaw | `{"type":"uniform","min_inclusive":{"absolute":-21},"max_inclu...` | WORLD_SURFACE_WG | none |
| explorify | `mausoleum` | jigsaw | `{"absolute":0}` | WORLD_SURFACE | beard_thin |
| explorify | `ruins` | jigsaw | `{"absolute":0}` | OCEAN_FLOOR_WG | beard_thin |
| explorify | `supply_cache/birch` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| explorify | `supply_cache/dark` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| explorify | `supply_cache/desert` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| explorify | `supply_cache/forest` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| explorify | `supply_cache/jungle` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| explorify | `supply_cache/mangrove` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| explorify | `supply_cache/taiga` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| explorify | `tavern` | jigsaw | `{"absolute":0}` | WORLD_SURFACE | beard_thin |
| explorify | `watchtower/plains` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| explorify | `watchtower/savanna` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| explorify | `watchtower/taiga` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| medieval_buildings | `fort` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| medieval_buildings | `house_1` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| medieval_buildings | `house_2` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| medieval_buildings | `ship` | jigsaw | `{"absolute":-6}` | WORLD_SURFACE_WG | none |
| medieval_buildings | `tower` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `abandoned_camp_bamboo_jungle` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `abandoned_camp_birch_forest` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `abandoned_camp_cherry_grove` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `abandoned_camp_dappled_forest` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `abandoned_camp_flower_forest` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `abandoned_camp_forest` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `abandoned_camp_meadow` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `abandoned_camp_old_growth_birch_forest` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `abandoned_camp_old_growth_pine_taiga` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `abandoned_camp_old_growth_spruce_taiga` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `abandoned_camp_pale_garden` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `abandoned_camp_savanna` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `abandoned_camp_snowy_taiga` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `abandoned_camp_sparse_jungle` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `abandoned_camp_swamp` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `abandoned_camp_taiga` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `abandoned_camp_windswept_forest` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `abandoned_camp_wooded_badlands` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `ancient_city` | jigsaw | `{"absolute":-27}` | - | beard_box |
| minecraft | `bastion_remnant` | jigsaw | `{"absolute":33}` | - | - |
| minecraft | `buried_treasure` | buried_treasure | `null` | - | - |
| minecraft | `desert_pyramid` | desert_pyramid | `null` | - | - |
| minecraft | `end_city` | end_city | `null` | - | - |
| minecraft | `fortress` | fortress | `null` | - | - |
| minecraft | `igloo` | igloo | `null` | - | - |
| minecraft | `jungle_pyramid` | jungle_temple | `null` | - | - |
| minecraft | `mansion` | woodland_mansion | `null` | - | - |
| minecraft | `mineshaft` | mineshaft | `null` | - | - |
| minecraft | `mineshaft_mesa` | mineshaft | `null` | - | - |
| minecraft | `monument` | ocean_monument | `null` | - | - |
| minecraft | `nether_fossil` | nether_fossil | `null` | - | beard_thin |
| minecraft | `ocean_ruin_cold` | ocean_ruin | `null` | - | - |
| minecraft | `ocean_ruin_warm` | ocean_ruin | `null` | - | - |
| minecraft | `pillager_outpost` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `ruined_portal` | ruined_portal | `null` | - | - |
| minecraft | `ruined_portal_desert` | ruined_portal | `null` | - | - |
| minecraft | `ruined_portal_jungle` | ruined_portal | `null` | - | - |
| minecraft | `ruined_portal_mountain` | ruined_portal | `null` | - | - |
| minecraft | `ruined_portal_nether` | ruined_portal | `null` | - | - |
| minecraft | `ruined_portal_ocean` | ruined_portal | `null` | - | - |
| minecraft | `ruined_portal_swamp` | ruined_portal | `null` | - | - |
| minecraft | `shipwreck` | shipwreck | `null` | - | - |
| minecraft | `shipwreck_beached` | shipwreck | `null` | - | - |
| minecraft | `stronghold` | stronghold | `null` | - | bury |
| minecraft | `swamp_hut` | swamp_hut | `null` | - | - |
| minecraft | `trail_ruins` | jigsaw | `{"absolute":-15}` | WORLD_SURFACE_WG | bury |
| minecraft | `trial_chambers` | jigsaw | `{"type":"minecraft:uniform","max_inclusive":{"absolute":-20},...` | - | encapsulate |
| minecraft | `village_desert` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `village_plains` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `village_savanna` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `village_snowy` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| minecraft | `village_taiga` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| structory | `abandoned_camp` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| structory | `abandoned_chapel` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| structory | `boat` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | - |
| structory | `dense_forest_ruin` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| structory | `firetower` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| structory | `graveyard` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| structory | `jungle_ruin` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| structory | `northern_ruin` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| structory | `old_manor` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_box |
| structory | `outcast_villager_desert` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| structory | `outcast_villager_grassy` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| structory | `ruin_grassy` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| structory | `swamp_ruin` | jigsaw | `{"absolute":-10}` | WORLD_SURFACE_WG | beard_thin |
| structory | `taiga_ruin_surface` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| structory | `taiga_ruin_underground` | jigsaw | `{"absolute":-10}` | WORLD_SURFACE_WG | bury |
| towns_and_towers | `exclusives/pillager_outpost_classic` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `exclusives/pillager_outpost_iberian` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `exclusives/pillager_outpost_mediterranean` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `exclusives/pillager_outpost_nilotic` | jigsaw | `{"absolute":-6}` | WORLD_SURFACE_WG | - |
| towns_and_towers | `exclusives/pillager_outpost_oriental` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `exclusives/pillager_outpost_rustic` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `exclusives/pillager_outpost_swedish` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `exclusives/pillager_outpost_tudor` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `exclusives/village_classic` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `exclusives/village_iberian` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `exclusives/village_mediterranean` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `exclusives/village_nilotic` | jigsaw | `{"absolute":-1}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `exclusives/village_piglin` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `exclusives/village_rustic` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `exclusives/village_swedish` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `exclusives/village_tudor` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `exclusives/village_wandering_trader_camp` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `mimic_desert` | jigsaw | `{"absolute":35}` | - | none |
| towns_and_towers | `pillager_outpost_badlands` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `pillager_outpost_beach` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `pillager_outpost_birch_forest` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `pillager_outpost_desert` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `pillager_outpost_flower_forest` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `pillager_outpost_forest` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `pillager_outpost_grove` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `pillager_outpost_jungle` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `pillager_outpost_meadow` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `pillager_outpost_mushroom_fields` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `pillager_outpost_ocean` | jigsaw | `{"absolute":58}` | - | - |
| towns_and_towers | `pillager_outpost_old_growth_taiga` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `pillager_outpost_savanna` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `pillager_outpost_savanna_plateau` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `pillager_outpost_snowy_beach` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `pillager_outpost_snowy_plains` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `pillager_outpost_snowy_slopes` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `pillager_outpost_snowy_taiga` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `pillager_outpost_sparse_jungle` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `pillager_outpost_sunflower_plains` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `pillager_outpost_swamp` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `pillager_outpost_taiga` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `pillager_outpost_wooded_badlands` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `village_badlands` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `village_beach` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `village_birch_forest` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `village_flower_forest` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `village_forest` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `village_grove` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `village_jungle` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `village_meadow` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `village_mushroom_fields` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `village_ocean` | jigsaw | `{"absolute":59}` | - | - |
| towns_and_towers | `village_old_growth_taiga` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `village_savanna_plateau` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `village_snowy_slopes` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `village_snowy_taiga` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `village_sparse_jungle` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `village_sunflower_plains` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `village_swamp` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `village_wooded_badlands` | jigsaw | `{"absolute":0}` | WORLD_SURFACE_WG | beard_thin |
| towns_and_towers | `wreckage_ocean` | jigsaw | `{"absolute":62}` | - | - |

## 本 mod 覆盖的两个（任务 C：船不浮空）

| 结构 | 原来 | 现在 | 理由 |
|---|---|---|---|
| `medieval_buildings:ship` | `{"absolute":-6}` + `WORLD_SURFACE_WG` | `{"absolute":62}`，**删投影** | 原式会落到该列最高点（有岛 ⇒ y≈200）⇒ 浮空 |
| `structory:boat` | `{"absolute":0}` + `WORLD_SURFACE_WG` | `{"absolute":62}`，**删投影** | 同上；62 = 水面(63)下一格 |

