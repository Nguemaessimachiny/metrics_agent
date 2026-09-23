# Cette étape se nomme builder
FROM python:3.12-slim AS builder

# Notre dossier de travail où le builder sera
WORKDIR /app 

# 
COPY requirements.txt . 

# 
RUN grep -v '^pytest' requirements.txt > requirements.prod.txt

# On installe les bibliothèques présentes dans requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r requirements.prod.txt

# Démarrons une nouvelle étape indépendante pour l'image finale
FROM python:3.12-slim

# C'est le dossier de travil pour l'image finale
WORKDIR /app

# 
COPY --from=builder /install /usr/local

# On prend le dossier app dans la machine et on copie dans le dossier app de l'image finale.
COPY app ./app

# On fait tourner l'application avec appuser donc évite l'utilisateur root
RUN useradd --create-home appuser

# 
USER appuser

# On expose le port et on fera la connexion avec  docker run -p 8000:8000
EXPOSE 8000

# `HEALTHCHECK` permet à Docker de vérifier automatiquement que l’API fonctionne en testant l’endpoint `/health` toutes les 30 secondes.
# Après 3 échecs consécutifs, le conteneur est considéré comme `unhealthy`.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

# 
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]