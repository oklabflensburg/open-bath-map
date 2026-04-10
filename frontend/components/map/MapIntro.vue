<template>
  <div class="space-y-6">
    <section class="space-y-2">
      <h2 class="text-xl font-bold text-slate-900 md:text-2xl">Wie funktioniert die Karte?</h2>
      <p class="text-sm leading-6 text-slate-700 md:text-base">
        Entdecke Badestellen, Strände und wassernahe Orte direkt auf der Karte. Ein Klick auf die Marker zeigt dir,
        was es vor Ort zu wissen gibt – von Lage und Wasserqualität bis zu nützlichen Infos für deinen Ausflug.
        Wenn du die Karte verschiebst oder hineinzoomst, lädt die Ansicht automatisch passende Orte im aktuellen
        Bereich nach.
      </p>
    </section>

    <section class="space-y-2">
      <h2 class="text-xl font-bold text-slate-900 md:text-2xl">Warum dieses Projekt?</h2>
      <p class="text-sm leading-6 text-slate-700 md:text-base">
        Die besten Plätze am Wasser zu finden, sollte einfach sein. In der Praxis sind Informationen zu Badestellen
        oft über viele Quellen verteilt, schwer lesbar aufbereitet oder kaum vergleichbar. Badestellenkarte bringt diese
        Daten an einem Ort zusammen – übersichtlich, verständlich und direkt auf dem Smartphone nutzbar.
      </p>
      <p class="text-sm leading-6 text-slate-700 md:text-base">
        Die Idee dahinter: Offene Verwaltungsdaten sollen nicht nur irgendwo veröffentlicht werden, sondern im Alltag
        wirklich hilfreich sein. Für spontane Sommertage, geplante Ausflüge oder den kurzen Check unterwegs zeigt die
        Karte auf einen Blick, wo sich Baden lohnt – und was dich dort erwartet.
      </p>
    </section>

    <section class="space-y-2">
      <h2 class="text-xl font-bold text-slate-900 md:text-2xl">Was ist enthalten?</h2>
      <p class="text-sm leading-6 text-slate-700 md:text-base">
        Die Karte verbindet offizielle Badestellen-Daten mit ergänzenden wasserbezogenen POIs. So bekommst du nicht
        nur einzelne Badeorte angezeigt, sondern auch ein besseres Gefühl für die Umgebung. Alle Einträge lassen sich
        nach demselben Prinzip erkunden und bilden gemeinsam eine Karte, die zum Suchen, Vergleichen und Entdecken
        einlädt.
      </p>
    </section>

    <section class="space-y-2">
      <h2 class="text-xl font-bold text-slate-900 md:text-2xl">Open Data und Open Source</h2>
      <p class="text-sm leading-6 text-slate-700 md:text-base">
        Die Daten zu den Badestellen stammen aus dem Open-Data-Portal Schleswig-Holstein. Dafür werden mehrere
        Datensätze zusammengeführt – darunter Stammdaten, Einstufungen, Infrastruktur, Saisondauer und Messwerte.
        So entsteht aus einzelnen Rohdaten eine Karte, die sich im Alltag leicht nutzen lässt.
      </p>
      <p class="text-sm leading-6 text-slate-700 md:text-base">
        Gleichzeitig ist Badestellenkarte selbst offen aufgebaut: nachvollziehbar, prüfbar und weiterentwickelbar. Denn
        gute digitale Werkzeuge sollten nicht nur gut aussehen, sondern auch transparent zeigen, woher ihre Daten
        kommen, wie sie verarbeitet werden und welche Annahmen dahinterstehen.
      </p>
      <p class="text-sm leading-6 text-slate-700 md:text-base">
        Genau deshalb ist das Projekt offen dokumentiert und der Quellcode öffentlich zugänglich – damit andere
        mitdenken, mitbauen und die Anwendung fachlich weiter verbessern können.
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
      <p class="text-sm leading-6 text-slate-700 md:text-base">
        GitHub-Repository:
        <a
          class="text-sky-700 underline decoration-sky-300 underline-offset-2"
          href="https://github.com/oklabflensburg/open-bath-map"
          target="_blank"
          rel="noreferrer"
        >
          github.com/oklabflensburg/open-bath-map
        </a>
      </p>
    </section>
  </div>
</template>