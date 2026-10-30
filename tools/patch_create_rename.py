#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_create_rename.py —— 26.3 里「同名同描述符、只是改了名字」的成员引用批量改名。

这类是最便宜的一类缺口：**描述符一模一样，只换常量池 NameAndType 的名字**，
指令长度/偏移/StackMapTable 全都不动，语义零损失（前提是确实只是改名）。

## 表（只收「描述符完全相同」的，语义可核对）

    owner / 旧名 / 描述符  ->  新名

来源：`tools/audit_create_api.py` 的「疑似改名」列（同描述符不同名）。

## 用法

    python tools/patch_create_rename.py --dry-run
    python tools/patch_create_rename.py
"""
import argparse
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from patch_create_ctxmap import Cf  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JAR = ROOT / "work" / "run26" / "mods-aero" / "create-fly-26.2-6.0.9-2-26.3-patched.jar"
BAK_SUFFIX = ".bak-black"

# (owner, old, desc, new)
TABLE = [
    ("net/minecraft/util/context/ContextMap$Builder", "withParameter",
     "(Lnet/minecraft/util/context/ContextKey;Ljava/lang/Object;)"
     "Lnet/minecraft/util/context/ContextMap$Builder;",
     "set"),
    ("net/minecraft/util/context/ContextMap$Builder", "getOptionalParameter",
     "(Lnet/minecraft/util/context/ContextKey;)Ljava/lang/Object;", "get"),
    ("net/minecraft/util/context/ContextMap$Builder", "create",
     "()Lnet/minecraft/util/context/ContextMap;", "build"),
    ("net/minecraft/world/level/block/CampfireBlock", "dowse",
     "(Lnet/minecraft/world/entity/Entity;Lnet/minecraft/world/level/LevelAccessor;"
     "Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;)V",
     "douse"),
]


def patch_class(buf, name, stats):
    cf = Cf(buf)
    changed = False
    for owner, old, desc, new in TABLE:
        idx = cf.find_ref(owner, old, desc)
        if idx is None:
            continue
        # 追加一个同名同描述符、只换名字的新 Methodref，然后把所有引用改指过去
        owner_cls = cf.class_name(int.from_bytes(cf.buf[int(cf.cp[idx][1]) + 1:
                                                      int(cf.cp[idx][1]) + 3], "big"))
        newidx = cf.add_methodref(owner_cls, new, desc,
                                  owner_class_idx=cf.find_class(owner_cls))
        # 把所有指向 idx 的指令改指 newidx（不改原条目，避免共享 NameAndType 误伤别人）
        data = bytearray(cf.buf)
        hit = 0
        for mname, mdesc, code in cf._methods():
            if not code:
                continue
            for off, op, _ln in decode(data, code[0], code[0] + code[1]):
                if op in (0xb6, 0xb7, 0xb8, 0xb9) or op == 0xb5 or op == 0xb4:
                    if int.from_bytes(data[off + 1:off + 3], "big") == idx:
                        data[off + 1:off + 3] = newidx.to_bytes(2, "big")
                        hit += 1
        if hit:
            cf.buf = bytes(data)
            cf.dirty = True
            changed = True
            stats[(owner, old, new)] = stats.get((owner, old, new), 0) + hit
    if not changed:
        return None
    return cf.serialize()


from patch_create_ctxmap import decode  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jar", default=str(DEFAULT_JAR))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    jar = Path(args.jar)
    zin = zipfile.ZipFile(jar)
    stats = {}
    plan = {}
    for n in zin.namelist():
        if not n.endswith(".class"):
            continue
        r = patch_class(zin.read(n), n[:-6], stats)
        if r:
            plan[n] = r

    for (owner, old, new), cnt in sorted(stats.items()):
        print("  %-55s %-22s -> %-12s %d 处" % (owner.split("/")[-1], old, new, cnt))
    print("改 %d 个 class，共 %d 处引用" % (len(plan), sum(stats.values())))
    if args.dry_run or not plan:
        return 0

    bak = jar.with_name(jar.name + BAK_SUFFIX)
    if not bak.exists():
        shutil.copy2(jar, bak)
        print("备份 -> %s" % bak.name)
    tmp = jar.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = plan[item.filename] if item.filename in plan else zin.read(item.filename)
            zi = zipfile.ZipInfo(item.filename, date_time=item.date_time)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = item.external_attr
            zout.writestr(zi, data)
    zin.close()
    shutil.move(str(tmp), str(jar))
    print("已写入 %s" % jar)
    return 0


if __name__ == "__main__":
    sys.exit(main())
