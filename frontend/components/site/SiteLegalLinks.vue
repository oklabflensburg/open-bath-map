<template>
  <nav
    aria-label="Rechtliche Seiten"
    class="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-400 sm:gap-x-4 sm:gap-y-2 sm:text-sm sm:text-slate-600"
  >
    <NuxtLink
      v-for="link in links"
      :key="link.to"
      :to="link.to"
      class="transition hover:text-slate-700 sm:hover:text-slate-900"
      :class="route.path === link.to ? 'font-medium text-slate-600 sm:font-semibold sm:text-slate-900' : ''"
    >
      {{ link.label }}
    </NuxtLink>
  </nav>
</template>

<script setup lang="ts">
import { useRoute } from '#imports'

const route = useRoute()

const links = [
  { to: '/', label: 'Karte' },
  { to: '/impressum', label: 'Impressum' },
  { to: '/datenschutz', label: 'Datenschutz' },
]
</script>
