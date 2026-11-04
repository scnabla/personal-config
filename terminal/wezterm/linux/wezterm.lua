--[[
Linux WezTerm 配置
[开关] 功能开关
[00] 本机路径与 SSH 设置
[01] 启动
[02] 字体、配色与背景
[03] 标签栏
[04] 光标
[05] 滚动与历史输出
[06] 鼠标操作
[07] 键盘快捷键与配色预览
[08] 中文命令面板
[09] 提示与关闭确认
[10] 渲染
[11] 当前窗格、标签页与窗口提示
]]

-- ========== [开关] 功能开关 ==========
-- true 开启，false 关闭；SSH 入口默认关闭，填写本机连接信息后再开启。
-- 修改后重载配置；默认终端、启动目录影响之后新建的会话，不改变已运行的程序。
local enabled = {
  ssh = false,             -- 内置 SSH 菜单入口；关闭不主动断开已有连接，也不禁止在终端手动运行 SSH
  background = true,       -- 背景图片及图片亮度；关闭后使用配色背景
  chinese_commands = true, -- 自定义中文命令面板；内置英文命令不受影响
  color_preview = true,    -- 实时配色预览；依赖 chinese_commands，关闭时一起停用预览入口、按键和事件
  focus_indicator = true,  -- 分屏明暗、标签高亮与窗口焦点提示
}

local wezterm = require 'wezterm'
local config = wezterm.config_builder()
-- ========== [00] 本机路径与 SSH 设置 ==========
local compat = {}
compat.paths = {
  background_image = 'imgs/saber.jpg',
}
-- 在本机填写连接信息后开启 enabled.ssh；密码不写入配置。
compat.ssh = {
  host = 'example.com',
  port = '22',
  user = 'your-user',
}

function compat.file_exists(path)
  local file = io.open(path, 'rb')
  if not file then return false end
  file:close()
  return true
end

function compat.warn_once(key, message)
  key = 'personal_compat_warning_' .. key
  if not wezterm.GLOBAL[key] then
    wezterm.GLOBAL[key] = true
    wezterm.log_warn(message)
  end
end

-- ========== [01] 启动 ==========
-- 不指定 default_prog，使用当前用户的默认 Shell。
config.default_cwd = wezterm.home_dir
config.launch_menu = {
  { label = '本机终端' },
}
-- [01.3.2] SSH 服务器
-- 使用 WezTerm 内置 SSH，入口自动出现在 Alt + L 启动菜单中。
-- 仅选择入口后连接；首次连接需核对指纹，密码不写入配置。
-- None 表示普通 SSH，服务器无需安装 WezTerm；断网不保留会话。
-- 显式空列表避免关闭后自动从系统 SSH 配置生成入口。
config.ssh_domains = {}
if enabled.ssh then
config.ssh_domains = {
  {
    name = 'SSH: ' .. compat.ssh.user .. '@' .. compat.ssh.host .. ':' .. compat.ssh.port,
    remote_address = compat.ssh.host .. ':' .. compat.ssh.port,
    username = compat.ssh.user,
    multiplexing = 'None',
    connect_automatically = false,
  },
}

end -- enabled.ssh

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

-- ----- [03.4] 标签栏中文字体 -----
config.window_frame = {
  font = wezterm.font_with_fallback { 'Noto Sans CJK SC', 'sans-serif' },
}

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

-- ----- [07.1] 默认快捷键 -----
-- 保留其他 WezTerm 默认快捷键，不设置 config.leader。
-- 不禁用默认键盘绑定；上方已确认的鼠标绑定保持不变。

-- ----- [07.2] 打开启动菜单 -----
-- Alt + L 打开启动菜单，选择本机默认终端或 SSH 服务器。
config.keys = {
  { key = 'r', mods = 'CTRL|SHIFT', action = wezterm.action.ReloadConfiguration },
  { key = 'LeftArrow', mods = 'CTRL|SHIFT', action = wezterm.action.ActivatePaneDirection 'Left' },
  { key = 'RightArrow', mods = 'CTRL|SHIFT', action = wezterm.action.ActivatePaneDirection 'Right' },
  { key = 'UpArrow', mods = 'CTRL|SHIFT', action = wezterm.action.ActivatePaneDirection 'Up' },
  { key = 'DownArrow', mods = 'CTRL|SHIFT', action = wezterm.action.ActivatePaneDirection 'Down' },
  { key = 'LeftArrow', mods = 'CTRL|ALT|SHIFT', action = wezterm.action.AdjustPaneSize { 'Left', 4 } },
  { key = 'RightArrow', mods = 'CTRL|ALT|SHIFT', action = wezterm.action.AdjustPaneSize { 'Right', 4 } },
  { key = 'UpArrow', mods = 'CTRL|ALT|SHIFT', action = wezterm.action.AdjustPaneSize { 'Up', 2 } },
  { key = 'DownArrow', mods = 'CTRL|ALT|SHIFT', action = wezterm.action.AdjustPaneSize { 'Down', 2 } },
  { key = 'F4', mods = 'CTRL|SHIFT', action = wezterm.action.TogglePaneZoomState },
  { key = 'Enter', mods = 'ALT', action = wezterm.action.ToggleFullScreen },
  { key = 'l', mods = 'ALT', action = wezterm.action.ShowLauncher },
  { key = 'F1', mods = 'CTRL|SHIFT', action = wezterm.action.SplitHorizontal { domain = 'CurrentPaneDomain' } },
  { key = 'F2', mods = 'CTRL|SHIFT', action = wezterm.action.SplitVertical { domain = 'CurrentPaneDomain' } },
  { key = 'F3', mods = 'CTRL|SHIFT', action = wezterm.action.CloseCurrentPane { confirm = true } },
}

-- ----- [07.3] 窗格快捷键 -----
-- Ctrl + Shift + F1 左右分屏，F2 上下分屏，F3 关闭当前窗格（需确认），F4 放大或恢复当前窗格。
-- Ctrl + Alt + Shift + 方向键调整大小：左右四列，上下两行。

-- ----- [07.4] 实时配色预览与名称显示 -----
-- 从命令面板进入后，列表关闭，直接在终端上观察效果。
-- 状态按窗口保存到内存，切换配色引起配置重载时仍可按 Esc 恢复。
local start_color_preview
if enabled.color_preview and enabled.chinese_commands then
local preview_names
local function get_preview_names()
  if not preview_names then
    preview_names = {}
    for name in pairs(wezterm.color.get_builtin_schemes()) do
      table.insert(preview_names, name)
    end
    table.sort(preview_names)
  end
  return preview_names
end

local function preview_key(win)
  return 'personal_color_preview_' .. tostring(win:window_id())
end

local function show_preview_name(win)
  local state = wezterm.GLOBAL[preview_key(win)]
  if state then
    -- 名称放在右侧，窗口较窄时优先保留名称；提示使用固定的高对比颜色。
    win:set_right_status(wezterm.format {
      { Foreground = { Color = '#ffffff' } },
      { Background = { Color = '#202020' } },
      { Text = ' ←/→ 切换 · Enter 保留 · Esc 恢复 | ' .. state.name .. ' ' },
    })
  else
    win:set_right_status('')
  end
end

start_color_preview = function(win, pane)
  local key = preview_key(win)
  if not wezterm.GLOBAL[key] then
    local overrides = win:get_config_overrides() or {}
    wezterm.GLOBAL[key] = {
      original = overrides.color_scheme or false,
      name = win:effective_config().color_scheme or config.color_scheme,
    }
  end
  if win:active_key_table() ~= 'color_preview' then
    win:perform_action(wezterm.action.ActivateKeyTable {
      name = 'color_preview', one_shot = false, prevent_fallback = true,
    }, pane)
  end
  show_preview_name(win)
end

local function step_color_preview(win, direction)
  local key = preview_key(win)
  local state = wezterm.GLOBAL[key]
  if not state then return end
  local names = get_preview_names()
  if #names == 0 then return end
  local current = direction > 0 and 0 or 1
  for index, name in ipairs(names) do
    if name == state.name then current = index; break end
  end
  state.name = names[(current - 1 + direction) % #names + 1]
  wezterm.GLOBAL[key] = state
  local overrides = win:get_config_overrides() or {}
  overrides.color_scheme = state.name
  win:set_config_overrides(overrides)
  show_preview_name(win)
end

local function finish_color_preview(win, pane, restore)
  local key = preview_key(win)
  local state = wezterm.GLOBAL[key]
  -- 命令面板也会列出这些动作；未进入预览时不影响其他按键模式。
  if not state then return end
  wezterm.GLOBAL[key] = false
  if win:active_key_table() == 'color_preview' then
    win:perform_action(wezterm.action.PopKeyTable, pane)
  end
  if state and restore then
    local overrides = win:get_config_overrides() or {}
    overrides.color_scheme = state.original or nil
    win:set_config_overrides(overrides)
  end
  show_preview_name(win)
end

-- 使用固定中文事件名，避免命令面板显示 event-defined-0 等匿名编号。
-- WezTerm 自动生成的条目仍带有 Emit event 前缀。
wezterm.on('预览：上一个配色（←）', function(win) step_color_preview(win, -1) end)
wezterm.on('预览：下一个配色（→）', function(win) step_color_preview(win, 1) end)
wezterm.on('预览：保留配色并退出（Enter）', function(win, pane) finish_color_preview(win, pane, false) end)
wezterm.on('预览：恢复配色并退出（Esc）', function(win, pane) finish_color_preview(win, pane, true) end)

-- 仅在预览期间接管这些按键，退出后恢复原来的快捷键。
config.key_tables = {
  color_preview = {
    { key = 'LeftArrow', mods = 'NONE', action = wezterm.action.EmitEvent '预览：上一个配色（←）' },
    { key = 'RightArrow', mods = 'NONE', action = wezterm.action.EmitEvent '预览：下一个配色（→）' },
    { key = 'Enter', mods = 'NONE', action = wezterm.action.EmitEvent '预览：保留配色并退出（Enter）' },
    { key = 'Escape', mods = 'NONE', action = wezterm.action.EmitEvent '预览：恢复配色并退出（Esc）' },
  },
}
wezterm.on('update-right-status', show_preview_name)

-- 切换配色会重载配置并清空临时按键模式；重载结束后恢复尚未退出的预览。
-- 这里只恢复按键和名称，不再次设置配色，避免反复重载。
wezterm.on('window-config-reloaded', function(win, pane)
  if wezterm.GLOBAL[preview_key(win)] then
    local active_pane = pane or win:active_pane()
    if active_pane then start_color_preview(win, active_pane) end
  else
    show_preview_name(win)
  end
end)

else
  -- 热重载关闭预览时，恢复原配色并清除残留状态和临时按键模式。
  wezterm.on('window-config-reloaded', function(win, pane)
    local key = 'personal_color_preview_' .. tostring(win:window_id())
    local state = wezterm.GLOBAL[key]
    wezterm.GLOBAL[key] = false
    if win:active_key_table() == 'color_preview' then
      local active_pane = pane or win:active_pane()
      if active_pane then win:perform_action(wezterm.action.PopKeyTable, active_pane) end
    end
    win:set_right_status('')
    if state then
      local overrides = win:get_config_overrides() or {}
      overrides.color_scheme = state.original or nil
      win:set_config_overrides(overrides)
    end
  end)
end -- 配色预览开关

-- ========== [08] 中文命令面板 ==========
-- Ctrl + Shift + P 打开；原有英文命令完整保留，只追加中文入口。
-- 来源：wezterm-gui/src/commands.rs 的 compute_default_actions。
-- 不执行这些操作，只有在面板中选择并确认后才会执行。
-- 不翻译程序内部的提示框、搜索框或复制模式专用按键表。
if enabled.chinese_commands then
wezterm.on('augment-command-palette', function(window, pane)
  local act = wezterm.action
  local entries = {}
  -- ----- [08.0] 快捷键标注 -----
  -- 标注默认快捷键及本配置的自定义快捷键，不创建新绑定。
  -- 无快捷键的项目显示“未绑定快捷键”，仍可在面板中选择执行。
  -- 这里只列便于使用的一组按键；之后修改绑定时需同步这里的说明。
  local shortcut_labels = {
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
  }
  local function add(label, action, shortcut)
    local hint = shortcut or shortcut_labels[label] or '未绑定快捷键'
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
  add('窗格：交换位置并跟随当前窗格', act.PaneSelect { mode = 'SwapWithActive' })
  add('窗格：交换位置但焦点留在原位置', act.PaneSelect { mode = 'SwapWithActiveKeepFocus' })
  add('窗格：选择并移到新标签页', act.PaneSelect { mode = 'MoveToNewTab' })
  add('窗格：选择并移到新窗口', act.PaneSelect { mode = 'MoveToNewWindow' })
  add('窗格：顺时针轮换位置', act.RotatePanes 'Clockwise')
  add('标签页：切换到上一个', act.ActivateTabRelative(-1))
  add('标签页：切换到下一个', act.ActivateTabRelative(1))
  add('窗口：切换到上一个', act.ActivateWindowRelative(-1))
  add('窗口：切换到下一个', act.ActivateWindowRelative(1))
  for _, direction in ipairs {
    { 'Left', '左', '←' }, { 'Right', '右', '→' }, { 'Up', '上', '↑' }, { 'Down', '下', '↓' },
  } do
    local horizontal = direction[1] == 'Left' or direction[1] == 'Right'
    local step = horizontal and 4 or 2
    add('窗格：向' .. direction[2] .. '调整大小' .. (horizontal and '四列' or '两行'), act.AdjustPaneSize { direction[1], step }, 'Ctrl + Alt + Shift + ' .. direction[3])
    add('窗格：切换到' .. direction[2] .. '方', act.ActivatePaneDirection(direction[1]), 'Ctrl + Shift + ' .. direction[3])
  end
  add('窗格：切换放大或还原', act.TogglePaneZoomState)
  add('菜单：打开启动菜单', act.ShowLauncher)
  add('菜单：打开标签页列表', act.ShowTabNavigator)

  -- ----- [08.5] 帮助与链接 -----
  add('帮助：打开调试面板', act.ShowDebugOverlay)
  add('链接：打开鼠标位置的链接', act.OpenLinkAtMouseCursor)

  -- ----- [08.6] 配色切换菜单 -----
  -- 命令面板只展示一个入口；全部内置配色放入独立的可搜索列表。
  -- 只改变当前窗口，不写入文件；新窗口仍使用配置中的默认配色。
  add('外观：切换配色', wezterm.action_callback(function(win, active_pane)
    local names = {}
    for name in pairs(wezterm.color.get_builtin_schemes()) do
      table.insert(names, name)
    end
    table.sort(names)
    local choices = {}
    local current = win:effective_config().color_scheme
    for _, name in ipairs(names) do
      table.insert(choices, {
        id = name,
        label = name .. (name == current and '（当前）' or ''),
      })
    end
    win:perform_action(act.InputSelector {
      title = '切换配色（全部内置配色，仅当前窗口）',
      description = '回车应用，Esc 取消，输入名称搜索',
      fuzzy_description = '搜索配色：',
      fuzzy = true,
      choices = choices,
      action = wezterm.action_callback(function(target_window, _, id)
        if not id then return end
        local overrides = target_window:get_config_overrides() or {}
        overrides.color_scheme = id
        target_window:set_config_overrides(overrides)
      end),
    }, active_pane)
  end))
  -- ----- [08.7] 保存默认配色 -----
  -- 仅在主动选择此项时保存；只替换当前配置中的配色赋值行。
  -- 未设置临时配色的窗口会跟随配置重载；其他窗口的试用配色保持不变。
  add('外观：保存当前配色为默认', wezterm.action_callback(function(win, active_pane)
    local function report(message)
      wezterm.log_info(message)
      win:toast_notification('默认配色', message, nil, 4000)
    end
    local scheme = win:effective_config().color_scheme
    if not scheme or not wezterm.color.get_builtin_schemes()[scheme] then
      report('未保存：当前配色不是内置配色。')
      return
    end
    local path = wezterm.config_file
    if not path then
      report('未保存：无法确定当前配置文件。')
      return
    end
    local file, err = io.open(path, 'rb')
    if not file then
      report('未保存：无法读取配置：' .. tostring(err))
      return
    end
    local original = file:read('*a')
    file:close()
    if not original then
      report('未保存：读取配置失败。')
      return
    end
    local updated, count = original:gsub('(\nconfig%.color_scheme%s*=%s*)[^\r\n]+', function(prefix)
      return prefix .. string.format('%q', scheme)
    end)
    if count ~= 1 or not load(updated) then
      report('未保存：配色赋值行不唯一或配置语法异常，请检查配置。')
      return
    end
    if updated ~= original then
      file, err = io.open(path, 'wb')
      if not file then
        report('未保存：无法写入配置：' .. tostring(err))
        return
      end
      local written, write_err = file:write(updated)
      local closed, close_err = file:close()
      if not written or not closed then
        wezterm.log_error('默认配色保存失败；请检查配置文件，日志不记录配置内容。')
        report('保存失败，请检查配置文件：' .. tostring(write_err or close_err))
        return
      end
    end
    -- 保存后移除本窗口的配色覆盖，让它也跟随已保存的默认值。
    local overrides = win:get_config_overrides() or {}
    overrides.color_scheme = nil
    win:set_config_overrides(overrides)
    win:perform_action(act.ReloadConfiguration, active_pane)
    report('默认配色已保存为：' .. scheme)
  end))
  -- ----- [08.8] 实时预览入口 -----
  if start_color_preview then
    add('外观：实时预览配色', wezterm.action_callback(start_color_preview))
  end
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
-- 当前仅运行 Shell 时也询问确认。
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
    -- 只有激活窗口的选中标签使用蓝色；其他窗口的选中标签使用灰色。
    local focused = wezterm.GLOBAL['personal_window_focus_' .. tostring(tab.window_id)] == true
    return {
      { Background = { Color = focused and '#89b4fa' or '#45475a' } },
      { Foreground = { Color = focused and '#11111b' or '#cdd6f4' } },
      { Attribute = { Intensity = 'Bold' } },
      { Text = ' ' .. text .. ' ' },
    }
  end
  return { { Text = ' ' .. text .. ' ' } }
end)

-- ----- [11.3] 独立窗口焦点提示 -----
-- 焦点事件中读取窗口状态，标题回调只读缓存，避免调用异步接口报错。
-- 标签栏左侧同步提示；不占用右侧配色名称，也不通过修改配置触发重载。
local function update_window_focus(win)
  local focused = win:is_focused()
  wezterm.GLOBAL['personal_window_focus_' .. tostring(win:window_id())] = focused
  win:set_left_status(wezterm.format {
    { Foreground = { Color = focused and '#a6e3a1' or '#a6adc8' } },
    { Background = { Color = '#1e1e2e' } },
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
    .. '] ' .. title .. zoomed .. ' — WezTerm'
end)

else
  -- 热重载关闭提示时清空左侧旧文字；默认标题和标签样式由 WezTerm 接管。
  wezterm.on('window-config-reloaded', function(win)
    wezterm.GLOBAL['personal_window_focus_' .. tostring(win:window_id())] = false
    win:set_left_status('')
  end)
end -- enabled.focus_indicator

return config
