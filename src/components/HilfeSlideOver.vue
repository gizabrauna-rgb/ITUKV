<template>
  <div class="fixed inset-0 z-50 flex">
    <!-- Backdrop -->
    <div class="absolute inset-0 bg-black/40" @click="$emit('close')"></div>

    <!-- Slide-Over Panel -->
    <div class="ml-auto relative bg-white w-full max-w-4xl h-full shadow-2xl flex overflow-hidden">
      <!-- Sidebar: Inhaltsverzeichnis -->
      <aside class="w-64 bg-gray-50 border-r border-gray-200 flex flex-col flex-shrink-0">
        <div class="p-5 border-b border-gray-200 flex items-center gap-2">
          <BookOpen class="w-5 h-5 text-[#0088ba]" />
          <div>
            <h2 class="font-bold text-gray-900 text-sm">Hilfe & Handbuch</h2>
            <p class="text-[11px] text-gray-500">{{ roleLabel }}</p>
          </div>
        </div>
        <nav class="flex-1 overflow-y-auto p-2">
          <button v-for="s in sections" :key="s.id" @click="scrollTo(s.id)"
            :class="['w-full text-left text-xs px-3 py-2 rounded-lg transition-colors',
                     activeSection === s.id ? 'bg-[#0088ba] text-white font-medium' : 'text-gray-700 hover:bg-white']">
            {{ s.title }}
          </button>
        </nav>
        <div class="p-3 border-t border-gray-200 text-[10px] text-gray-400 text-center">
          Stand 2026-05-28
        </div>
      </aside>

      <!-- Inhalt -->
      <div class="flex-1 flex flex-col">
        <header class="flex items-center justify-between p-4 border-b border-gray-100">
          <h3 class="font-bold text-gray-800">{{ headerTitle }}</h3>
          <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 p-1">
            <X class="w-5 h-5" />
          </button>
        </header>
        <main ref="contentEl" class="flex-1 overflow-y-auto p-6 prose prose-sm max-w-none" @scroll="onScroll">
          <!-- VERKÄUFER -->
          <template v-if="role === 'verkaeufer'">
            <section id="willkommen">
              <h2>Willkommen!</h2>
              <p>Schön, dass du das Dashboard nutzt. Hier hast du jederzeit den vollen Überblick über den Verkaufsprozess deines Unternehmens.</p>
              <p>Du siehst, wo wir gerade stehen, was als Nächstes ansteht, und kannst Dokumente, Verträge und Termine zentral ablegen.</p>
              <div class="bg-blue-50 border border-blue-100 rounded-xl p-4 my-4 not-prose">
                <p class="text-sm text-blue-900"><strong>Datenschutz:</strong> Du siehst ausschließlich deine eigene Akte. Andere Mandanten oder Interessenten haben keinen Einblick in deine Daten.</p>
              </div>
            </section>

            <section id="startseite">
              <h2>Deine Startseite – „Mein Projekt"</h2>
              <p>Nach dem Login siehst du deine persönliche Begrüßungsseite mit:</p>
              <ul>
                <li><strong>Was steht für dich an?</strong> – deine persönlichen Aufgaben in der aktuellen Phase. Klick auf eine Aufgabe öffnet das passende Tool.</li>
                <li><strong>Bereits erledigt – kannst du jederzeit anpassen</strong> – was du schon ausgefüllt hast (z.B. Ziele, Kosten-Bestätigung).</li>
                <li><strong>Wo stehen wir gerade?</strong> – Visualisierung der 5 Hauptstufen mit deinem Fortschritt.</li>
                <li><strong>Was im Hintergrund läuft</strong> – Aufgaben, die mibeca/Anwalt/Notar parallel für dich übernehmen.</li>
              </ul>
            </section>

            <section id="tabs">
              <h2>Tabs im Überblick</h2>
              <table class="not-prose w-full text-sm">
                <thead class="bg-gray-50">
                  <tr><th class="p-2 text-left">Tab</th><th class="p-2 text-left">Wofür?</th></tr>
                </thead>
                <tbody class="divide-y divide-gray-100">
                  <tr><td class="p-2"><strong>Mein Projekt</strong></td><td class="p-2">Startseite mit Aufgaben + Status</td></tr>
                  <tr><td class="p-2"><strong>Meine Daten</strong></td><td class="p-2">Persönliche + Unternehmens-Stammdaten</td></tr>
                  <tr><td class="p-2"><strong>Fragebogen</strong></td><td class="p-2">Unternehmensbewertungs-Fragebogen</td></tr>
                  <tr><td class="p-2"><strong>Bewertung</strong></td><td class="p-2">Ergebnis deiner Unternehmensbewertung</td></tr>
                  <tr><td class="p-2"><strong>Verträge</strong></td><td class="p-2">NDA + Mandatsvertrag online unterzeichnen</td></tr>
                  <tr><td class="p-2"><strong>Mein Exposé</strong></td><td class="p-2">Exposé prüfen + freigeben</td></tr>
                  <tr><td class="p-2"><strong>Interessenten</strong></td><td class="p-2">Wer hat sich beworben + VETO setzen</td></tr>
                  <tr><td class="p-2"><strong>Dokumente</strong></td><td class="p-2">Datenraum mit deinen Unterlagen</td></tr>
                  <tr><td class="p-2"><strong>Verlauf</strong></td><td class="p-2">Chronologische Kommunikation mit Jenny</td></tr>
                </tbody>
              </table>
            </section>

            <section id="daten">
              <h2>„Meine Daten" pflegen</h2>
              <p>Hier pflegst du deine persönlichen Kontaktdaten und die Unternehmens-Stammdaten. Alles wird automatisch gespeichert beim Klick außerhalb des Felds.</p>
              <p><strong>Read-only-Felder:</strong> mb-Nummer, Transaktionsnummer, Kundennummer – diese werden von mibeca vergeben und können nicht selbst geändert werden.</p>
              <p>Oben siehst du einen <strong>„Vollständigkeit"-Balken</strong> – je mehr Felder gepflegt sind, desto besser die Beratung durch Jenny.</p>
            </section>

            <section id="fragebogen">
              <h2>Fragebogen ausfüllen</h2>
              <p>Ca. 30 Fragen in Themen-Blöcken (Geschäftsmodell, Kunden, Mitarbeiter, Finanzen, Risiken).</p>
              <ol>
                <li>Tab <strong>Fragebogen</strong> öffnen</li>
                <li>Fragen Block für Block beantworten (Auto-Save aktiv)</li>
                <li>Am Ende <strong>„Fragebogen abgeben"</strong> klicken</li>
                <li>Jenny bekommt automatisch eine Benachrichtigung</li>
              </ol>
              <p><strong>Tipp:</strong> Du kannst in mehreren Sitzungen ausfüllen – Fortschritt wird gespeichert.</p>
            </section>

            <section id="ziele">
              <h2>Ziele & Motivationen erfassen</h2>
              <p>Strukturierte Selbst-Reflexion: Warum verkaufe ich? Was ist mir wichtig? Was sind Deal-Breaker?</p>
              <p><strong>Klick-Pfad:</strong> Mein Projekt → Klick auf „Ziele & Motivationen erfassen" → Modal öffnet sich</p>
              <p>Du gibst an: Motivation, Zeitrahmen, Wunsch-Verkaufserlös, Rolle nach Verkauf, Mitarbeiter/Standort, Deal-Struktur (Earn-Out etc.), Deal-Breaker.</p>
              <p>Auto-Save aktiv. Du kannst das Formular jederzeit nochmal über „Bereits erledigt – kannst du jederzeit anpassen" öffnen.</p>
            </section>

            <section id="kosten">
              <h2>Kosten-Tabelle ansehen</h2>
              <p>Damit du weißt, welche Kosten auf dich im Verkaufsprozess zukommen.</p>
              <p><strong>Klick-Pfad:</strong> Mein Projekt → Klick auf „Kosten-Tabelle ansehen" → Modal mit Tabelle öffnet sich.</p>
              <p>Die Tabelle zeigt typische Beträge für 500k und 1,5 Mio. € Verkaufserlös: mibeca-Honorar, Anwalt, Notar, Beratungsvergütung. Plus Nach-Steuer-Rechnung je Rechtsform.</p>
              <p>Klick auf <strong>„Verstanden"</strong> → Häkchen in Checkliste setzt sich automatisch.</p>
            </section>

            <section id="expose">
              <h2>Exposé prüfen + freigeben</h2>
              <p>Das Exposé ist die Verkaufs-Broschüre, die potenziellen Käufern (nach NDA) gezeigt wird.</p>
              <ol>
                <li>Tab <strong>Mein Exposé</strong> öffnen</li>
                <li>Vorschau durchlesen</li>
                <li>Bei Bedarf: <strong>„Korrektur-Wunsch"</strong> → Jenny passt an</li>
                <li>Wenn alles passt: <strong>„Freigeben"</strong></li>
              </ol>
            </section>

            <section id="vertraege">
              <h2>Verträge online unterzeichnen</h2>
              <ol>
                <li>Tab <strong>Verträge</strong> → den Vertrag wählen</li>
                <li><strong>„Jetzt online unterschreiben"</strong> klicken</li>
                <li>SMS-Code auf dein Handy → eingeben</li>
                <li>Mit Maus oder Touch unterschreiben → <strong>„Senden"</strong></li>
                <li>PDF-Kopie kommt per Mail</li>
              </ol>
              <p><strong>Sicherheit:</strong> 2-Faktor mit SMS-Code, verschlüsselte Speicherung im Datenraum.</p>
            </section>

            <section id="interessenten">
              <h2>Interessenten + VETO-Recht</h2>
              <p>Sobald mibeca Interessenten anspricht, siehst du sie hier mit Rating und NDA-Status.</p>
              <p><strong>VETO setzen:</strong> Bei Konkurrenten oder unerwünschten Käufern klickst du auf <strong>VETO</strong> → kurz begründen → Jenny entfernt den Interessenten.</p>
            </section>

            <section id="dokumente">
              <h2>Dokumente / Datenraum</h2>
              <p>Hier liegen alle relevanten Unterlagen zu deinem Unternehmen (Bilanzen, Verträge, Personal-Daten, Gesellschaftsverträge).</p>
              <p><strong>Upload:</strong> Tab Dokumente → Ordner wählen → Datei hochladen oder per Drag-&-Drop.</p>
              <p>Max. 100 MB pro Datei. Käufer-Interessenten sehen den Datenraum erst nach NDA-Unterschrift.</p>
            </section>

            <section id="verlauf-v">
              <h2>Verlauf – Nachrichten mit Jenny</h2>
              <p>Statt E-Mails: alles chronologisch in deiner Akte. Du siehst Mails, Telefonat-Notizen, Termin-Bestätigungen und automatische Aufgaben-Erledigungen.</p>
              <p><strong>Neue Nachricht:</strong> Direkt im Verlauf-Eingabefeld → landet in Jennys Posteingang.</p>
            </section>

            <section id="faq-v">
              <h2>Häufige Fragen</h2>
              <p><strong>Passwort vergessen?</strong> Login-Seite → „Passwort vergessen?" → Mail eingeben → Reset-Link (30 Min gültig).</p>
              <p><strong>Sehen andere Mandanten meine Daten?</strong> Nein. Technisch komplett isoliert.</p>
              <p><strong>Werden meine Daten an Käufer weitergegeben?</strong> Erst nach NDA. Du behältst die Kontrolle.</p>
              <p><strong>Technisches Problem?</strong> Mail an ab@mike-bergmann.de (Anna) oder jk@mike-bergmann.de (Jenny).</p>
            </section>
          </template>

          <!-- KÄUFER -->
          <template v-else-if="role === 'kaeufer'">
            <section id="willkommen">
              <h2>Willkommen!</h2>
              <p>Schön, dass du das Dashboard nutzt. Hier hast du den vollen Überblick über deine <strong>Akquisitionssuche</strong> – Suchprofil, gefundene Kandidaten, NDAs, Verhandlungen.</p>
              <div class="bg-blue-50 border border-blue-100 rounded-xl p-4 my-4 not-prose">
                <p class="text-sm text-blue-900"><strong>Datenschutz:</strong> Du siehst ausschließlich deine eigene Akte. Andere Käufer oder Verkäufer-Mandanten haben keinen Einblick.</p>
              </div>
            </section>

            <section id="startseite">
              <h2>Deine Startseite – „Mein Projekt"</h2>
              <p>Nach dem Login siehst du:</p>
              <ul>
                <li><strong>Was steht für dich an?</strong> – deine Käufer-Aufgaben in der aktuellen Phase.</li>
                <li><strong>Bereits erledigt – kannst du jederzeit anpassen</strong> – z.B. deine Akquisitionsstrategie.</li>
                <li><strong>Wo stehen wir gerade?</strong> – Visualisierung deiner 5 Hauptstufen.</li>
                <li><strong>Was im Hintergrund läuft</strong> – Aufgaben, die mibeca für dich übernimmt.</li>
              </ul>
            </section>

            <section id="tabs">
              <h2>Tabs im Überblick</h2>
              <table class="not-prose w-full text-sm">
                <thead class="bg-gray-50">
                  <tr><th class="p-2 text-left">Tab</th><th class="p-2 text-left">Wofür?</th></tr>
                </thead>
                <tbody class="divide-y divide-gray-100">
                  <tr><td class="p-2"><strong>Mein Projekt</strong></td><td class="p-2">Startseite mit Aufgaben + Status</td></tr>
                  <tr><td class="p-2"><strong>Meine Daten</strong></td><td class="p-2">Persönliche Kontaktdaten + Vorgangsnummern</td></tr>
                  <tr><td class="p-2"><strong>Mein Suchprofil</strong></td><td class="p-2">Was suchst du genau?</td></tr>
                  <tr><td class="p-2"><strong>Target-Vorschläge</strong></td><td class="p-2">Konkrete Kandidaten von mibeca</td></tr>
                  <tr><td class="p-2"><strong>Verträge</strong></td><td class="p-2">NDAs + Mandatsvertrag + ggf. Kaufvertrag</td></tr>
                  <tr><td class="p-2"><strong>Dokumente</strong></td><td class="p-2">Datenraum für DD-Material</td></tr>
                  <tr><td class="p-2"><strong>Verlauf</strong></td><td class="p-2">Chronologische Kommunikation</td></tr>
                </tbody>
              </table>
            </section>

            <section id="daten">
              <h2>„Meine Daten" pflegen</h2>
              <p>Persönliche Kontaktdaten + Vorgangsnummern (read-only) + Mandatslaufzeit. Auto-Save aktiv.</p>
            </section>

            <section id="suchprofil">
              <h2>Mein Suchprofil definieren</h2>
              <p>Damit mibeca passende Verkaufs-Kandidaten findet, brauchen wir deine genauen Kriterien.</p>
              <ul>
                <li><strong>Branche(n):</strong> z.B. „IT-Dienstleister, Maschinenbau"</li>
                <li><strong>Region:</strong> z.B. „DACH" oder „200km um Hannover"</li>
                <li><strong>Größe:</strong> Mitarbeiter-Range + Umsatz-Range</li>
                <li><strong>Finanzielle Eckdaten:</strong> EBIT-Marge mindestens, Recurring-Anteil</li>
                <li><strong>Strategische Kriterien:</strong> Wachstum vs. stabil, GF-Verbleib gewünscht</li>
                <li><strong>No-Gos</strong></li>
              </ul>
              <p>Wenn vollständig: <strong>„Freigeben"</strong> → mibeca startet die Recherche.</p>
            </section>

            <section id="akquisition">
              <h2>Akquisitionsstrategie & Ziele erfassen</h2>
              <p>Hilft Jenny, wirklich passende Kandidaten zu finden und Verhandlungen für dich zu führen.</p>
              <p><strong>Klick-Pfad:</strong> Mein Projekt → Klick auf „Budget-Rahmen + Strategische Ziele" → Modal öffnet sich</p>
              <p>Du gibst an: Warum kaufen? (Wachstum, Diversifikation, Markteintritt, Nachfolge, …), Hold-Period, Max. Kaufpreis, Eigenkapital + Finanzierung, Zielunternehmen-Profil, GF-Verbleib, Synergien, Deal-Breaker.</p>
              <p>Auto-Save aktiv. Jederzeit anpassbar.</p>
            </section>

            <section id="vorschlaege">
              <h2>Target-Vorschläge bewerten</h2>
              <p>Sobald mibeca passende Kandidaten gefunden hat, siehst du sie hier (vor NDA: anonymisiert).</p>
              <p>Pro Kandidat klickst du:</p>
              <ul>
                <li><strong>Interesse</strong> → Jenny startet anonyme Ansprache + NDA-Prozess</li>
                <li><strong>Rückfrage</strong> → Jenny klärt deine Frage</li>
                <li><strong>Kein Interesse</strong> → Kandidat aussortieren</li>
              </ul>
            </section>

            <section id="vertraege">
              <h2>Verträge online unterzeichnen</h2>
              <p>NDA mit Verkäufer-Kandidaten + Mandatsvertrag mit mibeca + ggf. Kaufvertrag.</p>
              <ol>
                <li>Tab <strong>Verträge</strong> öffnen</li>
                <li><strong>„Jetzt online unterschreiben"</strong></li>
                <li>SMS-Code → eingeben</li>
                <li>Mit Maus/Touch unterschreiben → <strong>„Senden"</strong></li>
              </ol>
            </section>

            <section id="datenraum">
              <h2>Datenraum</h2>
              <p>Hier liegen deine eigenen Dokumente (DD-Berichte, Bewertungs-Materialien, Kaufvertrags-Entwürfe).</p>
              <p>Nach NDA-Unterschrift bekommst du Zugang zum Datenraum des Verkäufer-Kandidaten (separater Bereich, Token-Link).</p>
            </section>

            <section id="verlauf-k">
              <h2>Verlauf – Nachrichten mit Jenny</h2>
              <p>Chronologische Kommunikation. Mails, Notizen, Termin-Bestätigungen, automatische Hinweise und Kandidaten-Feedback-Logs.</p>
            </section>

            <section id="faq-k">
              <h2>Häufige Fragen</h2>
              <p><strong>Welche Kosten kommen auf mich zu?</strong> mibeca-Honorar, Anwalts-Kosten (SPA-Prüfung), Notar, ggf. DD-Kosten, Bürgschaftsbank-Gebühren bei Finanzierung. Konkrete Zahlen mit Jenny besprechen.</p>
              <p><strong>Werden meine Daten an Verkäufer weitergegeben?</strong> Erst nach NDA. Vor NDA bleibst du anonym.</p>
              <p><strong>Passwort vergessen?</strong> Login-Seite → „Passwort vergessen?"</p>
              <p><strong>Technisches Problem?</strong> Mail an ab@mike-bergmann.de (Anna) oder jk@mike-bergmann.de (Jenny).</p>
            </section>
          </template>

          <!-- ADMIN -->
          <template v-else>
            <section id="willkommen">
              <h2>Willkommen im Admin-Bereich</h2>
              <p>Hier verwaltest du alle Mandate, Kontakte, Verträge, KI-Funktionen und Compliance. Du siehst <strong>alle</strong> Mandate (kein IDOR-Filter).</p>
            </section>

            <section id="uebersicht">
              <h2>Übersicht-Tab – dein Tages-Cockpit</h2>
              <ul>
                <li><strong>Stats:</strong> aktive Mandate, offene NDAs, Investoren, abgeschlossene Deals</li>
                <li><strong>„Wartet auf mich":</strong> alle akuten To-dos (Vertrag gegenzeichnen, NDA prüfen, Wiedervorlage, Mandate läuft aus, Pressetext, ungelesene Nachrichten, Fragebogen, Exposé-Freigabe)</li>
                <li><strong>Aktivitäts-Feed</strong> chronologisch</li>
                <li><strong>Anstehende Termine</strong></li>
              </ul>
            </section>

            <section id="projekte">
              <h2>Projekte-Tab</h2>
              <p>Alle Mandate als Tabelle mit Status, aktueller Phase, „Mandant zuletzt", „Nächster Schritt für dich" (gelb wenn dringend), NEU-Badge bei Aktivität ≤3 Tagen.</p>
              <p>Filter, Suche, +Neues Projekt, Status inline ändern, Wiedervorlage setzen, Löschen.</p>
            </section>

            <section id="akte">
              <h2>Akte arbeiten</h2>
              <p>Klick auf eine Zeile öffnet die Akte. Tab-Gruppen: Übersicht, Mandat, Verträge, Marktansprache, Datenraum, Abschluss, Verwaltung.</p>
              <p>Wichtigste Tabs: Master-Prozess, Mandat-Daten, Ziele/Strategie, Fragebogen, Bewertung, Exposé, Dokumente, Verlauf.</p>
            </section>

            <section id="crm">
              <h2>CRM / Kontakte</h2>
              <p>~5.000 Kontakte. Karten-Ansicht mit PLZ-Radius, Listen-Ansicht mit Filtern, Suche über Firma/Name/Branche, Bulk-Import/Export.</p>
            </section>

            <section id="ki">
              <h2>KI-Funktionen (Details)</h2>
              <h3>KI-Analyse im Dashboard</h3>
              <p>Akte → Datenraum → PDF auswählen → <strong>lila „KI-Analyse"-Button</strong> klicken. Modal mit Vorschlägen pro Feld – manuell übernehmen pro Feld.</p>
              <ul>
                <li>Max 10 MB PDF. Bei &gt;5 MB Button gelb.</li>
                <li>Pro Akte einmalig „KI erlauben" bestätigen (Opt-In).</li>
                <li>Audit-Log + Verlauf-Eintrag automatisch.</li>
              </ul>
              <h3>KI-Coworker (Jennys externer Assistent)</h3>
              <p>Service-Account mit Rolle <code>ai-agent</code> kann:</p>
              <ul>
                <li>Stammdaten in Kontakten + Mandaten ergänzen (eng begrenzte Feldliste)</li>
                <li>Verlauf-Einträge anhängen</li>
                <li>Listen lesen</li>
                <li>Bulk bis 500 Einträge pro Aufruf</li>
              </ul>
              <p><strong>Darf nicht:</strong> mb-Nummer/Status/Projekttyp ändern, Verträge anlegen, User anlegen, Dokumente hochladen, Mails versenden.</p>
              <h3>Notfall-Aus</h3>
              <p>Azure Portal → <code>itukv-func-v2</code> → Configuration → <code>AI_ANALYSE_AKTIV</code> auf <code>false</code> → Save.</p>
            </section>

            <section id="benutzer">
              <h2>Benutzer-Verwaltung</h2>
              <p>+Neuer Benutzer → Rolle wählen → bei Verkäufer/Investor passendes Mandat aus 6 Ansichten wählen.</p>
              <p>Interne Mailadressen (@mike-bergmann.de) bekommen <strong>kein Passwort</strong> – Microsoft-Login. Externe Mandanten bekommen 12-stelliges Initial-Passwort + Begrüßungsmail.</p>
              <p>Passwort-Reset: „Zugangsdaten neu senden"-Button.</p>
            </section>

            <section id="controlling">
              <h2>Controlling + Beirats-Bericht</h2>
              <p>KPIs, Pipeline-Wert, Provisions-Forecast, Top-Mandate, Phasen-Verteilung pro Verkauf/Kauf, Deal-Dauer pro Projekttyp, monatlicher Verlauf, Lessons Learned.</p>
              <p><strong>„Beirats-Bericht (PDF)"</strong>-Button oben rechts → druckfertiges PDF.</p>
            </section>

            <section id="audit">
              <h2>Audit & Backup</h2>
              <p>Jeder Schreibvorgang ist im Audit-Log. Filter nach User/Mandate/Aktion/Zeit.</p>
              <p>Wöchentliches Backup (Sonntags 03:00 UTC, 12 Wochen Rotation). Sofort-Backup-Button.</p>
            </section>

            <section id="tipps">
              <h2>Tipps & Tricks</h2>
              <ul>
                <li>Cmd+Shift+R bei komischen Anzeigen</li>
                <li>Tab bleibt nach Reload erhalten</li>
                <li>„Mandant zuletzt"-Spalte sortieren = aktive Mandanten zuerst</li>
                <li>Beirats-Bericht vor jedem Quartals-Meeting frisch generieren</li>
                <li>Audit-Log monatlich kurz durchscrollen</li>
              </ul>
            </section>
          </template>

          <!-- Footer-Spacer -->
          <div class="h-24"></div>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { BookOpen, X } from '@lucide/vue'

const props = defineProps({ role: { type: String, required: true } })
defineEmits(['close'])

const contentEl = ref(null)
const activeSection = ref('')

const roleLabel = computed(() => ({
  verkaeufer: 'Verkäufer-Mandant',
  kaeufer: 'Käufer-Mandant',
  admin: 'Admin (mibeca-Team)',
})[props.role] || '')

const headerTitle = computed(() => ({
  verkaeufer: 'Handbuch für Verkäufer',
  kaeufer: 'Handbuch für Käufer',
  admin: 'Admin-Handbuch',
})[props.role] || 'Handbuch')

const sections = computed(() => {
  if (props.role === 'verkaeufer') return [
    { id: 'willkommen', title: 'Willkommen' },
    { id: 'startseite', title: 'Startseite „Mein Projekt"' },
    { id: 'tabs', title: 'Tabs im Überblick' },
    { id: 'daten', title: 'Meine Daten' },
    { id: 'fragebogen', title: 'Fragebogen' },
    { id: 'ziele', title: 'Ziele & Motivationen' },
    { id: 'kosten', title: 'Kosten-Tabelle' },
    { id: 'expose', title: 'Exposé prüfen' },
    { id: 'vertraege', title: 'Verträge unterschreiben' },
    { id: 'interessenten', title: 'Interessenten + VETO' },
    { id: 'dokumente', title: 'Dokumente' },
    { id: 'verlauf-v', title: 'Verlauf' },
    { id: 'faq-v', title: 'Häufige Fragen' },
  ]
  if (props.role === 'kaeufer') return [
    { id: 'willkommen', title: 'Willkommen' },
    { id: 'startseite', title: 'Startseite „Mein Projekt"' },
    { id: 'tabs', title: 'Tabs im Überblick' },
    { id: 'daten', title: 'Meine Daten' },
    { id: 'suchprofil', title: 'Suchprofil' },
    { id: 'akquisition', title: 'Akquisitionsstrategie' },
    { id: 'vorschlaege', title: 'Target-Vorschläge' },
    { id: 'vertraege', title: 'Verträge unterschreiben' },
    { id: 'datenraum', title: 'Datenraum' },
    { id: 'verlauf-k', title: 'Verlauf' },
    { id: 'faq-k', title: 'Häufige Fragen' },
  ]
  return [
    { id: 'willkommen', title: 'Willkommen' },
    { id: 'uebersicht', title: 'Übersicht-Tab' },
    { id: 'projekte', title: 'Projekte-Tab' },
    { id: 'akte', title: 'Akte arbeiten' },
    { id: 'crm', title: 'CRM / Kontakte' },
    { id: 'ki', title: 'KI-Funktionen' },
    { id: 'benutzer', title: 'Benutzer-Verwaltung' },
    { id: 'controlling', title: 'Controlling' },
    { id: 'audit', title: 'Audit & Backup' },
    { id: 'tipps', title: 'Tipps & Tricks' },
  ]
})

function scrollTo(id) {
  const el = contentEl.value?.querySelector('#' + CSS.escape(id))
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  activeSection.value = id
}

function onScroll() {
  if (!contentEl.value) return
  const scrollTop = contentEl.value.scrollTop
  let active = sections.value[0]?.id
  for (const s of sections.value) {
    const el = contentEl.value.querySelector('#' + CSS.escape(s.id))
    if (el && el.offsetTop - 100 <= scrollTop) active = s.id
  }
  activeSection.value = active
}

function onEsc(e) { if (e.key === 'Escape') document.dispatchEvent(new CustomEvent('hilfe-close')) }
onMounted(() => window.addEventListener('keydown', onEsc))
onBeforeUnmount(() => window.removeEventListener('keydown', onEsc))
</script>

<style scoped>
@reference "tailwindcss";
.prose h2 { @apply text-lg font-bold text-gray-900 mt-6 mb-2; }
.prose h3 { @apply text-base font-semibold text-gray-800 mt-4 mb-1; }
.prose p { @apply text-sm text-gray-700 leading-relaxed mb-2; }
.prose ul, .prose ol { @apply text-sm text-gray-700 mb-3 ml-5 space-y-1; }
.prose ul { @apply list-disc; }
.prose ol { @apply list-decimal; }
.prose li { @apply leading-relaxed; }
.prose code { @apply bg-gray-100 text-pink-700 px-1 py-0.5 rounded text-xs font-mono; }
.prose table { @apply border border-gray-200 rounded-xl overflow-hidden my-3; }
.prose section { @apply mb-8; }
</style>
