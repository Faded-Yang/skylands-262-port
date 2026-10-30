#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_create_ctxmap.py —— 修 `ContextMap.Builder` 在 MC 26.3 的访问权限收紧 + 改名。

## 背景（黑屏的真正中止点）

26.3 的 `net.minecraft.util.context.ContextMap`：
    public static ContextMap.Builder builder();     // 唯一入口
    private ContextMap.Builder();                   // **private**！26.2 是 public
    Builder.build(ContextKeySet) ??  -> 实际是 buildAndValidate(ContextKeySet) / build()

Create 26.2 写的是 `new ContextMap.Builder()` + `Builder.create(ContextKeySet)`：
    new  #Builder      -> [uninit]
    dup                -> [uninit, uninit]
    invokespecial #<init>()V   -> 触发 IllegalAccessError（private）
    invokevirtual #create(LContextKeySet;)LContextMap;

后果链（实测）：
    ExtendedUnbakedGeometry.<clinit> IllegalAccessError
      -> ObjGeometry <clinit> 失败（NoClassDefFoundError: Could not initialize class）
      -> ModelManager.loadBlockModels 的 future 失败
      -> SimpleReloadInstance 的**共享 PreparationBarrier** 失败
      -> AtlasManager.reload 的 allReadyToUpload 永不 thenAccept
      -> TextureAtlas.createTexture 一次都没调用 -> 一条 `Created: ...-atlas` 都没有 -> 全黑

## 修法（指令长度不变 ⇒ 不影响任何偏移/StackMapTable）

1. `new Builder; dup; invokespecial <init>()V`（3+1+3 = 7 字节）
   -> `invokestatic ContextMap.builder()`（3）+ 4×`nop`（4）= 7 字节
   栈效果完全一致（原地留下一个已初始化的 Builder），max_stack 不变。
2. `Builder.create(LContextKeySet;)LContextMap;` -> 新 Methodref `buildAndValidate`（同描述符，3 字节改索引）
   `Builder.create()LContextMap;`                -> 新 Methodref `build`（同描述符）

## 用法

    python tools/patch_create_ctxmap.py --dry-run
    python tools/patch_create_ctxmap.py
"""
import argparse
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JAR = ROOT / "work" / "run26" / "mods-aero" / "create-fly-26.2-6.0.9-2-26.3-patched.jar"
BAK_SUFFIX = ".bak-black"

CTX = "net/minecraft/util/context/ContextMap"
BLD = "net/minecraft/util/context/ContextMap$Builder"
BLD_DESC = "Lnet/minecraft/util/context/ContextMap$Builder;"
KS_DESC = "(Lnet/minecraft/util/context/ContextKeySet;)Lnet/minecraft/util/context/ContextMap;"
NOARG_DESC = "()Lnet/minecraft/util/context/ContextMap;"


def u2(b, o):
    return int.from_bytes(b[o:o + 2], "big")


def u4(b, o):
    return int.from_bytes(b[o:o + 4], "big")


def parse_pool(buf):
    pos = 10
    count = u2(buf, 8)
    entries = []          # (tag, start, end) 按 index 顺序（long/double 只占一项）
    i = 1
    while i < count:
        tag = buf[pos]
        s = pos
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
        entries.append((tag, s, pos))
        i += 2 if tag in (5, 6) else 1
    return entries, pos, count


# --------------------------------------------------------------- 指令长度表
LEN = [1] * 256
for op, n in [(0x10, 2), (0x11, 3), (0x12, 2), (0x13, 3), (0x14, 3),
              (0x84, 3), (0xa9, 2), (0xbc, 2), (0xc5, 4), (0xc8, 5), (0xc9, 5)]:
    LEN[op] = n
for op in range(0x15, 0x1a):      # iload..aload
    LEN[op] = 2
for op in range(0x36, 0x3b):      # istore..astore
    LEN[op] = 2
for op in range(0x99, 0xa9):      # if*/goto/jsr
    LEN[op] = 3
for op in range(0xb2, 0xb9):      # getstatic..invokestatic
    LEN[op] = 3
LEN[0xb9] = 5                     # invokeinterface
LEN[0xba] = 5                     # invokedynamic
LEN[0xbb] = 3                     # new
LEN[0xbd] = 3                     # anewarray
LEN[0xc0] = 3                     # checkcast
LEN[0xc1] = 3                     # instanceof
LEN[0xc6] = 3                     # ifnull
LEN[0xc7] = 3                     # ifnonnull


def decode(code, start, end):
    """线性解码，yield (offset, opcode, length)。

    ⚠ tableswitch/lookupswitch 的 padding 是相对**code 数组起点**（JVMS 6.5），
    不是相对 class 文件偏移 —— 用绝对偏移对齐会漂移（已踩过）。
    """
    base = start
    i = start
    while i < end:
        op = code[i]
        if op == 0xaa:                          # tableswitch
            p = base + ((i - base + 4) & ~3)
            lo = int.from_bytes(code[p + 4:p + 8], "big", signed=True)
            hi = int.from_bytes(code[p + 8:p + 12], "big", signed=True)
            n = p + 12 + (hi - lo + 1) * 4 - i
        elif op == 0xab:                        # lookupswitch
            p = base + ((i - base + 4) & ~3)
            npairs = int.from_bytes(code[p + 4:p + 8], "big", signed=True)
            n = p + 8 + npairs * 8 - i
        elif op == 0xc4:                        # wide
            n = 6 if code[i + 1] == 0x84 else 4
        else:
            n = LEN[op]
        yield i, op, n
        i += n


class Cf:
    def __init__(self, buf):
        self.buf = buf
        self.entries, self.pool_end, cp_count = parse_pool(buf)
        self.cp = {}
        i = 1
        for tag, s, e in self.entries:
            self.cp[i] = (tag, s, e)
            i += 2 if tag in (5, 6) else 1
        self.next_idx = cp_count
        self.appended = bytearray()
        self.dirty = False

    # -- cp 读取
    def utf8(self, idx):
        tag, s, _ = self.cp[idx]
        if tag != 1:
            raise ValueError("cp %d not utf8" % idx)
        return self.buf[s + 3:s + 3 + u2(self.buf, s + 1)].decode("utf-8", "replace")

    def class_name(self, idx):
        tag, s, _ = self.cp[idx]
        if tag != 7:
            return None
        return self.utf8(u2(self.buf, s + 1))

    def find_class(self, name):
        for idx, (tag, s, _e) in self.cp.items():
            if tag == 7 and self.utf8(u2(self.buf, s + 1)) == name:
                return idx
        return None

    def find_ref(self, owner, name, desc):
        for idx, (tag, s, _e) in self.cp.items():
            if tag not in (10, 11):
                continue
            if self.class_name(u2(self.buf, s + 1)) != owner:
                continue
            nat = u2(self.buf, s + 3)
            _t, ns, _ne = self.cp[nat]
            if self.utf8(u2(self.buf, ns + 1)) != name:
                continue
            if self.utf8(u2(self.buf, ns + 3)) != desc:
                continue
            return idx
        return None

    # -- cp 追加
    def _add_utf8(self, s):
        b = s.encode()
        self.appended.append(1)
        self.appended += len(b).to_bytes(2, "big")
        self.appended += b
        i = self.next_idx
        self.next_idx += 1
        return i

    def _add_class(self, name):
        ui = self._add_utf8(name)
        self.appended.append(7)
        self.appended += ui.to_bytes(2, "big")
        i = self.next_idx
        self.next_idx += 1
        return i

    def add_methodref(self, owner, name, desc, owner_class_idx=None):
        ci = owner_class_idx if owner_class_idx else self._add_class(owner)
        ni = self._add_utf8(name)
        di = self._add_utf8(desc)
        self.appended.append(12)
        self.appended += ni.to_bytes(2, "big")
        self.appended += di.to_bytes(2, "big")
        nat = self.next_idx
        self.next_idx += 1
        self.appended.append(10)
        self.appended += ci.to_bytes(2, "big")
        self.appended += nat.to_bytes(2, "big")
        i = self.next_idx
        self.next_idx += 1
        return i

    # -- attribute 遍历
    def _methods(self):
        buf = self.buf
        pos = self.pool_end + 6
        ic = u2(buf, pos)
        pos += 2 + 2 * ic
        fc = u2(buf, pos)
        pos += 2
        for _ in range(fc):
            ac = u2(buf, pos + 6)
            pos += 8
            for _ in range(ac):
                pos += 6 + u4(buf, pos + 2)
        mc = u2(buf, pos)
        pos += 2
        out = []
        for _ in range(mc):
            base = pos
            nm = self.utf8(u2(buf, pos + 2))
            ds = self.utf8(u2(buf, pos + 4))
            ac = u2(buf, pos + 6)
            pos += 8
            code = None
            for _ in range(ac):
                an = self.utf8(u2(buf, pos))
                ln = u4(buf, pos + 2)
                if an == "Code":
                    code = (pos + 14, u4(buf, pos + 10))
                pos += 6 + ln
            out.append((nm, ds, code))
        return out

    def serialize(self):
        if not self.appended:
            return self.buf
        head = bytearray(self.buf[0:8])
        head += self.next_idx.to_bytes(2, "big")
        return bytes(head) + self.buf[10:self.pool_end] + bytes(self.appended) + self.buf[self.pool_end:]


def patch_class(buf, name):
    cf = Cf(buf)
    builder_cls = cf.find_class(BLD)
    if builder_cls is None:
        return None
    ctor_ref = cf.find_ref(BLD, "<init>", "()V")
    create_ks = cf.find_ref(BLD, "create", KS_DESC)
    create_0 = cf.find_ref(BLD, "create", NOARG_DESC)
    if ctor_ref is None and create_ks is None and create_0 is None:
        return None

    rep = {"class": name, "ctor_sites": 0, "create_ks": 0, "create_0": 0}

    new_builder_ref = None
    if ctor_ref is not None:
        ctx_cls = cf.find_class(CTX) or cf._add_class(CTX)
        new_builder_ref = cf.add_methodref(CTX, "builder", "()" + BLD_DESC, owner_class_idx=ctx_cls)
    ks_ref_new = None
    if create_ks is not None:
        ks_ref_new = cf.add_methodref(BLD, "buildAndValidate", KS_DESC, owner_class_idx=builder_cls)
    c0_ref_new = None
    if create_0 is not None:
        c0_ref_new = cf.add_methodref(BLD, "build", NOARG_DESC, owner_class_idx=builder_cls)

    data = bytearray(cf.buf)
    for mname, mdesc, code in cf._methods():
        if not code:
            continue
        cstart, clen = code
        end = cstart + clen
        # 1) new Builder; dup; invokespecial <init>
        if ctor_ref is not None:
            insts = list(decode(data, cstart, end))
            for k, (off, op, ln) in enumerate(insts):
                if op != 0xbb or u2(data, off + 1) != builder_cls:
                    continue
                if k + 2 >= len(insts):
                    continue
                o1, op1, _l1 = insts[k + 1]
                o2, op2, _l2 = insts[k + 2]
                if op1 != 0x59 or op2 != 0xb7 or u2(data, o2 + 1) != ctor_ref:
                    raise ValueError("%s.%s%s: new Builder 后面不是 dup/invokespecial，未处理 (off=%d)"
                                     % (name, mname, mdesc, off))
                data[off] = 0xB8                      # invokestatic
                data[off + 1:off + 3] = new_builder_ref.to_bytes(2, "big")
                for p in (off + 3, off + 4, off + 5, off + 6):
                    data[p] = 0x00                    # nop
                rep["ctor_sites"] += 1
        # 2) create -> buildAndValidate / build（同长度，只换索引）
        if ks_ref_new is not None or c0_ref_new is not None:
            for off, op, _ln in decode(data, cstart, end):
                if op not in (0xb6, 0xb7, 0xb8, 0xb9):
                    continue
                idx = u2(data, off + 1)
                if ks_ref_new is not None and idx == create_ks:
                    data[off + 1:off + 3] = ks_ref_new.to_bytes(2, "big")
                    rep["create_ks"] += 1
                elif c0_ref_new is not None and idx == create_0:
                    data[off + 1:off + 3] = c0_ref_new.to_bytes(2, "big")
                    rep["create_0"] += 1

    if rep["ctor_sites"] + rep["create_ks"] + rep["create_0"] == 0:
        return None
    cf.buf = bytes(data)
    return cf.serialize(), rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jar", default=str(DEFAULT_JAR))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    jar = Path(args.jar)
    zin = zipfile.ZipFile(jar)
    plan = {}
    for n in zin.namelist():
        if not n.endswith(".class"):
            continue
        try:
            r = patch_class(zin.read(n), n[:-6])
        except ValueError as e:
            print("!! %s" % e, file=sys.stderr)
            continue
        if r:
            plan[n] = r

    if not plan:
        print("没有需要修的 ContextMap.Builder 用法。")
        return

    print("将改 %d 个 class：" % len(plan))
    tot = 0
    for n, (_b, rep) in sorted(plan.items()):
        print("  %-70s new->builder:%d  create(ks)->buildAndValidate:%d  create()->build:%d"
              % (n, rep["ctor_sites"], rep["create_ks"], rep["create_0"]))
        tot += rep["ctor_sites"] + rep["create_ks"] + rep["create_0"]
    print("合计 %d 处" % tot)

    if args.dry_run:
        return

    bak = jar.with_name(jar.name + BAK_SUFFIX)
    if not bak.exists():
        shutil.copy2(jar, bak)
        print("备份 -> %s" % bak.name)
    else:
        print("备份已存在，保留: %s" % bak.name)

    tmp = jar.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = plan[item.filename][0] if item.filename in plan else zin.read(item.filename)
            zi = zipfile.ZipInfo(item.filename, date_time=item.date_time)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = item.external_attr
            zout.writestr(zi, data)
    zin.close()
    shutil.move(str(tmp), str(jar))
    print("已写入 %s" % jar)


if __name__ == "__main__":
    main()
