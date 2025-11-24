import streamlit as st
from Cv_reader import read_cv, call_chatbot_api, ask_vision
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

uploaded_file = st.file_uploader("📤 Téléverse un fichier CV (.pdf, .docx)", type=["pdf", "docx","png", "jpg", "jpeg"])

if uploaded_file is not None:
    st.success("Fichier bien importé 👍")
    st.info("Clique sur le bouton ci-dessous pour lancer l'analyse.")
    st.info("Matching : votre CV va être comparé aux meilleures offres d'emploi disponibles. Cliquez sur « Analyser le CV » pour lancer le matching.")

    # Détection du type de fichier et prévisualisation si image
    name = uploaded_file.name.lower()
    is_image = any(name.endswith(ext) for ext in (".png", ".jpg", ".jpeg"))
    is_pdf = name.endswith(".pdf")
    is_docx = name.endswith(".docx")

    if is_image:
        try:
            st.image(uploaded_file, caption="Aperçu de l'image", use_column_width=True)
        except Exception:
            pass

    if st.button("🔍 Analyser le fichier"):
        with st.spinner("Analyse en cours..."):
            try:
                if is_pdf or is_docx:
                    resultats = read_cv(uploaded_file)
                    # afficher JSON formaté ou tableau markdown comme avant
                    try:
                        result_dict = json.loads(resultats)
                        markdown_table = "| Clé | Valeur |\n|---|---|\n"
                        for key, value in result_dict.items():
                            markdown_table += f"| {key} | {str(value).replace(chr(10), '<br>')} |\n"
                        st.subheader("🔍 Résultat de l'analyse CV")
                        st.markdown(markdown_table, unsafe_allow_html=True)
                    except Exception:
                        st.subheader("🔍 Résultat brut")
                        st.json(resultats)
                    st.subheader("🔍 Matching de votre CV avec les meilleures offres d'emploi ...")

                elif is_image:
                    vision_result = ask_vision(uploaded_file)
                    st.subheader("🔍 Résultat vision")
                    if isinstance(vision_result, (dict, list)):
                        with st.expander("Voir le JSON formaté"):
                            st.json(vision_result)
                        if isinstance(vision_result, dict):
                            md = "| Clé | Valeur |\n|---|---|\n"
                            for k, v in vision_result.items():
                                md += f"| {k} | {str(v).replace(chr(10), '<br>')} |\n"
                            st.markdown(md, unsafe_allow_html=True)
                    else:
                        try:
                            parsed = json.loads(vision_result)
                            st.json(parsed)
                        except Exception:
                            st.text(str(vision_result))
                else:
                    st.error("Type de fichier non supporté.")
            except Exception as e:
                st.error(f"Erreur lors de l'analyse : {e}")
else:
    st.warning("Aucun fichier importé. Veuillez téléverser un CV ou une image pour commencer l'analyse.")
st.divider()
st.subheader("💬 Assistant de recherches d'offres d'emplois")

# Initialiser l'historique du chat
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# Champ de saisie utilisateur
user_input = st.text_input("Pose moi une question :", key="chat_input")

if st.button("Envoyer", key="send_btn"):
    if user_input.strip():
        # Ajouter le message utilisateur à l'historique
        st.session_state["chat_history"].append(("user", user_input))

        # Appeler ton agent chatbot
        bot_response = call_chatbot_api(user_input)

        # Ajouter réponse bot à l'historique
        st.session_state["chat_history"].append(("bot", bot_response))

# Affichage du chat
for role, message in st.session_state["chat_history"]:
    if role == "user":
        st.markdown(f"**👤 Toi :** {message}")
    else:
        st.markdown(f"**🤖 Assistant :** {message}")
