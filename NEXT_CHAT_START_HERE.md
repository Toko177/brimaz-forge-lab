# REPRISE DU PROJET — LISEZ CE FICHIER D'ABORD

**Date du dernier pointage documentaire : 10 octobre 2026.**
Ce fichier est volontairement present sur `main`, qui n'est **pas** la branche portant les
developpements actuels du simulateur Commander a quatre IA.

## Etat de reference

1. Branche de developpement la plus avancee a cette date :
   `feature/v16-multiplayer-defense-and-handoff-20261010`.
2. **Passation technique detaillee :**
   [docs/PASSATION_2026-10-10_V16.md sur la branche V16](https://github.com/Toko177/brimaz-forge-lab/blob/feature/v16-multiplayer-defense-and-handoff-20261010/docs/PASSATION_2026-10-10_V16.md).
3. Pull request en cours : [PR #7](https://github.com/Toko177/brimaz-forge-lab/pull/7).
4. Version de base du laboratoire : `improve/realism-and-ai-diagnostics`
   ([PR #1](https://github.com/Toko177/brimaz-forge-lab/pull/1)).
5. Rapport historique a conserver : `docs/RAPPORT_TRANSFERT_INTEGRAL_2026-10-09.md`.
6. Passation historique tres detaillee : `docs/PASSATION_ACTIVE_2026-10-10.md`.
   Elle precede V14-V16 et doit etre completee par le document V16.

## Instructions de reprise dans un futur chat

- **Lire le document V16 sur la branche cible**, puis controler l'etat effectif du depot.
  Ne pas supposer que les CI, PR ou SHA sont encore identiques a ceux notes ici.
- Utiliser l'app GitHub connectee pour verifier les branches, commits, PR, Actions,
  journaux et artefacts de parties reelles ; **ne pas se contenter de main**.
- Ne pas fusionner de heuristiques IA sans tests tactiques, parties Forge 2.0.15
  quatre joueurs, audit des fins naturelles et evaluation des censures.
- Le but est d'ameliorer toutes les IA, puis d'evaluer le deck Brimaz V3 legal.
  Aucune victoire simulee, retouche de carte, deck adverse ou regle Magic n'est admise.
- Garder ce pointeur a jour lorsque la branche active change, et mettre a jour la
  passation dans GitHub avant chaque fin de session de developpement.

**Point d'entree pratique :** ouvrir d'abord la PR #7 et le document V16 ;
suivre ensuite leurs commits, runs et artefacts les plus recents.
