<template>
  <div class="space-y-6">
    <section class="space-y-2">
      <h2 class="text-xl font-bold text-slate-900 md:text-2xl">Wie funktioniert die Karte?</h2>
      <p class="text-sm leading-6 text-slate-700 md:text-base">
        Klicke auf Marker, um Badestellen und wassernahe POIs zu öffnen. Beim Bewegen der Karte werden die Daten automatisch für den aktuellen Ausschnitt nachgeladen.
      </p>
    </section>

    <section class="space-y-2">
      <h2 class="text-xl font-bold text-slate-900 md:text-2xl">Was ist enthalten?</h2>
      <p class="text-sm leading-6 text-slate-700 md:text-base">
        Die Anwendung kombiniert offene Badestellen-Daten mit ergänzenden POIs auf derselben Karte. Beide Typen teilen sich dieselbe Auswahl- und Detaillogik, können später aber getrennt gefiltert und unterschiedlich gestaltet werden.
      </p>
    </section>

    <section class="space-y-2">
      <h2 class="text-xl font-bold text-slate-900 md:text-2xl">Open Data und Open Source</h2>
      <p class="text-sm leading-6 text-slate-700 md:text-base">
        Die Badestellen-Daten stammen aus dem Open-Data-Portal Schleswig-Holstein und werden aus mehreren Datensätzen zusammengeführt: Badegewässer Stammdaten, Einstufung, Infrastruktur, Saisondauer und Messungen. Die Karte selbst ist als offene, an die Denkmalkarte des OK Lab Flensburg angelehnte Anwendung aufgebaut und lässt sich transparent prüfen und fachlich anpassen.
      </p>
      <p class="text-sm leading-6 text-slate-700 md:text-base">
        Quellen im Open Data Portal:
        <a
          class="text-sky-700 underline decoration-sky-300 underline-offset-2"
          href="https://opendata.schleswig-holstein.de/collection/badegewasser-stammdaten/aktuell"
          target="_blank"
          rel="noreferrer"
        >
          Badegewässer Stammdaten
        </a>,
        <a
          class="text-sky-700 underline decoration-sky-300 underline-offset-2"
          href="https://opendata.schleswig-holstein.de/dataset/badegewasser-infrastruktur-aktuell"
          target="_blank"
          rel="noreferrer"
        >
          Badegewässer Infrastruktur
        </a>
        ,
        <a
          class="text-sky-700 underline decoration-sky-300 underline-offset-2"
          href="https://opendata.schleswig-holstein.de/dataset/badegewasser-saisondauer"
          target="_blank"
          rel="noreferrer"
        >
          Badegewässer Saisondauer
        </a>
        und
        <a
          class="text-sky-700 underline decoration-sky-300 underline-offset-2"
          href="https://opendata.schleswig-holstein.de/dataset/badegewasser-messungen"
          target="_blank"
          rel="noreferrer"
        >
          Badegewässer Messungen
        </a>.
      </p>
    </section>
  </div>
</template>
