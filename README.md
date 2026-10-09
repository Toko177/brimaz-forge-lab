# Brimaz Forge Lab

Projet : simulation réelle de Magic: The Gathering Commander à **quatre IA Forge 2.0.15**, avec contrôle de légalité des 100 cartes, parallélisation GitHub Actions, audit des décisions IA et certification des parties.

## Point d'entrée pour reprendre le projet

**[PASSATION ACTIVE — état post-V8, V9, CI, limites et prochaines actions](docs/PASSATION_ACTIVE_2026-10-10.md)** — à consulter en premier lors d'un nouveau chat. Informations vérifiées, liens GitHub Actions, scripts, contrôles de règles, historique non reproductible et protocole de continuation.

**[Lire le rapport de transmission intégral du 9 octobre 2026](docs/RAPPORT_TRANSFERT_INTEGRAL_2026-10-09.md)** — **447 lignes**, contexte, architecture, scripts, données, chronologie chiffrée, limites, bugs corrigés, V1–V6, première victoire de Brimaz, liens vers les actions et étapes prioritaires.

Documentation spécialisée :
- [Postmortem des 32 parties et victoire historique non reproduite](docs/canonical-postmortem-and-first-win.md)
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
- Correction ciblée du bug Forge `CharmEffect`, puis **une victoire Brimaz historique non reproduite** sur graine de régression, à 356,476 secondes : [résultat d'origine](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37969492744) et [replay divergent à 900 secondes](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37994894861).
- Cette victoire ne mesure pas encore le taux de victoire du deck ; la priorité reste la qualité du pilotage IA et l'audit des règles.
- V5/V6 sont des pilotes d'amélioration de l'IA, sans gain de winrate démontré.

## Développement post-V8

- [Calibration des tours personnels et des ouvertures Commander](docs/EDH_EMPIRICAL_PACING_AND_AI_CALIBRATION.md) : 4 parties V8, 2 sorties mana faibles, médiane 13 tours du joueur le plus actif, face à 9 rotations médianes humaines.
- [Audit des parties réelles V8](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37997796527) : 5 tests réussis, 4/4 parties naturelles.
- [V9 — choix de mulligan prudent propre à Brimaz](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37998385269) : tests et parties pilotes, vérifier les logs avant de conclure à un gain.
- **Ne pas confondre qualité des règles, qualité de l'IA et taux de victoire.** N'importe laquelle de ces dimensions peut invalider une mesure de winrate.
