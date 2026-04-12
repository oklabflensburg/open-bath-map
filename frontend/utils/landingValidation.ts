import type { LandingPageDefinition } from '../content/landingPages'

interface LandingConfig {
  regionLandingPages: LandingPageDefinition[]
  collectionLandingPages: LandingPageDefinition[]
}

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) {
    throw new Error(`LandingPageConfig: ${message}`)
  }
}

export function assertLandingPageConfig(config: LandingConfig) {
  const all = [...config.regionLandingPages, ...config.collectionLandingPages]
  const seen = new Set<string>()

  for (const page of all) {
    assert(page.slug === page.slug.toLowerCase(), `Slug must be lowercase: ${page.slug}`)
    assert(/^[a-z0-9-]+$/u.test(page.slug), `Slug must be url-safe: ${page.slug}`)
    assert(page.introParagraphs.length >= 1, `Intro is required for ${page.kind}:${page.slug}`)
    assert(page.metaTitle.trim().length > 10, `metaTitle missing for ${page.kind}:${page.slug}`)
    assert(page.metaDescription.trim().length > 20, `metaDescription missing for ${page.kind}:${page.slug}`)
    assert(page.ogTitle.trim().length > 5, `ogTitle missing for ${page.kind}:${page.slug}`)
    assert(page.ogDescription.trim().length > 20, `ogDescription missing for ${page.kind}:${page.slug}`)

    const key = `${page.kind}:${page.slug}`
    assert(!seen.has(key), `Duplicate key ${key}`)
    seen.add(key)
  }

  const regionSlugs = new Set(config.regionLandingPages.map((page) => page.slug))
  const collectionSlugs = new Set(config.collectionLandingPages.map((page) => page.slug))

  for (const page of all) {
    for (const relatedSlug of page.relatedRegions || []) {
      assert(regionSlugs.has(relatedSlug), `Unknown related region '${relatedSlug}' on ${page.kind}:${page.slug}`)
    }

    for (const relatedSlug of page.relatedCollections || []) {
      assert(collectionSlugs.has(relatedSlug), `Unknown related collection '${relatedSlug}' on ${page.kind}:${page.slug}`)
    }
  }
}
