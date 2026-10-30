#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_verify_world.py —— 启动 26.3 → 进世界 → 在游戏内抓图 → 用 /give 验证方块注册。

## 为什么要单独一个脚本

`launch.py` 只负责「启动到标题画面」的哨兵；进世界要 `--quickPlaySingleplayer`。
抓图必须**把窗口带到前台再抓合成桌面**（`PrintWindow` 抓不到 OpenGL）。

## 26.3 的两个坑（本轮实测）

1. **绝对不要最小化游戏窗口**：renderpearl 后端在最小化时取帧会抛
   `SurfaceException: Cannot acquire minimized window`（`GlSurface.acquireNextTexture`），
   然后游戏直接退出（无 crash-report，launch.py 报 `exit=4294967295`）。
   ⇒ `capdesk.py --no-minimize`，之后由本脚本把窗口**降到 z-order 底部**并还原用户的前台窗口。
2. **失去焦点会暂停单人游戏**（不论 `pauseOnLostFocus`），暂停时截图会拍到「游戏菜单」。
   ⇒ 靠日志里的 `Saving and pausing game...` 计数判断是否暂停，暂停了就按 `Esc` 恢复；
      并且只在「即将进世界」（`Starting integrated minecraft server`）时把窗口带到前台，
      尽可能缩短占用用户桌面的时间。

## 流程

1. 准备 game-dir：复制存档 / options.txt（`pauseOnLostFocus:false`）
2. 后台起 `tools/launch26/launch.py ... --quickPlaySingleplayer <world>`
3. 日志 `Starting integrated minecraft server` → 窗口带到前台（避免进世界即暂停）
4. `logged in with entity id` → 恢复暂停 → 发 `/time set day`、`/give @s <item>` → 抓图 1
5. 降到 z-order 底部，等 `--hold` 秒（默认 70）
6. 再带到前台 → 必要时 Esc 恢复 → 抓图 2（跨越 60 秒线的存活证据）
7. 降下窗口 → 汇总日志/进程/crash-report → 杀进程，写 JSON

## 用法

    python tools/run_verify_world.py --game-dir work/run26/probe44 \
        --mods work/run26/mods-crashfix --world 新的世界 \
        --save-src work/run26/probe40/saves/新的世界 \
        --prefix notes/probe44 --hold 70 [--no-give]
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

SW_RESTORE = 9
SW_SHOW = 5
HWND_BOTTOM = 1
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong


# ---------------------------------------------------------------- 窗口
def visible_windows():
    out = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cb(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        n = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, n + 1)
        pid = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        out.append({"hwnd": hwnd, "title": buf.value, "pid": pid.value})
        return True

    user32.EnumWindows(cb, 0)
    return out


def mc_windows():
    return [w for w in visible_windows() if "Minecraft" in w["title"]]


def bring_to_front(hwnd):
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.ShowWindow(hwnd, SW_SHOW)
    if user32.GetForegroundWindow() == hwnd:
        return True
    fg = user32.GetForegroundWindow()
    tid_fg = user32.GetWindowThreadProcessId(fg, None) if fg else 0
    tid_me = kernel32.GetCurrentThreadId()
    ok = False
    if tid_fg:
        user32.AttachThreadInput(tid_me, tid_fg, True)
    try:
        ok = bool(user32.SetForegroundWindow(hwnd))
    finally:
        if tid_fg:
            user32.AttachThreadInput(tid_me, tid_fg, False)
    time.sleep(0.4)
    return user32.GetForegroundWindow() == hwnd or ok


def foreground_is(hwnd):
    return user32.GetForegroundWindow() == hwnd


def lower_window(hwnd, fg0):
    """把游戏窗口压到 z-order 底部并把前台还给用户原来的窗口（**不最小化**）。"""
    user32.SetWindowPos(hwnd, HWND_BOTTOM, 0, 0, 0, 0,
                        SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)
    if fg0:
        user32.SetForegroundWindow(fg0)


# ---------------------------------------------------------------- 键盘
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wt.LONG), ("dy", wt.LONG), ("mouseData", wt.DWORD),
                ("dwFlags", wt.DWORD), ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wt.DWORD), ("wParamL", wt.WORD), ("wParamH", wt.WORD)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wt.DWORD), ("u", _INPUTUNION)]


KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004


def _send(inp):
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def send_vk(vk):
    for flags in (0, KEYEVENTF_KEYUP):
        i = INPUT()
        i.type = 1
        i.ki = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=flags, time=0, dwExtraInfo=0)
        _send(i)
        time.sleep(0.02)


def send_unicode(text):
    for ch in text:
        code = ord(ch)
        if code > 0xFFFF:
            continue
        for flags in (KEYEVENTF_UNICODE, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP):
            i = INPUT()
            i.type = 1
            i.ki = KEYBDINPUT(wVk=0, wScan=code, dwFlags=flags, time=0, dwExtraInfo=0)
            _send(i)
            time.sleep(0.008)


# ---------------------------------------------------------------- 杂
def read_text(p):
    try:
        return Path(p).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def log(msg):
    print("[verify] " + msg, flush=True)


def prepare(game_dir: Path, save_src: Path, world: str):
    game_dir.mkdir(parents=True, exist_ok=True)
    dst = game_dir / "saves" / world
    if dst.exists():
        log("存档已存在，沿用: %s" % dst)
    else:
        if not save_src.is_dir():
            raise SystemExit("存档源不存在: %s" % save_src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        log("复制存档 %s -> %s ..." % (save_src.name, dst))
        t = time.time()
        shutil.copytree(save_src, dst)
        log("  复制完成 %.1fs" % (time.time() - t))
    src = ROOT / "work" / "run26" / "probe42" / "options.txt"
    opt = game_dir / "options.txt"
    lines = []
    if opt.is_file():
        lines = opt.read_text(encoding="utf-8", errors="replace").splitlines()
    elif src.is_file():
        lines = src.read_text(encoding="utf-8", errors="replace").splitlines()
    keys = {"pauseOnLostFocus": "false", "fullscreen": "false", "maxFps": "60"}
    seen, out = set(), []
    for ln in lines:
        k = ln.split(":", 1)[0]
        if k in keys:
            out.append("%s:%s" % (k, keys[k]))
            seen.add(k)
        else:
            out.append(ln)
    for k, v in keys.items():
        if k not in seen:
            out.append("%s:%s" % (k, v))
    opt.write_text("\n".join(out) + "\n", encoding="utf-8")
    log("options.txt 已强制: %s" % json.dumps(keys))


def crash_reports_since(game_dir: Path, t0):
    d = game_dir / "crash-reports"
    if not d.is_dir():
        return []
    return sorted(p.name for p in d.iterdir() if p.stat().st_mtime >= t0)


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game-dir", required=True)
    ap.add_argument("--mods", required=True)
    ap.add_argument("--world", default="新的世界")
    ap.add_argument("--save-src", default="work/run26/probe40/saves/新的世界")
    ap.add_argument("--prefix", default="notes/probe44")
    ap.add_argument("--hold", type=float, default=70.0, help="进世界后再撑多少秒（>=60）")
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--give", default="simulated:spring")
    ap.add_argument("--no-give", action="store_true")
    ap.add_argument("--prepare-only", action="store_true")
    a = ap.parse_args()

    def abspath(s):
        p = Path(s)
        return p if p.is_absolute() else (ROOT / p)

    game_dir, mods = abspath(a.game_dir), abspath(a.mods)
    save_src = abspath(a.save_src)
    prefix = abspath(a.prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)

    scenario = {"game_dir": str(game_dir), "mods": str(mods), "world": a.world,
                "hold": a.hold, "shots": [], "events": [], "focus_seconds": 0.0}

    prepare(game_dir, save_src, a.world)
    if a.prepare_only:
        print(json.dumps(scenario, ensure_ascii=False, indent=2))
        return 0

    log_path = game_dir / "logs" / "latest.log"
    log_path.unlink(missing_ok=True)

    pre_hwnds = {w["hwnd"] for w in mc_windows()}
    fg0 = user32.GetForegroundWindow()
    log("启动前前台窗口 hwnd=%s（收尾时还给它）" % fg0)

    t_launch = time.time()
    cmd = [sys.executable, str(ROOT / "tools" / "launch26" / "launch.py"),
           "--game-dir", str(game_dir), "--mods", str(mods),
           "--timeout", str(a.timeout),
           "--extra-game-arg=--quickPlaySingleplayer", "--extra-game-arg=" + a.world]
    log("启动: launch.py --game-dir %s --mods %s --quickPlaySingleplayer %s"
        % (game_dir.name, mods.name, a.world))
    console = open(game_dir / "verify-launch-console.log", "w", encoding="utf-8", errors="replace")
    proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=console, stderr=subprocess.STDOUT,
                            creationflags=subprocess.CREATE_NO_WINDOW)

    state = {"hwnd": None, "pid": None, "joined": None, "pause_seen": 0,
             "focused_until_join": False, "shot1": False, "shot2": False}

    def find_game():
        for w in mc_windows():
            if w["hwnd"] not in pre_hwnds:
                state["hwnd"], state["pid"] = w["hwnd"], w["pid"]
                log("游戏窗口 hwnd=%s pid=%s title=%r"
                    % (state["hwnd"], state["pid"], w["title"]))
                return True
        return False

    def pause_count():
        return read_text(log_path).count("Saving and pausing game")

    def maybe_resume(tag):
        """日志里出现新的 `Saving and pausing game` ⇒ 大概率暂停了 ⇒ Esc 一下。"""
        n = pause_count()
        if n > state["pause_seen"]:
            if foreground_is(state["hwnd"]):
                log("[%s] 检出暂停（%d 次），发 Esc 恢复" % (tag, n))
                send_vk(0x1B)
                time.sleep(1.0)
                scenario["events"].append({"name": "resume", "tag": tag})
            state["pause_seen"] = n
            time.sleep(0.3)

    def shot(tag, tries=3):
        out = str(prefix.with_name(prefix.name + "-" + tag + ".png"))
        r = None
        txt = ""
        for attempt in range(1, tries + 1):
            # --require-foreground：只在前台确实是这个窗口时才抓帧，
            # 否则会抓到用户挡在上面的窗口（上一轮就抓到过 DSH 聊天窗）
            r = subprocess.run([sys.executable, str(ROOT / "tools" / "capdesk.py"),
                                out, str(state["pid"] or 0), "--no-minimize",
                                "--require-foreground"],
                               cwd=str(ROOT), capture_output=True, text=True)
            txt = (r.stdout or "") + (r.stderr or "")
            if r.returncode == 0:
                break
            log("  抓图失败 rc=%s（%d/%d），2s 后重试" % (r.returncode, attempt, tries))
            time.sleep(2.0)
        log("抓图 %s rc=%s" % (Path(out).name, r.returncode if r else "?"))
        for ln in txt.strip().splitlines():
            if "saved" in ln or "亮度" in ln or "窗口矩形" in ln or "前台" in ln:
                log("   " + ln)
        scenario["shots"].append({"tag": tag, "path": out, "rc": r.returncode,
                                  "capdesk": txt})
        return out

    def type_command(text):
        """在聊天框里输入一条命令（每一步都校验前台，前台变了就停手）。"""
        if not foreground_is(state["hwnd"]) and not bring_to_front(state["hwnd"]):
            log("!! 前台不是 MC，跳过命令 %r（不乱敲键盘）" % text)
            return False
        send_vk(0x54)                      # t → 打开聊天
        time.sleep(0.5)
        if not foreground_is(state["hwnd"]):
            log("!! 打开聊天后前台变了，停止输入")
            return False
        send_unicode(text)
        time.sleep(0.25)
        if not foreground_is(state["hwnd"]):
            log("!! 输入时前台变了，不按回车")
            return False
        send_vk(0x0D)                      # Enter
        time.sleep(0.9)
        scenario["events"].append({"name": "command", "cmd": text})
        log("已发送命令: %s" % text)
        return True

    deadline = t_launch + a.timeout
    t_focus0 = None
    while time.time() < deadline:
        time.sleep(0.8)
        if state["hwnd"] is None:
            find_game()
        text = read_text(log_path)

        # 进世界前把窗口带到前台：避免「进世界那一刻没焦点 ⇒ 立刻暂停」
        if state["hwnd"] and not state["focused_until_join"] and (
                "Starting integrated minecraft server" in text or "Sound engine started" in text):
            log("进世界前把 MC 带到前台（减少暂停概率）")
            bring_to_front(state["hwnd"])
            state["focused_until_join"] = True
            t_focus0 = time.time()
            scenario["events"].append({"name": "focus_before_join"})

        if state["joined"] is None and "logged in with entity id" in text:
            state["joined"] = time.time()
            log("进世界了（%.1fs）" % (state["joined"] - t_launch))
            scenario["events"].append({"name": "joined",
                                       "t": round(state["joined"] - t_launch, 1)})
            time.sleep(1.5)
            find_game()
            bring_to_front(state["hwnd"])
            maybe_resume("join")
            if not a.no_give:
                type_command("/time set day")
                type_command("/give @s " + a.give + " 3")
            shot("world-1")
            state["shot1"] = True
            lower_window(state["hwnd"], fg0)
            if t_focus0:
                scenario["focus_seconds"] += round(time.time() - t_focus0, 1)
            log("窗口已降到 z-order 底部（不最小化），等 %ss" % a.hold)

        elif state["joined"] is not None and not state["shot2"]:
            el = time.time() - state["joined"]
            if el >= a.hold:
                log("已停留 %.1fs，第二次取证" % el)
                if not bring_to_front(state["hwnd"]):
                    log("!! 无法把 MC 拉到前台")
                else:
                    maybe_resume("hold")
                    time.sleep(1.0)
                shot("world-2")
                scenario["events"].append({"name": "held", "t": round(el, 1)})
                state["shot2"] = True
                lower_window(state["hwnd"], fg0)
                break

        if "Unreported exception" in text or "Stopping server" in text:
            log("!! 日志出现崩溃/停止标记，提前结束")
            break
        if proc.poll() is not None:
            log("launch.py 已退出 rc=%s" % proc.returncode)
            break

    # 收尾
    alive = proc.poll() is None
    text = read_text(log_path)
    time.sleep(2.0)
    text2 = read_text(log_path)
    grew = len(text2) > len(text)
    reports = crash_reports_since(game_dir, t_launch)
    joined = state["joined"] is not None
    scenario.update({
        "launch_seconds": round(state["joined"] - t_launch, 1) if joined else None,
        "held_seconds": round(time.time() - state["joined"], 1) if joined else 0,
        "alive_at_end": alive,
        "log_growing": grew,
        "crash_reports": reports,
        "unreported_exception": "Unreported exception" in text2,
        "surface_exception": "Cannot acquire minimized window" in text2,
        "commands_logged": [ln for ln in text2.splitlines()
                            if "issued server command" in ln or "server command" in ln],
        "crashfix_log_lines": [ln for ln in text2.splitlines() if "crashfix" in ln],
        "log_tail": text2.splitlines()[-20:],
    })

    if state["hwnd"]:
        lower_window(state["hwnd"], fg0)
    if proc.poll() is None:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                       capture_output=True, text=True)
    out_json = str(prefix.with_name(prefix.name + "-verify.json"))
    Path(out_json).write_text(json.dumps(scenario, ensure_ascii=False, indent=2), encoding="utf-8")
    log("报告: %s" % out_json)
    print(json.dumps({k: v for k, v in scenario.items()
                      if k in ("launch_seconds", "held_seconds", "alive_at_end", "log_growing",
                               "crash_reports", "unreported_exception", "surface_exception",
                               "commands_logged", "crashfix_log_lines", "focus_seconds")},
                     ensure_ascii=False, indent=2))
    ok = joined and scenario["held_seconds"] >= 60 and not scenario["unreported_exception"]
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
