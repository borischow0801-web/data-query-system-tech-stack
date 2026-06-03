"""接口配置管理服务：CRUD、分页、筛选、脱敏与测试连接。"""
from typing import Any, Dict, List, Optional, Tuple

import json
import httpx
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.interface_config import DqInterfaceConfig


class InterfaceConfigService:
    def _coerce_timeout_ms(self, v: Any) -> int:
        """避免 timeout 被保存为 0/'0'/空字符串导致 httpx read 超时为 0 秒。"""
        if v is None:
            return 10000
        s = str(v).strip()
        if s == "":
            return 10000
        try:
            x = int(float(s))
        except Exception:
            return 10000
        if x <= 0:
            return 10000
        return max(1000, x)
    def list_interfaces(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        interface_code: Optional[str] = None,
        interface_name: Optional[str] = None,
        status: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        query = db.query(DqInterfaceConfig).filter(DqInterfaceConfig.deleted_flag == 0)
        if interface_code:
            query = query.filter(DqInterfaceConfig.interface_code.like(f"%{interface_code}%"))
        if interface_name:
            query = query.filter(DqInterfaceConfig.interface_name.like(f"%{interface_name}%"))
        if status is not None:
            query = query.filter(DqInterfaceConfig.status == status)
        total = query.count()
        rows = (
            query.order_by(DqInterfaceConfig.sort_no, DqInterfaceConfig.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return [self._to_list_dict(r) for r in rows], total

    def get_interface(self, db: Session, interface_id: int) -> Dict[str, Any]:
        row = (
            db.query(DqInterfaceConfig)
            .filter(DqInterfaceConfig.id == interface_id, DqInterfaceConfig.deleted_flag == 0)
            .first()
        )
        if not row:
            raise NotFoundError("接口配置不存在")
        return self._to_detail_dict(row)

    def create_interface(self, db: Session, data: Dict[str, Any]) -> Dict[str, Any]:
        if not data.get("interfaceCode") or not data.get("interfaceName"):
            raise ValidationError("接口编码和名称不能为空")
        exists = (
            db.query(DqInterfaceConfig)
            .filter(
                DqInterfaceConfig.interface_code == data["interfaceCode"],
                DqInterfaceConfig.env_code == data.get("envCode", "prod"),
                DqInterfaceConfig.deleted_flag == 0,
            )
            .first()
        )
        if exists:
            raise ValidationError("相同环境下接口编码已存在")
        row = DqInterfaceConfig(
            interface_code=data["interfaceCode"],
            interface_name=data["interfaceName"],
            interface_category=data.get("interfaceCategory"),
            env_code=data.get("envCode", "prod"),
            base_url=data.get("baseUrl", "").strip(),
            request_path=data.get("requestPath"),
            request_method=data.get("requestMethod", "POST"),
            content_type=data.get("contentType", "application/json"),
            timeout_ms=self._coerce_timeout_ms(data.get("timeoutMs", 10000)),
            token_value=data.get("tokenValue"),
            token_header_name=data.get("tokenHeaderName", "token"),
            auth_type=data.get("authType", "TOKEN"),
            sm2_public_key=data.get("sm2PublicKey"),
            encrypt_mode=data.get("encryptMode", "SM2_SM4"),
            sm2_cipher_mode=data.get("sm2CipherMode"),
            sm4_mode=data.get("sm4Mode"),
            sm4_padding=data.get("sm4Padding"),
            cipher_encoding=data.get("cipherEncoding"),
            encrypt_key_header_name=data.get("encryptKeyHeaderName", "secret"),
            request_data_field_name=data.get("requestDataFieldName", "data"),
            response_data_field_name=data.get("responseDataFieldName", "data"),
            response_code_field_name=data.get("responseCodeFieldName", "code"),
            response_msg_field_name=data.get("responseMsgFieldName", "msg"),
            success_code_value=data.get("successCodeValue", "200"),
            request_header_template=json.dumps(data.get("requestHeaderTemplate"))
            if isinstance(data.get("requestHeaderTemplate"), dict)
            else data.get("requestHeaderTemplate"),
            request_body_template=data.get("requestBodyTemplate"),
            response_mapping_template=data.get("responseMappingTemplate"),
            retry_count=data.get("retryCount", 0),
            retry_interval_ms=data.get("retryIntervalMs", 1000),
            cache_ttl_seconds=data.get("cacheTtlSeconds", 0),
            rate_limit_qps=data.get("rateLimitQps"),
            allow_open_api=data.get("allowOpenApi", 1),
            status=data.get("status", 1),
            sort_no=data.get("sortNo", 0),
            remark=data.get("remark"),
        )
        db.add(row)
        db.flush()
        return self._to_detail_dict(row)

    def update_interface(self, db: Session, interface_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        row: DqInterfaceConfig | None = (
            db.query(DqInterfaceConfig)
            .filter(DqInterfaceConfig.id == interface_id, DqInterfaceConfig.deleted_flag == 0)
            .first()
        )
        if not row:
            raise NotFoundError("接口配置不存在")
        # 简单字段更新（仅更新请求中提供的字段）
        mapping = {
            "interfaceCode": "interface_code",
            "interfaceName": "interface_name",
            "interfaceCategory": "interface_category",
            "envCode": "env_code",
            "baseUrl": "base_url",
            "requestPath": "request_path",
            "requestMethod": "request_method",
            "contentType": "content_type",
            "timeoutMs": "timeout_ms",
            "tokenValue": "token_value",
            "tokenHeaderName": "token_header_name",
            "authType": "auth_type",
            "sm2PublicKey": "sm2_public_key",
            "encryptMode": "encrypt_mode",
            "sm2CipherMode": "sm2_cipher_mode",
            "sm4Mode": "sm4_mode",
            "sm4Padding": "sm4_padding",
            "cipherEncoding": "cipher_encoding",
            "encryptKeyHeaderName": "encrypt_key_header_name",
            "requestDataFieldName": "request_data_field_name",
            "responseDataFieldName": "response_data_field_name",
            "responseCodeFieldName": "response_code_field_name",
            "responseMsgFieldName": "response_msg_field_name",
            "successCodeValue": "success_code_value",
            "retryCount": "retry_count",
            "retryIntervalMs": "retry_interval_ms",
            "cacheTtlSeconds": "cache_ttl_seconds",
            "rateLimitQps": "rate_limit_qps",
            "allowOpenApi": "allow_open_api",
            "status": "status",
            "sortNo": "sort_no",
            "remark": "remark",
        }
        for k, v in data.items():
            if k == "requestHeaderTemplate":
                setattr(
                    row,
                    "request_header_template",
                    json.dumps(v) if isinstance(v, dict) else v,
                )
            elif k == "requestBodyTemplate":
                row.request_body_template = v
            elif k == "responseMappingTemplate":
                row.response_mapping_template = v
            elif k == "tokenValue":
                # 前端编辑时允许留空表示“不修改 token”
                if v is None or str(v).strip() == "":
                    continue
                row.token_value = v
            elif k == "timeoutMs":
                row.timeout_ms = self._coerce_timeout_ms(v)
            elif k in mapping:
                setattr(row, mapping[k], v)
        db.flush()
        return self._to_detail_dict(row)

    def soft_delete_interface(self, db: Session, interface_id: int) -> None:
        row = (
            db.query(DqInterfaceConfig)
            .filter(DqInterfaceConfig.id == interface_id, DqInterfaceConfig.deleted_flag == 0)
            .first()
        )
        if not row:
            return
        row.deleted_flag = 1
        db.flush()

    def test_interface_connectivity(self, db: Session, interface_id: int) -> Dict[str, Any]:
        """简单连通性测试：根据 base_url + request_path 发起一次 HTTP 请求，不做加解密。"""
        row = (
            db.query(DqInterfaceConfig)
            .filter(DqInterfaceConfig.id == interface_id, DqInterfaceConfig.deleted_flag == 0)
            .first()
        )
        if not row:
            raise NotFoundError("接口配置不存在")
        url = row.base_url.rstrip("/")
        if row.request_path:
            url = f"{url}/{row.request_path.lstrip('/')}"
        # 细分 timeout：connect/pool 较短，read 使用 timeout_ms（便于大接口调大）
        connect_s = 5.0
        pool_s = 5.0
        write_s = 30.0
        read_s = max(1.0, (row.timeout_ms or 10000) / 1000.0)
        timeout = httpx.Timeout(connect=connect_s, read=read_s, write=write_s, pool=pool_s)
        headers: dict[str, str] = {}
        if row.token_value and row.token_header_name:
            headers[row.token_header_name] = row.token_value
        try:
            method = (row.request_method or "POST").upper()
            with httpx.Client(timeout=timeout) as client:
                if method == "GET":
                    resp = client.get(url, headers=headers)
                else:
                    resp = client.post(url, headers=headers)
            return {
                "url": url,
                "statusCode": resp.status_code,
                "ok": resp.status_code < 400,
            }
        except httpx.ConnectTimeout as e:
            return {"url": url, "statusCode": None, "ok": False, "error": f"connect timeout: {e}"}
        except httpx.ReadTimeout as e:
            return {"url": url, "statusCode": None, "ok": False, "error": f"read timeout: {e}"}
        except httpx.HTTPError as e:
            return {"url": url, "statusCode": None, "ok": False, "error": str(e)}

    def _mask_token(self, token: Optional[str]) -> Optional[str]:
        if not token:
            return token
        if len(token) <= 6:
            return "*" * len(token)
        return token[:3] + "****" + token[-3:]

    def _to_list_dict(self, r: DqInterfaceConfig) -> Dict[str, Any]:
        return {
            "id": r.id,
            "interfaceCode": r.interface_code,
            "interfaceName": r.interface_name,
            "interfaceCategory": r.interface_category,
            "envCode": r.env_code,
            "baseUrl": r.base_url,
            "requestPath": r.request_path,
            "requestMethod": r.request_method,
            "status": r.status,
            "encryptMode": r.encrypt_mode,
            "allowOpenApi": r.allow_open_api,
            "tokenMasked": self._mask_token(r.token_value),
        }

    def _to_detail_dict(self, r: DqInterfaceConfig) -> Dict[str, Any]:
        return {
            **self._to_list_dict(r),
            "contentType": r.content_type,
            "timeoutMs": r.timeout_ms,
            "tokenHeaderName": r.token_header_name,
            "authType": r.auth_type,
            "sm2PublicKey": r.sm2_public_key,
            "sm2CipherMode": r.sm2_cipher_mode,
            "sm4Mode": r.sm4_mode,
            "sm4Padding": r.sm4_padding,
            "cipherEncoding": r.cipher_encoding,
            "encryptKeyHeaderName": r.encrypt_key_header_name,
            "requestDataFieldName": r.request_data_field_name,
            "responseDataFieldName": r.response_data_field_name,
            "responseCodeFieldName": r.response_code_field_name,
            "responseMsgFieldName": r.response_msg_field_name,
            "successCodeValue": r.success_code_value,
            "requestHeaderTemplate": r.request_header_template,
            "requestBodyTemplate": r.request_body_template,
            "responseMappingTemplate": r.response_mapping_template,
            "retryCount": r.retry_count,
            "retryIntervalMs": r.retry_interval_ms,
            "cacheTtlSeconds": r.cache_ttl_seconds,
            "rateLimitQps": r.rate_limit_qps,
            "remark": r.remark,
        }

