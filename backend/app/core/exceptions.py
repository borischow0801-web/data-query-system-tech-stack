"""统一业务异常。"""
from typing import Optional


class AppException(Exception):
    """业务异常基类"""

    def __init__(
        self,
        message: str = "业务异常",
        code: str = "1",
    ):
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(AppException):
    """资源不存在"""

    def __init__(self, message: str = "资源不存在", code: str = "404"):
        super().__init__(message=message, code=code)


class UnauthorizedError(AppException):
    """未授权"""

    def __init__(self, message: str = "未授权", code: str = "401"):
        super().__init__(message=message, code=code)


class ValidationError(AppException):
    """参数校验失败"""

    def __init__(self, message: str = "参数校验失败", code: str = "400"):
        super().__init__(message=message, code=code)


class CryptoError(AppException):
    """加解密异常"""

    def __init__(self, message: str = "加解密失败", code: str = "CRYPTO_ERROR"):
        super().__init__(message=message, code=code)


class RemoteApiError(AppException):
    """外部接口调用异常"""

    def __init__(self, message: str = "外部接口调用失败", code: str = "REMOTE_ERROR"):
        super().__init__(message=message, code=code)
