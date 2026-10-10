# Simulateur Commander quatre IA — guide de lancement

**Mis à jour le 10 octobre 2026.**
Ce guide décrit l'exécution d'un vrai moteur de règles **Forge 2.0.15 /
Java 21**. Ce n'est pas un simulateur simplifié ou une estimation
Monte-Carlo sans jeu réel.

## 1. Lancer une campagne

Sur GitHub :

1. Ouvrir [Actions](https://github.com/Toko177/brimaz-forge-lab/actions).
2. Choisir **Commander simulator — run 4 AI games**.
3. Cliquer **Run workflow** sur la branche par défaut `main`.
4. Garder le `source_ref` de la branche active indiquée dans
   [NEXT_CHAT_START_HERE.md](../NEXT_CHAT_START_HERE.md).
5. Choisir le pod, le niveau de politique et le nombre de parties par rotation.

Le workflow est installé sur `main`, mais récupère le **code du simulateur**
sur `source_ref`. Ceci permet de conserver un lanceur stable pendant que le
moteur et les tests évoluent dans des branches de développement.

## 2. Paramètres

| Entrée | Choix | Effet |
|---|---|---|
| `source_ref` | nom de la branche | code Forge patché + scripts analysés |
| `pod` | `both`, `aristo`, `artifact` | adversaires présents |
| `policy` | `v15`, `v16`, `v17_strict`, `v17_proactive`, `v19_removal` | heuristiques partagées par les quatre IA ; V19 expérimentale cible les menaces adverses |
| `games_per_rotation` | 1, 2, 3 ou 5 | processus Forge indépendants, chacun à 4 joueurs |
| `seed_base` | entier positif | graine de référence, dérivée pour chaque siège et répétition |

**Exemple pour un test rapide :** `pod=both`, `policy=v17_strict`,
`games_per_rotation=1` donne **8 parties réelles** réparties sur
8 jobs (2 pods × 4 rotations, une partie par job).

**Exemple pour une première campagne plus large :**
`pod=both`, `games_per_rotation=5` donne **40 parties réelles**,
chaque partie exécutée dans un JVM distinct.
Ce sont des processus réels ; le nombre d'heures de calcul dépend
des durées observées et des files de jobs GitHub.

Le workflow fixe initialement une horloge de partie Forge de **360 s**
et une limite de processus de **445 s**. Les parties interrompues par
l'horloge sont classées comme **censurées**, pas comme défaites/victoires.


### Option V19 : choix des anti-créatures (expérimentale)

Avec `source_ref=feature/v19-opponent-removal-urgency-20261010`,
`policy=v19_removal` ajoute un bonus à certaines **cibles de retrait déjà
légales** dont les dégâts publics présentent un risque de défaite
prochainement (vie, poison, blessures d'un commandant précis).
Aucune carte adverse ni règle Magic n'est modifiée. Les évaluations
`FOUR_AI_REMOVAL_URGENCY` dans les journaux **ne signifient pas**
qu'un retrait a réellement été lancé. Ce mode reste expérimental
et doit être comparé à `v17_strict` sur des parties certifiées.

## 3. Contrôles automatiques

Chaque job :
- vérifie l'empreinte SHA256 des sept listes de cartes canoniques ;
- installe ou retrouve l'archive Forge officielle épinglée ;
- applique les correctifs Charm + V13 et les stratégies IA opt-in ;
- lance la simulation Forge en format Commander avec quatre IA ;
- archive les journaux complets et un `games.json` par job ;
- produit `four_seat_actions.json` et `four_seat_summary.md`,
  avec sorts joués, phases, attaques, blessures reçues/infligées,
  pertes de permanents attribuables et décisions lentes ;
- archive le SHA Git, SHA du JAR modifié et la politique choisie.

Les artefacts se trouvent dans le **run Actions → Artifacts**, sous
`commander-4ai-<run>-<pod>-rotation<N>`. Ils sont conservés
**30 jours** ; récupérer ou réarchiver les résultats importants pour
les conserver au-delà de la politique GitHub de rétention.

## 4. Limites : un résultat de Forge n'est pas automatiquement un winrate

Les logs décrivent les actions réellement produites par Forge.
Les modules d'audit signalent les écarts manifestes, mais la
**certification de légalité et de fin naturelle** reste une étape
indépendante (script `scripts/certify_commander_games.py`, avec le
rapport de légalité Scryfall, à réunir après les runs).

Pour interpréter les résultats :
- calculer les victoires **uniquement sur parties naturelles certifiées** ;
- conserver toutes les parties censurées et les erreurs moteur ;
- diversifier seeds, rotations et pods ; une graine identique ne
  garantit pas une trajectoire identique en présence de délais IA ;
- distinguer **performance de simulation**, **qualité de décision**,
  **niveau des decks** et **résolution fidèle des règles** ;
- ne jamais considérer un succès CI comme une preuve d'IA experte.

Le benchmark scientifique des différentes politiques reste dans les
PR et [la passation active](../NEXT_CHAT_START_HERE.md). Le lanceur
manuel sert à générer des parties réelles sans modifier le code.

## 5. Résultats de référence disponibles

- [V17 huit parties naturelles à quatre IA](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38081333961)
- [V17.1 strict/proactif, huit parties naturelles](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38082154931)
- [V18 analyse des journaux de huit vraies parties](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38082918169)

Pour un futur chat : ouvrir d'abord [NEXT_CHAT_START_HERE.md](../NEXT_CHAT_START_HERE.md)
puis la passation sur la branche active ; vérifier les derniers commits et
runs plutôt que supposer cette documentation à jour.

