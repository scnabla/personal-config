# Windows WezTerm 配置

适用于 Windows。目录包含 `wezterm.lua`、`fonts/` 和 `imgs/saber.jpg`，不依赖其他终端目录。

## 放置配置

安装 WezTerm 后，在文件资源管理器地址栏输入 `%USERPROFILE%\.config\wezterm`，创建不存在的目录。将本目录中的 `wezterm.lua`、`fonts/` 和 `imgs/` 复制进去：

```text
%USERPROFILE%\.config\wezterm\
├── wezterm.lua
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

## 内容

- 字体为 JetBrainsMono Nerd Font Mono，字号 12，包含常规、粗体、斜体、粗斜体。
- 配色为 Catppuccin Mocha，背景图片随目录提供。
- `Ctrl + Shift + F1/F2` 左右或上下分屏，`Ctrl + Shift + F3` 关闭窗格，`Ctrl + Shift + F4` 放大或恢复窗格。
- `Ctrl + Shift + F5` 正向轮换所有窗格内容，焦点留在屏幕原位置，布局和各位置的大小保持不变。
- `Alt + L` 打开启动菜单，`Alt + Enter` 切换全屏。
- `Ctrl + Alt + Shift + 方向键` 调整窗格大小，左右每次移动四列，上下每次移动两行。
- SSH 菜单默认关闭。需要时，在本机 `compat.ssh` 中填写连接信息并将 `enabled.ssh` 设为 `true`。
- UART 串口使用 [scnterm 的 Windows UART 版本](https://github.com/scnabla/scnterm/blob/personal/docs/uart-development.md)。参数集中在主配置的 `[01.3.3] UART 串口` 段，默认连接 COM3，波特率 1500000，8N1，无流控。按 `Alt + L` 选择 `UART: RK3568 (COM3)`，在当前窗口新建串口标签页；修改参数后关闭原串口标签页再重新连接。
- 串口日志需要支持该功能的 scnterm，Windows 本地版本 `20261108-serial-log-local` 已包含该功能。COM3 默认在新连接时自动记录；把该连接的 `log_on_connect` 设为 `false` 可改为手动开始。连接期间通过 `Alt + L` 启停日志。不支持日志的旧版 scnterm 自动跳过日志字段，保留原串口连接配置。
- `[01.3.4] 串口日志` 中集中设置保存目录、分文件大小和接收时间戳。默认保存到主 Lua 所在目录，包含接收时间，单文件达到 100 MB 后分文件；每次开始新建文件，停止期间的内容不补录，旧日志由用户手动删除。公共设置重载后用于下一次开始记录。

字体授权见 [fonts/OFL.txt](fonts/OFL.txt)。中文标签栏使用 Windows 系统字体 `Microsoft YaHei UI`。
