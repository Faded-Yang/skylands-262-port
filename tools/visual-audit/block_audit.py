# [port-repo] 原路径 scratch/vis/block_audit.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。
#!/usr/bin/env python3
"""block_audit.py — 游戏内方块渲染审计（mcpfabric bridge + Pillow 判定）

做什么
------
在固定平台上按 9x5 网格 setblock 一批方块，用**旁观模式**相机从正上方固定高度俯拍
（旁观模式无重力，相机不会掉，坐标可精确复现），对每个方块的顶面采样，
统计品红(#FF00FF family)像素占比 => 判定 missing texture。

几何为什么可靠
--------------
所有方块顶面都在 y=TOP_Y 平面，相机俯视 pitch=90：
世界平面(x,z) -> 屏幕(u,v) 是一个单应变换。用平台四角 4 个彩色混凝土标记块
（红/蓝/绿/黄）自动求 H（DLT），残差可打印。之后每个格子的采样区域由 H 投影得到，
因此窗口大小/DPR/FOV 变化都不需要写死。

用法
----
python block_audit.py --setup                 # 建平台+标记+相机，存一张校准图
python block_audit.py --ns interiors          # 审一个 namespace
python block_audit.py --ns interiors --ns aeroworks --limit 90
python block_audit.py --report                # 只根据已有 JSON 出 markdown
"""
import argparse, base64, json, os, re, sys, time, urllib.request
import numpy as np
from PIL import Image, ImageDraw

GAME_DEFAULT = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g300\game-vis1"
ROOT = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"

# ---- 世界几何（都是确定值）----
PLATFORM_Y = 100
BLOCK_Y = 101
TOP_Y = 102            # 方块顶面所在平面
GRID_X0, GRID_X1 = -4, 4     # 9 列
GRID_Z0, GRID_Z1 = 0, 4      # 5 行
CAM_EYE = (0.5, 114.0, 2.5)  # 眼高；feet = eye - 1.62
MARKERS = [((-6, -2), "minecraft:red_concrete"), ((6, -2), "minecraft:blue_concrete"),
           ((-6, 6), "minecraft:lime_concrete"), ((6, 6), "minecraft:yellow_concrete")]
MAGENTA_TH = 0.05          # 品红占比阈值

NS_ORDER = ["interiors", "createframed", "createdieselgenerators", "aeroworks", "aeronautics",
            "dndecor", "createdeco", "tfmg", "create_connected"]


def log(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------- bridge
class Bridge:
    def __init__(self, game_dir):
        cfg_path = os.path.join(game_dir, "config", "mcpfabric.config.json")
        cfg = json.load(open(cfg_path, encoding="utf-8"))
        self.url = "http://%s:%s/rpc" % (cfg.get("host", "127.0.0.1"), cfg.get("port", 25599))
        self.token = cfg.get("token", "")
        self.out_dir = os.path.join(game_dir, "shots")
        os.makedirs(self.out_dir, exist_ok=True)

    def call(self, method, params=None, timeout=60):
        body = json.dumps({"method": method, "params": params or {}}).encode()
        req = urllib.request.Request(self.url, data=body, headers={
            "content-type": "application/json", "authorization": "Bearer " + self.token})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())

    def cmd(self, command, timeout=60):
        return self.call("command.run", {"command": command}, timeout=timeout)

    def screenshot(self, path):
        body = self.call("vision.screenshot", {}, timeout=120)
        b64 = _find_png(body)
        if not b64:
            raise RuntimeError("no png in screenshot response: " + json.dumps(body)[:300])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(base64.b64decode(b64))
        return path


def _find_png(o, depth=0):
    if depth > 8 or o is None:
        return None
    if isinstance(o, str):
        if len(o) > 5000 and re.fullmatch(r"[A-Za-z0-9+/=\s]+", o[:300]):
            return o
        return None
    if isinstance(o, dict):
        for v in o.values():
            r = _find_png(v, depth + 1)
            if r: return r
    elif isinstance(o, list):
        for v in o:
            r = _find_png(v, depth + 1)
            if r: return r
    return None


# ---------------------------------------------------------------- 场景搭建
def setup_scene(br):
    """建平台 + 4 个标记块 + 旁观模式相机。返回状态 dict。"""
    steps = []
    def run(c):
        r = br.cmd(c)
        ok = bool(r.get("ok"))
        steps.append((c, ok, (r.get("error") or {}).get("message")))
        return ok

    run("gamemode spectator @a")
    run("time set day")
    run("weather clear")
    run("gamerule doDaylightCycle false")
    # 平台（15x11 smooth_stone）+ 清出上方空间
    run("fill -7 100 -3 7 100 7 minecraft:smooth_stone")
    run("fill -7 %d -3 7 %d 7 minecraft:air" % (BLOCK_Y, BLOCK_Y + 4))
    # 标记块
    for (x, z), blk in MARKERS:
        run("setblock %d %d %d %s" % (x, BLOCK_Y, z, blk))
    # 相机：旁观模式无重力，精确落到眼高
    feet = CAM_EYE[1] - 1.62
    run("tp @a %s %s %s 0 90" % (CAM_EYE[0], round(feet, 3), CAM_EYE[2]))
    return steps


# ---------------------------------------------------------------- 标定
# 思路：把平台 15x11 用 4 块大色块铺满（红/蓝/绿/黄），拍一张，检测四个色块的屏幕中心。
# 四块的世界中心坐标是确定的 => 4 点求单应 H（世界 y=TOP_Y 平面 -> 屏幕）。
# 大色块用「行/列投影阈值」定位，避免世界里同色像素（红色蘑菇）干扰。
QUADRANTS = [
    ("red_concrete", (-3.0, 0.0), "platform-red"),
    ("blue_concrete", (5.0, 0.0), "platform-blue"),
    ("lime_concrete", (-3.0, 6.0), "platform-lime"),
    ("yellow_concrete", (5.0, 6.0), "platform-yellow"),
]

def solve_homography(src, dst):
    """4+ 点 DLT 求单应矩阵 H：世界(x,z) -> 屏幕(u,v)。"""
    A = []
    for (x, z), (u, v) in zip(src, dst):
        A.append([-x, -z, -1, 0, 0, 0, u * x, u * z, u])
        A.append([0, 0, 0, -x, -z, -1, v * x, v * z, v])
    A = np.asarray(A, dtype=np.float64)
    _, _, Vt = np.linalg.svd(A)
    H = Vt[-1].reshape(3, 3)
    return H / H[2, 2]


def apply_h(H, x, z):
    p = H @ np.array([x, z, 1.0])
    return p[0] / p[2], p[1] / p[2]


QUAD_FILL = [
    ("-7 101 -3 0 101 2", "minecraft:red_concrete"),
    ("1 101 -3 8 101 2", "minecraft:blue_concrete"),
    ("-7 101 3 0 101 8", "minecraft:lime_concrete"),
    ("1 101 3 8 101 8", "minecraft:yellow_concrete"),
]


def _saturated(a, thr=95):
    r = a[..., 0].astype(np.int16); g = a[..., 1].astype(np.int16); b = a[..., 2].astype(np.int16)
    mx = np.maximum(np.maximum(r, g), b); mn = np.minimum(np.minimum(r, g), b)
    return (mx - mn) >= thr


def _longest_run(profile, frac=0.45):
    if profile.max() <= 0:
        return None
    idx = np.nonzero(profile >= profile.max() * frac)[0]
    if len(idx) == 0:
        return None
    groups = np.split(idx, np.where(np.diff(idx) > 3)[0] + 1)
    best = max(groups, key=lambda g: g[-1] - g[0])
    return int(best[0]), int(best[-1])


# 四种混凝土顶面的近似色度（归一化），用于按最近邻判定象限颜色
CHROMA_PROTOS = {
    "red_concrete": np.array([1.00, 0.30, 0.28]),
    "blue_concrete": np.array([0.32, 0.36, 1.00]),
    "lime_concrete": np.array([0.62, 1.00, 0.22]),
    "yellow_concrete": np.array([1.00, 0.82, 0.16]),
}
# 每个世界象限的外角（平台边界 x[-7,9], z[-3,9]）
WORLD_CORNER = {"red_concrete": (-7.0, -3.0), "blue_concrete": (9.0, -3.0),
                "lime_concrete": (-7.0, 9.0), "yellow_concrete": (9.0, 9.0)}


def _hue_family(rgb):
    v = np.asarray(rgb, dtype=np.float64)
    if v.max() < 40:
        return None
    c = v / v.max()
    best, bestd = None, 1e9
    for name, proto in CHROMA_PROTOS.items():
        d = float(np.linalg.norm(c - proto))
        if d < bestd:
            best, bestd = name, d
    return best if bestd < 0.45 else None


def calibrate(br, shot_path, debug_out=None):
    """铺 4 个大色块 -> 截图 -> 定位平台矩形 -> 四象限按色相归位 -> 用四角求 H -> 恢复平台。"""
    for cmd_fill, blk in QUAD_FILL:
        br.cmd("fill %s %s" % (cmd_fill, blk))
    time.sleep(0.35)
    br.screenshot(shot_path)
    im = Image.open(shot_path).convert("RGB")
    a = np.asarray(im)
    sat = _saturated(a)
    run_x = _longest_run(sat.sum(axis=0))
    run_y = _longest_run(sat.sum(axis=1))
    if run_x is None or run_y is None:
        raise RuntimeError("platform rectangle not found (sat px=%d)" % int(sat.sum()))
    px0, px1 = run_x; py0, py1 = run_y
    mx, my = (px0 + px1) // 2, (py0 + py1) // 2
    quads = {"TL": (px0, py0, mx, my), "TR": (mx + 1, py0, px1, my),
             "BL": (px0, my + 1, mx, py1), "BR": (mx + 1, my + 1, px1, py1)}
    detail = {}
    for qname, (x0, y0, x1, y1) in quads.items():
        w = x1 - x0; h = y1 - y0
        core = a[y0 + h // 8:y1 - h // 8 + 1, x0 + w // 8:x1 - w // 8 + 1]
        mean_rgb = core.reshape(-1, 3).mean(axis=0)
        detail[qname] = dict(rect=[x0, y0, x1, y1], mean=[int(v) for v in mean_rgb],
                             family=_hue_family(mean_rgb))
    fams = {q: d["family"] for q, d in detail.items()}
    if len(set(fams.values()) - {None}) < 4:
        raise RuntimeError("quadrant colors not identified: %s" % json.dumps(detail))
    # 屏幕四角 <-> 世界四角（由四象限颜色唯一确定）
    src = [WORLD_CORNER[fams["TL"]], WORLD_CORNER[fams["TR"]],
           WORLD_CORNER[fams["BL"]], WORLD_CORNER[fams["BR"]]]
    dst = [(px0, py0), (px1, py0), (px0, py1), (px1, py1)]
    H = solve_homography(src, dst)
    res = []
    for (x, z), (u, v) in zip(src, dst):
        pu, pv = apply_h(H, x, z)
        res.append(round(((pu - u) ** 2 + (pv - v) ** 2) ** 0.5, 1))
    u0, v0 = apply_h(H, 0.0, 0.0); u1, v1 = apply_h(H, 1.0, 0.0); u2, v2 = apply_h(H, 0.0, 1.0)
    cell_x = round(((u1 - u0) ** 2 + (v1 - v0) ** 2) ** 0.5, 1)
    cell_z = round(((u2 - u0) ** 2 + (v2 - v0) ** 2) ** 0.5, 1)
    # 合理性校验：x/z 方向格子尺寸应接近
    if not (0.75 < cell_x / max(cell_z, 0.1) < 1.33):
        raise RuntimeError("bad homography: cell_px=%s quadrants=%s" % ((cell_x, cell_z), json.dumps(fams)))
    br.cmd("fill -7 101 -3 9 101 9 minecraft:air")
    br.cmd("fill -7 100 -3 9 100 9 minecraft:smooth_stone")
    for (x, z), blk in MARKERS:
        br.cmd("setblock %d %d %d %s" % (x, BLOCK_Y, z, blk))
    info = dict(platform_rect=[px0, py0, px1, py1], quadrant_family=fams,
                reproj_residual_px=res, cell_px=[cell_x, cell_z], H=H.tolist(),
                image=os.path.abspath(shot_path))
    if debug_out:
        d = im.copy(); dr = ImageDraw.Draw(d)
        dr.rectangle([px0, py0, px1, py1], outline=(0, 255, 255), width=2)
        for gx in range(GRID_X0, GRID_X1 + 2):
            pu0, pv0 = apply_h(H, gx, GRID_Z0); pu1, pv1 = apply_h(H, gx, GRID_Z1 + 1)
            dr.line([pu0, pv0, pu1, pv1], fill=(0, 255, 0), width=1)
        for gz in range(GRID_Z0, GRID_Z1 + 2):
            pu0, pv0 = apply_h(H, GRID_X0, gz); pu1, pv1 = apply_h(H, GRID_X1 + 1, gz)
            dr.line([pu0, pv0, pu1, pv1], fill=(0, 255, 0), width=1)
        d.save(debug_out)
        info["debug"] = os.path.abspath(debug_out)
    return H, info


def save_H(path, H, info):
    json.dump(dict(H=H.tolist(), info=info), open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def load_H(path):
    d = json.load(open(path, encoding="utf-8"))
    return np.asarray(d["H"], dtype=np.float64), d["info"]


def verify_H(br, H, tmp_shot):
    """验证相机没动：平台中心应该还是石头灰，四角标记还在。"""
    br.screenshot(tmp_shot)
    im = Image.open(tmp_shot).convert("RGB")
    a = np.asarray(im)
    ok = 0
    for (x, z), _ in MARKERS:
        u, v = apply_h(H, x + 0.5, z + 0.5)
        ui, vi = int(round(u)), int(round(v))
        if 0 <= ui < im.width and 0 <= vi < im.height:
            px = a[vi, ui]
            if px.max() - px.min() > 25:   # 标记块是彩色的
                ok += 1
    return ok >= 3, ok


# ---------------------------------------------------------------- 判定
def cell_stats(im, H, gx, gz, inset=0.20):
    """投影该格顶面内部四边形，统计颜色。"""
    corners = [(gx + inset, gz + inset), (gx + 1 - inset, gz + inset),
               (gx + 1 - inset, gz + 1 - inset), (gx + inset, gz + 1 - inset)]
    poly = [apply_h(H, x, z) for x, z in corners]
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    x0 = max(0, int(min(xs)) - 1); x1 = min(im.width, int(max(xs)) + 2)
    y0 = max(0, int(min(ys)) - 1); y1 = min(im.height, int(max(ys)) + 2)
    if x1 <= x0 or y1 <= y0:
        return dict(magenta=0.0, black=0.0, uniq=0, mean=[0, 0, 0], px=0)
    local = [(u - x0, v - y0) for u, v in poly]
    mask = Image.new("1", (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(mask).polygon(local, fill=1)
    m = np.asarray(mask, dtype=bool)
    crop = np.asarray(im.crop((x0, y0, x1, y1)).convert("RGB")).astype(np.int16)
    px = crop[m]
    n = len(px)
    if n == 0:
        return dict(magenta=0.0, black=0.0, uniq=0, mean=[0, 0, 0], px=0)
    r, g, b = px[:, 0], px[:, 1], px[:, 2]
    mag = ((r >= 170) & (b >= 170) & (g <= 100) & (g < r - 90) & (g < b - 90)).mean()
    checker = ((r >= 170) & (b >= 170) & (g <= 100)).mean()
    blk = ((r <= 32) & (g <= 32) & (b <= 32)).mean()
    uniq = len(np.unique(px, axis=0))
    return dict(magenta=round(float(mag), 4), magenta_loose=round(float(checker), 4),
                black=round(float(blk), 4), uniq=int(uniq),
                mean=[int(v) for v in px.mean(axis=0)], px=int(n))


def annotate(path, out_path, H, records):
    im = Image.open(path).convert("RGB")
    d = ImageDraw.Draw(im)
    for rec in records:
        gx, gz = rec["gx"], rec["gz"]
        corners = [(gx + .15, gz + .15), (gx + .85, gz + .15), (gx + .85, gz + .85), (gx + .15, gz + .85)]
        poly = [apply_h(H, x, z) for x, z in corners]
        col = {"MISSING": (255, 0, 0), "NOT_PLACED": (0, 140, 255)}.get(rec["verdict"], (0, 200, 0))
        d.polygon(poly, outline=col)
        if rec["verdict"] != "OK":
            d.text((poly[0][0] + 2, poly[0][1] + 2), rec["verdict"][:3], fill=col)
    im.save(out_path)
    return os.path.abspath(out_path)


# ---------------------------------------------------------------- 批处理
def audit_namespace(br, ns, blocks, H, out_dir, shot_dir, th=MAGENTA_TH, max_blocks=None):
    ns_dir = os.path.join(out_dir, ns)
    os.makedirs(ns_dir, exist_ok=True)
    results = []
    cells = [(x, z) for z in range(GRID_Z0, GRID_Z1 + 1) for x in range(GRID_X0, GRID_X1 + 1)]
    total = len(blocks) if max_blocks is None else min(len(blocks), max_blocks)
    blocks = blocks[:total]
    batches = [blocks[i:i + len(cells)] for i in range(0, len(blocks), len(cells))]
    for bi, batch in enumerate(batches):
        t0 = time.time()
        br.cmd("fill %d %d %d %d %d %d minecraft:air"
               % (GRID_X0, BLOCK_Y, GRID_Z0, GRID_X1, BLOCK_Y, GRID_Z1))
        bad_set = []
        for (gx, gz), blk in zip(cells, batch):
            r = br.cmd("setblock %d %d %d %s" % (gx, BLOCK_Y, gz, blk))
            if not r.get("ok"):
                bad_set.append((blk, (r.get("error") or {}).get("message")))
        time.sleep(0.30)
        shot = os.path.join(shot_dir, "%s-b%02d.png" % (ns, bi))
        br.screenshot(shot)
        im = Image.open(shot).convert("RGB")
        recs = []
        for (gx, gz), blk in zip(cells, batch):
            st = cell_stats(im, H, gx, gz)
            missing = st["magenta"] >= th
            verdict = "MISSING" if missing else "OK"
            recs.append(dict(block=blk, gx=gx, gz=gz, verdict=verdict, **st))
        ann = annotate(shot, os.path.join(ns_dir, "%s-b%02d-audit.png" % (ns, bi)), H, recs)
        for rec in recs:
            rec.update(ns=ns, batch=bi, shot=os.path.abspath(shot), annotated=ann)
        results.extend(recs)
        nmiss = sum(1 for r in recs if r["verdict"] == "MISSING")
        log("[%s] batch %d/%d: %d blocks, missing=%d, %d setblock errors, %.1fs"
            % (ns, bi + 1, len(batches), len(batch), nmiss, len(bad_set), time.time() - t0))
        json.dump(results, open(os.path.join(ns_dir, "results.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    return results


def verify_markers(im, H, min_ok=3):
    """标记块（彩色混凝土）应仍在单应预测的位置；否则说明相机/世界变了，网格不可信。"""
    a = np.asarray(im)
    ok = 0
    for (x, z), _ in MARKERS:
        u, v = apply_h(H, x + 0.5, z + 0.5)
        ui, vi = int(round(u)), int(round(v))
        if not (6 <= ui < im.width - 6 and 6 <= vi < im.height - 6):
            continue
        win = a[vi - 6:vi + 7, ui - 6:ui + 7].reshape(-1, 3).astype(int)
        sat = win.max(axis=1) - win.min(axis=1)
        if float((sat > 60).mean()) > 0.5:
            ok += 1
    return ok >= min_ok


def audit_blocks(br, ns, blocks, H, out_dir, shot_dir, th=MAGENTA_TH, batch_cb=None):
    """按 45 个一批跑，返回 records。"""
    cells = [(x, z) for z in range(GRID_Z0, GRID_Z1 + 1) for x in range(GRID_X0, GRID_X1 + 1)]
    results = []
    n_batches = (len(blocks) + len(cells) - 1) // len(cells)
    for bi in range(n_batches):
        batch = blocks[bi * len(cells):(bi + 1) * len(cells)]
        t0 = time.time()
        br.cmd("fill %d %d %d %d %d %d minecraft:air"
               % (GRID_X0, BLOCK_Y, GRID_Z0, GRID_X1, BLOCK_Y, GRID_Z1))
        for (gx, gz), blk in zip(cells, batch):
            br.cmd("setblock %d %d %d %s" % (gx, BLOCK_Y, gz, blk))
        time.sleep(0.30)
        shot = os.path.join(shot_dir, "%s-b%02d.png" % (ns, bi))
        br.screenshot(shot)
        im = Image.open(shot).convert("RGB")
        # 先验证相机没动；一旦漂移立即停，宁可不产数据也不要错数
        if not verify_markers(im, H):
            log("[%s] %d/%d ABORT: camera moved, homography stale -> rerun --setup + --calibrate-only"
                % (ns, bi + 1, n_batches))
            return results
        # 权威核查：命令说成功不代表方块真的在（canSurvive/替换/被流体冲掉）
        actual = {}
        for (gx, gz), blk in zip(cells, batch):
            r = br.call("world.getBlock", {"x": gx, "y": BLOCK_Y, "z": gz})
            actual[(gx, gz)] = str(((r.get("result") or {}).get("id") or "?")).lower()
        recs = [dict(block=blk, gx=gx, gz=gz, actual=actual[(gx, gz)], **cell_stats(im, H, gx, gz))
                for (gx, gz), blk in zip(cells, batch)]
        for rec in recs:
            if rec["actual"] != rec["block"]:
                rec["verdict"] = "NOT_PLACED"
            elif rec["magenta"] >= th:
                rec["verdict"] = "MISSING"
            else:
                rec["verdict"] = "OK"
        ann = annotate(shot, os.path.join(out_dir, ns, "%s-b%02d-audit.png" % (ns, bi)), H, recs)
        for rec in recs:
            rec.update(ns=ns, batch=bi, shot=os.path.abspath(shot), annotated=ann)
        results.extend(recs)
        nmiss = sum(1 for r in recs if r["verdict"] == "MISSING")
        log("[%s] %d/%d: %d blocks, missing=%d, %.1fs  (%s)" %
            (ns, bi + 1, n_batches, len(batch), nmiss, time.time() - t0, os.path.basename(shot)),)
        if batch_cb:
            batch_cb(ns, bi, recs)
    return results


def write_namespace_reports(results, out_dir):
    by_ns = {}
    for r in results:
        by_ns.setdefault(r["ns"], []).append(r)
    for ns, recs in by_ns.items():
        ns_dir = os.path.join(out_dir, ns); os.makedirs(ns_dir, exist_ok=True)
        json.dump(recs, open(os.path.join(ns_dir, "results.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        with open(os.path.join(ns_dir, "results.csv"), "w", encoding="utf-8") as f:
            f.write("block,actual,verdict,magenta,magenta_loose,black,uniq,mean_r,mean_g,mean_b,gx,gz,batch,shot,annotated\n")
            for r in recs:
                f.write(",".join(str(v) for v in [
                    r["block"], r.get("actual", ""), r["verdict"], r["magenta"], r.get("magenta_loose", ""),
                    r["black"], r["uniq"], *r["mean"], r["gx"], r["gz"], r["batch"], r["shot"], r["annotated"]]) + "\n")
    return by_ns


def write_global_report(by_ns, out_md):
    order = [n for n in NS_ORDER if n in by_ns] + [n for n in by_ns if n not in NS_ORDER]
    lines = ["# 游戏内方块渲染审计（自动判定：品红像素占比 >= %.0f%% => missing texture）" % (MAGENTA_TH * 100),
             "", "| namespace | 已测方块 | MISSING | 占比 | 备注 |", "|---|---|---|---|---|"]
    tot = miss = 0
    for ns in order:
        recs = by_ns[ns]
        m = [r for r in recs if r["verdict"] == "MISSING"]
        tot += len(recs); miss += len(m)
        lines.append("| %s | %d | %d | %.1f%% | |" % (ns, len(recs), len(m), 100.0 * len(m) / max(len(recs), 1)))
    lines.append("| **合计** | **%d** | **%d** | **%.1f%%** | |" % (tot, miss, 100.0 * miss / max(tot, 1)))
    lines += ["", "## 破损清单", ""]
    for ns in order:
        m = [r for r in by_ns[ns] if r["verdict"] == "MISSING"]
        if not m:
            continue
        lines.append("### " + ns)
        lines.append("| block | 品红占比 | 格子(x,z) | 截图 |")
        lines.append("|---|---|---|---|")
        for r in sorted(m, key=lambda x: -x["magenta"]):
            lines.append("| %s | %.1f%% | %d,%d | %s |" % (r["block"], r["magenta"] * 100, r["gx"], r["gz"],
                                                          os.path.relpath(r["shot"], os.path.dirname(out_md))))
        lines.append("")
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    open(out_md, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return out_md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=GAME_DEFAULT)
    ap.add_argument("--setup", action="store_true")
    ap.add_argument("--calibrate-only", action="store_true")
    ap.add_argument("--ns", action="append", default=[])
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--th", type=float, default=MAGENTA_TH)
    args = ap.parse_args()

    out_dir = os.path.join(ROOT, "scratch", "vis", "blockaudit")
    os.makedirs(out_dir, exist_ok=True)
    shot_dir = os.path.join(args.game, "shots")
    H_path = os.path.join(out_dir, "homography.json")
    br = Bridge(args.game)

    if args.setup:
        for c, ok, err in setup_scene(br):
            log(("  OK  " if ok else "  FAIL") + "  " + c + ("" if ok else "   <- " + str(err)))
        time.sleep(3.0)   # 等 "gamemode updated" toast 消失
        log("setup done")
        return 0

    if args.calibrate_only or not os.path.exists(H_path):
        shot = os.path.join(shot_dir, "audit-calib.png")
        H, info = calibrate(br, shot, debug_out=os.path.join(out_dir, "audit-calib-debug.png"))
        save_H(H_path, H, info)
        log(json.dumps({k: v for k, v in info.items() if k != "H"}, ensure_ascii=False, indent=1))
        if args.calibrate_only:
            return 0
    else:
        H, info = load_H(H_path)
        log("loaded H, cell_px=%s" % (info.get("cell_px"),))

    blocklist = json.load(open(os.path.join(ROOT, "scratch", "vis", "blocklist.json"), encoding="utf-8"))
    nss = args.ns or NS_ORDER
    all_results = []
    for ns in nss:
        blocks = ["%s:%s" % (ns, b) for b in blocklist.get(ns, [])]
        if not blocks:
            log("no blocks for", ns); continue
        log("=== %s: %d blocks ===" % (ns, len(blocks)))
        os.makedirs(os.path.join(out_dir, ns), exist_ok=True)
        res = audit_blocks(br, ns, blocks, H, out_dir, shot_dir, th=args.th)
        all_results.extend(res)
        write_namespace_reports(res, out_dir)
        json.dump(all_results, open(os.path.join(out_dir, "all_results.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    by_ns = write_namespace_reports(all_results, out_dir)
    md = write_global_report(by_ns, os.path.join(ROOT, "scratch", "vis", "BLOCK-AUDIT-draft.md"))
    log("report:", md)
    return 0


if __name__ == "__main__":
    sys.exit(main())