#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R379：+1（59 jar）+ remap 成员改名从未生效（重估 1.20.1 那批）+ 缺口量化。"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
COLD = os.path.join(P, "docs", "SOLVED-FAMILIES.md")
h = open(HOT, encoding="utf-8", errors="replace").read()
shutil.copy2(HOT, HOT + ".bak-r379-" + datetime.datetime.now().strftime("%H%M%S"))

ROWS = [
 "| 🎉 **【R379 第六批：+1，mods-stable 59 jar】** 新增 `structures-1.2-26.3.jar`（More Structures 热气球结构，纯数据包）。"
 "`WORLD_OK 36.2s`（全新存档副本）+ promote 后 `TITLE_SCREEN_OK 25.7s`，日志 `Found new data pack structures` 无 parse/registry 报错 | —— | R379 |",

 "| ★★★★★ **【R379 `remap_intermediary.py` 的成员改名从来没生效过 —— 这推翻了「1.20.1 那批卡在 API 难度」的判断】** "
 "实测 `interiors` remap 前后 `class_=650 method_=128 field_=56` **一条没变**。"
 "**根因**：`_maps\\i20n-ns1.tiny` 的 **class 列是 intermediary、desc 列却是混淆空间**（`m (Ldde;…) method_11657 setValue`），"
 "工具按 `(owner, name, desc)` 三元组查 ⇒ **desc 永远 miss**。**`i21n-ns1.tiny` 的 desc 才是 intermediary 空间，1.20.1 应该用那个。**"
 "**⇒ 下一轮别再去修这个工具，直接吃 `est_gap_263.py` 的输出** | —— | R379 |",

 "| ★★★★★ **【R379 缺口量化工具 `tools/est_gap_263.py`（按 `(owner, 翻译后 desc)` 判，先走 name-only 表）】** "
 "**`interiors`**：150 条 MC 引用 = 32 已合法 + **118 可全自动** + **26 需人工**（其中 8 条是 `Direction.ordinal()` 误报 ⇒ **真实 18 条**）；"
 "Create 侧 32 个类里 **27 个前缀替换即命中**（`com/simibury`→`com/zurrtum`，**注意原作者命名是 simibury 不是 simibubi**），"
 "只有 4 个要换包（`ItemDescription`→`client/foundation/item`、`VecHelper`→`catnip/math`、`AllTags`→`AllItemTags`、`CreateRegistrate/TagGen`→`foundation/data`）+ `CreateBuildInfo` 已消失。"
 "**Registrate 26.3 垫片真实存在**（在 aeronautics jar 里），只差把 `NonNullFunction/Consumer/UnaryOperator/BiConsumer` 映射到 `java.util.function.*`。"
 "**⇒ `interiors` 从「黑洞」降级为 ≈2–2.5 人日的有界工程**；**`create-framed`** 54 条需人工 ⇒ ≈3 人日，排后 | —— | R379 |",

 "| ⚠ **【R379 `natures_spirit` 结论：不要开工；真身是 Fabric 1.21.1 / 176 class】** 实测不是 202 class 的 NeoForge 版；"
 "`terrablender` 只是 `suggests` 不是硬依赖。但**自定义注册表是 4 个不是 3 个**（多一个 `trunk_placer_type`），"
 "要动 **43 个 codec 扩展类**（Feature 12 / FoliagePlacer 11 / TrunkPlacer 13 / TreeDecorator 7）+ **564 条** MC 符号（A315/C191/D43/B15）"
 "⇒ **≈8–12 人日**。建议只做「12 个 `feature_type` + 对应数据子集」的最小切片 | —— | R379 |",

 "| ✅ **【R379 `nf_refs=0` 那批已清完，别再扫】** `_orig_scan.json` 里实际是 **19 个**（不是 11）。其中 14 个已在 `mods-stable`；"
 "2 个不是内容 mod（`create-aeronautics-bundled` 是 bundle、`kotlinforforge` 是 loader 库）；"
 "**只剩 2 个是 Java mod**：`gadgets-and-gizmos-bundled`（内嵌 `createthrusters` 34.6MB + `gadgetsngizmos` 2.7MB 两个真 Create 附属）、"
 "`FTBQuestsOptimizer`（依赖本包没有的 FTB Quests，**不可做**） | —— | R379 |",
]

anchor = "| 阶段A 生物刷新（现成 mod） |"
h = h.replace(anchor, "\n".join(ROWS) + "\n" + anchor)
h = h.replace("（**58 jar**，`TITLE_SCREEN_OK` 25.6s", "（**59 jar**，`TITLE_SCREEN_OK` 25.7s")
h = h.replace("F+B·N 剩 ~49**（`natures_spirit` 判定只能 Java 移植）",
              "F+B·N 剩 ~48**（**`nf_refs=0` 那批已清完**；`natures_spirit` ≈8–12 人日；`interiors` ≈2–2.5 人日、`create-framed` ≈3 人日已量化）")

lines = h.split("\n")
st = next(k for k, l in enumerate(lines) if l.strip().startswith("| 族 | 结论 |"))
en = st
while en < len(lines) and lines[en].startswith("|"):
    en += 1
rows = lines[st + 2:en]
KEEP = 10
moved, kept = rows[:-KEEP], rows[-KEEP:]
with open(COLD, "a", encoding="utf-8", newline="\n") as f:
    f.write("\n\n## 搬出索引行（t20）\n\n| 族 | 结论 | 轮次 |\n|---|---|---|\n")
    for r in moved:
        f.write(r + "\n")
h2 = "\n".join(lines[:st + 2] + kept + lines[en:])
open(HOT, "w", encoding="utf-8", newline="\n").write(h2)

tot = sum(os.path.getsize(f) for f in [
    os.path.expanduser("~/.dsh/AGENTS.md"),
    r"C:\Users\95959\OneDrive\Desktop\Work\AGENTS.md",
    HOT,
])
print("hot %d B; total %d B %s" % (len(h2.encode("utf-8")), tot, "OK" if tot <= 40960 else "OVER"))
