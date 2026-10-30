import urllib.request, zipfile, io, shutil, os, subprocess, sys, time
from pathlib import Path
ROOT=Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262")
SRV=ROOT/"work/run26/server26"
JAVA=r"C:\Users\95959\AppData\Roaming\.minecraft\runtime\java-runtime-epsilon\bin\java.exe"
SRV.mkdir(parents=True, exist_ok=True)
inst=SRV/"fabric-installer.jar"
if not inst.exists():
    req=urllib.request.Request("https://maven.fabricmc.net/net/fabricmc/fabric-installer/1.0.1/fabric-installer-1.0.1.jar", headers={"User-Agent":"Mozilla/5.0"})
    inst.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    print("installer", inst.stat().st_size)
# run installer
cmd=[JAVA,"-jar",str(inst),"server","-dir",str(SRV),"-mcversion","26.3","-loader","0.19.5","-downloadMinecraft"]
print("run:", " ".join(cmd))
p=subprocess.run(cmd, capture_output=True, text=True, timeout=600)
print("rc:", p.returncode)
print((p.stdout or "")[-1500:])
print((p.stderr or "")[-800:])
for f in sorted(SRV.glob("fabric-server*")): print("server launcher:", f.name, f.stat().st_size)
