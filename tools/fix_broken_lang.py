#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_broken_lang.py —— 修复损坏的 `zh_cn.json`（这两个文件让 386 条缺口被隐藏了很久）。

## 两个真实故障

1. **`createframed`**：文件里有一行 `// Translator's note: ...` 行注释 —— **JSON 不允许注释**。
   ⇒ 需要**在字符串感知的前提下**剥掉 `//` 行注释（不能简单按 `//` 切，因为译文本体可能含 `//`）。
2. **`ends_delight`**：文件以 **UTF-8 BOM**（`EF BB BF`）开头 ⇒ 用 `utf-8-sig` 解码即可。

## 安全策略

- 改之前备份 `<jar>.bak-langfix`
- 修复后**必须重新 `json.loads` 验证**
- 只动 `assets/*/lang/zh_cn.json`，其他条目原样回写
- 输出「修复前/后条数」与「是否仍损坏」

## 用法

    python tools/fix_broken_lang.py [--mods <dir>]
"""
import json
import os
import shutil
import sys
import zipfile

BASE = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
MODS = os.path.join(BASE, "work", "run26", "mods-stable")


def strip_line_comments(text):
    """在字符串感知的前提下剥掉 `//` 行注释（保留字符串里的 //）。"""
    out_lines = []
    for line in text.split("\n"):
        buf = []
        in_str = False
        esc = False
        i = 0
        cut = None
        while i < len(line):
            ch = line[i]
            if in_str:
                buf.append(ch)
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                    buf.append(ch)
                elif ch == "/" and i + 1 < len(line) and line[i + 1] == "/":
                    cut = i
                    break
                else:
                    buf.append(ch)
            i += 1
        out_lines.append("".join(buf).rstrip())
    return "\n".join(out_lines)


def try_parse(text):
    """依次尝试：原样 → utf-8-sig 去 BOM → 剥注释 → 两者都做。返回 (dict, 用的策略) 或 (None, 错误)"""
    attempts = [
        ("原样", text, False),
        ("去BOM", text.lstrip("\ufeff"), False),
        ("剥注释", text, True),
        ("去BOM+剥注释", text.lstrip("\ufeff"), True),
    ]
    last = None
    for name, body, strip in attempts:
        cand = strip_line_comments(body) if strip else body
        try:
            d = json.loads(cand)
            if isinstance(d, dict) and d:
                return d, name
        except Exception as e:
            last = str(e)[:70]
    return None, last


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    mods = MODS
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--mods":
            mods = argv[i + 1]

    fixed = 0
    for f in sorted(os.listdir(mods)):
        if not f.endswith(".jar"):
            continue
        path = os.path.join(mods, f)
        try:
            z = zipfile.ZipFile(path)
        except Exception:
            continue
        data = {n: z.read(n) for n in z.namelist()}
        z.close()
        changed = False
        for n in list(data):
            if not (n.startswith("assets/") and n.endswith("/lang/zh_cn.json")):
                continue
            raw = data[n]
            try:
                json.loads(raw.decode("utf-8"))
                continue          # 已经合法，不动
            except Exception:
                pass
            text = raw.decode("utf-8", "replace")
            d, how = try_parse(text)
            if d is None:
                print("  ★ %-40s %-40s 修不了: %s" % (f[:40], n.split("/")[1], how))
                continue
            data[n] = (json.dumps(d, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
            changed = True
            print("  ✅ %-40s %-20s %d 条（策略：%s）" % (f[:40], n.split("/")[1], len(d), how))
        if changed:
            shutil.copy2(path, path + ".bak-langfix")
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as w:
                for n, b in data.items():
                    w.writestr(n, b)
            fixed += 1
    print("\n修复 jar: %d 个" % fixed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
