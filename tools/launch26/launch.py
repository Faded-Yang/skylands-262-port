#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
launch.py -- 可复用的 "Minecraft 26.3 + Fabric" 客户端启动器

设计目标
--------
* 从 <mc>/versions/26.3/26.3.json 读 vanilla 元数据（libraries / assetIndex /
  mainClass / arguments.game / arguments.jvm），从 fabric profile json 读 Fabric
  的 libraries + mainClass，两者合并成一条可复现的 argv。
* 缺库自动下载（vanilla 用 downloads.artifact.url；Fabric 的库只有 maven
  group:artifact:version + repo url，按 maven 布局自己拼 path）。
* 所有写操作只落在 --game-dir 里（mods / natives / logs / 启动脚本 / 控制台日志），
  对 %APPDATA%\.minecraft 严格只读。
* --watch-title：盯 <game-dir>/logs/latest.log，命中"标题画面"标记行后自己杀掉
  进程树，用来做无人值守验收。

思路参考 minecraft-launcher-lib (JakobDev, MIT) 的 command.py：按 rules 过滤库、
拼 classpath、逐条替换 ${placeholder}。此处为自写实现，并补上了
arch 级 natives 过滤、sha1 校验、缺库补下载与标题画面哨兵。

用法
----
  python launch.py --game-dir D:\tmp\run1 --mods <mods目录> [--dry-run] [--watch-title]

只读环境变量：APPDATA 用来定位默认 .minecraft / java。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

# --------------------------------------------------------------------------- #
# 常量 / 默认值
# --------------------------------------------------------------------------- #

MC_VERSION = "26.3"
FABRIC_MAIN_CLASS = "net.fabricmc.loader.impl.launch.knot.KnotClient"
USER_AGENT = "launch26/1.0 (skylands-262 port harness)"

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]                     # ...\skylands-262
DEFAULT_FABRIC_PROFILE = REPO_ROOT / "work" / "fabric-profile-26.3.json"


def default_mc_dir() -> Path:
    return Path(os.environ.get("APPDATA", str(Path.home()))) / ".minecraft"


def default_java(mc_dir: Path) -> Path:
    return mc_dir / "runtime" / "java-runtime-epsilon" / "bin" / "java.exe"


# --------------------------------------------------------------------------- #
# 小工具
# --------------------------------------------------------------------------- #

def log(msg: str) -> None:
    print(msg, flush=True)


def _force_utf8_console() -> None:
    """Windows 控制台默认 cp936，中文/路径会把捕获端弄成乱码。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass


_force_utf8_console()


def sha1_of(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def norm_arch() -> str:
    """把 platform.machine() 归一成 launcher 用的口径 (x86 / x86_64 / arm64)。"""
    m = platform.machine().lower()
    if m in ("amd64", "x86_64", "x64"):
        return "x86_64"
    if m in ("arm64", "aarch64"):
        return "arm64"
    if m in ("x86", "i386", "i686"):
        return "x86"
    return m


def norm_os() -> str:
    s = platform.system().lower()
    return {"windows": "windows", "darwin": "osx", "linux": "linux"}.get(s, s)


# 本启动器不打开任何 launcher feature（demo / 自定义分辨率 / quickPlay 全部关掉）
FEATURES: dict[str, bool] = {
    "is_demo_user": False,
    "has_custom_resolution": False,
    "has_quick_plays_support": False,
    "is_quick_play_singleplayer": False,
    "is_quick_play_multiplayer": False,
    "is_quick_play_realms": False,
}

OS_INFO = {"name": norm_os(), "arch": norm_arch(), "version": platform.release()}


def rules_allow(rules, os_info=None, features=None) -> bool:
    """按 Mojang 的 rules 语义判定一条 library / argument 是否生效。

    规则列表为空 => 允许。否则从"默认拒绝"开始，按顺序匹配；最后一条命中的
    action 决定结果。规则里出现的每个条件都必须匹配（os.name / os.arch /
    os.version 正则 / features 全等）。
    """
    if not rules:
        return True
    os_info = os_info or OS_INFO
    features = FEATURES if features is None else features
    allow = False
    for rule in rules:
        matched = True
        if "os" in rule:
            want = rule["os"]
            if "name" in want and want["name"] != os_info.get("name"):
                matched = False
            if "arch" in want:
                arch = want["arch"]
                # launcher 在 32 位上写 "x86"，我们按前缀宽松匹配
                if arch != os_info.get("arch") and not (
                    arch == "x86" and os_info.get("arch") == "x86"
                ):
                    matched = False
            if "version" in want:
                import re

                if not re.match(want["version"], str(os_info.get("version", ""))):
                    matched = False
        if "features" in rule:
            for k, v in rule["features"].items():
                if bool(features.get(k, False)) != bool(v):
                    matched = False
        if matched:
            allow = rule.get("action") == "allow"
    return allow


def flatten_args(entries) -> list[str]:
    """arguments.game / arguments.jvm 是 str | {rules,value} 的混合数组。"""
    out: list[str] = []
    for entry in entries or []:
        if isinstance(entry, str):
            out.append(entry)
            continue
        if not isinstance(entry, dict):
            continue
        if not rules_allow(entry.get("rules")):
            continue
        value = entry.get("value")
        if isinstance(value, str):
            out.append(value)
        elif isinstance(value, list):
            out.extend(str(v) for v in value)
    return out


def maven_to_path(name: str) -> str:
    """'group:artifact:version[:classifier]' -> 'group/artifact/version/artifact-version[-classifier].jar'"""
    parts = name.split(":")
    if len(parts) < 3:
        raise ValueError(f"无法解析的 maven 坐标: {name}")
    group, artifact, version = parts[0], parts[1], parts[2]
    classifier = parts[3] if len(parts) > 3 else None
    filename = f"{artifact}-{version}" + (f"-{classifier}" if classifier else "") + ".jar"
    return f"{group.replace('.', '/')}/{artifact}/{version}/{filename}"


# --------------------------------------------------------------------------- #
# 库解析
# --------------------------------------------------------------------------- #

class Lib:
    __slots__ = ("path", "url", "sha1", "size", "origin", "name")

    def __init__(self, path, url, sha1, size, origin, name):
        self.path = path          # 相对 libraries/ 的路径
        self.url = url            # 完整下载 URL 或 None
        self.sha1 = sha1          # 期望 sha1 或 None
        self.size = size
        self.origin = origin      # "vanilla" | "fabric"
        self.name = name

    def __repr__(self):
        return f"<Lib {self.path}>"


# 我们跑的是 x86_64：显式剔掉别的架构的 natives 包。
# 26.3.json 里 `...:natives-windows-arm64` 的 rules 只写了 os.name=windows，
# 官方 rules 过滤放不过它 —— 而 arm64 的 dll 同名（lwjgl.dll），一旦排在前面被
# 共享库加载器抽出来就会 0xc000007b。所以在 rules 之后再按名字补一刀。
_FOREIGN_ARCH_TOKENS = {
    "x86_64": ("arm64", "aarch64", "x86_32", "i386"),
    "arm64": ("x86_64", "x86_32", "i386"),
}


def is_foreign_arch_natives(name: str) -> bool:
    for token in _FOREIGN_ARCH_TOKENS.get(norm_arch(), ()):
        if f":natives-{token}" in name or name.endswith(f"-{token}"):
            return True
        if token in ("arm64", "aarch64") and "arm64" in name:
            return True
    return False


def collect_libraries(vanilla_json, fabric_json=None) -> list[Lib]:
    libs: dict[str, Lib] = {}

    for entry in vanilla_json.get("libraries", []):
        if not rules_allow(entry.get("rules")):
            continue
        name = entry.get("name", "")
        downloads = entry.get("downloads") or {}

        # 1) 现代格式：downloads.artifact
        art = downloads.get("artifact")
        if art and art.get("path"):
            if is_foreign_arch_natives(name):
                continue
            libs.setdefault(
                art["path"],
                Lib(art["path"], art.get("url"), art.get("sha1"), art.get("size"),
                    "vanilla", name),
            )
            continue

        # 2) 老格式：downloads.classifiers + natives 映射（26.3 用不到，留着保证通用）
        natives = entry.get("natives")
        if natives and downloads.get("classifiers"):
            classifier = natives.get(norm_os())
            if classifier:
                classifier = classifier.replace("${arch}", "64" if norm_arch() == "x86_64" else "32")
                art = downloads["classifiers"].get(classifier)
                if art and art.get("path"):
                    libs.setdefault(
                        art["path"],
                        Lib(art["path"], art.get("url"), art.get("sha1"), art.get("size"),
                            "vanilla", name),
                    )
                    continue

    if fabric_json:
        for entry in fabric_json.get("libraries", []):
            if not rules_allow(entry.get("rules")):
                continue
            name = entry.get("name", "")
            path = maven_to_path(name)
            base = entry.get("url") or "https://maven.fabricmc.net/"
            if not base.endswith("/"):
                base += "/"
            libs.setdefault(
                path,
                Lib(path, base + path, entry.get("sha1"), entry.get("size"), "fabric", name),
            )

    return sorted(libs.values(), key=lambda l: (l.origin != "vanilla", l.path))


# --------------------------------------------------------------------------- #
# 下载
# --------------------------------------------------------------------------- #

def download(url: str, dest: Path, expect_sha1: str | None = None,
             expect_size: int | None = None) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    log(f"[download] {url}")
    log(f"           -> {dest}")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=180) as resp, tmp.open("wb") as f:
        shutil.copyfileobj(resp, f, 1 << 20)
    got = tmp.stat().st_size
    if expect_size is not None and got != expect_size:
        tmp.unlink()
        raise RuntimeError(f"大小不符: {url} 期望 {expect_size} 实得 {got}")
    if expect_sha1:
        actual = sha1_of(tmp)
        if actual != expect_sha1:
            tmp.unlink()
            raise RuntimeError(f"sha1 不符: {url} 期望 {expect_sha1} 实得 {actual}")
    tmp.replace(dest)
    log(f"[download] ok {got/1048576:.1f} MiB in {time.time()-t0:.1f}s")


def ensure_library(lib: Lib, libraries_root: Path, allow_download: bool) -> tuple[Path, bool]:
    """返回 (本地路径, 是否本来就有)。allow_download=False 时只报告不下载。"""
    local = libraries_root / lib.path
    if local.is_file() and local.stat().st_size > 0:
        return local, True
    if not allow_download:
        return local, False
    if not lib.url:
        raise RuntimeError(f"缺库且没有下载地址: {lib.path} ({lib.name})")
    download(lib.url, local, lib.sha1, lib.size)
    return local, False


# --------------------------------------------------------------------------- #
# natives
# --------------------------------------------------------------------------- #

def prepare_natives(src_natives: Path, game_dir: Path) -> Path:
    """把 26.3-natives 的已解包 dll + jna/lwjgl/netty 子目录复制到 game-dir/natives。

    为什么复制而不是直接用 <mc>/versions/26.3/26.3-natives：
    -Dorg.lwjgl.system.SharedLibraryExtractPath / -Djna.tmpdir / -Dio.netty.native.workdir
    都指向 natives 目录内部，直接指 .minecraft 就等于往里写东西。复制一份到
    game-dir 后，.minecraft 保持只读。
    """
    dest = game_dir / "natives"
    if dest.is_dir() and any(dest.iterdir()):
        # 已有内容：只补齐缺失文件，避免每次启动都重拷 20 MB
        for item in src_natives.rglob("*"):
            rel = item.relative_to(src_natives)
            target = dest / rel
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            elif not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_natives, dest, dirs_exist_ok=True)
    return dest


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #

def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def sync_mods(mods_src: Path, game_dir: Path) -> list[str]:
    mods_dir = game_dir / "mods"
    mods_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for jar in sorted(mods_src.glob("*.jar")):
        target = mods_dir / jar.name
        # 只比大小会漏掉「同尺寸不同内容」（例如只改了 accesswidener 头 / mixins.json），
        # 必须同时比 mtime，否则会拿上一轮的旧 jar 启动。
        if (target.exists()
                and target.stat().st_size == jar.stat().st_size
                and int(target.stat().st_mtime) == int(jar.stat().st_mtime)):
            copied.append(f"{jar.name} (已存在)")
            continue
        shutil.copy2(jar, target)
        copied.append(jar.name)
    # --mods 是权威来源：清掉 mods 里这次没给的旧 jar，避免上一轮残留污染验收
    keep = {jar.name for jar in mods_src.glob("*.jar")}
    for stale in mods_dir.glob("*.jar"):
        if stale.name not in keep:
            stale.unlink()
            copied.append(f"-{stale.name} (移除)")
    return copied


def build_command(args, mc_dir: Path) -> tuple[list[str], dict, list[Lib], Path]:
    """组装完整命令行。返回 (argv, 诊断信息, 库列表, natives 目录)。"""
    version_dir = mc_dir / "versions" / MC_VERSION
    vanilla_json_path = version_dir / f"{MC_VERSION}.json"
    vanilla = load_json(vanilla_json_path)
    fabric = load_json(args.fabric_profile) if args.fabric_profile else None

    client_jar = version_dir / f"{MC_VERSION}.jar"
    game_dir = args.game_dir.resolve()

    libraries_root = mc_dir / "libraries"
    libs = collect_libraries(vanilla, fabric)

    allow_download = not args.dry_run
    missing: list[str] = []
    classpath_entries: list[str] = []
    for lib in libs:
        local, existed = ensure_library(lib, libraries_root, allow_download)
        if not existed:
            missing.append(lib.path)
        classpath_entries.append(str(local))

    # vanilla 客户端 jar
    if not client_jar.is_file():
        client = (vanilla.get("downloads") or {}).get("client") or {}
        if allow_download and client.get("url"):
            download(client["url"], client_jar, client.get("sha1"), client.get("size"))
            missing.append(str(client_jar))
        elif not args.dry_run:
            raise RuntimeError(f"缺少客户端 jar 且无法下载: {client_jar}")
    classpath_entries.append(str(client_jar))

    classpath = ";".join(classpath_entries) if os.name == "nt" else ":".join(classpath_entries)

    # ---- natives 目录 ----
    if args.natives_dir:
        natives_dir = Path(args.natives_dir).resolve()
        if not args.dry_run:
            natives_dir.mkdir(parents=True, exist_ok=True)
    else:
        src_natives = version_dir / f"{MC_VERSION}-natives"
        if args.dry_run:
            natives_dir = game_dir / "natives"
        else:
            natives_dir = prepare_natives(src_natives, game_dir)

    # ---- log4j 配置（26.3 用的是 assets/log_configs/client-1.21.2.xml）----
    log_config = None
    logging_cfg = (vanilla.get("logging") or {}).get("client") or {}
    if logging_cfg:
        cfg_file = logging_cfg.get("file") or {}
        candidate = mc_dir / "assets" / "log_configs" / str(cfg_file.get("id"))
        if candidate.is_file():
            log_config = candidate
        elif not args.dry_run and cfg_file.get("url"):
            candidate = game_dir / "log_configs" / str(cfg_file.get("id"))
            download(cfg_file["url"], candidate, cfg_file.get("sha1"), cfg_file.get("size"))
            log_config = candidate

    asset_index = (vanilla.get("assetIndex") or {}).get("id") or vanilla.get("assets") or MC_VERSION

    # ---- 占位符表 ----
    subs = {
        "auth_player_name": args.username,
        "version_name": MC_VERSION,
        "game_directory": str(game_dir),
        "assets_root": str(mc_dir / "assets"),
        "assets_index_name": asset_index,
        "auth_uuid": args.uuid,
        "auth_access_token": args.access_token,
        "clientid": "",
        "auth_xuid": "",
        "user_type": "legacy",
        "version_type": vanilla.get("type", "release"),
        "user_properties": "{}",
        "natives_directory": str(natives_dir),
        "launcher_name": "launch26",
        "launcher_version": "1.0",
        "classpath": classpath,
        "classpath_separator": ";" if os.name == "nt" else ":",
        "library_directory": str(libraries_root),
        "resolution_width": str(args.width),
        "resolution_height": str(args.height),
        "quickPlayPath": "",
        "quickPlaySingleplayer": "",
        "quickPlayMultiplayer": "",
        "quickPlayRealms": "",
    }

    def substitute(token: str) -> str:
        for k, v in subs.items():
            token = token.replace("${" + k + "}", v)
        return token

    # ---- JVM 参数 ----
    jvm_args = flatten_args((vanilla.get("arguments") or {}).get("jvm"))
    if not jvm_args:                     # 极老版本兜底
        jvm_args = ["-Djava.library.path=${natives_directory}", "-cp", "${classpath}"]
    jvm_args = [substitute(a) for a in jvm_args]

    # java.library.path: vanilla 给的是 ${natives_directory}/java（这版本来就不存在，
    # 库实际由 lwjgl 的 SharedLibraryExtractPath 抽取）。我们把真实 dll 目录也串进去兜底。
    extra_lib_dirs = [str(natives_dir / "java")]
    for dll_dir in sorted({p.parent for p in natives_dir.rglob("*.dll")}):
        extra_lib_dirs.append(str(dll_dir))
    lib_path_value = ";".join(extra_lib_dirs) if os.name == "nt" else ":".join(extra_lib_dirs)
    for i, a in enumerate(jvm_args):
        if a.startswith("-Djava.library.path="):
            jvm_args[i] = "-Djava.library.path=" + lib_path_value

    # Fabric profile 自带的 jvm 参数（-DFabricMcEmu= ...）
    if fabric:
        jvm_args += [substitute(a) for a in flatten_args((fabric.get("arguments") or {}).get("jvm"))]

    if log_config:
        jvm_args.append(f"-Dlog4j.configurationFile={log_config}")

    # 关键 dsh 参数：Java 25 / JEP 472 需要显式放行 JNI，否则 LWJGL 直接起不来
    if not any(a.startswith("--enable-native-access") for a in jvm_args):
        jvm_args.append("--enable-native-access=ALL-UNNAMED")
    jvm_args.append(f"-Dfabric.gameVersion={MC_VERSION}")
    jvm_args.append("-Dfabric.development=false")
    if args.xmx and not any(a.startswith("-Xmx") for a in jvm_args):
        jvm_args.append(f"-Xmx{args.xmx}")
    if args.xms and not any(a.startswith("-Xms") for a in jvm_args):
        jvm_args.append(f"-Xms{args.xms}")

    for extra in args.extra_jvm_arg or []:
        jvm_args.append(extra)

    # ---- game 参数 ----
    game_args = flatten_args((vanilla.get("arguments") or {}).get("game"))
    if fabric:
        game_args += [substitute(a) for a in flatten_args((fabric.get("arguments") or {}).get("game"))]
    game_args = [substitute(a) for a in game_args]
    if not any(a == "--width" for a in game_args):
        game_args += ["--width", str(args.width), "--height", str(args.height)]
    for extra in args.extra_game_arg or []:
        game_args.append(extra)

    # 空值占位符（--clientId "" / --xuid ""）保留原样：官方 launcher 离线时也这样传
    main_class = FABRIC_MAIN_CLASS if fabric else vanilla.get("mainClass")

    argv = [str(args.java)] + jvm_args + [main_class] + game_args
    info = {
        "version_json": str(vanilla_json_path),
        "fabric_profile": str(args.fabric_profile) if args.fabric_profile else None,
        "main_class": main_class,
        "asset_index": asset_index,
        "natives_dir": str(natives_dir),
        "library_count": len(libs),
        "classpath_entry_count": len(classpath_entries),
        "downloaded_missing": missing,
        "log4j_config": str(log_config) if log_config else None,
        "game_dir": str(game_dir),
    }
    return argv, info, libs, natives_dir


# --------------------------------------------------------------------------- #
# 启动 + 标题画面哨兵
# --------------------------------------------------------------------------- #

TITLE_MARKERS = [
    "Backend library:",          # LWJGL 起来了
    "Sound engine started",      # 音频初始化完成
]
TITLE_MARKER_ATLAS = "blocks.png-atlas"   # 图集烘完 = 资源加载完成

ANSI_OR_BAD = ("\x00",)


def tail_new_lines(path: Path, offset: int) -> tuple[list[str], int]:
    if not path.is_file():
        return [], offset
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            f.seek(offset)
            data = f.read()
            new_offset = f.tell()
    except OSError:
        return [], offset
    return data.splitlines(), new_offset


def dump_threads(pid: int, game_dir: Path, tag: str = "hang") -> None:
    """超时/疑似卡死时先抓线程栈再杀进程（诊断世界生成卡死/死锁）。"""
    out = game_dir / f"{tag}-threads.txt"
    jcmd = Path(sys.executable).with_name("jcmd.exe")  # 不可用时的兜底，见下
    candidates = ["jcmd", str(jcmd)]
    for name in candidates:
        try:
            with out.open("w", encoding="utf-8", errors="replace") as f:
                subprocess.run([name, str(pid), "Thread.print"], stdout=f,
                               stderr=subprocess.STDOUT, timeout=60)
            if out.is_file() and out.stat().st_size > 1000:
                log(f"[launch26] 线程栈已保存: {out}")
                return
        except (OSError, subprocess.TimeoutExpired):
            continue
    log("[launch26] 线程栈抓取失败（jcmd 不可用）")


def kill_tree(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                       capture_output=True, text=True)
    else:
        try:
            os.kill(pid, 15)
        except OSError:
            pass


def launch_and_watch(argv, game_dir: Path, timeout_s: float, watch_title: bool) -> int:
    log_file = game_dir / "logs" / "latest.log"
    console_log = game_dir / "launch-console.log"
    game_dir.mkdir(parents=True, exist_ok=True)
    # latest.log 会被 MC 覆盖写，先清掉，否则哨兵会命中上一轮残留
    if log_file.is_file():
        try:
            log_file.unlink()
        except OSError:
            pass

    console = console_log.open("w", encoding="utf-8", errors="replace")
    t0 = time.time()
    proc = subprocess.Popen(
        argv,
        cwd=str(game_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    console_lines: list[str] = []

    def pump():
        try:
            for line in proc.stdout:            # type: ignore[union-attr]
                console.write(line)
                console.flush()
                console_lines.append(line.rstrip("\n"))
        except Exception:
            pass

    threading.Thread(target=pump, daemon=True).start()

    offset = 0
    markers_seen: dict[str, str] = {}
    verdict_title = False
    exit_code: int | None = None
    deadline = t0 + timeout_s
    last_narrate = 0.0

    while True:
        exit_code = proc.poll()

        lines, offset = tail_new_lines(log_file, offset)
        for line in lines:
            for marker in TITLE_MARKERS:
                if marker in line and marker not in markers_seen:
                    markers_seen[marker] = line
            if TITLE_MARKER_ATLAS in line and TITLE_MARKER_ATLAS not in markers_seen:
                markers_seen[TITLE_MARKER_ATLAS] = line
            if line.strip():
                log(f"[mc] {line}")

        if watch_title and all(m in markers_seen for m in TITLE_MARKERS) \
                and TITLE_MARKER_ATLAS in markers_seen:
            verdict_title = True
            log("")
            log("[launch26] === 标题画面标记全部命中 ===")
            for m in TITLE_MARKERS + [TITLE_MARKER_ATLAS]:
                log(f"[launch26] {m!r} <- {markers_seen[m]}")
            log(f"[launch26] 用时 {time.time()-t0:.1f}s，主动杀进程树 pid={proc.pid}")
            kill_tree(proc.pid)
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                pass
            break

        if exit_code is not None and not watch_title:
            break
        if exit_code is not None and watch_title:
            # 进程自己退了还没到标题画面：把尾巴捞出来
            time.sleep(0.5)
            lines, offset = tail_new_lines(log_file, offset)
            for line in lines:
                if line.strip():
                    log(f"[mc] {line}")
            log(f"[launch26] 进程退出 code={exit_code}，未命中标题画面标记")
            break
        if time.time() > deadline:
            log(f"[launch26] 超过 {timeout_s:.0f}s 仍未到标题画面，先抓线程栈再杀进程树")
            dump_threads(proc.pid, game_dir)
            kill_tree(proc.pid)
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                pass
            exit_code = -9
            break

        now = time.time()
        if now - last_narrate > 15:
            last_narrate = now
            log(f"[launch26] ... {now-t0:.0f}s, 进程{'存活' if exit_code is None else '已退出'}, "
                f"已见标记 {sorted(markers_seen)}")
        time.sleep(0.4)

    console.close()
    log("")
    if verdict_title:
        log("[launch26] RESULT: TITLE_SCREEN_OK")
        return 0
    log(f"[launch26] RESULT: FAILED (exit={exit_code})")
    log(f"[launch26] 控制台日志: {console_log}")
    if console_lines:
        log("[launch26] --- 控制台最后 40 行 ---")
        for line in console_lines[-40:]:
            log("  " + line)
    tail, _ = tail_new_lines(log_file, max(0, log_file.stat().st_size - 8000) if log_file.is_file() else 0)
    if tail:
        log("[launch26] --- latest.log 最后 40 行 ---")
        for line in tail[-40:]:
            log("  " + line)
    return 1


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="MC 26.3 + Fabric 客户端启动器（带任意 mods 目录）")
    p.add_argument("--game-dir", required=True, help="测试用的游戏目录（所有写操作都在这里）")
    p.add_argument("--mods", help="mods 源目录，*.jar 会被复制到 <game-dir>/mods")
    p.add_argument("--dry-run", action="store_true", help="只打印命令，不下载、不启动")
    p.add_argument("--mc-dir", default=str(default_mc_dir()), help=".minecraft 目录（只读）")
    p.add_argument("--fabric-profile", default=str(DEFAULT_FABRIC_PROFILE),
                   help="Fabric loader profile json")
    p.add_argument("--no-fabric", action="store_true", help="只跑 vanilla（调试用）")
    p.add_argument("--java", help="java.exe 路径，默认 <mc-dir>/runtime/java-runtime-epsilon")
    p.add_argument("--natives-dir", help="覆盖 natives 目录（默认 <game-dir>/natives）")
    p.add_argument("--username", default="Tester")
    p.add_argument("--uuid", default="00000000000000000000000000000001")
    p.add_argument("--access-token", default="0")
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--height", type=int, default=720)
    p.add_argument("--xmx", default="4G", help="最大堆（默认 4G；传空字符串则不设）")
    p.add_argument("--xms", default="", help="初始堆（默认不设）")
    p.add_argument("--watch-title", action="store_true",
                   help="盯 logs/latest.log，到标题画面就自动杀进程")
    p.add_argument("--timeout", type=float, default=300.0, help="到标题画面的超时秒数")
    p.add_argument("--extra-jvm-arg", action="append", default=[])
    p.add_argument("--extra-game-arg", action="append", default=[])
    args = p.parse_args(argv)

    args.mc_dir = Path(args.mc_dir).resolve()
    args.game_dir = Path(args.game_dir).resolve()
    args.fabric_profile = None if args.no_fabric else Path(args.fabric_profile).resolve()
    args.java = Path(args.java).resolve() if args.java else default_java(args.mc_dir)
    if not args.java.is_file():
        p.error(f"java.exe 不存在: {args.java}")
    return args


def quote_for_cmd(token: str) -> str:
    if token == "":
        return '""'
    if any(c in token for c in ' \t"'):
        return '"' + token.replace('"', '\\"') + '"'
    return token


def ensure_client_options(game_dir: Path) -> None:
    """新 game-dir 首次启动会在「讲述人/辅助功能」请求界面卡住（无人操作时）。

    这里预写 options.txt，跳过该提示并关闭讲述人，保证自动化启动不会挂住。
    只写缺失项，不覆盖已有用户配置。
    """
    game_dir.mkdir(parents=True, exist_ok=True)
    opt = game_dir / "options.txt"
    defaults = {
        "narrator": "0",
        "onboardAccessibility": "false",
        "skipMultiplayerWarning": "true",
        "tutorialStep": "none",
    }
    lines = []
    if opt.is_file():
        try:
            lines = opt.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            lines = []
    have = {ln.split(":", 1)[0]: i for i, ln in enumerate(lines) if ":" in ln}
    for key, val in defaults.items():
        if key in have:
            lines[have[key]] = f"{key}:{val}"
        else:
            lines.append(f"{key}:{val}")
    opt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"[launch26] options.txt 已确保: {opt}")


def main(argv=None) -> int:
    args = parse_args(argv)
    log(f"[launch26] mc_dir    = {args.mc_dir}")
    log(f"[launch26] game_dir  = {args.game_dir}")
    log(f"[launch26] java      = {args.java}")
    log(f"[launch26] fabric    = {args.fabric_profile or '(vanilla only)'}")
    if not args.dry_run:
        ensure_client_options(args.game_dir)

    if args.mods:
        mods_src = Path(args.mods).resolve()
        if not mods_src.is_dir():
            log(f"[launch26] 警告：--mods 目录不存在: {mods_src}")
        elif args.dry_run:
            log(f"[launch26] (dry-run) 会同步 mods: {[j.name for j in mods_src.glob('*.jar')]}")
        else:
            done = sync_mods(mods_src, args.game_dir)
            log(f"[launch26] mods 同步完成: {done}")

    cmd, info, libs, natives_dir = build_command(args, args.mc_dir)

    log("[launch26] ---- 汇总 ----")
    for k, v in info.items():
        log(f"[launch26]   {k}: {v}")
    if info["downloaded_missing"]:
        log(f"[launch26] 本轮下载/补上的库（{len(info['downloaded_missing'])} 条）:")
        for p in info["downloaded_missing"]:
            log(f"[launch26]   + {p}")

    if args.dry_run:
        log("")
        log("[launch26] ---- 完整命令行（可直接复制到 cmd 跑）----")
        log(" ".join(quote_for_cmd(c) for c in cmd))
        log("")
        log("[launch26] ---- classpath 明细 ----")
        for entry in cmd[cmd.index("-cp") + 1].split(os.pathsep if os.name != "nt" else ";"):
            log("[launch26]   " + entry)
        return 0

    # 把最终命令落盘到 game-dir，方便复现/排错
    cmd_file = args.game_dir / "launch-command.txt"
    cmd_file.parent.mkdir(parents=True, exist_ok=True)
    cmd_file.write_text(" ".join(quote_for_cmd(c) for c in cmd) + "\n", encoding="utf-8")
    log(f"[launch26] 命令行已写入 {cmd_file}")

    log("[launch26] ---- 启动 ----")
    return launch_and_watch(cmd, args.game_dir, args.timeout, args.watch_title)


if __name__ == "__main__":
    sys.exit(main())
