import streamlit as st
from cirleneniza.config import get_settings

st.set_page_config(page_title="Canal Cirlene Niza", page_icon="🍊")

settings = get_settings()


def main():
    st.title("🍊 Canal Cirlene Niza")
    st.markdown("### Plataforma de Aprovação")

    menu = st.sidebar.selectbox(
        "Navegação",
        ["Aprovação de Roteiro", "Visualização de Estilo", "Status"]
    )

    if menu == "Aprovação de Roteiro":
        st.header("Aprovação de Roteiro")
        st.info("Use /roteiro [tema] no Telegram para gerar um roteiro.")

        topic = st.text_input("Tema do vídeo", placeholder="Ex: 5 erros sobre proteína")

        if topic:
            st.markdown(f"**Tema:** {topic}")
            st.markdown("_Roteiro aparecerá aqui após geração via Telegram_")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Aprovar"):
                    st.success("Produção iniciada!")
            with col2:
                if st.button("↩️ Revisar"):
                    st.info("Feedback enviado ao Roteirista")

    elif menu == "Visualização de Estilo":
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

        st.markdown("### Logo CN Terracota")
        st.info("Logo será gerado pelo Diretor de Arte")

    elif menu == "Status":
        st.header("Status da Produção")
        st.info("Nenhuma produção em andamento")


if __name__ == "__main__":
    main()