# [port-repo] 原路径 scratch/vis/icon_audit.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。
#!/usr/bin/env python3
"""icon_audit.py — 创造背包/容器截图里的「物品图标是否破损」自动判定。

判定依据（均为 MC 26.3 反编译源码里的确定布局，见
work/refs/mc26.3/net/minecraft/client/gui/screens/inventory/CreativeModeInventoryScreen.java）：
  * 创造背包容器 GUI 尺寸 195x136 GUI 单位（构造器 super(..., 195, 136)）
  * 物品格 9 列 x 5 行；格子左上 = (leftPos + 9 + 18*col, topPos + 18 + 18*row)  [第 899 行 addSlot]
  * 槽位贴图 slot.png 18x18：上/左 1px #373737，下/右 1px #FFFFFF，内部 #8B8B8B
  * leftPos/topPos 居中：((屏幕GUI宽 - 195)//2, (屏幕GUI高 - 136)//2)
  * 标签页tab 26x32：x = leftPos + 27*column（右对齐时为 leftPos + 195 - 27*(7-column) + 1），
    y = topPos - 28（上排）或 topPos + 136 - 4（下排）

因为 GUI scale 是整数、截图可能被系统缩放，S（GUI scale）按 1.0..10.0 细步长搜索，
用「槽位边框颜色是否吻合」打分选最优；这一步不依赖任何固定分辨率。

用法：
  python icon_audit.py shot.png                 # 单图，打印 JSON + 存标注图
  python icon_audit.py shot.png --json o.json --annotate o.png
  python icon_audit.py --batch DIR              # 批量：DIR 下所有 png -> 表格(md+csv)
  python icon_audit.py --batch DIR --out DIR2   # 报告/标注图写到 DIR2
  python icon_audit.py --selftest               # 合成已知答案的自测
  python icon_audit.py shot.png --tabmap        # 顺带输出 tab 点击坐标表

退出码：0 正常；2 没找到 GUI 网格（不是创造背包截图）。
"""
import argparse, glob, json, os, sys
from dataclasses import dataclass, asdict, field
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw

# ---- 与 slot.png 完全一致的颜色（截图是 framebuffer 原始像素，颜色精确）----
BORDER_DARK = (55, 55, 55)      # #373737  上/左
BORDER_LIGHT = (255, 255, 255)  # #FFFFFF  下/右
SLOT_FILL = (139, 139, 139)     # #8B8B8B  内部
PANEL_BG = (198, 198, 198)      # #C6C6C6  容器面板底色

IMG_W, IMG_H = 195, 136          # 创造背包 GUI 尺寸
GRID_COLS, GRID_ROWS = 9, 5
GRID_X0, GRID_Y0 = 9, 18         # 相对 leftPos/topPos
CELL = 18

# ---- 判定阈值（可用 --magenta-th 等覆盖；逻辑见 classify_cell 注释）----
DEFAULTS = dict(
    magenta_frac_missing=0.15,   # 品红像素占比 >= 该值 => 基本可断定 missing texture
    black_frac_blackish=0.20,    # 黑像素占比达标 + 有一定品红 => 品红黑棋盘
    empty_frac=0.90,             # 图标区 >=90% 是槽位底色 => 空白（物品不可见/无物品）
    black_solid_frac=0.97,       # >=97% 纯黑 => 纯黑块（可能是正常黑色物品，需人工确认）
    color_tol=10,
)


def _close(arr, color, tol):
    return (np.abs(arr[..., 0].astype(np.int16) - color[0]) <= tol) & \
           (np.abs(arr[..., 1].astype(np.int16) - color[1]) <= tol) & \
           (np.abs(arr[..., 2].astype(np.int16) - color[2]) <= tol)


def load_rgb(path):
    im = Image.open(path)
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    arr = np.asarray(im, dtype=np.uint8)
    return im, arr


# 采样点用「GUI 单位」相对偏移描述，乘以 S 后取整；向量化后一次取色
def _sample_points():
    pts = []  # (dx, dy, color)
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            gx0 = GRID_X0 + c * CELL
            gy0 = GRID_Y0 + r * CELL
            # 四条边的中点；偏移取 0.5 = 1 GUI 单位边框的正中（取 0.2 会落到相邻像素）
            # 不采槽位底色：物品图标覆盖 16x16，仅透明像素才露出底色，不可靠
            pts.append((gx0 + CELL / 2.0, gy0 + 0.5, BORDER_DARK))
            pts.append((gx0 + 0.5, gy0 + CELL / 2.0, BORDER_DARK))
            pts.append((gx0 + CELL / 2.0, gy0 + CELL - 0.5, BORDER_LIGHT))
            pts.append((gx0 + CELL - 0.5, gy0 + CELL / 2.0, BORDER_LIGHT))
    return pts


_SAMPLES = _sample_points()
_SAMPLE_COLORS = np.array([s[2] for s in _SAMPLES], dtype=np.int16)
_SAMPLE_DX = np.array([s[0] for s in _SAMPLES], dtype=np.float64)
_SAMPLE_DY = np.array([s[1] for s in _SAMPLES], dtype=np.float64)


def score_grid(arr, S, left, top, tol=26):
    """按预测的槽位边框/底色给一个 (S,left,top) 打分，返回 0..1（向量化）。"""
    H, W = arr.shape[:2]
    xs = np.rint((left + _SAMPLE_DX) * S).astype(np.int32)
    ys = np.rint((top + _SAMPLE_DY) * S).astype(np.int32)
    if xs.min() < 0 or ys.min() < 0 or xs.max() >= W or ys.max() >= H:
        return 0.0
    got = arr[ys, xs, :3].astype(np.int16)
    ok = np.all(np.abs(got - _SAMPLE_COLORS) <= tol, axis=1)
    return float(ok.mean())


def _refine(arr, best):
    """在最优解附近细化 S / left / top。"""
    for _ in range(4):
        S0, l0, t0 = best["S"], best["left"], best["top"]
        better = best
        for dS in (-0.1, -0.05, -0.02, -0.01, 0, 0.01, 0.02, 0.05, 0.1):
            S = S0 + dS
            if S <= 0.5:
                continue
            for dl in (-2, -1, 0, 1, 2):
                for dt in (-2, -1, 0, 1, 2):
                    sc = score_grid(arr, S, l0 + dl, t0 + dt)
                    if sc > better["score"]:
                        better = dict(S=S, left=l0 + dl, top=t0 + dt, score=sc)
        if better["score"] <= best["score"] + 1e-9:
            break
        best = better
    return best


def detect_grid(arr, allow_offset_search=True):
    """返回 dict(S,left,top,score)，失败返回 None。

    先在「面板居中」假设下扫 GUI scale（正常 framebuffer 截图必定命中），
    再对整屏/裁剪图做偏移搜索兜底（桌面截图里窗口不在正中）。
    S 允许非整数：窗口被系统 DPI 缩放时 framebuffer 会被整倍放大。
    """
    H, W = arr.shape[:2]
    best = None
    for i in range(4, 41):          # 1.0 .. 10.0
        S = i / 4.0
        left = (W / S - IMG_W) / 2.0
        top = (H / S - IMG_H) / 2.0
        if left < -2 or top < -2:
            continue
        sc = score_grid(arr, S, left, top)
        if best is None or sc > best["score"]:
            best = dict(S=S, left=left, top=top, score=sc)
    if best is not None and best["score"] >= 0.65:
        return _snap_scale(arr, _refine(arr, best))
    if not allow_offset_search:
        return None
    # 兜底：窗口不在正中（桌面截图 / 裁剪图）——二维偏移粗搜
    coarse = None
    for i in range(4, 41, 1):
        S = i / 4.0
        mx = int(W / S - IMG_W - 1)
        my = int(H / S - IMG_H - 1)
        if mx < 0 or my < 0:
            continue
        for left in range(0, mx + 1, 3):
            for top in range(0, my + 1, 3):
                sc = score_grid(arr, S, left, top)
                if coarse is None or sc > coarse["score"]:
                    coarse = dict(S=S, left=left, top=top, score=sc)
                    if sc >= 0.9:
                        break
    if coarse is None or coarse["score"] < 0.35:
        return None
    return _snap_scale(arr, _refine(arr, coarse))


def _snap_scale(arr, best):
    """GUI scale 实际是整数（桌面截图再被整倍放大 → 仍是整数或 1.5 的倍数）；
    细化后若离 0.25 的倍数很近就吸附，再把偏移重新对齐。"""
    S = best["S"]
    snapped = round(S * 4) / 4.0
    if abs(snapped - S) <= 0.06:
        best2 = dict(S=snapped, left=best["left"], top=best["top"], score=best["score"])
        best2 = _refine(arr, best2)
        if best2["score"] >= best["score"] - 0.02:
            return best2
    return best


def cell_rect(g, c, r):
    S, left, top = g["S"], g["left"], g["top"]
    x0 = (left + GRID_X0 + c * CELL) * S
    y0 = (top + GRID_Y0 + r * CELL) * S
    return (int(round(x0)), int(round(y0)), int(round(x0 + CELL * S)), int(round(y0 + CELL * S)))


def classify_cell(arr, rect, th):
    """返回 dict(verdict, magenta, black, slotfill, slots, mean...)

    verdict:
      MISSING_MAGENTA  图标主色是品红 => missing texture（紫黑格子/纯品红）
      MISSING_CHECKER  品红+黑都显著 => 品红黑棋盘
      INVISIBLE        图标区几乎全是槽位底色 => 该格没有可见图标（无物品 或 物品不可见）
      BLACK_SOLID      几乎全纯黑（可能是正常黑物品，标记待人工确认）
      NORMAL           其它
    """
    x0, y0, x1, y1 = rect
    S = (x1 - x0) / CELL
    inset = max(1, int(round(S * 1.0)))
    ix0 = x0 + int(round(S))
    iy0 = y0 + int(round(S))
    ix1 = x1 - int(round(S))
    iy1 = y1 - int(round(S))
    icon = arr[iy0:iy1, ix0:ix1]
    if icon.size == 0:
        return dict(verdict="ERROR", magenta=0, black=0, slotfill=0, mean=[0, 0, 0])
    f = icon[..., :3].reshape(-1, 3).astype(np.int16)
    n = f.shape[0]
    r, g, b = f[:, 0], f[:, 1], f[:, 2]
    magenta = ((r >= 180) & (b >= 180) & (g <= 90) & (g < r - 100) & (g < b - 100))
    black = ((r <= 30) & (g <= 30) & (b <= 30))
    slotfill = (np.abs(r - SLOT_FILL[0]) <= 12) & (np.abs(g - SLOT_FILL[1]) <= 12) & (np.abs(b - SLOT_FILL[2]) <= 12)
    mf, bf, sf = magenta.mean(), black.mean(), slotfill.mean()
    std = float(icon[..., :3].reshape(-1, 3).std())
    if mf >= th["magenta_frac_missing"]:
        verdict = "MISSING_CHECKER" if bf >= th["black_frac_blackish"] else "MISSING_MAGENTA"
    elif sf >= th["empty_frac"] and std < 12:
        verdict = "INVISIBLE"
    elif bf >= th["black_solid_frac"]:
        verdict = "BLACK_SOLID"
    else:
        verdict = "NORMAL"
    return dict(verdict=verdict, magenta=round(float(mf), 4), black=round(float(bf), 4),
                slotfill=round(float(sf), 4), std=round(std, 2),
                mean=[int(v) for v in icon[..., :3].reshape(-1, 3).mean(axis=0)])


def analyze_image(path, th=None, annotate=True, out_dir=None, tabmap=False):
    th = {**DEFAULTS, **(th or {})}
    im, arr = load_rgb(path)
    g = detect_grid(arr)
    res = dict(image=os.path.abspath(path), size=list(im.size), ok=False)
    if g is None:
        res["error"] = "no creative-inventory grid found (GUI scale/panel not matched)"
        return res
    res.update(ok=True, gui_scale=round(g["S"], 3), left=round(g["left"], 2), top=round(g["top"], 2),
               grid_score=round(g["score"], 3), cols=GRID_COLS, rows=GRID_ROWS)
    cells = []
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            rect = cell_rect(g, c, r)
            info = classify_cell(arr, rect, th)
            info.update(col=c, row=r, rect=list(rect), index=r * GRID_COLS + c)
            cells.append(info)
    res["cells"] = cells
    # 统计：创造栏物品是连续填充的，末尾的空格是正常补白；
    # 最后一个"有图标"格子之前的空格 = 不可见物品（可疑）
    filled = [i for i, x in enumerate(cells) if x["verdict"] not in ("INVISIBLE",)]
    last = max(filled) if filled else -1
    gaps = [i for i in filled if False]
    empty_before_last = [i for i in range(max(last, 0) + 1) if cells[i]["verdict"] == "INVISIBLE"]
    missing = [i for i, x in enumerate(cells) if x["verdict"] in ("MISSING_MAGENTA", "MISSING_CHECKER")]
    blackish = [i for i, x in enumerate(cells) if x["verdict"] == "BLACK_SOLID"]
    res["summary"] = dict(
        slots=GRID_COLS * GRID_ROWS,
        visible=len(filled),
        missing=len(missing),
        invisible_gaps=len(empty_before_last),
        trailing_empty=GRID_COLS * GRID_ROWS - (last + 1) if last >= 0 else GRID_COLS * GRID_ROWS,
        black_solid=len(blackish),
        missing_indexes=missing,
        invisible_indexes=empty_before_last,
        black_indexes=blackish,
    )
    s = res["summary"]
    denom = max(s["visible"], 1)
    res["summary"]["missing_pct_of_visible"] = round(100.0 * s["missing"] / denom, 2)
    res["summary"]["broken_pct_of_visible"] = round(100.0 * (s["missing"] + s["invisible_gaps"]) / denom, 2)

    if tabmap:
        res["tabmap"] = tab_layout(g, im.size)
    if annotate:
        out = out_dir or os.path.dirname(os.path.abspath(path))
        os.makedirs(out, exist_ok=True)
        ap = os.path.join(out, os.path.splitext(os.path.basename(path))[0] + ".audit.png")
        res["annotated"] = draw_annotation(im, arr, g, cells, ap)
    return res


VERDICT_COLOR = {"MISSING_MAGENTA": (255, 0, 0), "MISSING_CHECKER": (255, 0, 0),
                 "INVISIBLE": (255, 170, 0), "BLACK_SOLID": (0, 120, 255), "NORMAL": (0, 200, 0)}


def draw_annotation(im, arr, g, cells, out_path):
    canvas = im.convert("RGBA").copy()
    d = ImageDraw.Draw(canvas)
    for c in cells:
        x0, y0, x1, y1 = c["rect"]
        col = VERDICT_COLOR.get(c["verdict"], (128, 128, 128))
        d.rectangle([x0, y0, x1 - 1, y1 - 1], outline=col + (255,), width=max(1, int(g["S"] // 2)))
        if c["verdict"] != "NORMAL":
            d.text((x0 + 2, y0 + 1), c["verdict"][:3], fill=col + (255,))
    canvas.save(out_path)
    return os.path.abspath(out_path)


def tab_layout(g, size):
    """算出 8 列 x 2 排 tab 的点击矩形（截图坐标系）。"""
    S, left, top = g["S"], g["left"], g["top"]
    rows = []
    for rname, ybase in (("top", top - 28), ("bottom", top + IMG_H - 4)):
        for col in range(8):
            rows.append(dict(row=rname, column=col,
                             rect=[int(left * S + 27 * col * S), int(ybase * S),
                                   int(left * S + (27 * col + 26) * S), int(ybase * S + 32 * S)],
                             center=[int(left * S + (27 * col + 13) * S), int(ybase * S + 16 * S)]))
    return dict(gui_scale=round(S, 3), tabs=rows)


def batch(dirpath, out_dir=None, th=None):
    files = sorted(glob.glob(os.path.join(dirpath, "*.png")))
    files = [f for f in files if not f.endswith(".audit.png")]
    results = []
    for i, f in enumerate(files, 1):
        try:
            r = analyze_image(f, th=th, annotate=True, out_dir=out_dir or dirpath)
        except Exception as e:  # 单图失败不影响批量
            r = dict(image=f, ok=False, error=repr(e))
        results.append(r)
        if r.get("ok"):
            s = r["summary"]
            print(f"[{i}/{len(files)}] {os.path.basename(f)}: slots={s['slots']} visible={s['visible']} "
                  f"missing={s['missing']} invisible={s['invisible_gaps']} "
                  f"broken={s['broken_pct_of_visible']}%", flush=True)
        else:
            print(f"[{i}/{len(files)}] {os.path.basename(f)}: SKIP ({r.get('error')})", flush=True)
    return results


def write_reports(results, out_dir):
    out_dir = out_dir or "."
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "icon_audit.json")
    csv_path = os.path.join(out_dir, "icon_audit.csv")
    md_path = os.path.join(out_dir, "icon_audit.md")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("image,ok,gui_scale,slots,visible,missing,invisible_gaps,trailing_empty,black_solid,"
                "missing_pct_of_visible,broken_pct_of_visible,missing_indexes,invisible_indexes\n")
        for r in results:
            s = r.get("summary") or {}
            f.write(",".join(str(v).replace(",", ";") for v in [
                os.path.basename(r["image"]), r.get("ok"), r.get("gui_scale"), s.get("slots"),
                s.get("visible"), s.get("missing"), s.get("invisible_gaps"), s.get("trailing_empty"),
                s.get("black_solid"), s.get("missing_pct_of_visible"), s.get("broken_pct_of_visible"),
                " ".join(map(str, s.get("missing_indexes", []))),
                " ".join(map(str, s.get("invisible_indexes", [])))]) + "\n")
    lines = ["| 截图 | GUI scale | 可见格 | missing(紫黑) | 不可见空格 | 纯黑块 | 破损占可见格 | 标注图 |",
             "|---|---|---|---|---|---|---|---|"]
    tot_m = tot_v = 0
    for r in results:
        if not r.get("ok"):
            lines.append(f"| {os.path.basename(r['image'])} | - | - | - | - | - | 无法识别 | - |")
            continue
        s = r["summary"]
        tot_m += s["missing"] + s["invisible_gaps"]
        tot_v += s["visible"]
        ann = os.path.basename(r.get("annotated", ""))
        lines.append(f"| {os.path.basename(r['image'])} | {r['gui_scale']} | {s['visible']} | {s['missing']} | "
                     f"{s['invisible_gaps']} | {s['black_solid']} | {s['broken_pct_of_visible']}% | {ann} |")
    if tot_v:
        lines.append(f"| **合计** | | **{tot_v}** | **{tot_m}** | | | **{round(100.0*tot_m/max(tot_v,1),2)}%** | |")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return dict(json=json_path, csv=csv_path, md=md_path)


# ---------------- 自测：合成一张已知答案的创造背包截图 ----------------
def make_missing_texture(size=16, block=1):
    """品红/黑棋盘（MC missingno 的风格：块状交替）。"""
    a = np.zeros((size, size, 4), dtype=np.uint8)
    for y in range(size):
        for x in range(size):
            on = ((x // block) + (y // block)) % 2 == 0
            a[y, x] = (255, 0, 255, 255) if on else (0, 0, 0, 255)
    return a


def make_synthetic(S, pad_gui=(6, 6)):
    """合成一张创造背包截图，返回 (image_array, expected dict)。"""
    W, H = IMG_W * S, IMG_H * S
    pad_x, pad_y = int(pad_gui[0] * S), int(pad_gui[1] * S)
    canvas = np.zeros((H + 2 * pad_y, W + 2 * pad_x, 4), dtype=np.uint8)
    canvas[..., :3] = (32, 32, 32)
    canvas[..., 3] = 255
    canvas[pad_y:pad_y + H, pad_x:pad_x + W, :3] = PANEL_BG
    left, top = pad_gui
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            x = int((left + GRID_X0 + c * CELL) * S)
            y = int((top + GRID_Y0 + r * CELL) * S)
            cell = np.zeros((CELL * S, CELL * S, 4), dtype=np.uint8)
            cell[..., 3] = 255
            cell[..., :3] = SLOT_FILL
            b = S
            cell[0:b, :, :3] = BORDER_DARK
            cell[:, 0:b, :3] = BORDER_DARK
            cell[-b:, :, :3] = BORDER_LIGHT
            cell[:, -b:, :3] = BORDER_LIGHT
            canvas[y:y + CELL * S, x:x + CELL * S] = cell
    kinds = {i: "normal" for i in range(45)}
    for i in (3, 7, 8, 14, 21, 22, 30, 33):
        kinds[i] = "missing"
    for i in (4, 12, 25):
        kinds[i] = "invisible"
    for idx, kind in kinds.items():
        r, c = divmod(idx, GRID_COLS)
        x = int((left + GRID_X0 + c * CELL + 1) * S)
        y = int((top + GRID_Y0 + r * CELL + 1) * S)
        if kind == "missing":
            mt = make_missing_texture(16, block=1)
            canvas[y:y + 16 * S, x:x + 16 * S] = np.repeat(np.repeat(mt, S, axis=0), S, axis=1)
        elif kind == "normal":
            col = ((idx * 53) % 160 + 60, (idx * 97) % 90 + 120, (idx * 31) % 160 + 60)
            canvas[y:y + 16 * S, x:x + 16 * S, :3] = col
            canvas[y:y + 16 * S, x:x + 16 * S, 3] = 255
    exp = dict(missing={i for i, k in kinds.items() if k == "missing"},
               invisible={i for i, k in kinds.items() if k == "invisible"})
    return canvas, exp


def selftest(workdir):
    """多 GUI scale + 非居中面板，验证检出；返回 0=全通过。"""
    import time
    os.makedirs(workdir, exist_ok=True)
    allok = True
    cases = [(2, (6, 6)), (3, (6, 6)), (4, (6, 6)), (3, (40, 25)), (2, (90, 12))]
    for S, pad in cases:
        canvas, exp = make_synthetic(S, pad)
        path = os.path.join(workdir, f"selftest_S{S}_pad{pad[0]}x{pad[1]}.png")
        Image.fromarray(canvas, "RGBA").save(path)
        t0 = time.time()
        res = analyze_image(path, annotate=True, out_dir=workdir)
        dt = time.time() - t0
        if not res.get("ok"):
            print(f"[FAIL] S={S} pad={pad}: no grid detected ({res.get('error')}) {dt:.1f}s")
            allok = False
            continue
        got = {i: c["verdict"] for i, c in enumerate(res["cells"])}
        got_m = {i for i, v in got.items() if v.startswith("MISSING")}
        got_i = {i for i, v in got.items() if v == "INVISIBLE"}
        m_ok = exp["missing"] == got_m
        i_ok = exp["invisible"] <= got_i
        ok = m_ok and i_ok
        allok = allok and ok
        print(f"[{'PASS' if ok else 'FAIL'}] S={S} pad={pad} detected_scale={res['gui_scale']} "
              f"score={res['grid_score']} missing {len(got_m)}/{len(exp['missing'])} "
              f"invisible {len(exp['invisible'] & got_i)}/{len(exp['invisible'])} {dt:.1f}s")
        if not m_ok:
            print("   missing exp-got:", sorted(exp["missing"] - got_m), " got-exp:", sorted(got_m - exp["missing"]))
        if not i_ok:
            print("   invisible exp-got:", sorted(exp["invisible"] - got_i))
    print("SELFTEST", "PASS" if allok else "FAIL")
    return 0 if allok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image", nargs="?")
    ap.add_argument("--batch")
    ap.add_argument("--out")
    ap.add_argument("--json")
    ap.add_argument("--annotate")
    ap.add_argument("--tabmap", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest(a.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "selftest"))
    if a.batch:
        res = batch(a.batch, out_dir=a.out)
        rep = write_reports(res, a.out or a.batch)
        print(json.dumps(rep, ensure_ascii=False))
        return 0
    if not a.image:
        ap.error("need an image, --batch DIR, or --selftest")
    r = analyze_image(a.image, annotate=True, out_dir=a.out, tabmap=a.tabmap)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=1)
    if not a.quiet:
        out = dict(r)
        out.pop("cells", None)
        print(json.dumps(out, ensure_ascii=False, indent=1))
        if r.get("ok"):
            for row in range(GRID_ROWS):
                line = ""
                for col in range(GRID_COLS):
                    v = r["cells"][row * GRID_COLS + col]["verdict"]
                    line += {"NORMAL": ".", "MISSING_MAGENTA": "M", "MISSING_CHECKER": "M",
                             "INVISIBLE": "_", "BLACK_SOLID": "B"}.get(v, "?")
                print("  " + line)
    return 0 if r.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())