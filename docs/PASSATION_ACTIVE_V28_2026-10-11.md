# V28 — Profilage des propriétés de cartes, règles Forge inchangées

**11 octobre 2026**, branche
`feature/v28-real-card-property-hotpath-profile-20261011`,
sur la V27, V26, V25, V24.

## La découverte JFR qui motive ce pilote

Run Java Flight Recorder réel :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38094816646
et affichage :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38095235384.

Une partie réelle Commander Forge 2.0.15 à quatre IA,
Aristocrates rotation 1, a fini naturellement en 305,55 s
avec deux timeouts `Ai(3)` au combat. Dans les
**échantillons de méthodes exécutées**, les plus présents sont :

| Méthode Java | Échantillons | Part descriptive |
|---|---:|---:|
| `CardProperty.cardHasProperty` | 11 059 | **46,18 %** |
| `FCollection.addAll` | 851 | 3,55 % |
| `CardState.getStaticAbilities` | 601 | 2,51 % |
| `Card.updateStaticAbilities` | 524 | 2,19 % |

Ces parts sont des **échantillons JFR d'une seule partie**,
pas une mesure exacte des temps exclusifs de CPU dans toutes
les parties Forge. Mais elles révèlent que les propriétés de
cartes et les contrôles de combat dominent cet exemple réel,
bien plus que la simple sélection de cible V19.

## V28 : ajout de télémétrie, aucun raccourci

- `scripts/patch_forge_card_property_profile.py`
  compile le source ORIGINAL au tag `forge-2.0.15` de
  `forge.game.card.CardProperty`, insérant **seulement** un
  appel d'observation avant son corps, sans modifier
  une seule branche de résultat ou règle Magic.
- `patches/java/forge/game/card/CardPropertyQueryProfiler.java`
  est un observateur concurrentsafe `LongAdder` et
  `ConcurrentHashMap`, limité à 256 libellés pour
  éviter le stockage non borné. Il est OFF par défaut ;
  flag `-Dbrimaz.profilePropertyQueries=true`.
  Émet à la fin de JVM `FOUR_AI_PROPERTY_PROFILE_TOTAL`
  et les 40 propriétés les plus interrogées
  (`FOUR_AI_PROPERTY_TOP calls=N property=...`).
  Un libellé de plus de 80 caractères est tronqué.
- `tests/java/forge/game/card/CardPropertyQueryProfilerChecks.java`
  teste l'activation opt-in et l'exactitude des compteurs.
- `.github/workflows/v28-property-query-profile.yml`
  lance un **vrai match Commander à 4 IA et 7 decks
  vérifiés SHA256** pour compter ces appels sans
  utiliser de jeu proxy. Les résultats d'une partie
  instrumentée ne constituent **pas un benchmark de
  vitesse** comparé à une partie sans observateur.

## Conditions d'adoption d'une FUTURE optimisation

Ne pas ajouter de cache général pour
`CardProperty.cardHasProperty` :
le résultat peut changer avec les LKI, les zones,
les capacités statiques, les compteurs, les sorts sur
pile et les changements de contrôleur. Les
retours de la fonction définissent des règles Magic
réelles, contrairement au prédicteur hypothétique
`ComputerUtilCombat` optimisé par V24.

Identifier d'abord, par l'instrumentation V28,
les chaînes `property` les plus fréquentes et
isoler éventuellement des fast paths sémantiquement
**identiques** pour des cas documentés.
Exiger tests Oracle adversariaux, comparaison des
journaux d'actions réels, zones, dégâts, seuils
de vie, et partie naturelle — puis généralisation
seulement si bénéfice prouvé.

**Pointeur de reprise :** `NEXT_CHAT_START_HERE.md`
sur `main` et [passation V27](PASSATION_ACTIVE_V27_2026-10-11.md).
