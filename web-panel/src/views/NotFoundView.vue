<template>
  <div class="flex min-h-screen flex-col items-center justify-center gap-4 bg-base-200 p-6 text-center">
    <h1 class="text-2xl font-bold">{{ $t('notFound.title') }}</h1>
    <RouterLink to="/" class="btn btn-primary">{{ $t('notFound.back') }}</RouterLink>
  </div>
</template>
