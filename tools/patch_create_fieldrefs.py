#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_create_fieldrefs.py —— 表驱动「字段引用」重写（改 owner / name / desc）

R356 新工具。比 `patch_create_fields.py` 通用：后者只处理 PushReaction 一族的枚举改名。
`getstatic/putstatic/getfield/putfield` 的解析键是 `class_index + name_and_type_index`，
两个都能改、**不需要动任何指令**（操作数长度不变），所以这类修补风险极低。

三种用法（表项可只填想改的字段）：

  * 枚举/常量改名： `KEYSYM` → `KEYBOARD`（owner、desc 不变）
  * 字段搬家/继承： `ItemEntity.hurtMarked` → `Entity.needsSync`（改 owner + name）
  * 字段彻底被删： 指向桥接类的静态字段（`dev/eriksonn/.../ContainerBridge.XXX`）

字段表：`tools/create_field_table.json`

    python tools/patch_create_fieldrefs.py [jar] [--table ...] [--dry-run]
"""
import json
import sys
import zipfile

ROOT = None
DEFAULT_TABLE = "tools/create_field_table.json"
DEFAULT_JAR = "work/run26/mods-aero/create-fly-26.2-6.0.9-2-26.3-patched.jar"


def u2(b, o):
    return int.from_bytes(b[o:o + 2], "big")


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


def utf8_value(buf, start):
    ln = u2(buf, start + 1)
    return buf[start + 3:start + 3 + ln].decode("utf-8", "replace")


def load_table(path):
    raw = json.loads(open(path, encoding="utf-8").read())
    out = []
    for e in raw:
        out.append({
            "owner": e["owner"],
            "name": e["name"],
            "desc": e["desc"],
            "new_owner": e.get("new_owner", e["owner"]),
            "new_name": e.get("new_name", e["name"]),
            "new_desc": e.get("new_desc", e["desc"]),
            "note": e.get("note", ""),
        })
    return out


def patch_class(data, table):
    """返回 (新字节, 命中条数, 明细)。"""
    entries, pool_end = parse_pool(data)
    cp = {}
    idx = 1
    for tag, s, e in entries:
        cp[idx] = (tag, s, e)
        idx += 2 if tag in (5, 6) else 1

    cache = {}

    def u(i):
        if i not in cache:
            cache[i] = utf8_value(data, cp[i][1])
        return cache[i]

    appended = bytearray()
    next_idx = u2(data, 8)      # ★ 必须用原始 cp_count：末位是 long/double 时会占两个槽
    new_utf8 = {}
    new_class = {}
    new_nat = {}

    def add_utf8(sv):
        nonlocal next_idx
        if sv in new_utf8:
            return new_utf8[sv]
        b = sv.encode("utf-8")
        appended.append(1)
        appended.extend(len(b).to_bytes(2, "big"))
        appended.extend(b)
        new_utf8[sv] = next_idx
        next_idx += 1
        return new_utf8[sv]

    def add_class(name):
        nonlocal next_idx
        if name in new_class:
            return new_class[name]
        ui = add_utf8(name)
        appended.append(7)
        appended.extend(ui.to_bytes(2, "big"))
        new_class[name] = next_idx
        next_idx += 1
        return new_class[name]

    def add_nat(nm, ds):
        nonlocal next_idx
        key = (nm, ds)
        if key in new_nat:
            return new_nat[key]
        # ⚠ 先把两个 Utf8 落盘（它们会向 appended 追加），再写 NameAndType，
        # 否则字节顺序会变成 [12][utf8 bytes][index] —— class 文件直接报废。
        ni = add_utf8(nm)
        di = add_utf8(ds)
        appended.append(12)
        appended.extend(ni.to_bytes(2, "big"))
        appended.extend(di.to_bytes(2, "big"))
        new_nat[key] = next_idx
        next_idx += 1
        return new_nat[key]

    patched = bytearray(data)
    hits = []
    for ent in table:
        for i, (tag, s, _e) in cp.items():
            if tag != 9:
                continue
            oi = u2(data, s + 1)
            if cp[oi][0] != 7:
                continue
            if u(u2(data, cp[oi][1] + 1)) != ent["owner"]:
                continue
            nat = u2(data, s + 3)
            if cp[nat][0] != 12:
                continue
            ns = cp[nat][1]
            if u(u2(data, ns + 1)) != ent["name"]:
                continue
            if u(u2(data, ns + 3)) != ent["desc"]:
                continue
            # 命中：改 owner / nat
            if ent["new_owner"] != ent["owner"]:
                patched[s + 1:s + 3] = add_class(ent["new_owner"]).to_bytes(2, "big")
            if (ent["new_name"], ent["new_desc"]) != (ent["name"], ent["desc"]):
                patched[s + 3:s + 5] = add_nat(ent["new_name"], ent["new_desc"]).to_bytes(2, "big")
            hits.append(ent["note"] or ("%s.%s" % (ent["owner"], ent["name"])))
    if not hits:
        return data, 0, []
    out = bytearray()
    out += patched[:8]
    out += next_idx.to_bytes(2, "big")
    out += patched[10:pool_end]
    out += appended
    out += patched[pool_end:]
    return bytes(out), len(hits), hits


def main():
    argv = sys.argv[1:]
    dry = "--dry-run" in argv
    table_path = DEFAULT_TABLE
    if "--table" in argv:
        table_path = argv[argv.index("--table") + 1]
        argv = [a for a in argv if a not in ("--table", table_path)]
    args = [a for a in argv if not a.startswith("--")]
    jar = args[0] if args else DEFAULT_JAR
    table = load_table(table_path)
    print("table: %d 条" % len(table))
    for e in table:
        print("   %s.%s -> %s.%s  (%s)" % (e["owner"].split("/")[-1], e["name"],
                                           e["new_owner"].split("/")[-1], e["new_name"], e["note"]))

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
            new, nhit, hits = patch_class(blobs[n], table)
        except Exception as ex:
            print("  [skip] %s: %s" % (n, ex))
            continue
        if nhit:
            blobs[n] = new
            total += nhit
            touched.append((n, nhit, hits))
    print("jar: %s" % jar)
    print("patched classes: %d | fieldref 条目: %d" % (len(touched), total))
    for n, nhit, hits in touched[:40]:
        print("   %-70s %d  %s" % (n[:-6].replace("/", ".")[:70], nhit, hits[0][:40]))
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
