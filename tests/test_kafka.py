# Required imports for testing
import pytest
import json
import time
from threading import Thread
from unittest import mock
from confluent_kafka import KafkaError
from geniusrise import State, StreamingOutput
from geniusrise_listeners.kafka import Kafka


# Test fixtures
@pytest.fixture
def mock_output():
    """Create a mock StreamingOutput object."""
    return mock.MagicMock(spec=StreamingOutput)


@pytest.fixture
def mock_state():
    """Create a mock State object."""
    return mock.MagicMock(spec=State)


@pytest.fixture
def mock_consumer():
    """Create a mock Kafka Consumer object."""
    return mock.MagicMock()


@pytest.fixture
def mock_message():
    """Create a mock Kafka Message object."""
    return mock.MagicMock()


# Tests


def test_kafka_init(mock_output, mock_state):
    """Test the __init__ method of Kafka class."""
    # Initializing Kafka with arbitrary arguments to check their assignment
    kwargs = {"example_arg": "value"}
    kafka_spout = Kafka(mock_output, mock_state, **kwargs)

    # Assert that the arguments passed during initialization are correctly set
    assert kafka_spout.top_level_arguments == kwargs


def test_kafka_listen_successful_data_processing(mock_output, mock_state):
    """Test a scenario where Kafka successfully processes a valid message."""
    kafka_spout = Kafka(mock_output, mock_state)

    # Mocks for the Kafka consumer and message
    mock_consumer = mock.MagicMock()
    mock_message = mock.MagicMock()

    # Define the initial state (both success and failure counts are 0)
    mock_state_data = {"success_count": 0, "failure_count": 0}
    mock_state.get_state.return_value = mock_state_data

    # Define a function to simulate the behavior of the `poll` method of Kafka consumer
    def poll_side_effect(*args, **kwargs):
        if mock_consumer.poll.call_count == 1:
            # For the first call, return a valid JSON message
            mock_message.value.return_value = json.dumps({"data": "test_data"}).encode()
            mock_message.error.return_value = None
            return mock_message
        # Terminate the listening after processing the first message
        raise KeyboardInterrupt

    mock_consumer.poll.side_effect = poll_side_effect

    # Mock the Kafka Consumer class to return our mock consumer
    with mock.patch("geniusrise_listeners.kafka.Consumer", return_value=mock_consumer):
        t = Thread(target=kafka_spout.listen, args=("test_topic", "test_group"))
        t.start()
        time.sleep(1)  # Give some time for the thread to process data
        t.join(
            timeout=2
        )  # Join the thread, but move on after 2 seconds if not finished

        # Assert if the message data was saved correctly
        mock_output.save.assert_called_with({"data": "test_data"})
        # Assert if the state's success count was updated
        assert mock_state_data["success_count"] == 1


def test_kafka_listen_json_decode_exception(mock_output, mock_state):
    kafka_spout = Kafka(mock_output, mock_state)
    mock_consumer = mock.MagicMock()
    mock_message = mock.MagicMock()

    # Invalid JSON
    mock_message.value.return_value = b"{ invalid_json"
    mock_message.error.return_value = None

    def poll_side_effect(*args, **kwargs):
        if mock_consumer.poll.call_count == 1:
            return mock_message
        raise KeyboardInterrupt

    mock_consumer.poll.side_effect = poll_side_effect

    mock_state.get_state.return_value = {"failure_count": 0}

    with mock.patch("geniusrise_listeners.kafka.Consumer", return_value=mock_consumer):
        t = Thread(target=kafka_spout.listen, args=("test_topic", "test_group"))
        t.start()
        time.sleep(1)
        t.join(timeout=2)

    assert mock_state.get_state(kafka_spout.id)["failure_count"] == 1


def test_kafka_listen_partition_end(mock_output, mock_state):
    kafka_spout = Kafka(mock_output, mock_state)
    mock_consumer = mock.MagicMock()
    mock_message = mock.MagicMock()

    # Mock Kafka partition end error
    mock_error = mock.MagicMock()
    mock_error.code.return_value = KafkaError._PARTITION_EOF
    mock_message.error.return_value = mock_error

    def poll_side_effect(*args, **kwargs):
        if mock_consumer.poll.call_count == 1:
            return mock_message
        raise KeyboardInterrupt

    mock_consumer.poll.side_effect = poll_side_effect

    mock_state.get_state.return_value = {"failure_count": 0}

    with mock.patch("geniusrise_listeners.kafka.Consumer", return_value=mock_consumer):
        t = Thread(target=kafka_spout.listen, args=("test_topic", "test_group"))
        t.start()
        time.sleep(1)
        t.join(timeout=2)

    assert mock_state.get_state(kafka_spout.id)["failure_count"] == 0


def test_kafka_listen_multiple_messages(mock_output, mock_state):
    kafka_spout = Kafka(mock_output, mock_state)
    mock_consumer = mock.MagicMock()
    mock_message = mock.MagicMock()

    mock_state_data = {"success_count": 0, "failure_count": 0}
    mock_state.get_state.return_value = mock_state_data

    mock_messages = [
        {"data": "test_data1"},
        {"data": "test_data2"},
        {"data": "test_data3"},
    ]

    def poll_side_effect(*args, **kwargs):
        if mock_consumer.poll.call_count <= len(mock_messages):
            mock_message.value.return_value = json.dumps(
                mock_messages[mock_consumer.poll.call_count - 1]
            ).encode()
            mock_message.error.return_value = None
            return mock_message
        raise KeyboardInterrupt

    mock_consumer.poll.side_effect = poll_side_effect

    with mock.patch("geniusrise_listeners.kafka.Consumer", return_value=mock_consumer):
        t = Thread(target=kafka_spout.listen, args=("test_topic", "test_group"))
        t.start()
        time.sleep(3)
        t.join(timeout=4)

        assert mock_output.save.call_count == 3
        assert mock_state_data["success_count"] == 3
