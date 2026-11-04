# WezTerm 配置

Windows 和 Linux 分别维护独立配置。每个目录均包含 `wezterm.lua`、四款字体、字体授权和背景图片，可单独下载使用。

| 平台 | 目录 | 配置位置 |
| --- | --- | --- |
| Windows | [windows/](windows/) | `%USERPROFILE%\.config\wezterm\` |
| Linux | [linux/](linux/) | `~/.config/wezterm/` |

安装 WezTerm 后，把对应平台目录里的 `wezterm.lua`、`fonts/` 和 `imgs/` 直接复制到配置位置，再打开 WezTerm。已有配置先自行备份。Linux 若设置了 `XDG_CONFIG_HOME`，配置位置为 `$XDG_CONFIG_HOME/wezterm/`。

配置文件的查找顺序见 [WezTerm 配置说明](https://wezterm.org/config/files.html)。

两端均使用 `Ctrl + Alt + Shift + 方向键` 调整窗格大小，左右每次移动四列，上下每次移动两行。字体、图片和配置不依赖另一平台目录。

SSH 菜单默认关闭，仓库仅保留示例地址和用户名。个人连接信息在本机填写。
