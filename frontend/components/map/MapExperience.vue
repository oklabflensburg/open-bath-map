<template>
  <main class="relative flex h-dvh w-full flex-col overflow-hidden bg-white text-slate-900 md:flex-row">
    <div id="mapContainer" class="relative order-2 flex min-h-0 flex-1 flex-col md:order-1 md:min-h-0">
      <ClientOnly>
        <MapView
          ref="mapViewRef"
          :features="state.currentMarkers.value"
          :is-loading="state.isLoading.value"
          :selected-item-id="state.selectedItem.value?.id ?? null"
          :user-location="state.currentUserLocation.value"
          @bounds-change="handleBoundsChange"
          @map-click="handleMapBackgroundClick"
          @marker-select="handleMarkerSelect"
          @ready="handleMapReady"
        />
      </ClientOnly>
    </div>

    <MapSidebar
      :fetch-error="state.fetchError.value"
      :filters="state.filters.value"
      :is-loading="state.isLoading.value"
      :is-locating="isLocating"
      :item="state.selectedItem.value"
      :location-error="locationError"
      :options="state.availableFilters.value"
      @close="closeSelection"
      @locate="handleLocate"
      @reset-filters="resetFilters"
      @update:filters="handleFiltersUpdate"
    />

    <div class="pointer-events-none fixed inset-x-0 bottom-4 z-[1200] flex justify-center px-4 md:hidden">
      <div class="pointer-events-auto rounded-full border border-slate-200 bg-white/95 px-4 py-2 shadow-lg backdrop-blur">
        <SiteLegalLinks />
      </div>
    </div>

    <MapBottomSheet
      :fetch-error="state.fetchError.value"
      :filters="state.filters.value"
      :is-locating="isLocating"
      :is-open="state.isBottomSheetOpen.value"
      :item="state.selectedItem.value"
      :location-error="locationError"
      :options="state.availableFilters.value"
      @close="state.closeBottomSheet()"
      @close-details="closeSelection"
      @open="state.openBottomSheet()"
      @locate="handleLocate"
      @reset-filters="resetFilters"
      @update:filters="handleFiltersUpdate"
    />
  </main>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useHead, useRuntimeConfig, useSeoMeta } from '#imports'
import type { FilterState, MapBounds, MapItem, UserLocation } from '../../types/map'
import { buildMetaDescription, buildMetaTitle } from '../../utils/formatters'

const state = useMapState()
const { loadBounds, loadRadius } = useMapData()
const { closeSelection, selectById } = useMapSelection()
const { isLocating, locationError, requestLocation } = useGeolocation()
const config = useRuntimeConfig()
const mapViewRef = ref<{
  focusItem: (item: MapItem, zoom?: number) => void
  centerOnLocation: (location: UserLocation, zoom?: number) => void
} | null>(null)
const didInitialBoundsLoad = ref(false)
const isMapReady = ref(false)

const canonicalUrl = computed(() => {
  const path = state.selectedSlug.value ? `/${state.selectedSlug.value}` : ''
  return `${config.public.siteUrl}${path}`
})

useSeoMeta({
  title: () => buildMetaTitle(state.selectedItem.value),
  ogTitle: () => buildMetaTitle(state.selectedItem.value),
  description: () => buildMetaDescription(state.selectedItem.value),
  ogDescription: () => buildMetaDescription(state.selectedItem.value),
})

useHead({
  link: () => [
    {
      rel: 'canonical',
      href: canonicalUrl.value,
    },
  ],
})

watch(() => state.selectedItem.value, (item) => {
  if (item && isMapReady.value) {
    focusSelectedItem(item)
  }

  if (item) {
    state.openBottomSheet()
  }
})

watch(() => state.filters.value, async () => {
  if (!didInitialBoundsLoad.value) {
    return
  }

  await reloadForCurrentMode()
}, { deep: true })

async function handleBoundsChange(bounds: MapBounds) {
  didInitialBoundsLoad.value = true
  await loadBounds(bounds)
}

async function handleMarkerSelect(id: string) {
  await selectById(id)
}

async function handleLocate() {
  const location = await requestLocation()
  if (!location) {
    return
  }

  await runRadiusSearch(location)
}

async function runRadiusSearch(location: UserLocation) {
  mapViewRef.value?.centerOnLocation(location, 12)
  await loadRadius(location)
}

function handleMapReady() {
  isMapReady.value = true
  if (state.selectedItem.value) {
    focusSelectedItem(state.selectedItem.value)
  }
}

function handleMapBackgroundClick() {
  if (state.selectedItem.value) {
    closeSelection()
  }
}

function handleFiltersUpdate(filters: FilterState) {
  state.filters.value = filters
}

function resetFilters() {
  state.filters.value = {
    type: 'all',
    category: '',
    infrastructure: '',
  }
}

async function reloadForCurrentMode() {
  if (state.queryMode.value === 'radius' && state.currentUserLocation.value) {
    await loadRadius(state.currentUserLocation.value)
    return
  }

  if (state.currentBounds.value) {
    await loadBounds(state.currentBounds.value)
  }
}

function focusSelectedItem(item: MapItem) {
  mapViewRef.value?.focusItem(item, 17)
}
</script>
