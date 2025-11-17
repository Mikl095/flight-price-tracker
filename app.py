import streamlit as st
import os
import random
from datetime import date, datetime

# ---- Utils ----
from utils.storage import ensure_data_file, load_routes, save_routes
from utils.plotting import plot_price_history

# ---- Email ----
from email_utils import send_email


# =========================================================
# Initialisation
# =========================================================
ensure_data_file()
routes = load_routes()

st.set_page_config(page_title="Flight Price Tracker", layout="wide")
st.title("✈️ Flight Price Tracker – Paris → Destinations personnalisables")


# =========================================================
# ----- SIDEBAR : SECTION EMAIL + TEST EMAIL -----
# =========================================================
st.sidebar.subheader("📧 Configuration Email (SendGrid)")

with st.sidebar.expander("Tester l'envoi d'email", expanded=False):
    test_email = st.text_input("Adresse email de test", key="test_email")

    if st.button("Envoyer email de test", key="btn_test_email"):
        if not test_email:
            st.warning("Veuillez entrer une adresse email.")
        else:
            ok = send_email(
                to=test_email,
                subject="Test SendGrid – Flight Tracker",
                html="""
                    <h2>Test réussi 🎉</h2>
                    <p>Votre configuration SendGrid fonctionne.</p>
                """
            )

            if ok:
                st.success("Email envoyé !")
            else:
                st.error("Erreur lors de l’envoi. Vérifiez la clé SENDGRID.")


# =========================================================
# ----- SIDEBAR : AJOUTER UN NOUVEAU VOL -----
# =========================================================
st.sidebar.header("➕ Ajouter un vol à surveiller")

origin = st.sidebar.text_input("Origine", "PAR")

dest_options = ["TYO", "OSA", "SPK", "PTP
