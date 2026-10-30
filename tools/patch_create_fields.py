#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_create_fields.py —— 用「常量池改 NameAndType」修 Create-Fly 的**字段**缺口。

## 为什么字段也能改常量池

任务书里说「字段引用改不了 owner，只能靠 mixin 加字段」——这句话只对了一半：
`getstatic Owner.FIELD` 的解析键是 `class_index + name_and_type_index`，**两个都能改**。
改 owner 需要目标类真有这个字段（我们自己的桥接类可以声明）；
改 name 则需要一个新的 NameAndType（名字变了、描述符不变）。

本脚本走「改 name」这条路：`PushReaction.IGNORE` → `PushReaction.IGNORE_ENTITY`。
枚举常量是同一族对象，语义完全等价，零降级。

## 26.2 → 26.3 的 PushReaction 改名表

26.3 把整套枚举常量重命名了（javap 实测 26.3 只有
PUSH_PULL / PUSH / POPPED / IMMOVEABLE / IGNORE_ENTITY）：

    26.2           26.3
    NORMAL      -> PUSH_PULL
    PUSH        -> PUSH
    PUSH_ONLY   -> PUSH
    BLOCK       -> IMMOVEABLE
    DESTROY     -> POPPED
    IGNORE      -> IGNORE_ENTITY

## 用法

    python tools/patch_create_fields.py <jar> [--dry-run]
"""
import sys
import zipfile

OWNER = "net/minecraft/world/level/material/PushReaction"

RENAMES = {
    "NORMAL": "PUSH_PULL",
    "PUSH_ONLY": "PUSH",
    "BLOCK": "IMMOVEABLE",
    "DESTROY": "POPPED",
    "IGNORE": "IGNORE_ENTITY",
}


# ---- 常量池 ---------------------------------------------------------------

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


def utf8_value(buf, start):
    ln = u2(buf, start + 1)
    return buf[start + 3:start + 3 + ln].decode("utf-8", "replace")


def patch_class(data):
    """返回 (new_bytes, n_fieldrefs, n_new_cp)。"""
    entries, pool_end = parse_pool(data)
    cp = {}
    idx = 1
    for tag, s, e in entries:
        cp[idx] = (tag, s, e)
        idx += 2 if tag in (5, 6) else 1

    utf8 = {}

    def u(idx_):
        v = utf8.get(idx_)
        if v is None:
            tag, s, e = cp[idx_]
            if tag != 1:
                raise ValueError("cp %d not utf8" % idx_)
            v = utf8_value(data, s)
            utf8[idx_] = v
        return v

    def cls_name(i):
        tag, s, e = cp[i]
        return u(u2(data, s + 1)) if tag == 7 else None

    # 找出所有指向 PushReaction 的 Fieldref
    hits = []
    for i, (tag, s, e) in cp.items():
        if tag != 9:
            continue
        if cls_name(u2(data, s + 1)) != OWNER:
            continue
        nat = u2(data, s + 3)
        ntag, ns, ne = cp[nat]
        nm = u(u2(data, ns + 1))
        if nm in RENAMES:
            hits.append((i, nat, nm, u2(data, ns + 3), u2(data, ns + 1)))
    if not hits:
        return data, 0, 0

    # 复用/新增 Utf8（新名字）
    name_utf8 = {}
    for i, (tag, s, e) in cp.items():
        if tag == 1:
            v = utf8_value(data, s)
            if v in set(RENAMES.values()):
                name_utf8.setdefault(v, i)

    appended = bytearray()
    new_count = max(cp) + 1

    def add_utf8(s):
        nonlocal new_count
        b = s.encode("utf-8")
        appended.append(1)
        appended.extend(len(b).to_bytes(2, "big"))
        appended.extend(b)
        idx2 = new_count
        new_count += 1
        return idx2

    # 复用/新增 NameAndType（(新名字, 原描述符)）
    nat_cache = {}
    for i, (tag, s, e) in cp.items():
        if tag == 12:
            nm = u(u2(data, s + 1))
            ds = u(u2(data, s + 3))
            nat_cache[(nm, ds)] = i

    patched = bytearray(data)
    for _fref, _nat, old, desc_idx, _name_idx in hits:
        new_name = RENAMES[old]
        desc = u(desc_idx)
        if new_name not in name_utf8:
            name_utf8[new_name] = add_utf8(new_name)
        key = (new_name, desc)
        if key not in nat_cache:
            nat_idx = new_count
            new_count += 1
            appended.append(12)
            appended.extend(name_utf8[new_name].to_bytes(2, "big"))
            appended.extend(desc_idx.to_bytes(2, "big"))
            nat_cache[key] = nat_idx
        else:
            nat_idx = nat_cache[key]
        # Fieldref: tag, class_index, name_and_type_index
        _t, fs, _fe = cp[_fref]
        patched[fs + 3:fs + 5] = nat_idx.to_bytes(2, "big")

    out = bytearray()
    out += patched[:8]
    out += (new_count).to_bytes(2, "big")
    out += patched[10:pool_end]
    out += appended
    out += patched[pool_end:]
    return bytes(out), len(hits), len(appended)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if not args:
        print(__doc__)
        return 2
    jar = args[0]
    z = zipfile.ZipFile(jar)
    names = z.namelist()
    blobs = {n: z.read(n) for n in names}
    z.close()

    total = 0
    touched = []
    for n in names:
        if not n.endswith(".class"):
            continue
        try:
            new, k, _nb = patch_class(blobs[n])
        except Exception as e:
            print("  [skip] %s: %s" % (n, e))
            continue
        if k:
            blobs[n] = new
            total += k
            touched.append((n, k))

    print("jar: %s" % jar)
    print("classes: %d | patched classes: %d | fieldref sites: %d"
          % (len(names), len(touched), total))
    for n, k in touched[:20]:
        print("   %-70s %d" % (n[:-6].replace("/", ".")[:70], k))
    if len(touched) > 20:
        print("   ... +%d more" % (len(touched) - 20))

    if dry or not total:
        print("dry-run / nothing to do -> jar untouched")
        return 0
    with zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED) as w:
        for n in names:
            w.writestr(n, blobs[n])
    print("jar rewritten.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
