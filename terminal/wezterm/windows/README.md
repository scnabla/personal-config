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
- `Alt + L` 打开启动菜单，`Alt + Enter` 切换全屏。
- `Ctrl + Alt + Shift + 方向键` 调整窗格大小，左右每次移动四列，上下每次移动两行。
- SSH 菜单默认关闭。需要时，在本机 `compat.ssh` 中填写连接信息并将 `enabled.ssh` 设为 `true`。

字体授权见 [fonts/OFL.txt](fonts/OFL.txt)。中文标签栏使用 Windows 系统字体 `Microsoft YaHei UI`。
