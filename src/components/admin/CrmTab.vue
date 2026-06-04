<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-xl font-bold text-gray-900">Kundenstamm</h2>
      <div class="flex gap-2">
        <button @click="toggleView" class="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-xl text-sm hover:bg-gray-50">
          <Map v-if="view === 'list'" class="w-4 h-4" /> <List v-else class="w-4 h-4" />
          {{ view === 'list' ? 'Kartenansicht' : 'Listenansicht' }}
        </button>
        <button @click="exportCsv" class="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-xl text-sm hover:bg-gray-50">
          <Download class="w-4 h-4" /> Exportieren
        </button>
        <button @click="showImport = true" class="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-xl text-sm hover:bg-gray-50">
          <Upload class="w-4 h-4" /> Importieren
        </button>
        <button @click="runBackfill" :disabled="backfillRunning" class="flex items-center gap-2 px-3 py-2 border border-amber-200 bg-amber-50 text-amber-800 rounded-xl text-sm hover:bg-amber-100 disabled:opacity-60">
          {{ backfillRunning ? 'Lädt…' : 'Verlauf nachtragen' }}
        </button>
        <button @click="runVersandStats" :disabled="statsRunning" class="flex items-center gap-2 px-3 py-2 border border-blue-200 bg-blue-50 text-blue-800 rounded-xl text-sm hover:bg-blue-100 disabled:opacity-60">
          {{ statsRunning ? 'Lädt…' : 'Versand-Recherche' }}
        </button>
        <button @click="showNewModal = true" class="flex items-center gap-2 px-3 py-2 bg-[#0088ba] text-white rounded-xl text-sm hover:bg-[#00a0d8]">
          <UserPlus class="w-4 h-4" /> Neuer Kontakt
        </button>
      </div>
    </div>

    <!-- Vereinheitlichte Filter-Zeile (gilt für Liste UND Karte) -->
    <div class="bg-white rounded-xl border border-gray-100 p-3 mb-3">
      <div class="flex gap-3 flex-wrap items-center">
        <div class="relative flex-1 min-w-[260px] max-w-md">
          <Search class="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
          <input v-model="search" placeholder="Suche: Firma, Name, E-Mail…" class="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30" />
        </div>
        <select v-model="filterStatus" class="border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none">
          <option value="">Status (alle)</option>
          <option>Investor</option>
          <option>Kunde</option>
          <option>Ex-Kunde</option>
          <option>Nichtkunde</option>
        </select>
        <label class="flex items-center gap-1.5 text-xs text-gray-600 cursor-pointer select-none">
          <input type="checkbox" v-model="showDuplikate" class="rounded text-[#0088ba]" />
          nur Duplikate
        </label>
        <!-- Investor-Sub-Typ: nur sichtbar wenn Investor gewählt -->
        <select v-if="filterStatus === 'Investor'" v-model="filterTyp" class="border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none">
          <option value="">Investor-Typ (alle)</option>
          <option>PE</option>
          <option>Systemhausgruppe</option>
          <option>Strategisch</option>
          <option>Sonstige</option>
        </select>
        <div class="flex items-center gap-2 border-l border-gray-200 pl-3">
          <label class="text-xs font-medium text-gray-600">PLZ</label>
          <input v-model="filterCenterPlz" placeholder="z.B. 80331" maxlength="5"
            class="w-24 px-2 py-1.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30" />
          <label class="text-xs font-medium text-gray-600">Umkreis</label>
          <select v-model.number="filterRadiusKm" class="px-2 py-1.5 border border-gray-200 rounded-lg text-sm focus:outline-none">
            <option :value="0">alle</option>
            <option :value="25">25 km</option>
            <option :value="50">50 km</option>
            <option :value="100">100 km</option>
            <option :value="200">200 km</option>
            <option :value="500">500 km</option>
          </select>
        </div>
        <button @click="showProduktFilter = !showProduktFilter" :class="['flex items-center gap-1.5 px-3 py-2 border rounded-xl text-sm', selectedProdukte.length ? 'border-[#0088ba] bg-[#0088ba]/5 text-[#0088ba]' : 'border-gray-200 text-gray-600 hover:bg-gray-50']">
          <Filter class="w-4 h-4" /> Produkte
          <span v-if="selectedProdukte.length" class="bg-[#0088ba] text-white text-[10px] px-1.5 py-0.5 rounded-full">{{ selectedProdukte.length }}</span>
        </button>
        <button v-if="hasAnyFilter" @click="clearAllFilters" class="text-xs text-gray-500 hover:text-gray-800 underline">Filter zurücksetzen</button>
        <div class="flex-1"></div>
        <span class="text-sm text-gray-500"><strong class="text-gray-800">{{ visibleList.length }}</strong> Treffer</span>
      </div>
      <!-- Produkt-Filter (aufklappbar) -->
      <div v-if="showProduktFilter" class="mt-3 pt-3 border-t border-gray-100">
        <div class="text-xs font-medium text-gray-600 mb-2">Produkte / Kundenart (Mehrfachauswahl)</div>
        <div class="flex flex-wrap gap-1.5">
          <button v-for="p in produktListe" :key="p.key"
            @click="toggleProdukt(p.key)"
            :class="['flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium border transition-colors',
                     selectedProdukte.includes(p.key) ? `${p.color} text-white border-transparent` : 'border-gray-200 text-gray-600 hover:bg-gray-50']">
            {{ p.label }}
            <span class="opacity-70">({{ countProdukt(p.key) }})</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Listenansicht -->
    <div v-if="view === 'list'" class="bg-white rounded-xl border border-gray-100 overflow-hidden">
      <div v-if="loading" class="p-8 text-center text-gray-400 text-sm">Lade Kontakte…</div>
      <div v-else-if="!visibleList.length" class="p-8 text-center text-gray-400 text-sm">
        Keine Treffer mit aktuellem Filter. <button @click="clearAllFilters" class="underline hover:text-gray-700">zurücksetzen</button>
      </div>
      <table v-else class="w-full">
        <thead class="bg-gray-50 border-b border-gray-100">
          <tr>
            <th class="text-left px-3 py-3 w-10">
              <input type="checkbox" :checked="allVisibleSelected" @change="toggleAllVisible"
                class="rounded border-gray-300 text-[#0088ba] focus:ring-[#0088ba]/30" title="Alle sichtbaren auswählen" />
            </th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Firma</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Name</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Typ</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">PLZ / Ort</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Produkte</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Aktionen</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="k in visibleList" :key="k.RowKey || k.id" :class="['hover:bg-gray-50', selectedIds.has(k.id || k.RowKey) && 'bg-[#0088ba]/5']">
            <td class="px-3 py-3">
              <input type="checkbox" :checked="selectedIds.has(k.id || k.RowKey)" @change="toggleSelect(k)"
                class="rounded border-gray-300 text-[#0088ba] focus:ring-[#0088ba]/30" />
            </td>
            <td class="px-4 py-3 text-sm font-medium text-gray-800">
              <button @click="openAkte(k)" class="text-left hover:text-[#0088ba] hover:underline">{{ k.firma }}</button>
            </td>
            <td class="px-4 py-3 text-sm text-gray-600">{{ k.name }}</td>
            <td class="px-4 py-3">
              <div class="flex flex-wrap gap-1">
                <span v-if="k.istTarget" class="text-xs px-2 py-0.5 rounded-full font-medium bg-orange-100 text-orange-700">Target</span>
                <span v-if="k.istInvestor" class="text-xs px-2 py-0.5 rounded-full font-medium bg-green-100 text-green-700">
                  Investor<span v-if="k.investorTyp || (k.typ && ['PE','Systemhausgruppe','Strategisch','Sonstige'].includes(k.typ))"> · {{ k.investorTyp || k.typ }}</span>
                </span>
                <span v-if="k.istKunde" class="text-xs px-2 py-0.5 rounded-full font-medium bg-blue-100 text-blue-700">Kunde</span>
                <span v-if="k.istExKunde" class="text-xs px-2 py-0.5 rounded-full font-medium bg-slate-200 text-slate-700">Ex-Kunde</span>
                <span v-if="!k.istTarget && !k.istInvestor && !k.istKunde && !k.istExKunde && k.typ" :class="typClass(k.typ)" class="text-xs px-2 py-0.5 rounded-full font-medium">{{ k.typ }}</span>
              </div>
            </td>
            <td class="px-4 py-3 text-sm text-gray-500">{{ k.plz }} {{ k.ort }}</td>
            <td class="px-4 py-3">
              <div class="flex flex-wrap gap-1">
                <span v-for="p in produktListe.filter(p => k[p.key])" :key="p.key"
                  :class="[p.color, 'text-white text-[10px] font-bold px-1.5 py-0.5 rounded']" :title="p.label">
                  {{ p.label }}
                </span>
              </div>
            </td>
            <td class="px-4 py-3">
              <a v-if="k.email" :href="`mailto:${k.email}`" class="inline-flex items-center gap-1 text-xs text-[#0088ba] hover:text-[#00a0d8] mr-2">
                <Mail class="w-3.5 h-3.5" /> Anschreiben
              </a>
              <button @click="openEdit(k)" class="text-xs text-gray-400 hover:text-gray-600">
                <Pencil class="w-3.5 h-3.5" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Kartenansicht (DACH) -->
    <div v-else>
      <div class="bg-white rounded-xl border border-gray-100 p-3 mb-3 flex items-center justify-between text-xs">
        <div class="text-gray-500 flex items-center gap-2 flex-wrap">
          <strong class="text-gray-800">{{ visibleList.length }}</strong> {{ filterRadiusKm ? 'Kontakte im Radius' : 'Kontakte sichtbar' }} ·
          <strong class="text-orange-600">{{ visibleTargets.length }}</strong> {{ filterRadiusKm ? 'Targets im Radius' : 'Targets gesamt' }} ·
          <strong class="text-gray-400">{{ mapData.withoutCoords || 0 }}</strong> ohne PLZ
          <span v-if="selectedProdukte.length" class="flex items-center gap-1 ml-2">
            · Pins gefärbt nach
            <span v-for="(p, i) in selectedProdukte" :key="p" class="flex items-center gap-1">
              <span class="w-2.5 h-2.5 rounded-full" :style="`background:${produktHexColor(p)}`"></span>
              <strong>{{ produktLabel(p) }}</strong>{{ i < selectedProdukte.length - 1 ? ',' : '' }}
            </span>
          </span>
        </div>
        <div class="flex items-center gap-3">
          <button @click="exportFilteredCsv" class="flex items-center gap-1.5 px-3 py-1 border border-gray-200 rounded-lg hover:bg-gray-50">
            <Download class="w-3 h-3" /> Auswahl exportieren ({{ visibleList.length }})
          </button>
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full" style="background:#f97316"></span>Target</span>
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full" style="background:#22c55e"></span>Investor</span>
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full" style="background:#60a5fa"></span>Kunde</span>
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full" style="background:#475569"></span>Ex-Kunde</span>
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full border border-gray-300" style="background:#d4d4d8"></span>Nichtkunde</span>
        </div>
      </div>
      <KundenMap
        :kontakte="visibleList.filter(k => k.lat && k.lon)"
        :targets="visibleTargets"
        :center-plz="filterCenterPlz"
        :center-coords="centerCoords"
        :radius-km="filterRadiusKm"
        :color-by-produkt="selectedProdukte[0] || ''" />
    </div>

    <!-- Sticky Aktion-Leiste bei Auswahl -->
    <div v-if="selectedCount > 0" class="fixed bottom-4 left-1/2 -translate-x-1/2 bg-[#161e2a] text-white rounded-2xl shadow-2xl px-5 py-3 flex items-center gap-4 z-40">
      <div class="flex items-center gap-2 text-sm">
        <CheckCircle class="w-5 h-5 text-[#c8b274]" />
        <strong>{{ selectedCount }}</strong> ausgewählt
      </div>
      <div class="w-px h-6 bg-white/20"></div>
      <button @click="clearSelection" class="text-xs text-gray-300 hover:text-white">Auswahl löschen</button>
      <div class="w-px h-6 bg-white/20"></div>
      <button @click="showAusschreibungModal = true" class="flex items-center gap-2 px-4 py-2 bg-[#0088ba] hover:bg-[#00a0d8] rounded-xl text-sm font-medium">
        <Megaphone class="w-4 h-4" /> Ausschreibung versenden
      </button>
    </div>

    <!-- Ausschreibung-Versand Modal -->
    <div v-if="showAusschreibungModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div class="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between sticky top-0 bg-white z-10">
          <div>
            <h3 class="font-bold text-gray-900">Ausschreibung versenden</h3>
            <p class="text-xs text-gray-500 mt-0.5">An {{ selectedCount }} ausgewählte Kontakte</p>
          </div>
          <button @click="showAusschreibungModal = false"><X class="w-5 h-5 text-gray-400" /></button>
        </div>
        <div class="p-6 space-y-4">
          <!-- Target wählen -->
          <div>
            <label class="text-xs font-medium text-gray-600 mb-1 block">Für welches Target ist die Ausschreibung? *</label>
            <select v-model="ausschreibungForm.targetId" @change="prefillTemplate" class="input">
              <option value="">— Target auswählen —</option>
              <option v-for="t in mapData.targets || []" :key="t.id" :value="t.id">
                {{ t.mbNr }} · {{ t.verkaueferName }} ({{ t.plz }} {{ t.ort }})
              </option>
            </select>
          </div>

          <div>
            <label class="text-xs font-medium text-gray-600 mb-1 block">Betreff *</label>
            <input v-model="ausschreibungForm.betreff" placeholder="z.B. IT-Systemhaus zu verkaufen – {{ mb-XXX }}" class="input" />
          </div>

          <div>
            <label class="text-xs font-medium text-gray-600 mb-1 block">Verteiler-Beschreibung <span class="text-gray-400">(für Mandant-Verlauf)</span></label>
            <input v-model="ausschreibungForm.filterBeschreibung" placeholder="z.B. alle Kontakte / IT-Branche DACH / PLZ 80000–99999 Bayern" class="input" />
          </div>

          <div>
            <label class="text-xs font-medium text-gray-600 mb-1 block">Anschreiben</label>
            <div class="flex flex-wrap gap-1 mb-1">
              <span class="text-[10px] text-gray-400 self-center mr-1">Platzhalter einfügen:</span>
              <button v-for="ph in ['vorname','firma','name','ort','mbNr','exposeUrl']" :key="ph"
                type="button" @click="insertPlatzhalter('{' + ph + '}')"
                class="text-[10px] px-2 py-0.5 rounded border border-gray-200 hover:border-[#0088ba] hover:text-[#0088ba] text-gray-600 bg-white">
                + {{ '{' + ph + '}' }}
              </button>
            </div>
            <textarea v-model="ausschreibungForm.text" ref="anschreibenRef" rows="10" class="input resize-none font-mono text-xs leading-relaxed"></textarea>
            <p class="text-xs text-gray-400 mt-1">Klick die Platzhalter oben, um sie an der Cursor-Position einzufügen.</p>
          </div>

          <!-- Vorschau erster Empfänger -->
          <div v-if="firstSelected" class="bg-gray-50 rounded-xl p-4 border border-gray-200">
            <div class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Vorschau (erste Auswahl: {{ firstSelected.firma || firstSelected.name }})</div>
            <div class="text-xs text-gray-500 mb-1"><strong>An:</strong> {{ firstSelected.email }}</div>
            <div class="text-xs text-gray-500 mb-2"><strong>Betreff:</strong> {{ replaceVars(ausschreibungForm.betreff, firstSelected) }}</div>
            <div class="text-sm text-gray-700 whitespace-pre-wrap border-t border-gray-200 pt-2">{{ replaceVars(ausschreibungForm.text, firstSelected) }}</div>
          </div>
        </div>
        <div v-if="sendProgress" class="px-6 py-3 border-t border-gray-100 bg-blue-50">
          <div class="text-xs text-gray-700 mb-1.5 flex justify-between">
            <span>Versand läuft: <strong>{{ sendProgress.current }} / {{ sendProgress.total }}</strong></span>
            <span>{{ sendProgress.sent }} ✓ · {{ sendProgress.skipped }} übersprungen · {{ sendProgress.failed }} Fehler</span>
          </div>
          <div class="w-full bg-white rounded-full h-2 overflow-hidden">
            <div class="bg-[#0088ba] h-full transition-all" :style="`width: ${(sendProgress.current / sendProgress.total) * 100}%`"></div>
          </div>
        </div>
        <div class="px-6 py-4 border-t border-gray-100 sticky bottom-0 bg-white flex flex-wrap justify-end gap-2">
          <button @click="showAusschreibungModal = false" class="px-4 py-2 text-sm border border-gray-200 rounded-xl">Abbrechen</button>
          <button @click="sendTestMail" :disabled="!ausschreibungForm.targetId || !ausschreibungForm.betreff || !ausschreibungForm.text || sending"
            class="flex items-center gap-2 px-4 py-2 border border-amber-200 bg-amber-50 text-amber-800 rounded-xl text-sm disabled:opacity-50">
            <Send class="w-4 h-4" /> Test-Mail an mich
          </button>
          <button @click="sendMailto" :disabled="!canSend" class="flex items-center gap-2 px-4 py-2 bg-gray-700 text-white rounded-xl text-sm disabled:opacity-50">
            <Mail class="w-4 h-4" /> E-Mail-App öffnen
          </button>
          <button @click="downloadCsv" :disabled="!canSend" class="flex items-center gap-2 px-4 py-2 border border-[#0088ba] text-[#0088ba] rounded-xl text-sm disabled:opacity-50">
            <Download class="w-4 h-4" /> Für Serien-Mail (CSV)
          </button>
          <button @click="sendAcs" :disabled="!canSend || sending" class="flex items-center gap-2 px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium disabled:opacity-50">
            <Send class="w-4 h-4" /> {{ sending ? 'Sende…' : 'Direkt senden (ACS)' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Sicherheits-Modal: potenzielle Mandanten-Mitarbeiter -->
    <div v-if="riskyModal" class="fixed inset-0 bg-black/60 flex items-center justify-center z-[60] px-4">
      <div class="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden shadow-2xl">
        <div class="px-6 py-4 border-b border-red-100 bg-red-50">
          <h3 class="font-bold text-red-900 flex items-center gap-2">
            <AlertCircle class="w-5 h-5" /> Sicherheits-Prüfung: mögliche Mandanten-Mitarbeiter
          </h3>
          <p class="text-xs text-red-800 mt-1">
            Es wurden {{ riskyModal.risky.length }} Empfänger gefunden, die möglicherweise zum Mandanten gehören.
            <strong>Vor dem Versand bitte prüfen</strong> — Haken setzen bedeutet „ist KEIN Mandanten-Mitarbeiter, darf Mail bekommen".
          </p>
        </div>
        <div class="p-6 overflow-y-auto flex-1 space-y-2">
          <div v-for="entry in riskyModal.risky" :key="entry.idx"
            class="flex items-start gap-3 p-3 rounded-xl border border-gray-200 hover:bg-gray-50">
            <input type="checkbox"
              :checked="!riskyAusgeschlossen.has(entry.idx)"
              @change="e => { const s = new Set(riskyAusgeschlossen); if (e.target.checked) s.delete(entry.idx); else s.add(entry.idx); riskyAusgeschlossen = s }"
              class="mt-1" />
            <div class="flex-1 min-w-0">
              <div class="font-semibold text-sm">{{ entry.recipient.firma || entry.recipient.name }}</div>
              <div class="text-xs text-gray-600 truncate">{{ entry.recipient.email }}</div>
              <div class="text-[10px] text-red-700 mt-1 italic">⚠ {{ entry.grund }}</div>
            </div>
          </div>
        </div>
        <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50">
          <div class="text-xs text-gray-600">
            {{ riskyModal.allRecipients.length - riskyAusgeschlossen.size }} von {{ riskyModal.allRecipients.length }} Empfängern werden Mails erhalten
          </div>
          <div class="flex gap-2">
            <button @click="riskyModal = null" class="px-4 py-2 text-sm border border-gray-200 rounded-xl">Abbrechen</button>
            <button @click="confirmRiskyAndSend" :disabled="sending"
              class="px-4 py-2 bg-red-600 text-white rounded-xl text-sm font-semibold hover:bg-red-700 disabled:opacity-50">
              {{ sending ? 'Sende…' : 'So versenden' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Import Modal -->
    <div v-if="showImport" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div class="bg-white rounded-2xl p-6 w-full max-w-sm">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold text-gray-900">Kontakte importieren</h3>
          <button @click="showImport = false"><X class="w-5 h-5 text-gray-400" /></button>
        </div>
        <p class="text-sm text-gray-500 mb-4">JSON-Array mit Kontakten einfügen oder CSV-Datei hochladen:</p>
        <textarea v-model="importJson" rows="6" class="w-full border border-gray-200 rounded-xl px-3 py-2 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 resize-none" placeholder='[{"firma":"Musterfirma","name":"Max Muster","email":"m@example.de","typ":"PE","plz":"80000","ort":"München"}]'></textarea>
        <div class="flex gap-3 mt-4">
          <button @click="showImport = false" class="flex-1 px-4 py-2 text-sm border border-gray-200 rounded-xl hover:bg-gray-50">Abbrechen</button>
          <button @click="doImport" :disabled="importing" class="flex-1 px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium disabled:opacity-50">
            {{ importing ? 'Importiere…' : 'Importieren' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Neuer Kontakt / Bearbeiten Modal -->
    <div v-if="showNewModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div class="bg-white rounded-2xl p-6 w-full max-w-lg">
        <div class="flex items-center justify-between mb-5">
          <h3 class="font-bold text-gray-900">{{ editKontakt ? 'Kontakt bearbeiten' : 'Neuer Kontakt' }}</h3>
          <button @click="closeModal"><X class="w-5 h-5 text-gray-400" /></button>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div class="col-span-2"><label class="field-label">Firma</label><input v-model="form.firma" class="input" /></div>
          <div><label class="field-label">Geschäftsführer</label><input v-model="form.geschaeftsfuehrer" placeholder="z.B. Max Mustermann" class="input" /></div>
          <div><label class="field-label">Name (Ansprechpartner)</label><input v-model="form.name" class="input" /></div>
          <div><label class="field-label">E-Mail (primär)</label><input v-model="form.email" type="email" class="input" /></div>
          <div><label class="field-label">Telefon (primär)</label><input v-model="form.telefon" class="input" /></div>

          <!-- Weitere E-Mails -->
          <div class="col-span-2">
            <label class="field-label">Weitere E-Mails</label>
            <div v-for="(e, i) in weitereEmails" :key="'e'+i" class="flex gap-2 mb-1">
              <input v-model="e.wert" placeholder="zusatz@beispiel.de" type="email" class="input flex-1" />
              <input v-model="e.label" placeholder="Label (privat/business…)" class="input w-40" />
              <button type="button" @click="weitereEmails.splice(i, 1)" class="px-2 text-red-500 hover:bg-red-50 rounded">✕</button>
            </div>
            <button type="button" @click="weitereEmails.push({ wert: '', label: '' })" class="text-xs text-[#0088ba] hover:underline">+ Weitere E-Mail</button>
          </div>

          <!-- Weitere Telefone -->
          <div class="col-span-2">
            <label class="field-label">Weitere Telefon-Nummern</label>
            <div v-for="(p, i) in weiterePhones" :key="'p'+i" class="flex gap-2 mb-1">
              <input v-model="p.wert" placeholder="+49 …" class="input flex-1" />
              <input v-model="p.label" placeholder="Label (mobil/büro…)" class="input w-40" />
              <button type="button" @click="weiterePhones.splice(i, 1)" class="px-2 text-red-500 hover:bg-red-50 rounded">✕</button>
            </div>
            <button type="button" @click="weiterePhones.push({ wert: '', label: '' })" class="text-xs text-[#0088ba] hover:underline">+ Weitere Telefon-Nummer</button>
          </div>

          <div><label class="field-label">Website</label><input v-model="form.website" class="input" /></div>
          <div><label class="field-label">Branche</label><input v-model="form.branche" placeholder="z.B. IT-Systemhaus" class="input" /></div>
          <div><label class="field-label">PLZ</label><input v-model="form.plz" class="input" /></div>
          <div><label class="field-label">Ort</label><input v-model="form.ort" class="input" /></div>

          <!-- Geschäftskennzahlen (für Kandidaten-Match) -->
          <div class="col-span-2 border-t border-gray-100 pt-4 mt-2">
            <div class="text-xs font-semibold text-gray-700 mb-2">Geschäftskennzahlen <span class="text-gray-400 font-normal">– für Kandidaten-Match</span></div>
            <div class="grid grid-cols-2 gap-3">
              <div><label class="field-label">Mitarbeiter (Anzahl)</label><input v-model.number="form.mitarbeiter" type="number" min="0" placeholder="z.B. 25" class="input" /></div>
              <div><label class="field-label">Umsatz (TEUR)</label><input v-model.number="form.umsatzTeur" type="number" min="0" placeholder="z.B. 2500" class="input" /></div>
              <div><label class="field-label">EBIT-Marge (%)</label><input v-model.number="form.ebitMarge" type="number" step="0.5" placeholder="z.B. 8" class="input" /></div>
              <div><label class="field-label">Wiederkehrende Umsätze (%)</label><input v-model.number="form.recurringPct" type="number" min="0" max="100" placeholder="z.B. 30" class="input" /></div>
            </div>
          </div>

          <!-- Multi-Rollen Checkboxen -->
          <div class="col-span-2">
            <label class="field-label">Rollen (mehrere möglich)</label>
            <div class="flex flex-wrap gap-3 mt-1">
              <label class="flex items-center gap-1.5 text-sm cursor-pointer">
                <input type="checkbox" v-model="form.istKunde" class="rounded text-[#0088ba]" /> Kunde
              </label>
              <label class="flex items-center gap-1.5 text-sm cursor-pointer">
                <input type="checkbox" v-model="form.istExKunde" class="rounded text-[#0088ba]" /> Ex-Kunde
              </label>
              <label class="flex items-center gap-1.5 text-sm cursor-pointer">
                <input type="checkbox" v-model="form.istInvestor" class="rounded text-[#0088ba]" /> Investor
              </label>
              <label class="flex items-center gap-1.5 text-sm cursor-pointer">
                <input type="checkbox" v-model="form.istTarget" class="rounded text-[#0088ba]" /> Target
              </label>
            </div>
          </div>
          <div v-if="form.istInvestor" class="col-span-2">
            <label class="field-label">Investor-Typ</label>
            <select v-model="form.investorTyp" class="input">
              <option value="">— wählen —</option>
              <option>PE</option><option>Systemhausgruppe</option><option>Strategisch</option><option>Sonstige</option>
            </select>
          </div>

          <div class="col-span-2"><label class="field-label">Sucht</label><input v-model="form.sucht" class="input" /></div>
          <div class="col-span-2"><label class="field-label">Bietet</label><input v-model="form.bietet" class="input" /></div>
          <div class="col-span-2"><label class="field-label">Kommentar</label><textarea v-model="form.kommentar" rows="2" class="input resize-none"></textarea></div>

          <!-- Weitere Ansprechpartner -->
          <div class="col-span-2 border-t border-gray-100 pt-4 mt-2">
            <div class="flex items-center justify-between mb-2">
              <label class="field-label">Weitere Ansprechpartner</label>
              <button type="button" @click="addAnsprechpartner" class="text-xs text-[#0088ba] hover:text-[#00a0d8] flex items-center gap-1">
                <Plus class="w-3 h-3" /> Hinzufügen
              </button>
            </div>
            <div v-if="!ansprechpartner.length" class="text-xs text-gray-400 italic">Noch keine weiteren Ansprechpartner.</div>
            <div v-else class="space-y-2">
              <div v-for="(a, i) in ansprechpartner" :key="i" class="grid grid-cols-2 gap-2 p-2 bg-gray-50 rounded-lg relative">
                <input v-model="a.name" placeholder="Name" class="input text-xs" />
                <input v-model="a.position" placeholder="Position (z.B. GF, Buchhaltung)" class="input text-xs" />
                <input v-model="a.email" type="email" placeholder="E-Mail" class="input text-xs" />
                <input v-model="a.telefon" placeholder="Telefon" class="input text-xs" />
                <button type="button" @click="removeAnsprechpartner(i)" class="absolute top-1 right-1 text-gray-400 hover:text-red-500">
                  <X class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
        <div class="flex gap-3 mt-5">
          <button v-if="editKontakt" @click="deleteCurrentKontakt" :disabled="saving" class="px-4 py-2 text-sm border border-red-200 text-red-600 rounded-xl hover:bg-red-50">
            Löschen
          </button>
          <a v-if="editKontakt && form.firma" :href="northdataLink" target="_blank" rel="noopener"
            class="flex items-center gap-1.5 px-4 py-2 text-sm border border-gray-200 text-gray-600 rounded-xl hover:bg-gray-50">
            Northdata öffnen
          </a>
          <button @click="closeModal" class="flex-1 px-4 py-2 text-sm border border-gray-200 rounded-xl hover:bg-gray-50">Abbrechen</button>
          <button @click="saveKontakt" :disabled="saving" class="flex-1 px-4 py-2 bg-[#0088ba] text-white rounded-xl text-sm font-medium disabled:opacity-50">
            {{ saving ? 'Speichern…' : 'Speichern' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Kundenakte Slide-Over -->
    <KundenAkte
      :kontakt="akteKontakt"
      :targets="mapData.targets || []"
      @close="closeAkte"
      @edit="onAkteEdit"
      @updated="loadData" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { Map, List, Download, Upload, UserPlus, Search, Mail, Pencil, X, CheckCircle, Megaphone, Send, Filter, Plus } from '@lucide/vue'
import { getKontakte, createKontakt, updateKontakt, importKontakte, exportKontakte, deleteKontakt } from '../../api.js'
import { toast } from '../../composables/useToast.js'
import { authFetch } from '../../api.js'
import KundenMap from '../KundenMap.vue'
import KundenAkte from './KundenAkte.vue'

const allKontakte = ref([])
const filtered = ref([])
const mapData = ref({ kontakte: [], targets: [], withoutCoords: 0 })
const loading = ref(true)
const view = ref('list')
const filterCenterPlz = ref('')
const filterRadiusKm = ref(0)
const showDuplikate = ref(false)

// Haversine: Entfernung in km zwischen zwei lat/lon Punkten
function distanceKm(lat1, lon1, lat2, lon2) {
  const R = 6371
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLon = (lon2 - lon1) * Math.PI / 180
  const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2
  return 2 * R * Math.asin(Math.sqrt(a))
}

// Zentrum-Koordinaten für Radius-Filter ermitteln
const plzLookupCache = ref({})
const centerCoords = ref(null)

watch([filterCenterPlz, () => mapData.value.kontakte?.length], async () => {
  if (!filterCenterPlz.value) { centerCoords.value = null; return }
  const plz = filterCenterPlz.value.trim()
  if (plz.length < 2) { centerCoords.value = null; return }

  // 1. Cache?
  if (plzLookupCache.value[plz]) { centerCoords.value = plzLookupCache.value[plz]; return }

  // 2. Exakter Match in unseren Daten?
  const allPoints = [...(mapData.value.targets || []), ...(mapData.value.kontakte || [])]
    .filter(x => x.plz && x.lat && x.lon)
  const exact = allPoints.find(x => x.plz === plz)
  if (exact) {
    centerCoords.value = { lat: exact.lat, lon: exact.lon }
    plzLookupCache.value[plz] = centerCoords.value
    return
  }

  // 3. Backend-Lookup
  try {
    const r = await authFetch('/plz-resolve', { method: 'POST', data: { plz } })
    centerCoords.value = { lat: r.lat, lon: r.lon }
    plzLookupCache.value[plz] = centerCoords.value
  } catch {
    centerCoords.value = null
  }
}, { immediate: true })

// EINE Datenquelle: Map-Daten (haben lat/lon) – wird für Liste und Karte verwendet
const visibleList = computed(() => {
  let r = (mapData.value.kontakte || [])
  // Such-Filter
  if (search.value) {
    const q = search.value.toLowerCase()
    r = r.filter(k => ((k.firma||'') + ' ' + (k.name||'') + ' ' + (k.email||'') + ' ' + (k.telefon||'') + ' ' + (k.ort||'') + ' ' + (k.plz||'') + ' ' + (k.sucht||'') + ' ' + (k.bietet||'') + ' ' + (k.kommentar||'') + ' ' + (k.notizenJson||'') + ' ' + (k.ansprechpartnerJson||'')).toLowerCase().includes(q))
  }
  // Typ-Filter
  if (filterTyp.value) r = r.filter(k => k.typ === filterTyp.value)
  // Status-Filter
  if (filterStatus.value) r = r.filter(k => {
    // Klassifizierungs-Hilfsfunktionen — jeder Kontakt landet in genau einer Kategorie
    const isKunde = k.istKunde === true || k.kundenstatus === 'Kunde'
    const isExKunde = k.istExKunde === true || k.kundenstatus === 'Ex-Kunde'
    const isInvestor = k.istInvestor === true || k.kundenstatus === 'Investor' || ['PE','Systemhausgruppe','Strategisch'].includes(k.typ)
    if (filterStatus.value === 'Kunde') return isKunde
    if (filterStatus.value === 'Ex-Kunde') return isExKunde
    if (filterStatus.value === 'Investor') return isInvestor
    // Nichtkunde = alles, was NICHT in den anderen drei Kategorien ist
    // (umfasst „Nichtkunde", „potenzieller Kunde", „Partner", „nicht geeignet", etc.)
    if (filterStatus.value === 'Nichtkunde') return !(isKunde || isExKunde || isInvestor)
    return true
  })
  if (filterTyp.value && filterStatus.value === 'Investor') {
    r = r.filter(k => (k.investorTyp || k.typ) === filterTyp.value)
  }
  // PLZ-Mitte + Umkreis
  if (filterCenterPlz.value && filterRadiusKm.value && centerCoords.value) {
    r = r.filter(k => k.lat && k.lon && distanceKm(centerCoords.value.lat, centerCoords.value.lon, k.lat, k.lon) <= filterRadiusKm.value)
  }
  // Produkt-Filter (Mehrfachauswahl: ALLE ausgewählten müssen wahr sein)
  if (selectedProdukte.value.length) {
    r = r.filter(k => selectedProdukte.value.every(p => k[p] === true))
  }
  // Duplikate-Filter: zeige nur Kontakte, deren Firma mehrfach vorkommt
  if (showDuplikate.value) {
    const firmaCounts = new Map()
    for (const k of r) {
      const f = (k.firma || '').toLowerCase().trim()
      if (f) firmaCounts.set(f, (firmaCounts.get(f) || 0) + 1)
    }
    r = r.filter(k => firmaCounts.get((k.firma || '').toLowerCase().trim()) > 1)
  }
  return r
})

const visibleTargets = computed(() => {
  let r = (mapData.value.targets || [])
  if (filterCenterPlz.value && filterRadiusKm.value && centerCoords.value) {
    r = r.filter(t => t.lat && t.lon && distanceKm(centerCoords.value.lat, centerCoords.value.lon, t.lat, t.lon) <= filterRadiusKm.value)
  }
  return r
})

const hasAnyFilter = computed(() =>
  !!(search.value || filterTyp.value || filterStatus.value || filterCenterPlz.value || filterRadiusKm.value || selectedProdukte.value.length)
)

function clearAllFilters() {
  search.value = ''
  filterTyp.value = ''
  filterStatus.value = ''
  filterCenterPlz.value = ''
  filterRadiusKm.value = 0
  selectedProdukte.value = []
}

function exportFilteredCsv() {
  const items = visibleList.value
  const fields = ['firma','name','email','telefon','plz','ort','typ','kundenstatus']
  const header = fields.join(';')
  const rows = items.map(k => fields.map(f => (k[f] || '').toString().replaceAll(';', ',')).join(';'))
  const csv = '﻿' + [header, ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filterCenterPlz.value && filterRadiusKm.value
    ? `kontakte_radius_${filterCenterPlz.value}_${filterRadiusKm.value}km.csv`
    : 'kontakte_filter.csv'
  a.click()
  URL.revokeObjectURL(url)
}

const search = ref('')
const filterTyp = ref('')
const filterStatus = ref('')
const showProduktFilter = ref(false)
const selectedProdukte = ref([])

const produktListe = [
  { key: 'hatUC', label: 'UC', color: 'bg-red-500' },
  { key: 'hatUCS', label: 'UCS', color: 'bg-purple-500' },
  { key: 'hatMC', label: 'MC', color: 'bg-yellow-500' },
  { key: 'hatFKE', label: 'FKE', color: 'bg-amber-600' },
  { key: 'hatUVE', label: 'UVE', color: 'bg-pink-500' },
  { key: 'hatVME', label: 'VME', color: 'bg-stone-600' },
  { key: 'hatKIwerkOne', label: 'KIwerk.one', color: 'bg-emerald-500' },
  { key: 'hatMSQ', label: 'MSQ', color: 'bg-indigo-500' },
  { key: 'hatKMQ', label: 'KMQ', color: 'bg-cyan-600' },
  { key: 'hatKIT', label: 'KIT', color: 'bg-fuchsia-500' },
]

function toggleProdukt(key) {
  const idx = selectedProdukte.value.indexOf(key)
  if (idx >= 0) selectedProdukte.value.splice(idx, 1)
  else selectedProdukte.value.push(key)
}

function countProdukt(key) {
  return (mapData.value.kontakte || []).filter(k => k[key] === true).length
}

const PRODUKT_HEX = {
  hatUC: '#ef4444', hatUCS: '#a855f7', hatMC: '#eab308', hatFKE: '#d97706',
  hatUVE: '#ec4899', hatVME: '#57534e', hatKIwerkOne: '#10b981',
  hatMSQ: '#6366f1', hatKMQ: '#0891b2', hatKIT: '#d946ef',
}
function produktHexColor(key) { return PRODUKT_HEX[key] || '#64748b' }
function produktLabel(key) { return produktListe.find(p => p.key === key)?.label || key }

// Mehrfach-Auswahl
const selectedIds = ref(new Set())
const selectedCount = computed(() => selectedIds.value.size)
const allVisibleSelected = computed(() => {
  if (!visibleList.value.length) return false
  return visibleList.value.every(k => selectedIds.value.has(k.id || k.RowKey))
})
function toggleSelect(k) {
  const id = k.id || k.RowKey
  const s = new Set(selectedIds.value)
  if (s.has(id)) s.delete(id); else s.add(id)
  selectedIds.value = s
}
function toggleAllVisible() {
  const s = new Set(selectedIds.value)
  const allSelected = allVisibleSelected.value
  for (const k of visibleList.value) {
    const id = k.id || k.RowKey
    if (allSelected) s.delete(id); else s.add(id)
  }
  selectedIds.value = s
}
function clearSelection() {
  selectedIds.value = new Set()
}

const selectedKontakte = computed(() =>
  (mapData.value.kontakte || []).filter(k => selectedIds.value.has(k.id || k.RowKey))
)
const firstSelected = computed(() => selectedKontakte.value[0])

// Ausschreibung-Versand
const showAusschreibungModal = ref(false)
const ausschreibungForm = ref({
  targetId: '',
  betreff: '',
  text: '',
  filterBeschreibung: 'alle Kontakte',
})

const canSend = computed(() =>
  ausschreibungForm.value.targetId && ausschreibungForm.value.betreff && ausschreibungForm.value.text && selectedCount.value > 0
)

function prefillTemplate() {
  const t = (mapData.value.targets || []).find(x => x.id === ausschreibungForm.value.targetId)
  if (!t) return
  const landingUrl = `https://targets.itukv.de/${(t.mbNr || '').toLowerCase()}`
  if (!ausschreibungForm.value.betreff) {
    ausschreibungForm.value.betreff = `IT-Systemhaus zu verkaufen – ${t.mbNr}`
  }
  if (!ausschreibungForm.value.text) {
    ausschreibungForm.value.text =
`Hallo {vorname},

aktuell betreue ich den Verkauf eines IT-Systemhauses (Projektnummer ${t.mbNr}) im Raum ${t.ort || t.region || '—'}.

Das Kurzexposé ist anonymisiert und direkt online einsehbar:

${landingUrl}

Wenn Du Interesse hast, kannst Du dort Deine Daten hinterlegen, das anonyme Exposé herunterladen, die Vertraulichkeitsvereinbarung (NDA) unterzeichnen und einen Termin mit unserer M&A-Beraterin Jennifer Kaplan buchen.

Viele Grüße
Mike Bergmann
mibeca GmbH – M&A-Beratung für IT-Unternehmen
www.itukv.de`
  }
}

const anschreibenRef = ref(null)
function insertPlatzhalter(ph) {
  const ta = anschreibenRef.value
  if (!ta) {
    ausschreibungForm.value.text += ph
    return
  }
  const start = ta.selectionStart
  const end = ta.selectionEnd
  const txt = ausschreibungForm.value.text || ''
  ausschreibungForm.value.text = txt.slice(0, start) + ph + txt.slice(end)
  nextTick(() => {
    ta.focus()
    ta.selectionStart = ta.selectionEnd = start + ph.length
  })
}

function replaceVars(text, k) {
  if (!text || !k) return text || ''
  const vorname = (k.name || '').trim().split(' ')[0] || ''
  const t = (mapData.value.targets || []).find(x => x.id === ausschreibungForm.value.targetId)
  const mbNr = t?.mbNr || ''
  const landingUrl = mbNr ? `https://targets.itukv.de/${mbNr.toLowerCase()}` : ''
  return text
    .replaceAll('{vorname}', vorname)
    .replaceAll('{firma}', k.firma || '')
    .replaceAll('{name}', k.name || '')
    .replaceAll('{ort}', k.ort || '')
    .replaceAll('{mbNr}', mbNr)
    .replaceAll('{exposeUrl}', landingUrl)
}

function sendMailto() {
  const subject = encodeURIComponent(ausschreibungForm.value.betreff)
  const body = encodeURIComponent(ausschreibungForm.value.text)
  const bcc = selectedKontakte.value.map(k => k.email).filter(Boolean).join(',')
  window.location.href = `mailto:?bcc=${bcc}&subject=${subject}&body=${body}`
}

function downloadCsv() {
  const fields = ['firma','name','email','plz','ort','betreff','text']
  const rows = selectedKontakte.value.map(k => [
    k.firma || '', k.name || '', k.email || '', k.plz || '', k.ort || '',
    replaceVars(ausschreibungForm.value.betreff, k),
    replaceVars(ausschreibungForm.value.text, k).replaceAll('\n', ' | ')
  ].map(v => `"${(v + '').replaceAll('"', '""')}"`).join(';'))
  const csv = '﻿' + [fields.join(';'), ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = 'ausschreibung_serienmail.csv'; a.click()
  URL.revokeObjectURL(url)
}

const sending = ref(false)
// Sicherheits-Pruefung: identifiziert Empfaenger, die wahrscheinlich Mitarbeiter
// des Mandanten sind. Pruefkriterien (nur diese zwei):
//   1) E-Mail-Domain == Mandanten-Website-Domain
//   2) Empfaenger-Firmenname enthaelt den (um Rechtsform bereinigten) Mandanten-Firmennamen
function findRiskyRecipients(recipients) {
  const t = (mapData.value.targets || []).find(x => x.id === ausschreibungForm.value.targetId)
  if (!t) return []
  const targetWebsite = (t.website || '').toLowerCase()
    .replace(/^https?:\/\//, '').replace(/^www\./, '').replace(/\/.*$/, '').trim()
  // Mandanten-Firmenname bereinigen: Rechtsform-Suffixe und Punkte/Kommata weg
  const rawFirma = ((t.firma || '') + '').toLowerCase().trim()
  const targetFirmaClean = rawFirma
    .replace(/\b(gmbh & co\. kg|gmbh & co kg|gmbh|ag|kg|ohg|kgaa|ug|gbr|e\.k\.|e\. k\.|e\.v\.|se|ltd)\b/g, '')
    .replace(/[.,]/g, ' ')
    .replace(/\s+/g, ' ').trim()
  const risky = []
  for (let i = 0; i < recipients.length; i++) {
    const r = recipients[i]
    const email = (r.email || '').toLowerCase()
    const firma = (r.firma || '').toLowerCase()
    const domain = email.split('@')[1] || ''
    let grund = null
    // Treffer 1: E-Mail-Domain == Website-Domain des Mandanten
    if (targetWebsite && domain && (domain === targetWebsite || domain.endsWith('.' + targetWebsite) || targetWebsite.endsWith('.' + domain))) {
      grund = `E-Mail-Domain ${domain} = Mandanten-Website ${targetWebsite}`
    }
    // Treffer 2: Empfaenger-Firmenname enthaelt vollstaendigen Mandanten-Firmennamen
    if (!grund && targetFirmaClean.length >= 4 && firma) {
      const firmaNormalized = firma.replace(/[.,]/g, ' ').replace(/\s+/g, ' ').trim()
      if (firmaNormalized.includes(targetFirmaClean)) {
        grund = `Empfaenger-Firma „${r.firma}" enthält Mandanten-Namen „${t.firma}"`
      }
    }
    if (grund) risky.push({ idx: i, recipient: r, grund })
  }
  return risky
}

// Sicherheits-Modal-State
const riskyModal = ref(null) // { risky: [...], allRecipients: [...] }
const riskyAusgeschlossen = ref(new Set())

async function sendAcs() {
  if (!canSend.value) return
  const recipients = selectedKontakte.value.map(k => ({
    email: k.email, firma: k.firma || '', name: k.name || '', ort: k.ort || '',
  })).filter(r => r.email)
  if (!recipients.length) { toast.warn('Keine Empfaenger mit E-Mail.'); return }
  // Sicherheits-Pruefung: wenn riskante Empfaenger gefunden -> Modal zeigen
  const risky = findRiskyRecipients(recipients)
  if (risky.length) {
    riskyAusgeschlossen.value = new Set(risky.map(r => r.idx))  // alle initial ausgeschlossen
    riskyModal.value = { risky, allRecipients: recipients }
    return
  }
  return doSend(recipients)
}

const sendProgress = ref(null)  // { total, sent, failed, skipped, current }
async function doSend(recipients) {
  if (!confirm(`Ausschreibung an ${recipients.length} Empfaenger versenden?`)) return
  sending.value = true
  // Chunk-Size 100 — bleibt unter HTTP-Timeout (4 Min) und schreibt pro Empfaenger sofort
  // einen Verlauf-Eintrag, damit beim Abbruch klar ist, wer schon eine Mail hat.
  const chunkSize = 100
  sendProgress.value = { total: recipients.length, sent: 0, failed: 0, skipped: 0, current: 0 }
  let aborted = false
  try {
    for (let i = 0; i < recipients.length; i += chunkSize) {
      const chunk = recipients.slice(i, i + chunkSize)
      sendProgress.value.current = i + chunk.length
      try {
        const r = await authFetch('/ausschreibung-versand', { method: 'POST', data: {
          targetId: ausschreibungForm.value.targetId,
          betreff: ausschreibungForm.value.betreff,
          text: ausschreibungForm.value.text,
          recipients: chunk,
          skipExisting: true,
          writeMandantInfo: i === 0,  // nur beim ersten Chunk
          filterBeschreibung: ausschreibungForm.value.filterBeschreibung,
        }})
        sendProgress.value.sent += (r.sent || 0)
        sendProgress.value.failed += (r.failed || 0)
        sendProgress.value.skipped += (r.skipped || 0)
        if (r.errors?.length) console.warn(`Chunk ${i/chunkSize+1} Fehler:`, r.errors)
      } catch (e) {
        console.error(`Chunk ${i/chunkSize+1} abgebrochen:`, e)
        aborted = true
        toast.error(`Chunk-Versand abgebrochen bei ${i + chunk.length} von ${recipients.length} — ` + (e?.response?.data?.error || e.message))
        break
      }
    }
    const p = sendProgress.value
    if (!aborted) {
      toast.success(`Versand fertig: ${p.sent} gesendet, ${p.skipped} bereits versendet (übersprungen), ${p.failed} fehlgeschlagen.`)
      showAusschreibungModal.value = false
      riskyModal.value = null
    } else {
      toast.warn(`Bis dahin: ${p.sent} versendet, ${p.skipped} übersprungen, ${p.failed} Fehler. Bei Wiederholung werden bereits versendete automatisch übersprungen.`)
    }
  } finally {
    sending.value = false
    setTimeout(() => { sendProgress.value = null }, 60000)
  }
}

function confirmRiskyAndSend() {
  if (!riskyModal.value) return
  const ausgeschlossen = riskyAusgeschlossen.value
  const finalRecipients = riskyModal.value.allRecipients.filter((_, idx) => !ausgeschlossen.has(idx))
  if (!finalRecipients.length) { toast.warn('Alle Empfaenger ausgeschlossen.'); return }
  doSend(finalRecipients)
}

async function sendTestMail() {
  if (!ausschreibungForm.value.targetId || !ausschreibungForm.value.betreff || !ausschreibungForm.value.text) {
    toast.warn('Bitte Target, Betreff und Text ausfuellen.')
    return
  }
  const meineEmail = sessionStorage.getItem('userEmail') || prompt('Test-Mail an welche Adresse?')
  if (!meineEmail) return
  // Bei Test-Mail: erstes selektiertes Kontakt als Demo-Daten nehmen (fuer Platzhalter)
  const demo = firstSelected.value || { firma: 'Test-Firma', name: 'Test-Name', ort: 'Test-Ort' }
  sending.value = true
  try {
    const r = await authFetch('/ausschreibung-versand', { method: 'POST', data: {
      targetId: ausschreibungForm.value.targetId,
      betreff: ausschreibungForm.value.betreff,
      text: ausschreibungForm.value.text,
      recipients: [{ ...demo }],
      testEmail: meineEmail,
    }})
    if (r.sent) toast.success(`Test-Mail an ${meineEmail} versendet.`)
    else toast.error('Test fehlgeschlagen: ' + JSON.stringify(r.errors?.[0]))
  } catch (e) {
    toast.error('Test fehlgeschlagen: ' + (e?.response?.data?.error || e.message))
  } finally { sending.value = false }
}
const showImport = ref(false)
const showNewModal = ref(false)

// One-Shot: Verlauf-Backfill fuer historische Landing-Page-Eintragungen
const backfillRunning = ref(false)
async function runBackfill() {
  if (!confirm('Verlauf-Einträge für historische Landing-Page-Eintragungen nachtragen? (kann mehrfach laufen, schreibt nichts doppelt)')) return
  backfillRunning.value = true
  try {
    const r = await authFetch('/backfill-kontakt-verlauf', { method: 'POST', data: { dryRun: false } })
    alert(`Fertig!\n\n${r.createdMailOut} × „Ausschreibung versendet" eingetragen\n${r.createdWichtig} × „Landing-Page-Eintragung" eingetragen\n${r.touchedKontakte} Kontakte aktualisiert\n${r.skipped} ohne CRM-Kontakt übersprungen`)
  } catch (e) {
    alert('Backfill fehlgeschlagen: ' + (e?.response?.data?.error || e.message))
  } finally {
    backfillRunning.value = false
  }
}

const statsRunning = ref(false)
async function runVersandStats() {
  const mb = prompt('Welches Mandat? (z.B. mb-250)', 'mb-250')
  if (!mb) return
  statsRunning.value = true
  try {
    const r = await authFetch('/versand-stats', { method: 'POST', data: { mbNr: mb.trim().toLowerCase() } })
    const fmt = d => d ? new Date(d).toLocaleString('de-DE') : '—'
    const preview = (r.preview || []).map(p => `• ${p.firma || p.email} (${fmt(p.datum)})`).join('\n')
    alert(`Ausschreibung ${r.mbNr}\n\nVersendet an: ${r.total} Kontakte\nErster Versand: ${fmt(r.ersterVersand)}\nLetzter Versand: ${fmt(r.letzterVersand)}\n\nErste ${Math.min(20, r.total)} Empfänger:\n${preview}`)
  } catch (e) {
    alert('Recherche fehlgeschlagen: ' + (e?.response?.data?.error || e.message))
  } finally {
    statsRunning.value = false
  }
}
const editKontakt = ref(null)
const akteKontakt = ref(null)
function openAkte(k) { akteKontakt.value = k }
function closeAkte() { akteKontakt.value = null }
function onAkteEdit(k) { akteKontakt.value = null; openEdit(k) }
const importJson = ref('')
const importing = ref(false)
const saving = ref(false)
const form = ref({
  firma: '', name: '', email: '', telefon: '', website: '',
  geschaeftsfuehrer: '', branche: '',
  plz: '', ort: '', sucht: '', bietet: '', kommentar: '',
  mitarbeiter: '', umsatzTeur: '', ebitMarge: '', recurringPct: '',
  istKunde: false, istExKunde: false, istInvestor: false, istTarget: false,
  investorTyp: '',
  typ: '',  // backward compat
})

async function loadData() {
  try {
    mapData.value = await authFetch('/kontakte/locations')
    allKontakte.value = mapData.value.kontakte || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(loadData)

function typClass(t) {
  if (t === 'PE') return 'bg-purple-100 text-purple-700'
  if (t === 'Systemhausgruppe') return 'bg-blue-100 text-blue-700'
  if (t === 'Strategisch') return 'bg-[#0088ba]/10 text-[#0088ba]'
  return 'bg-gray-100 text-gray-600'
}

function toggleView() {
  view.value = view.value === 'list' ? 'map' : 'list'
}

async function exportCsv() {
  try {
    const csv = await exportKontakte()
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'kontakte.csv'; a.click()
    URL.revokeObjectURL(url)
  } catch {
    toast.error('Export fehlgeschlagen')
  }
}

async function doImport() {
  importing.value = true
  try {
    const items = JSON.parse(importJson.value)
    const result = await importKontakte({ items })
    allKontakte.value = await getKontakte()
    applyFilters()
    showImport.value = false
    importJson.value = ''
    toast.success(`${result.imported} Kontakte importiert.`)
  } catch { toast.error('Import fehlgeschlagen – bitte JSON prüfen.') }
  finally { importing.value = false }
}

const ansprechpartner = ref([])
function parseAnsprechpartner(json) {
  try { const a = JSON.parse(json || '[]'); return Array.isArray(a) ? a : [] } catch { return [] }
}
function addAnsprechpartner() { ansprechpartner.value.push({ name: '', position: '', email: '', telefon: '' }) }
function removeAnsprechpartner(i) { ansprechpartner.value.splice(i, 1) }

// Weitere Mails/Telefone fuer den Hauptkontakt
const weitereEmails = ref([])
const weiterePhones = ref([])
function parseJsonArr(s) {
  try { const a = JSON.parse(s || '[]'); return Array.isArray(a) ? a : [] } catch { return [] }
}

function openEdit(k) {
  editKontakt.value = k
  form.value = { ...k }
  ansprechpartner.value = parseAnsprechpartner(k.ansprechpartnerJson)
  weitereEmails.value = parseJsonArr(k.weitereEmailsJson)
  weiterePhones.value = parseJsonArr(k.weiterePhonesJson)
  showNewModal.value = true
}
function closeModal() {
  showNewModal.value = false
  editKontakt.value = null
  form.value = {
    firma:'', name:'', email:'', telefon:'', website:'',
    geschaeftsfuehrer:'', branche:'',
    plz:'', ort:'', sucht:'', bietet:'', kommentar:'', typ:'Sonstige',
    mitarbeiter:'', umsatzTeur:'', ebitMarge:'', recurringPct:'',
    istKunde:false, istExKunde:false, istInvestor:false, istTarget:false, investorTyp:'',
  }
  ansprechpartner.value = []
  weitereEmails.value = []
  weiterePhones.value = []
}

async function saveKontakt() {
  saving.value = true
  try {
    const payload = {
      ...form.value,
      ansprechpartnerJson: JSON.stringify(ansprechpartner.value.filter(a => a.name || a.email || a.telefon)),
      weitereEmailsJson: JSON.stringify(weitereEmails.value.filter(e => e.wert)),
      weiterePhonesJson: JSON.stringify(weiterePhones.value.filter(p => p.wert)),
    }
    if (editKontakt.value) {
      await updateKontakt(editKontakt.value.RowKey, payload)
    } else {
      await createKontakt(payload)
    }
    await loadData()
    closeModal()
  } finally { saving.value = false }
}

async function deleteCurrentKontakt() {
  if (!editKontakt.value) return
  if (!confirm(`Kontakt „${form.value.firma || form.value.name}" wirklich löschen? Das lässt sich nicht rückgängig machen.`)) return
  saving.value = true
  try {
    await deleteKontakt(editKontakt.value.RowKey)
    await loadData()
    closeModal()
    toast.success('Kontakt gelöscht')
  } catch (e) {
    toast.error('Löschen fehlgeschlagen')
  } finally { saving.value = false }
}

const northdataLink = computed(() => {
  const q = encodeURIComponent(`${form.value.firma || ''} ${form.value.plz || ''}`.trim())
  return `https://www.northdata.de/?query=${q}`
})
</script>

<style scoped>
@reference "tailwindcss";
.input { @apply w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0088ba]/30 focus:border-[#0088ba]; }
.field-label { @apply block text-xs font-medium text-gray-600 mb-1; }
</style>
