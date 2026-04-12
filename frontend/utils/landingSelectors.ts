import type { MapItem } from '../types/map'
import type { LandingFilterDefinition, LandingPageDefinition, LandingPageKind } from '../content/landingPages'
import { collectionLandingPages, getLandingPath, regionLandingPages } from '../content/landingPages'

type LandingLink = {
  label: string
  to: string
}

const TEXT_FIELDS: Array<keyof MapItem> = ['title', 'description', 'address', 'city', 'district', 'category']

function normalize(value: string | null | undefined) {
  if (!value) {
    return ''
  }

  return value
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
}

function includesAny(haystack: string, terms: string[] | undefined) {
  if (!terms?.length) {
    return false
  }

  return terms.some((term) => haystack.includes(normalize(term)))
}

function arrayIncludesAny(values: string[] | undefined, terms: string[] | undefined) {
  if (!values?.length || !terms?.length) {
    return false
  }

  const normalizedValues = values.map((value) => normalize(value)).filter(Boolean)
  const normalizedTerms = terms.map((term) => normalize(term)).filter(Boolean)
  return normalizedTerms.some((term) => normalizedValues.some((value) => value.includes(term)))
}

function matchesFilter(item: MapItem, filter: LandingFilterDefinition) {
  const city = normalize(item.city)
  const district = normalize(item.district)
  const category = normalize(item.category)
  const amenities = item.amenities || []
  const tags = item.tags || []

  const textBlob = normalize(
    [
      ...TEXT_FIELDS.map((field) => String(item[field] || '')),
      ...tags,
      ...amenities,
      item.accessibility || '',
    ].join(' '),
  )

  if (filter.cityIncludes?.length && !includesAny(city, filter.cityIncludes)) {
    return false
  }

  if (filter.districtIncludes?.length && !includesAny(district, filter.districtIncludes)) {
    return false
  }

  if (filter.categoryIncludes?.length && !includesAny(category, filter.categoryIncludes)) {
    return false
  }

  if (filter.tagIncludes?.length && !arrayIncludesAny(tags, filter.tagIncludes)) {
    return false
  }

  if (filter.amenitiesIncludes?.length && !arrayIncludesAny(amenities, filter.amenitiesIncludes)) {
    return false
  }

  if (filter.textIncludes?.length && !includesAny(textBlob, filter.textIncludes)) {
    return false
  }

  if (filter.requireAmenities) {
    const hasAmenities = amenities.length > 0 || normalize(item.accessibility).length > 0
    if (!hasAmenities) {
      return false
    }
  }

  return true
}

function sortBathingSites(items: MapItem[]) {
  return [...items].sort((a, b) => {
    const districtCmp = String(a.district || '').localeCompare(String(b.district || ''), 'de')
    if (districtCmp !== 0) {
      return districtCmp
    }

    const cityCmp = String(a.city || '').localeCompare(String(b.city || ''), 'de')
    if (cityCmp !== 0) {
      return cityCmp
    }

    return a.title.localeCompare(b.title, 'de')
  })
}

export function selectBathingSitesForLanding(items: MapItem[], page: LandingPageDefinition) {
  const bathingSites = items.filter((item) => item.type === 'badestelle')
  return sortBathingSites(bathingSites.filter((item) => matchesFilter(item, page.filter)))
}

export function getLandingBySlug(kind: LandingPageKind, slug: string) {
  if (kind === 'region') {
    return regionLandingPages.find((page) => page.slug === slug) || null
  }

  return collectionLandingPages.find((page) => page.slug === slug) || null
}

export function getRelatedLandingLinks(page: LandingPageDefinition): LandingLink[] {
  const regionLinks = (page.relatedRegions || [])
    .map((slug) => regionLandingPages.find((candidate) => candidate.slug === slug))
    .filter((candidate): candidate is LandingPageDefinition => Boolean(candidate))
    .map((candidate) => ({
      label: candidate.h1,
      to: getLandingPath('region', candidate.slug),
    }))

  const collectionLinks = (page.relatedCollections || [])
    .map((slug) => collectionLandingPages.find((candidate) => candidate.slug === slug))
    .filter((candidate): candidate is LandingPageDefinition => Boolean(candidate))
    .map((candidate) => ({
      label: candidate.h1,
      to: getLandingPath('collection', candidate.slug),
    }))

  return [...regionLinks, ...collectionLinks]
}

export function getLandingMatchesForItem(item: MapItem) {
  if (item.type !== 'badestelle') {
    return {
      regions: [] as LandingPageDefinition[],
      collections: [] as LandingPageDefinition[],
    }
  }

  const regions = regionLandingPages.filter((page) => matchesFilter(item, page.filter))
  const collections = collectionLandingPages.filter((page) => matchesFilter(item, page.filter))
  return { regions, collections }
}

export function getSimilarBathingSites(items: MapItem[], pivot: MapItem, limit = 6) {
  if (pivot.type !== 'badestelle') {
    return [] as MapItem[]
  }

  const pivotDistrict = normalize(pivot.district)
  const pivotTags = (pivot.tags || []).map((tag) => normalize(tag)).filter(Boolean)

  return items
    .filter((candidate) => candidate.type === 'badestelle' && candidate.id !== pivot.id)
    .map((candidate) => {
      let score = 0
      if (normalize(candidate.district) === pivotDistrict && pivotDistrict) {
        score += 5
      }

      const candidateTags = (candidate.tags || []).map((tag) => normalize(tag)).filter(Boolean)
      const sharedTags = candidateTags.filter((tag) => pivotTags.includes(tag)).length
      score += sharedTags

      if (normalize(candidate.city) && normalize(candidate.city) === normalize(pivot.city)) {
        score += 2
      }

      return { candidate, score }
    })
    .filter((entry) => entry.score > 0)
    .sort((a, b) => {
      if (b.score !== a.score) {
        return b.score - a.score
      }
      return a.candidate.title.localeCompare(b.candidate.title, 'de')
    })
    .slice(0, limit)
    .map((entry) => entry.candidate)
}
