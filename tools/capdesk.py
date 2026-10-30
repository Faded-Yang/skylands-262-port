#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
capdesk.py —— 把目标窗口带到前台，抓**合成桌面**再裁窗口矩形，然后立刻最小化还回去。

## 为什么不用 capwin.py

`PrintWindow` 抓不到 OpenGL 的帧缓冲（返回全黑），26.3 走 SDL/OpenGL，
所以必须 `GetDC(0)` 抓桌面合成结果。这是 notes 里 mc-front2 那次踩坑的结论。

## 用法

    python tools/capdesk.py <out.png> <pid> [--no-minimize]

输出：png + 亮度统计（均值/最大/非黑像素比例）。

⚠ 26.3 的 renderpearl 后端**不能在最小化状态下取帧**：
`SurfaceException: Cannot acquire minimized window`（`GlSurface.acquireNextTexture`）
会直接把游戏带走。所以「抓完立刻最小化」只适用于抓完就结束的场景；
需要**继续跑**时加 `--no-minimize`（抓完保持前台，由调用方自己降 z-order）。
"""
import ctypes
import ctypes.wintypes as wt
import sys
import time

from PIL import Image

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

SRCCOPY = 0x00CC0020
SW_RESTORE = 9
SW_MINIMIZE = 6
SW_SHOW = 5


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wt.DWORD), ("biWidth", ctypes.c_long),
                ("biHeight", ctypes.c_long), ("biPlanes", wt.WORD),
                ("biBitCount", wt.WORD), ("biCompression", wt.DWORD),
                ("biSizeImage", wt.DWORD), ("biXPelsPerMeter", ctypes.c_long),
                ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wt.DWORD),
                ("biClrImportant", wt.DWORD)]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wt.DWORD * 3)]


def find_hwnds(pid):
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


def grab_rect(l, t, w, h):
    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    hbm = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
    gdi32.SelectObject(hdc_mem, hbm)
    ok = gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc_screen, l, t, SRCCOPY)

    bi = BITMAPINFO()
    bi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bi.bmiHeader.biWidth = w
    bi.bmiHeader.biHeight = -h
    bi.bmiHeader.biPlanes = 1
    bi.bmiHeader.biBitCount = 32
    bi.bmiHeader.biCompression = 0
    buf = ctypes.create_string_buffer(w * h * 4)
    lines = gdi32.GetDIBits(hdc_mem, hbm, 0, h, buf, ctypes.byref(bi), 0)
    img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")

    gdi32.DeleteObject(hbm)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(0, hdc_screen)
    return img, bool(ok), lines


def stats(img):
    px = list(img.convert("L").getdata())
    n = len(px)
    mean = sum(px) / n
    mx = max(px)
    nonblack = sum(1 for v in px if v > 8) / n
    return mean, mx, nonblack


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    out = sys.argv[1]
    pid = int(sys.argv[2])
    no_minimize = "--no-minimize" in sys.argv[3:]
    require_fg = "--require-foreground" in sys.argv[3:]

    # ⚠ 不声明 DPI 感知时 GetWindowRect 返回的是**虚拟化坐标**（本机 150% 缩放 ⇒ ÷1.5），
    # 而 BitBlt 用的是物理像素 ⇒ 裁出来的图会整体偏移（已踩过：窗口内容跑到图右上角）。
    try:
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))  # PER_MONITOR_AWARE_V2
    except Exception as e:
        print("SetProcessDpiAwarenessContext 失败（可忽略）:", e)

    ws = find_hwnds(pid)
    if not ws:
        print("pid=%d 没有可见窗口" % pid)
        return 1
    print("窗口:")
    for t, h in ws:
        print("   hwnd=%d title=%r" % (h, t))
    hwnd = ws[0][1]

    rect = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    l, t = rect.left, rect.top
    w, hh = rect.right - rect.left, rect.bottom - rect.top
    print("窗口矩形: (%d,%d) %dx%d" % (l, t, w, hh))

    # 带前台 + 还原，然后等几帧
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.ShowWindow(hwnd, SW_SHOW)
    user32.SetForegroundWindow(hwnd)
    time.sleep(2.0)

    best = None
    best_stat = None
    good = 0
    attempts = 10 if require_fg else 3
    for i in range(attempts):
        if require_fg and user32.GetForegroundWindow() != hwnd:
            print("  第 %d 次：前台不是目标窗口（可能被用户窗口遮住），跳过" % (i + 1))
            time.sleep(0.6)
            continue
        img, ok, lines = grab_rect(l, t, w, hh)
        st = stats(img)
        good += 1
        print("  抓第 %d 帧: BitBlt=%s lines=%s 亮度均值=%.1f 最大=%d 非黑=%.1f%%"
              % (i + 1, ok, lines, st[0], st[1], st[2] * 100))
        if best is None or st[0] > best_stat[0]:
            best, best_stat = img, st
        time.sleep(0.7)
        if require_fg and good >= 3:
            break

    if best is None:
        print("!! 一次都没在目标窗口前台时抓到帧，未保存")
        return 4

    best.save(out)
    print("saved:", out)
    print("最佳帧: 亮度均值=%.1f 最大=%d 非黑像素=%.1f%%" % (best_stat[0], best_stat[1], best_stat[2] * 100))

    # 还回去
    if no_minimize:
        print("保留窗口（--no-minimize，26.3 最小化会 SurfaceException）")
    else:
        user32.ShowWindow(hwnd, SW_MINIMIZE)
        print("已最小化窗口，交还桌面")
    return 0


if __name__ == "__main__":
    sys.exit(main())
