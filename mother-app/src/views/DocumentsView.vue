<script setup lang="ts">
// The test results and scans her midwife uploaded for her.
import { onMounted } from 'vue'

import { documents as documentsApi } from '@/api/endpoints'
import AppIcon from '@/components/AppIcon.vue'
import AsyncState from '@/components/AsyncState.vue'
import EmptyState from '@/components/EmptyState.vue'
import ModalDialog from '@/components/ModalDialog.vue'
import SurfaceCard from '@/components/SurfaceCard.vue'
import { useAsync } from '@/utils/useAsync'
import { useDocumentPreview } from '@/utils/useDocumentPreview'
import { useFormat } from '@/utils/useFormat'

const { dateTime } = useFormat()
const { data, loading, error, run } = useAsync(() => documentsApi.list())
onMounted(run)
const { busy, open, url, doc, view } = useDocumentPreview()
</script>

<template>
  <div class="flex flex-col gap-4 p-4 pt-6">
    <header class="animate-rise px-1 motion-reduce:animate-none">
      <h1 class="font-display text-2xl">{{ $t('nav.documents') }}</h1>
      <p class="mt-1 text-sm leading-relaxed text-base-content/60">{{ $t('documents.help') }}</p>
    </header>

    <AsyncState :loading="loading" :error="error" @retry="run">
      <SurfaceCard v-if="!data?.items.length">
        <EmptyState icon="file" :title="$t('nav.documents')" :text="$t('documents.empty')" />
      </SurfaceCard>
      <SurfaceCard v-else as="ul" class="list">
        <li v-for="d in data.items" :key="d.id" class="list-row items-center">
          <span class="grid size-11 place-items-center rounded-xl bg-primary/10 text-primary">
            <AppIcon :name="d.content_type.startsWith('image/') ? 'image' : 'file'" class="size-5" />
          </span>
          <div class="min-w-0">
            <div class="font-semibold">{{ $t(`documents.types.${d.document_type}`) }}</div>
            <div class="text-xs text-base-content/60">{{ dateTime(d.created_at) }}</div>
            <div v-if="d.notes" class="text-sm leading-relaxed">{{ d.notes }}</div>
          </div>
          <button class="btn btn-sm btn-outline" :disabled="busy" @click="view(d)">{{ $t('documents.view') }}</button>
        </li>
      </SurfaceCard>
    </AsyncState>

    <ModalDialog v-model:open="open" :title="doc ? $t(`documents.types.${doc.document_type}`) : ''" wide>
      <img v-if="doc?.content_type.startsWith('image/')" :src="url" :alt="doc.original_filename"
           class="max-h-[70vh] w-full rounded-box object-contain" />
      <iframe v-else-if="url" :src="url" class="h-[70vh] w-full rounded-box border-0" :title="doc?.original_filename" />
      <div class="modal-action">
        <a class="btn" :href="url" :download="doc?.original_filename"><AppIcon name="download" class="size-4" />{{ $t('documents.download') }}</a>
      </div>
    </ModalDialog>
  </div>
</template>
