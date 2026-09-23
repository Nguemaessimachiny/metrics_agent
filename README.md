# System Metrics Agent

Un agent Python modulaire capable de collecter les métriques système,
de les formater et de les transmettre en temps réel vers une API ou un
Webhook externe.

## Fonctionnalités

- Collecte du pourcentage CPU.
- Collecte de la mémoire RAM totale, utilisée et disponible.
- Utilisation de `psutil`.
- Utilisation de **`subprocess`** pour exécuter la commande système
  `uptime` et récupérer la charge système.
- Architecture modulaire :
  - `collector.py` : collecte ;
  - `formatter.py` : normalisation du payload ;
  - `sender.py` : envoi HTTP ;
  - `agent.py` : orchestration ;
  - `api.py` : API de réception avec **FastAPI**.
- Configuration externe avec `.env`.
- Gestion des erreurs réseau et des erreurs de collecte.
- Tests automatisés avec `pytest`.

## Architecture

```text
system_metrics_agent/
├── app/
│   ├── __init__.py
│   ├── agent.py
│   ├── api.py
│   ├── collector.py
│   ├── config.py
│   ├── formatter.py
│   └── sender.py
├── tests/
│   ├── test_api.py
│   ├── test_collector.py
│   ├── test_formatter.py
│   └── test_sender.py
├── .env.example
├── requirements.txt
└── README.md
```

## Installation

Créer un environnement virtuel :

```bash
python -m venv .venv
```

Linux/macOS :

```bash
source .venv/bin/activate
```

Windows :

```powershell
.venv\Scripts\Activate.ps1
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

Créer le fichier de configuration :

```bash
cp .env.example .env
```

Sous Windows, copier manuellement `.env.example` en `.env`.

## Démarrer l'API FastAPI

```bash
uvicorn app.api:app --reload
```

L'API est alors disponible sur :

```text
http://127.0.0.1:8000
```

Documentation interactive FastAPI :

```text
http://127.0.0.1:8000/docs
```

## Démarrer l'agent


Dans un deuxième terminal :

```bash
python -m app.agent
```

L'agent collecte les métriques selon l'intervalle défini dans `.env`
puis les envoie automatiquement vers `METRICS_ENDPOINT`.
<!-- -------------------------------------------------------------------- -->

## Conteneurisation avec Docker

Le projet fournit deux Dockerfiles distincts : un pour le développement, un pour la production.

### Lancer en développement (Dockerfile.dev)

Ce mode active le rechargement à chaud (`--reload` + montage du code en volume) et inclut les dépendances de test (`pytest`).

**Construire l'image :**
```bash
docker build -f Dockerfile.dev -t metrics-agent:dev .
```

**Lancer l'API avec hot-reload** (Linux / macOS) :
```bash
docker run -d -p 8000:8000 -v "$(pwd)":/app --name metrics-api-dev metrics-agent:dev
```

**Lancer l'API avec hot-reload** (Windows PowerShell) :
```powershell
docker run -d -p 8000:8000 -v ${PWD}:/app --name metrics-api-dev metrics-agent:dev
```

Le volume monte le code local dans `/app` : toute modification est prise en compte automatiquement grâce à `--reload`.

Vérifier que l'API répond :
```bash
curl http://localhost:8000/health
```

### Lancer en production (Dockerfile)

Ce mode utilise un build multi-stage, exclut `pytest`, tourne avec un utilisateur non-root, et inclut un `HEALTHCHECK` automatique sur `/health`.

**Construire l'image :**
```bash
docker build -t metrics-agent-prod .
```

**Lancer le service API :**
```bash
docker run -d -p 8000:8000 --name metrics-api metrics-agent-prod
```

**Lancer le service Agent** (même image, commande différente) :
```bash
docker run -d --name metrics-agent-worker \
  -e METRICS_ENDPOINT=http://metrics-api:8000/metrics \
  metrics-agent-prod python -m app.agent
```

### Choix technique : une image unique pour l'API et l'agent

L'API (`app.api`) et l'agent (`app.agent`) font partie du même package Python et partagent les mêmes dépendances. Plutôt que de maintenir deux images quasi identiques, une seule image de production (`metrics-agent-prod`) est construite : le `CMD` par défaut lance l'API, et le service agent est démarré en surchargeant simplement la commande au lancement du conteneur (`python -m app.agent`). Cette approche réduit la duplication et simplifie le pipeline CI/CD, qui n'a besoin de builder et publier qu'une seule image.

**Note sur `procps`** : l'image de production installe le paquet système `procps`, nécessaire à la commande `uptime` utilisée par `app/collector.py` pour la collecte de la charge système.

## Orchestration avec Docker Compose

_À compléter (Partie 2)_

## Pipeline CI/CD

_À compléter (Partie 3)_

## Images Docker Hub

_À compléter (Partie 4)_

## Exemple de configuration

```env
METRICS_ENDPOINT=http://127.0.0.1:8000/metrics
COLLECTION_INTERVAL=5
REQUEST_TIMEOUT=5
```

Pour envoyer vers un webhook externe, remplacer simplement :

```env
METRICS_ENDPOINT=https://example.com/webhook
```

## Exemple de métrique envoyée

```json
{
  "agent": "system-metrics-agent",
  "event_type": "system_metrics",
  "data": {
    "timestamp": "2026-08-27T12:00:00.000000+00:00",
    "hostname": "server-01",
    "cpu": {
      "percent": 23.4,
      "logical_cores": 8
    },
    "memory": {
      "total_bytes": 16777216000,
      "available_bytes": 8000000000,
      "used_bytes": 7777216000,
      "percent": 48.2
    },
    "system": {
      "load_1m": 0.12,
      "load_5m": 0.18,
      "load_15m": 0.20
    }
  }
}
```

## Endpoints

### Vérifier l'état de l'API

```http
GET /health
```

Réponse :

```json
{
  "status": "ok"
}
```

### Envoyer des métriques

```http
POST /metrics
```

### Récupérer la dernière métrique

```http
GET /metrics/latest
```

## Tests

Exécuter toute la suite :

```bash
pytest -q
```

Exécuter avec une couverture de code nécessite l'installation de
`pytest-cov` :

```bash
pip install pytest-cov
pytest --cov=app --cov-report=term-missing
```

## Robustesse

Le projet gère notamment :

- les erreurs d'exécution de `subprocess` ;
- les timeouts ;
- les erreurs de connexion HTTP ;
- les réponses HTTP en erreur ;
- les configurations invalides ;
- les payloads incomplets ;
- l'absence de métriques dans l'API.

## Démonstration du flux

```text
┌──────────────────┐
│ Système          │
│ CPU / RAM        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ collector.py     │
│ psutil           │
│ subprocess       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ formatter.py     │
│ Payload JSON     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ sender.py        │
│ HTTP POST        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ FastAPI          │
│ /metrics         │
└──────────────────┘
```
