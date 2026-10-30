# -*- coding: utf-8 -*-
"""cf.py —— 极简 class 文件读写器（26.3 字节码移植专用）

只做「结构编辑」：
  * 改 super_class / interfaces（class→interface 家族）
  * 替换 / 新增 / 删除方法（可同时改描述符）
  * 改方法访问标志
常量池只**追加**（索引稳定），方法/字段/属性的原始字节整体搬运。

用法示例：
    cf = ClassFile(blob)
    cf.set_super("java/lang/Object")
    cf.set_interfaces(["net/minecraft/world/level/levelgen/feature/Feature"])
    cf.replace_method("place", OLD_DESC, NEW_DESC,
                      body=[0x03, 0xAC], max_stack=1, max_locals=5)
    cf.add_method("codec", "()Lcom/mojang/serialization/MapCodec;", 0x0001,
                  body=[...], max_stack=1, max_locals=1)
    blob2 = cf.write()

每个动作都会返回 "changed"/"skip" 字符串，便于幂等闸。
"""
import struct


def u1(b, o):
    return b[o]


def u2(b, o):
    return int.from_bytes(b[o:o + 2], "big")


def u4(b, o):
    return int.from_bytes(b[o:o + 4], "big")


# 常量池条目长度（不含 tag 字节）；tag 5/6 占两个槽
_CP_LEN = {1: None, 3: 4, 4: 4, 5: 8, 6: 8, 7: 2, 8: 2, 9: 4, 10: 4, 11: 4,
           12: 4, 15: 3, 16: 2, 17: 4, 18: 4, 19: 2, 20: 2}

ACC_PUBLIC = 0x0001
ACC_PRIVATE = 0x0002
ACC_PROTECTED = 0x0004
ACC_STATIC = 0x0008
ACC_FINAL = 0x0010


class ClassFile(object):
    def __init__(self, buf):
        self.orig = buf
        self.magic = u4(buf, 0)
        self.minor = u2(buf, 4)
        self.major = u2(buf, 6)
        pos = 10
        count = u2(buf, 8)
        self.cp = {}          # idx -> (tag, payload_start, payload_end)
        self.cp_order = []
        i = 1
        while i < count:
            tag = buf[pos]
            if tag == 1:
                ln = u2(buf, pos + 1)
                end = pos + 3 + ln
            else:
                if tag not in _CP_LEN:
                    raise ValueError("unknown cp tag %d @%d" % (tag, pos))
                end = pos + 1 + _CP_LEN[tag]
            self.cp[i] = (tag, pos + 3 if tag == 1 else pos + 1, end)
            self.cp_order.append((i, tag, pos, end))
            pos = end
            i += 2 if tag in (5, 6) else 1
        self.pool_end = pos
        self.next_idx = count
        self.appended = bytearray()
        self._added = {}      # (tag, owner, name, desc) -> cp idx（本次运行内去重）
        self._added_class = {}

        self.access = u2(buf, pos)
        self.this_idx = u2(buf, pos + 2)
        self.super_idx = u2(buf, pos + 4)
        p = pos + 6
        n = u2(buf, p)
        self.interfaces = [u2(buf, p + 2 + 2 * k) for k in range(n)]
        p += 2 + 2 * n

        self.fields = []
        nf = u2(buf, p)
        p += 2
        for _ in range(nf):
            f = {"access": u2(buf, p), "name_idx": u2(buf, p + 2),
                 "desc_idx": u2(buf, p + 4),
                 "name": self.utf8(u2(buf, p + 2)),
                 "desc": self.utf8(u2(buf, p + 4)), "attrs": []}
            ac = u2(buf, p + 6)
            p += 8
            for _ in range(ac):
                an = u2(buf, p)
                ln = u4(buf, p + 2)
                f["attrs"].append((an, buf[p + 6:p + 6 + ln]))
                p += 6 + ln
            self.fields.append(f)

        self.methods = []
        nm = u2(buf, p)
        p += 2
        for _ in range(nm):
            m = {"access": u2(buf, p), "name_idx": u2(buf, p + 2),
                 "desc_idx": u2(buf, p + 4),
                 "name": self.utf8(u2(buf, p + 2)),
                 "desc": self.utf8(u2(buf, p + 4)), "attrs": []}
            ac = u2(buf, p + 6)
            p += 8
            for _ in range(ac):
                an = u2(buf, p)
                ln = u4(buf, p + 2)
                m["attrs"].append((an, buf[p + 6:p + 6 + ln]))
                p += 6 + ln
            self.methods.append(m)

        self.attrs = []
        na = u2(buf, p)
        p += 2
        for _ in range(na):
            an = u2(buf, p)
            ln = u4(buf, p + 2)
            self.attrs.append((an, buf[p + 6:p + 6 + ln]))
            p += 6 + ln
        self.tail_end = p

    # ---------------------------------------------------------------- cp
    def utf8(self, idx):
        tag, s, e = self.cp[idx]
        if tag != 1:
            raise ValueError("cp %d not utf8 (tag %d)" % (idx, tag))
        return self.orig[s:s + (e - s)].decode("utf-8", "replace")

    def class_name(self, idx):
        tag, s, _e = self.cp[idx]
        if tag != 7:
            raise ValueError("cp %d not class" % idx)
        return self.utf8(u2(self.orig, s))

    def add_utf8(self, s):
        b = s.encode("utf-8")
        self.appended.append(1)
        self.appended.extend(len(b).to_bytes(2, "big"))
        self.appended.extend(b)
        i = self.next_idx
        self.next_idx += 1
        return i

    def add_class(self, name):
        if name in self._added_class:
            return self._added_class[name]
        existing = self.find_class(name)
        if existing is not None:
            self._added_class[name] = existing
            return existing
        ui = self.add_utf8(name)
        self.appended.append(7)
        self.appended.extend(ui.to_bytes(2, "big"))
        i = self.next_idx
        self.next_idx += 1
        self._added_class[name] = i
        return i

    def _find_utf8(self, s):
        for idx, (tag, st, e) in self.cp.items():
            if tag == 1 and self.orig[st:e].decode("utf-8", "replace") == s:
                return idx
        return None

    def find_class(self, name):
        for idx, (tag, st, _e) in self.cp.items():
            if tag == 7:
                ui = u2(self.orig, st)
                t2, s2, e2 = self.cp[ui]
                if t2 == 1 and self.orig[s2:e2].decode("utf-8", "replace") == name:
                    return idx
        return None

    def class_ref(self, name):
        """找到或追加 Class 条目。"""
        i = self.find_class(name)
        return i if i is not None else self.add_class(name)

    def add_nameandtype(self, name, desc):
        ni = self.add_utf8(name)
        di = self.add_utf8(desc)
        self.appended.append(12)
        self.appended.extend(ni.to_bytes(2, "big"))
        self.appended.extend(di.to_bytes(2, "big"))
        i = self.next_idx
        self.next_idx += 1
        return i

    def add_member_ref(self, tag, owner, name, desc):
        key = (tag, owner, name, desc)
        if key in self._added:
            return self._added[key]
        existing = self.find_ref(owner, name, desc, (tag,))
        if existing is not None:
            self._added[key] = existing
            return existing
        ci = self.class_ref(owner)
        nt = self.add_nameandtype(name, desc)
        self.appended.append(tag)
        self.appended.extend(ci.to_bytes(2, "big"))
        self.appended.extend(nt.to_bytes(2, "big"))
        i = self.next_idx
        self.next_idx += 1
        self._added[key] = i
        return i

    def add_methodref(self, owner, name, desc):
        return self.add_member_ref(10, owner, name, desc)

    def add_ifacemethodref(self, owner, name, desc):
        return self.add_member_ref(11, owner, name, desc)

    def add_fieldref(self, owner, name, desc):
        return self.add_member_ref(9, owner, name, desc)

    def find_ref(self, owner, name, desc, tags=(9, 10, 11)):
        for idx, (tag, st, _e) in self.cp.items():
            if tag not in tags:
                continue
            oi = u2(self.orig, st)
            if self.cp[oi][0] != 7:
                continue
            if self.utf8(u2(self.orig, self.cp[oi][1])) != owner:
                continue
            nat = u2(self.orig, st + 2)
            if self.cp[nat][0] != 12:
                continue
            ns = self.cp[nat][1]
            if self.utf8(u2(self.orig, ns)) != name:
                continue
            if self.utf8(u2(self.orig, ns + 2)) != desc:
                continue
            return idx
        return None

    def find_string(self, s):
        for idx, (tag, st, _e) in self.cp.items():
            if tag == 8 and self.utf8(u2(self.orig, st)) == s:
                return idx
        return None

    # ---------------------------------------------------------------- 编辑
    def set_super(self, name):
        cur = self.class_name(self.super_idx) if self.super_idx else None
        if cur == name:
            return "skip(super 已是 %s)" % name
        self.super_idx = self.class_ref(name)
        return "super %s -> %s" % (cur, name)

    def set_interfaces(self, names):
        cur = [self.class_name(i) for i in self.interfaces]
        if sorted(cur) == sorted(names):
            return "skip(interfaces 已一致)"
        self.interfaces = [self.class_ref(n) for n in names]
        return "interfaces %s -> %s" % (cur, names)

    def get_method(self, name, desc):
        for m in self.methods:
            if m["name"] == name and m["desc"] == desc:
                return m
        return None

    def has_method(self, name, desc):
        return self.get_method(name, desc) is not None

    def set_method_access(self, name, desc, access):
        m = self.get_method(name, desc)
        if m is None:
            return "skip(方法不存在 %s%s)" % (name, desc)
        if m["access"] == access:
            return "skip(access 已是 %#06x)" % access
        old = m["access"]
        m["access"] = access
        return "%s access %#06x -> %#06x" % (name, old, access)

    def _code_attr(self, body, max_stack, max_locals):
        code_name = self._find_utf8("Code")
        if code_name is None:
            code_name = self.add_utf8("Code")
        payload = (max_stack.to_bytes(2, "big") + max_locals.to_bytes(2, "big")
                   + len(body).to_bytes(4, "big") + bytes(body)
                   + b"\x00\x00"                     # exception_table_length
                   + b"\x00\x00")                    # attributes_count
        return (code_name, payload)

    def method_code(self, m):
        """当前方法的 Code 字节（没有 Code 返回 None）。"""
        for an, payload in m["attrs"]:
            if self.utf8(an) == "Code":
                return payload[8:8 + u4(payload, 4)]
        return None

    def replace_method(self, name, old_desc, new_desc, body, max_stack,
                       max_locals, access=None):
        """把 (name, old_desc) 换成 (name, new_desc)，方法体整体替换。

        若已经存在 (name, new_desc) 且不存在 (name, old_desc) ⇒ 视为已修（幂等）。
        """
        if self.has_method(name, new_desc) and not self.has_method(name, old_desc):
            return "skip(%s%s 已是新形态)" % (name, new_desc)
        m = self.get_method(name, old_desc)
        if m is None:
            return "skip(找不到 %s%s)" % (name, old_desc)
        new_access = m["access"] if access is None else access
        if self.method_code(m) == bytes(body) and m["desc"] == new_desc \
                and m["access"] == new_access and len(m["attrs"]) == 1:
            return "skip(%s%s 字节已一致)" % (name, new_desc)
        cm = self.get_method(name, new_desc)
        if cm is not None and old_desc != new_desc:
            # 两个形态都在：删掉旧的（新描述符已经由别的条目建好）
            self.methods.remove(m)
            return "删除旧形态 %s%s" % (name, old_desc)
        if new_desc != m["desc"]:
            m["desc"] = new_desc
            m["desc_idx"] = self.add_utf8(new_desc)
        m["access"] = new_access
        m["attrs"] = [self._code_attr(body, max_stack, max_locals)]
        return "%s%s 体重写（%d 字节，max_stack=%d max_locals=%d）" % (
            name, new_desc, len(body), max_stack, max_locals)

    def add_method(self, name, desc, access, body, max_stack, max_locals):
        if self.has_method(name, desc):
            return "skip(已有 %s%s)" % (name, desc)
        self.methods.append({"access": access, "name": name, "desc": desc,
                             "name_idx": self.add_utf8(name),
                             "desc_idx": self.add_utf8(desc),
                             "attrs": [self._code_attr(body, max_stack, max_locals)]})
        return "新增 %s%s（%d 字节）" % (name, desc, len(body))

    def remove_method(self, name, desc):
        m = self.get_method(name, desc)
        if m is None:
            return "skip(没有 %s%s)" % (name, desc)
        self.methods.remove(m)
        return "删除 %s%s" % (name, desc)

    def set_field_desc(self, name, old_desc, new_desc):
        for f in self.fields:
            if f["name"] == name and f["desc"] == old_desc:
                f["desc"] = new_desc
                f["desc_idx"] = self.add_utf8(new_desc)
                f["attrs"] = []          # Signature 会过期，丢掉
                return "字段 %s 描述符 %s -> %s" % (name, old_desc, new_desc)
        if any(f["name"] == name and f["desc"] == new_desc for f in self.fields):
            return "skip(字段 %s 已是 %s)" % (name, new_desc)
        return "skip(找不到字段 %s:%s)" % (name, old_desc)

    def drop_class_attrs(self):
        if not self.attrs:
            return "skip(没有类属性)"
        n = len(self.attrs)
        self.attrs = []
        return "丢弃 %d 个类属性（Signature 等）" % n

    def set_access(self, access):
        if self.access == access:
            return "skip(access 一致)"
        old = self.access
        self.access = access
        return "access %#06x -> %#06x" % (old, access)

    # ---------------------------------------------------------------- 写
    def write(self):
        out = bytearray()
        out += struct.pack(">IHH", self.magic, self.minor, self.major)
        out += self.next_idx.to_bytes(2, "big")
        out += self.orig[10:self.pool_end]
        out += self.appended
        out += self.access.to_bytes(2, "big")
        out += self.this_idx.to_bytes(2, "big")
        out += self.super_idx.to_bytes(2, "big")
        out += len(self.interfaces).to_bytes(2, "big")
        for i in self.interfaces:
            out += i.to_bytes(2, "big")
        out += len(self.fields).to_bytes(2, "big")
        for f in self.fields:
            out += _member(f, self.cp)
        out += len(self.methods).to_bytes(2, "big")
        for m in self.methods:
            out += _member(m, self.cp)
        out += len(self.attrs).to_bytes(2, "big")
        for an, payload in self.attrs:
            out += an.to_bytes(2, "big")
            out += len(payload).to_bytes(4, "big")
            out += payload
        return bytes(out)


def _member(m, cp=None):
    out = bytearray()
    out += m["access"].to_bytes(2, "big")
    out += m["name_idx"].to_bytes(2, "big")
    out += m["desc_idx"].to_bytes(2, "big")
    out += len(m["attrs"]).to_bytes(2, "big")
    for an, payload in m["attrs"]:
        out += an.to_bytes(2, "big")
        out += len(payload).to_bytes(4, "big")
        out += payload
    return out
