# 数据查询系统 - 后端

## 技术栈

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- Pydantic v2
- Alembic
- httpx
- Redis
- Loguru
- gmssl（国密 SM2/SM4）

## 项目结构

```
backend/
├── app/
│   ├── api/              # 接口层
│   │   ├── deps.py        # 依赖注入
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── interfaces.py
│   │       ├── params.py
│   │       ├── query.py
│   │       ├── export.py
│   │       ├── open_api.py
│   │       └── router.py
│   ├── core/              # 核心配置与通用逻辑
│   │   ├── config.py
│   │   ├── response.py    # 统一响应格式
│   │   ├── exceptions.py
│   │   └── logger.py
│   ├── db/
│   │   ├── base.py        # SQLAlchemy Base、Mixin
│   │   ├── session.py
│   │   └── migrations/
│   ├── models/            # ORM 模型
│   ├── schemas/           # Pydantic 模型
│   ├── services/          # 业务逻辑
│   │   └── query_executor_service.py
│   ├── adapters/          # 外部适配
│   │   ├── crypto/        # SM2/SM4 加解密
│   │   │   ├── sm2_service.py
│   │   │   ├── sm4_service.py
│   │   │   └── hybrid_encrypt_service.py
│   │   └── remote_api_adapter.py
│   ├── tasks/
│   ├── utils/
│   └── main.py
├── alembic/
├── requirements.txt
└── README.md
```

## 虚拟环境与安装

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 环境变量

可创建 `.env`：

- `DATABASE_URL`：MySQL 连接，默认 `mysql+pymysql://root:password@localhost:3306/data_query?charset=utf8mb4`
- `REDIS_URL`：Redis 连接
- `SECRET_KEY`：JWT 密钥

## 数据库迁移

```bash
# 生成新迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head
```

## 启动

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API 一览

- `POST /api/login` - 登录
- `GET/POST /api/interfaces` - 接口配置列表/新增
- `PUT/DELETE /api/interfaces/{id}` - 更新/删除接口
- `GET/POST /api/interfaces/{id}/params` - 参数模板
- `POST /api/query/execute` - 执行查询
- `GET /api/query/history` - 查询历史
- `POST /api/export` - 创建导出任务
- `GET /api/export/{taskId}` - 查询导出任务
- `POST /open-api/query` - 开放 API 查询
