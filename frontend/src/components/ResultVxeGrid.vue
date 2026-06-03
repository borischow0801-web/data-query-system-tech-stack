<template>
  <div class="grid-wrap">
    <div class="toolbar">
      <el-input
        v-model="quickFilter"
        clearable
        placeholder="快速筛选（匹配任意列文本）"
        style="width: 240px"
        size="small"
      />
      <el-checkbox-group v-model="visibleFields" size="small" class="col-toggle">
        <el-checkbox v-for="c in columnDefs" :key="c.field" :label="c.field">{{ c.label }}</el-checkbox>
      </el-checkbox-group>
      <div class="tb-actions">
        <el-button size="small" type="primary" plain @click="exportAll">导出全部行(CSV)</el-button>
        <el-button size="small" @click="exportVisible">导出筛选后(CSV)</el-button>
      </div>
    </div>
    <vxe-table
      ref="tableRef"
      :data="filteredRows"
      border
      stripe
      size="small"
      height="480"
      show-overflow="tooltip"
      show-header-overflow="tooltip"
      :column-config="{ resizable: true }"
      :sort-config="{ multiple: true, trigger: 'cell' }"
      :row-config="{ isHover: true }"
      class="dq-vxe"
    >
      <vxe-column type="seq" width="52" fixed="left" title="#" />
      <vxe-column
        v-for="c in activeColumns"
        :key="c.field"
        :field="c.field"
        :title="c.label"
        :width="c.width"
        :min-width="c.minWidth || 110"
        sortable
      />
    </vxe-table>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { exportCsv } from "@/utils/csvExport";

const props = defineProps<{
  rows: Record<string, unknown>[];
  columnDefs: { field: string; label: string; width?: number; minWidth?: number; visible?: boolean }[];
  exportBasename?: string;
}>();

const tableRef = ref();
const quickFilter = ref("");

const columnDefs = computed(() =>
  (props.columnDefs || []).filter((c) => c.field && (c.visible !== false))
);

const visibleFields = ref<string[]>([]);

watch(
  () => columnDefs.value.map((c) => c.field),
  (fields) => {
    if (!visibleFields.value.length) visibleFields.value = [...fields];
    else visibleFields.value = visibleFields.value.filter((f) => fields.includes(f));
    if (!visibleFields.value.length) visibleFields.value = [...fields];
  },
  { immediate: true }
);

const activeColumns = computed(() => columnDefs.value.filter((c) => visibleFields.value.includes(c.field)));

const filteredRows = computed(() => {
  const q = quickFilter.value.trim().toLowerCase();
  const r = (props.rows || []) as Record<string, unknown>[];
  if (!q) return r;
  return r.filter((row) =>
    activeColumns.value.some((c) => String(row[c.field] ?? "")
      .toLowerCase()
      .includes(q))
  );
});

function exportAll() {
  exportCsv(props.rows as Record<string, unknown>[], activeColumns.value, props.exportBasename || "query-result");
}

function exportVisible() {
  exportCsv(filteredRows.value as Record<string, unknown>[], activeColumns.value, (props.exportBasename || "query-result") + "-filtered");
}
</script>

<style scoped>
.grid-wrap {
  width: 100%;
}
.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}
.col-toggle {
  flex: 1;
  min-width: 200px;
}
.tb-actions {
  flex-shrink: 0;
  display: flex;
  gap: 8px;
}
.dq-vxe {
  border-radius: 4px;
}
</style>
