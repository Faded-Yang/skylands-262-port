import gzip, sys
sys.path.insert(0, r"tools")
from wg_probe import NBT
for p in [r"work\run26\watch\saves\New World (3)\data\minecraft\world_gen_settings.dat"]:
    raw = gzip.decompress(open(p, "rb").read())
    n = NBT(raw); t = n.u1(); nm = n.s(); d = n.payload(10)
    print(p)
    print("root name:", repr(nm))
    def show(d, ind=""):
        for k, v in d.items():
            if isinstance(v, dict):
                print(ind + k + " {"); show(v, ind + "  "); print(ind + "}")
            else:
                print(ind + k, "=", repr(v)[:200])
    show(d)
