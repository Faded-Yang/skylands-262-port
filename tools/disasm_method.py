# -*- coding: utf-8 -*-
"""逐指令反汇编某个方法（默认 SphereBrush.<init>），确认有没有漏掉的 invokespecial。"""
import importlib.util
import sys
import zipfile

spec = importlib.util.spec_from_file_location("ac", "tools/audit_create_api.py")
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)

JAR = "work/run26/mods-aero/create-fly-26.2-6.0.9-2-26.3-patched.jar"
TARGET = "com/zurrtum/create/content/equipment/zapper/terrainzapper/SphereBrush.class"
WANT_METHOD = sys.argv[1] if len(sys.argv) > 1 else "<init>"

NAMES = {0xB2: "getstatic", 0xB3: "putstatic", 0xB4: "getfield", 0xB5: "putfield",
         0xB6: "invokevirtual", 0xB7: "invokespecial", 0xB8: "invokestatic",
         0xB9: "invokeinterface", 0xBB: "new", 0xBD: "anewarray", 0xC0: "checkcast",
         0xC1: "instanceof", 0xBA: "invokedynamic", 0x12: "ldc", 0x13: "ldc_w",
         0x14: "ldc2_w", 0xAA: "tableswitch", 0xAB: "lookupswitch", 0xC4: "wide"}

z = zipfile.ZipFile(JAR)
buf = z.read(TARGET)
z.close()

entries, pool_end = ac.parse_pool(buf)
cp = {}
i = 1
for tag, s, e in entries:
    cp[i] = (tag, s, e)
    i += 2 if tag in (5, 6) else 1


def utf8(idx):
    tag, s, e = cp[idx]
    return buf[s + 3:s + 3 + ac.u2(buf, s + 1)].decode("utf-8", "replace")


def desc(idx):
    if cp[idx][0] in (10, 11):
        s = cp[idx][1]
        o = utf8(ac.u2(buf, s + 1))
        nat = ac.u2(buf, s + 3)
        return "%s.%s%s" % (o, utf8(ac.u2(buf, cp[nat][1] + 1)), utf8(ac.u2(buf, cp[nat][1] + 3)))
    if cp[idx][0] == 9:
        s = cp[idx][1]
        o = utf8(ac.u2(buf, s + 1))
        nat = ac.u2(buf, s + 3)
        return "%s.%s:%s" % (o, utf8(ac.u2(buf, cp[nat][1] + 1)), utf8(ac.u2(buf, cp[nat][1] + 3)))
    if cp[idx][0] == 7:
        return "class " + utf8(ac.u2(buf, cp[idx][1] + 1))
    return "?"


pos = pool_end + 6
ic = ac.u2(buf, pos)
pos += 2 + 2 * ic
for seg in range(2):
    n = ac.u2(buf, pos)
    pos += 2
    for _ in range(n):
        nm = utf8(ac.u2(buf, pos + 2))
        ds = utf8(ac.u2(buf, pos + 4))
        acount = ac.u2(buf, pos + 6)
        pos += 8
        codes = []
        for _ in range(acount):
            an = utf8(ac.u2(buf, pos))
            ln = ac.u4(buf, pos + 2)
            if an == "Code":
                clen = ac.u4(buf, pos + 6 + 4)
                codes.append((pos + 6 + 8, clen))
            pos += 6 + ln
        if seg != 1 or nm != WANT_METHOD:
            continue
        print("=== %s%s" % (nm, ds))
        for cstart, clen in codes:
            code = buf[cstart:cstart + clen]
            j = 0
            while j < clen:
                op = code[j]
                if op in (0xB2, 0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8, 0xBB, 0xBD, 0xC0, 0xC1):
                    idx = ac.u2(code, j + 1)
                    print("  %4d %-14s #%-4d %s" % (j, NAMES.get(op, hex(op)), idx, desc(idx)))
                    j += 3
                elif op == 0xB9:
                    idx = ac.u2(code, j + 1)
                    print("  %4d %-14s #%-4d %s" % (j, NAMES[op], idx, desc(idx)))
                    j += 5
                elif op == 0xBA:
                    print("  %4d invokedynamic #%d" % (j, ac.u2(code, j + 1)))
                    j += 5
                else:
                    ln = ac.ILEN[op]
                    print("  %4d 0x%02x" % (j, op))
                    j += ln
