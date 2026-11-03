param(
    [string]$Destination = (Join-Path $env:USERPROFILE '.config\wezterm')
)

$ErrorActionPreference = 'Stop'
$sourceDir = [System.IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\')
$targetDir = [System.IO.Path]::GetFullPath($Destination).TrimEnd('\')
$defaultDir = [System.IO.Path]::GetFullPath((Join-Path $env:USERPROFILE '.config\wezterm')).TrimEnd('\')
$stamp = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8)

foreach ($relative in @('wezterm.lua', 'fonts\OFL.txt', 'imgs\saber.jpg', 'fonts\JetBrainsMonoNerdFontMono-Regular.ttf', 'fonts\JetBrainsMonoNerdFontMono-Bold.ttf', 'fonts\JetBrainsMonoNerdFontMono-Italic.ttf', 'fonts\JetBrainsMonoNerdFontMono-BoldItalic.ttf')) {
    if (-not (Test-Path -LiteralPath (Join-Path $sourceDir $relative) -PathType Leaf)) {
        throw "缺少文件：$relative。请下载完整的 wezterm 目录。"
    }
}
if ($sourceDir.StartsWith($targetDir + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
    throw '请将下载目录移到现有 WezTerm 配置目录之外，再运行安装。'
}
if ($sourceDir -ne $targetDir) {
    if (Test-Path -LiteralPath $targetDir) {
        $backupDir = $targetDir + '.backup-' + $stamp
        Move-Item -LiteralPath $targetDir -Destination $backupDir
        Write-Output "原配置已备份到：$backupDir"
    }
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Get-ChildItem -LiteralPath $sourceDir -Force | Copy-Item -Destination $targetDir -Recurse -Force
}
if ($targetDir -eq $defaultDir) {
    $legacy = Join-Path $env:USERPROFILE '.wezterm.lua'
    if (Test-Path -LiteralPath $legacy) {
        Move-Item -LiteralPath $legacy -Destination ($legacy + '.backup-' + $stamp)
        Write-Output '旧版 .wezterm.lua 已备份。'
    }
}
Write-Output "已安装到：$targetDir"
Write-Output '请重新打开 WezTerm。'
