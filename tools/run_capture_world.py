# -*- coding: utf-8 -*-
"""启动游戏 → 在标题画面阶段把窗口拉到前台（避免最小化导致的 InputConstants 崩溃）→
等世界加载完（日志 'logged in'）→ 抓合成桌面 → 打印亮度。

用法：python tools/run_capture_world.py <game-dir> <mods-dir> <world-id> <out.png>
"""
import ctypes
import ctypes.wintypes as wt
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = Path(sys.argv[1]).resolve()
MODS = Path(sys.argv[2]).resolve()
WORLD = sys.argv[3]
OUT = sys.argv[4]
LOG = GAME / "logs" / "latest.log"

user32 = ctypes.WinDLL("user32", use_last_error=True)
SW_RESTORE = 9


def find_hwnd(pid):
    found = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cb(hwnd, _):
        p = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid and user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1)
            if "Minecraft" in buf.value:
                found.append(hwnd)
        return True

    user32.EnumWindows(cb, 0)
    return found[0] if found else None


def game_pid():
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process -Filter \"Name='java.exe'\" | "
         "Where-Object { $_.CommandLine -like '*%s*' } | "
         "Select-Object -ExpandProperty ProcessId" % GAME.name],
        capture_output=True, text=True).stdout
    for line in out.split():
        if line.strip().isdigit():
            return int(line.strip())
    return None


launcher = subprocess.Popen(
    [sys.executable, str(ROOT / "tools" / "launch26" / "launch.py"),
     "--game-dir", str(GAME), "--mods", str(MODS), "--timeout", "260",
     "--extra-game-arg=--quickPlaySingleplayer", "--extra-game-arg=" + WORLD],
    cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("launcher pid", launcher.pid, flush=True)

t0 = time.time()
brought = False
joined = False
while time.time() - t0 < 200:
    time.sleep(2)
    text = ""
    try:
        text = LOG.read_text(encoding="utf-8", errors="replace")
    except OSError:
        pass
    if not brought and "Sound engine started" in text:
        pid = game_pid()
        if pid:
            hwnd = find_hwnd(pid)
            if hwnd:
                user32.ShowWindow(hwnd, SW_RESTORE)
                user32.SetForegroundWindow(hwnd)
                brought = True
                print("brought window to front at %.1fs" % (time.time() - t0), flush=True)
    if "logged in with entity id" in text:
        joined = True
        print("world joined at %.1fs" % (time.time() - t0), flush=True)
        break
    if "Stopping server" in text:
        print("server stopped (crash) at %.1fs" % (time.time() - t0), flush=True)
        break

if joined:
    time.sleep(0.3)
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "capdesk.py"), OUT, str(game_pid() or 0)],
                       cwd=str(ROOT), capture_output=True, text=True)
    print(r.stdout[-2000:], flush=True)
    print(r.stderr[-1000:], flush=True)
else:
    print("NOT JOINED", flush=True)

try:
    launcher.wait(timeout=5)
except Exception:
    pass
