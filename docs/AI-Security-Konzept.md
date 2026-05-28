# Security- & Compliance-Konzept: KI-gestützte Dokument-Analyse

**Projekt:** ITUKV Dashboard (mibeca GmbH)
**Modul:** KI-Analyse von hochgeladenen Dokumenten (BWA, Jahresabschluss, Exposé, Handelsregister)
**Version:** 1.1
**Stand:** 2026-05-28
**Verantwortlich:** Anna Giza-Braun (mibeca)

> Änderungen zur Vorversion (1.0 → 1.1):
> - KI-Service-Account-Schreibrechte sind jetzt zusätzlich durch die Mandanten-Schutz-Allowlist eingegrenzt (kein Setzen von `mbNr`, `status`, `projekttyp` etc.)
> - Auto-Verlauf-Eintrag wird bei KI-Analyse-Übernahmen weiterhin geschrieben (unverändert), zusätzlich existiert jetzt parallel ein Auto-Verlauf für Mandant-Self-Service-Aktionen (siehe Dashboard-Konzept §5.5)

---

## 1. Zusammenfassung

Das ITUKV Dashboard bietet eine KI-gestützte Auswertung von hochgeladenen Dokumenten.
Ein in den Datenraum hochgeladenes PDF kann auf Knopfdruck an Anthropic Claude
übermittelt werden, das extrahiert strukturierte Kennzahlen (Mitarbeiter, Umsatz,
EBIT, Geschäftsführer u. a.) und liefert Vorschläge zurück. Die Übernahme der Werte
ins Dashboard erfolgt ausschließlich nach manueller Bestätigung durch einen Admin.

**Aktivierungsstatus (Stand 2026-05-28): AKTIV in Produktion.**
Der globale Schalter `AI_ANALYSE_AKTIV` ist auf `true` gesetzt, der Anthropic-API-Key
ist in den Azure App-Settings hinterlegt. Die Funktion kann von Admins genutzt werden.

> Hinweis: Aktivierung erfolgte **vor** vollständigem Abschluss der vertraglichen und
> datenschutzrechtlichen Schritte aus Abschnitt 8. Die offenen Punkte sind in §1a
> dokumentiert und mit Priorität abzuarbeiten.

### 1a Aktueller Compliance-Status

| Pflicht | Status | Verantwortlich | Frist |
|---|---|---|---|
| Globaler Schalter aktiv | ✅ gesetzt | Anna | — |
| API-Key Azure-seitig hinterlegt | ✅ vorhanden | Anna | — |
| API-Key-Rotation (initialer Key kontextexponiert) | ⏳ ausstehend | Anna | umgehend |
| AVV / DPA mit Anthropic abgeschlossen | ⏳ ausstehend | Anna + Anthropic | bis Q3 |
| Verarbeitungsverzeichnis Art. 30 ergänzt | ⏳ ausstehend | DSB | bis Q3 |
| DSFA Art. 35 DSGVO durchgeführt | ⏳ ausstehend | DSB | vor breitem Roll-out |
| Mandanten-Information im Vertrag / Anlage | ⏳ ausstehend | Jenny + Anwalt | mit nächster Vertragsfassung |
| Pro-Akte-Opt-In im Code implementiert | ✅ vorhanden | — | — |
| Manuelle Übernahme zwingend | ✅ vorhanden | — | — |
| Audit-Log pro KI-Aufruf | ✅ vorhanden | — | — |
| Budget-Limit bei Anthropic | ⚠️ zu prüfen | Anna | innerhalb 7 Tagen |
| Spending-Alert konfiguriert | ⚠️ zu prüfen | Anna | innerhalb 7 Tagen |

**Bewertung:** Die technischen Schutzmaßnahmen sind vollständig (default-OFF-Architektur,
Per-Akte-Opt-In, manuelle Übernahme, Audit, 2-stufiger Mass-Assignment-Schutz). Die
**organisatorischen/vertraglichen Pflichten** sind noch nicht abgeschlossen – damit ist
die Verarbeitung formell unvollständig abgesichert. Bis zum Abschluss empfohlen:
zurückhaltende Nutzung (nur Test-Mandate, keine Live-Kunden-Akten mit besonders
sensiblen Daten).

---

## 2. Risiko-Einordnung nach EU AI Act

Der Use-Case fällt unter **„KI als Entscheidungsunterstützung"** (decision-support).
Die KI liest Dokumente und schlägt Werte vor – die finale Entscheidung über die
Übernahme trifft immer ein Mensch.

| Kriterium | Bewertung |
|---|---|
| Autonome Entscheidung? | nein – manuelle Bestätigung erforderlich |
| Klassifizierung Annex III AI Act | **kein High-Risk-System** (kein Beschäftigungs-, Justiz-, Kredit-Scoring-Kontext im Sinne der Verordnung) |
| Transparenzpflicht Art. 50 AI Act | ja – wird durch Audit-Log + KI-Badge im Verlauf erfüllt |
| Anbieter / Deployer | mibeca = Deployer; Anthropic = Anbieter |

---

## 3. Datenschutzrechtliche Einordnung (DSGVO)

| Rolle | Verantwortlich |
|---|---|
| Verantwortlicher (Art. 4 Nr. 7) | mibeca GmbH |
| Auftragsverarbeiter (Art. 28) | Anthropic PBC, San Francisco, USA |
| Datenarten | Unternehmens-Stammdaten, Geschäftskennzahlen, ggf. personenbezogene Daten (GF-Name, Ansprechpartner). Keine besonderen Kategorien nach Art. 9 |
| Rechtsgrundlage | Art. 6 (1) b (Vertrag mit Mandant) bzw. Art. 6 (1) f (berechtigtes Interesse, Effizienz) |
| Drittlandübermittlung | USA – Anthropic ist im EU-US Data Privacy Framework gelistet; ergänzend Standardvertragsklauseln (SCCs) |

### Anthropic-spezifische Fakten (Stand 2026)
- API-Daten werden **nicht** zum Training verwendet (vertraglich zugesichert, Default für API-Zugang)
- Aufbewahrung: max. 30 Tage für Trust & Safety, danach Löschung
- Datenstandort: AWS US-East primär; AWS EU verfügbar für Enterprise-Kunden
- Anthropic stellt AVV / DPA bereit unter https://www.anthropic.com/legal/dpa
- Zero-Retention-Mode buchbar (auf Anfrage)

---

## 4. Technische und organisatorische Maßnahmen (TOM)

### 4.1 Implementiert (Stand heute)

| Maßnahme | Beschreibung |
|---|---|
| **Globaler Kill-Switch** | KI-Analyse ist nur aktiv, wenn in Azure App-Settings explizit `AI_ANALYSE_AKTIV=true` gesetzt ist (aktuell: aktiv). Bei `false` lehnt das Backend mit 403 ab – sofortige Notfall-Deaktivierung jederzeit möglich. |
| **API-Key-Trennung** | `ANTHROPIC_API_KEY` ausschließlich in Azure App-Settings; nicht im Code, nicht im Frontend, nicht im Git-Repo. |
| **Pro-Akte-Opt-In** | Pro Akte muss `kiAnalyseErlaubt=true` gesetzt werden. Wird beim ersten Klick auf „KI-Analyse" über einen expliziten Bestätigungs-Dialog gesetzt. |
| **Manuelle Übernahme** | KI schreibt NICHTS automatisch ins Dashboard. Antwort wird als Vorschlag im Modal angezeigt; Admin wählt einzeln pro Feld und bestätigt. |
| **PDF-Limit** | Max. 10 MB pro Datei. |
| **Audit-Trail** | Jeder KI-Aufruf wird in der `auditlog`-Tabelle mit User-ID, Zeitstempel, Dokument-Name und Token-Verbrauch protokolliert. |
| **Verlauf-Eintrag** | Jede KI-Analyse erzeugt einen sichtbaren Verlauf-Eintrag in der Akte mit Marker „KI-Analyse". |
| **Mass-Assignment-Schutz (2-stufig)** | KI darf nur eine definierte Allowlist von Feldern schreiben (`AI_WRITABLE_TARGET_FIELDS` / `AI_WRITABLE_KONTAKT_FIELDS`). Zusätzlich wirkt seit v1.1 die `ADMIN_ONLY_TARGET_FIELDS`-Sperre: selbst die KI darf z.B. nicht `mbNr`, `status`, `projekttyp`, `verkaueferName`, `firma`, `mandatStart` oder `mandatLaufzeitMonate` setzen. |
| **Rollen-Trennung** | Eigener Service-Account `ai-agent` mit reduziertem Schreibumfang für externe KI-Anbindung. |
| **Authentifizierung** | Microsoft Entra ID (MSAL) + JWT (HMAC-SHA256, 600.000 PBKDF2-Iterationen) + Token-Längen-Check + IDOR-Schutz |
| **Transport-Verschlüsselung** | TLS 1.2+ erzwungen auf allen Wegen (Browser → Azure → Anthropic) |
| **CORS-Whitelist** | Backend akzeptiert ausschließlich Anfragen von `dashboard.itukv.de` |
| **Verschlüsselung at-rest** | Azure Storage Service Encryption (AES-256), Microsoft-managed Keys |
| **Backup** | Wöchentlicher automatischer Tabellen-Snapshot, 12 Wochen Vorhaltung. Passwörter werden nicht ins Backup übernommen. |

### 4.2 Datenfluss (vereinfacht)

```
[Browser Admin]           [Azure Static Web Apps]            [Azure Functions]                    [Anthropic API]
       │                          │                                 │                                    │
       │── Login (Entra ID) ─────▶│                                 │                                    │
       │◀────── JWT ──────────────│                                 │                                    │
       │                          │                                 │                                    │
       │── PDF-Upload ────────────────────────────────────────────▶│ Azure Blob Storage (datenraum)     │
       │                                                            │                                    │
       │── „KI-Analyse" Klick ────────────────────────────────────▶│                                    │
       │                                                            │── PDF + Prompt (HTTPS) ───────────▶│
       │                                                            │◀────── Strukturiertes JSON ────────│
       │◀── Vorschlag (Modal) ────────────────────────────────────│                                    │
       │── „Übernehmen" ──────────────────────────────────────────▶│ Schreibt nur freigegebene Felder   │
       │                                                            │ + Audit-Log-Eintrag                 │
```

### 4.3 Anthropic-Aufbewahrung

Sobald die Antwort gesendet ist, behält Anthropic die Anfrage maximal 30 Tage zu Trust-&-Safety-Zwecken.
Optional kann ein **Zero-Retention-Mode** mit Anthropic vereinbart werden (Enterprise-Plan).

---

## 5. Risiken und Restrisiken

| Risiko | Eintrittswahrscheinlichkeit | Schadenshöhe | Maßnahme |
|---|---|---|---|
| Daten-Leak bei Anthropic | sehr gering (zertifizierte Infrastruktur) | hoch | AVV, SCCs, Zero-Retention prüfen |
| Falsche KI-Extraktion → falsche Werte im Dashboard | mittel | mittel | Manuelle Übernahme zwingend, jeder Wert einzeln bestätigbar |
| Unautorisierte Nutzung der KI-Funktion | sehr gering | mittel | Admin-only, Per-Akte-Opt-In, Audit-Log |
| Compliance-Verstöße (fehlender AVV / DSFA) | wenn nicht durchgeführt: hoch | hoch | **Aktivierung erst nach AVV + DSFA** |
| Übermäßige Kosten durch fehlerhafte Nutzung | gering | gering | Anthropic-Budget-Limit (z. B. 20 €/Monat) |

---

## 6. Auftragsverarbeitung – was bei Anthropic zu beachten ist

- AVV/DPA über https://www.anthropic.com/legal/dpa anfordern und unterzeichnen
- Anthropic in das Verarbeitungsverzeichnis nach Art. 30 DSGVO aufnehmen
- Standardvertragsklauseln (SCCs) als Anlage zum AVV erforderlich für USA-Transfer
- Für besonders sensible Mandate: Zero-Retention-Vereinbarung anstreben

---

## 7. Mandanten-Information

Mandanten (Verkäufer) sollten – idealerweise im Mandatsvertrag oder einer Beilage – darüber
informiert werden, dass:

1. mibeca KI-Werkzeuge zur Dokumenten-Analyse einsetzt
2. konkret Anthropic Claude (USA) als Auftragsverarbeiter genutzt wird
3. Daten nicht zum Training verwendet werden
4. der Mandant der Verarbeitung widersprechen kann (Opt-Out pro Akte möglich)

---

## 8. Aktivierungs-Checkliste (Soll-Zustand bei aktiver KI)

Stand 2026-05-28: KI ist bereits **aktiv**. Folgende Punkte sind noch nachzuholen:

- [x] Technische Sicherheits-Maßnahmen umgesetzt (siehe §4.1)
- [x] Pro-Akte-Opt-In implementiert
- [x] Audit-Log für jeden KI-Aufruf aktiv
- [ ] AVV mit Anthropic abgeschlossen und unterzeichnet
- [ ] Anthropic im Verarbeitungsverzeichnis ergänzt (Art. 30 DSGVO)
- [ ] DSFA (Art. 35 DSGVO) durchgeführt und dokumentiert
- [ ] Mandanten-Information ergänzt (Mandatsvertrag oder Beilage)
- [ ] Budget-Limit bei Anthropic gesetzt (Empfehlung 20–50 €/Monat)
- [ ] Spending-Alert konfiguriert
- [ ] API-Key rotiert (initialer Key wurde kontextuell exponiert)
- [ ] Datenschutzbeauftragter / Anwalt hat zugestimmt
- [ ] Jenny + Anna sind zu „Vier-Augen-Bestätigung" bei sensiblen Akten geschult

Bis zur Abhakung aller Punkte gilt **vorsorglich**: KI-Analyse nur an Test- oder
Nicht-Hochrisiko-Mandate anwenden, keine Verarbeitung besonders sensibler personen-
bezogener Daten ohne explizite Freigabe durch DSB.

---

## 9. Notfall-/Reaktionsplan

| Ereignis | Reaktion |
|---|---|
| API-Key kompromittiert | Sofort in Anthropic Console widerrufen, neuen Key generieren, in Azure austauschen |
| Auffällige Aktivität im Audit-Log | Audit-Tab im Dashboard → Filter nach User → ggf. Konto sperren, Verlauf prüfen |
| Daten-Leak-Verdacht bei Anthropic | Globalen Schalter `AI_ANALYSE_AKTIV=false` setzen, Anthropic-Incident-Response kontaktieren |
| Mandant widerruft KI-Verarbeitung | Pro-Akte-Opt-In zurücknehmen (Feld `kiAnalyseErlaubt=false`), bisherige KI-Verlauf-Einträge ggf. löschen |

---

## 10. Referenzen

- Anthropic Trust Center: https://trust.anthropic.com
- Anthropic DPA: https://www.anthropic.com/legal/dpa
- Anthropic Privacy Policy: https://www.anthropic.com/legal/privacy
- EU AI Act: https://eur-lex.europa.eu/eli/reg/2024/1689/oj
- DSGVO: https://eur-lex.europa.eu/eli/reg/2016/679/oj

---

*Dieses Dokument wurde durch das Entwicklerteam erstellt und ersetzt nicht die rechtliche
Beratung durch einen Datenschutzbeauftragten oder Fachanwalt. Es dient als Diskussions-
und Audit-Grundlage.*

*Stand 2026-05-28.*
