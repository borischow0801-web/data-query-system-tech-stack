"""
正式接口最小联调脚本配置模板。

使用方式：
1) 复制为同目录下的 debug_real_query_config.py
   cp scripts/debug_real_query_config.example.py scripts/debug_real_query_config.py
2) 修改本文件中的各项配置为你拿到的正式接口值
3) 在 backend 目录下运行：
   python scripts/debug_real_query.py

配置原则：
- 所有“需要你手工填写”的东西集中在这里
- 每一步都会在脚本输出中打印（敏感信息会脱敏，SM4 密钥会原样打印用于联调核对）
"""

# -----------------------------------------------------------------------------
# 基础请求配置
# -----------------------------------------------------------------------------

# 远端接口基础地址（不要以 / 结尾）
# 示例：BASE_URL="https://api.example.com"
BASE_URL = "http://172.20.218.7:32000"

# 请求路径（可带或不带前导 /）
# 示例：REQUEST_PATH="/open/query"
REQUEST_PATH = "/gate/api/data/getBusinessListByDeptOrRegion"

# 请求方法：POST / GET / PUT ...（默认 POST）
REQUEST_METHOD = "POST"

# HTTP 超时（毫秒）
TIMEOUT_MS = 10000

# TLS 证书校验：生产建议 True；联调自测（自签名）可改 False
VERIFY_TLS = True


# -----------------------------------------------------------------------------
# 鉴权配置
# -----------------------------------------------------------------------------

# 授权码 / token 值（对方返回“请传递授权码”时，通常就是指这个值）
# 注意：此项目对接接口要求“token 值直接放 header”，不要加 "Bearer " 前缀
TOKEN = "300f5294b6f949feaf36b3cccacbba20"

# token 对应的 header 名（按对方文档：token）
TOKEN_HEADER_NAME = "token"

# -----------------------------------------------------------------------------
# 加密配置（SM2 + SM4 混合）
# -----------------------------------------------------------------------------

# SM2 公钥（HEX），可带或不带 04 前缀。务必确认与对方系统一致（常见：04 + X + Y）
# 示例（仅示意，长度不对）：SM2_PUBLIC_KEY="04abcd..."
SM2_PUBLIC_KEY = "04" + "b40e6e436223fb6c2460e9c00b60d724bf03944f8cf379df6cdbdfe07253ede0073dae5428927cc04312f9aadfb19eb36b1820947f19ee590890fad5b428c4b2"

# SM2 密文拼接模式：常见 C1C3C2（也有对方系统使用 C1C2C3）
SM2_CIPHER_MODE = "C1C3C2"

# SM4 模式：目前项目实现主要按 ECB 走（对齐常见 Java 实现）
SM4_MODE = "ECB"

# SM4 填充：目前项目实现对齐 PKCS5（gmssl 内部处理）
SM4_PADDING = "PKCS5"

# 密文编码：HEX / BASE64（当前项目默认 HEX，和 Java demo 常用一致）
CIPHER_ENCODING = "HEX"

# 传递“SM2 公钥加密后的 SM4 key”的 header 名（对方术语：secret）
# 示例：ENCRYPT_KEY_HEADER_NAME="secret"
ENCRYPT_KEY_HEADER_NAME = "secret"


# -----------------------------------------------------------------------------
# 请求/响应字段配置（非常关键：必须与对方 JSON 字段名一致）
# -----------------------------------------------------------------------------

# 请求体中承载“加密后的业务报文”的字段名
# 示例：REQUEST_DATA_FIELD_NAME="data"
REQUEST_DATA_FIELD_NAME = "data"

# 响应体中承载“加密后的业务报文”的字段名
# 示例：RESPONSE_DATA_FIELD_NAME="data"
RESPONSE_DATA_FIELD_NAME = "data"

# 响应码字段名
# 示例：RESPONSE_CODE_FIELD_NAME="code"
RESPONSE_CODE_FIELD_NAME = "code"

# 响应消息字段名
# 示例：RESPONSE_MSG_FIELD_NAME="msg"
RESPONSE_MSG_FIELD_NAME = "msg"

# 业务成功码的值（注意类型：脚本里会按字符串比较）
# 示例：SUCCESS_CODE_VALUE="200"
SUCCESS_CODE_VALUE = "200"


# -----------------------------------------------------------------------------
# 其他请求头（可选）
# -----------------------------------------------------------------------------

# 你可以在这里补充对方要求的额外 headers（如 appId、tenantId、版本号等）
# 示例：EXTRA_HEADERS={"X-App-Id": "demo", "X-Req-From": "dq-system"}
EXTRA_HEADERS = {
    # "X-App-Id": "REPLACE_ME",
}


# -----------------------------------------------------------------------------
# 测试业务参数（明文 data）
# -----------------------------------------------------------------------------

# 这里填写“业务明文参数”，脚本会 JSON dumps 为字符串后加密。
# 你也可以直接写一个 JSON 字符串（PLAIN_DATA 为 str），脚本会原样使用。
PLAIN_DATA = {
        "deptCode": "11371000MB2856435T",
	"regionCode": "371000000000",
	"regionLevel": "1",
	"startTime": "2026-01-01 00:00:00",
	"endTime": "2026-02-01 00:00:00",
	"page": "0",
}

