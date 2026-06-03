"""
SM2 公钥加密服务。
用于加密 SM4 密钥，密文格式兼容 C1C2C3 / C1C3C2，输出 HEX 小写（与 Java demo 一致）。
业务代码不直接调用，通过 HybridEncryptService 使用。
"""
from app.core.exceptions import CryptoError

# 使用 gmssl 实现 SM2
try:
    from gmssl import sm2
except ImportError:
    sm2 = None  # type: ignore


class Sm2Service:
    """SM2 加密：使用公钥加密 SM4 密钥，返回 HEX 密文。"""

    def __init__(self, public_key_hex: str, cipher_mode: str = "C1C3C2"):
        """
        :param public_key_hex: SM2 公钥（十六进制，可带或不带 04 前缀）
        :param cipher_mode: C1C2C3 或 C1C3C2
        """
        if not sm2:
            raise CryptoError("gmssl 未安装，无法使用 SM2")
        self.public_key_hex = public_key_hex.strip()
        if not self.public_key_hex.startswith("04"):
            self.public_key_hex = "04" + self.public_key_hex
        self.cipher_mode = cipher_mode.upper()

    def encrypt(self, plaintext: str) -> str:
        """
        使用 SM2 公钥加密明文（一般为 SM4 密钥）。
        :param plaintext: 明文字符串
        :return: 十六进制密文（小写，与 Java 端约定一致）
        """
        if not plaintext:
            raise CryptoError("SM2 加密明文不能为空")
        try:
            # gmssl sm2: 公钥 04+x+y，encrypt 返回 bytes
            mode = 1 if self.cipher_mode == "C1C3C2" else 0
            cipher = sm2.CryptSM2(public_key=self.public_key_hex, private_key=None, mode=mode)
            cipher_bytes = cipher.encrypt(plaintext.encode("utf-8"))
            hex_result = cipher_bytes.hex().lower()
            # 与对方 Java Sm2Util 约定：去除前缀 04，并转小写
            if hex_result.startswith("04"):
                hex_result = hex_result[2:]
            return hex_result
        except Exception as e:
            raise CryptoError(f"SM2 加密失败: {e}") from e


def encrypt_with_public_key(
    plain_text: str,
    public_key: str,
    cipher_mode: str = "C1C3C2",
    encoding: str = "HEX",
) -> str:
    """统一 SM2 加密方法：使用公钥加密明文（通常为 SM4 密钥）。"""
    svc = Sm2Service(public_key_hex=public_key, cipher_mode=cipher_mode)
    result = svc.encrypt(plain_text)
    # 当前实现仅支持 HEX，可按 encoding 扩展
    return result

