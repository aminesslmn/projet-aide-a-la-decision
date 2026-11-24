"""
Interface graphique du projet « mariage stable ».

Lancement :   py -m streamlit run interface.py
(prérequis :  py -m pip install -r requirements.txt)

Trois onglets :
  1. Une instance            : générer une instance, lancer l'algorithme, voir le résultat.
  2. Comparer les deux côtés : étudiants proposants vs établissements proposants.
  3. Les 22 scénarios        : campagne de tests de experiences.py, tableaux et graphiques.
"""

from collections import Counter

import pandas as pd
import streamlit as st

import experiences
from mariage_stable import (generer_instance, gale_shapley, paires_bloquantes,
                            satisfaction_etudiants, satisfaction_etablissements,
                            satisfaction_globale)

st.set_page_config(page_title="Mariage stable", layout="wide")
st.title("Mariage stable : affectation étudiants → établissements")

E = lambda e: f"E{e}"
H = lambda h: f"H{h}"
PROPOSANTS = {"Étudiants proposants": "etudiants", "Établissements proposants": "etablissements"}


# ---------------------------------------------------------------------------
# Calculs (mis en cache pour ne pas tout recalculer à chaque clic)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def calculer_instance(n_etu, n_etab, capacites, mode, correlation, k, graine, selon_prestige):
    return generer_instance(n_etu, n_etab, capacites=list(capacites) if capacites else None,
                            mode=mode, correlation=correlation, longueur_liste=k or None,
                            graine=graine, capacites_selon_prestige=selon_prestige)


@st.cache_data(show_spinner=False)
def calculer_resultat(_inst, cle, proposant):
    """`cle` identifie l'instance (l'objet Instance lui-même n'est pas haché)."""
    res = gale_shapley(_inst, proposant)
    se = satisfaction_etudiants(_inst, res)
    sh = satisfaction_etablissements(_inst, res)
    return res, se, sh, satisfaction_globale(se, sh), paires_bloquantes(_inst, res)


@st.cache_data(show_spinner=False)
def calculer_campagne(r):
    return experiences.lancer(r)


# ---------------------------------------------------------------------------
# Barre latérale : paramètres de l'instance
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Instance")
    n_etu = st.slider("Nombre d'étudiants", 2, 1000, 200, step=1)
    n_etab = st.slider("Nombre d'établissements", 1, 200, 10)

    mode = st.radio("Préférences", ["uniforme", "correle"], horizontal=True,
                    format_func=lambda m: "Uniformes" if m == "uniforme" else "Corrélées")
    correlation = 0.7
    if mode == "correle":
        correlation = st.slider("Corrélation", 0.05, 1.0, 0.7, 0.05,
                                help="Proche de 1 : tout le monde a les mêmes préférences.")

    st.subheader("Capacités")
    type_cap = st.radio("Places", ["automatique", "ratio", "personnalisées"],
                        format_func={"automatique": "Automatique (places = étudiants)",
                                     "ratio": "Ratio places / étudiants",
                                     "personnalisées": "Personnalisées"}.get)
    capacites = None
    if type_cap == "ratio":
        ratio = st.slider("Places en % des étudiants", 25, 200, 100, 5)
        total = round(ratio / 100 * n_etu)
        base, reste = divmod(total, n_etab)
        capacites = [base + (1 if h < reste else 0) for h in range(n_etab)]
    elif type_cap == "personnalisées":
        texte = st.text_input(f"{n_etab} capacités séparées par des virgules",
                              ",".join(["20"] * n_etab))
        try:
            capacites = [int(x) for x in texte.replace(" ", "").split(",") if x != ""]
        except ValueError:
            st.error("Les capacités doivent être des nombres entiers.")
            st.stop()
        if len(capacites) != n_etab or any(c < 0 for c in capacites):
            st.error(f"Il faut exactement {n_etab} capacités positives "
                     f"(reçu : {len(capacites)}).")
            st.stop()

    selon_prestige = None
    if mode == "correle":
        choix = st.selectbox("Capacités selon le prestige",
                             ["aucun", "direct", "inverse"],
                             format_func={"aucun": "Ordre donné",
                                          "direct": "Établissements populaires = grands",
                                          "inverse": "Établissements populaires = petits"}.get)
        selon_prestige = None if choix == "aucun" else choix

    k = st.slider("Longueur des listes des étudiants (0 = complète)", 0, n_etab, 0)
    graine = st.number_input("Graine aléatoire", 0, 100_000, 42)

cle = (n_etu, n_etab, tuple(capacites) if capacites else None, mode, correlation, k,
       int(graine), selon_prestige)
inst = calculer_instance(*cle)
st.sidebar.caption(inst.description)


def tableau_preferences(inst, limite=50):
    lignes_e = [{"Étudiant": E(e), "Classement": " > ".join(H(h) for h in p[:15])
                 + (" …" if len(p) > 15 else "")} for e, p in enumerate(inst.pref_etu[:limite])]
    lignes_h = [{"Établissement": H(h), "Capacité": inst.capacites[h],
                 "Classement": " > ".join(E(e) for e in p[:15]) + (" …" if len(p) > 15 else "")}
                for h, p in enumerate(inst.pref_etab[:limite])]
    return pd.DataFrame(lignes_e), pd.DataFrame(lignes_h)


onglet1, onglet2, onglet3 = st.tabs(["Une instance", "Comparer les deux côtés", "Les 22 scénarios"])

# ---------------------------------------------------------------------------
# Onglet 1 : une instance
# ---------------------------------------------------------------------------

with onglet1:
    choix = st.radio("Qui propose ?", list(PROPOSANTS), horizontal=True)
    res, se, sh, g, bloquantes = calculer_resultat(inst, cle, PROPOSANTS[choix])

    c = st.columns(7)
    c[0].metric("Stable", "Oui ✔" if not bloquantes else "Non ✘",
                f"{len(bloquantes)} paire(s) bloquante(s)", delta_color="off")
    c[1].metric("Propositions", res.nb_propositions)
    c[2].metric("Satisfaction étudiants", f"{se.moyenne:.3f}")
    c[3].metric("Satisfaction établ.", f"{sh.moyenne:.3f}")
    c[4].metric("Satisfaction globale", f"{g['globale']:.3f}")
    c[5].metric("Non affectés", f"{se.pct_non_servis:.1f} %")
    c[6].metric("Remplissage", f"{sh.extra['taux_remplissage']:.1f} %")

    st.caption(f"Rang moyen des étudiants : {se.rang_moyen:.2f} (1 = premier choix) · "
               f"{se.pct_premier:.1f} % ont leur 1er choix · {se.pct_top3:.1f} % un choix du top 3 · "
               f"Gini {se.gini:.3f} · satisfaction minimale {se.minimum:.3f}")

    st.subheader("Résultat par établissement")
    st.dataframe(pd.DataFrame([{
        "Établissement": H(h),
        "Capacité": inst.capacites[h],
        "Admis": len(L),
        "Places vides": inst.capacites[h] - len(L),
        "Satisfaction": round(sh.scores[h], 3),
        "Étudiants admis (du mieux au moins bien classé)":
            ", ".join(E(e) for e in L[:30]) + (" …" if len(L) > 30 else ""),
    } for h, L in enumerate(res.admis)]), hide_index=True, width="stretch")

    non_aff = [E(e) for e, h in enumerate(res.affectation_etu) if h is None]
    if non_aff:
        st.warning(f"{len(non_aff)} étudiant(s) sans affectation : "
                   + ", ".join(non_aff[:60]) + (" …" if len(non_aff) > 60 else ""))
    else:
        st.success("Tous les étudiants ont une place.")

    with st.expander("Préférences (50 premiers de chaque côté)"):
        df_e, df_h = tableau_preferences(inst)
        a, b = st.columns(2)
        a.dataframe(df_e, hide_index=True, width="stretch")
        b.dataframe(df_h, hide_index=True, width="stretch")

    if bloquantes:
        with st.expander("Paires bloquantes"):
            st.write(", ".join(f"({E(e)}, {H(h)})" for e, h in bloquantes))

# ---------------------------------------------------------------------------
# Onglet 2 : comparaison des deux côtés
# ---------------------------------------------------------------------------

with onglet2:
    resultats = {nom: calculer_resultat(inst, cle, p) for nom, p in PROPOSANTS.items()}

    def indicateurs(r):
        res, se, sh, g, bl = r
        return {
            "Stable": "oui" if not bl else f"non ({len(bl)})",
            "Propositions": res.nb_propositions,
            "Étudiants : satisfaction moyenne": round(se.moyenne, 3),
            "Étudiants : satisfaction minimale": round(se.minimum, 3),
            "Étudiants : Gini": round(se.gini, 3),
            "Étudiants : rang moyen": round(se.rang_moyen, 2),
            "Étudiants : % 1er choix": round(se.pct_premier, 1),
            "Étudiants : % top 3": round(se.pct_top3, 1),
            "Étudiants : % non affectés": round(se.pct_non_servis, 1),
            "Établissements : satisfaction moyenne": round(sh.moyenne, 3),
            "Établissements : satisfaction minimale": round(sh.minimum, 3),
            "Établissements : % remplissage": round(sh.extra["taux_remplissage"], 1),
            "Établissements : % admis idéaux": round(sh.extra["pct_admis_ideaux"], 1),
            "Satisfaction globale": round(g["globale"], 3),
            "Déséquilibre |S_etu − S_etab|": round(g["desequilibre"], 3),
        }

    st.dataframe(pd.DataFrame({nom: indicateurs(r) for nom, r in resultats.items()}).astype(str),
                 width="stretch")

    a_etu = resultats["Étudiants proposants"][0].affectation_etu
    a_etab = resultats["Établissements proposants"][0].affectation_etu
    differents = sum(x != y for x, y in zip(a_etu, a_etab))
    st.metric("Étudiants affectés différemment selon le côté proposant",
              f"{100 * differents / inst.n_etu:.1f} %",
              help="Proche de 0 % : il n'y a presque qu'une affectation stable, "
                   "le choix du côté proposant ne change rien.")

    st.subheader("Rang obtenu par les étudiants (1 = premier choix)")
    histos = {}
    for nom, (res, *_rest) in resultats.items():
        histos[nom] = Counter(inst.pref_etu[e].index(h) + 1
                              for e, h in enumerate(res.affectation_etu) if h is not None)
    st.bar_chart(pd.DataFrame(histos).fillna(0).sort_index(), stack=False)
    st.caption("Les étudiants non affectés ne figurent pas dans l'histogramme.")

# ---------------------------------------------------------------------------
# Onglet 3 : campagne des 22 scénarios
# ---------------------------------------------------------------------------

RATIO_PLACES = {"S11": 25, "S7": 50, "S12": 75, "S13": 95, "S2": 100,
                "S14": 105, "S15": 125, "S8": 150, "S16": 200}


def code(nom):
    """'S7 pénurie (50% places)' -> 'S07' (pour un tri correct dans les graphiques)."""
    return f"S{int(nom.split()[0][1:]):02d}"


with onglet3:
    st.write(f"Exécute les {len(experiences.SCENARIOS)} scénarios de `experiences.py`, "
             "avec les deux versions de l'algorithme, et fait la moyenne sur R instances.")
    with st.expander("Liste des scénarios"):
        st.dataframe(pd.DataFrame([{"Scénario": nom, "Paramètres": str(p)}
                                   for nom, p in experiences.SCENARIOS]),
                     hide_index=True, width="stretch")

    r = st.slider("R : instances par scénario", 1, 30, 10)
    if st.button("Lancer la campagne", type="primary"):
        with st.spinner(f"Calcul de {len(experiences.SCENARIOS) * 2 * r} exécutions…"):
            st.session_state["campagne"] = (r, calculer_campagne(r))

    if "campagne" in st.session_state:
        r_fait, lignes = st.session_state["campagne"]
        df = pd.DataFrame(lignes)[experiences.COLONNES]
        st.subheader(f"Résultats (moyennes sur {r_fait} instances)")
        affiche = df.copy()
        affiche["stable"] = (affiche["stable"] * 100).round(0).astype(int).astype(str) + " %"
        st.dataframe(affiche.round(3), hide_index=True, width="stretch")

        st.download_button("Télécharger resultats.csv",
                           df.round(4).to_csv(index=False).encode("utf-8"),
                           "resultats.csv", "text/csv")

        st.subheader("Satisfaction selon le nombre de places (étudiants proposants)")
        etu = df[df["proposant"] == "etudiants"].copy()
        etu["code"] = etu["scenario"].str.split().str[0]
        courbe = etu[etu["code"].isin(RATIO_PLACES)].copy()
        courbe["% de places"] = courbe["code"].map(RATIO_PLACES)
        courbe = (courbe.set_index("% de places").sort_index()
                  [["sat_etu", "sat_etab", "sat_globale"]]
                  .rename(columns={"sat_etu": "Étudiants", "sat_etab": "Établissements",
                                   "sat_globale": "Globale"}))
        st.line_chart(courbe)
        st.caption("Scénarios S11, S7, S12, S13, S2, S14, S15, S8, S16 "
                   "(200 étudiants, 10 établissements, préférences uniformes).")

        st.subheader("Satisfaction des étudiants par scénario")
        barres = df.assign(code=df["scenario"].map(code)).pivot(
            index="code", columns="proposant", values="sat_etu").rename(
            columns={"etudiants": "Étudiants proposants",
                     "etablissements": "Établissements proposants"})
        st.bar_chart(barres, stack=False)
