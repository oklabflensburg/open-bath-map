<template>
  <main class="min-h-screen bg-slate-50 text-slate-900">
    <div class="mx-auto flex min-h-screen max-w-4xl flex-col px-4 py-6 sm:px-6 lg:px-8">
      <header class="mb-10 flex flex-col gap-4 border-b border-slate-200 pb-6 sm:flex-row sm:items-end sm:justify-between">
        <div class="space-y-2">
          <NuxtLink to="/" class="text-sm font-medium text-sky-700 transition hover:text-sky-900">
            Zur Karte
          </NuxtLink>
          <div>
            <p class="text-sm uppercase tracking-[0.24em] text-slate-500">Badestellenkarte</p>
            <h1 class="text-3xl font-bold tracking-tight sm:text-4xl">{{ title }}</h1>
          </div>
        </div>

        <SiteLegalLinks />
      </header>

      <article class="site-legal-content max-w-none">
        <slot />
      </article>
    </div>
  </main>
</template>

<script setup lang="ts">
defineProps<{
  title: string
}>()
</script>

<style scoped>
.site-legal-content {
  color: rgb(51 65 85);
  font-size: 1rem;
  line-height: 1.75;
}

.site-legal-content :deep(h2) {
  margin: 2rem 0 0.75rem;
  color: rgb(15 23 42);
  font-size: 1.375rem;
  font-weight: 700;
  line-height: 1.3;
}

.site-legal-content :deep(p) {
  margin: 0.75rem 0;
}

.site-legal-content :deep(a) {
  color: rgb(3 105 161);
}
</style>
