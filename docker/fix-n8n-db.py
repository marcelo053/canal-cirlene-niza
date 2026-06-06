#!/usr/bin/env python3
"""
fix-n8n-db.py — Patches n8n SQLite DB após import de workflows via API.

Problemas que resolve (n8n 2.x):
  1. workflow_published_version.publishedVersionId desatualizado após PUT via API
  2. workflow_history nodes desatualizados (n8n lê nodes do histórico, não de workflow_entity)
  3. webhook_entity com paths no formato {workflowId}/webhook/{path} em vez de só {path}
     → NOTE: n8n 2.x registra com esse formato mesmo; os webhooks ficam em
       /webhook/{workflowId}/webhook/{path} ao invés de /webhook/{path}

Uso:
  cd docker/
  python3 fix-n8n-db.py

Pré-requisito: n8n deve estar PARADO (para evitar lock WAL).
"""

import json
import sqlite3
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "data/n8n/database.sqlite"
WORKFLOWS_DIR = SCRIPT_DIR / "n8n-workflows"

WORKFLOW_MAP = {
    "gerador-avatar-staging-cirl":    None,  # preenchido abaixo
    "gerador-slides-staging-cirl":    None,
    "montagem-staging-cirl":          None,
    "roteirista-staging-cirl":        None,
}


def load_workflow_ids(db: sqlite3.Connection) -> dict[str, str]:
    rows = db.execute(
        "SELECT id, name FROM workflow_entity WHERE name IN ({})".format(
            ",".join("?" * len(WORKFLOW_MAP))
        ),
        list(WORKFLOW_MAP.keys()),
    ).fetchall()
    return {name: wf_id for wf_id, name in rows}


def sync_nodes_to_history(db: sqlite3.Connection, wf_id: str, name: str, nodes_json: str, connections_json: str):
    """Atualiza workflow_entity e workflow_history com os nodes atuais."""
    db.execute(
        "UPDATE workflow_entity SET nodes=?, connections=? WHERE id=?",
        (nodes_json, connections_json, wf_id),
    )
    row = db.execute(
        "SELECT publishedVersionId FROM workflow_published_version WHERE workflowId=?",
        (wf_id,),
    ).fetchone()
    if row:
        db.execute(
            "UPDATE workflow_history SET nodes=?, connections=? WHERE workflowId=? AND versionId=?",
            (nodes_json, connections_json, wf_id, row[0]),
        )
        print(f"  ✓ {name}: nodes synced → history({row[0][:8]})")
    else:
        print(f"  ⚠ {name}: sem published version, pulando history sync")


def sync_published_version(db: sqlite3.Connection, wf_id: str, name: str):
    """Garante publishedVersionId == versionId atual do workflow."""
    row = db.execute(
        "SELECT versionId FROM workflow_entity WHERE id=?", (wf_id,)
    ).fetchone()
    if not row:
        print(f"  ✗ {name}: workflow não encontrado no DB")
        return

    version_id = row[0]

    existing = db.execute(
        "SELECT publishedVersionId FROM workflow_published_version WHERE workflowId=?",
        (wf_id,),
    ).fetchone()

    if existing:
        if existing[0] != version_id:
            db.execute(
                "UPDATE workflow_published_version SET publishedVersionId=? WHERE workflowId=?",
                (version_id, wf_id),
            )
            print(f"  ✓ {name}: publishedVersionId atualizado → {version_id[:8]}")
        else:
            print(f"  ✓ {name}: publishedVersionId já correto")
    else:
        db.execute(
            "INSERT INTO workflow_published_version (workflowId, publishedVersionId) VALUES (?,?)",
            (wf_id, version_id),
        )
        print(f"  ✓ {name}: published version criada → {version_id[:8]}")


def main():
    if not DB_PATH.exists():
        print(f"✗ DB não encontrado: {DB_PATH}")
        sys.exit(1)

    print(f"DB: {DB_PATH}")
    db = sqlite3.connect(str(DB_PATH))
    db.execute("PRAGMA journal_mode=WAL")

    # Carrega IDs dos workflows
    id_map = load_workflow_ids(db)
    if not id_map:
        print("✗ Nenhum workflow encontrado. Rode setup-workflows.sh primeiro.")
        sys.exit(1)

    print(f"\nWorkflows encontrados: {len(id_map)}")

    # Para cada workflow JSON, sincroniza nodes + published version
    print("\n[1/2] Sincronizando nodes workflow_entity → workflow_history...")
    for json_file in sorted(WORKFLOWS_DIR.glob("*.json")):
        wf = json.loads(json_file.read_text())
        name = wf.get("name", "")
        wf_id = id_map.get(name)
        if not wf_id:
            print(f"  ⚠ {name}: não encontrado no DB, pulando")
            continue
        nodes_json = json.dumps(wf["nodes"], ensure_ascii=False)
        connections_json = json.dumps(wf.get("connections", {}), ensure_ascii=False)
        sync_nodes_to_history(db, wf_id, name, nodes_json, connections_json)

    print("\n[2/2] Sincronizando published versions...")
    for name, wf_id in id_map.items():
        sync_published_version(db, wf_id, name)

    db.commit()
    db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    db.commit()
    db.close()

    print("\n✓ DB corrigido. Reinicie o n8n para carregar os webhooks.")
    print("  Webhooks ficam em: /webhook/{workflowId}/webhook/{path}")
    print("  Exemplo: POST http://localhost:5679/webhook/TKFJZJviFg45eV0q/webhook/gerador-slides-staging-cirl")


if __name__ == "__main__":
    main()
