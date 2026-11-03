#!/usr/bin/env bash
set -euo pipefail

source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
config_root="${XDG_CONFIG_HOME:-$HOME/.config}"
data_root="${XDG_DATA_HOME:-$HOME/.local/share}"
config_dir="$config_root/ghostty"
font_dir="$data_root/fonts/JetBrainsMonoNerdFont"

command -v ghostty >/dev/null || { printf '%s\n' '请先安装 Ghostty。' >&2; exit 1; }
command -v fc-cache >/dev/null || { printf '%s\n' '请先安装 fontconfig。' >&2; exit 1; }
(cd -- "$source_dir" && ghostty +validate-config --config-file="$source_dir/config.ghostty")

mkdir -p -- "$config_root" "$font_dir"
config_dir="$(realpath -m -- "$config_dir")"
if [[ "$source_dir" == "$config_dir/"* ]]; then
  printf '%s\n' '请将下载目录移到现有 Ghostty 配置目录之外，再运行安装。' >&2
  exit 1
fi
if [[ "$source_dir" != "$config_dir" ]]; then
  if [[ -e "$config_dir" || -L "$config_dir" ]]; then
    backup_dir="$config_dir.backup-$(date +%Y%m%d-%H%M%S)-$$"
    mv -- "$config_dir" "$backup_dir"
    printf '原配置已备份到：%s\n' "$backup_dir"
  fi
  mkdir -p -- "$config_dir"
  cp -R -- "$source_dir/." "$config_dir/"
fi
temp_config="$config_dir/config.ghostty.tmp-$$"
while IFS= read -r line || [[ -n "$line" ]]; do
  if [[ "$line" == 'background-image = imgs/saber.jpg' ]]; then
    printf 'background-image = %s/imgs/saber.jpg\n' "$config_dir"
  else
    printf '%s\n' "$line"
  fi
done < "$config_dir/config.ghostty" > "$temp_config"
mv -- "$temp_config" "$config_dir/config.ghostty"
cp -- "$source_dir"/fonts/*.ttf "$source_dir/fonts/OFL.txt" "$font_dir/"
fc-cache -f "$font_dir"
ghostty +validate-config --config-file="$config_dir/config.ghostty"
printf '已安装到：%s\n请重新打开 Ghostty。\n' "$config_dir"
