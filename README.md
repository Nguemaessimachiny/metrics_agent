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
---

# TP DevOps — Travail réalisé

## Prérequis du TP

- Docker Desktop installé et démarré
- Compte GitHub
- Compte Docker Hub (Parties 3 et 4)

---

## PARTIE 1 — Conteneurisation de l'application (Dockerfiles)

**Objectif :** créer deux Dockerfiles (dev et prod) pour lancer l'API et l'agent dans des conteneurs.

### Ce que nous avons fait

1. Créer `Dockerfile.dev` (développement)
2. Créer `Dockerfile` (production, multi-stage)
3. Créer `.dockerignore` pour alléger le contexte de build
4. Documenter le hot-reload (volume + `--reload`)
5. Tester les builds et l'endpoint `/health`

### Étape 1.1 — Image de développement (`Dockerfile.dev`)

Cette image :
- part de `python:3.12-slim`
- installe toutes les dépendances (y compris `pytest`)
- utilise un utilisateur non-root `appuser`
- lance uvicorn avec `--reload`
- expose le port `8000`

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

Le volume monte le code local dans `/app` : toute modification est prise en compte grâce à `--reload`.

**Vérifier :**
```bash
curl http://localhost:8000/health
```

Réponse attendue : `{"status":"ok"}`

**Arrêter le conteneur :**
```bash
docker rm -f metrics-api-dev
```

### Étape 1.2 — Image de production (`Dockerfile`)

Cette image :
- utilise un **build multi-stage**
- n'installe **pas** `pytest`
- tourne avec un utilisateur non-root
- définit un **HEALTHCHECK** sur `/health`
- expose le port `8000`
- installe `procps` (commande `uptime` pour l'agent)

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

**Vérifier le healthcheck :**
```bash
docker inspect --format="{{.State.Health.Status}}" metrics-api
```

Statut attendu : `healthy`

### Choix technique (Partie 1)

Une seule image de production (`metrics-agent-prod`) pour l'API et l'agent :
- le `CMD` par défaut lance l'API
- l'agent se lance en surchargeant la commande : `python -m app.agent`
- cela évite de maintenir deux images quasi identiques

---

## PARTIE 2 — Orchestration avec Docker Compose

**Objectif :** faire communiquer l'API et l'agent via Compose (réseau Docker, `.env`, healthcheck).

### Ce que nous avons fait

1. Créer `docker-compose.yaml` avec les services `api` et `agent`
2. Créer un réseau Docker dédié `metrics-net`
3. Utiliser `env_file: .env` pour la configuration
4. Configurer `depends_on` + healthcheck (l'agent attend que l'API soit healthy)
5. Forcer `METRICS_ENDPOINT=http://api:8000/metrics` pour l'agent (pas `127.0.0.1`)
6. Ajouter le bonus `docker-compose.override.yml` (mode développement)
7. Tester que l'agent envoie bien des métriques (`HTTP=201`)

### Étape 2.1 — Préparer le fichier `.env`

Le fichier `.env` n'est **jamais** commité (présent dans `.gitignore`).

```bash
cp .env.example .env
```

Windows PowerShell :
```powershell
Copy-Item .env.example .env
```

### Étape 2.2 — Comprendre les services Compose

Fichier : `docker-compose.yaml`

| Service | Rôle | Image | Port |
|---------|------|-------|------|
| `api` | API FastAPI | `metrics-agent-prod` | `8000:8000` |
| `agent` | Collecte et envoi des métriques | `metrics-agent-prod` | — |

Points importants :
- réseau dédié : `metrics-net`
- l'agent dépend de l'API : `depends_on` avec `condition: service_healthy`
- entre conteneurs, l'URL est `http://api:8000/metrics` (nom du service), **pas** `127.0.0.1`

### Étape 2.3 — Lancer en production (Compose)

```bash
docker compose -f docker-compose.yaml up -d --build
```

Cette commande :
1. construit l'image de production
2. démarre le service `api`
3. attend que le healthcheck soit `healthy`
4. démarre le service `agent`

### Étape 2.4 — Vérifier que tout fonctionne

```bash
curl http://localhost:8000/health
curl http://localhost:8000/metrics/latest
docker compose -f docker-compose.yaml ps
docker compose -f docker-compose.yaml logs agent --tail 20
```

Résultats attendus :
- `/health` → `{"status":"ok"}`
- `/metrics/latest` → un JSON de métriques
- logs agent → `Métriques envoyées avec succès. HTTP=201`

### Étape 2.5 — Arrêter les services

```bash
docker compose -f docker-compose.yaml down
```

### Étape 2.6 — Bonus : mode développement (override)

Fichier : `docker-compose.override.yml`

Avec un simple :
```bash
docker compose up -d --build
```

Compose fusionne automatiquement l'override et active :
- `Dockerfile.dev`
- montage du code en volume
- hot-reload (`--reload`) sur l'API

Pour forcer uniquement la production (sans override) :
```bash
docker compose -f docker-compose.yaml up -d --build
```

---

## PARTIE 3 — Pipeline CI/CD (GitHub Actions)

_À compléter_

---

## PARTIE 4 — Publication Docker Hub et déploiement

_À compléter_

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
