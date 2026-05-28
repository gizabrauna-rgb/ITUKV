# Anleitung: Budget-Limit + Spending-Alert in der Anthropic Console

**Ziel:** Vermeiden, dass unbeabsichtigte oder fehlerhafte KI-Aufrufe hohe Kosten verursachen.
**Aufwand:** ca. 5 Minuten.
**Zugriff:** Anthropic-Console-Login als Owner / Billing-Admin der Organisation.

---

## Schritt 1: Console öffnen

1. Browser → https://console.anthropic.com
2. Login mit dem mibeca-Account (Owner-Rolle)

---

## Schritt 2: Billing & Limits einsehen

1. Linkes Menü → **„Settings"** öffnen
2. Untermenü **„Billing"** → **„Billing Limits"** (oder „Usage Limits") wählen

Du siehst die aktuelle Nutzung (Token verbraucht, $-Summe) und vorhandene Limits.

---

## Schritt 3: Hard-Limit setzen

Ein Hard-Limit stoppt API-Aufrufe automatisch, sobald der Betrag erreicht ist.

1. Klick auf **„Set monthly spending limit"** (oder ähnlich)
2. Empfehlung für den Anfang: **50 US-Dollar pro Monat** (entspricht ca. 45 EUR)
   - Das reicht für mehrere hundert Dokument-Analysen, je nach PDF-Größe
   - Kann später angehoben werden, wenn ihr regelmäßig analysiert
3. Speichern
4. Anthropic blockiert ab Erreichen automatisch neue API-Aufrufe mit HTTP 429.

> Hinweis: Das Backend (ITUKV) zeigt dem Admin in dem Fall einen Fehler an. Die KI-
> Funktion ist dann ohne Datenverlust gesperrt, bis das nächste Abrechnungs-Zyklus
> beginnt oder das Limit manuell erhöht wird.

---

## Schritt 4: Spending-Alerts setzen

Alerts sind Mail-Benachrichtigungen, **bevor** das Limit erreicht wird.

1. Im selben Menü auf **„Alerts"** klicken
2. Drei Schwellen-Alerts anlegen (Empfehlung):

| Schwelle | Empfänger | Bedeutung |
|---|---|---|
| 50 % | ab@mike-bergmann.de | Frühwarnung – noch entspannt |
| 80 % | ab@mike-bergmann.de + jk@mike-bergmann.de | gelb – beobachten |
| 100 % | ab@mike-bergmann.de + jk@mike-bergmann.de | Limit erreicht – Service gesperrt |

3. Pro Alert: Schwelle eingeben + Mailadresse + speichern.

---

## Schritt 5: Workspace-Limit (optional, falls mehrere Workspaces)

Falls mibeca mehrere Anthropic-Workspaces hat (z. B. „Production" + „Test"), für
jeden Workspace ein eigenes Limit konfigurieren. So kann z. B. Test 5 USD und
Production 50 USD haben.

---

## Schritt 6: Bestätigung im Audit

Nach Einrichtung:

- Screenshot der Limit-Seite machen und unter `docs/legal/anthropic-limits-2026-05-28.png` ablegen
- Im AI-Security-Konzept (§1a Compliance-Tabelle) den Punkt **„Budget-Limit"** auf
  ✅ setzen und Datum eintragen

---

## Notfall: Limit zurücksetzen

Wenn versehentlich gesperrt:

1. In Billing-Limit das Limit anheben oder ganz entfernen
2. API ist sofort wieder verfügbar
3. Im Audit-Log dokumentieren, warum die Anhebung nötig war

---

## Was passiert ohne Limit?

- Anthropic stellt ungebremst Rechnung am Monatsende
- Bei einem Bug oder Missbrauch kann das schnell vierstellig werden
- Daher: **Hard-Limit ist Pflicht, kein Komfort**.

---

*Letzte Prüfung dieser Anleitung: 2026-05-28. Anthropic-UI kann sich ändern, dann
ggf. mit Anthropic-Support abgleichen.*
