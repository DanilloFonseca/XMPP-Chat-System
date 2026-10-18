#!/usr/bin/env bash
# preparar_finch.sh — instala o Finch (Pidgin em modo texto) e já deixa a
# conta user1@localhost configurada, com o bot (user2) na lista de contatos.
# Rode uma vez:  ./preparar_finch.sh   (na VM Mininet:  sudo ./preparar_finch.sh)
set -euo pipefail

if ! command -v finch >/dev/null 2>&1; then
    echo "[1/4] Instalando o Finch..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq finch
fi

echo "[2/4] Preparando ~/.purple (configurações do Pidgin/Finch)..."
mkdir -p "$HOME/.purple"

echo "[3/4] Criando a conta user1@localhost (TLS obrigatório)..."
cat > "$HOME/.purple/accounts.xml" <<'XML'
<?xml version='1.0' encoding='UTF-8' ?>
<account version='1.0'>
  <account>
    <protocol>prpl-jabber</protocol>
    <name>user1@localhost</name>
    <password>123</password>
    <settings>
      <setting name='port' type='int'>5222</setting>
      <setting name='connect_server' type='string'>127.0.0.1</setting>
      <setting name='require_tls' type='bool'>1</setting>
      <setting name='remember_password' type='bool'>1</setting>
    </settings>
  </account>
</account>
XML

echo "[4/5] Lista de contatos e mouse habilitado..."
cat > "$HOME/.purple/blist.xml" <<'XML'
<?xml version='1.0' encoding='UTF-8' ?>
<purple version='1.0'>
  <blist>
    <group name='XMPP'>
      <contact>
        <buddy account='user1@localhost' proto='prpl-jabber'>
          <name>user2@localhost</name>
          <alias>Bot (user2)</alias>
        </buddy>
      </contact>
    </group>
  </blist>
</purple>
XML

printf '[general]\nmouse = 1\n' > "$HOME/.gntrc"

echo "[5/5] Confiando no certificado autoassinado (evita o diálogo no 1º acesso)..."
mkdir -p "$HOME/.purple/certificates/x509/tls_peers"
cp ejabberd/server.crt "$HOME/.purple/certificates/x509/tls_peers/127.0.0.1" 2>/dev/null || true

echo
echo "Pronto. Rode:  finch"
echo "Dicas: setas para navegar, Enter no 'Bot (user2)' para conversar,"
echo "digite e Enter para enviar, F10 abre o menu (e o Quit)."
