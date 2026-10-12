# Groupes Commander actifs — 12 octobre 2026

## Décision : retirer Amalia des simulations actives

La demande est de **remplacer Amalia par un autre deck déjà présent**,
sans supprimer ni altérer les sept listes Commander canoniques.
Le remplaçant retenu est **Dungeon Party Time** (`Kaal_10347090`).
Son fichier existe déjà dans `forge_decks/`; les règles MTG, son
commandant, les 100 cartes et les SHA256 des sept decks restent inchangés.

| Groupe | Quatre sièges (avant rotation) | Modification |
|---|---|---|
| Aristocrats | Brimaz V3 · Radha · Dungeon Party Time · Zimone et Dina | Identique |
| Artifact | Brimaz V3 · Lathril · Urza · Dungeon Party Time | Amalia remplacée |

La liste historique Amalia (`Kaal_22193355`) demeure versionnée et
vérifiée par SHA256 mais n'est **plus lancée dans les groupes actifs**.

### Limite de couverture

Il reste cinq decks Kaal distincts dans les groupes actifs pour six
places adverses sur deux pods. Dungeon Party Time figure donc
**deux fois entre les pods**, jamais deux fois dans la même partie.
Cela modifie la pondération des archétypes : un résultat global ne
représente **pas** six adversaires indépendants. Rapporter
systématiquement le taux par pod, par siège, par commandant et le
taux de parties censurées. Ne pas présenter les deux confrontations
Dungeon comme deux archétypes indépendants.

### Source de vérité unique et prévention des mélanges

- `scripts/commander_pods.py` contient `PODS` et `OPPONENTS`,
  lus respectivement par `scripts/batch.py` et
  `scripts/deckbuild_run.py`. Ne plus maintenir deux listes copiées.
- `scripts/run_local_four_ai.py` écrit la version et les quatre
  decks de chaque pod dans le manifeste de provenance de la campagne.
- `scripts/compare_local_four_ai_campaigns.py` refuse une comparaison
  avec un roster différent ou une rotation de sièges incohérente.
- `scripts/deckbuild_cache.py` incorpore la version et le contenu
  de la configuration des pods dans les empreintes de cache ; les
  archives avec Amalia restent dans l'historique, mais une référence
  calculée avec l'ancien groupe ne peut pas servir au nouveau.
- `tests/test_commander_pods.py`,
  `tests/test_compare_local_four_ai_campaigns.py` et
  `tests/test_deckbuild_cache.py` contrôlent l'isolation, la
  présence des 7 decks inchangés et le refus de mélanges de groupes.

### Benchmarks

Les séries publiées **avant ce changement** utilisaient Amalia et
gardent leur composition originale. Ne pas réécrire ni réattribuer
leurs vainqueurs. Les prochaines campagnes auront de nouveaux logs,
provenances et SHA256, et devront être comparées uniquement à un
témoin exécuté sur la **même nouvelle composition**. Le mode
`v43_commander_single_seat` reste le comparateur pertinent pour
juger une nouvelle politique : un seul siège expérimental, trois
joueurs sous Forge, quatre rotations, vrais coûts et actions Forge.
Aucun gain de qualité de jeu n'est présumé du changement de deck.

### Points de contrôle opérationnels

```sh
python3 tests/test_commander_pods.py
python3 tests/test_run_local_four_ai.py
python3 tests/test_deckbuild_cache.py
python3 tests/test_compare_local_four_ai_campaigns.py
python3 tests/test_repository_structure.py
```

Historique conservé, une seule PR expérimentale ouverte,
aucun changement de `main` sans revue et résultats valides.


### Rapport V43 stratifié (extension d'audit)

L'auditeur `scripts/audit_v42_generic_commander.py` expose désormais
`roster_version`, `shared_opponents_across_pods` et `by_pod`
(nombres de paires, fins naturelles, censures, victoires
**uniquement** du candidat ou de la référence). Il refuse un résultat
où les métadonnées de roster diffèrent entre expérience et témoin.
Ce n'est pas une preuve de supériorité de l'IA : les intervalles
et nouvelles cohortes de vrais matchs restent nécessaires.
