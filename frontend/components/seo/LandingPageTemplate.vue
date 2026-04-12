<template>
  <main class="min-h-screen bg-slate-50">
    <div class="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-6 md:px-6 md:py-10">
      <Breadcrumbs :items="breadcrumbs" :current-label="page.h1" />

      <LandingPageHero
        :eyebrow="eyebrow"
        :title="page.h1"
        :subtitle="page.metaDescription"
      />

      <SeoIntroBlock :paragraphs="page.introParagraphs" />
      <SeoIntroBlock v-if="page.secondaryIntroParagraphs?.length" :paragraphs="page.secondaryIntroParagraphs" />

      <LandingPageStats
        :count="items.length"
        :source-hint="sourceHint"
        :type-label="typeLabel"
      />

      <section class="rounded-2xl border border-slate-200 bg-white p-4 md:p-6">
        <h2 class="text-lg font-semibold text-slate-900">Auswahllogik</h2>
        <p class="mt-2 text-sm leading-6 text-slate-700">{{ page.selectionLogicText }}</p>
      </section>

      <BathingSiteList :items="items" />

      <RelatedLandingLinks :links="relatedLinks" />

      <section class="rounded-2xl border border-slate-200 bg-white p-4 md:p-6">
        <NuxtLink class="inline-flex rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700" to="/">
          Zur interaktiven Karte
        </NuxtLink>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import BathingSiteList from './BathingSiteList.vue'
import Breadcrumbs from './Breadcrumbs.vue'
import LandingPageHero from './LandingPageHero.vue'
import LandingPageStats from './LandingPageStats.vue'
import RelatedLandingLinks from './RelatedLandingLinks.vue'
import SeoIntroBlock from './SeoIntroBlock.vue'
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
  eyebrow: string
  typeLabel: string
  sourceHint: string
  page: LandingPageDefinition
  items: MapItem[]
  breadcrumbs: BreadcrumbItem[]
  relatedLinks: RelatedLink[]
}>()
</script>
