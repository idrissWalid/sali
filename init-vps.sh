#!/bin/bash
# Script d'initialisation pour un VPS Oracle Cloud (1Go RAM)
# Exécutez ce script en tant que root : sudo bash init-vps.sh

echo "Début de l'initialisation du VPS..."

# 1. Création d'un fichier SWAP de 4Go
if [ ! -f /swapfile ]; then
    echo "Création d'un fichier d'échange (SWAP) de 4Go..."
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
    
    # Optimisation de la gestion du swap
    sysctl vm.swappiness=10
    echo 'vm.swappiness=10' | tee -a /etc/sysctl.conf
    echo "SWAP configuré avec succès."
else
    echo "Le fichier d'échange (SWAP) existe déjà."
fi

# 2. Installation de Docker et Docker Compose
if ! command -v docker &> /dev/null; then
    echo "Installation de Docker..."
    apt-get update
    apt-get install -y ca-certificates curl gnupg
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    
    # Ajout du repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    echo "Docker installé avec succès."
else
    echo "Docker est déjà installé."
fi

# 3. Autoriser l'utilisateur actuel à utiliser Docker (optionnel, si non-root)
if [ "$SUDO_USER" ]; then
    usermod -aG docker $SUDO_USER
    echo "Utilisateur $SUDO_USER ajouté au groupe docker."
fi

# 4. Ouverture des ports (Oracle Cloud bloque tout par défaut sur Ubuntu)
echo "Ouverture des ports 80, 443, 3000 et 8000 dans iptables..."
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 3000 -j ACCEPT
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT
if command -v netfilter-persistent &> /dev/null; then
    netfilter-persistent save
fi

echo "Initialisation terminée. Redémarrez votre session ou tapez 'newgrp docker' pour appliquer les changements de groupe."
