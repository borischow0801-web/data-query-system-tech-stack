# 数据查询系统（后端 + 前端）

## 技术栈

- 后端：Python 3.11+、FastAPI、SQLAlchemy 2、Pydantic v2、Alembic、httpx、Redis、Loguru、gmssl（SM2/SM4）
- 前端：Vue 3、TypeScript、Vite、Element Plus、Pinia、Axios、ECharts
- 数据库：MySQL 8（生产兼容瀚高）

---

## 一、目录结构

```text
backend/           # 后端 FastAPI 服务（含 Dockerfile）
frontend/          # 前端 Vue3 + Vite + 生产 Nginx（含 Dockerfile）
docs/              # 技术说明；对外开放契约见 docs/open-api-doc.md
deploy/            # Docker 部署示例环境变量
docker-compose.yml # 编排：MySQL + Redis + backend + frontend
secret/            # Java 版 SM2/SM4 demo 与工具类
```

---

## 二、后端启动

### 1. 创建虚拟环境并安装依赖

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

根据 `.env.example` 创建 `.env`：

```bash
cp .env.example .env
```

根据实际修改：

- `DATABASE_URL`：MySQL 连接
- `REDIS_URL`：Redis 连接（可暂不使用）
- `SECRET_KEY`：JWT 密钥
- `EXPORT_STORAGE_PATH`：导出文件存储目录

### 3. 初始化数据库

确保 MySQL 已创建库 `data_query`，然后在 `backend` 目录执行：

```bash
alembic upgrade head
```

### 4. 初始化默认数据（账号 + 示例接口）

在 `backend` 目录执行：

```bash
python -m scripts.init_seed
```

该脚本会：

- 创建管理员账号：`admin / admin123`
- 创建一个示例接口配置：`province_case_push`（用于演示）
- 为该接口创建一个简单参数模板（如 `sblsh`）

### 5. 启动后端

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动后可访问：

- 接口文档：`http://localhost:8000/docs`
- 健康检查：`GET /health`

---

## 三、前端启动

### 1. 安装依赖

```bash
cd frontend
npm install    # 或 pnpm install / yarn
```

### 2. 配置环境变量

开发环境已提供 `.env.development`：

```env
# 留空：前端请求走当前页面的同源路径 /api，由 Vite 代理到本机后端（局域网用服务器 IP 访问前端时不会误连到访问者电脑的 localhost）
VITE_API_BASE_URL=
# Vite 仅在本机把 /api 转发到该地址（后端应跑在同一台机器上）
VITE_PROXY_TARGET=http://127.0.0.1:8000
```

若后端端口不是 8000，请改 `VITE_PROXY_TARGET`。若需浏览器直连后端（不经代理），可设置 `VITE_API_BASE_URL=http://<后端主机>:8000`。

### 3. 启动前端

```bash
npm run dev
```

默认监听 `0.0.0.0:5173`，本机与其它机器均可访问：

- 本机：`http://localhost:5173` 或 `http://127.0.0.1:5173`
- 局域网：`http://<本机局域网IP>:5173`

---

## 四、联调流程示例

1. **确保后端已用 `--host 0.0.0.0` 启动（见上文），本机默认 `http://127.0.0.1:8000`；前端 dev 通过 Vite 代理访问该地址。已初始化 `dq_user` 表账号。**
2. 前端访问登录页（`/login`），使用数据库中的账号密码登录：
   - 登录成功后前端会缓存 JWT，并在所有 `/api/*` 请求中自动携带 `Authorization: Bearer <token>`。
3. 在左侧菜单依次体验：
   - **接口配置**：
     - 列表查询、分页、模糊搜索。
     - 新增/编辑接口配置（基础字段）。
     - 点击“测试”按钮调用后端 `POST /api/interfaces/{id}/test` 做连通性校验。
   - **参数模板**：
     - 在接口列表中点击“参数模板”进入。
     - 批量维护每个接口的参数模板，并保存到后端。
   - **查询执行**：
     - 选择接口 → 加载参数模板（`GET /api/interfaces/{id}/query-form-schema`）。
     - 动态生成查询表单，输入参数后执行查询。
     - 查看标准化 JSON、原始 JSON、表格视图。
   - **查询历史**：
     - 按接口编码、成功与否筛选历史查询。
     - 查看单条记录详情（含请求/响应摘要）。

> 说明：当前 SM2/SM4 加密链路已经抽象在 `adapters/crypto` 中，实际对接外部接口时只需替换对应实现或调整配置即可，不需要修改业务代码。

---

## 五、Mock / Real 模式切换说明

后端在 `Settings` 中提供演示模式开关：

- `USE_MOCK_REMOTE`：是否使用 mock 远程调用（不实际访问外部接口）
- `USE_MOCK_CRYPTO`：是否使用 mock 加密（不依赖 gmssl）

在开发/演示环境中推荐：

```env
USE_MOCK_REMOTE=true
USE_MOCK_CRYPTO=true
```

当切换到真实环境时：

1. 安装国密库 `gmssl`；
2. 将 `.env` 中：
   - `USE_MOCK_REMOTE=false`
   - `USE_MOCK_CRYPTO=false`
3. 在接口配置中填入真实 `base_url/token/sm2PublicKey` 等信息；
4. 系统会自动走真实加密和真实远程调用，无需修改业务代码。

---

## 六、Docker 与生产部署（含麒麟等 Linux 服务器）

本仓库提供 **backend / frontend 镜像** 与根目录 **`docker-compose.yml`**，默认编排：**MySQL 8 + Redis（预留）+ FastAPI（Gunicorn+UvicornWorker）+ Nginx 静态站点与同源反代**。

### 1. 前置条件

- 已安装 **Docker** 与 **Docker Compose** 插件（麒麟等国产系统请使用发行版提供的 Docker CE 或兼容运行时）。
- 宿主机与镜像 **CPU 架构一致**（如 aarch64 服务器需使用 arm64 镜像；官方 `python:3.11-slim-bookworm` 等多架构可用）。
- 开放端口：**`HTTP_PORT`（默认 8080）** 对访问方可见；若需直连调试后端可自行增加 `8000:8000` 映射。
- **目录**：首次启动前准备宿主机挂载目录（默认 `./data/exports`、`./data/query_payloads`、`./data/logs/backend`），用于导出文件、大报文落盘与日志。

### 2. 配置环境变量

```bash
cp deploy/env.docker.example .env
# 编辑 .env：至少设置 MYSQL_ROOT_PASSWORD、MYSQL_PASSWORD、SECRET_KEY
```

### 3. 构建与启动

```bash
docker compose up -d --build
```

- 前端（Nginx）：`http://<宿主机IP>:8080`（`HTTP_PORT` 可改）
- 同源反代：`/api/*`、`/open-api/*`、`/health`、`/docs` → 后端，**勿在浏览器写死 localhost:8000**。

### 4. 数据库迁移与种子数据

Compose 启动 **backend** 时入口脚本会执行 **`alembic upgrade head`**。首次建议再执行种子（需能连上同一 MySQL）：

```bash
docker compose exec backend python -m scripts.init_seed
```

- 管理端默认账号：`admin / admin123`（生产请立即修改密码或禁用）。
- 开放 API 演示凭证（请求头）：`X-App-Key: demo_app_key`，`X-App-Secret: demo_app_secret`（详见 `docs/open-api-doc.md`）。

### 5. 生产注意事项

- **不要把真实密码、SECRET_KEY 提交到仓库**；生产使用密钥管理或编排平台注入环境变量。
- **国密 `gmssl`**：多数情况下 pip 有预编译 wheel；若在特定麒麟/GLIBC 版本上构建失败，需在镜像内增加编译依赖（如 `gcc`）或改用经验证的基础镜像。
- **仅内网暴露**：生产建议关闭或对网关限制 `/docs`、`/openapi.json`。
- **外部数据库**：若 MySQL 由外部环境提供，可从 compose 中移除 `mysql` 服务，将 `DATABASE_URL` 指向外部地址即可。
- **跳过迁移（仅排障）**：容器环境变量 `SKIP_ALEMBIC=1` 可跳过 `alembic upgrade`（勿用于常规发布）。

### 6. 常见问题

| 现象 | 处理 |
|------|------|
| backend 反复重启 | 查看 `docker compose logs backend`，多为连不上 MySQL、或迁移失败 |
| 前端能开页但接口全失败 | 确认 Nginx 反代目标服务名为 `backend:8000`，且 backend 已 healthy |
| 导出文件找不到 | 检查宿主机 `HOST_EXPORT_DIR` 挂载与容器内 `EXPORT_STORAGE_PATH` 一致 |

---

## 七、对外开放 API（接口中台）

**完整契约、错误码与示例见：[docs/open-api-doc.md](docs/open-api-doc.md)。**

- **定位**：其他业务系统只需使用 **接口编码 + 业务参数** 调用本平台；上游 token、报文加解密等由平台在内部完成。
- **认证**：所有 `/open-api/*` 接口（除由网关统一鉴权的情况外）需在请求头携带 **`X-App-Key`**、**`X-App-Secret`**（演示见 `scripts.init_seed`）。
- **管理后台**：`/api/*` 使用 **`Authorization: Bearer <JWT>`**（登录 `POST /api/login`），用于配置接口与人工查询，**不等同于**开放 API 凭证。

### 正式接口联调配置与自检

1. **`.env` 配置（关闭 mock，走真实加密与远程调用）**
   - `USE_MOCK_REMOTE=false`
   - `USE_MOCK_CRYPTO=false`
   - 当前代码中未对上述配置做分支，系统始终使用真实加密（gmssl）与真实 httpx 调用；配置项保留便于后续扩展。

2. **国密依赖**
   - `requirements.txt` 中已包含 `gmssl`；安装：`pip install -r requirements.txt`。若未安装，加密时会抛出 `CryptoError("gmssl 未安装...")`。

3. **最小真实接口测试**
   - 在接口配置中维护好 `base_url`、`request_path`、`token_value`/`token_header_name`、`sm2_public_key` 及响应字段名（`response_code_field_name`、`response_data_field_name` 等）。
   - 执行联调自检脚本（在 `backend` 目录下）：
     ```bash
     python -m scripts.debug_real_query <interface_code> [env_code] [json_params]
     ```
     示例：`python -m scripts.debug_real_query province_case_push dev '{"sblsh":"03302095117791"}'`
   - 脚本会打印：明文 data、请求头、请求体、远程响应原文、解密结果，便于定位问题。

4. **若仍失败，优先检查**
   - gmssl 是否已安装、国密公钥/格式是否与对方一致；
   - 接口配置中 `base_url`、token、`sm2_public_key` 是否正确；
   - 响应 JSON 中 `code`/`data`/`message` 字段名是否与配置的 `response_code_field_name`、`response_data_field_name`、`response_msg_field_name` 一致；
   - 网络与超时（`timeout_ms`）、对方是否返回 200 及可解密 data。

5. **查询失败时查看具体原因**
   - 查询历史中失败记录（successFlag=0）会落库请求明文、请求头、响应原文、响应码/消息、错误信息；
   - 前端「查询历史」→「详情」可查看错误信息、请求明文、响应原文、解密结果。

---

## 八、大响应日志存储（避免 response_raw_text 过长写入失败）

不建议把超大请求/响应完整入库（会导致表膨胀、写入失败、查询变慢）。本项目采用“阈值内联 + 超阈值落盘”的方案：

- **阈值配置**（见 `backend/.env.example`）：
  - `QUERY_LOG_INLINE_MAX_BYTES=65535`
  - `QUERY_LOG_FILE_DIR=./storage/query_payloads`
- **落库策略**：
  - 小于阈值：全文可入库（DB）
  - 超过阈值：DB 仅保存 `preview/size/mode/path`，完整内容写入本地文件
- **查看完整 payload**：
  - 查询历史详情默认展示 preview
  - 通过接口按需读取：`GET /api/query/history/{id}/payload?kind=response_raw|response_plain|request_plain|request_cipher`

---

## 九、当前可演示功能清单

- 登录/鉴权：
  - `POST /api/login`，`GET /api/me`，前端登录页 + 登录态持久化。
- 接口配置管理：
  - 列表、分页、筛选、创建、编辑、删除、测试连接。
- 参数模板管理：
  - 接口下参数模板的批量维护与单条编辑/删除。
- 查询执行：
  - 动态表单（基于参数模板）、执行查询、查看标准结果/原始结果/表格视图、traceId 贯通。
- 查询历史：
  - 分页、按接口/成功状态过滤、查看详情（请求/响应摘要）。
- 导出：
  - 基于查询结果的 JSON/CSV/Excel 导出、导出任务落库与文件下载接口。
- 开放 API：
  - 请求头 `X-App-Key` / `X-App-Secret`；统一查询、历史、导出等（见 `docs/open-api-doc.md`）。
- 审计与日志：
  - 关键操作（登录、接口配置变更、参数模板变更、导出）写入审计表，查询/开放调用日志写入对应表。

---

## 十、真实环境待对接事项清单

以下能力在 mock 模式下已具备结构与接口，切换到真实环境时需要按实际情况接入：

1. **国密加解密库**：
   - 在 real 模式下安装并使用真实 gmssl 或等价国密库，确认与对方系统（如 Java + Hutool/BouncyCastle）的密文格式完全一致。
2. **真实外部接口地址与鉴权**：
   - 将示例接口配置中的 `base_url/token/sm2PublicKey` 等替换为生产环境真实值。
3. **Redis 缓存与任务队列（可选）**：
   - 将导出、大批量查询、定时任务等从同步改为 Redis + Celery 或 APScheduler 等异步方案。
4. **开放 API 客户端管理 UI**：
   - 增加前端页面管理 `dq_open_api_client`（创建/启停/重置秘钥）。
5. **更丰富的结果分析与图表**：
   - 针对实际业务数据增加同比/环比/趋势图等分析逻辑与可视化。

