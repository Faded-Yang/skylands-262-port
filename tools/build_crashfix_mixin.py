#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_crashfix_mixin.py —— 编译并打包 `sky262crashfix`（进世界 1 秒崩的修复）。

## 为什么

MC 26.3 的 `com.mojang.blaze3d.platform.InputConstants.isKeyDown(int)`：

    ByteBuffer b = SDLKeyboard.SDL_GetKeyboardState();
    return b != null && b.get(key) != 0;       // key >= limit 时 IndexOutOfBoundsException

`LevelLoadingScreen.onClose -> Gui.setScreen -> MouseHandler.grabMouse -> KeyMapping.setAll`
会在进世界那一刻遍历全部 KeyMapping 调它，一旦 SDL 键盘状态缓冲为空/过短就抛在 Render thread
⇒ `Minecraft.run` 当成致命错误 ⇒ 崩溃报告 + 退出。

修法：`InputConstantsGuardMixin`（`@Inject(at = HEAD, cancellable = true)`）在 HEAD 做同样的
边界检查，越界/空缓冲时返回 false（= 该键没按下），正常路径完全放行原方法。

## 产物

`work/run26/mods-aero/sky262crashfix-1.0.0.jar`（独立 mod，不碰任何其它 jar）：
    fabric.mod.json
    sky262crashfix.mixins.json
    skylands262/crashfix/CrashFixSupport.class
    skylands262/crashfix/mixin/InputConstantsGuardMixin.class

## 用法

    python tools/build_crashfix_mixin.py            # 编译 + 打包
    python tools/build_crashfix_mixin.py --no-jar   # 只编译
"""
import argparse
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work" / "run26" / "crashfix" / "src"
OUT = ROOT / "work" / "run26" / "crashfix" / "out"
MODS = ROOT / "work" / "run26" / "mods-aero"
JAR_OUT = MODS / "sky262crashfix-1.0.0.jar"

MC_HOME = Path(os.environ.get("APPDATA", "")) / ".minecraft"
MC_JAR = MC_HOME / "versions" / "26.3" / "26.3.jar"
JAVAC = MC_HOME / "runtime" / "java-runtime-epsilon" / "bin" / "javac.exe"

LIBS = [
    MC_HOME / "libraries" / "net" / "fabricmc" / "sponge-mixin" / "0.17.4+mixin.0.8.7" / "sponge-mixin-0.17.4+mixin.0.8.7.jar",
    MC_HOME / "libraries" / "org" / "lwjgl" / "lwjgl-sdl" / "3.4.3" / "lwjgl-sdl-3.4.3.jar",
    MC_HOME / "libraries" / "org" / "slf4j" / "slf4j-api" / "2.0.17" / "slf4j-api-2.0.17.jar",
]

RESOURCES = ["fabric.mod.json", "sky262crashfix.mixins.json"]


def java_sources():
    return sorted(str(p) for p in SRC.rglob("*.java"))


def compile_():
    for p in [MC_JAR, JAVAC] + LIBS:
        if not Path(p).is_file():
            print("!! 缺文件: %s" % p, file=sys.stderr)
            return False
    OUT.mkdir(parents=True, exist_ok=True)
    cp = ";".join(str(p) for p in [MC_JAR] + LIBS)
    srcs = java_sources()
    print("[1/2] javac %d 个源文件" % len(srcs), flush=True)
    cmd = [str(JAVAC), "-nowarn", "-encoding", "UTF-8", "--release", "21",
           "-cp", cp, "-d", str(OUT)] + srcs
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr, file=sys.stderr)
        return False
    if r.stderr.strip():
        print(r.stderr)
    print("      javac OK", flush=True)
    return True


def build_jar():
    print("[2/2] 打包 %s" % JAR_OUT.name, flush=True)
    classes = sorted(OUT.rglob("*.class"))
    if not classes:
        print("!! out/ 里没有 class", file=sys.stderr)
        return False
    tmp = JAR_OUT.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for name in RESOURCES:
            src = SRC / name
            if not src.is_file():
                print("!! 缺资源 %s" % src, file=sys.stderr)
                return False
            z.write(src, name)
        for c in classes:
            rel = c.relative_to(OUT).as_posix()
            z.write(c, rel)
    tmp.replace(JAR_OUT)
    # 自检：mixin 配置里的类必须真的在 jar 里
    with zipfile.ZipFile(JAR_OUT) as z:
        names = set(z.namelist())
        cfg = json.loads(z.read("sky262crashfix.mixins.json"))
        pkg = cfg["package"].replace(".", "/")
        for cls in cfg.get("client", []) + cfg.get("mixins", []):
            entry = "%s/%s.class" % (pkg, cls)
            if entry not in names:
                print("!! jar 里缺 %s" % entry, file=sys.stderr)
                return False
        print("      jar OK：%d 个条目，%d bytes" % (len(names), JAR_OUT.stat().st_size))
        print("      内容: %s" % ", ".join(sorted(names)))
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-jar", action="store_true")
    a = ap.parse_args()
    if not compile_():
        return 2
    if a.no_jar:
        return 0
    return 0 if build_jar() else 2


if __name__ == "__main__":
    sys.exit(main())
