<template>
  <section v-if="links.length" class="rounded-2xl border border-slate-200 bg-white p-4 md:p-6">
    <h2 class="text-lg font-semibold text-slate-900">Verwandte Seiten</h2>
    <ul class="mt-3 grid gap-2 md:grid-cols-2">
      <li v-for="link in links" :key="link.to">
        <NuxtLink :to="link.to" class="inline-flex rounded-lg px-3 py-2 text-sm text-sky-800 transition hover:bg-sky-50 hover:text-sky-900">
          {{ link.label }}
        </NuxtLink>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
interface RelatedLink {
  label: string
  to: string
}

defineProps<{
  links: RelatedLink[]
}>()
</script>
