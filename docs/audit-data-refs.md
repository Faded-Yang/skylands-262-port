# audit-data-refs —— live 114 数据引用完整性审计

> 静态审计（不占 GPU）：扫 live 114 jar 的 `data/<ns>/{recipe,tags,loot_table,advancement}`，提取物品/方块/标签引用，对比实际注册 id。
> DOCS FIRST：参考 `docs/API-263-data-schema.md §7`（源码 jar 缺 data、数据应从发布 jar 取）、`docs/HANDOFF.md`（改数据要么全删要么全修、半截引用会让注册表失败）、`docs/DELIVERY.md`（NS 数据实测口径）。

## 1. 方法
- 注册清单：所有 live jar（+ 26.3 原版 jar）的 `assets/<ns>/items/*.json`（物品）+ `assets/<ns>/blockstates/*.json`（方块）；
- 标签清单：所有 `data/<ns>/tags/<type>/**.json`（含 26.3 原版与嵌套 jar）；按 `(type, ns:path)` 精确匹配；
- 引用提取：
  - recipe：`ingredient(s)`、`result(s)`、`item`、`output(s)`、`target`、`transitional_item`、`catalyst`、`required`、`key`；
  - loot_table：`name`/`item`（物品）、`blocks`（方块）、children 递归；
  - advancement：`item(s)`（物品）、`block(s)`（方块）递归；
  - tags：条目直接 id；`#` 开头为标签引用；
- 对比口径：物品引用必须命中 item_ids ∪ block_ids（BlockItem 以 block id 计）；方块引用命中 block_ids ∪ item_ids；标签引用按 type 精确命中。

## 2. 总量
| 项 | 数量 |
|---|---:|
| 注册物品 id（assets/items） | 6,468 |
| 注册方块 id（blockstates） | 5,500 |
| 标签 id（含 vanilla） | 2,120 |
| 扫描 data JSON 文件 | 7,914 |
| 物品/方块引用 | 22,181 |
| 标签引用 | 2,277 |

## 3. 结论（按严重度）
| 结果 | 数量 | 说明 |
|---|---:|---|
| **缺失方块 id** | **0** | 无 |
| **缺失标签 id** | **0** | 无（按 type 精确） |
| **缺失物品 id** | **4** | 全部来自两个第三方 jar 的「未安装 mod 兼容数据」；不影响已装内容 |

### 3.1 缺失物品条目清单
| # | 来源 jar | 文件 | 缺失 id | 后果 |
|---|---|---|---|---|
| 1 | `FarmersDelight-26.3-3.6.28+refabricated.jar` | `data/c/tags/item/hidden_from_recipe_viewers.json` | `farmersdelight:debug_pumpkin_pie` | 标签条目被忽略；该物品本就不存在，仅影响隐藏调试物品，**无玩法影响** |
| 2 | 同上 | `data/farmersdelight/recipe/integration/silentgear/cutting/netherwood.json` | `silentgear:netherwood_log`、`silentgear:stripped_netherwood_log` | SilentGear 未安装 ⇒ 该切割配方**永不匹配**（不报错，静默无效） |
| 3 | `createaddition-1.3.4-26.3.jar` | `data/createaddition/recipe/compat/ae2/charged_certus_quartz.json` | `ae2:charged_certus_quartz_crystal` | AE2 未安装 ⇒ 该充能配方**永不匹配** |

### 3.1b 按命名空间统计（缺失引用）
| 命名空间 | 缺失引用数 | 来源 |
|---|---:|---|
| `silentgear` | 2 | FarmersDelight SilentGear 切割兼容配方 |
| `farmersdelight` | 1 | FarmersDelight debug tag entry |
| `ae2` | 1 | createaddition AE2 充能兼容配方 |

### 3.2 重点 reduced/自研件
| jar | recipe | tags | loot | adv | 缺失引用 |
|---|---:|---:|---:|---:|---:|
| `sky262-createdeco-2.1.3-beta-port.21` | 0 | 0 | 0 | 0 | 0（零 data，仅资源+注册） |
| `sky262-design-n-decor-2.2b-beta-port.32` | 0 | 0 | 0 | 0 | 0 |
| `sky262-tfmg-1.2.0-26.3-b5` | 0 | 0 | 0 | 0 | 0 |
| `sky262-copycats-reduced-0.1.0` | 0 | 0 | 0 | 0 | 0 |
| `sky262-create-submarine-3.3.0` | 0 | 0 | 0 | 0 | 0 |
| `sky262-createpropulsion-1.1.5` | 0 | 0 | 0 | 0 | 0 |
| `sky262-aeroworks-1.5.0` | 0 | 0 | 0 | 0 | 0 |
| `sky262-culturaldelights-0.17.7-26.3-reduced` | 0 | 0 | 0 | 0 | 0 |
| `sky262-quests-1.6.0` | 0 | 0 | 0 | 0 | 0（任务数据不走 data 注册表） |

> 这些 reduced 件本身不带 data，所以不存在「配方引用缺失 id」；功能缺失来自**没有数据**（已知降级），不是引用错误。

### 3.3 其它数据量大的 jar（0 缺失）
- `natures_spirit`：5625 refs、826 recipe、720 loot、502 adv、267 tags → **0 缺失**；
- `create-fly`：700 tags、2063 refs → 0 缺失；
- `sky262-create-recipes`：1607 recipe、632 loot、7 tags、4849 refs → **0 缺失**（新增 create 数据件全部命中 create 已注册 id）；
- `createframed`：313 recipe、251 tags、227 loot、2515 refs → 0；
- `DungeonsArise`/`Structory*`/`interiors`/`waystones` 等 → 0。

## 4. 修复方案（按优先级）
| 优先级 | 项 | 方案 | 风险 |
|---|---|---|---|
| P3（可忽略） | FarmersDelight 标签里的 `debug_pumpkin_pie` | 删除该 tag entry（或忽略；不影响玩法） | 无 |
| P2（低） | FarmersDelight 的 SilentGear 切割配方 2 条 | 删除 `recipe/integration/silentgear/` 目录（或加 `fabric:load_conditions` mod_loaded 条件） | 只影响未安装 SilentGear 的兼容配方 |
| P2（低） | createaddition 的 AE2 充能配方 1 条 | 删除 `recipe/compat/ae2/`（或加 mod_loaded 条件） | 只影响未安装 AE2 的兼容配方 |

- 这 4 条都**不会让 registry 加载失败**（与 `API-263-data-schema §7` 的致命半截引用不同），属于「静默不匹配」；
- **无需补注册 id**：`silentgear`/`ae2`/`debug_pumpkin_pie` 都不是我们移植的 mod；补注册只会引入无资源空物品，正确做法是删兼容数据或加加载条件；
- 如果需要物理清理：直接改 `FarmersDelight...jar` / `createaddition...jar` 内对应 JSON（先备份记 SHA），或用同 id 覆盖 recipe（重复 id 后者覆盖前者，但删除 tag entry 不能靠覆盖）；

## 5. 审计盲区 / 后续
- 注册清单以 assets 为准：**无模型的自定义注册物品**会被误报为缺失；本次 4 个缺失 id 已逐一确认无对应 assets/lang/模组，属真缺失；
- 未展开 `data/fabric` / `resource_conditions` 的条件求值：带 `mod_loaded` 条件的引用本可以合法缺失；当前 4 条均无此类条件，故按缺失记录；
- 未审计 worldgen（biome/feature/structure）引用：另属 `API-263 §8` 的级联过滤范畴，本轮只做 item/block/tag/loot/advancement。
## 6. 清理候选（P2/P3，待 promote）
- staging：`g70/stage/data-ref-clean-final`（base live 114，替换 FD/createaddition 同名 jar；114 jar）；
- **FarmersDelight**：`8528d8b9563169b0b593e72e160ba4520cf236fe676116f410ebe1050051ffdc`（3,439,093 B）；
  - 删除 `data/farmersdelight/recipe/integration/silentgear/`（实际是 **1 个 recipe 文件**，内含 2 个缺失 id：netherwood_log / stripped_netherwood_log）；
  - `data/c/tags/item/hidden_from_recipe_viewers.json` values 清空（只剩 debug_pumpkin_pie entry）；
  - diff：仅 3 个删除项 + 1 个 tag 修改，无新增/其它修改；
- **createaddition**：`8f47070036b5bed69f230eb780c7126db99a5bb3488bff3a98053bc428172fc9`（1,427,640 B）；
  - 删除 `data/createaddition/recipe/compat/ae2/`（1 个 recipe 文件）；
  - diff：仅 2 个删除项，无新增/修改；
- **复跑审计**（对 staging）：`item_miss=0`、`block_miss=0`、`tag_miss=0`；
- 两 jar 的 class/assets 均逐字节未变（diff 仅 data 文件），jar 数不变。

## 7. kubejs / datapack / compat 目录扫描
- live 114 jar 中 **`kubejs/` 0 条、`datapacks/` 0 条**；
- `data/*/{compat,integration}/` 共 227 条，分布：
  | jar | 条数 |
  |---|---:|
  | `sky262-create-recipes`（26.2 source 的 create compat 配方） | 174 |
  | `FarmersDelight` | 42 |
  | `createaddition` | 7 |
  | `create-fly` | 4 |
- 清理前缺失引用只在 FD（SilentGear）与 createaddition（AE2）；清理后对 staging 全量审计 **0 缺失**；其余 compat 配方引用的 mod 均已在 live 中。