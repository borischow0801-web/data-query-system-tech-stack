"""
正式接口最小联调脚本（强可观察性）。

目标：
- 不依赖前端页面
- 不强依赖数据库
- 你只需要手工填写一个本地配置文件（Python 文件最方便）
- 脚本会按固定顺序打印所有关键中间结果，任何一步失败都能明确看到“失败阶段”

准备：
1) 复制配置模板：
   cp scripts/debug_real_query_config.example.py scripts/debug_real_query_config.py
2) 修改 scripts/debug_real_query_config.py 中的配置项为正式接口值
3) 运行（在 backend 目录下）：
   python scripts/debug_real_query.py
或指定配置文件路径：
   python scripts/debug_real_query.py /abs/path/to/debug_real_query_config.py

注意：
- 本脚本**强制走真实联调链路**，不会读取 USE_MOCK_* 配置，也不会走 mock。
- crypto 使用项目现有 gmssl 实现（若未安装 gmssl，会明确提示）。
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from dataclasses import dataclass
from typing import Any

import httpx

# 确保 backend 在 path 中（允许从任意工作目录运行）
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from app.adapters.crypto.hybrid_encrypt_service import HybridEncryptService
from app.core.exceptions import CryptoError


def _mask(s: str | None, keep_start: int = 6, keep_end: int = 4) -> str | None:
    if s is None:
        return None
    s = str(s)
    if len(s) <= keep_start + keep_end:
        return "*" * len(s)
    return s[:keep_start] + "*" * (len(s) - keep_start - keep_end) + s[-keep_end:]


def _stage_fail(stage: str, msg: str) -> None:
    print("\n" + "=" * 80)
    print(f"[失败阶段] {stage}")
    print(f"[错误信息] {msg}")
    print("=" * 80 + "\n")


@dataclass
class DebugConfig:
    # 基础请求配置
    BASE_URL: str
    REQUEST_PATH: str
    REQUEST_METHOD: str = "POST"

    # 鉴权配置
    TOKEN: str | None = None
    TOKEN_HEADER_NAME: str | None = None

    # 加密配置
    SM2_PUBLIC_KEY: str = ""
    SM2_CIPHER_MODE: str = "C1C3C2"
    SM4_MODE: str = "ECB"
    SM4_PADDING: str = "PKCS5"
    CIPHER_ENCODING: str = "HEX"
    ENCRYPT_KEY_HEADER_NAME: str = "encryptKey"

    # 请求报文字段配置
    REQUEST_DATA_FIELD_NAME: str = "data"
    RESPONSE_DATA_FIELD_NAME: str = "data"
    RESPONSE_CODE_FIELD_NAME: str = "code"
    RESPONSE_MSG_FIELD_NAME: str = "msg"
    SUCCESS_CODE_VALUE: str = "200"

    # 其他请求头（可选）
    EXTRA_HEADERS: dict[str, str] | None = None

    # 测试业务参数
    PLAIN_DATA: dict[str, Any] | str | None = None

    # 其他
    TIMEOUT_MS: int = 10000
    VERIFY_TLS: bool = True  # 生产建议 True；联调自测可改 False


def _load_config_from_py(path: str) -> DebugConfig:
    spec = importlib.util.spec_from_file_location("debug_real_query_config", path)
    if not spec or not spec.loader:
        raise RuntimeError(f"无法加载配置文件: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]

    def _get(name: str, default: Any = None) -> Any:
        return getattr(mod, name, default)

    cfg = DebugConfig(
        BASE_URL=_get("BASE_URL", ""),
        REQUEST_PATH=_get("REQUEST_PATH", ""),
        REQUEST_METHOD=_get("REQUEST_METHOD", "POST"),
        TOKEN=_get("TOKEN", None),
        TOKEN_HEADER_NAME=_get("TOKEN_HEADER_NAME", None),
        SM2_PUBLIC_KEY=_get("SM2_PUBLIC_KEY", ""),
        SM2_CIPHER_MODE=_get("SM2_CIPHER_MODE", "C1C3C2"),
        SM4_MODE=_get("SM4_MODE", "ECB"),
        SM4_PADDING=_get("SM4_PADDING", "PKCS5"),
        CIPHER_ENCODING=_get("CIPHER_ENCODING", "HEX"),
        ENCRYPT_KEY_HEADER_NAME=_get("ENCRYPT_KEY_HEADER_NAME", "encryptKey"),
        REQUEST_DATA_FIELD_NAME=_get("REQUEST_DATA_FIELD_NAME", "data"),
        RESPONSE_DATA_FIELD_NAME=_get("RESPONSE_DATA_FIELD_NAME", "data"),
        RESPONSE_CODE_FIELD_NAME=_get("RESPONSE_CODE_FIELD_NAME", "code"),
        RESPONSE_MSG_FIELD_NAME=_get("RESPONSE_MSG_FIELD_NAME", "msg"),
        SUCCESS_CODE_VALUE=str(_get("SUCCESS_CODE_VALUE", "200")),
        EXTRA_HEADERS=_get("EXTRA_HEADERS", None),
        PLAIN_DATA=_get("PLAIN_DATA", None),
        TIMEOUT_MS=int(_get("TIMEOUT_MS", 10000)),
        VERIFY_TLS=bool(_get("VERIFY_TLS", True)),
    )
    return cfg


def _validate_config(cfg: DebugConfig) -> None:
    missing = []
    if not cfg.BASE_URL:
        missing.append("BASE_URL")
    if cfg.REQUEST_PATH is None:
        missing.append("REQUEST_PATH")
    if cfg.TOKEN and not cfg.TOKEN_HEADER_NAME:
        missing.append("TOKEN_HEADER_NAME(当 TOKEN 非空时必填)")
    if not cfg.SM2_PUBLIC_KEY:
        missing.append("SM2_PUBLIC_KEY")
    if not cfg.ENCRYPT_KEY_HEADER_NAME:
        missing.append("ENCRYPT_KEY_HEADER_NAME")
    if not cfg.REQUEST_DATA_FIELD_NAME:
        missing.append("REQUEST_DATA_FIELD_NAME")
    if not cfg.RESPONSE_DATA_FIELD_NAME:
        missing.append("RESPONSE_DATA_FIELD_NAME")
    if not cfg.RESPONSE_CODE_FIELD_NAME:
        missing.append("RESPONSE_CODE_FIELD_NAME")
    if not cfg.RESPONSE_MSG_FIELD_NAME:
        missing.append("RESPONSE_MSG_FIELD_NAME")
    if missing:
        raise ValueError("配置缺失: " + ", ".join(missing))


def _build_url(cfg: DebugConfig) -> str:
    base = cfg.BASE_URL.rstrip("/")
    path = (cfg.REQUEST_PATH or "").lstrip("/")
    return f"{base}/{path}" if path else base


def _build_plain_data_text(cfg: DebugConfig) -> str:
    if cfg.PLAIN_DATA is None:
        return "{}"
    if isinstance(cfg.PLAIN_DATA, str):
        return cfg.PLAIN_DATA
    return json.dumps(cfg.PLAIN_DATA, ensure_ascii=False)


def main() -> None:
    stage = "初始化"
    failed_stage: str | None = None
    decrypt_ok = False
    final_success = False
    response_code: str | None = None
    response_msg: str | None = None

    # 允许传入配置路径；否则默认读取 scripts/debug_real_query_config.py
    config_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "debug_real_query_config.py")
    if not os.path.isabs(config_path):
        config_path = os.path.abspath(config_path)

    try:
        stage = "配置加载"
        cfg = _load_config_from_py(config_path)

        stage = "配置校验"
        _validate_config(cfg)

        # 1) 配置摘要（脱敏）
        stage = "第一步：打印配置摘要"
        print("===== 第一步：配置摘要（敏感信息已脱敏）=====")
        print(f"CONFIG_PATH={config_path}")
        print(f"BASE_URL={cfg.BASE_URL}")
        print(f"REQUEST_PATH={cfg.REQUEST_PATH}")
        print(f"REQUEST_METHOD={cfg.REQUEST_METHOD}")
        print(f"TOKEN_HEADER_NAME={cfg.TOKEN_HEADER_NAME}")
        print(f"TOKEN={_mask(cfg.TOKEN, keep_start=3, keep_end=3) if cfg.TOKEN else None}")
        print(f"ENCRYPT_KEY_HEADER_NAME={cfg.ENCRYPT_KEY_HEADER_NAME}")
        print(f"SM2_PUBLIC_KEY={_mask(cfg.SM2_PUBLIC_KEY, keep_start=10, keep_end=10)}")
        print(f"SM2_CIPHER_MODE={cfg.SM2_CIPHER_MODE}")
        print(f"SM4_MODE={cfg.SM4_MODE}")
        print(f"SM4_PADDING={cfg.SM4_PADDING}")
        print(f"CIPHER_ENCODING={cfg.CIPHER_ENCODING}")
        print(f"REQUEST_DATA_FIELD_NAME={cfg.REQUEST_DATA_FIELD_NAME}")
        print(f"RESPONSE_DATA_FIELD_NAME={cfg.RESPONSE_DATA_FIELD_NAME}")
        print(f"RESPONSE_CODE_FIELD_NAME={cfg.RESPONSE_CODE_FIELD_NAME}")
        print(f"RESPONSE_MSG_FIELD_NAME={cfg.RESPONSE_MSG_FIELD_NAME}")
        print(f"SUCCESS_CODE_VALUE={cfg.SUCCESS_CODE_VALUE}")
        print(f"EXTRA_HEADERS={cfg.EXTRA_HEADERS or {}}")
        print(f"TIMEOUT_MS={cfg.TIMEOUT_MS}")
        print(f"VERIFY_TLS={cfg.VERIFY_TLS}")

        # 2) 明文 data
        stage = "第二步：打印明文 data"
        plain_data_text = _build_plain_data_text(cfg)
        print("\n===== 第二步：明文 data =====")
        print(plain_data_text)

        # 3/4/5) 混合加密
        stage = "第三步：生成 SM4 密钥 / 第四步：SM4 加密业务报文 / 第五步：SM2 加密 SM4 密钥"
        try:
            hybrid = HybridEncryptService(
                sm2_public_key_hex=cfg.SM2_PUBLIC_KEY,
                sm2_cipher_mode=cfg.SM2_CIPHER_MODE,
                sm4_mode=cfg.SM4_MODE,
                sm4_padding=cfg.SM4_PADDING,
                cipher_encoding=cfg.CIPHER_ENCODING,
            )
            encrypted_sm4_key, encrypted_data, sm4_key_plain = hybrid.encrypt_request(plain_data_text)
        except CryptoError as e:
            raise RuntimeError(f"国密加密失败（gmssl/密钥/模式/编码检查）: {e}") from e

        print("\n===== 第三步：SM4 密钥（明文，仅调试用途）=====")
        print(sm4_key_plain)
        print("\n===== 第四步：SM4 加密后的业务报文 =====")
        print(encrypted_data)
        print("\n===== 第五步：SM2 加密后的 SM4 密钥（secret）=====")
        print(encrypted_sm4_key)

        # 6) headers
        stage = "第六步：组装请求 headers"
        headers: dict[str, str] = {}
        if cfg.EXTRA_HEADERS:
            headers.update({str(k): str(v) for k, v in cfg.EXTRA_HEADERS.items()})
        if cfg.TOKEN and cfg.TOKEN_HEADER_NAME:
            headers[str(cfg.TOKEN_HEADER_NAME)] = str(cfg.TOKEN)
        # 按接口规则：secret = SM2(公钥加密 SM4 key)，放入 header（header 名由 ENCRYPT_KEY_HEADER_NAME 指定）
        headers[str(cfg.ENCRYPT_KEY_HEADER_NAME)] = str(encrypted_sm4_key)
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        print("\n===== 第六步：最终请求 headers =====")
        print(json.dumps(headers, ensure_ascii=False, indent=2))

        # 7) body
        stage = "第七步：组装请求 body"
        body = {str(cfg.REQUEST_DATA_FIELD_NAME): encrypted_data}
        print("\n===== 第七步：最终请求 body =====")
        print(json.dumps(body, ensure_ascii=False, indent=2))

        # 8) URL + Method
        stage = "第八步：打印请求 URL 和方法"
        url = _build_url(cfg)
        method = (cfg.REQUEST_METHOD or "POST").upper()
        print("\n===== 第八步：请求 URL / 方法 =====")
        print(f"{method} {url}")

        # 9/10) HTTP 请求 + 原始响应
        stage = "第九步：发起 HTTP 请求"
        try:
            timeout_sec = max(1.0, cfg.TIMEOUT_MS / 1000.0)
            with httpx.Client(timeout=timeout_sec, verify=cfg.VERIFY_TLS, trust_env=False) as client:
                if method == "POST":
                    r = client.post(url, json=body, headers=headers)
                elif method == "GET":
                    r = client.get(url, params=body, headers=headers)
                else:
                    r = client.request(method, url, json=body, headers=headers)
        except httpx.HTTPError as e:
            raise RuntimeError(f"HTTP 请求失败: {e}") from e

        print("\n===== 第九步：HTTP 状态码 =====")
        print(r.status_code)

        raw_text = r.text if r.text is not None else ""
        print("\n===== 第十步：远程接口原始响应文本 =====")
        print(raw_text)

        # 11) 解析 + 解密
        stage = "第十一步：解析响应 JSON"
        try:
            resp_json = r.json()
        except Exception as e:
            raise RuntimeError(f"响应 JSON 解析失败（请检查远端是否返回 JSON）: {e}") from e

        response_code = resp_json.get(cfg.RESPONSE_CODE_FIELD_NAME)
        response_msg = resp_json.get(cfg.RESPONSE_MSG_FIELD_NAME)
        if response_code is not None:
            response_code = str(response_code)
        if response_msg is not None:
            response_msg = str(response_msg)

        cipher_resp_data = resp_json.get(cfg.RESPONSE_DATA_FIELD_NAME)
        if not cipher_resp_data:
            failed_stage = "找不到响应 data 字段"
            print("\n===== 第十一步：响应中未找到加密 data 字段，跳过解密 =====")
        else:
            stage = "第十一步：SM4 解密响应 data"
            try:
                decrypted_text = hybrid.decrypt_response(str(cipher_resp_data), sm4_key_plain)
                decrypt_ok = True
                print("\n===== 第十一步：解密结果 =====")
                print(decrypted_text)
            except CryptoError as e:
                failed_stage = "SM4 解密失败"
                print("\n===== 第十一步：SM4 解密失败 =====")
                print(str(e))

        # 12) 最终判断
        stage = "第十二步：最终判断"
        success_code = str(cfg.SUCCESS_CODE_VALUE or "0")
        biz_ok = (response_code is not None) and (str(response_code) == success_code)
        final_success = bool(biz_ok and decrypt_ok)
        if not biz_ok:
            failed_stage = failed_stage or "外部返回业务失败码"
        if not decrypt_ok:
            failed_stage = failed_stage or "解密失败或无 data"

        print("\n===== 第十二步：最终判断 =====")
        print(f"请求是否成功: {final_success}")
        print(f"外部返回码: {response_code}")
        print(f"外部返回消息: {response_msg}")
        print(f"解密是否成功: {decrypt_ok}")
        print(f"失败卡在哪一步: {failed_stage if not final_success else None}")

    except Exception as e:
        _stage_fail(stage, str(e))


if __name__ == "__main__":
    main()
