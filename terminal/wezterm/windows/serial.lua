-- ScnTerm 串口配置：连接参数、文本日志和关键词高亮。
-- 由同目录 wezterm.lua 的 [01.3.3] 加载，节编号与主配置目录一致。
-- 保存后自动重载；连接参数用于新连接，日志公共设置用于下一次开始记录。
local wezterm = require 'wezterm'
local is_windows = wezterm.target_triple:find('windows', 1, true) ~= nil
local M = {}

function M.apply(config)
  -- [01.3.3] UART 串口
  -- 与 SSH 共用 Alt + L 启动菜单。
  -- 根据日志动作判断功能是否可用，旧版 scnterm 保留原来的串口连接配置。
  local serial_logging_supported = pcall(function()
    return wezterm.action.StartSerialLogging
  end)
  config.serial_ports = {}
  if is_windows then
    local serial_ports = {
      {
        name = 'UART: RK3568 (COM3)',
        port = 'COM3',
        baud = 1500000,
        data_bits = 8,
        parity = 'None',
        stop_bits = 1,
        flow_control = 'None',
        log_on_connect = true, -- 新连接自动记录；设为 false 后通过 Alt + L 手动开始
      },
    }
    if not serial_logging_supported then
      for _, serial in ipairs(serial_ports) do serial.log_on_connect = nil end
    end
    config.serial_ports = serial_ports
  end

  -- [01.3.4] 串口日志
  -- 适用于支持串口日志的 scnterm；所有串口共用以下设置。
  -- 省略 directory 时，直接保存在主 Lua 所在目录；相对路径也以该目录为基准。
  if serial_logging_supported then
    config.serial_logging = {
      max_file_size_mb = 100, -- 达到 100 MB 后分文件，后续文件依次追加 -1、-2
      timestamps = true,     -- 电脑接收时间，例如 [20261108-22:36:11.895]
      -- directory = 'serial-logs',
    }
  end
  -- 在串口窗格中按 Alt + L 可手动启停；每次开始均新建文件，停止期间的输出不补录。
  -- 公共设置重载后用于下一次开始记录，已有记录继续使用开始时的设置。

  -- [01.3.5] 串口关键词高亮
  -- 检查字段是否受支持；旧版 ScnTerm 和原版 WezTerm 跳过此段。
  local serial_highlighting_supported = pcall(function()
    local probe = wezterm.config_builder()
    probe.serial_highlighting = { rules = {} }
  end)
  if serial_highlighting_supported then
    config.serial_highlighting = {
      -- 默认不区分大小写；同一位置命中多组时，靠前的组优先。
      rules = {
        {
          foreground = '#FF6B81',
          keywords = { '错误', '失败', '[故障]' },
          patterns = { [[\b(?:error|fail(?:ed|ure)?|fatal)\b]] },
        },
        {
          foreground = '#FFB52E',
          keywords = { '警告', '超时' },
          patterns = { [[\bwarn(?:ing)?\b]], [[\btime(?:d)?[ -]?out\b]] },
        },
      },
    }
  end
  -- 所有串口共用规则，仅匹配文字变色；不改变日志、复制文本及设备原始数据。
  -- 保存后自动重载，当前画面和滚动历史随之更新；清空 rules 后恢复设备原色。
end

return M
