# Generic Streaming Spouts

![banner](./assets/banner.jpg)

This is a collection of generic Spouts and (micro) Batch spouts.

Includes:

| Name         | Description                                     | Output Type | Input Type |
| ------------ | ----------------------------------------------- | ----------- | ---------- |
| Webhook      | Cherrypy server that accepts all HTTP API calls | Streaming   | HTTP       |
| Webhook      | Cherrypy server that accepts all HTTP API calls | Batch       | HTTP       |
| Kafka        | Kafka client that listens to a topic            | Streaming   | Kafka      |
| Kafka        | Kafka client that listens to a topic            | Batch       | Kafka      |
| Websocket    | Websocket client that listens to a socket       | Streaming   | TCP        |
| Websocket    | Websocket client that listens to a socket       | Batch       | TCP        |
| UDP          | UDP server that listens to a given port         | Streaming   | UDP        |
| UDP          | UDP server that listens to a given port         | Batch       | UDP        |
| QUIC         | Aioquic server that listens to a given port     | Streaming   | UDP        |
| QUIC         | Aioquic server that listens to a given port     | Batch       | UDP        |
| HTTP Polling | HTTP client that keeps polling an API           | Streaming   | HTTP       |
| HTTP Polling | HTTP client that keeps polling an API           | Batch       | HTTP       |

All of the above spouts support both streaming and batch usecases.

## Usage

### Webhooks

Run the spout:

```bash
genius Webhook rise \
  streaming \
  --output_kafka_topic webhook_test \
  --output_kafka_cluster_connection_string localhost:9094 \
  postgres \
  --postgres_host 127.0.0.1 \
  --postgres_port 5432 \
  --postgres_user postgres \
  --postgres_password postgres \
  --postgres_database geniusrise \
  --postgres_table state \
  listen \
  --args port=3001
```

Test:

```bash
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{"lol": "teeeestss"}' \
     http://localhost:3001
```

### Kafka

```bash
genius Kafka rise \
  streaming \
  --output_kafka_topic kafka_test \
  --output_kafka_cluster_connection_string localhost:9094 \
  postgres \
  --postgres_host 127.0.0.1 \
  --postgres_port 5432 \
  --postgres_user postgres \
  --postgres_password postgres \
  --postgres_database geniusrise \
  --postgres_table state \
  listen \
  --args topic=kafka_test_input group_id=kafka_test bootstrap_servers=localhost:9094
```

### Websockets

```bash
genius Websocket rise \
  streaming \
  --output_kafka_topic websocket_test \
  --output_kafka_cluster_connection_string localhost:9094 \
  postgres \
  --postgres_host 127.0.0.1 \
  --postgres_port 5432 \
  --postgres_user postgres \
  --postgres_password postgres \
  --postgres_database geniusrise \
  --postgres_table state \
  listen \
  --args host=localhost port=3002
```

Test:

```bash
cargo install websocat
echo '{"lol": "heheheheheheheh"}' | websocat ws://localhost:3002
```

### UDP

```bash
genius Udp rise \
  streaming \
  --output_kafka_topic udp_test \
  --output_kafka_cluster_connection_string localhost:9094 \
  postgres \
  --postgres_host 127.0.0.1 \
  --postgres_port 5432 \
  --postgres_user postgres \
  --postgres_password postgres \
  --postgres_database geniusrise \
  --postgres_table state \
  listen \
  --args host=localhost port=3003
```

Test:

```bash
yay -S netcat
echo -n '{"key": "value"}' | nc -u -w1 localhost 3003
```

### QUIC

```bash
openssl genpkey -algorithm RSA -out ~/.ssh/quic_key.pem
openssl req -new -x509 -key ~/.ssh/quic_key.pem -out ~/.ssh/quic_cert.pem -days 365 -subj "/CN=localhost"

genius Quic rise \
  streaming \
  --output_kafka_topic udp_test \
  --output_kafka_cluster_connection_string localhost:9094 \
  postgres \
  --postgres_host 127.0.0.1 \
  --postgres_port 5432 \
  --postgres_user postgres \
  --postgres_password postgres \
  --postgres_database geniusrise \
  --postgres_table state \
  listen \
  --args cert_path=/home/ixaxaar/.ssh/quic_cert.pem key_path=/home/ixaxaar/.ssh/quic_key.pem host=localhost port=3004
```

Test:

```
go install github.com/spacewander/quick@latest

quick -insecure https://localhost:3004
```

### REST API polling

```bash
genius RESTAPIPoll rise \
  streaming \
  --output_kafka_topic poll_test \
  --output_kafka_cluster_connection_string localhost:9094 \
  postgres \
  --postgres_host 127.0.0.1 \
  --postgres_port 5432 \
  --postgres_user postgres \
  --postgres_password postgres \
  --postgres_database geniusrise \
  --postgres_table state \
  listen \
  --args url=https://reqres.in/api/users method=GET interval=6 body="" headers='{"content-type": "application/json"}' params='{"page": 2}'
```
