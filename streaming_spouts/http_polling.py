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
from typing import Optional, Dict

import requests
from requests.exceptions import HTTPError, RequestException

from geniusrise import Spout, StreamingOutput, State


class RESTAPIPoll(Spout):
    def __init__(self, output: StreamingOutput, state: State, **kwargs):
        super().__init__(output, state)
        self.top_level_arguments = kwargs

    def poll_api(
        self,
        url: str,
        method: str,
        body: Optional[Dict] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
    ):
        """
        Poll the REST API for data.

        :param url: The API endpoint.
        :param method: The HTTP method (GET, POST, etc.).
        :param body: The request body.
        :param headers: The request headers.
        :param params: The request query parameters.
        """
        try:
            response = getattr(requests, method.lower())(url, json=body, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            # Add additional data about the request
            enriched_data = {"data": data, "url": url, "method": method, "headers": headers, "params": params}

            # Use the output's save method
            self.output.save(enriched_data)

            # Update the state using the state
            current_state = self.state.get_state(self.id) or {"success_count": 0, "failure_count": 0}
            current_state["success_count"] += 1
            self.state.set_state(self.id, current_state)
        except HTTPError:
            self.log.error(
                f"HTTP error {response.status_code} when fetching data from {url}. Response: {response.text}"
            )
        except RequestException as e:
            self.log.error(f"Error fetching data from REST API: {e}")
        except Exception as e:
            self.log.error(f"Unexpected error: {e}")

            # Update the state using the state
            current_state = self.state.get_state(self.id) or {"success_count": 0, "failure_count": 0}
            current_state["failure_count"] += 1
            self.state.set_state(self.id, current_state)

    def listen(
        self,
        url: str,
        method: str,
        interval: int = 60,
        body: Optional[Dict] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
    ):
        """
        Start polling the REST API for data.

        :param url: The API endpoint.
        :param method: The HTTP method (GET, POST, etc.).
        :param interval: The polling interval in seconds.
        :param body: The request body.
        :param headers: The request headers.
        :param params: The request query parameters.
        """

        while True:
            self.poll_api(url, method, body, headers, params)
            time.sleep(interval)
