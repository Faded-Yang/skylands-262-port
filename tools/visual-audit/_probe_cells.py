# [port-repo] 原路径 scratch/vis/_probe_cells.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import icon_audit as ia
res = ia.analyze_image(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g300\game-vis1\shots\page2-0-0.png", annotate=False)
print("scale", res["gui_scale"], "left/top", res["left"], res["top"], "score", res["grid_score"])
for r in range(5):
    row = []
    for c in range(9):
        x = res["cells"][r*9+c]
        row.append(f"{x['slotfill']:.2f}/{x['std']:.0f}/{x['verdict'][:3]}")
    print("row", r, " | ".join(row))
print()
print("cells[36..44]:", [(i, res['cells'][i]['verdict'], res['cells'][i]['slotfill'], res['cells'][i]['std']) for i in range(36,45)])
