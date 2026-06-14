"""Canal Cirlene Niza — Streamlit Approval UI (Gate 2: Artes, Gate 3: Vídeo).

Configuração via env vars:
  BASEROW_URL           http://186.202.209.88:85
  BASEROW_TOKEN         <token da API>
  BASEROW_TABLE_PRODUCTIONS  <int>
  BASEROW_TABLE_SCENES       <int>
  FIELD_APPROVAL_STATUS      <int>   field ID do campo approval_status
  FIELD_APPROVAL_FEEDBACK    <int>   field ID do campo approval_feedback
  FIELD_TITLE                <int>   field ID do campo title/name
  FIELD_PRODUCTION_ID        <int>   field ID do campo production_id (string)
  FIELD_COST                 <int>   field ID do campo cost_estimate_usd (opcional)
  MINIO_ENDPOINT        http://186.202.209.88:9000
  MINIO_ACCESS_KEY      minioadmin
  MINIO_SECRET_KEY      minioadmin
"""
from __future__ import annotations

import datetime
import os

import requests
import streamlit as st

# ─── Config ──────────────────────────────────────────────────────────────────

BASEROW_URL = os.environ.get("BASEROW_URL", "").rstrip("/")
BASEROW_TOKEN = os.environ.get("BASEROW_TOKEN", "")
TABLE_PRODUCTIONS = os.environ.get("BASEROW_TABLE_PRODUCTIONS", "")
TABLE_SCENES = os.environ.get("BASEROW_TABLE_SCENES", "")
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")

# Field IDs (numeric) — set via env vars after Baserow tables are created
FIELD_APPROVAL_STATUS = os.environ.get("FIELD_APPROVAL_STATUS", "")
FIELD_APPROVAL_FEEDBACK = os.environ.get("FIELD_APPROVAL_FEEDBACK", "")
FIELD_TITLE = os.environ.get("FIELD_TITLE", "")
FIELD_PRODUCTION_ID = os.environ.get("FIELD_PRODUCTION_ID", "")
FIELD_COST = os.environ.get("FIELD_COST", "")

_CONFIGURED = all([BASEROW_URL, BASEROW_TOKEN, TABLE_PRODUCTIONS, TABLE_SCENES,
                   FIELD_APPROVAL_STATUS, FIELD_TITLE])


# ─── Baserow helpers ─────────────────────────────────────────────────────────

def _headers() -> dict:
    return {"Authorization": f"Token {BASEROW_TOKEN}", "Content-Type": "application/json"}


def _fk(field_id: str) -> str:
    """Return field_XXXX key from numeric ID string."""
    return f"field_{field_id}"


def _list_rows(table_id: str, filters: dict | None = None) -> list[dict]:
    params = {"size": 200}
    if filters:
        params.update(filters)
    rows: list[dict] = []
    url = f"{BASEROW_URL}/api/database/rows/table/{table_id}/"
    while url:
        r = requests.get(url, headers=_headers(), params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        rows.extend(data.get("results", []))
        url = data.get("next")
        params = {}  # only on first page
    return rows


def _patch_row(table_id: str, row_id: int, payload: dict) -> None:
    url = f"{BASEROW_URL}/api/database/rows/table/{table_id}/{row_id}/?user_field_names=false"
    r = requests.patch(url, headers=_headers(), json=payload, timeout=10)
    r.raise_for_status()


def _list_pending(status_value: str) -> list[dict]:
    """List productions with given approval_status single-select value."""
    return _list_rows(TABLE_PRODUCTIONS, {
        f"filter__field_{FIELD_APPROVAL_STATUS}__single_select_equal": status_value,
    })


def _scenes_for(production_id: str) -> list[dict]:
    """List scenes linked to a production_id value."""
    if not TABLE_SCENES or not FIELD_PRODUCTION_ID:
        return []
    return _list_rows(TABLE_SCENES, {
        f"filter__field_{FIELD_PRODUCTION_ID}__equal": production_id,
        "order_by": f"field_{FIELD_PRODUCTION_ID}",
    })


# ─── MinIO presigned URL ──────────────────────────────────────────────────────

def _presigned(minio_url: str) -> str | None:
    """Convert minio://bucket/key to a presigned HTTP URL."""
    if not minio_url or not minio_url.startswith("minio://"):
        return None
    path = minio_url[8:]
    parts = path.split("/", 1)
    if len(parts) < 2:
        return None
    bucket, key = parts
    try:
        from minio import Minio
        client = Minio(
            MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_ENDPOINT.startswith("https://"),
        )
        return client.presigned_get_object(bucket, key, expires=datetime.timedelta(hours=2))
    except Exception:
        # Fallback: direct HTTP URL (works if MinIO public)
        return f"{MINIO_ENDPOINT}/{bucket}/{key}"


# ─── UI helpers ──────────────────────────────────────────────────────────────

def _age(ts: str) -> str:
    try:
        dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return "?"
    delta = datetime.datetime.now(datetime.timezone.utc) - dt
    if delta.total_seconds() < 60:
        return f"{int(delta.total_seconds())}s"
    if delta.total_seconds() < 3600:
        return f"{int(delta.total_seconds() / 60)}min"
    if delta.days == 0:
        return f"{delta.seconds // 3600}h"
    return f"{delta.days}d"


def _approve_action(table_id: str, row_id: int, new_status: str, feedback: str = "") -> bool:
    try:
        payload: dict = {_fk(FIELD_APPROVAL_STATUS): new_status}
        if FIELD_APPROVAL_FEEDBACK and feedback:
            payload[_fk(FIELD_APPROVAL_FEEDBACK)] = feedback
        _patch_row(table_id, row_id, payload)
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar Baserow: {e}")
        return False


def _render_slide_gallery(production_pid: str) -> None:
    """Show slides from cirlene-slides bucket for this production."""
    # List via direct MinIO prefix listing
    try:
        from minio import Minio
        client = Minio(
            MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_ENDPOINT.startswith("https://"),
        )
        objects = list(client.list_objects("cirlene-slides", prefix=f"slides/{production_pid}"))
        if not objects:
            st.info("Slides ainda não gerados para esta produção.")
            return
        cols = st.columns(min(len(objects), 3))
        for i, obj in enumerate(objects):
            url = client.presigned_get_object("cirlene-slides", obj.object_name,
                                              expires=datetime.timedelta(hours=2))
            with cols[i % 3]:
                st.video(url)
                st.caption(obj.object_name.split("/")[-1])
    except ImportError:
        st.warning("minio package não instalado. `pip install minio`")
    except Exception as e:
        st.warning(f"Não foi possível listar slides: {e}")


def _render_scene_list(production_pid: str) -> None:
    """Show scenes from Baserow for this production."""
    scenes = _scenes_for(production_pid)
    if not scenes:
        st.info("Nenhuma cena no Baserow para esta produção.")
        return
    for scene in scenes:
        name = scene.get("Name") or scene.get(f"field_{FIELD_PRODUCTION_ID}", "?")
        audio_raw = scene.get("audio_url") or ""
        image_raw = scene.get("image_url") or ""
        st.markdown(f"**{name}**")
        col_img, col_aud = st.columns(2)
        with col_img:
            img_url = _presigned(image_raw) if image_raw.startswith("minio://") else image_raw
            if img_url:
                st.image(img_url, width=200)
            else:
                st.markdown("_(sem imagem)_")
        with col_aud:
            aud_url = _presigned(audio_raw) if audio_raw.startswith("minio://") else audio_raw
            if aud_url:
                st.audio(aud_url)
            else:
                st.markdown("_(sem áudio)_")
        st.markdown("---")


def _render_production_gate2(prod: dict) -> None:
    """Gate 2 card: show slides + approve/revise."""
    row_id = prod["id"]
    title = prod.get(_fk(FIELD_TITLE)) or f"Produção #{row_id}"
    production_pid = prod.get(_fk(FIELD_PRODUCTION_ID), "") if FIELD_PRODUCTION_ID else ""
    cost = prod.get(_fk(FIELD_COST), 0.0) if FIELD_COST else 0.0
    created = prod.get("created_on", "")
    age = _age(created) if created else "?"

    with st.expander(f"🎨 {title}  |  {age}  |  ~${float(cost or 0):.2f}  |  #{row_id}", expanded=True):
        tabs = st.tabs(["Slides Remotion", "Cenas Baserow"])
        with tabs[0]:
            if production_pid:
                _render_slide_gallery(production_pid)
            else:
                st.info("production_id não mapeado — configure FIELD_PRODUCTION_ID.")
        with tabs[1]:
            if production_pid:
                _render_scene_list(production_pid)
            else:
                st.info("production_id não mapeado.")

        col_a, col_rv = st.columns([1, 2])
        with col_a:
            if st.button("✓ Aprovar Artes", key=f"approve-arts-{row_id}", type="primary"):
                if _approve_action(TABLE_PRODUCTIONS, row_id, "approved_arts"):
                    st.success("Artes aprovadas! Pipeline avança para montagem.")
                    st.rerun()
        with col_rv:
            with st.form(key=f"revise-arts-{row_id}"):
                fb = st.text_area("Feedback", placeholder="Ex: Slide 2 com erro de digitação...",
                                  key=f"fb-arts-{row_id}")
                if st.form_submit_button("✎ Revisar"):
                    if fb.strip():
                        if _approve_action(TABLE_PRODUCTIONS, row_id, "revise_arts", fb.strip()):
                            st.success("Revisão enviada.")
                            st.rerun()
                    else:
                        st.warning("Forneça feedback antes de revisar.")


def _render_production_gate3(prod: dict) -> None:
    """Gate 3 card: show final video + approve/revise."""
    row_id = prod["id"]
    title = prod.get(_fk(FIELD_TITLE)) or f"Produção #{row_id}"
    production_pid = prod.get(_fk(FIELD_PRODUCTION_ID), "") if FIELD_PRODUCTION_ID else ""
    cost = prod.get(_fk(FIELD_COST), 0.0) if FIELD_COST else 0.0
    created = prod.get("created_on", "")
    age = _age(created) if created else "?"

    with st.expander(f"🎬 {title}  |  {age}  |  ~${float(cost or 0):.2f}  |  #{row_id}", expanded=True):
        # Show final video from MinIO
        video_path = f"minio://cirlene-video/{production_pid}/final.mp4" if production_pid else ""
        video_url = _presigned(video_path) if video_path else None
        if video_url:
            st.video(video_url)
        else:
            st.info("Vídeo final ainda não disponível ou production_id não configurado.")

        col_a, col_rv = st.columns([1, 2])
        with col_a:
            if st.button("✓ Aprovar Vídeo", key=f"approve-video-{row_id}", type="primary"):
                if _approve_action(TABLE_PRODUCTIONS, row_id, "approved_video"):
                    st.success("Vídeo aprovado! Será publicado nas plataformas.")
                    st.rerun()
        with col_rv:
            with st.form(key=f"revise-video-{row_id}"):
                fb = st.text_area("Feedback", placeholder="Ex: Corte no final abrupto...",
                                  key=f"fb-video-{row_id}")
                if st.form_submit_button("✎ Revisar"):
                    if fb.strip():
                        if _approve_action(TABLE_PRODUCTIONS, row_id, "revise_video", fb.strip()):
                            st.success("Revisão enviada.")
                            st.rerun()
                    else:
                        st.warning("Forneça feedback antes de revisar.")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="Cirlene Niza — Aprovação",
        page_icon="🌿",
        layout="wide",
    )
    st.title("🌿 Canal Cirlene Niza — Aprovação")

    # Auto-refresh every 30s
    st.components.v1.html("<meta http-equiv='refresh' content='30'>", height=0)

    if not _CONFIGURED:
        st.warning(
            "⚠️ Baserow não configurado. Defina as variáveis de ambiente:\n\n"
            "```\nBASEROW_URL, BASEROW_TOKEN, BASEROW_TABLE_PRODUCTIONS,\n"
            "BASEROW_TABLE_SCENES, FIELD_APPROVAL_STATUS, FIELD_TITLE\n```\n\n"
            "O app está no ar mas não pode conectar ao Baserow ainda."
        )
        st.stop()

    tab_gate2, tab_gate3 = st.tabs(["🎨 Gate 2 — Artes", "🎬 Gate 3 — Vídeo"])

    with tab_gate2:
        try:
            pending_arts = _list_pending("pending_arts")
        except Exception as e:
            st.error(f"Erro ao buscar produções: {e}")
            pending_arts = []

        if not pending_arts:
            st.info("Nenhuma produção aguardando aprovação de artes.")
        else:
            st.success(f"{len(pending_arts)} produção(ões) aguardando aprovação de artes")
            for prod in pending_arts:
                _render_production_gate2(prod)

    with tab_gate3:
        try:
            pending_video = _list_pending("pending_video")
        except Exception as e:
            st.error(f"Erro ao buscar produções: {e}")
            pending_video = []

        if not pending_video:
            st.info("Nenhum vídeo aguardando aprovação.")
        else:
            st.success(f"{len(pending_video)} vídeo(s) aguardando aprovação")
            for prod in pending_video:
                _render_production_gate3(prod)

    st.caption("Auto-atualização a cada 30s  |  Canal Cirlene Niza")


if __name__ == "__main__":
    main()
