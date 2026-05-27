#!/bin/bash
# Safe Backend Deploy Script — verhindert kaputte Deploys.
# Pflicht-Checks BEVOR Code aufs Server geht.

set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "$0")/.." && pwd)/backend"
RESOURCE_GROUP="ITUKV"
FUNC_APP="itukv-func-v2"
HEALTH_URL="https://${FUNC_APP}.azurewebsites.net/api/health"

cd "$BACKEND_DIR"

echo "═══════════════════════════════════════════════"
echo "  Backend Pre-Deploy Safety Checks"
echo "═══════════════════════════════════════════════"

# 1) Python Syntax Check (AST)
echo -n "  [1/4] Python Syntax (AST parse)… "
if ! python3 -c "import ast; ast.parse(open('function_app.py').read())" 2>/tmp/ast-err; then
  echo "FAIL"
  echo
  echo "❌ Python-Syntax-Fehler in function_app.py:"
  cat /tmp/ast-err
  echo
  echo "Deploy ABGEBROCHEN. Backend wird NICHT aktualisiert."
  exit 1
fi
echo "OK"

# 2) requirements.txt validität
echo -n "  [2/4] requirements.txt vorhanden… "
if [ ! -f requirements.txt ]; then
  echo "FAIL"
  echo "❌ requirements.txt fehlt"; exit 1
fi
echo "OK"

# 3) host.json valide JSON
echo -n "  [3/4] host.json valide JSON… "
if ! python3 -c "import json; json.load(open('host.json'))" 2>/tmp/json-err; then
  echo "FAIL"
  echo "❌ host.json ist kein valides JSON:"
  cat /tmp/json-err
  exit 1
fi
echo "OK"

# 4) function_app.py importiert sauber (Routen-Registrierung)
echo -n "  [4/4] Routen-Definitionen plausibel… "
ROUTES=$(grep -c "@app.route" function_app.py)
if [ "$ROUTES" -lt 30 ]; then
  echo "FAIL"
  echo "❌ Nur $ROUTES Routes gefunden — sieht kaputt aus. Erwartet ~60+."
  exit 1
fi
echo "OK ($ROUTES Routes)"

echo
echo "✅ Alle Pre-Checks bestanden — starte Deploy."
echo

# Zip + Deploy
rm -f /tmp/backend-deploy.zip
zip -r -q /tmp/backend-deploy.zip . -x "*.pyc" -x "__pycache__/*" -x ".venv/*" -x "*.log"
echo "  Zip-Größe: $(du -h /tmp/backend-deploy.zip | cut -f1)"

echo "  Deploying via az functionapp deployment source config-zip…"
DEPLOY_OUT=$(az functionapp deployment source config-zip \
  --resource-group "$RESOURCE_GROUP" --name "$FUNC_APP" \
  --src /tmp/backend-deploy.zip --build-remote true --timeout 600 2>&1)

if ! echo "$DEPLOY_OUT" | grep -q '"status_text"'; then
  echo "❌ Deploy fehlgeschlagen:"
  echo "$DEPLOY_OUT" | tail -10
  exit 1
fi
echo "  Deploy abgeschlossen."

# Health-Check: warte bis Backend antwortet
echo
echo "═══════════════════════════════════════════════"
echo "  Post-Deploy Health-Check (max 3 Min)"
echo "═══════════════════════════════════════════════"

START=$(date +%s)
DEADLINE=$((START + 180))
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  CODE=$(curl -s -o /dev/null -w '%{http_code}' "$HEALTH_URL" || echo "000")
  ELAPSED=$(($(date +%s) - START))
  if [ "$CODE" = "200" ]; then
    echo "✅ Backend antwortet ($CODE) nach ${ELAPSED}s — Deploy erfolgreich."
    exit 0
  fi
  echo "  ⏳ ${ELAPSED}s · HTTP $CODE · warte…"
  sleep 10
done

echo
echo "⚠️  Health-Check fehlgeschlagen nach 3 Min."
echo "   Backend antwortet nicht. Möglicherweise braucht der Cold-Start"
echo "   noch etwas länger ODER der Deploy hat den Host gebrochen."
echo "   Prüfe manuell: $HEALTH_URL"
exit 1
