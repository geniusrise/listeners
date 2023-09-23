![banner](./assets/banner.jpg)

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

# Listeners

This is a collection of generic streaming listeners (Spouts).

**Table of Contents**

- [Listeners](#listeners)
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
    - [socket.io](#socketio)
    - [ActiveMQ](#activemq)
    - [Kinesis](#kinesis)
    - [Grpc](#grpc)
    - [ZeroMQ](#zeromq)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

Includes:

| No. | Name                                        | Description                                           | Output Type | Input Type    |
| --- | ------------------------------------------- | ----------------------------------------------------- | ----------- | ------------- |
| 1   | [Webhook](listeners/webhook.py)             | Cherrypy server that accepts all HTTP API calls       | Streaming   | HTTP          |
| 2   | [Kafka](listeners/kafka.py)                 | Kafka client that listens to a topic                  | Streaming   | Kafka         |
| 3   | [Websocket](listeners/websocket.py)         | Websocket server that listens to a socket             | Streaming   | Websocket     |
| 4   | [UDP](listeners/udp.py)                     | UDP server that listens to a given port               | Streaming   | UDP           |
| 5   | [QUIC](listeners/quic.py)                   | Aioquic server that listens to a given port           | Streaming   | QUIC          |
| 6   | [HTTP Polling](listeners/http_polling.py)   | HTTP client that keeps polling an API                 | Streaming   | HTTP          |
| 7   | [RabbitMQ / AMQP](listeners/amqp.py)        | RabbitMQ client that listens to a given queue         | Streaming   | AMQP          |
| 8   | [MQTT](listeners/mqtt.py)                   | MQTT client that subscribes and listens to a topic    | Streaming   | MQTT          |
| 9   | [Redis Pub-Sub](listeners/redis_pubsub.py)  | Redis client that subscribes to a Pub/Sub channel     | Streaming   | Redis Pub-Sub |
| 10  | [Redis Streams](listeners/redis_streams.py) | Redis client that listens to a stream                 | Streaming   | Redis Streams |
| 11  | [AWS SNS](listeners/sns.py)                 | AWS client that listens to SNS notifications          | Streaming   | AWS SNS       |
| 12  | [AWS SQS](listeners/sqs.py)                 | AWS client that listens to messages from an SQS queue | Streaming   | AWS SQS       |
| 13  | [SocketIo](listeners/socketio.py)           | SocketIo client that listens to a namespace           | Streaming   | SocketIo      |
| 14  | [ActiveMQ](listeners/activemq.py)           | ActiveMQ client that listens to a queue               | Streaming   | ActiveMQ      |
| 15  | [Kinesis](listeners/kinesis.py)             | Kinesis client that listens to a stream               | Streaming   | Kinesis       |
| 16  | [Grpc](listeners/grpc.py)                   | gRPC client that listens to a server                  | Streaming   | gRPC          |
| 17  | [ZeroMQ](listeners/zeromq.py)               | ZeroMQ client that listens to a topic                 | Streaming   | ZeroMQ        |

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
  --args queue_name=geniusrise_test host=localhost username=admin password=admin
```

Test:

```bash
Go to http://localhost:15672/#/queues/%2F/geniusrise_test
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

### socket.io

```bash
genius SocketIo rise \
    streaming \
    --output_kafka_topic socketio_test \
    --output_kafka_cluster_connection_string localhost:9094 \
    postgres \
    --postgres_host 127.0.0.1 \
    --postgres_port 5432 \
    --postgres_user postgres \
    --postgres_password postgres \
    --postgres_database geniusrise \
    --postgres_table state \
    listen \
    --args url=http://localhost:3000 namespace=/chat
```

Test:

```bash
# Use a SocketIo client to emit a message to the specified namespace.
```

### ActiveMQ

```bash
genius ActiveMQ rise \
    streaming \
    --output_kafka_topic activemq_test \
    --output_kafka_cluster_connection_string localhost:9094 \
    postgres \
    --postgres_host 127.0.0.1 \
    --postgres_port 5432 \
    --postgres_user postgres \
    --postgres_password postgres \
    --postgres_database geniusrise \
    --postgres_table state \
    listen \
    --args host=localhost port=61613 destination=my_queue
```

Test:

```bash
# Use an ActiveMQ client to send a message to the specified destination.
```

### Kinesis

```bash
genius Kinesis rise \
    streaming \
    --output_kafka_topic kinesis_test \
    --output_kafka_cluster_connection_string localhost:9094 \
    postgres \
    --postgres_host 127.0.0.1 \
    --postgres_port 5432 \
    --postgres_user postgres \
    --postgres_password postgres \
    --postgres_database geniusrise \
    --postgres_table state \
    listen \
    --args stream_name=my_stream shard_id=shardId-000000000000
```

Test:

```bash
# Use the AWS CLI or SDK to put a record into the specified Kinesis stream.
```

### Grpc

```bash
genius Grpc rise \
    streaming \
    --output_kafka_topic grpc_test \
    --output_kafka_cluster_connection_string localhost:9094 \
    postgres \
    --postgres_host 127.0.0.1 \
    --postgres_port 5432 \
    --postgres_user postgres \
    --postgres_password postgres \
    --postgres_database geniusrise \
    --postgres_table state \
    listen \
    --args server_address=localhost:50051 request_data=my_request syntax=proto3
```

Test:

```bash
# Use a gRPC client to send a message to the specified server address.
```

### ZeroMQ

```bash
genius ZeroMQ rise \
    streaming \
    --output_kafka_topic zmq_test \
    --output_kafka_cluster_connection_string localhost:9094 \
    postgres \
    --postgres_host 127.0.0.1 \
    --postgres_port 5432 \
    --postgres_user postgres \
    --postgres_password postgres \
    --postgres_database geniusrise \
    --postgres_table state \
    listen \
    --args endpoint=tcp://localhost:5555 topic=my_topic syntax=json
```

Test:

```bash
# Use a ZeroMQ client to send a message to the specified endpoint and topic.
```
