<template>
  <el-form :model="model" label-width="100px" @submit.prevent>
    <el-row :gutter="12">
      <el-col :span="12" v-for="field in schema.fields" :key="field.field">
        <el-form-item :label="field.label">
          <component :is="getComponent(field)" v-model="model[field.field]" :placeholder="field.placeholder" />
        </el-form-item>
      </el-col>
    </el-row>
    <el-form-item>
      <el-button type="primary" @click="$emit('submit', model)">执行查询</el-button>
      <el-button @click="onReset">重置</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { reactive, watch } from "vue";

interface Field {
  field: string;
  label: string;
  dataType: string;
  component: string;
  required: boolean;
  defaultValue?: any;
  placeholder?: string;
}

interface Schema {
  interfaceId: number;
  fields: Field[];
}

const props = defineProps<{
  schema: Schema | null;
}>();

const emit = defineEmits<{
  (e: "submit", payload: any): void;
}>();

const model = reactive<Record<string, any>>({});

watch(
  () => props.schema,
  (s) => {
    Object.keys(model).forEach((k) => delete model[k]);
    if (s?.fields) {
      for (const f of s.fields) {
        model[f.field] = f.defaultValue ?? null;
      }
    }
  },
  { immediate: true }
);

function getComponent(field: Field) {
  if (field.component === "date") return "el-date-picker";
  if (field.component === "select") return "el-select";
  return "el-input";
}

function onReset() {
  if (!props.schema?.fields) return;
  for (const f of props.schema.fields) {
    model[f.field] = f.defaultValue ?? null;
  }
}
</script>

