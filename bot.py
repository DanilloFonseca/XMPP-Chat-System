#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot.py — Cliente XMPP em Python (xmpppy) integrado ao Broker MQTT (paho-mqtt).

Atividade Avaliativa — Unidade II
Tecnologias de Comunicação para IoT/IMD0907

O que este bot faz:
  1. Conecta no Ejabberd em localhost:5222 usando STARTTLS obrigatório
     (evidência de conexão segura: client.connect() retorna 'tls').
  2. Autentica como user2@localhost.
  3. Fica escutando mensagens de chat (por exemplo, enviadas pelo Pidgin).
  4. Ao receber uma mensagem:
     - responde ao remetente (comunicação bidirecional XMPP);
     - publica a mensagem no tópico MQTT imd0907/xmpp/mensagens
       (aparece no log do painel web);
     - se o texto for "ON" ou "OFF", publica em imd0907/painel/luz/set,
       o que faz o painel (painel/index.html) ligar/desligar a "luz".

Dependências (ver requirements.txt):
  xmpppy     — cliente XMPP
  paho-mqtt  — cliente MQTT
"""

import json
import time
from datetime import datetime

import paho.mqtt.client as mqtt
import xmpp  # módulo xmpppy

# ---------------------------------------------------------------------------
# Configurações
# ---------------------------------------------------------------------------

# Ejabberd (domínio e porta definidos em ejabberd/ejabberd.yml)
XMPP_DOMINIO = "localhost"
XMPP_HOST = "127.0.0.1"   # onde o Ejabberd escuta (porta 5222 do Docker)
XMPP_PORTA = 5222
XMPP_USUARIO = "user2"    # usuário criado com ejabberdctl register
XMPP_SENHA = "123"

# Broker Mosquitto (mosquitto/mosquitto.conf)
MQTT_HOST = "127.0.0.1"
MQTT_PORTA = 1883

# Tópicos combinados com o painel (painel/index.html)
TOPICO_MENSAGENS = "imd0907/xmpp/mensagens"   # log das mensagens no painel
TOPICO_LUZ = "imd0907/painel/luz/set"         # comando ON/OFF para o checkbox


# ---------------------------------------------------------------------------
# MQTT
# ---------------------------------------------------------------------------

def conectar_mqtt():
    """Conecta no broker MQTT e deixa o loop rodando em segundo plano.

    O paho-mqtt reconecta sozinho se a conexão cair (reconnect_on_failure).
    """
    # O callback_api_version só existe no paho-mqtt 2.x; em versões antigas
    # o comportamento padrão (v1) já serve, pois este bot não usa callbacks.
    try:
        cliente = mqtt.Client(
            client_id="bot-xmpp",
            protocol=mqtt.MQTTv311,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
    except AttributeError:
        cliente = mqtt.Client(client_id="bot-xmpp", protocol=mqtt.MQTTv311)
    cliente.reconnect_delay_set(min_delay=1, max_delay=30)
    cliente.connect(MQTT_HOST, MQTT_PORTA, keepalive=60)
    cliente.loop_start()  # thread separada para enviar/receber pacotes MQTT
    print(f"[MQTT] Conectado em {MQTT_HOST}:{MQTT_PORTA}")
    return cliente


def publicar_mqtt(cliente_mqtt, topico, payload):
    """Publica uma mensagem no broker (QoS 1 = entrega garantida)."""
    cliente_mqtt.publish(topico, payload, qos=1)
    print(f"[MQTT] Publicado em '{topico}': {payload}")


# ---------------------------------------------------------------------------
# XMPP
# ---------------------------------------------------------------------------

def tratar_mensagem(conexao, stanza):
    """Callback chamado pelo xmpppy a cada <message> recebida."""
    if stanza.getType() not in ("chat", "normal", None):
        return  # ignora mensagens de erro, manchetes etc.

    remetente = stanza.getFrom()          # JID de quem enviou (ex.: user1@localhost)
    texto = stanza.getBody() or ""        # corpo da mensagem
    texto_limpo = texto.strip()

    print(f"[XMPP] Mensagem de {remetente}: {texto_limpo!r}")

    # 1) Resposta ao remetente -> comunicação bidirecional via XMPP
    resposta = xmpp.Message(remetente, f"Recebido: {texto_limpo}")
    resposta.setAttr("type", "chat")
    conexao.send(resposta)

    # 2) Publica a mensagem no MQTT para aparecer no log do painel
    payload = json.dumps({
        "de": str(remetente),
        "texto": texto_limpo,
        "hora": datetime.now().strftime("%H:%M:%S"),
    })
    publicar_mqtt(MQTT, TOPICO_MENSAGENS, payload)

    # 3) Comando ON/OFF aciona a "luz" (checkbox) do painel via MQTT
    comando = texto_limpo.upper()
    if comando in ("ON", "OFF"):
        publicar_mqtt(MQTT, TOPICO_LUZ, comando)
        print(f"[BOT] Comando '{comando}' enviado para o painel.")


def tratar_presenca(conexao, stanza):
    """Aceita automaticamente pedidos de contato do Pidgin (subscribe)."""
    if stanza.getType() == "subscribe":
        jid = stanza.getFrom()
        conexao.send(xmpp.Presence(jid, "subscribed"))  # aprova o pedido
        conexao.send(xmpp.Presence(jid, "subscribe"))   # pede de volta
        print(f"[XMPP] Contato aceito: {jid}")


def conectar_xmpp():
    """Conecta no Ejabberd com STARTTLS obrigatório e autentica o bot.

    Retorna o cliente xmpppy já autenticado ou levanta RuntimeError.
    """
    cliente = xmpp.Client(XMPP_DOMINIO, debug=[])

    # A flag secure=None (padrão) faz o xmpppy negociar STARTTLS sozinho.
    # O retorno 'tls' é a evidência de que a conexão ficou criptografada.
    resultado = cliente.connect(server=(XMPP_HOST, XMPP_PORTA))
    if resultado != "tls":
        raise RuntimeError(
            f"Conexão sem TLS estabelecida: {resultado!r}. "
            "Verifique o certificado (ejabberd/server.pem) e o Ejabberd."
        )
    print(f"[XMPP] Conectado em {XMPP_HOST}:{XMPP_PORTA} — conexão TLS ativa.")

    # Autenticação SASL (o Ejabberd exige, pois starttls_required está ativo)
    if not cliente.auth(XMPP_USUARIO, XMPP_SENHA, resource="bot"):
        raise RuntimeError("Falha na autenticação do usuário " + XMPP_USUARIO)
    print(f"[XMPP] Autenticado como {XMPP_USUARIO}@{XMPP_DOMINIO}.")

    # Registra os callbacks de mensagem e presença
    cliente.RegisterHandler("message", tratar_mensagem)
    cliente.RegisterHandler("presence", tratar_presenca)

    # Anuncia presença online (aparece no Pidgin)
    cliente.sendInitPresence(requestRoster=0)
    print("[BOT] Pronto. Envie uma mensagem pelo Pidgin (ou 'ON'/'OFF').")
    return cliente


def principal():
    """Loop principal com reconexão automática em caso de queda."""
    global MQTT
    MQTT = conectar_mqtt()

    while True:
        cliente_xmpp = None
        try:
            cliente_xmpp = conectar_xmpp()
            # Processa o tráfego XMPP; Process(1) bloqueia até 1 s
            while cliente_xmpp.isConnected():
                cliente_xmpp.Process(1)
        except Exception as erro:
            print(f"[BOT] Erro na conexão XMPP: {erro}")

        # Tenta reconectar depois de uma pausa curta
        if cliente_xmpp is not None:
            try:
                cliente_xmpp.disconnect()
            except Exception:
                pass
        print("[BOT] Reconectando em 3 s...")
        time.sleep(3)


if __name__ == "__main__":
    principal()
