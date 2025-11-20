import streamlit as st
from Cv_reader import read_cv, extract_text_from_docx, extract_text_from_pdf
import json

st.set_page_config(page_title="Synthétiseur de CV", layout="centered", page_icon="📝")

st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #18191a !important;
        color: #fff !important;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
    }
    .stMarkdown, .stTitle, .stSubheader, .stSuccess, .stInfo, .stWarning, .stJson {
        color: #fff !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📝 Synthétiseur de CV")
st.markdown(
    """
    Bienvenue sur l'outil d'analyse automatique de CV !  
    Téléverse ton CV au format PDF ou DOCX et obtiens une synthèse intelligente en un clic.
    """
)

st.divider()

uploaded_file = st.file_uploader("📤 Téléverse un fichier CV (.pdf, .docx)", type=["pdf", "docx"])

if uploaded_file is not None:
    st.success("Fichier bien importé 👍")
    st.info("Clique sur le bouton ci-dessous pour lancer l'analyse de ton CV.")

    if st.button("🔍 Analyser le CV"):
        with st.spinner("Analyse du CV en cours..."):
            resultats = read_cv(uploaded_file)

        st.subheader("🔍 Résultat de l'analyse")
        try:
            result_dict = json.loads(resultats)
            # Générer le tableau Markdown
            markdown_table = "| Clé | Valeur |\n|---|---|\n"
            for key, value in result_dict.items():
                markdown_table += f"| {key} | {value} |\n"
            st.markdown(markdown_table, unsafe_allow_html=True)
        except Exception:
            st.json(resultats)
else:
    st.warning("Aucun fichier importé. Veuillez téléverser un CV pour commencer l'analyse.")