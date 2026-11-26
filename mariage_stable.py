"""
Projet Aide à la décision 2026-2027 : Algorithme du mariage stable
==================================================================

Affectation étudiants -> établissements (problème "many-to-one",
variante de Gale-Shapley avec capacités, dite "College Admissions").

Contenu :
  1. Génération de préférences aléatoires (uniformes ou corrélées).
  2. Algorithme du mariage stable (acceptation différée), côté
     étudiants proposants OU côté établissements proposants.
  3. Mesures de satisfaction (étudiants, établissements, globale).
  + Vérification de la stabilité du résultat.
  + Historique tour par tour (gale_shapley(..., historique=True)).

Uniquement la bibliothèque standard Python (>= 3.8).
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from statistics import mean, pstdev
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# 1. Génération des préférences
# ---------------------------------------------------------------------------

@dataclass
class Instance:
    """Une instance du problème."""
    pref_etu: List[List[int]]        # pref_etu[e] = établissements classés (meilleur d'abord)
    pref_etab: List[List[int]]       # pref_etab[h] = étudiants classés (meilleur d'abord)
    capacites: List[int]             # capacites[h] = nombre de places
    description: str = ""

    @property
    def n_etu(self) -> int:
        return len(self.pref_etu)

    @property
    def n_etab(self) -> int:
        return len(self.pref_etab)


def _classement_bruite(scores: List[float], bruit: float, rng: random.Random,
                       candidats: List[int]) -> List[int]:
    """Trie les candidats par score commun + bruit gaussien individuel (décroissant)."""
    return sorted(candidats, key=lambda c: scores[c] + rng.gauss(0, bruit), reverse=True)


def repartir_places(total: int, n_etab: int) -> List[int]:
    """Répartit `total` places le plus équitablement possible entre n_etab établissements."""
    base, reste = divmod(total, n_etab)
    return [base + (1 if h < reste else 0) for h in range(n_etab)]


def generer_instance(n_etu: int, n_etab: int, capacites: Optional[List[int]] = None,
                     mode: str = "uniforme", correlation: float = 0.7,
                     longueur_liste: Optional[int] = None,
                     graine: Optional[int] = None,
                     capacites_selon_prestige: Optional[str] = None) -> Instance:
    """Génère des préférences aléatoires.

    mode = "uniforme" : chaque agent classe l'autre côté selon une permutation
                        aléatoire uniforme (aucune corrélation).
    mode = "correle"  : chaque établissement a un « prestige » et chaque étudiant
                        une « note » communs ; chaque agent perçoit ces scores avec
                        un bruit individuel. correlation ∈ [0,1] : 1 = tout le monde
                        a les mêmes préférences, 0 = uniforme.
    longueur_liste    : si fourni, chaque étudiant ne classe que ses k premiers
                        établissements (listes incomplètes, comme dans Parcoursup).
    capacites         : par défaut, places réparties pour couvrir tous les étudiants.
    capacites_selon_prestige (mode "correle") : "direct" donne les plus grandes
                        capacités aux établissements les plus prestigieux,
                        "inverse" les plus petites ; None garde l'ordre fourni.
    """
    rng = random.Random(graine)
    if capacites is None:
        capacites = repartir_places(n_etu, n_etab)
    assert len(capacites) == n_etab

    etus, etabs = list(range(n_etu)), list(range(n_etab))

    if mode == "uniforme":
        pref_etu = [rng.sample(etabs, n_etab) for _ in etus]
        pref_etab = [rng.sample(etus, n_etu) for _ in etabs]
    elif mode == "correle":
        # bruit tel que correlation=1 -> bruit nul, correlation=0 -> bruit énorme
        bruit = (1 - correlation) / max(correlation, 1e-6)
        prestige = [rng.random() for _ in etabs]
        note = [rng.random() for _ in etus]
        pref_etu = [_classement_bruite(prestige, bruit, rng, etabs) for _ in etus]
        pref_etab = [_classement_bruite(note, bruit, rng, etus) for _ in etabs]
        if capacites_selon_prestige is not None:
            # "direct" : les établissements les plus prestigieux ont le plus de places
            # "inverse" : les plus prestigieux ont le moins de places
            par_prestige = sorted(etabs, key=lambda h: prestige[h], reverse=True)
            caps = sorted(capacites, reverse=(capacites_selon_prestige == "direct"))
            capacites = [0] * n_etab
            for h, c in zip(par_prestige, caps):
                capacites[h] = c
    else:
        raise ValueError(f"mode inconnu : {mode}")

    if longueur_liste is not None:
        pref_etu = [p[:longueur_liste] for p in pref_etu]
        # un établissement ne classe que les étudiants qui l'ont demandé
        demandeurs = [set() for _ in etabs]
        for e, p in enumerate(pref_etu):
            for h in p:
                demandeurs[h].add(e)
        pref_etab = [[e for e in pref_etab[h] if e in demandeurs[h]] for h in etabs]

    desc = (f"{mode}{'' if mode == 'uniforme' else f'(c={correlation})'}, "
            f"{n_etu} étu., {n_etab} étab., {sum(capacites)} places"
            + (f", listes de {longueur_liste}" if longueur_liste else ""))
    return Instance(pref_etu, pref_etab, capacites, desc)


# ---------------------------------------------------------------------------
# 2. Algorithme du mariage stable (acceptation différée)
# ---------------------------------------------------------------------------

@dataclass
class Resultat:
    affectation_etu: List[Optional[int]]     # établissement de chaque étudiant (None = non affecté)
    admis: List[List[int]]                   # étudiants admis par établissement
    nb_propositions: int
    proposant: str
    # Historique tour par tour (rempli seulement si historique=True). Chaque tour :
    #   {"tour": k, "propositions": [(e, h, acceptee)], "rejets": [(e, h)],
    #    "admis": admis de chaque établissement à la fin du tour}
    # Côté établissements proposants, un « rejet » (e, h) = e quitte h pour mieux.
    tours: List[dict] = field(default_factory=list)


def _rangs(prefs: List[List[int]], n_autres: int) -> List[List[Optional[int]]]:
    """rang[a][b] = position de b dans la liste de a (None si non classé). Accès O(1)."""
    r = [[None] * n_autres for _ in prefs]
    for a, p in enumerate(prefs):
        for i, b in enumerate(p):
            r[a][b] = i
    return r


def gale_shapley(inst: Instance, proposant: str = "etudiants",
                 historique: bool = False) -> Resultat:
    """Algorithme de Gale-Shapley many-to-one.

    proposant = "etudiants"      : optimal pour les étudiants (version Parcoursup/APB).
    proposant = "etablissements" : optimal pour les établissements.
    historique = True            : enregistre le déroulement tour par tour (Resultat.tours).
    Complexité : O(n_etu * n_etab) propositions au maximum.

    La file contient des couples (agent, tour) : un agent rejeté au tour k repasse
    au tour k+1. Cela ne change ni l'ordre de traitement ni le résultat ; le numéro
    de tour ne sert qu'à l'affichage pas à pas.
    """
    rang_etu = _rangs(inst.pref_etu, inst.n_etab)
    rang_etab = _rangs(inst.pref_etab, inst.n_etu)
    nb_prop = 0
    tours: List[dict] = []
    courant = {"tour": 1, "propositions": [], "rejets": []}

    def fermer_tour(admis_actuels):
        """Clôt le tour courant (s'il s'est passé quelque chose) avec une photo des admis."""
        if historique and (courant["propositions"] or courant["rejets"]):
            photo = [sorted(L, key=lambda x: rang_etab[h][x]) for h, L in enumerate(admis_actuels)]
            tours.append({**courant, "admis": photo})

    if proposant == "etudiants":
        prochain = [0] * inst.n_etu                 # indice du prochain établissement à demander
        admis: List[List[int]] = [[] for _ in range(inst.n_etab)]
        libres = deque((e, 1) for e in range(inst.n_etu))
        while libres:
            e, t = libres.popleft()
            if historique and t != courant["tour"]:
                fermer_tour(admis)
                courant = {"tour": t, "propositions": [], "rejets": []}
            if prochain[e] >= len(inst.pref_etu[e]):
                continue                            # liste épuisée : reste non affecté
            h = inst.pref_etu[e][prochain[e]]
            prochain[e] += 1
            nb_prop += 1
            if rang_etab[h][e] is None:             # h n'a pas classé e : refus
                if historique:
                    courant["propositions"].append((e, h, False))
                libres.append((e, t + 1))
                continue
            admis[h].append(e)
            pire = None
            if len(admis[h]) > inst.capacites[h]:   # trop de candidats : rejeter le pire
                pire = max(admis[h], key=lambda x: rang_etab[h][x])
                admis[h].remove(pire)
                libres.append((pire, t + 1))
            if historique:
                courant["propositions"].append((e, h, pire != e))
                if pire is not None and pire != e:
                    courant["rejets"].append((pire, h))
        fermer_tour(admis)
        affect: List[Optional[int]] = [None] * inst.n_etu
        for h, L in enumerate(admis):
            for e in L:
                affect[e] = h

    elif proposant == "etablissements":
        prochain = [0] * inst.n_etab
        affect = [None] * inst.n_etu
        nb_admis = [0] * inst.n_etab
        actifs = deque((h, 1) for h in range(inst.n_etab) if inst.capacites[h] > 0)

        def admis_actuels():
            A = [[] for _ in range(inst.n_etab)]
            for e_, h_ in enumerate(affect):
                if h_ is not None:
                    A[h_].append(e_)
            return A

        while actifs:
            h, t = actifs.popleft()
            if historique and t != courant["tour"]:
                fermer_tour(admis_actuels())
                courant = {"tour": t, "propositions": [], "rejets": []}
            # h propose à ses étudiants préférés tant qu'il a des places libres
            while nb_admis[h] < inst.capacites[h] and prochain[h] < len(inst.pref_etab[h]):
                e = inst.pref_etab[h][prochain[h]]
                prochain[h] += 1
                nb_prop += 1
                accepte = False
                if rang_etu[e][h] is not None:
                    actuel = affect[e]
                    if actuel is None:
                        affect[e] = h
                        nb_admis[h] += 1
                        accepte = True
                    elif rang_etu[e][h] < rang_etu[e][actuel]:
                        affect[e] = h
                        nb_admis[h] += 1
                        nb_admis[actuel] -= 1
                        actifs.append((actuel, t + 1))  # l'ancien établissement a une place libre
                        accepte = True
                        if historique:
                            courant["rejets"].append((e, actuel))
                if historique:
                    courant["propositions"].append((e, h, accepte))
        admis = admis_actuels()
        fermer_tour(admis)
    else:
        raise ValueError("proposant doit être 'etudiants' ou 'etablissements'")

    for L, h in zip(admis, range(inst.n_etab)):
        L.sort(key=lambda x: rang_etab[h][x])
    return Resultat(affect, admis, nb_prop, proposant, tours)


def paires_bloquantes(inst: Instance, res: Resultat) -> List[tuple]:
    """Renvoie les paires (e, h) bloquantes. Liste vide <=> affectation stable."""
    rang_etu = _rangs(inst.pref_etu, inst.n_etab)
    rang_etab = _rangs(inst.pref_etab, inst.n_etu)
    bloquantes = []
    for e in range(inst.n_etu):
        h_e = res.affectation_etu[e]
        for h in inst.pref_etu[e]:
            if h == h_e:
                break                               # établissements suivants moins bien classés
            if rang_etab[h][e] is None:
                continue
            if len(res.admis[h]) < inst.capacites[h]:
                bloquantes.append((e, h))           # place libre et e préfère h
            elif any(rang_etab[h][e] < rang_etab[h][x] for x in res.admis[h]):
                bloquantes.append((e, h))           # h préfère e à un de ses admis
    return bloquantes


# ---------------------------------------------------------------------------
# 3. Mesures de satisfaction
# ---------------------------------------------------------------------------
#
# Score individuel normalisé dans [0, 1] à partir du RANG obtenu :
#     s(r) = 1 - r / (L - 1)       r = rang (0 = 1er choix), L = longueur de la liste
#     s = 0 si l'agent n'obtient rien (étudiant non affecté / place vide).
#
#  - Étudiant e  : s_e = s(rang de son établissement dans sa liste).
#  - Établissement h : moyenne des scores sur ses capacites[h] places,
#        s_h = (1/c_h) * Σ_{admis x} s(rang de x)  (une place vide compte 0),
#    ce qui pénalise à la fois les mauvais admis et les places non pourvues.
#
# Indicateurs agrégés pour chaque côté : moyenne, écart-type, minimum
# (pire agent = critère égalitariste de Rawls), rang moyen, % 1er choix,
# % dans le top 3, % non affectés, indice de Gini (équité).
# Satisfaction globale = moyenne pondérée α·S_etu + (1-α)·S_etab
# et écart |S_etu - S_etab| (mesure du déséquilibre entre les deux côtés).

def _score(r: Optional[int], L: int) -> float:
    if r is None:
        return 0.0
    return 1.0 if L <= 1 else 1 - r / (L - 1)


def gini(valeurs: List[float]) -> float:
    """Indice de Gini (0 = égalité parfaite, 1 = inégalité maximale)."""
    v = sorted(valeurs)
    n, s = len(v), sum(v)
    if n == 0 or s == 0:
        return 0.0
    cum = sum((i + 1) * x for i, x in enumerate(v))
    return (2 * cum) / (n * s) - (n + 1) / n


@dataclass
class Satisfaction:
    scores: List[float]
    moyenne: float
    ecart_type: float
    minimum: float
    rang_moyen: float              # rang moyen (1 = premier choix), sur les agents servis
    pct_premier: float
    pct_top3: float
    pct_non_servis: float
    gini: float
    extra: Dict[str, float] = field(default_factory=dict)


def _agreger(scores, rangs, non_servis) -> Satisfaction:
    servis = [r for r in rangs if r is not None]
    n = len(scores)
    return Satisfaction(
        scores=scores,
        moyenne=mean(scores),
        ecart_type=pstdev(scores),
        minimum=min(scores),
        rang_moyen=(mean(servis) + 1) if servis else float("nan"),
        pct_premier=100 * sum(r == 0 for r in servis) / n,
        pct_top3=100 * sum(r < 3 for r in servis) / n,
        pct_non_servis=100 * non_servis / n,
        gini=gini(scores),
    )


def satisfaction_etudiants(inst: Instance, res: Resultat) -> Satisfaction:
    scores, rangs = [], []
    for e, h in enumerate(res.affectation_etu):
        L = len(inst.pref_etu[e])
        r = inst.pref_etu[e].index(h) if h is not None else None
        rangs.append(r)
        scores.append(_score(r, L))
    return _agreger(scores, rangs, sum(h is None for h in res.affectation_etu))


def satisfaction_etablissements(inst: Instance, res: Resultat) -> Satisfaction:
    rang_etab = _rangs(inst.pref_etab, inst.n_etu)
    scores, rangs_moyens, places_vides = [], [], 0
    for h in range(inst.n_etab):
        L, c = len(inst.pref_etab[h]), inst.capacites[h]
        rs = [rang_etab[h][e] for e in res.admis[h]]
        places_vides += c - len(rs)
        scores.append(sum(_score(r, L) for r in rs) / c if c else 1.0)
        # rang "idéal" : un établissement servi parfaitement a les rangs 0..c-1
        # on mesure l'écart moyen à cet idéal
        rangs_moyens.append(mean(r - i for i, r in enumerate(sorted(rs))) if rs else None)
    s = _agreger(scores, rangs_moyens, sum(len(a) == 0 for a in res.admis))
    s.extra["taux_remplissage"] = 100 * (1 - places_vides / max(1, sum(inst.capacites)))
    s.extra["pct_admis_ideaux"] = 100 * mean(
        (sum(1 for e in res.admis[h] if rang_etab[h][e] < inst.capacites[h]) / inst.capacites[h])
        if inst.capacites[h] else 1.0 for h in range(inst.n_etab))
    return s


def satisfaction_globale(s_etu: Satisfaction, s_etab: Satisfaction, alpha: float = 0.5) -> Dict[str, float]:
    return {
        "globale": alpha * s_etu.moyenne + (1 - alpha) * s_etab.moyenne,
        "desequilibre": abs(s_etu.moyenne - s_etab.moyenne),
    }


# ---------------------------------------------------------------------------
# Démonstration rapide
# ---------------------------------------------------------------------------

def afficher(inst: Instance, res: Resultat, noms_etab: Optional[List[str]] = None) -> None:
    nom = (lambda h: noms_etab[h]) if noms_etab else (lambda h: f"H{h}")
    print(f"Instance : {inst.description} | proposant : {res.proposant}")
    for h, L in enumerate(res.admis):
        print(f"  {nom(h)} (cap {inst.capacites[h]}) <- {['E%d' % e for e in L]}")
    nonaff = [e for e, h in enumerate(res.affectation_etu) if h is None]
    if nonaff:
        print(f"  Non affectés : {['E%d' % e for e in nonaff]}")
    se, sh = satisfaction_etudiants(inst, res), satisfaction_etablissements(inst, res)
    g = satisfaction_globale(se, sh)
    print(f"  Stable : {not paires_bloquantes(inst, res)} | propositions : {res.nb_propositions}")
    print(f"  Satisfaction étudiants = {se.moyenne:.3f} (rang moyen {se.rang_moyen:.2f}, "
          f"{se.pct_premier:.0f}% 1er choix)")
    print(f"  Satisfaction établissements = {sh.moyenne:.3f} | globale = {g['globale']:.3f}")


if __name__ == "__main__":
    inst = generer_instance(10, 3, capacites=[3, 3, 4], mode="correle", graine=42)
    print("Préférences étudiants :", inst.pref_etu)
    print("Préférences établissements :", inst.pref_etab, "\n")
    for p in ("etudiants", "etablissements"):
        afficher(inst, gale_shapley(inst, p), ["Etab_A", "Etab_B", "Etab_C"])
        print()
