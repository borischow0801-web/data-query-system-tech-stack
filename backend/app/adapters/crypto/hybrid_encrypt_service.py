"""
SM2 + SM4 混合加解密服务。
流程：生成 SM4 密钥 → SM4 加密 data → SM2 加密 SM4 密钥 → 组装请求；
响应：取 data 密文 → SM4 解密 → 返回明文。
所有加密逻辑仅在此模块与 sm2/sm4_service 内，业务层只调用本类。
"""
from app.core.exceptions import CryptoError
from app.adapters.crypto.sm2_service import Sm2Service
from app.adapters.crypto.sm4_service import Sm4Service


class HybridEncryptService:
    """混合加密：SM4 加密业务数据，SM2 加密 SM4 密钥。"""

    def __init__(
        self,
        sm2_public_key_hex: str,
        sm2_cipher_mode: str = "C1C3C2",
        sm4_mode: str = "ECB",
        sm4_padding: str = "PKCS5",
        cipher_encoding: str = "HEX",
    ):
        self.sm2_public_key_hex = sm2_public_key_hex
        self.sm2_cipher_mode = sm2_cipher_mode
        self.sm4_mode = sm4_mode
        self.sm4_padding = sm4_padding
        self.cipher_encoding = cipher_encoding.upper()

    def encrypt_request(self, data_plaintext: str) -> tuple[str, str, str]:
        """
        生成 SM4 密钥，SM4 加密 data，SM2 加密 SM4 密钥。
        :param data_plaintext: 业务报文明文（通常为 JSON 字符串）
        :return: (encrypted_sm4_key_hex, encrypted_data, sm4_key_plain) 解密响应时需用 sm4_key_plain
        """
        if not data_plaintext:
            raise CryptoError("请求明文不能为空")
        sm4_key = Sm4Service.generate_key()
        sm4_svc = Sm4Service(key=sm4_key, mode=self.sm4_mode, padding=self.sm4_padding, encoding=self.cipher_encoding)
        encrypted_data = sm4_svc.encrypt(data_plaintext)
        sm2_svc = Sm2Service(public_key_hex=self.sm2_public_key_hex, cipher_mode=self.sm2_cipher_mode)
        encrypted_key = sm2_svc.encrypt(sm4_key)
        return encrypted_key, encrypted_data, sm4_key

    def decrypt_response(self, encrypted_data: str, sm4_key: str) -> str:
        """
        使用 SM4 密钥解密响应 data 密文。
        :param encrypted_data: 响应中的密文字段值
        :param sm4_key: 本次请求使用的 SM4 密钥（明文）
        :return: 解密后的明文字符串
        """
        if not encrypted_data or not sm4_key:
            raise CryptoError("解密参数不能为空")
        sm4_svc = Sm4Service(key=sm4_key, mode=self.sm4_mode, padding=self.sm4_padding, encoding=self.cipher_encoding)
        return sm4_svc.decrypt(encrypted_data)


def build_encrypted_request(interface_config, plain_data: str) -> tuple[dict, dict, str]:
    """
    根据接口配置构建加密请求（占位封装，便于后续替换实现）。
    返回: (headers, body, sm4_key_plain)
    """
    hybrid = HybridEncryptService(
        sm2_public_key_hex=interface_config.sm2_public_key or "",
        sm2_cipher_mode=interface_config.sm2_cipher_mode or "C1C3C2",
        sm4_mode=interface_config.sm4_mode or "ECB",
        sm4_padding=interface_config.sm4_padding or "PKCS5",
        cipher_encoding=interface_config.cipher_encoding or "HEX",
    )
    encrypted_key, encrypted_data, sm4_key_plain = hybrid.encrypt_request(plain_data)
    # headers/body 按配置字段组装，占位：只返回密钥与 data 字段
    headers = {}
    if interface_config.token_value and interface_config.token_header_name:
        headers[interface_config.token_header_name] = interface_config.token_value
    headers[interface_config.encrypt_key_header_name or "encryptKey"] = encrypted_key
    body = {interface_config.request_data_field_name or "data": encrypted_data}
    return headers, body, sm4_key_plain


def decrypt_response(interface_config, response_data: str, sm4_key: str) -> str:
    """统一混合解密方法，便于后续替换 gmssl 或其他实现。"""
    hybrid = HybridEncryptService(
        sm2_public_key_hex=interface_config.sm2_public_key or "",
        sm2_cipher_mode=interface_config.sm2_cipher_mode or "C1C3C2",
        sm4_mode=interface_config.sm4_mode or "ECB",
        sm4_padding=interface_config.sm4_padding or "PKCS5",
        cipher_encoding=interface_config.cipher_encoding or "HEX",
    )
    return hybrid.decrypt_response(response_data, sm4_key)

