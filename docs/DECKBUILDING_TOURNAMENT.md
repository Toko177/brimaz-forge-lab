# Commander — tournoi multivariantes et comparaison fiable

## Objectif

Comparer **2 à 8 changements de cartes dans une même campagne Forge**, en
réutilisant **une seule référence commune** au lieu de rejouer la même
liste pour chaque candidat. Ce mécanisme s'ajoute au comparateur
[A/B individuel](DECKBUILDING_QUICKSTART.md) ; il ne crée ni nouvelle
version du moteur Magic, ni IA donnant des victoires fictives.

### Mode d'emploi

Éditer [\`decks/tournament-experiments.json\`](../decks/tournament-experiments.json)
sur la branche expérimentale :

\`\`\`json
{
  "variants": [
    {"id": "mana-fix", "swaps": "1 Plains -> 1 Shadowy Backstreet"},
    {"id": "fetchland", "swaps": "1 Swamp -> 1 Fabled Passage"}
  ]
}
\`\`\`

Les deux substitutions ci-dessus sont **des hypothèses de tests
expérimentaux**, pas des recommandations de deck final. Le canonique
\`decks/Brimaz_V3.txt\` n'est jamais modifié. Chaque \`id\` doit être
unique ; les candidats avec mêmes 100 cartes sont rejetés.

Un commit de ce fichier sur la branche
\`improve/realism-and-ai-diagnostics\` lance
[\`deckbuild-tournament.yml\`](../.github/workflows/deckbuild-tournament.yml).
Le lancement manuel (lorsque le workflow est visible sur la branche
GitHub par défaut) accepte le chemin d'un JSON différent et
\`repeats=1,2,4\`.

Chaque recette doit préserver les 100 cartes, le commandant déclaré
et le nombre de cartes remplacées. Scryfall vérifie ensuite
chaque véritable liste contre les règles Commander (et l'absence
de Game Changers selon la politique actuelle). La validation
Scryfall se fait avant le moindre jeu Forge ; le rapport
\`preflight.json\` compare déjà courbe de mana, terrains et MDFC.

### Économie de véritables parties

Pour \`N\` candidats (N de 2 à 8) et une répétition par
pod/siège :

| Plan | Parties réellement programmées |
|---|---:|
| Comparateurs A/B individuels, sans cache | 16 × N |
| Tournoi commun, référence non encore disponible | **8 + 8 × N** |
| Tournoi avec référence d'une campagne compatible déjà disponible | **8 × N** |

À 4 candidats, cela représente 64, 40 ou 32 parties respectivement.
Chaque jeu inclut réellement **4 joueurs IA Forge**, 100 cartes et
les deux pods adverses historiques, en faisant varier les 4 sièges.
L'exécution s'effectue sur jusqu'à **16 runners GitHub Actions
en parallèle**, sans fusionner les adversaires ni modifier les règles.

Une campagne à \`repeats=2\` ou \`repeats=4\` multiplie
proportionnellement les parties et le coût. La légalité et les logs
ne sont contrôlés qu'une fois par partie.

### Conservation du résultat et garanties

L'artefact \`commander-multivariant-certified-ranking\`
contient, pour chaque candidat :
- \`certificate.json\` : Scryfall, SHA256 du deck, résultat naturel
  four player, les modes de pertes, les parties censurées et les
  anomalies IA ;
- \`comparison.json\` : vrai taux de victoire conditionnel,
  Wilson 95 %, répartition par pod/siège, jeu comparé, et empreinte
  de tous les journaux de référence ;
- \`ranking.json\` et \`ranking.md\` : classement de présélection
  uniquement, construit **si et seulement si tous les candidats
  ont les mêmes SHA256 de parties de référence** ;
- \`preflight.json\` archivé lors de la préparation, basé sur
  Scryfall actuel.

Les vrais logs originaux sont conservés dans chaque artefact de jeu.
\`scripts/deckbuild_tournament.py assemble\` vérifie les 8 groupes
baseline uniques, chaque bras, pod, siège, graine, politique IA,
deck SHA256 et **CHAQUE transcript SHA256 avant de produire les
bundles A/B**. Une absence de jeu, un log modifié ou un candidat
dupliqué provoque un échec explicite.

Quand une référence d'un run antérieur possède une attestation
complète strictement identique (Forge + patchs + Scryfall + decks
+ seeds + pods + sièges + clock + profils), elle peut être téléchargée
et **recertifiée** au lieu d'être rejouée ; aucune partie censurée ne
devient victoire. Son taux de victoire n'est jamais décompté comme
un échantillon indépendant supplémentaire lors du classement des
autres candidats.

### Interprétation

Ces campagnes sont des outils de **screening**. Même si une variante
gagne 2/8 contre 0/8 pour une autre, cela ne démontre ni qu'elle
est meilleure chez les humains ni qu'elle gagne sur un nouvel
ensemble de graines. Plus de candidats sont testés, plus la
probabilité de faux gagnant augmente. Confirmer les plus prometteurs
sur **de nouvelles graines indépendantes**, avec davantage de
parties et des contrôles d'IA. Une IA sans timeout n'est pas
automatiquement une IA compétente.

L'IA V13 actuelle sait envisager Incubate et dispose d'un budget
de réflexion adaptatif pour les quatre joueurs ; elle reste
limitée dans les choix de combats complexes. Le tournoi n'ajoute
pas de raccourci illégal ni de moteur de combat approximatif.

### Implémentation

- \`scripts/deckbuild_tournament.py\` :
  \`prepare\` sérialise les variantes avec SHA256 de la liste,
  \`assemble\` contrôle le plan de jeux réel et construit
  des bundles de certificats.
- \`tests/test_deckbuild_tournament.py\` :
  vérifie 2 candidats, partage d'une seule référence, absence
  de mutation du deck canonique, détection de listes identiques,
  rejets des logs falsifiés et refus des shards manquants.
- \`.github/workflows/deckbuild-tournament.yml\` :
  validation Scryfall, matrice Forge partagée et rapports certifiés.

Pour reprendre le contexte technique intégral :
[PASSATION ACTIVE](PASSATION_ACTIVE_2026-10-10.md).
