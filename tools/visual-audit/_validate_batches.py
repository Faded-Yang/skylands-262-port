# [port-repo] 原路径 scratch/vis/_validate_batches.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。

import sys, os, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import block_audit as ba
from PIL import Image
import numpy as np

H, info = ba.load_H(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\scratch\vis\blockaudit\homography.json")
# 标记块颜色（顶面）：红/蓝/绿/黄
def marker_ok(a, u, v):
    ui, vi = int(round(u)), int(round(v))
    if not (0 <= ui < a.shape[1] and 0 <= vi < a.shape[0]): return False
    win = a[max(0,vi-6):vi+7, max(0,ui-6):ui+7].reshape(-1,3).astype(int)
    r,g,b = win[:,0], win[:,1], win[:,2]
    sat = (np.maximum(np.maximum(r,g),b) - np.minimum(np.minimum(r,g),b))
    return float((sat > 60).mean()) > 0.5

shots = sorted(glob.glob(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g300\game-vis1\shots\*-b*.png"))
shots = [s for s in shots if "audit" not in os.path.basename(s)]
valid, invalid = [], []
for s in shots:
    a = np.asarray(Image.open(s).convert("RGB"))
    ok = sum(marker_ok(a, *ba.apply_h(H, x+0.5, z+0.5)) for (x,z),_ in ba.MARKERS)
    (valid if ok >= 3 else invalid).append((os.path.basename(s), ok))
print("total shots:", len(shots), "valid:", len(valid), "invalid:", len(invalid))
print("first invalid:", invalid[:8])
# 按 namespace 统计
from collections import defaultdict
d = defaultdict(lambda: [0,0])
for n, ok in valid + invalid:
    ns = n.split("-b")[0]
    d[ns][0 if (n, ok) in valid else 1] += 1
for ns in sorted(d):
    print(f"  {ns}: valid={d[ns][0]} invalid={d[ns][1]}")
json.dump({"valid": [n for n,_ in valid], "invalid": [n for n,_ in invalid]},
          open(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\scratch\vis\blockaudit\batch_validity.json","w",encoding="utf-8"), indent=1)
