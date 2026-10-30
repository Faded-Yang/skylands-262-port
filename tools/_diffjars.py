import zipfile, json, sys
orig = r"C:\Users\95959\AppData\Roaming\.minecraft\versions\Create 航空学 × 浮空群岛\config\paxi\datapacks\aerolith-1.3.2-1.21.1.zip"
fix  = r"C:\Users\95959\AppData\Roaming\.minecraft\versions\Create 航空学 × 浮空群岛\config\paxi\datapacks\zzz-skylands-fix.zip"
bak  = r"work\run26\mods-crashfix\sky262-skylands-1.0.0.jar.bak-nocarver"
cur  = r"work\run26\mods-crashfix\sky262-skylands-1.0.0.jar"
for tag, p in [("ORIG aerolith", orig), ("ORIG zzz-fix", fix)]:
    print("="*20, tag)
    with zipfile.ZipFile(p) as z:
        for n in z.namelist():
            print("  ", n)
print("="*20, "DIFF bak-nocarver -> cur (json keys)")
def read(jar):
    d = {}
    with zipfile.ZipFile(jar) as z:
        for n in z.namelist():
            d[n] = z.read(n)
    return d
a, b = read(bak), read(cur)
for n in sorted(set(a) | set(b)):
    if n not in a: print("  +ADDED  ", n)
    elif n not in b: print("  -REMOVED", n)
    elif a[n] != b[n]:
        print("  *CHANGED", n)
        try:
            ja, jb = json.loads(a[n]), json.loads(b[n])
            print("     old:", json.dumps(ja, sort_keys=True)[:400])
            print("     new:", json.dumps(jb, sort_keys=True)[:400])
        except Exception:
            print("     (binary)")
