export interface SiteCoordinates {
  lat: number
  lon: number
}

export interface BathingSite {
  id: string
  name: string
  shortName?: string | null
  commonName?: string | null
  municipality?: string | null
  district?: string | null
  region?: string | null
  waterCategory?: string | null
  coastalWater?: string | null
  bathingWaterType?: string | null
  bathingSpotLengthM?: number | null
  description?: string | null
  bathingSpotInformation?: string | null
  impactsOnBathingWater?: string | null
  possiblePollutions?: string | null
  infrastructure: string[]
  waterQuality?: string | null
  waterQualityFromYear?: number | null
  waterQualityToYear?: number | null
  seasonalStatus?: string | null
  seasonStart?: string | null
  seasonEnd?: string | null
  lastSampleDate?: string | null
  sourceUrl: string
  sourceDataset: string
  coordinates: SiteCoordinates
  distanceKm?: number | null
}

export interface FilterOptions {
  districts: string[]
  municipalities: string[]
  waterCategories: string[]
  coastalWaters: string[]
  bathingWaterTypes: string[]
  waterQualities: string[]
  infrastructures: string[]
}

export interface BathingSiteListResponse {
  items: BathingSite[]
  total: number
  filterOptions: FilterOptions
  dataUpdatedAt: string
}

export interface HealthResponse {
  status: string
  cacheAgeSeconds: number | null
  cachedAt: string | null
  sourceUrls: Record<string, string>
  itemCount: number
}
