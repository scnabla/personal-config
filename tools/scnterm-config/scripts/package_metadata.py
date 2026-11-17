"""记录包来源，并保留随运行组件分发的许可证。"""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
package=root/'dist/ScnTermConfig'
licenses=package/'licenses';licenses.mkdir(exist_ok=True)
for source in (root/'assets/licenses').glob('*'):
    if source.is_file():shutil.copy2(source,licenses/source.name)
for name in ('tree-sitter','tree-sitter-lua','pyinstaller'):
    dist=importlib.metadata.distribution(name)
    for item in dist.files or []:
        if 'license' in item.name.lower() or 'copying' in item.name.lower():
            source=Path(dist.locate_file(item))
            if source.is_file():shutil.copy2(source,licenses/(name+'-'+source.name))
for base in {Path(sys.base_prefix),Path(sys.base_prefix)/'tcl'}:
    if base.is_dir():
        for pattern in ('LICENSE*','license*','*/license*'):
            for source in base.glob(pattern):
                if source.is_file():shutil.copy2(source,licenses/(source.parent.name+'-'+source.name))
# Cargo 元数据仅用于定位已下载的依赖许可证，不访问终端项目。
metadata=json.loads(subprocess.check_output(['cargo','metadata','--locked','--format-version','1','--manifest-path',str(root/'validator/Cargo.toml')],text=True,encoding='utf-8'))
for dep in metadata['packages']:
    directory=Path(dep['manifest_path']).parent
    for source in directory.glob('*'):
        if source.is_file() and source.name.lower().startswith(('license','copying')):
            shutil.copy2(source,licenses/(dep['name']+'-'+source.name))
commit=os.environ.get('GITHUB_SHA')
if not commit:
    result=subprocess.run(['git','rev-parse','HEAD'],cwd=root,capture_output=True,text=True)
    commit=result.stdout.strip() if result.returncode==0 else 'local-uncommitted'
info={'repository':os.environ.get('GITHUB_REPOSITORY','scnabla/personal-config'),'source_directory':'tools/scnterm-config','commit':commit,'run_url':os.environ.get('SCNTERM_BUILD_URL'),'python':sys.version.split()[0],
      'files':{str(p.relative_to(package)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in package.rglob('*') if p.is_file() and p.name!='build-info.json'}}
(package/'build-info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
