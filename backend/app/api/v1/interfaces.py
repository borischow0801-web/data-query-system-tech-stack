"""接口配置管理：CRUD + 分页/筛选/脱敏 + 测试连接。"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Path, Query

from app.api.deps import DbSession, CurrentUser
from app.core.response import success_response
from app.services.interface_config_service import InterfaceConfigService

router = APIRouter()
svc = InterfaceConfigService()


@router.get("")
def list_interfaces(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    interface_code: Optional[str] = Query(None),
    interface_name: Optional[str] = Query(None),
    status: Optional[int] = Query(None),
):
    data, total = svc.list_interfaces(
        db=db,
        page=page,
        page_size=page_size,
        interface_code=interface_code,
        interface_name=interface_name,
        status=status,
    )
    return success_response(
        data={
            "list": data,
            "total": total,
            "page": page,
            "pageSize": page_size,
        }
    )


@router.get("/{id}")
def get_interface(
    db: DbSession,
    current_user: CurrentUser,
    id: int = Path(...),
):
    detail = svc.get_interface(db, id)
    return success_response(data=detail)


@router.get("/{id}/result-config")
def get_result_config(
    db: DbSession,
    current_user: CurrentUser,
    id: int = Path(...),
):
    detail = svc.get_interface(db, id)
    # 统一使用 responseMappingTemplate 作为可维护配置载体
    return success_response(
        data={
            "interfaceId": id,
            "interfaceCode": detail.get("interfaceCode"),
            "resultConfig": detail.get("responseMappingTemplate"),
        }
    )


@router.put("/{id}/result-config")
def update_result_config(
    db: DbSession,
    current_user: CurrentUser,
    id: int = Path(...),
    body: dict[str, Any] | None = None,
):
    body = body or {}
    cfg = body.get("resultConfig")
    detail = svc.update_interface(db, id, {"responseMappingTemplate": cfg})
    db.commit()
    return success_response(
        data={
            "interfaceId": id,
            "interfaceCode": detail.get("interfaceCode"),
            "resultConfig": detail.get("responseMappingTemplate"),
        }
    )


@router.post("")
def create_interface(
    db: DbSession,
    current_user: CurrentUser,
    body: dict[str, Any],
):
    detail = svc.create_interface(db, body)
    db.commit()
    return success_response(data=detail)


@router.put("/{id}")
def update_interface(
    db: DbSession,
    current_user: CurrentUser,
    id: int = Path(...),
    body: dict[str, Any] | None = None,
):
    detail = svc.update_interface(db, id, body or {})
    db.commit()
    return success_response(data=detail)


@router.delete("/{id}")
def delete_interface(
    db: DbSession,
    current_user: CurrentUser,
    id: int = Path(...),
):
    svc.soft_delete_interface(db, id)
    db.commit()
    return success_response()


@router.post("/{id}/test")
def test_interface(
    db: DbSession,
    current_user: CurrentUser,
    id: int = Path(...),
):
    result = svc.test_interface_connectivity(db, id)
    return success_response(data=result)
