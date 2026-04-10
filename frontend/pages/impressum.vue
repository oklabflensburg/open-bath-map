<template>
  <SiteLegalPage title="Impressum">
    <h2>Anbieter</h2>
    <p>
      {{ config.public.addressName }}<br>
      {{ fullStreetAddress }}<br>
      {{ fullCityLine }}<br>
      Deutschland
    </p>

    <h2>Kontakt</h2>
    <p>
      E-Mail:
      <a :href="mailToLink">{{ config.public.contactMail }}</a><br>
      Telefon:
      <a :href="telLink">{{ config.public.contactPhone }}</a>
    </p>

    <h2>Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV</h2>
    <p>
      {{ config.public.privacyContactPerson }}<br>
      {{ fullStreetAddress }}<br>
      {{ fullCityLine }}
    </p>

    <h2>Projektbeschreibung</h2>
    <p>
      Die Badestellenkarte ist eine interaktive Kartenanwendung für Badestellen und wassernahe POIs in
      Schleswig-Holstein. Grundlage sind offene Datensätze, die über das Open-Data-Portal
      Schleswig-Holstein bereitgestellt werden.
    </p>

    <h2>Haftung für Inhalte</h2>
    <p>
      Die Inhalte dieser Website wurden mit angemessener Sorgfalt erstellt. Eine Gewähr für die
      Richtigkeit, Vollständigkeit und Aktualität der bereitgestellten Informationen wird jedoch nicht
      übernommen. Maßgeblich bleiben die Angaben der jeweiligen Datenquellen.
    </p>

    <h2>Haftung für Links</h2>
    <p>
      Diese Website enthält Links zu externen Websites Dritter. Auf deren Inhalte besteht kein Einfluss.
      Für die Inhalte der verlinkten Seiten sind ausschließlich deren Betreiber verantwortlich.
    </p>

    <h2>Urheberrecht</h2>
    <p>
      Soweit nicht anders gekennzeichnet, stammen die in der Anwendung angezeigten Daten aus offenen
      Quellen. Bitte ergänzt hier bei Bedarf konkrete Lizenzhinweise für Code, Design, Texte oder Daten.
    </p>
  </SiteLegalPage>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()
const siteUrl = useSiteUrl()
const pageUrl = toAbsoluteUrl('/impressum', siteUrl)

const fullStreetAddress = computed(
  () => `${config.public.addressStreet} ${config.public.addressHouseNumber}`,
)

const fullCityLine = computed(
  () => `${config.public.addressPostalCode} ${config.public.addressCity}`,
)

const mailToLink = computed(() => `mailto:${config.public.contactMail}`)

const telLink = computed(() => `tel:${config.public.contactPhone.replace(/"/g, '')}`)

useSeoMeta({
  title: 'Impressum | Badestellenkarte',
  description: 'Impressum der Badestellenkarte für Schleswig-Holstein.',
})

useJsonLd(() => ([
  {
    '@context': 'https://schema.org',
    '@type': 'WebPage',
    name: 'Impressum',
    url: pageUrl,
    description: 'Impressum der Badestellenkarte für Schleswig-Holstein.',
    isPartOf: {
      '@type': 'WebSite',
      name: 'Badestellenkarte',
      url: toAbsoluteUrl('/', siteUrl),
    },
    inLanguage: 'de-DE',
  },
  {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: config.public.addressName,
    email: config.public.contactMail || undefined,
    telephone: config.public.contactPhone || undefined,
    address: {
      '@type': 'PostalAddress',
      streetAddress: fullStreetAddress.value,
      postalCode: config.public.addressPostalCode || undefined,
      addressLocality: config.public.addressCity || undefined,
      addressCountry: 'DE',
    },
    url: toAbsoluteUrl('/', siteUrl),
  },
]), 'route-json-ld')
</script>
