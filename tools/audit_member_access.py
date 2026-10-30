#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_member_access.py —— 审计「成员存在但访问权限不允许」导致的 IllegalAccessError。

## 为什么需要它（与 audit_create_api.py 互补）

audit_create_api.py 查的是 A/B/C/D（类/方法/字段**不存在**）。
但 26.3 还有一类隐蔽缺口：**成员名字和描述符都在，只是访问权限收紧了**
（比如 `ContextMap$Builder.<init>` 在 26.2 是 public，26.3 变成 private）。
javac 编译期就会拒绝，但我们是**字节码直改**，所以能编过、只在运行期炸：

    java.lang.IllegalAccessError: class A tried to access private method
        'void net.minecraft.util.context.ContextMap$Builder.<init>()'
        at A.<clinit>(A.java:21)

而且它炸的时机极坏：`ExtendedUnbakedGeometry.<clinit>` 一炸 → ModelManager 的
reload listener 抛错 → SimpleReloadInstance 的共享 PreparationBarrier 失败 →
AtlasManager 的 allReadyToUpload 永远不完成 → 一个 atlas 都不建 → 全黑。

## 判定规则（JLS 6.6.1 / JVMS 5.4.4 访问检查）

对每个 Methodref/Fieldref（owner 在 MC jar 内）沿继承链解析出**声明类** member：
  * private   : 引用类 != 声明类            -> 必炸
  * (default) : 引用类与声明类不同包        -> 必炸
  * protected : 不同包 且 引用类不是声明类的子类 -> 必炸
public 或同包 -> OK。

## 用法

    python tools/audit_member_access.py                 # 默认扫 work/run26/mods-aero/*.jar
    python tools/audit_member_access.py --jar X.jar ... # 指定 jar
输出：notes/member-access-audit.txt
"""
import argparse
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MC_HOME = Path(r"C:\Users\95959\AppData\Roaming\.minecraft")
DEFAULT_MC = MC_HOME / "versions" / "26.3" / "26.3.jar"
DEFAULT_MODS = ROOT / "work" / "run26" / "mods-aero"
OUT_TXT = ROOT / "notes" / "member-access-audit.txt"

ACC_PUBLIC = 0x0001
ACC_PRIVATE = 0x0002
ACC_PROTECTED = 0x0004
ACC_STATIC = 0x0008
ACC_INTERFACE = 0x0200


def parse_cp(b):
    """返回 (cp, end_offset)。cp[i] = (tag, ...)。"""
    cnt = int.from_bytes(b[8:10], 'big')
    i = 10
    cp = [None] * cnt
    k = 1
    while k < cnt:
        tag = b[i]
        i += 1
        if tag == 1:                      # Utf8
            l = int.from_bytes(b[i:i + 2], 'big')
            i += 2
            cp[k] = (1, b[i:i + l].decode('utf-8', 'replace'))
            i += l
        elif tag in (7, 8, 16, 19, 20):   # Class,String,MethodType,Module,Package
            cp[k] = (tag, int.from_bytes(b[i:i + 2], 'big'))
            i += 2
        elif tag == 15:                   # MethodHandle
            cp[k] = (tag, b[i], int.from_bytes(b[i + 1:i + 3], 'big'))
            i += 3
        elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
            cp[k] = (tag, int.from_bytes(b[i:i + 2], 'big'), int.from_bytes(b[i + 2:i + 4], 'big'))
            i += 4
        elif tag in (5, 6):               # Long,Double 占两个槽
            cp[k] = (tag, None, None)
            i += 8
            k += 1
        else:
            raise ValueError('bad cp tag %d at %d' % (tag, i))
        k += 1
    return cp, i


def utf8(cp, idx):
    e = cp[idx]
    return e[1] if e and e[0] == 1 else None


def class_name(cp, idx):
    e = cp[idx]
    if not e or e[0] != 7:
        return None
    return utf8(cp, e[1])


def ref_target(cp, idx):
    """Methodref/Fieldref -> (owner, name, desc)"""
    e = cp[idx]
    if not e or e[0] not in (9, 10, 11):
        return None
    owner = class_name(cp, e[1])
    nt = cp[e[2]]
    if not nt or nt[0] != 12:
        return None
    return owner, utf8(cp, nt[1]), utf8(cp, nt[2])


def parse_class(b):
    """解析 class 结构：access, this, super, interfaces, methods, fields。"""
    cp, off = parse_cp(b)
    i = off
    access = int.from_bytes(b[i:i + 2], 'big')
    this_c = class_name(cp, int.from_bytes(b[i + 2:i + 4], 'big'))
    super_i = int.from_bytes(b[i + 4:i + 6], 'big')
    super_c = class_name(cp, super_i) if super_i else None
    n = int.from_bytes(b[i + 6:i + 8], 'big')
    i += 8
    ifaces = []
    for _ in range(n):
        ifaces.append(class_name(cp, int.from_bytes(b[i:i + 2], 'big')))
        i += 2

    def members(i):
        count = int.from_bytes(b[i:i + 2], 'big')
        i += 2
        out = {}
        for _ in range(count):
            acc = int.from_bytes(b[i:i + 2], 'big')
            name = utf8(cp, int.from_bytes(b[i + 2:i + 4], 'big'))
            desc = utf8(cp, int.from_bytes(b[i + 4:i + 6], 'big'))
            acount = int.from_bytes(b[i + 6:i + 8], 'big')
            i += 8
            attrs = {}
            for _ in range(acount):
                aname = utf8(cp, int.from_bytes(b[i:i + 2], 'big'))
                alen = int.from_bytes(b[i + 2:i + 6], 'big')
                attrs[aname] = b[i + 6:i + 6 + alen]
                i += 6 + alen
            out[(name, desc)] = (acc, attrs)
        return out, i

    fields, i = members(i)
    methods, i = members(i)
    return {
        'access': access, 'this': this_c, 'super': super_c, 'ifaces': ifaces,
        'fields': fields, 'methods': methods, 'cp': cp,
    }


def load_jar(path):
    """返回 {internal_name: parsed}"""
    out = {}
    z = zipfile.ZipFile(path)
    for n in z.namelist():
        if not n.endswith('.class'):
            continue
        try:
            out[n[:-6]] = parse_class(z.read(n))
        except Exception as e:
            print('  !! parse fail %s: %s' % (n, e), file=sys.stderr)
    return out


def is_subclass(cls, target, classes):
    seen = set()
    while cls and cls not in seen:
        seen.add(cls)
        if cls == target:
            return True
        c = classes.get(cls)
        if not c:
            return False
        cls = c['super']
    return False


def resolve_member(classes, owner, name, desc, kind):
    """沿继承链找声明类；返回 (declaring_class, acc) 或 None。"""
    seen = set()
    stack = [owner]
    while stack:
        c = stack.pop(0)
        if c in seen:
            continue
        seen.add(c)
        info = classes.get(c)
        if not info:
            continue
        table = info['methods'] if kind == 'method' else info['fields']
        if (name, desc) in table:
            return c, table[(name, desc)][0]
        if info['super']:
            stack.append(info['super'])
        stack.extend(info['ifaces'])
    return None


def pkg(internal):
    return internal.rsplit('/', 1)[0] if '/' in internal else ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mc', default=str(DEFAULT_MC))
    ap.add_argument('--jar', action='append', default=[])
    ap.add_argument('--mods', default=str(DEFAULT_MODS))
    args = ap.parse_args()

    print('[1/3] loading MC %s' % args.mc, flush=True)
    mc = load_jar(args.mc)
    print('      %d classes' % len(mc), flush=True)

    jars = [Path(x) for x in args.jar]
    if not jars:
        jars = sorted(Path(args.mods).glob('*.jar'))
    print('[2/3] scanning %d mod jars' % len(jars), flush=True)

    findings = []   # (severity, mod_jar, ref_class, owner, name, desc, decl, acc, reason)
    for jp in jars:
        try:
            mods = load_jar(jp)
        except Exception as e:
            print('  !! skip %s: %s' % (jp.name, e), file=sys.stderr)
            continue
        for cname, info in mods.items():
            cp = info['cp']
            for idx, e in enumerate(cp):
                if not e or e[0] not in (9, 10, 11):
                    continue
                t = ref_target(cp, idx)
                if not t:
                    continue
                owner, name, desc = t
                if owner not in mc:
                    continue          # 不是 MC 的：由 audit_create_api.py 管
                kind = 'field' if e[0] == 9 else 'method'
                r = resolve_member(mc, owner, name, desc, kind)
                if not r:
                    continue          # 不存在 -> A/B/C/D 族，不在这里管
                decl, acc = r
                if acc & ACC_PUBLIC:
                    continue
                ref_pkg, decl_pkg = pkg(cname), pkg(decl)
                if decl == cname:
                    continue          # 同类里访问 private 合法
                if acc & ACC_PRIVATE:
                    reason = 'private'
                elif acc & ACC_PROTECTED:
                    if ref_pkg == decl_pkg:
                        continue
                    if is_subclass(cname, decl, mc):
                        continue
                    reason = 'protected(cross-pkg, not subclass)'
                else:                     # package-private
                    if ref_pkg == decl_pkg:
                        continue
                    reason = 'package-private(cross-pkg)'
                findings.append((jp.name, cname, decl, name, desc, kind, reason, acc))

    print('[3/3] %d illegal refs' % len(findings), flush=True)
    lines = []
    lines.append('# member-access audit  (MC 26.3)')
    lines.append('')
    if not findings:
        lines.append('OK: 无访问权限缺口。')
    else:
        # 按 (decl, name, desc) 聚合
        agg = defaultdict(list)
        for f in findings:
            agg[(f[2], f[3], f[4], f[5], f[6])].append((f[0], f[1]))
        lines.append('| # | 声明类 | 成员 | 原因 | 引用类数 | 引用点 |')
        lines.append('|---|---|---|---|---|---|')
        for i, (k, v) in enumerate(sorted(agg.items(), key=lambda x: -len(x[1])), 1):
            decl, name, desc, kind, reason = k
            refs = sorted({r[1] for r in v})
            lines.append('| %d | `%s` | `%s%s` | %s | %d | %s |' % (
                i, decl, name, desc, reason, len(refs),
                '<br>'.join('`%s`' % r for r in refs[:6]) + ('<br>…' if len(refs) > 6 else '')))
        lines.append('')
        lines.append('## 明细')
        lines.append('')
        for f in findings:
            lines.append('%s :: %s -> %s.%s%s [%s]' % (f[0], f[1], f[2], f[3], f[4], f[6]))
    txt = '\n'.join(lines)
    OUT_TXT.write_text(txt, encoding='utf-8')
    print(txt[:4000])
    print('\n-> %s' % OUT_TXT)


if __name__ == '__main__':
    main()
