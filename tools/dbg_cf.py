# -*- coding: utf-8 -*-
"""调试 patch_create_final_overrides 的 Cf 解析：pool_end / this_idx 对不对。"""
import importlib.util
import zipfile

spec = importlib.util.spec_from_file_location("fo", "tools/patch_create_final_overrides.py")
fo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fo)

spec2 = importlib.util.spec_from_file_location("ac", "tools/audit_create_api.py")
ac = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(ac)

JAR = "work/run26/mods-aero/create-fly-26.2-6.0.9-2-26.3-patched.jar"
z = zipfile.ZipFile(JAR)
buf = z.read("com/zurrtum/create/content/logistics/box/PackageEntity.class")
z.close()

entries, pool_end, cnt = fo.parse_pool(buf)
print("cp_count", cnt, "entries", len(entries), "pool_end", pool_end)
print("class ver %d.%d" % (int.from_bytes(buf[6:8], "big"), int.from_bytes(buf[4:6], "big")))
print("access %04x this %d super %d" % (fo.u2(buf, pool_end), fo.u2(buf, pool_end + 2), fo.u2(buf, pool_end + 4)))
cp = {}
i = 1
for tag, s, e in entries:
    cp[i] = (tag, s, e)
    i += 2 if tag in (5, 6) else 1
for idx in (fo.u2(buf, pool_end + 2),):
    tag, s, e = cp[idx]
    print("this cp idx %d tag %d -> %r" % (idx, tag, buf[s+3:s+3+fo.u2(buf, s+1)].decode("utf-8", "replace")))

d = ac.parse_class(buf)
print("audit name:", d["name"])
