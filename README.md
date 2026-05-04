# Portfolio AI Agent (Actions, ETF, Fonds)

Agent IA modulaire pour suivre un portefeuille multi-actifs à partir d'ISIN, récupérer des données de marché, produire des synthèses neutres et générer des rapports horodatés.

## Objectifs (MVP)

- Charger un portefeuille (`data/portfolio.yaml`) et valider les ISIN.
- Dédupliquer et contrôler les actifs avant traitement.
- Préparer l'architecture pour le mapping ISIN→ticker, la collecte de données, l'analyse et le reporting.
- Garantir l'absence d'invention de données : champ inconnu => marqué `missing`.
- Inclure explicitement la clause de non-conseil financier.

## Architecture

```text
config/
data/
src/
  agents/
  modules/
reports/
tests/
```

## Démarrage rapide

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

## Format de portefeuille

Le fichier `data/portfolio.yaml` doit contenir :

- `name` (str)
- `isin` (str, 12 caractères alphanumériques)
- `type` (`action`, `etf`, `fonds`, `autre`)
- `currency` (str)
- `notes` (str optionnel)

## Sécurité

- Les secrets API sont lus via variables d'environnement (`.env` local, jamais versionné).
- Aucune clé API dans le code.

## Clause de non-conseil

> Cette analyse est informative et ne constitue pas un conseil financier.

