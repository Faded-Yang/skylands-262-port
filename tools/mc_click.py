#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mc_click.py —— 在「指定 pid 的 Minecraft 窗口」的**客户区相对坐标**上点一下。

## 为什么需要

`--quickPlaySingleplayer` 进世界时，如果存档带实验性设置，26.3 会先弹一个确认框
（「不支持使用实验性设置的世界」→ 三个按钮：创建备份并加载 / 我知道我在做什么！ / 取消），
**不点就一直卡在标题画面**（日志也不再动）。自动验收必须能点掉它。

用法：
    python tools/mc_click.py <pid> <relX 0~1> <relY 0~1>

只点一次、点前会把窗口提到前台并校验 `GetForegroundWindow`；拿不到前台就不点（返回 2）。
"""
import ctypes
import ctypes.wintypes as wt
import sys
import time

user32 = ctypes.WinDLL("user32", use_last_error=True)
SW_RESTORE = 9
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004


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


def send_key(pid, vk=0x0D):
    """向窗口投递一次按键（默认 Enter）。确认框的默认焦点在第 1 个按钮上，回车即可。
    26.3 是 SDL3，鼠标消息不认，但键盘消息一般能通。"""
    hwnd = find_hwnd(pid)
    if not hwnd:
        print("no window for pid %d" % pid)
        return 2
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.3)
    if user32.GetForegroundWindow() != hwnd:
        print("窗口没拿到前台，放弃按键")
        return 2
    user32.PostMessageW(hwnd, 0x0100, vk, 0)        # WM_KEYDOWN
    time.sleep(0.06)
    user32.PostMessageW(hwnd, 0x0101, vk, 0)        # WM_KEYUP
    user32.keybd_event(vk, 0, 0, 0)
    time.sleep(0.06)
    user32.keybd_event(vk, 0, 2, 0)
    print("sent key vk=%d to hwnd=%s" % (vk, hwnd))
    return 0


def main():
    if sys.argv[1] == "--key":
        return send_key(int(sys.argv[2]), int(sys.argv[3], 0) if len(sys.argv) > 3 else 0x0D)
    pid = int(sys.argv[1])
    rx, ry = float(sys.argv[2]), float(sys.argv[3])
    hwnd = find_hwnd(pid)
    if not hwnd:
        print("no window for pid %d" % pid)
        return 2
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.3)
    rect = wt.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    w, h = rect.right - rect.left, rect.bottom - rect.top
    pt = wt.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    x = pt.x + int(w * rx)
    y = pt.y + int(h * ry)
    fg = user32.GetForegroundWindow()
    print("hwnd=%s client=%dx%d screen=(%d,%d) fg=%s ok=%s" % (hwnd, w, h, x, y, fg, fg == hwnd))
    if fg != hwnd:
        print("窗口没拿到前台，放弃点击（避免点到用户桌面）")
        return 2
    cx, cy = int(w * rx), int(h * ry)
    # ① 先把光标移到目标（SetCursorPos 是**屏幕**坐标）
    user32.SetCursorPos(x, y)
    time.sleep(0.25)
    # ② 再向窗口**直接投递**鼠标消息：MC 的按钮命中测试用的是它自己收到的
    #    WM_MOUSEMOVE 里的客户区坐标；只挪光标不发消息时，它仍按上一次的位置判定，
    #    点了等于没点（本轮实测：只 SetCursorPos + mouse_event 时对话框纹丝不动）
    lparam = (cy << 16) | (cx & 0xFFFF)
    user32.PostMessageW(hwnd, 0x0200, 0, lparam)      # WM_MOUSEMOVE
    time.sleep(0.15)
    user32.PostMessageW(hwnd, 0x0201, 1, lparam)      # WM_LBUTTONDOWN
    time.sleep(0.08)
    user32.PostMessageW(hwnd, 0x0202, 0, lparam)      # WM_LBUTTONUP
    time.sleep(0.1)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    print("clicked client=(%d,%d) screen=(%d,%d)" % (cx, cy, x, y))
    return 0


if __name__ == "__main__":
    sys.exit(main())
