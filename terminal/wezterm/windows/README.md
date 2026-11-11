# Windows WezTerm 配置

适用于 Windows。目录包含 `wezterm.lua`、`ssh.lua`、`serial.lua`、`keys.lua`、`fonts/` 和 `imgs/saber.jpg`，不依赖其他终端目录。

## 放置配置

安装 WezTerm 后，在文件资源管理器地址栏输入 `%USERPROFILE%\.config\wezterm`，创建不存在的目录。将本目录中的 `wezterm.lua`、`ssh.lua`、`serial.lua`、`keys.lua`、`fonts/` 和 `imgs/` 复制进去：

```text
%USERPROFILE%\.config\wezterm\
├── wezterm.lua
├── ssh.lua
├── serial.lua
├── keys.lua
├── fonts\
│   ├── JetBrainsMonoNerdFontMono-Regular.ttf
│   ├── JetBrainsMonoNerdFontMono-Bold.ttf
│   ├── JetBrainsMonoNerdFontMono-Italic.ttf
│   ├── JetBrainsMonoNerdFontMono-BoldItalic.ttf
│   └── OFL.txt
└── imgs\
    └── saber.jpg
```

覆盖前先备份已有配置。若 `wezterm.exe` 所在目录中还有 `wezterm.lua`，先将该文件改名备份，因为程序目录中的配置优先加载。文件放好后重新打开 WezTerm 即可。

WezTerm 直接读取配置目录下的字体和背景图片，无需单独安装字体。默认终端优先使用 PowerShell 7，未安装时使用系统自带的 PowerShell。启动目录默认为当前用户目录。

## 配置文件分工

四个 Lua 文件放在同一目录。`wezterm.lua` 保留完整的编号目录，在 SSH、串口、日志、高亮和快捷键的原位置注明配置文件及对应节编号。

| 文件 | 设置内容 |
| --- | --- |
| [wezterm.lua](wezterm.lua) | 默认终端、外观、标签栏、鼠标操作、中文命令面板，以及各配置模块的加载入口 |
| [ssh.lua](ssh.lua) | `ssh_enabled` 开关、服务器 `host`/`port`/`user`、SSH 连接和目录记录文件 |
| [serial.lua](serial.lua) | 串口连接参数、自动记录、日志目录、分文件大小、时间戳和关键词高亮规则 |
| [keys.lua](keys.lua) | 自定义键盘绑定（包括 `Alt+P`）、F5 数字窗格选择、编号颜色及中文命令面板的快捷键标注 |

主配置从自身所在目录加载这三个模块；使用 `--config-file` 时同样按指定主配置所在目录查找。保存任一 Lua 文件后自动重载。更换串口或 SSH 连接参数后，新建连接使用新参数；已有连接不自动断开或重连。日志公共设置用于下一次开始记录，高亮规则重载后更新当前画面及滚动历史。

日志和 SSH 目录记录的相对路径仍以主 Lua 所在目录为基准。复制配置到其他设备时，四个 Lua 文件需一并复制；个人服务器信息保存在本机 `ssh.lua` 中，仓库保留示例值。

## 键盘快捷键

修改 `keys.lua` 的 `[07.2]` 中的 `config.keys`，即可调整自定义绑定的 `key`、`mods` 和 `action`。`Alt+P` 在同节进行兼容检查后追加。保存后自动重载，无需重启终端。

F5 的窗格选择动作和编号颜色同样在 `keys.lua` 中设置；中文命令面板复用该动作。`[08.0]` 的 `shortcut_labels` 只提供面板中的按键标注，不创建绑定；修改绑定时需同步修改对应标注。鼠标操作继续在主 `wezterm.lua` 的 `[06]` 中维护。

## 内容

- 字体为 JetBrainsMono Nerd Font Mono，字号 12，包含常规、粗体、斜体、粗斜体。
- 配色为 Catppuccin Mocha，背景图片随目录提供。
- `Ctrl + Shift + F1/F2` 左右或上下分屏，`Ctrl + Shift + F3` 关闭窗格，`Ctrl + Shift + F4` 放大或恢复窗格。
- 单独按 `F5` 显示当前标签页各窗格的数字标记，编号使用明亮橙黄色 `#FFB52E`。输入对应数字后，目标窗格与当前窗格交换位置，输入焦点留在原来的屏幕位置并操作换过来的目标窗格。按 `Esc` 取消；10 个窗格以内使用 `1` 至 `9`、`0`，更多窗格按实际显示的数字组合输入。中文命令面板提供“窗格：按数字交换到当前焦点位置”，并保留“窗格：正向轮换内容”。
- `Alt + L` 打开启动菜单，`Alt + Enter` 切换全屏。
- `Ctrl + Alt + Shift + 方向键` 调整窗格大小，左右每次移动四列，上下每次移动两行。
- SSH 菜单默认关闭。需要时，在本机 `ssh.lua` 的 `server` 中填写连接信息并将 `ssh_enabled` 设为 `true`。
- UART 串口使用 [scnterm 的 Windows UART 版本](https://github.com/scnabla/scnterm/blob/personal/docs/uart-development.md)。参数集中在 `serial.lua` 的 `[01.3.3] UART 串口` 段，默认连接 COM3，波特率 1500000，8N1，无流控。按 `Alt + L` 选择 `UART: RK3568 (COM3)`，在当前窗口新建串口标签页；修改参数后关闭原串口标签页再重新连接。
- 串口日志需要支持该功能的 scnterm，Windows 本地版本 `20261108-serial-log-local` 已包含该功能。COM3 默认在新连接时自动记录；把该连接的 `log_on_connect` 设为 `false` 可改为手动开始。连接期间通过 `Alt + L` 启停日志。不支持日志的旧版 scnterm 自动跳过日志字段，保留原串口连接配置。
- `serial.lua` 的 `[01.3.4] 串口日志` 中集中设置保存目录、分文件大小和接收时间戳。默认保存到主 Lua 所在目录，包含接收时间，单文件达到 100 MB 后分文件；每次开始新建文件，停止期间的内容不补录，旧日志由用户手动删除。公共设置重载后用于下一次开始记录。

## 串口关键词高亮

`serial.lua` 的 `[01.3.5] 串口关键词高亮` 段适用于包含该功能的 ScnTerm，Windows 本地版本 `20261110-serial-highlight-local` 已支持。旧版 ScnTerm 与原版 WezTerm 自动跳过高亮配置。

所有串口共用两组规则：错误、失败、`error`、`failed` 等文字使用玫红色 `#FF6B81`，警告、超时、`warning`、`timed out` 等文字使用橘黄色 `#FFB52E`。只改变匹配文字的颜色，日志、复制出的文本和实际收发内容保持不变，本地终端与 SSH 不应用这些规则。

每组的 `foreground` 设置颜色，`keywords` 添加按原样匹配的关键词，`patterns` 添加正则表达式。同一颜色可以对应多个关键词和表达式，默认不区分大小写；在 `serial_highlighting` 或某组规则中设置 `case_sensitive = true` 可区分大小写。多个规则重叠时，靠前的规则优先。

保存后自动重载，当前画面与滚动历史按新规则显示，无需重连串口。清空 `rules` 可恢复设备原色。配置错误会提示具体位置，并保留上一次成功加载的配置。

完整字段、正则语法与限制见 [ScnTerm 串口关键词高亮说明](https://github.com/scnabla/scnterm/blob/personal/docs/uart-development.md#串口关键词高亮)，可直接复制的通用示例见 [serial-highlighting.lua](https://github.com/scnabla/scnterm/blob/personal/docs/examples/serial-highlighting.lua)。

字体授权见 [fonts/OFL.txt](fonts/OFL.txt)。中文标签栏使用 Windows 系统字体 `Microsoft YaHei UI`。

## SSH 常用目录

包含 `ShowDirectoryMenu` 功能的 ScnTerm 使用 `Alt+P` 打开常用目录菜单。旧版本会跳过此快捷键。

在通过 `Alt+L` 建立的内置 SSH 会话中，回到空白命令提示符后使用：

- `↑`、`↓` 选择，回车进入对应目录。
- 选中“添加当前目录”后回车，读取并保存当前 Shell 的目录。
- `-` 删除选中的目录记录，不删除服务器上的目录。
- `Esc` 关闭菜单。

菜单只显示当前 SSH 连接的记录，同一连接的标签页和分屏共用列表。添加目录时会执行一次读取 `$PWD` 的命令，远端需有兼容 POSIX 的 Shell 及 `printf`、`base64`、`tr`。已有半行输入或前台程序正在运行时，应先回到空白命令提示符。

目录记录默认保存在主 Lua 同目录的 `scnterm-directory-bookmarks.json`，重启后保留。可在 `ssh.lua` 的 `M.apply` 函数中设置 `config.directory_bookmarks_file` 指定完整文件路径，相对路径以主 Lua 所在目录为基准；保存配置后重新打开菜单生效。修改位置不自动迁移旧记录，早期版本的文件位于 `%APPDATA%\wezterm\scnterm-directory-bookmarks.json`，可复制到新位置或继续配置为旧路径。该文件包含服务器标识和个人路径，不纳入配置仓库。详细说明见 [ScnTerm SSH 常用目录](https://github.com/scnabla/scnterm/blob/personal/docs/directory-menu.md)。
