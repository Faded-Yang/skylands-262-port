# -*- coding: utf-8 -*-
"""scan_icce.py — 全量扫描 Methodref/InterfaceMethodref 与 owner 实际类型不匹配（ICCE 类危险）。

JVM 规则：
  - owner 是 interface -> 必须 InterfaceMethodref(tag 11)；用 Methodref(10) 可能 ICCE
  - owner 是 class     -> 必须 Methodref(10)；用 InterfaceMethodref(11) 可能 ICCE（如 ContainerBridge）

用法: python tools/scan_icce.py [--json out.json] [--fix-staging outdir]
"""
import argparse, json, struct, sys, zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "work/run26/mods-stable"
MC = Path(r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar")
ACC_INTERFACE = 0x0200

def parse_cp(data):
    """return (cp entries list, offset after cp, cp_count)"""
    i = 8
    cnt = struct.unpack(">H", data[i:i+2])[0]; i += 2
    cp = [None] * cnt
    idx = 1
    while idx < cnt:
        tag = data[i]; i += 1
        if tag == 1:
            ln = struct.unpack(">H", data[i:i+2])[0]; i += 2
            cp[idx] = (1, data[i:i+ln].decode("utf-8", "replace")); i += ln
        elif tag in (7, 8, 16, 19, 20):
            cp[idx] = (tag, struct.unpack(">H", data[i:i+2])[0]); i += 2
        elif tag == 15:
            cp[idx] = (tag, struct.unpack(">BH", data[i:i+3])); i += 3
        elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
            cp[idx] = (tag, struct.unpack(">HH", data[i:i+4])); i += 4
        elif tag in (5, 6):
            cp[idx] = (tag, data[i:i+8]); i += 8; idx += 1
        else:
            raise ValueError("unsupported cp tag %d at %d" % (tag, i))
        idx += 1
    return cp, i

def cp_class_name(cp, class_index):
    e = cp[class_index]
    if not e or e[0] != 7: return None
    ne = cp[e[1]]
    return ne[1] if ne and ne[0] == 1 else None

def build_index(jars):
    """class internal name -> is_interface"""
    index = {}
    for p in jars:
        try: z = zipfile.ZipFile(p)
        except Exception: continue
        for n in z.namelist():
            if not n.endswith(".class"): continue
            try: b = z.read(n)
            except Exception: continue
            if len(b) < 10: continue
            try:
                cp, _ = parse_cp(b)
            except Exception:
                continue
            # access_flags right after cp
            off = 8
            cnt = struct.unpack(">H", b[off:off+2])[0]; off += 2
            # reparse to get offset
            i = off; idx = 1
            while idx < cnt:
                tag = b[i]; i += 1
                if tag == 1:
                    ln = struct.unpack(">H", b[i:i+2])[0]; i += 2 + ln
                elif tag in (7, 8, 16, 19, 20): i += 2
                elif tag == 15: i += 3
                elif tag in (3, 4, 9, 10, 11, 12, 17, 18): i += 4
                elif tag in (5, 6): i += 8; idx += 1
                else: break
                idx += 1
            if i + 6 > len(b): continue
            access = struct.unpack(">H", b[i:i+2])[0]
            index[n[:-6]] = bool(access & ACC_INTERFACE)
    return index

def scan_jar(p, index):
    findings = []
    try: z = zipfile.ZipFile(p)
    except Exception: return findings
    for n in z.namelist():
        if not n.endswith(".class"): continue
        try: b = z.read(n)
        except Exception: continue
        try: cp, _ = parse_cp(b)
        except Exception: continue
        for i, e in enumerate(cp):
            if not e or e[0] not in (10, 11): continue
            _, (ci, nti) = e
            owner = cp_class_name(cp, ci)
            if not owner or owner not in index: continue
            is_iface = index[owner]
            tag = e[0]
            bad = (tag == 11 and not is_iface) or (tag == 10 and is_iface)
            if bad:
                nt = cp[nti]
                name = desc = "?"
                if nt and nt[0] == 12:
                    a, c = nt[1]
                    na = cp[a]; de = cp[c]
                    name = na[1] if na and na[0] == 1 else "?"
                    desc = de[1] if de and de[0] == 1 else "?"
                findings.append({"class": n, "ref_index": i, "tag": tag,
                                 "owner": owner, "owner_is_iface": is_iface,
                                 "name": name, "desc": desc})
    return findings

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=str(ROOT / "work/run26/port/g31/out/icce-scan.json"))
    ap.add_argument("--limit", type=int, default=40)
    a = ap.parse_args()
    jars = [MC] + sorted(LIVE.glob("*.jar"))
    print("building class index from %d jars..." % len(jars))
    index = build_index(jars)
    print("classes:", len(index))
    allf = []
    for p in sorted(LIVE.glob("*.jar")):
        fs = scan_jar(p, index)
        if fs:
            print("== %-60s %d" % (p.name, len(fs)))
            for f in fs[:a.limit]:
                print("   %s#%d tag=%d owner=%s(%s) %s%s" % (f["class"], f["ref_index"], f["tag"],
                      f["owner"], "iface" if f["owner_is_iface"] else "class", f["name"], f["desc"]))
            allf.extend(dict(f, jar=p.name) for f in fs)
    out = Path(a.json); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(allf, ensure_ascii=False, indent=1), encoding="utf-8")
    print("TOTAL findings:", len(allf), "->", out)
    cnt = Counter((f["jar"], f["tag"]) for f in allf)
    for k, v in sorted(cnt.items(), key=lambda x: -x[1])[:20]:
        print("  ", k, v)

if __name__ == "__main__":
    main()
