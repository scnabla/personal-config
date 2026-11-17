"""SSH/快捷键独立文件的局部编辑与文件保护。"""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from scnterm_config.lua_document import ConfigError, Dynamic
from scnterm_config.module_document import ModuleDocument
from scnterm_config.storage import ConfigSession
from scnterm_config.serial_values import effective_value

SSH=b"local M={}\nlocal ssh_enabled=false\nlocal server={host='example.com',port='22',user='user'}\nfunction M.apply(config)\nconfig.ssh_domains={}\nif ssh_enabled then config.ssh_domains={{name='SSH: '..server.user,remote_address=server.host..':'..server.port,username=server.user,multiplexing='None',connect_automatically=false}} end\nend\nreturn M\n"
KEYS=b"local M={}\nfunction M.apply(config)\nconfig.keys={{key='F5',mods='NONE',action=M.custom}, -- keep\n{key='l',mods='ALT',action=wezterm.action.ShowLauncher}}\nif M.menu then table.insert(config.keys,{key='p',mods='ALT',action=M.menu}) end\nend\nM.shortcut_labels={['swap']='F5'}\nreturn M\n"

class ModuleTests(unittest.TestCase):
    def test_noop(self):
        for kind,data in [('ssh',SSH),('keys',KEYS)]:
            doc=ModuleDocument(data,kind);self.assertFalse(doc.reason);self.assertEqual(doc.build(doc.model),data)
    def test_legacy_server_fields_preserve_expressions(self):
        doc=ModuleDocument(SSH,'ssh');m=deepcopy(doc.model)
        self.assertEqual(m['rows'][0]['remote_address'],'example.com:22')
        m['enabled']=True;m['rows'][0]['remote_address']='host.example:2222';m['rows'][0]['username']='new-user'
        result=doc.build(m)
        self.assertIn(b"host='host.example',port='2222',user='new-user'",result)
        self.assertIn(b"remote_address=server.host..':'..server.port",result)
        self.assertIn(b'local ssh_enabled=true',result)
    def test_ssh_add_delete(self):
        doc=ModuleDocument(SSH,'ssh');m=deepcopy(doc.model)
        m['rows']=[{'name':'second','remote_address':'[::1]:22','username':'someone','multiplexing':'None','connect_automatically':False}]
        result=doc.build(m);parsed=ModuleDocument(result,'ssh')
        self.assertEqual(parsed.model['rows'][0]['name'],'second')
        self.assertIn(b"local server={host='example.com'",result)
    def test_key_changes_and_labels_preserve_action(self):
        doc=ModuleDocument(KEYS,'keys');m=deepcopy(doc.model);m['rows'][0]['key']='F6'
        result=doc.build(m)
        self.assertIn(b"key='F6',mods='NONE',action=M.custom",result)
        self.assertIn(b"['swap']='F6'",result);self.assertIn(b'-- keep',result)
    def test_insert_call_binding_edit_delete(self):
        doc=ModuleDocument(KEYS,'keys');m=deepcopy(doc.model);m['rows'][2]['key']='o'
        result=doc.build(m);self.assertIn(b"table.insert(config.keys,{key='o'",result)
        m['rows'].pop();result=doc.build(m);self.assertNotIn(b'table.insert',result)
    def test_key_action_replace_add_delete(self):
        doc=ModuleDocument(KEYS,'keys');m=deepcopy(doc.model)
        m['rows'][0]['action']='新建标签页'
        m['rows'].pop(1)
        m['rows'].append({'key':'F8','mods':'CTRL','action':'按数字交换窗格'})
        result=doc.build(m);parsed=ModuleDocument(result,'keys')
        self.assertEqual(len(parsed.model['rows']),3)
        self.assertIn(b"require('wezterm').action.SpawnTab",result)
    def test_duplicate_binding_and_bad_address(self):
        doc=ModuleDocument(KEYS,'keys');m=deepcopy(doc.model);m['rows'].append({'key':'F5','mods':'NONE','action':'复制'})
        with self.assertRaises(ConfigError):doc.build(m)
        doc=ModuleDocument(SSH,'ssh');m=deepcopy(doc.model);m['rows'][0]['remote_address']='host:99999'
        with self.assertRaises(ConfigError):doc.build(m)
    def test_dynamic_key_preserved(self):
        data=KEYS.replace(b"key='F5'",b'key=get_key()');doc=ModuleDocument(data,'keys');m=deepcopy(doc.model)
        m['rows'][0]['mods']='CTRL';self.assertIn(b'key=get_key()',doc.build(m))
        m['rows'][0]['key']='F5'
        with self.assertRaises(ConfigError):doc.build(m)
    def test_unsupported_lists_readonly(self):
        doc=ModuleDocument(b'config.keys=get_keys()','keys');self.assertTrue(doc.reason)
        m=deepcopy(doc.model);m['rows'].append({'key':'F5','mods':'NONE','action':'复制'})
        with self.assertRaises(ConfigError):doc.build(m)
    def test_bom_crlf_unchanged_regions(self):
        data=b'\xef\xbb\xbf'+KEYS.replace(b'\n',b'\r\n');doc=ModuleDocument(data,'keys');m=deepcopy(doc.model);m['rows'][1]['key']='x'
        self.assertEqual(doc.build(m),data.replace(b"key='l'",b"key='x'"))
    def test_file_save_backup_restore_and_conflict(self):
        for kind,source in [('ssh',SSH),('keys',KEYS)]:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/(kind+'.lua');path.write_bytes(source);session=ConfigSession(path)
                main=Path(tmp)/'wezterm.lua';main.write_bytes(b'-- untouched')
                field='username' if kind=='ssh' else 'key';session.model['rows'][0][field]='modified'
                candidate,diff=session.preview();self.assertIn(kind+'.lua',diff)
                backup=session.save(candidate);self.assertEqual(backup.name,kind+'.lua')
                original,_=session.restore_preview(backup);session.restore(backup,original)
                self.assertEqual(path.read_bytes(),source);self.assertEqual(main.read_bytes(),b'-- untouched')
                session.model['rows'][0][field]='other';candidate,_=session.preview();path.write_bytes(source+b'-- external')
                with self.assertRaises(ConfigError):session.save(candidate)
    def test_defaults_only_display(self):
        row={'name':'COM9'};model={'case_sensitive':True}
        self.assertEqual(effective_value('ports','port',None,row,model,None),'COM9')
        self.assertEqual(effective_value('ports','baud',None,row,model,None),9600)
        self.assertEqual(effective_value('ports','flow_control',None,row,model,None),'Software')
        self.assertEqual(effective_value('logging','timestamps',None,row,model,None),True)
        self.assertEqual(effective_value('rules','case_sensitive',None,row,model,None),True)
        self.assertEqual(row,{'name':'COM9'})
