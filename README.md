![banner](./assets/banner.jpg)

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

# Generic Streaming Spouts

This is a collection of generic streaming and (micro) batch spouts.

**Table of Contents**

- [Generic Streaming Spouts](#generic-streaming-spouts)
- [Streaming Spouts](#streaming-spouts)
  - [Usage](#usage)
    - [Webhooks](#webhooks)
    - [Kafka](#kafka)
    - [Websockets](#websockets)
    - [UDP](#udp)
    - [QUIC](#quic)
    - [REST API polling](#rest-api-polling)
    - [RabbitMQ / AMQP](#rabbitmq--amqp)
    - [MQTT](#mqtt)
    - [Redis Pub-Sub](#redis-pub-sub)
    - [Redis Streams](#redis-streams)
    - [AWS SNS](#aws-sns)
    - [AWS SQS](#aws-sqs)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

Includes:

| No. | Name                                               | Description                                           | Output Type | Input Type    |
| --- | -------------------------------------------------- | ----------------------------------------------------- | ----------- | ------------- |
| 1   | [Webhook](streaming_spouts/webhook.py)             | Cherrypy server that accepts all HTTP API calls       | Streaming   | HTTP          |
| 2   | [Webhook](streaming_spouts/webhook.py)             | Cherrypy server that accepts all HTTP API calls       | Batch       | HTTP          |
| 3   | [Kafka](streaming_spouts/kafka.py)                 | Kafka client that listens to a topic                  | Streaming   | Kafka         |
| 4   | [Kafka](streaming_spouts/kafka.py)                 | Kafka client that listens to a topic                  | Batch       | Kafka         |
| 5   | [Websocket](streaming_spouts/websocket.py)         | Websocket server that listens to a socket             | Streaming   | Websocket     |
| 6   | [Websocket](streaming_spouts/websocket.py)         | Websocket server that listens to a socket             | Batch       | Websocket     |
| 7   | [UDP](streaming_spouts/udp.py)                     | UDP server that listens to a given port               | Streaming   | UDP           |
| 8   | [UDP](streaming_spouts/udp.py)                     | UDP server that listens to a given port               | Batch       | UDP           |
| 9   | [QUIC](streaming_spouts/quic.py)                   | Aioquic server that listens to a given port           | Streaming   | QUIC          |
| 10  | [QUIC](streaming_spouts/quic.py)                   | Aioquic server that listens to a given port           | Batch       | QUIC          |
| 11  | [HTTP Polling](streaming_spouts/http_polling.py)   | HTTP client that keeps polling an API                 | Streaming   | HTTP          |
| 12  | [HTTP Polling](streaming_spouts/http_polling.py)   | HTTP client that keeps polling an API                 | Batch       | HTTP          |
| 13  | [RabbitMQ / AMQP](streaming_spouts/amqp.py)        | RabbitMQ client that listens to a given queue         | Streaming   | AMQP          |
| 14  | [RabbitMQ / AMQP](streaming_spouts/amqp.py)        | RabbitMQ client that listens to a given queue         | Batch       | AMQP          |
| 15  | [MQTT](streaming_spouts/mqtt.py)                   | MQTT client that subscribes and listens to a topic    | Streaming   | MQTT          |
| 16  | [MQTT](streaming_spouts/mqtt.py)                   | MQTT client that subscribes and listens to a topic    | Batch       | MQTT          |
| 17  | [Redis Pub-Sub](streaming_spouts/redis_pubsub.py)  | Redis client that subscribes to a Pub/Sub channel     | Streaming   | Redis Pub-Sub |
| 18  | [Redis Pub-Sub](streaming_spouts/redis_pubsub.py)  | Redis client that subscribes to a Pub/Sub channel     | Batch       | Redis Pub-Sub |
| 19  | [Redis Streams](streaming_spouts/redis_streams.py) | Redis client that listens to a stream                 | Streaming   | Redis Streams |
| 20  | [Redis Streams](streaming_spouts/redis_streams.py) | Redis client that listens to a stream                 | Batch       | Redis Streams |
| 21  | [AWS SNS](streaming_spouts/sns.py)                 | AWS client that listens to SNS notifications          | Streaming   | AWS SNS       |
| 22  | [AWS SNS](streaming_spouts/sns.py)                 | AWS client that listens to SNS notifications          | Batch       | AWS SNS       |
| 23  | [AWS SQS](streaming_spouts/sqs.py)                 | AWS client that listens to messages from an SQS queue | Streaming   | AWS SQS       |
| 24  | [AWS SQS](streaming_spouts/sqs.py)                 | AWS client that listens to messages from an SQS queue | Batch       | AWS SQS       |

# Streaming Spouts

## Usage

To test, first bring up all related services via the supplied docker-compose:

```bash
docker compose up -d
docker compose logs -f
```

These management consoles will be available:

| Console        | Link                    |
| -------------- | ----------------------- |
| Kafka UI       | http://localhost:8088/  |
| RabbitMQ UI    | http://localhost:15672/ |
| Localstack API | http://localhost:4566   |

Postgres can be accessed with:

```bash
docker exec -it geniusrise-postgres-1 psql -U postgres
```

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
  --args \
    cert_path=/home/ixaxaar/.ssh/quic_cert.pem \
    key_path=/home/ixaxaar/.ssh/quic_key.pem \
    host=localhost \
    port=3004
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
  --args \
    url=https://reqres.in/api/users \
    method=GET \
    interval=6 \
    body="" \
    headers='{"content-type": "application/json"}' \
    params='{"page": 2}'
```

### RabbitMQ / AMQP

```bash
genius RabbitMQ rise \
  streaming \
  --output_kafka_topic rabbitmq_test \
  --output_kafka_cluster_connection_string localhost:9094 \
  postgres \
  --postgres_host 127.0.0.1 \
  --postgres_port 5432 \
  --postgres_user postgres \
  --postgres_password postgres \
  --postgres_database geniusrise \
  --postgres_table state \
  listen \
  --args queue_name=geniusrise_test host=localhost
```

### MQTT

```bash
genius MQTT rise \
  streaming \
  --output_kafka_topic mqtt_test \
  --output_kafka_cluster_connection_string localhost:9094 \
  postgres \
  --postgres_host 127.0.0.1 \
  --postgres_port 5432 \
  --postgres_user postgres \
  --postgres_password postgres \
  --postgres_database geniusrise \
  --postgres_table state \
  listen \
  --args host=localhost port=1883 topic=geniusrise_test
```

```bash
snap install mqtt-explorer # GUI, create a topic, send a message
```

or

```bash
docker exec -it streaming-spouts-mosquitto-1 mosquitto_pub -h 127.0.0.1 -t "geniusrise_test" -m '{"test": "mqtt message"}'
```

### Redis Pub-Sub

```bash
genius RedisPubSub rise \
  streaming \
  --output_kafka_topic redispubsub_test \
  --output_kafka_cluster_connection_string localhost:9094 \
  postgres \
  --postgres_host 127.0.0.1 \
  --postgres_port 5432 \
  --postgres_user postgres \
  --postgres_password postgres \
  --postgres_database geniusrise \
  --postgres_table state \
  listen \
  --args channel=geniusrise_test host=localhost port=6380
```

Test:

```bash
redis-cli PUBLISH geniusrise_test '{"test": "redis pubsub message"}'
```

### Redis Streams

```bash
genius RedisStream rise \
  streaming \
  --output_kafka_topic redisstream_test \
  --output_kafka_cluster_connection_string localhost:9094 \
  postgres \
  --postgres_host 127.0.0.1 \
  --postgres_port 5432 \
  --postgres_user postgres \
  --postgres_password postgres \
  --postgres_database geniusrise \
  --postgres_table state \
  listen \
  --args stream_key=geniusrise_test host=localhost
```

Test:

```bash
redis-cli XADD geniusrise_test * test "redis stream message"
```

### AWS SNS

```bash
genius SNS rise \
  streaming \
  --output_kafka_topic sns_test \
  --output_kafka_cluster_connection_string localhost:9094 \
  postgres \
  --postgres_host 127.0.0.1 \
  --postgres_port 5432 \
  --postgres_user postgres \
  --postgres_password postgres \
  --postgres_database geniusrise \
  --postgres_table state \
  listen
```

Test:

```bash
aws sns create-topic --name geniusrise_test
aws sns publish --topic-arn arn:aws:sns:ap-south-1:866011655254:geniusrise_test --message '{"test": "sns message"}'
```

### AWS SQS

```bash
genius SQS rise \
  streaming \
  --output_kafka_topic sqs_test \
  --output_kafka_cluster_connection_string localhost:9094 \
  postgres \
  --postgres_host 127.0.0.1 \
  --postgres_port 5432 \
  --postgres_user postgres \
  --postgres_password postgres \
  --postgres_database geniusrise \
  --postgres_table state \
  listen \
  --args queue_url=https://sqs.ap-south-1.amazonaws.com/866011655254/geniusrise_test
```

Test:

```bash
aws sqs send-message --queue-url https://sqs.ap-south-1.amazonaws.com/866011655254/geniusrise_test --message-body '{"test": "sqs message"}'
```
