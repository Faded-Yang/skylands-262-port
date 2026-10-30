# [port-repo] 原路径 scratch/vis/_probe_grid.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。

from PIL import Image
import numpy as np
im = Image.open(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g300\game-vis1\shots\page2-0-0.png").convert("RGB")
a = np.asarray(im).astype(int)
def runs(vals, mask):
    out=[]; s=None
    for i,m in enumerate(mask):
        if m and s is None: s=i
        elif not m and s is not None: out.append((s,i-1)); s=None
    if s is not None: out.append((s,len(mask)-1))
    return out
# 水平扫描：找 y=230 处 #373737 / #FFFFFF 的竖线
row = a[230]
dark = np.all(np.abs(row-55)<=3, axis=1)
light = np.all(np.abs(row-255)<=3, axis=1)
print("y=230 dark x-runs:", runs(row, dark)[:30])
print("y=230 light x-runs:", runs(row, light)[:30])
# 垂直扫描 x=400
col = a[:,400]
darkv = np.all(np.abs(col-55)<=3, axis=1)
lightv = np.all(np.abs(col-255)<=3, axis=1)
print("x=400 dark y-runs:", runs(col, darkv)[:30])
# 找面板整体：列上 #373737 出现的频率
print("row 207 unique:", np.unique(a[207, 360:860].reshape(-1,3), axis=0)[:6])
