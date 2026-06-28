#!/usr/bin/env python3
"""
fix-n8n-db.py — Patches n8n SQLite DB após import de workflows via API.

Problemas que resolve (n8n 2.x / 2.23.4):

  1. webhook_entity com paths no formato {workflowId}/{nodeName}/{path} em vez de {path}
     ROOT CAUSE: n8n usa workflow_history.nodes para ativar. Quando o nó webhook não
     tem campo "webhookId" (undefined em JS), usa o path longo.
     FIX: garantir que todos os nós webhook em workflow_history.nodes e
     workflow_entity.nodes tenham "webhookId": null (não ausente).
     null != undefined → n8n usa o branch isFullPath=true → path curto.

  2. webhook_entity stale — apaga entradas para forçar re-registro limpo no restart.

Uso:
  cd docker/
  docker stop cirlene-n8n
  python3 fix-n8n-db.py    # roda via --volumes-from ou path direto
  docker start cirlene-n8n

Pré-requisito: n8n deve estar PARADO (para evitar lock WAL).

Detalhes técnicos do bug n8n 2.23.4:
  getNodeWebhookPath(workflowId, node, path, isFullPath, restartWebhook):
    if node.webhookId === undefined:  ← ausente no JSON → undefined em JS
      return `${workflowId}/${nodeName}/${path}`  ← LONG FORM
    else:
      if isFullPath === true:  ← Webhook node sempre tem isFullPath:true
        return path || node.webhookId  ← SHORT FORM ✓

  Quando webhookId é null (não undefined):
    node.webhookId === undefined → false → usa isFullPath=true → SHORT FORM ✓
"""

import json
import sqlite3
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "data/n8n/database.sqlite"


def fix_webhook_nodes_in_json(nodes_json: str) -> tuple[str, bool]:
    """
    Garante que todos os nós webhook tenham webhookId: null (não ausente).
    Retorna (novo_json, houve_mudança).
    """
    nodes = json.loads(nodes_json)
    changed = False
    for node in nodes:
        if "webhook" in node.get("type", "").lower():
            if "webhookId" not in node:
                node["webhookId"] = None
                changed = True
    return json.dumps(nodes, ensure_ascii=False), changed


def fix_workflow(db: sqlite3.Connection, wf_id: str, name: str):
    """Fix workflow_entity.nodes e workflow_history.nodes."""
    # Fix workflow_entity.nodes
    row = db.execute(
        "SELECT nodes FROM workflow_entity WHERE id=?", (wf_id,)
    ).fetchone()
    if row:
        new_nodes, changed = fix_webhook_nodes_in_json(row[0])
        if changed:
            db.execute(
                "UPDATE workflow_entity SET nodes=? WHERE id=?",
                (new_nodes, wf_id),
            )
            print(f"  ✓ {name}: workflow_entity.nodes corrigido")

    # Fix ALL workflow_history.nodes entries
    hist_rows = db.execute(
        "SELECT versionId, nodes FROM workflow_history WHERE workflowId=?",
        (wf_id,),
    ).fetchall()
    fixed_count = 0
    for ver_id, nodes_json in hist_rows:
        new_nodes, changed = fix_webhook_nodes_in_json(nodes_json)
        if changed:
            db.execute(
                "UPDATE workflow_history SET nodes=? WHERE workflowId=? AND versionId=?",
                (new_nodes, wf_id, ver_id),
            )
            fixed_count += 1
    if fixed_count:
        print(f"  ✓ {name}: {fixed_count} workflow_history entrada(s) corrigida(s)")


def main():
    if not DB_PATH.exists():
        print(f"✗ DB não encontrado: {DB_PATH}")
        sys.exit(1)

    print(f"DB: {DB_PATH}")
    db = sqlite3.connect(str(DB_PATH))
    db.execute("PRAGMA journal_mode=WAL")

    # Carrega todos os workflows
    workflows = db.execute("SELECT id, name FROM workflow_entity").fetchall()
    if not workflows:
        print("✗ Nenhum workflow encontrado.")
        sys.exit(1)

    print(f"\nWorkflows encontrados: {len(workflows)}")

    print("\n[1/2] Corrigindo webhookId nos nós webhook (workflow_entity + workflow_history)...")
    for wf_id, name in workflows:
        fix_workflow(db, wf_id, name)

    print("\n[2/2] Limpando webhook_entity (será re-populado no restart)...")
    count = db.execute("SELECT COUNT(*) FROM webhook_entity").fetchone()[0]
    db.execute("DELETE FROM webhook_entity")
    print(f"  ✓ Removidas {count} entradas de webhook_entity")

    db.commit()
    db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    db.commit()
    db.close()

    print("\n✓ DB corrigido. Reinicie o n8n para registrar os webhooks.")
    print("  Webhooks ficam em: /webhook/{path}")
    print("  Ex: POST http://localhost:5678/webhook/gerador-avatar-staging-cirl")


if __name__ == "__main__":
    main()
