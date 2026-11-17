# 第三方依赖

| 组件 | 用途 | 许可证与来源 |
| --- | --- | --- |
| Python、Tkinter | 程序运行与独立窗口 | [Python PSF](https://docs.python.org/3/license.html)、[Tcl/Tk](https://www.tcl-lang.org/software/tcltk/license.html) |
| tree-sitter、tree-sitter-lua | 解析 Lua 并保留原文位置 | MIT；[Python 绑定](https://github.com/tree-sitter/py-tree-sitter)、[Lua 语法](https://github.com/tree-sitter-grammars/tree-sitter-lua) |
| regex | 独立检查 Rust 正则语法 | MIT 或 Apache-2.0；[源码](https://github.com/rust-lang/regex) |
| serde_json | 校验程序的输入输出 | MIT 或 Apache-2.0；[源码](https://github.com/serde-rs/json) |
| PyInstaller | Windows 打包 | GPL-2.0-or-later，附发布包例外；[许可证](https://pyinstaller.org/en/stable/license.html) |

Python 依赖版本固定在 requirements 文件中，Rust 的直接及间接依赖固定在 `validator/Cargo.lock`。终端程序不是本项目的构建或运行依赖。

发布包的 `licenses/` 目录保留已分发组件的许可证。应用图标沿用 ScnTerm 项目的个人图标，仅复制静态资源，不引用终端代码。

Tcl 8.6 的分发许可证保存在 `assets/licenses/tcl-license.terms`，来源为 [Tcl 官方仓库](https://github.com/tcltk/tcl/blob/core-8-6-branch/license.terms)。
