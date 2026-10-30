#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_create_bridge.py —— 通用「调用点 → 桥接类」补丁器（方法引用）。

## 三种可做的变换

1. **invokestatic**：只改常量池 `class_index`（owner）到桥接类。
   桥接方法的 name+descriptor 必须与原调用点完全一致。这是 patch_create_codec.py 的范式。

2. **invokevirtual / invokeinterface**：opcode 改成 `invokestatic`，并把**接收者类型**
   补进描述符第一位。字节码层面天然成立 —— invokevirtual 栈上是 `[receiver, args...]`，
   invokestatic 按描述符吃参数，把 receiver 写成第一参数后栈形状完全一致。
   - invokevirtual：3 字节 → invokestatic 3 字节，长度不变。
   - invokeinterface：5 字节 → invokestatic(3) + nop nop(2)，长度不变，
     StackMapTable / 异常表 / 行号表全部不用动。

3. **字段**：见 patch_create_fields.py（改 NameAndType 的名字）。

## 桥接表（JSON）

    [
      {"owner": "net/minecraft/.../BlockBehaviour$Properties",
       "name": "isViewBlocking",
       "desc": "(L...StatePredicate;)L...Properties;",      # 26.2 调用点的描述符
       "bridge": "dev/eriksonn/aeronautics/compat/BlockPropertiesBridge",
       "new_desc": "(L...Properties;L...StatePredicate;)L...Properties;",  # 桥接方法的描述符
       "opcode": "virtual"}                                # 可选：static / virtual / interface
    ]

## 用法

    python tools/patch_create_bridge.py <jar> [--table tools/create_bridge_table.json] [--dry-run]
"""
import json
import sys
import zipfile

DEFAULT_TABLE = "tools/create_bridge_table.json"


def parse_pool(buf):
    if buf[:4] != b"\xca\xfe\xba\xbe":
        raise ValueError("not a class file")
    pos = 8
    count = u2(buf, pos)
    pos += 2
    entries = []
    i = 1
    while i < count:
        tag = buf[pos]
        start = pos
        if tag == 1:
            pos += 3 + u2(buf, pos + 1)
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
            raise ValueError("unknown cp tag %d at %d" % (tag, pos))
        entries.append((tag, start, pos))
        i += 2 if tag in (5, 6) else 1
    return entries, pos


def u2(buf, off):
    return int.from_bytes(buf[off:off + 2], "big")


def u4(buf, off):
    return int.from_bytes(buf[off:off + 4], "big")


def utf8_value(buf, start):
    ln = u2(buf, start + 1)
    return buf[start + 3:start + 3 + ln].decode("utf-8", "replace")


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


def iter_sites(code):
    """yield (opcode, cp_index, offset)。"""
    i, n = 0, len(code)
    while i < n:
        op = code[i]
        if op in (0xB2, 0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8, 0xBB, 0xBD, 0xC0, 0xC1):
            yield op, u2(code, i + 1), i
            i += ILEN[op]
        elif op == 0xB9:
            yield op, u2(code, i + 1), i
            i += 5
        elif op == 0xBA:
            i += 5
        elif op == 0x12:
            i += 2
        elif op in (0x13, 0x14):
            i += 3
        elif op == 0xAA:
            pad = (4 - ((i + 1) % 4)) % 4
            base = i + 1 + pad
            low = int.from_bytes(code[base + 4:base + 8], "big", signed=True)
            high = int.from_bytes(code[base + 8:base + 12], "big", signed=True)
            i = base + 12 + 4 * max(0, high - low + 1)
        elif op == 0xAB:
            pad = (4 - ((i + 1) % 4)) % 4
            base = i + 1 + pad
            npairs = int.from_bytes(code[base + 4:base + 8], "big", signed=True)
            i = base + 8 + 8 * max(0, npairs)
        elif op == 0xC4:
            i += 6 if code[i + 1] == 0x84 else 4
        else:
            i += ILEN[op]


def _methods_only(data, pool_end, u):
    """只扫 methods 段（跳过 fields），返回 Code 的绝对偏移。"""
    pos = pool_end
    pos += 6
    icount = u2(data, pos)
    pos += 2 + 2 * icount
    for seg in range(2):
        count = u2(data, pos)
        pos += 2
        out = []
        for _ in range(count):
            acount = u2(data, pos + 6)
            pos += 8
            for _ in range(acount):
                aname = u(u2(data, pos))
                alen = u4(data, pos + 2)
                if seg == 1 and aname == "Code":
                    clen = u4(data, pos + 6 + 4)
                    out.append((pos + 6 + 8, clen))
                pos += 6 + alen
        if seg == 1:
            return out
    return []


def patch_class(data, table):
    entries, pool_end = parse_pool(data)
    cp = {}
    idx = 1
    for tag, s, e in entries:
        cp[idx] = (tag, s, e)
        idx += 2 if tag in (5, 6) else 1
    utf8, added = {}, []
    ucache = {}

    def u(i):
        v = ucache.get(i)
        if v is None:
            tag, s, e = cp[i]
            if tag != 1:
                raise ValueError("cp %d not utf8" % i)
            v = utf8_value(data, s)
            ucache[i] = v
        return v

    def cls_name(i):
        tag, s, e = cp[i]
        return u(u2(data, s + 1)) if tag == 7 else None

    # 匹配的 Methodref
    targets = {}
    for i, (tag, s, e) in cp.items():
        if tag not in (10, 11):
            continue
        owner = cls_name(u2(data, s + 1))
        nat = u2(data, s + 3)
        if nat not in cp:
            continue
        nm = u(u2(data, cp[nat][1] + 1))
        ds = u(u2(data, cp[nat][1] + 3))
        for key in ((owner, nm, ds), ):
            if key in table:
                targets[i] = (key, tag, s, nat)
                break
    if not targets:
        return data, 0, 0, []

    # 找使用点
    site_map = {}
    for cstart, clen in _methods_only(data, pool_end, u):
        code = data[cstart:cstart + clen]
        for op, cpidx, off in iter_sites(code):
            if cpidx in targets:
                site_map.setdefault(cpidx, []).append((cstart, off))
    if not site_map:
        return data, 0, 0, []

    # 追加 cp：Class(bridge) / NameAndType(name, new_desc) / Utf8(new_desc)
    appended = bytearray()
    new_count = u2(data, 8)   # ★ 用原始 cp_count（末位 long/double 会占两个槽）

    def add_utf8(sv):
        nonlocal new_count
        b = sv.encode("utf-8")
        appended.append(1)
        appended.extend(len(b).to_bytes(2, "big"))
        appended.extend(b)
        i2 = new_count
        new_count += 1
        return i2

    def add_class(name):
        nonlocal new_count
        ui = add_utf8(name)
        appended.append(7)
        appended.extend(ui.to_bytes(2, "big"))
        i2 = new_count
        new_count += 1
        return i2

    utf8_by_value = {u(i): i for i in cp if cp[i][0] == 1}
    class_by_name = {}
    for i in cp:
        if cp[i][0] == 7:
            class_by_name.setdefault(cls_name(i), i)
    nat_by_key = {}
    for i in cp:
        if cp[i][0] == 12:
            nat_by_key[(u(u2(data, cp[i][1] + 1)), u(u2(data, cp[i][1] + 3)))] = i

    patched = bytearray(data)
    n_sites = 0
    used_ops = set()
    for cpidx, sites in site_map.items():
        key, tag, s, nat = targets[cpidx]
        ent = table[key]
        new_desc = ent["new_desc"]
        bridge = ent["bridge"]
        # 检查所有使用点的 opcode 是否一致可转
        for cstart, off in sites:
            op = patched[cstart + off]
            if op == 0xB8:
                pass
            elif op in (0xB6, 0xB9):
                patched[cstart + off] = 0xB8
                if op == 0xB9:
                    patched[cstart + off + 3] = 0
                    patched[cstart + off + 4] = 0
            elif op == 0xB7:
                print("  [warn] invokespecial 不能转 static：%s %s" % (key[0], key[1]))
                continue
            else:
                print("  [warn] 未知 opcode 0x%02x" % op)
                continue
            used_ops.add(hex(op))
            n_sites += 1
        # cp 改写
        if bridge not in class_by_name:
            class_by_name[bridge] = add_class(bridge)
        if new_desc not in utf8_by_value:
            utf8_by_value[new_desc] = add_utf8(new_desc)
        nkey = (key[1], new_desc)
        if nkey not in nat_by_key:
            nat_idx = new_count
            new_count += 1
            appended.append(12)
            appended.extend(utf8_by_value[nkey[0]].to_bytes(2, "big"))
            appended.extend(utf8_by_value[new_desc].to_bytes(2, "big"))
            nat_by_key[nkey] = nat_idx
        patched[s + 1:s + 3] = class_by_name[bridge].to_bytes(2, "big")
        patched[s + 3:s + 5] = nat_by_key[nkey].to_bytes(2, "big")

    out = bytearray()
    out += patched[:8]
    out += new_count.to_bytes(2, "big")
    out += patched[10:pool_end]
    out += appended
    out += patched[pool_end:]
    return bytes(out), len(site_map), n_sites, sorted(used_ops)


def load_table(path):
    data = json.loads(open(path, encoding="utf-8").read())
    out = {}
    for e in data:
        out[(e["owner"], e["name"], e["desc"])] = e
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    table_path = DEFAULT_TABLE
    if "--table" in sys.argv:
        table_path = sys.argv[sys.argv.index("--table") + 1]
    dry = "--dry-run" in sys.argv
    if not args:
        print(__doc__)
        return 2
    jar = args[0]
    table = load_table(table_path)
    print("table: %d 条" % len(table))

    z = zipfile.ZipFile(jar)
    names = z.namelist()
    blobs = {n: z.read(n) for n in names}
    z.close()

    total_sites = 0
    touched = []
    ops = set()
    for n in names:
        if not n.endswith(".class"):
            continue
        try:
            new, nref, nsites, uo = patch_class(blobs[n], table)
        except Exception as e:
            print("  [skip] %s: %s" % (n, e))
            continue
        if nsites:
            blobs[n] = new
            total_sites += nsites
            ops |= set(uo)
            touched.append((n, nref, nsites))
    print("jar: %s" % jar)
    print("patched classes: %d | methodref entries: %d | call sites: %d | opcodes: %s"
          % (len(touched), sum(t[1] for t in touched), total_sites, ",".join(ops)))
    for n, nref, ns in touched[:30]:
        print("   %-66s refs=%d sites=%d" % (n[:-6].replace("/", ".")[:66], nref, ns))
    if len(touched) > 30:
        print("   ... +%d more" % (len(touched) - 30))
    if dry or not total_sites:
        print("dry-run / nothing to do -> jar untouched")
        return 0
    with zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED) as w:
        for n in names:
            w.writestr(n, blobs[n])
    print("jar rewritten.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
