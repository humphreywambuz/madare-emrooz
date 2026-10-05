<script setup lang="ts">
import YesNo from '@/components/YesNo.vue'
import { useFormat } from '@/utils/useFormat'
import { SUBCATEGORY_QUESTIONS, useRehabForm } from '@/utils/useRehabForm'

const { errorText, num } = useFormat()
const {
  loading, busy, error, approved, subcategory, painLevel, hadSurgery, surgeryName, usesMedication, extra, questions, canSave, save,
} = useRehabForm()
</script>

<template>
  <div>
  <div v-if="loading" class="skeleton h-64 w-full rounded-box" />
  <form v-else class="flex flex-col gap-4" @submit.prevent="save">
    <p class="leading-relaxed text-base-content/70">{{ $t('rehab.formHelp') }}</p>
    <div v-if="approved" role="status" class="alert alert-info alert-soft text-sm">{{ $t('rehab.reapproval') }}</div>

    <fieldset class="fieldset">
      <legend class="fieldset-legend">{{ $t('rehab.subcategory') }}</legend>
      <select v-model="subcategory" class="select w-full">
        <option v-for="(_, value) in SUBCATEGORY_QUESTIONS" :key="value" :value="value">{{ $t(`rehab.subcategories.${value}`) }}</option>
      </select>
    </fieldset>

    <fieldset class="fieldset">
      <legend class="fieldset-legend">{{ $t('rehab.pain', { n: num(painLevel) }) }}</legend>
      <input v-model.number="painLevel" type="range" min="1" max="10" step="1" class="range range-primary w-full" />
      <div class="flex justify-between text-xs text-base-content/70"><span>{{ $t('rehab.painLow') }}</span><span>{{ $t('rehab.painHigh') }}</span></div>
    </fieldset>

    <div class="flex items-center justify-between gap-4 border-b border-base-300 py-2">
      <span>{{ $t('rehab.had_related_surgery') }}</span>
      <YesNo v-model="hadSurgery" name="surgery" />
    </div>
    <fieldset v-if="hadSurgery" class="fieldset">
      <legend class="fieldset-legend">{{ $t('rehab.related_surgery_name') }}</legend>
      <input v-model="surgeryName" class="input w-full" maxlength="255" required />
    </fieldset>
    <div class="flex items-center justify-between gap-4 border-b border-base-300 py-2">
      <span>{{ $t('rehab.uses_pain_medication') }}</span>
      <YesNo v-model="usesMedication" name="medication" />
    </div>

    <template v-for="q in questions" :key="`${subcategory}-${q.name}`">
      <fieldset v-if="q.options" class="fieldset">
        <legend class="fieldset-legend">{{ $t(`rehab.${q.name}`) }}</legend>
        <select v-model="extra[q.name]" class="select w-full">
          <option :value="null">{{ $t('app.skip') }}</option>
          <option v-for="o in q.options" :key="o" :value="o">{{ $t(`rehab.options.${q.name}.${o}`) }}</option>
        </select>
      </fieldset>
      <div v-else class="flex items-center justify-between gap-4 border-b border-base-300 py-2">
        <span>{{ $t(`rehab.${q.name}`) }}</span>
        <YesNo v-model="(extra[q.name] as boolean | null)" :name="q.name" optional />
      </div>
    </template>

    <div v-if="error" role="alert" class="alert alert-error alert-soft text-sm">{{ errorText(error) }}</div>
    <button class="btn btn-primary btn-lg btn-block mt-2" :disabled="busy || !canSave">
      <span v-if="busy" class="loading loading-spinner loading-sm" />{{ $t('app.save') }}
    </button>
  </form>
  </div>
</template>
