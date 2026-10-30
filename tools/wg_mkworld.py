"""Prepare a test world by copying a real save, wiping its regions, and pinning the seed.

python tools/wg_mkworld.py <out_save_dir> <seed>
"""
import gzip, os, sys, struct, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wg_probe import NBT

SRC = r"work\run26\watch\saves\New World (3)"
WIPE = ["region", "entities", "poi"]


def patch_seed(blob: bytes, seed: int) -> bytes:
    key = b"\x04\x00\x04seed"
    i = blob.find(key)
    if i < 0:
        raise SystemExit("seed tag not found")
    j = i + len(key)
    return blob[:j] + struct.pack(">q", seed) + blob[j + 8:]


def main():
    out = sys.argv[1]
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 123456789
    if os.path.isdir(out):
        shutil.rmtree(out)
    shutil.copytree(SRC, out)
    n = 0
    for root, dirs, files in os.walk(out):
        if os.path.basename(root) in WIPE:
            for f in files:
                if f.endswith(".mca"):
                    os.remove(os.path.join(root, f))
                    n += 1
    src = os.path.join(out, r"data\minecraft\world_gen_settings.dat")
    raw = gzip.decompress(open(src, "rb").read())
    with gzip.open(src, "wb") as f:
        f.write(patch_seed(raw, seed))
    back = gzip.decompress(open(src, "rb").read())
    nn = NBT(back); nn.u1(); nn.s(); d = nn.payload(10)
    print("world prepared:", out, " removed .mca:", n)
    print("  seed now:", d["data"]["seed"])


if __name__ == "__main__":
    main()
