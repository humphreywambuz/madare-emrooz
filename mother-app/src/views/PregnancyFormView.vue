<script setup lang="ts">
import DateInput from '@/components/DateInput.vue'
import ModalDialog from '@/components/ModalDialog.vue'
import { fieldErrorOf } from '@/utils/forms'
import { useFormat } from '@/utils/useFormat'
import { usePregnancyForm } from '@/utils/usePregnancyForm'

const { errorText, num } = useFormat()
const {
  loading, busy, error, current, lmpDate, cycleLength, conceptionType, providerType, providerName, ending, save, end,
} = usePregnancyForm()
</script>

<template>
  <div>
  <div v-if="loading" class="skeleton h-64 w-full rounded-box" />
  <div v-else class="flex flex-col gap-6">
    <p class="leading-relaxed text-base-content/70">{{ $t(current ? 'pregnancy.editHelp' : 'pregnancy.startHelp') }}</p>

    <form class="flex flex-col gap-2" @submit.prevent="save">
      <fieldset class="fieldset">
        <legend class="fieldset-legend">{{ $t('pregnancy.lmp_date') }}</legend>
        <DateInput v-model="lmpDate" :years-back="1" :years-ahead="0" required />
        <p v-if="fieldErrorOf(error, 'lmp_date')" class="label whitespace-normal text-error">{{ $t('pregnancy.lmpInvalid') }}</p>
      </fieldset>
      <fieldset class="fieldset">
        <legend class="fieldset-legend">{{ $t('pregnancy.cycle', { n: num(cycleLength) }) }}</legend>
        <input v-model.number="cycleLength" type="range" min="20" max="45" class="range range-primary w-full" />
        <p class="label whitespace-normal">{{ $t('pregnancy.cycleHint') }}</p>
      </fieldset>
      <fieldset class="fieldset">
        <legend class="fieldset-legend">{{ $t('pregnancy.conception_type') }}</legend>
        <div class="join">
          <input v-model="conceptionType" type="radio" class="btn join-item" name="conception" value="natural"
                 :aria-label="$t('pregnancy.natural')" />
          <input v-model="conceptionType" type="radio" class="btn join-item" name="conception" value="assisted"
                 :aria-label="$t('pregnancy.assisted')" />
        </div>
      </fieldset>
      <fieldset class="fieldset">
        <legend class="fieldset-legend">{{ $t('pregnancy.care_provider_type') }}</legend>
        <select v-model="providerType" class="select w-full">
          <option value="">{{ $t('pregnancy.noProvider') }}</option>
          <option v-for="p in ['specialist', 'midwife', 'health_center']" :key="p" :value="p">{{ $t(`pregnancy.provider.${p}`) }}</option>
        </select>
      </fieldset>
      <fieldset v-if="providerType" class="fieldset">
        <legend class="fieldset-legend">{{ $t('pregnancy.care_provider_name') }}</legend>
        <input v-model="providerName" class="input w-full" maxlength="200" />
      </fieldset>

      <div v-if="error" role="alert" class="alert alert-error alert-soft mt-2 text-sm">{{ errorText(error) }}</div>
      <button class="btn btn-primary btn-lg btn-block mt-4" :disabled="busy || !lmpDate">
        <span v-if="busy" class="loading loading-spinner loading-sm" />{{ $t(current ? 'app.save' : 'pregnancy.start') }}
      </button>
    </form>

    <section v-if="current" class="border-t border-base-300 pt-6">
      <h2 class="font-semibold">{{ $t('pregnancy.endTitle') }}</h2>
      <p class="mt-1 text-sm leading-relaxed text-base-content/70">{{ $t('pregnancy.endHelp') }}</p>
      <button class="btn mt-4" @click="ending = true">{{ $t('pregnancy.endOpen') }}</button>
    </section>

    <ModalDialog v-model:open="ending" :title="$t('pregnancy.endTitle')">
      <p class="leading-relaxed text-base-content/70">{{ $t('pregnancy.endQuestion') }}</p>
      <div class="modal-action flex-col">
        <button class="btn btn-primary btn-block" :disabled="busy" @click="end('delivered')">{{ $t('pregnancy.endDelivered') }}</button>
        <button class="btn btn-block" :disabled="busy" @click="end('ended')">{{ $t('pregnancy.endOther') }}</button>
      </div>
    </ModalDialog>
  </div>
  </div>
</template>
