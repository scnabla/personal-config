local wezterm = require 'wezterm'
local config = wezterm.config_builder()
package.path = wezterm.config_dir .. '/?.lua;' .. package.path
require('serial').apply(config)
config.keys = {{key='l',mods='ALT',action=wezterm.action.ShowLauncher}}
return config
