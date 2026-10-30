# -*- coding: utf-8 -*-
"""打印 SphereBrush 常量池 #1 / #151 / #18 的原始内容，确认没有解析错。"""
import importlib.util
import zipfile

spec = importlib.util.spec_from_file_location("ac", "tools/audit_create_api.py")
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)

JAR = "work/run26/mods-aero/create-fly-26.2-6.0.9-2-26.3-patched.jar"
z = zipfile.ZipFile(JAR)
buf = z.read("com/zurrtum/create/content/equipment/zapper/terrainzapper/SphereBrush.class")
z.close()

entries, pool_end = ac.parse_pool(buf)
cp = {}
i = 1
for tag, s, e in entries:
    cp[i] = (tag, s, e)
    i += 2 if tag in (5, 6) else 1
print("cp 条目数", len(cp), "pool_end", pool_end)


def u(idx):
    tag, s, e = cp[idx]
    ln = ac.u2(buf, s + 1)
    return buf[s + 3:s + 3 + ln]


def raw(idx):
    tag, s, e = cp[idx]
    return tag, buf[s:e]


for idx in (1, 9, 18, 24, 151):
    tag, b = raw(idx)
    print("cp#%-4d tag=%d raw=%r" % (idx, tag, b))
    if tag == 7:
        print("        class -> %r" % u(ac.u2(buf, cp[idx][1] + 1)))
    elif tag in (10, 11):
        s = cp[idx][1]
        print("        owner=%r nat=%d" % (u(ac.u2(buf, s + 1)), ac.u2(buf, s + 3)))
        nat = ac.u2(buf, s + 3)
        ns = cp[nat][1]
        print("        name=%r desc=%r" % (u(ac.u2(buf, ns + 1)), u(ac.u2(buf, ns + 3))))
