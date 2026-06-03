# 统一数据查询开放 API 说明（接口中台）

本文档面向 **调用方业务系统**，描述如何通过本平台 **以统一、简化的方式** 完成数据查询与结果导出。

## 1. 系统定位

- 本平台作为 **接口封装层 / 接口中台**：对上游复杂接口的 **鉴权头、报文结构、国密加解密、字段解析** 等均在 **系统内部** 完成。
- 调用方 **无需** 了解 SM2/SM4、对方 token、密文字段等细节；只需掌握：
  - 本平台分配的 **AppKey / AppSecret**；
  - 已配置的 **接口编码 `interfaceCode`**；
  - 与参数模板一致的 **业务参数 `params`**。

## 2. 接口分层（请务必区分）

| 类型 | 路径前缀 | 认证 | 用途 |
|------|-----------|------|------|
| **对外开放 API** | `/open-api/*` | `X-App-Key` + `X-App-Secret` | 供业务系统自动化调用（**推荐集成方式**） |
| **管理后台 API** | `/api/*` | `Authorization: Bearer <JWT>` | 人工配置接口、参数模板、运维查询 |
| **内部/运维** | 如 `GET /api/query/history/{id}/payload` | JWT | 大报文按需加载等，**不承诺给外部业务系统** |

Swagger/OpenAPI 中标签 **「开放API（业务系统对接）」** 下列出的路径即为对外契约；**「管理后台」** 为运维使用。

## 3. 通用约定

### 3.1 Base URL

- 与部署环境一致，例如：`https://your-gateway.example.com`。
- 若经 Nginx/网关 **同源反代**，浏览器或内网 HTTP 客户端访问：`/open-api/...`。
- **不要**在集成代码中写死 `localhost`，应使用配置项或网关域名。

### 3.2 请求头（开放 API 必带）

| 头名称 | 说明 |
|--------|------|
| `Content-Type` | `application/json`（POST JSON 时） |
| `X-App-Key` | 平台分配的客户端标识 |
| `X-App-Secret` | 平台分配的密钥（请走 HTTPS 或专线，勿日志打印） |
| `X-Trace-Id` | 可选，调用方传入则贯穿日志；不传由服务端生成 |

### 3.3 通用响应结构

HTTP 状态码一般为 **200**；业务成功与否看 JSON 中的 `success` 与 `code`：

```json
{
  "success": true,
  "code": "0",
  "message": "success",
  "traceId": "20260324120000-abc123",
  "data": { }
}
```

| 字段 | 说明 |
|------|------|
| `success` | 业务是否成功（注意：部分失败仍为 HTTP 200 + `success: false`） |
| `code` | 业务码，`"0"` 表示成功；非 0 见下文错误码 |
| `message` | 人类可读说明 |
| `traceId` | 链路 ID，排错时请提供给平台方 |
| `data` | 业务负载，随接口变化 |

### 3.4 错误码（常见）

| code | 含义 |
|------|------|
| `0` | 成功 |
| `400` | 参数校验失败等 |
| `401` | 开放客户端鉴权失败（Key/Secret 错误或未启用） |
| `404` | 资源不存在（含「无权访问」场景，避免泄露资源存在性） |
| `500` | 未预期异常 |
| 其他 | 查询执行失败时可能返回业务异常码（如 `REMOTE_ERROR`、`CRYPTO_ERROR` 等） |

**失败示例：**

```json
{
  "success": false,
  "code": "401",
  "message": "开放客户端凭证错误",
  "traceId": "xxx",
  "data": null
}
```

---

## 4. 接口列表

### 4.1 获取可对外的接口清单

- **路径**：`GET /open-api/interfaces`
- **说明**：返回已启用且允许开放调用的接口，供调用方选型。

**响应 `data`：**

```json
{
  "list": [
    {
      "interfaceCode": "province_case_push",
      "interfaceName": "省办件归集数据下发(示例)",
      "envCode": "prod",
      "interfaceCategory": "示例"
    }
  ]
}
```

---

### 4.2 执行统一查询（核心）

- **路径**：`POST /open-api/query`
- **说明**：按 `interfaceCode` 与业务参数发起一次查询；平台内部完成与上游的通信与解析。

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `interfaceCode` | string | 是 | 接口编码，须已配置且勾选允许开放 API |
| `params` | object | 否 | 业务参数键值，与参数模板一致 |
| `envCode` | string | 否 | 默认 `prod`，须与配置中环境一致 |

**示例请求：**

```http
POST /open-api/query HTTP/1.1
Host: api.example.com
Content-Type: application/json
X-App-Key: demo_app_key
X-App-Secret: demo_app_secret

{
  "interfaceCode": "province_case_push",
  "envCode": "prod",
  "params": {
    "sblsh": "03302095117791"
  }
}
```

**响应说明：**

为隐藏内部 `rawData` 等调试字段，开放查询的返回在标准 envelope 下，`data` 结构为：

| 字段 | 说明 |
|------|------|
| `interfaceCode` | 接口编码 |
| `durationMs` | 耗时（毫秒） |
| `queryRecordId` | 本次查询落库记录 ID，可用于历史/导出 |
| `result` | 标准化结果：`list`、`total`、`page`、`pageSize`、`summary` 等（与内部解析逻辑一致） |

**示例响应（成功，节选）：**

```json
{
  "success": true,
  "code": "0",
  "message": "success",
  "traceId": "xxx",
  "data": {
    "interfaceCode": "province_case_push",
    "durationMs": 120,
    "queryRecordId": 42,
    "result": {
      "list": [],
      "total": 0,
      "summary": { "count": 0 }
    }
  }
}
```

---

### 4.3 查询历史（当前客户端）

- **路径**：`GET /open-api/query/history`
- **查询参数**：`page`、`pageSize`、`interfaceCode`（可选）、`successFlag`（可选）
- **说明**：仅返回 **本 AppKey** 通过开放 API 产生的记录摘要。

**响应 `data`：**

```json
{
  "list": [
    {
      "id": 42,
      "traceId": "xxx",
      "interfaceCode": "province_case_push",
      "interfaceName": "…",
      "successFlag": 1,
      "durationMs": 120,
      "responseCode": "200",
      "responseMessage": "ok",
      "errorMessage": null,
      "createdAt": "2026-03-24T12:00:00"
    }
  ],
  "total": 100,
  "page": 1,
  "pageSize": 20
}
```

---

### 4.4 单条查询详情（当前客户端）

- **路径**：`GET /open-api/query/history/{history_id}`（`history_id` 为列表项中的 `id`）
- **说明**：返回摘要字段，**不包含**加解密中间报文；用于对账与排错。

**响应 `data`（示例）：**

```json
{
  "id": 42,
  "traceId": "xxx",
  "interfaceCode": "province_case_push",
  "successFlag": 1,
  "durationMs": 120,
  "createdAt": "2026-03-24T12:00:00",
  "responseCode": "200",
  "responseMessage": "ok",
  "errorMessage": null,
  "httpStatusCode": 200
}
```

---

### 4.5 创建导出任务

- **路径**：`POST /open-api/export`
- **说明**：仅允许导出 **本客户端** 产生且 **成功** 的查询记录。

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `queryRecordId` | int | 是 | `POST /open-api/query` 返回的 `data.queryRecordId` |
| `exportType` | string | 否 | `csv` 或 `xlsx`，默认 `csv` |

**响应 `data`：**

```json
{
  "taskId": "十六进制任务号",
  "status": "DONE",
  "fileName": "export_xxx.csv",
  "downloadPath": "/open-api/export/files/export_xxx.csv"
}
```

下载时请使用 **与查询相同的 Base URL** + `downloadPath`，并携带相同 `X-App-Key` / `X-App-Secret`。

---

### 4.6 查询导出任务状态

- **路径**：`GET /open-api/export/{taskId}`

**响应 `data`：** 含 `taskId`、`status`、`fileName`、`downloadPath`、`fileSize`、`failureReason` 等。

---

### 4.7 下载导出文件

- **路径**：`GET /open-api/export/files/{fileName}`
- **说明**：返回文件流；需携带开放 API 请求头。

---

## 5. 典型调用链路

1. （可选）`GET /open-api/interfaces` 确认可用接口与 `envCode`。
2. `POST /open-api/query` 执行业务查询，记录返回的 `traceId` 与 `data.queryRecordId`。
3. 若需留痕：`GET /open-api/query/history` / `GET /open-api/query/history/{id}`。
4. 若需表格文件：`POST /open-api/export` → `GET /open-api/export/{taskId}` → `GET /open-api/export/files/{fileName}`。

---

## 6. Swagger / OpenAPI

部署后可通过 **`/docs`** 查看交互文档；对外契约集中在标签 **「开放API（业务系统对接）」**。  
机器可读模式定义：`GET /openapi.json`（若生产关闭浏览器访问，可由网关脱敏后内网开放）。

---

## 7. 演示凭证（仅用于开发/联调）

执行 `python -m scripts.init_seed` 后（见根目录 README）：

- `X-App-Key: demo_app_key`
- `X-App-Secret: demo_app_secret`

**生产环境**请为每个业务系统单独开立客户端并轮换密钥；禁止复用演示 Key。
