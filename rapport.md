# Aide à la décision 2026–2027 — Projet : Algorithme du mariage stable

## 1. Introduction

On cherche à affecter des **étudiants** à des **établissements** disposant d'un nombre limité de places. Chaque étudiant classe les établissements et chaque établissement classe les étudiants. On veut une affectation **stable** : il ne doit exister aucun couple (étudiant *e*, établissement *h*) qui ont tous deux intérêt à rompre l'affectation pour s'associer (*paire bloquante*).

L'algorithme d'acceptation différée de Gale et Shapley (1962) résout ce problème. Nous l'étudions ici dans sa version « *many-to-one* » (admissions universitaires) : un établissement *h* a une capacité *c_h* ≥ 1.

Le travail comprend :

1. un générateur de préférences aléatoires ;
2. l'implantation de l'algorithme, côté étudiants et côté établissements ;
3. une méthode de mesure de la satisfaction, intégrée au programme ;
4. des tests sur 22 jeux de données, dont 14 consacrés à la capacité des établissements (pénurie, excédent, répartition des places) ;
5. une extension (sans implantation) vers les représentations compactes des préférences.

**Fichiers rendus :** `mariage_stable.py` (bibliothèque), `experiences.py` (campagne de tests), `resultats.csv` (résultats). Python ≥ 3.8, bibliothèque standard uniquement.

```
python mariage_stable.py      # petit exemple commenté
python experiences.py [R]     # R instances par scénario (30 par défaut)
```

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
- **capacités selon le prestige** (`capacites_selon_prestige`, mode `correle`) : `"direct"` donne les plus grandes capacités aux établissements les plus demandés, `"inverse"` les plus petites ;
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
- **Stabilité** : la fonction `paires_bloquantes()` vérifie le résultat. Elle a renvoyé une liste vide sur **100 % des 1320 exécutions** (section 6).
- **Optimalité** : la version étudiants proposants donne à chaque étudiant le meilleur établissement possible parmi toutes les affectations stables, et le pire pour les établissements. La version établissements proposants fait l'inverse. Les expériences le confirment.
- **Non-manipulabilité** : côté étudiants proposants, un étudiant n'a jamais intérêt à mentir sur ses préférences. C'est la raison pour laquelle les plateformes réelles utilisent cette version.

## 5. Mesure de la satisfaction

### 5.1 Score individuel

La satisfaction d'un agent dépend du **rang** de ce qu'il obtient dans sa liste. Les listes peuvent avoir des longueurs différentes, on normalise donc dans [0, 1] :

$$ s(r) = 1 - \frac{r}{L-1} $$

où *r* est le rang obtenu (0 = premier choix) et *L* la longueur de la liste. On a s = 1 pour le premier choix et s = 0 pour le dernier choix ou en l'absence d'affectation.

- **Étudiant *e*** : s_e = s(rang de son établissement). Un étudiant non affecté obtient 0.
- **Établissement *h*** : moyenne sur ses *c_h* **places** :
  $$ s_h = \frac{1}{c_h}\sum_{x \in \text{admis}(h)} s(\text{rang}_h(x)) $$
  Une place vide compte 0. Cette mesure pénalise donc à la fois les admis mal classés et les places non pourvues.

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

Le programme exécute 22 scénarios, avec **30 instances aléatoires** chacun, et les deux versions de l'algorithme. Les valeurs ci-dessous sont des moyennes. *Props* = nombre de propositions, *Rang* = rang moyen obtenu par les étudiants (1 = premier choix), *%NA* = étudiants non affectés.

| Scénario | Proposant | Stable | Props | S_etu | Rang | %1er | %top3 | %NA | Gini | S_etab | %Rempl. | S_glob |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 : 20 étu./4 étab., uniforme | étudiants | 100 % | 27 | 0,880 | 1,36 | 72,3 | 98,8 | 0 | 0,102 | 0,598 | 100 | 0,739 |
| | établ. | 100 % | 47 | 0,782 | 1,66 | 57,8 | 93,8 | 0 | 0,184 | 0,680 | 100 | 0,731 |
| S2 : 200/10, uniforme | étudiants | 100 % | 264 | 0,965 | 1,32 | 75,9 | 98,6 | 0 | 0,029 | 0,608 | 100 | 0,786 |
| | établ. | 100 % | 849 | 0,849 | 2,36 | 42,1 | 80,7 | 0 | 0,110 | 0,783 | 100 | 0,816 |
| S3 : 1000/20, uniforme | étudiants | 100 % | 1291 | 0,985 | 1,29 | 77,4 | 98,8 | 0 | 0,013 | 0,602 | 100 | 0,793 |
| | établ. | 100 % | 6148 | 0,878 | 3,33 | 30,1 | 66,2 | 0 | 0,082 | 0,843 | 100 | 0,860 |
| S4 : corrélé c = 0,3 | étudiants | 100 % | 291 | 0,950 | 1,45 | 68,9 | 96,6 | 0 | 0,040 | 0,637 | 100 | 0,793 |
| | établ. | 100 % | 940 | 0,867 | 2,20 | 46,5 | 83,3 | 0 | 0,099 | 0,757 | 100 | 0,812 |
| S5 : corrélé c = 0,7 | étudiants | 100 % | 555 | 0,803 | 2,78 | 35,1 | 71,6 | 0 | 0,142 | 0,678 | 100 | 0,740 |
| | établ. | 100 % | 1056 | 0,788 | 2,90 | 34,1 | 69,7 | 0 | 0,155 | 0,693 | 100 | 0,741 |
| S6 : corrélé c = 0,95 | étudiants | 100 % | 993 | 0,559 | 4,96 | 15,8 | 36,5 | 0 | 0,321 | 0,518 | 100 | 0,538 |
| | établ. | 100 % | 1151 | 0,559 | 4,97 | 15,8 | 36,5 | 0 | 0,322 | 0,518 | 100 | 0,538 |
| S7 : pénurie (50 % de places) | étudiants | 100 % | 1497 | 0,279 | 4,97 | 6,8 | 18,8 | 50 | 0,662 | 0,969 | 100 | 0,624 |
| | établ. | 100 % | 132 | 0,279 | 4,97 | 6,8 | 18,8 | 50 | 0,662 | 0,969 | 100 | 0,624 |
| S8 : excédent (150 % de places) | étudiants | 100 % | 200 | 1,000 | 1,00 | 99,8 | 100 | 0 | 0,000 | 0,335 | 66,7 | 0,667 |
| | établ. | 100 % | 1998 | 1,000 | 1,00 | 99,8 | 100 | 0 | 0,000 | 0,335 | 66,7 | 0,667 |
| S9 : listes courtes (k = 3) | étudiants | 100 % | 251 | 0,873 | 1,24 | 78,9 | 99,2 | 0,8 | 0,119 | 0,590 | 99,2 | 0,731 |
| | établ. | 100 % | 466 | 0,865 | 1,26 | 77,7 | 99,2 | 0,8 | 0,126 | 0,596 | 99,2 | 0,730 |
| S10 : 1-1 classique, n = 100 | étudiants | 100 % | 526 | 0,957 | 5,25 | 19,3 | 47,2 | 0 | 0,024 | 0,819 | 100 | 0,888 |
| | établ. | 100 % | 529 | 0,812 | 19,60 | 5,4 | 14,8 | 0 | 0,116 | 0,957 | 100 | 0,884 |

*S2 à S9 : 200 étudiants et 10 établissements. Les temps d'exécution restent inférieurs à 10 ms, même pour 1000 étudiants.*

### 6.1 Cas supplémentaires : capacité des établissements

Pour étudier l'effet du nombre de places, on ajoute 12 scénarios. Tous ont 200 étudiants, préférences uniformes et 10 établissements, sauf indication contraire.

- **A. Nombre total de places** (de 25 % à 200 % du nombre d'étudiants, places égales partout). Avec S7 (50 %), S2 (100 %) et S8 (150 %), on obtient une courbe complète.
- **B. Répartition inégale** des 200 places : un grand établissement et des petits, deux grands, ou 200 établissements d'une seule place.
- **C. Capacité et popularité** (préférences corrélées, c = 0,7, capacités 40, 35, 30, 25, 20, 15, 15, 10, 5, 5) : les établissements les plus demandés sont les plus petits (S20) ou les plus grands (S21). S22 combine pénurie et corrélation.

| Scénario | Proposant | Stable | Props | S_etu | Rang | %1er | %top3 | %NA | Gini | S_etab | %Rempl. | S_glob |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S11 : pénurie sévère (25 %) | étudiants | 100 % | 1757 | 0,135 | 5,15 | 3,0 | 8,9 | 75 | 0,834 | 0,988 | 100 | 0,561 |
| | établ. | 100 % | 56 | 0,135 | 5,15 | 3,0 | 8,9 | 75 | 0,834 | 0,988 | 100 | 0,561 |
| S7 : pénurie (50 %) *(rappel)* | étudiants | 100 % | 1497 | 0,279 | 4,97 | 6,8 | 18,8 | 50 | 0,662 | 0,969 | 100 | 0,624 |
| S12 : pénurie modérée (75 %) | étudiants | 100 % | 1155 | 0,469 | 4,37 | 13,2 | 34,4 | 25 | 0,455 | 0,936 | 100 | 0,703 |
| | établ. | 100 % | 259 | 0,468 | 4,38 | 13,2 | 34,2 | 25 | 0,456 | 0,936 | 100 | 0,702 |
| S13 : légère pénurie (95 %) | étudiants | 100 % | 740 | 0,700 | 3,37 | 26,1 | 59,0 | 5 | 0,232 | 0,871 | 100 | 0,786 |
| | établ. | 100 % | 504 | 0,697 | 3,40 | 25,7 | 58,5 | 5 | 0,235 | 0,873 | 100 | 0,785 |
| S2 : équilibre (100 %) *(rappel)* | étudiants | 100 % | 264 | 0,965 | 1,32 | 75,9 | 98,6 | 0 | 0,029 | 0,608 | 100 | 0,786 |
| | établ. | 100 % | 849 | 0,849 | 2,36 | 42,1 | 80,7 | 0 | 0,110 | 0,783 | 100 | 0,816 |
| S14 : léger excédent (105 %) | étudiants | 100 % | 225 | 0,986 | 1,13 | 88,8 | 99,8 | 0 | 0,013 | 0,524 | 95,2 | 0,755 |
| | établ. | 100 % | 1771 | 0,985 | 1,13 | 88,5 | 99,8 | 0 | 0,013 | 0,525 | 95,2 | 0,755 |
| S15 : excédent modéré (125 %) | étudiants | 100 % | 203 | 0,998 | 1,02 | 98,4 | 100 | 0 | 0,002 | 0,407 | 80,0 | 0,703 |
| | établ. | 100 % | 1969 | 0,998 | 1,02 | 98,3 | 100 | 0 | 0,002 | 0,407 | 80,0 | 0,703 |
| S8 : excédent (150 %) *(rappel)* | étudiants | 100 % | 200 | 1,000 | 1,00 | 99,8 | 100 | 0 | 0,000 | 0,335 | 66,7 | 0,667 |
| S16 : fort excédent (200 %) | étudiants | 100 % | 200 | 1,000 | 1,00 | 100 | 100 | 0 | 0,000 | 0,251 | 50,0 | 0,625 |
| | établ. | 100 % | 2000 | 1,000 | 1,00 | 100 | 100 | 0 | 0,000 | 0,251 | 50,0 | 0,625 |
| S17 : 1 grand (110) + 9 petits (10) | étudiants | 100 % | 733 | 0,704 | 3,67 | 23,2 | 56,5 | 0 | 0,213 | 0,885 | 100 | 0,795 |
| | établ. | 100 % | 448 | 0,698 | 3,71 | 23,0 | 55,7 | 0 | 0,217 | 0,888 | 100 | 0,793 |
| S18 : 2 grands (60) + 8 petits (10) | étudiants | 100 % | 515 | 0,825 | 2,57 | 35,8 | 75,5 | 0 | 0,121 | 0,820 | 100 | 0,823 |
| | établ. | 100 % | 622 | 0,786 | 2,92 | 31,3 | 69,1 | 0 | 0,151 | 0,843 | 100 | 0,815 |
| S19 : 200 étab. à 1 place | étudiants | 100 % | 1043 | 0,979 | 5,21 | 19,8 | 48,8 | 0 | 0,012 | 0,813 | 100 | 0,896 |
| | établ. | 100 % | 1191 | 0,836 | 33,69 | 3,1 | 8,5 | 0 | 0,098 | 0,975 | 100 | 0,905 |
| S20 : populaires = petits | étudiants | 100 % | 779 | 0,678 | 3,89 | 16,4 | 50,1 | 0 | 0,208 | 0,769 | 100 | 0,723 |
| | établ. | 100 % | 797 | 0,671 | 3,96 | 16,2 | 49,3 | 0 | 0,215 | 0,773 | 100 | 0,722 |
| S21 : populaires = grands | étudiants | 100 % | 361 | 0,911 | 1,80 | 61,1 | 89,6 | 0 | 0,072 | 0,600 | 100 | 0,755 |
| | établ. | 100 % | 1234 | 0,888 | 2,01 | 57,3 | 86,1 | 0 | 0,092 | 0,637 | 100 | 0,762 |
| S22 : pénurie (50 %) + corrélé | étudiants | 100 % | 1448 | 0,306 | 4,48 | 8,1 | 22,2 | 50 | 0,642 | 0,946 | 100 | 0,626 |
| | établ. | 100 % | 204 | 0,306 | 4,50 | 8,0 | 22,1 | 50 | 0,643 | 0,947 | 100 | 0,626 |

*Les lignes « rappel » reprennent S2, S7 et S8 pour lire la courbe dans l'ordre croissant du nombre de places. Dans tous les cas, %NA = max(0, 1 − places/étudiants) et le taux de remplissage = min(100 %, étudiants/places), comme attendu avec des listes complètes.*

### Analyse

1. **Stabilité** : les 1320 affectations produites (22 scénarios × 30 instances × 2 versions) sont stables, ce qui valide l'implantation.
2. **Le côté qui propose est avantagé** (S1–S4, S10). Dans le cas 1-1 uniforme (S10), le rang moyen d'un étudiant passe de 5,25 à 19,6 quand les établissements proposent, et celui des établissements évolue en sens inverse. On retrouve le résultat théorique : rang ≈ ln n pour le côté proposant contre ≈ n / ln n pour l'autre.
3. **Effet de la corrélation** (S4 → S6) : plus les préférences se ressemblent, plus la satisfaction baisse et plus les inégalités augmentent (Gini 0,04 → 0,32), car tout le monde vise les mêmes établissements. Il existe alors presque une seule affectation stable : les deux versions donnent le même résultat et le choix du côté proposant n'a plus d'effet.
4. **Effet de la capacité** : en pénurie (S7), la moitié des étudiants restent sans place et les établissements sont presque parfaitement satisfaits (0,97). En excédent (S8), la situation s'inverse : les étudiants obtiennent leur premier choix et un tiers des places restent vides. Les deux versions coïncident dans ces cas déséquilibrés, ce qui illustre le « *core* étroit » des marchés déséquilibrés (Ashlagi et al.).
5. **Listes courtes** (S9) : quelques étudiants (0,8 %) restent sans affectation alors qu'il y a assez de places. Le nombre de vœux est un vrai levier de conception du système.
6. **Coût** : le nombre de propositions reste très inférieur à la borne *n·m*. Il est plus élevé du côté qui doit « descendre » dans ses listes.
7. **Satisfaction globale** : elle est proche pour les deux versions. Le choix du côté proposant est donc surtout un choix d'**équité** (qui est favorisé) plus que d'efficacité. La mesure du minimum et le Gini rendent ce choix visible pour le décideur.
8. **Courbe offre/demande** (S11 → S16) : quand le nombre de places passe de 25 % à 200 % des étudiants, S_etu monte de 0,135 à 1,000 et S_etab descend de 0,988 à 0,251. Le côté **rare** est toujours le mieux servi. La satisfaction globale est maximale près de l'équilibre (0,786 à 95–100 %) et baisse des deux côtés : la pénurie laisse des étudiants sans place, l'excédent laisse des places vides.
9. **Basculement autour de l'équilibre** (S13, S2, S14) : il suffit de 5 % de places en moins ou en plus pour changer le marché. À 95 %, le rang moyen des étudiants est 3,37. À 105 %, il est 1,13, avec 89 % de premiers choix. Au même moment, l'écart entre les deux versions de l'algorithme disparaît : à l'équilibre exact (S2), proposer donne un vrai avantage (0,965 contre 0,849 pour les étudiants), mais à 95 % ou 105 % les deux versions donnent presque le même résultat. C'est le résultat d'Ashlagi et al. : dans un marché déséquilibré, même légèrement, c'est le rapport de forces et non le côté proposant qui décide.
10. **Pénurie et coût** : en pénurie, la version étudiants proposants demande beaucoup plus de propositions (1757 contre 56 en S11), car les étudiants rejetés descendent toute leur liste. En excédent, c'est l'inverse (200 contre 2000 en S16). Le résultat est le même, mais le coût de calcul dépend du côté rare.
11. **Répartition inégale des places** (S17, S18 contre S2, même total de 200) : concentrer les places dans un grand établissement fait baisser la satisfaction des étudiants (0,965 → 0,704 avec un établissement de 110 places) et augmente les inégalités (Gini 0,03 → 0,21). Les préférences étant uniformes, la plupart des étudiants préfèrent un petit établissement, qui ne peut pas les prendre, et finissent dans le grand. Les établissements, eux, sont plus satisfaits (0,885), car les petits établissements remplissent leurs places avec leurs meilleurs candidats. À total égal, la **forme** de l'offre compte donc autant que sa taille.
12. **Établissements à une place** (S19, 200 × 1) : on retrouve le cas 1-1 (comme S10) avec un fort avantage pour le côté proposant : le rang moyen des étudiants passe de 5,2 à 33,7 quand les établissements proposent. Plus les capacités sont petites, plus il existe d'affectations stables différentes, et plus le choix du côté proposant est important.
13. **Capacité et popularité** (S20, S21) : si les établissements les plus demandés sont **grands**, 61 % des étudiants ont leur premier choix (S_etu = 0,911, Gini 0,07). S'ils sont **petits**, seulement 16 % l'obtiennent (S_etu = 0,678, Gini 0,21). Les capacités sont pourtant les mêmes dans les deux cas : seule leur attribution change. Pour un décideur, augmenter les places des formations les plus demandées est le levier le plus efficace pour la satisfaction des étudiants.
14. **Pénurie et préférences corrélées** (S22 contre S7) : avec 50 % de places, la moitié des étudiants restent sans affectation dans les deux cas. Les inégalités restent très fortes (Gini 0,64). Mais les établissements classent tous les étudiants à peu près de la même façon. Les étudiants sans place devraient donc être surtout ceux qui ont une note commune faible : la pénurie n'est plus répartie au hasard. Ce point n'est pas mesuré ici. On pourrait le vérifier en comparant la note des étudiants non affectés à celle des autres.

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

Nous avons implanté un générateur de préférences configurable, l'algorithme de Gale-Shapley *many-to-one* dans ses deux variantes avec vérification de stabilité, et une batterie de mesures de satisfaction : moyenne, minimum, Gini, rangs et taux de remplissage. Les tests sur 22 jeux de données confirment la stabilité des résultats et l'avantage du côté proposant dans les marchés équilibrés. Ils montrent aussi l'influence de la corrélation des préférences, de la longueur des listes et surtout de la capacité : le nombre total de places, leur répartition entre établissements et leur attribution aux établissements les plus demandés. L'extension aux représentations compactes (LP-trees, CP-nets, GAI, logique pondérée) rend le système utilisable sur des alternatives multi-attributs. Elle conserve l'algorithme et ses garanties, à condition de fournir un ordre total strict par départage.

### Références

- D. Gale, L. S. Shapley, *College Admissions and the Stability of Marriage*, American Mathematical Monthly, 1962.
- A. E. Roth, M. Sotomayor, *Two-Sided Matching*, Cambridge University Press, 1990.
- I. Ashlagi, Y. Kanoria, J. D. Leshno, *Unbalanced Random Matching Markets*, Journal of Political Economy, 2017.
- C. Boutilier et al., *CP-nets: A Tool for Representing and Reasoning with Conditional Ceteris Paribus Preference Statements*, JAIR, 2004.
- R. Booth et al., *Learning Conditionally Lexicographic Preference Relations*, ECAI, 2010.
