#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「当前真实状态」更新到 R367：地形已回滚（拆地面是错的）+ carver 已修好。"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
h = open(HOT, encoding="utf-8", errors="replace").read()

i = h.find("- **当前真实状态（R362 之后）**")
j = h.find("- **削减清单**", i)
if i < 0 or j < 0:
    print("★ 锚点未找到", i, j)
    sys.exit(1)

NEW = """- **当前真实状态（R367 之后）**：
  - ✅ **标题画面**｜✅ **进世界**（用户验收「能进」）｜✅ **方块/物品/BE 真注册**（137 方块）｜✅ **物品图标正常**
  - ✅ **汉化 100%**（en 8,628 / zh 8,850 / 缺 0，见 R366）
  - ✅ **88 条配方**｜✅ 崩溃已修（`sky262crashfix`）｜✅ `Multiple atlases` 清零｜✅ 创造标签页出现
  - ✅ **配方/数据包形态（R367 定稿）**：**原版 aerolith 地形（`sea_level=64`，含平整海面）+ 洞穴只在浮岛高度带**
    - ⚠ **不要再拆低层地面**！R363 那次 `min(gradient(104→120))` + `sea_level=-64` **已被用户否决并回滚**
      （后果：地牢/结构悬空、液体流成条；用户原话「效果甚至不如给海面开个大洞」）
    - carver：`tools\\fix_carvers_islands.py` —— 从 26.3 原版 jar 取**完整** carver 配置，
      只改 `y=[170,450]`（对齐岛带 176..220 / 320..447）+ `count` 改 `uniform(2,14)`。
      **⚠ 绝不能只写 `{"type":...}` 就完事** —— 会丢 `count`/`probability`/`thickness` 导致雕刻器空转
  - **一键启动：`启动浮岛世界.bat`** → `mods-stable`（**45 jar**，与 `watch\\mods` 完全一致）
  - ⚠ **`mods-full`（46 jar，含 `sky-villages`）是代理的暂存区，不要直接给用户用**；
    要给用户必须先复制进 `mods-stable` 并**独立 game-dir 进世界实测**
  - ⚠ **`launch.py --mods` 会同步改 `<game-dir>\\mods`** —— 实验一律用 `work\\run26\\stag1`
  - ⚠ **已知未做**：真浮岛（岛 2~5 格厚、无锥底）、矿脉（地面未拆所以原版矿带仍在，**可用**）、
    创造标签页无分区、Create 的 27 条加工类配方（`create:crushing` 等）、余下 8 个 1.21.x mod 与 40 个 NeoForge-only mod
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
