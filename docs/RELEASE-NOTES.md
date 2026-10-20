# Release Notes —— skylands-262（MC 26.3 / Fabric 0.19.5 / Java 25）

> 交付物：`work/run26/mods-stable`（**100 jar**，截至 2026-10-20；Miner's Delight + Abnormals Delight 已并入；+2 液体燃料兼容壳待并入 → 102）｜移植覆盖 101/110｜汉化 100%（zh-final2 已 promote）
> 证据口径：每条「已验证」均来自游戏内 MCP 实测（player.getState / world.getBlock / chat.send / screenshot.take）。

## 核心
- 26.3 平台迁移：Block/Item Properties 全部 setId；旧 recipe/advancements 清除；手写 jar 用 tools/pack_jar.py 保目录条目。已验证：标题+进世界+0 crash。
- 语言加载修复：26.3 一次解析全部 mod lang，任一坏 JSON 全局失效；修掉 extruder zh_cn 缺逗号、createaddition vi_vn 控制字符。已验证：无 Unable to load languages，全量 lang 审计 0 坏文件。
- **UTF-8 BOM 修复（2026-10-20）**：minersdelight `es_es.json` 带 BOM ⇒ 26.3 全量 mod lang 回退 en_us（表现为 ponder 标题/按钮/提示全部英文，而 jar 内 zh 正常）。已重打包为 `833d7333…`（仅该文件去 BOM，147,673 B；base `88e909f9…`）；`tools/lang_audit.py` 增加 BOM 扫描（live 114 jar/1053 lang files → BOM=0）。

## 装饰（1163 方块）
- createdeco 389/389（4A08DE19…）：门/活板门/围栏/窗/牌匾/支撑楔/币堆等。已验证：black_placard / zinc_support_wedge[orientation=2] / blue_brick_stairs / andesite_trapdoor setblock+读回一致；Missing model=0、blockstate 异常=0。
- Design-n-Decor 774/846（2FEEF8AB…）：齿轮/飞轮/大风扇/地砖/容器/展示板/灯。已验证：cogwheel 三轴 setblock+读回；Missing model=0。
- 共同基线：ids 只增不减、variant 补齐幂等、解包断言 variant model 递归 parent 存在（problems=0）。

## 食物 / 农业包
- FarmersDelight refabricated + chefsdelight / corndelight / ends_delight 等。已验证：标题+进世界+物品在创造栏可见。
- reduced 类：culturaldelights / minersdelight / mynethersdelight（assets+手写注册）。已验证：进世界 0 crash、物品可获取。

## 任务系统（自研 sky262-quests 1.6.0）
- J 键任务书、22 章 543 任务、提交/领取/锁定/奖励、进度存档、命令与结构化日志。已验证：按钮「关闭/提交/检查/领取」中文、锁定提示中文、描述多行可读、无「空气」图标。
- UI v2（86900d5b…）**widget 化**：任务格改为 `AbstractWidget`（命中区域=高亮区域）、章节/翻页/四按钮为真 Button、11 个中文 tooltip 与禁用原因（请先选择任务/未解锁/已完成/已领取）。mcpfabric `ui.widgets`+`ui.click` 实测：章节/翻页可点、点任务格后 Submit 由 disabled→enabled、点 Submit 服务端回执 `submit <quest> -> missing-items`；17 个 widget 全暴露。

## 世界生成：natures_spirit
- 153 个 NS 生物群系可生成/可定位（84B1C308…，B2）。已验证：/locate biome natures_spirit:redwood_forest 返回坐标并实拍巨型红杉林；blooming_highlands 实拍雪松/秋色/湖；地表 grass_block。
- 数据完整：loot 720 + recipe 826 + advancement 502；MCP 实测 loot give 白杨木台阶、recipe give aspen_button、advancement grant alluaudia_bundle 全成功。
- 地形特征：156 feature + 181 placed_feature，全 129 群系 features 填回。

## 机械 / 交互
- 挤出机：已验证 onSpeedChanged 0.0→-16.0、recipe matched sandstone。
- Slice and Dice：551 条 cutting 配方加载，useItemOn+useWithoutItem 双 override；已验证切制交互可用。
- 喷气背包：右键推力 60 tick、约 3 格/次；needsSync + ClientboundSetEntityMotionPacket；已验证推进位移与粒子。
- 动力装载器 / 柴油发电机 43 方块 / 中央厨房：标题+进世界+方块可放置。

## 工具与客户端
- sky262-mcp（WS 25576）+ tools/mcp_fabric_client.mjs：getState/getBlock/chat.send/screenshot.take 全链路；多轮实拍截图留档（g33/mcp-shots）。
- 创造栏：DP 19 物品、CEI 15 物品可见（01FAFE34… / 82EAB589…）。

## 汉化（CEI 思索界面）
- CEI（a2c510b3…）：ponder 15 个场景 nbt 完成 26.3 palette 迁移（Name/Properties→id/properties，缺失会导致场景全空）；zh_cn 原为英文复制（假汉化），已用 1.21.1 原包真实中文按 key 合并（335/336 键）+ 手译 1 键；另把源码中 181 处硬编码 ponder/GUI 英文文本（scene.title/scene.text 字面量）替换为中文并重编译（0 errors）。
- 已知降级：ponder 3D 场景渲染依赖 live create-fly（R421 修复，未改动）；我方仅做文本汉化，不改渲染代码。

## 流体（CEI / DragonsPlus）
- CEI 26.3 流体注册（FluidEntry 直注册 still/flowing）已在 live（72880D90…），编译 0 错；MCP 实测 experience/blue_dye 两流体块 setblock+读回一致；DP 保持 live（01FAFE34…，新构建仅 fabric.mod.json 版本下限差异）。详见 docs/port-fluids-263.md。

## 机械 / 交互
- Sophisticated Storage 1.6.7（reduced 壳，ad13f766…）：59 方块 + 147 物品（88 plain + 59 block items）+ 自建创造栏「精妙存储」；item model 全量重建为 vanilla item/generated（原 mod 自定义 loader 在 26.3 不可用）。MCP 实测：147 items 日志、give copper_chest→铜箱子/copper_barrel→铜桶（无 %s）、setblock 读回、Missing model 0、bad item textures 0、0 crash。
- Sophisticated Backpacks 3.26.12（reduced 壳，68573bde…）：79 注册项（6 方块 + 73 物品）+ 自建创造栏「精妙背包」。MCP 实测：give backpack/advanced_pickup_upgrade 到手（已汉化）、setblock backpack/diamond_backpack 读回一致、Missing model 0、0 crash、registry 0。GUI/存储功能未移植。
- Create: Connected 1.3.3（reduced，37fec0a3…）：109 个 QoL 方块（齿轮箱/离合器/滑槽/风扇染料催化剂/copycat 系列等）纯外观注册 + 自建创造栏页签。MCP 实测：109 blocks 注册日志、10/10 setblock 读回一致、Missing model 0、0 crash、registry 0。

## 结构
- Sable x Create Crafts & Additions Compat 0.1.13（reduced，21c75509…）：跨 sable 子世界的接线渲染/断线逻辑（保留 10 class + 非致命 mixin：默认 defaultRequire 0）。MCP 实测：mod 列表加载、标题+世界可进、0 crash、0 registry；行为细节留手测。
- Create: Hangars 1.0.0（reduced 纯数据，9bf2ea54…）：8 个 jigsaw 机库结构 + structure_set + template_pool（26.3 processor 包装与 blockstate 转换）。MCP 实测 /locate structure igcah:plains_hangar/birch_hangar/savannah_hangar 均返回坐标，tp 后实拍完整木构机库（条纹屋顶/大门/石柱），抽样方块 oak_planks。
- Awakened Islands 1.0.0（reduced，4e14bc6f…）：浮空岛生成（原 sable schematic 改用 26.3 原版 StructureTemplate 路径）。MCP 实测 /sky262_islands spawn → 日志 loaded template 16x17x17、placed ok=true sampledNonAir=6，世界方块命中 levitite/andesite/tall_grass，截图可见雪原上空浮空岛；概率生成 1/4096 新 chunk。
- No Void Structures 2.0.1（b3，b1712dbc…）：21 个结构覆盖 = 26.3 原版结构 body + Lithostitched delegating wrapper；MCP 实测 registry 0 / world OK / locate village_plains、pillager_outpost、swamp_hut 均返回坐标（虚空行为待浮空岛地图验证）。

## 液体燃料兼容壳（占位，待行为移植）
- `portable_engine_liquid_fuel` 2.0.0 / `createliquidfuel` 3.0.0：纯行为 addon（data_maps + mixin，无 assets/方块/物品），当前仅兼容壳；目标行为见 KNOWN-LIMITATIONS，排在用户手测反馈后的优化批次。

## 已知限制
见 docs/KNOWN-LIMITATIONS.md。

## 广度收口补充（R620）
- **TFMG 436/436 方块**（zh_cn 1299 键，锂火把/铝块等中文名生效）；**create_connected 109**；**create_submarine 43**（3 命名空间）；**createpropulsion 33**；**copycats 46**；**sophisticated backpacks 79 项 / storage 59 方块+147 物品**（壳，无 GUI）；**create-hangars 8 结构**；**awakened islands**（\`/sky262_islands spawn\` 实测生成带植被浮空岛）；**No Void Structures**（3 条 /locate 命中）。
- 验证：MCP 实测 5 方块读回、NS 红杉林实拍、任务书中文按钮、\`/loot\`+\`/recipe\` 成功；114 jar 标题回归 PASS（Loading 194+ mods）。
- 新增硬断言：**解 jar 后**方块模型递归 parent、**item 模型贴图存在性**、**lang 值不含格式占位符** 三查，任一不通过不打包。