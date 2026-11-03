# 个人终端配置

Ghostty 和 WezTerm 各自维护完整的配置、字体、背景图片和安装脚本。使用其中一款时，只需下载对应目录。

| 终端 | 平台 | 独立目录 | 安装方式 |
| --- | --- | --- | --- |
| Ghostty | Linux | [ghostty/](ghostty/) | 在目录中运行 `bash install.sh` |
| WezTerm | Windows | [wezterm/](wezterm/) | 在目录中运行 `powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1` |

安装前需已安装对应的终端程序。安装脚本会备份已有配置；安装后重新打开终端。具体说明见各目录的 `README.md`。

两套目录分别包含常规、粗体、斜体和粗斜体四种 `JetBrainsMono Nerd Font Mono` 字体，版本为 JetBrains Mono 2.304、Nerd Fonts 3.5.1，分别附带 `fonts/OFL.txt`。字体来源为 [Nerd Fonts v3.5.1](https://github.com/ryanoasis/nerd-fonts/tree/v3.5.1/patched-fonts/JetBrainsMono/Ligatures)。

个人服务器地址、用户名和绝对路径仅保存在本机配置中。更新仓库时，保留示例连接信息。
