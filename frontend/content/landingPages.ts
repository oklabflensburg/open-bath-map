import { assertLandingPageConfig } from '../utils/landingValidation'

export type LandingPageKind = 'region' | 'collection'

export interface LandingFilterDefinition {
  districtIncludes?: string[]
  cityIncludes?: string[]
  tagIncludes?: string[]
  textIncludes?: string[]
  categoryIncludes?: string[]
  amenitiesIncludes?: string[]
  requireAmenities?: boolean
}

export interface LandingPageDefinition {
  kind: LandingPageKind
  slug: string
  title: string
  h1: string
  metaTitle: string
  metaDescription: string
  ogTitle: string
  ogDescription: string
  introParagraphs: string[]
  secondaryIntroParagraphs?: string[]
  regionType?: 'stadt' | 'gewaesserraum' | 'kueste'
  collectionType?: 'ausstattung' | 'natur' | 'kueste'
  filter: LandingFilterDefinition
  selectionLogicText: string
  highlightedSlugs?: string[]
  relatedRegions?: string[]
  relatedCollections?: string[]
}

export const regionLandingPages: LandingPageDefinition[] = [
  {
    kind: 'region',
    slug: 'flensburg',
    title: 'Badestellen in Flensburg',
    h1: 'Badestellen in Flensburg',
    metaTitle: 'Badestellen in Flensburg - Karte, Infos und Wasserqualitaet',
    metaDescription: 'Uebersicht der erfassten Badestellen in Flensburg mit Karte, Detailseiten und datenbasierten Angaben aus offenen Quellen.',
    ogTitle: 'Badestellen in Flensburg',
    ogDescription: 'Alle erfassten Badestellen in Flensburg auf einen Blick: Karte, Detailinfos und Verlinkungen zu passenden Themenseiten.',
    introParagraphs: [
      'Auf dieser Seite findest du Badestellen in Flensburg, die in den zugrunde liegenden Open-Data-Quellen erfasst sind.',
      'Die Uebersicht hilft beim schnellen Vergleich von Lage, hinterlegter Ausstattung und weiteren Informationen aus den Detailseiten.',
    ],
    secondaryIntroParagraphs: [
      'Fuer die Auswahl werden die in den Datensaetzen gefuehrten Orts- und Kreisangaben zu Flensburg genutzt.',
    ],
    regionType: 'stadt',
    filter: {
      cityIncludes: ['flensburg'],
      districtIncludes: ['flensburg'],
    },
    selectionLogicText: 'Zuordnung ueber Stadt- und Kreisangaben mit Bezug auf Flensburg.',
    relatedRegions: ['kiel', 'schlei'],
    relatedCollections: ['mit-infrastruktur', 'ostsee'],
  },
  {
    kind: 'region',
    slug: 'kiel',
    title: 'Badestellen in Kiel',
    h1: 'Badestellen in Kiel',
    metaTitle: 'Badestellen in Kiel - Orte zum Baden mit Karte und Details',
    metaDescription: 'Finde Badestellen in Kiel auf der Karte. Mit Detailseiten, verknuepften Datenfeldern und direkten Links zu verwandten Sammlungen.',
    ogTitle: 'Badestellen in Kiel',
    ogDescription: 'Kieler Badestellen als datenbasierte Uebersicht mit Karte, Filterkontext und weiterfuehrenden Detailseiten.',
    introParagraphs: [
      'Diese Seite buendelt Badestellen in Kiel, die in den offenen Datensaetzen als Standort in Kiel gefuehrt werden.',
      'Du kannst die Seite als redaktionelle Einstiegsebene nutzen und anschliessend in die einzelnen Detailseiten wechseln.',
    ],
    secondaryIntroParagraphs: [
      'Die Auswahl basiert auf den hinterlegten Orts- und Kreisfeldern mit Kiel-Bezug.',
    ],
    regionType: 'stadt',
    filter: {
      cityIncludes: ['kiel'],
      districtIncludes: ['kiel'],
    },
    selectionLogicText: 'Zuordnung ueber Stadt- und Kreisangaben mit Bezug auf Kiel.',
    relatedRegions: ['flensburg', 'eckernfoerder-bucht'],
    relatedCollections: ['mit-infrastruktur', 'ostsee'],
  },
  {
    kind: 'region',
    slug: 'luebeck',
    title: 'Badestellen in Luebeck',
    h1: 'Badestellen in Luebeck',
    metaTitle: 'Badestellen in Luebeck - Karte, Lage und Detailinfos',
    metaDescription: 'Badestellen in Luebeck auf einer Seite: mit Kartenbezug, Detailseiten und transparenten Datenquellen.',
    ogTitle: 'Badestellen in Luebeck',
    ogDescription: 'Uebersicht zu Badestellen in Luebeck mit direktem Zugriff auf Karten- und Detailinformationen.',
    introParagraphs: [
      'Hier sind Badestellen in Luebeck zusammengefasst, die in den Datensaetzen entsprechend verortet sind.',
      'Die Seite schafft einen schnellen Einstieg in die vorhandenen Informationen und verlinkt auf die jeweiligen Detailseiten.',
    ],
    secondaryIntroParagraphs: [
      'Die Selektion folgt den hinterlegten Stadt- und Kreisangaben mit Luebeck-Bezug.',
    ],
    regionType: 'stadt',
    filter: {
      cityIncludes: ['luebeck'],
      districtIncludes: ['luebeck'],
    },
    selectionLogicText: 'Zuordnung ueber Stadt- und Kreisangaben mit Bezug auf Luebeck.',
    relatedRegions: ['kiel', 'eckernfoerder-bucht'],
    relatedCollections: ['ostsee', 'naturbadestellen'],
  },
  {
    kind: 'region',
    slug: 'schlei',
    title: 'Badestellen an der Schlei',
    h1: 'Badestellen an der Schlei',
    metaTitle: 'Badestellen an der Schlei - Badeorte im Ueberblick',
    metaDescription: 'Datenbasierte Uebersicht von Badestellen an der Schlei mit Kartenbezug, Detailseiten und nachvollziehbarer Auswahl.',
    ogTitle: 'Badestellen an der Schlei',
    ogDescription: 'Alle erfassten Badestellen mit Schlei-Bezug, aufbereitet als indexierbare Uebersichtsseite.',
    introParagraphs: [
      'Diese Regionenseite listet Badestellen mit Schlei-Bezug aus den verfuegbaren Datenfeldern und Bezeichnungen.',
      'So lassen sich geeignete Orte entlang der Schlei in einer kompakten Uebersicht vergleichen.',
    ],
    secondaryIntroParagraphs: [
      'Die Auswahl erfolgt ueber Begriffe wie Schlei in Titel-, Adress-, Kreis- oder Tag-Feldern.',
    ],
    regionType: 'gewaesserraum',
    filter: {
      textIncludes: ['schlei'],
      tagIncludes: ['schlei'],
    },
    selectionLogicText: 'Zuordnung ueber Schlei-Begriffe in textuellen Feldern und Tags.',
    relatedRegions: ['flensburg', 'eckernfoerder-bucht'],
    relatedCollections: ['ostsee', 'mit-infrastruktur'],
  },
  {
    kind: 'region',
    slug: 'eckernfoerder-bucht',
    title: 'Badestellen in der Eckernfoerder Bucht',
    h1: 'Badestellen in der Eckernfoerder Bucht',
    metaTitle: 'Badestellen in der Eckernfoerder Bucht - Karte und Uebersicht',
    metaDescription: 'Badestellen in der Eckernfoerder Bucht als indexierbare Uebersicht mit Detailseiten und Datengrundlage.',
    ogTitle: 'Badestellen in der Eckernfoerder Bucht',
    ogDescription: 'Regionale Landingpage fuer Badestellen mit Bezug zur Eckernfoerder Bucht.',
    introParagraphs: [
      'Auf dieser Seite werden Badestellen mit Bezug zur Eckernfoerder Bucht gebuendelt dargestellt.',
      'Die Liste ist datenbasiert und verknuepft direkt mit den jeweiligen Detailseiten.',
    ],
    secondaryIntroParagraphs: [
      'Die Zuordnung basiert auf Treffern in Orts-, Kreis-, Tag- und Titelangaben rund um Eckernfoerde und die Bucht.',
    ],
    regionType: 'gewaesserraum',
    filter: {
      textIncludes: ['eckernfoerde', 'eckernforder', 'eckernfoerder bucht', 'eckernfoerde bucht'],
      tagIncludes: ['eckernfoerde', 'eckernforder', 'eckernfoerder bucht', 'eckernfoerde bucht'],
      districtIncludes: ['rendsburg-eckernfoerde', 'rendsburg-eckernforder'],
    },
    selectionLogicText: 'Zuordnung ueber Begriffe zur Eckernfoerder Bucht in textuellen Feldern und Kreisbezeichnungen.',
    relatedRegions: ['kiel', 'schlei'],
    relatedCollections: ['ostsee', 'mit-infrastruktur'],
  },
]

export const collectionLandingPages: LandingPageDefinition[] = [
  {
    kind: 'collection',
    slug: 'mit-infrastruktur',
    title: 'Badestellen mit Infrastruktur',
    h1: 'Badestellen mit Infrastruktur',
    metaTitle: 'Badestellen mit Infrastruktur in Schleswig-Holstein',
    metaDescription: 'Sammlung von Badestellen mit hinterlegten Infrastrukturmerkmalen aus den offenen Datensaetzen.',
    ogTitle: 'Badestellen mit Infrastruktur',
    ogDescription: 'Datenbasierte Sammlung: Badestellen mit dokumentierten Infrastrukturangaben.',
    introParagraphs: [
      'Diese Sammlung buendelt Badestellen, bei denen in den verfuegbaren Datensaetzen Infrastrukturmerkmale hinterlegt sind.',
      'Je nach Eintrag koennen dazu beispielsweise Parkmoeglichkeiten, sanitaere Einrichtungen oder weitere Angebote gehoeren.',
    ],
    secondaryIntroParagraphs: [
      'Eine Badestelle wird aufgenommen, wenn mindestens ein Infrastrukturwert oder ein expliziter Zugangshinweis vorliegt.',
    ],
    collectionType: 'ausstattung',
    filter: {
      requireAmenities: true,
    },
    selectionLogicText: 'Auswahl, wenn ein Amenity-Eintrag oder ein Zugangs-/Infrastrukturhinweis vorhanden ist.',
    relatedRegions: ['flensburg', 'kiel', 'luebeck'],
    relatedCollections: ['ostsee', 'nordsee', 'naturbadestellen'],
  },
  {
    kind: 'collection',
    slug: 'naturbadestellen',
    title: 'Naturbadestellen in Schleswig-Holstein',
    h1: 'Naturbadestellen in Schleswig-Holstein',
    metaTitle: 'Naturbadestellen in Schleswig-Holstein - Karte und Uebersicht',
    metaDescription: 'Sammlung von Badestellen mit Naturbad-Bezug in Kategorie- oder Textfeldern der vorhandenen Daten.',
    ogTitle: 'Naturbadestellen in Schleswig-Holstein',
    ogDescription: 'Datenbasierte Uebersicht von Naturbadestellen mit direkter Verlinkung in die Detailseiten.',
    introParagraphs: [
      'Hier findest du Badestellen mit Naturbad-Bezug in den verfuegbaren Kategorisierungen und Bezeichnungen.',
      'Die Sammlung ist als Orientierung gedacht und basiert ausschliesslich auf vorhandenen Datenfeldern.',
    ],
    secondaryIntroParagraphs: [
      'Die Auswahl erfolgt ueber Kategorie-, Tag- und Texttreffer zu Naturbad/Naturbadestelle.',
    ],
    collectionType: 'natur',
    filter: {
      categoryIncludes: ['naturbad'],
      textIncludes: ['naturbad'],
      tagIncludes: ['naturbad'],
    },
    selectionLogicText: 'Zuordnung ueber Naturbad-Begriffe in Kategorie-, Tag- und Textfeldern.',
    relatedRegions: ['schlei', 'eckernfoerder-bucht'],
    relatedCollections: ['mit-infrastruktur', 'ostsee', 'nordsee'],
  },
  {
    kind: 'collection',
    slug: 'ostsee',
    title: 'Badestellen an der Ostsee in Schleswig-Holstein',
    h1: 'Badestellen an der Ostsee in Schleswig-Holstein',
    metaTitle: 'Badestellen an der Ostsee - Karte und Uebersicht',
    metaDescription: 'Alle erfassten Ostsee-Badestellen in Schleswig-Holstein mit Karte, Detailinfos und thematisch verwandten Links.',
    ogTitle: 'Badestellen an der Ostsee',
    ogDescription: 'Sammlung von Badestellen mit Ostsee-Bezug auf Basis der vorhandenen Tags und Textfelder.',
    introParagraphs: [
      'Diese Seite buendelt Badestellen mit Ostsee-Bezug in Schleswig-Holstein.',
      'Sie eignet sich als Einstieg in die Datensicht und verweist auf die einzelnen Detailseiten der jeweiligen Orte.',
    ],
    secondaryIntroParagraphs: [
      'Die Aufnahme erfolgt ueber Ostsee-Treffer in Tags und Textangaben.',
    ],
    collectionType: 'kueste',
    filter: {
      tagIncludes: ['ostsee'],
      textIncludes: ['ostsee'],
    },
    selectionLogicText: 'Zuordnung ueber Ostsee-Begriffe in Tags und textuellen Feldern.',
    relatedRegions: ['kiel', 'luebeck', 'eckernfoerder-bucht', 'schlei'],
    relatedCollections: ['nordsee', 'mit-infrastruktur'],
  },
  {
    kind: 'collection',
    slug: 'nordsee',
    title: 'Badestellen an der Nordsee in Schleswig-Holstein',
    h1: 'Badestellen an der Nordsee in Schleswig-Holstein',
    metaTitle: 'Badestellen an der Nordsee - Karte und Uebersicht',
    metaDescription: 'Datenbasierte Uebersicht von Nordsee-Badestellen in Schleswig-Holstein inklusive Detailseiten und internen Verlinkungen.',
    ogTitle: 'Badestellen an der Nordsee',
    ogDescription: 'Sammlung mit Nordsee-Bezug auf Basis der verfuegbaren Tags und textuellen Angaben.',
    introParagraphs: [
      'Diese Sammlung zeigt Badestellen mit Nordsee-Bezug in Schleswig-Holstein.',
      'Die Seite ergaenzt die Kartenansicht um eine indexierbare, redaktionell lesbare Uebersicht.',
    ],
    secondaryIntroParagraphs: [
      'Die Auswahl erfolgt ueber Nordsee-Treffer in Tags und Textfeldern.',
    ],
    collectionType: 'kueste',
    filter: {
      tagIncludes: ['nordsee'],
      textIncludes: ['nordsee'],
    },
    selectionLogicText: 'Zuordnung ueber Nordsee-Begriffe in Tags und textuellen Feldern.',
    relatedRegions: ['flensburg'],
    relatedCollections: ['ostsee', 'mit-infrastruktur'],
  },
]

export const allLandingPages: LandingPageDefinition[] = [
  ...regionLandingPages,
  ...collectionLandingPages,
]

export const landingPageByKey = new Map(
  allLandingPages.map((page) => [`${page.kind}:${page.slug}`, page]),
)

export function getLandingPath(kind: LandingPageKind, slug: string) {
  return kind === 'region' ? `/regionen/${slug}` : `/sammlungen/${slug}`
}

assertLandingPageConfig({
  regionLandingPages,
  collectionLandingPages,
})
