<template>
  <div class="relative order-3 z-[1000] shrink-0 md:hidden">
    <section
      class="flex flex-col overflow-hidden rounded-t-[1.5rem] border-t border-slate-300 bg-slate-100/95 shadow-[0_-12px_32px_rgba(15,23,42,0.18)] backdrop-blur"
      :class="isDragging ? 'transition-none' : 'transition-[height,transform] duration-200 ease-out'"
      :style="sheetStyle"
      @click="onSheetClick"
      @touchstart="onTouchStart"
      @touchmove="onTouchMove"
      @touchend="onTouchEnd"
      @touchcancel="onTouchEnd"
    >
      <div class="flex cursor-grab justify-center py-2 active:cursor-grabbing">
        <div class="h-1.5 w-14 rounded-full bg-slate-300" />
      </div>

      <div
        v-show="isOpen"
        ref="contentElement"
        class="flex-1 overflow-y-auto px-4 pb-24"
      >
        <div class="mb-4 flex justify-center">
          <div class="inline-flex rounded-full border border-slate-300 bg-white p-1">
          <button
            class="rounded-full px-4 py-2 text-sm font-medium transition"
            :class="activeTab === 'info' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'"
            type="button"
            @click="setActiveTab('info')"
          >
            Info
          </button>
          <button
            class="rounded-full px-4 py-2 text-sm font-medium transition"
            :class="activeTab === 'search' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'"
            type="button"
            @click="setActiveTab('search')"
          >
            Suche &amp; Filter
          </button>
          <button
            class="rounded-full px-4 py-2 text-sm font-medium transition"
            :class="activeTab === 'result' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'"
            type="button"
            @click="setActiveTab('result')"
          >
            Marker
          </button>
          </div>
        </div>

        <section v-if="activeTab === 'info'">
          <MapIntro />
        </section>

        <section v-else-if="activeTab === 'search'">
          <div class="mb-4">
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
          </div>

          <p v-if="fetchError" class="mb-4 text-sm text-rose-700">
            {{ fetchError }}
          </p>

          <div class="mb-4">
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

        <section v-else>
          <div v-if="!item" class="rounded-xl border border-dashed border-slate-300 bg-white px-4 py-6 text-sm text-slate-600">
            Wähle einen Marker auf der Karte oder einen Treffer aus der Suche, um hier die Details zu sehen.
          </div>

          <article v-else class="rounded-xl border border-slate-300 bg-white">
            <img
              v-if="showImage"
              :src="item.imageUrl || undefined"
              :alt="item.title"
              class="h-48 w-full rounded-t-xl object-cover"
              @error="applyImageFallback"
            >
            <div class="p-4">
              <div class="mb-3 flex items-start justify-between gap-3">
                <div>
                  <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                    {{ labelForType(item.type) }}<span v-if="item.category"> · {{ item.category }}</span>
                  </p>
                  <h2 class="mt-1 text-xl font-bold leading-tight text-slate-900">{{ item.title }}</h2>
                </div>
                <button class="rounded-full border border-slate-300 p-2 text-slate-600" type="button" @click.stop="closeDetails">
                  <span class="sr-only">Schließen</span>
                  ×
                </button>
              </div>

              <ul class="space-y-3 text-sm leading-6 text-slate-700">
                <li v-if="formattedAddress">{{ formattedAddress }}</li>
                <li v-if="item.description">{{ item.description }}</li>
                <li v-if="item.type === 'badestelle' && item.waterQuality">Wasserqualität: {{ item.waterQuality }}</li>
                <li v-if="item.type === 'badestelle' && formattedSeasonDuration">Badegewässer Saisondauer: {{ formattedSeasonDuration }}</li>
                <li v-if="item.accessibility">Zugang: {{ item.accessibility }}</li>
                <li v-if="item.type === 'badestelle' && item.possiblePollutions">Mögliche Belastungen: {{ item.possiblePollutions }}</li>
                <li v-if="item.type === 'poi' && item.openingHours">Öffnungszeiten: {{ item.openingHours }}</li>
                <li v-if="item.amenities.length">{{ item.type === 'badestelle' ? 'Ausstattung' : 'Angebot' }}: {{ item.amenities.join(', ') }}</li>
                <li v-if="formattedDate">Aktualisiert: {{ formattedDate }}</li>
              </ul>
            </div>
          </article>
        </section>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { FilterState, MapFilterOptions, MapItem } from '../../types/map'
import { formatAddress, formatDate, formatSeasonDuration, isValidHttpUrl, labelForType } from '../../utils/formatters'
import { applyImageFallback } from '../../composables/useImageFallback'

const props = defineProps<{
  item: MapItem | null
  isOpen: boolean
  filters: FilterState
  options: MapFilterOptions
  searchQuery: string
  searchResults: MapItem[]
  searchTotal: number
  isSearching: boolean
  fetchError: string | null
  isLocating: boolean
  locationError: string | null
}>()

const emit = defineEmits<{
  clearSearch: []
  close: []
  closeDetails: []
  open: []
  locate: []
  resetFilters: []
  selectSearchResult: [id: string]
  'update:filters': [filters: FilterState]
  'update:search': [value: string]
}>()

const contentElement = ref<HTMLElement | null>(null)
const activeTab = ref<'info' | 'search' | 'result'>('info')
const isDragging = ref(false)
const translateY = ref(0)
const openHeight = '58dvh'
const closedHeight = '2.25rem'
let touchStartY = 0
let startScrollTop = 0
let canDragSheet = false

const formattedAddress = computed(() => props.item ? formatAddress(props.item) : null)
const formattedDate = computed(() => formatDate(props.item?.lastUpdate))
const formattedSeasonDuration = computed(() => formatSeasonDuration(props.item))
const showImage = computed(() => isValidHttpUrl(props.item?.imageUrl))
const sheetStyle = computed(() => {
  if (isDragging.value) {
    return {
      height: `max(${closedHeight}, calc(${openHeight} - ${translateY.value}px))`,
      transform: 'translateY(0)',
    }
  }

  return {
    height: props.isOpen ? openHeight : closedHeight,
    transform: 'translateY(0)',
  }
})

watch(() => props.item, (item) => {
  activeTab.value = item ? 'result' : activeTab.value === 'result' ? 'info' : activeTab.value
})

watch(activeTab, () => {
  scrollToTop()
})

function isAtTop(scrollTop: number) {
  return scrollTop <= 0
}

function isAtBottom(element: HTMLElement | null, scrollTop: number) {
  if (!element) {
    return false
  }

  const maxScrollTop = Math.max(0, element.scrollHeight - element.clientHeight)
  return scrollTop >= maxScrollTop - 1
}

function onTouchStart(event: TouchEvent) {
  const touch = event.touches[0]
  if (!touch) {
    return
  }

  touchStartY = touch.clientY
  startScrollTop = contentElement.value?.scrollTop ?? 0
  canDragSheet = props.isOpen && (
    isAtTop(startScrollTop)
    || isAtBottom(contentElement.value, startScrollTop)
  )
  isDragging.value = false
}

function onTouchMove(event: TouchEvent) {
  const touch = event.touches[0]
  if (!touch) {
    return
  }

  const deltaY = touch.clientY - touchStartY

  if (!props.isOpen) {
    if (deltaY < -24) {
      emit('open')
    }
    return
  }

  const scrollTop = contentElement.value?.scrollTop ?? 0
  if (
    !canDragSheet
    && deltaY > 0
    && (isAtTop(scrollTop) || isAtBottom(contentElement.value, scrollTop))
  ) {
    canDragSheet = true
  }

  if (!canDragSheet || deltaY <= 0) {
    translateY.value = 0
    return
  }

  isDragging.value = true
  translateY.value = deltaY
  event.preventDefault()
}

function onTouchEnd() {
  if (translateY.value > 96) {
    translateY.value = 0
    isDragging.value = false
    canDragSheet = false
    emit('close')
    return
  }

  translateY.value = 0
  isDragging.value = false
  canDragSheet = false
}

function onSheetClick() {
  if (!props.isOpen) {
    emit('open')
  }
}

function closeDetails() {
  activeTab.value = 'info'
  emit('closeDetails')
}

function setActiveTab(tab: 'info' | 'search' | 'result') {
  activeTab.value = tab
}

function scrollToTop() {
  contentElement.value?.scrollTo({ top: 0, behavior: 'auto' })
}
</script>
