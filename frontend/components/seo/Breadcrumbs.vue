<template>
  <nav aria-label="Breadcrumb" class="text-sm text-slate-600">
    <ol class="flex flex-wrap items-center gap-2">
      <li>
        <NuxtLink class="hover:text-slate-900" to="/">Start</NuxtLink>
      </li>
      <li v-for="(crumb, index) in items" :key="`${crumb.to}-${index}`" class="flex items-center gap-2">
        <span aria-hidden="true" class="text-slate-400">/</span>
        <NuxtLink class="hover:text-slate-900" :to="crumb.to">{{ crumb.label }}</NuxtLink>
      </li>
      <li v-if="currentLabel" class="flex items-center gap-2">
        <span aria-hidden="true" class="text-slate-400">/</span>
        <span class="font-medium text-slate-900">{{ currentLabel }}</span>
      </li>
    </ol>
  </nav>
</template>

<script setup lang="ts">
interface BreadcrumbItem {
  label: string
  to: string
}

defineProps<{
  items: BreadcrumbItem[]
  currentLabel?: string
}>()
</script>
