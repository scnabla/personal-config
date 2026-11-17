-- ScnTerm 键盘配置：自定义绑定、窗格数字选择及中文命令面板的快捷键标注。
-- 由同目录 wezterm.lua 的 [07.2] 加载；保存后自动重载。
local wezterm = require 'wezterm'
local M = {}

-- [07.1] 默认快捷键
-- 保留 WezTerm 默认键盘绑定，不设置 config.leader；鼠标操作在主 Lua 的 [06]。

-- [07.2] 自定义快捷键
-- 数字窗格选择动作同时用于 F5 和中文命令面板。
M.swap_pane_by_number = wezterm.action.PaneSelect {
  alphabet = '1234567890',
  mode = 'SwapWithActive',
}

-- 旧版 ScnTerm 与原版 WezTerm 不提供 SSH 目录菜单，跳过相关绑定和菜单入口。
local directory_menu_supported, directory_menu_action = pcall(function()
  return wezterm.action.ShowDirectoryMenu
end)
if directory_menu_supported then
  M.directory_menu_action = directory_menu_action
end

function M.apply(config)
  config.pane_select_fg_color = '#FFB52E'

  config.keys = {
    { key = 'LeftArrow', mods = 'CTRL|ALT|SHIFT', action = wezterm.action.AdjustPaneSize { 'Left', 4 } },
    { key = 'RightArrow', mods = 'CTRL|ALT|SHIFT', action = wezterm.action.AdjustPaneSize { 'Right', 4 } },
    { key = 'UpArrow', mods = 'CTRL|ALT|SHIFT', action = wezterm.action.AdjustPaneSize { 'Up', 2 } },
    { key = 'DownArrow', mods = 'CTRL|ALT|SHIFT', action = wezterm.action.AdjustPaneSize { 'Down', 2 } },
    { key = 'F4', mods = 'CTRL|SHIFT', action = wezterm.action.TogglePaneZoomState },
    { key = 'F5', mods = 'NONE', action = M.swap_pane_by_number },
    { key = 'Enter', mods = 'ALT', action = wezterm.action.ToggleFullScreen },
    { key = 'l', mods = 'ALT', action = wezterm.action.ShowLauncher },
    { key = 'F1', mods = 'CTRL|SHIFT', action = wezterm.action.SplitHorizontal { domain = 'CurrentPaneDomain' } },
    { key = 'F2', mods = 'CTRL|SHIFT', action = wezterm.action.SplitVertical { domain = 'CurrentPaneDomain' } },
    { key = 'F3', mods = 'CTRL|SHIFT', action = wezterm.action.CloseCurrentPane { confirm = true } },
  }

  -- Alt + P 打开当前 SSH 连接的目录菜单，上下选择、回车进入或添加，- 删除记录。
  if M.directory_menu_action then
    table.insert(config.keys, { key = 'p', mods = 'ALT', action = M.directory_menu_action })
  end
end

-- [07.3] 窗格快捷键
-- Ctrl + Shift + F1 左右分屏，F2 上下分屏，F3 关闭当前窗格（需确认），F4 放大或恢复当前窗格。
-- F5 显示数字标记，按对应数字交换窗格，焦点留在屏幕原位置；Esc 取消。
-- Ctrl + Alt + Shift + 方向键调整大小：左右四列，上下两行。
-- Alt + L 打开启动菜单，Alt + Enter 切换全屏。

-- [08.0] 中文命令面板的快捷键标注
-- 此表只提供显示文字，不创建绑定；修改上方按键时同步更新对应标注。
-- 未列出的命令由主 Lua 显示“未绑定快捷键”。
M.shortcut_labels = {
  ['配置：重新加载配置'] = 'Ctrl + Shift + R',
  ['终端：新建标签页'] = 'Ctrl + Shift + T',
  ['终端：新建窗口'] = 'Ctrl + Shift + N',
  ['终端：上下分屏'] = 'Ctrl + Shift + F2',
  ['终端：左右分屏'] = 'Ctrl + Shift + F1',
  ['终端：关闭当前标签页（需确认）'] = 'Ctrl + Shift + W',
  ['终端：关闭当前窗格（需确认）'] = 'Ctrl + Shift + F3',
  ['编辑：复制到系统剪贴板'] = 'Ctrl + Shift + C',
  ['编辑：从系统剪贴板粘贴'] = 'Ctrl + Shift + V；右键',
  ['编辑：清除历史输出，保留当前屏幕'] = 'Ctrl + Shift + K',
  ['编辑：快速选择文本'] = 'Ctrl + Shift + Space',
  ['编辑：选择字符或表情'] = 'Ctrl + Shift + U',
  ['编辑：进入键盘复制模式'] = 'Ctrl + Shift + X',
  ['编辑：打开命令面板'] = 'Ctrl + Shift + P',
  ['搜索：搜索选中文本或输入关键词'] = 'Ctrl + Shift + F',
  ['字号：缩小'] = 'Ctrl + -',
  ['字号：放大'] = 'Ctrl + =',
  ['字号：恢复配置字号'] = 'Ctrl + 0',
  ['滚动：向上翻一页'] = 'Shift + PageUp',
  ['滚动：向下翻一页'] = 'Shift + PageDown',
  ['窗口：切换全屏'] = 'Alt + Enter',
  ['窗口：隐藏窗口'] = 'Ctrl + Shift + M',
  ['标签页：切换到上一个'] = 'Ctrl + Shift + Tab',
  ['标签页：切换到下一个'] = 'Ctrl + Tab',
  ['窗格：切换放大或还原'] = 'Ctrl + Shift + F4',
  ['菜单：打开启动菜单'] = 'Alt + L',
  ['帮助：打开调试面板'] = 'Ctrl + Shift + L',
  ['链接：打开鼠标位置的链接'] = 'Ctrl + 左键点击',
  ['窗格：按数字交换到当前焦点位置'] = 'F5',
  ['SSH：常用目录'] = 'Alt+P',
  ['窗格：向左调整大小四列'] = 'Ctrl + Alt + Shift + ←',
  ['窗格：向右调整大小四列'] = 'Ctrl + Alt + Shift + →',
  ['窗格：向上调整大小两行'] = 'Ctrl + Alt + Shift + ↑',
  ['窗格：向下调整大小两行'] = 'Ctrl + Alt + Shift + ↓',
  ['窗格：切换到左方'] = 'Ctrl + Shift + ←',
  ['窗格：切换到右方'] = 'Ctrl + Shift + →',
  ['窗格：切换到上方'] = 'Ctrl + Shift + ↑',
  ['窗格：切换到下方'] = 'Ctrl + Shift + ↓',
}

return M
