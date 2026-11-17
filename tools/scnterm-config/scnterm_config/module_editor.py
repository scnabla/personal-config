"""SSH 与快捷键独立表单；保存入口由主窗口按当前文件选择。"""
from copy import deepcopy
import tkinter as tk
from tkinter import ttk, messagebox
from .lua_document import Dynamic, ConfigError
from .module_document import FIELDS, ACTION_CODES

BOOL={'是':True,'否':False}
LABELS={'name':'连接名称','remote_address':'服务器地址','username':'用户名',
        'multiplexing':'会话类型','connect_automatically':'启动时连接',
        'key':'按键','mods':'修饰键','action':'动作'}
CHOICES={'multiplexing':['None','WezTerm'],'connect_automatically':['是','否'],
         'action':list(ACTION_CODES)}
CUSTOM='自定义动作（保留原代码）'


class ModuleEditor(ttk.Frame):
    def __init__(self,app,parent,kind):
        super().__init__(parent,padding=16)
        self.app=app;self.kind=kind;self.filename=kind+'.lua';self.session=None
        self.index=None;self.current=None;self.original_display={};self.widgets={};self.touched=set()
        self.columnconfigure(1,weight=1);self.rowconfigure(2,weight=1)
        self.notice=ttk.Label(self,text='打开配置目录后开始编辑',wraplength=900)
        self.notice.grid(row=0,column=0,columnspan=2,sticky='w',pady=(0,12))
        self.enabled_frame=ttk.Frame(self)
        ttk.Label(self.enabled_frame,text='启用 SSH 菜单').pack(side='left',padx=(0,12))
        self.enabled=ttk.Combobox(self.enabled_frame,values=list(BOOL),state='readonly',width=8)
        self.enabled.pack(side='left');self.enabled.bind('<<ComboboxSelected>>',self.set_enabled)
        left=ttk.Frame(self);left.grid(row=2,column=0,sticky='ns',padx=(0,16))
        listing=ttk.Frame(left);listing.pack(fill='both',expand=True)
        self.listbox=tk.Listbox(listing,width=30,exportselection=False,selectbackground='#FFB52E',selectforeground='#172033',font=('Segoe UI',10))
        vertical=ttk.Scrollbar(listing,command=self.listbox.yview);vertical.pack(side='right',fill='y')
        horizontal=ttk.Scrollbar(left,orient='horizontal',command=self.listbox.xview);horizontal.pack(fill='x')
        self.listbox.configure(yscrollcommand=vertical.set,xscrollcommand=horizontal.set)
        self.listbox.pack(fill='both',expand=True);self.listbox.bind('<<ListboxSelect>>',self.select)
        buttons=ttk.Frame(left);buttons.pack(fill='x',pady=10)
        self.add_button=ttk.Button(buttons,text='新增服务器' if kind=='ssh' else '新增绑定',command=self.add);self.add_button.pack(side='left')
        self.delete_button=ttk.Button(buttons,text='删除',command=self.delete);self.delete_button.pack(side='left',padx=8)
        form=ttk.Frame(self);form.grid(row=2,column=1,sticky='nsew');form.columnconfigure(1,weight=1)
        for row,key in enumerate(FIELDS[kind]):
            ttk.Label(form,text=LABELS[key]).grid(row=row,column=0,sticky='w',padx=(0,12),pady=8)
            widget=ttk.Combobox(form,values=CHOICES[key],state='readonly') if key in CHOICES else ttk.Entry(form)
            widget.grid(row=row,column=1,sticky='ew',pady=8);self.widgets[key]=widget
            widget.bind('<KeyRelease>',lambda e:self.app.update_status())
            if key in CHOICES:widget.bind('<<ComboboxSelected>>',lambda e,k=key:self.touch(k))
        hint=('地址使用 主机:端口；省略端口时使用 22。\n用户名未填写时由 SSH 配置或当前用户确定。\nNone 为普通 SSH；WezTerm 需要服务器安装 WezTerm。\n密码不保存在此文件中。' if kind=='ssh' else
              '修饰键示例：CTRL|SHIFT、ALT；无修饰键填 NONE。\n自定义动作保留原代码，也可明确选择列表中的动作替换。\n条件分支保持原样，菜单是否可用仍由终端版本决定。')
        ttk.Label(form,text=hint,wraplength=600,foreground='#526078').grid(row=len(FIELDS[kind]),column=0,columnspan=2,sticky='w',pady=16)
        self.details=ttk.Label(form,text='',wraplength=600,foreground='#526078')
        self.details.grid(row=len(FIELDS[kind])+1,column=0,columnspan=2,sticky='w')
        self.refresh()

    def writable(self):return self.session is not None and self.session.document.list_node is not None
    def rows(self):return self.session.model['rows'] if self.session else []
    def touch(self,key):self.touched.add(key);self.app.update_status()
    def display(self,key,value):
        if isinstance(value,Dynamic):return CUSTOM if key=='action' else value.source
        if value is None:
            value={'multiplexing':'WezTerm','connect_automatically':False,'mods':'NONE'}.get(key)
        if type(value) is bool:return '是' if value else '否'
        return '' if value is None else str(value)
    def refresh(self,selected=0,reason=None):
        self.index=None;self.current=None
        self.notice.configure(text=reason or (self.session.document.reason if self.session else '') or (self.filename if self.session else '未找到 '+self.filename))
        self.enabled_frame.grid_forget()
        if self.kind=='ssh' and self.session and self.session.document.enabled_node is not None:
            value=self.session.model['enabled'];self.enabled_frame.grid(row=1,column=0,columnspan=2,sticky='w',pady=(0,12))
            self.enabled.configure(state='disabled' if isinstance(value,Dynamic) else 'readonly')
            self.enabled.set(value.source if isinstance(value,Dynamic) else ('是' if value else '否'))
        self.listbox.delete(0,'end')
        for row in self.rows():
            if self.kind=='ssh':
                name=row.get('name');label=(name if isinstance(name,str) else '自动名称')+' · '+self.display('remote_address',row.get('remote_address'))
            else:label=self.display('mods',row.get('mods'))+' + '+self.display('key',row.get('key'))+' · '+self.display('action',row.get('action'))
            self.listbox.insert('end',label)
        self.add_button.configure(state='normal' if self.writable() else 'disabled')
        self.delete_button.configure(state='normal' if self.writable() and self.rows() else 'disabled')
        if self.rows():
            selected=min(max(selected,0),len(self.rows())-1);self.listbox.selection_set(selected);self.load(selected)
        else:self.load(None)
    def refresh_saved(self):
        # 新主表条目在重新解析时可能位于条件追加条目前，按内容保留选中项。
        def values(row):return {k:v for k,v in (row or {}).items() if not k.startswith('_') and v is not None}
        previous=values(self.current)
        selected=next((i for i,row in enumerate(self.rows()) if values(row)==previous),self.index or 0)
        self.refresh(selected)

    def load(self,index):
        self.index=index;self.current=self.rows()[index] if index is not None else None
        self.original_display={};self.touched.clear();details=[]
        for key,widget in self.widgets.items():
            value=self.current.get(key) if self.current is not None else None
            text=self.display(key,value) if self.current is not None else ''
            widget.configure(state='normal')
            if key=='action':widget.configure(values=([CUSTOM] if isinstance(value,Dynamic) else [])+CHOICES[key])
            widget.delete(0,'end');widget.insert(0,text)
            readonly=self.current is None or not self.writable() or (isinstance(value,Dynamic) and key!='action')
            widget.configure(state='disabled' if readonly else ('readonly' if key in CHOICES else 'normal'))
            self.original_display[key]=text
            if isinstance(value,Dynamic):details.append(LABELS[key]+'：'+value.source)
        self.details.configure(text='\n'.join(details))
    def dirty_form(self):return self.current is not None and (bool(self.touched) or any(w.get()!=self.original_display[k] for k,w in self.widgets.items()))
    def flush(self):
        if not self.writable() or self.current is None:return
        row=deepcopy(self.current)
        for key,widget in self.widgets.items():
            text=widget.get()
            if text==self.original_display[key] and key not in self.touched:continue
            if key=='action' and text==CUSTOM:continue
            row[key]=BOOL[text] if key=='connect_automatically' else (text if text else None)
        trial=deepcopy(self.session.model);trial['rows'][self.index]=row
        self.session.document.build(trial);self.session.model=trial;self.load(self.index)
        self.app.update_status()
    def set_enabled(self,event=None):
        if self.session and not isinstance(self.session.model['enabled'],Dynamic):
            self.session.model['enabled']=BOOL[self.enabled.get()];self.app.update_status()
    def select(self,event=None):
        selected=self.listbox.curselection()
        if not selected or selected[0]==self.index:return
        try:self.flush();self.load(selected[0])
        except (ConfigError,OSError,ValueError) as e:
            self.listbox.selection_clear(0,'end')
            if self.index is not None:self.listbox.selection_set(self.index)
            self.app.error(e)
    def add(self):
        if not self.writable():return
        try:
            self.flush()
            if self.kind=='ssh':
                names={r.get('name') for r in self.rows()};n=1
                while f'服务器 {n}' in names:n+=1
                row={'name':f'服务器 {n}','remote_address':'example.com:22','username':None,'multiplexing':'None','connect_automatically':False}
            else:
                row={'key':'','mods':'NONE','action':'打开启动菜单'}
            self.rows().append(row);self.refresh(len(self.rows())-1);self.app.update_status()
        except (ConfigError,OSError,ValueError) as e:self.app.error(e)
    def delete(self):
        if self.index is None or not self.writable():return
        if not messagebox.askyesno('删除条目','删除选中的条目？确认保存后才修改文件。',parent=self):return
        index=self.index;self.rows().pop(index);self.refresh(max(0,index-1));self.app.update_status()
