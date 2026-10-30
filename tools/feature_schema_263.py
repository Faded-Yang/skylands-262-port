#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""feature_schema_263.py —— 从 26.3.jar 反查**每个 feature type 的 JSON schema**（字段名 + 是否必填）。

原理：26.3 里 feature 本身就是 config（记录类实现了 Feature），字段名由
`RecordCodecBuilder` 里的 `ldc "字符串"` + `Codec.fieldOf/optionalFieldOf` 决定。
javap -c 出来就是「字段名 + fieldOf/optionalFieldOf」的序列，机械解析即可。

用法：
    python tools/feature_schema_263.py [--jar <26.3.jar>] [--out schema263.json]
输出：{type: {"class":.., "fields":[{"name":..,"optional":bool}, ...]}}
"""
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

MC = Path(r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar")
JAVAP = Path(r"C:\Users\95959\AppData\Roaming\.minecraft\runtime\java-runtime-epsilon\bin\javap.exe")

# javap 里 `ldc ... // String xxx` 与下一处 fieldOf 的距离
STR_RE = re.compile(r'// String (\S+)$')
CALL_RE = re.compile(r'// InterfaceMethod com/mojang/serialization/(?:Codec|codecs/PrimitiveCodec|MapCodec)\.'
                     r'(optionalFieldOf|fieldOf)')


def cp_strings(z, entry):
    """返回某个 class 的常量池 UTF8 列表（备用：解析类型注册名）。"""
    import struct
    d = z.read(entry)
    i = 8
    n = struct.unpack('>H', d[i:i + 2])[0]
    i += 2
    out = []
    k = 1
    while k < n:
        t = d[i]
        i += 1
        if t == 1:
            l = struct.unpack('>H', d[i:i + 2])[0]
            i += 2
            s = d[i:i + l]
            i += l
            try:
                out.append(s.decode('utf-8'))
            except Exception:
                pass
        elif t in (7, 8, 16, 19, 20):
            i += 2
        elif t == 15:
            i += 3
        elif t in (3, 4, 9, 10, 11, 12, 17, 18):
            i += 4
        elif t in (5, 6):
            i += 8
            k += 1
        else:
            raise RuntimeError("bad cp tag %d" % t)
        k += 1
    return out


def feature_types(z):
    """从 FeatureTypes.class 里按注册名/类名成对抽出 type -> class。"""
    s = cp_strings(z, 'net/minecraft/world/level/levelgen/feature/FeatureTypes.class')
    out = {}
    for i, x in enumerate(s):
        if x.startswith('net/minecraft/world/level/levelgen/feature/') and x.endswith('Feature') \
                and i > 0 and re.fullmatch(r'[a-z0-9_]+', s[i - 1]):
            out['minecraft:' + s[i - 1]] = x.replace('/', '.')
    # 少数类型名不在 FeatureTypes（如 ore，类名 OreFeature 前一条是别的）
    for i, x in enumerate(s):
        if x.startswith('net/minecraft/world/level/levelgen/feature/') and x.endswith('Feature') and i > 0:
            out.setdefault('minecraft:?', '')
    return out


def parse_class(cls, jar):
    """javap -p -c 该类，抓 lambda$static$N 里的 (字段名, 可选) 序列。"""
    r = subprocess.run([str(JAVAP), '-p', '-c', '-cp', str(jar), cls],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0:
        return None
    lines = r.stdout.splitlines()
    fields = []
    for idx, line in enumerate(lines):
        m = STR_RE.search(line)
        if not m:
            continue
        name = m.group(1)
        # 往后 3 行内找 fieldOf/optionalFieldOf
        opt = None
        for j in range(idx + 1, min(idx + 4, len(lines))):
            c = CALL_RE.search(lines[j])
            if c:
                opt = (c.group(1) == 'optionalFieldOf')
                break
        if opt is not None and name not in ('type',):
            fields.append({"name": name, "optional": opt})
    # 去重保序
    seen = set()
    out = []
    for f in fields:
        if f['name'] in seen:
            continue
        seen.add(f['name'])
        out.append(f)
    return out


def superclass(cls, jar):
    r = subprocess.run([str(JAVAP), '-p', '-cp', str(jar), cls],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    m = re.search(r'^(?:public |abstract |final )*(?:class|record) [\w.$]+ extends ([\w.$]+)',
                  r.stdout, re.M)
    if not m:
        return None
    sup = m.group(1)
    return sup if not sup.startswith('java.') else None


def parse_class_chain(cls, jar, depth=3):
    """字段可能在父类里建 codec（如 OreFeature -> AbstractOreFeature）。
    返回 None = javap 失败；返回 [] = 该类确实没有 config 字段（如 blue_ice）。"""
    cur = cls
    last = None
    for _ in range(depth):
        if not cur:
            break
        f = parse_class(cur, jar)
        if f is None:
            return last
        if f:
            return f
        last = f
        cur = superclass(cur, jar)
    return last if last is not None else []


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    jar = MC
    out_path = Path('schema263.json')
    extra = []
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == '--jar':
            jar = Path(args[i + 1])
        elif a == '--out':
            out_path = Path(args[i + 1])
        elif a == '--class':
            extra.append(args[i + 1])
    if extra:
        for c in extra:
            f = parse_class_chain(c, jar)
            print('%-72s %s' % (c, ', '.join(x['name'] + ('?' if x['optional'] else '') for x in f or [])),
                  flush=True)
        return
    z = zipfile.ZipFile(jar)
    types = feature_types(z)
    res = {}
    for t, cls in sorted(types.items()):
        if not cls:
            continue
        f = parse_class_chain(cls, jar)
        if f is None:
            print('JAVAP FAIL', t, cls, flush=True)
            continue
        res[t] = {"class": cls, "fields": f}
        print('%-42s %-40s %s' % (t, cls.rsplit('.', 1)[-1],
                                  ', '.join(x['name'] + ('?' if x['optional'] else '') for x in f)), flush=True)
    out_path.write_text(json.dumps(res, indent=1), encoding='utf-8')
    print('\n%d types -> %s' % (len(res), out_path), flush=True)


if __name__ == '__main__':
    main()
