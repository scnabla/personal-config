"""SSH 与快捷键的静态表编辑；保留函数、条件分支和未修改的 Lua 原文。"""
from copy import deepcopy
import re
from .lua_document import LuaDocument, ConfigError, Dynamic, lua, walk

# 新动作的源码来自固定清单，不接受界面输入的代码。
ACTION_CODES = {
    '打开启动菜单': 'ShowLauncher',
    '打开 SSH 目录菜单': 'ShowDirectoryMenu',
    '重新加载配置': 'ReloadConfiguration',
    '新建标签页': "SpawnTab 'CurrentPaneDomain'",
    '左右分屏': "SplitHorizontal { domain = 'CurrentPaneDomain' }",
    '上下分屏': "SplitVertical { domain = 'CurrentPaneDomain' }",
    '关闭窗格（确认）': 'CloseCurrentPane { confirm = true }',
    '关闭标签页（确认）': 'CloseCurrentTab { confirm = true }',
    '放大或还原窗格': 'TogglePaneZoomState',
    '切换全屏': 'ToggleFullScreen',
    '复制': "CopyTo 'Clipboard'",
    '粘贴': "PasteFrom 'Clipboard'",
    '上一个标签页': 'ActivateTabRelative(-1)',
    '下一个标签页': 'ActivateTabRelative(1)',
    '按数字交换窗格': "PaneSelect { alphabet = '1234567890', mode = 'SwapWithActive' }",
}
FIELDS = {
    'ssh': ('name','remote_address','username','multiplexing','connect_automatically'),
    'keys': ('key','mods','action'),
}


def compact(text): return re.sub(r'\s+', '', text).replace('"', "'")
def action_code(label): return "require('wezterm').action." + ACTION_CODES[label]

def parse_action(text):
    suffix = re.sub(r"^(?:wezterm|act|action|require\(['\"]wezterm['\"]\))\.?(?:action\.)?", '', text)
    for label, code in ACTION_CODES.items():
        if compact(suffix) == compact(code):return label
    return Dynamic(text)


def address_parts(address):
    # 保留地址字面内容，支持 host、host:port 和 [IPv6]:port。
    if not isinstance(address,str) or not address.strip() or any(c.isspace() for c in address):
        raise ConfigError('服务器地址不能为空或包含空白')
    if address.startswith('['):
        match=re.fullmatch(r'(\[[^\]]+\])(?::(\d+))?',address)
        if not match:raise ConfigError('IPv6 地址使用 [地址]:端口 格式')
        host,port=match.group(1),match.group(2) or '22'
    elif address.count(':')<=1:
        host,separator,port=address.partition(':')
        if separator and not port:raise ConfigError('冒号后需要填写 SSH 端口')
        port=port or '22'
    else:raise ConfigError('IPv6 地址使用 [地址]:端口 格式')
    if not host or not port.isascii() or not port.isdigit() or not 1<=int(port)<=65535:
        raise ConfigError('SSH 端口必须在 1 至 65535 之间')
    return host,port


def combo(key,mods):
    if not isinstance(key,str) or not isinstance(mods,(str,type(None))):return None
    aliases={'LeftArrow':'←','RightArrow':'→','UpArrow':'↑','DownArrow':'↓'}
    return '|'.join(sorted(x.upper() for x in (mods or 'NONE').split('|') if x!='NONE'))+'|'+aliases.get(key,key).upper()

def label_combo(text):
    parts=[p.strip() for p in text.split('+')]
    return combo(parts[-1],'|'.join(parts[:-1]).upper())

def display_combo(key,mods):
    return ' + '.join([x.title() for x in (mods or 'NONE').split('|') if x!='NONE']+[key.upper() if len(key)==1 else key])


class ModuleDocument(LuaDocument):
    def __init__(self,data,kind):
        super().__init__(data)
        self.kind=kind;self.list_node=None;self.row_nodes={};self.row_fields={};self.insert_calls={}
        self.alias_fields={};self.enabled_node=None;self.reason='';self.labels=[]
        self.model={'rows':[], 'enabled':None}
        target='config.ssh_domains' if kind=='ssh' else 'config.keys'
        assignments=[]
        for node in walk(self.tree.root_node):
            if node.type!='assignment_statement':continue
            vs=next((c for c in node.named_children if c.type=='variable_list'),None)
            es=next((c for c in node.named_children if c.type=='expression_list'),None)
            if vs is not None and es is not None and len(vs.named_children)==len(es.named_children)==1:
                assignments.append((self.text(vs.named_children[0]),es.named_children[0],node))
        hits=[(value,node) for name,value,node in assignments if name==target]
        if kind=='ssh' and len(hits)==2 and hits[0][0].type=='table_constructor' and not self.fields(hits[0][0]):hits=hits[1:]
        if len(hits)!=1 or hits[0][0].type!='table_constructor' or not self.supported_scope(hits[0][1]):
            self.reason='未找到可直接编辑的配置表，或配置存在多次赋值。'
        else:
            self.list_node=hits[0][0]
            if kind=='ssh':self.find_legacy(assignments)
            try:
                for field in self.fields(self.list_node):
                    value=field.child_by_field_name('value')
                    if field.child_by_field_name('name') is not None or value.type!='table_constructor':raise ConfigError('配置列表含动态条目，当前只读。')
                    self.read_row(value,field)
                if kind=='keys':
                    for node in walk(self.tree.root_node):
                        if node.type!='function_call' or self.text(node.child_by_field_name('name'))!='table.insert':continue
                        args=node.child_by_field_name('arguments').named_children
                        if len(args)==2 and self.text(args[0])==target:
                            if args[1].type!='table_constructor' or node.parent.type!='block' or not self.supported_scope(node):raise ConfigError('快捷键包含动态追加条目，当前只读。')
                            self.read_row(args[1],None);self.insert_calls[args[1].start_byte]=node
                    for name,value,_ in assignments:
                        if name=='M.shortcut_labels' and value.type=='table_constructor':
                            self.labels.extend(self.fields(value))
            except ConfigError as e:
                self.reason=str(e);self.list_node=None;self.model['rows']=[]
        self.original=deepcopy(self.model)

    def supported_scope(self,node):
        owner=node.parent
        while owner is not None:
            if owner.type in ('function_declaration','function_definition'):
                return owner.type=='function_declaration' and self.text(owner.child_by_field_name('name'))=='M.apply' and self.text(owner.child_by_field_name('parameters'))=='(config)'
            owner=owner.parent
        return True

    def find_legacy(self,assignments):
        # 现有 ssh.lua 的根级 server/ssh_enabled；只识别唯一、静态声明。
        for name in ('server','ssh_enabled'):
            hits=[(v,n) for k,v,n in assignments if k==name]
            if len(hits)!=1:continue
            value,node=hits[0]
            if node.parent.type!='variable_declaration' or node.parent.parent.type!='chunk':continue
            if name=='server' and value.type=='table_constructor':
                try:self.alias_fields=self.mapping(value)
                except ConfigError:pass
            elif name=='ssh_enabled':
                self.enabled_node=value;self.model['enabled']=self.literal(value)

    def read_row(self,node,field):
        fields=self.mapping(node);row={'_id':node.start_byte}
        self.row_nodes[node.start_byte]=node;self.row_fields[node.start_byte]=field
        for key in FIELDS[self.kind]:
            f=fields.get(key)
            if f is None:continue
            v=f.child_by_field_name('value');value=self.literal(v)
            if self.kind=='keys' and key=='action':value=parse_action(self.text(v))
            if self.kind=='ssh' and key in ('remote_address','username'):
                expression=compact(self.text(v))
                alias_keys=('host','port') if key=='remote_address' else ('user',)
                expected="server.host..':'..server.port" if key=='remote_address' else 'server.user'
                if expression==expected and all(k in self.alias_fields for k in alias_keys):
                    values=[self.literal(self.alias_fields[k].child_by_field_name('value')) for k in alias_keys]
                    if all(isinstance(x,str) for x in values):
                        value=':'.join(values);row['_alias_'+key]=True
            row[key]=value
        self.model['rows'].append(row)

    def validate(self,model):
        if set(model)!=set(self.original):raise ConfigError('存在不允许修改的配置')
        if self.list_node is None and model!=self.original:raise ConfigError('当前配置只读')
        if model['enabled']!=self.original['enabled'] and (self.enabled_node is None or type(model['enabled']) is not bool or isinstance(self.original['enabled'],Dynamic)):
            raise ConfigError('SSH 开关不可修改')
        names=set();bindings=set()
        for row in model['rows']:
            if set(row)-set(FIELDS[self.kind])-{'_id','_alias_remote_address','_alias_username'}:raise ConfigError('存在未支持的字段')
            for key in FIELDS[self.kind]:
                value=row.get(key)
                if value is None or isinstance(value,Dynamic):continue
                expected=bool if key=='connect_automatically' else str
                if type(value)!=expected or (isinstance(value,str) and '\x00' in value):raise ConfigError(f'{key} 的值无效')
            if self.kind=='ssh':
                name=row.get('name');address=row.get('remote_address')
                if not name or name=='local':raise ConfigError('连接名称不能为空或使用 local')
                if isinstance(name,str):
                    if name in names:raise ConfigError('SSH 连接名称不能重复')
                    names.add(name)
                if not isinstance(address,Dynamic):address_parts(address)
                if row.get('multiplexing') not in (None,'None','WezTerm') and not isinstance(row.get('multiplexing'),Dynamic):raise ConfigError('SSH 会话类型无效')
            else:
                key=row.get('key');mods=row.get('mods')
                if not key:raise ConfigError('按键不能为空')
                if isinstance(mods,str) and any(x not in ('NONE','CTRL','SHIFT','ALT','SUPER','LEADER','CMD','WIN','OPT','META','LEFT_ALT','RIGHT_ALT') for x in mods.split('|')):raise ConfigError('修饰键使用 CTRL、SHIFT、ALT、SUPER 等名称，以 | 分隔；无修饰键填 NONE')
                action=row.get('action')
                if not isinstance(action,Dynamic) and action not in ACTION_CODES:raise ConfigError('请选择快捷键动作')
                binding=combo(key,mods)
                if binding is not None:
                    if binding in bindings:raise ConfigError('按键组合重复')
                    bindings.add(binding)

    def build(self,model):
        if model==self.original:return self.data
        self.validate(model);patches=[]
        def replace(node,value):patches.append((node.start_byte,node.end_byte,value.encode()))
        def append_fields(node,entries):
            if not entries:return
            fields=self.fields(node)
            if fields and not any(c.type in (',',';') and c.start_byte>=fields[-1].end_byte for c in node.children):patches.append((fields[-1].end_byte,fields[-1].end_byte,b','))
            indent=re.match(rb'[ \t]*',self.data[:node.start_byte].rsplit(b'\n',1)[-1])[0].decode()
            text=self.nl+''.join(indent+'  '+item+','+self.nl for item in entries)+indent
            patches.append((node.end_byte-1,node.end_byte-1,text.encode()))
        old={r['_id']:r for r in self.original['rows']};ids=[r['_id'] for r in model['rows'] if '_id' in r]
        if len(ids)!=len(set(ids)) or any(i not in old for i in ids) or ids!=[i for i in old if i in ids]:raise ConfigError('条目标识或顺序已变化，请重新读取配置')
        for identity in old:
            if identity in ids:continue
            if identity in self.insert_calls:replace(self.insert_calls[identity],'')
            else:
                field=self.row_fields[identity];end=field.end_byte
                following=next((c for c in self.list_node.children if c.start_byte>=end and c.type in (',',';')),None)
                if following and not self.data[end:following.start_byte].strip():end=following.end_byte
                patches.append((field.start_byte,end,b''))
        additions=[]
        for row in model['rows']:
            identity=row.get('_id')
            if identity is None:
                items=[]
                for key in FIELDS[self.kind]:
                    value=row.get(key)
                    if value is not None:items.append(key+' = '+(action_code(value) if key=='action' else lua(value)))
                additions.append('{ '+', '.join(items)+' }');continue
            node=self.row_nodes[identity];fields=self.mapping(node);extra=[]
            for key in FIELDS[self.kind]:
                value=row.get(key);before=old[identity].get(key)
                if value==before:continue
                if isinstance(value,Dynamic) or (isinstance(before,Dynamic) and key!='action'):raise ConfigError(f'{key} 由代码计算，不能修改')
                if old[identity].get('_alias_'+key):
                    vals=address_parts(value) if key=='remote_address' else (value,)
                    for alias,v in zip(('host','port') if key=='remote_address' else ('user',),vals):replace(self.alias_fields[alias].child_by_field_name('value'),lua(v))
                    continue
                text=action_code(value) if key=='action' else lua(value)
                if key in fields:replace(fields[key].child_by_field_name('value'),text)
                elif value is not None:extra.append(key+' = '+text)
            append_fields(node,extra)
        # 新增和删除可同时发生；插入前所需的逗号不依赖被删除条目。
        if additions:
            retained=[self.row_fields[i] for i in ids if i not in self.insert_calls]
            if retained:
                last=retained[-1]
                if not any(c.type in (',',';') and c.start_byte>=last.end_byte and c.start_byte<next((f.start_byte for f in self.fields(self.list_node) if f.start_byte>last.end_byte),self.list_node.end_byte) for c in self.list_node.children):patches.append((last.end_byte,last.end_byte,b','))
            indent=re.match(rb'[ \t]*',self.data[:self.list_node.start_byte].rsplit(b'\n',1)[-1])[0].decode()
            text=self.nl+''.join(indent+'  '+entry+','+self.nl for entry in additions)+indent
            patches.append((self.list_node.end_byte-1,self.list_node.end_byte-1,text.encode()))
        if model['enabled']!=self.original['enabled']:replace(self.enabled_node,lua(model['enabled']))
        if self.kind=='keys':
            changes={}
            current={r.get('_id'):r for r in model['rows']}
            for identity,row in old.items():
                before=combo(row.get('key'),row.get('mods'));after=current.get(identity)
                if before is not None and (after is None or combo(after.get('key'),after.get('mods'))!=before):changes[before]='未绑定快捷键' if after is None else display_combo(after['key'],after.get('mods'))
            for field in self.labels:
                node=field.child_by_field_name('value');value=self.literal(node)
                if isinstance(value,str) and label_combo(value) in changes:replace(node,lua(changes[label_combo(value)]))
        patches=sorted(set(patches),key=lambda item:(item[0],item[1]))
        for left,right in zip(patches,patches[1:]):
            if left[1]>right[0]:raise ConfigError('修改位置重叠，文件未保存')
        result=self.data
        for start,end,data in reversed(patches):result=result[:start]+data+result[end:]
        parsed=ModuleDocument(result,self.kind)
        if parsed.reason:raise ConfigError('修改后配置结构无法识别，文件未保存')
        # table.insert 条目在主表后读取；新主表条目可能排在这些条目前。
        def clean(row):return {k:v for k,v in row.items() if not k.startswith('_') and v is not None}
        expected=[clean(r) for r in model['rows']];actual=[clean(r) for r in parsed.model['rows']]
        if sorted(repr(sorted(r.items())) for r in expected)!=sorted(repr(sorted(r.items())) for r in actual) or parsed.model['enabled']!=model['enabled']:raise ConfigError('修改后的配置值与预览不一致，文件未保存')
        return result
