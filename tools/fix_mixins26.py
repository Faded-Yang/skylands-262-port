#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_mixins26.py —— 按 audit_mixins26.py 的结果批量修 mixin。

两类修改，**成对**执行，绝不单独做：
  A. 致命条目 → 从 *.mixins.json 摘掉 + 把 .java 移到 <src>\\_dropped_mixin26\\
     （只摘不移：类还在源码里但没注册，无害；只移不摘：运行期 MixinApplyError）
  B. 注入点缺失（require 有效值 > 0）→ 给对应 @Inject/... 加 `require = 0`（只告警不崩）

用法：
  python tools/fix_mixins26.py --dry-run        # 只打印计划
  python tools/fix_mixins26.py                  # 执行
  python tools/fix_mixins26.py --only-require0  # 只做 B
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_mixins26 as A  # noqa: E402

ROOT = A.ROOT
REPORT = ROOT / "tools" / ".cache" / "mixinaudit26" / "report.json"

# ---------------------------------------------------------------------------
# 致命条目：摘条目 + 移走类。value = 原因（写进 MANIFEST / 交付说明）
# ---------------------------------------------------------------------------
DROP = {
    # ---- 目标 class → interface -------------------------------------------------
    ("sable", "explosion.ExplosionMixin"):
        "26.3 Explosion 变 interface；实现类 ServerExplosion 无 x/y/z 字段（只有 center:Vec3）、"
        "level 是 ServerLevel，且 explode 的方块循环搬到 interactWithBlocks —— retarget 是重写不是改名，整条降级",
    # ---- 目标成员被删/语义变了，无法机械替换 ------------------------------------
    ("sable", "entity.entity_leashing.LeashableMixin"):
        "@Overwrite 的 legacyElasticRangeLeashBehaviour 在 26.3 删除（换成 onElasticLeashPull/checkElasticInteractions），语义不同",
    ("sable", "entity.entities_stick_sublevels.LivingEntityMixin"):
        "26.3 LivingEntity 的 lerpSteps/lerpYRot/lerpXRot 删除，换成 lerpHeadSteps/lerpYHeadRot + lerpHeadRotationStep（头部而非身体插值），语义不同",
    ("sable", "sign_interaction.SignBlockEntityMixin"):
        "isFacingFrontText(Player) 删除，26.3 换成 getSlotPlayerIsFacing(Player)->SignTextSlot（返回类型/语义都变了）",
    ("sable", "world_border.LevelMixin"):
        "26.3 Level 无 worldBorder 字段（也无 getWorldBorder），border 数据搬到 LevelData 侧",
    # ---- 渲染侧：26.3 渲染管线改成 submit/extract 两段式，字段整体删除 ----------
    ("sable", "block_decal_render.LevelRendererMixin"):
        "LevelRenderer 无 level 字段（26.3 渲染改 submit 阶段）；同族渲染降级",
    ("sable", "particle.LevelRendererMixin"):
        "LevelRenderer 无 level 字段；addParticleInternal 签名也变了",
    ("sable", "sublevel_render.LevelRendererMixin"):
        "LevelRenderer 无 level/allChanged/renderLevel（26.3 改 submit 两段式）",
    ("sable", "sublevel_render.block_entity_render.LevelRendererMixin"):
        "LevelRenderer 无 level/destructionProgress 字段，BlockEntityRenderDispatcher 三阶段化",
    ("sable", "sublevel_render.impl.vanilla.LevelRendererMixin"):
        "LevelRenderer 无 level/minecraft 字段；setupRender/isSectionCompiled/renderSectionLayer 全删",
    ("sable", "sublevel_render.RenderSectionAccessor"):
        "26.3 RenderSection 完全重写，无 globalBlockEntities 字段（唯一引用处 VanillaChunkedSubLevelRenderData 的 import 已删）",
    ("sable", "sublevel_render.RenderSectionMixin"):
        "26.3 RenderSection 无 dirty 字段 / getDistToPlayerSqr / setDirty",
    ("sable", "entity.entity_rotations_and_riding.EntityRenderDispatcherMixin"):
        "EntityRenderDispatcher 无 level 字段，render(...) 已三阶段化",
    ("sable-fabric", "block_outline_render.LevelRendererMixin"):
        "LevelRenderer 无 level 字段；renderLevel 在 26.3 删除",
    ("simulated", "accessor.CreateBlockEntityBuilderAccessor"):
        "目标 CreateBlockEntityBuilder 在 create-fly 里不存在（本项目 src/stub 的垫片无 visualFactory/renderNormally 字段），"
        "@Accessor 应用期会失败；且无任何源码引用",
    ("simulated", "ponder.PonderUIMixin"):
        "26.3 PonderUI.renderScene 参数改成 (GuiGraphicsExtractor,int,int,float,float)，scene index 不再是参数；"
        "@Inject 回调描述符无法机械对齐（ponder 阴影偏移/淡出降级）",
    # ---- 可选 mod 不存在 --------------------------------------------------------
    ("sable", "compatibility.etched.StopListeningSoundMixin"):
        "目标 gg.moonflower.etched... 是可选 compat，运行环境里没有 Etched 这个 mod",
}


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------
def load_report():
    if not REPORT.is_file():
        sys.exit(f"找不到审计报告 {REPORT}；先跑 tools\\audit_mixins26.py --json {REPORT}")
    return json.loads(REPORT.read_text(encoding="utf-8"))


def cfg_by_name(name):
    for c in A.CONFIGS:
        if c["name"] == name:
            return c
    raise KeyError(name)


def drop_entries(report, dry=False):
    plan = []
    for it in report["items"]:
        key = (it["config"], it["entry"])
        if key not in DROP:
            continue
        plan.append((key, it))
    if not plan:
        print("[drop] 没有要摘的条目")
        return 0

    # 按配置分组改 json（先全部读完再写，避免半途）
    docs = {}
    for name in {k[0] for k, _ in plan}:
        c = cfg_by_name(name)
        docs[name] = (c, json.loads(c["cfg"].read_text(encoding="utf-8")))

    moved = 0
    manifest = []
    for (name, entry), it in plan:
        c, data = docs[name]
        found = False
        for sect in A.SECTIONS:
            lst = data.get(sect) or []
            if entry in lst:
                lst.remove(entry)
                found = True
        if not found:
            print(f"[drop] !! json 里找不到条目 {name}:{entry}（可能已摘）")
            continue
        src = Path(it["file"])
        dst = c["drop"] / src.relative_to(c["src"])
        print(f"[drop] {name:<14} {entry:<58} -> {dst.relative_to(ROOT)}")
        if not dry:
            if src.is_file():
                dst.parent.mkdir(parents=True, exist_ok=True)
                if dst.exists():
                    dst.unlink()
                shutil.move(str(src), str(dst))
                moved += 1
            else:
                print(f"        !! 源文件不存在: {src}")
        manifest.append((name, entry, DROP[(name, entry)], str(dst.relative_to(ROOT))))

    if not dry:
        for name, (c, data) in docs.items():
            c["cfg"].write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")
            print(f"[drop] 已重写 {c['cfg'].name}")
        # MANIFEST
        if manifest:
            c0 = cfg_by_name(manifest[0][0])
            man = c0["drop"] / "MANIFEST.md"
            man.parent.mkdir(parents=True, exist_ok=True)
            lines = ["# _dropped_mixin26 —— 26.3 下摘掉的 mixin 条目\n",
                     "> 由 `tools/fix_mixins26.py` 生成。每条都已从对应 `*.mixins.json` 摘除，",
                     "> 源码移到本目录。**不要单独恢复其中一半**。\n"]
            for name, entry, reason, dst in manifest:
                lines.append(f"- `{name}` / `{entry}`：{reason}")
            man.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"[drop] MANIFEST: {man.relative_to(ROOT)}")
    return moved


def _annotations_missing(src, names):
    """返回需要加 require=0 的 (start,end,ann_name) 列表。"""
    hits = []
    for ann in A.INJECTORS:
        for (s, e, argstr) in A.find_annotations(src, ann):
            if not argstr:
                continue
            for key, vals in A.parse_annotation_args(argstr):
                if key != "method":
                    continue
                for v in vals:
                    got = A.parse_method_spec(v)
                    if not got:
                        continue
                    nm = got[0]
                    if nm in names:
                        hits.append((s, e, ann))
                        break
    # 去重（同一注解多个 method 值只补一次）
    seen, out = set(), []
    for s, e, ann in hits:
        if s in seen:
            continue
        seen.add(s)
        out.append((s, e, ann))
    return out


def add_require0(text, start, end, ann_name):
    inner = text[start:end]
    m = re.search(r"\brequire\s*=\s*(\d+)", inner)
    if m:
        if m.group(1) == "0":
            return text, False
        return (text[:start + m.start(1)] + "0" + text[start + m.end(1):], True)
    # 插到最后一个 ')' 前的非空白处
    close = end - 1
    assert text[close] == ")", text[start:end][:80]
    ins = close
    while ins > 0 and text[ins - 1].isspace():
        ins -= 1
    sep = "" if text[ins - 1] in "(," else ", "
    return text[:ins] + sep + "require = 0" + text[ins:], True


def require0(report, dry=False):
    changed = 0
    for it in report["items"]:
        if not it["status"].startswith("FIX:"):
            continue
        if (it["config"], it["entry"]) in DROP:
            continue
        names = set()
        for p in it["problems"]:
            if p["level"] != "fix":
                continue
            m = re.search(r"目标方法不存在:\s*(\S+)", p["text"])
            if m:
                names.add(m.group(1).split("(")[0])
            m = re.search(r"方法\s+(\S+)\s+描述符不符", p["text"])
            if m:
                names.add(m.group(1).split("(")[0])
        if not names:
            print(f"[require0] !! {it['entry']} 状态是 FIX 但解析不出方法名，跳过")
            continue
        path = Path(it["file"])
        raw = path.read_text(encoding="utf-8", errors="replace")
        src = A.strip_comments(raw)
        hits = _annotations_missing(src, names)
        if not hits:
            print(f"[require0] !! {it['entry']} 源码里找不到对应 method= 注解，跳过")
            continue
        new = raw
        # 从后往前改，保证偏移有效
        for s, e, ann in sorted(hits, key=lambda x: -x[0]):
            new, did = add_require0(new, s, e, ann)
            if did:
                changed += 1
        print(f"[require0] {it['config']:<14} {it['entry']:<58} "
              f"ann={','.join(h[2] for h in hits)} names={sorted(names)}")
        if not dry:
            path.write_text(new, encoding="utf-8")
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only-require0", action="store_true")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    report = load_report()
    print(f"报告: {REPORT}")
    print(f"总条目 {report['summary']['total']}，坏 {report['summary']['bad']}")
    if not args.only_require0:
        drop_entries(report, args.dry_run)
    n = require0(report, args.dry_run)
    print(f"\n[summary] require=0 补了 {n} 处；drop 见上")


if __name__ == "__main__":
    main()
