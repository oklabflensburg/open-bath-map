<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-4 md:p-6">
    <h2 class="text-lg font-semibold text-slate-900">Gefundene Badestellen</h2>
    <p v-if="!items.length" class="mt-3 text-sm text-slate-600">Fuer diese Seite wurden aktuell keine passenden Badestellen gefunden.</p>

    <ul v-else class="mt-4 grid gap-3 md:grid-cols-2">
      <li v-for="item in items" :key="item.id" class="rounded-xl border border-slate-200 p-4">
        <NuxtLink :to="`/${item.slug}`" class="group">
          <p class="text-base font-semibold text-slate-900 transition group-hover:text-sky-800">{{ item.title }}</p>
          <p class="mt-1 text-sm text-slate-600">{{ item.city || item.district || 'Schleswig-Holstein' }}</p>
          <p v-if="item.waterQuality" class="mt-2 text-sm text-slate-700">Wasserqualitaet: {{ item.waterQuality }}</p>
          <p v-if="item.amenities.length" class="mt-1 text-sm text-slate-700">Ausstattung: {{ item.amenities.slice(0, 3).join(', ') }}</p>
        </NuxtLink>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import type { MapItem } from '../../types/map'

defineProps<{
  items: MapItem[]
}>()
</script>
