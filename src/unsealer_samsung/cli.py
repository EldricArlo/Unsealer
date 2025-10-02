# src/unsealer_samsung/cli.py

"""
命令行界面模块 (Command-Line Interface)

本文件是 Unsealer 工具的用户交互入口。它负责：
  - 使用 argparse 解析命令行参数（如输入文件、密码、输出格式等）。
  - 读取输入的 .spass 文件。
  - 调用 decrypter 模块中的核心函数来执行解密。
  - 根据用户指定的格式，将解密后的数据写入输出文件（CSV, TXT, MD）。
  - 处理各种预期的错误（如文件未找到、密码错误）并向用户提供清晰的反馈。
  - [设计] 使用 'rich' 和 'pyfiglet' 库，以“技术优雅”为理念，提供美观专业的终端输出。
"""

import argparse
import sys
import csv
from pathlib import Path
from datetime import datetime

# --- 从 rich 导入所需组件 ---
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel
from rich.box import ROUNDED
from rich.align import Align

# --- 导入 pyfiglet 库 ---
import pyfiglet

# 从同一个包内的 decrypter 模块导入核心解密函数。
from .decrypter import decrypt_and_parse

# --- 初始化 rich 控制台 ---
console = Console(stderr=True)

# --- 数据保存函数 (美学重构) ---

def save_as_csv(data: list, output_file: Path):
    """将数据保存为CSV文件。"""
    if not data: return
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

def save_as_txt(data: list, output_file: Path, banner: str):
    """
    [设计] 将数据保存为一份排版精美的TXT报告。
    """
    if not data: return
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(banner)
        f.write("─" * 80 + "\n")
        f.write(f"报告生成于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("─" * 80 + "\n\n")
        labels = ["名称", "网址", "用户", "密码", "备注"]
        max_label_width = max(len(label) for label in labels) + 1
        for i, entry in enumerate(data, 1):
            f.write(f"--- [ 条目 {i} ] " + "─" * (65 - len(str(i))) + "\n")
            f.write(f"{'名称:':<{max_label_width}} {entry['name']}\n")
            f.write(f"{'网址:':<{max_label_width}} {entry['url']}\n")
            f.write(f"{'用户:':<{max_label_width}} {entry['username']}\n")
            f.write(f"{'密码:':<{max_label_width}} {entry['password']}\n")
            f.write(f"{'备注:':<{max_label_width}} {entry['notes']}\n\n")
        f.write("─" * 80 + "\n")
        f.write("--- 报告结束 ---\n")

def save_as_md(data: list, output_file: Path, banner: str):
    """
    [优化与强化] 将数据保存为卡片式 Markdown 文档，并使用业界标准方法确保Banner完美对齐。
    """
    if not data: return
    with open(output_file, 'w', encoding='utf-8') as f:
        
        # --- 按照你的最新要求进行修改 ---
        # 1. 清理 banner 字符串首尾的空行。
        clean_banner = banner.strip()
        
        # 2. 将清理后的多行艺术字拆分成一个列表，每一行是列表中的一个元素。
        lines = clean_banner.split('\n')
        
        # 3. [核心修改] 检查列表不为空，然后给第一行（也就是文件的第二行）前面加上三个空格。
        if lines:
            lines[0] = "   " + lines[0]
        
        # 4. 将修改后的行列表重新组合成一个完整的字符串。
        modified_banner = "\n".join(lines)
        
        # 5. 最后，将这个手动调整过的 banner 写入代码块中。
        f.write(f"```\n{modified_banner}\n```\n\n")

        # 遍历每个凭证条目，并为每个条目创建一个独立的区块（这部分逻辑保持不变）
        for entry in data:
            f.write(f"## {entry['name']}\n\n")
            f.write(f"- **网址**: `{entry['url']}`\n")
            f.write(f"- **用户**: `{entry['username']}`\n")
            f.write(f"- **密码**: `{entry['password']}`\n")
            if entry['notes']:
                f.write(f"- **备注**: {entry['notes']}\n")
            
            f.write("\n---\n\n")
        
        f.write(f"\n*报告由 Unsealer 生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

# --- 辅助函数 ---

def _display_banner() -> str:
    """生成、显示美观的Banner，并返回纯文本版本以供文件写入。"""
    # 修复了截图中的字体问题，改用更兼容终端的字体
    plain_banner = pyfiglet.figlet_format("Unsealer", font="slant") + "  for Samsung Pass"
    
    title_panel = Panel(
        Align.center(f"[bold cyan]{plain_banner}[/bold cyan]"),
        box=ROUNDED,
        border_style="cyan",
        title="[bold white]Unsealer[/bold white]",
        subtitle="[cyan]v.2.0[/cyan]"
    )
    console.print(title_panel)
    return plain_banner

def _setup_arg_parser() -> argparse.ArgumentParser:
    """配置并返回命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="一个用于解密三星密码本 (.spass) 文件的优雅工具。",
        epilog="用法示例: unsealer my_backup.spass -f txt -o decrypted.txt"
    )
    parser.add_argument("input_file", type=Path, help="输入的 .spass 文件路径。")
    parser.add_argument("password", type=str, nargs='?', default=None, help="您的三星账户主密码 (可选)。")
    parser.add_argument(
        "-f", "--format", choices=["csv", "txt", "md"], default="csv", help="输出文件格式 (默认为: csv)。"
    )
    parser.add_argument(
        "-o", "--output", type=Path, help="输出文件的路径 (默认: 与输入文件同名，扩展名不同)。"
    )
    parser.add_argument(
        "--preview", action="store_true", help="在终端中用表格预览前5条结果，而不是保存到文件。"
    )
    return parser

def _process_decryption(args: argparse.Namespace, plain_banner: str):
    """执行核心的解密、处理和保存逻辑，并处理相关错误。"""
    try:
        console.print(f"[cyan]> [/cyan]正在读取文件: [bold magenta]{args.input_file}[/bold magenta]")
        file_content = args.input_file.read_bytes()

        decrypted_data = None
        with console.status("[bold green]正在解密，请稍候...[/bold green]", spinner="aesthetic"):
            decrypted_data = decrypt_and_parse(file_content, args.password)

        if not decrypted_data:
            console.print("[yellow]! [/yellow]解密成功，但文件中未找到任何登录凭证条目。")
            return

        console.print(f"[green]✓ [/green]成功找到 [bold yellow]{len(decrypted_data)}[/bold yellow] 条凭证。")

        if args.preview:
            table = Table(
                title="[bold]数据预览 (前5条)[/bold]", box=ROUNDED, border_style="cyan", header_style="bold cyan"
            )
            table.add_column("名称", style="white", no_wrap=True)
            table.add_column("网址", style="bright_blue")
            table.add_column("用户", style="green")
            table.add_column("密码", style="magenta")
            for entry in decrypted_data[:5]:
                table.add_row(entry['name'], entry['url'], entry['username'], entry['password'])
            console.print(table)
            console.print("[dim]> 预览模式不会保存任何文件。[/dim]")
            return

        console.print(f"[cyan]> [/cyan]正在保存到 [bold magenta]{args.output}[/bold magenta] (格式: [yellow]{args.format.upper()}[/yellow])...")
        
        save_dispatch = {
            'csv': save_as_csv,
            'txt': lambda data, path: save_as_txt(data, path, plain_banner),
            'md': lambda data, path: save_as_md(data, path, plain_banner),
        }
        save_dispatch[args.format](decrypted_data, args.output)
        
        console.print(f"\n[bold green]✓ 操作成功！[/bold green] 数据已保存至 [bold magenta]{args.output}[/bold magenta]")

    except FileNotFoundError:
        console.print(f"[bold red]✗ 错误:[/bold red] 输入文件未找到: [magenta]{args.input_file}[/magenta]")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[bold red]✗ 错误:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]✗ 发生未知错误:[/bold red] {e}")
        console.print_exception(show_locals=False)
        sys.exit(1)

# --- 主函数 ---

def main():
    """
    命令行工具的主入口函数。
    """
    plain_banner = _display_banner()
    
    parser = _setup_arg_parser()
    args = parser.parse_args()

    if not args.password:
        args.password = Prompt.ask("[bold yellow]> [/bold yellow]请输入您的三星账户主密码", password=True)

    if not args.output and not args.preview:
        args.output = args.input_file.with_suffix(f'.{args.format}')

    _process_decryption(args, plain_banner)

if __name__ == '__main__':
    main()