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

import asyncio

import websockets
from geniusrise import Spout, State, StreamingOutput


class Websocket(Spout):
    def __init__(self, output: StreamingOutput, state: State, **kwargs):
        r"""
        Initialize the Websocket class.

        Args:
            output (StreamingOutput): An instance of the StreamingOutput class for saving the data.
            state (State): An instance of the State class for maintaining the state.
            **kwargs: Additional keyword arguments.

        ## Using geniusrise to invoke via command line
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
                --args host=localhost port=8765
        ```

        ## Using geniusrise to invoke via YAML file
        ```yaml
        version: "1"
        spouts:
            my_websocket_spout:
                name: "Websocket"
                method: "listen"
                args:
                    host: "localhost"
                    port: 8765
                output:
                    type: "streaming"
                    args:
                        output_topic: "websocket_test"
                        kafka_servers: "localhost:9094"
                state:
                    type: "postgres"
                    args:
                        postgres_host: "127.0.0.1"
                        postgres_port: 5432
                        postgres_user: "postgres"
                        postgres_password: "postgres"
                        postgres_database: "geniusrise"
                        postgres_table: "state"
                deploy:
                    type: "k8s"
                    args:
                        name: "my_websocket_spout"
                        namespace: "default"
                        image: "my_websocket_spout_image"
                        replicas: 1
        ```
        """
        super().__init__(output, state)
        self.top_level_arguments = kwargs

    async def __listen(self, host: str, port: int):
        """
        Start listening for data from the WebSocket server.
        """
        async with websockets.serve(self.receive_message, host, port):  # type: ignore
            await asyncio.Future()  # run forever

    async def receive_message(self, websocket, path):
        """
        Receive a message from a WebSocket client and save it along with metadata.

        Args:
            websocket: WebSocket client connection.
            path: WebSocket path.
        """
        try:
            data = await websocket.recv()

            # Add additional metadata
            enriched_data = {
                "data": data,
                "path": path,
                "client_address": websocket.remote_address,
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
            self.log.error(f"Error processing WebSocket data: {e}")

            # Update the state using the state
            current_state = self.state.get_state(self.id) or {
                "success_count": 0,
                "failure_count": 0,
            }
            current_state["failure_count"] += 1
            self.state.set_state(self.id, current_state)

    def listen(self, host: str = "localhost", port: int = 8765):
        """
        📖 Start the WebSocket server.

        Args:
            host (str): The WebSocket server host. Defaults to "localhost".
            port (int): The WebSocket server port. Defaults to 8765.

        Raises:
            Exception: If unable to start the WebSocket server.
        """
        asyncio.run(self.__listen(host, port))