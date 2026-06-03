"""参数模板：接口下参数管理 + 独立 CRUD + query-form-schema。"""
from typing import Any, Dict, List

from fastapi import APIRouter, Path

from app.api.deps import DbSession, CurrentUser
from app.core.response import success_response
from app.services.parameter_template_service import ParameterTemplateService

interface_router = APIRouter()
param_router = APIRouter()
svc = ParameterTemplateService()


@interface_router.get("/{id}/params")
def list_params(
    db: DbSession,
    current_user: CurrentUser,
    id: int = Path(...),
):
    data = svc.list_params(db, id)
    return success_response(data=data)


@interface_router.post("/{id}/params")
def save_params_batch(
    db: DbSession,
    current_user: CurrentUser,
    id: int = Path(...),
    body: Dict[str, Any] | List[Dict[str, Any]] | None = None,
):
    """批量保存参数模板：body 可以是 {items:[...]} 或直接 [...]."""
    items: List[Dict[str, Any]]
    if isinstance(body, dict) and "items" in body:
        items = body["items"]  # type: ignore
    else:
        items = body or []  # type: ignore
    result = svc.save_params_batch(db, id, items)
    db.commit()
    return success_response(data=result)


@param_router.put("/params/{param_id}")
def update_param(
    db: DbSession,
    current_user: CurrentUser,
    param_id: int = Path(...),
    body: Dict[str, Any] | None = None,
):
    result = svc.update_param(db, param_id, body or {})
    db.commit()
    return success_response(data=result)


@param_router.delete("/params/{param_id}")
def delete_param(
    db: DbSession,
    current_user: CurrentUser,
    param_id: int = Path(...),
):
    svc.delete_param(db, param_id)
    db.commit()
    return success_response()


@interface_router.get("/{id}/query-form-schema")
def get_query_form_schema(
    db: DbSession,
    current_user: CurrentUser,
    id: int = Path(...),
):
    schema = svc.build_query_form_schema(db, id)
    return success_response(data=schema)

