$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (!(Test-Path '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw '创建项目虚拟环境失败' }
}
& .venv\Scripts\python.exe -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw '安装项目依赖失败' }
& cargo build --release --locked --manifest-path validator/Cargo.toml
if ($LASTEXITCODE -ne 0) { throw '正则检查器构建失败' }
& .venv\Scripts\python.exe -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw '自动测试失败' }
& .venv\Scripts\python.exe -m PyInstaller --noconfirm --windowed --onedir --name ScnTermConfig --add-binary 'validator\target\release\scnterm-config-validator.exe;.' --collect-all tree_sitter_lua --copy-metadata tree-sitter --copy-metadata tree-sitter-lua --icon assets/scnterm.ico --add-data 'assets/scnterm.ico;assets' run.py
if ($LASTEXITCODE -ne 0) { throw 'Windows 打包失败' }
foreach ($file in @('README.md','LICENSE','THIRD_PARTY.md')) { Copy-Item $file dist\ScnTermConfig }
Copy-Item examples dist\ScnTermConfig\examples -Recurse -Force
& .venv\Scripts\python.exe scripts/package_metadata.py
if ($LASTEXITCODE -ne 0) { throw '生成包信息失败' }
Write-Output 'dist\ScnTermConfig\ScnTermConfig.exe'
