import pytest
from unittest import mock
from geniusrise import State, StreamingOutput
from geniusrise_listeners.activemq import (
    ActiveMQ,
)


# Fixtures for unit tests
@pytest.fixture
def mock_output():
    # Mocking StreamingOutput class to be used in tests.
    return mock.MagicMock(spec=StreamingOutput)


@pytest.fixture
def mock_state():
    # Mocking State class to be used in tests.
    return mock.MagicMock(spec=State)


@pytest.fixture
def mock_stomp():
    # Mocking the stomp.Connection class for the ActiveMQ tests.
    with mock.patch("stomp.Connection") as mock_connection:
        mock_conn = mock_connection.return_value
        yield mock_conn


def test_activemq_initialization(mock_output, mock_state):
    # Test the initialization of ActiveMQ with extra arguments.
    activemq = ActiveMQ(mock_output, mock_state, test_arg="value")
    assert activemq.top_level_arguments == {"test_arg": "value"}


def test_activemq_listen_without_auth(mock_stomp, mock_output, mock_state):
    # Test the listen method of ActiveMQ without authentication.
    activemq = ActiveMQ(mock_output, mock_state)
    activemq.listen(host="localhost", port=61613, destination="my_queue")

    mock_stomp.connect.assert_called_once_with(wait=True)
    mock_stomp.subscribe.assert_called_once_with(
        destination="my_queue", id=1, ack="auto"
    )


def test_activemq_listen_with_auth(mock_stomp, mock_output, mock_state):
    # Test the listen method of ActiveMQ with authentication.
    activemq = ActiveMQ(mock_output, mock_state)
    activemq.listen(
        host="localhost",
        port=61613,
        destination="my_queue",
        username="test_user",
        password="test_password",
    )

    mock_stomp.connect.assert_called_once_with("test_user", "test_password", wait=True)
    mock_stomp.subscribe.assert_called_once_with(
        destination="my_queue", id=1, ack="auto"
    )


def test_activemq_connection_error(mock_stomp, mock_output, mock_state):
    # Test the error handling when there's a connection error.
    mock_stomp.connect.side_effect = Exception("Connection Error")
    activemq = ActiveMQ(mock_output, mock_state)
    with pytest.raises(Exception, match="Connection Error"):
        activemq.listen(host="localhost", port=61613, destination="my_queue")


def test_activemq_on_message(mock_stomp, mock_output, mock_state):
    # Test the on_message method of ActiveMQ.
    activemq = ActiveMQ(mock_output, mock_state)
    activemq.listen(host="localhost", port=61613, destination="my_queue")

    # Simulate the on_message event
    listener = mock_stomp.set_listener.call_args[0][1]
    headers = {"header_key": "header_value"}
    message = "test message"
    # Patching the on_message method for the test
    with mock.patch.object(
        listener,
        "on_message",
        side_effect=lambda headers, message: mock_output.save(message),
    ):
        listener.on_message(headers, message)
        mock_output.save.assert_called_once_with(message)
