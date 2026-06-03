"""
查询执行服务。
流程：参数校验 → 加载接口配置 → 组装 data → 生成 SM4 密钥 → SM4 加密 data → SM2 加密 SM4 密钥
     → 调用外部接口 → SM4 解密响应 → 记录日志 → 返回标准化结果。
所有业务逻辑在此或通过 adapter 完成，Controller 仅调用本服务。
"""
import json
import time
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import CryptoError, NotFoundError, RemoteApiError, ValidationError
from app.db.session import SessionLocal
from app.models.interface_config import DqInterfaceConfig
from app.models.query_record import DqQueryRecord
from app.adapters.crypto.hybrid_encrypt_service import HybridEncryptService
from app.adapters.remote_api_adapter import RemoteApiAdapter
from app.core.logger import logger
from app.services.result_parser_service import ResultParserService
from app.services.analysis_service import ResultAnalysisService
from app.services.payload_store_service import PayloadStoreService
from app.utils.trace_util import generate_trace_id


class QueryExecutorService:
    """查询执行：加密、调用、解密、落库、返回。"""

    def execute(
        self,
        interface_code: str,
        params: dict[str, Any],
        env_code: str = "prod",
        trigger_type: str = "WEB",
        operator_user_id: int | None = None,
        trigger_client_id: int | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """
        执行一次查询。
        :param interface_code: 接口编码
        :param params: 前端/开放 API 传入的参数，用于组装 data
        :param env_code: 环境
        :param trigger_type: WEB / OPEN_API / TASK
        :param operator_user_id: 操作用户 ID（可选）
        :param trigger_client_id: 开放客户端 ID（可选）
        :return: 标准化结果 { success, code, message, traceId, data, rawData, durationMs, ... }
        """
        trace_id = trace_id or generate_trace_id()
        started_at = time.time()
        db: Session = SessionLocal()
        record: DqQueryRecord | None = None
        request_plain_text: str | None = None
        request_cipher_text: str | None = None
        request_headers_text: str | None = None
        response_raw_text: str | None = None
        response_code: str | None = None
        response_message: str | None = None
        config: DqInterfaceConfig | None = None
        timeout_plan: dict | None = None
        failure_stage: str | None = None
        raw_params: dict[str, Any] | None = None
        normalized_params: dict[str, Any] | None = None
        request_meta: dict[str, Any] | None = None
        hints: list[str] = []
        try:
            # 1. 加载接口配置
            config = self._get_interface_config(db, interface_code, env_code)
            # 1.1 参数规范化与规则校验（严格按接口规则）
            failure_stage = "validation_failed"
            raw_params = dict(params or {})
            normalized_params, request_meta, hints = self._normalize_params(config, raw_params)
            params = normalized_params
            # 2. 组装 data 明文（按参数模板与 params 组装，此处简化：直接以 params 为 data）
            data_plaintext = json.dumps(params, ensure_ascii=False)
            request_plain_text = data_plaintext
            # 3. 混合加密（返回加密密钥、加密数据、SM4 明文密钥供解密用）
            encrypted_key, encrypted_data, sm4_key_plain = self._encrypt_payload(config, data_plaintext)
            request_cipher_text = encrypted_data
            # 4. 组装请求头与 body
            headers = self._build_headers(config, encrypted_key)
            request_headers_text = json.dumps(headers, ensure_ascii=False)
            body = self._build_body(config, encrypted_data)
            # 5. 调用外部接口
            adapter = self._build_adapter(config)
            timeout_obj = adapter._build_timeout() if hasattr(adapter, "_build_timeout") else None
            timeout_plan = getattr(adapter, "_timeout_debug", lambda _: None)(timeout_obj) if timeout_obj is not None else None
            # 关键日志：对齐“最小联调脚本 vs 正式系统”差异
            try:
                url = f"{adapter.base_url}/{adapter.request_path}" if adapter.request_path else adapter.base_url
            except Exception:
                url = None
            log_headers = dict(headers)
            for k in list(log_headers.keys()):
                lk = str(k).lower()
                if lk in ("token", "authorization", "secret", "encryptkey"):
                    v = str(log_headers.get(k) or "")
                    log_headers[k] = (v[:6] + "****" + v[-4:]) if len(v) > 12 else "****"
            body_debug = {}
            try:
                for bk, bv in (body or {}).items():
                    if isinstance(bv, str):
                        body_debug[bk] = f"<str len={len(bv)}>"
                    else:
                        body_debug[bk] = f"<{type(bv).__name__}>"
            except Exception:
                body_debug = {"_": "<unavailable>"}
            logger.info(
                f"[EXEC] interface={interface_code}/{env_code} url={url} "
                f"timeout_ms={getattr(config, 'timeout_ms', None)} timeout_detail={(getattr(config, 'ext_json', None) or {}).get('httpTimeout') if isinstance(getattr(config, 'ext_json', None), dict) else None} "
                f"timeout_effective={timeout_plan} "
                f"headers={log_headers} body={body_debug} params={params}"
            )
            failure_stage = "remote_call"
            http_status, raw_response, _ = adapter.request(body, headers_override=headers)
            response_raw_text = raw_response
            # 6. 解析响应、解密
            failure_stage = "decrypt_response"
            decrypted_text, response_code, response_message = self._parse_and_decrypt_response(
                config, raw_response, http_status, sm4_key_plain
            )
            # 与最小联调脚本一致：成功码默认 200（但以配置为准）
            success_code = str(config.success_code_value or "200")
            success = response_code is not None and str(response_code) == success_code
            duration_ms = int((time.time() - started_at) * 1000)
            # 7. 落库
            failure_stage = "persist_record"
            payload_store = PayloadStoreService()
            sp_req_plain = payload_store.store_text(trace_id=trace_id, kind="request_plain", text=request_plain_text, ext="json")
            sp_req_cipher = payload_store.store_text(trace_id=trace_id, kind="request_cipher", text=request_cipher_text, ext="txt")
            sp_resp_raw = payload_store.store_text(trace_id=trace_id, kind="response_raw", text=response_raw_text, ext="json")
            sp_resp_plain = payload_store.store_text(trace_id=trace_id, kind="response_plain", text=decrypted_text, ext="json")

            record = self._save_query_record(
                db=db,
                trace_id=trace_id,
                config=config,
                trigger_type=trigger_type,
                operator_user_id=operator_user_id,
                trigger_client_id=trigger_client_id,
                request_plain_text=sp_req_plain.full_text,
                request_cipher_text=sp_req_cipher.full_text,
                request_headers_text=request_headers_text,
                response_plain_text=sp_resp_plain.full_text,
                response_raw_text=sp_resp_raw.full_text or (sp_resp_raw.preview_text if sp_resp_raw.store_mode == "DB" else None),
                response_code=response_code,
                response_message=response_message,
                http_status_code=http_status,
                success_flag=1 if success else 0,
                duration_ms=duration_ms,
                started_at=started_at,
                ext_json={
                    "timeout": {
                        "timeoutMs": config.timeout_ms,
                        "detail": getattr(config, "ext_json", {}) and (config.ext_json or {}).get("httpTimeout"),
                        "effective": timeout_plan,
                    },
                    "failureStage": None,
                    "requestParamsRaw": raw_params,
                    "requestParams": params,
                    "requestMeta": request_meta,
                    "hints": hints,
                },
            )
            # 大报文预览/大小/存储位置
            record.response_raw_preview = sp_resp_raw.preview_text
            record.response_plain_preview = sp_resp_plain.preview_text
            record.response_raw_size = sp_resp_raw.size_bytes
            record.response_plain_size = sp_resp_plain.size_bytes
            # 同一次查询，统一记录 payload store（优先 FILE）
            record.payload_store_mode = "FILE" if (
                sp_req_plain.store_mode == "FILE"
                or sp_req_cipher.store_mode == "FILE"
                or sp_resp_raw.store_mode == "FILE"
                or sp_resp_plain.store_mode == "FILE"
            ) else "DB"
            record.payload_store_path = (
                sp_resp_raw.store_path
                or sp_resp_plain.store_path
                or sp_req_plain.store_path
                or sp_req_cipher.store_path
            )
            db.commit()
            # 8. 标准化返回
            # rawData：尽可能返回外部原始 JSON（便于前端展示）
            raw_json: Any = None
            try:
                raw_json = json.loads(raw_response) if raw_response else None
            except Exception:
                raw_json = raw_response

            parsed = None
            decrypted_json: Any = None
            try:
                decrypted_json = json.loads(decrypted_text) if decrypted_text else None
            except Exception:
                decrypted_json = decrypted_text
            try:
                parsed = ResultParserService().parse(config, decrypted_json, params)
            except Exception:
                parsed = None
            analysis: dict = {}
            display: dict = {}
            if parsed:
                display = {
                    "resultMode": parsed.result_mode,
                    "columns": parsed.columns,
                    "detailSections": parsed.detail_sections,
                }
                analysis = ResultAnalysisService().analyze(
                    parsed.list,
                    parsed.stats_config,
                    duration_ms=duration_ms,
                    success=success,
                    page=parsed.page,
                    page_size=parsed.page_size,
                    total=parsed.total,
                )
            return self._standard_result(
                success=success,
                trace_id=trace_id,
                interface_code=interface_code,
                data={
                    "list": (parsed.list if parsed else []),
                    "total": (parsed.total if parsed else None),
                    "page": (parsed.page if parsed else None),
                    "pageSize": (parsed.page_size if parsed else None),
                    "rawData": (parsed.raw_data if parsed else decrypted_json),
                    "summary": (parsed.summary if parsed else {"count": 0}),
                    "display": display,
                    "analysis": analysis,
                    "hints": hints,
                    "requestMeta": request_meta,
                },
                raw_data=raw_json,
                duration_ms=duration_ms,
                message=response_message or "success",
                query_record_id=record.id,
            )
        except (ValidationError, NotFoundError, CryptoError, RemoteApiError) as e:
            db.rollback()
            duration_ms = int((time.time() - started_at) * 1000)
            err_msg = getattr(e, "message", str(e))
            # 失败阶段细化
            if isinstance(e, ValidationError):
                failure_stage = "validation_failed"
            elif isinstance(e, RemoteApiError):
                # adapter 内已按 connect/read/write/pool 细分 code，这里归一 stage 便于前端展示
                err_code = getattr(e, "code", "") or ""
                if err_code == "REMOTE_TIMEOUT_CONNECT":
                    failure_stage = "remote_timeout_connect"
                elif err_code in ("REMOTE_TIMEOUT_READ", "REMOTE_TIMEOUT_WRITE", "REMOTE_TIMEOUT_POOL"):
                    failure_stage = "remote_timeout_read"
                elif err_code == "REMOTE_PROXY_CONFIG":
                    failure_stage = "remote_proxy_config"
                else:
                    failure_stage = "remote_business_error"
            elif isinstance(e, CryptoError):
                failure_stage = "decrypt_failed"
            if response_raw_text and (response_code is None and response_message is None):
                try:
                    rj = json.loads(response_raw_text)
                    response_code = rj.get("code")
                    # 与真实接口对齐：默认 msg，可由配置覆盖
                    response_message = rj.get((config.response_msg_field_name if config else None) or "msg")
                    if response_code is not None:
                        response_code = str(response_code)
                except Exception:
                    pass
            err_record_id: int | None = None
            if record is None and db:
                payload_store = PayloadStoreService()
                sp_req_plain = payload_store.store_text(trace_id=trace_id, kind="request_plain", text=request_plain_text, ext="json")
                sp_req_cipher = payload_store.store_text(trace_id=trace_id, kind="request_cipher", text=request_cipher_text, ext="txt")
                sp_resp_raw = payload_store.store_text(trace_id=trace_id, kind="response_raw", text=response_raw_text, ext="json")
                err_rec = self._save_error_record(
                    db, trace_id, interface_code, env_code, trigger_type,
                    operator_user_id, trigger_client_id, err_msg, duration_ms,
                    request_plain_text=sp_req_plain.full_text,
                    request_cipher_text=sp_req_cipher.full_text,
                    request_headers_text=request_headers_text,
                    response_raw_text=sp_resp_raw.full_text or (sp_resp_raw.preview_text if sp_resp_raw.store_mode == "DB" else None),
                    response_code=response_code,
                    response_message=response_message,
                    response_raw_preview=sp_resp_raw.preview_text,
                    response_raw_size=sp_resp_raw.size_bytes,
                    payload_store_mode=sp_resp_raw.store_mode,
                    payload_store_path=sp_resp_raw.store_path,
                    ext_json={
                        "timeout": {
                            "timeoutMs": (config.timeout_ms if config else None),
                            "detail": (config.ext_json or {}).get("httpTimeout") if config else None,
                            "effective": timeout_plan,
                        },
                        "failureStage": failure_stage,
                        "errorType": getattr(e, "code", None),
                        "requestParamsRaw": raw_params,
                        "requestParams": normalized_params or params,
                        "requestMeta": request_meta,
                        "hints": hints,
                    },
                )
                db.commit()
                if err_rec is not None:
                    err_record_id = err_rec.id
            return self._standard_result(
                success=False,
                trace_id=trace_id,
                interface_code=interface_code,
                message=err_msg,
                code=getattr(e, "code", "1"),
                duration_ms=duration_ms,
                query_record_id=err_record_id,
            )
        except Exception as e:
            db.rollback()
            duration_ms = int((time.time() - started_at) * 1000)
            err_msg = str(e)
            err_record_id: int | None = None
            if record is None and db:
                try:
                    payload_store = PayloadStoreService()
                    sp_req_plain = payload_store.store_text(trace_id=trace_id, kind="request_plain", text=request_plain_text, ext="json")
                    sp_req_cipher = payload_store.store_text(trace_id=trace_id, kind="request_cipher", text=request_cipher_text, ext="txt")
                    sp_resp_raw = payload_store.store_text(trace_id=trace_id, kind="response_raw", text=response_raw_text, ext="json")
                    err_rec = self._save_error_record(
                        db, trace_id, interface_code, env_code, trigger_type,
                        operator_user_id, trigger_client_id, err_msg, duration_ms,
                        request_plain_text=sp_req_plain.full_text,
                        request_cipher_text=sp_req_cipher.full_text,
                        request_headers_text=request_headers_text,
                        response_raw_text=sp_resp_raw.full_text or (sp_resp_raw.preview_text if sp_resp_raw.store_mode == "DB" else None),
                        response_code=response_code,
                        response_message=response_message,
                        response_raw_preview=sp_resp_raw.preview_text,
                        response_raw_size=sp_resp_raw.size_bytes,
                        payload_store_mode=sp_resp_raw.store_mode,
                        payload_store_path=sp_resp_raw.store_path,
                        ext_json={
                            "timeout": {
                                "timeoutMs": (config.timeout_ms if config else None),
                                "detail": (config.ext_json or {}).get("httpTimeout") if config else None,
                                "effective": timeout_plan,
                            },
                            "failureStage": failure_stage or "local_processing_error",
                            "errorType": "UNHANDLED",
                            "exceptionClass": type(e).__name__,
                            "requestParamsRaw": raw_params,
                            "requestParams": normalized_params or params,
                            "requestMeta": request_meta,
                            "hints": hints,
                        },
                    )
                    db.commit()
                    if err_rec is not None:
                        err_record_id = err_rec.id
                except Exception:
                    db.rollback()
            return self._standard_result(
                success=False,
                trace_id=trace_id,
                interface_code=interface_code,
                message=err_msg,
                code="500",
                duration_ms=duration_ms,
                query_record_id=err_record_id,
            )
        finally:
            db.close()

    def _get_interface_config(self, db: Session, interface_code: str, env_code: str) -> DqInterfaceConfig:
        row = (
            db.query(DqInterfaceConfig)
            .filter(
                DqInterfaceConfig.interface_code == interface_code,
                DqInterfaceConfig.env_code == env_code,
                DqInterfaceConfig.deleted_flag == 0,
                DqInterfaceConfig.status == 1,
            )
            .first()
        )
        if not row:
            raise NotFoundError(f"接口配置不存在: {interface_code}/{env_code}")
        return row

    def _encrypt_payload(self, config: DqInterfaceConfig, data_plaintext: str) -> tuple[str, str, str]:
        if not config.sm2_public_key or config.encrypt_mode != "SM2_SM4":
            raise ValidationError("接口未配置 SM2 公钥或加密模式不是 SM2_SM4")
        hybrid = HybridEncryptService(
            sm2_public_key_hex=config.sm2_public_key,
            sm2_cipher_mode=config.sm2_cipher_mode or "C1C3C2",
            sm4_mode=config.sm4_mode or "ECB",
            sm4_padding=config.sm4_padding or "PKCS5",
            cipher_encoding=config.cipher_encoding or "HEX",
        )
        return hybrid.encrypt_request(data_plaintext)

    def _build_headers(self, config: DqInterfaceConfig, encrypted_key: str) -> dict:
        headers = {}
        if config.token_value and config.token_header_name:
            headers[config.token_header_name] = config.token_value
        key_header = config.encrypt_key_header_name or "encryptKey"
        headers[key_header] = encrypted_key
        return headers

    def _build_body(self, config: DqInterfaceConfig, encrypted_data: str) -> dict:
        field = config.request_data_field_name or "data"
        return {field: encrypted_data}

    def _build_adapter(self, config: DqInterfaceConfig) -> RemoteApiAdapter:
        extra_headers = {}
        if config.request_header_template:
            try:
                extra_headers = json.loads(config.request_header_template)
            except json.JSONDecodeError:
                pass
        # httpx 细分 timeout：优先读 ext_json.httpTimeout（毫秒），否则用 timeout_ms 作为 read timeout
        ext = config.ext_json if isinstance(getattr(config, "ext_json", None), dict) else {}
        timeout_detail = ext.get("httpTimeout") or {}
        verify_tls = ext.get("verifyTls", True)
        if verify_tls is None:
            verify_tls = True
        trust_env = ext.get("httpTrustEnv", False)
        return RemoteApiAdapter(
            base_url=config.base_url,
            request_path=config.request_path or "",
            method=config.request_method or "POST",
            timeout_ms=config.timeout_ms or 10000,
            timeout_detail=timeout_detail if isinstance(timeout_detail, dict) else {},
            headers=extra_headers,
            content_type=config.content_type or "application/json",
            retry_count=config.retry_count or 0,
            retry_interval_ms=config.retry_interval_ms or 1000,
            verify_tls=bool(verify_tls),
            trust_env=bool(trust_env),
        )

    def _normalize_params(
        self, config: DqInterfaceConfig, params: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
        """
        严格按用户已确认的接口规则做参数构造与校验：
        - deptCode/regionCode：二选一必填（两者都空才报错）；空值字段不强行传递
        - page/start/limit：page=0 时 start/limit 可为空；page=1 时 start/limit 必填；禁止混传
        - regionLevel：保留语义并输出风险提示（1=当前及以下，2=当前）
        - 时间范围：不拦截大跨度，但计算跨度并给风险提示，便于区分“远端慢/本系统超时”
        """
        code = (config.interface_code or "").strip()
        # 默认：不改变任何参数，仅做轻量清洗
        out: dict[str, Any] = dict(params or {})
        hints: list[str] = []
        meta: dict[str, Any] = {}

        def _strip_empty(k: str) -> None:
            v = out.get(k)
            if v is None:
                out.pop(k, None)
                return
            if isinstance(v, str) and v.strip() == "":
                out.pop(k, None)

        for k in ("deptCode", "regionCode", "startTime", "endTime", "page", "start", "limit", "regionLevel"):
            _strip_empty(k)

        def _coerce_str_fields(keys: tuple[str, ...]) -> None:
            for k in keys:
                if k in out and out[k] is not None:
                    out[k] = str(out[k]).strip()

        # 仅对已确认规则的接口做强校验（当前以 getBusinessListByDeptOrRegion 为主）
        if code not in ("getBusinessListByDeptOrRegion",):
            return out, meta, hints

        # 与最小联调脚本一致：分页/区划字段使用字符串
        _coerce_str_fields(("page", "start", "limit", "regionLevel", "regionCode", "deptCode"))

        # 1) deptCode/regionCode：二选一必填
        dept = out.get("deptCode")
        region = out.get("regionCode")
        if (dept is None or str(dept).strip() == "") and (region is None or str(region).strip() == ""):
            raise ValidationError("参数校验失败：deptCode 与 regionCode 二选一必填（允许其中一个为空）")

        # 2) regionLevel：保留语义并提示
        rl = out.get("regionLevel")
        rl_s = str(rl).strip() if rl is not None else ""
        if rl_s == "1":
            hints.append("regionLevel=1：查询范围为当前区划及以下区划，范围更大，远端可能响应较慢。")
            meta["regionLevelMeaning"] = "当前区划及以下区划"
        elif rl_s == "2":
            meta["regionLevelMeaning"] = "当前区划"
        elif rl_s:
            meta["regionLevelMeaning"] = f"未知({rl_s})"

        # 3) 时间范围跨度：不拦截，只提示
        def _parse_dt(s: Any):
            if s is None:
                return None
            ss = str(s).strip()
            if not ss:
                return None
            from datetime import datetime

            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(ss, fmt)
                except Exception:
                    pass
            try:
                return datetime.fromisoformat(ss)
            except Exception:
                return None

        st = _parse_dt(out.get("startTime"))
        et = _parse_dt(out.get("endTime"))
        if st and et and et >= st:
            days = (et - st).days
            meta["timeRangeDays"] = days
            if days > 31:
                hints.append(f"时间跨度约 {days} 天：范围较大，远端接口可能响应较慢；若超时可考虑调大 read timeout。")

        # 4) page/start/limit 规则
        page_v = out.get("page")
        page_s = str(page_v).strip() if page_v is not None else ""
        # page 允许字符串 "0"/"1"
        if page_s in ("0", "1"):
            meta["page"] = int(page_s)
        else:
            meta["page"] = page_s or None

        start_present = "start" in out and out.get("start") is not None and str(out.get("start")).strip() != ""
        limit_present = "limit" in out and out.get("limit") is not None and str(out.get("limit")).strip() != ""

        if page_s == "0":
            # page=0：start/limit 可以为空（允许不传），但不允许混传非空 start/limit
            if start_present or limit_present:
                raise ValidationError("参数校验失败：page=0 时 start/limit 必须为空或不传（不能混传非空 start/limit）")
            # 明确移除（避免误传空字符串）
            out.pop("start", None)
            out.pop("limit", None)
        elif page_s == "1":
            # page=1：start/limit 必须有值
            if not start_present or not limit_present:
                raise ValidationError("参数校验失败：page=1 时必须同时传 start 与 limit")
            meta["start"] = out.get("start")
            meta["limit"] = out.get("limit")
        elif page_s:
            # 其他 page：不猜规则，仅提示，避免拍脑袋
            hints.append(f"page={page_s}：当前仅严格校验 page=0/1 的分页规则，请确认远端接口对该值的语义。")

        meta["pagingRule"] = "page=0: start/limit 可为空且不传；page=1: start/limit 必填"
        meta["deptOrRegionRule"] = "deptCode/regionCode 二选一必填"

        return out, meta, hints

    def _apply_query_guards(self, config: DqInterfaceConfig, params: dict[str, Any]) -> None:
        """
        列表接口的大数据保护：
        - 仅对“已提供的 limit”做最大上限，避免一次性拉取过大数据导致远程 read timeout
        说明：此处不依赖参数模板，作为最后一道保护，避免一次性拉取过大数据导致远程 read timeout。
        """
        if not isinstance(params, dict):
            return
        # 仅对明确的列表类接口做保护（默认关闭，由 ext_json.queryGuardEnabled 显式开启）
        code = (config.interface_code or "").strip()
        if code not in ("getBusinessListByDeptOrRegion", "getChainListByDeptOrRegion"):
            return

        def _get_int(key: str) -> int | None:
            v = params.get(key)
            if v is None:
                return None
            try:
                return int(str(v))
            except Exception:
                return None

        max_limit = 500
        # cap：仅当调用方明确传入 limit 时才修正，避免改变远端默认行为（与最小联调脚本一致）
        limit2 = _get_int("limit")
        if limit2 is not None and limit2 > max_limit:
            params["limit"] = max_limit

    def _parse_and_decrypt_response(
        self,
        config: DqInterfaceConfig,
        raw_response: str,
        http_status: int,
        sm4_key_plain: str | None,
    ) -> tuple[str | None, str | None, str | None]:
        if http_status != 200:
            if http_status == 504:
                return None, None, (
                    "HTTP 504：网关/上游在超时时间内未返回（常见为网关 60s 限制）。"
                    "请缩小时间范围、减小 limit，或联系运维调大网关超时。"
                )
            return None, None, f"HTTP {http_status}"
        try:
            resp_json = json.loads(raw_response)
        except json.JSONDecodeError:
            return None, None, "响应非 JSON"
        code = resp_json.get(config.response_code_field_name or "code")
        # 与最小联调脚本一致：默认 msg（但以配置为准）
        msg = resp_json.get(config.response_msg_field_name or "msg")
        data_field = config.response_data_field_name or "data"
        cipher_data = resp_json.get(data_field)
        if not cipher_data:
            return None, code, msg
        if not sm4_key_plain:
            return None, code, msg
        hybrid = HybridEncryptService(
            sm2_public_key_hex=config.sm2_public_key or "",
            sm2_cipher_mode=config.sm2_cipher_mode or "C1C3C2",
            sm4_mode=config.sm4_mode or "ECB",
            sm4_padding=config.sm4_padding or "PKCS5",
            cipher_encoding=config.cipher_encoding or "HEX",
        )
        decrypted = hybrid.decrypt_response(cipher_data, sm4_key_plain)
        return decrypted, code, msg

    def _save_query_record(
        self,
        db: Session,
        trace_id: str,
        config: DqInterfaceConfig,
        trigger_type: str,
        operator_user_id: int | None,
        trigger_client_id: int | None,
        request_plain_text: str,
        request_cipher_text: str,
        request_headers_text: str | None,
        response_plain_text: str | None,
        response_raw_text: str,
        response_code: str | None,
        response_message: str | None,
        http_status_code: int,
        success_flag: int,
        duration_ms: int,
        started_at: float,
        ext_json: dict | None = None,
    ) -> DqQueryRecord:
        from datetime import datetime
        record = DqQueryRecord(
            trace_id=trace_id,
            interface_id=config.id,
            interface_code=config.interface_code,
            trigger_type=trigger_type,
            trigger_client_id=trigger_client_id,
            operator_user_id=operator_user_id,
            request_plain_text=request_plain_text,
            request_cipher_text=request_cipher_text,
            request_headers_text=request_headers_text,
            response_plain_text=response_plain_text,
            response_raw_text=response_raw_text,
            response_code=response_code,
            response_message=response_message,
            http_status_code=http_status_code,
            success_flag=success_flag,
            duration_ms=duration_ms,
            started_at=datetime.fromtimestamp(started_at),
            finished_at=datetime.now(),
            ext_json=ext_json,
        )
        db.add(record)
        return record

    def _save_error_record(
        self,
        db: Session,
        trace_id: str,
        interface_code: str,
        env_code: str,
        trigger_type: str,
        operator_user_id: int | None,
        trigger_client_id: int | None,
        error_message: str,
        duration_ms: int,
        *,
        request_plain_text: str | None = None,
        request_cipher_text: str | None = None,
        request_headers_text: str | None = None,
        response_raw_text: str | None = None,
        response_code: str | None = None,
        response_message: str | None = None,
        response_raw_preview: str | None = None,
        response_plain_preview: str | None = None,
        response_raw_size: int | None = None,
        response_plain_size: int | None = None,
        payload_store_mode: str | None = None,
        payload_store_path: str | None = None,
        ext_json: dict | None = None,
    ) -> DqQueryRecord | None:
        from datetime import datetime
        try:
            config = self._get_interface_config(db, interface_code, env_code)
        except NotFoundError:
            return None
        record = DqQueryRecord(
            trace_id=trace_id,
            interface_id=config.id,
            interface_code=interface_code,
            trigger_type=trigger_type,
            trigger_client_id=trigger_client_id,
            operator_user_id=operator_user_id,
            success_flag=0,
            error_message=(error_message or "")[:1000],
            duration_ms=duration_ms,
            request_plain_text=request_plain_text,
            request_cipher_text=request_cipher_text,
            request_headers_text=request_headers_text,
            response_raw_text=response_raw_text,
            response_raw_preview=response_raw_preview,
            response_plain_preview=response_plain_preview,
            response_raw_size=response_raw_size,
            response_plain_size=response_plain_size,
            payload_store_mode=payload_store_mode or "DB",
            payload_store_path=payload_store_path,
            response_code=response_code,
            response_message=(response_message or "")[:500] if response_message else None,
            started_at=datetime.now(),
            finished_at=datetime.now(),
            ext_json=ext_json,
        )
        db.add(record)
        db.flush()
        return record

    def _standard_result(
        self,
        success: bool,
        trace_id: str,
        interface_code: str,
        message: str = "success",
        code: str = "0",
        data: Any = None,
        raw_data: Any = None,
        duration_ms: int = 0,
        query_record_id: int | None = None,
    ) -> dict[str, Any]:
        out: dict[str, Any] = {
            "success": success,
            "code": code,
            "message": message,
            "traceId": trace_id,
            "interfaceCode": interface_code,
            "durationMs": duration_ms,
            "data": data,
            "rawData": raw_data,
        }
        if query_record_id is not None:
            out["queryRecordId"] = query_record_id
        return out
