# [port-repo] 原路径 scratch/vis/_final_report.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。

import json, os, sys
from collections import defaultdict
ROOT = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
sys.path.insert(0, os.path.join(ROOT, "scratch", "vis"))
import block_audit as ba

res = json.load(open(os.path.join(ROOT, "scratch/vis/blockaudit/all_results.json"), encoding="utf-8"))
val = json.load(open(os.path.join(ROOT, "scratch/vis/blockaudit/batch_validity.json"), encoding="utf-8"))
valid = set(val["valid"])
for r in res:
    r["batch_ok"] = os.path.basename(r["shot"]) in valid

by_ns = defaultdict(list)
for r in res: by_ns[r["ns"]].append(r)
order = [n for n in ba.NS_ORDER if n in by_ns] + [n for n in by_ns if n not in ba.NS_ORDER]

md = []
md.append("# 游戏内方块渲染审计（26.3，118 jar 交付包）")
md.append("")
md.append("## 结论（可信部分：批次里 3/4 角标块仍在校准位置上）")
md.append("")
md.append("| namespace | 可信批次已测 | MISSING(紫黑) | 备注 |")
md.append("|---|---|---|---|")
tot_ok = tot_miss = 0
for ns in order:
    rs = [r for r in by_ns[ns] if r["batch_ok"]]
    if not rs: continue
    m = [r for r in rs if r["verdict"] == "MISSING"]
    tot_ok += len(rs); tot_miss += len(m)
    md.append("| %s | %d | %d | |" % (ns, len(rs), len(m)))
md.append("| **合计** | **%d** | **%d** | |" % (tot_ok, tot_miss))
md.append("")
md.append("## 不可信部分（相机漂移，网格对不上，数字作废）")
md.append("")
md.append("| namespace | 作废批次 | 已测（作废） |")
md.append("|---|---|---|")
for ns in order:
    rs = [r for r in by_ns[ns] if not r["batch_ok"]]
    if not rs: continue
    shots = sorted({os.path.basename(r["shot"]) for r in rs})
    md.append("| %s | %d | %d |" % (ns, len(shots), len(rs)))
md.append("")
md.append("原因：本实例与 Lead 共用，审计中途玩家被 tp/转向，固定单应标定失效；")
md.append("shots/*-b*.png 里能直接看到平台已旋转出画面。判定器本身已用「注入已知品红棋盘」正控验证（3/3 命中、0 误报），")
md.append("问题只在相机漂移。")
md.append("")
md.append("## 运行中出现的 2 个 MISSING 均为误报（已核实）")
md.append("")
md.append("1. create_connected:magenta_fan_dyeing_catalyst —— 模型 textures = minecraft:block/magenta_concrete_powder，本来就是品红，正常。")
md.append("2. create_connected:brass_gearbox —— 真实纹理是黄铜色(114,71,49 / 158,105,71 / 255,235,140)，")
md.append("   截图那一格实际是染色催化剂，属标定失效的连带误报。")
md.append("")
md.append("## 复跑方法（约 2 分钟，必须独占实例）")
md.append("")
md.append("1. python scratch/vis/block_audit.py --setup")
md.append("2. python scratch/vis/block_audit.py --calibrate-only  （cell_px 应≈37.7 且 x/z 一致）")
md.append("3. python scratch/vis/block_audit.py  （9 个 namespace，2119 方块；每批 1.4-2s）")
md.append("4. python scratch/vis/audit_report.py")
md.append("5. 期间不要动该实例；相机一动就要回第 2 步重标。")
md.append("")
md.append("## 批次截图")
md.append("")
for ns in order:
    shots = sorted({os.path.basename(r["shot"]) for r in by_ns[ns]})
    md.append("- %s（%d）：%s" % (ns, len(shots), "、".join(shots[:8]) + (" ..." if len(shots) > 8 else "")))
out = os.path.join(ROOT, "work/run26/port/g300/game-vis1/shots/BLOCK-AUDIT.md")
open(out, "w", encoding="utf-8").write("\n".join(md) + "\n")
print("wrote", out)
print("trustworthy blocks:", tot_ok, "missing:", tot_miss)
