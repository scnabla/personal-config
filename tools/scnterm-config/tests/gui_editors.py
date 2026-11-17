"""窗口回归：明确值、空框提示、多文件编辑与独立保存。仅使用副本。"""
import json
import shutil
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scnterm_config.app import Application
from scnterm_config.lua_document import LuaDocument
from scnterm_config.module_document import ModuleDocument
if sys.platform=='win32':
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
root=Path(__file__).resolve().parents[1];work=root/'.cache/gui-editors';work.mkdir(parents=True,exist_ok=True)
folder=work/'config';folder.mkdir(exist_ok=True)
for name in ['wezterm.lua','ssh.lua','keys.lua']:shutil.copy2(root/'examples'/name,folder/name)
serial=b"function M.apply(config)\nconfig.serial_ports={{name='COM8'}}\nconfig.serial_logging={}\nconfig.serial_highlighting={case_sensitive=true,rules={{foreground='#FFB52E'}}}\nend\n"
(folder/'serial.lua').write_bytes(serial)
main=(folder/'wezterm.lua').read_bytes();original_keys=(folder/'keys.lua').read_bytes()
app=Application();errors=[];app.error=lambda e:errors.append(str(e));result={}

def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)
def click(label):
    buttons=[w for w in descendants(app) if w.winfo_class()=='TButton' and w.cget('text')==label and w.winfo_ismapped()]
    assert buttons,label
    buttons[-1].invoke();app.update()
def field(editor,key,value):
    widget=editor.widgets[key]
    if widget.winfo_class()=='Text':widget.delete('1.0','end');widget.insert('1.0',value)
    elif widget.winfo_class()=='TCombobox':
        widget.set(value);widget.event_generate('<<ComboboxSelected>>')
    else:widget.delete(0,'end');widget.insert(0,value)
    app.update()
def save():
    click('预览并保存');assert not errors,errors;click('确认保存');assert not errors,errors
try:
    app.open_directory(folder);app.update();ports,logging,rules=app.editors
    assert len(app.tabs.tabs())==6
    assert ports.widgets['baud'].get()=='9600' and ports.widgets['port'].get()=='COM8'
    assert ports.widgets['flow_control'].get()=='Software' and ports.widgets['log_on_connect'].get()=='否'
    assert logging.widgets['max_file_size_mb'].get()=='100' and logging.widgets['timestamps'].get()=='是'
    assert logging.widgets['directory'].get()==str(folder.resolve())
    assert rules.widgets['case_sensitive'].get()=='是' and not hasattr(rules,'case')
    app.flush();assert app.session.preview()[0]==serial
    app.tabs.select(rules);app.update()
    for key in ('keywords','patterns'):
        widget=rules.widgets[key];assert widget.get('1.0','end-1c')=='' and widget.hint.winfo_ismapped()
        assert widget.hint.winfo_y()+widget.hint.winfo_height()<=widget.winfo_height(),key
    field(rules,'keywords','error');assert not rules.widgets['keywords'].hint.winfo_ismapped()
    field(rules,'keywords','');assert rules.widgets['keywords'].hint.winfo_ismapped()
    field(rules,'case_sensitive','是');save()
    parsed=LuaDocument((folder/'serial.lua').read_bytes());assert parsed.model['rules'][0]['case_sensitive'] is True
    # 改为否后与保留的共用 true 无关，新规则也明确为否。
    field(rules,'case_sensitive','否');rules.add();app.update()
    assert rules.widgets['case_sensitive'].get()=='否';save()
    parsed=LuaDocument((folder/'serial.lua').read_bytes());assert parsed.model['case_sensitive'] is True
    assert all(r['case_sensitive'] is False for r in parsed.model['rules'])
    assert b'\xe6\xa0\xbc\xe5\xbc\x8f\xe5\x8f\x82\xe8\x80\x83' not in (folder/'serial.lua').read_bytes()
    # 跨文件切换保留尚未保存的串口表单。
    field(ports,'baud','115200');before_serial=(folder/'serial.lua').read_bytes()
    ssh=app.module_editors['ssh'];app.tabs.select(ssh);app.update()
    assert len(ssh.rows())==1 and ssh.enabled.get()=='否'
    field(ssh,'remote_address','host.example:2222');field(ssh,'username','alice')
    ssh.enabled.set('是');ssh.enabled.event_generate('<<ComboboxSelected>>');ssh.add();app.update()
    field(ssh,'name','第二台');field(ssh,'remote_address','second.example:22');field(ssh,'username','bob');save()
    assert (folder/'serial.lua').read_bytes()==before_serial and ports.widgets['baud'].get()=='115200'
    assert (folder/'keys.lua').read_bytes()==original_keys
    saved_ssh=(folder/'ssh.lua').read_bytes();doc=ModuleDocument(saved_ssh,'ssh')
    assert len(doc.model['rows'])==2 and doc.model['enabled'] is True
    assert doc.model['rows'][0]['username']=='alice' and doc.model['rows'][1]['username']=='bob'
    # 修改按键、选择动作及新增绑定，保存只修改 keys.lua。
    keys=app.module_editors['keys'];app.tabs.select(keys);app.update()
    field(keys,'key','F10');field(keys,'mods','CTRL');field(keys,'action','复制')
    keys.add();app.update();field(keys,'key','F12');field(keys,'action','新建标签页');save()
    assert (folder/'ssh.lua').read_bytes()==saved_ssh and (folder/'serial.lua').read_bytes()==before_serial
    assert len(ModuleDocument((folder/'keys.lua').read_bytes(),'keys').model['rows'])==13
    assert keys.widgets['key'].get()=='F12'
    # 删除新增绑定后仍保留其他动作和函数。
    with patch('tkinter.messagebox.askyesno',return_value=True):keys.delete()
    save();remaining=ModuleDocument((folder/'keys.lua').read_bytes(),'keys').model['rows']
    assert len(remaining)==12 and not any(r.get('key')=='F12' for r in remaining)
    assert any(r.get('key')=='p' for r in remaining)
    # 恢复当前文件，不丢失串口输入。
    click('恢复备份');click('预览恢复内容');click('确认保存')
    assert len(ModuleDocument((folder/'keys.lua').read_bytes(),'keys').model['rows'])==13
    assert ports.widgets['baud'].get()=='115200'
    app.tabs.select(ports);app.update();save()
    assert LuaDocument((folder/'serial.lua').read_bytes()).model['ports'][0]['baud']==115200
    assert (folder/'wezterm.lua').read_bytes()==main
    # 真实页面截图仅来自测试进程，供布局检查。
    if sys.platform=='win32':
        from window_capture import capture
        for name,page in [('rules',rules),('ssh',ssh),('keys',keys)]:
            app.tabs.select(page);app.update();capture(app,work/(name+'.bmp'))
    # 缺少某个文件不阻止其他文件编辑，不自动创建。
    missing=work/'only-ssh';missing.mkdir(exist_ok=True);shutil.copy2(root/'examples/ssh.lua',missing/'ssh.lua')
    app.open_directory(missing);app.tabs.select(app.module_editors['ssh']);app.update()
    assert app.module_editors['ssh'].writable() and app.session is None
    assert not (missing/'keys.lua').exists() and not (missing/'serial.lua').exists()
    assert not errors,errors
    result={'passed':True,'checks':['actual values without rewriting omitted fields','gray hints excluded from input','independent case sensitivity','SSH multiple servers','shortcut action add edit delete','per-file save and restore','cross-tab pending inputs','main Lua unchanged','missing files']}
except Exception as e:
    result={'passed':False,'error':repr(e),'errors':errors};raise
finally:
    (work/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');app.destroy()
