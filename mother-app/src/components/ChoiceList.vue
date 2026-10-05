<script setup lang="ts">
// A single choice from a short list, each option on its own row.
const model = defineModel<string | null>({ required: true })
defineProps<{ name: string; options: { value: string; label: string; hint?: string }[] }>()
</script>

<template>
  <div class="flex flex-col gap-2">
    <label v-for="option in options" :key="option.value"
           class="flex cursor-pointer items-center gap-4 rounded-box border border-base-300 bg-base-100 p-4 transition-colors has-checked:border-primary has-checked:bg-primary/10">
      <input v-model="model" type="radio" class="radio radio-primary" :name="name" :value="option.value" />
      <span>
        <span class="block font-semibold">{{ option.label }}</span>
        <span v-if="option.hint" class="block text-sm leading-relaxed text-base-content/60">{{ option.hint }}</span>
      </span>
    </label>
  </div>
</template>
