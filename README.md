# Brimaz Forge Lab

**Lancer de vraies parties à quatre IA :** [GitHub Actions — Commander simulator](https://github.com/Toko177/brimaz-forge-lab/actions/workflows/commander-four-ai-simulator.yml) · [Guide d'utilisation](docs/HOW_TO_RUN_FOUR_AI_SIMULATOR.md).

**Nouveau pilote V24 :** [Optimisation expérimentale des combats à quatre IA (PR #17)](https://github.com/Toko177/brimaz-forge-lab/pull/17) · [Guide pour lancer les vrais matchs localement sous Windows/Linux](https://github.com/Toko177/brimaz-forge-lab/blob/feature/v24-combat-trigger-fast-negatives-20261011/docs/RUN_LOCAL_4AI_COMMANDER.md). V24 n'est pas validée par un benchmark : nouveaux jobs GitHub bloqués avant allocation de runner.

**Candidate consolidée :** [PR #15 — simulateur Forge réel à quatre IA](https://github.com/Toko177/brimaz-forge-lab/pull/15) (en brouillon, CI et validation du jeu en cours).

**Dernier développement et passation :** [NEXT_CHAT_START_HERE.md](NEXT_CHAT_START_HERE.md), branche expérimentale de contresorts en PR #13 (base V20 PR #12). La branche `main` conserve surtout l'ancienne version du moteur.


> **REPRISE DU PROJET (10 octobre 2026 et après) :**
> ouvrir d'abord [NEXT_CHAT_START_HERE.md](NEXT_CHAT_START_HERE.md) pour
> retrouver la branche active, les PR et la **passation V16**.
> Ce README de la branche main décrit encore surtout V1–V6 ; ne pas prendre
> main pour le moteur IA courant.


Projet : simulation réelle de Magic: The Gathering Commander à **quatre IA Forge 2.0.15**, avec contrôle de légalité des 100 cartes, parallélisation GitHub Actions, audit des décisions IA et certification des parties.

## Point d'entrée pour reprendre le projet

**[Lire le rapport de transmission intégral du 9 octobre 2026](docs/RAPPORT_TRANSFERT_INTEGRAL_2026-10-09.md)** — **447 lignes**, contexte, architecture, scripts, données, chronologie chiffrée, limites, bugs corrigés, V1–V6, première victoire de Brimaz, liens vers les actions et étapes prioritaires.

Documentation spécialisée :
- [Postmortem des 32 parties et première victoire certifiée](docs/canonical-postmortem-and-first-win.md)
- [Règles et critères de validité](docs/realism-protocol.md)
- [Qualité de l'IA et parallélisme](docs/ai-quality-and-parallelism.md)
- [Architecture du futur lookahead à quatre joueurs](docs/multiplayer-lookahead-roadmap.md)

## Résultat actuel à ne pas mal interpréter

- 32 parties canoniques avant correction moteur : 29 naturelles certifiées, 3 censurées ; Brimaz 0/29.
- Correction ciblée du bug Forge `CharmEffect`, puis **une première victoire de Brimaz** sur graine de régression, tour 24, 356,476 secondes, trois adversaires éliminés : [certification](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37969492744).
- Cette victoire ne mesure pas encore le taux de victoire du deck ; la priorité reste la qualité du pilotage IA et l'audit des règles.
- V5/V6 sont des pilotes d'amélioration de l'IA, sans gain de winrate démontré.
