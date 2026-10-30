#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
capwin.py —— 用 PrintWindow + GDI 抓任意窗口的像素，不需要接管桌面（不触发 USER_CONTROL）。

为什么不用 mcp__windows__Screenshot：那个走桌面接管，用户正在用机器时会被拒。
为什么不用 Add-Type + System.Drawing：本机 PowerShell 找不到 System.Drawing.Common，
Bitmap/Graphics 类型全部转发失败。

用法：  python tools/capwin.py <输出png> [pid]
"""
import ctypes
import ctypes.wintypes as wt
import sys

try:
    from PIL import Image
except ImportError:
    print("需要 Pillow", file=sys.stderr)
    sys.exit(2)

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

PW_RENDERFULLCONTENT = 0x00000002
SRCCOPY = 0x00CC0020


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


def find_hwnd(pid):
    """按 pid 找到第一个可见顶层窗口（优先有标题的）。"""
    found = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cb(hwnd, _):
        p = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid and user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1)
            found.append((buf.value, hwnd))
            return True
        return True

    user32.EnumWindows(cb, 0)
    found.sort(key=lambda t: -len(t[0]))      # 标题最长的多半是主窗口
    return found


def grab(hwnd, out_path):
    r = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(r)):
        return "GetWindowRect 失败"
    w, h = r.right - r.left, r.bottom - r.top
    if w <= 0 or h <= 0:
        return "窗口尺寸无效 %dx%d" % (w, h)

    hdc_screen = user32.GetDC(0)
    hdc_win = gdi32.CreateCompatibleDC(hdc_screen)
    hbm = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
    gdi32.SelectObject(hdc_win, hbm)

    ok = user32.PrintWindow(hwnd, hdc_win, PW_RENDERFULLCONTENT)
    if not ok:
        gdi32.BitBlt(hdc_win, 0, 0, w, h, user32.GetWindowDC(hwnd), 0, 0, SRCCOPY)

    bi = BITMAPINFO()
    bi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bi.bmiHeader.biWidth = w
    bi.bmiHeader.biHeight = -h            # 负数 = 自上而下
    bi.bmiHeader.biPlanes = 1
    bi.bmiHeader.biBitCount = 32
    bi.bmiHeader.biCompression = 0        # BI_RGB

    buf = ctypes.create_string_buffer(w * h * 4)
    lines = gdi32.GetDIBits(hdc_win, hbm, 0, h, buf, ctypes.byref(bi), 0)

    img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1)
    img.convert("RGB").save(out_path)

    gdi32.DeleteObject(hbm)
    gdi32.DeleteDC(hdc_win)
    user32.ReleaseDC(0, hdc_screen)
    return "ok PrintWindow=%s GetDIBits=%s 尺寸=%dx%d" % (bool(ok), lines, w, h)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    out = sys.argv[1]
    if len(sys.argv) >= 3:
        pid = int(sys.argv[2])
    else:
        # 自动找 Minecraft 窗口
        import subprocess
        out_txt = subprocess.run(["tasklist", "/FI", "IMAGENAME eq java.exe", "/FO", "CSV", "/NH"],
                                 capture_output=True, text=True, errors="replace").stdout
        pids = [int(ln.split(",")[1].strip('"')) for ln in out_txt.splitlines()
                if ln.count(",") >= 1 and ln.split(",")[1].strip('"').isdigit()]
        cands = []
        for p in pids:
            cands += [(t, h, p) for t, h in find_hwnd(p)]
        mc = [c for c in cands if "Minecraft" in c[0]]
        if not mc:
            print("找不到 Minecraft 窗口；候选：")
            for t, h, p in cands:
                print("   pid=%d hwnd=%d title=%r" % (p, h, t))
            return 1
        pid = mc[0][2]
        print("自动选中 pid=%d title=%r" % (pid, mc[0][0]))

    ws = find_hwnd(pid)
    if not ws:
        print("pid=%d 没有可见窗口" % pid)
        return 1
    for t, h in ws:
        print("  窗口: hwnd=%d title=%r" % (h, t))
    print(grab(ws[0][1], out))
    print("saved:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
