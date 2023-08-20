# Generic Streaming Spouts

This is a collection of a bunch of generic Spouts and (micro) Batch spouts.

Currently includes:

| Name         | Description                                     | Output Type | Input Type |
| ------------ | ----------------------------------------------- | ----------- | ---------- |
| Webhook      | Cherrypy server that accepts all HTTP API calls | Streaming   | HTTP       |
| WebhookBatch | Cherrypy server that accepts all HTTP API calls | Batch       | HTTP       |
| Kafka        | Kafka client that listens to a topic            | Streaming   | Kafka      |
| Kafka        | Kafka client that listens to a topic            | Batch       | Kafka      |
