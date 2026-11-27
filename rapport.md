# Aide à la décision 2026–2027 — Projet : Algorithme du mariage stable

> **Document de travail de l'équipe.** Il explique comment lancer le code, comment chaque partie du sujet est réalisée et ce que montrent les tests, pour servir de base à la rédaction du rapport final. La partie 5 (représentations compactes) est rédigée par un autre membre de l'équipe : la section 9 n'en contient qu'un brouillon.

## Sommaire

1. Introduction et énoncé
2. Lancer le code
3. Organisation du code
4. Modélisation
5. Partie 1 — Génération des préférences aléatoires
6. Partie 2 — L'algorithme du mariage stable
7. Partie 3 — Mesure de la satisfaction
8. Partie 4 — Tests sur plusieurs jeux de données
9. Partie 5 — Extension aux représentations compactes (brouillon, à finaliser)
10. Aide à la rédaction du rapport
11. Conclusion et références

---

## 1. Introduction et énoncé

On cherche à affecter des **étudiants** à des **établissements** disposant d'un nombre limité de places. Chaque étudiant classe les établissements et chaque établissement classe les étudiants. On veut une affectation **stable** : il ne doit exister aucun couple (étudiant *e*, établissement *h*) qui ont tous deux intérêt à rompre l'affectation pour s'associer (*paire bloquante*).

L'algorithme d'acceptation différée de Gale et Shapley (1962) résout ce problème. Nous l'étudions dans sa version « *many-to-one* » (admissions universitaires, type Parcoursup) : un établissement *h* a une capacité *c_h* ≥ 1.

**L'énoncé demande :**

| # | Demande | Où c'est fait | Section |
|---|---|---|---|
| 1 | Générer des préférences aléatoires des étudiants et des établissements | `mariage_stable.py` : `generer_instance()` | 5 |
| 2 | Implanter l'algorithme du mariage stable | `mariage_stable.py` : `gale_shapley()`, `paires_bloquantes()` | 6 |
| 3 | Mesurer la satisfaction des étudiants et des établissements, intégrée à l'implantation | `mariage_stable.py` : `satisfaction_*()` | 7 |
| 4 | Tester le programme sur plusieurs jeux de données | `experiences.py`, `resultats.csv` | 8 |
| 5 | Proposer une extension vers les représentations compactes (sans implantation) | — (rédaction) | 9 |

En plus, `interface.py` fournit une interface graphique (Streamlit) pour faire la démonstration.

---

## 2. Lancer le code

### 2.1 Prérequis

- **Python ≥ 3.8** (testé avec Python 3.12).
- `mariage_stable.py` et `experiences.py` n'utilisent **que la bibliothèque standard** : rien à installer.
- `interface.py` a besoin de `streamlit` (≥ 1.37) et `pandas`, listés dans `requirements.txt`.

### 2.2 Sans installation : bibliothèque et tests

Dans le dossier du projet :

```bash
python3 mariage_stable.py     # petit exemple : 10 étudiants, 3 établissements, les 2 versions
python3 experiences.py        # les 3 scénarios, 30 instances chacun -> resultats.csv
python3 experiences.py 5      # même chose avec 5 instances (plus rapide)
```

- `mariage_stable.py` affiche les préférences, les admis de chaque établissement, la stabilité, le nombre de propositions et les satisfactions, pour les deux versions de l'algorithme.
- `experiences.py` affiche un tableau (une ligne par scénario et par côté proposant) et **réécrit `resultats.csv`**. Les résultats sont reproductibles : les graines aléatoires sont fixées (0, 1, …, R−1).

### 2.3 Interface graphique

Une seule fois, créer un environnement virtuel et installer les dépendances (il faut une connexion Internet) :

```bash
python3 -m venv ~/.venvs/mariage
~/.venvs/mariage/bin/pip install -r requirements.txt
```

Puis, à chaque fois :

```bash
~/.venvs/mariage/bin/streamlit run interface.py
```

et ouvrir **http://localhost:8501** dans le navigateur. `Ctrl+C` dans le terminal arrête l'interface.
Variante : `source ~/.venvs/mariage/bin/activate`, puis simplement `streamlit run interface.py`.

**Problèmes fréquents**

| Message | Cause | Solution |
|---|---|---|
| `Échec temporaire dans la résolution du nom` pendant `pip install` | Pas d'Internet | Se reconnecter et relancer `pip install` |
| `…/bin/streamlit: Aucun fichier ou dossier de ce nom` | L'installation a échoué ou n'a pas été faite | Relancer `pip install -r requirements.txt` dans le venv |
| `La commande « run » n'a pas été trouvée` | On a tapé `run interface.py` | La commande est `streamlit run interface.py` |
| `externally-managed-environment` | `pip install` hors venv sur Ubuntu | Utiliser le venv (2.3) |

### 2.4 Ce que montre l'interface

Barre latérale : nombre d'étudiants et d'établissements, préférences uniformes ou corrélées (et le niveau de corrélation), capacités (automatiques, ratio places/étudiants ou personnalisées), longueur des listes, graine.

| Onglet | Contenu | Usage en démo |
|---|---|---|
| **Une instance** | Stabilité, nombre de propositions, satisfactions (étudiants, établissements, globale), % non affectés, remplissage ; admis de chaque établissement ; préférences ; paires bloquantes éventuelles | Montrer un résultat et sa stabilité |
| **Pas à pas** | Déroulement tour par tour : propositions, rejets, admis provisoires | Expliquer l'algorithme sur une petite instance (≤ 20 étudiants) |
| **Comparer les deux côtés** | Tous les indicateurs pour les deux versions, % d'étudiants affectés différemment, histogramme des rangs obtenus | Montrer l'avantage du côté proposant |
| **Les scénarios** | Lance la campagne de `experiences.py` (R réglable), tableau, téléchargement du CSV, graphique par scénario | Montrer les résultats des tests |

---

## 3. Organisation du code

| Fichier | Rôle |
|---|---|
| `mariage_stable.py` | Bibliothèque : données, génération, algorithme, stabilité, satisfaction |
| `experiences.py` | Campagne de tests : 3 scénarios × R instances × 2 versions → `resultats.csv` |
| `interface.py` | Interface Streamlit (4 onglets), utilise les deux fichiers précédents |
| `resultats.csv` | Résultats de `python3 experiences.py` (30 instances par scénario) |
| `requirements.txt` | Dépendances de l'interface |

**Fonctions principales de `mariage_stable.py`**

| Fonction / classe | Rôle |
|---|---|
| `Instance` | Une instance : `pref_etu`, `pref_etab`, `capacites`, `description` |
| `repartir_places(total, n_etab)` | Répartit `total` places le plus également possible |
| `generer_instance(...)` | **Partie 1** : génère une instance aléatoire |
| `Resultat` | Sortie de l'algorithme : `affectation_etu`, `admis`, `nb_propositions`, `proposant`, `tours` |
| `_rangs(prefs, n)` | Table des rangs `rang[a][b]` (accès en O(1)) |
| `gale_shapley(inst, proposant, historique)` | **Partie 2** : l'algorithme, côté étudiants ou établissements |
| `paires_bloquantes(inst, res)` | Vérifie la stabilité (liste vide = stable) |
| `satisfaction_etudiants`, `satisfaction_etablissements`, `satisfaction_globale` | **Partie 3** : mesures de satisfaction |
| `gini(valeurs)` | Indice de Gini |
| `afficher(inst, res)` | Affichage console d'un résultat |

---

## 4. Modélisation

- *E* = {0, …, n−1} les étudiants ; *H* = {0, …, m−1} les établissements. Dans l'affichage : E0, E1, … et H0, H1, …
- `pref_etu[e]` : liste ordonnée (meilleur d'abord) des établissements acceptables pour *e*.
- `pref_etab[h]` : liste ordonnée des étudiants acceptables pour *h*.
- `capacites[h]` : nombre de places de *h*.

Une **affectation** associe à chaque étudiant au plus un établissement, sans dépasser les capacités. Elle est **stable** s'il n'existe pas de paire (*e*, *h*) telle que :
- *e* préfère *h* à son affectation (ou *e* n'est pas affecté), **et**
- *h* a une place libre **ou** préfère *e* à l'un de ses admis.

Une telle paire est dite **bloquante** : *e* et *h* auraient tous deux intérêt à quitter l'affectation pour s'associer.

---

## 5. Partie 1 — Génération des préférences aléatoires

### 5.1 Ce qui est fait

La fonction `generer_instance(n_etu, n_etab, capacites=None, mode="uniforme", correlation=0.7, longueur_liste=None, graine=None)` renvoie une `Instance`. Elle propose deux modèles de préférences :

| Mode | Principe | Intérêt |
|---|---|---|
| `uniforme` | Chaque agent tire une permutation aléatoire uniforme de l'autre côté (`random.sample`). | Modèle de référence de la littérature, sans structure. |
| `correle` | Chaque établissement a un **prestige** commun et chaque étudiant une **note** commune, tirés uniformément dans [0, 1]. Chaque agent classe l'autre côté selon *score commun + bruit gaussien individuel*. | Plus réaliste : tout le monde veut les « bons » établissements et les « bons » étudiants. |

### 5.2 Comment fonctionne le mode corrélé

1. On tire un prestige `prestige[h]` pour chaque établissement et une note `note[e]` pour chaque étudiant.
2. Le paramètre `correlation` = *c* ∈ ]0, 1] fixe l'écart-type du bruit : **σ = (1 − c) / c**.
3. Chaque étudiant classe les établissements par ordre décroissant de `prestige[h] + N(0, σ)`, avec un bruit tiré pour lui seul. Les établissements font de même avec les notes (fonction `_classement_bruite`).

Interprétation : les scores communs sont étalés sur [0, 1].
- *c* = 0,95 → σ ≈ 0,05 : le bruit est très petit, presque tout le monde a **la même liste**.
- *c* = 0,7 → σ ≈ 0,43 : préférences ressemblantes mais variées.
- *c* → 0 → σ très grand : on retrouve des préférences quasi uniformes.

### 5.3 Options

- **Capacités** : par défaut `repartir_places(n_etu, n_etab)` donne autant de places que d'étudiants, réparties le plus également possible (par exemple 200 étudiants et 10 établissements → 20 places chacun). On peut passer une liste `capacites` pour créer une pénurie, un excédent ou des tailles inégales.
- **Listes incomplètes** (`longueur_liste = k`) : chaque étudiant ne garde que ses *k* premiers choix, comme sur une plateforme de vœux. Chaque établissement ne classe alors que les étudiants qui l'ont demandé.
- **Graine** (`graine`) : même graine → même instance. C'est ce qui rend les tests reproductibles.

---

## 6. Partie 2 — L'algorithme du mariage stable

### 6.1 Version étudiants proposants (la version « Parcoursup »)

```
tous les étudiants sont libres
tant qu'il existe un étudiant libre e qui n'a pas épuisé sa liste :
    h ← prochain établissement de la liste de e
    si h n'a pas classé e : refus, e reste libre
    sinon :
        h ajoute e à ses admis provisoires
        si |admis(h)| > c_h :
            h rejette son admis le moins bien classé, qui redevient libre
```

Les admissions sont **provisoires** (« acceptation différée ») : un établissement peut rejeter plus tard un étudiant s'il reçoit mieux. Un étudiant qui a épuisé sa liste reste non affecté.

### 6.2 Version établissements proposants

Chaque établissement qui a des places libres propose à ses étudiants préférés, pas encore sollicités. Un étudiant garde la meilleure proposition reçue. S'il quitte un établissement pour un meilleur, l'établissement quitté retrouve une place et reprend ses propositions.

### 6.3 Implantation (`gale_shapley`)

- **Tables de rangs** : `_rangs()` convertit chaque liste en tableau `rang[a][b]` = position de *b* dans la liste de *a* (`None` si non classé). Comparer deux candidats coûte alors O(1).
- **Côté étudiants** : une file (`deque`) contient les étudiants libres ; `prochain[e]` indique le prochain établissement à demander ; `admis[h]` est la liste des admis provisoires. Quand un établissement dépasse sa capacité, il rejette l'admis de plus grand rang.
- **Côté établissements** : une file contient les établissements ayant des places libres ; `affect[e]` est l'offre gardée par l'étudiant ; `nb_admis[h]` compte les places prises. Quand un étudiant change d'établissement, l'ancien est remis dans la file.
- **Résultat** (`Resultat`) : l'établissement de chaque étudiant (`None` si non affecté), les admis de chaque établissement (triés du mieux au moins bien classé), le nombre de propositions et le côté proposant.
- **Historique** : avec `historique=True`, chaque tour est enregistré (propositions, rejets, admis à la fin du tour). C'est ce qu'affiche l'onglet « Pas à pas ». Cela ne change pas le résultat.
- **Vérification** : `paires_bloquantes(inst, res)` parcourt, pour chaque étudiant, les établissements qu'il préfère à son affectation, et teste s'ils ont une place libre ou un admis moins bien classé que lui. Liste vide ⇔ affectation stable.

### 6.4 Exemple déroulé (4 étudiants, 2 établissements de 2 places)

| Agent | Préférences |
|---|---|
| E0 | H0 > H1 |
| E1 | H0 > H1 |
| E2 | H1 > H0 |
| E3 | H0 > H1 |
| H0 (2 places) | E2 > E1 > E0 > E3 |
| H1 (2 places) | E0 > E3 > E1 > E2 |

**Étudiants proposants** (5 propositions) :
- Tour 1 : E0, E1 et E3 demandent H0 ; E2 demande H1. H0 garde ses 2 préférés parmi les 3, E1 et E0, et refuse E3.
- Tour 2 : E3 demande son 2e choix H1, qui l'accepte (place libre).
- Résultat : H0 ← {E1, E0}, H1 ← {E3, E2}. Stable. Trois étudiants sur quatre ont leur 1er choix.

**Établissements proposants** (4 propositions) :
- Tour 1 : H0 propose à E2 et E1, H1 propose à E0 et E3. Chacun accepte, car c'est sa seule offre.
- Résultat : H0 ← {E2, E1}, H1 ← {E0, E3}. Stable aussi, mais seul E1 a son 1er choix, alors que les établissements ont leurs préférés.

| | S_etu | S_etab | S_globale |
|---|---|---|---|
| Étudiants proposants | 0,75 | 0,42 | 0,58 |
| Établissements proposants | 0,25 | 0,83 | 0,54 |

Les **deux affectations sont stables** mais différentes : chaque version favorise le côté qui propose. C'est exactement ce que montrent ensuite les tests à grande échelle.

### 6.5 Propriétés (résultats théoriques à citer)

- **Terminaison et complexité** : chaque agent propose au plus une fois à chaque membre de l'autre côté. Il y a donc au plus *n × m* propositions, et l'algorithme est en O(*n·m*), à un facteur *c_h* près pour la recherche du pire admis.
- **Stabilité** : le résultat est toujours stable. `paires_bloquantes()` l'a vérifié sur **100 % des 180 exécutions** des tests (section 8).
- **Optimalité** : la version étudiants proposants donne à chaque étudiant le meilleur établissement possible parmi toutes les affectations stables, et le pire pour les établissements. La version établissements proposants fait l'inverse.
- **Non-manipulabilité** (non testée ici) : côté étudiants proposants, un étudiant n'a jamais intérêt à mentir sur ses préférences. C'est pourquoi les plateformes réelles utilisent cette version.

---

## 7. Partie 3 — Mesure de la satisfaction

### 7.1 Score individuel

La satisfaction d'un agent dépend du **rang** de ce qu'il obtient dans sa liste. Les listes peuvent avoir des longueurs différentes, on normalise donc dans [0, 1] :

$$ s(r) = 1 - \frac{r}{L-1} $$

où *r* est le rang obtenu (0 = premier choix) et *L* la longueur de la liste. On a s = 1 pour le premier choix et s = 0 pour le dernier choix ou en l'absence d'affectation. Si *L* = 1, s = 1.

- **Étudiant *e*** : s_e = s(rang de son établissement dans sa liste). Un étudiant non affecté obtient 0.
- **Établissement *h*** : moyenne sur ses *c_h* **places** :
  $$ s_h = \frac{1}{c_h}\sum_{x \in \text{admis}(h)} s(\text{rang}_h(x)) $$
  Une place vide compte 0.

*Exemple* (section 6.4, étudiants proposants) : H0 a 4 étudiants classés (*L* = 4) et admet E1 (rang 1) et E0 (rang 2). s_H0 = (1 − 1/3 + 1 − 2/3) / 2 = **0,5**.

**Pourquoi compter les places vides ?**

- **L'objectif d'un établissement** est de remplir ses places avec de bons étudiants. Une place vide est une perte réelle : enseignants, salles et budget prévus pour rien.
- **Sans cette règle, le score serait trompeur.** Un établissement de 40 places qui n'admet que son candidat préféré obtiendrait 1, un score parfait, avec une moyenne sur ses admis, alors que 39 places sont vides. Avec une moyenne sur ses places, il obtient 1/40.
- **Symétrie avec les étudiants** : un étudiant non affecté vaut 0, donc une place non pourvue vaut 0.

### 7.2 Indicateurs agrégés (pour chaque côté)

Les fonctions `satisfaction_etudiants()` et `satisfaction_etablissements()` renvoient un objet `Satisfaction` avec :

| Indicateur | Champ | Ce qu'il mesure |
|---|---|---|
| Moyenne *S* | `moyenne` | Efficacité (critère utilitariste) |
| Minimum | `minimum` | Situation du plus mal servi (critère égalitariste de Rawls) |
| Écart-type | `ecart_type` | Dispersion |
| Indice de Gini | `gini` | Inégalité : 0 = tout le monde a le même score, 1 = inégalité maximale |
| Rang moyen | `rang_moyen` | Étudiants : rang moyen obtenu (1 = 1er choix). Établissements : écart moyen à leurs *c_h* candidats idéaux |
| % 1er choix, % top 3 | `pct_premier`, `pct_top3` | Indicateurs lisibles pour un décideur |
| % non servis | `pct_non_servis` | Étudiants non affectés / établissements sans aucun admis |
| Taux de remplissage | `extra["taux_remplissage"]` | % de places occupées |
| % admis idéaux | `extra["pct_admis_ideaux"]` | Part des admis qui figurent parmi les *c_h* premiers choix de l'établissement |

Le taux de remplissage et le % d'admis idéaux permettent de distinguer, dans un mauvais score d'établissement, les « mauvais admis » des « places vides ».

L'**indice de Gini** est calculé sur les scores triés *v₁ ≤ … ≤ vₙ* : G = 2·Σ i·vᵢ / (n·Σ vᵢ) − (n+1)/n.

### 7.3 Satisfaction globale

`satisfaction_globale(s_etu, s_etab, alpha=0.5)` renvoie :
- **S = α·S_etu + (1 − α)·S_etab**. Avec α = 0,5 par défaut, les deux côtés pèsent autant ; le décideur peut changer α pour favoriser un côté.
- le **déséquilibre |S_etu − S_etab|**, qui montre si un côté est beaucoup mieux servi que l'autre.

---

## 8. Partie 4 — Tests sur plusieurs jeux de données

### 8.1 Protocole

`experiences.py` exécute, pour chaque scénario :
1. **R = 30 instances aléatoires**, avec les graines 0 à 29 (reproductible) ;
2. sur chaque instance, **les deux versions** de l'algorithme ;
3. pour chaque exécution : vérification de la stabilité, nombre de propositions, temps de calcul et tous les indicateurs de satisfaction ;
4. la **moyenne** sur les 30 instances, écrite dans `resultats.csv`.

Au total : 3 scénarios × 30 instances × 2 versions = **180 exécutions**.

Les trois scénarios ont tous **200 étudiants et 10 établissements**, pour être comparables. Chacun ne change qu'**un seul facteur** par rapport à la référence :

| Scénario | Préférences | Places | Facteur étudié |
|---|---|---|---|
| **S1 : référence** | uniformes | 200 (20 par établissement) | — |
| **S2 : préférences corrélées** | corrélées, *c* = 0,95 | 200 | Ressemblance des préférences |
| **S3 : pénurie** | uniformes | 100 (10 par établissement) | Nombre de places |

### 8.2 Résultats

*Props* = nombre de propositions, *Rang* = rang moyen obtenu par les étudiants (1 = premier choix), *%NA* = étudiants non affectés.

| Scénario | Proposant | Stable | Props | S_etu | Rang | %1er | %top3 | %NA | Gini | S_etab | %Rempl. | S_glob |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 : référence | étudiants | 100 % | 264 | 0,965 | 1,32 | 75,9 | 98,6 | 0 | 0,029 | 0,608 | 100 | 0,786 |
| | établ. | 100 % | 849 | 0,849 | 2,36 | 42,1 | 80,7 | 0 | 0,110 | 0,783 | 100 | 0,816 |
| S2 : corrélées (c = 0,95) | étudiants | 100 % | 993 | 0,559 | 4,96 | 15,8 | 36,5 | 0 | 0,321 | 0,518 | 100 | 0,538 |
| | établ. | 100 % | 1151 | 0,559 | 4,97 | 15,8 | 36,5 | 0 | 0,322 | 0,518 | 100 | 0,538 |
| S3 : pénurie (50 %) | étudiants | 100 % | 1497 | 0,279 | 4,97 | 6,8 | 18,8 | 50 | 0,662 | 0,969 | 100 | 0,624 |
| | établ. | 100 % | 132 | 0,279 | 4,97 | 6,8 | 18,8 | 50 | 0,662 | 0,969 | 100 | 0,624 |

*Chaque exécution prend moins de 10 ms.*

### 8.3 Explication des trois tests

**S1 — Référence : le côté qui propose est avantagé.**
- *Pourquoi ce test* : c'est le cas « normal » (autant de places que d'étudiants, goûts indépendants). Il sert de point de comparaison et permet de vérifier la propriété d'optimalité.
- *Ce qu'on attend* : d'après la théorie, chaque version donne la meilleure affectation stable pour le côté qui propose.
- *Ce qu'on observe* : quand les étudiants proposent, S_etu = 0,965 et 76 % ont leur 1er choix. Quand ce sont les établissements, S_etu tombe à 0,849 (42 % de 1er choix) et S_etab monte de 0,608 à 0,783. La satisfaction globale est proche (0,786 contre 0,816).
- *Message* : choisir le côté qui propose est un **choix d'équité** (qui est favorisé), plus que d'efficacité.

**S2 — Préférences très corrélées : les deux versions donnent le même résultat.**
- *Pourquoi ce test* : dans la réalité, tout le monde veut les mêmes établissements. On veut voir comment l'algorithme se comporte quand les préférences se ressemblent.
- *Ce qu'on attend* : si tout le monde a presque le même classement, il n'existe presque qu'**une seule affectation stable** : les meilleurs étudiants prennent les meilleurs établissements, et ainsi de suite.
- *Ce qu'on observe* : les deux versions donnent les mêmes valeurs (S_etu = 0,559 des deux côtés). La satisfaction baisse fortement par rapport à S1 (0,965 → 0,559) et les inégalités augmentent (Gini 0,03 → 0,32) : seuls 16 % des étudiants ont leur 1er choix.
- *Message* : quand les préférences sont corrélées, le choix du côté qui propose **n'a plus d'effet**, et c'est la concurrence pour les mêmes places qui fait baisser la satisfaction.

**S3 — Pénurie (50 % de places) : le côté rare est le mieux servi.**
- *Pourquoi ce test* : vérifier que l'algorithme gère un marché déséquilibré (moins de places que d'étudiants) et voir qui en profite.
- *Ce qu'on attend* : la moitié des étudiants restent sans place ; le résultat doit rester stable ; les établissements, qui ont le choix, remplissent leurs places avec de bons candidats.
- *Ce qu'on observe* : 50 % de non-affectés, 100 % de places remplies, S_etab = 0,969 contre S_etu = 0,279. Les deux versions donnent encore le même résultat : dans un marché déséquilibré, c'est le rapport de forces qui décide, pas le côté proposant (Ashlagi et al., 2017).
- *Coût* : les étudiants rejetés descendent toute leur liste, donc la version étudiants proposants fait beaucoup plus de propositions (1497 contre 132).

### 8.4 Conclusions des tests

1. **Correction** : les 180 affectations sont stables, ce qui valide l'implantation.
2. **Optimalité** : le côté qui propose est avantagé quand le marché est équilibré (S1).
3. **Corrélation** : plus les préférences se ressemblent, plus la satisfaction baisse et plus elle est inégale ; les deux versions coïncident (S2).
4. **Capacité** : le côté rare est le mieux servi ; en pénurie, les deux versions coïncident aussi (S3).
5. **Coût** : le nombre de propositions reste très inférieur à la borne *n·m* = 2000, mais dépend du côté qui doit « descendre » dans ses listes.

### 8.5 Refaire les tests

- `python3 experiences.py` (30 instances, ~1 seconde) régénère `resultats.csv`. Les valeurs sont identiques à celles du tableau, sauf les temps de calcul.
- Dans l'interface, onglet « Les scénarios », bouton « Lancer la campagne ».
- **Colonnes de `resultats.csv`** : `scenario`, `proposant`, `stable` (part d'exécutions stables, 1 = 100 %), `propositions`, `temps_ms`, `sat_etu`, `min_etu`, `gini_etu`, `rang_moy_etu`, `pct_1er`, `pct_top3`, `pct_non_affectes`, `sat_etab`, `min_etab`, `remplissage`, `pct_admis_ideaux`, `sat_globale`, `desequilibre`.

---

## 9. Partie 5 — Extension aux représentations compactes (brouillon, à faire)



### 9.1 Motivation

Dans la réalité, un étudiant ne choisit pas seulement un établissement mais une **combinaison** : (établissement, spécialité, ville, régime internat/externat…). Avec 4 attributs de 5 valeurs, on obtient déjà 625 alternatives, et un ordre total sur ces alternatives est impossible à demander. De même, un établissement ne classe pas des milliers de candidats à la main : il applique des critères (moyenne, filière du bac, motivation…). Il faut donc des **représentations compactes** des préférences. faut voir le cours semaine 5-10 sur moodle  (partie 3 )

### 9.2 Architecture proposée

```
  Élicitation compacte  ──►  Module d'inférence  ──►  Gale-Shapley (inchangé)  ──►  Satisfaction
  (CP-net, LP-tree,           (calcul du                (étudiants proposants)       (rang ou
   GAI / additif,             « prochain meilleur                                      degré de
   logique pondérée)          choix »)                                                 dominance)
```

L'algorithme n'a jamais besoin de la liste complète. Il demande seulement à chaque étudiant son **prochain meilleur choix** et à chaque établissement une **comparaison entre deux candidats**. Ces deux opérations sont les points d'interface avec la représentation compacte.

### 9.3 Côté étudiants

| Représentation | Exemple | Utilisation dans l'algorithme |
|---|---|---|
| **Préférences lexicographiques / LP-trees** | « D'abord la spécialité Info > Maths ; puis, si Info, la ville Alger > Oran ; sinon … » | Ordre total. Le *k*-ième meilleur choix se calcule en temps polynomial par parcours de l'arbre, sans énumérer toutes les alternatives. Comparaison en O(nb d'attributs). |
| **CP-nets** | « Je préfère Alger à Oran ; *si* Alger, je préfère l'externat, *sinon* l'internat » | L'alternative optimale se calcule en temps linéaire (*forward sweep*) si le réseau est acyclique. Le CP-net ne définit qu'un ordre **partiel** : on propose de générer une **extension linéaire** (tri topologique successif) pour alimenter l'algorithme. Les ex æquo ou incomparables peuvent être départagés par une règle fixée ou un tirage. |
| **Utilité additive / GAI** | u(x) = Σ u_i(x_i) ou une somme sur des sous-ensembles d'attributs liés | Ordre (pré)total. Le prochain meilleur choix s'obtient par recherche *best-first* ou par programmation dynamique sur l'arbre de jonction GAI. |
| **Logique pondérée / logique de pénalités** | Buts (« ville = Alger », poids 5 ; « internat », poids 2) | Le score d'une alternative est la somme des poids des buts satisfaits (ou violés). Ordre pré-total, à départager. |

### 9.4 Côté établissements

L'établissement exprime une **fonction de score** sur les attributs des candidats (note × 0,6 + filière × 0,3 + entretien × 0,1), ou un **LP-tree** (d'abord la filière, puis la note). La comparaison de deux candidats, seule opération utilisée par l'algorithme, devient un calcul direct. Les quotas (par exemple de boursiers) se traduisent par des capacités par catégorie.

### 9.5 Conséquences et points de vigilance

- **Stabilité** : si chaque représentation produit un ordre total strict (après départage), l'algorithme et ses garanties (stabilité, optimalité, non-manipulabilité) restent inchangés.
- **Ordres partiels / indifférences** : plusieurs notions de stabilité existent alors (faible, forte, super-stabilité). La stabilité faible existe toujours (par départage). La recherche d'une affectation stable *maximum* avec indifférences est NP-difficile : il faut choisir le départage avec soin.
- **Complexité** : les requêtes de dominance dans un CP-net général sont PSPACE-complètes. On se limite donc aux CP-nets acycliques ou arborescents et aux LP-trees, où les opérations utiles sont polynomiales.
- **Mesure de satisfaction adaptée** : le rang *r* devient la position dans l'extension linéaire. On peut aussi définir un score qualitatif, par exemple le nombre d'alternatives qui dominent strictement l'alternative obtenue, normalisé, ou la fraction des buts pondérés satisfaits.
- **Élicitation** : l'interface pose des questions simples (importance des attributs, préférences conditionnelles), ce qui réduit fortement la charge cognitive par rapport à un classement complet.

---

## 10. Aide à la rédaction du rapport

### 10.1 Plan conseillé pour le rapport final

1. **Introduction** : le problème, la stabilité, Gale-Shapley *many-to-one* (section 1, 4).
2. **Partie 1** : les deux modes de génération, le rôle de *c*, les options (section 5).
3. **Partie 2** : pseudo-code, les deux versions, l'exemple déroulé de la section 6.4, les propriétés (section 6).
4. **Partie 3** : la formule s(r), le choix des places vides à 0, les indicateurs, la satisfaction globale (section 7).
5. **Partie 4** : protocole, tableau, les 3 messages (section 8).
6. **Partie 5** : extension (section 9, à finaliser).
7. **Conclusion**.

### 10.2 Les messages clés à retenir

- Le résultat de Gale-Shapley est **toujours stable** (vérifié sur les 180 exécutions).
- **Celui qui propose est avantagé** : c'est un choix politique (équité), pas d'efficacité.
- Quand les **préférences se ressemblent** ou que le **marché est déséquilibré**, il n'y a presque qu'une affectation stable et les deux versions donnent le même résultat.
- La satisfaction d'un établissement compte ses **places vides** : sinon un établissement presque vide paraîtrait parfaitement satisfait.

### 10.3 Figures et tableaux utiles

- Le tableau de l'exemple 6.4 (4 étudiants, 2 établissements) avec les deux résultats.
- Une capture de l'onglet « Pas à pas » sur une petite instance.
- Le tableau de la section 8.2 (ou une version réduite : S_etu, S_etab, %1er, %NA).
- L'histogramme des rangs de l'onglet « Comparer les deux côtés » sur S1 (200 étudiants, 10 établissements, préférences uniformes).

### 10.4 Questions possibles du jury

| Question | Réponse courte |
|---|---|
| Pourquoi l'algorithme termine-t-il ? | Chaque agent propose au plus une fois à chaque membre de l'autre côté : au plus *n·m* propositions. |
| Comment savez-vous que le résultat est stable ? | `paires_bloquantes()` vérifie la définition sur chaque résultat : 0 paire bloquante sur 180 exécutions. |
| Pourquoi deux versions ? | Elles donnent les deux affectations stables extrêmes : la meilleure pour les étudiants et la meilleure pour les établissements. |
| Pourquoi une place vide compte 0 ? | Sinon un établissement qui n'admet que son préféré aurait un score parfait (section 7.1). |
| Pourquoi normaliser par *L* − 1 ? | Pour comparer des agents dont les listes n'ont pas la même longueur (listes incomplètes). |
| Que représente *c* ? | La ressemblance des préférences : σ = (1 − c)/c, *c* = 1 → tout le monde a la même liste. |
| Les résultats sont-ils reproductibles ? | Oui : graines fixées 0 à R−1 ; `python3 experiences.py` redonne les mêmes valeurs. |

### 10.5 Limites à mentionner

- Préférences **strictes** (pas d'ex æquo), tirées selon deux modèles simples.
- La satisfaction est **ordinale** (basée sur le rang) : elle ne mesure pas l'intensité des préférences.
- Les capacités et les préférences sont **connues et sincères** (pas de stratégie des agents).
- 3 scénarios seulement, choisis pour illustrer le fonctionnement de l'algorithme.

---

## 11. Conclusion et références

Nous avons implanté un générateur de préférences configurable (uniforme ou corrélé), l'algorithme de Gale-Shapley *many-to-one* dans ses deux variantes avec vérification de stabilité, et une batterie de mesures de satisfaction : moyenne, minimum, Gini, rangs et taux de remplissage. Les tests sur 3 jeux de données confirment la stabilité des résultats et l'avantage du côté proposant dans un marché équilibré. Ils montrent aussi que cet avantage disparaît quand les préférences sont corrélées ou que les places manquent. L'extension aux représentations compactes (partie 5) permettrait d'utiliser le système sur des alternatives multi-attributs sans modifier l'algorithme.

### Références

- D. Gale, L. S. Shapley, *College Admissions and the Stability of Marriage*, American Mathematical Monthly, 1962.
- A. E. Roth, M. Sotomayor, *Two-Sided Matching*, Cambridge University Press, 1990.
- I. Ashlagi, Y. Kanoria, J. D. Leshno, *Unbalanced Random Matching Markets*, Journal of Political Economy, 2017.
- C. Boutilier et al., *CP-nets: A Tool for Representing and Reasoning with Conditional Ceteris Paribus Preference Statements*, JAIR, 2004.
- R. Booth et al., *Learning Conditionally Lexicographic Preference Relations*, ECAI, 2010.
