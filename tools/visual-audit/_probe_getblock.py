# [port-repo] 原路径 scratch/vis/_probe_getblock.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import block_audit as ba
br = ba.Bridge(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g300\game-vis1")
for pos in [(0,101,2), (-4,101,0), (8,101,8)]:
    r = br.call("world.getBlock", {"x": pos[0], "y": pos[1], "z": pos[2]})
    print(pos, json.dumps(r)[:300])
