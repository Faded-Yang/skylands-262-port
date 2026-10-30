# [port-repo] 原路径 scratch/vis/_texcheck2.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。

import zipfile, json, io
from pathlib import Path
from PIL import Image
from collections import Counter
MODS = Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\mods-stable")
target = "assets/create_connected/blockstates/brass_gearbox.json"
found = None
for j in sorted(MODS.glob("*.jar")):
    try: z = zipfile.ZipFile(j)
    except Exception: continue
    if target in z.namelist():
        found = (j, z); break
print("jar:", found[0].name if found else None)
j, z = found
names = z.namelist()
for want in ["brass_gearbox", "magenta_fan_dyeing_catalyst"]:
    bs = "assets/create_connected/blockstates/%s.json" % want
    st = json.loads(z.read(bs))
    variants = st.get("variants", {})
    mv = list(variants.values())[0]
    if isinstance(mv, list): mv = mv[0]
    mp = mv.get("model")
    mpath = "assets/%s/models/%s.json" % (mp.split(":")[0], mp.split(":", 1)[1])
    mj = json.loads(z.read(mpath)) if mpath in names else {}
    texs = mj.get("textures", {})
    print("---", want, "model", mp, "textures", texs)
    for k, v in texs.items():
        if str(v).startswith("#"): continue
        ns, path = v.split(":", 1)
        tp = "assets/%s/textures/%s.png" % (ns, path)
        if tp in names:
            im = Image.open(io.BytesIO(z.read(tp))).convert("RGB")
            print("   ", k, v, im.size, Counter(im.getdata()).most_common(3))
