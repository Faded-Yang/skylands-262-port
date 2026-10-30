# [port-repo] 原路径 scratch/vis/_detector_selftest.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。

import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import block_audit as ba
from PIL import Image
H, info = ba.load_H(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\scratch\vis\blockaudit\homography.json")
src = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g300\game-vis1\shots\interiors-b00.png"
out = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\scratch\vis\blockaudit\detector-selftest.png"
im = Image.open(src).convert("RGB")
targets = [(0,0), (4,2), (-4,4)]
for (gx,gz) in targets:
    poly = [ba.apply_h(H, gx+0.05, gz+0.05), ba.apply_h(H, gx+0.95, gz+0.05),
            ba.apply_h(H, gx+0.95, gz+0.95), ba.apply_h(H, gx+0.05, gz+0.95)]
    xs=[p[0] for p in poly]; ys=[p[1] for p in poly]
    x0,y0,x1,y1 = int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))
    for yy in range(max(0,y0), min(im.height,y1)):
        for xx in range(max(0,x0), min(im.width,x1)):
            on = ((xx-x0)//6 + (yy-y0)//6) % 2 == 0
            im.putpixel((xx,yy), (255,0,255) if on else (0,0,0))
im.save(out)
im2 = Image.open(out).convert("RGB")
cells = [(x,z) for z in range(ba.GRID_Z0, ba.GRID_Z1+1) for x in range(ba.GRID_X0, ba.GRID_X1+1)]
flagged=[]; stats={}
for (gx,gz) in cells:
    st = ba.cell_stats(im2, H, gx, gz)
    stats[(gx,gz)] = st["magenta"]
    if st["magenta"] >= 0.05: flagged.append((gx,gz,round(st["magenta"],3)))
exp=set(targets); got={(a,b) for a,b,_ in flagged}
print("targets:", targets); print("flagged:", flagged)
print("PASS" if got==exp else "FAIL", "| extra:", got-exp, "| missed:", exp-got)
print("max magenta on non-target:", round(max(v for k,v in stats.items() if k not in exp),4))
