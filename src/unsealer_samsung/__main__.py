# src/unsealer_samsung/__main__.py

"""
包可执行入口 (Package Executable Entry Point)

当用户使用 `python -m unsealer_samsung` 命令时，Python解释器会寻找并执行这个文件。
它的作用是调用 cli 模块中的 main 函数，使得整个包可以像一个独立的应用一样被运行。
"""

from .cli import main

if __name__ == "__main__":
    main()