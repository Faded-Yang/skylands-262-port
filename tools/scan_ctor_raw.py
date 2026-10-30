# -*- coding: utf-8 -*-
"""用**原始字节搜索**（不依赖字节码解析）找出所有含 `invokespecial <cp#>` 指向
BlockPos.<init>(Vec3i)V 的类 —— 排除「解析失步」导致的漏判。"""
import importlib.util
import sys
import zipfile

spec = importlib.util.spec_from_file_location("ac", "tools/audit_create_api.py")
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)

JAR = sys.argv[1] if len(sys.argv) > 1 else "work/run26/mods-aero/create-fly-26.2-6.0.9-2-26.3-patched.jar"
OWNER = sys.argv[2] if len(sys.argv) > 2 else "net/minecraft/core/BlockPos"
NAME = sys.argv[3] if len(sys.argv) > 3 else "<init>"
DESC = sys.argv[4] if len(sys.argv) > 4 else "(Lnet/minecraft/core/Vec3i;)V"

z = zipfile.ZipFile(JAR)
names = [n for n in z.namelist() if n.endswith(".class") and not n.startswith("META-INF/")]

found = []
for n in names:
    buf = z.read(n)
    try:
        entries, pool_end = ac.parse_pool(buf)
    except Exception:
        continue
    cp = {}
    i = 1
    for tag, s, e in entries:
        cp[i] = (tag, s, e)
        i += 2 if tag in (5, 6) else 1

    def u(idx):
        tag, s, e = cp[idx]
        ln = ac.u2(buf, s + 1)
        return buf[s + 3:s + 3 + ln].decode("utf-8", "replace")

    def cn(idx):
        tag, s, e = cp[idx]
        return u(ac.u2(buf, s + 1)) if tag == 7 else None

    refs = []
    for idx, (tag, s, e) in cp.items():
        if tag not in (10, 11):
            continue
        o = cn(ac.u2(buf, s + 1))
        nat = ac.u2(buf, s + 3)
        if nat not in cp:
            continue
        nm = u(ac.u2(buf, cp[nat][1] + 1))
        ds = u(ac.u2(buf, cp[nat][1] + 3))
        if o == OWNER and nm == NAME and ds == DESC:
            refs.append(idx)
    if not refs:
        continue
    hits = []
    for idx in refs:
        pat = bytes([0xB7]) + idx.to_bytes(2, "big")
        c = buf.count(pat)
        if c:
            hits.append((idx, c))
    if hits:
        found.append((n, hits, len(refs)))

z.close()
print("含 `invokespecial` 指向 %s.%s%s 的类: %d" % (OWNER, NAME, DESC, len(found)))
for n, hits, nrefs in found:
    print("  %-76s %s (refs=%d)" % (n[:-6], hits, nrefs))
