# pip install pyzmq - if tests are not working
import pytest
from unittest import mock
from geniusrise import State, StreamingOutput, InMemoryState
from geniusrise_listeners.zeromq import ZeroMQ

# Fixtures


# Fixture to mock the StreamingOutput object
@pytest.fixture
def mock_output():
    return mock.MagicMock(spec=StreamingOutput)


# Fixture to mock the State object
@pytest.fixture
def mock_state():
    return mock.MagicMock(spec=State)


# Fixture to mock the zmq.Context and its socket
@pytest.fixture
def mock_zmq():
    with mock.patch("zmq.Context") as mock_context:
        mock_socket = mock_context.return_value.socket.return_value
        yield mock_socket


# Test if the ZeroMQ object is properly initialized with custom arguments
def test_zeromq_init(mock_output, mock_state):
    zmq_instance = ZeroMQ(mock_output, mock_state, arg1="value1")
    assert zmq_instance.top_level_arguments == {"arg1": "value1"}


# Test the behavior when the ZeroMQ listener fails to receive a message
def test_zeromq_listen_failure(mock_output, mock_zmq):
    ims = InMemoryState()
    zmq_instance = ZeroMQ(mock_output, ims)
    endpoint = "tcp://localhost:5555"
    topic = "my_topic"
    syntax = "json"

    mock_zmq.recv_string.side_effect = Exception("Failed to receive message")

    # Simulate a single loop iteration
    zmq_instance.listen(endpoint=endpoint, topic=topic, syntax=syntax)

    assert zmq_instance.state.get_state(zmq_instance.id)["failure_count"] == 1


# Test the behavior when an unsupported socket type is provided
def test_zeromq_unsupported_socket_type(mock_output, mock_state):
    zmq_instance = ZeroMQ(mock_output, mock_state)
    endpoint = "tcp://localhost:5555"
    topic = "my_topic"
    syntax = "json"

    with pytest.raises(ValueError):
        zmq_instance.listen(
            endpoint=endpoint, topic=topic, syntax=syntax, socket_type="INVALID_TYPE"
        )


# Test both success and failure scenarios in the same test
def test_zeromq_listen_success_and_failure(mock_output, mock_state, mock_zmq):
    # Setup mock to simulate a successful JSON message followed by a non-JSON message.
    mock_zmq.recv_string.side_effect = [
        'topic_name {"key": "value"}',
        "topic_name Not a JSON message",
    ]
    # Mock the get_state method to return the appropriate values
    mock_state.get_state.side_effect = [None, {"success_count": 1, "failure_count": 0}]

    # Create an instance of ZeroMQ.
    zmq_instance = ZeroMQ(mock_output, mock_state)

    # Run the listen method. This is expected to run twice based on our mock setup (once for success and once for failure).
    try:
        zmq_instance.listen(
            endpoint="tcp://localhost:5555", topic="topic_name", syntax="json"
        )
    except Exception as e:
        # Exception raised to prevent infinite loop
        if "Expecting value" not in str(e):
            raise

    # Check that the output's save method was called once (for the successful message).
    mock_output.save.assert_called_once_with(
        {"data": {"key": "value"}, "topic": "topic_name", "syntax": "json"}
    )

    # Assert that the state's set_state method was called twice:
    #    - once for the successful message
    #    - once for the failed message
    mock_state.set_state.assert_has_calls(
        [
            mock.call(zmq_instance.id, {"success_count": 1, "failure_count": 0}),
            mock.call(zmq_instance.id, {"success_count": 1, "failure_count": 1}),
        ]
    )
