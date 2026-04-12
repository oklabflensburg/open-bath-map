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

export function formatMeasurementValue(value?: number | null, unit = '') {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return null
  }

  const formatter = Number.isInteger(value)
    ? new Intl.NumberFormat('de-DE', { maximumFractionDigits: 0 })
    : new Intl.NumberFormat('de-DE', { minimumFractionDigits: 1, maximumFractionDigits: 2 })
  const suffix = unit ? ` ${unit}` : ''
  return `${formatter.format(value)}${suffix}`
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
    return 'Badestellen in Schleswig-Holstein - Karte, Infos und Wasserqualitaet'
  }

  const location = item.city || item.district || 'Schleswig-Holstein'
  if (item.type === 'badestelle') {
    return `${item.title} in ${location} - Infos, Lage und Wasserqualitaet`
  }
  return `${item.title} in ${location} - Lage und Detailinformationen`
}

export function buildMetaDescription(item?: MapItem | null) {
  if (!item) {
    return 'Interaktive Karte fuer Badestellen in Schleswig-Holstein mit Detailseiten, Filtern und datenbasierten Informationen aus offenen Quellen.'
  }

  const location = item.city || item.district || 'Schleswig-Holstein'
  const typeLabel = item.type === 'badestelle' ? 'Badestelle' : 'Ort'
  return item.description
    || `${typeLabel} in ${location} mit Kartenlage, Detaildaten und weiterfuehrenden Informationen.`
}
