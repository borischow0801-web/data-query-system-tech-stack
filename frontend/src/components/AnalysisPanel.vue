<template>
  <div v-if="analysis && Object.keys(analysis).length" class="analysis-root">
    <el-row :gutter="12" class="cards-row">
      <el-col :xs="12" :sm="6" v-for="card in basicCards" :key="card.key">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-value" :class="card.tone">{{ card.value }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="charts-row" v-if="hasCharts">
      <el-col :xs="24" :lg="12" v-if="primaryGroup">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <span class="card-h">{{ primaryGroup.label }} — 分布</span>
          </template>
          <div ref="barRef" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12" v-if="analysis.timeTrend?.points?.length">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <span class="card-h">时间趋势（{{ analysis.timeTrend.granularity === "month" ? "月" : "日" }}）</span>
          </template>
          <div ref="lineRef" class="chart-box"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" v-if="analysis.topN?.length">
      <el-col :span="24">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <span class="card-h">Top 排名</span>
          </template>
          <div ref="topRef" class="chart-box tall"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts";

const props = defineProps<{
  analysis: any;
}>();

const barRef = ref<HTMLDivElement | null>(null);
const lineRef = ref<HTMLDivElement | null>(null);
const topRef = ref<HTMLDivElement | null>(null);
let chartBar: echarts.ECharts | null = null;
let chartLine: echarts.ECharts | null = null;
let chartTop: echarts.ECharts | null = null;

const basicCards = computed(() => {
  const b = props.analysis?.basic || {};
  const ok = b.success === true || b.success === 1;
  return [
    { key: "rows", label: "当前结果行数", value: b.currentPageRowCount ?? "—", tone: "" },
    { key: "total", label: "记录总数(接口)", value: b.totalCount ?? "—", tone: "" },
    { key: "dur", label: "查询耗时(ms)", value: b.durationMs ?? "—", tone: "" },
    { key: "ok", label: "状态", value: ok ? "成功" : "失败", tone: ok ? "ok" : "fail" }
  ];
});

const primaryGroup = computed(() => props.analysis?.groupBy?.[0]);

const hasCharts = computed(() => {
  const g = primaryGroup.value?.buckets?.length;
  const t = props.analysis?.timeTrend?.points?.length;
  return g || t;
});

function disposeAll() {
  chartBar?.dispose();
  chartLine?.dispose();
  chartTop?.dispose();
  chartBar = chartLine = chartTop = null;
}

function renderCharts() {
  disposeAll();
  const g = primaryGroup.value;
  if (g?.buckets?.length && barRef.value) {
    chartBar = echarts.init(barRef.value);
    chartBar.setOption({
      color: ["#5470c6"],
      tooltip: { trigger: "axis" },
      grid: { left: "3%", right: "4%", bottom: "12%", containLabel: true },
      xAxis: {
        type: "category",
        data: g.buckets.map((x: any) => x.value),
        axisLabel: { rotate: 30, interval: 0, fontSize: 11 }
      },
      yAxis: { type: "value", minInterval: 1 },
      series: [{ type: "bar", data: g.buckets.map((x: any) => x.count), barMaxWidth: 36 }]
    });
  }
  const tr = props.analysis?.timeTrend;
  if (tr?.points?.length && lineRef.value) {
    chartLine = echarts.init(lineRef.value);
    chartLine.setOption({
      tooltip: { trigger: "axis" },
      grid: { left: "3%", right: "4%", bottom: "10%", containLabel: true },
      xAxis: { type: "category", data: tr.points.map((p: any) => p.bucket) },
      yAxis: { type: "value", minInterval: 1 },
      series: [{ type: "line", smooth: true, data: tr.points.map((p: any) => p.count), areaStyle: { opacity: 0.08 } }]
    });
  }
  const tops = props.analysis?.topN;
  if (tops?.length && topRef.value) {
    chartTop = echarts.init(topRef.value);
    const t0 = tops[0];
    chartTop.setOption({
      tooltip: { trigger: "axis" },
      grid: { left: "3%", right: "8%", bottom: "8%", containLabel: true },
      xAxis: { type: "value", minInterval: 1 },
      yAxis: {
        type: "category",
        data: (t0.items || []).map((x: any) => x.value).reverse(),
        axisLabel: { width: 140, overflow: "truncate" }
      },
      series: [
        {
          type: "bar",
          data: (t0.items || []).map((x: any) => x.count).reverse(),
          barMaxWidth: 22
        }
      ]
    });
  }
}

onMounted(() => {
  renderCharts();
  window.addEventListener("resize", resize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resize);
  disposeAll();
});

function resize() {
  chartBar?.resize();
  chartLine?.resize();
  chartTop?.resize();
}

watch(
  () => props.analysis,
  () => {
    setTimeout(renderCharts, 0);
  },
  { deep: true }
);
</script>

<style scoped>
.analysis-root {
  margin-bottom: 16px;
}
.cards-row {
  margin-bottom: 12px;
}
.stat-card {
  border-radius: 6px;
}
.stat-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.stat-value {
  font-size: 20px;
  font-weight: 600;
  margin-top: 4px;
  color: var(--el-text-color-primary);
}
.stat-value.ok {
  color: var(--el-color-success);
}
.stat-value.fail {
  color: var(--el-color-danger);
}
.chart-card {
  border-radius: 6px;
}
.card-h {
  font-weight: 600;
  font-size: 14px;
}
.chart-box {
  height: 260px;
}
.chart-box.tall {
  height: 320px;
}
</style>
