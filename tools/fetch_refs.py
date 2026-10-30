import urllib.request, zipfile, io, shutil, sys, os
from pathlib import Path
ROOT=Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262")
base=ROOT/"work/refs/repos"; base.mkdir(parents=True, exist_ok=True)
repos=[
 ("fabric-docs","FabricMC/fabric-docs",["main","master","dev"]),
 ("neoforged-documentation","neoforged/documentation",["main","master"]),
 ("fabricators-create","Fabricators-of-Create/Create",["main","1.20.1","dev/1.20.1","1.20.1/dev"]),
 ("create-wiki","Creators-of-Create/wiki",["master","main"]),
 ("yan-mc-mod-dev","yan-mc/minecraft-mod-dev",["main","master"]),
]
def get(url, timeout=180):
    req=urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()
for name, slug, branches in repos:
    dest=base/name
    if dest.exists() and any(dest.iterdir()):
        print("exists", name); continue
    got=False
    for br in branches:
        url=f"https://codeload.github.com/{slug}/zip/refs/heads/{br}"
        try:
            data=get(url)
        except Exception as e:
            print(name, br, "ERR", str(e)[:100]); continue
        try:
            z=zipfile.ZipFile(io.BytesIO(data))
        except Exception as e:
            print(name, br, "bad zip", e); continue
        tmp=base/(name+".tmp")
        if tmp.exists(): shutil.rmtree(tmp)
        z.extractall(tmp)
        inner=[p for p in tmp.iterdir() if p.is_dir()]
        if not inner:
            shutil.rmtree(tmp); print(name, br, "empty"); continue
        if dest.exists(): shutil.rmtree(dest)
        inner[0].rename(dest)
        shutil.rmtree(tmp)
        print("OK", name, br, "files:", sum(1 for _ in dest.rglob("*") if _.is_file()))
        got=True; break
    if not got: print("FAILED", name)
