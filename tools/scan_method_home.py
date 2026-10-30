# -*- coding: utf-8 -*-
"""scan_method_home.py —— 在 26.3 里找「某个方法名」现在落在哪个类

用途：26.2 的某个方法在 26.3 从原 owner 消失了，先全量扫一遍新家（可能整体搬到了 *Util），
      能直接转调就不用猜语义。

    python tools/scan_method_home.py preciseInsert countSpace insertExist
"""
import sys
import zipfile

MC = r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar"


def cp_entries(buf):
    pos = 10
    count = int.from_bytes(buf[8:10], "big")
    i = 1
    utf8, classes, out = {}, {}, []
    while i < count:
        tag = buf[pos]
        start = pos
        if tag == 1:
            ln = int.from_bytes(buf[pos + 1:pos + 3], "big")
            utf8[i] = buf[pos + 3:pos + 3 + ln].decode("utf-8", "replace")
            pos += 3 + ln
        elif tag in (3, 4):
            pos += 5
        elif tag in (5, 6):
            pos += 9
        elif tag in (7, 8, 16, 19, 20):
            if tag == 7:
                classes[i] = int.from_bytes(buf[pos + 1:pos + 3], "big")
            pos += 3
        elif tag in (9, 10, 11, 12, 17, 18):
            pos += 5
        elif tag == 15:
            pos += 4
        else:
            raise ValueError("tag %d" % tag)
        out.append((tag, start, pos, i))
        i += 2 if tag in (5, 6) else 1
    return utf8, classes, out, pos, count


def main():
    wants = set(sys.argv[1:])
    if not wants:
        print(__doc__)
        return 2
    z = zipfile.ZipFile(MC)
    hits = {}
    for n in z.namelist():
        if not n.endswith(".class") or n.startswith("META-INF/"):
            continue
        buf = z.read(n)
        try:
            utf8, classes, _out, _pe, _cnt = cp_entries(buf)
        except Exception:
            continue
        # 只看「方法名」：Utf8 出现在 NameAndType 的第一半
        found = set()
        for tag, start, _end, idx in _out:
            if tag != 12:
                continue
            ni = int.from_bytes(buf[start + 1:start + 3], "big")
            nm = utf8.get(ni)
            if nm in wants:
                found.add(nm)
        for f in found:
            hits.setdefault(f, []).append(n[:-6].replace("/", "."))
    z.close()
    for w in sys.argv[1:]:
        lst = sorted(set(hits.get(w, [])))
        print("== %s : %d 个类" % (w, len(lst)))
        for c in lst[:25]:
            print("   %s" % c)
        if len(lst) > 25:
            print("   ... +%d" % (len(lst) - 25))
    return 0


if __name__ == "__main__":
    sys.exit(main())
