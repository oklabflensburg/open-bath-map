<template>
  <MapExperience />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useFetch, useRoute, useRuntimeConfig, useSeoMeta } from '#imports'
import type { MapItem } from '../types/map'
import { buildMetaDescription, buildMetaTitle, formatAddress, isValidHttpUrl } from '../utils/formatters'

const route = useRoute()
const config = useRuntimeConfig()
const state = useMapState()
const siteUrl = useSiteUrl()
const slug = computed(() => typeof route.params.slug === 'string' ? route.params.slug : '')
const ssrItem = ref<MapItem | null>(null)
const websiteUrl = toAbsoluteUrl('/', siteUrl)
const pageUrl = computed(() => toAbsoluteUrl(route.path || '/', siteUrl))

definePageMeta({
  key: 'map',
})

if (import.meta.server && slug.value) {
  const { data } = await useFetch<MapItem>(`${config.public.apiBase}/api/map/v1/details`, {
    query: { slug: slug.value },
    key: `detail-meta:${slug.value}`,
    server: true,
    lazy: false,
    default: () => null,
  })
  ssrItem.value = data.value
}

const seoItem = computed(() => state.selectedItem.value ?? ssrItem.value)

useSeoMeta({
  title: () => buildMetaTitle(seoItem.value),
  ogTitle: () => buildMetaTitle(seoItem.value),
  description: () => buildMetaDescription(seoItem.value),
  ogDescription: () => buildMetaDescription(seoItem.value),
  ogImage: () => seoItem.value?.imageUrl || undefined,
  twitterCard: () => seoItem.value?.imageUrl ? 'summary_large_image' : 'summary',
  twitterImage: () => seoItem.value?.imageUrl || undefined,
})

useJsonLd(() => {
  const item = seoItem.value
  const sameAs = item
    ? [item.website, item.wikipediaUrl, item.wikidataUrl].filter(isValidHttpUrl)
    : []
  const baseSchema = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'Badestellenkarte',
    url: websiteUrl,
    description: 'Interaktive Karte für Badestellen und wassernahe POIs in Schleswig-Holstein.',
    inLanguage: 'de-DE',
  }

  if (!item) {
    return [
      baseSchema,
      {
        '@context': 'https://schema.org',
        '@type': 'CollectionPage',
        name: 'Badestellen und POIs in Schleswig-Holstein',
        url: pageUrl.value,
        description: buildMetaDescription(null),
        isPartOf: {
          '@type': 'WebSite',
          name: 'Badestellenkarte',
          url: websiteUrl,
        },
      },
    ]
  }

  const schemaType = item.type === 'badestelle' ? 'TouristAttraction' : 'Place'

  return [
    baseSchema,
    {
      '@context': 'https://schema.org',
      '@type': 'WebPage',
      name: buildMetaTitle(item),
      url: pageUrl.value,
      description: buildMetaDescription(item),
      image: item.imageUrl || undefined,
      primaryImageOfPage: item.imageUrl
        ? {
            '@type': 'ImageObject',
            url: item.imageUrl,
          }
        : undefined,
      isPartOf: {
        '@type': 'WebSite',
        name: 'Badestellenkarte',
        url: websiteUrl,
      },
      about: {
        '@type': schemaType,
        name: item.title,
        url: pageUrl.value,
      },
    },
    {
      '@context': 'https://schema.org',
      '@type': schemaType,
      name: item.title,
      url: pageUrl.value,
      description: buildMetaDescription(item),
      image: item.imageUrl || undefined,
      sameAs: sameAs.length ? sameAs : undefined,
      touristType: item.type === 'badestelle' ? 'Badegäste' : undefined,
      additionalType: item.type === 'badestelle' ? 'https://schema.org/Beach' : undefined,
      keywords: item.amenities.length || item.tags.length ? [...item.amenities, ...item.tags].join(', ') : undefined,
      containedInPlace: item.city || item.district
        ? {
            '@type': 'AdministrativeArea',
            name: [item.city, item.district].filter(Boolean).join(', '),
          }
        : undefined,
      address: formatAddress(item)
        ? {
            '@type': 'PostalAddress',
            streetAddress: item.address || undefined,
            postalCode: item.postcode || undefined,
            addressLocality: item.city || undefined,
            addressCountry: 'DE',
          }
        : undefined,
      geo: {
        '@type': 'GeoCoordinates',
        latitude: item.lat,
        longitude: item.lng,
      },
      isPartOf: {
        '@type': 'WebSite',
        name: 'Badestellenkarte',
        url: websiteUrl,
      },
    },
  ]
}, 'route-json-ld')
</script>
