# audit_data_refs.py -- 静态审计 live mods 的 data 引用 vs assets 注册 id
# 用法: python tools/audit_data_refs.py（输出 work/audit_refs_raw3.json，报告 docs/audit-data-refs.md）
import io, json, os, re, sys, zipfile, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
root=r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
stable=(sys.argv[1] if len(sys.argv)>1 else os.path.join(root,"work","run26","mods-stable")); mcjar=r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar"
idpat=re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")
item_ids=set(); block_ids=set(); tags=set(); tags_by_type=set()
def scan_zip(z):
    for n in z.namelist():
        ps=n.split("/")
        if len(ps)>=4 and ps[0]=="assets" and ps[2] in ("items","blockstates") and n.endswith(".json"):
            (item_ids if ps[2]=="items" else block_ids).add(ps[1]+":"+os.path.basename(n)[:-5])
        if n.startswith("data/") and "/tags/" in n and n.endswith(".json") and len(ps)>=5 and ps[2]=="tags":
            typ=ps[3]; path=ps[1]+":"+"/".join(ps[4:])[:-5]; tags.add(path); tags_by_type.add((typ,path))
        if n.endswith(".jar"):
            try:
                with zipfile.ZipFile(io.BytesIO(z.read(n))) as zz: scan_zip(zz)
            except Exception: pass
jars=[os.path.join(stable,f) for f in sorted(os.listdir(stable)) if f.endswith(".jar")]
for p in jars:
    try:
        with zipfile.ZipFile(p) as z: scan_zip(z)
    except Exception as e: print("ERR",p,e)
with zipfile.ZipFile(mcjar) as z: scan_zip(z)
print("items",len(item_ids),"blocks",len(block_ids),"tags",len(tags))
def isid(s): return isinstance(s,str) and idpat.match(s) is not None
refs=[]; tagrefs=[]
def add(kind,i):
    if isinstance(i,str):
        if i.startswith("#"): tagrefs.append((kind,i[1:]))
        elif isid(i): refs.append((kind,i))
def walk(v,kind):
    if isinstance(v,str): add(kind,v)
    elif isinstance(v,list):
        for x in v: walk(x,kind)
    elif isinstance(v,dict):
        for k in ("item","id","tag"):
            if k in v: walk(v[k],kind)
def loot(v):
    if isinstance(v,dict):
        if "blocks" in v: walk(v["blocks"],"block")
        for k in ("name","item"):
            if k in v: walk(v[k],"item")
        for k,vv in v.items():
            if k not in ("blocks","name","item"): loot(vv)
    elif isinstance(v,list):
        for x in v: loot(x)
def adv(v):
    if isinstance(v,dict):
        for k in ("block","blocks"):
            if k in v: walk(v[k],"block")
        for k in ("item","items"):
            if k in v: walk(v[k],"item")
        for vv in v.values(): adv(vv)
    elif isinstance(v,list):
        for x in v: adv(x)
detail=[]
for p in jars:
    jar=os.path.basename(p)
    try:
        with zipfile.ZipFile(p) as z:
            for n in z.namelist():
                if not n.startswith("data/") or not n.endswith(".json"): continue
                ps=n.split("/")
                if len(ps)<4: continue
                try: doc=json.loads(z.read(n))
                except Exception: continue
                r0=len(refs); t0=len(tagrefs)
                if "/recipe/" in n:
                    for k in ("ingredient","ingredients","result","results","item","output","target","outputs","transitional_item","catalyst","required"):
                        if k in doc: walk(doc[k],"item")
                    if isinstance(doc.get("key"),dict):
                        for v in doc["key"].values(): walk(v,"item")
                elif "/loot_table/" in n: loot(doc)
                elif "/advancement/" in n: adv(doc)
                elif "/tags/" in n:
                    typ=ps[3] if len(ps)>4 else ""
                    if typ not in ("item","block"): continue
                    vals=doc.get("values",[]) if isinstance(doc,dict) else doc
                    for v in vals:
                        if isinstance(v,str):
                            if v.startswith("#"): tagrefs.append((typ,v[1:]))
                            elif isid(v): refs.append((typ,v))
                else: continue
                for kind,i in refs[r0:]: detail.append((jar,n,kind,i))
                for kind,i in tagrefs[t0:]: detail.append((jar,n,"tagref-"+kind,i))
    except Exception as e: print("ERR",jar,e)
item_miss=[]; block_miss=[]; tag_miss=[]
for kind,i in refs:
    if kind=="block" and i not in block_ids and i not in item_ids: block_miss.append((kind,i))
    elif kind!="block" and i not in item_ids and i not in block_ids: item_miss.append((kind,i))
for kind,t in tagrefs:
    if (kind,t) not in tags_by_type: tag_miss.append((kind,t))
print("refs",len(refs),"tagrefs",len(tagrefs))
print("item_miss",len(item_miss),"block_miss",len(block_miss),"tag_miss",len(tag_miss))
print("item examples",item_miss[:10])
print("block examples",block_miss[:10])
print("tag missing counter",collections.Counter(t for _,t in tag_miss).most_common(30))
json.dump({"item_miss":item_miss,"block_miss":block_miss,"tag_miss":tag_miss,"detail":detail},open(os.path.join(root,"work","audit_refs_raw3.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)