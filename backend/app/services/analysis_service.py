"""查询结果自动分析：基于结构化列表与 stats 配置生成分组/趋势/TopN 等（供前端直接展示）。"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from typing import Any

_DATE_RE = re.compile(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})")


def _row_get(row: Any, field: str) -> Any:
    if not field:
        return None
    if isinstance(row, dict):
        cur: Any = row
        for part in field.split("."):
            if not isinstance(cur, dict):
                return None
            cur = cur.get(part)
        return cur
    return None


def _norm_key(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (dict, list)):
        return str(v)[:200]
    s = str(v).strip()
    return s if s else ""


def _parse_date_bucket(val: Any, granularity: str) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    try:
        if "T" in s or (len(s) >= 19 and s[4] == "-"):
            dt = datetime.fromisoformat(s.replace("Z", "+00:00").split("+")[0])
        else:
            m = _DATE_RE.search(s)
            if not m:
                return None
            dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except Exception:
        return None
    if granularity == "month":
        return dt.strftime("%Y-%m")
    return dt.strftime("%Y-%m-%d")


class ResultAnalysisService:
    """列表型结果统计分析。"""

    def analyze(
        self,
        rows: list[Any],
        stats_config: dict[str, Any] | None,
        *,
        duration_ms: int,
        success: bool,
        page: int | None,
        page_size: int | None,
        total: int | None,
    ) -> dict[str, Any]:
        stats_config = stats_config or {}
        if not isinstance(rows, list):
            rows = []

        dict_rows = [r for r in rows if isinstance(r, dict)]

        basic: dict[str, Any] = {
            "currentPageRowCount": len(rows),
            "totalCount": total if total is not None else len(dict_rows),
            "page": page,
            "pageSize": page_size,
            "durationMs": duration_ms,
            "success": success,
        }

        group_out: list[dict[str, Any]] = []
        gb = stats_config.get("groupBy") or stats_config.get("group_by") or []
        if isinstance(gb, list):
            for g in gb:
                if not isinstance(g, dict):
                    continue
                field = g.get("field")
                if not field:
                    continue
                label = g.get("label") or field
                limit = int(g.get("limit") or 50)
                buckets = self._group_count(dict_rows, field, limit)
                group_out.append({"field": field, "label": label, "buckets": buckets})

        trend_cfg = stats_config.get("timeTrend") or stats_config.get("time_trend")
        time_trend: dict[str, Any] | None = None
        if isinstance(trend_cfg, dict):
            tf = trend_cfg.get("field")
            gran = (trend_cfg.get("granularity") or "day").lower()
            if tf and gran in ("day", "month"):
                points = self._time_series(dict_rows, tf, gran)
                if points:
                    time_trend = {
                        "field": tf,
                        "granularity": gran,
                        "points": points,
                    }

        top_out: list[dict[str, Any]] = []
        tops = stats_config.get("topN") or stats_config.get("top_n") or []
        if isinstance(tops, list):
            for t in tops:
                if not isinstance(t, dict):
                    continue
                field = t.get("field")
                if not field:
                    continue
                n = int(t.get("n") or 10)
                label = t.get("label") or field
                items = self._top_values(dict_rows, field, n)
                top_out.append({"field": field, "label": label, "items": items})

        return {
            "basic": basic,
            "groupBy": group_out,
            "timeTrend": time_trend,
            "topN": top_out,
        }

    def _group_count(self, rows: list[dict], field: str, limit: int) -> list[dict[str, Any]]:
        c: Counter[str] = Counter()
        for row in rows:
            k = _norm_key(_row_get(row, field))
            key = k if k else "(空)"
            c[key] += 1
        out = [{"value": k, "count": v} for k, v in c.most_common(limit)]
        return out

    def _time_series(self, rows: list[dict], field: str, gran: str) -> list[dict[str, Any]]:
        c: Counter[str] = Counter()
        for row in rows:
            b = _parse_date_bucket(_row_get(row, field), gran)
            if b:
                c[b] += 1
        keys = sorted(c.keys())
        return [{"bucket": k, "count": c[k]} for k in keys]

    def _top_values(self, rows: list[dict], field: str, n: int) -> list[dict[str, Any]]:
        return self._group_count(rows, field, n)
