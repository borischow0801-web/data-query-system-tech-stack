<template>
  <div class="dq-workspace">
    <div class="page-head">
      <div>
        <h2 class="title">查询工作台</h2>
        <p class="sub">面向运维与分析：选择接口、填写条件后查看表格、统计与导出；底层加解密由平台完成。</p>
      </div>
      <div class="head-meta" v-if="lastMeta.traceId">
        <el-tag size="small" type="info">traceId: {{ lastMeta.traceId }}</el-tag>
        <el-tag size="small" v-if="lastMeta.durationMs != null">耗时 {{ lastMeta.durationMs }} ms</el-tag>
        <el-tag size="small" :type="lastMeta.success ? 'success' : 'danger'">{{ lastMeta.success ? "成功" : "失败" }}</el-tag>
      </div>
    </div>

    <el-card class="block-card" shadow="never">
      <template #header>
        <span class="card-title">查询条件</span>
      </template>
      <el-form :inline="true" :model="form">
        <el-form-item label="接口">
          <el-select v-model="form.interfaceId" placeholder="选择接口" filterable style="width: 320px" @change="onInterfaceChange">
            <el-option v-for="i in interfaces" :key="i.id" :label="`${i.interfaceCode} — ${i.interfaceName}`" :value="i.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadSchema" :disabled="!form.interfaceId" :loading="loadingSchema">加载参数模板</el-button>
        </el-form-item>
      </el-form>

      <dynamic-query-form v-if="schema" :schema="schema" @submit="onExecute" :loading="executing" />
    </el-card>

    <el-card v-if="errorMessage" class="block-card" shadow="never">
      <el-alert type="error" :title="errorMessage" show-icon :closable="false" />
    </el-card>

    <template v-if="dataBlock && !errorMessage">
      <el-card v-if="(dataBlock.hints || []).length" class="block-card" shadow="never">
        <el-alert
          type="warning"
          title="范围/参数风险提示"
          show-icon
          :closable="false"
        >
          <ul class="hint-list">
            <li v-for="(h, idx) in dataBlock.hints" :key="idx">{{ h }}</li>
          </ul>
        </el-alert>
      </el-card>
      <el-card class="block-card result-card" shadow="never">
        <template #header>
          <div class="result-header">
            <span class="card-title">查询结果</span>
            <div class="result-actions" v-if="lastMeta.queryRecordId">
              <el-button size="small" type="primary" @click="onServerExport('csv')" :loading="exporting">服务端导出 CSV</el-button>
              <el-button size="small" @click="onServerExport('xlsx')" :loading="exporting">服务端导出 Excel</el-button>
            </div>
          </div>
        </template>

        <analysis-panel v-if="dataBlock.analysis" :analysis="dataBlock.analysis" />

        <div v-if="isDetailView" class="detail-wrap">
          <detail-section-panel :sections="dataBlock.display?.detailSections || []" />
        </div>

        <div v-if="showTable" class="table-wrap">
          <result-vxe-grid
            :rows="tableRows"
            :column-defs="tableColumns"
            :export-basename="exportBaseName"
          />
          <div class="pager" v-if="showPager">
            <el-pagination
              background
              layout="prev, pager, next, total"
              :total="dataBlock.total || 0"
              :page-size="dataBlock.pageSize || pageSize"
              :current-page="page"
              @current-change="onPageChange"
            />
          </div>
        </div>

        <el-row :gutter="16" class="aux-row">
          <el-col :span="24">
            <el-collapse>
              <el-collapse-item title="解密后 JSON（辅助）" name="plain">
                <json-viewer :value="dataBlock.rawData ?? dataBlock" />
              </el-collapse-item>
              <el-collapse-item title="原始响应 JSON（辅助）" name="raw">
                <json-viewer :value="rawResult" />
              </el-collapse-item>
            </el-collapse>
          </el-col>
        </el-row>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import DynamicQueryForm from "@/components/DynamicQueryForm.vue";
import JsonViewer from "@/components/JsonViewer.vue";
import ResultVxeGrid from "@/components/ResultVxeGrid.vue";
import AnalysisPanel from "@/components/AnalysisPanel.vue";
import DetailSectionPanel from "@/components/DetailSectionPanel.vue";
import { listInterfaces } from "@/api/interfaces";
import { getQueryFormSchema } from "@/api/params";
import { executeQuery } from "@/api/query";
import { createExportTask } from "@/api/export";

const interfaces = ref<any[]>([]);
const schema = ref<any | null>(null);
const dataBlock = ref<any | null>(null);
const rawResult = ref<any | null>(null);
const errorMessage = ref<string>("");
const loadingSchema = ref(false);
const executing = ref(false);
const exporting = ref(false);
const page = ref(1);
const pageSize = ref(20);

const lastMeta = reactive({
  traceId: "" as string,
  durationMs: null as number | null,
  success: true,
  queryRecordId: null as number | null
});

const form = reactive({
  interfaceId: null as number | null
});

const isDetailView = computed(() => {
  const m = dataBlock.value?.display?.resultMode;
  return m === "detail" || m === "mixed";
});

const showTable = computed(() => {
  const m = dataBlock.value?.display?.resultMode || "list";
  if (m === "detail") return Array.isArray(dataBlock.value?.list) && dataBlock.value.list.length > 0;
  if (m === "mixed") return true;
  return true;
});

const tableRows = computed(() => {
  const list = dataBlock.value?.list || [];
  if (!Array.isArray(list)) return [];
  const ps = dataBlock.value?.pageSize || pageSize.value;
  const p = page.value;
  if (dataBlock.value?.page && dataBlock.value?.pageSize && dataBlock.value?.total != null) return list;
  return list.slice((p - 1) * ps, p * ps);
});

const showPager = computed(() => {
  const list = dataBlock.value?.list || [];
  if (!Array.isArray(list)) return false;
  if (dataBlock.value?.page && dataBlock.value?.pageSize && dataBlock.value?.total != null) return false;
  return list.length > (dataBlock.value?.pageSize || pageSize.value);
});

const tableColumns = computed(() => {
  const cols = dataBlock.value?.display?.columns;
  if (cols && cols.length) return cols;
  const first = tableRows.value[0];
  if (first && typeof first === "object")
    return Object.keys(first).map((k, i) => ({ field: k, label: k, sortNo: i, visible: true }));
  return [];
});

const exportBaseName = computed(() => {
  const iface = interfaces.value.find((i) => i.id === form.interfaceId);
  return iface ? `query-${iface.interfaceCode}` : "query-result";
});

async function loadInterfaces() {
  const res = await listInterfaces({ page: 1, pageSize: 200 });
  interfaces.value = res.list || [];
}

async function loadSchema() {
  if (!form.interfaceId) return;
  loadingSchema.value = true;
  try {
    schema.value = await getQueryFormSchema(form.interfaceId);
  } catch (e: any) {
    ElMessage.error(e?.message || "加载参数模板失败");
  } finally {
    loadingSchema.value = false;
  }
}

function onInterfaceChange() {
  schema.value = null;
  dataBlock.value = null;
  rawResult.value = null;
  errorMessage.value = "";
  page.value = 1;
  lastMeta.traceId = "";
  lastMeta.durationMs = null;
  lastMeta.success = true;
  lastMeta.queryRecordId = null;
}

async function onExecute(params: any) {
  const iface = interfaces.value.find((i) => i.id === form.interfaceId);
  if (!iface) {
    ElMessage.error("请选择接口");
    return;
  }
  executing.value = true;
  errorMessage.value = "";
  page.value = 1;
  try {
    // 仅做“风险提示”，不拦截（后端会按接口规则做严格校验）
    if (params) {
      const rl = params.regionLevel != null ? String(params.regionLevel).trim() : "";
      const pg = params.page != null ? String(params.page).trim() : "";
      if (iface.interfaceCode === "getBusinessListByDeptOrRegion") {
        if (rl === "1") ElMessage.warning("regionLevel=1 范围更大，远端接口可能响应较慢。");
        if (pg === "0") ElMessage.info("page=0：start/limit 可为空（按接口规则）。");
      }
    }
    const payload = {
      interfaceCode: iface.interfaceCode,
      params,
      envCode: iface.envCode || "prod"
    };
    const res: any = await executeQuery(payload);
    if (res && res.success === false) {
      // 失败提示尽量可定位（remote_timeout_xxx / validation_failed 等）
      const code = res.code;
      const msg = res.message || "查询失败";
      if (code === "REMOTE_TIMEOUT_READ") {
        errorMessage.value = `远端读取超时（remote_timeout_read）：${msg}`;
      } else if (code === "REMOTE_TIMEOUT_CONNECT") {
        errorMessage.value = `远端连接超时（remote_timeout_connect）：${msg}`;
      } else if (code === "REMOTE_PROXY_CONFIG") {
        errorMessage.value = `代理配置异常（请取消系统 SOCKS 代理或安装 httpx[socks]）：${msg}`;
      } else if (code === "400") {
        errorMessage.value = `参数校验失败：${msg}`;
      } else {
        errorMessage.value = code ? `${code}: ${msg}` : msg;
      }
      dataBlock.value = null;
      rawResult.value = null;
      return;
    }
    lastMeta.traceId = res.traceId || "";
    lastMeta.durationMs = res.durationMs ?? null;
    lastMeta.success = res.success !== false;
    lastMeta.queryRecordId = res.queryRecordId ?? null;
    dataBlock.value = res.data ?? null;
    rawResult.value = res.rawData ?? null;
    ElMessage.success("查询完成");
  } catch (e: any) {
    const code = e?.code || e?.response?.data?.code;
    const msg = e?.message || e?.response?.data?.message || "查询失败";
    if (code === "REMOTE_TIMEOUT_READ") {
      errorMessage.value = `远程读取超时：${msg}。建议缩小范围/增加分页(limit)/调整该接口 timeoutMs。`;
    } else if (code === "REMOTE_TIMEOUT_CONNECT") {
      errorMessage.value = `远程连接超时：${msg}。请检查网络、DNS、对方服务可用性。`;
    } else {
      errorMessage.value = msg;
    }
    dataBlock.value = null;
  } finally {
    executing.value = false;
  }
}

function onPageChange(p: number) {
  page.value = p;
}

async function onServerExport(t: "csv" | "xlsx") {
  if (!lastMeta.queryRecordId) {
    ElMessage.warning("无 queryRecordId，请先成功执行查询");
    return;
  }
  exporting.value = true;
  try {
    const r: any = await createExportTask({ queryRecordId: lastMeta.queryRecordId, exportType: t });
    const url = r?.fileUrl || r?.data?.fileUrl;
    if (url) {
      ElMessage.success("导出完成，正在下载");
      window.open(url, "_blank");
    } else {
      ElMessage.success("导出任务已创建");
    }
  } catch (e: any) {
    ElMessage.error(e?.message || "导出失败");
  } finally {
    exporting.value = false;
  }
}

onMounted(loadInterfaces);
</script>

<style scoped>
.dq-workspace {
  max-width: 1600px;
  margin: 0 auto;
}
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
}
.title {
  margin: 0 0 6px;
  font-size: 20px;
  font-weight: 600;
  color: var(--dq-text, #1f2937);
}
.sub {
  margin: 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  max-width: 720px;
  line-height: 1.5;
}
.head-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}
.block-card {
  border-radius: 8px;
  margin-bottom: 16px;
}
.result-card {
  border: 1px solid var(--el-border-color-lighter);
}
.card-title {
  font-weight: 600;
  font-size: 15px;
}
.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.result-actions {
  display: flex;
  gap: 8px;
}
.detail-wrap {
  margin-bottom: 16px;
}
.table-wrap {
  margin-bottom: 16px;
}
.pager {
  margin-top: 12px;
  text-align: right;
}
.aux-row {
  margin-top: 8px;
}
.hint-list {
  margin: 8px 0 0;
  padding-left: 18px;
  line-height: 1.6;
}
</style>
