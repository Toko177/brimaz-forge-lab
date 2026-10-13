# Brimaz V5 — expérience contrôlée sur le « tour 4 à vide »

**13 octobre 2026 — V5 EXPÉRIMENTALE. La V4 actuelle n'est pas modifiée.**

## Hypothèse née de vraies parties, pas du classement heuristique de cartes

Dans la campagne Forge [V3 vs V4, 16 parties dont 13 naturelles certifiées](BRIMAZ_V3_V4_FORGE_AB_2026-10-13.md) :
- V3 a fait **0 victoire sur 7** parties certifiées ; V4 **0/6**. Aucune supériorité de la V4 n'est prouvée et le pilotage IA a produit des erreurs de temps de décision / repli sur les attaques.
- Brimaz a été lancé **sans qu'aucune de ses capacités d'Incubation ne soit ensuite résolue** dans 4/7 parties certifiées V3 et 2/6 V4. Ce sont **des résultats de parties distinctes**, pas un taux de succès d'un effet de carte.
- Dans les **huit** journaux V4 (incluant deux parties non certifiées), **Throne of Geth a été lancé dans deux parties et sa capacité n'a jamais été activée**. **Myr Sire a été lancé dans une partie**. Ces observations sont exactes pour les événements lus, mais ne prouvent PAS que les cartes seraient mauvaises entre les mains d'un humain.

**Constat strict de règles, complètement vérifiable :**
Brimaz coûte `{2}{W}{B}`, et n'a pas de capacité ETB ni d'incubation sur son propre lancement. Sans réduction de coûts, la V4 ne comporte **aucune créature Phyrexian / artefact-créature payable avec exactement un mana** après ce lancement. Dans une position où Brimaz a déjà été lancé et où il reste un seul mana, **aucun lancement à un mana ne peut donc activer sa capacité**. Avec un seul mana restant, deux options changeraient ce point précis.

## Deux échanges, hypothèse falsifiable V4 → V5

| V4 conservée | Essai V5 (budget, Commander WB) | Effet justifié par l'Oracle, et coût de l'échange |
|---|---|---|
| **Throne of Geth** — artefact {2}, sacrifice autre artefact + engagement pour proliférer | **Vault Skirge** — artefact-créature **Phyrexian**, {1}{B/P}, 1/1 volante et lien de vie | Choisir **{1} + 2 points de vie** permet de le lancer avec un seul mana libre et de déclencher **Incubation 2** (sa valeur de mana est toujours 2). Vol/lifelink utilisables même sans commandant. **Perte : un exutoire de sacrifice qui prolifère indépendamment de Brimaz**. |
| **Myr Sire** — artefact-créature Phyrexian {2}, crée un Myr Phyrexian artefact 1/1 quand il meurt | **Changeling Outcast** — Phyrexian par *changeling* sur la pile, {B}, 1/1 imblocable qui ne peut pas bloquer | Pour **un mana noir libre**, le lancer déclenche **Incubation 1**. Sans Brimaz, reste un porteur de bonus tribaux imblocable et peut déclencher la pioche de Gix en infligeant des dégâts. **Perte : le corps de remplacement lors de la mort de Myr Sire, et l'utilité de ses deux corps d'artefacts pour les sacrifices**. |

**V5 n'est pas promue comme une meilleure liste**. Les deux échanges sont proposés pour **isoler un problème spécifique** ; les avantages et sacrifices sont explicites. Ne pas écrire que Vault Skirge a MV1 : **il a MV2**, même si l'on paie deux PV au lieu du mana noir. Changeling Outcast est Phyrexian via *changeling* bien qu'il n'ait pas le mot Phyrexian sur sa ligne de type imprimée.

## Preuve exacte du gain tactique (pas une simulation de parties)

Le script contrôlé [brimaz_v5_tempo_audit.py](../scripts/brimaz_v5_tempo_audit.py), avec [tests fail-closed](../tests/test_brimaz_v5_tempo_audit.py), compare les **100 mêmes cartes sauf deux** et calcule par dénombrement hypergéométrique la probabilité de **voir au moins une option** parmi les **12 premières cartes** (7 de départ + 5 tours de pioche, sans mulligan) :

| Situation FIXÉE et testée | V4 | Essai V5 |
|---|---:|---:|
| Brimaz déjà en jeu, **1 mana quelconque** disponible, au moins 3 PV pour payer Vault Skirge | **0 %** | **12,00 %** d'avoir vu Vault Skirge |
| Brimaz déjà en jeu, **1 mana noir** disponible, au moins 3 PV | **0 %** | **22,67 %** d'avoir vu au moins un des deux |
| Créatures Phyrexian/artefact-créature naturellement payables pour 1 mana, sans réduction de coût | **0** | **2** |

Calcul analytique du dernier chiffre : `1 - C(98,12)/C(100,12) = 0,226666…`. **Ces pourcentages sont des disponibilités de cartes vues sous scénario fixé**, en aucun cas la probabilité de produire effectivement un Incubateur en vraie partie, de maintenir Brimaz, de disposer du mana, de transformer, d'attaquer ou de gagner. Le choix de lancer un 1-drop avant Brimaz peut aussi éliminer le suivi après lui ; le chiffre ne conditionne pas sur les sorts déjà joués.

La probabilité de voir la carte n'est pas le winrate. **Les données humaines de combat et les attaques ne sont pas mesurées.**

## Limites bloquantes pour affirmer « meilleure V5 »

1. **Aucun vrai A/B V4/V5 à quatre joueurs réussi** sur une métrique distinguant les listes (la première campagne V3/V4 avait zéro victoire dans les deux bras).
2. **Aucune simulation validée du mana coloré**, du mulligan et de la consommation de cartes T1–T5. Le calcul fixe le mana résiduel **après** la résolution de Brimaz.
3. **Aucune évaluation de l'opportunité perdue** : Throne of Geth prolifère des Incubateurs, de la Chalice et des créatures à marqueurs ; Myr Sire assure un second corps Phyrexian lorsqu'il meurt. Les deux peuvent être supérieurs en partie longue.
4. **Pilotage humain différent de l'IA** : même si l'une des nouvelles cartes sort plus tôt, cela ne prouve pas que le deck gagne contre KaalDeagle.

## Verdict opérationnel et seuil d'acceptation

- **Prouvé :** deux lignes de cast et d'attaque initialement indisponibles sont ajoutées par deux cartes courantes et légales (après audit Oracle CI).
- **Non prouvé :** augmentation du nombre de victoires, de dégâts réels, de résilience, ou de pression jusqu'à trois adversaires.
- La **V4 reste la liste de référence** et la **V5 reste une variante isolée**. Pour promouvoir un remplacement, recueillir un échantillon de parties humaines à quatre avec journaux : n° de tour Brimaz posé, détructions, casts Phyrexian suivants, Incubateurs créés et transformés, première attaque menaçante, tenue face aux wipes, gagnant et tour final. Comparer les mêmes adversaires et même politique de mulligan. Il faut faire jouer V4 et V5 avant de conclure.

### Références Oracle en texte complet

- [Vault Skirge](https://mtg.wtf/card?q=%21vault+skirge) — {1}{B/P}, artefact-créature Phyrexian, vol, lien de vie, Commander légal
- [Changeling Outcast (édition Modern Horizons)](https://mtg.wtf/card/mh1/82/Changeling-Outcast) — {B}, changeling, ne peut pas bloquer ou être bloqué
- [Throne of Geth](https://mtg.wtf/card/2xm/301/Throne-of-Geth) — {T}, sacrifiez un artefact : proliférez
- [Myr Sire](https://mtg.wtf/card/cm2/204/Myr-Sire) — Phyrexian Myr, jeton 1/1 Phyrexian Myr à la mort
- [Texte et règles Incubation](https://magic.wizards.com/en/news/feature/march-of-the-machine-release-notes)
