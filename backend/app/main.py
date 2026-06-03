"""
数据查询系统 - FastAPI 入口。
统一响应格式、全局异常处理、路由挂载。
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import get_settings
from app.core.response import error_response
from app.core.exceptions import AppException, ValidationError
from app.api.v1.router import api_router
from app.api.v1.open_api import router as open_api_router
from app.utils.trace_util import generate_trace_id

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description=(
        "统一数据查询接口封装层（接口中台）：对上游复杂接口的加解密与报文格式在系统内完成；"
        "业务系统请优先对接 `/open-api/*`（请求头 X-App-Key / X-App-Secret），"
        "管理配置与人工操作用 `/api/*`（JWT）。详见 `docs/open-api-doc.md`。"
    ),
    version="1.0.0",
    openapi_tags=[
        {
            "name": "开放API（业务系统对接）",
            "description": "供其他业务系统调用的统一查询、历史与导出；使用 X-App-Key、X-App-Secret，无需了解底层加解密细节。",
        },
        {
            "name": "管理后台",
            "description": "登录后 JWT 访问：接口配置、参数模板、人工查询与运维。",
        },
        {
            "name": "系统",
            "description": "健康检查等。",
        },
    ],
)

# JWT 走 Authorization 头，无需 cookie 跨域凭证；allow_credentials=True 时不能与 allow_origins=["*"] 同用（浏览器会拒绝）。
# 直连后端（不经 Vite 代理）时仍返回合法 CORS 头，便于局域网 IP 访问。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id") or generate_trace_id()
    # 将 trace_id 放入 request.state，便于 service / 审计使用
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response


@app.exception_handler(AppException)
def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=200,
        content=error_response(
            message=exc.message,
            code=exc.code,
            trace_id=getattr(request.state, "trace_id", None)
            or request.headers.get("X-Trace-Id")
            or generate_trace_id(),
        ),
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    """将 FastAPI 的校验异常也包装为统一响应。"""
    trace_id = getattr(request.state, "trace_id", None) or generate_trace_id()
    return JSONResponse(
        status_code=200,
        content=error_response(
            message="参数校验失败",
            code="400",
            trace_id=trace_id,
            data={"errors": exc.errors()},
        ),
    )


# 内部管理 API：/api/*
app.include_router(api_router)

# 开放 API：/open-api/*
app.include_router(open_api_router, prefix="/open-api")


@app.get("/health", tags=["系统"])
def health():
    return {"status": "ok", "app": settings.app_name}
