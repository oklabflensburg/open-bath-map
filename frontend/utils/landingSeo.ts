import type { LandingPageDefinition } from '../content/landingPages'
import type { MapItem } from '../types/map'

interface Breadcrumb {
  label: string
  to: string
}

export function buildLandingMeta(page: LandingPageDefinition) {
  return {
    title: page.metaTitle,
    description: page.metaDescription,
    ogTitle: page.ogTitle,
    ogDescription: page.ogDescription,
  }
}

export function buildLandingJsonLd(
  page: LandingPageDefinition,
  pageUrl: string,
  websiteUrl: string,
  breadcrumbs: Breadcrumb[],
  items: MapItem[],
) {
  const breadcrumbList = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: breadcrumbs.map((breadcrumb, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: breadcrumb.label,
      item: new URL(breadcrumb.to, `${websiteUrl}/`).toString(),
    })),
  }

  const itemList = {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: page.h1,
    numberOfItems: items.length,
    itemListElement: items.slice(0, 100).map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      url: new URL(`/${item.slug}`, `${websiteUrl}/`).toString(),
      name: item.title,
    })),
  }

  const collectionPage = {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: page.h1,
    url: pageUrl,
    description: page.metaDescription,
    isPartOf: {
      '@type': 'WebSite',
      name: 'Badestellenkarte',
      url: websiteUrl,
    },
  }

  return [collectionPage, breadcrumbList, itemList]
}
