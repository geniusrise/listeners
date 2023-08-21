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

import socket

from geniusrise import Spout, State, StreamingOutput


class Udp(Spout):
    def __init__(self, output: StreamingOutput, state: State, **kwargs):
        super().__init__(output, state)
        self.top_level_arguments = kwargs

    def listen(self, host: str = "localhost", port: int = 12345):
        """
        Start listening for data from the UDP server.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind((host, port))
            while True:
                try:
                    data, addr = s.recvfrom(1024)

                    # Enrich the data with metadata about the sender's address and port
                    enriched_data = {
                        "data": data.decode("utf-8"),  # Assuming the data is a utf-8 encoded string
                        "sender_address": addr[0],
                        "sender_port": addr[1],
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
                    self.log.error(f"Error processing UDP data: {e}")

                    # Update the state using the state
                    current_state = self.state.get_state(self.id) or {
                        "success_count": 0,
                        "failure_count": 0,
                    }
                    current_state["failure_count"] += 1
                    self.state.set_state(self.id, current_state)
