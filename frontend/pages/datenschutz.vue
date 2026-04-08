<template>
  <SiteLegalPage title="Datenschutz">
    <p>
      Diese Vorlage ist eine technische Basis und muss vor dem Livegang an den tatsächlichen Betrieb,
      das Hosting und die eingesetzten Dienste angepasst werden.
    </p>

    <h2>1. Verantwortliche Stelle</h2>
    <p>
      {{ config.public.addressName }}<br>
      {{ fullStreetAddress }}<br>
      {{ fullCityLine }}<br>
      E-Mail:
      <a :href="mailToLink">{{ config.public.contactMail }}</a>
    </p>

    <h2>2. Verarbeitung beim Aufruf der Website</h2>
    <p>
      Beim Aufruf der Website verarbeitet der Hosting-Anbieter technisch erforderliche Verbindungsdaten,
      insbesondere IP-Adresse, Datum und Uhrzeit, angeforderte Inhalte, übertragene Datenmenge,
      Browserkennung und Referrer. Die Verarbeitung erfolgt zur Bereitstellung, Stabilität und Sicherheit
      des Angebots.
    </p>

    <h2>3. Karten- und Open-Data-Dienste</h2>
    <p>
      Für die Kartendarstellung werden OpenStreetMap-Daten verwendet, die ausschließlich über eigene
      Server ausgeliefert werden. Dabei werden technisch erforderliche Anfragen an die von uns
      betriebenen Server für Kartenkacheln und Datendienste gesendet. Eine Übermittlung an externe
      Kartendienstleister erfolgt in diesem Zusammenhang nicht. Die Verarbeitung erfolgt auf Grundlage
      von Art. 6 Abs. 1 lit. f DSGVO aufgrund unseres berechtigten Interesses an einer funktionsfähigen
      und nutzerfreundlichen Bereitstellung der Kartenansicht.
    </p>

    <h2>4. Standortfunktion</h2>
    <p>
      Die Standortfunktion wird nur nach aktiver Freigabe durch den Nutzer im Browser verwendet. Die
      ermittelte Position dient ausschließlich dazu, Badestellen im Umkreis anzuzeigen. Es erfolgt
      keine serverseitige Speicherung der Standortdaten. Die Verarbeitung erfolgt nur für die Dauer der
      jeweiligen Nutzung der Funktion und auf Grundlage der Einwilligung gemäß Art. 6 Abs. 1 lit. a
      DSGVO.
    </p>

    <h2>5. Cookies und lokale Speicherung</h2>
    <p>
      Nach aktuellem Stand setzt die Anwendung keine offensichtlichen Tracking- oder Marketing-Cookies.
      Prüft vor Veröffentlichung trotzdem den tatsächlichen Einsatz von Hosting-, Analyse- oder
      Consent-Werkzeugen und ergänzt die Erklärung entsprechend.
    </p>

    <h2>6. Empfänger und Drittlandtransfer</h2>
    <p>
      Eine Übermittlung personenbezogener Daten an Drittanbieter oder sonstige externe Empfänger findet
      im Rahmen dieses Angebots nicht statt. Ein Transfer personenbezogener Daten in Staaten außerhalb
      der Europäischen Union oder des Europäischen Wirtschaftsraums erfolgt nicht.
    </p>

    <h2>7. Speicherdauer</h2>
    <p>
      Personenbezogene Daten werden nur so lange gespeichert, wie dies für den jeweiligen Zweck
      erforderlich ist. Soweit gesetzliche Aufbewahrungspflichten nach deutschem Recht bestehen,
      insbesondere aus dem Handelsgesetzbuch (HGB) oder der Abgabenordnung (AO), erfolgt die
      Speicherung für die gesetzlich vorgeschriebene Dauer. Anschließend werden die Daten gelöscht,
      sofern keine weitere rechtliche Verpflichtung oder Berechtigung zur Aufbewahrung besteht.
    </p>

    <h2>8. Rechte der betroffenen Personen</h2>
    <p>
      Betroffene Personen haben im Rahmen der gesetzlichen Voraussetzungen ein Recht auf Auskunft,
      Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit sowie Widerspruch.
      Zudem besteht ein Beschwerderecht bei einer Datenschutzaufsichtsbehörde.
    </p>

    <h2>9. Stand</h2>
    <p>8. April 2026</p>
  </SiteLegalPage>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()

const fullStreetAddress = computed(
  () => `${config.public.addressStreet} ${config.public.addressHouseNumber}`,
)

const fullCityLine = computed(
  () => `${config.public.addressPostalCode} ${config.public.addressCity}`,
)

const mailToLink = computed(() => `mailto:${config.public.contactMail}`)

useSeoMeta({
  title: 'Datenschutz | Badestellenkarte',
  description: 'Datenschutzhinweise der Badestellenkarte für Schleswig-Holstein.',
})
</script>
