# mibeca Security- & Compliance-Dokumentation

**Stand:** 2026-05-28
**Pflege:** Anna Giza-Braun

## Übersicht der Dokumente

Diese Mappe enthält die vollständige Security- und Compliance-Dokumentation für das
ITUKV Dashboard. Alle Dateien sind im Markdown-Format und können direkt in Confluence
oder ein anderes Wiki kopiert werden.

| Datei | Inhalt | Status / Pflicht |
|---|---|---|
| **Security-Konzept-Dashboard.md** | Gesamtkonzept: Architektur, Auth, Datenfluss, TOM, Backup, Risiken | ✅ Pflicht (DSGVO Art. 30 Grundlage) |
| **AI-Security-Konzept.md** | KI-spezifisches Konzept inkl. AI-Act-Bewertung | ✅ Pflicht solange KI aktiv |
| **1-Mandanten-Info-KI-Anlage.md** | Mustertext für Mandatsvertrags-Anlage | An Anwalt geben |
| **2-DSFA-Vorlage.md** | Datenschutz-Folgenabschätzung (Art. 35 DSGVO) | An DSB geben zur Prüfung |
| **3-Verarbeitungsverzeichnis-Anthropic.md** | Eintrag fürs zentrale Art-30-Verzeichnis | Ins bestehende Art-30-Register übernehmen |
| **4-AVV-Anfrage-Anthropic.md** | Anleitung + Mail-Vorlage für DPA-Anforderung | Selbst durchführen |
| **5-Anleitung-Anthropic-Budget.md** | Schritt-für-Schritt Budget-Limit + Alerts | Selbst durchführen, ~5 Min |
| **6-Anleitung-API-Key-Rotation.md** | Schritt-für-Schritt Key-Rotation | Erster Lauf am Tag der Erstellung |

## Reihenfolge zur Abarbeitung der offenen Compliance-Punkte

Empfohlene Reihenfolge:

1. **API-Key rotieren** (Vorlage 6) – höchste Dringlichkeit, da initialer Key kontextuell exponiert
2. **Budget-Limit + Alerts setzen** (Vorlage 5) – Kostenrisiko sofort eingrenzen
3. **AVV mit Anthropic anfragen** (Vorlage 4) – Frist ca. 5 Werktage Reaktion
4. **DSFA an DSB geben** (Vorlage 2) – mit AVV-Ergebnis ggf. ergänzen
5. **Verarbeitungsverzeichnis ergänzen** (Vorlage 3) – sobald AVV unterzeichnet
6. **Mandanten-Info an Anwalt** (Vorlage 1) – für nächste Vertragsfassung

## Status-Tracking

In der `AI-Security-Konzept.md` Abschnitt §1a befindet sich eine Compliance-Tabelle, die
nach jedem abgearbeiteten Schritt aktualisiert werden soll. Beim Erreichen vollständiger
Compliance ✅ überall: das Konzept-Doc als „v1.2" markieren und Stand-Datum aktualisieren.

## Konvention für neue Compliance-Dokumente

- Markdown im Ordner `docs/`
- Nummerierung im Dateinamen für Sortier-Reihenfolge
- Stand-Datum im Doc-Header
- Bei wesentlicher Änderung: Version (v1.x) im Header hochzählen + Changelog-Block ergänzen

## Confluence-Empfehlung

In Confluence pro Markdown-Datei eine eigene Seite anlegen unter
`mibeca → Datenschutz & Compliance → ITUKV Dashboard`. So lassen sich Änderungen
versioniert nachvollziehen.

---

*Diese Dokumentations-Mappe ist ein lebendes Konstrukt. Bei jeder relevanten Änderung
am Verfahren bitte das passende Dokument aktualisieren.*
