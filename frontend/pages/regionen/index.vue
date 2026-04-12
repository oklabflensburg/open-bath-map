<template>
  <main class="min-h-screen bg-slate-50">
    <div class="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-6 md:px-6 md:py-10">
      <Breadcrumbs :items="[]" current-label="Regionen" />

      <LandingPageHero
        eyebrow="Regionenuebersicht"
        title="Regionen mit Badestellen in Schleswig-Holstein"
        subtitle="Regionale Landingpages mit indexierbaren Uebersichten, Detaillinks und transparenter Datengrundlage."
      />

      <SeoIntroBlock :paragraphs="intro" />

      <section class="rounded-2xl border border-slate-200 bg-white p-4 md:p-6">
        <h2 class="text-lg font-semibold text-slate-900">Alle Regionen</h2>
        <ul class="mt-3 grid gap-2 md:grid-cols-2">
          <li v-for="page in regionLandingPages" :key="page.slug">
            <NuxtLink :to="`/regionen/${page.slug}`" class="inline-flex rounded-lg px-3 py-2 text-sm text-sky-800 transition hover:bg-sky-50 hover:text-sky-900">
              {{ page.h1 }}
            </NuxtLink>
          </li>
        </ul>
      </section>

      <section class="rounded-2xl border border-slate-200 bg-white p-4 md:p-6">
        <NuxtLink class="inline-flex rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700" to="/sammlungen">
          Zu den Sammlungen
        </NuxtLink>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useHead, useRoute, useSeoMeta } from '#imports'
import { regionLandingPages } from '../../content/landingPages'

const route = useRoute()
const siteUrl = useSiteUrl()
const pageUrl = computed(() => toAbsoluteUrl(route.path || '/regionen', siteUrl))

const intro = [
  'Diese Uebersichtsseite verlinkt regionale Landingpages fuer ausgewaehlte Orte und Gewaesserraeume in Schleswig-Holstein.',
  'Jede Regionenseite zeigt die dazu passenden Badestellen aus den vorhandenen Datenfeldern und fuehrt direkt zu den Detailseiten.',
]

useSeoMeta({
  title: 'Regionen mit Badestellen in Schleswig-Holstein',
  description: 'Indexierbare Regionen-Seiten fuer Badestellen in Schleswig-Holstein mit Karte, Detaillinks und datenbasierter Auswahl.',
  ogTitle: 'Regionen mit Badestellen in Schleswig-Holstein',
  ogDescription: 'Regionale Einstiegsseiten zu Badestellen in Schleswig-Holstein.',
  ogType: 'website',
  ogUrl: pageUrl,
  twitterCard: 'summary',
})

useHead({
  link: [
    {
      rel: 'canonical',
      href: pageUrl.value,
    },
  ],
})

useJsonLd(() => ({
  '@context': 'https://schema.org',
  '@type': 'CollectionPage',
  name: 'Regionen mit Badestellen in Schleswig-Holstein',
  url: pageUrl.value,
  description: 'Uebersicht regionaler Landingpages fuer Badestellen in Schleswig-Holstein.',
}))
</script>
