# Known Limitations —— skylands-262（MC 26.3 / Fabric 0.19.5）

> 以下为有意保留的降级；均不影响「标题可进 + 世界可进 + 0 crash」基线。

## 装饰：createdeco / Design-n-Decor
- 装饰方块无 BlockEntity、无交互/动画（纯外观）；ponder 未做。
- DnD 剩 72 id 未移植：velvet 32（缺 create seat 贴图，永久跳过）+ 杂项 40（casing/part/slope 等枚举，未尝试）。
- 少量 cosmetic 贴图缺失（如 dndecor:block/display_board），不影响 missing model 判据。
- 部分方块用近似模型/属性降级（属性兜底、原版 placer 等价）。

## natures_spirit
- 树形使用 26.3 原版 placer：NS 自定义 FoliagePlacer/TrunkPlacer/TreeDecorator 未移植（26.3 重构 tree worldgen API，需逐类移植 28 个类，2–4 轮高回归风险，已押后）。
- 2 个自定义 feature type（huge_brown/red_mushroom）数据删除；少量自定义 rule test 用 tag_match 等价替代。
- advancement 502 条，shoot_coconut 跳过（26.3 结构差异）。
- resourcepacks/ 整体移除：Paxi 会把 mod jar 内 resourcepacks 当 datapack 加载，旧 1.21 覆盖会污染 registry（死路）；需要时按 26.3 重建。
- village 结构数据未恢复；地形特征族只恢复 tree/ore/simple_block/vegetation_patch。

## 食物（reduced 类）
- culturaldelights / minersdelight / mynethersdelight：assets+手写注册，部分食物无食用效果/无作物生长逻辑；少数缺 FD 刀板/锅交互扩展。

## 机械 / 机器
- 柴油发电机：43 方块可放置，机器无功能行为（无发电/无流体逻辑）。
- 挤出机：配方/动力连通 PASS，产物渲染/BER 未完成（外观降级）。
- sliceanddice：配方加载、交互可用；部分切割产物模型简化。
- 中央厨房：机械臂×FD 联动为降级实现，ponder 未做。

## 流体（CEI / DragonsPlus）
- CEI 流体注册已正确（live）；游戏内 `create_enchantment_industry:experience` setblock/读回已 PASS（探针实拍 `fluids_live.png`）。
- DP 保持 live 旧件：新构建仅 create 依赖下限升至 >=6.0.9-4，live create 为 6.0.9-2 ⇒ 不可启动；不升级 create-fly（上游链风险）。

## 结构 / 世界生成
- No Void Structures 仅验证「数据加载 + 世界可进 + /locate structure 返回坐标」；结构不在虚空生成的目标行为待浮空岛地图验证。
- 浮空岛世界（aeronautics/sable）结构/地形仍降级：simulated 实体缺 EntityRenderer（honey_glue 首帧 NPE 历史问题）。

## 任务系统
- titleItem 为 air 的条目走 fallback 显示英文物品名（Sandworm gauntlet / Ice gauntlet），不出现「空气」但非中文；需补 zh_cn 键。
- 少数任务格标题回退到任务标题（原 icon 缺失），属数据问题非 GUI bug。

## 平台 / 验证
- 语言加载为全局硬依赖：任一 mod lang JSON 坏都会让所有 mod lang 失效（已修两处；新增件必须跑 tools/lang_audit.py）。
- 26.3 worldgen 数据 schema 与 1.21 差异大（feature 平铺 / provider 数据化 / configured_feature 目录改名 / noise firstOctave→base_octave / placement random_offset→offset / blockstate id-properties），数据包类件必须按 docs/api-landmines.md 校验。
- 所有件仅验证「标题 + 进世界 + 抽样 MCP」；未做长时稳定性/存档兼容/多人测试。