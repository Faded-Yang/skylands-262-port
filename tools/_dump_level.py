import gzip, sys
sys.path.insert(0, r"tools")
from wg_probe import NBT
p = r"work\run26\probe46\saves\新的世界\level.dat"
raw = gzip.decompress(open(p,"rb").read())
n = NBT(raw); t = n.u1(); name = n.s(); d = n.payload(10)
def walk(d, prefix="", depth=0):
    if depth > 2: 
        print(prefix, "{...}")
        return
    for k, v in d.items():
        if isinstance(v, dict):
            print(prefix + k, "{", len(v), "keys }")
            walk(v, prefix + "  ", depth+1)
        elif isinstance(v, list):
            print(prefix + k, "[list", len(v), "]")
        else:
            print(prefix + k, "=", repr(v)[:120])
print("ROOT:", list(d.keys()))
walk(d)
