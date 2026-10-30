# -*- coding: utf-8 -*-
"""在所有 mod jar（含嵌套）里搜字符串 'terrainzapper' / 'SphereBrush'，找出谁引用了它
（用来判断是不是某个 mixin 往 SphereBrush.<init> 里注入了代码）。"""
import io
import zipfile
from pathlib import Path

MODS = Path("work/run26/mods-aero")
NEEDLES = [b"terrainzapper", b"SphereBrush", b"TerrainBrushes"]


def scan(name, z, depth=0):
    for e in z.namelist():
        if not e.endswith(".class"):
            continue
        try:
            b = z.read(e)
        except Exception:
            continue
        for nd in NEEDLES:
            if nd in b:
                print("%s%-70s 含 %s" % ("  " * depth, e, nd.decode()))
    for e in z.namelist():
        if e.endswith(".jar") and depth < 2:
            try:
                inner = zipfile.ZipFile(io.BytesIO(z.read(e)))
            except Exception:
                continue
            print("%s[嵌套] %s!%s" % ("  " * depth, name, e))
            scan(name + "!" + e, inner, depth + 1)


for jar in sorted(MODS.glob("*.jar")):
    print("=" * 90)
    print(jar.name)
    scan(jar.name, zipfile.ZipFile(jar))
