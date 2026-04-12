<template>
  <section class="grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 md:grid-cols-3 md:p-6">
    <article class="rounded-xl bg-slate-50 p-4">
      <p class="text-xs uppercase tracking-[0.14em] text-slate-500">Badestellen</p>
      <p class="mt-1 text-2xl font-bold text-slate-900">{{ count }}</p>
    </article>
    <article class="rounded-xl bg-slate-50 p-4">
      <p class="text-xs uppercase tracking-[0.14em] text-slate-500">Typ</p>
      <p class="mt-1 text-sm font-medium text-slate-900">{{ typeLabel }}</p>
    </article>
    <article class="rounded-xl bg-slate-50 p-4">
      <p class="text-xs uppercase tracking-[0.14em] text-slate-500">Datengrundlage</p>
      <p class="mt-1 text-sm font-medium text-slate-900">{{ sourceHint }}</p>
    </article>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  count: number
  typeLabel: string
  sourceHint: string
}>()
</script>
