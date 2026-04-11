export type MapItemType = 'badestelle' | 'poi'

export interface MapItem {
  id: string
  slug: string
  type: MapItemType
  title: string
  description?: string | null
  category?: string | null
  lat: number
  lng: number
  address?: string | null
  postcode?: string | null
  city?: string | null
  municipality?: string | null
  imageUrl?: string | null
  website?: string | null
  wikipediaUrl?: string | null
  wikipediaTitle?: string | null
  wikipediaSummary?: string | null
  wikidataId?: string | null
  wikidataUrl?: string | null
  sourceName?: string | null
  contentLicense?: string | null
  tags: string[]
  waterQuality?: string | null
  accessibility?: string | null
  possiblePollutions?: string | null
  seasonalStatus?: string | null
  seasonStart?: string | null
  seasonEnd?: string | null
  lastUpdate?: string | null
  district?: string | null
  openingHours?: string | null
  amenities: string[]
  distanceKm?: number | null
}

export interface MapFeatureProperties {
  id: string
  slug: string
  type: MapItemType
  title: string
  category?: string | null
  city?: string | null
  waterQuality?: string | null
}

export interface MapFeature {
  type: 'Feature'
  id: string
  geometry: {
    type: 'Point'
    coordinates: [number, number]
  }
  properties: MapFeatureProperties
}

export interface MapFilterOptions {
  types: MapItemType[]
  categories: string[]
  cities: string[]
  tags: string[]
  infrastructures: string[]
}

export interface MapFeatureCollection {
  type: 'FeatureCollection'
  features: MapFeature[]
  filters: MapFilterOptions
  total: number
}

export interface MapItemSearchResponse {
  items: MapItem[]
  total: number
}

export interface MapBounds {
  xmin: number
  ymin: number
  xmax: number
  ymax: number
}

export interface UserLocation {
  lat: number
  lng: number
}

export interface FilterState {
  type: 'all' | MapItemType
  category: string
  infrastructure: string
}
