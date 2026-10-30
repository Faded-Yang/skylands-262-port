# -*- coding: utf-8 -*-
"""scan_iface_invoke.py —— 26.3 把 class 改成 interface 的「调用点」全量扫描（快速版）

26.2 里是 class、26.3 里是 interface 的类型，Create 若用 `invokevirtual`/`invokespecial` 调它，
第一次执行就炸：
    IncompatibleClassChangeError: Found interface X, but class was expected
这类问题 A/B/C/D 审计都看不到（名字、描述符都还在）。

做法：直接读 26.3 jar 的 **access_flags**（ACC_INTERFACE=0x0200）建表，**不跑 javap**；
再扫 Create jar 的常量池，把 `Methodref(tag 10)` 命中 interface owner 的条目 + 实际 opcode 统计出来。

    python tools/scan_iface_invoke.py [jar]
"""
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAR = ROOT / "work" / "run26" / "mods-aero" / "create-fly-26.2-6.0.9-2-26.3-patched.jar"
MC = r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar"


def u2(b, o):
    return int.from_bytes(b[o:o + 2], "big")


ILEN = [1] * 256
for _op in range(0x15, 0x1A):
    ILEN[_op] = 2
for _op in range(0x36, 0x3B):
    ILEN[_op] = 2
for _op in range(0x99, 0xA9):
    ILEN[_op] = 3
ILEN[0x10] = 2
ILEN[0x11] = 3
ILEN[0x12] = 2
ILEN[0x13] = 3
ILEN[0x14] = 3
ILEN[0x84] = 3
ILEN[0xA9] = 2
for _op in range(0xB2, 0xB9):
    ILEN[_op] = 3
ILEN[0xB9] = 5
ILEN[0xBA] = 5
ILEN[0xBB] = 3
ILEN[0xBC] = 2
ILEN[0xBD] = 3
ILEN[0xC0] = 3
ILEN[0xC1] = 3
ILEN[0xC5] = 4
ILEN[0xC6] = 3
ILEN[0xC7] = 3
ILEN[0xC8] = 5
ILEN[0xC9] = 5


def u4(b, o):
    return int.from_bytes(b[o:o + 4], "big")


def parse_cp(buf):
    pos = 10
    count = u2(buf, 8)
    cp = {}
    i = 1
    while i < count:
        tag = buf[pos]
        start = pos
        if tag == 1:
            ln = u2(buf, pos + 1)
            pos += 3 + ln
        elif tag in (3, 4):
            pos += 5
        elif tag in (5, 6):
            pos += 9
        elif tag in (7, 8, 16, 19, 20):
            pos += 3
        elif tag in (9, 10, 11, 12, 17, 18):
            pos += 5
        elif tag == 15:
            pos += 4
        else:
            raise ValueError("tag %d" % tag)
        cp[i] = (tag, start, pos)
        i += 2 if tag in (5, 6) else 1
    return cp, pos


def utf8(buf, cp, idx):
    tag, s, e = cp[idx]
    return buf[s + 3:e].decode("utf-8", "replace") if tag == 1 else None


def access_flags(buf):
    cp, pool_end = parse_cp(buf)
    return u2(buf, pool_end)


def interface_set():
    names = set()
    z = zipfile.ZipFile(MC)
    for n in z.namelist():
        if not n.endswith(".class") or n.startswith("META-INF/"):
            continue
        buf = z.read(n)
        try:
            if access_flags(buf) & 0x0200:
                names.add(n[:-6])
        except Exception:
            pass
    z.close()
    return names


def main():
    jar = Path(sys.argv[1]) if len(sys.argv) > 1 else JAR
    ifaces = interface_set()
    print("26.3 interface 数: %d" % len(ifaces))
    z = zipfile.ZipFile(jar)
    per_owner = Counter()
    per_member = Counter()
    cls_of_member = defaultdict(set)
    for n in z.namelist():
        if not n.endswith(".class"):
            continue
        buf = z.read(n)
        try:
            cp, pool_end = parse_cp(buf)
        except Exception:
            continue
        hit = {}
        for idx, (tag, s, _e) in cp.items():
            if tag != 10:
                continue
            ci = u2(buf, s + 1)
            if cp.get(ci, (0,))[0] != 7:
                continue
            owner = utf8(buf, cp, u2(buf, cp[ci][1] + 1))
            if owner not in ifaces:
                continue
            nat = u2(buf, s + 3)
            if cp.get(nat, (0,))[0] != 12:
                continue
            nm = utf8(buf, cp, u2(buf, cp[nat][1] + 1))
            ds = utf8(buf, cp, u2(buf, cp[nat][1] + 3))
            hit[idx] = (owner, nm, ds)
        if not hit:
            continue
        # 扫方法体里的 opcode
        pos = pool_end + 6
        ic = u2(buf, pos)
        pos += 2 + 2 * ic
        for seg in range(2):
            cnt = u2(buf, pos)
            pos += 2
            for _ in range(cnt):
                ac = u2(buf, pos + 6)
                pos += 8
                codes = []
                for _ in range(ac):
                    alen = u4(buf, pos + 2)
                    nm = utf8(buf, cp, u2(buf, pos))
                    if seg == 1 and nm == "Code":
                        codes.append((pos + 6 + 8, u4(buf, pos + 6 + 4)))
                    pos += 6 + alen
                for cstart, clen in codes:
                    i = 0
                    while i < clen:
                        op = buf[cstart + i]
                        if op in (0xB6, 0xB7, 0xB8):
                            idx = u2(buf, cstart + i + 1)
                            if idx in hit:
                                o = hit[idx]
                                per_owner[o[0]] += 1
                                per_member[o] += 1
                                cls_of_member[o].add(n[:-6])
                            i += 3
                        elif op == 0xB9:
                            idx = u2(buf, cstart + i + 1)
                            if idx in hit:
                                o = hit[idx]
                                per_owner[o[0]] += 0  # invokeinterface 是对的，不计
                            i += 5
                        else:
                            i += ILEN[op]
    z.close()
    print("Methodref 打在 interface 上的 owner: %d 个，指令 %d 处" %
          (len(per_owner), sum(per_owner.values())))
    for owner, cnt in per_owner.most_common():
        print("  %-74s %3d 处 %2d 成员" % (owner, cnt, sum(1 for m in per_member if m[0] == owner)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
