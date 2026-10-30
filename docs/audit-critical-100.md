# audit-critical-100 —— 飞岛地图单 chunk / Create 内容失效 静态审计

> 只读静态审计，未改 live。DOCS FIRST 参考：docs/worldgen-design.md、docs/worldgen-structures.md、docs/API-263-data-schema.md §7/§8、docs/KNOWN-LIMITATIONS.md、docs/audit-data-refs.md。

## A. 飞岛地图只加载一个 chunk

### A1（高，但有反证）服务器实际已生成多区块
- 证据：watch/saves/sky islands/dimensions/minecraft/overworld/region/ 有 16 个 .mca、52,297,728 B（不是单 chunk）。
- 结论：优先查客户端地图/Xaero 缓存/视距/刷新，而不是先改 worldgen。
- 验证：同存档 F3 飞离出生点 200–500 格；Xaero 清缓存/重新扫描；/forceload add 0 0 512 512 后看 region 是否新增；对比 sky_test3（region 0）。

### A2（高嫌疑）zsky262_preset 可能没有被选中
- level.dat 的 simulated:world_preset = "minecraft:normal"，不是 skylands:sky_islands。
- zsky262_preset 只把 skylands:sky_islands 加进 data/minecraft/tags/worldgen/world_preset/normal.json（普通预设可选列表），没有把当前世界切到该预设。
- 该存档实际浮空地形来自 saves/sky islands/datapacks/aerolith-1.3.2-26.3.zip：它覆盖 minecraft:overworld 的 noise_settings、dimension_type、部分 ore placed_feature/carver。
- 验证：新建世界选「浮岛世界」后立刻读 level.dat 的 simulated:world_preset；若不是 skylands:sky_islands，预设选择/持久化链有问题；临时移除 aerolith 再建同预设对比。
- 建议：先修预设选择/持久化（显式写入 skylands:sky_islands），不要只依赖 normal tag。

### A3（中）外部 aerolith 数据包覆盖 overworld 生成器
- aerolith 的 noise_settings/overworld.json 键与 26.3 原版基本一致，但额外有 carvers 字段、sea_level=64（原版 63）；dimension_type/overworld.json 也覆盖。
- 风险：该包是实际生成器；若版本/字段不兼容或包未加载，区块可能只出出生点/虚空，表现类似只加载一个 chunk。
- 验证：base live + 只保留 aerolith 新建世界，/forceload add 0 0 256 256；再移除 aerolith 对比。
- 建议：把 aerolith 纳入版本锁定/自检（pack_format、noise_settings 键校验），或把生成器复制进 preset，避免双来源。

### A4（中）awakened islands 在 CHUNK_GENERATE 阶段 placeInWorld
- sky262-awakened-islands 注册 ServerChunkEvents.CHUNK_GENERATE，按 1/4096 概率在 y=200 调 StructureTemplate.placeInWorld；lambda 有 catch-all。
- 风险：在 chunk 生成事件中写结构会触碰邻居 chunk（模板 16x17x17），可能部分放置/日志刷屏；现有日志多次出现 StructureTemplate Serialization errors。catch-all 会吞异常，通常不会让整块区停住，但会制造只有出生岛/部分方块现象。
- 验证：关 awakened islands 重建同种子对比 region；/sky262_islands spawn 看 loaded template... placed ok=...；检查 island1.nbt 的 block entities/entities。
- 建议：移到 CHUNK_LOAD/玩家进入后的延迟任务，或改用 structure_set/worldgen structure。

### A5（低）Paxi 没有加载全局包
- watch/config/paxi/ 只有 load order 两个 ~21B json，没有 paxi/datapacks；aerolith 是存档内 datapack（level.dat DataPacks 的 file/aerolith...zip），不是 Paxi 全局包。
- 结论：这次 Paxi 包未加载不是主因；若用户用外部 Paxi 包需另查 config/paxi/datapacks。

### A6（低）空 stub feature 没有静态证据
- 扫描 live 114 的 placed_feature/feature：没有 placed_feature 缺失 feature；config:{} 多为合法 no_op/矿石/树类；zsky262_preset 本身无 feature。
- 目前不支持空 feature 导致 chunk 中止的假设；若要排除，仅需筛 config 空且 type 非 no_op 的清单。

## B. Create 内容在后续 mod 加入后几乎不能用

### B1（高）crashfix 对所有 SmartBlockEntity 提前 initialize
- 1.0.5 SmartBlockEntityClientInitMixin 在 BlockEntity.setLevel TAIL（client）调用 SmartBlockEntity.initialize()；只加了 ClientLevel + ThreadLocal 守卫，真实 ClientLevel 里仍对所有 Create BE 提前初始化。
- 风险：Create 客户端行为（audio/tooltip/animation/filtering/scroll）原本等首 tick（且可能先 readClient）才注册；提前 initialize 会在 NBT 读入前创建/重复创建，叠加 CEI/DP/aeronautics 的注入后出现顺序/覆盖，表现机器存在但功能错乱。
- 验证：改用只针对 mixer/whistle/cuckoo 的窄初始化（或只保留 renderer guard）做 A/B；在 beginClientInit 打 BE 类名日志确认范围；对 mixer 之外机器移除 mixin 看是否恢复。
- 建议：只对确实需要首帧行为的 BE 提前 initialize，或延迟到首 tick 前但先 readClient；不要对所有 SmartBlockEntity。

### B2（高）多个 mod 同时注入同一批 Create 类
- 静态扫描 live 114 的 mixin target：
  - aeronautics：WaterWheelBlockEntity、FlywheelBlockEntity、SmartBlockEntity、Contraption、PonderScene 等；
  - CEI：SmartBlockEntity、ConnectivityHandler、CrushingWheelControllerBlockEntity、FillingBySpout、OpenEndedPipe 等；
  - DP：BasinOperatingBlockEntity（含 MechanicalMixer）、BlockEntityBehaviour、MixingRecipe、FluidStack 等；
  - createframed / constraintfix / interiors 也各有 Create 目标（门/绳/座位）。
- 风险：这些 Inject/Redirect 叠加我们的提前初始化，容易行为注册顺序/重复冲突；与用户「后续 mod 加入后几乎不能用」吻合。
- 验证：base+Create 逐个加 CEI/DP/aeronautics/createframed 的 staging 二分；对 mixer/press 用 /data get block 看 Running/Speed/behaviours。
- 建议：先测无附属 Create 基线，再逐个加回；确认 B1 是否放大。

### B3（中）sky262-create-recipes 1607 条静态配方覆盖 runtime
- 件带 1607 recipe（26.2 source），Create 26.3 自身有 RuntimeDataGenerator；静态包与动态生成可能同 ID 覆盖/顺序冲突，旧 schema 虽能解析但语义未必与 26.3 一致。
- 风险：部分机器匹配到旧配方（材质/数量/处理时间不对），表现机器能用但产出/配方不对。
- 验证：日志 Duplicate recipe/Failed parse（当前未见不代表无覆盖）；临时移除/只保留 pressing/milling/cutting 核心配方做 A/B；对比 RecipeManager 数量。
- 建议：静态配方只保留 runtime 不生成/缺失的类型，或按 ID 黑名单跳过 runtime 已生成配方。

### B4（中低）createfix 跳过 modded namespace 运行时 cutting 配方
- sky262-createfix 对 RuntimeDataGenerator 跳过 modded namespace（日志 [sky262-createfix] skipped runtime cutting recipe...）。
- 影响只限 modded 木材切割，不是 Create 整机不可用；但会改变 Create 运行时配方集合，可能与 B3 叠加。
- 验证：只装 create+createfix+一个 modded 木材 mod，检查 saw 对 modded planks 的配方。

### B5（低）sky262-mechanicals 共享库
- 91 entries、无 mixin；提供 AbstractMechanicalRecipe/BehaviourType/BlockPredicateUtils 等共享类。
- 不太可能直接破坏 Create 核心；若其 RecipeRequirementType/BlockEntityBehaviour 初始化早于 Create 注册，可能影响依赖它的机器。
- 验证：移除 mechanicals 看 Create 基线是否恢复（extruder 会失效，可区分）。

### B6（低）Create tags / 数据引用
- docs/audit-data-refs.md 对 live 114 审计：Create 数据引用 item/block/tag 缺失 0；create-recipes 的 4849 refs 全命中。
- 结论：不是引用不存在 id；更可能是 B1/B2/B3 的初始化/覆盖问题。

## C. 建议验证顺序（不改 live）
1. A1：同存档 F3/forceload/region 计数 + Xaero 清缓存，排除客户端地图。
2. A2/A3：新建世界只装 zsky262_preset（无 aerolith）→选浮岛预设→检查 level.dat 与 forceload；再单独装 aerolith 对比。
3. A4：关 awakened islands 对比 region；/sky262_islands spawn 日志。
4. B1：窄范围初始化/移除 crashfix mixin 的 A/B 看 Create 机器；抓 SmartBlockEntity.initialize 的 BE 类名日志。
5. B2：base+Create 逐个加 CEI/DP/aeronautics/createframed 的 staging 二分；记录 Running/Speed/behaviours。
6. B3：静态配方 jar 只保留核心配方做 A/B，观察 saw/mill/mixer 配方。

## D. 结论先行
- 单 chunk 现象不能先归因 worldgen：sky islands 存档有 16 个 region、52 MB，服务器生成过多区块；优先查客户端地图缓存/预设未选中/aerolith 数据包。
- Create「几乎不能用」最大静态嫌疑是 B1（对所有 SmartBlockEntity 提前 initialize）叠加 B2（多个附属 mixin 到同一批 Create 类）；B3 第二嫌疑；createfix/mechanicals/tags 证据较弱。
- 以上均为静态推断；每条已给出 A/B 验证方法，未改 live。
