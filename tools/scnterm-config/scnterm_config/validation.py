"""独立 Rust 正则检查器；通过标准输入传递规则，不执行用户命令。"""
from pathlib import Path
import json
import subprocess
import sys
from .lua_document import ConfigError,Dynamic

def validate_patterns(model):
    patterns=[]
    default=model.get('case_sensitive')
    for row in model['rules']:
        case=row.get('case_sensitive')
        if case is None:case=default
        for field in ('keywords','patterns'):
            values=row.get(field)
            if isinstance(values,list):
                patterns.extend({'pattern':value,'literal':field=='keywords','case_sensitive':case is True} for value in values)
    if not patterns:return
    filename='scnterm-config-validator'+('.exe' if sys.platform=='win32' else '')
    root=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent.parent))
    candidates=[root/filename,root/'validator/target/release'/filename]
    exe=next((p for p in candidates if p.is_file()),None)
    if exe is None:raise ConfigError('缺少正则校验程序，请使用完整安装目录')
    try:
        result=subprocess.run([str(exe)],input=json.dumps(patterns,ensure_ascii=False),capture_output=True,text=True,encoding='utf-8',timeout=8,creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
        if result.returncode:raise ConfigError('正则校验程序未正常完成，文件未保存')
        data=json.loads(result.stdout)
        if not data.get('ok'):raise ConfigError(data.get('error','正则表达式无效'))
    except (OSError,subprocess.TimeoutExpired,json.JSONDecodeError) as e:raise ConfigError('正则校验未完成，文件未保存') from e
