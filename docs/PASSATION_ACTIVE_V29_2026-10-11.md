# V29 — Les vraies options légales à la place d'un recast Brimaz

**11 octobre 2026**, nouvelle branche :
`feature/v29-real-commander-recast-legal-alternatives-20261011`.

## Problème prouvé par les vraies parties

V27, 16 vrais matchs Forge 2.0.15 à quatre IA,
14 fins naturelles / 2 censurées :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38095705276.

- Quatre jeux ont montré des relances répétées de
  Brimaz après sa sortie du champ de bataille.
- Le vrai code `BrimazTurnPlanner.planDevelopment`
  force, quand sa capacité est payable et légalement
  castable, **Brimaz avant les cartes de développement**.
- Cela ne prouve pas que l'ordre est mauvais :
  lancer Brimaz tôt favorise aussi Incubate et les synergies
  phyrexianes. Les autres cartes peuvent même ne pas être
  légalement disponibles au même moment.

## V29, instrument sans changement de choix

Au point exact où Forge a **déjà confirmé la légalité et le
paiement de Brimaz en MAIN1**, le flag désactivé par défaut
`-Dbrimaz.commanderTempoShadow=true` teste
trois alternatives dont le pilote connaissait déjà la
fonction et les contraintes :
`Orzhov Signet`, `Spawning Pit` et
`Krark-Clan Ironworks`.

Chaque alternative est soumise à Forge :
`sa.canPlay()`, `sa.canCastTiming(ai)` et
`ComputerUtilCost.canPayCost(sa,ai,false)`,
**sans jouer ni payer la capacité**. Elle doit en plus
passer le filtre `usefulBlockedSpell` propre à l'ordre
original de développement. Le choix réel retourne
**toujours Brimaz, comme avant**, sans accès à la main
cachée adverse ni modification des règles.

Log V29 :
`FOUR_AI_COMMANDER_TEMPO_SHADOW player=Ai(N)-... 
globalTurn=... life=... greatestVisibleEnemyPower=...
legalEngineAlternatives=N engineNames=... selected=Brimaz`.

Ne pas confondre deux spells chacun payables individuellement
avec la possibilité de payer **les deux ensemble**.

## Validation

- `scripts/patch_forge_brimaz_v13.py` :
  modification observatrice strictement dans le
  constructeur de la politique Brimaz existante ;
- `scripts/audit_v29_commander_tempo.py` :
  compare deux vraies parties par pod/position, même graine,
  un flag désactivé et un flag actif ; classe les situations
  avec alternatives légales et vérifie les événements réels ;
- `tests/test_audit_v29_commander_tempo.py` :
  test de parser explicitement **SYNTHÉTIQUE**, qui
  n'est jamais compté comme une vraie partie ;
- `.github/workflows/four-ai-v29-commander-tempo.yml` :
  deux pods, **4 processus Forge Commander réels**,
  Java21, decks SHA256 canoniques, 420 s maximum par match.

La moindre divergence de déroulement et les timeouts sont
des résultats observés, non une preuve que ce flag améliore
le winrate.

## Prochain test tactique conditionnel

Si le match réel présente effectivement des états où
Brimaz fut choisi malgré une alternative de mana/outlet
légale et payable, construire **alors** une politique
optionnelle (par exemple Orzhov Signet d'abord après
forte pression ou coût de commandant élevé), avec
tests dans le même état public, et pairs A/B.
Si le compteur est zéro : ne pas publier une heuristique
théorique sans occasions.

Tout le moteur reste Forge 2.0.15 réel ; le pilote
Brimaz n'a aucune faveur de règles et les trois
autres IA conservent les mêmes mécanismes.
Ceci n'est pas une certification d'expertise humaine.

Passation principale sur `main/NEXT_CHAT_START_HERE.md`.
