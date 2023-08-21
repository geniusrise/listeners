# 🧠 Geniusrise
# Copyright (C) 2023  geniusrise.ai
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
from typing import Optional

from confluent_kafka import Consumer, KafkaError
from geniusrise import Spout, State, StreamingOutput


class Kafka(Spout):
    def __init__(self, output: StreamingOutput, state: State, **kwargs):
        super().__init__(output, state)
        self.top_level_arguments = kwargs

    def listen(
        self,
        topic: str,
        group_id: str,
        bootstrap_servers: str = "localhost:9092",
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Start listening for data from the Kafka topic.
        """
        config = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
        }
        if username and password:
            config.update(
                {
                    "security.protocol": "SASL_PLAINTEXT",
                    "sasl.mechanisms": "PLAIN",
                    "sasl.username": username,
                    "sasl.password": password,
                }
            )
        consumer = Consumer(config)

        consumer.subscribe([topic])

        while True:
            try:
                message = consumer.poll(1.0)

                if message is None:
                    continue
                if message.error():
                    if message.error().code() == KafkaError._PARTITION_EOF:
                        self.log.info(f"Reached end of topic {topic}, partition {message.partition()}")
                    else:
                        self.log.error(f"Error while consuming message: {message.error()}")
                else:
                    # Use the output's save method
                    self.output.save(json.loads(message.value()))

                    # Update the state using the state
                    current_state = self.state.get_state(self.id) or {
                        "success_count": 0,
                        "failure_count": 0,
                    }
                    current_state["success_count"] += 1
                    self.state.set_state(self.id, current_state)
            except Exception as e:
                self.log.error(f"Error processing Kafka message: {e}")

                # Update the state using the state
                current_state = self.state.get_state(self.id) or {
                    "success_count": 0,
                    "failure_count": 0,
                }
                current_state["failure_count"] += 1
                self.state.set_state(self.id, current_state)

        consumer.close()
