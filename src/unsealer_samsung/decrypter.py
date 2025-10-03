# src/unsealer_samsung/decrypter.py

"""
核心解密与解析模块 (Core Decrypter & Parser) - 精简优化版

[!] 设计理念:
本模块的目标是成为一个强大的“数据提炼层”。它不仅负责解密，更要将原始、混乱的数据
提炼成干净、结构化、易于使用的格式，为上层（展示层）提供最优质的数据源。

[!] 版本 3.1 (改进版) 修改说明:
1.  **消除魔法数字**: 将所有加密相关的硬编码数字（如salt长度、迭代次数）定义为常量，提高代码可读性和可维护性。
2.  **内容精简**: 根据用户反馈，严格收紧了 `logins` 表的字段白名单，彻底过滤掉
    `_id`, `favicon`, `created_time`, `ssl_valid` 及所有 `reserved_*` 等对最终用户
    无意义的元数据字段。
3.  **专注核心**: 现在的输出将100%专注于用户凭证本身，让报告更加清晰、专业。
"""

import base64
import hashlib
import csv
import io
import re
import json
import sys
import binascii
from typing import List, Dict, Any, Union

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
except ImportError:
    print("错误：核心加密库 'pycryptodome' 未安装。请运行 'pip install pycryptodome'。")
    raise

# --- [新] 加密参数常量 ---
# 将“魔法数字”定义为常量，增强代码的可读性和可维护性。
SALT_SIZE = 20
IV_SIZE = 16  # AES-128/256 CBC IV 长度为 16 字节
KEY_SIZE = 32  # AES-256 密钥长度为 32 字节

# [改进] 增加安全注释，解释迭代次数的来源和安全含义
# PBKDF2的迭代次数 (70000) 由三星的加密标准决定，必须使用此数值才能成功解密。
# 注意：在2025年的标准下，70000次迭代的安全性被认为是偏低的。
PBKDF2_ITERATIONS = 70000


# --- 辅助解析函数 (无需改动) ---


def _safe_b64_decode(b64_string: str) -> str:
    if not b64_string or b64_string.strip() in ["", "JiYmTlVMTCYmJg=="]:
        return ""
    try:
        return base64.b64decode(b64_string).decode("utf-8")
    except Exception:
        return b64_string


def _parse_json_field(field_value: str) -> Union[Dict, str]:
    try:
        cleaned_value = field_value.replace('\\"', '"').strip()
        if cleaned_value.startswith('"') and cleaned_value.endswith('"'):
            cleaned_value = cleaned_value[1:-1]
        return json.loads(cleaned_value)
    except (json.JSONDecodeError, TypeError):
        return field_value


def _parse_multi_b64_field(field_value: str) -> List[str]:
    if not field_value:
        return []
    decoded_parts = []
    parts = field_value.split("&&&")
    for part in parts:
        if not part:
            continue
        b64_part = part.split("#")[0]
        decoded = _safe_b64_decode(b64_part)
        if decoded:
            decoded_parts.append(decoded)
    return decoded_parts


def clean_android_url(url: str) -> str:
    if not url or re.search(r"\.[a-zA-Z]{2,}", url) or url.startswith("http"):
        return url
    if url.startswith("android://"):
        try:
            return url.split("@")[-1]
        except Exception:
            return url
    return url


# --- 核心解析逻辑 ---


def parse_decrypted_content(decrypted_content: str) -> Dict[str, List[Dict[str, Any]]]:
    all_tables: Dict[str, List[Dict[str, Any]]] = {}
    blocks = decrypted_content.split("next_table")
    unknown_table_count = 0

    TABLE_SCHEMA = {
        "logins": {
            "fingerprint": ["origin_url", "username_value", "password_value"],
            "json_fields": ["otp"],
            "useful_fields": [
                "title",
                "username_value",
                "password_value",
                "origin_url",
                "credential_memo",
                "otp",
            ],
        },
        "identities": {
            "fingerprint": [
                "id_card_detail",
                "telephone_number_list",
                "email_address_list",
            ],
            "json_fields": ["id_card_detail"],
            "multi_b64_fields": ["telephone_number_list", "email_address_list"],
            "useful_fields": [
                "name",
                "id_card_detail",
                "telephone_number_list",
                "email_address_list",
            ],
        },
        "addresses": {
            "fingerprint": ["full_address", "street_address", "country_code"],
            "useful_fields": [
                "full_name",
                "company_name",
                "street_address",
                "city",
                "state",
                "zipcode",
                "country_code",
                "phone_number",
                "email",
            ],
        },
        "notes": {
            "fingerprint": ["note_title", "note_detail"],
            "useful_fields": ["note_title", "note_detail"],
        },
    }

    for block_index, block in enumerate(blocks):
        clean_block = block.strip()
        if not clean_block or clean_block.count(";") < 2:
            continue

        try:
            reader = csv.DictReader(io.StringIO(clean_block), delimiter=";")
            headers = reader.fieldnames
            if not headers:
                continue

            table_name = None
            schema = {}
            for name, sch in TABLE_SCHEMA.items():
                if all(fp in headers for fp in sch["fingerprint"]):
                    table_name = name
                    schema = sch
                    break

            if not table_name:
                if "24" in headers and len(headers) == 1:
                    continue
                unknown_table_count += 1
                table_name = f"unknown_data_{unknown_table_count}"
                schema = {"useful_fields": headers}

            table_entries: List[Dict[str, Any]] = []
            for row in reader:
                entry = {}
                for field in schema.get("useful_fields", []):
                    raw_value_pre = row.get(field)
                    if raw_value_pre is None:
                        continue

                    raw_value = _safe_b64_decode(raw_value_pre)
                    if not raw_value:
                        continue

                    if field in schema.get("json_fields", []):
                        entry[field] = _parse_json_field(raw_value)
                    elif field in schema.get("multi_b64_fields", []):
                        entry[field] = _parse_multi_b64_field(raw_value)
                    elif field == "origin_url":
                        entry[field] = clean_android_url(raw_value)
                    else:
                        entry[field] = raw_value

                if entry:
                    table_entries.append(entry)

            if table_entries:
                all_tables[table_name] = table_entries
        # [改进] 将静默忽略错误的 "except Exception: continue" 替换为带有警告的捕获
        # 这有助于在不中断程序的情况下，发现并调试潜在的数据格式问题。
        except Exception as e:
            print(
                f"警告: 解析数据块 #{block_index} 时出现问题并已跳过。错误: {e}",
                file=sys.stderr,
            )
            continue

    if not all_tables:
        raise ValueError("解密成功，但在文件中未找到任何有价值的数据。")

    return all_tables


def decrypt_and_parse(
    file_content_bytes: bytes, password: str
) -> Dict[str, List[Dict[str, Any]]]:
    """主解密函数。"""
    try:
        binary_data = base64.b64decode(file_content_bytes.decode("utf-8").strip())

        # [改进] 使用常量替代硬编码的“魔法数字”
        salt_end = SALT_SIZE
        iv_end = salt_end + IV_SIZE

        salt, iv, encrypted_data = (
            binary_data[:salt_end],
            binary_data[salt_end:iv_end],
            binary_data[iv_end:],
        )

        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            PBKDF2_ITERATIONS,
            dklen=KEY_SIZE,
        )

        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_data = unpad(
            cipher.decrypt(encrypted_data), AES.block_size, style="pkcs7"
        )

        return parse_decrypted_content(decrypted_data.decode("utf-8"))

    # [改进] 增强异常处理的安全性，避免泄露潜在的敏感信息
    except (ValueError, binascii.Error):
        # 这些通常是密码错误或文件格式不正确的直接标志
        raise ValueError(
            "解密失败。请仔细检查您的密码是否正确，并确认文件是有效的三星密码本备份。"
        )
    except Exception as e:
        # 捕获所有其他意外错误，但不暴露原始异常信息，防止敏感数据泄露。
        # 这种做法在处理加密和敏感数据时是一种良好的安全实践。
        # 具体的错误细节（e）可以在调试时打印，但不应直接抛给最终用户。
        raise ValueError("解密或解析过程中发生未知内部错误。文件可能已损坏。")