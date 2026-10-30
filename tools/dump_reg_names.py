#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dump_reg_names.py —— 从某个 jar 的 class 常量池里抽「注册名」字符串（用于两个版本对照）。

用法: python dump_reg_names.py <jar> <内部类名…>
"""
import re
import struct
import sys
import zipfile


def cp_strings(d):
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
            raise RuntimeError('tag %d' % t)
        k += 1
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    z = zipfile.ZipFile(sys.argv[1])
    for cls in sys.argv[2:]:
        try:
            d = z.read(cls.replace('.', '/') + '.class')
        except KeyError:
            print(cls, 'MISSING')
            continue
        s = cp_strings(d)
        names = [x for x in s if re.fullmatch(r'[a-z0-9_]{2,40}', x)]
        # 去掉明显不是注册名的
        skip = {'registry', 'bootstrap', 'codec', 'field', 'java'}
        names = [x for x in names if x not in skip and not x.startswith('lambda')]
        print('%s: %s' % (cls, sorted(set(names))))


if __name__ == '__main__':
    main()
