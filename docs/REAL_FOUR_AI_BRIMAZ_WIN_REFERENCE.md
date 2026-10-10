# Référence de vraie victoire Brimaz dans Forge Commander (quatre IA)

**10 octobre 2026** — cas empirique de régression et de gameplay,
**pas** estimation de taux de victoire. Les données proviennent du
vrai moteur **Forge 2.0.15 / Java 21** avec quatre sièges IA et les
7 listes de cartes canoniques normalisées et vérifiées SHA256.

## Match et preuve

- Workflow : https://github.com/Toko177/brimaz-forge-lab/actions/runs/38089750692
- Artefact : `brimaz-v13-incubate-adaptive-artifact-r2`.
- Pod : `artifact`, rotation 2, `repeat=1`.
- Graine Forge : **20830001** ; politique `V13-incubate-adaptive`,
  quatre profils IA `Default`.
- Sièges :
  1. EDH Urza (`Kaal_11485202`),
  2. EDH Amalia (`Kaal_22193355`),
  3. **Brimaz V3**,
  4. EDH Lathril (`Kaal_23328062`).
- Résultat brut :
  `Game Result: Game 1 ended in 78474 ms. Ai(3)-Brimaz V3 has won!`.
- Journal `Game Outcome:` : Urza, Amalia et Lathril ont
  **chacun perdu parce que leurs points de vie sont arrivés à zéro** ;
  Brimaz gagnant car tous les adversaires ont perdu.
- Temps de partie rapporté dans le jeu : **1 min 16 s**.
- Pas de `AI_EVAL_TIMEOUT_V10` observé dans cette partie.

## Décisions et synergies réellement présentes dans les événements

Le journal contient notamment des sorts ou effets activés par
Brimaz :
- `Brimaz, Blight of Oreskos` et création/activation
  d'`Incubator Token` ;
- `Mirkwood Bats` (multiples capacités déclenchées) ;
- `Essence of Orthodoxy` et `Metastatic Evangel` ;
- `Vraan, Executioner Thane`, `Grafted Butcher`,
  `Lurrus of the Dream-Den` et
  `Athreos, God of Passage`.

Les actions de combat du journal font apparaître plusieurs
attaques de Brimaz avec des jetons phyrexians, Brimaz, Athreos,
Mirkwood Bats et d'autres créatures. Le moteur a réellement
résolu les pertes de vie et les éliminations.

**Ne pas inventer une causalité précise** du genre « Mirkwood Bats
a tué les trois joueurs » : ces lignes prouvent la présence et le
déclenchement de l'effet, mais une analyse détaillée des changements
de points de vie et des capacités sur pile serait nécessaire pour
attribuer précisément chaque dégât.

## Usage comme régression future

C'est un **point de contrôle de fonctionnement**, pas un test
déterministe de garantie de victoire. Forge peut produire des
trajectoires différentes avec la même graine selon les timings IA
et les changements de code.

Pour une nouvelle politique sur le simulateur :
1. exécuter `artifact`, rotation 2, `seed_base=20810001`
   (car `batch.py` ajoute `10000*rotation`), une partie réelle ;
2. comparer les éléments de développement phyrexian / Incubate,
   les sorts lancés, les événements de combat et les issues naturelles ;
3. ne pas considérer une défaite dans cette nouvelle exécution comme
   une preuve de régression sans avoir vérifié l'état et les actions
   à décision égale ;
4. conserver toutes les censures, erreurs de moteur, empreintes des
   logs et métadonnées du patch appliqué.

Le pilote V23 tente de réduire les délais sur des parties lentes ;
**son objectif n'est pas de fabriquer une victoire Brimaz**.
La référence de réussite et la référence de défaillance (V22
censurée à 360 s) doivent toutes les deux rester dans le corpus.

Les autres preuves et notes :
[point de reprise permanent](../NEXT_CHAT_START_HERE.md) et
[PR #16 V23](https://github.com/Toko177/brimaz-forge-lab/pull/16).

