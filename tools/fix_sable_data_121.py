#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_sable_data_121.py —— sable 系附加数据包（sablephysicscompat 这类）的 26.3 数据修复。

## 实测出来的两条（sablephysicscompat-1.3.0 在 26.3 上）

### 1) `physics_block_properties/*.json` 从**数组**变成**单个对象**

26.3 的 sable（`mods-stable/sable-fabric-26.3.jar`）每个文件一个条目：

    { "selector": "#sable:bouncy", "properties": { "sable:restitution": 0.5 }, "overrides": {...} }

而 1.21 时代的 addon 写的是「一个文件一个数组」：

    [ { "selector": "aether:enchanted_gravitite", "properties": {...} }, ... ]

26.3 报错原文：

    Couldn't parse data file 'sable:float' from 'sable:physics_block_properties/float.json':
    DataResult.Error['Not a JSON object: [{"selector":"aether:enchanted_gravitite",...

⇒ 数组要**按条目拆成多个文件**（`<原名>_0.json`、`<原名>_1.json` …）。

### 2) 这些 addon 的 tag JSON 有**尾逗号**，26.3 用严格 JSON 解析（Gson StrictJsonParser）

    Couldn't read tag list sable:bouncy from sable:tags/block/bouncy.json
    Caused by: MalformedJsonException ... at line 11 column 4 path $.values[7]

⇒ 去掉 `,` 后紧跟 `}` / `]` 的尾逗号。

## 用法

    python tools/fix_sable_data_121.py <in.jar> <out.jar> [--dry-run]
"""
import json
import re
import sys
import zipfile

TRAILING = re.compile(r',(\s*[}\]])')


def strip_trailing(txt):
    """去掉 JSON 尾逗号 **和 `//` 行注释**（字符串内的不动：简单状态机）。

    26.3 用 Gson 的 StrictJsonParser，`//` 注释同样会炸：
        MalformedJsonException ... at line 4 column 1 path $.values[0]
    （sablephysicscompat 的 tags/block/float_025.json 等就是这么写的）
    """
    out = []
    i = 0
    n = len(txt)
    in_str = False
    esc = False
    while i < n:
        c = txt[i]
        if in_str:
            out.append(c)
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        if txt.startswith('//', i):
            j = txt.find('\n', i)
            i = n if j < 0 else j      # 丢到行尾（保留换行）
            continue
        if c == ',':
            # 往后看是不是只有空白直到 } 或 ]
            j = i + 1
            while j < n and txt[j] in ' \t\r\n':
                j += 1
            if j < n and txt[j] in '}]':
                i += 1        # 丢掉这个逗号
                continue
        out.append(c)
        i += 1
    return ''.join(out)


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    if len(args) < 2:
        print(__doc__)
        return 2
    src, dst = args[0], args[1]
    z = zipfile.ZipFile(src)
    names = z.namelist()
    blobs = {}
    stats = {"trailing": 0, "split": 0, "files": 0}
    drop = set()
    add = {}
    for n in names:
        b = z.read(n)
        blobs[n] = b
        if not (n.startswith('data/') and n.endswith('.json')):
            continue
        txt = b.decode('utf-8', 'replace')
        try:
            d = json.loads(txt)
        except Exception:
            fixed = strip_trailing(txt)
            try:
                d = json.loads(fixed)
            except Exception:
                stats["bad"] = stats.get("bad", 0) + 1
                continue
            stats["trailing"] += 1
            blobs[n] = fixed.encode('utf-8')
        # physics_block_properties 数组 -> 拆文件
        # ⚠ 命名不能与已有的 float_1.json / float_4.json 撞车（原 jar 里就有这些名字）
        if '/physics_block_properties/' in n and isinstance(d, list):
            drop.add(n)
            stem = n[:-len('.json')]
            for i, entry in enumerate(d):
                newname = '%s_split%d.json' % (stem, i)
                add[newname] = (
                    json.dumps(entry, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
                stats["split"] += 1
            stats["files"] += 1
    print('jar: %s' % src)
    print('  尾逗号修复 %d 个 / physics_block_properties 数组拆文件 %d 个（原 %d 个文件）/ 仍无法解析 %d 个'
          % (stats["trailing"], stats["split"], stats["files"], stats.get("bad", 0)))
    if dry:
        print('dry-run -> 未写文件')
        return 0
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as w:
        for n in names:
            if n in drop:
                continue
            w.writestr(n, blobs[n])
        for n, b in sorted(add.items()):
            w.writestr(n, b)
    print('写出 %s' % dst)
    return 0


if __name__ == '__main__':
    sys.exit(main())
