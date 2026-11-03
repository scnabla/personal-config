# 个人终端配置

保存 Linux 端 Ghostty 和 Windows 端 WezTerm 的个人配置。

| 终端 | 仓库文件 | 配置位置 |
| --- | --- | --- |
| Ghostty | [ghostty/config.ghostty](ghostty/config.ghostty) | `~/.config/ghostty/config.ghostty` |
| WezTerm | [wezterm/wezterm.lua](wezterm/wezterm.lua) | `%USERPROFILE%\.config\wezterm\wezterm.lua` |

## 恢复配置

备份目标设备的现有配置，将对应文件复制到配置位置。更换系统用户名时，使用目标用户的主目录。复制后重新加载配置。

### Ghostty

- 安装 `JetBrainsMono Nerd Font Mono` 字体。
- 背景图片默认关闭；使用时取消 `background-image` 的注释，填写目标设备上的图片路径。
- 当前使用 `Monokai Classic` 主题，字号为 14。

### WezTerm

- 安装 `JetBrainsMono Nerd Font Mono` 字体，或将字体文件放在 `wezterm.lua` 同级的 `fonts/` 目录中。
- 背景图片放在配置目录下的 `imgs/saber.jpg`；缺失时使用配色背景。
- Windows 启动目录默认为用户目录，可通过 `compat.paths.windows_project` 修改。
- SSH 菜单默认关闭。在 `compat.ssh` 中填写服务器地址、端口和用户名后，将 `enabled.ssh` 设为 `true`。
- 默认终端优先使用 PowerShell 7，标签栏字体设置为 `Microsoft YaHei UI`。
- 当前使用 `Catppuccin Mocha` 配色，字号为 12。

字体与背景图片需单独准备。

个人服务器地址、用户名和绝对路径仅保存在本机配置中。更新公开版本时，保留仓库中的示例值。
