# Unsealer (Samsung)

[![PyPI Version](https://img.shields.io/badge/pypi-v0.1.0-blue)](https://pypi.org/project/unsealer-samsung/)
[![Python Versions](https://img.shields.io/badge/python-3.7+-brightgreen.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Unsealer (Samsung)** is a simple, open-source command-line tool to decrypt Samsung Pass (`.spass`) backup files. It allows you to securely export your stored credentials into human-readable formats like CSV, TXT, or Markdown, giving you control over your own data.

<br>

> [!CAUTION]
> **Disclaimer & Security Notice**
>
> This tool is based on reverse engineering of the `.spass` file format and is provided for personal, educational, and data recovery purposes only. It is not an official Samsung product.
>
> - **Use it at your own risk.** The author is not responsible for any data loss or security breaches.
> - **Handle your password data with extreme care.** Your master password and decrypted files contain highly sensitive information. Do not share them or store them in unsecured locations.
> - **This tool runs entirely offline.** It does not connect to the internet or send your data anywhere.

<br>

## Key Features

-   **Secure Offline Decryption**: All operations are performed locally on your machine.
-   **Multiple Export Formats**: Save your data as CSV (for spreadsheets), plain TXT, or a Markdown table.
-   **Easy to Use**: A straightforward command-line interface.
-   **Cross-Platform**: Runs on Windows, macOS, and Linux (anywhere Python is installed).
-   **Open Source**: The code is fully transparent and available for audit.

---

## Installation

You need **Python 3.7+** and **Git** installed on your system to install this tool directly from its GitHub repository.

Open your terminal or command prompt and run the following command:

```bash
pip install git+https://github.com/EldricArlo/Unsealer.git
```

This command will:
1.  Download the source code from GitHub.
2.  Automatically install the required `pycryptodome` library.
3.  Add the `unsealer` command to your system's PATH, making it available everywhere.

> [!TIP]
> If the `pip` command is not found, try using `pip3` instead: `pip3 install git+...`

---

## Usage

The tool requires two main arguments: the path to your `.spass` file and your Samsung account master password.

### Basic Command Structure

```bash
unsealer <path_to_your_spass_file> "<your_master_password>" [options]
```

> [!IMPORTANT]
> **Always wrap your password in quotes (`"`)!**
> This prevents special characters in your password (like `!`, `$`, `&`, etc.) from being misinterpreted by your command line shell.

### Options

| Flag                 | Long Version         | Description                                                                                              |
| -------------------- | -------------------- | -------------------------------------------------------------------------------------------------------- |
| `input_file`         | _(N/A)_              | **(Required)** The path to your `.spass` backup file.                                                    |
| `password`           | _(N/A)_              | **(Required)** Your Samsung account master password.                                                     |
| `-f`                 | `--format`           | The output format. Choices: `csv`, `txt`, `md`. **Default is `csv`**.                                      |
| `-o`                 | `--output`           | The path for the output file. If not specified, it defaults to the input filename with the new extension. |

### Examples

**1. Decrypt and Save as CSV (Default)**

This is the most common use case. It will decrypt `my_samsung_data.spass` and create a `my_samsung_data.csv` file in the same folder.

```bash
unsealer ./my_samsung_data.spass "MyP@ssw0rd!123"
```

**2. Decrypt and Save as a Plain Text File**

This command specifies the format as `txt` and sets a custom output file name.

```bash
unsealer C:\Users\Me\Desktop\samsung.spass "MyP@ssw0rd!123" -f txt -o C:\Users\Me\Desktop\decrypted.txt
```

**3. Decrypt and Save as a Markdown Table**

This exports the data into a clean, readable Markdown table named `report.md`.

```bash
unsealer ./my_samsung_data.spass "MyP@ssw0rd!123" --format md --output report.md
```

---

## Acknowledgements

The core decryption logic used in this project would not have been possible without the excellent reverse engineering work done by **0xdeb7ef** in the [**spass-manager**](https://github.com/0xdeb7ef/spass-manager) project. Our Python implementation is a direct port of the logic discovered and documented there. We are grateful for their contribution to the open-source community.

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.