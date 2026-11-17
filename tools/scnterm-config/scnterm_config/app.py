"""Windows 独立配置窗口；界面不执行 Lua，不打开串口设备。"""
from copy import deepcopy
from pathlib import Path
import argparse
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from .lua_document import ConfigError, Dynamic, SCHEMAS
from .storage import ConfigSession
from .serial_values import effective_value
from .module_editor import ModuleEditor
from .hint_text import HintText, KEYWORDS_HINT, PATTERNS_HINT

LABELS={'name':'连接名称','port':'端口','baud':'波特率','data_bits':'数据位','parity':'校验位',
        'stop_bits':'停止位','flow_control':'流控','log_on_connect':'连接时记录日志',
        'directory':'日志目录','max_file_size_mb':'单个文件大小（MB）','timestamps':'接收时间戳',
        'foreground':'文字颜色','keywords':'关键词','patterns':'正则表达式',
        'case_sensitive':'区分大小写'}
OPTIONS={'data_bits':['5','6','7','8'],'stop_bits':['1','2'],
         'parity':['None','Odd','Even'],'flow_control':['None','Software','Hardware']}
BOOL={'是':True,'否':False}

class Editor(ttk.Frame):
    def __init__(self,app,parent,section,kind):
        super().__init__(parent,padding=16);self.app=app;self.section=section;self.kind=kind
        self.index=None;self.current=None;self.widgets={};self.original_display={};self.explicit_fields=set()
        self.columnconfigure(1,weight=1);self.rowconfigure(1,weight=1)
        self.notice=ttk.Label(self,text='',wraplength=820);self.notice.grid(row=0,column=0,columnspan=2,sticky='w',pady=(0,12))
        if section!='logging':
            left=ttk.Frame(self);left.grid(row=1,column=0,sticky='ns',padx=(0,16))
            self.listbox=tk.Listbox(left,width=28,exportselection=False,activestyle='none',bd=0,
                highlightthickness=1,highlightbackground='#CBD5E1',selectbackground='#FFB52E',selectforeground='#172033',font=('Segoe UI',10))
            self.listbox.pack(fill='both',expand=True);self.listbox.bind('<<ListboxSelect>>',self.select)
            actions=ttk.Frame(left);actions.pack(fill='x',pady=(10,0))
            self.add_button=ttk.Button(actions,text='新增连接' if section=='ports' else '新增规则',command=self.add);self.add_button.pack(side='left')
            self.delete_button=ttk.Button(actions,text='删除',command=self.delete);self.delete_button.pack(side='left',padx=6)
        holder=ttk.Frame(self);holder.grid(row=1,column=1,sticky='nsew');holder.rowconfigure(0,weight=1);holder.columnconfigure(0,weight=1)
        canvas=tk.Canvas(holder,highlightthickness=0,background='#F5F7FA');scroll=ttk.Scrollbar(holder,orient='vertical',command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set);canvas.grid(row=0,column=0,sticky='nsew');scroll.grid(row=0,column=1,sticky='ns')
        self.form=ttk.Frame(canvas,padding=(0,0,16,8));window=canvas.create_window((0,0),window=self.form,anchor='nw')
        canvas.bind('<Configure>',lambda e:canvas.itemconfigure(window,width=e.width))
        self.form.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
        self.form.columnconfigure(1,weight=1)
        for row,(key,typ) in enumerate(SCHEMAS[kind].items()):
            ttk.Label(self.form,text=LABELS[key]).grid(row=row,column=0,sticky='nw',padx=(0,16),pady=7)
            if typ==list:
                widget=HintText(self.form,PATTERNS_HINT if key=='patterns' else KEYWORDS_HINT,height=8 if key=='patterns' else 5,wrap='none',font=('Consolas',10),bd=1,relief='solid',undo=True)
                widget.bind('<<InputChanged>>',lambda e:self.app.update_status())
            elif typ==bool:widget=ttk.Combobox(self.form,values=list(BOOL),state='readonly')
            elif key in OPTIONS:widget=ttk.Combobox(self.form,values=OPTIONS[key],state='readonly')
            else:widget=ttk.Entry(self.form)
            widget.grid(row=row,column=1,sticky='ew',pady=7);self.widgets[key]=widget
            widget.bind('<KeyRelease>',lambda e:self.app.update_status(),add='+')
            if isinstance(widget,ttk.Combobox):widget.bind('<<ComboboxSelected>>',lambda e,k=key:self.selected_value(k),add='+')
            if key=='foreground':ttk.Button(self.form,text='选色',command=self.choose_color).grid(row=row,column=2,padx=6)
            if key=='directory':ttk.Button(self.form,text='浏览',command=self.choose_directory).grid(row=row,column=2,padx=6)
        r=len(SCHEMAS[kind])
        hint={'ports':'连接参数在下次连接时生效。',
              'logging':'相对路径以主 Lua 所在目录为准；清空目录后恢复为主 Lua 所在目录。设置用于下一次开始记录。',
              'rules':'只改变匹配文字的颜色。靠前的规则优先；正则按原样填写，无需增加 Lua 引号或反斜杠。'}[section]
        ttk.Label(self.form,text=hint,wraplength=540,foreground='#526078').grid(row=r,column=0,columnspan=3,sticky='w',pady=12)

    def rows(self):return self.app.session.model[self.section] if self.app.session else []
    def writable(self):return self.app.session and (self.section in self.app.session.document.sections or self.section in self.app.session.document.creatable)
    def refresh(self,selected=0):
        self.current=None;self.index=None
        reason=self.app.session.document.reasons.get(self.section,'') if self.app.session else ('未找到 serial.lua' if self.app.directory else '打开配置目录后开始编辑')
        self.notice.configure(text=reason or ('保存前可预览修改。'))
        if self.section!='logging':
            self.listbox.delete(0,'end')
            for n,row in enumerate(self.rows()):
                label=f"{row.get('name','未命名')} · {row.get('port') or row.get('name','未填写端口')}" if self.section=='ports' else f"{n+1}. {row.get('foreground','未设置颜色')} · "+', '.join(str(x) for x in (row.get('keywords') if isinstance(row.get('keywords'),list) else []))
                self.listbox.insert('end',label[:100])
            self.add_button.configure(state='normal' if self.writable() else 'disabled')
            self.delete_button.configure(state='normal' if self.writable() and self.rows() else 'disabled')
            if self.rows():
                selected=max(0,min(selected,len(self.rows())-1));self.listbox.selection_set(selected);self.load(selected)
            else:self.load(None)
        else:self.load(0 if self.writable() else None)

    def selected_value(self,key):
        self.explicit_fields.add(key);self.app.update_status()

    def actual_value(self,key,value):
        return effective_value(self.section,key,value,self.current or {},
                               self.app.session.model if self.app.session else {},self.app.directory)

    def display(self,key,value):
        if self.current is None:return ''
        value=self.actual_value(key,value)
        if isinstance(value,Dynamic):return value.source
        typ=SCHEMAS[self.kind][key]
        if typ==bool:return next(k for k,v in BOOL.items() if type(v)==type(value) and v==value)
        if typ==list:return '\n'.join(value or [])
        return '' if value is None else str(value)

    def put(self,key,value,readonly=False):
        widget=self.widgets[key];text=self.display(key,value)
        widget.configure(state='normal')
        if isinstance(widget,tk.Text):widget.delete('1.0','end');widget.insert('1.0',text)
        else:widget.delete(0,'end');widget.insert(0,text)
        widget.configure(state='disabled' if readonly else ('readonly' if isinstance(widget,ttk.Combobox) else 'normal'))
        if isinstance(widget,HintText):widget.sync_hint()
        self.original_display[key]=text

    def load(self,index):
        self.index=index;self.current=None;self.original_display={};self.explicit_fields.clear()
        if index is not None:self.current=self.rows() if self.section=='logging' else self.rows()[index]
        for key in self.widgets:
            value=self.current.get(key) if self.current is not None else None
            self.put(key,value,self.current is None or isinstance(self.actual_value(key,value),Dynamic) or not self.writable())
        if self.current is not None and any(isinstance(v,Dynamic) for v in self.current.values()):self.notice.configure(text='由代码计算的字段只读，其余字段可以修改。')

    def read_widget(self,key):
        widget=self.widgets[key]
        return widget.get('1.0','end-1c') if isinstance(widget,tk.Text) else widget.get()

    def dirty_form(self):return self.current is not None and (bool(self.explicit_fields) or any(self.read_widget(k)!=v for k,v in self.original_display.items()))

    def flush(self):
        if self.current is None or not self.writable():return
        updated=deepcopy(self.current)
        for key in self.widgets:
            text=self.read_widget(key)
            if text==self.original_display.get(key) and key not in self.explicit_fields:continue
            if isinstance(self.actual_value(key,self.current.get(key)),Dynamic):raise ConfigError('由代码计算的字段不能修改')
            typ=SCHEMAS[self.kind][key]
            if typ==bool:value=BOOL[text]
            elif typ==list:value=text.splitlines() if text else []
            elif typ==int:
                if re_integer(text):value=int(text)
                else:raise ConfigError(LABELS[key]+'必须填写整数')
            else:
                if text=='' and key in ('name','port'):raise ConfigError(LABELS[key]+'不能为空')
                value=None if text=='' else text
            updated[key]=value
        trial=deepcopy(self.app.session.model)
        if self.section=='logging':trial[self.section]=updated
        else:trial[self.section][self.index]=updated
        self.app.session.document.build(trial)
        self.app.session.model=trial
        self.current=trial[self.section] if self.section=='logging' else trial[self.section][self.index]
        self.load(self.index)
        self.app.update_status()

    def select(self,event=None):
        selected=self.listbox.curselection()
        if not selected:return
        index=selected[0]
        if index==self.index:return
        try:self.flush();self.load(index)
        except (ConfigError,OSError,ValueError) as e:
            self.listbox.selection_clear(0,'end')
            if self.index is not None:self.listbox.selection_set(self.index)
            self.app.error(e)

    def add(self):
        try:
            self.flush()
            if not self.writable():return
            if self.section=='ports':
                existing={str(x.get('name')) for x in self.rows()};n=1
                while f'串口 {n}' in existing:n+=1
                row={'name':f'串口 {n}','port':f'COM{n}','baud':115200,'data_bits':8,'parity':'None','stop_bits':1,'flow_control':'None','log_on_connect':False}
            else:row={'foreground':'#FFB52E','keywords':[],'patterns':[],'case_sensitive':False}
            self.rows().append(row);self.refresh(len(self.rows())-1);self.app.update_status()
        except (ConfigError,OSError,ValueError) as e:self.app.error(e)

    def delete(self):
        if self.index is None:return
        try:
            if self.current.get('_protected'):raise ConfigError('条目包含动态代码，不能删除')
            if not messagebox.askyesno('删除条目','删除选中的条目？修改将在预览并保存后写入文件。',parent=self):return
            index=self.index;self.rows().pop(index);self.refresh(max(0,index-1));self.app.update_status()
        except (ConfigError,OSError,ValueError) as e:self.app.error(e)

    def choose_color(self):
        if self.current is None or isinstance(self.current.get('foreground'),Dynamic):return
        chosen=colorchooser.askcolor(parent=self,title='选择高亮颜色')[1]
        if chosen:self.widgets['foreground'].delete(0,'end');self.widgets['foreground'].insert(0,chosen.upper())

    def choose_directory(self):
        if self.current is None or isinstance(self.current.get('directory'),Dynamic):return
        chosen=filedialog.askdirectory(parent=self,title='选择日志目录')
        if chosen:self.widgets['directory'].delete(0,'end');self.widgets['directory'].insert(0,chosen)



def re_integer(text):return text.isascii() and text.isdigit()


class Application(tk.Tk):
    def __init__(self,directory=None):
        super().__init__();self.title('ScnTerm 配置');self.geometry('1120x780');self.minsize(940,640)
        self.session=None;self.directory=None;self.editors=[];self.module_editors={}
        icon=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1]))/'assets/scnterm.ico'
        if sys.platform=='win32' and icon.is_file():self.iconbitmap(str(icon))
        style=ttk.Style(self);style.theme_use('clam');style.configure('.',font=('Microsoft YaHei UI',10))
        style.configure('TFrame',background='#F5F7FA');style.configure('TLabel',background='#F5F7FA',foreground='#172033')
        style.configure('TButton',padding=(12,7));style.configure('Accent.TButton',background='#FFB52E',foreground='#172033')
        style.map('Accent.TButton',background=[('active','#FFD07A')]);style.configure('TNotebook.Tab',padding=(18,10))
        self.configure(background='#F5F7FA')
        toolbar=ttk.Frame(self,padding=(18,14));toolbar.pack(fill='x')
        ttk.Label(toolbar,text='ScnTerm 配置',font=('Microsoft YaHei UI',17,'bold')).pack(side='left',padx=(0,20))
        ttk.Button(toolbar,text='打开配置目录',command=self.choose).pack(side='left')
        ttk.Button(toolbar,text='重新读取',command=self.reopen).pack(side='left',padx=8)
        self.save_button=ttk.Button(toolbar,text='预览并保存',style='Accent.TButton',command=self.preview_save);self.save_button.pack(side='right')
        ttk.Button(toolbar,text='恢复备份',command=self.restore_dialog).pack(side='right',padx=8)
        self.location=ttk.Label(self,text='选择 Lua 配置所在目录',padding=(20,0,20,12));self.location.pack(fill='x')
        self.tabs=ttk.Notebook(self);self.tabs.pack(fill='both',expand=True,padx=18,pady=(0,12))
        for section,kind,label in [('ports','ports','串口连接'),('logging','logging','日志'),('rules','rule','高亮规则')]:
            editor=Editor(self,self.tabs,section,kind);self.editors.append(editor);self.tabs.add(editor,text=label)
        for kind,label in [('ssh','SSH · ssh.lua'),('keys','快捷键 · keys.lua')]:
            editor=ModuleEditor(self,self.tabs,kind);self.module_editors[kind]=editor;self.tabs.add(editor,text=label)
        readonly=ttk.Frame(self.tabs,padding=16);self.tabs.add(readonly,text='其他配置 · 只读')
        self.file_choice=ttk.Combobox(readonly,state='readonly');self.file_choice.pack(fill='x',pady=(0,10));self.file_choice.bind('<<ComboboxSelected>>',lambda e:self.show_readonly())
        holder=ttk.Frame(readonly);holder.pack(fill='both',expand=True)
        self.source=tk.Text(holder,wrap='none',state='disabled',font=('Consolas',10),bg='#FFFFFF',fg='#172033',bd=1,relief='solid')
        scroll=ttk.Scrollbar(holder,command=self.source.yview);self.source.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y')
        horizontal=ttk.Scrollbar(holder,orient='horizontal',command=self.source.xview)
        self.source.configure(xscrollcommand=horizontal.set);horizontal.pack(side='bottom',fill='x')
        self.source.pack(fill='both',expand=True)
        self.status=ttk.Label(self,text='未打开配置',padding=(20,0,20,12));self.status.pack(side='bottom',fill='x',before=self.tabs)
        self.protocol('WM_DELETE_WINDOW',self.close)
        self.bind('<Control-s>',lambda e:self.preview_save())
        self.tabs.bind('<<NotebookTabChanged>>',lambda e:self.update_status())
        for editor in self.editors:editor.refresh()
        self.save_button.configure(state='disabled')
        if directory:self.after(50,lambda:self.open_directory(Path(directory)))

    def error(self,error):messagebox.showerror('未完成操作',str(error),parent=self)
    def active_session(self):
        selected=self.tabs.select()
        for editor in self.module_editors.values():
            if selected==str(editor):return editor.session
        return self.session if any(selected==str(e) for e in self.editors) else None
    def has_changes(self):
        serial=self.session is not None and (self.session.model!=self.session.document.original or any(e.dirty_form() for e in self.editors))
        return serial or any(e.session and (e.session.model!=e.session.document.original or e.dirty_form()) for e in self.module_editors.values())
    def discard_ok(self):return not self.has_changes() or messagebox.askyesno('尚未保存','放弃尚未保存的修改？',parent=self)
    def choose(self):
        if not self.discard_ok():return
        folder=filedialog.askdirectory(parent=self,title='打开 ScnTerm 配置目录',initialdir=str(Path.home()/'.config/wezterm'))
        if folder:self.open_directory(Path(folder))
    def reopen(self):
        if self.directory and self.discard_ok():self.open_directory(self.directory)
    def open_directory(self,folder):
        folder=Path(folder).resolve()
        if not folder.is_dir():self.error(ConfigError('配置目录不存在'));return
        sessions={};errors={}
        for name in ('serial','ssh','keys'):
            try:sessions[name]=ConfigSession(folder/(name+'.lua'))
            except (OSError,ConfigError,ValueError) as e:
                sessions[name]=None;errors[name]=('未找到 '+name+'.lua') if not (folder/(name+'.lua')).exists() else str(e)
        self.session=sessions['serial'];self.directory=folder;self.location.configure(text=str(folder))
        for editor in self.editors:
            editor.refresh()
            if 'serial' in errors:editor.notice.configure(text=errors['serial'])
        for kind,editor in self.module_editors.items():
            editor.session=sessions[kind];editor.refresh(reason=errors.get(kind))
        files=sorted(p.name for p in folder.glob('*.lua') if p.is_file() and p.name not in ('serial.lua','ssh.lua','keys.lua'))
        self.file_choice.configure(values=files);self.file_choice.set('wezterm.lua' if 'wezterm.lua' in files else files[0] if files else '')
        self.source.configure(state='normal');self.source.delete('1.0','end');self.source.configure(state='disabled')
        if files:self.show_readonly()
        self.update_status()
    def show_readonly(self):
        try:
            name=self.file_choice.get()
            if Path(name).name!=name or not name.endswith('.lua'):return
            path=self.directory/name
            if path.stat().st_size>LuaDocumentLimit:raise ConfigError('文件超过 2 MB，无法预览')
            text=path.read_text(encoding='utf-8-sig')
            self.source.configure(state='normal');self.source.delete('1.0','end');self.source.insert('1.0',text);self.source.configure(state='disabled')
        except (OSError,UnicodeError,ConfigError) as e:self.error(e)
    def update_status(self):
        if not hasattr(self,'status'):return
        self.save_button.configure(state='normal' if self.active_session() else 'disabled')
        self.status.configure(text='有待保存的修改' if self.has_changes() else ('配置已读取' if self.directory else '未打开配置'))
    def flush(self):
        for editor in self.editors:editor.flush()
    def refresh_session(self,session):
        if session is self.session:
            for editor in self.editors:editor.refresh(editor.index or 0)
        else:
            for editor in self.module_editors.values():
                if editor.session is session:editor.refresh_saved()

    def diff_dialog(self,diff,save,title='确认修改',session=None):
        session=session or self.active_session()
        filename=session.filename
        dialog=tk.Toplevel(self);dialog.title(title);dialog.geometry('940x650');dialog.transient(self);dialog.grab_set()
        ttk.Label(dialog,text=('仅恢复 '+filename+'；检测到外部修改时停止恢复。' if title=='确认恢复' else '仅修改 '+filename+'。保存前自动备份原文件。'),padding=12).pack(fill='x')
        holder=ttk.Frame(dialog);holder.pack(fill='both',expand=True,padx=12)
        text=tk.Text(holder,wrap='none',font=('Consolas',10))
        vertical=ttk.Scrollbar(holder,command=text.yview);vertical.pack(side='right',fill='y')
        horizontal=ttk.Scrollbar(holder,orient='horizontal',command=text.xview);horizontal.pack(side='bottom',fill='x')
        text.configure(yscrollcommand=vertical.set,xscrollcommand=horizontal.set);text.pack(fill='both',expand=True)
        text.tag_configure('add',foreground='#126D43');text.tag_configure('remove',foreground='#B42336')
        for line in diff.splitlines(True):text.insert('end',line,'add' if line.startswith('+') else 'remove' if line.startswith('-') else '')
        text.configure(state='disabled')
        actions=ttk.Frame(dialog,padding=12);actions.pack(side='bottom',fill='x',before=holder)
        ttk.Button(actions,text='返回编辑',command=dialog.destroy).pack(side='right',padx=8)
        def confirm():
            try:
                save();dialog.destroy()
                self.refresh_session(session);self.update_status()
                if not self.has_changes():self.status.configure(text='已保存 '+filename)
            except (OSError,ConfigError,ValueError) as e:self.error(e)
        ttk.Button(actions,text='确认保存',style='Accent.TButton',command=confirm).pack(side='right')
    def preview_save(self):
        session=self.active_session()
        if not session:return
        try:
            if session is self.session:self.flush()
            else:
                for editor in self.module_editors.values():
                    if editor.session is session:editor.flush()
            candidate,diff=session.preview()
            if not diff:messagebox.showinfo('无需保存','当前文件没有变化。',parent=self);return
            self.diff_dialog(diff,lambda:session.save(candidate),session=session)
        except (OSError,ConfigError,ValueError) as e:self.error(e)
    def restore_dialog(self):
        session=self.active_session()
        if not session:return
        dirty=(session.model!=session.document.original or any(e.dirty_form() for e in self.editors)) if session is self.session else any(e.dirty_form() or e.session.model!=e.session.document.original for e in self.module_editors.values() if e.session is session)
        if dirty and not messagebox.askyesno('尚未保存','放弃 '+session.filename+' 中尚未保存的修改？',parent=self):return
        try:
            session.reload();self.refresh_session(session);backups=session.backups()
        except (OSError,ConfigError,ValueError) as e:self.error(e);return
        if not backups:messagebox.showinfo('恢复备份','当前文件没有备份。',parent=self);return
        dialog=tk.Toplevel(self);dialog.title('选择备份 · '+session.filename);dialog.geometry('650x340');dialog.transient(self);dialog.grab_set()
        listing=tk.Listbox(dialog,exportselection=False,font=('Consolas',10));listing.pack(fill='both',expand=True,padx=12,pady=12)
        for backup in backups:listing.insert('end',backup.parent.name)
        listing.selection_set(0)
        def choose():
            try:
                selected=listing.curselection()
                if not selected:return
                backup=backups[selected[0]];data,diff=session.restore_preview(backup)
                dialog.destroy();self.diff_dialog(diff,lambda:session.restore(backup,data),'确认恢复',session)
            except (OSError,ConfigError,ValueError) as e:self.error(e)
        ttk.Button(dialog,text='预览恢复内容',command=choose).pack(pady=(0,12))
    def close(self):
        if self.discard_ok():self.destroy()

LuaDocumentLimit=2*1024*1024

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config-dir');args=parser.parse_args()
    if sys.platform=='win32':
        import ctypes
        try:ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError,OSError):pass
    default=Path.home()/'.config/wezterm'
    directory=args.config_dir or (str(default) if any((default/name).is_file() for name in ('serial.lua','ssh.lua','keys.lua')) else None)
    app=Application(directory);app.mainloop()

if __name__=='__main__':main()
