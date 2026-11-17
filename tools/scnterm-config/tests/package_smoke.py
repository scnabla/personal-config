"""启动打包程序并核对窗口与独立校验器，仅操作本次创建的进程。"""
import ctypes as c
from ctypes import wintypes as w
import json
from pathlib import Path
import subprocess
import time
import sys
from window_capture import capture

c.windll.shcore.SetProcessDpiAwareness(1)
root=Path(__file__).resolve().parents[1]
package=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root/'dist/ScnTermConfig'
work=root/'.cache/package-smoke';work.mkdir(parents=True,exist_ok=True)
helper=package/'_internal/scnterm-config-validator.exe'
request=[{'pattern':r'\p{Han}+','literal':False,'case_sensitive':False}]
checked=subprocess.run([str(helper)],input=json.dumps(request),text=True,encoding='utf-8',capture_output=True,creationflags=0x08000000,check=True)
assert json.loads(checked.stdout)['ok']
user=c.windll.user32
callback=c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
user.EnumWindows.argtypes=[callback,w.LPARAM]
user.GetWindowThreadProcessId.argtypes=[w.HWND,c.POINTER(w.DWORD)]
user.GetWindowTextW.argtypes=[w.HWND,w.LPWSTR,c.c_int]
user.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
process=subprocess.Popen([str(package/'ScnTermConfig.exe'),'--config-dir',str(root/'examples')])
result={'pid':process.pid,'package':str(package)}
try:
    deadline=time.monotonic()+25;windows=[]
    @callback
    def visit(hwnd,_):
        pid=w.DWORD();user.GetWindowThreadProcessId(hwnd,c.byref(pid))
        if pid.value==process.pid:
            title=c.create_unicode_buffer(256);user.GetWindowTextW(hwnd,title,256)
            if title.value=='ScnTerm 配置':windows.append(hwnd)
        return True
    while time.monotonic()<deadline and not windows:
        if process.poll() is not None:raise RuntimeError('打包程序提前退出')
        user.EnumWindows(visit,0);time.sleep(.2)
    assert windows,'未找到打包程序窗口'
    time.sleep(1)
    class Window:
        def winfo_id(self):return windows[0]
    capture(Window(),work/'window.bmp')
    user.PostMessageW(windows[0],0x0010,0,0)
    assert process.wait(timeout=8)==0
    result.update(passed=True,checks=['packaged GUI startup','packaged Rust regex helper','normal window close'])
finally:
    if process.poll() is None:process.terminate();process.wait(timeout=5)
    (work/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
