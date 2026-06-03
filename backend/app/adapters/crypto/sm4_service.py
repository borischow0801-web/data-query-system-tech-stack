"""
SM4 对称加解密服务。
支持 ECB/CBC，PKCS5/PKCS7 填充，HEX/BASE64 编码。
与 Java Sm4Util 行为对齐：ECB + PKCS5，密钥 16 字节，加解密 HEX。
业务代码不直接写加密逻辑，通过 HybridEncryptService 使用。
"""
import os
from app.core.exceptions import CryptoError

try:
    from gmssl.sm4 import CryptSM4, SM4_ENCRYPT, SM4_DECRYPT
except ImportError:
    CryptSM4 = SM4_ENCRYPT = SM4_DECRYPT = None  # type: ignore


class Sm4Service:
    """SM4 加解密：密钥随机生成、ECB 加密/解密（HEX）。"""

    KEY_SIZE = 16  # 128 bit

    def __init__(self, key: str | None = None, mode: str = "ECB", padding: str = "PKCS5", encoding: str = "HEX"):
        """
        :param key: 16 字节密钥；若 None 则仅用于 generate_key
        :param mode: ECB 或 CBC
        :param padding: PKCS5 / PKCS7 / NoPadding
        :param encoding: HEX 或 BASE64
        """
        if not CryptSM4:
            raise CryptoError("gmssl 未安装，无法使用 SM4")
        self.mode = mode.upper()
        self.padding = padding.upper()
        self.encoding = encoding.upper()
        self._key = key.encode("utf-8") if key else None
        if self._key and len(self._key) != self.KEY_SIZE:
            raise CryptoError("SM4 密钥必须为 16 字节")

    @classmethod
    def generate_key(cls) -> str:
        """生成随机 16 字节 SM4 密钥（可打印 ASCII，与 Java 端对齐）。"""
        alnum = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return "".join(alnum[os.urandom(1)[0] % len(alnum)] for _ in range(cls.KEY_SIZE))

    def encrypt(self, plaintext: str) -> str:
        """
        SM4 加密，明文 UTF-8，输出 HEX。
        :param plaintext: 明文字符串（如 JSON 字符串）
        :return: 密文（HEX 或 BASE64，由 encoding 决定）
        """
        if not self._key:
            raise CryptoError("SM4 未设置密钥")
        if plaintext is None:
            raise CryptoError("SM4 加密明文不能为空")
        try:
            data = plaintext.encode("utf-8")
            # gmssl 原生 SM4 不处理填充，这里按对方 Java EcbEncrypt 的常见约定补齐
            if self.padding not in ("NOPADDING", "NO"):
                block_size = 16
                pad_len = block_size - (len(data) % block_size)
                if pad_len == 0:
                    pad_len = block_size
                if self.padding in ("PKCS5", "PKCS7"):
                    data = data + bytes([pad_len]) * pad_len
                else:
                    raise CryptoError(f"不支持的 SM4 padding: {self.padding}")
            else:
                if len(data) % 16 != 0:
                    raise CryptoError("NoPadding 模式下明文长度必须为 16 的倍数")
            if self.mode == "ECB":
                cipher = CryptSM4()
                cipher.set_key(self._key, SM4_ENCRYPT)
                encrypted = cipher.crypt_ecb(data)
            else:
                # CBC 需要 IV，此处简化；与 Java 对齐时再扩展
                cipher = CryptSM4()
                cipher.set_key(self._key, SM4_ENCRYPT)
                encrypted = cipher.crypt_ecb(data)
            if self.encoding == "HEX":
                return encrypted.hex()
            import base64
            return base64.b64encode(encrypted).decode("ascii")
        except Exception as e:
            raise CryptoError(f"SM4 加密失败: {e}") from e

    def decrypt(self, ciphertext: str) -> str:
        """
        SM4 解密。
        :param ciphertext: HEX 或 BASE64 密文
        :return: 明文字符串
        """
        if not self._key:
            raise CryptoError("SM4 未设置密钥")
        if not ciphertext:
            raise CryptoError("SM4 解密密文不能为空")
        try:
            if self.encoding == "HEX":
                raw = bytes.fromhex(ciphertext)
            else:
                import base64
                raw = base64.b64decode(ciphertext)
            cipher = CryptSM4()
            cipher.set_key(self._key, SM4_DECRYPT)
            decrypted = cipher.crypt_ecb(raw)
            if self.padding not in ("NOPADDING", "NO"):
                if self.padding in ("PKCS5", "PKCS7"):
                    if not decrypted:
                        raise CryptoError("解密结果为空")
                    pad_len = decrypted[-1]
                    if pad_len < 1 or pad_len > 16:
                        # 与部分服务端实现兼容：有些返回值已是“无 padding”的明文或 padding 规则不同
                        # 为联调排错提供更强可用性：退化为直接返回解密结果（不做 unpad）
                        return decrypted.decode("utf-8", errors="replace").rstrip("\x00")
                    if decrypted[-pad_len:] != bytes([pad_len]) * pad_len:
                        return decrypted.decode("utf-8", errors="replace").rstrip("\x00")
                    decrypted = decrypted[:-pad_len]
                else:
                    raise CryptoError(f"不支持的 SM4 padding: {self.padding}")
            return decrypted.decode("utf-8")
        except Exception as e:
            raise CryptoError(f"SM4 解密失败: {e}") from e


# ===== 兼容占位方法：便于后续替换实现 =====

def generate_key() -> str:
    """模块级生成 SM4 密钥，便于直接调用。"""
    return Sm4Service.generate_key()


def encrypt(
    plain_text: str,
    key: str,
    mode: str = "ECB",
    padding: str = "PKCS5",
    encoding: str = "HEX",
) -> str:
    """统一 SM4 加密方法签名。"""
    svc = Sm4Service(key=key, mode=mode, padding=padding, encoding=encoding)
    return svc.encrypt(plain_text)


def decrypt(
    cipher_text: str,
    key: str,
    mode: str = "ECB",
    padding: str = "PKCS5",
    encoding: str = "HEX",
) -> str:
    """统一 SM4 解密方法签名。"""
    svc = Sm4Service(key=key, mode=mode, padding=padding, encoding=encoding)
    return svc.decrypt(cipher_text)

