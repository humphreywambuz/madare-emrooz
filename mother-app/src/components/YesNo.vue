<script setup lang="ts">
// Yes / no, or left unanswered when `optional` (unanswered is not the same as "no").
const model = defineModel<boolean | null>({ required: true })
defineProps<{ name: string; optional?: boolean }>()
</script>

<template>
  <div class="join">
    <input v-model="model" type="radio" class="btn btn-sm join-item" :name="name" :value="true" :aria-label="$t('app.yes')" />
    <input v-model="model" type="radio" class="btn btn-sm join-item" :name="name" :value="false" :aria-label="$t('app.no')" />
    <input v-if="optional" v-model="model" type="radio" class="btn btn-sm join-item" :name="name" :value="null"
           :aria-label="$t('app.skip')" />
  </div>
</template>
