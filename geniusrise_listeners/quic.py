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
import json

from aioquic.asyncio import QuicConnectionProtocol, serve
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import StreamDataReceived
from geniusrise import Spout, State, StreamingOutput


class GeniusQuicProtocol(QuicConnectionProtocol):
    def __init__(self, *args, handler, **kwargs):
        super().__init__(*args, **kwargs)
        self.handler = handler

    def quic_event_received(self, event):
        if isinstance(event, StreamDataReceived):
            asyncio.create_task(self.handler(event.data, event.stream_id))


class Quic(Spout):
    def __init__(self, output: StreamingOutput, state: State, **kwargs):
        r"""
        Initialize the Quic class.

        Args:
            output (StreamingOutput): An instance of the StreamingOutput class for saving the data.
            state (State): An instance of the State class for maintaining the state.
            **kwargs: Additional keyword arguments.

        ## Using geniusrise to invoke via command line
        ```bash
        genius Quic rise \
            streaming \
                --output_kafka_topic quic_test \
                --output_kafka_cluster_connection_string localhost:9094 \
            listen \
                --args cert_path=/path/to/cert.pem key_path=/path/to/key.pem host=localhost port=4433
        ```

        ## Using geniusrise to invoke via YAML file
        ```yaml
        version: "1"
        spouts:
            my_quic_spout:
                name: "Quic"
                method: "listen"
                args:
                    cert_path: "/path/to/cert.pem"
                    key_path: "/path/to/key.pem"
                    host: "localhost"
                    port: 4433
                output:
                    type: "streaming"
                    args:
                        output_topic: "quic_test"
                        kafka_servers: "localhost:9094"
        ```
        """
        super().__init__(output, state)
        self.top_level_arguments = kwargs

    async def handle_stream_data(self, data: bytes, stream_id: int):
        """
        Handle incoming stream data.

        :param data: The incoming data.
        :param stream_id: The ID of the stream.
        """
        try:
            data = json.loads(data.decode())

            # Add additional data about the stream ID
            enriched_data = {
                "data": data,
                "stream_id": stream_id,
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
            self.log.error(f"Error processing stream data: {e}")

            # Update the state using the state
            current_state = self.state.get_state(self.id) or {
                "success_count": 0,
                "failure_count": 0,
            }
            current_state["failure_count"] += 1
            self.state.set_state(self.id, current_state)

    def listen(self, cert_path: str, key_path: str, host: str = "localhost", port: int = 4433):
        """
        📖 Start listening for data from the QUIC server.

        Args:
            cert_path (str): Path to the certificate file.
            key_path (str): Path to the private key file.
            host (str): Hostname to listen on. Defaults to "localhost".
            port (int): Port to listen on. Defaults to 4433.

        Raises:
            Exception: If unable to start the QUIC server.
        """
        configuration = QuicConfiguration(is_client=False)
        configuration.load_cert_chain(cert_path, key_path)

        loop = asyncio.get_event_loop()
        server = loop.run_until_complete(
            serve(
                host=host,
                port=port,
                configuration=configuration,
                create_protocol=lambda *args, **kwargs: GeniusQuicProtocol(
                    *args, handler=self.handle_stream_data, **kwargs
                ),
            )
        )

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.close()
            loop.run_until_complete(server.wait_closed())
            loop.close()
