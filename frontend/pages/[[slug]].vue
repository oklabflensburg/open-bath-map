<template>
  <MapExperience />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useFetch, useRoute, useRuntimeConfig, useSeoMeta } from '#imports'
import type { MapItem } from '../types/map'
import { buildMetaDescription, buildMetaTitle } from '../utils/formatters'

const route = useRoute()
const config = useRuntimeConfig()
const slug = computed(() => typeof route.params.slug === 'string' ? route.params.slug : '')

const { data } = await useFetch<MapItem>(`${config.public.apiBase}/api/map/v1/details`, {
  query: computed(() => ({ slug: slug.value || undefined })),
  key: computed(() => `detail-meta:${slug.value || 'home'}`),
  server: true,
  lazy: false,
  default: () => null,
})

useSeoMeta({
  title: () => buildMetaTitle(data.value),
  ogTitle: () => buildMetaTitle(data.value),
  description: () => buildMetaDescription(data.value),
  ogDescription: () => buildMetaDescription(data.value),
})
</script>
