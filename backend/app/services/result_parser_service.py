"""结果解析服务：按 response_mapping_template 将解密响应解析为列表/详情结构 + 展示元数据。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from app.models.interface_config import DqInterfaceConfig


def _get_by_path(obj: Any, path: str | None) -> Any:
    if obj is None or not path:
        return None
    cur = obj
    for part in str(path).split("."):
        if part == "":
            continue
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def _to_int(x: Any) -> int | None:
    if x is None:
        return None
    if isinstance(x, int):
        return x
    try:
        return int(str(x))
    except Exception:
        return None


def _flatten_kv(obj: Any, max_items: int = 80) -> list[dict[str, Any]]:
    """单层对象转 {label, value, rawKey} 列表。"""
    if not isinstance(obj, dict):
        return [{"label": "值", "value": _display_scalar(obj), "rawKey": "_"}]
    out: list[dict[str, Any]] = []
    for i, (k, v) in enumerate(obj.items()):
        if i >= max_items:
            out.append({"label": "…", "value": f"其余 {len(obj) - max_items} 项已省略", "rawKey": "…"})
            break
        out.append({"label": str(k), "value": _display_scalar(v), "rawKey": str(k)})
    return out


def _display_scalar(v: Any) -> str:
    if v is None:
        return "—"
    if isinstance(v, (dict, list)):
        try:
            s = json.dumps(v, ensure_ascii=False)
            return s if len(s) <= 500 else s[:500] + "…"
        except Exception:
            return str(v)[:500]
    s = str(v).strip()
    return s if s else "—"


def _table_from_list(lst: list[Any]) -> dict[str, Any]:
    dict_rows = [r for r in lst if isinstance(r, dict)]
    if not dict_rows:
        return {"type": "empty", "columns": [], "rows": []}
    keys: list[str] = []
    for r in dict_rows[:20]:
        for k in r.keys():
            if k not in keys:
                keys.append(k)
    cols = [{"field": k, "label": k} for k in keys[:40]]
    return {"type": "table", "columns": cols, "rows": dict_rows[:500]}


@dataclass
class ParsedResult:
    list: list[Any]
    total: int | None
    page: int | None
    page_size: int | None
    raw_data: Any
    summary: dict[str, Any] | None = None
    result_mode: str = "list"
    columns: list[dict[str, Any]] = field(default_factory=list)
    detail_sections: list[dict[str, Any]] = field(default_factory=list)
    stats_config: dict[str, Any] = field(default_factory=dict)


class ResultParserService:
    """
    - response_mapping_template JSON 支持：
      result_mode / resultMode: list | detail | mixed
      listPath / list_path, totalPath / total_path, pagePath, pageSizePath
      columns: [{ field, label, sortNo, visible, width? }]
      detailSections / detail_sections: [{ key, title, path? }]
      detailRootPath / detail_root_path: 详情块默认前缀
      stats / stats_config: 传给 ResultAnalysisService
    """

    def parse(
        self,
        interface_config: DqInterfaceConfig,
        decrypted_json: Any,
        request_params: dict[str, Any] | None = None,
    ) -> ParsedResult:
        request_params = request_params or {}

        mapping: dict[str, Any] = {}
        if interface_config.response_mapping_template:
            try:
                mapping = json.loads(interface_config.response_mapping_template) or {}
            except Exception:
                mapping = {}

        list_path = mapping.get("listPath") or mapping.get("list_path")
        total_path = mapping.get("totalPath") or mapping.get("total_path")
        page_path = mapping.get("pagePath") or mapping.get("page_path")
        page_size_path = mapping.get("pageSizePath") or mapping.get("page_size_path")
        result_mode = (mapping.get("result_mode") or mapping.get("resultMode") or "").lower() or "list"
        detail_root = mapping.get("detailRootPath") or mapping.get("detail_root_path") or "data"
        stats_config = mapping.get("stats_config") or mapping.get("stats") or {}
        if not isinstance(stats_config, dict):
            stats_config = {}

        raw_cols = mapping.get("columns")
        columns: list[dict[str, Any]] = []
        if isinstance(raw_cols, list):
            for c in raw_cols:
                if not isinstance(c, dict):
                    continue
                f = c.get("field")
                if not f:
                    continue
                columns.append(
                    {
                        "field": str(f),
                        "label": str(c.get("label") or f),
                        "sortNo": _to_int(c.get("sortNo") or c.get("sort_no")) or 0,
                        "visible": c.get("visible", True),
                        "width": c.get("width"),
                        "minWidth": c.get("minWidth") or c.get("min_width"),
                    }
                )
            columns.sort(key=lambda x: x["sortNo"])

        data = decrypted_json

        lst = _get_by_path(data, list_path) if list_path else None
        total = _get_by_path(data, total_path) if total_path else None
        page = _get_by_path(data, page_path) if page_path else None
        page_size = _get_by_path(data, page_size_path) if page_size_path else None

        if lst is None:
            candidates = [
                "list",
                "rows",
                "data",
                "data.list",
                "data.rows",
                "data.records",
                "data.data",
                "records",
                "items",
                "data.items",
            ]
            for p in candidates:
                v = _get_by_path(data, p)
                if isinstance(v, list):
                    lst = v
                    break
            if lst is None and isinstance(data, list):
                lst = data

        if total is None:
            for p in ["total", "count", "recordsTotal", "data.total", "data.count", "data.recordsTotal"]:
                v = _get_by_path(data, p)
                if isinstance(v, int):
                    total = v
                    break
                if isinstance(v, str) and v.isdigit():
                    total = int(v)
                    break

        page = _to_int(page) or _to_int(request_params.get("page"))
        page_size = _to_int(page_size) or _to_int(request_params.get("pageSize"))

        if not isinstance(lst, list):
            lst = []

        detail_sections: list[dict[str, Any]] = []
        raw_sections = mapping.get("detailSections") or mapping.get("detail_sections") or []
        if result_mode in ("detail", "mixed") and isinstance(raw_sections, list):
            for sec in raw_sections:
                if not isinstance(sec, dict):
                    continue
                key = sec.get("key") or "section"
                title = sec.get("title") or key
                path = sec.get("path")
                if not path:
                    path = f"{detail_root}.{key}" if detail_root else str(key)
                val = _get_by_path(data, path)
                if val is None and detail_root:
                    val = _get_by_path(_get_by_path(data, detail_root), str(key))

                block: dict[str, Any] = {"key": key, "title": title, "path": path}
                if val is None:
                    block["render"] = {"type": "empty", "message": "本节暂无数据（路径与响应不一致时可忽略）"}
                    detail_sections.append(block)
                    continue
                if isinstance(val, list):
                    block["render"] = _table_from_list(val)
                elif isinstance(val, dict):
                    block["render"] = {"type": "kv", "items": _flatten_kv(val)}
                else:
                    block["render"] = {
                        "type": "kv",
                        "items": [{"label": "值", "value": _display_scalar(val), "rawKey": "value"}],
                    }
                detail_sections.append(block)

        if result_mode == "detail" and not detail_sections and isinstance(_get_by_path(data, detail_root), dict):
            root_obj = _get_by_path(data, detail_root)
            detail_sections.append(
                {
                    "key": "data",
                    "title": "详情",
                    "path": detail_root,
                    "render": {"type": "kv", "items": _flatten_kv(root_obj)},
                }
            )

        if not columns and lst and isinstance(lst[0] if lst else None, dict):
            first = lst[0]
            for i, k in enumerate(first.keys()):
                columns.append(
                    {
                        "field": str(k),
                        "label": str(k),
                        "sortNo": i,
                        "visible": True,
                    }
                )

        total_i = total if isinstance(total, int) else _to_int(total)

        return ParsedResult(
            list=lst,
            total=total_i,
            page=page,
            page_size=page_size,
            raw_data=decrypted_json,
            summary={"count": len(lst)},
            result_mode=result_mode if result_mode in ("list", "detail", "mixed") else "list",
            columns=columns,
            detail_sections=detail_sections,
            stats_config=stats_config,
        )
