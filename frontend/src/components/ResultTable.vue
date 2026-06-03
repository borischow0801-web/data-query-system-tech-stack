<template>
  <el-table :data="rows" style="width: 100%">
    <el-table-column v-for="col in columns" :key="col" :prop="col" :label="col" />
  </el-table>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  data: any;
}>();

const rows = computed(() => {
  if (Array.isArray(props.data)) return props.data;
  if (props.data && Array.isArray(props.data.rows)) return props.data.rows;
  return [];
});

const columns = computed(() => {
  const first = rows.value[0];
  return first ? Object.keys(first) : [];
});
</script>

