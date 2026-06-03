<template>
  <el-card>
    <div class="header">
      <el-button @click="$router.back()">返回</el-button>
      <span>接口 {{ interfaceId }} 参数模板</span>
      <el-button type="primary" @click="onSave" :loading="saving">保存</el-button>
    </div>
    <el-table :data="items" style="width: 100%">
      <el-table-column prop="paramCode" label="参数编码">
        <template #default="scope">
          <el-input v-model="scope.row.paramCode" />
        </template>
      </el-table-column>
      <el-table-column prop="displayName" label="显示名称">
        <template #default="scope">
          <el-input v-model="scope.row.displayName" />
        </template>
      </el-table-column>
      <el-table-column prop="dataType" label="类型">
        <template #default="scope">
          <el-select v-model="scope.row.dataType">
            <el-option label="string" value="string" />
            <el-option label="number" value="number" />
            <el-option label="date" value="date" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column prop="formComponent" label="组件">
        <template #default="scope">
          <el-select v-model="scope.row.formComponent">
            <el-option label="输入框" value="input" />
            <el-option label="下拉框" value="select" />
            <el-option label="日期" value="date" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column prop="requiredFlag" label="必填" width="80">
        <template #default="scope">
          <el-switch v-model="scope.row.requiredFlag" :active-value="1" :inactive-value="0" />
        </template>
      </el-table-column>
      <el-table-column label="排序" width="110">
        <template #default="scope">
          <el-button size="small" @click="moveUp(scope.$index)" :disabled="scope.$index === 0">上移</el-button>
          <el-button size="small" @click="moveDown(scope.$index)" :disabled="scope.$index === items.length - 1">下移</el-button>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="80">
        <template #default="scope">
          <el-button size="small" type="danger" @click="onRemove(scope.$index)">删</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-button style="margin-top: 8px" @click="onAdd">新增参数</el-button>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { listParams, saveParamsBatch } from "@/api/params";

const route = useRoute();
const interfaceId = Number(route.params.id);

const items = ref<any[]>([]);
const saving = ref(false);

async function loadData() {
  const res = await listParams(interfaceId);
  items.value = res || [];
}

function onAdd() {
  items.value.push({
    paramCode: "",
    displayName: "",
    dataType: "string",
    formComponent: "input",
    requiredFlag: 0
  });
}

function onRemove(index: number) {
  items.value.splice(index, 1);
}

function moveUp(index: number) {
  if (index <= 0) return;
  const cur = items.value[index];
  items.value.splice(index, 1);
  items.value.splice(index - 1, 0, cur);
}

function moveDown(index: number) {
  if (index >= items.value.length - 1) return;
  const cur = items.value[index];
  items.value.splice(index, 1);
  items.value.splice(index + 1, 0, cur);
}

async function onSave() {
  try {
    saving.value = true;
    // 前端先做基础校验，避免后端 500
    const clean = (items.value || []).map((it: any, idx: number) => ({
      ...it,
      sortNo: idx + 1
    }));
    for (const it of clean) {
      if (!it.paramCode || String(it.paramCode).trim() === "") {
        ElMessage.error("参数编码不能为空");
        return;
      }
    }
    await saveParamsBatch(interfaceId, clean);
    ElMessage.success("保存成功");
    loadData();
  } catch (e: any) {
    ElMessage.error(e?.message || e?.response?.data?.message || "保存失败");
  } finally {
    saving.value = false;
  }
}

onMounted(loadData);
</script>

<style scoped>
.header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
</style>

