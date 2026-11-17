# ScnTerm 配置

独立的 Windows 桌面配置程序，读取独立 Lua 文件，编辑串口连接、日志、关键词高亮、SSH 服务器和快捷键。项目不引用 ScnTerm 的源码或库，也不与终端共用构建流程。

源码位于 [personal-config/tools/scnterm-config](https://github.com/scnabla/personal-config/tree/main/tools/scnterm-config)。Windows 下载：[配置程序发布页](https://github.com/scnabla/personal-config/releases/tag/scnterm-config)。

## 使用

无需安装 Python 或 Rust。解压完整程序目录，打开 `ScnTermConfig.exe`。程序优先读取用户目录中的 `.config/wezterm`，也可以通过“打开配置目录”选择其他位置。

支持独立的 `serial.lua`、`ssh.lua` 和 `keys.lua`；缺少某个文件时显示文件名，不影响其他文件使用，也不自动创建文件。推荐将 `wezterm.lua`、`serial.lua`、`ssh.lua`、`keys.lua` 放在同一目录，主配置负责加载模块。

1. 在“串口连接”中选择或新增连接，填写端口和通信参数。
2. 在“日志”中设置自动记录之外的公共选项：目录、文件大小和接收时间戳。自动记录在各连接中设置。
3. 在“高亮规则”中新增颜色组，关键词和正则表达式各按每行一个填写。正则直接填写，不增加 Lua 引号或额外转义。
4. 在“SSH”中增删服务器，填写地址、用户名和会话类型；在“快捷键”中增删绑定、修改按键组合或选择动作。
5. 点击“预览并保存”，核对当前文件的差异后确认保存。保存前自动备份原文件；其他文件的待保存输入继续保留。
6. 串口参数用于新连接，日志公共设置用于下一次开始记录；高亮规则随终端配置重载生效。

选择其他条目时自动保留并检查当前输入；编辑完成后点击“预览并保存”，确认差异后才写入文件。关闭程序或切换配置目录时，尚未保存的修改会提示确认。

## 写入范围

| 内容 | 权限 |
| --- | --- |
| `serial.lua` 的连接、日志、高亮设置 | 可编辑受支持的静态值，支持新增和删除连接、高亮组 |
| `ssh.lua` | 多服务器增删改，支持现有模块的 SSH 开关和 `server` 参数表 |
| `keys.lua` | 绑定增删改、按键和修饰键编辑、常用动作选择 |
| 动态计算字段，例如 `baud = get_baud()` | 保留原文并只读；快捷键动作可明确选择清单内动作替换 |
| `wezterm.lua` 及其他 Lua | 只读预览 |

编辑器解析配置声明，不执行 Lua 或计算条件分支。支持直接的 `config.serial_ports`、`config.serial_logging`、`config.serial_highlighting` 表，以及现有 `M.apply(config)` 中局部 `serial_ports` 表再赋给 `config.serial_ports` 的写法。多次赋值无法明确区分、动态列表或不支持的表键保持只读。

在具有明确 `M.apply(config)` 入口的 `serial.lua` 中，缺少的串口、日志或高亮章节可在首次编辑时新增。其他文件不会自动改写，也不会自动添加主配置的模块加载代码。完整示例见 `examples/`。

界面显示省略字段实际采用的值，读取时不补写 Lua。例如已有串口省略波特率时显示 9600，省略流控时显示 Software；新建连接使用 115200、8N1、None（无流控），端口名称需按设备修改。日志大小省略时显示 100 MB，时间戳显示“是”，日志目录显示所选配置目录。颜色输入支持 `#RRGGBB` 和 `#RRGGBBAA`。规则顺序沿用文件顺序，当前界面不调整规则顺序。

## 高亮输入

每条规则独立选择是否区分大小写，只提供“是 / 否”。新建规则为“否”。读取旧 Lua 时仍兼容共用 `case_sensitive`：单条规则省略时显示原共用设置的结果，两处均省略时显示“否”；仅查看或修改其他字段不会自动补写或删除原设置。

关键词与正则输入框为空时显示灰色格式参考，输入后提示消失。参考文字不会参与匹配或写入文件。关键词按原文匹配；正则可使用完整单词、词形变化、数字和十六进制数等常用示例。

## SSH 与快捷键

SSH 页面支持唯一的 `config.ssh_domains` 表，以及现有 `ssh_enabled`、`server.host`、`server.port`、`server.user` 模块写法。新增服务器使用普通 SSH（`multiplexing = 'None'`）、关闭启动时连接；填写地址和用户名后预览保存。原文件存在 SSH 菜单开关时需设为“是”，终端启动菜单才会显示服务器。密码不写入配置。

快捷键页面支持 `config.keys` 表和 `table.insert(config.keys, {...})` 条目。修饰键使用 `CTRL|SHIFT`、`ALT` 等组合，无修饰键填 `NONE`；相同按键组合不能重复。动作清单包含启动菜单、SSH 目录菜单、复制粘贴、分屏、关闭确认、标签切换、全屏和数字窗格交换等常用动作。现有自定义动作显示原代码，修改按键时保留动作，也可明确选择清单内动作替换。

修改或删除已有绑定时，同文件 `M.shortcut_labels` 中与原按键组合完全对应的文字同步更新；含多种操作的混合说明保留原样。不会自动创建未知动作或修改函数实现。配置中的条件分支保留，动态列表、无法区分的多次赋值和其他未支持的结构只读。

“预览并保存”和“恢复备份”均针对当前页面所属文件。串口连接、日志与高亮共同编辑 `serial.lua`；SSH 与快捷键各自保存。跨文件的修改需要分别确认，不进行多文件批量覆盖。

## 文件保护与恢复

- 保留无关代码、注释、UTF-8 BOM 和换行格式；没有修改时不写文件。
- 修改已有值时只替换对应位置；新增和删除条目不对整份文件格式化。
- 保存前检查 Lua 语法、受支持字段类型和范围，以及 Rust 正则表达式语法。无法识别的动态代码保留原样。
- 检测到文件被其他程序修改时停止保存，避免覆盖外部改动。需要重新读取后再编辑。
- 备份保存在配置目录的 `.scnterm-config-backups/` 下，每次保存使用独立子目录，原文件不会覆盖旧备份。
- “恢复备份”先展示差异，仅恢复与当前保存结果对应的备份；原文件或备份内容变化时拒绝恢复。连续多次修改可从最近一次开始逐次恢复。
- 本程序不打开串口、不发送设备命令、不修改日志或 SSH 路径记录，也不负责安装、启动或重启终端。

只读预览限于 UTF-8 Lua 文件，单个文件不超过 2 MB。配置目录应可写，备份由用户自行保留和整理。语法和字段检查不替代目标 ScnTerm 版本的完整配置加载；编辑器不会执行配置来检查运行结果。

## 源码运行与构建

Python 3.11 及以上版本需要包含 Tkinter，Rust 用于构建独立的正则校验程序。依赖安装在项目虚拟环境，不修改系统环境。

以下命令在 `tools/scnterm-config/` 目录执行。Windows 构建：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-windows.ps1
```

产物为 `dist/ScnTermConfig/`，需要保留整个目录。源码启动：

```powershell
.venv\Scripts\python.exe run.py --config-dir examples
```

自动测试：

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

文件分工、实现限制和测试说明见 [开发说明](https://github.com/scnabla/personal-config/blob/main/tools/scnterm-config/docs/development.md)。
