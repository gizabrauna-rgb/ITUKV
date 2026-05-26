<script setup>
// Öffentliche Signier-Seite. Wird ohne Login geladen über /sign/<token>.
// Workflow:
// 1. Beim Mount laden wir Meta-Infos + PDF-Vorschau.
// 2. Lead klickt "Code anfordern" → wir verschicken 6-stelligen Code per Mail.
// 3. Lead trägt Code ein, zeichnet/tippt Signatur, akzeptiert AGB-Klausel.
// 4. Submit → Backend bettet Signatur ein und schickt signiertes PDF.
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import {
  publicFetchSignInfo, publicFetchSignPdfBlob,
  publicSendSignCode, publicSubmitSignature,
} from "./api.js";

// ── Token aus URL ───────────────────────────────────────────────
const token = (() => {
  const m = window.location.pathname.match(/^\/sign\/([^/?#]+)/);
  return m ? decodeURIComponent(m[1]) : "";
})();

// ── State ───────────────────────────────────────────────────────
const loading = ref(true);
const errorMsg = ref("");
const info = ref(null);
const pdfUrl = ref("");
const phase = ref("review");   // review | sign | done

// Code-Eingabe
const codeRequested = ref(false);
const codeSending = ref(false);
const codeFlash = ref("");
const code = ref("");

// Signatur
const sigMode = ref("drawn");  // drawn | typed
const sigName = ref("");
const acceptAgb = ref(false);

// Canvas für gezeichnete Signatur
const canvasRef = ref(null);
let drawing = false;
let lastPos = null;
let canvasDirty = false;

function _ctx() { return canvasRef.value?.getContext("2d"); }

function _pos(e) {
  const c = canvasRef.value;
  const r = c.getBoundingClientRect();
  const t = (e.touches?.[0]) || e;
  return { x: (t.clientX - r.left) * (c.width / r.width),
           y: (t.clientY - r.top)  * (c.height / r.height) };
}

function startDraw(e) {
  e.preventDefault();
  drawing = true; canvasDirty = true;
  lastPos = _pos(e);
}
function moveDraw(e) {
  if (!drawing) return;
  e.preventDefault();
  const p = _pos(e); const ctx = _ctx();
  ctx.strokeStyle = "#0A2F2F"; ctx.lineWidth = 2.2; ctx.lineCap = "round";
  ctx.beginPath(); ctx.moveTo(lastPos.x, lastPos.y); ctx.lineTo(p.x, p.y); ctx.stroke();
  lastPos = p;
}
function endDraw(e) { e?.preventDefault?.(); drawing = false; }
function clearCanvas() {
  const c = canvasRef.value; if (!c) return;
  const ctx = c.getContext("2d");
  ctx.clearRect(0, 0, c.width, c.height);
  canvasDirty = false;
}

function buildTypedSignaturePng() {
  // Stilisierter Name als Bild: italic, Handschrift-ähnliche Font.
  // Canvas eng am Text, damit beim Einbetten ins PDF kein Leerraum entsteht.
  const c = document.createElement("canvas");
  c.width = 520; c.height = 90;
  const ctx = c.getContext("2d");
  ctx.fillStyle = "#0A2F2F";
  ctx.font = "italic 48px 'Brush Script MT', 'Snell Roundhand', cursive";
  ctx.textBaseline = "middle";
  ctx.fillText(sigName.value || "", 6, 48);
  return c.toDataURL("image/png");
}

function getSignatureDataUrl() {
  if (sigMode.value === "typed") return buildTypedSignaturePng();
  const c = canvasRef.value;
  return c ? c.toDataURL("image/png") : "";
}

// ── Onmount: lade Info + PDF ──────────────────────────────────
onMounted(async () => {
  if (!token) {
    errorMsg.value = "Ungültiger Signier-Link.";
    loading.value = false; return;
  }
  try {
    const i = await publicFetchSignInfo(token);
    info.value = i;
    if (i.status !== "pending") {
      phase.value = i.status === "signed" ? "done" : "expired";
    }
    try {
      pdfUrl.value = await publicFetchSignPdfBlob(token);
    } catch (e) {
      // PDF-Vorschau ist nicht-kritisch
      console.warn("PDF-Vorschau konnte nicht geladen werden:", e);
    }
  } catch (e) {
    errorMsg.value = e.message || "Link konnte nicht geladen werden.";
  } finally {
    loading.value = false;
  }
});

onBeforeUnmount(() => { if (pdfUrl.value) URL.revokeObjectURL(pdfUrl.value); });

// ── Aktionen ──────────────────────────────────────────────────
async function requestCode() {
  codeSending.value = true; errorMsg.value = ""; codeFlash.value = "";
  try {
    await publicSendSignCode(token);
    codeRequested.value = true;
    codeFlash.value = `Code wurde an ${info.value?.lead_email || "Deine Mail"} geschickt.`;
  } catch (e) {
    errorMsg.value = e.message || "Code konnte nicht versendet werden.";
  } finally {
    codeSending.value = false;
  }
}

const submitting = ref(false);
async function submitSignature() {
  errorMsg.value = "";
  if (!acceptAgb.value) {
    errorMsg.value = "Bitte den Hinweis zur elektronischen Signatur akzeptieren.";
    return;
  }
  if (!sigName.value.trim()) {
    errorMsg.value = "Bitte deinen Vor- und Nachnamen eintragen.";
    return;
  }
  if (sigMode.value === "drawn" && !canvasDirty) {
    errorMsg.value = "Bitte zeichne deine Unterschrift im Feld.";
    return;
  }
  if (!code.value || code.value.length < 4) {
    errorMsg.value = "Bitte den 6-stelligen Bestätigungscode eintragen.";
    return;
  }
  submitting.value = true;
  try {
    const res = await publicSubmitSignature({
      token,
      code: code.value.trim(),
      signature_name: sigName.value.trim(),
      signature_image: getSignatureDataUrl(),
      signature_method: sigMode.value,
      accept_agb: true,
    });
    phase.value = "done";
    // PDF neu laden (zeigt jetzt die signierte Variante)
    try {
      if (pdfUrl.value) URL.revokeObjectURL(pdfUrl.value);
      pdfUrl.value = await publicFetchSignPdfBlob(token);
    } catch (_) {}
  } catch (e) {
    errorMsg.value = e.message || "Signatur konnte nicht abgeschlossen werden.";
  } finally {
    submitting.value = false;
  }
}

const heading = computed(() => {
  if (phase.value === "done") return "Vertrag ist unterschrieben ✅";
  if (phase.value === "expired") return "Dieser Signier-Link ist abgelaufen.";
  return "Mandatsvertrag prüfen & unterschreiben";
});
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <!-- Header -->
    <div class="bg-[#161e2a] text-white py-4 px-5 flex items-center gap-3 shadow-sm">
      <img src="/Logo_mibeca_Start.png" alt="mibeca" class="h-10 w-auto" />
      <div>
        <span class="font-bold text-sm">ITUKV Dashboard</span>
        <span class="text-gray-400 text-xs ml-2">Elektronische Unterschrift</span>
      </div>
    </div>

    <div v-if="loading" class="p-10 text-center text-slate-500">Lade …</div>

    <div v-else-if="errorMsg && !info"
      class="max-w-xl mx-auto m-10 bg-white rounded-2xl shadow p-8 text-center">
      <h2 class="text-xl font-bold text-red-700 mb-2">Fehler</h2>
      <p class="text-slate-600">{{ errorMsg }}</p>
    </div>

    <div v-else class="max-w-4xl mx-auto p-4 sm:p-6 space-y-5">
      <!-- Status-Banner -->
      <div class="bg-white rounded-2xl shadow p-5">
        <h1 class="text-2xl font-bold text-slate-900">{{ heading }}</h1>
        <p v-if="info" class="text-sm text-slate-500 mt-1">
          mibeca GmbH · Jennifer Kaplan
        </p>
        <p v-if="info?.expires_at && phase==='review'" class="text-xs text-slate-400 mt-1">
          Gültig bis: {{ new Date(info.expires_at).toLocaleDateString("de-DE") }}
        </p>
      </div>

      <!-- PDF-Vorschau -->
      <div class="bg-white rounded-2xl shadow overflow-hidden">
        <div class="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
          <span class="text-sm font-semibold text-slate-700">📄 Vertrag</span>
          <a v-if="pdfUrl" :href="pdfUrl" target="_blank" rel="noopener"
             class="text-xs text-teal-700 hover:underline">In neuem Tab öffnen ↗</a>
        </div>
        <div v-if="pdfUrl" class="bg-slate-100">
          <iframe :src="pdfUrl" class="w-full" style="height:70vh;border:0;"></iframe>
        </div>
        <div v-else class="p-10 text-center text-slate-400 text-sm">
          PDF-Vorschau nicht verfügbar – das Dokument wird trotzdem signiert.
        </div>
      </div>

      <!-- Bereits signiert -->
      <div v-if="phase==='done'" class="bg-emerald-50 border border-emerald-200 rounded-2xl p-6">
        <h3 class="text-lg font-bold text-emerald-800">✅ Vielen Dank!</h3>
        <p class="text-sm text-emerald-700 mt-1">
          Der Vertrag wurde rechtsverbindlich unterzeichnet. Du bekommst eine Kopie
          mit Audit-Trail per Mail. Den Vertrag kannst du oben jederzeit wieder ansehen.
        </p>
      </div>
      <div v-else-if="phase==='expired'" class="bg-amber-50 border border-amber-200 rounded-2xl p-6">
        <h3 class="text-lg font-bold text-amber-800">Link abgelaufen</h3>
        <p class="text-sm text-amber-700 mt-1">
          Bitte fordere bei deinem Anbieter einen neuen Signier-Link an.
        </p>
      </div>

      <!-- Signier-Formular -->
      <div v-else class="bg-white rounded-2xl shadow p-5 space-y-4">
        <h2 class="text-lg font-bold text-slate-900">Unterschrift leisten</h2>

        <!-- Code anfordern -->
        <div class="bg-slate-50 rounded-lg p-4">
          <p class="text-sm text-slate-600 mb-2">
            Wir schicken einen 6-stelligen Bestätigungscode an
            <strong>{{ info?.lead_email }}</strong> – das verifiziert deine Identität.
          </p>
          <button @click="requestCode" :disabled="codeSending"
            class="px-4 py-2 bg-teal-600 text-white rounded-lg font-semibold hover:bg-teal-700 disabled:opacity-50">
            {{ codeSending ? "Sende …" : (codeRequested ? "Code erneut senden" : "Code per Mail anfordern") }}
          </button>
          <p v-if="codeFlash" class="text-xs text-teal-700 mt-2">{{ codeFlash }}</p>
          <input v-model="code" placeholder="6-stelliger Code"
            inputmode="numeric" maxlength="6"
            class="mt-3 w-full px-3 py-2 border border-slate-300 rounded-lg tracking-widest font-mono text-center" />
        </div>

        <!-- Name -->
        <div>
          <label class="block text-xs font-semibold text-slate-500 uppercase mb-1">
            Vor- und Nachname
          </label>
          <input v-model="sigName" type="text" placeholder="z.B. Anna Beispielfrau"
            class="w-full px-3 py-2 border border-slate-300 rounded-lg" />
        </div>

        <!-- Signatur-Modus -->
        <div>
          <div class="flex gap-2 mb-2">
            <button type="button" @click="sigMode='drawn'; clearCanvas()"
              :class="['px-3 py-1.5 text-sm rounded-lg border-2',
                sigMode==='drawn' ? 'border-teal-500 bg-teal-50 text-teal-800 font-semibold'
                                  : 'border-slate-200 bg-white']">
              ✍️ Selbst zeichnen
            </button>
            <button type="button" @click="sigMode='typed'"
              :class="['px-3 py-1.5 text-sm rounded-lg border-2',
                sigMode==='typed' ? 'border-teal-500 bg-teal-50 text-teal-800 font-semibold'
                                  : 'border-slate-200 bg-white']">
              ⌨️ Stilisierter Name
            </button>
          </div>
          <div v-if="sigMode==='drawn'" class="border-2 border-dashed border-slate-300 rounded-lg bg-white">
            <canvas ref="canvasRef" width="600" height="180"
              class="w-full"
              style="touch-action:none; cursor:crosshair;"
              @mousedown="startDraw" @mousemove="moveDraw" @mouseup="endDraw" @mouseleave="endDraw"
              @touchstart="startDraw" @touchmove="moveDraw" @touchend="endDraw" />
            <div class="flex justify-between items-center px-3 py-1.5 border-t border-slate-100">
              <span class="text-xs text-slate-400">Mit Maus oder Finger im Feld unterschreiben</span>
              <button type="button" @click="clearCanvas"
                class="text-xs text-slate-500 hover:text-slate-800">Zurücksetzen</button>
            </div>
          </div>
          <div v-else class="border-2 border-slate-300 rounded-lg bg-white p-4">
            <div style="font-family:'Brush Script MT','Snell Roundhand',cursive;
                       font-style:italic; font-size:42px; color:#0A2F2F;">
              {{ sigName || "Dein Name" }}
            </div>
          </div>
        </div>

        <!-- AGB-Akzeptanz -->
        <label class="flex items-start gap-2 text-sm text-slate-700 cursor-pointer">
          <input type="checkbox" v-model="acceptAgb" class="mt-0.5" />
          <span>
            Ich akzeptiere die elektronische Signatur als gleichwertig zur
            handschriftlichen Unterschrift (eIDAS Art. 25). Mit dem Klick auf
            „Rechtsverbindlich unterschreiben" gebe ich eine bindende
            Willenserklärung ab.
          </span>
        </label>

        <p v-if="errorMsg" class="text-sm text-red-600">{{ errorMsg }}</p>

        <button @click="submitSignature" :disabled="submitting"
          class="w-full py-3 bg-teal-600 text-white rounded-xl font-bold hover:bg-teal-700 disabled:opacity-50">
          {{ submitting ? "Unterschrift wird erstellt …" : "📝 Rechtsverbindlich unterschreiben" }}
        </button>
      </div>

      <p class="text-center text-xs text-slate-400 pb-6">
        Diese Signatur-Plattform wird über KIwerk.one bereitgestellt.
      </p>
    </div>
  </div>
</template>
