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

import paho.mqtt.client as mqtt
from geniusrise import Spout, State, StreamingOutput


class MQTT(Spout):
    def __init__(self, output: StreamingOutput, state: State, **kwargs):
        super().__init__(output, state)
        self.top_level_arguments = kwargs

    def _on_connect(self, client, userdata, flags, rc):
        """
        Callback function that is called when the client connects to the broker.

        :param client: MQTT client instance.
        :param userdata: Private user data as set in Client() or userdata_set().
        :param flags: Response flags sent by the broker.
        :param rc: Connection result.
        """
        self.log.debug(f"Connected with result code {rc}")
        client.subscribe(self.topic)

    def _on_message(self, client, userdata, msg):
        """
        Callback function that is called when a message is received.

        :param client: MQTT client instance.
        :param userdata: Private user data as set in Client() or userdata_set().
        :param msg: An instance of MQTTMessage.
        """
        try:
            data = json.loads(msg.payload)

            # Enrich the data with metadata about the topic
            enriched_data = {
                "data": data,
                "topic": msg.topic,
            }

            # Use the output's save method
            self.output.save(enriched_data)

            # Update the state using the state
            current_state = self.state.get_state(self.id) or {
                "success_count": 0,
                "failure_count": 0,
            }
            current_state["success_count"] += 1
            self.state.set_state(self.id, current_state)
        except Exception as e:
            self.log.error(f"Error processing MQTT message: {e}")

            # Update the state using the state
            current_state = self.state.get_state(self.id) or {
                "success_count": 0,
                "failure_count": 0,
            }
            current_state["failure_count"] += 1
            self.state.set_state(self.id, current_state)

    def listen(
        self,
        host: str = "localhost",
        port: int = 1883,
        topic: str = "#",
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Start listening for data from the MQTT broker.
        """
        self.topic = topic
        try:
            self.log.info("Starting MQTT listener...")
            client = mqtt.Client()
            if username and password:
                client.username_pw_set(username, password)
            client.on_connect = self._on_connect
            client.on_message = self._on_message
            client.connect(host, port, 60)
            self.log.info("Waiting for messages. To exit press CTRL+C")
            client.loop_forever()
        except Exception as e:
            self.log.error(f"Error listening to MQTT: {e}")
            # Update the state using the state
            current_state = self.state.get_state(self.id) or {
                "success_count": 0,
                "failure_count": 0,
            }
            current_state["failure_count"] += 1
            self.state.set_state(self.id, current_state)
            raise
