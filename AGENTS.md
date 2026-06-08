# AGENTS.md

## 项目定位

本项目是一个数据查询中台 / 接口封装平台。核心职责是将外部业务接口的鉴权、SM2/SM4 国密加解密、请求组装、响应解析、查询历史、结果展示和导出能力统一封装。

管理端用于人工配置与查询；开放 API 用于其他业务系统通过接口编码和业务参数调用平台能力。

## 协作原则

- 不要把文档中的规划能力直接当作已实现能力。
- 修改前先阅读 `README.md`、`docs/`、后端服务层和前端页面，确认当前实现状态。
- 不要提交真实 token、SM2 公钥、AppSecret、数据库密码或业务数据。
- 仓库中已有历史 payload 样本，处理前需确认是否包含敏感数据。
- 默认不要修改业务代码，除非任务明确要求。
- 如需改动数据库结构，优先通过 Alembic 迁移，不要只改 ORM 模型。
- 如需改动接口行为，同时检查前端 API 封装、页面调用、开放 API 文档和 README。

## 技术栈

后端：

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- Pydantic v2
- Alembic
- MySQL 8，文档称生产兼容瀚高
- httpx
- Loguru
- gmssl
- python-jose、passlib、bcrypt
- pandas、openpyxl

前端：

- Vue 3
- TypeScript
- Vite
- Element Plus
- Pinia
- Vue Router
- Axios
- ECharts
- vxe-table

部署：

- Docker Compose
- MySQL 8
- Redis 7，当前主要为预留
- FastAPI + Gunicorn + UvicornWorker
- Nginx 静态前端与同源反代

## 主要目录

- `backend/`：FastAPI 后端。
- `backend/app/api/v1/`：管理 API 与开放 API 路由。
- `backend/app/services/`：核心业务逻辑。
- `backend/app/adapters/`：外部接口调用与国密适配。
- `backend/app/models/`：SQLAlchemy ORM 模型。
- `backend/alembic/versions/`：数据库迁移脚本。
- `backend/scripts/`：种子数据、真实查询调试、结果配置初始化脚本。
- `frontend/`：Vue 管理端。
- `frontend/src/views/`：页面。
- `frontend/src/components/`：动态表单、表格、分析图表、JSON 查看等组件。
- `frontend/src/api/`：前端 API 封装。
- `docs/`：技术栈、数据库设计、开放 API、威海接口与业务接口说明。
- `deploy/`：Docker 环境变量示例。
- `secret/`：Java 版 SM2/SM4 demo 与工具类。

## 已确认功能

- 管理端 JWT 登录。
- 接口配置 CRUD 与连通性测试。
- 参数模板维护与动态表单 schema。
- 查询执行链路：加载配置、参数处理、国密加密、远端调用、响应解密、落库。
- 查询历史、详情、结构化回放和完整 payload 读取。
- 结果解析、统计分析和图表展示。
- 成功查询记录导出 CSV/XLSX。
- 开放 API：接口清单、统一查询、历史、详情、导出、文件下载。
- 大响应阈值内入库，超阈值落盘。

## 待确认或未完全落地能力

- `USE_MOCK_REMOTE`、`USE_MOCK_CRYPTO` 配置存在，但当前查询执行链路未真正按开关切换 mock。
- Redis 配置和 Compose 服务存在，但业务代码未实际使用。
- `cache_ttl_seconds`、`rate_limit_qps` 字段存在，但缓存和限流未落地。
- `dq_audit_log` 表和模型存在，但未看到实际写入调用。
- 用户、角色、用户角色表存在，但 RBAC 权限控制未落地。
- 开放 API 客户端管理 UI 未实现。
- `ip_whitelist` 字段存在，但开放 API 鉴权未校验来源 IP。
- `request_body_template`、`request_path_expr` 字段存在，但请求组装主要仍直接使用 `params`。
- 导出任务当前同步生成，非后台异步队列。

## 运行与部署提示

本地后端：

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
python -m scripts.init_seed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

本地前端：

```bash
cd frontend
npm install
npm run dev
```

Docker：

```bash
cp deploy/env.docker.example .env
docker compose up -d --build
docker compose exec backend python -m scripts.init_seed
```

## 注意事项

- `backend/scripts/init_seed.py` 会创建 `admin / admin123` 和 demo 开放 API 凭证，生产环境需立即替换或禁用。
- `app_secret_hash` 字段当前实际为明文比对，待安全加固。
- 管理端 `/docs`、`/openapi.json` 在 Nginx 中有反代配置，生产是否暴露待确认。
- 文档中部分中文文件名显示乱码，编码/文件名来源待确认。
