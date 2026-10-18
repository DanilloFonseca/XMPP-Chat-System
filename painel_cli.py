#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
painel_cli.py — versão em terminal do painel MQTT (painel/index.html).

É o "cliente MQTT" que executa a ação pedida na atividade:
  - assina imd0907/painel/luz/set e liga/desliga a "luz" (em texto);
  - assina imd0907/xmpp/mensagens e mostra o log do chat;
  - publica o estado em imd0907/painel/luz/estado, como o painel web.

Uso:  python3 painel_cli.py
"""

import json

import paho.mqtt.client as mqtt

MQTT_HOST = "127.0.0.1"
MQTT_PORTA = 1883

# Tópicos combinados com bot.py e painel/index.html
TOPICO_COMANDO = "imd0907/painel/luz/set"
TOPICO_ESTADO = "imd0907/painel/luz/estado"
TOPICO_MENSAGENS = "imd0907/xmpp/mensagens"

luz_ligada = False


def desenhar():
    """Redesenha a 'tela' do painel com o estado atual da luz."""
    if luz_ligada:
        estado = "\033[1;33m●  LIGADA\033[0m"
    else:
        estado = "\033[90m○  desligada\033[0m"

    # Limpa o terminal e mostra o painel fixo
    print("\033[2J\033[H", end="")
    print("=" * 42)
    print("  PAINEL MQTT  (cliente em terminal)")
    print("=" * 42)
    print(f"  Luz: {estado}")
    print("-" * 42)
    print("  Log do chat:")


def ao_receber(cliente, dados_usuario, mensagem):
    """Callback do paho-mqtt para cada mensagem recebida."""
    global luz_ligada

    topico = mensagem.topic
    payload = mensagem.payload.decode()

    if topico == TOPICO_COMANDO:
        # Comando ON/OFF vindo do bot -> executa a ação (liga/desliga a luz)
        luz_ligada = payload.upper() == "ON"
        desenhar()
        cliente.publish(TOPICO_ESTADO, payload, qos=1)

    elif topico == TOPICO_MENSAGENS:
        # Mensagem do chat -> exibe no log
        try:
            dados = json.loads(payload)
            print(f"  {dados['de']}: {dados['texto']}")
        except (ValueError, KeyError):
            print(f"  {payload}")


def principal():
    cliente = mqtt.Client(client_id="painel-cli", protocol=mqtt.MQTTv311)
    cliente.on_message = ao_receber
    cliente.connect(MQTT_HOST, MQTT_PORTA, keepalive=60)
    cliente.subscribe([(TOPICO_COMANDO, 0), (TOPICO_MENSAGENS, 0)])

    desenhar()
    print("  aguardando comandos ON/OFF...")
    cliente.loop_forever()


if __name__ == "__main__":
    principal()
