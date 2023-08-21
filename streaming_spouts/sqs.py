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

import boto3
from geniusrise import Spout, State, StreamingOutput


class SQS(Spout):
    def __init__(self, output: StreamingOutput, state: State, **kwargs):
        super().__init__(output, state)
        self.top_level_arguments = kwargs
        self.sqs = boto3.client("sqs")
        self.queue_url = self.top_level_arguments.get("queue_url")

    def listen(self):
        """
        Start listening for new messages in the SQS queue.
        """
        while True:
            try:
                # Receive message from SQS queue
                response = self.sqs.receive_message(
                    QueueUrl=self.queue_url,
                    AttributeNames=["All"],
                    MaxNumberOfMessages=10,  # Fetch up to 10 messages
                    MessageAttributeNames=["All"],
                    VisibilityTimeout=0,
                    WaitTimeSeconds=0,
                )

                if "Messages" in response:
                    for message in response["Messages"]:
                        receipt_handle = message["ReceiptHandle"]

                        # Enrich the data with metadata about the message ID
                        enriched_data = {
                            "data": message,
                            "message_id": message["MessageId"],
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

                        # Delete received message from queue
                        self.sqs.delete_message(QueueUrl=self.queue_url, ReceiptHandle=receipt_handle)
                else:
                    self.log.info("No messages available in the queue.")
            except Exception as e:
                self.log.error(f"Error processing SQS message: {e}")

                # Update the state using the state
                current_state = self.state.get_state(self.id) or {
                    "success_count": 0,
                    "failure_count": 0,
                }
                current_state["failure_count"] += 1
                self.state.set_state(self.id, current_state)
