<template>
  <CollectionLandingPage
    :page="landingPage"
    :items="landingItems"
    :breadcrumbs="breadcrumbs"
    :related-links="relatedLinks"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { createError, useFetch, useHead, useRoute, useRuntimeConfig, useSeoMeta } from '#imports'
import CollectionLandingPage from '../../components/seo/CollectionLandingPage.vue'
import { getLandingPath } from '../../content/landingPages'
import type { MapItemSearchResponse } from '../../types/map'
import { buildLandingJsonLd, buildLandingMeta } from '../../utils/landingSeo'
import { getLandingBySlug, getRelatedLandingLinks, selectBathingSitesForLanding } from '../../utils/landingSelectors'

const route = useRoute()
const config = useRuntimeConfig()
const siteUrl = useSiteUrl()
const slug = computed(() => {
  const raw = route.params.slug
  if (Array.isArray(raw)) {
    return raw[0] || ''
  }
  return typeof raw === 'string' ? raw : ''
})
const landingPage = computed(() => {
  const page = getLandingBySlug('collection', slug.value)
  if (!page) {
    throw createError({ statusCode: 404, statusMessage: 'Collection not found' })
  }
  return page
})

const { data } = await useFetch<MapItemSearchResponse>(`${config.public.apiBase}/api/map/v1/items`, {
  query: {
    type: 'badestelle',
    limit: 5000,
  },
  key: `landing-collection-items:${slug.value}`,
  server: true,
  lazy: false,
  default: () => ({ items: [], total: 0 }),
})

const landingItems = computed(() => selectBathingSitesForLanding(data.value?.items || [], landingPage.value))
const relatedLinks = computed(() => getRelatedLandingLinks(landingPage.value))
const canonicalUrl = computed(() => toAbsoluteUrl(getLandingPath('collection', slug.value), siteUrl))
const breadcrumbs = computed(() => [
  { label: 'Sammlungen', to: '/sammlungen' },
])

const meta = computed(() => buildLandingMeta(landingPage.value))

useSeoMeta({
  title: () => meta.value.title,
  description: () => meta.value.description,
  ogTitle: () => meta.value.ogTitle,
  ogDescription: () => meta.value.ogDescription,
  ogType: 'website',
  ogUrl: () => canonicalUrl.value,
  twitterCard: 'summary',
})

useHead({
  link: [
    {
      rel: 'canonical',
      href: canonicalUrl.value,
    },
  ],
})

useJsonLd(() => buildLandingJsonLd(
  landingPage.value,
  canonicalUrl.value,
  toAbsoluteUrl('/', siteUrl),
  [
    { label: 'Start', to: '/' },
    { label: 'Sammlungen', to: '/sammlungen' },
    { label: landingPage.value.h1, to: getLandingPath('collection', slug.value) },
  ],
  landingItems.value,
), `collection-json-ld:${slug.value}`)
</script>
