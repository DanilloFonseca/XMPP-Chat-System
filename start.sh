#!/usr/bin/env bash
# start.sh — prepara TUDO: certificado TLS, containers, usuários e dependências.
# Rode com:  ./start.sh   (dentro da VM Mininet use:  sudo ./start.sh)
set -euo pipefail
cd "$(dirname "$0")"

# Descobre se o Docker precisa de sudo (ex.: dentro da VM Mininet-WiFi)
if docker info >/dev/null 2>&1; then
    DOCKER=docker
else
    DOCKER="sudo docker"
fi

echo "[1/5] Gerando certificado TLS (se ainda não existir)..."
[ -f ejabberd/server.pem ] || ./gerar_certificado.sh

echo "[2/5] Subindo containers (Ejabberd + Mosquitto)..."
"$DOCKER" compose up -d

echo "[3/5] Aguardando o Ejabberd ficar pronto..."
for _ in $(seq 1 30); do
    status="$("$DOCKER" inspect --format '{{.State.Health.Status}}' ejabberd 2>/dev/null || true)"
    [ "$status" = healthy ] && break
    sleep 2
done

echo "[4/5] Registrando usuários ('already registered' pode ser ignorado)..."
"$DOCKER" exec ejabberd ejabberdctl register admin localhost admin123 || true
"$DOCKER" exec ejabberd ejabberdctl register user1 localhost 123    || true
"$DOCKER" exec ejabberd ejabberdctl register user2 localhost 123    || true

echo "[5/6] Autorizando presença mútua no roster (user1 <-> user2)..."
"$DOCKER" exec ejabberd ejabberdctl add_rosteritem user1 localhost user2 localhost "Bot (user2)" "" both || true
"$DOCKER" exec ejabberd ejabberdctl add_rosteritem user2 localhost user1 localhost "user1" "" both || true

echo "[6/6] Instalando dependências do bot (xmpppy + paho-mqtt)..."
if ! python3 -c "import xmpp, paho.mqtt" 2>/dev/null; then
    python3 -m pip install -r requirements.txt --break-system-packages >/dev/null 2>&1 \
        || python3 -m pip install -r requirements.txt >/dev/null 2>&1 \
        || echo "ATENÇÃO: rode manualmente: python3 -m pip install --break-system-packages -r requirements.txt"
fi

echo
echo "Tudo pronto!"
echo "  1) Abra painel/index.html no navegador (luz via MQTT)."
echo "  2) Pidgin: user1@localhost, senha 123, porta 5222, 'Require encryption'."
echo "  3) Inicie o bot:  python3 bot.py"
echo "  4) Envie ON ou OFF pelo Pidgin e veja a luz do painel."
