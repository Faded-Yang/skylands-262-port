# [port-repo] 原路径 scratch/flatdup.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。

import zipfile, json, re
from pathlib import Path
from collections import defaultdict

MODS = Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\mods-stable")
VAN = Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\refs\mc26.3\assets")
res = {}; zips = {}
for j in sorted(MODS.glob("*.jar")):
    try: z = zipfile.ZipFile(j)
    except Exception: continue
    zips[j.name]=z
    for n in z.namelist():
        if n.startswith("assets/"): res.setdefault(n, j.name)
van=set()
for p in VAN.rglob("*"):
    if p.is_file(): van.add(str(p.relative_to(VAN.parent)).replace("\\","/"))
def load(p):
    if p in res: data=zips[res[p]].read(p)
    elif p in van: data=(VAN.parent/p).read_bytes()
    else: return None
    try: return json.loads(data)
    except Exception: return False
def split(r): return r.split(":",1) if ":" in r else ("minecraft", r)
def collect_refs(node,out):
    if node is None: return
    if isinstance(node,str): out.append(node); return
    if isinstance(node,list):
        for x in node: collect_refs(x,out); 
        return
    if isinstance(node,dict):
        t=node.get("type","minecraft:model")
        if t in ("minecraft:model","model"):
            collect_refs(node.get("model"),out)
            if isinstance(node.get("base"),str): out.append(node["base"])
        else:
            for k,v in node.items():
                if k in ("type","property","index","scale","threshold","when","value","amount"): continue
                collect_refs(v,out)

def flat_icon(mid):
    """if model chain reaches builtin/generated or item/generated with layer0, return (layer0, parentset)"""
    chain=[]; seen=set(); cur=mid; parents=[]
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
    is_generated = ("generated" in top) or any("generated" in p for p in parents)
    if not is_generated: return None
    v = slots.get("layer0")
    if isinstance(v,str) and not v.startswith("#"): return v
    return None

users = defaultdict(list)
for p, jn in sorted(res.items()):
    m = re.match(r"assets/([^/]+)/items/(.+)\.json$", p)
    if not m: continue
    ns, path = m.group(1), m.group(2)
    d = load(p)
    if not isinstance(d, dict): continue
    refs=[]
    if "model" in d: collect_refs(d["model"], refs)
    elif "parent" in d: refs=[f"{ns}:item/{path}"]
    for mid in refs:
        t = flat_icon(mid)
        if t: users[t].append(f"{ns}:{path}")

print("items whose flat icon texture is shared by >=3 items:")
for tex, u in sorted(users.items(), key=lambda kv:-len(kv[1])):
    if len(u) < 3: break
    print(f"{len(u):4d}  {tex}")
    print(f"        e.g. {u[:6]}")
