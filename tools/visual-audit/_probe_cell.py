# [port-repo] 原路径 scratch/vis/_probe_cell.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。

from PIL import Image
import numpy as np
im = Image.open(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g300\game-vis1\shots\page2-0-0.png").convert("RGB")
a = np.asarray(im).astype(int)
print("img", a.shape)
# 网格：scale3, left=115, top=51 -> 格子 x0=(115+9+18c)*3, y0=(51+18+18r)*3
def cell(c,r):
    x0=(115+9+18*c)*3; y0=(51+18+18*r)*3
    return a[y0+3:y0+54-3, x0+3:x0+54-3]
for (c,r) in [(0,0),(3,4),(7,4),(8,4)]:
    ic = cell(c,r)
    cols, counts = np.unique(ic.reshape(-1,3), axis=0, return_counts=True)
    top = np.argsort(-counts)[:3]
    print((c,r), "dominant:", [(tuple(cols[i]), int(counts[i])) for i in top], "std", round(float(ic.std()),1))
