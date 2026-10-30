#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性：把 R367（1.21.x 移植结论 + 地形回滚 + carver 修复）追加进热层台账。"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
ARC = os.path.join(P, "docs", "SOLVED-FAMILIES.md")
h = open(HOT, encoding="utf-8", errors="replace").read()
b0 = len(h.encode("utf-8"))
shutil.copy2(HOT, HOT + ".bak-r367-" + datetime.datetime.now().strftime("%H%M%S"))

ROWS = [
    "| ★★★★★ **【R367 1.21.x→26.3 的第一道门是「intermediary→官方名」重映射，不是 API】** Modrinth 的 1.21.x Fabric jar "
    "全用 `class_2338` 这类 **intermediary** 名，而 **26.3 完全不混淆**（`core.BlockPos`）且 **loader 在 26.3 打 `Mappings not present!` = 运行期不重映射** "
    "⇒ **首个类加载就 `NoClassDefFoundError: class_7923`**。这也是「F 类 7 个只活 2 个」的真因：活下来的 `explorify`/`medieval-buildings` 都是 **0 class 的纯数据 mod**。"
    "**tiny-remapper 不够用**（类名能改，但**描述符里带 MC 类型的方法/字段名一律不改**）⇒ 自写 `tools\\remap_intermediary.py`（含继承链 + 改名表叠加），"
    "把 `when-dungeons-arise` 从 B91/C19 压到 **B1/C0/A0**。**另一个静默坑：`method_info.descriptor_index` 不走 NameAndType 表**，漏改就报 `ResourceLocation` 崩溃 | —— | R367 |",
    "| ★★★★ **【R367 26.3 数据包 schema 又两条（不在旧事实表里）】** ① **blockstate JSON**：`{\"Name\":..,\"Properties\":..}` → **`{\"id\":..,\"properties\":..}`**；"
    "② **`placement_modifier_type` 的 `random_offset` 被删**、并入 `offset`，字段变 **`x`/`y`/`z`** 三个 IntProvider（不是 `xz`/`y`）。"
    "③ **26.3 自带数据自动升级器**，但**只管 `worldgen/structure` 那层**（日志 `Upgrading pre-26.3 data from 'imst' on the fly`），`processor_list` 的 blockstate 与 `placement` 的 random_offset **它不转**。"
    "工具 `tools\\convert_121_data.py` | —— | R367 |",
    "| ⚠⚠⚠ **【R367 `launch.py --mods` 会改用户的运行目录】** `--mods <dir>` 是权威来源，会**同步进 `<game-dir>\\mods` 并删多余 jar**。"
    "**用真实 game-dir（`work\\run26\\watch`）做实验 = 直接改用户环境**（用户两次「数据包错误」截图就是这么来的：从 mods-full 撤了 jar，`watch\\mods` 里还留着）。"
    "**⇒ 所有实验必须用独立 game-dir（`work\\run26\\stag1`）** | —— | R367 |",
    "| ✅ **【R367 1.21.x 移植结果：1 成 / 3 只到标题 / 5 败】** ✅ **`sky-villages`**（唯一完整可用，进世界实测 OK）；"
    "⚠ `immersive-structures` / `strayed-fates-forsaken`（卡 `configured_feature` 字段 schema）、`when-dungeons-arise`（代码全修好，卡 4 个自定义**附魔** JSON 的 `No key type`）；"
    "❌ `cultural-delights`（`class_2248`，疑残留旧 jar 待复测）/ `ends-delight` / `natures-spirit`（A94/B38/C53/D83 未验证）/ `dragonlib`（需先剥 JIJ）；"
    "☠ `lodestonelib` **放弃**（`porting_lib` 只到 1.20.1）。**9 个里只有 1 个是结构性死路，其余全是数据 schema**。详见 `docs\\port-1.21x.md` | —— | R367 |",
    "| ⚠⚠ **【R367 地形回滚：拆地面是错的，已撤销】** 用户实测反馈：「没了海洋 ⇒ 地牢/结构全部悬空；液体没承托流成一条条；**效果甚至不如给海面开个大洞**」。"
    "⇒ **撤销 `min(原, gradient(104→120))` 与 `sea_level=-64`**，恢复 `_off_aerolith-1.3.2-26.3.zip`（`sea_level=64`、`final_density=minecraft:add` 未切地）。"
    "**正确形态 = 原版地形（含平整海面）+ 洞穴只在浮岛高度带**。工具 `tools\\restore_sea_terrain.py` | —— | R367 |",
    "| ★★★★★ **【R367 洞穴不生成的真正原因（两层）】** 用户实测「还没遇到浮岛内洞穴」。① 我把 carver 的 `y` 下界设成 **140**，而浮岛实测在中层 176..220 / 高层 320..447 ⇒ "
    "**下界落在岛下方的虚空**，且原版 `count` 是 **`very_biased_to_bottom`**（强烈偏底部）⇒ 绝大多数尝试打在空气里（空气不是 `#overworld_carver_replaceables`，挖不动）；"
    "② **更致命**：源包没有 carver 文件，我现编的 `{\"type\":\"minecraft:cave\"}` **丢了 `count`/`probability`/`thickness`/`replaceable`** ⇒ 雕刻器等于关闭。"
    "**修法 `tools\\fix_carvers_islands.py`**：从 **26.3 原版 jar** 取完整 carver，只改 `y=[170,450]` + `count` 改 `uniform(2,14)`，其余原样 | —— | R367 |",
]

anchor = "| 阶段A 生物刷新（现成 mod） |"
if anchor in h:
    h = h.replace(anchor, "\n".join(ROWS) + "\n" + anchor)
open(HOT, "w", encoding="utf-8", newline="\n").write(h)

# 体积控制：搬走最旧行
lines = h.split("\n")
st = next(k for k, l in enumerate(lines) if l.strip().startswith("| 族 | 结论 |"))
en = st
while en < len(lines) and lines[en].startswith("|"):
    en += 1
rows = lines[st + 2:en]
KEEP = 10
moved, kept = rows[:-KEEP], rows[-KEEP:]
with open(ARC, "a", encoding="utf-8", newline="\n") as f:
    f.write("\n\n## 搬出索引行（t8）\n\n| 族 | 结论 | 轮次 |\n|---|---|---|\n")
    for r in moved:
        f.write(r + "\n")
h2 = "\n".join(lines[:st + 2] + kept + lines[en:])
open(HOT, "w", encoding="utf-8", newline="\n").write(h2)

tot = sum(os.path.getsize(f) for f in [
    os.path.expanduser("~/.dsh/AGENTS.md"),
    r"C:\Users\95959\OneDrive\Desktop\Work\AGENTS.md",
    HOT,
])
print("moved %d; hot %d -> %d B; total %d B %s"
      % (len(moved), b0, len(h2.encode("utf-8")), tot, "OK" if tot <= 40960 else "OVER"))
