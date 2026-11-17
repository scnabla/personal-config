"""仅捕获传入的测试窗口，不切换桌面。"""
import ctypes as c
from ctypes import wintypes as w
import struct

def capture(root,path):
    user=c.windll.user32;gdi=c.windll.gdi32
    user.GetAncestor.argtypes=[w.HWND,w.UINT];user.GetAncestor.restype=w.HWND
    user.GetWindowRect.argtypes=[w.HWND,c.POINTER(w.RECT)]
    user.GetDC.argtypes=[w.HWND];user.GetDC.restype=w.HDC
    user.ReleaseDC.argtypes=[w.HWND,w.HDC]
    user.PrintWindow.argtypes=[w.HWND,w.HDC,w.UINT]
    gdi.CreateCompatibleDC.argtypes=[w.HDC];gdi.CreateCompatibleDC.restype=w.HDC
    gdi.CreateCompatibleBitmap.argtypes=[w.HDC,c.c_int,c.c_int];gdi.CreateCompatibleBitmap.restype=w.HBITMAP
    gdi.SelectObject.argtypes=[w.HDC,w.HGDIOBJ];gdi.SelectObject.restype=w.HGDIOBJ
    gdi.DeleteObject.argtypes=[w.HGDIOBJ];gdi.DeleteDC.argtypes=[w.HDC]
    gdi.GetDIBits.argtypes=[w.HDC,w.HBITMAP,w.UINT,w.UINT,c.c_void_p,c.c_void_p,w.UINT]
    hwnd=user.GetAncestor(root.winfo_id(),2);rect=w.RECT();user.GetWindowRect(hwnd,c.byref(rect))
    width,height=rect.right-rect.left,rect.bottom-rect.top
    dc=user.GetDC(hwnd);memory=gdi.CreateCompatibleDC(dc);bitmap=gdi.CreateCompatibleBitmap(dc,width,height);old=gdi.SelectObject(memory,bitmap)
    try:
        if not user.PrintWindow(hwnd,memory,2):raise RuntimeError('测试窗口截图失败')
        header=struct.pack('<IiiHHIIiiII',40,width,-height,1,32,0,width*height*4,0,0,0,0)
        info=c.create_string_buffer(header+bytes(16));pixels=c.create_string_buffer(width*height*4)
        gdi.SelectObject(memory,old)
        if not gdi.GetDIBits(memory,bitmap,0,height,pixels,info,0):raise RuntimeError('读取测试截图失败')
        path.write_bytes(struct.pack('<2sIHHI',b'BM',54+len(pixels),0,0,54)+header+pixels.raw)
    finally:gdi.DeleteObject(bitmap);gdi.DeleteDC(memory);user.ReleaseDC(hwnd,dc)
