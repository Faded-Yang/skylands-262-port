import zipfile, re
mc = r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar"
z = zipfile.ZipFile(mc)
names = [n for n in z.namelist() if re.search(r"quickplay|QuickPlay", n, re.I)]
print("classes:", names[:20])
for n in names[:5]:
    data = z.read(n)
    ss = re.findall(rb"[\x20-\x7e]{4,}", data)
    print("==", n)
    for s in ss:
        t = s.decode()
        if any(k in t.lower() for k in ("quickplay", "level", "singleplayer", "world", "usage", "argument", "demo", "realm")):
            print("   ", t)
