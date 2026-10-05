<script setup lang="ts">
import YesNo from '@/components/YesNo.vue'
import { useFormat } from '@/utils/useFormat'
import { HISTORY_SECTIONS, useHistoryForm } from '@/utils/useHistoryForm'

const { errorText } = useFormat()
const { loading, busy, error, flags, texts, save } = useHistoryForm()
</script>

<template>
  <div>
  <div v-if="loading" class="skeleton h-64 w-full rounded-box" />
  <form v-else class="flex flex-col gap-6" @submit.prevent="save">
    <p class="leading-relaxed text-base-content/70">{{ $t('history.help') }}</p>

    <section v-for="section in HISTORY_SECTIONS" :key="section.title" class="flex flex-col gap-2">
      <h2 class="text-lg font-bold">{{ $t(`history.sections.${section.title}`) }}</h2>

      <div v-if="section.counts" class="grid grid-cols-2 gap-4">
        <fieldset v-for="name in section.counts" :key="name" class="fieldset">
          <legend class="fieldset-legend">{{ $t(`history.${name}`) }}</legend>
          <input v-model="texts[name]" class="input ltr w-full" inputmode="numeric" />
        </fieldset>
      </div>

      <div v-for="flag in section.flags" :key="flag.name" class="border-b border-base-300 py-2">
        <div class="flex items-center justify-between gap-4">
          <span>{{ $t(`history.${flag.name}`) }}</span>
          <YesNo v-model="flags[flag.name]" :name="flag.name" optional />
        </div>
        <input v-if="flag.detail && flags[flag.name]" v-model="texts[flag.detail]" class="input mt-2 w-full" maxlength="2000"
               :placeholder="$t(`history.${flag.detail}`)" :aria-label="$t(`history.${flag.detail}`)" />
      </div>

      <fieldset v-for="name in section.notes" :key="name" class="fieldset">
        <legend class="fieldset-legend">{{ $t(`history.${name}`) }}</legend>
        <textarea v-model="texts[name]" class="textarea w-full" rows="2" maxlength="2000" />
      </fieldset>
    </section>

    <div v-if="error" role="alert" class="alert alert-error alert-soft text-sm">{{ errorText(error) }}</div>
    <button class="btn btn-primary btn-lg btn-block" :disabled="busy">
      <span v-if="busy" class="loading loading-spinner loading-sm" />{{ $t('app.save') }}
    </button>
  </form>
  </div>
</template>
