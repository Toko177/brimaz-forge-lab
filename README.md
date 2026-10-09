# Brimaz Forge Lab

Projet : simulation réelle de Magic: The Gathering Commander à **quatre IA Forge 2.0.15**, avec contrôle de légalité des 100 cartes, parallélisation GitHub Actions, audit des décisions IA et certification des parties.

## Point d'entrée pour reprendre le projet

**[Lire le rapport de transmission intégral du 9 octobre 2026](docs/RAPPORT_TRANSFERT_INTEGRAL_2026-10-09.md)** — **447 lignes**, contexte, architecture, scripts, données, chronologie chiffrée, limites, bugs corrigés, V1–V6, première victoire de Brimaz, liens vers les actions et étapes prioritaires.

Documentation spécialisée :
- [Postmortem des 32 parties et première victoire certifiée](docs/canonical-postmortem-and-first-win.md)
- [Règles et critères de validité](docs/realism-protocol.md)
- [Qualité de l'IA et parallélisme](docs/ai-quality-and-parallelism.md)
- [Architecture du futur lookahead à quatre joueurs](docs/multiplayer-lookahead-roadmap.md)

## Mise à jour du 9 octobre 2026 : victoire historique non reproduite

**Attention :** la première victoire Brimaz (seed `20291010`, seuil moteur 360 s)
a satisfait la certification de sortie naturelle et de légalité, mais une
relecture avec seuil 900 s, IA Forge Default, mêmes cartes et sièges, a donné
**Radha vainqueur** (437 493 ms). La première divergence est au tour Forge 33,
sur un choix de donjon effectué par une IA adverse. L'horloge seule n'est
pas une cause démontrée ; la seed Forge n'assure pas ici une trace déterministe.
Ne pas compter la victoire historique comme résultat reproduit ni comme
preuve de performance de Brimaz.

[Comparaison forensique des journaux](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37994894861).
[V7 observateur : 4 parties certifiées, 0 victoire Brimaz](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37992540124).
V8 expérimente des transformations défensives d'Incubateurs, toujours
sous le moteur de règles Forge.

## Résultat actuel à ne pas mal interpréter

- 32 parties canoniques avant correction moteur : 29 naturelles certifiées, 3 censurées ; Brimaz 0/29.
- Correction ciblée du bug Forge `CharmEffect`, puis **une première victoire de Brimaz** sur graine de régression, tour 24, 356,476 secondes, trois adversaires éliminés : [certification](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37969492744).
- Cette victoire ne mesure pas encore le taux de victoire du deck ; la priorité reste la qualité du pilotage IA et l'audit des règles.
- V5/V6 sont des pilotes d'amélioration de l'IA, sans gain de winrate démontré.
