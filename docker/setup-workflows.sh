#!/bin/bash
# Importa os workflows de staging no n8n via API.
# Uso: ./setup-workflows.sh [N8N_URL]
set -e

N8N_URL="${1:-http://localhost:5679}"
API="${N8N_URL}/api/v1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKFLOWS_DIR="${SCRIPT_DIR}/n8n-workflows"

echo "→ n8n: ${N8N_URL}"

# Aguarda n8n estar pronto
echo "→ Aguardando n8n..."
for i in $(seq 1 30); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${N8N_URL}/healthz" 2>/dev/null || echo "000")
  [ "$STATUS" = "200" ] && break
  sleep 3
done
echo "→ n8n pronto"

# Cria API key se não existir
API_KEY_FILE="${SCRIPT_DIR}/.n8n-api-key"
if [ ! -f "$API_KEY_FILE" ]; then
  echo "→ Criando API key..."
  RESPONSE=$(curl -s -X POST "${N8N_URL}/api/v1/user-settings" \
    -H "Content-Type: application/json" \
    -b "n8n-auth=skip" 2>/dev/null || echo "{}")

  # Tenta obter/criar via owner setup se necessário
  KEY_RESP=$(curl -s -X POST "${API}/api-key" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" 2>/dev/null || echo "{}")

  API_KEY=$(echo "$KEY_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('apiKey',''))" 2>/dev/null || echo "")

  if [ -z "$API_KEY" ]; then
    echo "→ AVISO: Não consegui criar API key automaticamente."
    echo "→ Crie manualmente em: ${N8N_URL}/settings/api"
    echo "→ Depois salve em: ${API_KEY_FILE}"
    echo "→ e rode novamente."
    exit 1
  fi
  echo "$API_KEY" > "$API_KEY_FILE"
fi

API_KEY=$(cat "$API_KEY_FILE")
echo "→ API key: ${API_KEY:0:8}..."

import_workflow() {
  local file="$1"
  local name=$(python3 -c "import json; d=json.load(open('$file')); print(d['name'])")

  # Verifica se já existe
  EXISTING=$(curl -s "${API}/workflows" \
    -H "X-N8N-API-KEY: ${API_KEY}" | \
    python3 -c "import sys,json; d=json.load(sys.stdin); wfs=d.get('data',[]); print(next((w['id'] for w in wfs if w['name']=='${name}'),''))" 2>/dev/null || echo "")

  if [ -n "$EXISTING" ]; then
    echo "→ Atualizando: ${name} (id: ${EXISTING})"
    curl -s -X PUT "${API}/workflows/${EXISTING}" \
      -H "X-N8N-API-KEY: ${API_KEY}" \
      -H "Content-Type: application/json" \
      -d @"$file" > /dev/null
  else
    echo "→ Criando: ${name}"
    curl -s -X POST "${API}/workflows" \
      -H "X-N8N-API-KEY: ${API_KEY}" \
      -H "Content-Type: application/json" \
      -d @"$file" > /dev/null
  fi
  echo "   ✓ ${name}"
}

for f in "${WORKFLOWS_DIR}"/*.json; do
  import_workflow "$f"
done

echo ""
echo "✓ Workflows importados: ${N8N_URL}/workflows"
