import { useRuntimeConfig } from '#imports'
import type { FilterState, MapBounds, MapFeature, MapFeatureCollection, MapItem, UserLocation } from '../types/map'

let markerRequestSequence = 0
let detailRequestSequence = 0
let pendingRequests = 0

function toQueryFilters(filters: FilterState) {
  return {
    type: filters.type === 'all' ? undefined : filters.type,
    category: filters.category || undefined,
    infrastructure: filters.infrastructure || undefined,
  }
}

function toFeatureFromItem(item: MapItem): MapFeature {
  return {
    type: 'Feature',
    id: item.id,
    geometry: {
      type: 'Point',
      coordinates: [item.lng, item.lat],
    },
    properties: {
      id: item.id,
      slug: item.slug,
      type: item.type,
      title: item.title,
      category: item.category,
      city: item.city,
      waterQuality: item.waterQuality,
    },
  }
}

export function useMapData() {
  const config = useRuntimeConfig()
  const state = useMapState()

  function beginRequest(scope: 'markers' | 'details') {
    pendingRequests += 1
    state.isLoading.value = pendingRequests > 0
    state.fetchError.value = null
    if (scope === 'markers') {
      markerRequestSequence += 1
      return markerRequestSequence
    }

    detailRequestSequence += 1
    return detailRequestSequence
  }

  function finishRequest() {
    pendingRequests = Math.max(0, pendingRequests - 1)
    state.isLoading.value = pendingRequests > 0
  }

  function applyFeatureCollection(collection: MapFeatureCollection) {
    state.currentMarkers.value = collection.features
    state.availableFilters.value = collection.filters
  }

  async function loadBounds(bounds: MapBounds) {
    const requestId = beginRequest('markers')
    state.currentBounds.value = bounds
    state.queryMode.value = 'bounds'

    try {
      const collection = await $fetch<MapFeatureCollection>(`${config.public.apiBase}/api/map/v1/bounds`, {
        query: {
          ...bounds,
          ...toQueryFilters(state.filters.value),
        },
      })

      if (requestId !== markerRequestSequence) {
        return
      }

      applyFeatureCollection(collection)
      restoreSelectionMarker()
    } catch (error) {
      if (requestId === markerRequestSequence) {
        state.fetchError.value = error instanceof Error ? error.message : 'Die Kartendaten konnten nicht geladen werden.'
      }
    } finally {
      finishRequest()
    }
  }

  async function loadRadius(location: UserLocation, radiusKm = 25) {
    const requestId = beginRequest('markers')
    state.currentUserLocation.value = location
    state.queryMode.value = 'radius'

    try {
      const collection = await $fetch<MapFeatureCollection>(`${config.public.apiBase}/api/map/v1/radius`, {
        query: {
          lat: location.lat,
          lng: location.lng,
          radius_km: radiusKm,
          ...toQueryFilters(state.filters.value),
        },
      })

      if (requestId !== markerRequestSequence) {
        return
      }

      applyFeatureCollection(collection)
      restoreSelectionMarker()
    } catch (error) {
      if (requestId === markerRequestSequence) {
        state.fetchError.value = error instanceof Error ? error.message : 'Die Radius-Abfrage ist fehlgeschlagen.'
      }
    } finally {
      finishRequest()
    }
  }

  async function loadDetailsById(id: string) {
    return await loadDetails({ id })
  }

  async function loadDetailsBySlug(slug: string) {
    return await loadDetails({ slug })
  }

  async function loadDetails(query: { id?: string, slug?: string }) {
    const requestId = beginRequest('details')

    try {
      const item = await $fetch<MapItem>(`${config.public.apiBase}/api/map/v1/details`, { query })
      if (requestId !== detailRequestSequence) {
        return null
      }

      state.setSelectedItem(item)
      upsertSelectedMarker(item)
      return item
    } catch (error) {
      if (requestId === detailRequestSequence) {
        state.fetchError.value = error instanceof Error ? error.message : 'Die Detaildaten konnten nicht geladen werden.'
      }
      return null
    } finally {
      finishRequest()
    }
  }

  function upsertSelectedMarker(item: MapItem) {
    const nextFeature = toFeatureFromItem(item)
    const existing = state.currentMarkers.value.find((feature) => feature.id === item.id)
    if (existing) {
      return
    }

    state.currentMarkers.value = [nextFeature, ...state.currentMarkers.value]
  }

  function restoreSelectionMarker() {
    if (!state.selectedItem.value) {
      return
    }

    upsertSelectedMarker(state.selectedItem.value)
  }

  return {
    loadBounds,
    loadRadius,
    loadDetailsById,
    loadDetailsBySlug,
    upsertSelectedMarker,
  }
}
