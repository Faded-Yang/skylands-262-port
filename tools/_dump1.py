import sys, os, glob, json
sys.path.insert(0, r"tools")
import importlib.util
spec = importlib.util.spec_from_file_location("wp", r"tools\wg_probe.py")
wp = importlib.util.module_from_spec(spec); spec.loader.exec_module(wp)
reg = r"work\run26\watch\saves\New World (3)\dimensions\minecraft\overworld\region"
f = sorted(glob.glob(os.path.join(reg,"*.mca")))[0]
blob = next(wp.iter_region(f))
ch = wp.read_chunk(blob)
print("top keys:", list(ch.keys()))
print("xPos,zPos:", ch.get("xPos"), ch.get("zPos"), "Status:", ch.get("Status"))
secs = ch.get("sections") or []
print("num sections:", len(secs))
for s in secs[:3]:
    print("--- section keys:", list(s.keys()), "Y=", s.get("Y"))
    bs = s.get("block_states")
    if bs:
        print("   block_states keys:", list(bs.keys()))
        pal = bs.get("palette")
        print("   palette type:", type(pal), "len", len(pal) if pal is not None else None)
        print("   palette[:6]:", json.dumps(pal[:6], default=str)[:600])
        d = bs.get("data")
        print("   data:", type(d), len(d) if d is not None else None)
        if d: print("   data[:3]:", d[:3])
