#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「当前真实状态」更新到 R369：真浮岛已做（岛厚 14.1）、水柱已修、船已修、结构 25%。"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
h = open(HOT, encoding="utf-8", errors="replace").read()

i = h.find("- **当前真实状态（R367 之后）**")
j = h.find("- **削减清单**", i)
if i < 0 or j < 0:
    print("★ 锚点未找到", i, j)
    sys.exit(1)

NEW = """- **当前真实状态（R369 之后）**：
  - ✅ **标题画面**｜✅ **进世界**（用户验收）｜✅ 方块/物品/BE 真注册（137）｜✅ 物品图标正常
  - ✅ **汉化 100%**（en 8,628 / zh 8,850 / 缺 0，R366）｜✅ 88 条配方｜✅ `sky262crashfix`｜✅ 创造标签页
  - ✅ **浮岛地形 = 可选「世界类型」**（mod **`zsky262_preset`**，`skylands:sky_islands`；用户实测「成功启动浮岛地图」）
    - **岛厚已做对**（R369）：根因是 2D mask `xz_scale` 太小（0.0068 ≈ 7.5 万格一个特征 ⇒ 可见范围内 mask 近乎常数 ⇒ 均匀薄片）。
      改成 **0.30/0.42 离散大块 mask + 两段式锥底** ⇒ 实测 1,115,136 列，**两带厚度中位 14.1**（中带 p50=11 / 高带 p50=17，max 57/74），
      锥形 边缘3→4→7→9→9→中心17，29/26 个 blob，最大 403×403 / 479×479
    - **水柱已修**（R369）：carver 只挖 y≥168 + **`aquifers` 整键删除**；实测 y≤63=28.8M 块 / y64-79=**236** / y80-159=7 / y≥160=0（无连续竖列）
    - **船已修**（R369）：`structory:boat`、`medieval_buildings:ship` → `{"absolute":62}` 且**删投影**；实测 boat 落 y=61
    - ⚠ **结构上岛只有 25%**：40 个结构起点 高带 10 个 / 海平面 1 / y<60 23 个；**村庄 0 实例**（样本区是海洋群系）
    - ⚠ **`aquifers` 关掉的代价**：y<64 不再有空气洞穴/岩浆湖，地下探索变少
    - ⚠ **老存档不会变**，必须**新建世界**；本 jar 覆盖 structory/medieval_buildings 的结构 ⇒ **删那两个 mod 必须同时删本 mod**（否则 template_pool Unbound 崩）
  - **一键启动：`启动浮岛世界.bat`** → `mods-stable`（**47 jar**，含 `modmenu-21.0.0`，已与 `watch\\mods` 同步）
  - ⚠ **`mods-full` 是代理暂存区**；给用户前必须先进世界实测
  - ⚠ **`launch.py --mods` 会同步改 `<game-dir>\\mods`** —— 实验一律用 `work\\run26\\stag1`
  - ⚠ **已知未做**：结构上岛比例（村庄无实例）、创造标签页无分区、Create 的 27 条加工类配方、
    余下 8 个 1.21.x mod 与 40 个 NeoForge-only mod（**这是当前主目标：107 个 mod 全量移植**）
  - **⇒ 本项目现在实际也在移植 Create（上游 ZurrTum/Create-Fly 无 26.3 分支，最新只到 26.2）**
"""
h2 = h[:i] + NEW + h[j:]
open(HOT, "w", encoding="utf-8", newline="\n").write(h2)

tot = sum(os.path.getsize(f) for f in [
    os.path.expanduser("~/.dsh/AGENTS.md"),
    r"C:\Users\95959\OneDrive\Desktop\Work\AGENTS.md",
    HOT,
])
print("updated; hot %d B; total %d B %s" % (len(h2.encode("utf-8")), tot, "OK" if tot <= 40960 else "OVER"))
