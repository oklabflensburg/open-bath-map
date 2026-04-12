<template>
  <LandingPageTemplate
    eyebrow="Regionenseite"
    :page="page"
    :items="items"
    :breadcrumbs="breadcrumbs"
    :related-links="relatedLinks"
    type-label="Region"
    source-hint="Open Data Schleswig-Holstein"
  />
</template>

<script setup lang="ts">
import LandingPageTemplate from './LandingPageTemplate.vue'
import type { LandingPageDefinition } from '../../content/landingPages'
import type { MapItem } from '../../types/map'

interface BreadcrumbItem {
  label: string
  to: string
}

interface RelatedLink {
  label: string
  to: string
}

defineProps<{
  page: LandingPageDefinition
  items: MapItem[]
  breadcrumbs: BreadcrumbItem[]
  relatedLinks: RelatedLink[]
}>()
</script>
