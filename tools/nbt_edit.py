#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nbt_edit.py —— 极简 NBT 读写（只做「删一个键」这类手术），够用就好。

## 为什么需要

26.3 用**自定义世界预设**建的存档会在 `level.dat` 里写入 `enabled_features`
（本轮实测是 `["minecraft:redstone_experiments"]`），于是每次进世界都会先弹：

    不支持使用实验性设置的世界
      创建备份并加载 / 我知道我在做什么！ / 取消

自动验收时这个框会**永久卡住**（日志停在 `Loaded N advancements` 不动）。
`SetCursorPos`+`mouse_event`、`PostMessage(WM_LBUTTONDOWN)` 两种点击**都无效**
（26.3 是 SDL3 后端 "Created window using SDL video driver: windows"，
SDL 不认伪造的鼠标消息）⇒ 干脆把世界侧的 `enabled_features` 删掉。

⚠ 只对**测试存档的副本**用，不要动用户的真实存档。

## 用法

    python tools/nbt_edit.py strip-experimental <level.dat> [--dry-run]

会先写 `<level.dat>.bak-nbt-experimental`，再就地重写。
"""
import gzip
import sys

TAG_END, TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG = 0, 1, 2, 3, 4
TAG_FLOAT, TAG_DOUBLE, TAG_BYTE_ARRAY, TAG_STRING = 5, 6, 7, 8
TAG_LIST, TAG_COMPOUND, TAG_INT_ARRAY, TAG_LONG_ARRAY = 9, 10, 11, 12


class R:
    def __init__(self, b):
        self.b = b
        self.i = 0

    def u1(self):
        v = self.b[self.i]
        self.i += 1
        return v

    def i2(self):
        v = int.from_bytes(self.b[self.i:self.i + 2], "big", signed=True)
        self.i += 2
        return v

    def i4(self):
        v = int.from_bytes(self.b[self.i:self.i + 4], "big", signed=True)
        self.i += 4
        return v

    def i8(self):
        v = int.from_bytes(self.b[self.i:self.i + 8], "big", signed=True)
        self.i += 8
        return v

    def f4(self):
        import struct
        v = struct.unpack(">f", self.b[self.i:self.i + 4])[0]
        self.i += 4
        return v

    def f8(self):
        import struct
        v = struct.unpack(">d", self.b[self.i:self.i + 8])[0]
        self.i += 8
        return v

    def raw(self, n):
        v = self.b[self.i:self.i + n]
        self.i += n
        return v

    def string(self):
        n = int.from_bytes(self.b[self.i:self.i + 2], "big", signed=False)
        self.i += 2
        return self.raw(n).decode("utf-8", "replace")

    def payload(self, t):
        if t == TAG_BYTE:
            return self.u1()
        if t == TAG_SHORT:
            return self.i2()
        if t == TAG_INT:
            return self.i4()
        if t == TAG_LONG:
            return self.i8()
        if t == TAG_FLOAT:
            return self.f4()
        if t == TAG_DOUBLE:
            return self.f8()
        if t == TAG_BYTE_ARRAY:
            n = self.i4()
            return self.raw(n)
        if t == TAG_STRING:
            return self.string()
        if t == TAG_LIST:
            et = self.u1()
            n = self.i4()
            return (et, [self.payload(et) for _ in range(n)])
        if t == TAG_COMPOUND:
            out = []
            while True:
                tt = self.u1()
                if tt == TAG_END:
                    return out
                name = self.string()
                out.append((tt, name, self.payload(tt)))
        if t == TAG_INT_ARRAY:
            n = self.i4()
            return [self.i4() for _ in range(n)]
        if t == TAG_LONG_ARRAY:
            n = self.i4()
            return [self.i8() for _ in range(n)]
        raise ValueError("unknown tag %d at %d" % (t, self.i))


def wstr(s):
    b = s.encode("utf-8")
    return len(b).to_bytes(2, "big") + b


def wtag(t, name, v, out):
    """写一个**带名字**的 tag（compound 成员 / 根 tag）。"""
    out.append(bytes([t]))
    out.append(wstr(name))
    wpayload(t, v, out)


def wpayload(t, v, out):
    """只写 tag 的 **payload**（list 元素就是纯 payload，不带 tag 字节/名字）。"""
    import struct
    if t == TAG_BYTE:
        out.append(bytes([v & 0xFF]))
    elif t == TAG_SHORT:
        out.append(int(v).to_bytes(2, "big", signed=True))
    elif t == TAG_INT:
        out.append(int(v).to_bytes(4, "big", signed=True))
    elif t == TAG_LONG:
        out.append(int(v).to_bytes(8, "big", signed=True))
    elif t == TAG_FLOAT:
        out.append(struct.pack(">f", v))
    elif t == TAG_DOUBLE:
        out.append(struct.pack(">d", v))
    elif t == TAG_BYTE_ARRAY:
        out.append(len(v).to_bytes(4, "big", signed=True) + bytes(v))
    elif t == TAG_STRING:
        out.append(wstr(v))
    elif t == TAG_LIST:
        et, items = v
        out.append(bytes([et]))
        out.append(len(items).to_bytes(4, "big", signed=True))
        for it in items:
            wpayload(et, it, out)
    elif t == TAG_COMPOUND:
        for tt, nm, vv in v:
            wtag(tt, nm, vv, out)
        out.append(b"\x00")
    elif t == TAG_INT_ARRAY:
        out.append(len(v).to_bytes(4, "big", signed=True))
        for x in v:
            out.append(int(x).to_bytes(4, "big", signed=True))
    elif t == TAG_LONG_ARRAY:
        out.append(len(v).to_bytes(4, "big", signed=True))
        for x in v:
            out.append(int(x).to_bytes(8, "big", signed=True))
    else:
        raise ValueError(t)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    mode, path = sys.argv[1], sys.argv[2]
    dry = "--dry-run" in sys.argv
    raw = gzip.open(path, "rb").read()
    r = R(raw)
    t = r.u1()
    name = r.string()
    root = r.payload(t)
    removed = []

    def strip(compound, where=""):
        keep = []
        for tt, nm, vv in compound:
            if nm == "enabled_features":
                removed.append("%s/%s" % (where, nm))
                continue
            if tt == TAG_COMPOUND:
                strip(vv, where + "/" + nm)
            keep.append((tt, nm, vv))
        compound[:] = keep

    if mode == "strip-experimental":
        strip(root)
    elif mode == "clean-feature-flags":
        # 1.21.x 的三个实验性 flag：26.3 里不再作为 flag 存在，但老存档的
        # `DataPacks.Disabled` 里还留着 ⇒ 26.3 每次进世界都弹「不支持使用实验性设置的世界」。
        FLAGS = {"minecart_improvements", "redstone_experiments", "trade_rebalance"}

        def clean(comp):
            for tt, nm, vv in comp:
                if tt == TAG_COMPOUND:
                    clean(vv)
                elif tt == TAG_LIST and nm == "Disabled":
                    et, items = vv
                    keep = [x for x in items if x not in FLAGS]
                    if len(keep) != len(items):
                        removed.append("%s: %s" % (nm, sorted(set(items) - set(keep))))
                        vv[1][:] = keep

        clean(root)
    else:
        print("未知模式 %s" % mode)
        return 2

    print("删掉的键: %s" % (removed or "（没有）"))
    if not removed:
        return 0
    if dry:
        print("dry-run -> 未写文件")
        return 0
    # 备份：raw 是**解压后**的 NBT 字节，直接存成 .bak-nbt 文件（不是再压一层）
    open(path + ".bak-nbt-experimental", "wb").write(raw)
    buf = []
    wtag(t, name, root, buf)
    data = b"".join(buf)
    with gzip.open(path, "wb") as f:
        f.write(data)
    print("写出 %s（NBT %d B，原 NBT %d B）" % (path, len(data), len(raw)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

