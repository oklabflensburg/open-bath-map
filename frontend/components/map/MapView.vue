<template>
  <div class="relative h-full min-h-0 w-full">
    <div ref="mapElement" class="h-full w-full" />
    <div v-if="isLoading" class="pointer-events-none absolute left-4 top-4 z-[950] rounded-full bg-white/95 px-3 py-2 text-sm text-slate-700 shadow">
      Karte wird aktualisiert
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { MapFeature, MapItem, UserLocation } from '../../types/map'

declare global {
  interface Window {
    L?: any
  }
}

const props = defineProps<{
  features: MapFeature[]
  selectedItemId?: string | null
  userLocation?: UserLocation | null
  isLoading?: boolean
}>()

const emit = defineEmits<{
  'bounds-change': [bounds: { xmin: number, ymin: number, xmax: number, ymax: number }]
  'marker-select': [id: string]
  'map-click': []
  ready: []
}>()

const mapElement = ref<HTMLElement | null>(null)
const markerIndex = new Map<string, any>()

let LRef: typeof import('leaflet') | null = null
let map: any = null
let zoomControl: any = null
let clusterGroup: any = null
let selectedMarker: any = null
let userMarker: any = null
let resizeObserver: ResizeObserver | null = null
let suppressedMoveendCount = 0
let lastEmittedBoundsKey: string | null = null
let suppressBoundsUntil = 0

function getLeafletModule(module: any) {
  return (module?.default ?? module) as any
}

function createMarkerIcon(type: MapFeature['properties']['type'], active = false) {
  const tone = type === 'badestelle' ? 'is-badestelle' : 'is-poi'
  const state = active ? 'is-active' : ''

  return LRef!.divIcon({
    className: '',
    html: `<span class="map-marker ${tone} ${state}"></span>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    tooltipAnchor: [0, -16],
  })
}

function resetSelectedMarker() {
  if (!selectedMarker) {
    return
  }

  const feature = selectedMarker.feature as MapFeature | undefined
  if (feature && selectedMarker._map && selectedMarker._icon?.parentNode) {
    try {
      selectedMarker.setIcon(createMarkerIcon(feature.properties.type, false))
    } catch {
      // MarkerCluster/Leaflet can briefly hold stale marker DOM during fast updates.
    }
  }
  selectedMarker = null
}

function setSelectedMarker(marker: any) {
  if (!marker) {
    return
  }

  resetSelectedMarker()
  const feature = marker.feature as MapFeature
  if (feature && marker._map && marker._icon?.parentNode) {
    try {
      marker.setIcon(createMarkerIcon(feature.properties.type, true))
    } catch {
      return
    }
  }
  selectedMarker = marker
}

function syncMarkers() {
  if (!LRef || !map) {
    return
  }

  map?.stop?.()
  resetSelectedMarker()
  markerIndex.clear()
  if (clusterGroup) {
    map.removeLayer(clusterGroup)
  }
  clusterGroup = createClusterGroup()
  map.addLayer(clusterGroup)

  props.features.forEach((feature) => {
    const [lng, lat] = feature.geometry.coordinates
    const marker = LRef!.marker([lat, lng], {
      icon: createMarkerIcon(feature.properties.type, feature.id === props.selectedItemId),
    })
      .bindTooltip(feature.properties.title, { direction: 'top' })
      .on('click', (event: any) => {
        LRef?.DomEvent.stopPropagation(event)
        emit('marker-select', feature.id)
      })

    marker.feature = feature
    markerIndex.set(feature.id, marker)
    clusterGroup.addLayer(marker)

    if (feature.id === props.selectedItemId) {
      selectedMarker = marker
    }
  })
}

function createClusterGroup() {
  return LRef!.markerClusterGroup({
    zoomToBoundsOnClick: true,
    showCoverageOnHover: false,
    disableClusteringAtZoom: 14,
    maxClusterRadius: 48,
    animate: false,
    animateAddingMarkers: false,
  })
}

function emitBounds() {
  if (!map) {
    return
  }

  const bounds = map.getBounds()
  const nextBounds = {
    xmin: bounds.getWest(),
    ymin: bounds.getSouth(),
    xmax: bounds.getEast(),
    ymax: bounds.getNorth(),
  }
  const boundsKey = `${nextBounds.xmin}:${nextBounds.ymin}:${nextBounds.xmax}:${nextBounds.ymax}`

  if (suppressedMoveendCount > 0 || Date.now() < suppressBoundsUntil) {
    suppressedMoveendCount -= 1
    lastEmittedBoundsKey = boundsKey
    return
  }

  if (boundsKey === lastEmittedBoundsKey) {
    return
  }

  lastEmittedBoundsKey = boundsKey
  emit('bounds-change', nextBounds)
}

function updateZoomControl() {
  if (!map || !LRef) {
    return
  }

  if (zoomControl) {
    map.removeControl(zoomControl)
  }

  zoomControl = LRef.control.zoom({
    position: window.innerWidth >= 1024 ? 'topleft' : 'bottomright',
  }).addTo(map)
}

function updateUserLocationMarker() {
  if (!LRef || !map) {
    return
  }

  if (userMarker) {
    userMarker.remove()
    userMarker = null
  }

  if (!props.userLocation) {
    return
  }

  userMarker = LRef.circleMarker([props.userLocation.lat, props.userLocation.lng], {
    radius: 8,
    weight: 3,
    color: '#ffffff',
    fillColor: '#0f172a',
    fillOpacity: 1,
  }).addTo(map)
}

async function initializeMap() {
  if (!mapElement.value || map) {
    return
  }

  const leafletModule = await import('leaflet')
  const leaflet = getLeafletModule(leafletModule)
  window.L = leaflet
  await import('leaflet.markercluster')
  LRef = leaflet

  map = leaflet.map(mapElement.value, { zoomControl: false }).setView([54.35, 10.1], 8)

  leaflet.tileLayer('https://tiles.oklabflensburg.de/gosm/{z}/{x}/{y}.png', {
    maxZoom: 20,
    attribution:
      '© OpenStreetMap-Mitwirkende | Badestellen-Daten: <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noreferrer">CC BY 4.0</a> (Sozialministerium S-H)',
  }).addTo(map)

  clusterGroup = createClusterGroup()

  map.addLayer(clusterGroup)
  map.on('moveend', emitBounds)
  map.on('click', () => emit('map-click'))

  updateZoomControl()
  syncMarkers()
  updateUserLocationMarker()
  emitBounds()
  emit('ready')

  window.addEventListener('resize', handleResize)
  resizeObserver = new ResizeObserver(() => {
    map?.invalidateSize()
  })
  resizeObserver.observe(mapElement.value)
  requestAnimationFrame(() => map?.invalidateSize())
}

function handleResize() {
  updateZoomControl()
  map?.invalidateSize()
}

function focusItem(item: MapItem, zoom = 17) {
  if (!map) {
    return
  }

  const marker = markerIndex.get(item.id)
  if (marker) {
    setSelectedMarker(marker)
  }

  const targetZoom = Math.max(map.getZoom(), zoom)
  suppressedMoveendCount += 1
  suppressBoundsUntil = Date.now() + 900
  if (map.getZoom() === targetZoom) {
    map.panTo([item.lat, item.lng], {
      animate: true,
      duration: 0.35,
    })
    return
  }

  map.setView([item.lat, item.lng], targetZoom, {
    animate: true,
  })
}

function centerOnLocation(location: UserLocation, zoom = 12) {
  const targetZoom = Math.max(map?.getZoom?.() ?? zoom, zoom)
  suppressedMoveendCount += 1
  suppressBoundsUntil = Date.now() + 900
  if (!map) {
    return
  }

  if (map.getZoom() === targetZoom) {
    map.panTo([location.lat, location.lng], {
      animate: true,
      duration: 0.35,
    })
    return
  }

  map.setView([location.lat, location.lng], targetZoom, {
    animate: true,
  })
}

watch(() => props.features, syncMarkers, { deep: true })

watch(() => props.selectedItemId, (selectedId) => {
  if (!selectedId) {
    resetSelectedMarker()
    return
  }

  const marker = markerIndex.get(selectedId)
  if (marker) {
    setSelectedMarker(marker)
  }
})

watch(() => props.userLocation, updateUserLocationMarker, { deep: true })

onMounted(initializeMap)

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  resizeObserver?.disconnect()
  map?.remove()
})

defineExpose({
  focusItem,
  centerOnLocation,
})
</script>
