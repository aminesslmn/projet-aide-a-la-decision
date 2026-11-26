"""
Tests du programme sur plusieurs jeux de données.

Pour chaque scénario on génère R instances aléatoires (graines différentes),
on lance Gale-Shapley côté étudiants ET côté établissements, on vérifie la
stabilité et on agrège les mesures de satisfaction.
Résultats : affichage console + fichier resultats.csv
"""

import csv
import sys
import time
from statistics import mean

from mariage_stable import (generer_instance, gale_shapley, paires_bloquantes,
                            satisfaction_etudiants, satisfaction_etablissements,
                            satisfaction_globale)

R = 30  # répétitions par scénario

# (nom, paramètres de generer_instance)
SCENARIOS = [
    ("S1 référence (uniforme)",   dict(n_etu=200, n_etab=10, mode="uniforme")),
    ("S2 corrélé c=0.95",         dict(n_etu=200, n_etab=10, mode="correle", correlation=0.95)),
    ("S3 pénurie (50% places)",   dict(n_etu=200, n_etab=10, mode="uniforme", capacites=[10] * 10)),
]

COLONNES = ["scenario", "proposant", "stable", "propositions", "temps_ms",
            "sat_etu", "min_etu", "gini_etu", "rang_moy_etu", "pct_1er", "pct_top3",
            "pct_non_affectes", "sat_etab", "min_etab", "remplissage", "pct_admis_ideaux",
            "sat_globale", "desequilibre"]


def lancer(r=None):
    """Exécute tous les scénarios avec r instances chacun (par défaut : R)."""
    r = r or R
    lignes = []
    for nom, params in SCENARIOS:
        for proposant in ("etudiants", "etablissements"):
            acc = {c: [] for c in COLONNES[2:]}
            for graine in range(r):
                inst = generer_instance(graine=graine, **params)
                t0 = time.perf_counter()
                res = gale_shapley(inst, proposant)
                dt = (time.perf_counter() - t0) * 1000
                se = satisfaction_etudiants(inst, res)
                sh = satisfaction_etablissements(inst, res)
                g = satisfaction_globale(se, sh)
                acc["stable"].append(1.0 if not paires_bloquantes(inst, res) else 0.0)
                acc["propositions"].append(res.nb_propositions)
                acc["temps_ms"].append(dt)
                acc["sat_etu"].append(se.moyenne)
                acc["min_etu"].append(se.minimum)
                acc["gini_etu"].append(se.gini)
                acc["rang_moy_etu"].append(se.rang_moyen)
                acc["pct_1er"].append(se.pct_premier)
                acc["pct_top3"].append(se.pct_top3)
                acc["pct_non_affectes"].append(se.pct_non_servis)
                acc["sat_etab"].append(sh.moyenne)
                acc["min_etab"].append(sh.minimum)
                acc["remplissage"].append(sh.extra["taux_remplissage"])
                acc["pct_admis_ideaux"].append(sh.extra["pct_admis_ideaux"])
                acc["sat_globale"].append(g["globale"])
                acc["desequilibre"].append(g["desequilibre"])
            ligne = {"scenario": nom, "proposant": proposant}
            ligne.update({k: mean(v) for k, v in acc.items()})
            lignes.append(ligne)
    return lignes


def afficher(lignes):
    entete = (f"{'Scénario':<34}{'Prop.':<7}{'Stab':>5}{'Props':>8}{'ms':>7}"
              f"{'S_etu':>7}{'Rang':>6}{'%1er':>6}{'%top3':>6}{'%NA':>6}{'Gini':>6}"
              f"{'S_etab':>7}{'%Rempl':>7}{'S_glob':>7}")
    print(entete)
    print("-" * len(entete))
    for l in lignes:
        print(f"{l['scenario']:<34}{l['proposant'][:5]:<7}{l['stable']*100:>4.0f}%"
              f"{l['propositions']:>8.0f}{l['temps_ms']:>7.1f}"
              f"{l['sat_etu']:>7.3f}{l['rang_moy_etu']:>6.2f}{l['pct_1er']:>6.1f}"
              f"{l['pct_top3']:>6.1f}{l['pct_non_affectes']:>6.1f}{l['gini_etu']:>6.3f}"
              f"{l['sat_etab']:>7.3f}{l['remplissage']:>7.1f}{l['sat_globale']:>7.3f}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        R = int(sys.argv[1])
    lignes = lancer()
    afficher(lignes)
    with open("resultats.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES)
        w.writeheader()
        for l in lignes:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in l.items()})
    print(f"\n{R} instances par scénario. Résultats écrits dans resultats.csv")
