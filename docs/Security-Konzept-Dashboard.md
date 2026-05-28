# Security- & Compliance-Konzept – ITUKV Dashboard (mibeca GmbH)

**Version:** 1.1
**Stand:** 2026-05-28
**Verantwortlich:** Anna Giza-Braun (mibeca)
**Klassifizierung:** Vertraulich – nur für mibeca + Datenschutzberater

> Änderungen zur Vorversion (1.0 → 1.1):
> - Mass-Assignment: zusätzliche ADMIN-only-Allowlist für `mbNr`, Vorgangsnummern, Mandatslaufzeit
> - Microsoft-Auto-Detection beim User-Anlegen: keine Passwort-Vergabe für interne Domains
> - Neue strukturierte Mandanten-Felder (Ziele, Akquisitionsstrategie, Kosten-Bestätigung)
> - Auto-Verlauf-Logging bei Mandant-Self-Service-Aktionen
> - UX-Persistenz via sessionStorage (Tab-Wahl) – keine sensiblen Daten

---

## Inhaltsverzeichnis

1. Zusammenfassung
2. System-Überblick
3. Rechtliche Einordnung (DSGVO + EU AI Act)
4. Authentifizierung & Autorisierung
5. Datenfluss & Schnittstellen
6. Technische und Organisatorische Maßnahmen (TOM)
7. Daten-Lebenszyklus (Erfassung → Löschung)
8. KI-Komponenten (gesondert)
9. Backup, Wiederherstellung, Notfall
10. Audit & Nachvollziehbarkeit
11. Risiken & Restrisiken
12. Verantwortlichkeiten
13. Compliance-Checkliste (Go-Live)
14. Anhänge

---

## 1. Zusammenfassung

Das ITUKV Dashboard ist eine Web-Anwendung für die mibeca GmbH zur Abwicklung von
M&A-Mandaten (Kauf und Verkauf von IT-Unternehmen). Es verarbeitet sensible
Geschäftsdaten (NDAs, Bewertungen, Kennzahlen, Vertragsverhandlungen) sowie
personenbezogene Daten von Geschäftsführern, Käufern und Interessenten.

Dieses Dokument beschreibt das Sicherheits- und Datenschutzkonzept und dient
als Grundlage für die Verarbeitungstätigkeit nach Art. 30 DSGVO sowie als
Bewertungsmaßstab für interne Audits.

---

## 2. System-Überblick

### 2.1 Architektur

```
   ┌──────────────────────────────────────────────────────────────────┐
   │                          NUTZER                                  │
   │   Admin (mibeca)   Verkäufer   Käufer/Interessent   KI-Coworker  │
   └─────────────────────┬────────────────────────────────────────────┘
                         │ HTTPS
                         ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │  Azure Static Web Apps (Frankfurt)                               │
   │  dashboard.itukv.de · targets.itukv.de                           │
   │  Vue 3 SPA (Frontend)                                            │
   └─────────────────────┬────────────────────────────────────────────┘
                         │ HTTPS + JWT (HMAC-SHA256)
                         ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │  Azure Functions (Westeurope)                                    │
   │  itukv-func-v2.azurewebsites.net                                 │
   │  Python 3 · Microsoft Entra ID + JWT                             │
   └──┬──────────┬───────────┬───────────┬───────────────┬────────────┘
      │          │           │           │               │
      ▼          ▼           ▼           ▼               ▼
   ┌─────┐  ┌────────┐  ┌──────────┐ ┌──────────┐  ┌────────────┐
   │Table│  │  Blob  │  │   ACS    │ │ Anthropic│  │  SendGrid  │
   │Stor │  │ Storage│  │ (E-Mail) │ │ (KI)*    │  │(Inbound)   │
   └─────┘  └────────┘  └──────────┘ └──────────┘  └────────────┘
   * KI-Komponente default deaktiviert (siehe §8)
```

### 2.2 Komponenten und Zuständigkeit

| Komponente | Rolle | Standort | Eingesetzt für |
|---|---|---|---|
| Azure Static Web Apps | Frontend-Hosting | Frankfurt | HTML/JS-Auslieferung |
| Azure Functions | Backend-API | Westeurope | Business-Logik, Auth-Prüfung |
| Azure Table Storage | Datenbank | Westeurope | strukturierte Daten (Akten, Kontakte, Verlauf, User) |
| Azure Blob Storage | Datei-Speicher | Westeurope | PDFs, Bilder, Videos, Backups |
| Azure Communication Services | E-Mail-Versand | Westeurope | Mandanten-Mails, Reset-Mails |
| Microsoft Entra ID | Identitäts-Provider | Microsoft Cloud | SSO für interne User |
| SendGrid Inbound | E-Mail-Empfang | USA (gehärtet) | Reply-Mails landen automatisch im Verlauf |
| Anthropic Claude (optional) | KI-Analyse | USA / AWS | Dokumenten-Extraktion (default OFF) |

Alle Azure-Komponenten liegen geo-redundant innerhalb der EU (LRS / GRS).

### 2.3 Tech-Stack

- **Frontend:** Vue 3 + Vite + Tailwind CSS
- **Backend:** Python 3 (Azure Functions v2 Programming Model)
- **Auth:** Microsoft Entra ID (MSAL) + JWT (HMAC-SHA256)
- **Datenbank:** Azure Table Storage (NoSQL)
- **Datei-Storage:** Azure Blob Storage (datenraum, backups, sign-pdf)
- **Mail:** Azure Communication Services + SendGrid Inbound Parse

---

## 3. Rechtliche Einordnung

### 3.1 DSGVO – Verarbeitungs-Charakterisierung

| Punkt | Bewertung |
|---|---|
| Verantwortlicher (Art. 4 Nr. 7) | mibeca GmbH |
| Datenarten | Stammdaten Personen (Name, GF, Ansprechpartner), Kontaktdaten, Unternehmens-Stammdaten, Geschäftskennzahlen, Vertragsdaten, ggf. Bonitätsdaten |
| Besondere Kategorien Art. 9 | **nein** – keine Gesundheits-, Religions-, Gewerkschafts- oder politischen Daten |
| Rechtsgrundlagen | Art. 6 (1) b (Vertrag mit Mandanten) · Art. 6 (1) f (berechtigtes Interesse bei Marktansprache und Lead-Pflege) |
| Drittlandstransfer | Anthropic (USA, optional) und SendGrid (USA) – über SCCs + DPF abgesichert |
| Auftragsverarbeiter | Microsoft Azure, Anthropic, SendGrid, ACS |
| Verarbeitungsverzeichnis | erforderlich nach Art. 30 |
| DSFA | empfohlen für KI-Komponente und ggf. für Profiling im Match |

### 3.2 EU AI Act – Risiko-Klassifizierung

Das Dashboard nutzt KI an genau einer Stelle: **Dokument-Analyse** (BWA / Jahresabschluss).
Diese ist optional, default deaktiviert und unterstützt nur menschliche Entscheidungen.

| Komponente | AI-Act-Klasse | Begründung |
|---|---|---|
| KI-Dokument-Analyse | **Minimal Risk / Limited Risk** | Decision-Support, keine autonome Entscheidung, keine Annex-III-Kategorie |
| Kandidaten-Match (Score) | **Minimal Risk** | Regelbasierter Algorithmus, keine ML-Inferenz |
| Auto-Termin-Reminder | **Minimal Risk** | Statische Regeln |
| Audit-Log | **Minimal Risk** | Klassische Datenbank-Funktion |

Es liegt **kein High-Risk-System** im Sinne des AI Acts vor. Pflichten:
- **Art. 50 (Transparenz):** erfüllt durch Audit-Log + sichtbare „KI"-Markierungen
- **Art. 53 (General-purpose AI):** Anbieter Anthropic, mibeca ist Deployer
- **Art. 4 (KI-Kompetenz):** Anna + Jenny sind in der Bedienung geschult

---

## 4. Authentifizierung & Autorisierung

### 4.1 Identifizierung

| Nutzergruppe | Auth-Methode | Token |
|---|---|---|
| Interne Mitarbeiter | Microsoft Entra ID (MSAL) – Multi-Tenant | ID-Token von Microsoft, danach Tausch in dashboard-JWT |
| Externe Verkäufer / Käufer | E-Mail + Passwort | dashboard-JWT |
| KI-Service-Account | E-Mail + Passwort | dashboard-JWT mit Rolle `ai-agent` |
| Webhook-Quellen (SendGrid) | Shared Secret im URL-Parameter (`?key=...`) | – |
| Öffentliche Landing-Pages | keine | – |
| Öffentliche Exposé-Bereiche | per-Interessent UUID-Token, min. 32 Zeichen | – |

### 4.2 Token-Details

- **Algorithmus:** HMAC-SHA256
- **Secret:** in Azure App Setting `JWT_SECRET`, niemals im Repo
- **Default-Secret deaktiviert:** Backend lehnt Auth ab, wenn Secret = `dev-secret` oder leer
- **Gültigkeit:** 7 Tage
- **Inhalt:** UserID, Rolle, Name, Email, TargetID (falls Partner)
- **`exp`-Claim** wird bei jedem Aufruf geprüft

### 4.3 MSAL-Token-Validierung

Beim Login werden Microsoft-Tokens **serverseitig** gegen die Microsoft JWKS verifiziert
(Signatur + Issuer + Audience). Der E-Mail-Claim wird aus dem **verifizierten** Token
gezogen, nie aus dem Request-Body. Bootstrap-Pfad (erster Login = Admin) wurde
entfernt – neue User müssen vom Admin angelegt werden.

### 4.4 Passwort-Hashing

PBKDF2-HMAC-SHA256 mit **600.000 Iterationen** (OWASP-Empfehlung 2024+).
Hash-Format: `pbkdf2$ITERATIONS$salt$hash`. Beim Login werden alte Hashes
(3-Feld-Format mit 100.000 Iterationen) automatisch auf den aktuellen Standard
hochgezogen.

**Microsoft-Auto-Detection beim User-Anlegen (seit v1.1):**
Der `user-create`-Endpoint erkennt interne Mitarbeiter automatisch (Rolle = `admin`
oder Mailadresse endet auf `@mike-bergmann.de` / `@mibeca.de`). Für diese User wird
**kein Passwort generiert und kein Passwort-Hash gespeichert**. Der Login erfolgt
ausschließlich über Microsoft Entra ID. Vorteil: keine ungenutzten Passwörter, die
abhandenkommen könnten. Externe Mandanten (Verkäufer/Investor) bekommen wie bisher
ein 12-stelliges Initial-Passwort + Begrüßungs-Mail.

### 4.5 Rollen-Modell

| Rolle | Rechte |
|---|---|
| `admin` | Alles im Backend, alle Akten lesbar/schreibbar, User-Verwaltung |
| `target` | nur eigene Akte – IDOR-Schutz auf Backend-Seite (`p.targetId == tid`) |
| `investor` | nur eigene Kauf-Mandate |
| `ai-agent` | nur lesen + Bulk-Update auf Allowlist-Felder + Verlauf-Anhängen |

### 4.6 OData-Injection-Schutz

Alle Azure-Table-Queries verwenden parametrisierte OData-Filter (`@email`, `@token`, `@pk`).
Es gibt keine f-String-basierten Queries mit User-Input.

### 4.7 IDOR-Schutz

Routen mit personen- oder akten-bezogenen Daten (`target-get`, `target-update`,
`dokument-stream-url` u. a.) prüfen explizit: wenn `role != admin`, muss
`p.targetId == requestedTargetId` sein. Andernfalls 403.

### 4.7a Mass-Assignment – Admin-only-Felder (seit v1.1)

Über die generelle `TARGET_WRITABLE_FIELDS`-Allowlist hinaus gibt es eine zusätzliche
**Admin-only-Allowlist** im `target-update`-Endpoint. Selbst ein eingeloggter Mandant
mit Schreibrecht auf seine eigene Akte (IDOR-konform) darf folgende Felder **nicht**
ändern – das Backend ignoriert solche Mitlieferungen stillschweigend:

- `mbNr` (Vorgangsnummer / Mandatsnummer)
- `transaktionsnummer`
- `kundennummer`
- `projekttyp`
- `status`
- `verkaueferName`
- `firma`
- `mandatStart`, `mandatLaufzeitMonate`

Hintergrund: Diese Felder sind organisationsseitig vergeben (Jenny/Anna) und dürfen
nicht durch ein manipuliertes Client-Payload überschrieben werden. Im Frontend sind
die zugehörigen Eingabefelder zusätzlich `readonly` markiert, der Backend-Schutz ist
aber die maßgebliche Schutzschicht.

### 4.8 CORS

`Access-Control-Allow-Origin` ist auf `dashboard.itukv.de` (+ EU-Production-Domains)
fest verdrahtet. Wildcard wurde entfernt. Andere Origins können die API nicht
direkt aus dem Browser aufrufen.

---

## 5. Datenfluss & Schnittstellen

### 5.1 Schreibender Datenfluss (Beispiel: Verkäufer füllt Fragebogen)

1. Verkäufer öffnet `dashboard.itukv.de`, MSAL-Login
2. Browser → SWA → Vue-App lädt
3. Vue-App → Backend `POST /target-get` mit JWT
4. Backend prüft JWT-Signatur + Ablauf + IDOR
5. Backend liest Target aus Table Storage
6. Verkäufer füllt Fragebogen, klickt „Speichern"
7. Vue-App → `POST /target-update` mit JWT + Payload
8. Backend filtert Payload gegen TARGET_WRITABLE_FIELDS (Mass-Assignment-Schutz)
9. Backend schreibt in Table Storage
10. Backend schreibt Audit-Log-Eintrag `{user, "update", "target", id, fields}`

### 5.2 Lesender Datenfluss (Beispiel: Käufer öffnet Exposé)

1. Käufer klickt Link `targets.itukv.de/expose-mb-XXX/<token>`
2. SWA lädt Vue-App
3. Vue-App → Backend `GET /expose-public?token=...`
4. Backend prüft `is_valid_public_token(token)` (≥ 24 Zeichen, alphanumerisch)
5. Backend sucht Interessent mit dem Token (parametrisiert)
6. Backend liefert nur Public-safe Felder zurück (kein Telefon, keine PII anderer)

### 5.3 Externe Schnittstellen

| Schnittstelle | Authentifizierung | Datenfluss |
|---|---|---|
| Microsoft Graph / Entra ID | OAuth 2.0 (MSAL) | nur Login-Identifikation |
| Azure Communication Services | Connection String | ausgehende E-Mails |
| SendGrid Inbound Parse | Shared Secret in URL | eingehende E-Mails → Verlauf |
| Anthropic API | API-Key in Azure App Setting | PDF → strukturierte Antwort (default OFF) |

### 5.4 Datenfelder im Detail

Siehe Anhang A für eine vollständige Liste der gespeicherten Felder pro Tabelle.

### 5.5 Auto-Verlauf-Logging bei Mandant-Self-Service-Aktionen (seit v1.1)

Wenn ein Verkäufer/Käufer im Mandanten-Portal eine Self-Service-Aufgabe abschließt,
schreibt das Backend automatisch einen Verlauf-Eintrag in die Akte. Das gibt der
Beraterin Jenny eine Echtzeit-Sicht auf Mandanten-Aktivität, ohne extra Push-Logik.

Aktuell getrackt:
- **Kosten-Tabelle zur Kenntnis genommen** → `kostenInfoBestaetigtAm`
- **Ziele & Motivationen ausgefüllt/angepasst** (Verkäufer) → `zieleMotivationenJson`
- **Akquisitionsstrategie ausgefüllt/angepasst** (Käufer) → `akquisitionsstrategieJson`
- **Fragebogen abgegeben** → `fragebogenStatus = abgegeben`

Eintrag-Struktur (in `kommunikationJson` an die Akte angehängt):

```json
{
  "id": "auto<timestamp>",
  "typ": "aufgabe",
  "datum": "<ISO 8601 UTC>",
  "autor": "<User-Name oder Mailadresse>",
  "betreff": "Aufgabe erledigt: <Beschreibung>",
  "createdBy": "<User-RowKey>",
  "createdByMandant": true
}
```

Datenschutz: Der Eintrag enthält keine Inhalte des Formulars, nur die Tatsache des
Abschlusses. Ein Mandant kann den Eintrag nicht selbst nachträglich verändern – das
Logging passiert ausschließlich serverseitig im `target-update`-Endpoint.

---

## 6. Technische und Organisatorische Maßnahmen (TOM)

### 6.1 Zutrittskontrolle (physisch)

Microsoft-Rechenzentren (Westeurope = Niederlande, Irland) – ISO 27001 / SOC 2 zertifiziert.
mibeca selbst hat keinen physischen Zugriff auf Server.

### 6.2 Zugangskontrolle (technisch)

- Mandatory TLS 1.2+ überall
- Microsoft Entra ID mit MFA-Fähigkeit (kann auf User-Ebene erzwungen werden)
- Passwort-Reset via Token-Link (nicht über Sofort-Reset)
- Token-Längen-Check auf allen öffentlichen Endpunkten (≥ 24 Zeichen)
- Sitzungsende nach 7 Tagen (JWT-exp)

### 6.3 Zugriffskontrolle (Daten)

- Rollen-Modell (admin / target / investor / ai-agent)
- IDOR-Schutz auf jeder akten-bezogenen Route
- Mass-Assignment-Allowlists für target-update und ai-bulk-update
- Path-Traversal-Filter beim Upload (Slashes, Punktsequenzen werden ersetzt)

### 6.4 Weitergabekontrolle

- Verschlüsselte Übertragung (TLS 1.2+)
- SAS-URLs für direkten Blob-Zugriff: max. 10 Minuten gültig (Read), max. 15 Minuten (Write)
- NDA-Dokumente nur für Admin lesbar (extra Prüfung in `/dokument-stream-url`)

### 6.5 Eingabekontrolle (Audit)

- Audit-Log-Tabelle protokolliert: create, update, delete an Targets, Kontakten, Usern
- KI-Aufrufe und Backup-Trigger ebenfalls geloggt
- Audit ist im Dashboard unter „Audit & Backup" sichtbar (admin-only)

### 6.6 Auftragskontrolle

- Auftragsverarbeiter: Microsoft Azure, Anthropic, SendGrid, ACS
- AVV mit Microsoft: Standard, bereits unterzeichnet beim Azure-Vertrag
- AVV mit Anthropic: bei Aktivierung der KI-Komponente erforderlich (siehe §8)
- AVV mit SendGrid: erforderlich (für Webhook-Empfang)

### 6.7 Verfügbarkeitskontrolle

- Geo-redundante Storage-Replikation (Azure GRS/LRS)
- Health-Check-Endpunkt `/api/health` für Monitoring
- Sicheres Deploy-Script verhindert kaputten Code (AST-Check, Routes-Check, Health-Check)
- Wöchentliches automatisches Backup (12-Wochen-Rotation)

### 6.8 Trennungsgebot

- Test- und Produktivdaten getrennt (Staging-Umgebung in Planung)
- Mandanten-Daten gegen Cross-Access geschützt (IDOR)
- Logische Trennung über `targetId` und Rolle

### 6.9 Client-seitige UX-Persistenz (seit v1.1)

Das Frontend nutzt `sessionStorage` für UX-Komfort:

| Schlüssel | Inhalt | Lebensdauer |
|---|---|---|
| `target.tab` | aktiver Tab im Mandanten-Portal | bis Browser-Tab geschlossen |
| `admin.tab` | aktiver Tab im Admin-Portal | bis Browser-Tab geschlossen |
| `mandate.view` | gewählte Ansicht (Cockpit/Liste) | bis Browser-Tab geschlossen |
| `targetId` / `userRole` / `userName` / `partnerJwt` | bestehende Auth-Werte | bis Browser-Tab geschlossen |

`sessionStorage` ist domain-gebunden, beim Schließen des Browser-Tabs automatisch
gelöscht und nicht über andere Tabs/Browser geteilt. Keine besonderen Datenkategorien.
Tokens (JWT) liegen ebenfalls in `sessionStorage`, nicht in `localStorage` – damit
keine persistenten Spuren auf gemeinsam genutzten Rechnern bleiben.

---

## 7. Daten-Lebenszyklus

### 7.1 Erfassung

| Quelle | Daten | Speicherort |
|---|---|---|
| Manuell durch Admin | Mandate, Kontakte, Verlauf | Table Storage |
| Verkäufer-Self-Service | Fragebogen, Profil | Table Storage |
| Interessenten-Anfrage | Kontaktdaten | Table Storage |
| Upload | Dokumente (PDF, Bilder, Videos) | Blob Storage |
| Eingehende Mail (SendGrid) | Verlauf-Einträge | Table Storage |

### 7.2 Aufbewahrungsfristen (Empfehlung)

| Datenart | Frist | Begründung |
|---|---|---|
| Aktive Mandate | unbegrenzt | laufender Vertrag |
| Abgeschlossene Mandate | 10 Jahre nach Closing | HGB / AO |
| Lead-Daten (Nichtkunden) | 3 Jahre nach letztem Kontakt | DSGVO Speicherbegrenzung |
| NDAs | nach Vertragsende | bis 10 Jahre nach Verkauf |
| Verlauf-Einträge | mit Mandat | s.o. |
| Backup-Snapshots | 12 Wochen | technische Wiederherstellung |
| Audit-Log | 24 Monate | Compliance-Nachweis |
| Anthropic-Aufrufe | 30 Tage bei Anthropic | Anthropic-Default |

### 7.3 Löschung

- Soft-Delete im Frontend (Lösch-Button mit Bestätigung)
- Hard-Delete im Backend (`delete_entity` in Azure Table)
- Zugehörige Dokumente werden mitgelöscht (Blob)
- Löschvorgänge landen im Audit-Log

### 7.4 Auskunft & Portabilität (Art. 15 / 20 DSGVO)

Bei Anfrage eines Betroffenen kann ein Admin im Backup-Tab ein JSON-Export
für eine spezifische Akte/Kontakt erstellen.

---

## 8. KI-Komponente (eingehende Detaildoku)

Siehe separates Dokument: [AI-Security-Konzept.md](./AI-Security-Konzept.md).

Stand: **default deaktiviert** durch Azure-Setting `AI_ANALYSE_AKTIV=false`.
Aktivierung erfordert:
- AVV mit Anthropic
- DSFA durchgeführt
- Mandanten-Information ergänzt
- Pro-Akte-Opt-In durch User
- Manuelles Übernehmen der KI-Vorschläge

---

## 9. Backup, Wiederherstellung, Notfall

### 9.1 Backup

- **Wöchentlich automatisch:** Sonntags 03:00 UTC, alle Tabellen als JSON in Blob `backups/`
- **Manuell:** Admin-Button im „Audit & Backup"-Tab
- **Aufbewahrung:** 12 Wochen Rotation (älteste werden gelöscht)
- **Inhalt:** keine Passwörter (Risk-Hygiene)
- **Recovery:** JSON kann durch Admin-Script in die Tabellen zurückgespielt werden

### 9.2 Code-Wiederherstellung

- Vollständige Versionierung in Git (GitHub Repo `gizabrauna-rgb/ITUKV`)
- Deploy zu jedem Commit reversibel über `git revert` + Deploy-Script
- Safe-Deploy-Script mit 4 Pre-Checks + Health-Check verhindert kaputte Deploys

### 9.3 Incident-Response

| Vorfall | Sofortmaßnahme |
|---|---|
| Account kompromittiert | Admin sperrt User, neuer Passwort-Reset via Token-Link |
| Datenleck-Verdacht | Audit-Log prüfen, Anthropic-Schalter umlegen, Microsoft-Incident-Team kontaktieren |
| Backend offline | Health-Check zeigt Problem, Re-Deploy letzter funktionierender Commit |
| Datenverlust | Backup aus „Audit & Backup"-Tab herunterladen + zurückspielen |
| API-Key kompromittiert | Key in Anthropic Console widerrufen, neuen erstellen, in Azure setzen |

---

## 10. Audit & Nachvollziehbarkeit

Jeder schreibende Vorgang im Backend wird in der `auditlog`-Tabelle protokolliert mit:

- Zeitstempel (UTC ISO 8601)
- UserID + UserName + UserRole
- Aktion (`create`, `update`, `delete`, `ai_update`, `ai_analyze`, …)
- Objekt-Typ + Objekt-ID
- Details (geänderte Felder, alte/neue Werte bei KI-Updates)

Admin-Zugriff über Dashboard → „Audit & Backup". Filter nach User oder Target möglich.
Export via Browser-DevTools möglich, dediziertes CSV-Export-Feature in Planung.

---

## 11. Risiken & Restrisiken

| Risiko | Eintritt | Schaden | Maßnahme | Restrisiko |
|---|---|---|---|---|
| Account-Übernahme (Phishing) | mittel | hoch | MFA, Token-Reset-Link, Audit-Log | gering |
| Code-Injection | gering | hoch | OData-Parametrisierung, Path-Sanitization | sehr gering |
| Datenverlust durch Bug | gering | mittel | Wochen-Backup + Safe-Deploy | sehr gering |
| Cross-User-Datenzugriff (IDOR) | gering | hoch | IDOR-Schutz auf jeder Route | sehr gering |
| Microsoft Azure Ausfall | sehr gering | hoch | Geo-Redundanz, Multi-Region möglich | mittel |
| Anthropic Daten-Leak | sehr gering | hoch | Default-OFF, AVV, Per-Akte-Opt-In | gering (nach AVV) |
| Falsche KI-Antwort | mittel | mittel | manuelle Übernahme zwingend | gering |
| DSGVO-Verstoß (fehlende DSFA, Info) | hoch ohne Maßnahmen | hoch | Aktivierung erst nach Checkliste | gering bei Compliance |

---

## 12. Verantwortlichkeiten

| Rolle | Person | Verantwortung |
|---|---|---|
| Verantwortlicher (Art. 4 Nr. 7 DSGVO) | mibeca GmbH / GF | Gesamtverantwortung |
| Datenschutzbeauftragter | extern bestellt | Beratung, Audit |
| System-Admin | Anna Giza-Braun | technischer Betrieb, User-Verwaltung |
| Operativ | Jenny Kaplan | Mandats-Bearbeitung |
| Entwicklung | externer Dienstleister | Code, Wartung, Deploy |

---

## 13. Compliance-Checkliste (Go-Live)

### 13.1 Datenschutz – muss bei Aufnahme oder Wechsel von Verarbeitungen geprüft werden

- [ ] Verarbeitungsverzeichnis (Art. 30 DSGVO) gepflegt
- [ ] AVV mit Microsoft Azure unterschrieben
- [ ] AVV mit SendGrid unterschrieben (für Inbound Parse)
- [ ] AVV mit Anthropic (bei Aktivierung der KI-Komponente)
- [ ] Mandanten-Information in den Mandatsverträgen
- [ ] Datenschutzerklärung auf dashboard.itukv.de + targets.itukv.de aktuell
- [ ] DSFA für KI-Komponente durchgeführt (vor `AI_ANALYSE_AKTIV=true`)

### 13.2 Technisch

- [x] JWT_SECRET in Azure gesetzt (nicht `dev-secret`)
- [x] CORS-Whitelist statt Wildcard
- [x] PBKDF2 mit 600.000 Iterationen
- [x] Microsoft-Token serverseitig verifiziert
- [x] OData-Queries parametrisiert
- [x] IDOR-Schutz aktiv
- [x] Mass-Assignment-Allowlists
- [x] Path-Traversal-Filter
- [x] Token-Längen-Check public Endpoints
- [x] SAS-URL-Lebensdauer 10 Min (Read) / 15 Min (Write)
- [x] Health-Check + Safe-Deploy-Script
- [x] Wöchentliches Backup (12-Wochen-Rotation)
- [x] Audit-Trail aktiv
- [ ] Monitoring/Alert für Backend-Ausfall (Application Insights — Empfehlung)
- [ ] Staging-Umgebung (Empfehlung)

### 13.3 Organisatorisch

- [ ] User-Schulung „KI-Kompetenz" nach AI-Act Art. 4
- [ ] Notfall-Plan dokumentiert und allen Admins bekannt
- [ ] Datenschutzbeauftragter informiert
- [ ] Regelmäßige Audit-Log-Review (vierteljährlich)
- [ ] Lösch-Konzept für abgeschlossene Mandate (10-Jahre-Frist)

---

## 14. Anhänge

### Anhang A: Datenfelder (Übersicht)

**Tabelle `users`:**
RowKey (UUID), email, name, role (admin/target/investor/ai-agent),
passwordHash (PBKDF2 600k), targetId, createdAt, lastSeen, lastSeenVerlauf (JSON-Map)

**Tabelle `targets`:**
RowKey (UUID), mbNr, verkaueferName, firma, region, plz, branche, mitarbeiter,
umsatz, projekttyp, status, mandatStart, mandatLaufzeitMonate, geschaeftsfuehrer,
kundennummer, transaktionsnummer, kostenInfoBestaetigtAm,
diverse JSON-Blobs (phasenJson, fragebogenJson, bewertungJson, exposeJson, landingJson,
kommunikationJson, termineJson, vertragJson, loiJson, lessonsLearnedJson, suchprofilJson,
zieleMotivationenJson, akquisitionsstrategieJson, kiAnalyseErlaubt …)

Mandanten-Self-Service-Felder (seit v1.1, durch das Backend in der target-Tabelle gespeichert):

| Feld | Wer schreibt? | Inhalt |
|---|---|---|
| `kostenInfoBestaetigtAm` | Verkäufer (Self-Service) | ISO-Zeitstempel der Kosten-Bestätigung |
| `zieleMotivationenJson` | Verkäufer (Self-Service) | Strukturierte Antworten: Motivation, Zeitrahmen, Wunsch-Rolle, Deal-Struktur, Deal-Breaker |
| `akquisitionsstrategieJson` | Käufer (Self-Service) | Strukturierte Antworten: Motivation, Hold-Period, Budget, Finanzierung, Zielprofil, Synergien, Deal-Breaker |

Alle Felder sind in `TARGET_WRITABLE_FIELDS` enthalten, also durch den allgemeinen
Mass-Assignment-Schutz abgedeckt. Sie liegen außerhalb der `ADMIN_ONLY_TARGET_FIELDS`-
Allowlist, weil der Mandant sie selbst pflegen darf.

**Tabelle `kontakte`:**
RowKey (UUID), firma, name, geschaeftsfuehrer, email, telefon, plz, ort, website,
branche, mitarbeiter, umsatzTeur, ebitMarge, recurringPct, sucht, bietet,
ansprechpartnerJson, kundenstatus, istKunde, istExKunde, istInvestor, istNichtkunde

**Tabelle `interessenten`:**
RowKey, targetId, firma, name, email, telefon, ndaStatus, exposeToken, …

**Tabelle `dokumente`:**
PartitionKey=targetId, RowKey, fileName, blobName, ordner, size, contentType,
uploadedAt, uploadedBy

**Tabelle `auditlog`:**
PartitionKey="audit", RowKey=timestamp+uuid, ts, userId, userName, userRole,
action, targetType, targetId, details (JSON)

**Tabelle `passwordresets`:**
PartitionKey="reset", RowKey=token, userId, exp (30 Min)

**Blob-Container `datenraum`:**
PDF, Bild, Video, Audio – pro Akte ein Pfad `{targetId}/{ordner}/{filename}`

**Blob-Container `backups`:**
Wöchentliche JSON-Snapshots, 12-Wochen-Rotation

### Anhang B: Sicherheits-Audit-Historie

| Datum | Audit-Art | Findings | Status |
|---|---|---|---|
| 2026-05-27 | Initial-Audit | 4 kritische, 4 hohe, mehrere Hygiene-Findings | alle geschlossen, siehe Git-Commits |
| 2026-05-28 | Hardening-Iteration | Mandant kann mbNr/Vorgangsnummern setzen; Microsoft-User bekommen unnötig Passwort; fehlendes Self-Service-Aktivitäts-Logging | alle geschlossen, siehe Commits e482320, user-create-Patch, d050e2f |

Detail-Findings dieses Audits:
- Login-Bypass über unverifizierten MSAL-Token (BEHOBEN)
- IDOR auf target-get / target-update (BEHOBEN)
- /kontakte für alle eingeloggten User (BEHOBEN, jetzt admin-only)
- OData-Injection an mehreren Stellen (BEHOBEN, parametrisiert)
- JWT-Default-Secret „dev-secret" (BEHOBEN, Boot-Assertion)
- Inbound-Webhook ungeschützt (BEHOBEN, Shared Secret)
- Password-Forgot ohne Token-Link (BEHOBEN, Token-Reset-Flow)
- CORS-Wildcard (BEHOBEN, Whitelist)
- SAS-URL-Lebensdauer 60-120 Min (BEHOBEN, 10-15 Min)
- PBKDF2 100k Iterationen (BEHOBEN, 600k + Opportunistic-Upgrade)
- Path-Traversal-Filter (BEHOBEN)
- Token-Längen-Check (BEHOBEN)
- Mass-Assignment-Schutz (BEHOBEN, Allowlists)

### Anhang C: API-Endpunkte (Auszug)

| Pfad | Methode | Auth | Zweck |
|---|---|---|---|
| `/health` | GET | – | Health-Check |
| `/auth/resolve` | POST | MSAL-ID-Token | Login interne User |
| `/login` | POST | E-Mail+Passwort | Login externe User |
| `/password-forgot` | POST | – | Reset-Link anfordern |
| `/target-get` | POST | JWT + IDOR | Akte lesen |
| `/target-update` | POST | JWT + IDOR + Allowlist | Akte ändern |
| `/audit-log` | GET | admin | Audit anzeigen |
| `/backup-trigger` | POST | admin | Sofort-Backup |
| `/ai-analyze-document` | POST | admin + Compliance-Schalter + Opt-In | KI-Analyse |
| `/ai-bulk-update` | POST | ai-agent / admin | Bulk-Felder schreiben (Allowlist) |

Vollständige Liste: 80 Endpunkte, dokumentiert in `backend/function_app.py`.

### Anhang D: Verwendete externe Bibliotheken

**Backend (Python):**
azure-functions, azure-data-tables, azure-storage-blob, azure-communication-email,
PyMuPDF, weasyprint, jinja2, requests, beautifulsoup4, openai, anthropic,
PyJWT[crypto], cryptography

**Frontend (JavaScript):**
Vue 3, Vite, Tailwind CSS, MSAL.js, axios, Lucide Icons, TipTap (Rich-Text), Leaflet (Karten)

Alle Pakete werden über npm/pip ausschließlich aus offiziellen Registries bezogen.
Bekannte Sicherheitslücken werden durch monatliche `npm audit` / `pip-audit` Checks
adressiert (manuell, Automatisierung in Planung).

---

*Dieses Dokument ist ein lebendes Dokument und wird mindestens jährlich aktualisiert
oder bei wesentlichen Änderungen an Architektur, Datenfluss oder rechtlichen
Rahmenbedingungen. Stand 2026-05-28.*

*Es ersetzt nicht die rechtliche Bewertung durch einen Datenschutzbeauftragten
oder Fachanwalt für IT-Recht.*

**Erstellt durch:** mibeca Entwicklerteam (anhand des aktuellen Code-Stands)
**Genehmigung durch:** _______________ (mibeca-GF / DSB)
