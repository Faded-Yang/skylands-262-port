import zipfile, json
orig = r"C:\Users\95959\AppData\Roaming\.minecraft\versions\Create 航空学 × 浮空群岛\config\paxi\datapacks\aerolith-1.3.2-1.21.1.zip"
bak  = r"work\run26\mods-crashfix\sky262-skylands-1.0.0.jar.bak-nocarver"
cur  = r"work\run26\mods-crashfix\sky262-skylands-1.0.0.jar"
def get(jar, name):
    with zipfile.ZipFile(jar) as z:
        return json.loads(z.read(name))
ns = "data/minecraft/worldgen/noise_settings/overworld.json"
o = get(orig, ns)
b = get(bak, ns)
c = get(cur, ns)
print("ORIG keys:", sorted(o.keys()))
print("BAK  keys:", sorted(b.keys()))
print("CUR  keys:", sorted(c.keys()))
for k in ("sea_level", "carvers", "aquifers", "default_block", "default_fluid", "noise", "material_rule", "surface_rule", "spawn_target"):
    print("\n--", k)
    for tag, d in (("ORIG", o), ("BAK", b), ("CUR", c)):
        v = d.get(k, "<absent>")
        s = json.dumps(v, sort_keys=True)
        print("   %-4s %s" % (tag, s[:300]))
# also diff router
print("\n== noise_router ORIG ==")
print(json.dumps(o.get("noise_router"), indent=1, sort_keys=True)[:3000])
print("\n== final_density BAK vs CUR identical? ==", b.get("noise_router", {}).get("final_density") == c.get("noise_router", {}).get("final_density"))
print("== final_density ORIG vs BAK identical? ==", o.get("noise_router", {}).get("final_density") == b.get("noise_router", {}).get("final_density"))
