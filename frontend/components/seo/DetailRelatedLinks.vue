<template>
  <section class="border-t border-slate-200 bg-slate-50">
    <div v-if="item" class="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-8 md:px-6">
      <h2 class="text-xl font-semibold text-slate-900">Weitere passende Seiten</h2>

      <div v-if="regionLinks.length" class="rounded-2xl border border-slate-200 bg-white p-4 md:p-6">
        <h3 class="text-base font-semibold text-slate-900">Passende Regionen</h3>
        <ul class="mt-3 flex flex-wrap gap-2">
          <li v-for="link in regionLinks" :key="link.to">
            <NuxtLink :to="link.to" class="inline-flex rounded-lg bg-sky-50 px-3 py-2 text-sm text-sky-800 transition hover:bg-sky-100">
              {{ link.label }}
            </NuxtLink>
          </li>
        </ul>
      </div>

      <div v-if="collectionLinks.length" class="rounded-2xl border border-slate-200 bg-white p-4 md:p-6">
        <h3 class="text-base font-semibold text-slate-900">Passende Sammlungen</h3>
        <ul class="mt-3 flex flex-wrap gap-2">
          <li v-for="link in collectionLinks" :key="link.to">
            <NuxtLink :to="link.to" class="inline-flex rounded-lg bg-sky-50 px-3 py-2 text-sm text-sky-800 transition hover:bg-sky-100">
              {{ link.label }}
            </NuxtLink>
          </li>
        </ul>
      </div>

      <div v-if="similarSites.length" class="rounded-2xl border border-slate-200 bg-white p-4 md:p-6">
        <h3 class="text-base font-semibold text-slate-900">Aehnliche Badestellen</h3>
        <ul class="mt-3 grid gap-2 md:grid-cols-2">
          <li v-for="site in similarSites" :key="site.id">
            <NuxtLink :to="`/${site.slug}`" class="inline-flex rounded-lg px-2 py-1 text-sm text-sky-800 transition hover:bg-sky-50 hover:text-sky-900">
              {{ site.title }}
            </NuxtLink>
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { MapItem } from '../../types/map'

interface RelatedLink {
  label: string
  to: string
}

defineProps<{
  item: MapItem | null
  regionLinks: RelatedLink[]
  collectionLinks: RelatedLink[]
  similarSites: MapItem[]
}>()
</script>
