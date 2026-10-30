import gzip, sys, json
sys.path.insert(0, r"tools")
from wg_probe import NBT
for name, p in [("probe46","work\\run26\\probe46\\saves\\新的世界\\level.dat"),
                ("watch_NW3","work\\run26\\watch\\saves\\New World (3)\\level.dat"),
                ("watch_NW2","work\\run26\\watch\\saves\\New World (2)\\level.dat")]:
    raw = gzip.decompress(open(p,"rb").read())
    n = NBT(raw); n.u1(); n.s(); d = n.payload(10)["Data"]
    print("==", name)
    print("  preset:", d.get("simulated:world_preset"))
    dp = d.get("DataPacks", {})
    print("  enabled :", dp.get("Enabled"))
    print("  disabled:", dp.get("Disabled"))
