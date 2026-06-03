<template>
  <div>
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="query">
          <el-form-item label="接口编码">
            <el-input v-model="query.interfaceCode" />
          </el-form-item>
          <el-form-item label="接口名称">
            <el-input v-model="query.interfaceName" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadData">查询</el-button>
            <el-button @click="onReset">重置</el-button>
          </el-form-item>
        </el-form>
        <el-button type="primary" @click="onCreate">新增接口</el-button>
      </div>
      <el-table :data="list" style="width: 100%" v-loading="loading">
        <el-table-column prop="interfaceCode" label="接口编码" />
        <el-table-column prop="interfaceName" label="接口名称" />
        <el-table-column prop="envCode" label="环境" />
        <el-table-column prop="baseUrl" label="地址" />
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag type="success" v-if="scope.row.status === 1">启用</el-tag>
            <el-tag type="info" v-else>停用</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260">
          <template #default="scope">
            <el-button size="small" @click="onEdit(scope.row)">编辑</el-button>
            <el-button size="small" @click="onParams(scope.row)">参数模板</el-button>
            <el-button size="small" @click="onResultConfig(scope.row)">结果配置</el-button>
            <el-button size="small" @click="onTest(scope.row)">测试</el-button>
            <el-button size="small" type="danger" @click="onDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination">
        <el-pagination
          background
          layout="prev, pager, next, total"
          :total="total"
          :page-size="query.pageSize"
          :current-page="query.page"
          @current-change="onPageChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" title="接口配置" width="900px">
      <el-form :model="form" label-width="140px">
        <el-form-item label="接口编码">
          <el-input v-model="form.interfaceCode" />
        </el-form-item>
        <el-form-item label="接口名称">
          <el-input v-model="form.interfaceName" />
        </el-form-item>
        <el-form-item label="环境">
          <el-input v-model="form.envCode" />
        </el-form-item>
        <el-form-item label="基础地址">
          <el-input v-model="form.baseUrl" />
        </el-form-item>
        <el-form-item label="请求路径">
          <el-input v-model="form.requestPath" />
        </el-form-item>
        <el-form-item label="方法">
          <el-select v-model="form.requestMethod">
            <el-option label="POST" value="POST" />
            <el-option label="GET" value="GET" />
          </el-select>
        </el-form-item>
        <el-form-item label="超时(ms)">
          <el-input-number v-model="form.timeoutMs" :min="1000" :max="300000" :step="1000" style="width: 240px" />
          <div class="hint">建议：小查询 10000；大列表可按需调大（例如 30000/60000）。</div>
        </el-form-item>
        <el-divider content-position="left">鉴权与请求字段</el-divider>
        <el-form-item label="token header 名">
          <el-input v-model="form.tokenHeaderName" placeholder="例如：token" />
        </el-form-item>
        <el-form-item label="token 值（可留空不改）">
          <el-input v-model="form.tokenValueInput" type="password" show-password placeholder="编辑时留空表示不修改；新建请填写" />
          <div class="hint" v-if="form.tokenMasked">当前：{{ form.tokenMasked }}</div>
        </el-form-item>
        <el-form-item label="secret header 名">
          <el-input v-model="form.encryptKeyHeaderName" placeholder="例如：secret" />
        </el-form-item>
        <el-form-item label="请求 data 字段名">
          <el-input v-model="form.requestDataFieldName" placeholder="例如：data" />
        </el-form-item>
        <el-form-item label="响应 data 字段名">
          <el-input v-model="form.responseDataFieldName" placeholder="例如：data" />
        </el-form-item>
        <el-form-item label="响应 code 字段名">
          <el-input v-model="form.responseCodeFieldName" placeholder="例如：code" />
        </el-form-item>
        <el-form-item label="响应 msg 字段名">
          <el-input v-model="form.responseMsgFieldName" placeholder="例如：msg" />
        </el-form-item>
        <el-form-item label="成功码">
          <el-input v-model="form.successCodeValue" placeholder="例如：200" />
        </el-form-item>
        <el-divider content-position="left">国密配置</el-divider>
        <el-form-item label="SM2 公钥">
          <el-input v-model="form.sm2PublicKey" type="textarea" :rows="3" placeholder="HEX，可带或不带 04" />
        </el-form-item>
        <el-form-item label="SM2 模式">
          <el-select v-model="form.sm2CipherMode" placeholder="C1C3C2">
            <el-option label="C1C3C2" value="C1C3C2" />
            <el-option label="C1C2C3" value="C1C2C3" />
          </el-select>
        </el-form-item>
        <el-form-item label="SM4 模式">
          <el-select v-model="form.sm4Mode" placeholder="ECB">
            <el-option label="ECB" value="ECB" />
            <el-option label="CBC(未实现)" value="CBC" />
          </el-select>
        </el-form-item>
        <el-form-item label="SM4 padding">
          <el-select v-model="form.sm4Padding" placeholder="PKCS5">
            <el-option label="PKCS5" value="PKCS5" />
            <el-option label="PKCS7" value="PKCS7" />
            <el-option label="NoPadding" value="NoPadding" />
          </el-select>
        </el-form-item>
        <el-form-item label="密文编码">
          <el-select v-model="form.cipherEncoding" placeholder="HEX">
            <el-option label="HEX" value="HEX" />
            <el-option label="BASE64" value="BASE64" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="resultConfigVisible" title="结果展示配置（JSON）" width="900px">
      <el-alert
        type="info"
        title="保存后影响：解析路径、查询工作台表格列/详情分组、自动统计（分组/趋势/TopN）、开放 API 返回结构。可参考 backend/scripts/init_result_configs.py。"
        show-icon
        style="margin-bottom: 12px"
      />
      <el-input
        v-model="resultConfigText"
        type="textarea"
        :rows="18"
        placeholder='{"result_mode":"list","listPath":"data.data","totalPath":"data.total","columns":[{"field":"id","label":"编号"}],"stats":{"groupBy":[{"field":"dept","label":"部门"}],"timeTrend":{"field":"applydate","granularity":"day"},"topN":[{"field":"name","n":5}]}}'
      />
      <template #footer>
        <el-button @click="resultConfigVisible = false">取消</el-button>
        <el-button type="primary" @click="onSaveResultConfig" :loading="savingResultConfig">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { listInterfaces, createInterface, updateInterface, deleteInterface, testInterface, getInterfaceDetail, getResultConfig, updateResultConfig } from "@/api/interfaces";

const router = useRouter();

const query = reactive({
  page: 1,
  pageSize: 10,
  interfaceCode: "",
  interfaceName: ""
});

const list = ref<any[]>([]);
const total = ref(0);
const loading = ref(false);
const saving = ref(false);

const dialogVisible = ref(false);
const editingId = ref<number | null>(null);
const resultConfigVisible = ref(false);
const savingResultConfig = ref(false);
const editingResultConfigId = ref<number | null>(null);
const resultConfigText = ref<string>("");
const form = reactive<any>({
  interfaceCode: "",
  interfaceName: "",
  envCode: "prod",
  baseUrl: "",
  requestPath: "",
  requestMethod: "POST",
  timeoutMs: 10000,
  tokenHeaderName: "token",
  tokenMasked: "",
  tokenValueInput: "",
  encryptKeyHeaderName: "secret",
  requestDataFieldName: "data",
  responseDataFieldName: "data",
  responseCodeFieldName: "code",
  responseMsgFieldName: "msg",
  successCodeValue: "200",
  sm2PublicKey: "",
  sm2CipherMode: "C1C3C2",
  sm4Mode: "ECB",
  sm4Padding: "PKCS5",
  cipherEncoding: "HEX"
});

async function loadData() {
  loading.value = true;
  try {
    const res = await listInterfaces(query);
    list.value = res.list || [];
    total.value = res.total || 0;
  } finally {
    loading.value = false;
  }
}

function onReset() {
  query.interfaceCode = "";
  query.interfaceName = "";
  query.page = 1;
  loadData();
}

function onPageChange(p: number) {
  query.page = p;
  loadData();
}

function onCreate() {
  editingId.value = null;
  Object.assign(form, {
    interfaceCode: "",
    interfaceName: "",
    envCode: "prod",
    baseUrl: "",
    requestPath: "",
    requestMethod: "POST",
    timeoutMs: 10000,
    tokenHeaderName: "token",
    tokenMasked: "",
    tokenValueInput: "",
    encryptKeyHeaderName: "secret",
    requestDataFieldName: "data",
    responseDataFieldName: "data",
    responseCodeFieldName: "code",
    responseMsgFieldName: "msg",
    successCodeValue: "200",
    sm2PublicKey: "",
    sm2CipherMode: "C1C3C2",
    sm4Mode: "ECB",
    sm4Padding: "PKCS5",
    cipherEncoding: "HEX"
  });
  dialogVisible.value = true;
}

async function onEdit(row: any) {
  editingId.value = row.id;
  const detail = await getInterfaceDetail(row.id);
  Object.assign(form, detail);
  form.tokenValueInput = "";
  dialogVisible.value = true;
}

async function onSave() {
  try {
    saving.value = true;
    const payload: any = { ...form };
    // tokenValueInput 非空才提交 tokenValue，避免覆盖旧 token
    if (payload.tokenValueInput && String(payload.tokenValueInput).trim() !== "") {
      payload.tokenValue = payload.tokenValueInput;
    }
    delete payload.tokenValueInput;
    delete payload.tokenMasked;
    if (editingId.value) {
      await updateInterface(editingId.value, payload);
    } else {
      await createInterface(payload);
    }
    ElMessage.success("保存成功");
    dialogVisible.value = false;
    loadData();
  } catch (e: any) {
    ElMessage.error(e?.message || "保存失败");
  } finally {
    saving.value = false;
  }
}

async function onDelete(row: any) {
  await ElMessageBox.confirm("确认删除该接口？", "提示", { type: "warning" });
  await deleteInterface(row.id);
  ElMessage.success("删除成功");
  loadData();
}

async function onTest(row: any) {
  const res = await testInterface(row.id);
  if (res.ok) {
    ElMessage.success(`连通成功，状态码：${res.statusCode}`);
  } else {
    ElMessage.error(`连通失败：${res.error || res.statusCode}`);
  }
}

function onParams(row: any) {
  router.push({ name: "interface-params", params: { id: row.id } });
}

async function onResultConfig(row: any) {
  editingResultConfigId.value = row.id;
  try {
    const res: any = await getResultConfig(row.id);
    const cfg = res?.resultConfig ?? res?.data?.resultConfig ?? res;
    resultConfigText.value = typeof cfg === "string" ? cfg : JSON.stringify(cfg || {}, null, 2);
    resultConfigVisible.value = true;
  } catch (e: any) {
    ElMessage.error(e?.message || "加载结果配置失败");
  }
}

async function onSaveResultConfig() {
  if (!editingResultConfigId.value) return;
  try {
    savingResultConfig.value = true;
    // 支持直接粘贴 JSON
    let cfg: any = resultConfigText.value;
    try {
      cfg = JSON.parse(resultConfigText.value);
    } catch {
      // 允许保存字符串（后端也会存）
      cfg = resultConfigText.value;
    }
    await updateResultConfig(editingResultConfigId.value, cfg);
    ElMessage.success("保存成功");
    resultConfigVisible.value = false;
  } catch (e: any) {
    ElMessage.error(e?.message || "保存失败");
  } finally {
    savingResultConfig.value = false;
  }
}

onMounted(loadData);
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}
.pagination {
  margin-top: 12px;
  text-align: right;
}
.hint {
  margin-top: 4px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
</style>

