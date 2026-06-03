"""
外部接口调用适配器。
负责：组装 Header/Body、发送 HTTP 请求、重试、错误处理。
不包含加解密逻辑，加解密由 HybridEncryptService 完成后再传入。
"""
import time
from typing import Any

import httpx

from app.core.exceptions import RemoteApiError
from app.core.logger import logger


class RemoteApiAdapter:
    """统一外部 HTTP 接口调用。"""

    def __init__(
        self,
        base_url: str,
        request_path: str = "",
        method: str = "POST",
        timeout_ms: int = 10000,
        timeout_detail: dict | None = None,
        headers: dict | None = None,
        content_type: str = "application/json",
        retry_count: int = 0,
        retry_interval_ms: int = 1000,
        verify_tls: bool = True,
        trust_env: bool = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.request_path = (request_path or "").strip().lstrip("/")
        self.method = method.upper()
        self.timeout_ms = timeout_ms
        self.timeout_detail = timeout_detail or {}
        self.headers = dict(headers or {})
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = content_type
        self.retry_count = max(0, retry_count)
        self.retry_interval_ms = max(0, retry_interval_ms)
        self.verify_tls = verify_tls
        # 内网/政务接口默认不走系统代理，避免 HTTP(S)_PROXY 指向 SOCKS 但未安装 socksio 导致 ImportError
        self.trust_env = trust_env

    def request(self, body: dict, headers_override: dict | None = None) -> tuple[int, str, dict]:
        """
        发送请求，按配置重试。
        :param body: 请求体（已包含加密后的 data 等）
        :param headers_override: 本次请求覆盖的 header（如 token、encryptKey）
        :return: (http_status_code, raw_response_text, response_headers_dict)
        """
        url = f"{self.base_url}/{self.request_path}" if self.request_path else self.base_url
        headers = {**self.headers, **(headers_override or {})}
        last_exc: Exception | None = None

        for attempt in range(self.retry_count + 1):
            try:
                timeout = self._build_timeout()
                logger.info(
                    f"Remote request [{self.method}] {url} attempt={attempt+1} timeout={self._timeout_debug(timeout)}"
                )
                with httpx.Client(
                    timeout=timeout,
                    verify=self.verify_tls,
                    trust_env=self.trust_env,
                ) as client:
                    if self.method == "POST":
                        r = client.post(url, json=body, headers=headers)
                    elif self.method == "GET":
                        r = client.get(url, params=body, headers=headers)
                    else:
                        r = client.request(self.method, url, json=body, headers=headers)
                    logger.info(f"Remote response status={r.status_code} url={url}")
                    return r.status_code, r.text, dict(r.headers)
            except ImportError as e:
                last_exc = e
                msg = str(e)
                if "socks" in msg.lower():
                    msg = (
                        "检测到系统代理为 SOCKS，但未安装 socksio。"
                        "内网接口已默认直连（trust_env=false）；若仍报错请取消 HTTP_PROXY/ALL_PROXY 或执行 pip install httpx[socks]。"
                    )
                logger.error(f"Remote request failed attempt={attempt+1} url={url} error={msg}")
                if attempt < self.retry_count:
                    time.sleep(self._sleep_seconds(attempt))
                    continue
                raise RemoteApiError(msg, code="REMOTE_PROXY_CONFIG") from e
            except httpx.TimeoutException as e:
                last_exc = e
                msg = f"请求超时(timeout): {e}"
                logger.error(f"Remote request failed attempt={attempt+1} url={url} error={msg}")
                if attempt < self.retry_count:
                    time.sleep(self._sleep_seconds(attempt))
                    continue
                raise RemoteApiError(msg, code="REMOTE_TIMEOUT_READ") from e
            except httpx.ConnectTimeout as e:
                last_exc = e
                msg = f"连接超时(connect timeout): {e}"
                logger.error(f"Remote request failed attempt={attempt+1} url={url} error={msg}")
                if attempt < self.retry_count:
                    time.sleep(self._sleep_seconds(attempt))
                    continue
                raise RemoteApiError(msg, code="REMOTE_TIMEOUT_CONNECT") from e
            except httpx.ReadTimeout as e:
                last_exc = e
                msg = f"读取超时(read timeout): {e}"
                logger.error(f"Remote request failed attempt={attempt+1} url={url} error={msg}")
                if attempt < self.retry_count:
                    time.sleep(self._sleep_seconds(attempt))
                    continue
                raise RemoteApiError(msg, code="REMOTE_TIMEOUT_READ") from e
            except httpx.WriteTimeout as e:
                last_exc = e
                msg = f"写入超时(write timeout): {e}"
                logger.error(f"Remote request failed attempt={attempt+1} url={url} error={msg}")
                if attempt < self.retry_count:
                    time.sleep(self._sleep_seconds(attempt))
                    continue
                raise RemoteApiError(msg, code="REMOTE_TIMEOUT_WRITE") from e
            except httpx.PoolTimeout as e:
                last_exc = e
                msg = f"连接池超时(pool timeout): {e}"
                logger.error(f"Remote request failed attempt={attempt+1} url={url} error={msg}")
                if attempt < self.retry_count:
                    time.sleep(self._sleep_seconds(attempt))
                    continue
                raise RemoteApiError(msg, code="REMOTE_TIMEOUT_POOL") from e
            except httpx.HTTPError as e:
                last_exc = e
                logger.error(f"Remote request failed attempt={attempt+1} url={url} error={e}")
                if attempt < self.retry_count:
                    time.sleep(self._sleep_seconds(attempt))
                    continue
            except Exception as e:
                last_exc = e
                msg = f"远端请求异常({type(e).__name__}): {e}"
                logger.error(f"Remote request failed attempt={attempt+1} url={url} error={msg}")
                if attempt < self.retry_count:
                    time.sleep(self._sleep_seconds(attempt))
                    continue
                raise RemoteApiError(msg, code="REMOTE_ERROR") from e
        raise RemoteApiError(f"请求失败: {last_exc}", code="REMOTE_ERROR") from last_exc

    def _build_timeout(self) -> httpx.Timeout:
        """
        细分 timeout：
        - connect/pool 通常不宜太长
        - read 对大结果集可更长（使用 timeout_ms 作为 read 的默认值）
        可通过 timeout_detail 覆盖（单位毫秒）：connect_ms/read_ms/write_ms/pool_ms
        """
        def _ms(v: Any, default_ms: int) -> float:
            try:
                x = int(v)
                if x <= 0:
                    return max(1000, int(default_ms or 0)) / 1000.0
                return x / 1000.0
            except Exception:
                return max(1000, int(default_ms or 0)) / 1000.0

        connect_s = _ms(self.timeout_detail.get("connect_ms"), 5000)
        pool_s = _ms(self.timeout_detail.get("pool_ms"), 5000)
        write_s = _ms(self.timeout_detail.get("write_ms"), 30000)
        # 核心：read 允许按接口 timeout_ms 调整（默认 10s）
        base_ms = 10000
        try:
            base_ms = int(self.timeout_ms) if self.timeout_ms is not None else 10000
        except Exception:
            base_ms = 10000
        if base_ms <= 0:
            base_ms = 10000
        read_s = _ms(self.timeout_detail.get("read_ms"), base_ms)
        return httpx.Timeout(connect=connect_s, read=read_s, write=write_s, pool=pool_s)

    def _sleep_seconds(self, attempt: int) -> float:
        """重试退避：以 retry_interval_ms 为基准，做轻量递增，避免雪崩。"""
        base = max(0, int(self.retry_interval_ms or 0)) / 1000.0
        if base <= 0:
            base = 0.8
        return min(10.0, base * (attempt + 1))

    def _timeout_debug(self, t: httpx.Timeout) -> dict[str, Any]:
        return {
            "connect": getattr(t, "connect", None),
            "read": getattr(t, "read", None),
            "write": getattr(t, "write", None),
            "pool": getattr(t, "pool", None),
        }
