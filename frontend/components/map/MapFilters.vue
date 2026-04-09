<template>
  <div class="space-y-4 rounded-xl border border-slate-300 bg-white p-4">
    <label class="block space-y-1">
      <span class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Volltextsuche</span>
      <input
        class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-sky-700"
        :value="searchQuery"
        type="search"
        placeholder="Ort, Badestelle, Adresse, Angebot …"
        @input="$emit('update:search', ($event.target as HTMLInputElement).value)"
      >
    </label>

    <div class="flex flex-wrap gap-2">
      <button
        v-for="option in typeOptions"
        :key="option.value"
        class="rounded-full border px-3 py-1.5 text-sm transition"
        :class="filters.type === option.value ? 'border-sky-700 bg-sky-700 text-white' : 'border-slate-300 bg-white text-slate-700 hover:border-slate-400'"
        type="button"
        @click="$emit('update:filters', { ...filters, type: option.value })"
      >
        {{ option.label }}
      </button>
    </div>

    <label class="block space-y-1">
      <span class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Kategorie</span>
      <select
        class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-700"
        :value="filters.category"
        @change="$emit('update:filters', { ...filters, category: ($event.target as HTMLSelectElement).value })"
      >
        <option value="">Alle Kategorien</option>
        <option v-for="category in options.categories" :key="category" :value="category">
          {{ category }}
        </option>
      </select>
    </label>

    <label class="block space-y-1">
      <span class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Ausstattung</span>
      <select
        class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-700"
        :value="filters.infrastructure"
        @change="$emit('update:filters', { ...filters, infrastructure: ($event.target as HTMLSelectElement).value })"
      >
        <option value="">Alle Einrichtungen</option>
        <option v-for="infrastructure in options.infrastructures" :key="infrastructure" :value="infrastructure">
          {{ infrastructure }}
        </option>
      </select>
    </label>

    <div class="flex flex-wrap gap-2">
      <button
        class="rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-400"
        type="button"
        :disabled="isLocating"
        @click="$emit('locate')"
      >
        {{ isLocating ? 'Standort wird ermittelt…' : 'Meinen Standort verwenden' }}
      </button>
      <button
        class="rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400"
        type="button"
        @click="$emit('reset')"
      >
        Filter zurücksetzen
      </button>
    </div>

    <p v-if="locationError" class="text-sm text-rose-700">
      {{ locationError }}
    </p>
  </div>
</template>

<script setup lang="ts">
import type { FilterState, MapFilterOptions } from '../../types/map'

defineProps<{
  filters: FilterState
  options: MapFilterOptions
  searchQuery: string
  isLocating?: boolean
  locationError?: string | null
}>()

defineEmits<{
  'update:filters': [filters: FilterState]
  'update:search': [value: string]
  locate: []
  reset: []
}>()

const typeOptions = [
  { label: 'Alle', value: 'all' as const },
  { label: 'Badestellen', value: 'badestelle' as const },
  { label: 'POIs', value: 'poi' as const },
]
</script>
