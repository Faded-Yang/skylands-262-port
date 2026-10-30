#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""focuswin.py —— 把目标窗口抢到前台，并（可选）给它发键盘输入。

为什么不用 `mcp__windows__*`：那套工具有 USER_CONTROL 租约，用户在用电脑时直接拒绝
（`{"code":"USER_CONTROL","state":"user"}`）。本脚本是纯 ctypes + user32，不申请任何租约，
但**抢前台**要靠 `AttachThreadInput` —— 单独 `SetForegroundWindow` 在 Windows 上经常被忽略
（本机实测：capdesk.py 连续 10 次都失败）。

用法：
    python tools/focuswin.py --pid 1234                     # 只抢前台
    python tools/focuswin.py --pid 1234 --text "/gamemode spectator" --enter
    python tools/focuswin.py --pid 1234 --keys "t" --text "/tp @s 0 300 0 0 40" --enter
    python tools/focuswin.py --pid 1234 --keys "e"          # 单个虚拟键

`--keys` 里支持 "t"、"e"、"esc"、"f2"、"enter"、"space"、"shift"、"ctrl" 等单个键名。
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import sys
import time

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

SW_RESTORE = 9
SW_SHOW = 5

VK = {
    "enter": 0x0D, "return": 0x0D, "esc": 0x1B, "escape": 0x1B,
    "space": 0x20, "tab": 0x09, "backspace": 0x08,
    "shift": 0x10, "ctrl": 0x11, "control": 0x11, "alt": 0x12,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f5": 0x74,
    # ⚠ UNICODE 注入的 "/" 在本机（中文布局/输入法）会变成别的字符（实测变 "a"），
    # 命令前缀必须用**虚拟键**打：VK_OEM_2 = 0xBF。
    "slash": 0xBF, "oem2": 0xBF,
}
for ch in "abcdefghijklmnopqrstuvwxyz":
    VK[ch] = ord(ch.upper())
for d in "0123456789":
    VK[d] = ord(d)

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ctypes.POINTER(wt.ULONG))]


class _INPUTunion(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("padding", ctypes.c_byte * 32)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wt.DWORD), ("u", _INPUTunion)]


def find_hwnd(pid):
    out = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cb(hwnd, _):
        p = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid and user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1)
            out.append((buf.value, hwnd))
        return True

    user32.EnumWindows(cb, 0)
    out.sort(key=lambda t: -len(t[0]))
    return out


def force_foreground(hwnd):
    """AttachThreadInput 抢前台（比裸 SetForegroundWindow 可靠得多）。"""
    fg = user32.GetForegroundWindow()
    if fg == hwnd:
        return True
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.ShowWindow(hwnd, SW_SHOW)
    # ALT 抖动：让当前前台进程"自愿"交出前台权
    user32.keybd_event(0x12, 0, 0, 0)
    user32.keybd_event(0x12, 0, KEYEVENTF_KEYUP, 0)
    cur_tid = kernel32.GetCurrentThreadId()
    fg_tid = user32.GetWindowThreadProcessId(fg, None) if fg else 0
    attached = False
    if fg_tid and fg_tid != cur_tid:
        attached = bool(user32.AttachThreadInput(cur_tid, fg_tid, True))
    user32.BringWindowToTop(hwnd)
    user32.SetActiveWindow(hwnd)
    ok = user32.SetForegroundWindow(hwnd)
    if attached:
        user32.AttachThreadInput(cur_tid, fg_tid, False)
    time.sleep(0.4)
    return user32.GetForegroundWindow() == hwnd


def send_vk(vk, up=False):
    inp = INPUT(type=1)
    inp.u.ki = KEYBDINPUT(vk, 0, KEYEVENTF_KEYUP if up else 0, 0, None)
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def tap_vk(vk, hold_ms=40):
    send_vk(vk, False)
    time.sleep(hold_ms / 1000.0)
    send_vk(vk, True)
    time.sleep(0.06)


def type_text(text):
    """逐字符走 SendInput 的 UNICODE 通道（GLFW/SDL 能收到）。"""
    for ch in text:
        vk = 0
        scan = ord(ch)
        down = INPUT(type=1)
        down.u.ki = KEYBDINPUT(vk, scan, KEYEVENTF_UNICODE, 0, None)
        up = INPUT(type=1)
        up.u.ki = KEYBDINPUT(vk, scan, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, None)
        user32.SendInput(1, ctypes.byref(down), ctypes.sizeof(INPUT))
        time.sleep(0.012)
        user32.SendInput(1, ctypes.byref(up), ctypes.sizeof(INPUT))
        time.sleep(0.012)


def click_at(x, y, button="left", double=False):
    """屏幕物理像素坐标点击（先 SetCursorPos 再 mouse_event）。"""
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_RIGHTDOWN = 0x0008
    MOUSEEVENTF_RIGHTUP = 0x0010
    down = MOUSEEVENTF_RIGHTDOWN if button == "right" else MOUSEEVENTF_LEFTDOWN
    up = MOUSEEVENTF_RIGHTUP if button == "right" else MOUSEEVENTF_LEFTUP
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.15)
    for _ in range(2 if double else 1):
        user32.mouse_event(down, 0, 0, 0, 0)
        time.sleep(0.05)
        user32.mouse_event(up, 0, 0, 0, 0)
        time.sleep(0.12)
    print("clicked (%d,%d) %s%s" % (x, y, button, " x2" if double else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, required=True)
    ap.add_argument("--keys", action="append", default=[], help="先按的虚拟键（可多次）")
    ap.add_argument("--key-delay", type=float, default=0.6)
    ap.add_argument("--text", help="要输入的文本")
    ap.add_argument("--enter", action="store_true", help="文本后补一个回车")
    ap.add_argument("--no-focus", action="store_true")
    ap.add_argument("--click", help="屏幕坐标 x,y（在 --keys/--text 之后点）")
    ap.add_argument("--double", action="store_true")
    ap.add_argument("--button", default="left")
    args = ap.parse_args()

    try:
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        pass

    ws = find_hwnd(args.pid)
    if not ws:
        print("pid=%d 没有可见窗口" % args.pid)
        return 1
    print("窗口:", [(t, h) for t, h in ws])
    hwnd = ws[0][1]

    if not args.no_focus:
        ok = force_foreground(hwnd)
        print("抢前台:", "成功" if ok else "失败（GetForegroundWindow 不是目标窗口）")
        if not ok:
            return 2
        time.sleep(0.5)

    for name in args.keys:
        vk = VK.get(name.lower())
        if vk is None:
            print("!! 不认识的键名:", name)
            return 3
        tap_vk(vk)
        print("按下", name)
        time.sleep(args.key_delay)

    if args.text is not None:
        type_text(args.text)
        print("已输入 %d 个字符" % len(args.text))
        time.sleep(0.2)

    if args.enter:
        tap_vk(VK["enter"])
        print("回车")

    if args.click:
        cx, cy = [int(v) for v in args.click.split(",")]
        time.sleep(0.2)
        click_at(cx, cy, args.button, args.double)
    return 0


if __name__ == "__main__":
    sys.exit(main())
