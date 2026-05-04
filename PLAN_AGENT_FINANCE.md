# Plan complet — Agent IA de suivi d'actions financières (avec Codex)

## 1) Résumé du projet
Cet agent IA a pour but d'aider un utilisateur à **suivre une liste d'actions**, à **agréger des données fiables**, puis à produire un **résumé clair et actionnable** (informatif uniquement).

### Ce que l'agent fera
- Prendre une liste de tickers (ex: `AAPL`, `MSFT`, `AIR.PA`) en entrée.
- Récupérer automatiquement : cours, variation, historique court terme, actualités, publications de résultats, indicateurs clés, sentiment de marché.
- Générer un rapport lisible : faits, signaux, incertitudes, points de vigilance.
- Évaluer la qualité de ses propres réponses (tests + score).
- S'auto-améliorer via des recommandations techniques et métier.

### Usage cible
- Suivi personnel et éducatif.
- Veille régulière d'un portefeuille.
- Support à la décision **sans conseil financier professionnel**.

### Limites
- Pas de recommandation d'achat/vente définitive.
- Dépendance à la qualité/latence des API externes.
- Risque d'informations incomplètes en cas d'indisponibilité des sources.

---

## 2) Architecture générale
Architecture simple (V1) puis extensible.

### Composants
1. **Interface utilisateur**
   - CLI au départ (`python -m src.main --tickers AAPL,MSFT`).
   - Option future : dashboard web.

2. **Moteur agent IA (orchestrateur)**
   - Coordonne les modules : collecte -> validation -> analyse -> résumé -> scoring.
   - Gère les retries, timeouts, fallback et journalisation.

3. **Module récupération des données**
   - Connecteurs API marchés/prix.
   - Connecteurs news/earnings/fundamentaux.
   - Contrôle de fraîcheur (timestamp) et qualité de source.

4. **Module d'analyse**
   - Calculs de variations, volatilité simple, comparaison période courte.
   - Extraction d'événements significatifs (news/résultats).
   - Détection d'incertitude (données manquantes/anciennes).

5. **Module de résumé**
   - Génération structurée : “Faits”, “Interprétation prudente”, “Incertitudes”, “À surveiller”.
   - Inclusion automatique du disclaimer non-conseil financier.

6. **Module de test automatique**
   - Tests unitaires + intégration + qualité de texte.
   - Vérifie l'absence d'hallucinations factuelles.

7. **Module de notation**
   - Score /100 avec grille pondérée (précision, clarté, conformité, robustesse).

8. **Module recommandations d'amélioration**
   - Analyse les échecs de tests et baisse de score.
   - Propose backlog priorisé (quick wins / moyen terme).

9. **Stockage**
   - SQLite pour V1 (runs, scores, métadonnées, cache API).
   - Stockage chiffré des secrets via variables d'environnement + vault (phase avancée).

---

## 3) Plan de build étape par étape

## Phase 1 — Cadrage du projet
- Définir périmètre V1 (CLI + 3 à 10 tickers + rapport texte/markdown).
- Définir persona utilisateur et fréquence d'usage (quotidien/hebdo).
- Définir KPI de succès :
  - Taux de réponses complètes > 95%.
  - Temps de génération < 20 sec pour 5 tickers.
  - Score qualité > 80/100.
- Définir exigences non fonctionnelles : sécurité, observabilité, maintenabilité.

## Phase 2 — Choix des sources de données/API
- Sélectionner 1 source principale + 1 source de secours par type de données.
- Exemples de catégories de fournisseurs :
  - Prix/market data,
  - News financières,
  - Fundamentals/earnings,
  - Sentiment (news/social agrégé).
- Critères de choix : couverture, SLA, coût, latence, limites de quota, licence.
- Définir politique de fiabilité :
  - `source_rank`,
  - validation croisée minimale,
  - marquage “incertain/ancien”.

## Phase 3 — Création de la structure du projet
- Initialiser repo Python (`pyproject.toml`, `src/`, `tests/`).
- Ajouter lint/format/type-check (ruff, black, mypy).
- Mettre en place logs structurés + configuration centralisée.
- Préparer fichiers `.env.example` et policy de secrets.

## Phase 4 — Développement du module de récupération
- Implémenter `DataProvider` abstrait.
- Créer connecteurs API (prix/news/fundamentaux).
- Gérer erreurs réseau, backoff, retry, quota, timeout.
- Normaliser les données vers un schéma unique.
- Ajouter cache local (TTL configurable).

## Phase 5 — Développement du module d'analyse
- Calculer métriques : variation J, variation 5j, volatilité simple.
- Détecter signaux : gap, news majeure, publication de résultats.
- Produire une analyse prudente avec niveaux de confiance.
- Bloquer explicitement les formulations de conseil ferme.

## Phase 6 — Génération des rapports
- Template markdown/JSON standard.
- Sections : résumé exécutif, détails ticker par ticker, risques/incertitudes.
- Ajouter traces de provenance : source + timestamp + fraîcheur.
- Export vers `reports/YYYY-MM-DD/`.

## Phase 7 — Système de test automatique
- Unit tests sur parsing/normalisation/calculs.
- Intégration sur pipeline complet avec mocks API.
- Tests de robustesse (API down, données manquantes, ticker invalide).
- Tests de conformité linguistique (présence disclaimer, absence conseil impératif).

## Phase 8 — Système de notation
- Implémenter `ScoringEngine` (/100).
- Calcul par critères pondérés (voir section 9).
- Conserver historique des scores et tendances.

## Phase 9 — Conseils d'amélioration générés par l'IA
- Générer recommandations à partir :
  - scores faibles,
  - tests en échec,
  - latence excessive,
  - sources instables.
- Produire plan d'action priorisé avec effort/impact.

## Phase 10 — Tests finaux et optimisation
- Test de charge léger (N tickers, runs répétés).
- Optimiser cache, parallélisation contrôlée, prompts.
- Revue sécurité (secrets, logs, données personnelles).
- Préparer release v1.0 + documentation d'exploitation.

---

## 4) Prompts à utiliser dans Codex (copier-coller)

### Phase 1 — Cadrage
"Crée un document de cadrage pour un agent IA de suivi d'actions en Python. Inclus objectifs, non-objectifs, KPI (qualité, latence, fiabilité), contraintes légales (pas de conseil financier), et backlog MVP sur 2 semaines."

### Phase 2 — APIs
"Propose une interface `MarketDataProvider` et une matrice de décision pour choisir des APIs de prix, news et fondamentaux. Ajoute critères coût, couverture, quotas, latence, SLA et stratégie fallback."

### Phase 3 — Skeleton projet
"Scaffold un projet Python propre avec `src/`, `tests/`, `config/`, `reports/`, `data/`, `pyproject.toml`, `ruff`, `black`, `mypy`, `pytest`, logging structuré, et `.env.example`."

### Phase 4 — Collecte des données
"Implémente un module `data_ingestion` avec un provider abstrait + un provider concret mocké. Ajoute retry exponentiel, timeout, gestion d'erreurs, cache TTL, et normalisation en dataclasses Pydantic."

### Phase 5 — Analyse
"Implémente `analysis_engine` pour calculer variation journalière, variation 5 jours, volatilité simple et signaux événementiels. Retourne aussi un `confidence_score` et un champ `limitations`."

### Phase 6 — Rapport
"Crée `report_generator` qui produit un rapport Markdown + JSON par ticker. Le rapport doit contenir: faits, interprétation prudente, incertitudes, prochaines vérifications et disclaimer légal."

### Phase 7 — Tests auto
"Écris une suite `pytest` complète (unit + intégration) pour l'agent. Couvre cas nominaux, API indisponible, données manquantes, ticker invalide, et vérifie la présence du disclaimer."

### Phase 8 — Notation
"Implémente `scoring_engine` sur 100 points avec pondérations configurables, explication du score et stockage historique en SQLite."

### Phase 9 — Auto-amélioration
"Implémente `improvement_advisor` qui analyse scores/tests/logs et génère 5 recommandations priorisées (impact, effort, risque, échéance)."

### Phase 10 — Durcissement
"Ajoute instrumentation (temps par module, taux d'erreur, fraîcheur des données), optimise performances, et crée un script CI local qui exécute lint + tests + génération de rapport d'exemple."

---

## 5) Exemple d'arborescence du projet
```text
stock-agent/
├─ README.md
├─ pyproject.toml
├─ .env.example
├─ config/
│  ├─ settings.yaml
│  └─ providers.yaml
├─ src/
│  ├─ main.py
│  ├─ orchestrator/
│  │  └─ agent_runner.py
│  ├─ data_ingestion/
│  │  ├─ base_provider.py
│  │  ├─ market_provider.py
│  │  ├─ news_provider.py
│  │  └─ normalizer.py
│  ├─ analysis/
│  │  ├─ metrics.py
│  │  ├─ events.py
│  │  └─ analysis_engine.py
│  ├─ summarization/
│  │  ├─ prompt_templates.py
│  │  └─ report_generator.py
│  ├─ evaluation/
│  │  ├─ test_runner.py
│  │  ├─ scoring_engine.py
│  │  └─ improvement_advisor.py
│  └─ storage/
│     ├─ sqlite_store.py
│     └─ cache.py
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  └─ fixtures/
├─ data/
│  ├─ cache/
│  └─ snapshots/
└─ reports/
   └─ 2026-05-04/
```

---

## 6) Fonctionnalités minimum viables (MVP)
- Entrée utilisateur : liste de tickers + horizon court.
- Collecte prix + variation journalière + 3 à 5 news récentes.
- Résumé clair par ticker (Markdown).
- Mention explicite des incertitudes/données manquantes.
- Disclaimers légaux systématiques.
- Tests automatiques de base + score qualité.

---

## 7) Fonctionnalités avancées
- Alertes automatiques (seuil de variation/prix/volume).
- Dashboard web (historique, heatmap, watchlist).
- Comparaison multi-actions et benchmark indice.
- Analyse de sentiment multi-source plus fine.
- Mémoire historique et détection de dérive.
- Scoring de risque (volatilité, drawdown, dispersion news).
- Notifications Email / Telegram / Discord.
- Planificateur quotidien (cron / workflow).

---

## 8) Système de test (auto-évaluation)
Pour chaque rapport généré, exécuter les contrôles suivants :

1. **Exactitude des données**
   - Champs obligatoires présents (prix, variation, timestamp, source).
   - Cohérence interne (ex: variation calculée vs prix).
   - Fraîcheur (âge des données < seuil).

2. **Clarté du résumé**
   - Présence d'un résumé court en langage simple.
   - Longueur maîtrisée (ex: 120–250 mots par ticker).
   - Terminologie compréhensible non experte.

3. **Cohérence de l'analyse**
   - Les conclusions sont supportées par des faits cités.
   - Les limites et incertitudes sont explicites.

4. **Respect des limites financières**
   - Vérifier l'absence de formulations impératives :
     “achetez”, “vendez maintenant”, etc.
   - Vérifier la présence du disclaimer réglementaire.

5. **Gestion des erreurs**
   - API indisponible => message propre + fallback.
   - Données partielles => rapport partiel avec drapeau “incomplet”.

6. **Qualité globale**
   - Score global et justification par critères.
   - Archivage pour suivi de tendance.

---

## 9) Système de notation (grille /100)
- **Précision factuelle (30 pts)**
  - Concordance données/sources, pas d'invention.
- **Fraîcheur et provenance (15 pts)**
  - Timestamps, sources, indicateur d'ancienneté.
- **Clarté du résumé (15 pts)**
  - Lisibilité, concision, structure.
- **Cohérence de l'analyse (15 pts)**
  - Raisonnement prudent, aligné sur les faits.
- **Conformité légale/éthique (15 pts)**
  - Disclaimer + pas de conseil financier direct.
- **Robustesse technique (10 pts)**
  - Gestion erreurs, fallback, complétude.

### Interprétation
- 90–100 : excellent, prêt production surveillée.
- 75–89 : bon, améliorations ciblées recommandées.
- 60–74 : acceptable mais fragile.
- <60 : insuffisant, corriger avant usage.

---

## 10) Conseils d'amélioration automatique
Le module d'amélioration génère un rapport “Next Iteration Plan” :

1. **Code** : dette technique, duplication, modules lents.
2. **Sources de données** : API instables, latence élevée, couverture faible.
3. **Analyses** : métriques insuffisantes, signaux mal calibrés.
4. **Présentation** : jargon excessif, structure confuse.
5. **Fiabilité** : taux d'échec, timeouts, données manquantes.
6. **Sécurité** : secrets exposés, logs trop verbeux, permissions excessives.

### Format recommandé
- Recommandation
- Impact (1–5)
- Effort (1–5)
- Priorité (Haute/Moyenne/Basse)
- Action concrète
- Responsable (humain/agent)
- Échéance

---

## 11) Exemple de sortie attendue (fictive)

**Ticker : ABCD**
- Prix actuel : 123,40 USD (source: ProviderX, horodatage: 2026-05-04 14:30 UTC)
- Variation jour : +1,8%
- Variation 5 jours : -0,9%
- News clés :
  1) L'entreprise annonce un nouveau partenariat industriel.
  2) Résultats trimestriels légèrement supérieurs aux attentes.
- Indicateurs : P/E (si disponible), volume relatif, volatilité 30j.
- Sentiment global : modérément positif (confiance: 0,68).

**Résumé simple**
ABCD progresse aujourd'hui, possiblement soutenue par des annonces récentes positives. La dynamique hebdomadaire reste toutefois mitigée. Les données fondamentales disponibles suggèrent une valorisation à surveiller selon le secteur.

**Incertitudes**
- Certaines métriques fondamentales sont datées de plus de 30 jours.
- Le score de sentiment repose sur un échantillon limité de news.

**Avertissement**
Cette analyse est fournie à titre informatif uniquement et ne constitue pas un conseil en investissement.

---

## 12) Précautions légales et sécurité
- **Conseil financier** : afficher systématiquement un disclaimer.
- **Clés API** : stocker dans variables d'environnement/vault, jamais dans Git.
- **Confidentialité** : minimiser les données utilisateur stockées.
- **Sécurité** : chiffrer stockage sensible, rotation des clés, contrôle d'accès.
- **Auditabilité** : garder trace source + timestamp + version modèle.
- **Limites IA** : signaler incertitude, absence de données, biais potentiels.

---

## Bonus : feuille de route 30 jours
- Semaine 1 : cadrage + setup + collecte minimale.
- Semaine 2 : analyse + résumé + tests de base.
- Semaine 3 : scoring + auto-amélioration + robustesse.
- Semaine 4 : optimisation + sécurité + documentation + release v1.
