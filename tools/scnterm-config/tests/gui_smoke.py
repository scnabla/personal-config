"""在 Windows 独立桌面执行真实 Tk 控件操作，不使用全局输入。"""
import hashlib
import json
import shutil
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scnterm_config.app import Application
from scnterm_config.lua_document import LuaDocument

if sys.platform=='win32':
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
root=Path(__file__).resolve().parents[1]
work=root/'.cache/gui-smoke';work.mkdir(parents=True,exist_ok=True)
folder=work/'config';folder.mkdir(exist_ok=True)
for name in ['serial.lua','wezterm.lua']:shutil.copy2(root/'examples'/name,folder/name)
for name in ['ssh.lua','keys.lua']:(folder/name).write_text('-- readonly\nreturn {}\n',encoding='utf-8')
unchanged={name:(folder/name).read_bytes() for name in ['wezterm.lua','ssh.lua','keys.lua']}
original=(folder/'serial.lua').read_bytes()
app=Application();errors=[];app.error=lambda e:errors.append(str(e))
result={}

def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)
def click(label):
    buttons=[w for w in descendants(app) if w.winfo_class()=='TButton' and w.cget('text')==label]
    assert buttons,label
    button=buttons[-1];assert button.winfo_ismapped(),label
    top=button.winfo_toplevel()
    assert button.winfo_rooty()+button.winfo_height()<=top.winfo_rooty()+top.winfo_height(),label
    button.invoke();app.update()
def set_field(editor,key,value):
    widget=editor.widgets[key]
    if widget.winfo_class()=='Text':widget.delete('1.0','end');widget.insert('1.0',value)
    elif widget.winfo_class()=='TCombobox':widget.set(value)
    else:widget.delete(0,'end');widget.insert(0,value)
try:
    app.open_directory(folder);app.update()
    assert not errors,errors
    ports,logging,rules=app.editors
    set_field(ports,'baud','921600');ports.apply();app.update()
    ports.add();set_field(ports,'name','第二设备');set_field(ports,'port','COM9');ports.apply()
    set_field(logging,'max_file_size_mb','25');set_field(logging,'directory','logs');logging.apply()
    rules.add();set_field(rules,'keywords','测试错误\n失败');set_field(rules,'patterns',r'\berror\b');rules.apply()
    assert not errors,errors
    app.preview_save();app.update();click('确认保存')
    assert not errors,errors
    doc=LuaDocument((folder/'serial.lua').read_bytes())
    assert doc.model['ports'][0]['baud']==921600 and len(doc.model['ports'])==2
    assert doc.model['logging']['max_file_size_mb']==25
    assert doc.model['rules'][-1]['patterns']==[r'\berror\b']
    assert all((folder/n).read_bytes()==b for n,b in unchanged.items())
    assert str(app.source.cget('state'))=='disabled'
    assert app.source.get('1.0','end-1c')==(folder/'wezterm.lua').read_text(encoding='utf-8')
    assert app.status.winfo_ismapped() and app.status.winfo_height()>10
    # 原生窗口和控件实际创建，记录布局供复查。
    app.tabs.select(0);app.update()
    if sys.platform=='win32':
        from window_capture import capture
        capture(app,work/'window.bmp')
    result['window']={'title':app.title(),'width':app.winfo_width(),'height':app.winfo_height(),'tabs':[app.tabs.tab(i,'text') for i in range(4)]}
    before=(folder/'serial.lua').read_bytes()
    set_field(ports,'baud','bad');ports.apply();assert errors;errors.clear()
    assert (folder/'serial.lua').read_bytes()==before
    set_field(ports,'baud','921600');ports.apply()
    app.restore_dialog();app.update();click('预览恢复内容');click('确认保存')
    assert not errors,errors
    assert (folder/'serial.lua').read_bytes()==original
    # 删除通过真实按钮回调，确认仅作用于配置副本。
    with patch('tkinter.messagebox.askyesno',return_value=True):ports.delete()
    app.preview_save();app.update();click('确认保存')
    assert not errors,errors
    assert not LuaDocument((folder/'serial.lua').read_bytes()).model['ports']
    # 外部改动后，确认保存必须失败。
    ports.add();ports.apply()
    app.preview_save();app.update()
    external=(folder/'serial.lua').read_bytes()+b'\n-- external edit\n';(folder/'serial.lua').write_bytes(external)
    click('确认保存');assert errors and '其他程序修改' in errors[-1];errors.clear()
    assert (folder/'serial.lua').read_bytes()==external
    result.update(passed=True,checks=['Windows Tk window','connection add edit delete','logging fields','highlight keywords and regex','diff confirmation','backup restore','invalid input','read-only files','external edit protection'])
except Exception as e:
    result.update(passed=False,error=repr(e),errors=errors)
    raise
finally:
    (work/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    app.destroy()
