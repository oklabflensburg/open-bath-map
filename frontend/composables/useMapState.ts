import { useState } from '#imports'
import type { FilterState, MapBounds, MapFeature, MapFilterOptions, MapItem, UserLocation } from '../types/map'

const defaultFilters = (): FilterState => ({
  type: 'badestelle',
  category: '',
  infrastructure: '',
})

const defaultFilterOptions = (): MapFilterOptions => ({
  types: ['badestelle', 'poi'],
  categories: [],
  cities: [],
  tags: [],
  infrastructures: [],
})

export function useMapState() {
  const selectedItem = useState<MapItem | null>('map:selected-item', () => null)
  const selectedSlug = useState<string | null>('map:selected-slug', () => null)
  const currentMarkers = useState<MapFeature[]>('map:current-markers', () => [])
  const currentBounds = useState<MapBounds | null>('map:current-bounds', () => null)
  const currentUserLocation = useState<UserLocation | null>('map:user-location', () => null)
  const filters = useState<FilterState>('map:filters', defaultFilters)
  const availableFilters = useState<MapFilterOptions>('map:available-filters', defaultFilterOptions)
  const isSidebarOpen = useState<boolean>('map:sidebar-open', () => false)
  const isBottomSheetOpen = useState<boolean>('map:bottomsheet-open', () => true)
  const isLoading = useState<boolean>('map:is-loading', () => false)
  const fetchError = useState<string | null>('map:fetch-error', () => null)
  const queryMode = useState<'bounds' | 'radius'>('map:query-mode', () => 'bounds')

  function setSelectedItem(item: MapItem | null) {
    selectedItem.value = item
    selectedSlug.value = item?.slug ?? null
    isSidebarOpen.value = !!item
    isBottomSheetOpen.value = true
  }

  function clearSelection() {
    setSelectedItem(null)
  }

  function openBottomSheet() {
    isBottomSheetOpen.value = true
  }

  function closeBottomSheet() {
    isBottomSheetOpen.value = false
  }

  return {
    selectedItem,
    selectedSlug,
    currentMarkers,
    currentBounds,
    currentUserLocation,
    filters,
    availableFilters,
    isSidebarOpen,
    isBottomSheetOpen,
    isLoading,
    fetchError,
    queryMode,
    setSelectedItem,
    clearSelection,
    openBottomSheet,
    closeBottomSheet,
  }
}
