"""大报文存储：DB 预览 + 文件完整内容。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime

from app.core.config import get_settings
from app.core.logger import logger


@dataclass
class StoredPayload:
    full_text: str | None
    preview_text: str | None
    size_bytes: int | None
    store_mode: str  # DB / FILE
    store_path: str | None
    store_error: str | None = None


class PayloadStoreService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _ensure_dir(self, p: str) -> None:
        os.makedirs(p, exist_ok=True)

    def _bytes_len(self, s: str) -> int:
        return len(s.encode("utf-8", errors="replace"))

    def store_text(
        self,
        *,
        trace_id: str,
        kind: str,  # request_plain / request_cipher / response_raw / response_plain
        text: str | None,
        ext: str = "txt",
    ) -> StoredPayload:
        """
        - 小于阈值：full_text 入库（DB），preview=full_text
        - 超阈值：full_text 不入库（None），preview 入库，完整内容落文件
        """
        if text is None:
            return StoredPayload(
                full_text=None,
                preview_text=None,
                size_bytes=None,
                store_mode="DB",
                store_path=None,
            )

        max_bytes = int(self.settings.query_log_inline_max_bytes or 65535)
        size = self._bytes_len(text)

        # 预览：前 4096 字符（可按需调整）
        preview = text[:4096]

        if size <= max_bytes:
            return StoredPayload(
                full_text=text,
                preview_text=preview,
                size_bytes=size,
                store_mode="DB",
                store_path=None,
            )

        # FILE mode
        base_dir = os.path.abspath(self.settings.query_log_file_dir or "./storage/query_payloads")
        date_dir = datetime.now().strftime("%Y%m%d")
        dir_path = os.path.join(base_dir, date_dir)
        file_name = f"{trace_id}_{kind}.{ext}"
        file_path = os.path.join(dir_path, file_name)

        try:
            self._ensure_dir(dir_path)
            with open(file_path, "w", encoding="utf-8", errors="replace") as f:
                f.write(text)
            return StoredPayload(
                full_text=None,  # 不入库，避免字段过大
                preview_text=preview,
                size_bytes=size,
                store_mode="FILE",
                store_path=file_path,
            )
        except Exception as e:
            # 落盘失败：降级为只存 preview（且不影响主流程）
            logger.error(f"Payload store failed trace_id={trace_id} kind={kind} error={e}")
            return StoredPayload(
                full_text=None,
                preview_text=preview,
                size_bytes=size,
                store_mode="DB",
                store_path=None,
                store_error=str(e),
            )

