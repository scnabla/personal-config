-- ScnTerm SSH 配置：连接开关、服务器和目录记录路径。
-- Alt+P 等键盘绑定在同目录 keys.lua 中维护。
-- 由同目录 wezterm.lua 的 [01.3.2] 加载；保存后自动重载，不自动连接或断开会话。
local M = {}

-- [开关] SSH 菜单入口
-- true 开启，false 关闭；关闭不主动断开已有连接，也不禁止在终端手动运行 SSH。
local ssh_enabled = false

-- [00.4] SSH 服务器
-- 填写 host、port 和 user 后开启 ssh_enabled；密码不写入配置。
local server = {
  host = 'example.com',
  port = '22',
  user = 'your-user',
}

function M.apply(config)
  -- [目录记录] 保存文件
  -- 目录记录默认与主 Lua 同目录；取消注释可指定其他文件，相对路径以主 Lua 为基准。
  -- config.directory_bookmarks_file = 'scnterm-directory-bookmarks.json'

  -- [01.3.2] SSH 服务器
  -- 使用 WezTerm 内置 SSH，入口自动出现在 Alt + L 启动菜单中。
  -- 仅选择入口后连接；首次连接需核对指纹，密码不写入配置。
  -- None 表示普通 SSH，服务器无需安装 WezTerm；断网不保留会话。
  -- 显式空列表避免关闭后自动从系统 SSH 配置生成入口。
  config.ssh_domains = {}
  if ssh_enabled then
    config.ssh_domains = {
      {
        name = 'SSH: ' .. server.user .. '@' .. server.host .. ':' .. server.port,
        remote_address = server.host .. ':' .. server.port,
        username = server.user,
        multiplexing = 'None',
        connect_automatically = false,
      },
    }
  end -- ssh_enabled
end

return M
