# [port-repo] 原路径 scratch/iconscan.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。

import zipfile, json, re
from pathlib import Path
from collections import defaultdict
MODS = Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\mods-stable")
VAN = Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\refs\mc26.3\assets")
res={}; zips={}
for j in sorted(MODS.glob("*.jar")):
    try: z=zipfile.ZipFile(j)
    except Exception: continue
    zips[j.name]=z
    for n in z.namelist():
        if n.startswith("assets/"): res.setdefault(n, j.name)
van=set()
for p in VAN.rglob("*"):
    if p.is_file(): van.add(str(p.relative_to(VAN.parent)).replace("\\","/"))
def exists(p): return p in res or p in van
def load(p):
    if p in res: data=zips[res[p]].read(p)
    elif p in van: data=(VAN.parent/p).read_bytes()
    else: return None
    try: return json.loads(data)
    except Exception: return False
def split(r): return r.split(":",1) if ":" in r else ("minecraft", r)

def icon_texture(mid):
    chain=[]; cur=mid; seen=set(); parents=[]
    while cur and cur not in seen and len(chain)<30:
        seen.add(cur); parents.append(cur)
        if re.match(r"^(minecraft:)?builtin/", cur): break
        ns,p=split(cur)
        obj=load(f"assets/{ns}/models/{p}.json")
        if obj is None or obj is False: return None
        chain.append(obj); cur=obj.get("parent")
    slots={}
    for m in chain:
        if isinstance(m.get("textures"),dict): slots.update(m["textures"])
    top = parents[-1] if parents else ""
    if "generated" not in top and not any("generated" in p for p in parents): return None
    v=slots.get("layer0")
    if not isinstance(v,str) or v.startswith("#"): return None
    return v

rows=[]
for p, jn in sorted(res.items()):
    m = re.match(r"assets/([^/]+)/items/(.+)\.json$", p)
    if not m: continue
    ns, path = m.group(1), m.group(2)
    d = load(p)
    if not isinstance(d, dict): continue
    mod = d.get("model")
    mid = None
    if isinstance(mod, dict):
        t = mod.get("type")
        if t in ("minecraft:model", None): mid = mod.get("model")
    if not isinstance(mid, str): continue
    tex = icon_texture(mid)
    if not tex: continue
    tns, tpath = split(tex)
    expected = f"item/{path}"
    ok = (tns == ns and tpath == expected) or (tns == "minecraft" and tpath == expected)
    if ok: continue
    # is there a proper texture for this item?
    cand = f"assets/{ns}/textures/item/{path}.png"
    rows.append(dict(ns=ns, id=f"{ns}:{path}", model=mid, tex=tex, proper_exists=exists(cand), cand=cand, jar=jn))

print("flat items whose icon texture != item path:", len(rows))
by_ns = defaultdict(list)
for r in rows: by_ns[r["ns"]].append(r)
for ns, lst in sorted(by_ns.items(), key=lambda kv:-len(kv[1])):
    fixable = sum(1 for r in lst if r["proper_exists"])
    print(f"{ns:26s} {len(lst):4d}  fixable(own png exists)={fixable}")
print()
for ns in ["sophisticatedbackpacks","sophisticatedstorage","tfmg"]:
    lst = by_ns.get(ns, [])
    for r in lst[:8]:
        print(ns, "|", r["id"], "->", r["tex"], "| proper png:", r["proper_exists"])
Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\scratch\iconfix_list.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
print("written iconfix_list.json", len(rows))
