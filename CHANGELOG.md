# CHANGELOG.md

## Unreleased

### Documentation

- 新增项目协作说明 `AGENTS.md`。
- 新增 AI 上下文说明 `AI_CONTEXT.md`。
- 新增任务清单 `TASKS.md`。
- 新增变更记录 `CHANGELOG.md`。

### Current Confirmed Capabilities

- 后端提供 FastAPI 管理 API 与开放 API。
- 前端提供 Vue 3 管理端页面。
- 支持 JWT 登录、接口配置、参数模板、查询执行、查询历史、结果解析、统计分析和导出。
- 支持 `/open-api/*` 给外部业务系统调用。
- 支持 SM2/SM4 混合加解密链路。
- 支持查询大 payload 阈值内入库、超阈值落盘。
- 提供 Docker Compose 编排 MySQL、Redis、后端和前端 Nginx。

### Known Gaps

- mock 配置存在，但查询执行链路未真正按 `USE_MOCK_REMOTE` / `USE_MOCK_CRYPTO` 切换。
- Redis、缓存、限流为预留能力，当前未见业务落地。
- 审计日志表存在，但未见实际写入。
- RBAC 表存在，但权限控制未落地。
- 开放 API `app_secret_hash` 当前实际为明文比对。
- 开放 API 客户端 IP 白名单字段未实际使用。
- 请求体模板和参数路径注入字段存在，但查询组装未完整使用。
- 未发现测试文件。

## 2026-06-08

### Review

- 完成一次只读项目审查。
- 审查范围包括 README、配置文件、数据库迁移脚本、后端代码、前端代码和 `docs/` 文档。
- 未修改业务代码。

### Findings

- 项目定位为数据查询中台 / 接口封装平台。
- 后端主体功能较完整，但部分文档描述超前于实现。
- 前端已具备内部管理端雏形。
- 数据库设计覆盖核心实体，但未声明外键约束。
- 部署路径以 Docker Compose 为主，本地开发路径也已在 README 中说明。
