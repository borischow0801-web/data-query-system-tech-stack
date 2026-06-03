<template>
  <div class="dq-history">
    <div class="page-head">
      <h2 class="title">查询历史</h2>
      <p class="sub">按 trace、接口筛选；详情中可结构化回放列表/统计（基于已保存的解密结果）。</p>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query">
        <el-form-item label="接口编码">
          <el-input v-model="query.interfaceCode" clearable placeholder="模糊留空即全部" style="width: 200px" />
        </el-form-item>
        <el-form-item label="结果">
          <el-select v-model="query.successFlag" clearable placeholder="全部" style="width: 120px">
            <el-option label="成功" :value="1" />
            <el-option label="失败" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="list" v-loading="loading" border stripe style="width: 100%" class="hist-table">
        <el-table-column prop="traceId" label="traceId" min-width="160" show-overflow-tooltip />
        <el-table-column prop="interfaceCode" label="接口编码" width="160" show-overflow-tooltip />
        <el-table-column prop="interfaceName" label="接口名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="triggerType" label="来源" width="100" />
        <el-table-column prop="successFlag" label="结果" width="88">
          <template #default="scope">
            <el-tag type="success" v-if="scope.row.successFlag === 1">成功</el-tag>
            <el-tag type="danger" v-else>失败</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="responseCode" label="外部码" width="90" />
        <el-table-column prop="durationMs" label="耗时(ms)" width="100" />
        <el-table-column prop="createdAt" label="时间" width="170" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" link @click="onDetail(scope.row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="total"
          :page-size="query.pageSize"
          :current-page="query.page"
          @current-change="onPageChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="detailVisible" title="查询详情" width="960px" top="4vh" class="detail-dlg" destroy-on-close>
      <template v-if="detail">
        <el-tabs v-model="detailTab">
          <el-tab-pane label="运行摘要" name="meta">
            <el-alert
              v-if="detail.successFlag === 0 && detail.errorMessage"
              type="error"
              :title="detail.errorMessage"
              show-icon
              style="margin-bottom: 12px"
            />
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="traceId" :span="2">{{ detail.traceId }}</el-descriptions-item>
              <el-descriptions-item label="接口编码">{{ detail.interfaceCode }}</el-descriptions-item>
              <el-descriptions-item label="结果">
                <el-tag :type="detail.successFlag === 1 ? 'success' : 'danger'">{{ detail.successFlag === 1 ? "成功" : "失败" }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="响应码">{{ detail.responseCode ?? "—" }}</el-descriptions-item>
              <el-descriptions-item label="响应消息">{{ detail.responseMessage ?? "—" }}</el-descriptions-item>
              <el-descriptions-item label="耗时(ms)">{{ detail.durationMs ?? "—" }}</el-descriptions-item>
              <el-descriptions-item label="时间">{{ detail.createdAt }}</el-descriptions-item>
            </el-descriptions>
            <div class="dlg-actions" v-if="detail.successFlag === 1 && detail.id">
              <el-button size="small" type="primary" @click="exportFromHistory('csv')" :loading="exporting">导出 CSV</el-button>
              <el-button size="small" @click="exportFromHistory('xlsx')" :loading="exporting">导出 Excel</el-button>
            </div>
          </el-tab-pane>

          <el-tab-pane label="结构化回放" name="struct" :disabled="detail.successFlag !== 1">
            <div v-loading="structLoading">
              <template v-if="structView">
                <analysis-panel v-if="structView.analysis" :analysis="structView.analysis" />
                <div v-if="structView.resultMode === 'detail' || structView.resultMode === 'mixed'">
                  <detail-section-panel :sections="structView.display?.detailSections || []" />
                </div>
                <div
                  v-if="
                    structView.list?.length &&
                    (structView.resultMode === 'list' || structView.resultMode === 'mixed')
                  "
                  class="struct-table"
                >
                  <result-vxe-grid
                    :rows="structView.list"
                    :column-defs="structView.display?.columns || []"
                    :export-basename="`history-${detail.interfaceCode}`"
                  />
                </div>
                <el-empty
                  v-if="structView.resultMode === 'list' && !structView.list?.length"
                  description="列表为空"
                />
              </template>
              <el-empty v-else-if="!structLoading && detail.successFlag === 1" description="点击本标签已自动加载结构化视图" />
            </div>
          </el-tab-pane>

          <el-tab-pane label="报文与调试" name="raw">
            <el-divider content-position="left">请求明文</el-divider>
            <pre class="detail-block">{{ detail.requestPlain ?? "—" }}</pre>
            <el-divider content-position="left">响应原文（预览）</el-divider>
            <pre class="detail-block">{{ detail.responseRawPreview ?? detail.responseRaw ?? "—" }}</pre>
            <div class="meta" v-if="detail.responseRawSize || detail.payloadStoreMode">
              size={{ detail.responseRawSize ?? "—" }} bytes, store={{ detail.payloadStoreMode ?? "—" }}
            </div>
            <el-divider content-position="left">解密结果（预览）</el-divider>
            <pre class="detail-block">{{ detail.responsePlainPreview ?? detail.responsePlain ?? "—" }}</pre>
            <div class="actions">
              <el-button size="small" @click="loadFullPayload('response_raw')" :disabled="loadingPayload">完整原始响应</el-button>
              <el-button size="small" @click="loadFullPayload('response_plain')" :disabled="loadingPayload">完整解密结果</el-button>
            </div>
          </el-tab-pane>
        </el-tabs>
      </template>
    </el-dialog>

    <el-dialog v-model="fullVisible" :title="fullTitle" width="900px">
      <pre class="detail-block tall">{{ fullText }}</pre>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, watch, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { listQueryHistory, getQueryHistoryDetail, getQueryHistoryStructuredView } from "@/api/query";
import { createExportTask } from "@/api/export";
import AnalysisPanel from "@/components/AnalysisPanel.vue";
import DetailSectionPanel from "@/components/DetailSectionPanel.vue";
import ResultVxeGrid from "@/components/ResultVxeGrid.vue";

const query = reactive<any>({
  page: 1,
  pageSize: 10,
  interfaceCode: "",
  successFlag: null
});

const list = ref<any[]>([]);
const total = ref(0);
const loading = ref(false);

const detailVisible = ref(false);
const detail = ref<any | null>(null);
const detailTab = ref("meta");
const structView = ref<any | null>(null);
const structLoading = ref(false);
const loadingPayload = ref(false);
const exporting = ref(false);
const fullVisible = ref(false);
const fullText = ref<string>("");
const fullTitle = ref<string>("");

async function loadData() {
  loading.value = true;
  try {
    const params: any = { page: query.page, pageSize: query.pageSize };
    if (query.interfaceCode) params.interfaceCode = query.interfaceCode;
    if (query.successFlag !== null && query.successFlag !== undefined) params.successFlag = query.successFlag;
    const res = await listQueryHistory(params);
    list.value = res.list || [];
    total.value = res.total || 0;
  } finally {
    loading.value = false;
  }
}

async function onDetail(row: any) {
  detailTab.value = "meta";
  structView.value = null;
  const res: any = await getQueryHistoryDetail(row.id);
  detail.value = res?.traceId != null ? res : res?.data ?? res;
  detailVisible.value = true;
}

async function loadStruct() {
  if (!detail.value?.id || detail.value.successFlag !== 1) return;
  structLoading.value = true;
  try {
    const res: any = await getQueryHistoryStructuredView(detail.value.id);
    structView.value = res?.recordId != null ? res : res?.data ?? res;
  } catch (e: any) {
    const code = e?.code || e?.response?.data?.code;
    const msg = e?.message || e?.response?.data?.message || "结构化回放加载失败";
    ElMessage.error(code ? `${code}: ${msg}` : msg);
  } finally {
    structLoading.value = false;
  }
}

watch(detailTab, (t) => {
  if (t === "struct" && detail.value?.id && !structView.value) loadStruct();
});

async function loadFullPayload(kind: string) {
  if (!detail.value?.id) return;
  loadingPayload.value = true;
  try {
    const raw = ((import.meta as any).env?.VITE_API_BASE_URL as string | undefined)?.trim() || "";
    const url = raw
      ? `${raw.replace(/\/$/, "")}/api/query/history/${detail.value.id}/payload?kind=${kind}`
      : `/api/query/history/${detail.value.id}/payload?kind=${kind}`;
    const resp = await fetch(url, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token") || ""}` }
    });
    const json = await resp.json();
    const text = json?.data?.text ?? "";
    fullText.value = text || "(空)";
    fullTitle.value = `完整内容：${kind}`;
    fullVisible.value = true;
  } catch (e: any) {
    fullText.value = e?.message || "加载失败";
    fullTitle.value = `完整内容：${kind}`;
    fullVisible.value = true;
  } finally {
    loadingPayload.value = false;
  }
}

async function exportFromHistory(t: "csv" | "xlsx") {
  if (!detail.value?.id) return;
  exporting.value = true;
  try {
    const r: any = await createExportTask({ queryRecordId: detail.value.id, exportType: t });
    const url = r?.fileUrl || r?.data?.fileUrl;
    if (url) window.open(url, "_blank");
    ElMessage.success("导出完成");
  } catch (e: any) {
    ElMessage.error(e?.message || "导出失败");
  } finally {
    exporting.value = false;
  }
}

function onPageChange(p: number) {
  query.page = p;
  loadData();
}

onMounted(loadData);
</script>

<style scoped>
.dq-history {
  max-width: 1400px;
  margin: 0 auto;
}
.page-head {
  margin-bottom: 16px;
}
.title {
  margin: 0 0 6px;
  font-size: 20px;
  font-weight: 600;
}
.sub {
  margin: 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.filter-card {
  border-radius: 8px;
}
.hist-table {
  margin-top: 4px;
}
.pagination {
  margin-top: 12px;
  text-align: right;
}
.detail-block {
  margin: 0;
  padding: 8px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
  max-height: 200px;
  overflow: auto;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}
.detail-block.tall {
  max-height: 480px;
}
.meta {
  margin-top: 6px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
.actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}
.dlg-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}
.struct-table {
  margin-top: 12px;
}
</style>
