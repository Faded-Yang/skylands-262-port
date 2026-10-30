# -*- coding: utf-8 -*-
"""把 aeronautics jar 里的嵌套 jar 抽出来单独扫（含 BlockPos.<init>(Vec3i) 与 SphereBrush）。"""
import importlib.util
import io
import os
import zipfile

spec = importlib.util.spec_from_file_location("ac", "tools/audit_create_api.py")
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)

AERO = "work/run26/mods-aero/aeronautics-fabric-0.1.0-port.26.3.jar"
OUTDIR = "work/run26/_nestedjars"
os.makedirs(OUTDIR, exist_ok=True)

za = zipfile.ZipFile(AERO)
nested = [n for n in za.namelist() if n.endswith(".jar")]
print("嵌套 jar:", nested)
for n in nested:
    data = za.read(n)
    dest = os.path.join(OUTDIR, os.path.basename(n))
    with open(dest, "wb") as f:
        f.write(data)
    zz = zipfile.ZipFile(io.BytesIO(data))
    names = zz.namelist()
    print("\n%s: %d 条目 / %d class" % (dest, len(names), len([x for x in names if x.endswith('.class')])))
    sb = [x for x in names if x.endswith("SphereBrush.class")]
    print("  SphereBrush:", sb)
    # 扫 BlockPos ctor 引用（raw）
    hits = []
    for e in names:
        if not e.endswith(".class"):
            continue
        buf = zz.read(e)
        try:
            entries, _ = ac.parse_pool(buf)
        except Exception:
            continue
        cp = {}
        i = 1
        for tag, s, en in entries:
            cp[i] = (tag, s, en)
            i += 2 if tag in (5, 6) else 1

        def u(idx):
            tag, s, en = cp[idx]
            ln = ac.u2(buf, s + 1)
            return buf[s + 3:s + 3 + ln].decode("utf-8", "replace")

        for idx, (tag, s, en) in cp.items():
            if tag not in (10, 11):
                continue
            try:
                oi = ac.u2(buf, s + 1)
                if cp[oi][0] != 7:
                    continue
                owner = u(ac.u2(buf, cp[oi][1] + 1))
                if owner != "net/minecraft/core/BlockPos":
                    continue
                nat = ac.u2(buf, s + 3)
                nm = u(ac.u2(buf, cp[nat][1] + 1))
                ds = u(ac.u2(buf, cp[nat][1] + 3))
                if nm == "<init>" and "(Lnet/minecraft/core/Vec3i;)V" == ds:
                    pat = bytes([0xB7]) + idx.to_bytes(2, "big")
                    hits.append((e, idx, buf.count(pat)))
            except Exception:
                continue
    print("  仍含 invokespecial BlockPos.<init>(Vec3i) 的类: %d" % len(hits))
    for e, idx, c in hits[:20]:
        print("    %-72s cp#%d x%d" % (e[:-6], idx, c))
za.close()
