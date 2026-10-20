"""大报文存储：DB 预览 + 文件完整内容。"""

from __future__ import annotations

import os
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logger import logger


@dataclass
class StoredPayload:
    full_text: str | None
    preview_text: str | None
    size_bytes: int | None
    store_mode: str  # DB / FILE
    store_path: str | None
    store_error: str | None = None


@dataclass
class LoadedPayload:
    text: str
    source: str
    path: str | None = None


class PayloadStoreService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _ensure_dir(self, p: str) -> None:
        os.makedirs(p, exist_ok=True)

    def _bytes_len(self, s: str) -> int:
        return len(s.encode("utf-8", errors="replace"))

    def load_record_text(self, record: Any, kind: str) -> LoadedPayload:
        fields = {
            "request_plain": "request_plain_text",
            "request_cipher": "request_cipher_text",
            "response_raw": "response_raw_text",
            "response_plain": "response_plain_text",
        }
        if kind not in fields:
            raise ValidationError("kind 不支持")
        text = getattr(record, fields[kind], None)
        if text is not None:
            return LoadedPayload(text=text, source="DB")

        # A record stores one representative path; select only the requested sibling.
        directories = []
        stored_path = getattr(record, "payload_store_path", None)
        if stored_path:
            directories.append(Path(stored_path).parent)
        base = Path(self.settings.query_log_file_dir or "./storage/query_payloads").absolute()
        for field in ("created_at", "started_at"):
            dt = getattr(record, field, None)
            if dt:
                directories.append(base / dt.strftime("%Y%m%d"))
        directories.append(base)
        for directory in dict.fromkeys(directories):
            for ext in ("json", "txt"):
                path = directory / f"{record.trace_id}_{kind}.{ext}"
                try:
                    text = path.read_text(encoding="utf-8")
                except FileNotFoundError:
                    continue
                except (OSError, UnicodeError) as exc:
                    raise ValidationError(f"完整报文读取失败：{kind}") from exc
                return LoadedPayload(text=text, source="FILE", path=str(path))
        raise NotFoundError(f"未找到完整报文：{kind}")

    def load_record_json(self, record: Any) -> Any:
        payload = self.load_record_text(record, "response_plain")
        try:
            return json.loads(payload.text)
        except (ValueError, TypeError) as exc:
            raise ValidationError("解密响应不是有效 JSON，无法回放或导出") from exc

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

