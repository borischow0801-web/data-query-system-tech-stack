# AI_CONTEXT.md

## 当前项目一句话说明

数据查询系统是一个面向内部管理端和外部业务系统的数据查询中台，用后端统一处理外部接口鉴权、SM2/SM4 加解密、请求组装、响应解析、查询记录、导出和开放 API。

## 当前实现状态

项目不是空架子，已经具备可运行的前后端主体：

- 后端提供管理 API 和开放 API。
- 前端提供内部管理与查询页面。
- 数据库迁移已覆盖用户、接口配置、参数模板、查询记录、导出任务、开放 API 客户端、开放 API 调用日志、审计日志等表。
- Docker Compose 可编排 MySQL、Redis、后端、前端 Nginx。

但部分能力仍是预留字段或文档规划，不能视为已完成。

## 后端上下文

入口：

- `backend/app/main.py`
- 管理 API 挂载 `/api/*`
- 开放 API 挂载 `/open-api/*`
- 健康检查 `/health`

核心路由：

- `backend/app/api/v1/auth.py`
- `backend/app/api/v1/interfaces.py`
- `backend/app/api/v1/params.py`
- `backend/app/api/v1/query.py`
- `backend/app/api/v1/export.py`
- `backend/app/api/v1/open_api.py`

核心服务：

- `QueryExecutorService`：查询执行主链路。
- `InterfaceConfigService`：接口配置 CRUD。
- `ParameterTemplateService`：参数模板维护。
- `ResultParserService`：按结果映射配置解析响应。
- `ResultAnalysisService`：生成基础统计、分组、趋势、TopN。
- `PayloadStoreService`：大 payload 入库/落盘策略。
- `create_export_task_from_record`：同步生成 CSV/XLSX。

外部接口与国密：

- `RemoteApiAdapter` 使用 httpx 调用外部接口。
- `HybridEncryptService` 负责 SM2 + SM4 混合加解密。
- `Sm2Service`、`Sm4Service` 在 `backend/app/adapters/crypto/`。

## 前端上下文

入口：

- `frontend/src/main.ts`
- `frontend/src/App.vue`
- `frontend/src/router/index.ts`

页面：

- `Login.vue`：登录页。
- `Dashboard.vue`：简单工作台。
- `InterfaceList.vue`：接口配置、结果配置入口。
- `ParamTemplate.vue`：参数模板。
- `QueryExecute.vue`：查询工作台。
- `QueryHistory.vue`：查询历史、详情、结构化回放、导出。

组件：

- `DynamicQueryForm.vue`
- `ResultVxeGrid.vue`
- `AnalysisPanel.vue`
- `DetailSectionPanel.vue`
- `JsonViewer.vue`
- `ResultTable.vue`

API 封装：

- `frontend/src/api/http.ts`
- `frontend/src/api/auth.ts`
- `frontend/src/api/interfaces.ts`
- `frontend/src/api/params.ts`
- `frontend/src/api/query.ts`
- `frontend/src/api/export.ts`

## 数据库上下文

迁移脚本：

- `backend/alembic/versions/20250316000000_init_tables.py`
- `backend/alembic/versions/20260318000100_query_record_payload_store.py`

核心表：

- `dq_user`
- `dq_role`
- `dq_user_role`
- `dq_interface_config`
- `dq_interface_param_template`
- `dq_query_record`
- `dq_export_task`
- `dq_open_api_client`
- `dq_open_api_call_log`
- `dq_audit_log`

已确认：

- 查询记录表有大字段和 payload 文件落盘字段。
- 开放 API 调用日志有实际写入。
- 审计日志表已存在，但实际写入待确认，当前未发现调用。
- 迁移脚本未声明外键约束，关系主要靠应用层维护。

## 重要业务边界

不要编造新的业务领域。当前能确认的业务上下文只有：

- 数据查询中台。
- 对接外部业务接口。
- 威海政务服务云平台 / 办件归集系统相关接口说明。
- 通过接口编码、环境、参数模板执行配置化查询。
- 对内管理端和对外开放 API 两类访问方式。

不确定的真实生产接口、真实字段含义、真实组织权限、真实部署拓扑均应标记为待确认。

## 已知不一致

- README 前半部分描述 mock 开关可用，后文又说明当前代码未对 mock 配置做分支；实际代码也未真正使用 mock 开关。
- README 声称关键操作写审计表，但代码未看到 `DqAuditLog` 写入。
- `app_secret_hash` 字段名暗示哈希存储，但当前为明文比对。
- `encrypt_key_header_name`、`response_msg_field_name`、`success_code_value` 的默认值在迁移、模型、服务、前端之间不完全一致。
- 文档中部分中文文件名乱码，原因待确认。

## 修改建议优先级

高优先级：

- 修正文档与实现不一致，尤其 mock、审计、开放 API 密钥存储。
- 明确生产敏感数据处理策略。
- 为核心查询链路补测试。

中优先级：

- 实现或移除 Redis、缓存、限流等预留能力。
- 增加开放 API 客户端管理页面。
- 增加 RBAC 或明确当前仅登录校验。

低优先级：

- 改善动态表单能力。
- 完善 Dashboard。
- 清理乱码文档文件名。
