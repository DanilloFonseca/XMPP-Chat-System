# IoT Communication Technologies - IMD0907
## XMPP Chat

ejabberd server with TLS and Mosquitto broker in Docker, running on the Mininet-WiFi VM.

## VM

Everything runs on the pre-configured Mininet-WiFi VM:
https://github.com/intrig-unicamp/mininet-wifi#pre-configured-virtual-machine

## Files

- `docker-compose.yml`: starts ejabberd and mosquitto
- `gerar_certificado.sh`: generates the self-signed certificate (`ejabberd/server.pem`)
- `ejabberd/ejabberd.yml`: ejabberd config
- `mosquitto/mosquitto.conf`: mosquitto config
- `painel/index.html`: MQTT dashboard with a checkbox

## Ports

| Port | Service | Usage |
|---|---|---|
| 5222 | ejabberd | XMPP client connections (STARTTLS required) |
| 5280 | ejabberd | admin panel at http://localhost:5280/admin |
| 1883 | mosquitto | MQTT |
| 9001 | mosquitto | MQTT over WebSocket, used by the dashboard |

## How to run

On the VM:

```bash
sudo apt install pidgin -y

./gerar_certificado.sh
sudo docker compose up -d
```

Create the users:

```bash
sudo docker exec ejabberd ejabberdctl register admin localhost admin123
sudo docker exec ejabberd ejabberdctl register user1 localhost 123
sudo docker exec ejabberd ejabberdctl register user2 localhost 123
```

## Pidgin

- Protocol XMPP, username `user1`, domain `localhost`, password `123`
- Advanced: `Require encryption`, port `5222`, connect server `127.0.0.1`

Accept the certificate on the first connection. Same for `user2`.

## Bot Python (cliente XMPP + MQTT)

O bot `bot.py` usa o módulo `xmpppy` para conversar com o Ejabberd e o
`paho-mqtt` para publicar no Mosquitto. Ele loga como `user2`, responde às
mensagens recebidas (comunicação bidirecional) e, quando recebe `ON` ou `OFF`,
publica no tópico `imd0907/painel/luz/set`, que liga/desliga a luz do painel.

```bash
python3 -m pip install -r requirements.txt
python3 bot.py
```

No Pidgin, com `user1` conectado, envie uma mensagem para `user2@localhost`:

- `Olá` -> o bot responde e a mensagem aparece no log do painel
- `ON` -> o bot responde e o checkbox/luz do painel é marcado
- `OFF` -> o bot responde e o checkbox/luz é desmarcado

O bot exige a conexão TLS do Ejabberd e imprime `conexão TLS ativa` quando
consegue negociar o STARTTLS.

## Dashboard

Open `painel/index.html` in the VM's Firefox. It connects to mosquitto on port 9001 and the status changes to "conectado".

Topics:

- `imd0907/painel/luz/set`: receives `ON` or `OFF` and checks or unchecks the checkbox
- `imd0907/painel/luz/estado`: the dashboard publishes the current checkbox state here
- `imd0907/xmpp/mensagens`: chat messages, shown in the page log

The MQTT.js library is loaded from unpkg, so the VM needs internet access for the dashboard to work.

To test without the chat:

```bash
sudo docker exec -it mosquitto mosquitto_sub -t 'imd0907/#' -v
sudo docker exec mosquitto mosquitto_pub -t imd0907/painel/luz/set -m ON
```

## Stop

```bash
sudo docker compose down
```
