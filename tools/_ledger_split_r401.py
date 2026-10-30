#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_ledger_split_r401.py —— 把 skylands-262/AGENTS.md 热层压到预算内（零丢失）。

按 `ledger-budget` 要求：
1. 先备份原件
2. 长索引行**整段**搬进 `docs/SOLVED-FAMILIES.md`（不改字）
3. 热层只留坐标 / 纪律 / 索引指针（指针必须写清「搜什么词」）
4. 自查：热层 + 上级 AGENTS.md ≤ 40 KB
"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
COLD = os.path.join(P, "docs", "SOLVED-FAMILIES.md")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

h = open(HOT, encoding="utf-8", errors="replace").read()
shutil.copy2(HOT, HOT + ".bak-split-" + TS)

lines = h.split("\n")
# 收集「已解族索引」表里的全部数据行（整段搬走，不改字）
st = next(i for i, l in enumerate(lines) if l.strip().startswith("| 族 | 结论 |"))
en = st
while en < len(lines) and lines[en].startswith("|"):
    en += 1
table_rows = lines[st + 2:en]

with open(COLD, "a", encoding="utf-8", newline="\n") as f:
    f.write("\n\n## 搬出索引行（t42，R401 预算压缩：R399/R400 完整行）\n\n| 族 | 结论 | 轮次 |\n|---|---|---|\n")
    for r in table_rows:
        f.write(r + "\n")

NEW = r"""# AGENTS.md —— skylands-262 台账（**热层：只放坐标 / 纪律 / 索引**）

> 每步注入 ⇒ **只放「下一步就要用」的**；深度资料在 `docs\`，按需读。
> ⚠ harness 每步重读，**免疫上下文压缩**；摘要与本文件冲突时**以本文件为准**。
> 预算：本文件 + `Work\AGENTS.md` + `~\.dsh\AGENTS.md` **≤ 40 KB**（超了就从尾部截断，剪掉的是最新写的）。

---

## 一、坐标（当前交付状态）

- **目标**：天穹群岛整合包（原 1.21.1 + NeoForge，110 mod）→ **MC 26.3 + Fabric Loader 0.19.5 + Java 25**，全部游戏内容。
- **交付物 = `work\run26\mods-stable`，71 jar**；`启动浮岛世界.bat` → 它（启动时同步进 `watch\mods`）。
  - 本体实测：`TITLE_SCREEN_OK` ~29 s + `WORLD_OK` ~45 s；`Loading 150 mods` / `Loaded 2343 advancements` / `Registry loading errors: 0`
  - 自移植的 4 个核心：`aeronautics` `2DF06E76…BD2B`(31,547,810 B) · `sable` `54ADAAE1…` · `create-fly` `280B586B…D41F`(19,639,235 B) · `sablecompanion`
- **汉化 100%**：en 10,129 / zh 10,357 / 缺 0（42 namespace）。工具 `tools\lang_audit.py`。
- **浮岛地形 = 可选世界类型**（mod `zsky262_preset`，15 条目 / 6,127 B，`tools\build_preset_r368.py`）：
  原版 aerolith 地形 + **唯一改动** carver `skylands:cave/canyon` `y=[170,450]`。**用户已定稿，不要再动**
  （否决过：拆低层地面、岛加厚成 `island_*`、三层叠加、删 aquifers、船覆盖）。
- 移植进度 **71 / 110**；剩余用 `tools\diff_pack.py` 算。交付说明 `docs\DELIVERY.md`（已修 / 未修 / 降级）。

---

## 二、纪律（硬约束，违反会翻车）

- **验收门槛三级**：`compileJava` 0 错 ≠ 能跑；**只过标题 ≠ 能跑**；**进世界 ≠ 功能生效**（Jade 插件被静默丢弃就是例子）。
  必须 `tools\launch26\launch.py` 真启动；**每次用全新存档副本**（同一存档被试过一次会变实验性 ⇒ 伪装成超时）。
- **绝不能碰 `work\run26\watch`**（`launch.py --mods` 会同步改它 = 改用户运行环境）。实验一律 `stag1` / `port\gN`。
- 只 promote「标题 + 进世界」都实测过的；promote 后立刻复跑标题。
- **改 jar**：先备份并记原 SHA-256；**只让目标 class 变化**（其余 entry 逐字节不动）；改完 `javap -p -c` 逐方法比对。
- **子代理失败后**先核 jar 的 mtime/大小/SHA **与源码目录的 `.bak-*`**，再决定重跑 —— 失败代理会留半成品。
- **判「26.3 有没有某成员」必须在「加载了 fabric-api 的运行期」验证**，不能只 `javap 26.3.jar`（fabric-api 会织方法）。
- **改数据要么全删干净、要么全修**：留半截引用会让整个注册表失败，报错还会指向别人（`mineable/pickaxe` 那次）。
- **玩法级回归**（读档才跑的代码）用一次性驱动 mod：`phase=place` 放方块+存盘 → `phase=reload` 重进+强制提升 pending BE。
  `watch_world.py` 只能「进世界」，做不到这个 ⇒ 已修的两个 bug 就是它漏的。

---

## 三、索引（已解族：只列结论；精确修法在 `docs\fix-*.md`）

> 全表见 `docs\SOLVED-FAMILIES.md`（搜「搬出索引行」）。**动手前按族名先查一次 `docs\fix-*.md`**，查不到就 javap 现查。

| 族 | 结论 | 详情 |
|---|---|---|
| **`ValueInput.contains` 假警报（已结案）** | `fabric-api` 的 `FabricValueInput` 提供 `default contains(String)`，运行期织进 `ValueInput` ⇒ 能调通。**判 26.3 成员要在带 fabric-api 的运行期验** | `docs\fix-valueinput.md` |
| **同族 4 处 `neighborChanged` NPE（已全修）** | 26.3 把第 5 参 `BlockPos`→`@Nullable Orientation`（普通世界恒 null），端口只改签名、体还在读 ⇒ NPE ⇒ 服务器崩。删门 / 保留 `canSurvive` | `docs\fix-npe-*.md`（handle / last2 / and-itemhelper） |
| **`ItemContainerContents.allItemsCopyStream` 已删（已修）** | 26.3 等价是 **`itemCopies()`**；无源码 ⇒ **ASM 只改 1 个 method-ref**，只 1 个 class 变 | `docs\fix-npe-and-itemhelper.md` |
| **静态地雷扫描（工具已建）** | `tools\scan_landmines.py`：178 条地雷（高危 47）。**自检**：旧 create jar 能精确复现已知地雷、当前件 0 条 | `docs\api-landmines.md` |
| **`RenderTypes.glint` 族（已修）** | 26.3 不是改名，是**劈成 `Function<Identifier,RenderType>` 工厂**；`glint()`→`Sheets.cutoutBlockItemGlintSheet()` 等 | `docs\fix-landmines-1.md` |
| **`InterpolationHandler` 族（已修）** | 26.3 变成**接口** ⇒ 旧件抛 ICCE/NoSuchField；`position()`→`target().position()`、`interpolateTo` 加 `PositionPath`+boolean、`steps=0`→`cancel()` | `docs\fix-landmines-1.md` |
| **`PonderRenderTypes.<clinit>:38`（进行中）** | 26.3 `OutputTarget` 类整个不存在、`setOutputTarget` 也没有 ⇒ 要**重写**不是改名。**挡住所有 catnip 渲染路径（穿 backtank 必崩）** | `docs\api-landmines.md` 搜 `PonderRenderTypes` |
| **`ProcessingRecipe` 框架已删（垫片已建）** | 26.3 改用 `CreateRecipe<T>` 家族；垫片 `g10/shim/proc-recipe-compat.jar`（123 成员 / 契约测试 17/17） | `docs\port-procrecipe.md` |
| **26.3 数据层硬坑** | 战利品 `"name":"minecraft:air"`、advancement 引用已删 `trigger_type`、配方引用不存在 item/tag ⇒ **整注册表失败** | `docs\DEGRADATIONS.md` |
| **26.3 客户端 API 改名** | `getTimer()`→`getDeltaTracker()`、`getMainCamera()`→`mainCamera()`、`Camera.getLookVector()` 已删、`Level.isDay()` 已删、`EntityType.PLAYER`→`EntityTypes.PLAYER`、`moveTo`→`snapTo`、`MobSpawnType`→`EntitySpawnReason` | `docs\port-smallmods.md` |
| **Create 包名 / 命名** | Create 是 ZurrTum 分支 `com.zurrtum.create`；`BlockEntityBehaviour` 在 `api.behaviour`；`ResourceLocation`→**`Identifier`** | —— |
| **26.3 数据 schema** | `recipes`→`recipe`、`loot_tables`→`loot_table`、`tags/{blocks,items}`→`{block,item}`、配方 `result.item`→`id`、loot 条件键 `condition`→`type` | `docs\DEGRADATIONS.md` |

---

## 四、深度资料在哪（**26.3 专用；1.21.11 的已归档，别读**）

| 要找什么 | 读哪份（搜什么词） |
|---|---|
| 26.3 依赖矩阵（哪些库有 26.3 构建） | `docs\DEPS-26.3.md` 搜「已有 / 缺失」 |
| 已解族的完整行 | `docs\SOLVED-FAMILIES.md` 搜「搬出索引行」 |
| 削减清单（进交付说明） | `docs\DEGRADATIONS.md` |
| 交付说明（用户向） | `docs\DELIVERY.md` |
| 地雷清单 | `docs\api-landmines.md`（搜类名） |
| 启动器的用法与坑 | `tools\launch26\README.md` |
| 1.21.11 时期（**已作废，只做留档**） | `docs\ARCHIVE-1.21.11.md` / `docs\PHASE-LOG.md` |

---

## 五、硬规则速查（全表 `docs\HARD-RULES.md`）

`1` 先跑 `check_parse.py` 再读数 ｜ `2` 回滚按有无备份 ｜ `4` 判进步看**族是否清零**不是总数
`10` 改 import 前确认同 import 还有别的成员在用 ｜ `13` javac 行号≠要改的行
`18` 改签名的闸门要排除即将被重写的那一行 ｜ `31` 删声明必须清掉**全部**使用处
`34` 直方图 top-N 不是完整错误列表 ｜ `36` **绝不按方法名一刀切**
**★ 40 局部别名法**：参数类型变了、体很大 ⇒ 只换签名 + 体首注入局部变量
**★ 39**：改动变差时**先拿本表逐条对** —— 答案通常在表上
"""

open(HOT, "w", encoding="utf-8", newline="\n").write(NEW)

files = [os.path.expanduser("~/.dsh/AGENTS.md"),
         r"C:\Users\95959\OneDrive\Desktop\Work\AGENTS.md", HOT]
tot = sum(os.path.getsize(f) for f in files)
for f in files:
    print("  %-46s %7d B" % (os.path.basename(os.path.dirname(f)) + "/" + os.path.basename(f), os.path.getsize(f)))
print("注入合计 %d B  %s  (目标 ≤ 40960)" % (tot, "OK" if tot <= 40960 else "仍超，需再砍"))
print("搬走的索引行: %d 行 → %s" % (len(table_rows), COLD))
