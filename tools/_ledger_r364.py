#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性：把 R364 的结论追加进热层台账。用文件方式避免内联引号/编码问题。"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
h = open(HOT, encoding="utf-8", errors="replace").read()
b0 = len(h.encode("utf-8"))
shutil.copy2(HOT, HOT + ".bak-r364-" + datetime.datetime.now().strftime("%H%M%S"))

ROWS = [
    "| 🎉🎉 **【R364 全量移植可行性的硬数据】** 用 `tools\\check_263_availability.py` 逐个查 Modrinth"
    "（按 mrpack 的 sha1 反查 project）：原包 **107 mod → A 有 26.3 Fabric 构建 33 / B 只有 26.3 NeoForge 4 / D 无 Fabric 70**。"
    "**A 类全在性能+UI+地图+结构**（sodium/iris/lithium/ferritecore/ImmediatelyFast/jei/Jade/Controlling/IPN/MouseTweaks/"
    "AppleSkin/BetterF3/Waystones/Xaero/Towns&Towers/Structory/Geophilic/**lithostitched** 等）。"
    "**D 类 70 个全是 Create 附属**（NeoForge 专属，上游无 Fabric 版）。清单 `notes\\avail-263.md` | —— | R364 |",

    "| ✅ **【R364 43 个 mod 联合启动通过】** `tools\\fetch_263_mods.py` 下载 33 个 A 类（0 失败）+ 核心 8 个 + 依赖 3 个"
    "（`shogi` / `fabric-language-kotlin` / `waystones`，用新工具 `tools\\fetch_dep.py`）⇒ `work\\run26\\mods-full` **43 jar**，"
    "`RESULT: TITLE_SCREEN_OK` **35.0s**。**一键启动 `启动浮岛世界.bat` 已指向 `mods-full`**，且 quickPlay 改成 `=` 形式 | —— | R364 |",

    "| ★★★★ **【R364 依赖坑：Fabric 化的传递依赖要换库】** `Waystones` 需要 **`shogi`**（有 `26.3.0.3+fabric-26.3`）；"
    "`InventoryProfilesNext` / `libIPN` 需要 **`fabric-language-kotlin`**（原包 NeoForge 用 `kotlinforforge`，Fabric 上要换成 FLK ≥1.13.10+kotlin.2.3.20）。"
    "**Modrinth 按 slug 查版本首次请求容易超时，会误判成“无 26.3”** ⇒ 用 `tools\\fetch_dep.py` 重试，别凭一次查询下结论 | —— | R364 |",

    "| ★★★★★ **【R364 真浮岛必须换密度式】** 现在岛的**中位厚度只有 2~5 格且无锥底**：密度式 `-0.6 ± noise(y_scale=3)` "
    "让正负**逐格翻转**，只能长毛边（拆地面后才暴露，不是 cut 造成的）。且地面一拆，**原版矿带全落虚空 ⇒ 实际没有矿**。"
    "**批准方案**：`final_density = min(islandMask2D(x,z), coneProfile(y))` + 岛内叠 3D 噪声，并把 ore 的 `height_range` 抬到岛带（y≈190..230）。"
    "验收指标：厚度中位 ≥12 格、≥6 种矿、y∈[-64,180] 空气 ≥99% | —— | R364 |",

    "| ⚠ **【R364 地形两个新坑】** ① `generate-structures=false` 会让**服务端初始化直接崩**（`Failed to initialize server`）"
    "⇒ 想去掉结构 beardifier 补的地形墩，要用 datapack **清空 structure_set**，别关开关；"
    "② **`quickPlaySingleplayer` 在 26.3 是 `withOptionalArg()`，空格分隔的世界名不生效**，必须 `--quickPlaySingleplayer=<world>` | —— | R364 |",
]

anchor = "| 阶段A 生物刷新（现成 mod） |"
if anchor in h:
    h = h.replace(anchor, "\n".join(ROWS) + "\n" + anchor)
else:
    print("★ anchor 未找到，追加到文件末尾")
    h += "\n" + "\n".join(ROWS) + "\n"

open(HOT, "w", encoding="utf-8", newline="\n").write(h)
tot = sum(os.path.getsize(f) for f in [
    os.path.expanduser("~/.dsh/AGENTS.md"),
    r"C:\Users\95959\OneDrive\Desktop\Work\AGENTS.md",
    HOT,
])
print("hot %d -> %d B; total %d B %s" % (b0, len(h.encode("utf-8")), tot, "OK" if tot <= 40960 else "OVER"))
