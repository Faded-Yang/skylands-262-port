# [port-repo] 原路径 scratch/vis/audit_report.py（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
# 脚本内的绝对工程路径/配套数据（游戏截图、blockaudit/all_results.json 等）不随仓库发布，跑之前按本机路径替换。
#!/usr/bin/env python3
"""audit_report.py — 把 block_audit.py 的 all_results.json 变成
  * <shot_dir>/BLOCK-AUDIT.md（按 namespace 的统计 + 破损清单 + 特写索引）
  * 每个破损方块的放大特写 crop
"""
import json, os, sys
from collections import defaultdict
from PIL import Image, ImageDraw

ROOT = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
sys.path.insert(0, os.path.join(ROOT, "scratch", "vis"))
import block_audit as ba


def crop_cell(rec, out_path, pad=45, scale=3):
    im = Image.open(rec["shot"]).convert("RGB")
    H, _ = ba.load_H(os.path.join(ROOT, "scratch", "vis", "blockaudit", "homography.json"))
    u, v = ba.apply_h(H, rec["gx"] + 0.5, rec["gz"] + 0.5)
    x0, y0 = max(0, int(u - pad)), max(0, int(v - pad))
    x1, y1 = min(im.width, int(u + pad)), min(im.height, int(v + pad))
    c = im.crop((x0, y0, x1, y1)).resize(((x1 - x0) * scale, (y1 - y0) * scale), Image.NEAREST)
    d = ImageDraw.Draw(c)
    cu, cv = (u - x0) * scale, (v - y0) * scale
    r = 0.42 * 37.7 * scale
    d.rectangle([cu - r, cv - r, cu + r, cv + r], outline=(255, 0, 0), width=2)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    c.save(out_path)
    return out_path


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "scratch", "vis", "blockaudit", "all_results.json")
    shot_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "work", "run26", "port", "g300", "game-vis1", "shots")
    out_md = os.path.join(shot_dir, "BLOCK-AUDIT.md")
    crop_dir = os.path.join(shot_dir, "crops")
    recs = json.load(open(src, encoding="utf-8"))
    by_ns = defaultdict(list)
    for r in recs:
        by_ns[r["ns"]].append(r)
    order = [n for n in ba.NS_ORDER if n in by_ns] + [n for n in by_ns if n not in ba.NS_ORDER]

    lines = []
    lines.append("# 游戏内方块渲染审计（26.3 + 118 jar 交付包）")
    lines.append("")
    lines.append("方法：旁观模式固定相机俯拍 9x5 网格；每个方块用 /setblock 放到 y=101，"
                 "再用 world.getBlock 权威核查是否真的放下；对顶面按单应投影取样，"
                 "**顶面品红像素（missing texture 特征色）占比 >= 5% 判为 MISSING**。")
    lines.append("")
    lines.append("| namespace | 已测 | MISSING | 占比 | NOT_PLACED(变 air/被替换) |")
    lines.append("|---|---|---|---|---|")
    tot = miss = npl = 0
    worst = []
    for ns in order:
        rs = by_ns[ns]
        m = [r for r in rs if r["verdict"] == "MISSING"]
        n = [r for r in rs if r["verdict"] == "NOT_PLACED"]
        tot += len(rs); miss += len(m); npl += len(n)
        lines.append("| %s | %d | %d | %.1f%% | %d |" % (ns, len(rs), len(m),
                     100.0 * len(m) / max(len(rs), 1), len(n)))
        worst.extend(m)
    lines.append("| **合计** | **%d** | **%d** | **%.1f%%** | **%d** |" % (tot, miss, 100.0 * miss / max(tot, 1), npl))
    lines.append("")
    lines.append("## 破损清单（MISSING）")
    lines.append("")
    if not miss:
        lines.append("**0 个**：本次抽测的所有 namespace 方块顶面都没有出现 missing texture 品红。")
    else:
        lines.append("| namespace | block | 品红占比 | 格子 | 批次截图 | 特写 |")
        lines.append("|---|---|---|---|---|---|")
        for r in sorted(worst, key=lambda x: -x["magenta"]):
            name = r["block"].replace(":", "_").replace("/", "_")
            crop = crop_cell(r, os.path.join(crop_dir, name + ".png"))
            lines.append("| %s | %s | %.1f%% | %d,%d | %s | %s |" % (
                r["ns"], r["block"], r["magenta"] * 100, r["gx"], r["gz"],
                os.path.basename(r["shot"]),
                os.path.relpath(crop, os.path.dirname(out_md)).replace("\\", "/")))
    lines.append("")
    nplist = [r for r in recs if r["verdict"] == "NOT_PLACED"]
    lines.append("## 放下去但不是自己（NOT_PLACED，%d 个）" % len(nplist))
    lines.append("")
    if nplist:
        lines.append("这些是 /setblock 返回 ok 但 world.getBlock 读到别的方块（多为 canSurvive 失败变 air，或被流体/其它方块替换）。**不计入破损**。")
        lines.append("")
        lines.append("| namespace | 期望 block | 实际 | 格子 | 批次截图 |")
        lines.append("|---|---|---|---|---|")
        for r in nplist[:200]:
            lines.append("| %s | %s | %s | %d,%d | %s |" % (r["ns"], r["block"], r.get("actual", "?"),
                                                           r["gx"], r["gz"], os.path.basename(r["shot"])))
        if len(nplist) > 200:
            lines.append("| ... | 共 %d 个，见各 namespace results.csv | | | |" % len(nplist))
    else:
        lines.append("无。")
    lines.append("")
    lines.append("## 每批次截图")
    lines.append("")
    for ns in order:
        shots = sorted({r["shot"] for r in by_ns[ns]})
        lines.append("- %s（%d 批）：%s" % (ns, len(shots),
                    "、".join(os.path.basename(s) for s in shots[:8]) + (" ..." if len(shots) > 8 else "")))
    open(out_md, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("wrote", out_md)
    print("total=%d missing=%d not_placed=%d" % (tot, miss, npl))


if __name__ == "__main__":
    main()
