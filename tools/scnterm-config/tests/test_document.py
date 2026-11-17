"""验证实际文件行为，测试配置不依赖终端源码。"""
import tempfile
import unittest
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
from scnterm_config.lua_document import LuaDocument, ConfigError, Dynamic, lua
from scnterm_config.storage import ConfigSession

SAMPLE=b'''-- keep this comment\nlocal M = {}\nfunction M.apply(config)\n  local serial_ports = {\n    { name = 'board', port = 'COM3', baud = 1500000, custom = 'keep' }, -- port comment\n  }\n  config.serial_ports = {}\n  config.serial_ports = serial_ports\n  config.serial_logging = { max_file_size_mb = 100, timestamps = true }\n  config.serial_highlighting = { rules = { {foreground='#FFB52E', patterns={[[\\berror\\b]]},keywords={'warn'}} } }\n  config.font_size = 14\nend\nreturn M\n'''

class DocumentTests(unittest.TestCase):
    def setUp(self):self.doc=LuaDocument(SAMPLE);self.model=deepcopy(self.doc.model)
    def build(self):return self.doc.build(self.model)
    def test_noop_is_byte_identical(self):self.assertEqual(self.build(),SAMPLE)
    def test_single_scalar_only(self):
        self.model['ports'][0]['baud']=115200
        self.assertEqual(self.build(),SAMPLE.replace(b'1500000',b'115200'))
    def test_bom_crlf_and_chinese(self):
        raw=b'\xef\xbb\xbf'+SAMPLE.replace(b'\n',b'\r\n').replace(b'board','设备'.encode())
        d=LuaDocument(raw);m=deepcopy(d.model);m['ports'][0]['baud']=9600
        self.assertEqual(d.build(m),raw.replace(b'1500000',b'9600'))
    def test_add_connection(self):
        self.model['ports'].append({'name':'second','port':'COM4','baud':115200})
        result=self.build();d=LuaDocument(result)
        self.assertEqual(len(d.model['ports']),2);self.assertIn(b"custom = 'keep'",result)
    def test_remove_connection_keeps_comments(self):
        self.model['ports']=[];result=self.build()
        self.assertEqual(LuaDocument(result).model['ports'],[]);self.assertIn(b'-- port comment',result)
    def test_replace_only_row_without_trailing_comma(self):
        d=LuaDocument(b"config.serial_ports={{name='one',port='COM1'}}")
        m=deepcopy(d.model);m['ports']=[{'name':'two','port':'COM2'}]
        self.assertEqual(LuaDocument(d.build(m)).model['ports'][0]['name'],'two')
    def test_dynamic_value_preserved(self):
        d=LuaDocument(SAMPLE.replace(b'1500000',b'get_baud()'));m=deepcopy(d.model)
        m['logging']['timestamps']=False
        self.assertIn(b'baud = get_baud()',d.build(m))
        m['ports'][0]['baud']=115200
        with self.assertRaises(ConfigError):d.build(m)
    def test_dynamic_row_cannot_be_deleted(self):
        d=LuaDocument(SAMPLE.replace(b'1500000',b'get_baud()'));m=deepcopy(d.model);m['ports']=[]
        with self.assertRaises(ConfigError):d.build(m)
    def test_dynamic_sections_readonly(self):
        d=LuaDocument(b'config.serial_ports=get_ports()');m=deepcopy(d.model);m['ports']=[{'name':'x'}]
        with self.assertRaises(ConfigError):d.build(m)
    def test_ambiguous_assignments_readonly(self):
        d=LuaDocument(SAMPLE.replace(b'return M', b'config.serial_logging={timestamps=false}\nreturn M'))
        self.assertIn('logging',d.reasons)
    def test_syntax_failure(self):
        with self.assertRaises(ConfigError):LuaDocument(b'config.serial_ports = {')
    def test_unknown_fields_and_unrelated_code_preserved(self):
        self.model['ports'][0]['port']='COM9';s=self.build()
        self.assertIn(b"custom = 'keep'",s);self.assertIn(b'config.font_size = 14',s)
    def test_unknown_input_rejected(self):
        self.model['logging']['font_size']=20
        with self.assertRaises(ConfigError):self.build()
    def test_regex_backslash_unicode_and_quotes(self):
        value=r"\b(error|失败)\b'\path"
        self.model['rules'][0]['patterns']=[value]
        self.assertEqual(LuaDocument(self.build()).model['rules'][0]['patterns'],[value])
    def test_keyword_comments_preserved(self):
        raw=SAMPLE.replace(b"keywords={'warn'}",b"keywords={'warn', -- important\n'error'}")
        d=LuaDocument(raw);m=deepcopy(d.model);m['rules'][0]['keywords']=['WARN','error','失败']
        s=d.build(m);self.assertIn(b'-- important',s)
        self.assertEqual(LuaDocument(s).model['rules'][0]['keywords'],['WARN','error','失败'])
    def test_remove_and_add_rules(self):
        self.model['rules']=[{'foreground':'#AABBCC','keywords':['新']}]
        d=LuaDocument(self.build());self.assertEqual(d.model['rules'][0]['keywords'],['新'])
    def test_add_directory_without_reformat(self):
        self.model['logging']['directory']='D:/日志'
        s=self.build();self.assertIn(b'max_file_size_mb = 100, timestamps = true',s)
        self.assertEqual(LuaDocument(s).model['logging']['directory'],'D:/日志')
    def test_missing_sections_can_be_added_to_apply(self):
        d=LuaDocument(b'local M={}\nfunction M.apply(config)\nend\nreturn M\n');m=deepcopy(d.model)
        m['ports']=[{'name':'board','port':'COM1'}];m['logging']={'timestamps':True}
        m['rules']=[{'foreground':'#FF0000','patterns':['error']}]
        result=d.build(m);self.assertEqual(set(LuaDocument(result).sections),{'ports','logging','rules'})
    def test_invalid_fields(self):
        for key,value in [('baud',0),('baud',True),('data_bits',9),('stop_bits',3),('parity','bad'),('name',''),('port','')]:
            with self.subTest(key=key):
                m=deepcopy(self.model);m['ports'][0][key]=value
                with self.assertRaises(ConfigError):self.doc.build(m)
    def test_duplicate_names(self):
        self.model['ports'].append({'name':'board','port':'COM9'})
        with self.assertRaises(ConfigError):self.build()
    def test_invalid_color(self):
        self.model['rules'][0]['foreground']='orange?'
        with self.assertRaises(ConfigError):self.build()
    def test_dynamic_array_is_readonly(self):
        d=LuaDocument(SAMPLE.replace(b"keywords={'warn'}",b'keywords=load_keywords()'))
        m=deepcopy(d.model);m['rules'][0]['keywords']=['x']
        with self.assertRaises(ConfigError):d.build(m)
    def test_unknown_function_is_readonly(self):
        d=LuaDocument(b"function unrelated(config) config.serial_ports={{name='x'}} end")
        self.assertIn('ports',d.reasons)
    def test_alias_other_scope_is_readonly(self):
        d=LuaDocument(b"function other() local serial_ports={{name='x'}} end function M.apply(config) config.serial_ports=serial_ports end")
        self.assertIn('ports',d.reasons)
    def test_alias_reassigned_is_readonly(self):
        d=LuaDocument(SAMPLE.replace(b'config.serial_ports = serial_ports',b'serial_ports = other_ports()\n config.serial_ports = serial_ports'))
        self.assertIn('ports',d.reasons)
    def test_unsupported_type_preserved_while_editing(self):
        raw=SAMPLE.replace(b'timestamps = true',b"timestamps = 'custom'")
        d=LuaDocument(raw);m=deepcopy(d.model);m['ports'][0]['baud']=9600
        self.assertEqual(d.build(m),raw.replace(b'1500000',b'9600'))
    def test_terminal_reserved_name_rejected(self):
        self.model['ports'][0]['name']='local'
        with self.assertRaises(ConfigError):self.build()
    def test_new_connection_follows_table_indentation(self):
        self.model['ports'].append({'name':'other','port':'COM9'})
        text=self.build().decode()
        self.assertIn("\n    {\n      name = 'other',\n      port = 'COM9',\n    },",text)
        self.assertIn("{ name = 'board', port = 'COM3', baud = 1500000, custom = 'keep' }, -- port comment",text)
    def test_no_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'must-not-exist'
            s=("os.execute("+lua("touch "+str(path))+")\n").encode()+SAMPLE
            LuaDocument(s);self.assertFalse(path.exists())

class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'serial.lua';self.path.write_bytes(SAMPLE)
        self.session=ConfigSession(self.path)
    def changed(self):
        self.session.model['ports'][0]['baud']=115200
        return self.session.preview()[0]
    def test_noop_does_not_write(self):
        before=self.path.stat().st_mtime_ns
        self.assertIsNone(self.session.save(self.session.preview()[0]))
        self.assertEqual(before,self.path.stat().st_mtime_ns)
    def test_save_backup_restore(self):
        data=self.changed();backup=self.session.save(data)
        self.assertEqual(backup.read_bytes(),SAMPLE);self.assertEqual(self.path.read_bytes(),data)
        old,diff=self.session.restore_preview(backup);self.assertIn('1500000',diff)
        self.session.restore(backup,old);self.assertEqual(self.path.read_bytes(),SAMPLE)
    def test_failed_reload_cannot_overwrite_external_edit(self):
        candidate=self.changed();self.path.write_bytes(b'local broken = {')
        with self.assertRaises(ConfigError):self.session.reload()
        with self.assertRaises(ConfigError):self.session.save(candidate)
        self.assertEqual(self.path.read_bytes(),b'local broken = {')
    def test_invalid_backup_metadata_rejected(self):
        backup=self.session.save(self.changed())
        (backup.parent/'record.json').write_text('[]',encoding='utf-8')
        with self.assertRaises(ConfigError):self.session.restore_preview(backup)
    def test_external_change_blocks_save(self):
        data=self.changed();self.path.write_bytes(SAMPLE+b'-- external\n')
        with self.assertRaises(ConfigError):self.session.save(data)
        self.assertTrue(self.path.read_bytes().endswith(b'-- external\n'))
    def test_readonly_filename(self):
        p=self.path.with_name('wezterm.lua');p.write_bytes(SAMPLE)
        with self.assertRaises(ConfigError):ConfigSession(p)
    def test_preview_must_match(self):
        data=self.changed();self.session.model['ports'][0]['baud']=9600
        with self.assertRaises(ConfigError):self.session.save(data)
    def test_replace_failure_keeps_original(self):
        data=self.changed()
        with patch('os.replace',side_effect=OSError('disk error')):
            with self.assertRaises(OSError):self.session.save(data)
        self.assertEqual(self.path.read_bytes(),SAMPLE);self.assertFalse(list(self.path.parent.glob('.serial-*.tmp')))
    def test_tampered_backup_rejected(self):
        backup=self.session.save(self.changed());backup.write_bytes(b'bad')
        with self.assertRaises(ConfigError):self.session.restore_preview(backup)
    def test_invalid_regex_blocks_save(self):
        for pattern in ['[', '(?<=error)word', r'(word)\1']:
            self.session.model['rules'][0]['patterns']=[pattern]
            with self.assertRaises(ConfigError):self.session.preview()
            self.assertEqual(self.path.read_bytes(),SAMPLE)
    def test_regex_size_limit_matches_terminal(self):
        self.session.model['rules'][0]['patterns']=[r'\p{Han}{1000}']
        with self.assertRaises(ConfigError):self.session.preview()
    def test_rust_unicode_regex_supported(self):
        self.session.model['rules'][0]['patterns']=[r'\p{Han}+',r'(?i)error']
        self.session.preview()
    def test_external_change_during_save(self):
        data=self.changed()
        real_replace=self.session._replace
        def interfere(candidate):
            self.path.write_bytes(SAMPLE+b'-- newer\n')
            return real_replace(candidate)
        with patch.object(self.session,'_replace',side_effect=interfere):
            with self.assertRaises(ConfigError):self.session.save(data)
        self.assertTrue(self.path.read_bytes().endswith(b'-- newer\n'))
    def test_other_files_untouched(self):
        files=[self.path.with_name(n) for n in ['wezterm.lua','ssh.lua','keys.lua']]
        for f in files:f.write_bytes(b'untouched')
        self.session.save(self.changed())
        for f in files:self.assertEqual(f.read_bytes(),b'untouched')

if __name__=='__main__':unittest.main()
