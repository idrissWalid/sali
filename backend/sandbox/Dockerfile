FROM python:3.11-slim

# Sécurité : utilisateur non-root
RUN groupadd -r sandbox && useradd -r -g sandbox sandbox

WORKDIR /app

# Installer les dépendances système nécessaires pour la compilation (XGBoost, LightGBM, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copier les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le runner
COPY runner.py .

# Répertoires temporaires pour graphiques et config matplotlib
RUN mkdir -p /tmp/sandbox /tmp/mpl_config && chown sandbox:sandbox /tmp/sandbox /tmp/mpl_config

# Config matplotlib pour éviter les warnings
ENV MPLCONFIGDIR=/tmp/mpl_config

# Passer en utilisateur non-root
USER sandbox

# Point d'entrée : lecture depuis stdin, écriture vers stdout
CMD ["python", "runner.py"]
