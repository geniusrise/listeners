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

import grpc
from geniusrise import Spout, State, StreamingOutput
from typing import Optional
from my_service_pb2 import StreamRequest
from my_service_pb2_grpc import MyServiceStub


class Grpc(Spout):
    def __init__(self, output: StreamingOutput, state: State, **kwargs):
        r"""
        Initialize the Grpc class.

        Args:
            output (StreamingOutput): An instance of the StreamingOutput class for saving the data.
            state (State): An instance of the State class for maintaining the state.
            **kwargs: Additional keyword arguments.

        ## Using geniusrise to invoke via command line
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

        ## Using geniusrise to invoke via YAML file
        ```yaml
        version: "1"
        spouts:
            my_grpc_spout:
                name: "Grpc"
                method: "listen"
                args:
                    server_address: "localhost:50051"
                    request_data: "my_request"
                    syntax: "proto3"
                output:
                    type: "streaming"
                    args:
                        output_topic: "grpc_test"
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
                        name: "my_grpc_spout"
                        namespace: "default"
                        image: "my_grpc_spout_image"
                        replicas: 1
        ```
        """
        super().__init__(output, state)
        self.top_level_arguments = kwargs

    def listen(
        self,
        server_address: str,
        request_data: str,
        syntax: str,
        certificate: Optional[str] = None,
        client_key: Optional[str] = None,
        client_cert: Optional[str] = None,
    ):
        """
        📖 Start listening for data from the gRPC server.

        Args:
            server_address (str): The address of the gRPC server.
            request_data (str): Data to send in the request.
            syntax (str): The syntax to be used (e.g., "proto3").
            certificate (Optional[str]): Optional server certificate for SSL/TLS.
            client_key (Optional[str]): Optional client key for SSL/TLS.
            client_cert (Optional[str]): Optional client certificate for SSL/TLS.

        Raises:
            grpc.RpcError: If there is an error while processing gRPC messages.
        """
        # Use the syntax parameter as needed
        # ...

        if certificate and client_key and client_cert:
            with open(client_key, "rb") as f:
                private_key = f.read()
            with open(client_cert, "rb") as f:
                certificate_chain = f.read()
            with open(certificate, "rb") as f:
                root_certificates = f.read()

            credentials = grpc.ssl_channel_credentials(
                root_certificates=root_certificates,
                private_key=private_key,
                certificate_chain=certificate_chain,
            )
            channel = grpc.secure_channel(server_address, credentials)
        else:
            channel = grpc.insecure_channel(server_address)

        stub = MyServiceStub(channel)
        request = StreamRequest(request_data=request_data)

        try:
            for response in stub.StreamMessages(request):
                # Enrich the data with metadata about the response
                enriched_data = {
                    "data": response.response_data,
                    "syntax": syntax,  # Include the syntax in the enriched data
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

        except grpc.RpcError as e:
            self.log.error(f"Error processing gRPC message: {e}")

            # Update the state using the state
            current_state = self.state.get_state(self.id) or {
                "success_count": 0,
                "failure_count": 0,
            }
            current_state["failure_count"] += 1
            self.state.set_state(self.id, current_state)