#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_world_preset_mod.py —— 浮岛地形「世界类型」构建器（v3：厚岛 + 岛内洞穴 + 水柱治理）

## 历史
* v1：只带 noise_settings + world_preset → 引用悬空，卡「正在准备生成世界」
* v2：自带 6 个 `custom:` 密度函数 / dimension_type(576) / carver / lang → 用户实测可进世界
  **但**：final_density 只是 `gradient + noise(y_scale=3)` 的薄片，岛厚 2~5 格、无锥底；
       洞穴只有 y<64（岛太薄塞不进）；结构全贴海平面；水从海床漏成水柱。
* v3（本版）：**不动低层地形（海平面/海床原样保留，用户已否决拆地面）**，
  在它上面叠两带「2D mask × 锥形剖面」浮岛：

      final_density = max(low_terrain, island_a, island_b) + beardifier

  每一带：
      top   = base + a1*N(continentalness, s1) + a2*N(erosion, s2) + 3*N(gravel, .06)
      mask2D= N(continentalness, m1) + w*N(erosion, m2) - bias        # 判「这一列有没有岛」
      cap   = 0.10 * (top - y)                                        # 顶面平滑
      depth = max((top-2) - y, 0)
      cone  = mask2D - K*depth                                        # 越往下脚印越小 → 锥形
      island= min(cap, cone)                                          # >0 实心

  ⇒ 厚度 = plateau + mask2D / K；中心厚、边缘薄；岛间（mask2D<0）整列空气。
  ⚠ 关键教训：mask 的 `xz_scale` 决定岛的大小。旧版 `wg_realislands.py` 用 0.0068
    （≈ 7.5 万格一个特征）⇒ mask 在 300 格内近似常数 ⇒ **整片均匀薄片**，这正是
    「岛只有 2~5 格厚」的真正原因。本版用 0.55/0.75（特征 ~100~250 格）。

## 顺带修的
* 洞穴：`y` 抬到岛带（不再切海床 → 海面不再漏成水柱），上/下两带各一份 carver
* `aquifers` 整键删除（= 关闭）⇒ 没有地下水/浮岛湖，只有 sea_level 那一层静水
* 船：`medieval_buildings:ship` / `structory:boat` 原为 `WORLD_SURFACE_WG` 投影
  + 负偏移 ⇒ 落在**岛顶**（y≈200）→ 浮空。改成 `absolute 62` + 去掉投影 ⇒ 钉在水面。

## 用法
    python tools/build_world_preset_mod.py [--out <jar>] [--mods <mods-stable>] [--quiet]
"""
import json
import os
import sys
import zipfile

BASE = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
MC_JAR = r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar"
AEROLITH = os.path.join(BASE, r"work\run26\watch\saves\sky islands\datapacks\aerolith-1.3.2-26.3.zip")
MODS_STABLE = os.path.join(BASE, r"work\run26\mods-stable")
NS, ID = "skylands", "sky_islands"
MOD_ID, VERSION = "zsky262_preset", "1.0.0"
# ⚠ mod id 故意以 z 开头：Fabric 的资源包按 **mod 加载顺序（按 mod id 排序）** 叠加，
# **后加载者胜**（探针实测，见 docs/worldgen-v2.md §6）。
# 本 mod 要覆盖 `structory:boat` / `medieval_buildings:ship` 两个**其它 mod** 的定义
# ⇒ id 必须排在它们后面（"z..." > "structory" / "towns_and_towers" / "medieval_buildings"）。
DEFAULT_OUT = os.path.join(BASE, r"work\run26\mods-stable\sky262-preset-1.0.0.jar")

LANG = {
    "zh_cn": {"generator.skylands.sky_islands": "浮岛世界",
              "world_preset.skylands.sky_islands": "浮岛世界"},
    "en_us": {"generator.skylands.sky_islands": "Sky Islands",
              "world_preset.skylands.sky_islands": "Sky Islands"},
}

SHIFT_X = "custom:skylands_shift_x"
SHIFT_Z = "minecraft:shift_z"

# ============================ 可调参数 ============================
# 带 A（中层，结构主战场）：实测旧岛带 176..220，这里顶面 ≈ 184..223
BAND_A = dict(
    top_base=200.0, top_a=16.0, top_s=0.23,      # ±16 大尺度起伏
    top_b=7.0, top_s2=0.62,                      # ±7 中尺度
    mask_s1=0.30, mask_s2=0.70, mask_w=0.50,     # 2D mask 频率（决定岛的大小）
    bias=-0.11,                                  # 调覆盖率：↑ = 岛少（实测 0.00→均值 14.5%）
    sat=0.70,                                    # mask 饱和值（决定中心最大厚度）
    knee=0.20,                                   # 饱和前的拐点（边缘陡、内部缓）
    k_edge=3.40, k_core=0.35,                    # 两段斜率
    cone=0.034,                                  # 竖向收锥：厚度 = core/cone
)
# 带 B（高层）：实测旧岛带 320..447，顶面 ≈ 346..395
BAND_B = dict(
    top_base=366.0, top_a=20.0, top_s=0.20,
    top_b=9.0, top_s2=0.55,
    mask_s1=0.42, mask_s2=0.85, mask_w=0.50,
    bias=-0.09,
    sat=0.65,
    knee=0.20,
    k_edge=3.40, k_core=0.40,
    cone=0.036,
)
PLATEAU = 2.0     # 顶面往下这一段是「平板」，再往下开始收锥
CAP_K = 0.10      # 顶面过渡带宽度（1/CAP_K = 10 格）
DETAIL_A = 3.0    # 顶面块级细节振幅
# 洞穴：只在岛带里挖（> 64 ⇒ 绝不碰海床）
CARVER_BANDS = {
    "cave": [(168, 252, 1, 4), (318, 462, 1, 4)],        # (y0,y1,count_min,count_max)
    "canyon": [(176, 248, None, None), (330, 455, None, None)],
}
# 结构覆盖：id -> (start_height, 是否删掉 project_start_to_heightmap)
STRUCT_PATCH = {
    # 船型建筑：原为 WORLD_SURFACE_WG 投影 ⇒ 落在岛顶/山丘顶 = 浮空。
    # 钉死在水面（sea_level=64 ⇒ 水顶 y=63），不再投影。
    "medieval_buildings:ship": ({"absolute": 62}, True),
    "structory:boat": ({"absolute": 62}, True),
}
# =================================================================


def A(l, r):
    return {"type": "minecraft:add", "left": l, "right": r}


def S(l, r):
    return {"type": "minecraft:sub", "left": l, "right": r}


def M(l, r):
    return {"type": "minecraft:mul", "left": l, "right": r}


def MN(l, r):
    return {"type": "minecraft:min", "left": l, "right": r}


def MX(l, r):
    return {"type": "minecraft:max", "left": l, "right": r}


def N(noise, xz, y=0.0):
    return {"type": "minecraft:noise", "noise": noise, "xz_scale": xz, "y_scale": y,
            "shift_x": SHIFT_X, "shift_z": SHIFT_Z}


def band_top(p):
    """顶面高度场（2D + 块级细节）。"""
    return A(
        A(p["top_base"], M(p["top_a"], N("minecraft:continentalness", p["top_s"]))),
        A(M(p["top_b"], N("minecraft:erosion", p["top_s2"])),
          M(DETAIL_A, N("minecraft:gravel", 0.06, 0.06))))


def band_mask(p):
    """2D 岛存在性场：>0 = 有岛。"""
    return S(A(N("minecraft:continentalness", p["mask_s1"]),
               M(p["mask_w"], N("minecraft:erosion", p["mask_s2"]))),
             p["bias"])


def band_body(p, top_ref):
    """min(cap, cone)：顶面平滑 + 两段式锥形底。

    为什么不是线性锥（旧版）：线性锥下「厚度 ∝ mask」，而 mask 在岛边缘附近是线性上升的，
    于是**面积的大头落在薄边**上 ⇒ 岛厚中位数只有 3~5 格（实测 v3a：p50=4）。
    改成两段：拐点 knee 之前用陡坡 k_edge（边缘几格内就拉到 ~14 格厚），
    之后用缓坡 k_core（往中心再长一截，保留可见的锥底）。

    这里用 min/max 手写 —— **不用 minecraft:clamp**（26.3 的 codec 会静默改成 [0,1]），
    也不用 minecraft:sqrt（26.3 没注册这个类型）。
    """
    cap = M(S(top_ref, "minecraft:y"), CAP_K)
    m = MN(MX(band_mask(p), 0.0), p["sat"])
    core = A(M(MN(m, p["knee"]), p["k_edge"]),
             M(MX(S(m, p["knee"]), 0.0), p["k_core"]))
    depth = MX(S(S(top_ref, PLATEAU), "minecraft:y"), 0.0)
    cone = S(core, M(depth, p["cone"]))
    return MN(cap, cone)


def build_entries(mc, a, mods_dir):
    entries = {}

    # ---- 1) 原有 6 个 custom: 密度函数（id 不能改，噪声设置硬引用）----
    n_df = 0
    for n in a.namelist():
        if "/density_function/" in n:
            entries[n] = a.read(n).decode("utf-8", "replace")
            n_df += 1
    print("[1] 原有密度函数 %d 个（custom:，id 不变）" % n_df)

    # ---- 1b) 新增：岛顶面 + 岛体（两带）----
    for tag, p in (("a", BAND_A), ("b", BAND_B)):
        top_path = "data/custom/worldgen/density_function/skylands/island_top_%s.json" % tag
        body_path = "data/custom/worldgen/density_function/skylands/island_%s.json" % tag
        entries[top_path] = json.dumps(band_top(p), indent=1, ensure_ascii=False) + "\n"
        top_ref = "custom:skylands/island_top_%s" % tag
        entries[body_path] = json.dumps(band_body(p, top_ref), indent=1, ensure_ascii=False) + "\n"
        print("[1b] custom:skylands/island_top_%s  base=%.0f mask_s=%.2f bias=%.2f "
              "knee=%.2f k=(%.2f,%.2f) cone=%.3f sat=%.2f"
              % (tag, p["top_base"], p["mask_s1"], p["bias"], p["knee"],
                 p["k_edge"], p["k_core"], p["cone"], p["sat"]))

    # ---- 2) 噪声设置 ----
    noise = json.loads(a.read("data/minecraft/worldgen/noise_settings/overworld.json")
                       .decode("utf-8", "replace"))
    low = noise["noise_router"]["final_density"]          # 原低层地形，逐字保留
    noise["noise_router"]["final_density"] = A(
        MX(MX(low, "custom:skylands/island_a"), "custom:skylands/island_b"),
        {"type": "minecraft:beardifier"})
    noise["aquifers"] = None
    noise.pop("aquifers", None)                            # Optional<Config> ⇒ 缺键 = 关闭
    carvers = []
    for kind, bands in CARVER_BANDS.items():
        for i, (y0, y1, c0, c1) in enumerate(bands):
            cid = "%s:%s" % (NS, kind if i == 0 else "%s_high" % kind)
            src = "data/minecraft/worldgen/carver/%s.json" % kind
            d = json.loads(a.read(src).decode("utf-8", "replace"))
            d["y"] = {"type": "minecraft:uniform",
                      "min_inclusive": {"absolute": y0},
                      "max_inclusive": {"absolute": y1}}
            if c0 is not None:
                d["count"] = {"type": "minecraft:uniform",
                              "min_inclusive": c0, "max_inclusive": c1}
            entries["data/%s/worldgen/carver/%s.json" % (NS, cid.split(":")[1])] = \
                json.dumps(d, indent=1, ensure_ascii=False) + "\n"
            carvers.append(cid)
            print("[3] carver %-18s y=%d..%d count=%s" % (cid, y0, y1, json.dumps(d.get("count"))))
    noise["carvers"] = {"air": carvers}
    entries["data/%s/worldgen/noise_settings/%s.json" % (NS, ID)] = \
        json.dumps(noise, indent=2, ensure_ascii=False) + "\n"
    print("[2] 噪声设置 sea_level=%s aquifers=%s carvers=%d 个"
          % (noise.get("sea_level"), noise.get("aquifers", "缺键(关闭)"), len(carvers)))

    # ---- 4) 维度类型（576 高，独立 id）----
    dt = json.loads(a.read("data/minecraft/dimension_type/overworld.json")
                    .decode("utf-8", "replace"))
    entries["data/%s/dimension_type/%s.json" % (NS, ID)] = \
        json.dumps(dt, indent=1, ensure_ascii=False) + "\n"
    print("[4] 维度类型 -> %s:%s  min_y=%s height=%s" % (NS, ID, dt.get("min_y"), dt.get("height")))

    # ---- 5) 世界预设 ----
    cand = [n for n in mc.namelist()
            if "/worldgen/world_preset/" in n and not n.startswith("data/minecraft/tags/")
            and n.endswith(".json")]
    cand.sort(key=lambda n: (not n.endswith("/normal.json"), n))
    preset = json.loads(mc.read(cand[0]).decode("utf-8", "replace"))
    ow = preset["dimensions"]["minecraft:overworld"]
    ow["type"] = "%s:%s" % (NS, ID)
    ow["generator"]["settings"] = "%s:%s" % (NS, ID)
    entries["data/%s/worldgen/world_preset/%s.json" % (NS, ID)] = \
        json.dumps(preset, indent=2, ensure_ascii=False) + "\n"
    print("[5] 世界预设 -> %s:%s（模板 %s）" % (NS, ID, cand[0]))

    # ---- 6) minecraft:normal 标签 ----
    tag = {"values": ["minecraft:normal", "minecraft:large_biomes", "minecraft:amplified",
                      "%s:%s" % (NS, ID)]}
    entries["data/minecraft/tags/worldgen/world_preset/normal.json"] = \
        json.dumps(tag, indent=2, ensure_ascii=False) + "\n"
    print("[6] 并入 minecraft:normal 标签")

    # ---- 7) 结构覆盖（船）----
    n = 0 if os.environ.get("WG_NO_STRUCT") else patch_structures(entries, mods_dir)
    print("[7] 结构覆盖 %d 个%s" % (n, " (跳过: WG_NO_STRUCT)" if os.environ.get("WG_NO_STRUCT") else ""))

    # ---- 8) lang + fabric.mod.json ----
    for lang, kv in LANG.items():
        entries["assets/%s/lang/%s.json" % (NS, lang)] = \
            json.dumps(kv, indent=2, ensure_ascii=False) + "\n"
    entries["fabric.mod.json"] = json.dumps({
        "schemaVersion": 1, "id": MOD_ID, "version": VERSION,
        "name": "Sky Islands World Preset",
        "description": "把「天穹群岛」浮岛地形做成可选的世界类型（与默认/超平坦并列）。",
        "authors": ["skylands-262 port"], "license": "MIT", "environment": "*",
        "depends": {"fabricloader": ">=0.19.0", "minecraft": ">=26.1- <26.4-"},
        # 软依赖：只为「排到它们后面」（不硬失败）
        "recommends": {"structory": ">=0", "medieval_buildings": ">=0",
                       "towns_and_towers": ">=0"},
    }, indent=2, ensure_ascii=False) + "\n"
    return entries


def patch_structures(entries, mods_dir):
    """从 mods-stable 各 jar 里找出 STRUCT_PATCH 的结构定义，改 start_height 后整份覆盖。"""
    want = {k: v for k, v in STRUCT_PATCH.items()}
    done = {}
    if not os.path.isdir(mods_dir):
        print("    !! mods dir missing: %s" % mods_dir)
        return 0
    for jar_name in sorted(os.listdir(mods_dir)):
        if not jar_name.endswith(".jar") or not want:
            continue
        try:
            z = zipfile.ZipFile(os.path.join(mods_dir, jar_name))
        except Exception:
            continue
        for e in z.namelist():
            if "/worldgen/structure/" not in e or "/tags/" in e or not e.endswith(".json"):
                continue
            ns = e.split("/")[1]
            sid = "%s:%s" % (ns, e.split("/worldgen/structure/")[1][:-5])
            if sid not in want:
                continue
            d = json.loads(z.read(e))
            sh, drop = want[sid]
            old = json.dumps({k: d.get(k) for k in ("start_height", "project_start_to_heightmap")})
            d["start_height"] = sh
            if drop:
                d.pop("project_start_to_heightmap", None)
            entries[e] = json.dumps(d, indent=2, ensure_ascii=False) + "\n"
            done[sid] = (jar_name, old, json.dumps(sh))
            print("    %-28s %s  ->  %s" % (sid, old, json.dumps(sh)))
            want.pop(sid)
        z.close()
    for miss in want:
        print("    !! 未找到结构 %s（对应的 jar 不在 %s）" % (miss, mods_dir))
    return len(done)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    out = DEFAULT_OUT
    mods = MODS_STABLE
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--out":
            out = argv[i + 1]
        if a == "--mods":
            mods = argv[i + 1]

    a = zipfile.ZipFile(AEROLITH)
    mc = zipfile.ZipFile(MC_JAR)
    entries = build_entries(mc, a, mods)
    mc.close()
    a.close()

    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out):
        os.remove(out)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as w:
        for n, t in sorted(entries.items()):
            w.writestr(n, t.encode("utf-8"))
    print("\n写出 %s (%d 条目, %d B)" % (os.path.basename(out), len(entries),
                                       os.path.getsize(out)))
    for n in sorted(entries):
        print("   " + n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
