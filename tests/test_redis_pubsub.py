import pytest
import json
from unittest import mock
from geniusrise import State, StreamingOutput
from geniusrise_listeners.redis_pubsub import RedisPubSub


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
def mock_redis():
    # Mocking the redis.StrictRedis class for the RedisPubSub tests.
    with mock.patch("redis.StrictRedis") as mock_strict_redis:
        mock_redis_instance = mock_strict_redis.return_value
        yield mock_redis_instance


# Unit Tests
def test_redis_pubsub_init(mock_output, mock_state):
    """Test the __init__ method of RedisPubSub class."""
    kwargs = {"example_arg": "value"}
    redis_spout = RedisPubSub(mock_output, mock_state, **kwargs)

    assert redis_spout.top_level_arguments == kwargs


def test_listen_successful_message(mock_redis, mock_output, mock_state):
    """Test listening and successful processing of a message from Redis Pub/Sub."""
    mock_pubsub = mock_redis.pubsub.return_value
    mock_message = {
        "type": "message",
        "data": json.dumps({"sample_key": "sample_value"}),
    }
    mock_pubsub.listen.return_value = [mock_message]
    mock_state.get_state.return_value = {"success_count": 0, "failure_count": 0}

    redis_spout = RedisPubSub(mock_output, mock_state)
    redis_spout.listen(channel="test-channel")

    mock_output.save.assert_called_once()
    state_data = mock_state.get_state.return_value
    assert state_data["success_count"] == 1
    assert state_data["failure_count"] == 0


def test_listen_error_message(mock_redis, mock_output, mock_state):
    """Test error handling when processing a message from Redis Pub/Sub."""
    mock_pubsub = mock_redis.pubsub.return_value
    mock_message = {"type": "message", "data": "{malformed json}"}
    mock_pubsub.listen.return_value = [mock_message]
    mock_state.get_state.return_value = {"success_count": 0, "failure_count": 0}

    redis_spout = RedisPubSub(mock_output, mock_state)
    redis_spout.listen(channel="test-channel")

    mock_output.save.assert_not_called()
    state_data = mock_state.get_state.return_value
    assert state_data["success_count"] == 0
    assert state_data["failure_count"] == 1


def test_listen_non_message_type(mock_redis, mock_output, mock_state):
    """Test that non-'message' types are not processed."""
    mock_pubsub = mock_redis.pubsub.return_value
    mock_message = {"type": "subscribe", "data": "test-channel"}
    mock_pubsub.listen.return_value = [mock_message]

    redis_spout = RedisPubSub(mock_output, mock_state)
    redis_spout.listen(channel="test-channel")

    mock_output.save.assert_not_called()
    mock_state.get_state.assert_not_called()


def test_listen_empty_message_data(mock_redis, mock_output, mock_state):
    """Test listening and handling of an empty message from Redis Pub/Sub."""
    mock_pubsub = mock_redis.pubsub.return_value
    mock_message = {"type": "message", "data": ""}
    mock_pubsub.listen.return_value = [mock_message]
    mock_state.get_state.return_value = {"success_count": 0, "failure_count": 0}

    redis_spout = RedisPubSub(mock_output, mock_state)
    redis_spout.listen(channel="test-channel")

    mock_output.save.assert_not_called()
    state_data = mock_state.get_state.return_value
    assert state_data["success_count"] == 0
    assert state_data["failure_count"] == 1


def test_listen_unsubscribe_type(mock_redis, mock_output, mock_state):
    """Test that 'unsubscribe' types are handled correctly."""
    mock_pubsub = mock_redis.pubsub.return_value
    mock_message = {"type": "unsubscribe", "data": "test-channel"}
    mock_pubsub.listen.return_value = [mock_message]

    redis_spout = RedisPubSub(mock_output, mock_state)
    redis_spout.listen(channel="test-channel")

    mock_output.save.assert_not_called()
    mock_state.get_state.assert_not_called()


def test_listen_multiple_messages(mock_redis, mock_output, mock_state):
    """Test handling of multiple messages from Redis Pub/Sub."""
    mock_pubsub = mock_redis.pubsub.return_value
    mock_messages = [
        {"type": "message", "data": json.dumps({"key1": "value1"})},
        {"type": "message", "data": json.dumps({"key2": "value2"})},
    ]
    mock_pubsub.listen.return_value = mock_messages

    mock_state.get_state.return_value = {"success_count": 0, "failure_count": 0}

    redis_spout = RedisPubSub(mock_output, mock_state)
    redis_spout.listen(channel="test-channel")

    assert mock_output.save.call_count == 2
    state_data = mock_state.get_state.return_value
    assert state_data["success_count"] == 2
    assert state_data["failure_count"] == 0
