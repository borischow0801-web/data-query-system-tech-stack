<template>
  <pre class="json-viewer">{{ formatted }}</pre>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  value: any;
}>();

const formatted = computed(() => {
  try {
    return JSON.stringify(props.value ?? {}, null, 2);
  } catch {
    return String(props.value ?? "");
  }
});
</script>

<style scoped>
.json-viewer {
  background: #1e1e1e;
  color: #dcdcdc;
  padding: 8px;
  border-radius: 4px;
  max-height: 400px;
  overflow: auto;
  font-family: Menlo, Monaco, Consolas, "Courier New", monospace;
  font-size: 12px;
}
</style>

