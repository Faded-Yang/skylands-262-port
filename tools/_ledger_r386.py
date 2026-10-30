#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R386：escalated 打通（66 jar）+ 「542 不可信」证实 + 两个流水线缺口 + 三个数据层硬坑。"""
import datetime
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
HOT = os.path.join(P, "AGENTS.md")
COLD = os.path.join(P, "docs", "SOLVED-FAMILIES.md")
h = open(HOT, encoding="utf-8", errors="replace").read()
shutil.copy2(HOT, HOT + ".bak-r386-" + datetime.datetime.now().strftime("%H%M%S"))

ROWS = [
 "| 🎉 **【R386 `escalated` 打通，mods-stable 66 jar】** `Create: Escalated 1.2.1`（1.20.1 Fabric）：**javac 0 错 / 56 class**；"
 "`WORLD_OK 36.2s`（`entity id 13`，无 `Registry loading errors`）；promote 后 66 jar `TITLE_SCREEN_OK 25.3s`。"
 "降级清单一长串（datagen / Ponder / architectury 配置 / **客户端 BER + Flywheel Visual ⇒ 扶梯踏步动画没了，方块仍静态渲染** / "
 "5 个 advancement / SAFE_NBT / setMaxUpStep / 6 张 `minecraft:air` 手栏杆战利品表 / 2 个配方换材料），详见 `docs/port-1201.md` §1.4 | —— | R386 |",

 "| ★★★★★ **【R386 「542 不可信」被证实：之前的 1.20.1 错误数是用坏流水线测的】** `escalated` 的真实错误轨迹："
 "**1268（未换 Create 包名）→ 353（+`_crate_pkg`）→ 107（删 datagen/ponder/config/client-renderer）→ 33 → 1 → 0**。"
 "**542 的大头是** ① `com.simibubi.create` **完全没换** ② 内类 `$` vs `.` 的垃圾类名级联。"
 "**⇒ 以后看到旧轮次的错误数（542/1869）不要当成工作量依据，必须用 g8 流水线重测** | —— | R386 |",

 "| ★★★★ **【R386 g8 流水线的两个缺口（已补，新增脚本别覆盖）】** ① **`_rewrite26.py` 不做 Create 包名迁移** ⇒ 每个 Create 附属必须再跑 **`g8/_crate_pkg.py`**"
 "（**按 create jar 的类索引 resolve**，因为 `net.createmod.catnip` 的 common/client 划分**不能按名字推**）；"
 "② **`@ExpectPlatform` 桥接要单独一个 pass**：CFR 把参数名丢成 `void varK_N;`（K = 参数下标）⇒ 新写 **`g8/_ep_bridge.py`**（copycats 一次修 13 个） | —— | R386 |",

 "| ⚠ **【R386 `copycats` 未通（1342→1294 错）：客户端模型系统是它的核心，降级就没意义】** 314 java，语法层已清零。三类卡点："
 "① registrate 垫片 **builder 泛型不符**（66 个 `wrong number of type arguments` + 43 个 `customItemModel`）；"
 "② **客户端模型系统**（`CopycatModelFabric`/`UniversalMeshEmitter`/`CopycatRenderContextFabric` 直接拼 quad，26.3 renderpearl 全换）"
 "⇒ **降级等于 mod 失去意义**；③ config（architectury）+ mixin（refmap 是 1.20.1）+ JEI/EMI。"
 "**下轮顺序**：先修通用族（~70 条）→ 删 config/mixin/JEI/EMI/datagen → 最后单开一轮做模型系统 | —— | R386 |",

 "| ★★★★★ **【R386 三个 26.3 数据层硬坑（任何一个都会让「进世界」直接失败）】** "
 "① 战利品表里 `\"name\": \"minecraft:air\"` → **`Item must not be minecraft:air`**；"
 "② advancement 引用**已删的 `trigger_type`** → **整个 advancement 注册表失败**；"
 "③ 配方引用**不存在的 item/tag**（含 `minecraft:chain`→`iron_chain` 改名）→ **整个 recipe 注册表失败**。"
 "**⇒ 删数据时要「要么全删干净、要么全修」，不能留半截引用** | —— | R386 |",
]

anchor = "| 阶段A 生物刷新（现成 mod） |"
h = h.replace(anchor, "\n".join(ROWS) + "\n" + anchor)
h = h.replace("（**65 jar**，进世界 `WORLD_OK` / `entity id 5`", "（**66 jar**，进世界 `WORLD_OK`")
h = h.replace("剩 5 个 1.20.1 目标（`createaddition`/`copycats`/`escalated`/`create-jetpack`/`railways-navigator`，**已验证 1.20.1 能通**）",
              "1.20.1 目标已通 3 个（`interiors`/`create-framed`/**`escalated`**），剩 `railways-navigator`/`createaddition`；`copycats` 卡在客户端模型系统")

lines = h.split("\n")
st = next(k for k, l in enumerate(lines) if l.strip().startswith("| 族 | 结论 |"))
en = st
while en < len(lines) and lines[en].startswith("|"):
    en += 1
rows = lines[st + 2:en]
KEEP = 9
moved, kept = rows[:-KEEP], rows[-KEEP:]
with open(COLD, "a", encoding="utf-8", newline="\n") as f:
    f.write("\n\n## 搬出索引行（t27）\n\n| 族 | 结论 | 轮次 |\n|---|---|---|\n")
    for r in moved:
        f.write(r + "\n")
h2 = "\n".join(lines[:st + 2] + kept + lines[en:])
open(HOT, "w", encoding="utf-8", newline="\n").write(h2)

tot = sum(os.path.getsize(f) for f in [
    os.path.expanduser("~/.dsh/AGENTS.md"),
    r"C:\Users\95959\OneDrive\Desktop\Work\AGENTS.md",
    HOT,
])
print("hot %d B; 注入合计 %d B %s" % (len(h2.encode("utf-8")), tot, "OK" if tot <= 65536 else "OVER"))
