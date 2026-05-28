<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Topbar -->
    <header class="bg-[#161e2a] text-white px-6 py-3 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <img src="/Logo_mibeca_Start.png" alt="mibeca" class="h-10 w-auto" />
        <div>
          <span class="font-bold text-sm">ITUKV Dashboard</span>
          <span class="text-gray-400 text-xs ml-2">Verkäufer-Portal</span>
        </div>
      </div>
      <div class="flex items-center gap-4">
        <button @click="openVerlauf" class="relative flex items-center gap-1.5 text-xs text-gray-300 hover:text-white" :title="`${unreadTotal} ungelesene Nachrichten`">
          <Bell class="w-4 h-4" />
          <span v-if="unreadTotal > 0" class="absolute -top-1 -right-2 bg-red-500 text-white text-[10px] font-bold rounded-full min-w-[16px] h-4 px-1 flex items-center justify-center">
            {{ unreadTotal > 99 ? '99+' : unreadTotal }}
          </span>
        </button>
        <span class="text-sm text-gray-300">{{ userName }}</span>
        <button @click="$emit('logout')" class="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white">
          <LogOut class="w-4 h-4" /> Abmelden
        </button>
      </div>
    </header>

    <div class="max-w-7xl mx-auto px-6 py-8">
      <!-- Begrüßungs-Card (schlank) -->
      <div class="bg-gradient-to-br from-white to-[#0088ba]/5 border border-[#0088ba]/10 rounded-2xl p-6 mb-5">
        <div class="flex items-start justify-between gap-4 flex-wrap">
          <div class="flex-1 min-w-0">
            <div v-if="projekttyp" class="mb-2">
              <span class="inline-flex items-center gap-1.5 text-xs font-semibold bg-[#0088ba]/10 text-[#0088ba] px-2.5 py-1 rounded-full">
                <Briefcase class="w-3 h-3" />
                {{ projekttyp }}
              </span>
              <span v-if="targetData?.mbNr" class="ml-2 inline-flex items-center text-xs font-mono bg-gray-100 text-gray-700 px-2 py-1 rounded">{{ targetData.mbNr }}</span>
            </div>
            <h1 class="text-2xl font-bold text-gray-900">{{ greetingTime }}, {{ firstName || userName }}!</h1>
            <p class="text-sm text-gray-600 mt-1">Hier ist dein aktueller Stand bei deinem M&A-Projekt mit mibeca.</p>
          </div>
          <!-- Ansprechpartnerin inline -->
          <div class="flex items-center gap-2 text-xs text-gray-600 bg-white border border-gray-100 rounded-xl px-3 py-2">
            <div class="w-7 h-7 rounded-full bg-[#0088ba]/10 flex items-center justify-center">
              <User class="w-4 h-4 text-[#0088ba]" />
            </div>
            <div>
              <div class="text-[10px] uppercase tracking-wide text-gray-400 font-semibold">Deine Ansprechpartnerin</div>
              <div class="text-sm font-semibold text-gray-900 leading-tight">Jennifer Kaplan</div>
              <a href="mailto:jk@mike-bergmann.de" class="text-[11px] text-[#0088ba] hover:underline">jk@mike-bergmann.de</a>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab Nav -->
      <div class="flex gap-1 mb-6 bg-white rounded-xl border border-gray-100 p-1 w-fit">
        <button v-for="item in visibleNavItems" :key="item.tab" @click="tab = item.tab"
          :class="['flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors', tab === item.tab ? 'bg-[#0088ba] text-white' : 'text-gray-600 hover:bg-gray-50']">
          <component :is="item.icon" class="w-4 h-4" />
          {{ item.label }}
        </button>
      </div>

      <!-- Tab: Mein Projekt -->
      <div v-if="tab === 'projekt'">
        <!-- 1) Was steht für DICH an? -->
        <div v-if="meineOffenenAufgaben.length" class="bg-white rounded-2xl border-2 border-[#0088ba]/20 p-6 mb-4">
          <div class="flex items-start gap-3 mb-4">
            <div class="w-10 h-10 rounded-full bg-[#0088ba]/10 flex items-center justify-center flex-shrink-0">
              <CheckCircle class="w-5 h-5 text-[#0088ba]" />
            </div>
            <div>
              <h3 class="font-bold text-gray-900">Was steht für dich an?</h3>
              <p class="text-xs text-gray-500">{{ meineOffenenAufgaben.length }} {{ meineOffenenAufgaben.length === 1 ? 'Aufgabe' : 'Aufgaben' }} aus der aktuellen Phase</p>
            </div>
          </div>
          <div class="space-y-2">
            <button v-for="a in meineOffenenAufgaben" :key="a.id" @click="goToTab(tabForAufgabe(a.label))"
              class="w-full flex items-center justify-between gap-3 p-3 border border-gray-100 rounded-xl hover:border-[#0088ba] hover:bg-[#0088ba]/5 text-left transition-colors">
              <div class="flex items-center gap-3 min-w-0">
                <Circle class="w-4 h-4 text-gray-300 flex-shrink-0" />
                <span class="text-sm text-gray-800 truncate">{{ cleanLabel(a.label) }}</span>
              </div>
              <span class="text-xs text-[#0088ba] flex items-center gap-1 flex-shrink-0">
                Erledigen <ChevronRight class="w-3 h-3" />
              </span>
            </button>
          </div>
        </div>
        <div v-else-if="phasen.length" class="bg-green-50 border border-green-200 rounded-2xl p-6 mb-4 flex items-start gap-3">
          <CheckCircle class="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 class="font-bold text-green-900">Aktuell brauchen wir nichts von dir</h3>
            <p class="text-sm text-green-800 mt-1">mibeca arbeitet im Hintergrund. Du wirst informiert sobald wir dich brauchen — z.B. bei Erstkennenlernen, NDA-Freigabe oder Vertragsverhandlung.</p>
          </div>
        </div>

        <!-- 2) Wo stehen wir gerade? (Stufen-Leiste + was mibeca gerade macht) -->
        <div v-if="phasen.length" class="bg-white rounded-2xl border border-gray-100 overflow-hidden mb-4">
          <!-- Header mit Stufen-Leiste -->
          <div class="bg-gradient-to-br from-[#0088ba] to-[#00a0d8] p-6 text-white">
            <div class="text-xs uppercase tracking-wide opacity-80 mb-1">Wo stehen wir gerade?</div>
            <div class="text-xl font-bold mb-1">{{ aktuelleStufeName }}</div>
            <div class="text-sm opacity-90 mb-4">{{ aktuelleStufeBeschreibung }}</div>
            <div class="flex items-center gap-2 mt-4">
              <div v-for="(stufe, idx) in stufenListe" :key="stufe.key" class="flex-1">
                <div :class="['h-2 rounded-full transition-all',
                  idx < aktuelleStufeIdx ? 'bg-white' : idx === aktuelleStufeIdx ? 'bg-white' : 'bg-white/20']"></div>
                <div :class="['text-[10px] mt-1.5 text-center font-medium',
                  idx === aktuelleStufeIdx ? 'text-white' : 'text-white/60']">{{ stufe.name }}</div>
              </div>
            </div>
          </div>
          <!-- Im Hintergrund: was mibeca / andere gerade machen (ohne deine eigenen Aufgaben) -->
          <div v-if="aufgabenOhneMich.length" class="p-5 border-t border-gray-100">
            <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Was im Hintergrund läuft</h4>
            <ul class="space-y-2">
              <li v-for="t in aufgabenOhneMich" :key="t.id" class="flex items-center gap-3 text-sm">
                <div :class="['w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0', t.done ? 'bg-green-500' : 'bg-gray-200']">
                  <Check v-if="t.done" class="w-3 h-3 text-white" />
                </div>
                <span :class="t.done ? 'text-gray-400 line-through' : 'text-gray-700'">{{ cleanLabel(t.label) }}</span>
                <span v-if="t.verantwortlich" class="ml-auto text-[10px] px-2 py-0.5 rounded-full font-medium bg-gray-100 text-gray-500">
                  {{ t.verantwortlich }}
                </span>
              </li>
            </ul>
          </div>
          <!-- Toggle: Alle Schritte -->
          <div class="px-5 py-3 border-t border-gray-100 bg-gray-50">
            <button @click="showAllPhasen = !showAllPhasen" class="text-xs text-[#0088ba] font-medium hover:underline flex items-center gap-1">
              {{ showAllPhasen ? 'Alle Schritte ausblenden' : 'Alle Schritte anzeigen' }}
              <ChevronRight :class="['w-3 h-3 transition-transform', showAllPhasen ? 'rotate-90' : '']" />
            </button>
            <ul v-if="showAllPhasen" class="space-y-2 mt-3">
              <li v-for="(p, idx) in phasen" :key="p.id" class="flex items-center gap-3 text-sm">
                <div :class="['w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0', phasenStatus(p) === 'done' ? 'bg-green-100 text-green-700' : phasenStatus(p) === 'current' ? 'bg-[#0088ba] text-white' : 'bg-gray-100 text-gray-400']">
                  <Check v-if="phasenStatus(p) === 'done'" class="w-3.5 h-3.5" />
                  <span v-else>{{ idx + 1 }}</span>
                </div>
                <span :class="phasenStatus(p) === 'done' ? 'text-gray-400 line-through' : phasenStatus(p) === 'current' ? 'font-semibold text-gray-900' : 'text-gray-500'">{{ cleanLabel(p.titel) }}</span>
              </li>
            </ul>
            <p v-if="showAllPhasen" class="text-xs text-gray-400 mt-3">Die Schritte werden von deiner Ansprechpartnerin bei mibeca aktualisiert.</p>
          </div>
        </div>

        <!-- Mandatsvertrag-Status (nur wenn vorhanden + relevant) -->
        <div v-if="vertragInfo && (vertragInfo.signiertAm || vertragInfo.gegengezeichnetAm || vertragInfo.signToken)" class="mb-4">
          <div v-if="vertragInfo.gegengezeichnetAm" class="bg-green-50 border border-green-200 rounded-xl p-4 flex items-center gap-3">
            <CheckCircle class="w-6 h-6 text-green-600 flex-shrink-0" />
            <div class="flex-1">
              <p class="font-semibold text-green-900 text-sm">Mandatsvertrag vollständig unterschrieben</p>
              <p class="text-xs text-green-700">Gegengezeichnet am {{ formatDate(vertragInfo.gegengezeichnetAm) }}</p>
            </div>
          </div>
          <div v-else-if="vertragInfo.signiertAm" class="bg-yellow-50 border border-yellow-200 rounded-xl p-4 flex items-center gap-3">
            <Clock class="w-6 h-6 text-yellow-600 flex-shrink-0" />
            <div>
              <p class="font-semibold text-yellow-900 text-sm">Vertrag unterschrieben – wartet auf Gegenzeichnung durch mibeca</p>
            </div>
          </div>
        </div>

        <!-- Pressetext nur in spaeten Phasen (Phase 13+) -->
        <PressetextFreigabe v-if="currentPhase >= 13" :target-id="targetId" />
      </div>

      <!-- Tab: Fragebogen Unternehmensbewertung -->
      <div v-else-if="tab === 'fragebogen'">
        <Fragebogen :target-id="targetId" />
      </div>

      <!-- Tab: Bewertung (Scoring auf Basis 33 Fragen) -->
      <div v-else-if="tab === 'bewertung'">
        <Unternehmensbewertung :target-id="targetId" :read-only="true" />
      </div>

      <!-- Tab: Target-Vorschläge (nur bei Kauf-Mandat) -->
      <div v-else-if="tab === 'vorschlaege'">
        <KaeuferVorschlaege :target-id="targetId" />
      </div>

      <!-- Tab: Suchprofil (nur Kauf-Mandat) -->
      <div v-else-if="tab === 'suchprofil'">
        <Suchprofil :target-id="targetId" />
      </div>

      <!-- Tab: Verträge (read-only Status für Käufer) -->
      <div v-else-if="tab === 'vertraege'">
        <h2 class="text-xl font-bold text-gray-900 mb-5 flex items-center gap-2">
          <FileText class="w-6 h-6 text-[#0088ba]" /> Meine Verträge
        </h2>
        <div v-if="vertragInfo" class="space-y-3">
          <!-- Mandatsvertrag-Karte -->
          <div class="bg-white rounded-xl border border-gray-100 p-5">
            <div class="flex items-start justify-between mb-3">
              <div>
                <h3 class="font-semibold text-gray-900">Mandatsvertrag</h3>
                <p class="text-xs text-gray-500">Vereinbarung mit mibeca GmbH</p>
              </div>
              <span v-if="vertragInfo.gegengezeichnetAm" class="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">✅ Vollständig unterschrieben</span>
              <span v-else-if="vertragInfo.signiertAm" class="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full font-medium">⏳ Wartet auf Gegenzeichnung</span>
              <span v-else-if="vertragInfo.gesendetAm" class="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium">📩 Zur Signatur gesendet</span>
              <span v-else class="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">Entwurf</span>
            </div>
            <!-- Sign-CTA: wenn Vertrag gesendet aber noch nicht unterschrieben -->
            <a v-if="vertragInfo.signToken && !vertragInfo.signiertAm" :href="`${apiBaseUrl?.replace(/\/api$/, '')}/sign/${vertragInfo.signToken}`" target="_blank" rel="noopener"
              class="inline-flex items-center gap-2 px-5 py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 mr-2">
              <FileText class="w-4 h-4" /> Jetzt online unterschreiben
            </a>
            <a v-if="vertragInfo.signToken" :href="`${apiBaseUrl}/sign-pdf?token=${vertragInfo.signToken}`" target="_blank" rel="noopener"
              class="inline-flex items-center gap-2 px-4 py-2 border border-gray-200 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-50">
              <Download class="w-4 h-4" /> Vertrag herunterladen
            </a>
            <p v-if="vertragInfo.signToken && !vertragInfo.signiertAm" class="text-xs text-gray-500 mt-3">
              Klick auf „Jetzt online unterschreiben" — der Vertrag öffnet sich, du unterschreibst per Maus oder Finger, fertig.
            </p>
          </div>
        </div>
        <div v-else class="bg-white rounded-xl border border-gray-100 p-10 text-center text-sm text-gray-400">
          <FileText class="w-10 h-10 mx-auto mb-3 text-gray-200" />
          Noch keine Verträge angelegt. mibeca informiert dich sobald etwas zur Unterschrift bereit liegt.
        </div>
      </div>

      <!-- Tab: Meine Daten (Mandat-Vorlage) -->
      <div v-else-if="tab === 'mandat'">
        <MandatDaten :target-id="targetId" :read-only="impersonating" />
      </div>

      <!-- Tab: Mein Exposé (Freigabe) -->
      <div v-else-if="tab === 'expose'">
        <ExposeFreigabe :target-id="targetId" />
      </div>

      <!-- Tab: Verlauf -->
      <div v-else-if="tab === 'verlauf'">
        <Verlauf :target-id="targetId" :read-only="true" />
      </div>

      <!-- Tab: Interessenten -->
      <div v-else-if="tab === 'interessenten'">
        <h2 class="text-xl font-bold text-gray-900 mb-5">Meine Interessenten</h2>
        <div v-if="loadingInt" class="text-center text-gray-400 text-sm py-10">Lade Interessenten…</div>
        <div v-else-if="!interessenten.length" class="bg-white rounded-xl border border-gray-100 p-8 text-center text-gray-400 text-sm">
          <Users class="w-10 h-10 mx-auto mb-3 text-gray-200" />
          Noch keine Interessenten. Sobald jemand ein NDA unterzeichnet, erscheint er hier.
        </div>
        <div v-else class="space-y-3">
          <div v-for="i in interessenten" :key="i.RowKey" class="bg-white rounded-xl border border-gray-100 p-5">
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="font-medium text-gray-800">{{ i.firma || i.name }}</span>
                  <span :class="ndaClass(i.ndaStatus)" class="text-xs px-2 py-0.5 rounded-full font-medium">{{ ndaLabel(i.ndaStatus) }}</span>
                  <span v-if="i.veto" class="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full font-medium">VETO</span>
                </div>
                <div class="text-xs text-gray-400 mt-0.5">
                  {{ i.plz }} {{ i.ort }}
                  <span v-if="i.ndaUploadedAt"> · NDA seit {{ new Date(i.ndaUploadedAt).toLocaleDateString('de-DE') }}</span>
                </div>
              </div>
              <!-- Rating -->
              <div class="flex items-center gap-0.5">
                <button v-for="n in 5" :key="n" @click="setRating(i, n)" class="p-0.5">
                  <Star :class="n <= i.rating ? 'text-[#c8b274] fill-[#c8b274]' : 'text-gray-200'" class="w-4 h-4" />
                </button>
              </div>
            </div>

            <!-- Aktionen -->
            <div class="flex gap-2 mt-3">
              <!-- Freigabe-Toggle -->
              <button @click="toggleFreigabe(i)"
                :class="['flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-colors', i.freigegebenFuerKontakt ? 'bg-green-50 text-green-700 border-green-200' : 'text-gray-500 border-gray-200 hover:bg-gray-50']">
                <UserCheck class="w-3.5 h-3.5" />
                {{ i.freigegebenFuerKontakt ? 'Freigegeben' : 'Freigabe geben' }}
              </button>

              <!-- VETO -->
              <button v-if="!i.veto" @click="openVeto(i)"
                class="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 transition-colors">
                <Ban class="w-3.5 h-3.5" /> VETO setzen
              </button>
              <button v-else @click="removeVeto(i)"
                class="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-red-50 text-red-600 border border-red-200">
                <Ban class="w-3.5 h-3.5" /> VETO entfernen
              </button>
            </div>

            <!-- VETO Begründung -->
            <div v-if="i.veto && i.vetoBegruendung" class="mt-2 text-xs text-red-500 bg-red-50 rounded-lg px-3 py-2">
              Begründung: {{ i.vetoBegruendung }}
            </div>
          </div>
        </div>
      </div>

      <!-- Tab: Links -->
      <div v-else-if="tab === 'links'">
        <div class="flex items-center justify-between mb-5">
          <h2 class="text-xl font-bold text-gray-900">Wichtige Links</h2>
          <button @click="showLinkModal = true" class="flex items-center gap-2 px-3 py-2 bg-[#0088ba] text-white rounded-xl text-sm hover:bg-[#00a0d8]">
            <Plus class="w-4 h-4" /> Link hinzufügen
          </button>
        </div>
        <div v-if="!links.length" class="bg-white rounded-xl border border-gray-100 p-8 text-center text-gray-400 text-sm">
          <LinkIcon class="w-10 h-10 mx-auto mb-3 text-gray-200" />
          Noch keine Links hinterlegt.
        </div>
        <div v-else class="space-y-3">
          <div v-for="l in links" :key="l.RowKey || l.id" class="bg-white rounded-xl border border-gray-100 p-4 flex items-start gap-3">
            <div class="w-10 h-10 bg-[#0088ba]/10 rounded-lg flex items-center justify-center flex-shrink-0">
              <LinkIcon class="w-5 h-5 text-[#0088ba]" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <a :href="l.url" target="_blank" rel="noopener" class="font-medium text-gray-900 hover:text-[#0088ba] truncate">{{ l.titel }}</a>
                <span v-if="l.kategorie" class="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{{ l.kategorie }}</span>
                <span v-if="l.system" class="text-[10px] uppercase tracking-wide bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full font-semibold">System</span>
              </div>
              <div class="text-xs text-gray-400 mt-0.5 truncate">{{ l.url }}</div>
              <div v-if="l.beschreibung" class="text-sm text-gray-600 mt-1">{{ l.beschreibung }}</div>
            </div>
            <button v-if="!l.system" @click="deleteLink(l)" class="text-gray-300 hover:text-red-500"><Trash2 class="w-4 h-4" /></button>
          </div>
        </div>
      </div>

      <!-- Link Modal -->
      <div v-if="showLinkModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
        <div class="bg-white rounded-2xl p-6 w-full max-w-md">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-bold text-gray-900">Link hinzufügen</h3>
            <button @click="showLinkModal = false"><X class="w-5 h-5 text-gray-400" /></button>
          </div>
          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Titel *</label>
              <input v-model="linkForm.titel" placeholder="z.B. Datenraum" class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">URL *</label>
              <input v-model="linkForm.url" placeholder="https://…" class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Kategorie</label>
              <select v-model="linkForm.kategorie" class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none">
                <option>Allgemein</option><option>Datenraum</option><option>Element-Raum</option><option>Tools</option><option>Externe Dokumente</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Beschreibung</label>
              <textarea v-model="linkForm.beschreibung" rows="2" class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 resize-none"></textarea>
            </div>
          </div>
          <div class="flex gap-3 mt-5">
            <button @click="showLinkModal = false" class="flex-1 px-4 py-2 text-sm border border-gray-200 rounded-xl">Abbrechen</button>
            <button @click="createLink" class="flex-1 px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium">Speichern</button>
          </div>
        </div>
      </div>

      <!-- Tab: Dokumente -->
      <div v-else-if="tab === 'dokumente'">
        <h2 class="text-xl font-bold text-gray-900 mb-2">Meine Dokumente</h2>
        <p class="text-sm text-gray-500 mb-5">Du kannst Dateien hochladen. Löschen können nur die mibeca-Berater (zur Sicherheit deiner Daten).</p>
        <!-- Verkäufer darf hochladen, aber NDAs sind im DokumenteAkte ohnehin admin-only via Backend -->
        <DokumenteAkte :target-id="targetId" :read-only="false" />
      </div>
    </div>

    <!-- VETO Modal -->
    <div v-if="vetoTarget" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div class="bg-white rounded-2xl p-6 w-full max-w-sm">
        <h3 class="font-bold text-gray-900 mb-2">VETO setzen</h3>
        <p class="text-sm text-gray-500 mb-3">Bitte gib eine kurze Begründung an:</p>
        <textarea v-model="vetoText" rows="3" class="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-200 resize-none" placeholder="Begründung…"></textarea>
        <div class="flex gap-3 mt-4">
          <button @click="vetoTarget = null; vetoText = ''" class="flex-1 px-4 py-2 text-sm border border-gray-200 rounded-xl">Abbrechen</button>
          <button @click="confirmVeto" class="flex-1 px-4 py-2 bg-red-500 text-white rounded-xl text-sm font-medium">VETO bestätigen</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import {
  Building2, LogOut, Briefcase, Users, FolderOpen, Check, CheckCircle, Circle,
  Star, UserCheck, Ban, Folder, ChevronLeft, Upload, FileText, Download,
  Link as LinkIcon, Plus, Trash2, X, ClipboardList, FileEdit, MessageSquare, TrendingUp, Clock, Bell,
  User, ChevronRight
} from '@lucide/vue'

const apiBaseUrl = import.meta.env.VITE_API_BASE || 'https://itukv-func-v2.azurewebsites.net/api'
import MandatDaten from '../components/target/MandatDaten.vue'
import PressetextFreigabe from '../components/target/PressetextFreigabe.vue'
import KaeuferVorschlaege from '../components/target/KaeuferVorschlaege.vue'
import Suchprofil from '../components/admin/Suchprofil.vue'
import DokumenteAkte from '../components/admin/DokumenteAkte.vue'
import Fragebogen from '../components/target/Fragebogen.vue'
import Unternehmensbewertung from '../components/target/Unternehmensbewertung.vue'
import ExposeFreigabe from '../components/target/ExposeFreigabe.vue'
import Verlauf from '../components/admin/Verlauf.vue'
import { authFetch, getInteressenten, updateInteressent, verlaufUnreadCount, verlaufMarkRead } from '../api.js'
import { getPhasenVorlage } from '../lib/phasenTemplates.js'

const props = defineProps({ userName: String, projekttyp: String, impersonating: Boolean })
const emit = defineEmits(['logout'])
const targetId = sessionStorage.getItem('targetId') || ''

const tab = ref('projekt')
const checkliste = ref([])
const interessenten = ref([])
const dokumente = ref([])
const links = ref([])
const target = ref(null)
const vertragInfo = computed(() => {
  try { return target.value?.vertragJson ? JSON.parse(target.value.vertragJson) : null } catch { return null }
})
function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
const showAllPhasen = ref(false)
const loadingCheck = ref(true)
const loadingInt = ref(true)
const selectedOrdner = ref(null)
const vetoTarget = ref(null)
const vetoText = ref('')
const showLinkModal = ref(false)
const linkForm = ref({ titel: '', url: '', beschreibung: '', kategorie: 'Allgemein' })

// Projekttypen mit Links-Tab
const TYPES_WITH_LINKS = ['UVE Target', 'MC Target', 'MC Investoren']

const navItems = computed(() => {
  const istKauf = /kauf|investor/i.test(props.projekttyp || target.value?.projekttyp || '')
  let base
  if (istKauf) {
    base = [
      { tab: 'projekt', label: 'Mein Projekt', icon: Briefcase },
      { tab: 'mandat', label: 'Meine Daten', icon: ClipboardList },
      { tab: 'suchprofil', label: 'Mein Suchprofil', icon: FileEdit },
      { tab: 'vorschlaege', label: 'Target-Vorschläge', icon: Users },
      { tab: 'vertraege', label: 'Verträge', icon: FileText },
      { tab: 'dokumente', label: 'Dokumente', icon: FolderOpen },
    ]
  } else {
    base = [
      { tab: 'projekt', label: 'Mein Projekt', icon: Briefcase },
      { tab: 'mandat', label: 'Meine Daten', icon: ClipboardList },
      { tab: 'fragebogen', label: 'Fragebogen', icon: FileEdit },
      { tab: 'bewertung', label: 'Bewertung', icon: TrendingUp },
      { tab: 'vertraege', label: 'Verträge', icon: FileText },
      { tab: 'expose', label: 'Mein Exposé', icon: FileText },
      { tab: 'interessenten', label: 'Interessenten', icon: Users },
      { tab: 'dokumente', label: 'Dokumente', icon: FolderOpen },
    ]
  }
  if (TYPES_WITH_LINKS.includes(props.projekttyp)) {
    base.push({ tab: 'links', label: 'Links', icon: LinkIcon })
  }
  base.push({ tab: 'verlauf', label: 'Verlauf', icon: MessageSquare })
  return base
})
const visibleNavItems = computed(() => navItems.value)

const ordnerListe = ['Unterlagen Ausschreibung', 'Exposé', 'Protokoll', 'NDA', 'Gesprächsnotizen', 'Datenraum', 'Beratervertrag', 'Diverses']

const doneCount = computed(() => checkliste.value.filter(i => i.done).length)
const progress = computed(() => !checkliste.value.length ? 0 : Math.round(doneCount.value / checkliste.value.length * 100))

// --- Master-Prozess (Phasen-Sicht für Kunden) ---
const phasen = computed(() => {
  let stored = []
  try { stored = JSON.parse(target.value?.phasenJson || '[]') } catch { stored = [] }
  // Fallback: wenn am Target noch keine Phasen gespeichert sind, nutze die
  // Standard-Vorlage (Verkauf oder Kauf) - so sieht der Mandant sofort
  // den vordefinierten Prozess, auch wenn das Admin-Setup noch nicht ausgefuehrt wurde
  if (!Array.isArray(stored) || stored.length === 0) {
    return getPhasenVorlage(props.projekttyp || target.value?.projekttyp || '')
  }
  return stored
})
function isPhaseDone(p) { return p.aufgaben && p.aufgaben.length && p.aufgaben.every(t => t.done) }
const currentPhase = computed(() => {
  for (let i = 0; i < phasen.value.length; i++) {
    if (!isPhaseDone(phasen.value[i])) return i + 1
  }
  return phasen.value.length || 1
})
const currentPhaseTitle = computed(() => {
  const p = phasen.value[currentPhase.value - 1]
  return p ? p.titel.replace(/^\d+\.\s*/, '') : '—'
})
const donePhasen = computed(() => phasen.value.filter(isPhaseDone).length)
const phasenProgress = computed(() => !phasen.value.length ? 0 : Math.round(donePhasen.value / phasen.value.length * 100))

// Begruessungs-Card
const targetData = computed(() => target.value)
const firstName = computed(() => {
  const n = target.value?.vorname || (props.userName || '').split(' ')[0] || ''
  return n.trim()
})
const greetingTime = computed(() => {
  const h = new Date().getHours()
  if (h < 11) return 'Guten Morgen'
  if (h < 17) return 'Guten Tag'
  return 'Guten Abend'
})
const offeneAufgaben = computed(() => {
  let count = 0
  for (const p of phasen.value) {
    if (!Array.isArray(p.aufgaben)) continue
    for (const t of p.aufgaben) if (!t.done) count++
  }
  return count
})
const naechsterTermin = computed(() => {
  let termine = []
  try { termine = JSON.parse(target.value?.termineJson || '[]') } catch { termine = [] }
  const today = new Date().toISOString().slice(0, 10)
  return termine
    .filter(t => !t.erledigt && t.datum && t.datum >= today)
    .sort((a, b) => (a.datum || '').localeCompare(b.datum || ''))[0]
})
const naechsterTerminLabel = computed(() => {
  if (!naechsterTermin.value) return '—'
  const d = new Date(naechsterTermin.value.datum)
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' })
})
const naechsterTerminText = computed(() => {
  return naechsterTermin.value?.titel || 'keiner geplant'
})

// =========== Aktuelle Aufgaben + Stufen-Logik (Mein Projekt) ===========
const aktuellePhaseObj = computed(() => phasen.value[currentPhase.value - 1] || null)

function cleanLabel(s) {
  if (!s) return ''
  return s
    .replace(/^MB\d+:\s*/i, '')           // "MB050: ..." entfernen
    .replace(/^\d+\.\s*/, '')              // "1. ..." entfernen
    .replace(/\s*\(.+?Vorlage:.+?\)/i, '') // "(Vorlage: ...)" entfernen
}

function isMineResponsibility(verantwortlich) {
  if (!verantwortlich) return false
  const v = verantwortlich.toLowerCase()
  return v === 'kunde' || v === 'käufer' || v === 'kaeufer' || v === 'verkäufer' || v === 'verkaeufer'
}

const meineOffenenAufgaben = computed(() => {
  const ph = aktuellePhaseObj.value
  if (!ph || !Array.isArray(ph.aufgaben)) return []
  return ph.aufgaben.filter(a => !a.done && (!a.verantwortlich || isMineResponsibility(a.verantwortlich)))
})

// Aufgaben der aktuellen Phase, die NICHT der Mandant zu erledigen hat
// (also: mibeca, Steuerberater, externe Partner – damit der Mandant sieht, was im Hintergrund läuft)
const aufgabenOhneMich = computed(() => {
  const ph = aktuellePhaseObj.value
  if (!ph || !Array.isArray(ph.aufgaben)) return []
  return ph.aufgaben.filter(a => a.verantwortlich && !isMineResponsibility(a.verantwortlich))
})

// Mapping: Aufgaben-Label → Ziel-Tab
function tabForAufgabe(label) {
  const l = (label || '').toLowerCase()
  if (l.includes('fragebogen')) return 'fragebogen'
  if (l.includes('bewertung')) return 'bewertung'
  if (l.includes('expos')) return 'expose'
  if (l.includes('mandat') && (l.includes('unterz') || l.includes('vertrag') || l.includes('signier'))) return 'vertraege'
  if (l.includes('vertrag') || l.includes('signatur') || l.includes('unterschr')) return 'vertraege'
  if (l.includes('datenraum') || l.includes('dokument') || l.includes('bilanz') || l.includes('jahresabschluss')) return 'dokumente'
  if (l.includes('suchprofil') || l.includes('such')) return 'suchprofil'
  if (l.includes('kandidat') || l.includes('vorschlag') || l.includes('long-list')) return 'vorschlaege'
  if (l.includes('interessent') || l.includes('nda') || l.includes('veto')) return 'interessenten'
  return 'mandat'
}

function goToTab(t) {
  if (!t) return
  tab.value = t
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Stufen-Visualisierung (4 Hauptstufen statt 15 Detail-Phasen)
const stufenListe = computed(() => {
  const istKauf = /kauf|investor/i.test(props.projekttyp || target.value?.projekttyp || '')
  if (istKauf) {
    return [
      { key: 'briefing', name: 'Briefing', range: [1, 2] },
      { key: 'markt', name: 'Marktansprache', range: [3, 5] },
      { key: 'kontakt', name: 'Erstgespräche', range: [6, 7] },
      { key: 'verhandlung', name: 'LOI & DD', range: [8, 9] },
      { key: 'closing', name: 'Closing', range: [10, 10] },
    ]
  }
  return [
    { key: 'vorbereitung', name: 'Vorbereitung', range: [1, 2] },
    { key: 'markt', name: 'Marktansprache', range: [3, 7] },
    { key: 'verhandlung', name: 'Verhandlung', range: [8, 12] },
    { key: 'closing', name: 'Closing', range: [13, 15] },
  ]
})

const aktuelleStufeIdx = computed(() => {
  const cp = currentPhase.value
  return stufenListe.value.findIndex(s => cp >= s.range[0] && cp <= s.range[1])
})

const aktuelleStufeName = computed(() => {
  if (!phasen.value.length) return 'In Vorbereitung'
  const s = stufenListe.value[aktuelleStufeIdx.value]
  return s ? s.name : 'In Vorbereitung'
})

const aktuelleStufeBeschreibung = computed(() => {
  const istKauf = /kauf|investor/i.test(props.projekttyp || target.value?.projekttyp || '')
  const key = stufenListe.value[aktuelleStufeIdx.value]?.key
  const txt = istKauf ? {
    briefing: 'Wir klären gemeinsam Suchkriterien, Region und Größenklasse.',
    markt: 'mibeca screent den Markt und stellt dir passende Kandidaten vor.',
    kontakt: 'Du lernst die spannendsten Kandidaten kennen.',
    verhandlung: 'LOI verhandeln und Due Diligence prüfen.',
    closing: 'Vertrag und Notartermin.',
  } : {
    vorbereitung: 'Wir bereiten dein Mandat vor: Unterlagen, Exposé, Mandatsvertrag.',
    markt: 'mibeca spricht Interessenten an, holt NDAs ein und koordiniert Erstgespräche.',
    verhandlung: 'Indikative Angebote, LOI und Due Diligence stehen an.',
    closing: 'Vertragsunterzeichnung, Notartermin, Erfolgsmeldung.',
  }
  return txt[key] || ''
})
function phasenStatus(p) {
  if (isPhaseDone(p)) return 'done'
  if (phasen.value[currentPhase.value - 1]?.id === p.id) return 'current'
  return 'pending'
}
const filteredDok = computed(() => dokumente.value.filter(d => d.ordner === selectedOrdner.value))

function countInOrdner(o) { return dokumente.value.filter(d => d.ordner === o).length }

async function loadAllData() {
  if (targetId) {
    try {
      target.value = await authFetch('/target-get', { method: 'POST', data: { id: targetId } })
      checkliste.value = JSON.parse(target.value.checklisteJson || '[]')
    } catch {} finally { loadingCheck.value = false }
    try { interessenten.value = await getInteressenten(targetId) } catch {} finally { loadingInt.value = false }
    // Dokumente bei Bedarf separat ueber DokumenteAkte (nicht hier)
  } else if (props.impersonating && props.projekttyp) {
    // Admin testet eine Ansicht – leere Liste, in echter Sitzung kommt sie aus dem Target
    checkliste.value = []
    loadingCheck.value = false; loadingInt.value = false
  } else {
    loadingCheck.value = false; loadingInt.value = false
  }
  // Links IMMER neu setzen – System-Links bei UVE auch im Impersonation-Mode
  try {
    const isUve = (target.value?.projekttyp || props.projekttyp || '').toLowerCase().includes('uve')
    const systemLinks = isUve ? [
      { id: 'sys-uve-kurs', system: true, kategorie: 'Kajabi Videokurse', titel: 'UVE Videokurse', url: 'https://www.mike-bergmann-akademie.de/products/mb058-uv-expressweg', beschreibung: 'Unternehmensverkauf-Expressweg – Videokurse von Mike Bergmann.' },
      { id: 'sys-uve-livecall', system: true, kategorie: 'Live-Calls', titel: 'UVE Live Call (Zoom)', url: 'https://us02web.zoom.us/j/85389200945?pwd=btDgPrB3awzuJNtxh8nrU8zX1cQSIb.1', beschreibung: 'Wiederkehrender Live Call zum UVE.' },
    ] : []
    // Veröffentlichte Ausschreibung -> automatisch als Link
    try {
      const landing = target.value?.landingJson ? JSON.parse(target.value.landingJson) : null
      if (landing?.status === 'published' && target.value?.mbNr) {
        const url = `${window.location.origin}/${target.value.mbNr.toLowerCase()}`
        systemLinks.push({
          id: 'sys-ausschreibung', system: true, kategorie: 'Meine Ausschreibung',
          titel: `Öffentliche Ausschreibung ${target.value.mbNr.toUpperCase()}`,
          url, beschreibung: 'Hier siehst du, wie deine Ausschreibung im Internet aussieht. Diesen Link kannst du an Interessenten schicken.',
        })
      }
    } catch {}
    const custom = target.value?.linksJson ? JSON.parse(target.value.linksJson) : []
    links.value = [...systemLinks, ...custom.filter(l => !systemLinks.some(s => s.id === l.id))]
  } catch { links.value = [] }
}

const unreadTotal = ref(0)
async function pollUnread() {
  try { const r = await verlaufUnreadCount(); unreadTotal.value = r?.total || 0 } catch {}
}
async function openVerlauf() {
  tab.value = 'verlauf'
  try { if (targetId) await verlaufMarkRead(targetId); unreadTotal.value = 0 } catch {}
}
let unreadTimer = null
onMounted(() => {
  loadAllData()
  pollUnread()
  unreadTimer = setInterval(pollUnread, 30000)
})
import { onBeforeUnmount } from 'vue'
onBeforeUnmount(() => { if (unreadTimer) clearInterval(unreadTimer) })
watch(() => props.projekttyp, loadAllData)

async function persistLinks() {
  if (!targetId) return
  const custom = links.value.filter(l => !l.system)
  await authFetch('/target-update', { method: 'POST', data: { id: targetId, linksJson: JSON.stringify(custom) } })
}

async function createLink() {
  if (!linkForm.value.titel || !linkForm.value.url) return
  const newLink = { id: 'l-' + Date.now(), ...linkForm.value, targetId }
  links.value.push(newLink)
  showLinkModal.value = false
  linkForm.value = { titel: '', url: '', beschreibung: '', kategorie: 'Allgemein' }
  await persistLinks()
}

async function deleteLink(l) {
  if (!confirm('Link löschen?')) return
  links.value = links.value.filter(x => (x.id || x.RowKey) !== (l.id || l.RowKey))
  await persistLinks()
}

async function toggleItem(item) {
  item.done = !item.done
  if (!targetId) return
  try {
    await authFetch('/target-update', { method: 'POST', data: { id: targetId, checklisteJson: JSON.stringify(checkliste.value) } })
  } catch (e) { console.error(e) }
}

async function setRating(i, n) {
  i.rating = n
  try { await updateInteressent(i.RowKey, { rating: n }) } catch (e) { console.error(e) }
}

async function toggleFreigabe(i) {
  i.freigegebenFuerKontakt = !i.freigegebenFuerKontakt
  try { await updateInteressent(i.RowKey, { freigegebenFuerKontakt: i.freigegebenFuerKontakt }) } catch (e) { console.error(e) }
}

function openVeto(i) { vetoTarget.value = i }
async function confirmVeto() {
  vetoTarget.value.veto = true
  vetoTarget.value.vetoBegruendung = vetoText.value
  try { await updateInteressent(vetoTarget.value.RowKey, { veto: true, vetoBegruendung: vetoText.value }) } catch (e) { console.error(e) }
  vetoTarget.value = null; vetoText.value = ''
}
async function removeVeto(i) {
  i.veto = false; i.vetoBegruendung = ''
  try { await updateInteressent(i.RowKey, { veto: false, vetoBegruendung: '' }) } catch (e) { console.error(e) }
}

function ndaClass(s) {
  if (s === 'unterzeichnet') return 'bg-green-100 text-green-700'
  if (s === 'gesendet') return 'bg-yellow-100 text-yellow-700'
  if (s === 'abgelehnt') return 'bg-red-100 text-red-700'
  return 'bg-gray-100 text-gray-500'
}
function ndaLabel(s) {
  return { unterzeichnet:'NDA unterzeichnet', gesendet:'NDA gesendet', abgelehnt:'NDA abgelehnt' }[s] || 'NDA ausstehend'
}

async function openOrdner(o) { selectedOrdner.value = o }
</script>
