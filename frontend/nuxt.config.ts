import { resolve } from 'node:path'
import process from 'node:process'
import { fileURLToPath } from 'node:url'

const rootEnvPath = resolve(fileURLToPath(new URL('..', import.meta.url)), '.env')
process.loadEnvFile(rootEnvPath)

export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  devtools: { enabled: false },
  experimental: {
    appManifest: false,
  },
  modules: ['@nuxtjs/tailwindcss'],
  css: [
    '~/assets/css/main.css',
    'leaflet/dist/leaflet.css',
    'leaflet.markercluster/dist/MarkerCluster.css',
    'leaflet.markercluster/dist/MarkerCluster.Default.css',
  ],
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE,
      siteUrl: process.env.NUXT_PUBLIC_SITE_URL,
    },
  },
  app: {
    head: {
      title: 'Badestellen und POIs in Schleswig-Holstein',
      meta: [
        {
          name: 'description',
          content:
            'Interaktive Karte für Badestellen und wassernahe POIs in Schleswig-Holstein.',
        },
        { name: 'theme-color', content: '#111827' },
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
        { rel: 'preconnect', href: 'https://tiles.oklabflensburg.de/gosm' },
      ],
    },
  },
  typescript: {
    strict: true,
    typeCheck: false,
  },
})
