<template>
  <section v-if="showSearchState" class="rounded-xl border border-slate-300 bg-white p-4">
    <div class="flex items-center justify-between gap-3">
      <div>
        <h2 class="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">Suche</h2>
        <p class="mt-1 text-sm text-slate-600">
          <span v-if="isSearching">Suche läuft…</span>
          <span v-else-if="items.length">{{ total }} Treffer für „{{ query }}“</span>
          <span v-else>Keine Treffer für „{{ query }}“</span>
        </p>
      </div>
      <button
        class="rounded-full border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 transition hover:border-slate-400"
        type="button"
        @click="$emit('clear')"
      >
        Suche löschen
      </button>
    </div>

    <ul v-if="items.length" class="mt-4 space-y-2">
      <li v-for="item in items" :key="item.id">
        <button
          class="w-full rounded-xl border px-4 py-3 text-left transition"
          :class="item.id === selectedItemId ? 'border-sky-700 bg-sky-50' : 'border-slate-200 bg-slate-50 hover:border-slate-300 hover:bg-white'"
          type="button"
          @click="$emit('select', item.id)"
        >
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            {{ labelForType(item.type) }}<span v-if="item.category"> · {{ item.category }}</span>
          </p>
          <p class="mt-1 text-base font-semibold leading-tight text-slate-900">{{ item.title }}</p>
          <p v-if="item.city || item.address" class="mt-1 text-sm text-slate-600">
            {{ formatAddress(item) || item.city }}
          </p>
        </button>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { MapItem } from '../../types/map'
import { formatAddress, labelForType } from '../../utils/formatters'

const props = defineProps<{
  query: string
  items: MapItem[]
  total: number
  isSearching: boolean
  selectedItemId?: string | null
}>()

defineEmits<{
  clear: []
  select: [id: string]
}>()

const showSearchState = computed(() => props.query.trim().length >= 2)
</script>
