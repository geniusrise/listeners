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

import stomp
from typing import Optional
from geniusrise import Spout, State, StreamingOutput


class ActiveMQ(Spout):
    def __init__(self, output: StreamingOutput, state: State, **kwargs):
        r"""
        Initialize the ActiveMQ class.

        Args:
            output (StreamingOutput): An instance of the StreamingOutput class for saving the data.
            state (State): An instance of the State class for maintaining the state.
            **kwargs: Additional keyword arguments.

        ## Using geniusrise to invoke via command line
        ```bash
        genius ActiveMQ rise \
            streaming \
                --output_kafka_topic activemq_test \
                --output_kafka_cluster_connection_string localhost:9094 \
            none \
            listen \
                --args host=localhost port=61613 destination=my_queue
        ```

        ## Using geniusrise to invoke via YAML file
        ```yaml
        version: "1"
        spouts:
            my_activemq_spout:
                name: "ActiveMQ"
                method: "listen"
                args:
                    host: "localhost"
                    port: 61613
                    destination: "my_queue"
                output:
                    type: "streaming"
                    args:
                        output_topic: "activemq_test"
                        kafka_servers: "localhost:9094"
        ```
        """
        super().__init__(output, state)
        self.top_level_arguments = kwargs

    def listen(
        self,
        host: str,
        port: int,
        destination: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        📖 Start listening for data from the ActiveMQ server.

        Args:
            host (str): The ActiveMQ server host.
            port (int): The ActiveMQ server port.
            destination (str): The ActiveMQ destination (queue or topic).
            username (Optional[str]): The username for authentication. Defaults to None.
            password (Optional[str]): The password for authentication. Defaults to None.

        Raises:
            Exception: If unable to connect to the ActiveMQ server.
        """

        class MyListener(stomp.ConnectionListener):
            def on_message(self, headers, message):
                self._message_handler(headers, message)

        conn = stomp.Connection([(host, port)])
        conn.set_listener("", MyListener())

        if username and password:
            conn.connect(username, password, wait=True)
        else:
            conn.connect(wait=True)

        conn.subscribe(destination=destination, id=1, ack="auto")

        self.log.info(f"Listening for ActiveMQ messages from {host}:{port}, destination: {destination}")
