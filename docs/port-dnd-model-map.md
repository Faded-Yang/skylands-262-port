# DnD（Design-n-Decor）模型路径映射表 + 剔除清单

> 适用：26.3 Fabric 移植。DnD 1.21.1 模型引用的 create 模型路径在 create-fly fork 里改成了子目录结构；
> 生成器 `_dnd_gen8.py` 里常量化 `CREATE_MODEL_MAP`，所有批次复用。

## 1. create 模型路径映射（4 条，全部已存在）
| 原引用（DnD 1.21.1） | fork 实际路径 |
|---|---|
| `create:block/cogwheel` | `create:block/cogwheel/block` |
| `create:block/large_cogwheel` | `create:block/large_cogwheel/block` |
| `create:block/cogwheel_shaftless` | `create:block/cogwheel/shaftless` |
| `create:block/large_cogwheel_shaftless` | `create:block/large_cogwheel/shaftless` |

## 2. 其它命名空间引用处理
- `minecraft:block/air` 等模型 → 用 MC 自带；出现 `missingno` 纹理是原版占位（vanilla air 模型），**已在资源自检中豁免**；
- `create:block/seat/top_<color>`（velvet 系列用）→ fork **不存在** ⇒ 该系列方块在生成器里直接过滤（`_velvet_` 前缀），不放入批次；
- `assets/everycomp/**`、`assets/quark/**` 等第三方命名空间资源一律不拷（与 CDG 同规则）。

## 3. 剔除清单（永久跳过）
| id/系列 | 原因 |
|---|---|
| `*_velvet_block`（amber/aqua/beige/coral… 等） | 模型引用 `create:block/seat/top_*`，fork 无此贴图；等 create 补或我们自补贴图后再收 |

## 4. 递归解析规则（生成器已实现）
1. blockstate（variants + multipart.apply）→ 模型引用；
2. 模型 `parent` 递归向上；
3. 命中 `CREATE_MODEL_MAP` 先重写；
4. 目标在 DnD jar 里 → 拷贝；不在 → 记为 unresolved；
5. 若某方块闭包里出现 unresolved ⇒ 该方块整批**剔除并记录**（宁可少几个，不要品红）；
6. 解析结果写入 `/tmp` 式日志：`R511 closure rounds N unresolved [...]`、`R511 dropped ids [...]`，build 日志可见。

## 5. 当前状态
- DnD batch7（累积 357 方块）：资源自检 **0 missing**；`unresolved=[]`；无剔除；
- 后续批次直接用同一生成器 + 映射表，无需再手工 diff。
