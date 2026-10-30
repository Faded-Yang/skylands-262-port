# [port-repo] 原路径 scratch/vis/_dbg.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import icon_audit as ia
im, arr = ia.load_rgb(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\scratch\vis\selftest\selftest_synthetic.png")
print("shape", arr.shape)
g = ia.detect_grid(arr)
print("grid", {k: (round(v,3) if isinstance(v,float) else v) for k,v in g.items()})
for idx in (4, 12, 25, 3, 0):
    r, c = divmod(idx, 9)
    rect = ia.cell_rect(g, c, r)
    info = ia.classify_cell(arr, rect, ia.DEFAULTS)
    print(idx, rect, info)
