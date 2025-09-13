# src/unsealer_samsung/cli.py

"""
命令行界面模块 (Command-Line Interface)

本文件是 Unsealer 工具的用户交互入口。它负责：
  - 使用 argparse 解析命令行参数（如输入文件、密码、输出格式等）。
  - 读取输入的 .spass 文件。
  - 调用 decrypter 模块中的核心函数来执行解密。
  - 根据用户指定的格式，将解密后的数据写入输出文件（CSV, TXT, MD）。
  - 处理各种预期的错误（如文件未找到、密码错误）并向用户提供清晰的反馈。
"""

import argparse
import sys
import csv
from pathlib import Path

# 从同一个包内的 decrypter 模块导入核心解密函数。
# 这里的 "." 表示相对导入。
from .decrypter import decrypt_and_parse

# --- 数据保存函数 ---

def save_as_csv(data: list, output_file: Path):
    """将数据保存为CSV文件。"""
    if not data: return # 如果没有数据，则不创建文件。
    # 使用 'w' 模式打开文件，newline='' 是处理CSV文件的标准做法，防止出现空行。
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        # 使用 csv.DictWriter 可以方便地将字典列表写入CSV。
        # fieldnames 从第一条数据中获取表头。
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader() # 写入表头
        writer.writerows(data)   # 写入所有数据行

def save_as_txt(data: list, output_file: Path):
    """将数据保存为人类可读的TXT文件。"""
    if not data: return
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, entry in enumerate(data, 1): # 从1开始计数
            f.write(f"--- 条目 {i} ---\n")
            f.write(f"名称: {entry['name']}\n")
            f.write(f"网址: {entry['url']}\n")
            f.write(f"用户: {entry['username']}\n")
            f.write(f"密码: {entry['password']}\n")
            f.write(f"备注: {entry['notes']}\n\n")

def save_as_md(data: list, output_file: Path):
    """将数据保存为Markdown表格文件。"""
    if not data: return
    with open(output_file, 'w', encoding='utf-8') as f:
        # 写入Markdown表格的表头和分隔线。
        f.write("| 名称 | 网址 | 用户 | 密码 | 备注 |\n")
        f.write("|------|------|------|------|------|\n")
        for entry in data:
            # 清理数据：将内容中的 `|` 替换为 `\|`，防止破坏表格结构。
            # 同时将换行符替换为空格。
            clean_entry = {k: v.replace('|', '\\|').replace('\n', ' ') for k, v in entry.items()}
            f.write(f"| {clean_entry['name']} | {clean_entry['url']} | {clean_entry['username']} | {clean_entry['password']} | {clean_entry['notes']} |\n")

# --- 主函数 ---

def main():
    """
    命令行工具的主入口函数。
    """
    # 1. 设置命令行参数解析器
    parser = argparse.ArgumentParser(
        description="Unsealer (Samsung): 解密三星密码本 (.spass) 文件并导出内容。",
        # epilog 会显示在帮助信息的末尾，通常用于展示用法示例。
        epilog="用法示例: unsealer my_backup.spass \"MyP@ssw0rd\" -f csv -o decrypted_data.csv"
    )
    
    # 定义必须的位置参数
    parser.add_argument("input_file", type=Path, help="输入的 .spass 文件路径。")
    parser.add_argument("password", type=str, help="您的三星账户主密码。")
    
    # 定义可选参数
    parser.add_argument(
        "-f", "--format", 
        choices=["csv", "txt", "md"], # 限制可选值
        default="csv",                # 设置默认值
        help="输出文件格式 (默认为: csv)。"
    )
    parser.add_argument(
        "-o", "--output", 
        type=Path, 
        help="输出文件的路径 (默认: 与输入文件同名，扩展名不同)。"
    )
    
    # 解析用户在命令行中输入的参数。
    args = parser.parse_args()

    # 2. 逻辑处理
    # 如果用户没有指定输出文件名，则根据输入文件名自动生成一个。
    if not args.output:
        # .with_suffix() 方法可以方便地替换文件扩展名。
        args.output = args.input_file.with_suffix(f'.{args.format}')

    try:
        # 打印状态信息，给用户反馈。
        print(f"[*] 正在读取文件: {args.input_file}")
        # 必须以二进制模式 ('rb') 读取文件，因为加密数据是二进制的。
        file_content = args.input_file.read_bytes()
        
        print("[*] 正在使用提供的密码进行解密...")
        # 调用核心解密函数。
        decrypted_data = decrypt_and_parse(file_content, args.password)
        
        # 检查解密结果。
        if not decrypted_data:
            print("[!] 解密成功，但文件中未找到任何登录凭证条目。")
            return # 正常退出

        print(f"[*] 成功找到 {len(decrypted_data)} 条凭证。正在保存到 {args.output} (格式: {args.format.upper()})...")
        
        # 根据用户选择的格式，调用相应的保存函数。
        if args.format == 'csv':
            save_as_csv(decrypted_data, args.output)
        elif args.format == 'txt':
            save_as_txt(decrypted_data, args.output)
        elif args.format == 'md':
            save_as_md(decrypted_data, args.output)
            
        print(f"[+] 操作成功！数据已保存到 {args.output}")

    # 3. 错误处理
    # 捕获特定类型的错误，并向用户显示友好的错误信息。
    except FileNotFoundError:
        print(f"[错误] 输入文件未找到: {args.input_file}", file=sys.stderr)
        sys.exit(1) # 以错误码 1 退出程序。
    except ValueError as e:
        # 这个 ValueError 是由 decrypter 模块在解密失败时抛出的。
        print(f"[错误] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # 捕获所有其他意外错误，以防程序崩溃。
        print(f"[严重错误] 发生未知错误: {e}", file=sys.stderr)
        sys.exit(1)

# 当这个文件作为主程序直接运行时 (例如 python cli.py)，__name__ 的值是 '__main__'。
# 这使得文件既可以被其他模块导入，也可以独立运行。
if __name__ == '__main__':
    main()