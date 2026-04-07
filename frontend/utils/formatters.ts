import type { MapItem, MapItemType } from '../types/map'

export function formatDate(value?: string | null) {
  if (!value) {
    return null
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return null
  }

  return new Intl.DateTimeFormat('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(date)
}

export function formatSeasonDuration(item?: MapItem | null) {
  if (!item) {
    return null
  }

  const start = formatDate(item.seasonStart)
  const end = formatDate(item.seasonEnd)
  if (start && end) {
    return `${start} bis ${end}`
  }

  if (start) {
    return `ab ${start}`
  }

  if (end) {
    return `bis ${end}`
  }

  return item.seasonalStatus || null
}

export function formatAddress(item: MapItem) {
  return [item.address, [item.postcode, item.city].filter(Boolean).join(' ')].filter(Boolean).join(', ')
}

export function isValidHttpUrl(value?: string | null) {
  if (!value) {
    return false
  }

  try {
    const url = new URL(value)
    return url.protocol === 'http:' || url.protocol === 'https:'
  } catch {
    return false
  }
}

export function labelForType(type: MapItemType) {
  return type === 'badestelle' ? 'Badestelle' : 'POI'
}

export function buildMetaTitle(item?: MapItem | null) {
  if (!item) {
    return 'Badestellen und POIs in Schleswig-Holstein'
  }

  return `${item.title} | Badestellen und POIs`
}

export function buildMetaDescription(item?: MapItem | null) {
  if (!item) {
    return 'Interaktive Karte für Badestellen und wassernahe POIs in Schleswig-Holstein mit automatischem Nachladen beim Bewegen der Karte.'
  }

  return item.description
    || `${labelForType(item.type)} in ${item.city || 'Schleswig-Holstein'} mit Detailansicht auf der interaktiven Karte.`
}
