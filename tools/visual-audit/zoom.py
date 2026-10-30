# [port-repo] 原路径 scratch/vis/zoom.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。
import sys
from PIL import Image
import numpy as np
src, out, x0, y0, x1, y1, scale = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:7]), int(sys.argv[7]) if len(sys.argv) > 7 else 4
im = Image.open(src).convert("RGBA")
c = im.crop((x0, y0, x1, y1)).resize(((x1-x0)*scale, (y1-y0)*scale), Image.NEAREST)
c.save(out)
a = np.asarray(im.crop((x0,y0,x1,y1)).convert("RGB")).astype(int)
r,g,b = a[...,0],a[...,1],a[...,2]
mag = ((r>=180)&(b>=180)&(g<=90)).mean()
blk = ((r<=30)&(g<=30)&(b<=30)).mean()
print(f"crop {x0},{y0},{x1},{y1} size={x1-x0}x{y1-y0} magenta={mag:.3f} black={blk:.3f} saved {out}")
