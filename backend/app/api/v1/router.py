"""聚合 v1 所有路由。开放 API 在 main 中单独挂载 /open-api。"""
from fastapi import APIRouter

from app.api.v1 import auth, interfaces, params, query, export

api_router = APIRouter(prefix="/api", tags=["管理后台"])

# 认证
api_router.include_router(auth.router, prefix="", tags=["管理后台"])
# 接口配置
api_router.include_router(interfaces.router, prefix="/interfaces", tags=["管理后台"])
# 参数模板：接口下挂载 /interfaces/{id}/params
api_router.include_router(params.interface_router, prefix="/interfaces", tags=["管理后台"])
# 参数模板：独立 CRUD /api/params/{id}
api_router.include_router(params.param_router, prefix="", tags=["管理后台"])
# 查询执行与历史
api_router.include_router(query.router, prefix="/query", tags=["管理后台"])
# 导出
api_router.include_router(export.router, prefix="/export", tags=["管理后台"])
