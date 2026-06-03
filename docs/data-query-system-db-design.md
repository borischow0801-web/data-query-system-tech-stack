# 数据查询系统数据库表结构设计文档

## 1. 文档说明

本文档用于指导“数据查询系统”的数据库设计与开发落地，适用于以下业务场景：

- 对接多个外部数据接口
- 统一管理 token、SM2 公钥、接口地址、加密规则
- 动态维护查询参数模板
- 保存查询历史与调用日志
- 支持结果分析与导出
- 支持对外开放 API，供其他业务系统调用
- 支持后续权限管理、审计追踪、异步任务扩展

数据库设计遵循以下原则：

- 兼容 **MySQL 8**
- 生产环境兼容 **瀚高数据库（按 MySQL 兼容 SQL 编写）**
- 尽量避免依赖特定数据库方言特性
- 主业务逻辑放在应用层，不依赖复杂存储过程
- 统一使用 `utf8mb4`
- 所有表保留必要的审计字段与扩展字段

---

## 2. 命名规范

### 2.1 表命名规范
- 采用小写字母 + 下划线
- 表名前缀建议统一为 `dq_`（data query）
- 中间表命名遵循 `主表_关联表` 风格

### 2.2 字段命名规范
- 主键统一：`id`
- 创建时间：`created_at`
- 更新时间：`updated_at`
- 创建人：`created_by`
- 更新人：`updated_by`
- 删除标记：`deleted_flag`
- 启用状态：`status`
- 备注：`remark`
- 扩展字段：`ext_json`

### 2.3 通用字段约定
- `id`：`BIGINT`
- 状态字段：`TINYINT`
- 时间字段：`DATETIME`
- JSON 扩展字段：`JSON`，若兼容性不稳可降级为 `TEXT`

---

## 3. 核心实体关系

本系统建议至少包含以下核心实体：

1. 用户表
2. 角色表
3. 用户角色关联表
4. 接口配置表
5. 接口参数模板表
6. 查询执行记录表
7. 查询结果缓存表（可选）
8. 导出任务表
9. 开放 API 客户端表
10. 开放 API 调用日志表
11. 系统操作审计日志表

---

## 4. 表关系图（逻辑）

```text
dq_user
  └─< dq_user_role >─ dq_role

dq_interface_config
  └─< dq_interface_param_template
  └─< dq_query_record
  └─< dq_export_task

dq_query_record
  └─< dq_open_api_call_log
  └─< dq_export_task（可通过 query_record_id 关联）

dq_open_api_client
  └─< dq_open_api_call_log

dq_user
  └─< dq_query_record
  └─< dq_export_task
  └─< dq_audit_log
```

说明：

- 一个接口配置可以对应多条参数模板
- 一个接口配置可以对应多条查询记录
- 一个查询记录可以对应多个导出任务或开放调用日志
- 一个开放客户端可以产生多条开放接口调用记录
- 用户、角色为后台管理与审计服务

---

## 5. 表结构设计

## 5.1 用户表 `dq_user`

### 设计用途
保存系统后台登录用户信息，用于权限控制、日志留痕、操作审计。

### 建表 SQL

```sql
CREATE TABLE dq_user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
    username VARCHAR(64) NOT NULL COMMENT '登录账号',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    real_name VARCHAR(64) NOT NULL COMMENT '真实姓名',
    mobile VARCHAR(32) DEFAULT NULL COMMENT '手机号',
    email VARCHAR(128) DEFAULT NULL COMMENT '邮箱',
    status TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1启用，0禁用',
    last_login_at DATETIME DEFAULT NULL COMMENT '最后登录时间',
    remark VARCHAR(500) DEFAULT NULL COMMENT '备注',
    ext_json JSON DEFAULT NULL COMMENT '扩展字段',
    deleted_flag TINYINT NOT NULL DEFAULT 0 COMMENT '删除标记：0否，1是',
    created_by BIGINT DEFAULT NULL COMMENT '创建人',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_by BIGINT DEFAULT NULL COMMENT '更新人',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_dq_user_username (username),
    KEY idx_dq_user_status (status),
    KEY idx_dq_user_deleted_flag (deleted_flag)
) COMMENT='用户表';
```

### 字段说明

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT | 主键 |
| username | VARCHAR(64) | 登录账号，唯一 |
| password_hash | VARCHAR(255) | 密码哈希值 |
| real_name | VARCHAR(64) | 用户姓名 |
| mobile | VARCHAR(32) | 手机号 |
| email | VARCHAR(128) | 邮箱 |
| status | TINYINT | 启用/禁用 |
| last_login_at | DATETIME | 最后登录时间 |
| remark | VARCHAR(500) | 备注 |
| ext_json | JSON | 扩展信息 |
| deleted_flag | TINYINT | 逻辑删除标记 |
| created_by | BIGINT | 创建人 |
| created_at | DATETIME | 创建时间 |
| updated_by | BIGINT | 更新人 |
| updated_at | DATETIME | 更新时间 |

---

## 5.2 角色表 `dq_role`

### 设计用途
保存角色信息，用于 RBAC 权限模型扩展。

### 建表 SQL

```sql
CREATE TABLE dq_role (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
    role_code VARCHAR(64) NOT NULL COMMENT '角色编码',
    role_name VARCHAR(64) NOT NULL COMMENT '角色名称',
    status TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1启用，0禁用',
    remark VARCHAR(500) DEFAULT NULL COMMENT '备注',
    ext_json JSON DEFAULT NULL COMMENT '扩展字段',
    deleted_flag TINYINT NOT NULL DEFAULT 0 COMMENT '删除标记：0否，1是',
    created_by BIGINT DEFAULT NULL COMMENT '创建人',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_by BIGINT DEFAULT NULL COMMENT '更新人',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_dq_role_code (role_code),
    KEY idx_dq_role_status (status),
    KEY idx_dq_role_deleted_flag (deleted_flag)
) COMMENT='角色表';
```

---

## 5.3 用户角色关联表 `dq_user_role`

### 设计用途
建立用户与角色的多对多关系。

### 建表 SQL

```sql
CREATE TABLE dq_user_role (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    role_id BIGINT NOT NULL COMMENT '角色ID',
    created_by BIGINT DEFAULT NULL COMMENT '创建人',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_dq_user_role (user_id, role_id),
    KEY idx_dq_user_role_user_id (user_id),
    KEY idx_dq_user_role_role_id (role_id)
) COMMENT='用户角色关联表';
```

---

## 5.4 接口配置表 `dq_interface_config`

### 设计用途
保存外部接口接入配置，是本系统最核心的配置表。

### 设计说明
该表需要支持：

- 多接口配置
- 多环境扩展
- Token 配置
- SM2 公钥配置
- Header / Body 模板配置
- 加密规则配置
- 响应规则配置
- 重试与缓存策略
- 对外开放调用控制

### 建表 SQL

```sql
CREATE TABLE dq_interface_config (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
    interface_code VARCHAR(64) NOT NULL COMMENT '接口编码',
    interface_name VARCHAR(128) NOT NULL COMMENT '接口名称',
    interface_category VARCHAR(64) DEFAULT NULL COMMENT '接口分类',
    env_code VARCHAR(32) NOT NULL DEFAULT 'prod' COMMENT '环境编码：dev/test/prod',
    base_url VARCHAR(500) NOT NULL COMMENT '基础地址',
    request_path VARCHAR(500) DEFAULT NULL COMMENT '请求路径',
    request_method VARCHAR(16) NOT NULL DEFAULT 'POST' COMMENT '请求方式',
    content_type VARCHAR(64) NOT NULL DEFAULT 'application/json' COMMENT '内容类型',
    timeout_ms INT NOT NULL DEFAULT 10000 COMMENT '超时时间毫秒',
    token_value VARCHAR(512) DEFAULT NULL COMMENT 'Token值',
    token_header_name VARCHAR(64) DEFAULT 'token' COMMENT 'Token头名称',
    auth_type VARCHAR(32) NOT NULL DEFAULT 'TOKEN' COMMENT '鉴权方式：NONE/TOKEN/BEARER/CUSTOM',
    sm2_public_key TEXT DEFAULT NULL COMMENT 'SM2公钥',
    encrypt_mode VARCHAR(32) NOT NULL DEFAULT 'SM2_SM4' COMMENT '加密模式',
    sm2_cipher_mode VARCHAR(32) DEFAULT NULL COMMENT 'SM2密文模式：C1C2C3/C1C3C2',
    sm4_mode VARCHAR(32) DEFAULT NULL COMMENT 'SM4模式：ECB/CBC',
    sm4_padding VARCHAR(32) DEFAULT NULL COMMENT 'SM4填充方式：PKCS5/PKCS7/NoPadding',
    cipher_encoding VARCHAR(32) DEFAULT NULL COMMENT '密文编码：HEX/BASE64',
    encrypt_key_header_name VARCHAR(64) DEFAULT 'encryptKey' COMMENT '加密SM4密钥的header字段名',
    request_data_field_name VARCHAR(64) DEFAULT 'data' COMMENT '请求密文字段名',
    response_data_field_name VARCHAR(64) DEFAULT 'data' COMMENT '响应密文字段名',
    response_code_field_name VARCHAR(64) DEFAULT 'code' COMMENT '响应状态码字段名',
    response_msg_field_name VARCHAR(64) DEFAULT 'message' COMMENT '响应消息字段名',
    success_code_value VARCHAR(64) DEFAULT '0' COMMENT '成功状态码值',
    request_header_template TEXT DEFAULT NULL COMMENT '请求头模板JSON',
    request_body_template TEXT DEFAULT NULL COMMENT '请求体模板JSON',
    response_mapping_template TEXT DEFAULT NULL COMMENT '响应映射模板JSON',
    retry_count INT NOT NULL DEFAULT 0 COMMENT '失败重试次数',
    retry_interval_ms INT NOT NULL DEFAULT 1000 COMMENT '重试间隔毫秒',
    cache_ttl_seconds INT NOT NULL DEFAULT 0 COMMENT '缓存秒数，0表示不缓存',
    rate_limit_qps INT DEFAULT NULL COMMENT '接口级限流QPS',
    allow_open_api TINYINT NOT NULL DEFAULT 1 COMMENT '是否允许开放API调用：1是，0否',
    status TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1启用，0停用',
    sort_no INT NOT NULL DEFAULT 0 COMMENT '排序号',
    remark VARCHAR(500) DEFAULT NULL COMMENT '备注',
    ext_json JSON DEFAULT NULL COMMENT '扩展字段',
    deleted_flag TINYINT NOT NULL DEFAULT 0 COMMENT '删除标记：0否，1是',
    created_by BIGINT DEFAULT NULL COMMENT '创建人',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_by BIGINT DEFAULT NULL COMMENT '更新人',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_dq_interface_code_env (interface_code, env_code),
    KEY idx_dq_interface_status (status),
    KEY idx_dq_interface_category (interface_category),
    KEY idx_dq_interface_deleted_flag (deleted_flag)
) COMMENT='接口配置表';
```

### 字段说明（核心）

| 字段 | 说明 |
|---|---|
| interface_code | 接口唯一编码，程序内推荐通过此字段识别接口 |
| interface_name | 展示名称 |
| env_code | 环境隔离，支持 dev/test/prod |
| base_url | 主机地址 |
| request_path | 具体路径 |
| token_value | token 值，仅后端使用 |
| sm2_public_key | 对方系统下发的 SM2 公钥 |
| encrypt_mode | 统一标识加密方案 |
| request_data_field_name | 请求体中的密文字段名 |
| response_data_field_name | 响应体中的密文字段名 |
| response_mapping_template | 用于将外部响应映射为本系统标准结构 |
| allow_open_api | 是否允许外部系统经由本系统调用该接口 |

---

## 5.5 接口参数模板表 `dq_interface_param_template`

### 设计用途
定义每个接口的入参模板，用于：

- 前端动态渲染查询表单
- 后端执行参数校验
- 生成 data 明文报文

### 建表 SQL

```sql
CREATE TABLE dq_interface_param_template (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
    interface_id BIGINT NOT NULL COMMENT '接口配置ID',
    param_code VARCHAR(64) NOT NULL COMMENT '参数编码',
    param_name VARCHAR(128) NOT NULL COMMENT '参数名称',
    display_name VARCHAR(128) NOT NULL COMMENT '显示名称',
    data_type VARCHAR(32) NOT NULL COMMENT '数据类型：string/number/date/month/boolean/json',
    form_component VARCHAR(32) NOT NULL DEFAULT 'input' COMMENT '表单组件类型',
    required_flag TINYINT NOT NULL DEFAULT 0 COMMENT '是否必填：1是，0否',
    default_value VARCHAR(500) DEFAULT NULL COMMENT '默认值',
    example_value VARCHAR(500) DEFAULT NULL COMMENT '示例值',
    placeholder_text VARCHAR(255) DEFAULT NULL COMMENT '占位提示',
    validation_rule VARCHAR(500) DEFAULT NULL COMMENT '校验规则描述',
    request_path_expr VARCHAR(255) DEFAULT NULL COMMENT '写入请求报文的路径表达式',
    sort_no INT NOT NULL DEFAULT 0 COMMENT '排序号',
    visible_flag TINYINT NOT NULL DEFAULT 1 COMMENT '是否可见：1是，0否',
    queryable_flag TINYINT NOT NULL DEFAULT 1 COMMENT '是否参与查询：1是，0否',
    analyzable_flag TINYINT NOT NULL DEFAULT 0 COMMENT '是否参与分析条件：1是，0否',
    exportable_flag TINYINT NOT NULL DEFAULT 1 COMMENT '是否允许导出：1是，0否',
    remark VARCHAR(500) DEFAULT NULL COMMENT '备注',
    ext_json JSON DEFAULT NULL COMMENT '扩展字段',
    deleted_flag TINYINT NOT NULL DEFAULT 0 COMMENT '删除标记：0否，1是',
    created_by BIGINT DEFAULT NULL COMMENT '创建人',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_by BIGINT DEFAULT NULL COMMENT '更新人',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_dq_param_interface_code (interface_id, param_code),
    KEY idx_dq_param_interface_id (interface_id),
    KEY idx_dq_param_sort_no (sort_no),
    KEY idx_dq_param_deleted_flag (deleted_flag)
) COMMENT='接口参数模板表';
```

### 字段说明（核心）

| 字段 | 说明 |
|---|---|
| interface_id | 关联接口配置表 |
| param_code | 参数编码，程序字段名 |
| display_name | 前端表单显示名 |
| data_type | 数据类型 |
| form_component | 动态表单组件类型 |
| required_flag | 是否必填 |
| request_path_expr | 参数注入到报文模板中的路径表达式 |
| analyzable_flag | 是否作为分析筛选维度 |
| exportable_flag | 是否允许导出 |

---

## 5.6 查询执行记录表 `dq_query_record`

### 设计用途
保存每一次查询调用的完整轨迹，是业务日志与问题排查的核心表。

### 设计说明
建议按月分区或定期归档，避免日志无限增长。

### 建表 SQL

```sql
CREATE TABLE dq_query_record (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
    trace_id VARCHAR(64) NOT NULL COMMENT '链路追踪ID',
    interface_id BIGINT NOT NULL COMMENT '接口配置ID',
    interface_code VARCHAR(64) NOT NULL COMMENT '接口编码冗余',
    trigger_type VARCHAR(32) NOT NULL DEFAULT 'WEB' COMMENT '触发来源：WEB/OPEN_API/TASK',
    trigger_client_id BIGINT DEFAULT NULL COMMENT '开放客户端ID',
    operator_user_id BIGINT DEFAULT NULL COMMENT '操作用户ID',
    request_plain_text MEDIUMTEXT DEFAULT NULL COMMENT '请求明文',
    request_cipher_text MEDIUMTEXT DEFAULT NULL COMMENT '请求密文',
    request_headers_text TEXT DEFAULT NULL COMMENT '请求头摘要',
    response_plain_text MEDIUMTEXT DEFAULT NULL COMMENT '响应解密后明文',
    response_cipher_text MEDIUMTEXT DEFAULT NULL COMMENT '响应密文',
    response_raw_text MEDIUMTEXT DEFAULT NULL COMMENT '原始响应文本',
    response_code VARCHAR(64) DEFAULT NULL COMMENT '外部接口响应码',
    response_message VARCHAR(500) DEFAULT NULL COMMENT '外部接口响应消息',
    http_status_code INT DEFAULT NULL COMMENT 'HTTP状态码',
    success_flag TINYINT NOT NULL DEFAULT 0 COMMENT '是否成功：1是，0否',
    duration_ms INT DEFAULT NULL COMMENT '耗时毫秒',
    error_code VARCHAR(64) DEFAULT NULL COMMENT '系统错误码',
    error_message VARCHAR(1000) DEFAULT NULL COMMENT '错误信息',
    analysis_status TINYINT NOT NULL DEFAULT 0 COMMENT '分析状态：0未分析，1已分析',
    export_status TINYINT NOT NULL DEFAULT 0 COMMENT '导出状态：0未导出，1已导出',
    started_at DATETIME DEFAULT NULL COMMENT '开始时间',
    finished_at DATETIME DEFAULT NULL COMMENT '结束时间',
    ext_json JSON DEFAULT NULL COMMENT '扩展字段',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    KEY idx_dq_query_trace_id (trace_id),
    KEY idx_dq_query_interface_id (interface_id),
    KEY idx_dq_query_interface_code (interface_code),
    KEY idx_dq_query_trigger_type (trigger_type),
    KEY idx_dq_query_operator_user_id (operator_user_id),
    KEY idx_dq_query_success_flag (success_flag),
    KEY idx_dq_query_created_at (created_at)
) COMMENT='查询执行记录表';
```

### 字段说明（核心）

| 字段 | 说明 |
|---|---|
| trace_id | 整条调用链唯一标识 |
| trigger_type | 触发来源：页面、开放API、定时任务 |
| request_plain_text | 明文请求，需按脱敏规则保存 |
| request_cipher_text | 请求密文，可只存摘要，生产可选不全量存 |
| response_plain_text | 解密后的返回结果 |
| response_cipher_text | 响应密文 |
| success_flag | 调用是否成功 |
| duration_ms | 接口耗时 |
| error_message | 异常原因 |

> 生产建议：`request_cipher_text`、`response_cipher_text` 也可以只保存摘要或截断值，避免日志表过大。

---

## 5.7 查询结果缓存表 `dq_query_cache`（可选）

### 设计用途
对高频、幂等查询结果做短期缓存，减少对第三方接口的重复调用。

### 建表 SQL

```sql
CREATE TABLE dq_query_cache (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
    interface_code VARCHAR(64) NOT NULL COMMENT '接口编码',
    cache_key VARCHAR(128) NOT NULL COMMENT '缓存键',
    request_hash VARCHAR(128) NOT NULL COMMENT '请求摘要',
    result_text MEDIUMTEXT NOT NULL COMMENT '缓存结果',
    expired_at DATETIME NOT NULL COMMENT '过期时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_dq_query_cache_key (cache_key),
    KEY idx_dq_query_cache_interface_code (interface_code),
    KEY idx_dq_query_cache_expired_at (expired_at)
) COMMENT='查询结果缓存表';
```

---

## 5.8 导出任务表 `dq_export_task`

### 设计用途
管理结果导出任务，支持同步导出和异步导出。

### 建表 SQL

```sql
CREATE TABLE dq_export_task (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
    task_no VARCHAR(64) NOT NULL COMMENT '任务编号',
    interface_id BIGINT DEFAULT NULL COMMENT '接口配置ID',
    query_record_id BIGINT DEFAULT NULL COMMENT '关联查询记录ID',
    operator_user_id BIGINT DEFAULT NULL COMMENT '操作用户ID',
    export_type VARCHAR(32) NOT NULL COMMENT '导出类型：EXCEL/CSV/JSON/PDF',
    export_scope VARCHAR(32) NOT NULL DEFAULT 'RESULT' COMMENT '导出范围：RESULT/RAW/ANALYSIS',
    file_name VARCHAR(255) DEFAULT NULL COMMENT '文件名',
    file_path VARCHAR(500) DEFAULT NULL COMMENT '文件路径',
    file_size BIGINT DEFAULT NULL COMMENT '文件大小字节',
    task_status VARCHAR(32) NOT NULL DEFAULT 'PENDING' COMMENT '任务状态：PENDING/RUNNING/SUCCESS/FAILED',
    failure_reason VARCHAR(1000) DEFAULT NULL COMMENT '失败原因',
    started_at DATETIME DEFAULT NULL COMMENT '开始时间',
    finished_at DATETIME DEFAULT NULL COMMENT '结束时间',
    ext_json JSON DEFAULT NULL COMMENT '扩展字段',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_dq_export_task_no (task_no),
    KEY idx_dq_export_query_record_id (query_record_id),
    KEY idx_dq_export_operator_user_id (operator_user_id),
    KEY idx_dq_export_task_status (task_status),
    KEY idx_dq_export_created_at (created_at)
) COMMENT='导出任务表';
```

---

## 5.9 开放 API 客户端表 `dq_open_api_client`

### 设计用途
管理外部业务系统接入本查询系统的调用凭证。

### 设计说明
不能明文保存 secret，建议保存 hash 或加密后密文。

### 建表 SQL

```sql
CREATE TABLE dq_open_api_client (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
    client_code VARCHAR(64) NOT NULL COMMENT '客户端编码',
    client_name VARCHAR(128) NOT NULL COMMENT '客户端名称',
    app_key VARCHAR(128) NOT NULL COMMENT '应用Key',
    app_secret_hash VARCHAR(255) NOT NULL COMMENT '应用Secret哈希',
    contact_name VARCHAR(64) DEFAULT NULL COMMENT '联系人',
    contact_mobile VARCHAR(32) DEFAULT NULL COMMENT '联系电话',
    ip_whitelist TEXT DEFAULT NULL COMMENT 'IP白名单，逗号分隔',
    status TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1启用，0禁用',
    remark VARCHAR(500) DEFAULT NULL COMMENT '备注',
    ext_json JSON DEFAULT NULL COMMENT '扩展字段',
    deleted_flag TINYINT NOT NULL DEFAULT 0 COMMENT '删除标记：0否，1是',
    created_by BIGINT DEFAULT NULL COMMENT '创建人',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_by BIGINT DEFAULT NULL COMMENT '更新人',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_dq_open_api_client_code (client_code),
    UNIQUE KEY uk_dq_open_api_app_key (app_key),
    KEY idx_dq_open_api_status (status),
    KEY idx_dq_open_api_deleted_flag (deleted_flag)
) COMMENT='开放API客户端表';
```

---

## 5.10 开放 API 调用日志表 `dq_open_api_call_log`

### 设计用途
记录外部业务系统通过开放 API 调用本系统的日志。

### 建表 SQL

```sql
CREATE TABLE dq_open_api_call_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
    trace_id VARCHAR(64) NOT NULL COMMENT '链路追踪ID',
    client_id BIGINT NOT NULL COMMENT '开放客户端ID',
    client_code VARCHAR(64) NOT NULL COMMENT '客户端编码冗余',
    interface_code VARCHAR(64) NOT NULL COMMENT '调用的接口编码',
    request_uri VARCHAR(255) DEFAULT NULL COMMENT '请求URI',
    request_method VARCHAR(16) DEFAULT NULL COMMENT '请求方法',
    request_ip VARCHAR(64) DEFAULT NULL COMMENT '请求IP',
    request_params_text MEDIUMTEXT DEFAULT NULL COMMENT '请求参数',
    response_text MEDIUMTEXT DEFAULT NULL COMMENT '响应内容',
    http_status_code INT DEFAULT NULL COMMENT 'HTTP状态码',
    success_flag TINYINT NOT NULL DEFAULT 0 COMMENT '是否成功：1是，0否',
    duration_ms INT DEFAULT NULL COMMENT '耗时毫秒',
    error_message VARCHAR(1000) DEFAULT NULL COMMENT '错误信息',
    query_record_id BIGINT DEFAULT NULL COMMENT '关联查询记录ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    KEY idx_dq_open_call_trace_id (trace_id),
    KEY idx_dq_open_call_client_id (client_id),
    KEY idx_dq_open_call_interface_code (interface_code),
    KEY idx_dq_open_call_success_flag (success_flag),
    KEY idx_dq_open_call_created_at (created_at)
) COMMENT='开放API调用日志表';
```

---

## 5.11 审计日志表 `dq_audit_log`

### 设计用途
记录后台敏感操作，例如：

- 新增/修改接口配置
- 修改 token
- 修改 SM2 公钥
- 执行导出
- 开放客户端新增或禁用

### 建表 SQL

```sql
CREATE TABLE dq_audit_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
    operator_user_id BIGINT DEFAULT NULL COMMENT '操作用户ID',
    operator_name VARCHAR(64) DEFAULT NULL COMMENT '操作人姓名',
    module_name VARCHAR(64) NOT NULL COMMENT '模块名称',
    operation_type VARCHAR(32) NOT NULL COMMENT '操作类型：CREATE/UPDATE/DELETE/EXPORT/LOGIN',
    target_type VARCHAR(64) NOT NULL COMMENT '目标类型',
    target_id BIGINT DEFAULT NULL COMMENT '目标ID',
    target_code VARCHAR(128) DEFAULT NULL COMMENT '目标编码',
    operation_content TEXT DEFAULT NULL COMMENT '操作内容',
    request_ip VARCHAR(64) DEFAULT NULL COMMENT '请求IP',
    success_flag TINYINT NOT NULL DEFAULT 1 COMMENT '是否成功：1是，0否',
    error_message VARCHAR(1000) DEFAULT NULL COMMENT '失败原因',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    KEY idx_dq_audit_operator_user_id (operator_user_id),
    KEY idx_dq_audit_module_name (module_name),
    KEY idx_dq_audit_operation_type (operation_type),
    KEY idx_dq_audit_target_type (target_type),
    KEY idx_dq_audit_created_at (created_at)
) COMMENT='审计日志表';
```

---

## 6. 推荐初始化数据

## 6.1 初始化角色

建议初始化以下角色：

| role_code | role_name | 说明 |
|---|---|---|
| SUPER_ADMIN | 超级管理员 | 系统全权限 |
| CONFIG_ADMIN | 配置管理员 | 管理接口配置、参数模板 |
| QUERY_USER | 查询用户 | 执行查询、查看结果 |
| AUDITOR | 审计人员 | 查看日志、审计记录 |
| OPEN_API_ADMIN | 开放平台管理员 | 管理外部调用方 |

---

## 6.2 初始化接口示例

建议初始化“省办件归集数据下发”接口一条配置记录，包括：

- interface_code：`province_case_push`
- interface_name：`省办件归集数据下发`
- base_url：`http://172.20.218.7:32000`
- token_value：按实际配置
- sm2_public_key：按实际配置
- encrypt_mode：`SM2_SM4`

---

## 7. 建索引建议

## 7.1 高频查询索引
以下字段建议建索引：

- `dq_interface_config.interface_code`
- `dq_interface_param_template.interface_id`
- `dq_query_record.trace_id`
- `dq_query_record.interface_code`
- `dq_query_record.created_at`
- `dq_export_task.task_no`
- `dq_open_api_client.app_key`
- `dq_open_api_call_log.client_id`

## 7.2 大表归档建议
以下表后期可能快速膨胀：

- `dq_query_record`
- `dq_open_api_call_log`
- `dq_audit_log`

建议：

- 按月归档
- 或按时间区间迁移历史数据
- 必要时拆分冷热数据

---

## 8. 安全设计建议

## 8.1 敏感字段处理
以下字段不得在页面明文展示：

- `token_value`
- `app_secret_hash`
- 未来若有私钥配置，也不得明文保存

建议：

- 页面展示时脱敏
- 更新时采用“覆盖更新，不回显原值”
- 审计日志不记录完整敏感值

## 8.2 日志脱敏建议
以下内容写入日志时应脱敏或摘要化：

- 身份证号
- 手机号
- token
- 密钥
- 敏感业务参数
- 完整密文

---

## 9. 一期必须落库的表

若一期先快速落地，建议最少建以下 7 张表：

1. `dq_user`
2. `dq_role`
3. `dq_user_role`
4. `dq_interface_config`
5. `dq_interface_param_template`
6. `dq_query_record`
7. `dq_export_task`

这样已经可以支撑：

- 用户登录
- 接口配置
- 参数模板
- 查询执行
- 查询日志
- 结果导出

---

## 10. 二期扩展表

二期建议增加：

1. `dq_open_api_client`
2. `dq_open_api_call_log`
3. `dq_audit_log`
4. `dq_query_cache`

这样可以支撑：

- 对外 API 开放
- 调用方管理
- 审计追踪
- 查询缓存加速

---

## 11. 给 Cursor 的数据库开发约束

### 11.1 建模约束
- 所有 ORM Model 与表名保持一致
- 所有主键统一使用 `BIGINT`
- 所有状态字段统一使用 `TINYINT` 或短枚举字符串
- 所有审计字段在 BaseModel 中统一抽象
- 所有逻辑删除表必须带 `deleted_flag`

### 11.2 代码约束
- 接口配置表与参数模板表必须拆分建模，不允许混在一个表
- 查询记录必须保存 `trace_id`
- 导出任务必须独立建表，不允许直接依赖前端下载
- 开放 API 客户端与调用日志分表设计
- 敏感字段读写必须经过服务层处理

### 11.3 SQL 兼容性约束
- 按 MySQL 8 语法编写
- 避免复杂触发器、存储过程、窗口特性依赖
- JSON 字段仅作扩展，不作核心查询依赖
- 生产若瀚高 JSON 兼容性有限，可退化为 TEXT

---

## 12. 最终建议

本数据库设计已经覆盖以下核心能力：

- 多接口接入配置
- 国密加解密参数配置
- 动态参数模板
- 查询日志留痕
- 结果导出
- 外部系统调用
- 审计追踪
- 后续缓存、分析、任务扩展

在此基础上，Cursor 可以继续开展以下开发工作：

1. SQLAlchemy 模型生成
2. Alembic 迁移脚本生成
3. 后端 CRUD 接口生成
4. 查询执行服务开发
5. 动态表单接口开发
6. 日志与导出模块开发

---

## 13. 建议的后续文档

建议在本数据库文档之后，继续补齐以下文档：

1. 后端 API 设计文档
2. 接口配置字段字典文档
3. 查询执行流程文档
4. Cursor 开发约束文档
5. 前端页面原型说明文档

补齐后即可进入较完整的开发阶段。
