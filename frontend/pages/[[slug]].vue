<template>
  <MapExperience />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useFetch, useRoute, useRuntimeConfig, useSeoMeta } from '#imports'
import type { MapItem } from '../types/map'
import { buildMetaDescription, buildMetaTitle } from '../utils/formatters'

const route = useRoute()
const config = useRuntimeConfig()
const state = useMapState()
const slug = computed(() => typeof route.params.slug === 'string' ? route.params.slug : '')
const ssrItem = ref<MapItem | null>(null)

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
})
</script>
