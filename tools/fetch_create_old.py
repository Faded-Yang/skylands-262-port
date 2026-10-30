import urllib.request, zipfile, io, shutil
from pathlib import Path
ROOT=Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262")
base=ROOT/"work/refs/repos"
name="fabricators-create-old"
url="https://codeload.github.com/Fabricators-of-Create/Create-Fabric-Old/zip/refs/heads/master"
req=urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
data=urllib.request.urlopen(req, timeout=300).read()
print("downloaded", len(data))
z=zipfile.ZipFile(io.BytesIO(data))
tmp=base/(name+".tmp")
if tmp.exists(): shutil.rmtree(tmp)
z.extractall(tmp)
inner=[p for p in tmp.iterdir() if p.is_dir()][0]
dest=base/name
if dest.exists(): shutil.rmtree(dest)
inner.rename(dest); shutil.rmtree(tmp)
print("OK", dest, "files", sum(1 for _ in dest.rglob("*") if _.is_file()))
# branch sanity
for p in (dest/"src").glob("*"):
    print("  src/", p.name)
