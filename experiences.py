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
                            satisfaction_globale, chercher_mensonges, tronquer_listes)

R = 30  # répétitions par scénario

# (nom, paramètres de generer_instance)
SCENARIOS = [
    ("S1 petit uniforme",         dict(n_etu=20,   n_etab=4,  mode="uniforme")),
    ("S2 moyen uniforme",         dict(n_etu=200,  n_etab=10, mode="uniforme")),
    ("S3 grand uniforme",         dict(n_etu=1000, n_etab=20, mode="uniforme")),
    ("S4 corrélé c=0.3",          dict(n_etu=200,  n_etab=10, mode="correle", correlation=0.3)),
    ("S5 corrélé c=0.7",          dict(n_etu=200,  n_etab=10, mode="correle", correlation=0.7)),
    ("S6 corrélé c=0.95",         dict(n_etu=200,  n_etab=10, mode="correle", correlation=0.95)),
    ("S7 pénurie (50% places)",   dict(n_etu=200,  n_etab=10, mode="uniforme", capacites=[10] * 10)),
    ("S8 excédent (150% places)", dict(n_etu=200,  n_etab=10, mode="uniforme", capacites=[30] * 10)),
    ("S9 listes courtes (k=3)",   dict(n_etu=200,  n_etab=10, mode="uniforme", longueur_liste=3)),
    ("S10 1-1 classique n=100",   dict(n_etu=100,  n_etab=100, mode="uniforme")),
    # --- A. Nombre total de places (rapport places / étudiants) ---
    ("S11 pénurie sévère (25%)",       dict(n_etu=200, n_etab=10, mode="uniforme", capacites=[5] * 10)),
    ("S12 pénurie modérée (75%)",      dict(n_etu=200, n_etab=10, mode="uniforme", capacites=[15] * 10)),
    ("S13 légère pénurie (95%)",       dict(n_etu=200, n_etab=10, mode="uniforme", capacites=[19] * 10)),
    ("S14 léger excédent (105%)",      dict(n_etu=200, n_etab=10, mode="uniforme", capacites=[21] * 10)),
    ("S15 excédent modéré (125%)",     dict(n_etu=200, n_etab=10, mode="uniforme", capacites=[25] * 10)),
    ("S16 fort excédent (200%)",       dict(n_etu=200, n_etab=10, mode="uniforme", capacites=[40] * 10)),
    # --- B. Répartition inégale des places (total = 200) ---
    ("S17 1 grand + 9 petits",         dict(n_etu=200, n_etab=10, mode="uniforme", capacites=[110] + [10] * 9)),
    ("S18 2 grands + 8 petits",        dict(n_etu=200, n_etab=10, mode="uniforme", capacites=[60, 60] + [10] * 8)),
    ("S19 200 étab. à 1 place",        dict(n_etu=200, n_etab=200, mode="uniforme")),
    # --- C. Capacité et popularité (préférences corrélées c=0.7) ---
    ("S20 populaires = petits",        dict(n_etu=200, n_etab=10, mode="correle", correlation=0.7,
                                            capacites=[40, 35, 30, 25, 20, 15, 15, 10, 5, 5],
                                            capacites_selon_prestige="inverse")),
    ("S21 populaires = grands",        dict(n_etu=200, n_etab=10, mode="correle", correlation=0.7,
                                            capacites=[40, 35, 30, 25, 20, 15, 15, 10, 5, 5],
                                            capacites_selon_prestige="direct")),
    ("S22 pénurie + corrélé (50%)",    dict(n_etu=200, n_etab=10, mode="correle", correlation=0.7,
                                            capacites=[10] * 10)),
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


# ---------------------------------------------------------------------------
# Manipulation : python experiences.py --manipulation [R]
# ---------------------------------------------------------------------------

# A. Un seul étudiant ment : peut-il gagner ?
MANIP_INDIVIDUEL = [
    ("1-1 n=30 uniforme",          dict(n_etu=30, n_etab=30, mode="uniforme")),
    ("1-1 n=30 corrélé c=0.7",     dict(n_etu=30, n_etab=30, mode="correle", correlation=0.7)),
    ("60 étu./6 étab. uniforme",   dict(n_etu=60, n_etab=6, mode="uniforme")),
    ("60 étu./6 étab. corrélé 0.7", dict(n_etu=60, n_etab=6, mode="correle", correlation=0.7)),
]
TYPES_MENSONGE = ["troncature", "en_tete", "echange"]
COLONNES_INDIV = (["cas", "proposant", "pct_gagnants"]
                  + [f"pct_{t}" for t in TYPES_MENSONGE]
                  + ["gain_moyen_rangs", "pct_instable_vrai"])

# B. Beaucoup d'étudiants déclarent une liste courte (vraies listes complètes)
MANIP_COLLECTIF_BASE = dict(n_etu=200, n_etab=10, mode="uniforme")
FRACTIONS = [0.0, 0.25, 0.5, 1.0]
LONGUEURS = [1, 3]
COLONNES_COLL = ["k", "pct_menteurs", "proposant", "bloquantes_declarees", "bloquantes_vraies",
                 "pct_instable_vrai", "pct_non_affectes", "sat_etu", "sat_menteurs",
                 "sat_honnetes", "sat_etab", "remplissage"]


def experience_manipulation(r=10):
    """Renvoie (lignes A, lignes B). Toutes les mesures utilisent les VRAIES préférences."""
    lignes_a = []
    for nom, params in MANIP_INDIVIDUEL:
        for proposant in ("etudiants", "etablissements"):
            gagnants, par_type, gains, instables, total = 0, {t: 0 for t in TYPES_MENSONGE}, [], 0, 0
            for graine in range(r):
                inst = generer_instance(graine=graine, **params)
                total += inst.n_etu
                for m in chercher_mensonges(inst, proposant):
                    gagnants += 1
                    for t in m.types_gagnants:
                        par_type[t] += 1
                    r_h = m.rang_honnete if m.rang_honnete is not None else len(inst.pref_etu[m.etudiant])
                    gains.append(r_h - m.rang_mensonge)
                    instables += not m.stable_vrai
            ligne = {"cas": nom, "proposant": proposant,
                     "pct_gagnants": 100 * gagnants / total,
                     "gain_moyen_rangs": mean(gains) if gains else 0.0,
                     "pct_instable_vrai": 100 * instables / gagnants if gagnants else 0.0}
            ligne.update({f"pct_{t}": 100 * par_type[t] / total for t in TYPES_MENSONGE})
            lignes_a.append(ligne)

    lignes_b = []
    for k in LONGUEURS:
        for frac in FRACTIONS:
            for proposant in ("etudiants", "etablissements"):
                acc = {c: [] for c in COLONNES_COLL[3:]}
                for graine in range(r):
                    vrai = generer_instance(graine=graine, **MANIP_COLLECTIF_BASE)
                    declare, menteurs = tronquer_listes(vrai, frac, k, graine)
                    res = gale_shapley(declare, proposant)
                    bp_vrai = len(paires_bloquantes(vrai, res))
                    se = satisfaction_etudiants(vrai, res)
                    sh = satisfaction_etablissements(vrai, res)
                    honnetes = sorted(set(range(vrai.n_etu)) - set(menteurs))
                    acc["bloquantes_declarees"].append(len(paires_bloquantes(declare, res)))
                    acc["bloquantes_vraies"].append(bp_vrai)
                    acc["pct_instable_vrai"].append(100.0 if bp_vrai else 0.0)
                    acc["pct_non_affectes"].append(se.pct_non_servis)
                    acc["sat_etu"].append(se.moyenne)
                    if menteurs:
                        acc["sat_menteurs"].append(mean(se.scores[e] for e in menteurs))
                    if honnetes:
                        acc["sat_honnetes"].append(mean(se.scores[e] for e in honnetes))
                    acc["sat_etab"].append(sh.moyenne)
                    acc["remplissage"].append(sh.extra["taux_remplissage"])
                ligne = {"k": k, "pct_menteurs": int(100 * frac), "proposant": proposant}
                ligne.update({c: (mean(v) if v else float("nan")) for c, v in acc.items()})
                lignes_b.append(ligne)
    return lignes_a, lignes_b


def _ecrire_csv(nom, colonnes, lignes):
    with open(nom, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colonnes)
        w.writeheader()
        for l in lignes:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in l.items()})


def afficher_manipulation(lignes_a, lignes_b):
    print("A. Un étudiant ment seul (mensonges simples, mesuré avec ses vraies préférences)")
    print(f"{'Cas':<30}{'Prop.':<7}{'%gagne':>8}{'%tronq':>8}{'%tête':>8}{'%échg':>8}"
          f"{'gain':>7}{'%inst.':>8}")
    for l in lignes_a:
        print(f"{l['cas']:<30}{l['proposant'][:5]:<7}{l['pct_gagnants']:>8.1f}"
              f"{l['pct_troncature']:>8.1f}{l['pct_en_tete']:>8.1f}{l['pct_echange']:>8.1f}"
              f"{l['gain_moyen_rangs']:>7.2f}{l['pct_instable_vrai']:>8.1f}")
    print("\nB. Une part des étudiants déclare seulement k choix (200 étu., 10 étab., uniforme)")
    print(f"{'k':>2}{'%ment':>7} {'Prop.':<7}{'BP décl':>8}{'BP vrai':>8}{'%inst':>7}{'%NA':>6}"
          f"{'S_etu':>7}{'S_ment':>7}{'S_honn':>7}{'S_etab':>7}{'%Rempl':>7}")
    for l in lignes_b:
        f = lambda x: "   -  " if x != x else f"{x:>7.3f}"
        print(f"{l['k']:>2}{l['pct_menteurs']:>6}% {l['proposant'][:5]:<7}"
              f"{l['bloquantes_declarees']:>8.1f}{l['bloquantes_vraies']:>8.1f}"
              f"{l['pct_instable_vrai']:>7.0f}{l['pct_non_affectes']:>6.1f}{l['sat_etu']:>7.3f}"
              f"{f(l['sat_menteurs'])}{f(l['sat_honnetes'])}{l['sat_etab']:>7.3f}{l['remplissage']:>7.1f}")


if __name__ == "__main__" and "--manipulation" in sys.argv:
    args = [a for a in sys.argv[1:] if a != "--manipulation"]
    r_manip = int(args[0]) if args else 10
    a, b = experience_manipulation(r_manip)
    afficher_manipulation(a, b)
    _ecrire_csv("resultats_manipulation_individuel.csv", COLONNES_INDIV, a)
    _ecrire_csv("resultats_manipulation_collectif.csv", COLONNES_COLL, b)
    print(f"\n{r_manip} instances par cas. Résultats écrits dans "
          "resultats_manipulation_individuel.csv et resultats_manipulation_collectif.csv")
    sys.exit(0)


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
