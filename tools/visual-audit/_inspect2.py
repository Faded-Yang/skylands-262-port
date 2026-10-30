# [port-repo] 原路径 scratch/vis/_inspect2.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。

from PIL import Image
from collections import Counter
p = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\refs\mc26.3\assets\minecraft\textures\gui\sprites\container\slot.png"
im = Image.open(p).convert("RGBA")
print("slot size", im.size)
c = Counter(im.getdata())
print("colors:", c.most_common(8))
for y in range(18):
    print("".join(f"{im.getpixel((x,y))[0]:02x}" for x in range(18)))
# creative tab background sprite
import glob, os
tabs = glob.glob(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\refs\mc26.3\assets\minecraft\textures\gui\container\creative_inventory\*.png")
print("creative sprites:", [os.path.basename(t) for t in tabs][:20])
for t in tabs[:3]:
    im2 = Image.open(t).convert("RGBA")
    print(os.path.basename(t), im2.size, Counter(im2.getdata()).most_common(4))
