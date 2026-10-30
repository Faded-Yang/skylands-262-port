# [port-repo] 原路径 scratch/vis/_probe_cell2.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import icon_audit as ia
import numpy as np
im, arr = ia.load_rgb(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g300\game-vis1\shots\page2-0-0.png")
g = ia.detect_grid(arr)
print("grid", {k:(round(v,3) if isinstance(v,float) else v) for k,v in g.items()})
for (c,r) in [(8,4),(7,4),(6,4),(0,4),(0,0)]:
    rect = ia.cell_rect(g, c, r)
    x0,y0,x1,y1 = rect
    S=(x1-x0)/18
    ix0=x0+int(round(S)); iy0=y0+int(round(S)); ix1=x1-int(round(S)); iy1=y1-int(round(S))
    icon = arr[iy0:iy1, ix0:ix1, :3]
    cols, counts = np.unique(icon.reshape(-1,3), axis=0, return_counts=True)
    top = np.argsort(-counts)[:3]
    print((c,r), "rect", rect, "S", round(S,2), "mean", icon.reshape(-1,3).mean(axis=0).round(1),
          "dominant", [(tuple(int(v) for v in cols[i]), int(counts[i])) for i in top])
    print("   cell center px", arr[(y0+y1)//2, (x0+x1)//2, :3], "top-left+2", arr[y0+2, x0+2, :3], "bottom-right-2", arr[y1-3, x1-3, :3])
