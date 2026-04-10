import { computed } from 'vue'
import { useHead, useRuntimeConfig } from '#imports'

type JsonLdNode = Record<string, unknown>
type JsonLdValue = JsonLdNode | JsonLdNode[] | null

export function useJsonLd(schema: () => JsonLdValue, key = 'json-ld') {
  const scripts = computed(() => {
    const value = schema()
    if (!value) {
      return []
    }

    return [
      {
        key,
        type: 'application/ld+json',
        innerHTML: JSON.stringify(value),
      },
    ]
  })

  useHead({
    script: scripts,
  })
}

export function useSiteUrl() {
  const config = useRuntimeConfig()
  const configuredSiteUrl = config.public.siteUrl?.trim()
  return (configuredSiteUrl || 'http://localhost:3000').replace(/\/+$/u, '')
}

export function toAbsoluteUrl(path: string, siteUrl = useSiteUrl()) {
  return new URL(path, `${siteUrl}/`).toString()
}
