import zipfile, re, json, sys
from pathlib import Path
mods = Path(sys.argv[1] if len(sys.argv)>1 else r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\mods-stable")
outdir = Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g29")
blocks={}; items={}
for j in sorted(mods.glob("*.jar")):
    try: z=zipfile.ZipFile(j)
    except Exception: continue
    for n in z.namelist():
        m=re.match(r"assets/([^/]+)/blockstates/(.+)\.json$", n)
        if m: blocks.setdefault(m.group(1), []).append(m.group(2))
        m2=re.match(r"assets/([^/]+)/items/(.+)\.json$", n)
        if m2:
            p=m2.group(2)
            if "/" in p: continue  # nested model part, not an item id
            items.setdefault(m2.group(1), []).append(p)
(outdir/"block_ids.json").write_text(json.dumps(blocks, indent=0), encoding="utf-8")
(outdir/"item_ids.json").write_text(json.dumps(items, indent=0), encoding="utf-8")
print("blocks:", sum(len(v) for v in blocks.values()), "items:", sum(len(v) for v in items.values()))