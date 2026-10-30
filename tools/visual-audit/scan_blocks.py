# [port-repo] 原路径 scratch/vis/scan_blocks.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。

import zipfile, re, json
from pathlib import Path
from collections import defaultdict
MODS = Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\mods-stable")
want = ["interiors","createframed","createdieselgenerators","aeroworks","aeronautics","dndecor","createdeco","tfmg","create_connected"]
found = defaultdict(set)
for j in sorted(MODS.glob("*.jar")):
    try: z = zipfile.ZipFile(j)
    except Exception as e: continue
    for n in z.namelist():
        m = re.match(r"assets/([^/]+)/blockstates/(.+).json$", n)
        if m and m.group(1) in want:
            found[m.group(1)].add(m.group(2))
out = {}
for k in want:
    v = sorted(found.get(k, []))
    slash = [x for x in v if "/" in x]
    out[k] = v
    print(f"{k}: {len(v)} blockstates, with-slash={len(slash)}")
    print("   sample:", v[:5])
    if slash: print("   slash sample:", slash[:5])
Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\scratch\vis").mkdir(parents=True, exist_ok=True)
json.dump({k: v for k, v in out.items()}, open(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\scratch\vis\blocklist.json", "w", encoding="utf-8"), ensure_ascii=False)
print("total", sum(len(v) for v in out.values()))
