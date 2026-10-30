import ctypes, time, sys
from ctypes import wintypes
u = ctypes.windll.user32
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]
class INPUT(ctypes.Structure):
    class _I(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]
    _anonymous_ = ("i",)
    _fields_ = [("type", wintypes.DWORD), ("i", _I)]
def send(flag):
    inp = INPUT(); inp.type = 0
    inp.mi = MOUSEINPUT(0,0,0,flag,0,None)
    u.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
hold = float(sys.argv[1]) if len(sys.argv)>1 else 2.0
# focus minecraft window
hwnd = 0
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
def find(h, _):
    global hwnd
    b = ctypes.create_unicode_buffer(512)
    u.GetWindowTextW(h, b, 512)
    if u.IsWindowVisible(h) and "Minecraft" in b.value:
        hwnd = h
        return False
    return True
u.EnumWindows(WNDENUMPROC(find), 0)
print("hwnd", hwnd)
if hwnd:
    u.SetForegroundWindow(hwnd)
    time.sleep(0.4)
send(MOUSEEVENTF_RIGHTDOWN); print("right down")
time.sleep(hold)
send(MOUSEEVENTF_RIGHTUP); print("right up")