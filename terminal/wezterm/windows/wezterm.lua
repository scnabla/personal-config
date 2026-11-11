--[[
Windows WezTerm 配置
通用设置在本文件；同目录 ssh.lua 管理 SSH，serial.lua 管理串口，keys.lua 管理键盘快捷键。
配置目录：搜索“[编号] 标题”，跳到下一处匹配即可定位正文。
【win】表示该项包含 Windows 专属设置、处理逻辑或快捷键说明。
[开关] 功能开关：集中开启或关闭可选配置
[00] 多端兼容与工具设置
  ├─ [00.1] 系统识别【win】
  ├─ [00.2] 路径【win】
  ├─ [00.3] 程序名【win】
  ├─ [00.4] SSH 服务器 → ssh.lua
  ├─ [00.5] Windows 标签栏字体【win】
  └─ [00.6] 文件检查、程序查找与平台选择逻辑【win】
[01] 启动
  ├─ [01.0] 系统识别与路径检查【win】
  ├─ [01.1] 默认终端【win】
  ├─ [01.2] 启动目录【win】
  └─ [01.3] 启动菜单
      ├─ [01.3.1] 本机默认终端【win】
      ├─ [01.3.2] SSH 服务器 → ssh.lua
      ├─ [01.3.3] UART 串口【win】 → serial.lua
      ├─ [01.3.4] 串口日志 → serial.lua
      └─ [01.3.5] 串口关键词高亮 → serial.lua
[02] 外观
  ├─ [02.1] 字体与字号
  ├─ [02.2] 配色方案
  ├─ [02.3] 背景
  │   ├─ [02.3.1] 背景透明度
  │   ├─ [02.3.2] 背景图片
  │   └─ [02.3.3] 图片亮度
  └─ [02.4] 窗口内边距
[03] 标签栏
  ├─ [03.1] 显示位置
  ├─ [03.2] 单标签页显示
  ├─ [03.3] 标签栏样式
  └─ [03.4] 标签栏中文字体【win】
[04] 光标
  └─ [04.1] 形状与闪烁
[05] 滚动与历史输出
  ├─ [05.1] 滚动条
  └─ [05.2] 历史输出行数
[06] 鼠标操作
  ├─ [06.1] 选中文本自动复制
  ├─ [06.2] 右键粘贴
  └─ [06.3] Ctrl 点击打开链接
[07] 键盘快捷键 → keys.lua
  ├─ [07.1] 默认快捷键 → keys.lua
  ├─ [07.2] 自定义快捷键 → keys.lua
  └─ [07.3] 窗格快捷键 → keys.lua
[08] 中文命令面板
  ├─ [08.0] 快捷键标注【win】 → keys.lua
  ├─ [08.1] 配置与终端
  ├─ [08.2] 编辑与搜索
  ├─ [08.3] 字号与滚动
  ├─ [08.4] 窗口、标签页与分屏
  └─ [08.5] 帮助与链接
[09] 提示与通知
  ├─ [09.1] 终端提示音
  └─ [09.2] 关闭确认
[10] 渲染与性能
  └─ [10.1] 渲染方式
[11] 当前选中状态
  ├─ [11.1] 分屏明暗区分
  ├─ [11.2] 当前标签突出显示
  └─ [11.3] 独立窗口焦点提示

仅加入已确认的设置，其余保持 WezTerm 默认值。
]]

-- ========== [开关] 功能开关 ==========
-- true 开启，false 关闭；SSH 开关单独放在 ssh.lua 的 [开关]。
-- 修改后重载配置；默认终端、启动目录影响之后新建的会话，不改变已运行的程序。
local enabled = {
  windows_settings = true, -- 【win】指定终端、启动目录和标签栏字体；关闭后使用默认终端、用户目录和默认字体
  background = true,       -- 背景图片及图片亮度；关闭后使用配色背景
  chinese_commands = true, -- 自定义中文命令面板；内置英文命令不受影响
  focus_indicator = true,  -- 分屏明暗、标签高亮与窗口焦点提示
}

local wezterm = require 'wezterm'
local config = wezterm.config_builder()
-- 从实际主 Lua 所在目录加载模块，也适用于 --config-file 指定的配置。
-- require 会将 ssh.lua、serial.lua、keys.lua 加入配置监听，保存任一文件后自动重载。
package.path = wezterm.config_dir .. '/?.lua;' .. package.path
-- ========== [00] 多端兼容与工具设置 ==========
-- 多端兼容设置：启动目录、背景图、程序名和字体在下方设置；SSH 服务器见 ssh.lua。
-- 修改值后在 WezTerm 中重新加载配置；这里不会修改系统环境变量。
local compat = {}

-- ----- [00.1] 系统识别 -----
-- 仅识别 Windows；其他平台使用默认终端和字体。
compat.is_windows = wezterm.target_triple:find('windows', 1, true) ~= nil

-- ----- [00.2] 路径 -----
-- 路径：通常只需要修改前两项。
compat.paths = {
  -- Windows 启动目录；目录不存在时自动使用用户目录。macOS/Linux 使用用户目录。
  windows_project = os.getenv('USERPROFILE') or wezterm.home_dir,
  -- 背景图片相对于 wezterm.lua 所在目录；跨设备同步时把图片一并带上。
  background_image = 'imgs/saber.jpg',
  -- 下面两项优先读取 Windows 环境变量，后面的路径仅是读取失败时的备用值。
  windows_system_root = os.getenv('SystemRoot') or 'C:/Windows',
  windows_program_files = os.getenv('ProgramFiles') or 'C:/Program Files',
}

-- ----- [00.3] 程序名 -----
-- 程序名：只有安装的程序用了不同文件名时才改。
-- 查找顺序是本文件下方列出的常见安装位置，然后是 PATH 中的绝对目录。
-- 不在启动目录或项目文件夹里查找程序。
compat.programs = {
  -- Windows 默认终端优先使用 PowerShell 7；找不到时依次使用下面两项。
  pwsh = 'pwsh.exe',
  windows_powershell = 'powershell.exe',
  windows_cmd = 'cmd.exe',
}

-- ----- [00.4] SSH 服务器 -----
-- 配置位于同目录 ssh.lua 的 [开关] 和 [00.4]；连接加载见 [01.3.2]。
-- 修改服务器、用户名、端口或 SSH 开关时编辑 ssh.lua。

-- ----- [00.5] Windows 标签栏字体 -----
-- 仅 Windows 指定字体；其他平台使用默认字体，不执行外部字体检查。
compat.windows_tab_font = 'Microsoft YaHei UI'

-- ----- [00.6] 文件检查、程序查找与平台选择逻辑 -----
function compat.file_exists(path)
  local file = io.open(path, 'rb')
  if not file then return false end
  file:close()
  return true
end

local function directory_exists(path)
  local ok = pcall(wezterm.read_dir, path)
  return ok
end

function compat.warn_once(key, message)
  key = 'personal_compat_warning_' .. key
  if not wezterm.GLOBAL[key] then
    wezterm.GLOBAL[key] = true
    wezterm.log_warn(message)
  end
end

-- 以下是查找与回退逻辑；路径、程序名和字体在上方对应小节设置。
local function find_program(name, candidates)
  for _, path in ipairs(candidates or {}) do
    if compat.file_exists(path) then return path end
  end
  -- 仅用于 Windows 默认终端；不搜索当前目录或相对 PATH。
  for directory in (os.getenv('PATH') or ''):gmatch('[^;]+') do
    directory = directory:gsub('^"', ''):gsub('"$', '')
    local absolute = directory:match('^%a:[/\\]') or directory:match('^[/\\][/\\]')
    if absolute then
      local path = directory .. '/' .. name
      if compat.file_exists(path) then return path end
    end
  end
end

function compat.default_shell()
  if not (enabled.windows_settings and compat.is_windows) then return { label = '系统默认终端' } end

  local pwsh = find_program(compat.programs.pwsh, {
    compat.paths.windows_program_files .. '/PowerShell/7/' .. compat.programs.pwsh,
  })
  if pwsh then return { args = { pwsh }, label = 'PowerShell 7' } end

  local powershell = compat.paths.windows_system_root .. '/System32/WindowsPowerShell/v1.0/' .. compat.programs.windows_powershell
  if compat.file_exists(powershell) then
    compat.warn_once('pwsh', '未找到 PowerShell 7，使用 Windows PowerShell；未安装或修改任何工具。')
    return { args = { powershell }, label = 'Windows PowerShell' }
  end

  compat.warn_once('shell', '未找到 PowerShell，使用系统命令提示符。')
  return { args = { compat.paths.windows_system_root .. '/System32/' .. compat.programs.windows_cmd }, label = '命令提示符' }
end

function compat.default_cwd()
  if not enabled.windows_settings then return wezterm.home_dir end
  local home = compat.is_windows and (os.getenv('USERPROFILE') or wezterm.home_dir) or wezterm.home_dir
  if compat.is_windows and directory_exists(compat.paths.windows_project) then
    return compat.paths.windows_project
  end
  return home
end

-- ========== [01] 启动 ==========

-- ----- [01.0] 系统识别与路径检查 -----
-- 路径、程序名及按系统选择的逻辑集中在上方 [00]。

-- ----- [01.1] 默认终端 -----
-- Windows 优先 PowerShell 7；其他系统不指定程序，由 WezTerm 使用用户默认 shell。
local shell = compat.default_shell()
if shell.args then config.default_prog = shell.args end

-- ----- [01.2] 启动目录 -----
-- 本机 Windows 项目路径存在时沿用；其他设备或系统回退到用户目录。
config.default_cwd = compat.default_cwd()

-- ----- [01.3] 启动菜单 -----
config.launch_menu = {
  -- [01.3.1] 本机默认终端
  {
    label = shell.label,
    args = config.default_prog,
  },
}
-- [01.3.2] SSH 服务器
-- 连接开关、服务器和目录记录路径在同目录 ssh.lua 中设置。
-- 此处加载连接配置；Alt + L 入口沿用内置 SSH，Alt + P 接入见 [07.2]。
local ssh = require 'ssh'
ssh.apply(config)

-- [01.3.3] UART 串口
-- 同目录 serial.lua 的 [01.3.3] 设置串口名称、端口、波特率等参数。
-- 此处一并加载串口连接、日志和高亮配置；Alt + L 选择连接。
require('serial').apply(config)

-- [01.3.4] 串口日志
-- 设置位于 serial.lua 的 [01.3.3] log_on_connect 和 [01.3.4] serial_logging。
-- 日志目录默认与主 Lua 相同，相对路径也以主 Lua 所在目录为基准。

-- [01.3.5] 串口关键词高亮
-- 规则与颜色在 serial.lua 的 [01.3.5] 中维护；由上方统一加载。

-- ========== [02] 外观 ==========

-- ----- [02.1] 字体与字号 -----
-- 使用 Nerd Font 显示 Starship 图标与箭头。
config.font_dirs = { wezterm.config_dir .. '/fonts' }
config.font = wezterm.font('JetBrainsMono Nerd Font Mono')
config.font_size = 12

-- ----- [02.2] 配色方案 -----
config.color_scheme = 'Catppuccin Mocha'
-- 窗格分隔线使用醒目的橘黄色；不改变其他配色。
config.colors = { split = '#FFB000' }

-- ----- [02.3] 背景 -----

-- [02.3.1] 背景透明度
-- 1.0 表示完全不透明。
config.window_background_opacity = 1.0
-- 文字自带的背景色透明，保留彩色文字；对串口、SSH 和本地终端均生效。
-- config.text_background_opacity = 0.0

-- [02.3.2] 背景图片
-- 图片位于本配置文件旁的 imgs 文件夹中。
-- 多端同步时一并带上 imgs/saber.jpg；缺失时使用配色背景，不因路径不存在而报错。
if enabled.background then
local background_path = wezterm.config_dir .. '/' .. compat.paths.background_image
if compat.file_exists(background_path) then
  config.window_background_image = background_path
else
  compat.warn_once('background', '背景图片 ' .. compat.paths.background_image .. ' 不存在或不可读，暂时使用配色背景。')
end

-- [02.3.3] 图片亮度
-- 将背景图片亮度调至原图的 15%，不修改图片文件。
config.window_background_image_hsb = { brightness = 0.15 }
end -- enabled.background

-- ----- [02.4] 窗口内边距 -----
-- 保留 WezTerm 默认内边距，不设置 config.window_padding。

-- ========== [03] 标签栏 ==========

-- ----- [03.1] 显示位置 -----
-- false 表示标签栏位于顶部。
config.tab_bar_at_bottom = false

-- ----- [03.2] 单标签页显示 -----
-- 只有一个标签页时也显示标签栏。
config.hide_tab_bar_if_only_one_tab = false

-- ----- [03.3] 标签栏样式 -----
-- 保留默认图形样式，不设置 config.use_fancy_tab_bar。
-- 标签、新建标签按钮及悬停状态使用亮橘黄色。
local tab_bar_colors = wezterm.get_builtin_color_schemes()[config.color_scheme].tab_bar
for _, state in ipairs({ 'active_tab', 'inactive_tab', 'inactive_tab_hover', 'new_tab', 'new_tab_hover' }) do
  tab_bar_colors[state].fg_color = '#FFB52E'
end
tab_bar_colors.background = '#111820'
-- 未选中标签右侧使用灰蓝分隔线，区分相邻标签。
tab_bar_colors.inactive_tab_edge = '#53677D'
tab_bar_colors.active_tab.bg_color = '#155E63'
tab_bar_colors.inactive_tab.bg_color = '#202B3A'
tab_bar_colors.inactive_tab_hover.bg_color = '#30465A'
tab_bar_colors.new_tab.bg_color = '#111820'
tab_bar_colors.new_tab_hover.bg_color = '#30465A'
config.colors.tab_bar = tab_bar_colors
-- 图形标签栏的空白区域由 window_frame 控制。
config.window_frame = {
  active_titlebar_bg = '#111820',
  inactive_titlebar_bg = '#111820',
}


-- ----- [03.4] 标签栏中文字体 -----
-- 仅 Windows 指定中文字体；其他平台保留 WezTerm 默认字体。
-- 仅影响图形标签栏及其状态文字，不改变终端正文字体和字号。
if enabled.windows_settings and compat.is_windows then
  config.window_frame.font = wezterm.font(compat.windows_tab_font)
end

-- ========== [04] 光标 ==========

-- ----- [04.1] 形状与闪烁 -----
-- 竖线光标，启用闪烁，明暗切换间隔为 800 毫秒。
config.default_cursor_style = 'BlinkingBar'
config.cursor_blink_rate = 800

-- ========== [05] 滚动与历史输出 ==========

-- ----- [05.1] 滚动条 -----
-- 显示滚动条，便于拖动查看历史输出。
config.enable_scroll_bar = true

-- ----- [05.2] 历史输出行数 -----
-- 保留 WezTerm 默认行数，不设置 config.scrollback_lines。

-- ========== [06] 鼠标操作 ==========

config.mouse_bindings = {
  -- ----- [06.1] 选中文本自动复制 -----
  -- 使用左键选择文本后，松开鼠标即复制到系统剪贴板。
  {
    event = { Up = { streak = 1, button = 'Left' } },
    mods = 'NONE',
    action = wezterm.action.CompleteSelection 'Clipboard',
  },
  -- ----- [06.2] 右键粘贴 -----
  -- 点击右键，粘贴系统剪贴板中的内容。
  {
    event = { Down = { streak = 1, button = 'Right' } },
    mods = 'NONE',
    action = wezterm.action.PasteFrom 'Clipboard',
  },
  -- ----- [06.3] Ctrl 点击打开链接 -----
  -- 普通左键仍用于选择文本，按住 Ctrl 点击才打开链接。
  {
    event = { Down = { streak = 1, button = 'Left' } },
    mods = 'CTRL',
    action = wezterm.action.Nop,
  },
  {
    event = { Up = { streak = 1, button = 'Left' } },
    mods = 'CTRL',
    action = wezterm.action.OpenLinkAtMouseCursor,
  },
}

-- ========== [07] 键盘快捷键 ==========
-- 自定义绑定、窗格数字选择和命令面板的快捷键标注统一在同目录 keys.lua 中维护。

-- ----- [07.1] 默认快捷键 -----
-- keys.lua 的 [07.1] 说明默认按键的保留方式；鼠标操作见本文件 [06]。

-- ----- [07.2] 自定义快捷键 -----
-- keys.lua 的 [07.2] 设置 F5、Alt + L、Alt + P、分屏及调整窗格大小等绑定。
local keys = require 'keys'
keys.apply(config)

-- ----- [07.3] 窗格快捷键 -----
-- 操作说明见 keys.lua 的 [07.3]，在上方统一加载。

-- ========== [08] 中文命令面板 ==========
-- Ctrl + Shift + P 打开；原有英文命令完整保留，只追加中文入口。
-- 按已安装的 20240203-110809-5046fc22 版本默认命令表整理。
-- 来源：wezterm-gui/src/commands.rs 的 compute_default_actions。
-- 不执行这些操作，只有在面板中选择并确认后才会执行。
-- 不翻译程序内部的提示框、搜索框或复制模式专用按键表。
if enabled.chinese_commands then
wezterm.on('augment-command-palette', function(window, pane)
  local act = wezterm.action
  local entries = {}
  -- ----- [08.0] 快捷键标注 -----
  -- 标注文字在 keys.lua 的 [08.0] 维护；此处只组合命令名称和对应标注。
  local function add(label, action)
    local hint = keys.shortcut_labels[label] or '未绑定快捷键'
    table.insert(entries, { brief = label .. '  [' .. hint .. ']', action = action })
  end

  -- ----- [08.1] 配置与终端 -----
  add('配置：重新加载配置', act.ReloadConfiguration)
  add('终端：新建标签页', act.SpawnTab 'CurrentPaneDomain')
  add('终端：新建窗口', act.SpawnWindow)
  add('终端：上下分屏', act.SplitVertical { domain = 'CurrentPaneDomain' })
  add('终端：左右分屏', act.SplitHorizontal { domain = 'CurrentPaneDomain' })
  add('终端：关闭当前标签页（需确认）', act.CloseCurrentTab { confirm = true })
  add('终端：关闭当前窗格（需确认）', act.CloseCurrentPane { confirm = true })
  add('终端：重置当前终端状态', act.ResetTerminal)
  -- 目录菜单动作及兼容检查由 keys.lua 提供。
  if keys.directory_menu_action then
    add('SSH：常用目录', keys.directory_menu_action)
  end

  -- ----- [08.2] 编辑与搜索 -----
  add('编辑：复制到系统剪贴板', act.CopyTo 'Clipboard')
  add('编辑：从系统剪贴板粘贴', act.PasteFrom 'Clipboard')
  add('编辑：清除历史输出，保留当前屏幕', act.ClearScrollback 'ScrollbackOnly')
  add('编辑：清除历史输出和当前屏幕', act.ClearScrollback 'ScrollbackAndViewport')
  add('编辑：快速选择文本', act.QuickSelect)
  add('编辑：选择字符或表情', act.CharSelect {})
  add('编辑：进入键盘复制模式', act.ActivateCopyMode)
  add('编辑：退出全部临时快捷键模式', act.ClearKeyTableStack)
  add('编辑：打开命令面板', act.ActivateCommandPalette)
  add('搜索：搜索选中文本或输入关键词', act.Search 'CurrentSelectionOrEmptyString')

  -- ----- [08.3] 字号与滚动 -----
  add('字号：缩小', act.DecreaseFontSize)
  add('字号：放大', act.IncreaseFontSize)
  add('字号：恢复配置字号', act.ResetFontSize)
  add('字号：恢复字号和窗口大小', act.ResetFontAndWindowSize)
  add('滚动：向上翻一页', act.ScrollByPage(-1))
  add('滚动：向下翻一页', act.ScrollByPage(1))
  add('滚动：跳到顶部', act.ScrollToTop)
  add('滚动：跳到底部', act.ScrollToBottom)

  -- ----- [08.4] 窗口、标签页与分屏 -----
  add('窗口：切换全屏', act.ToggleFullScreen)
  add('窗口：切换置顶', act.ToggleAlwaysOnTop)
  add('窗口：切换置底', act.ToggleAlwaysOnBottom)
  add('窗口：始终置底', act.SetWindowLevel 'AlwaysOnBottom')
  add('窗口：恢复普通层级', act.SetWindowLevel 'Normal')
  add('窗口：始终置顶', act.SetWindowLevel 'AlwaysOnTop')
  add('窗口：隐藏窗口', act.Hide)
  add('窗格：显示编号并选择窗格', act.PaneSelect { mode = 'Activate' })
  add('窗格：按数字交换到当前焦点位置', keys.swap_pane_by_number)
  add('窗格：交换位置并跟随当前窗格', act.PaneSelect { mode = 'SwapWithActiveKeepFocus' })
  add('窗格：选择并移到新标签页', act.PaneSelect { mode = 'MoveToNewTab' })
  add('窗格：选择并移到新窗口', act.PaneSelect { mode = 'MoveToNewWindow' })
  add('窗格：正向轮换内容', act.RotatePanes 'Clockwise')
  add('标签页：切换到上一个', act.ActivateTabRelative(-1))
  add('标签页：切换到下一个', act.ActivateTabRelative(1))
  add('窗口：切换到上一个', act.ActivateWindowRelative(-1))
  add('窗口：切换到下一个', act.ActivateWindowRelative(1))
  for _, direction in ipairs {
    { 'Left', '左' }, { 'Right', '右' }, { 'Up', '上' }, { 'Down', '下' },
  } do
    local horizontal = direction[1] == 'Left' or direction[1] == 'Right'
    local step = horizontal and 4 or 2
    add('窗格：向' .. direction[2] .. '调整大小' .. (horizontal and '四列' or '两行'), act.AdjustPaneSize { direction[1], step })
    add('窗格：切换到' .. direction[2] .. '方', act.ActivatePaneDirection(direction[1]))
  end
  add('窗格：切换放大或还原', act.TogglePaneZoomState)
  add('菜单：打开启动菜单', act.ShowLauncher)
  add('菜单：打开标签页列表', act.ShowTabNavigator)

  -- ----- [08.5] 帮助与链接 -----
  add('帮助：打开调试面板', act.ShowDebugOverlay)
  add('链接：打开鼠标位置的链接', act.OpenLinkAtMouseCursor)

  return entries
end)

end -- enabled.chinese_commands

-- ========== [09] 提示与通知 ==========

-- ----- [09.1] 终端提示音 -----
-- 关闭终端响铃，不修改其他程序或系统的声音设置。
config.audible_bell = 'Disabled'

-- ----- [09.2] 关闭确认 -----
-- 通过窗口关闭按钮等方式关闭时询问确认。
config.window_close_confirmation = 'AlwaysPrompt'
-- 不因当前仅运行 PowerShell 等常见终端而跳过确认。
-- 此列表也影响标签页和窗格的关闭确认。
config.skip_close_confirmation_for_processes_named = {}

-- ========== [10] 渲染与性能 ==========

-- ----- [10.1] 渲染方式 -----
-- 使用 OpenGL；更改渲染方式后完整退出并重新启动 WezTerm。
-- 不修改帧率或显卡选择。
config.front_end = 'OpenGL'

-- ========== [11] 当前选中状态 ==========

-- ----- [11.1] 分屏明暗区分 -----
-- 当前窗格保持原样；其他窗格降低亮度和饱和度，仍可阅读。
if enabled.focus_indicator then
config.inactive_pane_hsb = { saturation = 0.8, brightness = 0.35 }

-- ----- [11.2] 当前标签突出显示 -----
-- 保留自定义标签名；没有自定义名称时使用当前窗格标题。
wezterm.on('format-tab-title', function(tab, tabs, panes, effective_config, hover, max_width)
  local title = tab.tab_title
  if not title or title == '' then
    title = tab.active_pane and tab.active_pane.title or '终端'
  end
  local prefix = tab.is_active and '当前 ' or ''
  local text = prefix .. tostring(tab.tab_index + 1) .. ': ' .. title
  text = wezterm.truncate_right(text, math.max(1, max_width - 2))
  if tab.is_active then
    -- 选中标签使用青绿色，与未选中标签的蓝灰色区分；窗口未激活时略微调暗。
    local focused = wezterm.GLOBAL['personal_window_focus_' .. tostring(tab.window_id)] == true
    return {
      { Background = { Color = focused and '#155E63' or '#244A50' } },
      { Foreground = { Color = '#FFB52E' } },
      { Attribute = { Intensity = 'Bold' } },
      { Text = ' ' .. text .. ' ' },
    }
  end
  return { { Text = ' ' .. text .. ' ' } }
end)

-- ----- [11.3] 独立窗口焦点提示 -----
-- 焦点事件中读取窗口状态，标题回调只读缓存，避免调用异步接口报错。
-- 标签栏左侧同步显示焦点提示。
local function update_window_focus(win)
  local focused = win:is_focused()
  wezterm.GLOBAL['personal_window_focus_' .. tostring(win:window_id())] = focused
  win:set_left_status(wezterm.format {
    { Foreground = { Color = '#FFB52E' } },
    { Background = { Color = '#111820' } },
    { Text = focused and ' 当前窗口 ' or ' 未激活 ' },
  })
end
wezterm.on('window-focus-changed', update_window_focus)
wezterm.on('window-config-reloaded', function(win)
  -- 重载后先清空再恢复，避免状态文字相同时跳过标题和标签栏刷新。
  -- 只更新显示，不抢占焦点、不修改配置，也不启动循环刷新。
  win:set_left_status('')
  update_window_focus(win)
end)
wezterm.on('format-window-title', function(tab, pane, tabs, panes, effective_config)
  local focused = wezterm.GLOBAL['personal_window_focus_' .. tostring(tab.window_id)]
  local status = focused == nil and '窗口' or (focused and '当前窗口' or '未激活')
  local title = tab.tab_title
  if not title or title == '' then title = pane and pane.title or '终端' end
  local zoomed = pane and pane.is_zoomed and ' [窗格已放大]' or ''
  return '[' .. status .. '] [' .. tostring(tab.tab_index + 1) .. '/' .. tostring(#tabs)
    .. '] ' .. title .. zoomed .. ' — ' .. (wezterm.app_name or 'WezTerm')
end)

else
  -- 热重载关闭提示时清空左侧旧文字；默认标题和标签样式由 WezTerm 接管。
  wezterm.on('window-config-reloaded', function(win)
    wezterm.GLOBAL['personal_window_focus_' .. tostring(win:window_id())] = false
    win:set_left_status('')
  end)
end -- enabled.focus_indicator

return config
