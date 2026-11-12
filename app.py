import streamlit as st
import pandas as pd
from blockchain_core import Blockchain

st.set_page_config(page_title="Registre Blockchain", layout="wide")
st.title("Registre blockchain du projet")

bc = Blockchain.load_from_file("blockchain.json")

st.subheader("Vérification de l'intégrité")
if st.button("Vérifier la chaîne"):
    if bc.is_valid():
        st.success("Chaîne valide : aucune modification détectée.")
    else:
        st.error("Chaîne INVALIDE : des données ont été modifiées.")

st.subheader(f"Blocs enregistrés : {len(bc.chain)}")
lignes = [
    {
        "Index": b.index,
        "Date": b.timestamp,
        "Données": str(b.data),
        "Hash précédent": b.previous_hash[:16] + "...",
        "Hash": b.hash[:16] + "...",
    }
    for b in bc.chain
]
st.dataframe(pd.DataFrame(lignes), use_container_width=True)
