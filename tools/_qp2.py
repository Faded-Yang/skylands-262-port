import zipfile, re
mc = r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar"
z = zipfile.ZipFile(mc)
for n in ["net/minecraft/client/main/Main.class", "net/minecraft/client/main/GameConfig.class",
          "net/minecraft/client/quickplay/QuickPlay.class"]:
    data = z.read(n)
    ss = [s.decode() for s in re.findall(rb"[\x20-\x7e]{3,}", data)]
    print("="*20, n)
    for t in ss:
        lu = t.lower()
        if "quick" in lu or "worldid" in lu or "quickplay" in lu:
            print("   ", t)
