from pathlib import Path
import pandas as pd
import streamlit as st
from blockchain_core import Blockchain

RACINE = Path(__file__).parent
RESULTATS = RACINE / "results"

st.set_page_config(page_title="SAP Intelligent Investment", layout="wide")
st.title("SAP Intelligent Investment")
st.caption("Simulation d'investissement : Deep Learning (LSTM), agents autonomes et blockchain. "
           "Aucune opération réelle : tout l'argent est virtuel.")


@st.cache_data
def charger_csv(nom, **kwargs):
    return pd.read_csv(RESULTATS / nom, **kwargs)


pred = charger_csv("predictions.csv")
valeurs = charger_csv("valeurs_test.csv", parse_dates=["date"]).set_index("date")
comp = charger_csv("comparaison_test.csv", index_col=0)

bc = Blockchain.load_from_file(str(RACINE / "blockchain.json"))
registre = pd.DataFrame([{"bloc": b.index, **b.data, "hash": b.hash} for b in bc.chain[1:]])
if "motif_risque" not in registre.columns:
    st.warning("Le registre blockchain chargé est une ancienne version de test. "
               "Remplacez blockchain.json par le registre de la simulation.")
    st.stop()

onglets = st.tabs(["Vue d'ensemble", "Prévisions", "Décisions et transactions",
                   "Blockchain", "Méthode et limites"])

# ---------------------------------------------------------------- Vue d'ensemble
with onglets[0]:
    st.subheader("Performance du portefeuille virtuel (période de test)")
    col_sys = [c for c in comp.columns if c.startswith("Système")][0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Valeur finale", f"{comp.loc['Valeur finale ($)', col_sys]:,.2f} $")
    c2.metric("Profit net", f"{comp.loc['Profit net ($)', col_sys]:,.2f} $")
    c3.metric("Ratio de Sharpe", f"{comp.loc['Sharpe (annualisé)', col_sys]:.2f}")
    c4.metric("Max Drawdown", f"{comp.loc['Max Drawdown (%)', col_sys]:.2f} %")

    st.line_chart(valeurs[["Buy and Hold", "SMA 10/20", "Système d'agents"]])
    st.caption("Capital initial : 10 000 $ virtuels. Coûts de transaction : 0,1 % par opération.")
    st.dataframe(comp)

    v1 = RESULTATS / "comparaison_test_v1.csv"
    if v1.exists():
        with st.expander("Version 1 du système (avant correction de l'agent de risque)"):
            st.dataframe(pd.read_csv(v1, index_col=0))

# ---------------------------------------------------------------- Prévisions
with onglets[1]:
    st.subheader("Prévisions du modèle LSTM")
    ens = st.selectbox("Ensemble de données", ["test", "val"])
    d = pred[pred["ensemble"] == ens].copy()
    d["date"] = pd.to_datetime(d["date"])

    err = d["rendement_predit"] - d["rendement_reel"]
    mae, rmse = err.abs().mean(), (err ** 2).mean() ** 0.5
    mae0, rmse0 = d["rendement_reel"].abs().mean(), (d["rendement_reel"] ** 2).mean() ** 0.5
    direction = (d["rendement_predit"] > 0).eq(d["rendement_reel"] > 0).mean()

    a, b, c, e = st.columns(4)
    a.metric("MAE (LSTM)", f"{mae:.5f}", f"référence 0 : {mae0:.5f}", delta_color="off")
    b.metric("RMSE (LSTM)", f"{rmse:.5f}", f"référence 0 : {rmse0:.5f}", delta_color="off")
    c.metric("Précision de direction", f"{100 * direction:.1f} %")
    e.metric("Jours de hausse réels", f"{100 * (d['rendement_reel'] > 0).mean():.1f} %")

    n = st.slider("Nombre de derniers jours affichés", 30, len(d), min(120, len(d)))
    graphe = d.set_index("date")[["prix_reel_t1", "prix_predit_t1"]].tail(n)
    graphe.columns = ["Prix réel (jour suivant)", "Prix prévu (jour suivant)"]
    st.line_chart(graphe)
    st.caption("La référence « rendement = 0 » suppose que le prix de demain égale celui d'aujourd'hui. "
               "Un modèle utile doit obtenir une erreur plus faible que cette référence.")

# ---------------------------------------------------------------- Décisions
with onglets[2]:
    st.subheader("Décisions des agents et transactions")
    actions = st.multiselect("Actions affichées", ["BUY", "SELL", "HOLD"], default=["BUY", "SELL"])
    colonnes = ["bloc", "date", "signal", "action", "motif_risque", "prevision", "quantite",
                "prix", "valeur_avant", "valeur_apres", "frais_cumules"]
    filtre = registre[registre["action"].isin(actions)][colonnes]
    k1, k2, k3 = st.columns(3)
    k1.metric("Décisions enregistrées", len(registre))
    k2.metric("Transactions exécutées", int((registre["action"] != "HOLD").sum()))
    k3.metric("Frais cumulés", f"{registre['frais_cumules'].iloc[-1]:,.2f} $")
    st.dataframe(filtre)
    st.markdown("**Interventions de l'agent de risque**")
    st.bar_chart(registre["motif_risque"].value_counts())

# ---------------------------------------------------------------- Blockchain
with onglets[3]:
    st.subheader("Registre blockchain")
    m1, m2 = st.columns(2)
    m1.metric("Nombre de blocs", len(bc.chain))
    m2.metric("Date du dernier bloc", str(bc.chain[-1].data.get("date", "")))
    if st.button("Vérifier l'intégrité de la chaîne"):
        if bc.is_valid():
            st.success("Chaîne valide : aucune modification détectée.")
        else:
            st.error("Chaîne INVALIDE : des données ont été modifiées.")
    st.write("Hash du bloc de genèse :")
    st.code(bc.chain[0].hash)
    st.write("Hash du dernier bloc :")
    st.code(bc.chain[-1].hash)

    i = st.number_input("Consulter un bloc (index)", min_value=0, max_value=len(bc.chain) - 1,
                        value=len(bc.chain) - 1, step=1)
    st.json(bc.chain[int(i)].to_dict())
    st.download_button("Télécharger blockchain.json",
                       data=(RACINE / "blockchain.json").read_bytes(),
                       file_name="blockchain.json")
    st.caption("La blockchain garantit la traçabilité et la détection des modifications. "
               "Elle ne garantit ni l'exactitude des prévisions ni la rentabilité de la stratégie.")

# ---------------------------------------------------------------- Méthode
with onglets[4]:
    st.subheader("Méthode, hypothèses et limites")
    st.markdown("""
**Données** : action SAP SE, cotations journalières. Période retenue : à partir du 04/01/1999
(les journées à prix identiques et à volume nul, toutes antérieures au 12/06/1998, sont exclues).

**Découpage chronologique** : entraînement 1999-2017, validation 2018-2021, test 2022-2026.
Le scaler est ajusté uniquement sur l'entraînement.

**Modèle** : LSTM (32 neurones) sur des séquences de 20 jours et 9 variables, qui prévoit le
rendement logarithmique du lendemain. Moyenne de 3 entraînements.

**Agents** : prévision, stratégie (seuil de 0,1 %), risque (exposition maximale 90 %, stop-loss 10 %,
limite de perte 20 % avec pause), exécution (opérations virtuelles et enregistrement dans la blockchain).

**Hypothèses de simulation** : capital initial 10 000 $, coûts de 0,1 % par opération, décisions
exécutées au cours de clôture, fractions d'action autorisées, Sharpe annualisé sur 252 jours sans taux sans risque.

**Limites** : une seule période de test ; le modèle n'apporte pas d'amélioration mesurable par rapport à la
référence « rendement = 0 » ; le système d'agents ne bat pas Buy and Hold sur cette période.
La perte maximale de 20 % est une limite de déclenchement, pas un plafond absolu du drawdown.
""")
