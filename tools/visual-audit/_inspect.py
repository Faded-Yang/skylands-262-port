# [port-repo] 原路径 scratch/vis/_inspect.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。

import sys, os, glob
from PIL import Image
import PIL
print("pillow", PIL.__version__)
base = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\refs\mc26.3\assets\minecraft\textures"
cands = glob.glob(os.path.join(base, "**", "missingno.png"), recursive=True)
print("missingno:", cands)
for c in cands:
    im = Image.open(c).convert("RGBA")
    print("size", im.size)
    px = list(im.getdata())
    from collections import Counter
    print(Counter(px).most_common(6))
    # print first 16x16 as characters
    w,h = im.size
    for y in range(min(h,16)):
        row = ""
        for x in range(min(w,16)):
            r,g,b,a = im.getpixel((x,y))
            row += "M" if (r>200 and g<60 and b>200) else ("K" if (r<40 and g<40 and b<40) else ".")
        print(row)
slots = glob.glob(os.path.join(base, "gui", "sprites", "container", "slot*.png"))
print("slot sprites:", [os.path.basename(s) for s in slots])
for s in slots[:2]:
    im = Image.open(s).convert("RGBA")
    print(os.path.basename(s), im.size, list(im.getdata())[:3])
