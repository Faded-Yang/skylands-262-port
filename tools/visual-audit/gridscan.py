# [port-repo] 原路径 scratch/gridscan.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。
import sys, json
from PIL import Image
from collections import Counter

MAG = (255, 0, 255)
def is_mag(p, tol=40):
    return abs(p[0]-255) < tol and p[1] < tol and abs(p[2]-255) < tol

def grid_stats(path, origin=(366, 205), cell=36, cols=9, rows=5, inset=4):
    im = Image.open(path).convert("RGB")
    ox, oy = origin
    res = []
    for r in range(rows):
        for c in range(cols):
            x0 = ox + c*cell + inset; y0 = oy + r*cell + inset
            x1 = x0 + cell - 2*inset; y1 = y0 + cell - 2*inset
            if x1 > im.width or y1 > im.height: continue
            crop = im.crop((x0, y0, x1, y1))
            px = list(crop.getdata())
            n = len(px)
            mag = sum(1 for p in px if is_mag(p))
            dark = sum(1 for p in px if p[0] < 24 and p[1] < 24 and p[2] < 24)
            # "empty slot" = nearly uniform dark grey slot bg (about 55,55,55) or transparent-ish
            uniq = len(set(px))
            res.append(dict(r=r, c=c, mag=round(mag/n,3), dark=round(dark/n,3), uniq=uniq))
    return res

if __name__ == "__main__":
    for p in sys.argv[1:]:
        st = grid_stats(p)
        broken = [s for s in st if s["mag"] > 0.25]
        nonempty = [s for s in st if s["uniq"] > 6]
        print(p.split("\\")[-1], "cells=", len(st), "nonempty=", len(nonempty), "missing-ish=", len(broken),
              "sample=", [(s["r"], s["c"], s["mag"]) for s in broken[:6]])
