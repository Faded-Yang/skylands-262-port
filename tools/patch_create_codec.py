#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_create_codec.py —— 修复 Create-Fly 26.2 在 MC 26.3 上的方块 MapCodec 缺口。

## 为什么需要

26.3 移除了整套方块 MapCodec 体系：`BlockBehaviour.simpleCodec(Function)` 与
`BlockBehaviour.propertiesCodec()` 双双不存在（vanilla 方块已全部零 CODEC）。
但 Create-Fly 26.2 的 31 个方块类仍在 `<clinit>` 里 `invokestatic` 它们：

    java.lang.NoSuchMethodError: 'com.mojang.serialization.MapCodec
      com.zurrtum.create.content.kinetics.steamEngine.SteamEngineBlock.simpleCodec(java.util.function.Function)'
        at ...SteamEngineBlock.<clinit> -> Blocks.register -> AllBlocks.<clinit> -> Bootstrap.bootStrap

## 为什么不用 mixin

Mixin 禁止往目标类合并 non-private static 方法：
    InvalidMixinException: ... contains non-private static method simpleCodec(...)
所以「把方法加回 BlockBehaviour」走不通。

## 本脚本的做法

直接改 class 文件的**常量池**：把这些 `CONSTANT_Methodref` 的 **class_index**
从 `BlockBehaviour` 换成我们自己的桥接类 `dev/eriksonn/aeronautics/compat/BlockCodecBridge`。
**方法名与描述符原样不动** —— JVM 按 `owner + name + descriptor` 解析，改 owner 就等于改目标。

桥接类的两个静态方法与 Create 的调用点描述符完全一致，返回 `MapCodec.unit` 占位
（26.3 不再拿方块 codec 序列化任何东西，该值永不被调用）。

## 用法

    python tools/patch_create_codec.py <create-fly.jar> [--dry-run]

幂等：已打过的 jar 再跑会报告「0 处需改」。
"""
import io
import sys
import zipfile

BRIDGE = "dev/eriksonn/aeronautics/compat/BlockCodecBridge"
TARGET_NAMES = {"simpleCodec", "propertiesCodec"}

# ---- class 文件常量池解析 -------------------------------------------------

def parse_pool(buf):
    """返回 (entries, pool_end_offset)。entries 是 [(tag, start, end, extra)]。

    extra 用于记录 tag 相关字段偏移，方便就地改。
    """
    if buf[:4] != b"\xca\xfe\xba\xbe":
        raise ValueError("not a class file")
    pos = 8
    count = int.from_bytes(buf[pos:pos + 2], "big")
    pos += 2
    entries = []
    i = 1
    while i < count:
        tag = buf[pos]
        start = pos
        if tag == 1:                                  # Utf8
            ln = int.from_bytes(buf[pos + 1:pos + 3], "big")
            pos += 3 + ln
        elif tag in (3, 4):                           # Integer / Float
            pos += 5
        elif tag in (5, 6):                           # Long / Double（占 2 槽）
            pos += 9
        elif tag in (7, 8, 16, 19, 20):               # Class / String / MethodType / Module / Package
            pos += 3
        elif tag in (9, 10, 11, 12, 17, 18):          # Field/Method/InterfaceMethodref / NameAndType / (Invoke)Dynamic
            pos += 5
        elif tag == 15:                               # MethodHandle
            pos += 4
        else:
            raise ValueError("unknown constant pool tag %d at %d" % (tag, pos))
        entries.append((tag, start, pos))
        i += 2 if tag in (5, 6) else 1
    return entries, pos


def utf8_value(buf, tag, start):
    ln = int.from_bytes(buf[start + 1:start + 3], "big")
    return buf[start + 3:start + 3 + ln].decode("utf-8", "replace")


def u2(buf, off):
    return int.from_bytes(buf[off:off + 2], "big")


def patch_class(data):
    """返回 (new_bytes, n_patched)。"""
    entries, pool_end = parse_pool(data)

    # 索引 -> 条目（注意 long/double 占 2 槽，这里按解析顺序就是 cp index 顺序）
    by_index = {}
    idx = 1
    for tag, s, e in entries:
        by_index[idx] = (tag, s, e)
        idx += 2 if tag in (5, 6) else 1

    # 1) 找 Utf8 名字
    name_utf8 = {}
    for cp_idx, (tag, s, e) in by_index.items():
        if tag == 1:
            v = utf8_value(data, tag, s)
            if v in TARGET_NAMES:
                name_utf8.setdefault(v, []).append(cp_idx)
    if not name_utf8:
        return data, 0

    # 2) 找 NameAndType（name_index 命中）
    nat_idx = set()
    for cp_idx, (tag, s, e) in by_index.items():
        if tag == 12 and u2(data, s + 1) in {i for lst in name_utf8.values() for i in lst}:
            nat_idx.add(cp_idx)
    if not nat_idx:
        return data, 0

    # 3) 找 Methodref（name_and_type_index 命中），记录 class_index 字段偏移
    methodrefs = []
    for cp_idx, (tag, s, e) in by_index.items():
        if tag == 10 and u2(data, s + 3) in nat_idx:
            methodrefs.append(s + 1)          # class_index 位于 tag 后第 1 字节
    if not methodrefs:
        return data, 0

    # 4) 追加 Utf8(BRIDGE) 与 Class(->新 Utf8)，拿新 Class 的 cp index
    new_count = max(by_index) + 1
    utf8_bytes = BRIDGE.encode("utf-8")
    appended = bytearray()
    appended.append(1)
    appended += len(utf8_bytes).to_bytes(2, "big")
    appended += utf8_bytes
    bridge_utf8_idx = new_count
    appended.append(7)
    appended += bridge_utf8_idx.to_bytes(2, "big")
    bridge_class_idx = new_count + 1

    # 5) 就地改 class_index
    patched = bytearray(data)
    for off in methodrefs:
        patched[off:off + 2] = bridge_class_idx.to_bytes(2, "big")

    # 6) 更新 constant_pool_count 并插入新条目
    new_pool_count = new_count + 2
    out = bytearray()
    out += patched[:8]
    out += new_pool_count.to_bytes(2, "big")
    out += patched[10:pool_end]
    out += appended
    out += patched[pool_end:]
    return bytes(out), len(methodrefs)


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

    total_sites = 0
    touched = []
    for n in names:
        if not n.endswith(".class"):
            continue
        try:
            new, k = patch_class(blobs[n])
        except Exception as e:
            print("  [skip] %s: %s" % (n, e))
            continue
        if k:
            blobs[n] = new
            total_sites += k
            touched.append((n, k))

    print("jar: %s" % jar)
    print("classes: %d | patched classes: %d | methodref sites: %d"
          % (len(names), len(touched), total_sites))
    for n, k in touched[:12]:
        print("   %-74s %d" % (n.replace('/', '.')[:-6][:74], k))
    if len(touched) > 12:
        print("   ... +%d more" % (len(touched) - 12))

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
