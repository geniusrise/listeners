import pytest
import asyncio
import logging
from unittest import mock
from geniusrise import State, StreamingOutput
from geniusrise_listeners.redis_streams import RedisStream

# Fixtures


@pytest.fixture
def mock_output():
    """Fixture to mock the StreamingOutput."""
    return mock.MagicMock(spec=StreamingOutput)


@pytest.fixture
def mock_state():
    """Fixture to mock the State."""
    return mock.MagicMock(spec=State)


@pytest.fixture
def mock_redis_client():
    """Fixture to mock the Redis client."""
    with mock.patch("redis.StrictRedis") as mock_client:
        yield mock_client.return_value


def test_redis_stream_initialization(mock_output, mock_state):
    """Test if the RedisStream is initialized with the provided top-level arguments."""
    redis_stream = RedisStream(
        output=mock_output, state=mock_state, some_key="some_value"
    )
    assert redis_stream.top_level_arguments == {"some_key": "some_value"}


def test_redis_stream_listen_success(mock_output, mock_state, mock_redis_client):
    """Test if the RedisStream listener processes messages correctly from the stream."""
    # Mocked messages from the Redis stream
    mock_messages = [
        ("msg_id_1", {"key1": "value1", "key2": "value2"}),
        ("msg_id_2", {"key3": "value3", "key4": "value4"}),
    ]
    mock_redis_client.xread.return_value = [("my_stream", mock_messages)]

    redis_stream = RedisStream(output=mock_output, state=mock_state)
    loop = asyncio.get_event_loop()

    # Run the listener for a limited time using a timeout
    with pytest.raises(asyncio.TimeoutError):
        loop.run_until_complete(
            asyncio.wait_for(redis_stream._listen(stream_key="my_stream"), timeout=1)
        )

    # Check if the output's save method was called with the correct arguments
    mock_output.save.assert_called_with(
        {
            "data": {"key3": "value3", "key4": "value4"},
            "stream_key": "my_stream",
            "message_id": "msg_id_2",
        }
    )


def test_redis_stream_with_last_id_in_state(mock_output, mock_state, mock_redis_client):
    """Test if the RedisStream listener reads messages starting from the correct last_id in state."""
    # Mocked state containing a last_id
    mock_state.get_state.return_value = {
        "success_count": 0,
        "failure_count": 0,
        "last_id": "msg_id_0",
    }

    redis_stream = RedisStream(output=mock_output, state=mock_state)
    loop = asyncio.get_event_loop()

    # Run the listener for a limited time using a timeout
    with pytest.raises(asyncio.TimeoutError):
        loop.run_until_complete(
            asyncio.wait_for(redis_stream._listen(stream_key="my_stream"), timeout=1)
        )

    # Check if the Redis stream was read starting from the correct last_id
    mock_redis_client.xread.assert_called_once_with(
        {"my_stream": "msg_id_0", "count": 10, "block": 1000}
    )


def test_redis_stream_listen_exception(mock_output, mock_state, mock_redis_client):
    """Test how the RedisStream listener handles exceptions during reading."""
    # Mocking an exception when reading from the Redis stream
    mock_redis_client.xread.side_effect = Exception("Redis error")
    # Mock the return value for the get_state call
    mock_state.get_state.return_value = {
        "success_count": 0,
        "failure_count": 0,
        "last_id": "0",
    }

    redis_stream = RedisStream(output=mock_output, state=mock_state)
    loop = asyncio.get_event_loop()

    # Run the listener for a limited time using a timeout
    with pytest.raises(asyncio.TimeoutError):
        loop.run_until_complete(
            asyncio.wait_for(redis_stream._listen(stream_key="my_stream"), timeout=1)
        )

    # Check if the state was updated correctly after the exception
    mock_state.set_state.assert_called_with(
        redis_stream.id, {"success_count": 0, "failure_count": 1, "last_id": "0"}
    )


def test_redis_stream_connection_exception(mock_output, mock_state, caplog):
    """Test how the RedisStream listener handles connection errors."""
    # Mock the Redis client to raise a connection error
    with mock.patch(
        "redis.StrictRedis", side_effect=Exception("Connection error")
    ) as mock_redis:
        caplog.set_level(logging.ERROR)  # To capture error logs
        redis_stream = RedisStream(output=mock_output, state=mock_state)
        loop = asyncio.get_event_loop()

        # Run the listener for a limited time using a timeout
        loop.run_until_complete(
            asyncio.wait_for(redis_stream._listen(stream_key="my_stream"), timeout=1)
        )

        # Check if the error was logged correctly
        assert "Error processing Redis Stream message: Connection error" in caplog.text
