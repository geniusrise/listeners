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

import redis  # type: ignore
from geniusrise import Spout, State, StreamingOutput


class RedisPubSub(Spout):
    def __init__(self, output: StreamingOutput, state: State, **kwargs):
        super().__init__(output, state)
        self.top_level_arguments = kwargs

    def listen(
        self,
        channel: str,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
    ):
        """
        Start listening for data from the Redis Pub/Sub channel.
        """
        self.redis = redis.StrictRedis(host=host, port=port, password=password, decode_responses=True, db=db)
        pubsub = self.redis.pubsub()
        pubsub.subscribe(channel)

        self.log.info(
            f"Listening to channel {channel} on Redis server at {self.top_level_arguments['host']}:{self.top_level_arguments['port']}"
        )

        try:
            for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])

                    # Enrich the data with metadata about the channel
                    enriched_data = {
                        "data": data,
                        "channel": channel,
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
            self.log.error(f"Error processing Redis Pub/Sub message: {e}")

            # Update the state using the state
            current_state = self.state.get_state(self.id) or {
                "success_count": 0,
                "failure_count": 0,
            }
            current_state["failure_count"] += 1
            self.state.set_state(self.id, current_state)
