import pytest
from unittest import mock
from geniusrise import State, StreamingOutput
import json
from geniusrise_listeners.amqp import (
    RabbitMQ,
)


@pytest.fixture
def mock_output():
    """Fixture for mocking StreamingOutput object."""
    return mock.MagicMock(spec=StreamingOutput)


@pytest.fixture
def mock_state():
    """Fixture for mocking State object."""
    return mock.MagicMock(spec=State)


@pytest.fixture
def mock_pika():
    """Fixture for mocking pika connection, parameters, and credentials."""
    with mock.patch("pika.BlockingConnection") as mock_conn, mock.patch(
        "pika.ConnectionParameters"
    ) as mock_params, mock.patch("pika.PlainCredentials") as mock_cred:
        mock_channel = mock_conn.return_value.channel.return_value
        yield mock_channel, mock_params, mock_cred


def test_rabbitmq_initialization(mock_output, mock_state):
    """Test the initialization of RabbitMQ object with custom arguments."""
    rabbitmq = RabbitMQ(mock_output, mock_state, test_arg="value")
    assert rabbitmq.top_level_arguments == {"test_arg": "value"}


def test_rabbitmq_listen_without_auth(mock_pika, mock_output, mock_state):
    """Test RabbitMQ listen functionality without authentication."""
    mock_channel, _, _ = mock_pika
    rabbitmq = RabbitMQ(mock_output, mock_state)
    rabbitmq.listen(queue_name="my_queue", host="localhost")
    mock_channel.queue_declare.assert_called_once_with(queue="my_queue", durable=True)
    mock_channel.basic_consume.assert_called_once()


def test_rabbitmq_listen_with_auth(mock_pika, mock_output, mock_state):
    """Test RabbitMQ listen functionality with authentication."""
    mock_channel, mock_params, mock_cred = mock_pika
    rabbitmq = RabbitMQ(mock_output, mock_state)
    rabbitmq.listen(
        queue_name="my_queue",
        host="localhost",
        username="test_user",
        password="test_pass",
    )

    mock_cred.assert_called_once_with("test_user", "test_pass")
    mock_channel.queue_declare.assert_called_once_with(queue="my_queue", durable=True)
    mock_channel.basic_consume.assert_called_once()


def test_callback_success(mock_pika, mock_output, mock_state):
    """Test successful callback handling with valid JSON message."""
    rabbitmq = RabbitMQ(mock_output, mock_state)
    mock_ch = mock.Mock()
    mock_method = mock.Mock(routing_key="test_key")
    mock_properties = mock.Mock(headers={})
    body = json.dumps({"key": "value"})

    # Mock the return value for get_state
    mock_state.get_state.return_value = {"success_count": 0, "failure_count": 0}
    rabbitmq._callback(mock_ch, mock_method, mock_properties, body)
    mock_state.set_state.assert_called_once()  # Ensure the state was updated once

    # Extract the arguments passed to set_state
    args, kwargs = mock_state.set_state.call_args

    assert "success_count" in args[1]
    assert args[1]["success_count"] == 1


def test_callback_error(mock_pika, mock_output, mock_state):
    """Test callback handling with invalid JSON message triggering an error."""
    rabbitmq = RabbitMQ(mock_output, mock_state)
    mock_ch = mock.Mock()
    mock_method = mock.Mock(routing_key="test_key")
    mock_properties = mock.Mock(headers={})
    body = "invalid json"  # Non-JSON body to trigger an exception

    # Mock the return value for get_state
    mock_state.get_state.return_value = {"success_count": 0, "failure_count": 0}
    rabbitmq._callback(mock_ch, mock_method, mock_properties, body)
    # Ensure the state was updated once
    mock_state.set_state.assert_called_once()

    # Extract the arguments passed to set_state
    args, kwargs = mock_state.set_state.call_args

    assert "failure_count" in args[1]
    assert args[1]["failure_count"] == 1


def test_rabbitmq_listen_no_auth_provided(mock_pika, mock_output, mock_state):
    """Test RabbitMQ listen functionality when no authentication is provided."""
    mock_channel, mock_params, _ = mock_pika
    rabbitmq = RabbitMQ(mock_output, mock_state)

    rabbitmq.listen(queue_name="my_queue", host="localhost")
    mock_channel.queue_declare.assert_called_once_with(queue="my_queue", durable=True)
    mock_params.assert_called_once_with(host="localhost")


def test_callback_with_non_json_body(mock_pika, mock_output, mock_state):
    """Test callback handling when receiving a non-JSON formatted message."""
    rabbitmq = RabbitMQ(mock_output, mock_state)
    mock_ch = mock.Mock()
    mock_method = mock.Mock(routing_key="test_key")
    mock_properties = mock.Mock(headers={})
    body = "not a json string"

    # Mock the return value for get_state
    mock_state.get_state.return_value = {"success_count": 0, "failure_count": 0}
    rabbitmq._callback(mock_ch, mock_method, mock_properties, body)
    # Ensure the state was updated once
    mock_state.set_state.assert_called_once()

    # Extract the arguments passed to set_state
    args, kwargs = mock_state.set_state.call_args

    assert "failure_count" in args[1]
    assert args[1]["failure_count"] == 1
