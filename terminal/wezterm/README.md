# WezTerm 配置

适用于 Windows。目录包含 `wezterm.lua`、`fonts/`、`imgs/saber.jpg` 和安装脚本，不依赖其他终端目录。

## 安装

安装 WezTerm 后，下载完整的 `wezterm` 目录，在该目录中打开 PowerShell 并执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

脚本将配置、字体和图片复制到 `%USERPROFILE%\.config\wezterm`。已有目录和主目录下的旧版 `.wezterm.lua` 会备份为带有 `.backup-` 后缀的文件或目录。安装完成后重新打开 WezTerm。

WezTerm 直接读取配置目录下的字体和背景图片，无需单独安装字体。默认终端优先使用 PowerShell 7，未安装时使用系统自带的 PowerShell。启动目录默认为当前用户目录。

## 内容

- 字体为 JetBrainsMono Nerd Font Mono，字号 12，包含常规、粗体、斜体、粗斜体。
- 配色为 Catppuccin Mocha，背景图片随目录提供。
- `Ctrl + Shift + F1/F2` 左右或上下分屏，`Ctrl + Shift + F3` 关闭窗格，`Ctrl + Shift + F4` 放大或恢复窗格。
- `Alt + L` 打开启动菜单，`Alt + Enter` 切换全屏。
- `Ctrl + Alt + Shift + 方向键` 调整窗格大小，每次移动一个字符单元格。
- SSH 菜单默认关闭。需要时，在本机 `compat.ssh` 中填写连接信息并将 `enabled.ssh` 设为 `true`。

字体授权见 [fonts/OFL.txt](fonts/OFL.txt)。中文标签栏使用 Windows 系统字体 `Microsoft YaHei UI`。
