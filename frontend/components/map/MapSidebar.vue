<template>
  <aside class="hidden h-full w-[26rem] shrink-0 border-l border-slate-300 bg-slate-100 md:flex md:flex-col">
    <div class="flex-1 overflow-y-auto px-6 py-8">
      <header class="mb-6 space-y-1">
        <h1 class="text-3xl font-bold leading-tight text-slate-900">Badestellenkarte</h1>
        <p class="text-lg text-slate-600">Open Data für Badestellen und POIs in Schleswig-Holstein</p>
      </header>

      <div class="mb-6 inline-flex rounded-full border border-slate-300 bg-white p-1">
        <button
          class="rounded-full px-4 py-2 text-sm font-medium transition"
          :class="activeTab === 'info' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'"
          type="button"
          @click="activeTab = 'info'"
        >
          Info
        </button>
        <button
          class="rounded-full px-4 py-2 text-sm font-medium transition"
          :class="activeTab === 'search' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'"
          type="button"
          @click="activeTab = 'search'"
        >
          Suche &amp; Filter
        </button>
        <button
          class="rounded-full px-4 py-2 text-sm font-medium transition"
          :class="activeTab === 'result' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'"
          type="button"
          @click="activeTab = 'result'"
        >
          Marker
        </button>
      </div>

      <section v-if="activeTab === 'info'">
        <MapIntro />
      </section>

      <section v-else-if="activeTab === 'search'">
        <MapFilters
          :filters="filters"
          :is-locating="isLocating"
          :location-error="locationError"
          :options="options"
          :search-query="searchQuery"
          @locate="$emit('locate')"
          @reset="$emit('resetFilters')"
          @update:filters="$emit('update:filters', $event)"
          @update:search="$emit('update:search', $event)"
        />

        <p v-if="fetchError" class="mt-4 text-sm text-rose-700">
          {{ fetchError }}
        </p>

        <div class="mt-4">
          <MapSearchResults
            :is-searching="isSearching"
            :items="searchResults"
            :query="searchQuery"
            :selected-item-id="item?.id ?? null"
            :total="searchTotal"
            @clear="$emit('clearSearch')"
            @select="$emit('selectSearchResult', $event)"
          />
        </div>
      </section>

      <section v-else class="mt-1">
        <div v-if="!item" class="rounded-xl border border-dashed border-slate-300 bg-white px-4 py-6 text-sm text-slate-600">
          Wähle einen Marker auf der Karte oder einen Treffer aus der Suche, um hier die Details zu sehen.
        </div>

        <article v-else class="overflow-hidden rounded-xl border border-slate-300 bg-white">
          <img
            v-if="showImage"
            :src="item.imageUrl || undefined"
            :alt="item.title"
            class="h-56 w-full object-cover"
            @error="applyImageFallback"
          >
          <div class="p-5">
            <div class="mb-3 flex items-start justify-between gap-4">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  {{ labelForType(item.type) }}
                </p>
                <h2 class="mt-1 text-2xl font-bold leading-tight text-slate-900">{{ item.title }}</h2>
              </div>
              <button class="rounded-full border border-slate-300 p-2 text-slate-600 transition hover:bg-slate-100" type="button" @click="closeDetails">
                <span class="sr-only">Schließen</span>
                ×
              </button>
            </div>

            <ul class="space-y-4 text-sm leading-6 text-slate-700">
              <li v-if="formattedAddress">
                <strong class="block text-slate-900">Adresse</strong>
                {{ formattedAddress }}
              </li>
              <li v-if="item.description">
                <strong class="block text-slate-900">Beschreibung</strong>
                {{ item.description }}
              </li>
              <li v-if="item.type === 'badestelle' && item.waterQuality">
                <strong class="block text-slate-900">Wasserqualität</strong>
                {{ item.waterQuality }}
              </li>
              <li v-if="item.type === 'badestelle' && formattedSeasonDuration">
                <strong class="block text-slate-900">Badegewässer Saisondauer</strong>
                {{ formattedSeasonDuration }}
              </li>
              <li v-if="item.accessibility">
                <strong class="block text-slate-900">Zugang</strong>
                {{ item.accessibility }}
              </li>
              <li v-if="item.type === 'badestelle' && item.possiblePollutions">
                <strong class="block text-slate-900">Mögliche Belastungen</strong>
                {{ item.possiblePollutions }}
              </li>
              <li v-if="item.type === 'poi' && item.openingHours">
                <strong class="block text-slate-900">Öffnungszeiten</strong>
                {{ item.openingHours }}
              </li>
              <li v-if="item.type === 'poi' && item.contentLicense">
                <strong class="block text-slate-900">Lizenz</strong>
                {{ item.contentLicense }}
              </li>
              <li v-if="item.type === 'poi' && item.sourceName">
                <strong class="block text-slate-900">Quelle</strong>
                {{ item.sourceName }}
              </li>
              <li v-if="item.amenities.length">
                <strong class="block text-slate-900">{{ item.type === 'badestelle' ? 'Ausstattung' : 'Angebot' }}</strong>
                {{ item.amenities.join(', ') }}
              </li>
              <li v-if="formattedDate">
                <strong class="block text-slate-900">Letzte Aktualisierung</strong>
                {{ formattedDate }}
              </li>
            </ul>
          </div>
        </article>
      </section>
    </div>

    <div class="border-t border-slate-300 px-6 py-4">
      <SiteLegalLinks />
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { FilterState, MapFilterOptions, MapItem } from '../../types/map'
import { formatAddress, formatDate, formatSeasonDuration, isValidHttpUrl, labelForType } from '../../utils/formatters'
import { applyImageFallback } from '../../composables/useImageFallback'

const props = defineProps<{
  item: MapItem | null
  filters: FilterState
  options: MapFilterOptions
  searchQuery: string
  searchResults: MapItem[]
  searchTotal: number
  isLoading: boolean
  isSearching: boolean
  fetchError: string | null
  isLocating: boolean
  locationError: string | null
}>()

const emit = defineEmits<{
  clearSearch: []
  close: []
  locate: []
  resetFilters: []
  selectSearchResult: [id: string]
  'update:filters': [filters: FilterState]
  'update:search': [value: string]
}>()

const activeTab = ref<'info' | 'search' | 'result'>('info')

const formattedAddress = computed(() => props.item ? formatAddress(props.item) : null)
const formattedDate = computed(() => formatDate(props.item?.lastUpdate))
const formattedSeasonDuration = computed(() => formatSeasonDuration(props.item))
const showImage = computed(() => isValidHttpUrl(props.item?.imageUrl))

watch(() => props.item, (item) => {
  activeTab.value = item ? 'result' : activeTab.value === 'result' ? 'info' : activeTab.value
})

function closeDetails() {
  activeTab.value = 'info'
  emit('close')
}
</script>
