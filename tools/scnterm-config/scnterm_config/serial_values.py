"""串口表单采用的实际值；显示省略字段时不改变 Lua 模型。"""

PORT_VALUES = {'baud':9600, 'data_bits':8, 'stop_bits':1, 'parity':'None',
               'flow_control':'Software', 'log_on_connect':False}
LOG_VALUES = {'max_file_size_mb':100, 'timestamps':True}


def effective_value(section, key, value, row, model, directory):
    if value is not None:
        return value
    if section == 'ports':
        return row.get('name') if key == 'port' else PORT_VALUES.get(key)
    if section == 'logging':
        return str(directory) if key == 'directory' and directory else LOG_VALUES.get(key)
    if key == 'case_sensitive':
        inherited = model.get('case_sensitive')
        return False if inherited is None else inherited
    return None
