# -*- coding: utf-8 -*-
"""扫 Create jar 的类继承关系：
1) AbstractSimiWidget 的所有子类里，谁覆盖了 extractRenderState / extractWidgetRenderState；
2) PackageEntity / BlueprintEntity / EjectorItemEntity 的子类里，谁覆盖了 canSimulateMovement /
   moveOrInterpolateTo(Vec3,FF)；
3) 谁调用了这些方法（判断删除是否是「解析回父类」安全的）。"""
import importlib.util
import zipfile
from collections import defaultdict

spec = importlib.util.spec_from_file_location("ac", "tools/audit_create_api.py")
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)

JAR = "work/run26/mods-aero/create-fly-26.2-6.0.9-2-26.3-patched.jar"
z = zipfile.ZipFile(JAR)
names = [n for n in z.namelist() if n.endswith(".class") and not n.startswith("META-INF/")]

info = {}
for n in names:
    try:
        d = ac.parse_class(z.read(n))
    except Exception:
        continue
    info[d["name"]] = d
z.close()
print("解析 %d 个类" % len(info))

children = defaultdict(list)
for cn, d in info.items():
    for s in d["supers"]:
        children[s].append(cn)


def subclasses(root):
    out, stack = [], [root]
    while stack:
        c = stack.pop()
        for ch in children.get(c, []):
            if ch not in out:
                out.append(ch)
                stack.append(ch)
    return out


def has(d, name, desc):
    return desc in (d["methods"].get(name) or set())


TARGETS = [
    ("AbstractSimiWidget", "com/zurrtum/create/client/catnip/gui/widget/AbstractSimiWidget",
     [("extractRenderState", "(Lnet/minecraft/client/gui/GuiGraphicsExtractor;IIF)V"),
      ("extractWidgetRenderState", "(Lnet/minecraft/client/gui/GuiGraphicsExtractor;IIF)V")]),
    ("PackageEntity", "com/zurrtum/create/content/logistics/box/PackageEntity",
     [("canSimulateMovement", "()Z")]),
    ("BlueprintEntity", "com/zurrtum/create/content/equipment/blueprint/BlueprintEntity",
     [("moveOrInterpolateTo", "(Lnet/minecraft/world/phys/Vec3;FF)V")]),
    ("EjectorItemEntity", "com/zurrtum/create/content/logistics/depot/EjectorItemEntity",
     [("moveOrInterpolateTo", "(Lnet/minecraft/world/phys/Vec3;FF)V")]),
]

for label, root, methods in TARGETS:
    print("=" * 70)
    print(label, root, "存在" if root in info else "**不在 jar 里**")
    subs = subclasses(root)
    print("  子类 %d 个: %s" % (len(subs), ", ".join(s.split("/")[-1] for s in subs[:20])))
    for nm, ds in methods:
        over = [c for c in subs if has(info.get(c, {}), nm, ds)]
        print("  %s%s 被这些子类覆盖: %s" % (nm, ds, over or "无"))
        # 调用点：谁引用了 (任意 owner, nm, ds)
        callers = []
        for cn, d in info.items():
            for i, (kind, owner, n2, d2) in d["member_refs"].items():
                if n2 == nm and d2 == ds and kind == "M" and owner == root:
                    callers.append(cn)
        print("    引用 owner==%s 的调用方: %d 个 %s"
              % (root.split("/")[-1], len(set(callers)),
                 ", ".join(sorted(set(x.split("/")[-1] for x in callers))[:12])))
