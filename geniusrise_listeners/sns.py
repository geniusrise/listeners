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

import boto3
from botocore.exceptions import ClientError
from geniusrise import Spout, State, StreamingOutput


class SNS(Spout):
    def __init__(self, output: StreamingOutput, state: State, **kwargs):
        r"""
        Initialize the SNS class.

        Args:
            output (StreamingOutput): An instance of the StreamingOutput class for saving the data.
            state (State): An instance of the State class for maintaining the state.
            **kwargs: Additional keyword arguments.

        ## Using geniusrise to invoke via command line
        ```bash
        genius SNS rise \
            streaming \
                --output_kafka_topic sns_test \
                --output_kafka_cluster_connection_string localhost:9094 \
            listen
        ```

        ## Using geniusrise to invoke via YAML file
        ```yaml
        version: "1"
        spouts:
            my_sns_spout:
                name: "SNS"
                method: "listen"
                output:
                    type: "streaming"
                    args:
                        output_topic: "sns_test"
                        kafka_servers: "localhost:9094"
        ```
        """
        super().__init__(output, state)
        self.top_level_arguments = kwargs
        self.sns = boto3.resource("sns")

    async def _listen_to_subscription(self, subscription):
        """
        📖 Listen to a specific subscription.

        Args:
            subscription: The subscription to listen to.

        Raises:
            ClientError: If unable to connect to the AWS SNS service.
        """
        try:
            while True:
                try:
                    messages = subscription.get_messages()
                    for message in messages:
                        # Enrich the data with metadata about the subscription ARN
                        enriched_data = {
                            "data": message,
                            "subscription_arn": subscription.arn,
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
                    self.log.exception(f"Failed to process SNS message: {e}")
                    current_state = self.state.get_state(self.id) or {
                        "success_count": 0,
                        "failure_count": 0,
                    }
                    current_state["failure_count"] += 1
                    self.state.set_state(self.id, current_state)
        except ClientError as e:
            self.log.error(f"Error processing SNS message from subscription {subscription.arn}: {e}")

            # Update the state using the state
            current_state = self.state.get_state(self.id) or {
                "success_count": 0,
                "failure_count": 0,
            }
            current_state["failure_count"] += 1
            self.state.set_state(self.id, current_state)

    async def _listen(self):
        """
        📖 Start listening for data from AWS SNS.

        Raises:
            ClientError: If unable to connect to the AWS SNS service.
        """
        try:
            for topic in self.sns.topics.all():
                for subscription in topic.subscriptions.all():
                    self.log.info(f"Listening to topic {topic.arn} with subscription {subscription.arn}")
                    await self._listen_to_subscription(subscription)
        except ClientError as e:
            self.log.error(f"Error listening to AWS SNS: {e}")

            # Update the state using the state
            current_state = self.state.get_state(self.id) or {
                "success_count": 0,
                "failure_count": 0,
            }
            current_state["failure_count"] += 1
            self.state.set_state(self.id, current_state)

    def listen(self):
        """
        📖 Start the asyncio event loop to listen for data from AWS SNS.
        """
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._listen())
        self.log.info("Exiting...")
