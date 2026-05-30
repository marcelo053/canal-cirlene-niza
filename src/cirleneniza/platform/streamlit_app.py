import json
import threading
import time

import streamlit as st

from cirleneniza.config import get_settings
from cirleneniza.tools.baserow import BaserowClient

st.set_page_config(page_title="Canal Cirlene Niza", page_icon="🍊", layout="wide")


@st.cache_resource
def _get_baserow() -> BaserowClient:
    cfg = get_settings()
    return BaserowClient(base_url=cfg.baserow_url, token=cfg.baserow_token)


def _list_productions(status: str | None = None) -> list[dict]:
    cfg = get_settings()
    baserow = _get_baserow()
    try:
        return baserow.list_rows(
            cfg.baserow_table_productions,
            filter_field="status" if status else None,
            filter_value=status,
            order_by="-id",
            size=50,
        )
    except Exception as e:
        st.error(f"Erro ao listar produções: {e}")
        return []


def _parse_script_data(keywords_json: str) -> dict:
    if not keywords_json:
        return {}
    try:
        return json.loads(keywords_json)
    except Exception:
        return {}


def _launch_producao(production_id: int, script_data: dict, topic: str, style_guide: str = "") -> None:
    from cirleneniza.crew.video_crew_produzir import ProduzirCrew
    session = {
        "topic": topic,
        "production_id": production_id,
        "script_data": script_data,
        "style_guide": style_guide,
    }
    thread = threading.Thread(target=ProduzirCrew().run, args=(session,), daemon=True)
    thread.start()


def _render_roteiro(sd: dict) -> None:
    if sd.get("intro"):
        with st.expander("INTRO"):
            st.write(sd["intro"])
    if sd.get("main"):
        with st.expander("MAIN"):
            st.write(sd["main"])
    if sd.get("outro"):
        with st.expander("OUTRO"):
            st.write(sd["outro"])
    cenas = sd.get("cena_prompts", [])
    if cenas:
        with st.expander(f"Cenas ({len(cenas)})"):
            for i, c in enumerate(cenas, 1):
                st.markdown(f"**Cena {i}: {c.get('scene', '')}**")
                if c.get("hook_technique"):
                    st.caption(f"HOOK: {c['hook_technique']}")
                st.write(c.get("locutor", ""))
                st.divider()


def _section_pendentes() -> None:
    st.header("Pendentes de Aprovação")
    productions = _list_productions("rascunho")

    if not productions:
        st.info("Nenhum roteiro aguardando aprovação. Gere um via Telegram com /roteiro.")
        return

    cfg = get_settings()
    baserow = _get_baserow()

    for prod in productions:
        prod_id = prod["id"]
        title = prod.get("title", f"Produção #{prod_id}")
        keywords_json = prod.get("keywords", "")
        thumbnail_url = prod.get("thumbnail_url", "")
        sd = _parse_script_data(keywords_json)

        with st.container(border=True):
            col_info, col_thumb = st.columns([3, 1])
            with col_info:
                st.subheader(title)
                st.caption(f"ID: {prod_id}")
                if sd:
                    _render_roteiro(sd)
                else:
                    roteiro_text = prod.get("roteiro", "")
                    if roteiro_text:
                        with st.expander("Roteiro"):
                            st.text(roteiro_text[:3000])
                    else:
                        st.warning("Roteiro não disponível para preview.")
            with col_thumb:
                if thumbnail_url:
                    st.image(thumbnail_url, caption="Thumbnail", use_container_width=True)
                else:
                    st.caption("Sem thumbnail")

            col_aprovar, col_descartar = st.columns(2)
            with col_aprovar:
                if st.button("Aprovar e Produzir", key=f"aprovar_{prod_id}", type="primary"):
                    if not sd:
                        st.error("script_data ausente — roteiro não pode ser produzido automaticamente.")
                    else:
                        try:
                            baserow.update_row(cfg.baserow_table_productions, prod_id, {"status": "em_producao"})
                            _launch_producao(prod_id, sd, title)
                            st.success(f"Produção #{prod_id} iniciada em background!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao iniciar produção: {e}")
            with col_descartar:
                if st.button("Descartar", key=f"descartar_{prod_id}"):
                    try:
                        baserow.update_row(cfg.baserow_table_productions, prod_id, {"status": "erro"})
                        st.warning(f"Produção #{prod_id} descartada.")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao descartar: {e}")


def _section_em_producao() -> None:
    st.header("Em Produção")
    productions = _list_productions("em_producao")

    if not productions:
        st.info("Nenhuma produção em andamento.")
        return

    auto_refresh = st.toggle("Auto-refresh (30s)", value=False, key="refresh_toggle")

    for prod in productions:
        prod_id = prod["id"]
        title = prod.get("title", f"Produção #{prod_id}")
        with st.container(border=True):
            st.subheader(f"{title}")
            st.caption(f"ID: {prod_id} | Status: em_producao")

    if auto_refresh:
        time.sleep(30)
        st.rerun()


def _section_concluidos() -> None:
    st.header("Concluídos")
    productions = _list_productions("pronto")

    if not productions:
        st.info("Nenhuma produção concluída.")
        return

    for prod in productions:
        prod_id = prod["id"]
        title = prod.get("title", f"Produção #{prod_id}")
        video_url = prod.get("video_final_url", "")
        thumbnail_url = prod.get("thumbnail_url", "")

        with st.container(border=True):
            col_info, col_thumb = st.columns([3, 1])
            with col_info:
                st.subheader(title)
                st.caption(f"ID: {prod_id}")
                if video_url:
                    st.markdown(f"[Ver vídeo final]({video_url})")
                else:
                    st.caption("Vídeo não disponível")
            with col_thumb:
                if thumbnail_url:
                    st.image(thumbnail_url, caption="Thumbnail", use_container_width=True)


def _section_style_guide() -> None:
    st.header("Visual Style Guide")
    st.markdown("### Paleta de Cores")
    cols = st.columns(3)
    colors = [
        ("#E07B39", "Laranja Primário"),
        ("#C45C26", "Laranja Escuro"),
        ("#A65E2E", "Terracota"),
    ]
    for col, (color, name) in zip(cols, colors):
        col.color_picker(name, color, disabled=True)
    st.markdown("### Identidade Visual")
    st.markdown("- **Fonte Logo:** Georgia (serif)")
    st.markdown("- **Avatar:** Cirlene Niza — talking photo HeyGen")
    st.markdown("- **Proporção vídeo:** 9:16 (portrait)")
    st.markdown("- **Duração alvo:** 2–3 minutos")


def main():
    st.title("Canal Cirlene Niza")
    st.markdown("**Painel de Aprovação e Acompanhamento**")

    menu = st.sidebar.selectbox(
        "Navegação",
        ["Pendentes", "Em Produção", "Concluídos", "Style Guide"],
    )

    if menu == "Pendentes":
        _section_pendentes()
    elif menu == "Em Produção":
        _section_em_producao()
    elif menu == "Concluídos":
        _section_concluidos()
    elif menu == "Style Guide":
        _section_style_guide()


if __name__ == "__main__":
    main()
