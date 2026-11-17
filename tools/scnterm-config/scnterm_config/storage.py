"""独立 Lua 文件保存、冲突检测和受限备份恢复。"""
from pathlib import Path
from datetime import datetime
from copy import deepcopy
import difflib
import hashlib
import json
import os
import tempfile
import uuid
from .lua_document import LuaDocument, ConfigError
from .module_document import ModuleDocument


def digest(data): return hashlib.sha256(data).hexdigest()


class ConfigSession:
    def __init__(self,path):
        original=Path(path).absolute()
        if original.name not in ('serial.lua','ssh.lua','keys.lua'):raise ConfigError('仅允许编辑 serial.lua、ssh.lua 和 keys.lua')
        self.filename=original.name
        self.parse=LuaDocument if self.filename=='serial.lua' else lambda data:ModuleDocument(data,self.filename[:-4])
        if original.is_symlink():raise ConfigError('配置是链接文件，当前只读')
        self.path=original.resolve()
        self.reload()

    def reload(self):
        if self.path.is_symlink() or not self.path.is_file():raise ConfigError('配置文件不存在或已替换为链接')
        if self.path.stat().st_size>LuaDocument.LIMIT:raise ConfigError('配置文件超过 2 MB')
        data=self.path.read_bytes();document=self.parse(data)
        self.data=data;self.document=document;self.model=deepcopy(document.model)

    def preview(self):
        candidate=self.document.build(self.model)
        if candidate!=self.data and self.filename=='serial.lua':
            from .validation import validate_patterns
            validate_patterns(self.model)
        diff=''.join(difflib.unified_diff(self.data.decode('utf-8-sig').splitlines(True),candidate.decode('utf-8-sig').splitlines(True),fromfile='保存前 / '+self.filename,tofile='保存后 / '+self.filename))
        return candidate,diff

    def _unchanged(self):
        if self.path.is_symlink() or self.path.stat().st_size!=len(self.data) or self.path.read_bytes()!=self.data:raise ConfigError('文件已被其他程序修改。请重新打开配置后再编辑，当前修改未写入。')

    def _replace(self,candidate):
        temp=None
        try:
            with tempfile.NamedTemporaryFile(dir=self.path.parent,prefix='.'+self.filename[:-4]+'-',suffix='.tmp',delete=False) as f:
                temp=Path(f.name);f.write(candidate);f.flush();os.fsync(f.fileno())
            os.chmod(temp,self.path.stat().st_mode)
            self._unchanged()
            os.replace(temp,self.path);temp=None
        finally:
            if temp is not None:temp.unlink(missing_ok=True)

    def save(self,previewed):
        candidate,_=self.preview()
        if candidate!=previewed:raise ConfigError('修改内容已变化，请重新预览')
        self._unchanged()
        if candidate==self.data:return None
        folder=self.path.parent/'.scnterm-config-backups'
        if folder.is_symlink():raise ConfigError('备份目录不能是链接')
        folder.mkdir(exist_ok=True)
        backup=folder/(datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'-'+uuid.uuid4().hex[:8])
        backup.mkdir()
        original=backup/self.filename
        with original.open('xb') as f:f.write(self.data);f.flush();os.fsync(f.fileno())
        metadata={'path':str(self.path),'before':digest(self.data),'after':digest(candidate)}
        (backup/'record.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
        self._replace(candidate)
        self.reload()
        return original

    def backups(self):
        folder=self.path.parent/'.scnterm-config-backups'
        if folder.is_symlink():return []
        return sorted((p for p in folder.glob('*/'+self.filename) if not p.is_symlink()),reverse=True)

    def restore_preview(self,backup):
        backup=Path(backup)
        folder=self.path.parent/'.scnterm-config-backups'
        if backup.name!=self.filename or backup.is_symlink() or backup.parent.is_symlink() or folder.is_symlink() or backup.parent.parent!=folder:raise ConfigError('备份位置无效')
        info=json.loads((backup.parent/'record.json').read_text(encoding='utf-8'))
        if not isinstance(info,dict):raise ConfigError('备份记录格式无效')
        if backup.stat().st_size>LuaDocument.LIMIT:raise ConfigError('备份文件超过 2 MB')
        data=backup.read_bytes()
        if info.get('path')!=str(self.path) or info.get('before')!=digest(data):raise ConfigError('备份不属于当前配置或内容已变化')
        self._unchanged()
        if info.get('after')!=digest(self.data):raise ConfigError('当前文件与这份备份对应的保存结果不同。请先恢复最近一次修改，或手动核对文件。')
        self.parse(data)
        diff=''.join(difflib.unified_diff(self.data.decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),fromfile='当前 / '+self.filename,tofile='恢复后 / '+self.filename))
        return data,diff

    def restore(self,backup,previewed):
        data,_=self.restore_preview(backup)
        if data!=previewed:raise ConfigError('备份已变化，请重新预览')
        # 被替换的版本已经是这次保存的结果；原始版本保存在备份中。
        self._replace(data);self.reload()
