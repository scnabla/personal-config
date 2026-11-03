# Ghostty 配置

适用于 Linux。目录包含 `config.ghostty`、`fonts/`、`imgs/saber.jpg` 和安装脚本，不依赖其他终端目录。

## 安装

安装 Ghostty 和 fontconfig 后，下载完整的 `ghostty` 目录，在该目录中执行：

```bash
bash install.sh
```

脚本将配置复制到 `${XDG_CONFIG_HOME:-~/.config}/ghostty`，将字体安装到 `${XDG_DATA_HOME:-~/.local/share}/fonts/JetBrainsMonoNerdFont`，刷新字体缓存，并为背景图片写入本机安装路径。已有配置目录会备份为 `ghostty.backup-时间-进程号`。安装完成后重新打开 Ghostty。

## 内容

- 字体为 JetBrainsMono Nerd Font Mono，字号 14，包含常规、粗体、斜体、粗斜体。
- 配色为 Monokai Classic，背景图片随目录提供。
- `Ctrl + Shift + F1/F2` 左右或上下分屏，`Ctrl + Shift + F3` 关闭窗格，`Ctrl + Shift + F4` 放大或恢复窗格。
- `Ctrl + Shift + 方向键` 切换窗格，`Alt + Enter` 切换全屏。
- `Ctrl + Alt + Shift + 方向键` 调整窗格大小，每次移动 10 像素。

字体授权见 [fonts/OFL.txt](fonts/OFL.txt)。更新仓库配置时，背景图片保留 `imgs/saber.jpg` 相对路径，不提交安装后生成的个人绝对路径。
