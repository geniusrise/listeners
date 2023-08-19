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

from geniusrise import Spout, StreamingOutput, State


class Udp(Spout):
    def __init__(
        self,
        output_config: StreamingOutput,
        state_manager: State,
        host: str = "localhost",
        port: int = 12345,
    ):
        super().__init__(output_config, state_manager)
        self.host = host
        self.port = port

    def listen(self):
        """
        Start listening for data from the UDP server.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind((self.host, self.port))
            while True:
                try:
                    data, addr = s.recvfrom(1024)

                    # Use the output_config's save method
                    self.output_config.save(data)

                    # Update the state using the state_manager
                    current_state = self.state_manager.get_state(self.id) or {"success_count": 0, "failure_count": 0}
                    current_state["success_count"] += 1
                    self.state_manager.set_state(self.id, current_state)
                except Exception as e:
                    self.log.error(f"Error processing UDP data: {e}")

                    # Update the state using the state_manager
                    current_state = self.state_manager.get_state(self.id) or {"success_count": 0, "failure_count": 0}
                    current_state["failure_count"] += 1
                    self.state_manager.set_state(self.id, current_state)
