# Unsealer (Samsung)

[![PyPI Version](https://img.shields.io/badge/pypi-v0.2.0-blue)](https://pypi.org/project/unsealer-samsung/)
[![Python Versions](https://img.shields.io/badge/python-3.7+-brightgreen.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Telegram](https://img.shields.io/badge/Telegram-%235AA9E6?logo=telegram&labelColor=FFFFFF)](https://t.me/+dHEs5v_mLfNjYjk0)

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
-   **User-Friendly CLI**: An enhanced command-line interface with colors, spinners, and progress indicators.
-   **Safe Password Input**: Prompts for your password securely without showing it on screen.
-   **Data Preview**: Quickly preview your decrypted data directly in the terminal without saving a file.
-   **Cross-Platform**: Runs on Windows, macOS, and Linux (anywhere Python is installed).
-   **Open Source**: The code is fully transparent and available for audit.

---

## How to Get Your `.spass` File

The `.spass` backup file is typically created using Samsung's **Smart Switch** application on your PC or Mac.

1.  **Connect Your Phone**: Connect your Samsung phone to your computer via a USB cable.
2.  **Open Smart Switch**: Launch the Smart Switch application on your computer.
3.  **Perform a Backup**:
    *   Click on the "Backup" option.
    *   You may be prompted to select which items to back up. Ensure that **"Settings"** or a similar category containing passwords is selected.
    *   Let the backup process complete.
4.  **Locate the File**:
    *   After the backup is finished, navigate to the Smart Switch backup folder on your computer.
    *   Inside the backup folder, look for a path similar to `\SAMSUNG\PASS\backup\`.
    *   You should find your backup file there, usually named with a timestamp, e.g., `20250913_103000.spass`.

This is the file you will use with Unsealer.

---

## Installation

You need **Python 3.7+** installed on your system.

### 1. Recommended Method (via PyPI)

This is the simplest and most direct way. Open your terminal or command prompt and run:

```bash
pip install unsealer-samsung
```

> [!TIP]
> If the `pip` command is not found, try using `pip3` instead: `pip3 install unsealer-samsung`

### 2. Alternative Method (Latest Version from GitHub)

If you want to install the absolute latest (potentially unstable) version directly from the source code, you will also need **Git**.

```bash
pip install git+https://github.com/EldricArlo/Unsealer.git
```

---

## Usage

The tool requires the path to your `.spass` file. You can provide your password directly or wait for the tool to ask for it securely.

### Basic Command Structure

```bash
unsealer <path_to_your_spass_file> "[your_master_password]" [options]
```

> [!IMPORTANT]
> If you provide your password as an argument, **always wrap your password in quotes (`"`)!**
> This prevents special characters in your password (like `!`, `$`, `&`, etc.) from being misinterpreted by your command line shell.

### Options

| Flag                 | Long Version         | Description                                                                                              |
| -------------------- | -------------------- | -------------------------------------------------------------------------------------------------------- |
| `input_file`         | _(N/A)_              | **(Required)** The path to your `.spass` backup file.                                                    |
| `password`           | _(N/A)_              | **(Optional)** Your Samsung account master password. If not provided, the tool will securely prompt you for it. |
| `-f`                 | `--format`           | The output format. Choices: `csv`, `txt`, `md`. **Default is `csv`**.                                      |
| `-o`                 | `--output`           | The path for the output file. If not specified, it defaults to the input filename with the new extension. |
|                      | `--preview`          | Displays the first 5 entries as a table in the terminal instead of saving a file.                         |


### Examples

**1. Recommended Secure Usage (Interactive Password Prompt)**

Simply run the command with the file path. The tool will then securely ask for your password. This is the safest way to use it.

```bash
unsealer ./my_samsung_data.spass
# The program will now prompt:
# Please enter your Samsung account master password: ****
```

**2. Decrypt and Save as CSV (Password as Argument)**

This will decrypt `my_samsung_data.spass` and create `my_samsung_data.csv` in the same folder.

```bash
unsealer ./my_samsung_data.spass "MyP@ssw0rd!123"
```

**3. Preview Data Directly in the Terminal**

If you just want to quickly check the contents without creating a file, use the `--preview` flag.

```bash
unsealer ./samsung.spass "MyP@ssw0rd!123" --preview
```

**4. Save as a Markdown Table with a Custom Name**

This exports the data into a clean, readable Markdown table named `report.md`.

```bash
unsealer C:\backups\samsung.spass "MyP@ssw0rd!123" --format md --output report.md
```

---

## FAQ (Frequently Asked Questions)

**Q: I'm getting a "decryption or parsing failed" error. What's wrong?**
A: This is the most common error and it almost always means one of three things:
   1.  **Incorrect Password**: You might have mistyped your Samsung account master password. Passwords are case-sensitive. Please double-check it carefully.
   2.  **Corrupted File**: The `.spass` file itself might be damaged or incomplete from the backup process. Try creating a fresh backup from your phone using Smart Switch.
   3.  **Incompatible File Format**: Samsung may have updated the encryption or data structure within the `.spass` file in a newer version of Smart Switch or Samsung Pass. Since this tool is based on reverse engineering, a format change could render it unable to read newer files until the tool itself is updated.

**Q: Is this tool safe? Can it steal my passwords?**
A: This tool is designed with security as a top priority.
   - It runs **100% offline**. It does not and cannot send any of your data over the internet.
   - It is **open source**, meaning anyone can inspect the code (`decrypter.py`) to verify that it only performs local decryption.

**Q: Will this tool work with future versions of Samsung Pass?**
A: **Maybe not.** This tool is based on the file format used by Samsung as of the time of its development. If Samsung decides to change its encryption method in a future update, this tool may stop working until it is updated by the community.

---

## How It Works (Technical Details)

For those interested in the technical specifics, the decryption process follows these key steps, based on the reverse engineering of the `.spass` format:

1.  **Base64 Decode**: The entire `.spass` file is a Base64 encoded string. The first step is to decode it into raw binary data.
2.  **Extract Components**: The binary data is split into three parts: a 20-byte **salt**, a 16-byte **initialization vector (IV)**, and the remaining **encrypted data**.
3.  **Derive Key**: Your master password is not the direct key. Instead, the tool uses the **PBKDF2-SHA256** algorithm. It combines your password with the salt and performs 70,000 rounds of hashing to derive a secure 256-bit (32-byte) AES key. This makes brute-force attacks extremely difficult.
4.  **AES Decrypt**: The derived key and IV are used to decrypt the data using the **AES-256-CBC** cipher.
5.  **Parse Data**: The decrypted content is a large text block. The tool parses this block, finds the login credentials table, and decodes each field (which is also Base64 encoded) to retrieve your final data.

---

## Acknowledgements

The core decryption logic used in this project would not have been possible without the excellent reverse engineering work done by **0xdeb7ef** in the [**spass-manager**](https://github.com/0xdeb7ef/spass-manager) project. Our Python implementation is a direct port of the logic discovered and documented there. We are grateful for their contribution to the open-source community.

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
