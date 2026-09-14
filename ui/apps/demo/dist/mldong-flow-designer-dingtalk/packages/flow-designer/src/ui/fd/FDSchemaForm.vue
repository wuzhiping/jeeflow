<template>
  <FDForm v-if="formItems?.length" :label-width="labelWidth">
    <FDFormItem
      v-for="item in formItems"
      :key="item.name"
      :label="item.helpMessage && item.helpMessage.length ? undefined : item.label"
    >
      <template v-if="item.helpMessage && item.helpMessage.length" #label>
        {{ item.label }}
        <FDTooltip>
          <template #content>
            <template v-if="Array.isArray(item.helpMessage)">
              <div v-for="(msg, i) in item.helpMessage" :key="i">{{ msg }}</div>
            </template>
            <template v-else>{{ item.helpMessage }}</template>
          </template>
          <img :src="QuestionSvg" />
        </FDTooltip>
      </template>
      <FDInput v-if="item.component == 'Input'" v-model="model[item.name]" v-bind="{...item.componentProps}"></FDInput>
      <FDSelect v-else-if="item.component == 'Select'" v-model="model[item.name]" v-bind="{...item.componentProps}"></FDSelect>
      <template v-else-if="item.slot">
        <slot :name="item.slot" v-bind="renderContext"></slot>
      </template>
      <component v-else :is="item.render ? item.render(renderContext) : undefined" v-model="model[item.name]" v-model:value="model[item.name]" v-model:checked="model[item.name]" />
    </FDFormItem>
  </FDForm>
</template>

<script setup lang="ts">
/**
 * FDSchemaForm —— FDFormType 元数据 → 表单的共享渲染器
 * canvas 抽屉 / dingtalk 编辑抽屉 / dingtalk 流程弹窗三处共用，
 * 保证双模式内置表单外观与能力（Input/Select/slot/render/helpMessage）完全一致。
 * model 为外部 reactive 对象，直接按 item.name 读写（设计器场景无校验需求）。
 */
import FDForm from './FDForm.vue'
import FDFormItem from './FDFormItem.vue'
import FDInput from './FDInput.vue'
import FDSelect from './FDSelect.vue'
import FDTooltip from './FDTooltip.vue'
import QuestionSvg from '../../assets/question.svg'
import type { FDFormItemType } from '../../types'

withDefaults(defineProps<{
  formItems?: FDFormItemType[]
  model: Record<string, any>
  labelWidth?: string
  renderContext?: any
}>(), {
  labelWidth: '120px'
})
</script>
