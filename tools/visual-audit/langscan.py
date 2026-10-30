# [port-repo] 原路径 scratch/langscan.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。

import zipfile, json, re
from pathlib import Path
from collections import defaultdict, Counter

MODS = Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\mods-stable")
VAN = Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\refs\mc26.3\assets")

langs = {"en_us": defaultdict(dict), "zh_cn": defaultdict(dict)}
zips = {}
for j in sorted(MODS.glob("*.jar")):
    try: z = zipfile.ZipFile(j)
    except Exception: continue
    zips[j.name] = z
    for n in z.namelist():
        m = re.match(r"assets/([^/]+)/lang/(en_us|zh_cn)\.json$", n)
        if m:
            ns, lg = m.group(1), m.group(2)
            try: data = json.loads(z.read(n))
            except Exception:
                print("BAD LANG", j.name, n); continue
            langs[lg][ns].update(data)
# vanilla lang
for lg in langs:
    p = VAN / "minecraft" / "lang" / (lg + ".json")
    if p.exists():
        langs[lg]["minecraft"].update(json.loads(p.read_text(encoding="utf-8")))

def has(lg, ns, key):
    return key in langs[lg].get(ns, {}) or ("minecraft" != ns and key in langs[lg].get("minecraft", {}))

# collect item definitions and blockstates per namespace
items = defaultdict(list)
blocks = defaultdict(list)
for name, z in zips.items():
    for n in z.namelist():
        m = re.match(r"assets/([^/]+)/items/(.+)\.json$", n)
        if m: items[m.group(1)].append(m.group(2))
        m = re.match(r"assets/([^/]+)/blockstates/(.+)\.json$", n)
        if m: blocks[m.group(1)].append(m.group(2))

# itemGroup keys used: scan tab registration in lang? approximate: itemGroup.<ns>.*
print("=== creative tab keys present in zh_cn (sample of itemGroup.*) ===")
for ns in sorted(langs["zh_cn"]):
    ks = [k for k in langs["zh_cn"][ns] if k.startswith("itemGroup.")]
    en = [k for k in langs["en_us"][ns] if k.startswith("itemGroup.")]
    if ks or en:
        miss_en = [k for k in ks if k not in langs["en_us"][ns]]
        print(f"{ns:24s} zh_itemGroup={len(ks):2d} en_itemGroup={len(en):2d} zh_not_in_en={len(miss_en)}")

print()
print("=== item/block name keys missing in BOTH en and zh ===")
rows = []
for ns in sorted(items):
    miss = 0; tot = 0
    samples = []
    for p in items[ns]:
        tot += 1
        k_item = f"item.{ns}.{p}"
        k_block = f"block.{ns}.{p}"
        ok = has("en_us", ns, k_item) or has("en_us", ns, k_block)
        ok2 = has("zh_cn", ns, k_item) or has("zh_cn", ns, k_block)
        if not ok and not ok2:
            miss += 1
            if len(samples) < 3: samples.append(p)
    if miss:
        rows.append((ns, miss, tot, samples))
for r in sorted(rows, key=lambda x: -x[1]):
    print(f"{r[0]:24s} missing_both={r[1]:4d}/{r[2]:4d}  {r[3]}")
print()
print("=== item/block name keys missing in zh_cn only (falls back to English) ===")
rows2 = []
for ns in sorted(items):
    miss = 0; tot = 0; samples = []
    for p in items[ns]:
        tot += 1
        ok_en = has("en_us", ns, f"item.{ns}.{p}") or has("en_us", ns, f"block.{ns}.{p}")
        ok_zh = has("zh_cn", ns, f"item.{ns}.{p}") or has("zh_cn", ns, f"block.{ns}.{p}")
        if ok_en and not ok_zh:
            miss += 1
            if len(samples) < 3: samples.append(p)
    if miss: rows2.append((ns, miss, tot, samples))
for r in sorted(rows2, key=lambda x: -x[1])[:25]:
    print(f"{r[0]:24s} missing_zh={r[1]:4d}/{r[2]:4d}  {r[3]}")
