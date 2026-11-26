# Aide à la décision 2026–2027 — Projet : Algorithme du mariage stable

## 1. Introduction

On cherche à affecter des **étudiants** à des **établissements** disposant d'un nombre limité de places. Chaque étudiant classe les établissements et chaque établissement classe les étudiants. On veut une affectation **stable** : il ne doit exister aucun couple (étudiant *e*, établissement *h*) qui ont tous deux intérêt à rompre l'affectation pour s'associer (*paire bloquante*).

L'algorithme d'acceptation différée de Gale et Shapley (1962) résout ce problème. Nous l'étudions ici dans sa version « *many-to-one* » (admissions universitaires) : un établissement *h* a une capacité *c_h* ≥ 1.

Le travail comprend :

1. un générateur de préférences aléatoires ;
2. l'implantation de l'algorithme, côté étudiants et côté établissements ;
3. une méthode de mesure de la satisfaction, intégrée au programme ;
4. des tests sur 3 jeux de données choisis pour montrer le fonctionnement de l'algorithme (référence, préférences corrélées, pénurie de places) ;
5. une extension (sans implantation) vers les représentations compactes des préférences.

**Fichiers rendus :** `mariage_stable.py` (bibliothèque), `experiences.py` (campagne de tests), `resultats.csv` (résultats), `interface.py` (interface graphique). Python ≥ 3.8. La bibliothèque et les tests n'utilisent que la bibliothèque standard ; l'interface nécessite `streamlit` et `pandas` (`requirements.txt`).

```
python mariage_stable.py      # petit exemple commenté
python experiences.py [R]     # R instances par scénario (30 par défaut)

pip install -r requirements.txt
streamlit run interface.py    # interface graphique dans le navigateur
```

L'interface propose quatre onglets :

- **Une instance** : générer une instance et voir l'affectation obtenue (stabilité, satisfaction, résultat par établissement) ;
- **Pas à pas** : rejouer l'algorithme tour par tour (propositions, rejets, admis provisoires) ;
- **Comparer les deux côtés** : les deux versions de l'algorithme sur la même instance ;
- **Les scénarios** : le tableau des résultats, les graphiques et le téléchargement de `resultats.csv`.

## 2. Modélisation

- *E* = {0, …, n−1} les étudiants ; *H* = {0, …, m−1} les établissements.
- `pref_etu[e]` : liste ordonnée (meilleur d'abord) des établissements acceptables pour *e*.
- `pref_etab[h]` : liste ordonnée des étudiants acceptables pour *h*.
- `capacites[h]` : nombre de places de *h*.

Une **affectation** associe à chaque étudiant au plus un établissement, sans dépasser les capacités. Elle est **stable** s'il n'existe pas de paire (*e*, *h*) telle que *e* préfère *h* à son affectation (ou n'est pas affecté), et *h* a une place libre ou préfère *e* à l'un de ses admis.

## 3. Génération des préférences aléatoires

La fonction `generer_instance(n_etu, n_etab, capacites, mode, correlation, longueur_liste, graine)` propose deux modèles :

| Mode | Principe | Intérêt |
|---|---|---|
| `uniforme` | Chaque agent tire une permutation aléatoire uniforme de l'autre côté. | Modèle de référence de la littérature, sans structure. |
| `correle` | Chaque établissement a un **prestige** commun et chaque étudiant une **note** commune (tirés dans [0,1]). Chaque agent classe selon *score commun + bruit gaussien individuel*. Le paramètre `correlation` ∈ [0,1] règle le bruit : σ = (1−c)/c. | Plus réaliste : tout le monde veut les « bons » établissements et les « bons » étudiants. c → 1 : préférences identiques ; c → 0 : uniforme. |

Options supplémentaires :

- **capacités** : par défaut réparties pour que le nombre de places soit égal au nombre d'étudiants ; on peut fixer une pénurie ou un excédent, et répartir les places de façon inégale ;
- **listes incomplètes** (`longueur_liste = k`) : chaque étudiant ne classe que *k* établissements, comme sur une plateforme de vœux ; un établissement ne classe alors que ses candidats ;
- **graine** : reproductibilité des expériences.

## 4. L'algorithme du mariage stable

### 4.1 Version étudiants proposants

```
tous les étudiants sont libres
tant qu'il existe un étudiant libre e qui n'a pas épuisé sa liste :
    h ← prochain établissement de la liste de e
    si h n'a pas classé e : e reste libre
    sinon :
        h ajoute e à ses admis provisoires
        si |admis(h)| > c_h :
            h rejette son admis le moins bien classé, qui redevient libre
```

### 4.2 Version établissements proposants

Chaque établissement ayant des places libres propose à ses étudiants préférés pas encore sollicités. Un étudiant garde la meilleure proposition reçue et libère une place dans l'établissement qu'il abandonne. Cet établissement reprend alors ses propositions.

### 4.3 Détails d'implantation et propriétés

- Les préférences sont converties en **tables de rangs** (`rang[a][b]`), ce qui permet une comparaison en O(1).
- Une file (`deque`) gère les agents libres.
- **Terminaison et complexité** : chaque agent propose au plus une fois à chaque membre de l'autre côté. Il y a donc au plus *n × m* propositions, et l'algorithme est en O(*n·m*) (à un facteur *c_h* près pour la recherche du pire admis).
- **Stabilité** : la fonction `paires_bloquantes()` vérifie le résultat. Elle a renvoyé une liste vide sur **100 % des 180 exécutions** (section 6).
- **Optimalité** : la version étudiants proposants donne à chaque étudiant le meilleur établissement possible parmi toutes les affectations stables, et le pire pour les établissements. La version établissements proposants fait l'inverse. Les expériences le confirment.
- **Non-manipulabilité** (résultat théorique connu, non testé ici) : côté étudiants proposants, un étudiant n'a jamais intérêt à mentir sur ses préférences. C'est la raison pour laquelle les plateformes réelles utilisent cette version.

## 5. Mesure de la satisfaction

### 5.1 Score individuel

La satisfaction d'un agent dépend du **rang** de ce qu'il obtient dans sa liste. Les listes peuvent avoir des longueurs différentes, on normalise donc dans [0, 1] :

$$ s(r) = 1 - \frac{r}{L-1} $$

où *r* est le rang obtenu (0 = premier choix) et *L* la longueur de la liste. On a s = 1 pour le premier choix et s = 0 pour le dernier choix ou en l'absence d'affectation.

- **Étudiant *e*** : s_e = s(rang de son établissement). Un étudiant non affecté obtient 0.
- **Établissement *h*** : moyenne sur ses *c_h* **places** :
  $$ s_h = \frac{1}{c_h}\sum_{x \in \text{admis}(h)} s(\text{rang}_h(x)) $$
  Une place vide compte 0. Cette mesure pénalise donc à la fois les admis mal classés et les places non pourvues.

  *Pourquoi compter les places vides ?*

  - **L'objectif d'un établissement** est de remplir ses places avec de bons étudiants. Une place vide est une perte réelle : enseignants, salles et budget prévus pour rien.
  - **Sans cette règle, le score serait trompeur.** Prenons un établissement de 40 places qui n'admet que son candidat préféré. Avec une moyenne sur ses admis, il obtiendrait 1, un score parfait, alors que 39 places sont vides. Avec une moyenne sur ses places, il obtient 1/40.
  - **Symétrie avec les étudiants** : un étudiant non affecté vaut 0, donc une place non pourvue vaut 0.

  Le taux de remplissage et le % d'admis idéaux sont donnés à part. Le décideur peut donc distinguer les « mauvais admis » des « places vides ».

### 5.2 Indicateurs agrégés (pour chaque côté)

| Indicateur | Ce qu'il mesure |
|---|---|
| Moyenne *S* | Efficacité (critère utilitariste) |
| Minimum | Situation du plus mal servi (critère égalitariste de Rawls) |
| Écart-type, **indice de Gini** | Équité de la répartition |
| Rang moyen, % 1er choix, % top 3 | Indicateurs lisibles pour un décideur |
| % non affectés / taux de remplissage | Couverture |
| % admis « idéaux » (établissement) | Part des admis figurant parmi ses *c_h* premiers choix |

**Satisfaction globale** : S = α·S_etu + (1−α)·S_etab, avec α = 0,5 par défaut. Le décideur peut ajuster α pour donner plus de poids à l'un des deux côtés. On mesure aussi le **déséquilibre** |S_etu − S_etab|. Ces mesures sont calculées par `satisfaction_etudiants()`, `satisfaction_etablissements()` et `satisfaction_globale()`.

## 6. Expérimentations

Le programme exécute 3 scénarios, avec **30 instances aléatoires** chacun, et les deux versions de l'algorithme. Chaque scénario montre un facteur qui change le comportement de l'algorithme. Tous ont 200 étudiants et 10 établissements. Les valeurs ci-dessous sont des moyennes. *Props* = nombre de propositions, *Rang* = rang moyen obtenu par les étudiants (1 = premier choix), *%NA* = étudiants non affectés.

| Scénario | Proposant | Stable | Props | S_etu | Rang | %1er | %top3 | %NA | Gini | S_etab | %Rempl. | S_glob |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 : référence (uniforme, places = étudiants) | étudiants | 100 % | 264 | 0,965 | 1,32 | 75,9 | 98,6 | 0 | 0,029 | 0,608 | 100 | 0,786 |
| | établ. | 100 % | 849 | 0,849 | 2,36 | 42,1 | 80,7 | 0 | 0,110 | 0,783 | 100 | 0,816 |
| S2 : préférences corrélées (c = 0,95) | étudiants | 100 % | 993 | 0,559 | 4,96 | 15,8 | 36,5 | 0 | 0,321 | 0,518 | 100 | 0,538 |
| | établ. | 100 % | 1151 | 0,559 | 4,97 | 15,8 | 36,5 | 0 | 0,322 | 0,518 | 100 | 0,538 |
| S3 : pénurie (50 % de places) | étudiants | 100 % | 1497 | 0,279 | 4,97 | 6,8 | 18,8 | 50 | 0,662 | 0,969 | 100 | 0,624 |
| | établ. | 100 % | 132 | 0,279 | 4,97 | 6,8 | 18,8 | 50 | 0,662 | 0,969 | 100 | 0,624 |

*Les temps d'exécution restent inférieurs à 10 ms.*

### Analyse

1. **Stabilité** : les 180 affectations produites (3 scénarios × 30 instances × 2 versions) sont stables, ce qui valide l'implantation.
2. **Le côté qui propose est avantagé** (S1) : la satisfaction des étudiants passe de 0,965 à 0,849 quand ce sont les établissements qui proposent, et celle des établissements de 0,608 à 0,783. On retrouve l'optimalité théorique : chaque version donne la meilleure affectation stable pour le côté qui propose.
3. **Effet de la corrélation** (S1 → S2) : quand tout le monde vise les mêmes établissements, la satisfaction baisse (0,965 → 0,559) et les inégalités augmentent (Gini 0,03 → 0,32). Il existe alors presque une seule affectation stable : les deux versions donnent le même résultat et le choix du côté proposant n'a plus d'effet.
4. **Effet de la capacité** (S3) : en pénurie, la moitié des étudiants restent sans place, mais le résultat reste stable et les établissements sont presque parfaitement satisfaits (0,97). Le côté rare est le mieux servi, et les deux versions coïncident dans ce marché déséquilibré (Ashlagi et al.).
5. **Coût** : le nombre de propositions reste très inférieur à la borne *n·m*. Il est plus élevé du côté qui doit « descendre » dans ses listes : en pénurie, les étudiants rejetés parcourent toute leur liste (1497 propositions contre 132).
6. **Satisfaction globale** : elle est proche pour les deux versions. Le choix du côté proposant est donc surtout un choix d'**équité** (qui est favorisé) plus que d'efficacité. La mesure du minimum et le Gini rendent ce choix visible pour le décideur.

## 7. Extension : représentations compactes des préférences (sans implantation)

### 7.1 Motivation

Dans la réalité, un étudiant ne choisit pas seulement un établissement mais une **combinaison** : (établissement, spécialité, ville, régime internat/externat…). Avec 4 attributs de 5 valeurs, on obtient déjà 625 alternatives, et un ordre total sur ces alternatives est impossible à demander. De même, un établissement ne classe pas des milliers de candidats à la main : il applique des critères (moyenne, filière du bac, motivation…). Il faut donc des **représentations compactes** des préférences.

### 7.2 Architecture proposée

```
  Élicitation compacte  ──►  Module d'inférence  ──►  Gale-Shapley (inchangé)  ──►  Satisfaction
  (CP-net, LP-tree,           (calcul du                (étudiants proposants)       (rang ou
   GAI / additif,             « prochain meilleur                                      degré de
   logique pondérée)          choix »)                                                 dominance)
```

L'algorithme n'a jamais besoin de la liste complète. Il demande seulement à chaque étudiant son **prochain meilleur choix** et à chaque établissement une **comparaison entre deux candidats**. Ces deux opérations sont les points d'interface avec la représentation compacte.

### 7.3 Côté étudiants

| Représentation | Exemple | Utilisation dans l'algorithme |
|---|---|---|
| **Préférences lexicographiques / LP-trees** | « D'abord la spécialité Info > Maths ; puis, si Info, la ville Alger > Oran ; sinon … » | Ordre total. Le *k*-ième meilleur choix se calcule en temps polynomial par parcours de l'arbre, sans énumérer toutes les alternatives. Comparaison en O(nb d'attributs). |
| **CP-nets** | « Je préfère Alger à Oran ; *si* Alger, je préfère l'externat, *sinon* l'internat » | L'alternative optimale se calcule en temps linéaire (*forward sweep*) si le réseau est acyclique. Le CP-net ne définit qu'un ordre **partiel** : on propose de générer une **extension linéaire** (tri topologique successif) pour alimenter l'algorithme. Les ex æquo ou incomparables peuvent être départagés par une règle fixée ou un tirage. |
| **Utilité additive / GAI** | u(x) = Σ u_i(x_i) ou une somme sur des sous-ensembles d'attributs liés | Ordre (pré)total. Le prochain meilleur choix s'obtient par recherche *best-first* ou par programmation dynamique sur l'arbre de jonction GAI. |
| **Logique pondérée / logique de pénalités** | Buts (« ville = Alger », poids 5 ; « internat », poids 2) | Le score d'une alternative est la somme des poids des buts satisfaits (ou violés). Ordre pré-total, à départager. |

### 7.4 Côté établissements

L'établissement exprime une **fonction de score** sur les attributs des candidats (note × 0,6 + filière × 0,3 + entretien × 0,1), ou un **LP-tree** (d'abord la filière, puis la note). La comparaison de deux candidats, seule opération utilisée par l'algorithme, devient un calcul direct. Les quotas (par exemple de boursiers) se traduisent par des capacités par catégorie.

### 7.5 Conséquences et points de vigilance

- **Stabilité** : si chaque représentation produit un ordre total strict (après départage), l'algorithme et ses garanties (stabilité, optimalité, non-manipulabilité) restent inchangés.
- **Ordres partiels / indifférences** : plusieurs notions de stabilité existent alors (faible, forte, super-stabilité). La stabilité faible existe toujours (par départage). La recherche d'une affectation stable *maximum* avec indifférences est NP-difficile : il faut choisir le départage avec soin, par exemple avec un départage unique commun pour limiter les inefficacités.
- **Complexité** : les requêtes de dominance dans un CP-net général sont PSPACE-complètes. On se limite donc aux CP-nets acycliques ou arborescents et aux LP-trees, où les opérations utiles sont polynomiales.
- **Mesure de satisfaction adaptée** : le rang *r* devient la position dans l'extension linéaire. On peut aussi définir un score qualitatif, par exemple le nombre d'alternatives qui dominent strictement l'alternative obtenue dans le CP-net, normalisé par le nombre total d'alternatives, ou la fraction des buts pondérés satisfaits en logique pondérée.
- **Élicitation** : l'interface pose des questions simples (importance des attributs, préférences conditionnelles), ce qui réduit fortement la charge cognitive par rapport à un classement complet.

## 8. Conclusion

Nous avons implanté un générateur de préférences configurable, l'algorithme de Gale-Shapley *many-to-one* dans ses deux variantes avec vérification de stabilité, et une batterie de mesures de satisfaction : moyenne, minimum, Gini, rangs et taux de remplissage. Les tests sur 3 jeux de données confirment la stabilité des résultats et l'avantage du côté proposant dans un marché équilibré. Ils montrent aussi l'influence de la corrélation des préférences et du nombre de places. L'extension aux représentations compactes (LP-trees, CP-nets, GAI, logique pondérée) rend le système utilisable sur des alternatives multi-attributs. Elle conserve l'algorithme et ses garanties, à condition de fournir un ordre total strict par départage.

### Références

- D. Gale, L. S. Shapley, *College Admissions and the Stability of Marriage*, American Mathematical Monthly, 1962.
- A. E. Roth, M. Sotomayor, *Two-Sided Matching*, Cambridge University Press, 1990.
- I. Ashlagi, Y. Kanoria, J. D. Leshno, *Unbalanced Random Matching Markets*, Journal of Political Economy, 2017.
- C. Boutilier et al., *CP-nets: A Tool for Representing and Reasoning with Conditional Ceteris Paribus Preference Statements*, JAIR, 2004.
- R. Booth et al., *Learning Conditionally Lexicographic Preference Relations*, ECAI, 2010.
