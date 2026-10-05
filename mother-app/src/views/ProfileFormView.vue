<script setup lang="ts">
// A new mother's first screen (her goal, then her profile); the same form edits it later.
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import BrandMark from '@/components/BrandMark.vue'
import ChoiceList from '@/components/ChoiceList.vue'
import DateInput from '@/components/DateInput.vue'
import { fieldErrorOf } from '@/utils/forms'
import { useFormat } from '@/utils/useFormat'
import { BLOOD_TYPES, useProfileForm } from '@/utils/useProfileForm'

const { t } = useI18n()
const { errorText } = useFormat()
const {
  isNew, busy, error, canSave, isPregnancyPath, save,
  goal, firstName, lastName, birthDate, height, weight, nationalCode, motherBlood, spouseBlood, status,
} = useProfileForm()

const goals = computed(() =>
  (['pregnancy', 'fitness', 'rehabilitation'] as const).map((value) => ({
    value, label: t(`goal.${value}.label`), hint: t(`goal.${value}.hint`),
  })),
)
const statuses = computed(() =>
  (['pregnant', 'trying_to_conceive', 'postpartum'] as const).map((value) => ({ value, label: t(`status.${value}`) })),
)
</script>

<template>
  <div :class="isNew ? 'mx-auto min-h-screen w-full max-w-md p-4 pb-12' : ''">
    <header v-if="isNew" class="flex flex-col gap-2 py-6">
      <BrandMark />
      <h1 class="font-display text-2xl">{{ $t('welcome.title') }}</h1>
      <p class="leading-relaxed text-base-content/70">{{ $t('welcome.text') }}</p>
    </header>

    <form class="flex flex-col gap-6" @submit.prevent="save">
      <section class="flex flex-col gap-2">
        <h2 class="text-lg font-bold">{{ $t('profile.goalTitle') }}</h2>
        <ChoiceList v-model="goal" name="goal" :options="goals" />
      </section>

      <section v-if="goal" class="flex flex-col gap-2">
        <h2 class="text-lg font-bold">{{ $t('profile.aboutTitle') }}</h2>
        <div class="grid grid-cols-2 gap-4">
          <fieldset class="fieldset">
            <legend class="fieldset-legend">{{ $t('profile.first_name') }}</legend>
            <input v-model="firstName" class="input w-full" required maxlength="100" autocomplete="given-name" />
          </fieldset>
          <fieldset class="fieldset">
            <legend class="fieldset-legend">{{ $t('profile.last_name') }}</legend>
            <input v-model="lastName" class="input w-full" required maxlength="100" autocomplete="family-name" />
          </fieldset>
        </div>
        <fieldset class="fieldset">
          <legend class="fieldset-legend">{{ $t('profile.birth_date') }}</legend>
          <DateInput v-model="birthDate" :years-back="60" :years-ahead="0" />
        </fieldset>
        <div class="grid grid-cols-2 gap-4">
          <fieldset class="fieldset">
            <legend class="fieldset-legend">{{ $t('profile.height_cm') }}</legend>
            <input v-model="height" class="input ltr w-full" inputmode="decimal"
                   :class="{ 'input-error': fieldErrorOf(error, 'height_cm') }" />
          </fieldset>
          <fieldset class="fieldset">
            <legend class="fieldset-legend">{{ $t('profile.initial_weight_kg') }}</legend>
            <input v-model="weight" class="input ltr w-full" inputmode="decimal"
                   :class="{ 'input-error': fieldErrorOf(error, 'initial_weight_kg') }" />
          </fieldset>
        </div>

        <template v-if="isPregnancyPath">
          <fieldset class="fieldset">
            <legend class="fieldset-legend">{{ $t('profile.national_code') }}</legend>
            <input v-model="nationalCode" class="input ltr w-full" inputmode="numeric" maxlength="10"
                   :class="{ 'input-error': fieldErrorOf(error, 'national_code') }" />
            <p class="label whitespace-normal">{{ $t('profile.optionalHint') }}</p>
          </fieldset>
          <div class="grid grid-cols-2 gap-4">
            <fieldset class="fieldset">
              <legend class="fieldset-legend">{{ $t('profile.mother_blood_type') }}</legend>
              <select v-model="motherBlood" class="select w-full">
                <option value="">{{ $t('profile.unknown') }}</option>
                <option v-for="b in BLOOD_TYPES" :key="b" :value="b">{{ b }}</option>
              </select>
            </fieldset>
            <fieldset class="fieldset">
              <legend class="fieldset-legend">{{ $t('profile.spouse_blood_type') }}</legend>
              <select v-model="spouseBlood" class="select w-full">
                <option value="">{{ $t('profile.unknown') }}</option>
                <option v-for="b in BLOOD_TYPES" :key="b" :value="b">{{ b }}</option>
              </select>
            </fieldset>
          </div>
          <fieldset class="fieldset">
            <legend class="fieldset-legend">{{ $t('profile.statusTitle') }}</legend>
            <ChoiceList v-model="status" name="status" :options="statuses" />
          </fieldset>
        </template>
      </section>

      <div v-if="error" role="alert" class="alert alert-error alert-soft text-sm">{{ errorText(error) }}</div>
      <button v-if="goal" class="btn btn-primary btn-lg btn-block" :disabled="busy || !canSave">
        <span v-if="busy" class="loading loading-spinner loading-sm" />{{ $t(isNew ? 'welcome.start' : 'app.save') }}
      </button>
    </form>
  </div>
</template>
