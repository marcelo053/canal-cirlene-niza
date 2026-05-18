#!/usr/bin/env python3
"""
Cria as 5 tabelas do Canal Cirlene Niza no Baserow database 177.
Uso: BASEROW_URL=... BASEROW_EMAIL=... BASEROW_PASSWORD=... python3 baserow_create_tables.py
Ou:  python3 baserow_create_tables.py (lê .env automaticamente)
"""
import os
import sys
import json
import requests
from pathlib import Path

# --- Config ---
SCRIPT_DIR = Path(__file__).parent
ENV_PATH = SCRIPT_DIR.parent / ".env"
DATABASE_ID = 177


def load_env(path):
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def get_jwt(base_url, email, password):
    r = requests.post(f"{base_url}/api/user/token-auth/", json={"email": email, "password": password})
    r.raise_for_status()
    return r.json()["token"]


def create_table(base_url, headers, db_id, name, fields):
    r = requests.post(
        f"{base_url}/api/database/tables/database/{db_id}/",
        headers=headers,
        json={"name": name},
    )
    r.raise_for_status()
    table_id = r.json()["id"]
    print(f"  ✓ Tabela criada: {name} (id={table_id})")

    # Remove campo padrão "Name" se necessário e cria os campos
    for field in fields:
        rf = requests.post(
            f"{base_url}/api/database/fields/table/{table_id}/",
            headers=headers,
            json=field,
        )
        if rf.status_code not in (200, 201):
            print(f"    ⚠ Campo {field['name']}: {rf.text[:120]}")
        else:
            print(f"    + {field['name']} ({field['type']})")

    return table_id


def main():
    load_env(ENV_PATH)

    base_url = os.environ.get("BASEROW_URL", "http://186.202.209.88:85").rstrip("/")
    email    = os.environ.get("BASEROW_EMAIL") or input("Baserow email: ")
    password = os.environ.get("BASEROW_PASSWORD") or input("Baserow password: ")

    print(f"\nConectando em {base_url} ...")
    token = get_jwt(base_url, email, password)
    headers = {"Authorization": f"JWT {token}", "Content-Type": "application/json"}
    print("JWT obtido.\n")

    # ------------------------------------------------------------------ #
    # Definição das tabelas                                                #
    # ------------------------------------------------------------------ #

    STATUS_PRODUCAO = [
        {"value": "rascunho",    "color": "light-gray"},
        {"value": "em_producao", "color": "blue"},
        {"value": "pronto",      "color": "green"},
        {"value": "publicado",   "color": "dark-green"},
        {"value": "erro",        "color": "red"},
    ]

    STATUS_POST = [
        {"value": "pendente",  "color": "light-gray"},
        {"value": "pronto",    "color": "blue"},
        {"value": "publicado", "color": "dark-green"},
        {"value": "erro",      "color": "red"},
    ]

    PLATAFORMAS = [
        {"value": "youtube",   "color": "red"},
        {"value": "tiktok",    "color": "dark-blue"},
        {"value": "instagram", "color": "pink"},
    ]

    tables = [
        {
            "name": "productions_cirlene",
            "fields": [
                {"name": "title",             "type": "text"},
                {"name": "status",            "type": "single_select", "select_options": STATUS_PRODUCAO},
                {"name": "roteiro",           "type": "long_text"},
                {"name": "keywords",          "type": "text"},
                {"name": "duracao_segundos",  "type": "number", "number_decimal_places": 0},
                {"name": "video_final_url",   "type": "url"},
                {"name": "created_at",        "type": "date", "date_include_time": True},
            ],
        },
        {
            "name": "scenes_cirlene",
            "fields": [
                {"name": "production_id",    "type": "number", "number_decimal_places": 0},
                {"name": "scene_number",     "type": "number", "number_decimal_places": 0},
                {"name": "narration_text",   "type": "long_text"},
                {"name": "audio_url",        "type": "url"},
                {"name": "image_url",        "type": "url"},
                {"name": "avatar_url",       "type": "url"},
                {"name": "duration_seconds", "type": "number", "number_decimal_places": 1},
            ],
        },
        {
            "name": "social_posts_cirlene",
            "fields": [
                {"name": "production_id", "type": "number", "number_decimal_places": 0},
                {"name": "platform",      "type": "single_select", "select_options": PLATAFORMAS},
                {"name": "status",        "type": "single_select", "select_options": STATUS_POST},
                {"name": "video_url",     "type": "url"},
                {"name": "title",         "type": "text"},
                {"name": "description",   "type": "long_text"},
                {"name": "tags",          "type": "text"},
                {"name": "post_url",      "type": "url"},
                {"name": "published_at",  "type": "date", "date_include_time": True},
                {"name": "error_message", "type": "long_text"},
            ],
        },
        {
            "name": "metrics_cirlene",
            "fields": [
                {"name": "post_id",      "type": "number", "number_decimal_places": 0},
                {"name": "platform",     "type": "single_select", "select_options": PLATAFORMAS},
                {"name": "views",        "type": "number", "number_decimal_places": 0},
                {"name": "likes",        "type": "number", "number_decimal_places": 0},
                {"name": "comments",     "type": "number", "number_decimal_places": 0},
                {"name": "shares",       "type": "number", "number_decimal_places": 0},
                {"name": "collected_at", "type": "date", "date_include_time": True},
            ],
        },
        {
            "name": "costs_cirlene",
            "fields": [
                {"name": "production_id", "type": "number", "number_decimal_places": 0},
                {"name": "service",       "type": "single_select", "select_options": [
                    {"value": "elevenlabs", "color": "purple"},
                    {"value": "heygen",     "color": "blue"},
                    {"value": "evolink",    "color": "orange"},
                    {"value": "fal",        "color": "pink"},
                    {"value": "ffmpeg",     "color": "light-gray"},
                ]},
                {"name": "cost_usd",      "type": "number", "number_decimal_places": 4},
                {"name": "tokens_used",   "type": "number", "number_decimal_places": 0},
                {"name": "description",   "type": "text"},
                {"name": "created_at",    "type": "date", "date_include_time": True},
            ],
        },
    ]

    # ------------------------------------------------------------------ #
    # Criação                                                              #
    # ------------------------------------------------------------------ #
    created = {}
    for t in tables:
        print(f"Criando {t['name']} ...")
        try:
            tid = create_table(base_url, headers, DATABASE_ID, t["name"], t["fields"])
            created[t["name"]] = tid
        except requests.HTTPError as e:
            print(f"  ERRO: {e.response.text[:200]}")

    print("\n=== IDs criados ===")
    for name, tid in created.items():
        print(f"{tid}  {name}")

    print("\nAtualize BASEROW_TABLE_* no .env do projeto com esses IDs.")


if __name__ == "__main__":
    main()
