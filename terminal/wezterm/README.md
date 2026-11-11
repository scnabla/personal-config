# WezTerm 配置

仅维护 Windows 配置，完整文件位于 [windows/](windows/)，包含 `wezterm.lua`、`ssh.lua`、`serial.lua`、`keys.lua`、四款字体、字体授权和背景图片，可单独下载使用。

安装 WezTerm 后，把 `windows/` 目录里的 `wezterm.lua`、`ssh.lua`、`serial.lua`、`keys.lua`、`fonts/` 和 `imgs/` 直接复制到 `%USERPROFILE%\.config\wezterm\`，再打开 WezTerm。覆盖前先备份已有配置，详细步骤见 [Windows 配置说明](windows/README.md)。

使用 `Ctrl + Alt + Shift + 方向键` 调整窗格大小，左右每次移动四列，上下每次移动两行。

SSH 菜单默认关闭，仓库仅保留示例地址和用户名。个人连接信息在本机 `ssh.lua` 中填写。串口连接、日志和高亮规则在 `serial.lua` 中设置，键盘快捷键和命令面板中的按键标注在 `keys.lua` 中设置，主 `wezterm.lua` 保留目录及加载说明。
