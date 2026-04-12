<template>
  <section class="rounded-2xl border border-slate-200 bg-gradient-to-br from-slate-50 to-sky-50 p-6 md:p-8">
    <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{{ eyebrow }}</p>
    <h1 class="mt-2 text-3xl font-bold leading-tight text-slate-900 md:text-4xl">{{ title }}</h1>
    <p v-if="subtitle" class="mt-3 max-w-3xl text-base leading-7 text-slate-700">{{ subtitle }}</p>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  eyebrow: string
  title: string
  subtitle?: string
}>()
</script>
