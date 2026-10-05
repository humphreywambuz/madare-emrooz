<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import AppIcon from '@/components/AppIcon.vue'
import { usePartnerLink } from '@/utils/usePartnerLink'

const { t } = useI18n()
const { loading, busy, link, qr, create, revoke, copy } = usePartnerLink(() => t('partner.copied'))
</script>

<template>
  <div>
  <div v-if="loading" class="skeleton h-64 w-full rounded-box" />
  <div v-else class="flex flex-col gap-6">
    <p class="leading-relaxed text-base-content/70">{{ $t('partner.help') }}</p>

    <template v-if="link">
      <!-- A QR code must stay dark on white to scan, whatever the theme. -->
      <img v-if="qr" :src="qr" :alt="$t('partner.qrAlt')" class="mx-auto w-64 rounded-box border border-base-300" />
      <p class="text-center text-sm leading-relaxed text-base-content/70">{{ $t('partner.scan') }}</p>
      <div class="flex flex-col gap-2">
        <button class="btn" @click="copy"><AppIcon name="copy" class="size-4" />{{ $t('partner.copy') }}</button>
        <button class="btn btn-ghost text-error" :disabled="busy" @click="revoke">{{ $t('partner.revoke') }}</button>
      </div>
      <p class="text-sm leading-relaxed text-base-content/70">{{ $t('partner.revokeHelp') }}</p>
    </template>

    <button v-else class="btn btn-primary btn-lg btn-block" :disabled="busy" @click="create">
      <span v-if="busy" class="loading loading-spinner loading-sm" />{{ $t('partner.create') }}
    </button>
  </div>
  </div>
</template>
