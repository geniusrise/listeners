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

from typing import List

import cherrypy
from geniusrise import Spout, State, StreamingOutput


class Webhook(Spout):
    def __init__(self, output: StreamingOutput, state: State, **kwargs):
        super().__init__(output, state)
        self.top_level_arguments = kwargs  # this literally contains argparse's parsed dict
        self.buffer: List[dict] = []

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def default(self, *args, **kwargs):
        try:
            data = cherrypy.request.json

            # Add additional data about the endpoint and headers
            enriched_data = {
                "data": data,
                "endpoint": cherrypy.url(),
                "headers": dict(cherrypy.request.headers),
            }

            # Use the output's save method
            self.output.save(enriched_data)

            # Update the state using the state
            current_state = self.state.get_state(self.id) or {
                "success_count": 0,
                "failure_count": 0,
            }
            if "success_count" not in current_state.keys():
                current_state = {"success_count": 0, "failure_count": 0}
            current_state["success_count"] += 1
            self.state.set_state(self.id, current_state)

            return ""
        except Exception as e:
            self.log.error(f"Error processing webhook data: {e}")

            # Update the state using the state
            current_state = self.state.get_state(self.id) or {
                "success_count": 0,
                "failure_count": 0,
            }
            current_state["failure_count"] += 1
            self.state.set_state(self.id, current_state)

            cherrypy.response.status = 500
            return "Error processing data"

    def listen(self, endpoint: str = "*", port: int = 3000):
        """
        Start listening for data from the webhook.
        """
        # Disable CherryPy's default loggers
        cherrypy.log.access_log.propagate = False
        cherrypy.log.error_log.propagate = False

        # Set CherryPy's error and access loggers to use your logger
        cherrypy.log.error_log.addHandler(self.log)
        cherrypy.log.access_log.addHandler(self.log)

        cherrypy.config.update(
            {
                "server.socket_host": "0.0.0.0",
                "server.socket_port": port,
                "log.screen": False,  # Disable logging to the console
            }
        )
        cherrypy.tree.mount(self, "/")
        cherrypy.engine.start()
        cherrypy.engine.block()
