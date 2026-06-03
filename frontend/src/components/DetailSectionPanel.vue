<template>
  <div class="detail-panel">
    <el-empty v-if="!sections?.length" description="暂无分组展示配置，请在下方的 JSON 中查看原始结构" />
    <div v-for="sec in sections" :key="sec.key" class="section-block">
      <div class="section-title">{{ sec.title }}</div>
      <template v-if="sec.render?.type === 'table'">
        <el-table
          v-if="(sec.render.rows || []).length"
          :data="sec.render.rows"
          border
          stripe
          size="small"
          max-height="360"
          style="width: 100%"
        >
          <el-table-column
            v-for="col in sec.render.columns || []"
            :key="col.field"
            :prop="col.field"
            :label="col.label"
            min-width="120"
            show-overflow-tooltip
          />
        </el-table>
        <el-empty v-else description="本节无表格数据" :image-size="64" />
      </template>
      <template v-else-if="sec.render?.type === 'kv'">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item
            v-for="(it, idx) in sec.render.items || []"
            :key="idx"
            :label="it.label"
            :span="1"
          >
            <el-tooltip v-if="String(it.value || '').length > 80" :content="String(it.value)" placement="top">
              <span class="cell-ellipsis">{{ it.value }}</span>
            </el-tooltip>
            <span v-else>{{ it.value }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </template>
      <template v-else-if="sec.render?.type === 'empty'">
        <el-alert type="info" :closable="false">{{ sec.render.message || "暂无数据" }}</el-alert>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  sections: any[];
}>();
</script>

<style scoped>
.detail-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.section-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 10px;
  color: var(--dq-text, #303133);
  border-left: 3px solid var(--el-color-primary);
  padding-left: 8px;
}
.cell-ellipsis {
  display: inline-block;
  max-width: 360px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: bottom;
}
</style>
