"""只解析 Lua 并按字节位置编辑串口配置，不执行配置代码。"""
from dataclasses import dataclass
from copy import deepcopy
import re
from tree_sitter import Language, Parser
import tree_sitter_lua

class ConfigError(ValueError):
    pass

@dataclass(frozen=True)
class Dynamic:
    source: str

SCHEMAS = {
    'ports': {'name': str, 'port': str, 'baud': int, 'data_bits': int, 'parity': str,
              'stop_bits': int, 'flow_control': str, 'log_on_connect': bool},
    'logging': {'directory': str, 'max_file_size_mb': int, 'timestamps': bool},
    'rule': {'foreground': str, 'keywords': list, 'patterns': list, 'case_sensitive': bool},
}


def walk(node):
    yield node
    for child in node.named_children:
        yield from walk(child)


def decode_string(raw):
    long = re.fullmatch(r'\[(=*)\[(.*)\]\1\]', raw, re.S)
    if long:
        return re.sub(r'^\r?\n', '', long[2], count=1).replace('\r\n', '\n')
    if len(raw) < 2 or raw[0] not in "\"'":
        raise ConfigError('无法识别字符串')
    text = raw[1:-1]
    result = bytearray()
    i = 0
    escapes = {'a':7,'b':8,'f':12,'n':10,'r':13,'t':9,'v':11,'\\':92,'"':34,"'":39}
    while i < len(text):
        if text[i] != '\\':
            result.extend(text[i].encode('utf-8')); i += 1; continue
        i += 1
        if i == len(text): raise ConfigError('字符串转义不完整')
        c = text[i]; i += 1
        if c in escapes: result.append(escapes[c])
        elif c == 'z':
            while i < len(text) and text[i].isspace(): i += 1
        elif c == 'x':
            result.append(int(text[i:i+2], 16)); i += 2
        elif c == 'u' and i < len(text) and text[i] == '{':
            end = text.index('}',i); result.extend(chr(int(text[i+1:end],16)).encode()); i=end+1
        elif c.isdigit():
            digits = c
            while i < len(text) and len(digits)<3 and text[i].isdigit(): digits+=text[i];i+=1
            result.append(int(digits))
        elif c in '\r\n':
            if c == '\r' and i < len(text) and text[i]=='\n': i+=1
            result.append(10)
        else: raise ConfigError('不支持的字符串转义')
    return result.decode('utf-8')


def lua(value, indent='', newline='\n'):
    if value is None: return 'nil'
    if type(value) is bool: return 'true' if value else 'false'
    if type(value) is int: return str(value)
    if isinstance(value,str):
        out = value.replace('\\','\\\\').replace("'","\\'")
        out = ''.join(f'\\{ord(c):03d}' if ord(c)<32 or ord(c)==127 else c for c in out)
        return "'"+out+"'"
    if isinstance(value,list):
        if any(isinstance(x,dict) for x in value):
            inner=indent+'  '
            return '{'+newline+''.join(inner+lua(x,inner,newline)+','+newline for x in value)+indent+'}'
        return '{ '+', '.join(lua(x,indent,newline) for x in value)+' }'
    if isinstance(value,dict):
        inner=indent+'  '
        return '{'+newline+''.join(inner+k+' = '+lua(v,inner,newline)+','+newline for k,v in value.items() if not k.startswith('_'))+indent+'}'
    raise ConfigError('无法保存动态表达式')


class LuaDocument:
    LIMIT = 2 * 1024 * 1024
    def __init__(self, data):
        if len(data)>self.LIMIT: raise ConfigError('配置文件超过 2 MB')
        try: data.decode('utf-8-sig')
        except UnicodeError as e: raise ConfigError('仅支持 UTF-8 配置文件，请先转换编码') from e
        self.data=data
        self.parser=Parser(Language(tree_sitter_lua.language()))
        self.tree=self.parser.parse(data)
        if self.tree.root_node.has_error:
            bad=next((n for n in walk(self.tree.root_node) if n.type=='ERROR' or n.is_missing),self.tree.root_node)
            raise ConfigError(f'Lua 语法错误，第 {bad.start_point.row+1} 行；文件未修改')
        self.nl='\r\n' if b'\r\n' in data else '\n'
        self.sections={}; self.reasons={}; self.records={};self.nodes={};self.creatable=set();self.insert_at=None
        funcs=[n for n in self.tree.root_node.named_children if n.type=='function_declaration' and self.text(n.child_by_field_name('name'))=='M.apply' and self.text(n.child_by_field_name('parameters'))=='(config)']
        if len(funcs)==1:
            self.insert_at=funcs[0].children[-1].start_byte
        self.model={'ports':[],'logging':{},'rules':[], 'case_sensitive':None}
        self._locate()
        self.original=deepcopy(self.model)

    def text(self,n): return self.data[n.start_byte:n.end_byte].decode('utf-8')

    def literal(self,n):
        text=self.text(n)
        try:
            if n.type=='string': return decode_string(text)
            if n.type=='true': return True
            if n.type=='false': return False
            if n.type=='nil': return None
            if n.type=='number' and re.fullmatch(r'\d+',text): return int(text)
            if n.type=='table_constructor':
                fields=self.fields(n)
                if all(f.child_by_field_name('name') is None for f in fields):
                    values=[self.literal(f.child_by_field_name('value')) for f in fields]
                    if all(isinstance(x,str) for x in values): return values
        except (ValueError,UnicodeError,OverflowError): pass
        return Dynamic(text)

    @staticmethod
    def fields(n): return [c for c in n.named_children if c.type=='field']

    def mapping(self,n):
        out={}
        for f in self.fields(n):
            key=f.child_by_field_name('name')
            if key is None or key.type!='identifier': raise ConfigError('包含未支持的表键，保留为只读')
            name=self.text(key)
            if name in out: raise ConfigError('配置项重复，保留为只读')
            out[name]=f
        return out

    def record(self,n,kind):
        fields=self.mapping(n);out={'_id':n.start_byte}
        self.records[n.start_byte]=(n,kind)
        for name,f in fields.items():
            if name in SCHEMAS[kind]:
                v=f.child_by_field_name('value');value=self.literal(v)
                out[name]=value if value is None or type(value)==SCHEMAS[kind][name] else Dynamic(self.text(v))
        # 未知字段含有代码时，禁止删除整条记录。
        out['_protected']=any(isinstance(self.literal(f.child_by_field_name('value')),Dynamic) for f in fields.values())
        return out

    def _locate(self):
        assignments=[]
        for n in walk(self.tree.root_node):
            if n.type!='assignment_statement':continue
            vs=next((c for c in n.named_children if c.type=='variable_list'),None)
            es=next((c for c in n.named_children if c.type=='expression_list'),None)
            if vs is None or es is None or len(vs.named_children)!=1 or len(es.named_children)!=1:continue
            assignments.append((self.text(vs.named_children[0]),es.named_children[0],n))
        for section,key,kind in [('ports','serial_ports','ports'),('logging','serial_logging','logging'),('rules','serial_highlighting','rule')]:
            hits=[(v,n) for k,v,n in assignments if k=='config.'+key]
            if section=='ports':
                resolved=[]
                for value,statement in hits:
                    if value.type=='identifier' and self.text(value)=='serial_ports':
                        alias=[(v,n) for k,v,n in assignments if k=='serial_ports']
                        if len(alias)==1:
                            declaration=alias[0][1]
                            scope=declaration.parent.parent if declaration.parent.type=='variable_declaration' else None
                            ancestors=[];parent=statement.parent
                            while parent is not None:
                                ancestors.append(parent);parent=parent.parent
                            if scope in ancestors and declaration.end_byte<statement.start_byte:
                                value=alias[0][0]
                    resolved.append((value,statement))
                # 支持现有模块中先清空列表、再使用 Windows 本地列表的写法。
                if len(resolved)==2 and resolved[0][0].type=='table_constructor' and not self.fields(resolved[0][0]):
                    resolved=resolved[1:]
                hits=resolved
            if not hits:
                if self.insert_at is not None:self.creatable.add(section)
                else:self.reasons[section]='文件中没有该配置，当前只读'
                continue
            if len(hits)!=1 or hits[0][0].type!='table_constructor':
                self.reasons[section]='配置由代码计算或存在多次赋值，当前只读'
                continue
            node=hits[0][0]
            statement=hits[0][1]
            owner=statement.parent
            while owner is not None and owner.type not in ('function_declaration','function_definition'):
                owner=owner.parent
            if owner is not None and (owner.type!='function_declaration' or self.text(owner.child_by_field_name('name'))!='M.apply' or self.text(owner.child_by_field_name('parameters'))!='(config)'):
                self.reasons[section]='配置位于未支持的函数中，当前只读'
                continue
            try:
                if section=='ports':
                    rows=[]
                    for field in self.fields(node):
                        v=field.child_by_field_name('value')
                        if field.child_by_field_name('name') or v.type!='table_constructor':raise ConfigError('串口列表包含动态条目，当前只读')
                        rows.append(self.record(v,kind))
                    self.model['ports']=rows
                elif section=='logging':self.model['logging']=self.record(node,kind)
                else:
                    fields=self.mapping(node)
                    case=fields.get('case_sensitive')
                    self.model['case_sensitive']=self.literal(case.child_by_field_name('value')) if case else None
                    rulefield=fields.get('rules')
                    if rulefield is None: raise ConfigError('没有规则列表，当前只读')
                    rules=rulefield.child_by_field_name('value')
                    if rules.type!='table_constructor':raise ConfigError('高亮规则由代码计算，当前只读')
                    rows=[]
                    for field in self.fields(rules):
                        v=field.child_by_field_name('value')
                        if field.child_by_field_name('name') or v.type!='table_constructor':raise ConfigError('高亮规则包含动态条目，当前只读')
                        rows.append(self.record(v,kind))
                    self.model['rules']=rows;self.nodes['rules_list']=rules
                self.sections[section]=node
            except ConfigError as e:
                self.reasons[section]=str(e)
                self.model[section]=[] if section!='logging' else {}

    def validate(self,model):
        for section in ['ports','logging','rules']:
            if section not in self.sections and section not in self.creatable and model[section]!=self.original[section]:raise ConfigError('禁止修改只读配置')
        if set(model)!=set(self.original):raise ConfigError('存在不允许修改的配置')
        for group,rows in [('ports',model['ports']),('logging',[model['logging']]),('rule',model['rules'])]:
            for row in rows:
                if set(row)-set(SCHEMAS[group])-{'_id','_protected'}:raise ConfigError('存在未支持的字段')
                for k,v in row.items():
                    if k.startswith('_') or v is None or isinstance(v,Dynamic):continue
                    if type(v)!=SCHEMAS[group][k]:raise ConfigError(f'{k} 的值类型不正确')
                    if isinstance(v,str) and '\x00' in v:raise ConfigError(f'{k} 不能包含空字符')
                    if isinstance(v,list) and not all(type(x)==str and x and len(x.encode())<=4096 for x in v):raise ConfigError(f'{k} 每行必须是 1 至 4096 字节的非空文字')
                if group=='ports':
                    for k,allowed in [('data_bits',[5,6,7,8]),('stop_bits',[1,2]),('parity',['None','Odd','Even']),('flow_control',['None','Software','Hardware'])]:
                        if k in row and row[k] is not None and not isinstance(row[k],Dynamic) and row[k] not in allowed:raise ConfigError(f'{k} 的值不受支持')
                    if 'baud' in row and row['baud'] is not None and not isinstance(row['baud'],Dynamic) and not 0<row['baud']<=4294967295:raise ConfigError('波特率必须在 1 至 4294967295 之间')
                    if not row.get('name'):raise ConfigError('连接名称不能为空')
                    if row.get('name')=='local':raise ConfigError('local 是终端保留名称，请使用其他连接名称')
                    if row.get('port')=='':raise ConfigError('端口名称不能为空')
                if group=='logging':
                    size=row.get('max_file_size_mb')
                    if size is not None and not isinstance(size,Dynamic) and not 0<size<=18446744073709:raise ConfigError('日志文件大小必须为正整数且不能溢出')
                if group=='rule':
                    color=row.get('foreground')
                    if not isinstance(color,Dynamic) and not re.fullmatch(r'#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?',color or ''):raise ConfigError('颜色使用 #RRGGBB 或 #RRGGBBAA 格式')
        names=[r.get('name') for r in model['ports'] if not isinstance(r.get('name'),Dynamic)]
        if len(names)!=len(set(names)):raise ConfigError('串口连接名称不能重复')
        if len(model['rules'])>32:raise ConfigError('高亮规则最多 32 组')
        if sum(len(r.get(k) or []) for r in model['rules'] for k in ('keywords','patterns') if not isinstance(r.get(k),Dynamic))>128:raise ConfigError('关键词与正则合计最多 128 条')
        case=model['case_sensitive']
        if case is not None and not isinstance(case,Dynamic) and type(case)!=bool:raise ConfigError('大小写选项必须为布尔值')

    def build(self,model):
        self.validate(model)
        patches=[]
        def add(start,end,value):patches.append((start,end,value.encode()))
        def insert_fields(node,entries,retained=None):
            if not entries:return
            fields=self.fields(node) if retained is None else retained
            if fields:
                last=fields[-1];suffix=self.data[last.end_byte:node.end_byte-1]
                # 注释不充当分隔符；从语法树读取逗号或分号。
                trailing=any(c.type in (',',';') and c.start_byte>=last.end_byte for c in node.children)
                if not trailing:add(last.end_byte,last.end_byte,',')
            line=self.data[:node.start_byte].rsplit(b'\n',1)[-1]
            indent=re.match(rb'[ \t]*',line)[0].decode()
            text=self.nl+''.join(indent+'  '+entry+self.nl for entry in entries)+indent
            add(node.end_byte-1,node.end_byte-1,text)
        def remove_field(parent,field):
            end=field.end_byte
            following=[c for c in parent.children if c.start_byte>=end and c.type in (',',';')]
            if following and self.data[end:following[0].start_byte].strip()==b'':end=following[0].end_byte
            add(field.start_byte,end,'')
        def edit_record(node,new,kind):
            fields=self.mapping(node);added=[]
            for key in SCHEMAS[kind]:
                field=fields.get(key)
                old=self.literal(field.child_by_field_name('value')) if field else None
                if old is not None and type(old)!=SCHEMAS[kind][key]:
                    old=Dynamic(self.text(field.child_by_field_name('value')))
                value=new.get(key)
                if old==value:continue
                if isinstance(old,Dynamic) or isinstance(value,Dynamic):raise ConfigError(f'{key} 由代码计算，不能修改')
                if field:
                    v=field.child_by_field_name('value')
                    # 字符串列表含注释时，仅替换对应字符串；增删另按表成员处理。
                    if isinstance(old,list) and isinstance(value,list) and v.type=='table_constructor':
                        fs=self.fields(v)
                        for index in range(min(len(fs),len(value))):
                            vn=fs[index].child_by_field_name('value')
                            if old[index]!=value[index]:add(vn.start_byte,vn.end_byte,lua(value[index]))
                        for f in fs[len(value):]:remove_field(v,f)
                        insert_fields(v,[lua(x)+',' for x in value[len(fs):]],fs[:len(value)])
                    else:add(v.start_byte,v.end_byte,lua(value))
                elif value is not None:added.append(key+' = '+lua(value,newline=self.nl)+',')
            insert_fields(node,added)
        def edit_list(node,rows,kind):
            fields=self.fields(node);old_ids={f.child_by_field_name('value').start_byte:f for f in fields}
            ids=[r.get('_id') for r in rows if r.get('_id') is not None]
            if len(ids)!=len(set(ids)) or any(i not in old_ids for i in ids):raise ConfigError('条目标识不匹配，请重新打开配置')
            if ids!=[i for i in old_ids if i in ids]:raise ConfigError('当前不支持调整条目顺序')
            for identity,field in old_ids.items():
                if identity not in ids:
                    old=self.record(field.child_by_field_name('value'),kind)
                    if old['_protected']:raise ConfigError('条目包含动态代码，不能删除')
                    remove_field(node,field)
            entries=[]
            for row in rows:
                identity=row.get('_id')
                if identity is None:
                    line=self.data[:node.start_byte].rsplit(b'\n',1)[-1]
                    indent=re.match(rb'[ \t]*',line)[0].decode()+'  '
                    entries.append(lua(row,indent,newline=self.nl)+',')
                else:edit_record(old_ids[identity].child_by_field_name('value'),row,kind)
            insert_fields(node,entries,[f for i,f in old_ids.items() if i in ids])
        if 'ports' in self.sections:edit_list(self.sections['ports'],model['ports'],'ports')
        if 'logging' in self.sections:edit_record(self.sections['logging'],model['logging'],'logging')
        if 'rules' in self.sections:
            edit_list(self.nodes['rules_list'],model['rules'],'rule')
            node=self.sections['rules'];field=self.mapping(node).get('case_sensitive');old=self.original['case_sensitive'];new=model['case_sensitive']
            if old!=new:
                if isinstance(old,Dynamic) or isinstance(new,Dynamic):raise ConfigError('大小写选项由代码计算，不能修改')
                if field:
                    value=field.child_by_field_name('value');add(value.start_byte,value.end_byte,lua(new))
                else:insert_fields(node,['case_sensitive = '+lua(new)+','])
        elif 'rules' not in self.creatable and model['case_sensitive']!=self.original['case_sensitive']:raise ConfigError('高亮设置只读')
        additions=[]
        expected=set(self.sections)
        for section,key in [('ports','serial_ports'),('logging','serial_logging'),('rules','serial_highlighting')]:
            changed=model[section]!=self.original[section] or (section=='rules' and model['case_sensitive']!=self.original['case_sensitive'])
            if section in self.creatable and changed:
                value=model[section] if section!='rules' else {'rules':model['rules'],'case_sensitive':model['case_sensitive']}
                additions.append('  config.'+key+' = '+lua(value,'  ',self.nl)+self.nl)
                expected.add(section)
        if additions:add(self.insert_at,self.insert_at,self.nl+''.join(additions))
        ordered=sorted(patches,key=lambda p:(p[0],p[1]))
        for left,right in zip(ordered,ordered[1:]):
            if left[1]>right[0]:raise ConfigError('修改范围重叠，文件未保存')
        result=self.data
        for start,end,value in reversed(ordered):result=result[:start]+value+result[end:]
        if len(result)>self.LIMIT:raise ConfigError('配置文件超过 2 MB')
        parsed=LuaDocument(result)
        # 修改后仍须能识别相同章节，避免插入位置改变 Lua 结构。
        if set(parsed.sections)!=expected:raise ConfigError('修改后配置结构无法识别，文件未保存')
        def values(value):
            if isinstance(value,dict):return {k:values(v) for k,v in value.items() if not k.startswith('_') and v is not None}
            if isinstance(value,list):return [values(v) for v in value]
            return value
        if values(parsed.model)!=values(model):raise ConfigError('修改后的配置值与预览不一致，文件未保存')
        return result
