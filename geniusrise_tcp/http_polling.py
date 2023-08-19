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

import time

import requests  # type: ignore

from geniusrise import Spout, StreamingOutput, State


class RESTAPIPoll(Spout):
    def __init__(
        self,
        output_config: StreamingOutput,
        state_manager: State,
        url: str,
        method: str,
        interval: int = 60,
        body=None,
    ):
        super().__init__(output_config, state_manager)
        self.url = url
        self.method = method
        self.interval = interval
        self.body = body

    def listen(self):
        """
        Start polling the REST API for data.
        """
        while True:
            try:
                response = getattr(requests, self.method.lower())(self.url, json=self.body)
                response.raise_for_status()
                data = response.json()

                # Use the output_config's save method
                self.output_config.save(data)

                # Update the state using the state_manager
                current_state = self.state_manager.get_state(self.id) or {"success_count": 0, "failure_count": 0}
                current_state["success_count"] += 1
                self.state_manager.set_state(self.id, current_state)
            except Exception as e:
                self.log.error(f"Error fetching data from REST API: {e}")

                # Update the state using the state_manager
                current_state = self.state_manager.get_state(self.id) or {"success_count": 0, "failure_count": 0}
                current_state["failure_count"] += 1
                self.state_manager.set_state(self.id, current_state)

            time.sleep(self.interval)
