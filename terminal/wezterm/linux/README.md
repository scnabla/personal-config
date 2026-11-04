# Linux WezTerm 配置

目录包含独立的 `wezterm.lua`、`fonts/` 和 `imgs/saber.jpg`。

## 放置配置

安装 WezTerm 后，将本目录中的 `wezterm.lua`、`fonts/` 和 `imgs/` 复制到 `~/.config/wezterm/`，目录结构如下：

```text
~/.config/wezterm/
├── wezterm.lua
├── fonts/
│   ├── JetBrainsMonoNerdFontMono-Regular.ttf
│   ├── JetBrainsMonoNerdFontMono-Bold.ttf
│   ├── JetBrainsMonoNerdFontMono-Italic.ttf
│   ├── JetBrainsMonoNerdFontMono-BoldItalic.ttf
│   └── OFL.txt
└── imgs/
    └── saber.jpg
```

若设置了 `XDG_CONFIG_HOME`，使用 `$XDG_CONFIG_HOME/wezterm/`。覆盖前先备份已有配置，文件放好后重新打开 WezTerm 即可。

字体和图片从配置目录读取，无需单独安装字体。启动目录为用户主目录，终端使用当前用户的默认 Shell。中文标签栏优先使用系统的 `Noto Sans CJK SC`，缺失时使用系统无衬线字体。

## 外观

- 字体为 JetBrainsMono Nerd Font Mono，字号 12，包含常规、粗体、斜体、粗斜体。
- 配色为 Catppuccin Mocha，背景图亮度为原图的 15%。
- 非当前窗格降低亮度，当前标签和窗口显示状态提示。
- 命令面板提供中文操作入口和配色预览。

## 快捷键

| 快捷键 | 操作 |
| --- | --- |
| `Ctrl + Shift + F1` | 左右分屏 |
| `Ctrl + Shift + F2` | 上下分屏 |
| `Ctrl + Shift + F3` | 关闭当前窗格，需确认 |
| `Ctrl + Shift + F4` | 放大或恢复当前窗格 |
| `Ctrl + Shift + 方向键` | 切换窗格 |
| `Ctrl + Alt + Shift + 左右方向键` | 调整窗格宽度，每次四列 |
| `Ctrl + Alt + Shift + 上下方向键` | 调整窗格高度，每次两行 |
| `Ctrl + Shift + R` | 重新加载配置 |
| `Ctrl + Shift + P` | 打开命令面板 |
| `Alt + L` | 打开启动菜单 |
| `Alt + Enter` | 切换全屏 |

桌面环境若占用同一快捷键，需在系统键盘设置中解除冲突。

SSH 菜单默认关闭。在本机 `compat.ssh` 中填写连接信息，再将 `enabled.ssh` 设为 `true` 即可启用。

字体授权见 [fonts/OFL.txt](fonts/OFL.txt)。
