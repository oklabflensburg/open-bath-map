import { ref } from 'vue'
import type { UserLocation } from '../types/map'

export function useGeolocation() {
  const isLocating = ref(false)
  const locationError = ref<string | null>(null)

  async function requestLocation(): Promise<UserLocation | null> {
    if (!import.meta.client || !navigator.geolocation) {
      locationError.value = 'Geolocation wird in diesem Browser nicht unterstützt.'
      return null
    }

    isLocating.value = true
    locationError.value = null

    try {
      return await new Promise((resolve) => {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            resolve({
              lat: position.coords.latitude,
              lng: position.coords.longitude,
            })
          },
          (error) => {
            locationError.value = error.message || 'Standort konnte nicht ermittelt werden.'
            resolve(null)
          },
          {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 60000,
          },
        )
      })
    } finally {
      isLocating.value = false
    }
  }

  return {
    isLocating,
    locationError,
    requestLocation,
  }
}
