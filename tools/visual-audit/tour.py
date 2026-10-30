# [port-repo] 原路径 scratch/tour.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。
import json, os, subprocess, sys, time, urllib.request, base64
from pathlib import Path
from PIL import Image

ROOT = Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262")
GAME = Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g300\game-vis1")
SHOTS = GAME / "shots" / "tour"
SHOTS.mkdir(parents=True, exist_ok=True)
PY = sys.executable
FOCUS = ROOT / "tools" / "focuswin.py"
cfg = json.loads((GAME / "config" / "mcpfabric.config.json").read_text(encoding="utf-8"))
URL = "http://%s:%d/rpc" % (cfg.get("host","127.0.0.1"), cfg.get("port",25599))
HDRS = {"content-type": "application/json", "authorization": "Bearer " + cfg.get("token","")}

def call(method, params=None):
    body = json.dumps({"method": method, "params": params or {}}).encode()
    req = urllib.request.Request(URL, data=body, headers=HDRS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"transportError": str(e)}

pid = int(subprocess.check_output(["powershell","-NoProfile","-Command",
      "(Get-Process java | Select-Object -First 1).Id"]).decode().strip())

CLIENT = (640, 440)
def click(fx, fy):
    subprocess.run([PY, str(FOCUS), "--pid", str(pid), "--click", "%d,%d" % (CLIENT[0]+fx, CLIENT[1]+fy)],
                   capture_output=True)
    time.sleep(0.55)

def shot(name):
    r = call("vision.screenshot")
    res = r.get("result") or {}
    b64 = res.get("base64")
    if not b64:
        print("NO IMAGE", name, json.dumps(r)[:200]); return None
    p = SHOTS / (name + ".png")
    p.write_bytes(base64.b64decode(b64))
    # title crop + grid area crop
    im = Image.open(p).convert("RGBA")
    im.crop((366, 168, 912, 196)).resize((546*2, 28*2), Image.NEAREST).save(SHOTS / (name + "_title.png"))
    return p

TAB_X = [385, 464, 543, 622, 701, 780, 859]
TAB_Y = 120
GRIDBOX = (366, 205, 906, 525)

# go to page 1
for _ in range(6):
    click(380, 30)
time.sleep(0.5)
state = call("screen.get")
print("screen:", json.dumps(state.get("result")))

manifest = []
for page in range(1, 6):
    for ti, tx in enumerate(TAB_X):
        click(tx, TAB_Y)
        time.sleep(0.35)
        name = "p%d_t%d" % (page, ti + 1)
        p = shot(name)
        sc = call("screen.get").get("result") or {}
        manifest.append({"page": page, "tab": ti + 1, "file": str(p) if p else None,
                         "screen": sc.get("screen"), "inWorld": sc.get("inWorld")})
        print(name, "ok" if p else "FAIL", sc.get("screen"))
    # next page
    click(890, 30)
    time.sleep(0.4)
(SHOTS / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
print("done", len(manifest))
