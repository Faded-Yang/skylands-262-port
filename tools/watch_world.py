#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""watch_world.py —— 启动 26.3 + 指定 mods，**用 quickPlay 直接进单人世界**，按日志判定「进世界成功」。

`launch.py` 的哨兵只认「到标题画面」；进世界要另判。本脚本不碰窗口（不抢焦点、不截图），
只读 `<game-dir>/logs/latest.log`，判定完就 `taskkill /F /T` 杀掉自己起的整棵进程树。

## 判定

- **WORLD_OK**：日志出现 `logged in with entity id`（服务端完成玩家加入 ⇒ 世界真的起来了）
  + 之前必须已经出现 `Starting integrated minecraft server`（排除菜单里残留）
- **FAIL_REGISTRY**：`Failed to load registries` / `Unbound values in registry` / `No key`
- **FAIL_CRASH**：`Exception in thread "main"` / `A fatal error has been detected` / crash-report 新增
- **FAIL_TIMEOUT**：超时
- 另外把「数据包错误」「mixin 报错」等前 5 条匹配行回显，便于定位

## 用法

    python tools/watch_world.py --game-dir work/run26/stag1 --mods work/run26/staging-da \\
        --world "sky islands" [--timeout 300] [--tag da4]
"""
import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCH = ROOT / "tools" / "launch26" / "launch.py"

FAIL_PATTERNS = [
    # ⚠ 只放「真的会导致进不了世界」的硬失败。
    # 反例（实测踩过）：`Error loading class: ... (java.lang.ClassNotFoundException: ...)` 是
    # **mixin 插件扫描可选目标时打的 WARN**，正常启动也会有一串；按它判失败会误杀。
    ("registry", "Failed to load registries"),
    ("registry", "Unbound values in registry"),
    ("registry", "Unknown registry key"),
    ("registry", "Failed to parse either"),
    ("registry", "Errors in currently selected datapacks"),
    ("mixin", "Mixin apply failed"),
    ("mixin", "InvalidMixinException"),
    ("crash", "Exception in thread \"main\""),
    ("crash", "A fatal error has been detected"),
    ("crash", "Minecraft has crashed"),
]


def tail(path, n=12):
    try:
        txt = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return txt[-n:]
    except OSError:
        return []


def find_java_pid(game_dir):
    """按命令行里的 game-dir 找**本次**启动的 java 进程（不碰别人的 java）。"""
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='java.exe'\" | "
          "Where-Object { $_.CommandLine -like '*%s*' } | "
          "Select-Object -ExpandProperty ProcessId" % str(game_dir).replace("'", "''"))
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return None
    for line in out.split():
        if line.strip().isdigit():
            return int(line.strip())
    return None


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--game-dir", required=True)
    ap.add_argument("--mods", required=True)
    ap.add_argument("--world", default="sky islands")
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--tag", default="world")
    ap.add_argument("--click-if-stuck", default="0.812,0.658",
                    help="卡在「实验性设置」确认框时点的客户区相对坐标；传空串关闭")
    a = ap.parse_args()

    game = Path(a.game_dir).resolve()
    log = game / "logs" / "latest.log"
    if log.exists():
        try:
            log.unlink()
        except OSError:
            # 上一轮被 taskkill 的进程有时还持有句柄；launch.py 启动时自己会删，别在这里硬失败
            print("[world] 旧的 latest.log 删不掉（被占用），交给 launch.py 处理", flush=True)
    cmd = [sys.executable, str(LAUNCH), "--game-dir", str(game), "--mods", str(a.mods),
           "--timeout", str(int(a.timeout)),
           "--extra-game-arg=--quickPlaySingleplayer", "--extra-game-arg=" + a.world]
    print("[world] launch: %s" % " ".join(cmd[2:]), flush=True)
    proc = subprocess.Popen(cmd, cwd=str(ROOT),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    result = "FAIL_TIMEOUT"
    seen_fail = []
    joined = False
    server_started = False
    adv_at = None            # 第一次见到 "Loaded N advancements" 的时刻（它之后就是世界载入）
    clicks = 0
    while time.time() - t0 < a.timeout:
        time.sleep(2)
        if proc.poll() is not None and not joined:
            # 启动器自己退了（崩了/超时）
            time.sleep(1)
            break
        try:
            txt = log.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "Starting integrated minecraft server" in txt:
            server_started = True
        if adv_at is None and "Loaded " in txt and " advancements" in txt:
            adv_at = time.time()
        # ⚠ 26.3 用自定义世界预设建的存档会被标成「实验性设置」，进世界前弹确认框，不点就一直卡住
        #    （实测：日志停在 "Loaded 1920 advancements" 不动）。这里在 25s/60s 各点一次
        #    「我知道我在做什么！」（客户区相对坐标默认 0.807,0.645）。
        if (adv_at and not server_started and a.click_if_stuck and clicks < 6
                and time.time() - adv_at > (25 + 12 * clicks)):
            try:
                rx, ry = [float(x) for x in a.click_if_stuck.split(",")]
            except Exception:
                rx = ry = None
            if rx is not None:
                game_pid = find_java_pid(game)
                if game_pid:
                    r = subprocess.run([sys.executable, str(ROOT / "tools" / "mc_click.py"),
                                        str(game_pid), str(rx), str(ry)],
                                       capture_output=True, text=True, timeout=30)
                    print("[world] 点击实验性设置确认框: %s" % (r.stdout or r.stderr).strip(), flush=True)
            clicks += 1
        for kind, pat in FAIL_PATTERNS:
            if pat in txt and (kind, pat) not in seen_fail:
                seen_fail.append((kind, pat))
        if server_started and "logged in with entity id" in txt:
            joined = True
            result = "WORLD_OK"
            break
        if seen_fail:
            kind = seen_fail[0][0]
            result = {"registry": "FAIL_REGISTRY", "mixin": "FAIL_MIXIN"}.get(kind, "FAIL_CRASH")
            time.sleep(2)
            break

    dt = time.time() - t0
    print("[world] result=%s in %.1fs (server_started=%s joined=%s)" % (result, dt, server_started, joined), flush=True)
    if result == "WORLD_OK":
        for line in tail(log, 6):
            print("  [mc] " + line, flush=True)
    else:
        for kind, pat in seen_fail[:8]:
            print("  [hit:%s] %s" % (kind, pat), flush=True)
        for line in tail(log, 25):
            print("  [mc] " + line, flush=True)
    # 杀掉自己起的整棵进程树（launch.py -> java）；只杀本次 Popen 的 pid
    try:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                       capture_output=True, text=True, timeout=30)
    except Exception as e:
        print("[world] taskkill 失败: %r" % (e,), flush=True)
    try:
        proc.wait(timeout=10)
    except Exception:
        pass
    print("[world] RESULT: %s" % result, flush=True)
    return 0 if result == "WORLD_OK" else 1


if __name__ == "__main__":
    sys.exit(main())

