"""在当前测试桌面依次验证源码窗口和打包程序。"""
from pathlib import Path
import runpy

tests=Path(__file__).resolve().parent
for name in ('gui_smoke.py','package_smoke.py'):
    runpy.run_path(str(tests/name),run_name='__main__')
