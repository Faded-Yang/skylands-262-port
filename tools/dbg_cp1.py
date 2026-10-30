# -*- coding: utf-8 -*-
"""精确打印 SphereBrush 的 cp#1（<init> 的目标）——确认它到底是 ShapedBrush 还是 BlockPos。"""
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


def utf8_at(idx):
    tag, s, _e = cp[idx]
    assert tag == 1, (idx, tag)
    ln = ac.u2(buf, s + 1)
    return buf[s + 3:s + 3 + ln].decode("utf-8", "replace")


def class_at(idx):
    tag, s, _e = cp[idx]
    assert tag == 7, (idx, tag)
    return utf8_at(ac.u2(buf, s + 1))


for want in (1, 9, 151):
    tag, s, e = cp[want]
    if tag in (9, 10, 11):
        ci = ac.u2(buf, s + 1)
        nat = ac.u2(buf, s + 3)
        ns = cp[nat][1]
        print("cp#%-4d Methodref owner=%r  name=%r desc=%r"
              % (want, class_at(ci), utf8_at(ac.u2(buf, ns + 1)), utf8_at(ac.u2(buf, ns + 3))))
    else:
        print("cp#%-4d tag=%d" % (want, tag))

# 也打印 this_class 与 super_class
print("this=%r super=%r" % (class_at(ac.u2(buf, pool_end + 2)), class_at(ac.u2(buf, pool_end + 4))))
