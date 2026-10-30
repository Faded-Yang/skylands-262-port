# [port-repo] 原路径 scratch/vis/_texcheck.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。

import zipfile, json, io
from pathlib import Path
from PIL import Image
from collections import Counter
MODS = Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\mods-stable")
jar = None
for j in MODS.glob("*create_connected*.jar"):
    jar = j
print("jar:", jar.name if jar else None)
z = zipfile.ZipFile(jar)
names = z.namelist()
for want in ["brass_gearbox", "magenta_fan_dyeing_catalyst"]:
    bs = [n for n in names if n.endswith("blockstates/%s.json" % want)]
    print("---", want, "blockstate:", bs)
    if not bs: continue
    st = json.loads(z.read(bs[0]))
    model = st.get("variants", {})
    print("  variants sample:", list(model.items())[:2])
    # 取第一个 model 路径 -> 模型 json -> textures
    mv = list(model.values())[0]
    if isinstance(mv, list): mv = mv[0]
    mp = mv.get("model")
    print("  model:", mp)
    mpath = "assets/%s/models/%s.json" % (mp.split(":")[0], mp.split(":",1)[1])
    if mpath in names:
        mj = json.loads(z.read(mpath))
        print("  textures:", mj.get("textures"))
        for k, v in (mj.get("textures") or {}).items():
            if v.startswith("#"): continue
            ns, path = v.split(":",1)
            tp = "assets/%s/textures/%s.png" % (ns, path)
            if tp in names:
                im = Image.open(io.BytesIO(z.read(tp))).convert("RGB")
                c = Counter(im.getdata())
                print("   ", k, v, im.size, "dominant:", c.most_common(3))
