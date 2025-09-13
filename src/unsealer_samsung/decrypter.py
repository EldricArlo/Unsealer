# src/unsealer_samsung/decrypter.py

"""
核心解密与解析模块 (Core Decrypter & Parser)

本文件包含了处理三星密码本 (.spass) 文件的所有核心密码学操作和数据解析逻辑。
它的设计原则是“纯粹”：
  - 只负责解密和解析，不处理文件读取、写入或任何命令行交互。
  - 所有的函数都是可独立测试的。

致谢:
本文件的解密逻辑基于 0xdeb7ef 在其开源项目 spass-manager 中的逆向工程工作。
"""

# --- 导入标准库 ---
import base64
import hashlib
import csv
import io
import re
from typing import List, Dict, Any

# --- 导入第三方库 ---
# 导入强大的加密库 pycryptodome，用于AES解密。
try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
except ImportError:
    # 这是一个友好的错误提示，如果用户没有安装依赖，程序会以更明确的方式失败。
    print("错误：核心加密库 'pycryptodome' 未安装。请运行 'pip install pycryptodome'。")
    raise


def clean_android_url(url: str) -> str:
    """
    智能清理和转换URL。

    三星密码本会存储一些特定于安卓应用的链接 (如 android://...)。
    此函数尝试将这些链接转换为更通用的标准网址，同时保留已经是标准网址的链接。

    Args:
        url: 从三星密码本中解析出的原始URL字符串。

    Returns:
        清理或转换后的URL字符串。
    """
    if not url:
        return ""

    # 策略1: 如果URL看起来已经是一个标准的域名 (例如 a.com, b.co.uk)，则直接返回。
    # 使用正则表达式查找一个点后面跟着至少两个字母的模式。
    if re.search(r"\.[a-zA-Z]{2,}", url):
        return url

    # 策略2: 如果是安卓应用链接，则尝试进行转换。
    if url.startswith("android://"):
        try:
            # 应用包名通常位于 "@" 符号之后。
            package_name = url.split("@")[-1]

            # 常见应用包名到域名的手动映射表，可以提高准确性。
            package_to_domain_map = {
                "com.anthropic.claude": "claude.ai",
                "com.google.android.gm": "mail.google.com",
                "com.google.android.googlequicksearchbox": "google.com",
                "com.facebook.katana": "facebook.com",
                "com.twitter.android": "twitter.com",
                "com.instagram.android": "instagram.com",
                "com.zhiliaoapp.musically": "tiktok.com",
                "com.tencent.mm": "weixin.qq.com",
            }
            if package_name in package_to_domain_map:
                return package_to_domain_map[package_name]
            
            # 如果不在映射表中，尝试从包名反向构造域名 (例如 com.example.app -> example.com)。
            parts = package_name.split(".")
            if len(parts) >= 2:
                domain = f"{parts[-2]}.{parts[-1]}"
                # 避免生成像 "google.android" 这样无意义的域名。
                if "android" not in domain:
                    return domain

            # 如果以上方法都失败，则返回原始包名作为最后的备选方案。
            return package_name
        except Exception:
            # 如果在解析过程中发生任何错误，安全地返回原始URL，避免程序崩溃。
            return url

    # 策略3: 如果不属于以上任何情况，直接返回原始字符串。
    return url


def parse_decrypted_content(decrypted_content: str) -> List[Dict[str, Any]]:
    """
    解析解密后的纯文本数据块。

    这个数据块的特点是：
      - 使用 "next_table" 字符串分隔不同的数据表（如密码、地址等）。
      - 表格内容类似于CSV，但使用分号 (;) 作为分隔符。
      - 每个字段的内容都经过了额外的Base64编码（双重编码）。

    Args:
        decrypted_content: AES解密并移除填充后得到的UTF-8字符串。

    Returns:
        一个包含密码条目的列表，每个条目是一个字典。
    """
    imported_entries: List[Dict[str, Any]] = []

    # 1. 按 "next_table" 分割，找到包含登录凭证的数据块。
    blocks = decrypted_content.split("next_table")
    login_data_block = None
    
    # 登录凭证块有一个非常独特的表头，我们可以用它来识别。
    expected_header_start = "_id;origin_url;action_url;"
    for block in blocks:
        # 清理每个块前后的空白字符。
        clean_block = block.strip()
        if clean_block.startswith(expected_header_start):
            login_data_block = clean_block
            break

    # 如果遍历完所有块都没有找到登录数据，则抛出错误。
    if not login_data_block:
        raise ValueError("在解密内容中未找到有效的登录数据块。")

    # 2. 将找到的数据块当作一个CSV文件来处理。
    # 使用 io.StringIO 将字符串模拟成一个内存中的文本文件，以便csv模块可以读取。
    reader = csv.DictReader(io.StringIO(login_data_block), delimiter=";")

    for row in reader:
        # 定义一个内部帮助函数，用于安全地解码每个字段。
        def decode_field(field_name: str) -> str:
            b64_string = row.get(field_name, "").strip()
            
            # "JiYmTlVMTCYmJg==" 是 "&&&NULL&&&" 的Base64编码，代表空值，直接返回空字符串。
            if not b64_string or b64_string == "JiYmTlVMTCYmJg==":
                return ""
            try:
                # 尝试进行Base64解码，还原最原始的信息。
                return base64.b64decode(b64_string).decode("utf-8")
            except Exception:
                # 如果解码失败（例如，字段本身不是Base64编码的），则安全地返回原始值。
                return row.get(field_name, "")

        # 每个凭证条目必须有一个标题，否则我们认为它是无效数据并跳过。
        title = decode_field("title")
        if not title:
            continue

        # 3. 组装成一个结构清晰的字典。
        entry: Dict[str, Any] = {
            "name": title,
            "url": clean_android_url(decode_field("origin_url")),
            "username": decode_field("username_value"),
            "password": decode_field("password_value"),
            "notes": decode_field("credential_memo"),
        }
        imported_entries.append(entry)

    return imported_entries


def decrypt_and_parse(file_content_bytes: bytes, password: str) -> List[Dict[str, Any]]:
    """
    执行从读取文件内容到最终解析出数据的完整流程。

    这是整个解密过程的“总指挥”。

    Args:
        file_content_bytes: .spass文件的原始二进制内容。
        password: 用户的三星账户主密码。

    Returns:
        一个包含所有解析出的密码条目的列表。
    
    Raises:
        ValueError: 如果密码错误、文件损坏或格式不正确，导致解密或解析失败。
    """
    try:
        # 步骤 1: 初始Base64解码
        # .spass 文件内容是一个大的Base64字符串，先将其解码成二进制数据块。
        base64_data = file_content_bytes.decode("utf-8").strip()
        binary_data = base64.b64decode(base64_data)

        # 步骤 2: 拆分组件
        # 根据固定的偏移量，从二进制数据块中分离出盐、IV和加密数据。
        # [ 20字节的盐 | 16字节的IV | 剩余的加密核心数据 ]
        salt = binary_data[:20]
        iv = binary_data[20:36]
        encrypted_data = binary_data[36:]

        # 步骤 3: 派生加密密钥
        # 使用PBKDF2算法从用户密码和盐中派生出真正的加密密钥。
        # 这是一个计算密集型操作，旨在增加暴力破解的难度。
        key = hashlib.pbkdf2_hmac(
            hash_name="sha256",          # 使用的哈希算法
            password=password.encode("utf-8"), # 用户密码
            salt=salt,                         # 从文件中提取的盐
            iterations=70000,                  # 迭代次数，越高越安全
            dklen=32                           # 派生密钥的长度（32字节 = 256位，用于AES-256）
        )

        # 步骤 4: AES解密与移除填充
        # 使用派生出的密钥和IV，通过AES-256-CBC模式解密数据。
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_padded_data = cipher.decrypt(encrypted_data)
        
        # 解密后的数据末尾包含了PKCS#7填充，需要将其移除以获得原始数据。
        decrypted_data = unpad(decrypted_padded_data, AES.block_size, style="pkcs7")

        # 将解密后的二进制数据转换为UTF-8字符串。
        final_content = decrypted_data.decode("utf-8")

        # 步骤 5: 调用解析器进行最终解析
        # 将解密出的纯文本内容交给解析函数，以提取结构化的凭证数据。
        return parse_decrypted_content(final_content)

    except Exception as e:
        # 捕获在上述过程中可能发生的任何异常（如Base64解码错误、填充错误、解密失败等）。
        # 将底层技术性错误包装成一个对用户更友好的ValueError。
        # 绝大多数情况下，这里的失败意味着密码错误或文件损坏。
        raise ValueError(f"解密或解析失败，请检查密码和文件是否正确。原始错误: {e}")