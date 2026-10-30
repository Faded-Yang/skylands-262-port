#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_aeronautics_tab.py -- 把创造标签页的 3 个 mixin 塞进**冻结版** aeronautics jar。

## 为什么不直接用 gradlew 产出的新 jar

`gradlew jar` 会把源码树里的 `data/**` 全量装回去（`advancement` 116+38、`recipe` 93+51、
`loot_table` 96+42），而冻结 jar 是**构建后再裁过数据**的（advancement 只剩 5/3、recipe 5/6）。
直接换新 jar 会立刻踩：

    Registry loading errors:
      > Errors in registry minecraft:advancement:
        Unknown registry key ... minecraft:trigger_type: simulated:big_beam_builtin
        Advancement criteria cannot be empty

⇒ 正确做法：以冻结 jar 为底（保住数据裁剪与所有已打补丁），只覆盖 3 个新 class + mixin 配置。

用法：
    python tools/patch_aeronautics_tab.py --base <frozen jar> --build <new jar> --out <out jar>
"""
import argparse
import os
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")

MIXIN_DIR = "dev/simulated_team/simulated/mixin/creative_tab_sections/"
NEW_CLASSES = [
    MIXIN_DIR + "CreativeModeInventoryScreenMixin.class",
    MIXIN_DIR + "CreativeModeTabMixin.class",
    MIXIN_DIR + "ItemPickerMenuMixin.class",
    # 标签页内容兜底（R362：section 元数据缺失 ⇒ 兜底列全部 simulated/aeronautics 物品）
    "dev/simulated_team/simulated/registrate/simulated_tab/SimulatedCreativeTab.class",
]
MIXIN_JSON = "simulated.mixins.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="冻结版 jar（数据已裁剪）")
    ap.add_argument("--build", required=True, help="gradlew 产出的新 jar（取新 class 与 mixins.json）")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    b = zipfile.ZipFile(args.base)
    n = zipfile.ZipFile(args.build)

    missing = [c for c in NEW_CLASSES if c not in n.namelist()]
    if missing:
        raise SystemExit("新 jar 里没有这些 class，编译没带上？%s" % missing)

    tmp = args.out + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        replaced = 0
        for item in b.infolist():
            # ⚠ base 里**已经有** SimulatedCreativeTab.class：必须先跳过旧副本，
            # 否则新副本会变成同名第二个 entry，Java 只加载第一个（旧版）⇒ 补丁等于没打。
            if item.filename in NEW_CLASSES:
                continue
            data = b.read(item.filename)
            if item.filename == MIXIN_JSON:
                data = n.read(MIXIN_JSON)
                replaced += 1
            z.writestr(item, data)
        assert replaced == 1, "base 里没有 %s" % MIXIN_JSON
        for c in NEW_CLASSES:
            z.writestr(c, n.read(c))
    os.replace(tmp, args.out)

    print("[out] %s" % args.out)
    print("       + %d 个 class, 替换 %s" % (len(NEW_CLASSES), MIXIN_JSON))
    print("       base entries %d -> %d" % (len(b.namelist()), len(zipfile.ZipFile(args.out).namelist())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
