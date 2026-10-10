# REPRISE DU PROJET — LISEZ CE FICHIER D'ABORD

**Date du dernier pointage documentaire : 10 octobre 2026.**
Ce fichier est volontairement present sur `main`, qui n'est **pas** la branche portant les
developpements actuels du simulateur Commander a quatre IA.

## Etat de reference

1. Branche de developpement la plus avancee a cette date :
   `feature/v17-defense-robustness-20261010`.
2. **Passation technique detaillee :**
   [docs/PASSATION_2026-10-10_V17_R1.md sur la branche V16](https://github.com/Toko177/brimaz-forge-lab/blob/feature/v17-defense-robustness-20261010/docs/PASSATION_2026-10-10_V17_R1.md).
3. Pull request en cours : [PR #9](https://github.com/Toko177/brimaz-forge-lab/pull/9).
4. Version de base du laboratoire : `improve/realism-and-ai-diagnostics`
   ([PR #1](https://github.com/Toko177/brimaz-forge-lab/pull/1)).
5. Rapport historique a conserver : `docs/RAPPORT_TRANSFERT_INTEGRAL_2026-10-09.md`.
6. Passation historique tres detaillee : `docs/PASSATION_ACTIVE_2026-10-10.md`.
   Elle precede V14-V16 et doit etre completee par le document V17.1.

## Instructions de reprise dans un futur chat

- **Lire le document V17.1 sur la branche cible**, puis controler l'etat effectif du depot.
  Ne pas supposer que les CI, PR ou SHA sont encore identiques a ceux notes ici.
- Utiliser l'app GitHub connectee pour verifier les branches, commits, PR, Actions,
  journaux et artefacts de parties reelles ; **ne pas se contenter de main**.
- Ne pas fusionner de heuristiques IA sans tests tactiques, parties Forge 2.0.15
  quatre joueurs, audit des fins naturelles et evaluation des censures.
- Le but est d'ameliorer toutes les IA, puis d'evaluer le deck Brimaz V3 legal.
  Aucune victoire simulee, retouche de carte, deck adverse ou regle Magic n'est admise.
- Garder ce pointeur a jour lorsque la branche active change, et mettre a jour la
  passation dans GitHub avant chaque fin de session de developpement.

**Point d'entree pratique :** ouvrir d'abord la PR #9 et le document V17.1 ;
suivre ensuite leurs commits, runs et artefacts les plus recents.

## Point de validation supplementaire

La branche V17 est issue de la V16, qui etait elle-meme issue des developpements V13–V15.
La V17 ajoute le calcul de couverture des bloqueurs pour trois adversaires
et conserve les proprietes Java precedentes (notamment pour revenir a la V16).
Son benchmark Forge utilise le workflow `.github/workflows/four-ai-v17-coverage.yml`.
La PR #9 doit rester en brouillon tant que les resultats tactiques et les
fins de parties naturelles ne sont pas examines.

## Derniere extension V17.1

La PR #9 conserve la politique de couverture stricte de V17 en mode reference,
et teste separement une defense anticipee a 85 % du seuil de defaite avec
cout d'opportunite offensif. Le solveur verifie davantage de restrictions
Forge et sait ameliorer deux menaces letales venant de deux adversaires
differents. La nouvelle campagne de parties doit etre lue avant de conclure.
