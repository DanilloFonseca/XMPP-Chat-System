# Chat XMPP

Servidor ejabberd com TLS e broker Mosquitto em Docker, rodando na VM da Mininet WiFi.

## Arquivos

- `docker-compose.yml`: sobe o ejabberd e o mosquitto
- `gerar_certificado.sh`: gera o certificado autoassinado (`ejabberd/server.pem`)
- `ejabberd/ejabberd.yml`: config do ejabberd
- `mosquitto/mosquitto.conf`: config do mosquitto

## Como rodar

Na VM:

```bash
sudo apt install pidgin -y

./gerar_certificado.sh
sudo docker compose up -d
```

Criar os usuários:

```bash
sudo docker exec ejabberd ejabberdctl register admin localhost admin123
sudo docker exec ejabberd ejabberdctl register user1 localhost 123
sudo docker exec ejabberd ejabberdctl register user2 localhost 123
```

## Pidgin

- Protocolo XMPP, usuário `user1`, domínio `localhost`, senha `123`
- Advanced: `Require encryption`, porta `5222`, servidor `127.0.0.1`

Aceitar o certificado na primeira conexão. Mesma coisa para o `user2`.

## Parar

```bash
sudo docker compose down
```