import pytest
from unittest import mock
from geniusrise import State, StreamingOutput
from geniusrise_listeners.websocket import Websocket
import asyncio
from unittest.mock import AsyncMock


# Mock output fixture that simulates a StreamingOutput
@pytest.fixture
def mock_output():
    return mock.MagicMock(spec=StreamingOutput)


# Mock state fixture that simulates the State
@pytest.fixture
def mock_state():
    return mock.MagicMock(spec=State)


# Fixture to create a mocked Websocket instance
@pytest.fixture
def mock_websocket(mock_output, mock_state):
    return Websocket(mock_output, mock_state)


# Tests initialization of the WebSocket with custom arguments
def test_websocket_init_with_args(mock_output, mock_state):
    custom_kwargs = {
        "arg1": "value1",
        "arg2": "value2",
    }
    websocket = Websocket(mock_output, mock_state, **custom_kwargs)
    assert websocket.output == mock_output
    assert websocket.state == mock_state
    assert websocket.top_level_arguments == custom_kwargs


# Tests initialization of the WebSocket with non-string custom arguments
def test_websocket_init_non_string_custom_args(mock_output, mock_state):
    custom_kwargs = {
        "arg_int": 123,
        "arg_float": 456.789,
        "arg_list": [1, 2, 3],
        "arg_dict": {"key": "value"},
    }
    websocket = Websocket(mock_output, mock_state, **custom_kwargs)
    assert websocket.output == mock_output
    assert websocket.state == mock_state
    assert websocket.top_level_arguments == custom_kwargs


# Tests the receive_message method of the Websocket class for a successful data reception
def test_receive_message_successful(mock_websocket):
    # Simulating a state with success and failure counts
    mock_websocket.state.get_state.return_value = {
        "success_count": 0,
        "failure_count": 0,
    }
    mock_websocket.state.set_state = mock.MagicMock()
    mock_websocket.recv = AsyncMock(return_value="sample_data")
    mock_websocket.remote_address = ("127.0.0.1", 8765)
    path = "/test"

    # Simulating the async call to receive_message method
    asyncio.run(mock_websocket.receive_message(mock_websocket, path))

    # Assertions to ensure correct methods were called
    expected_data = {
        "data": "sample_data",
        "path": path,
        "client_address": ("127.0.0.1", 8765),
    }
    mock_websocket.output.save.assert_called_once_with(expected_data)
    mock_websocket.state.set_state.assert_called_once_with(
        mock_websocket.id, {"success_count": 1, "failure_count": 0}
    )


# Tests the receive_message method of the Websocket class for a data reception failure
def test_receive_message_failure(mock_websocket):
    # Simulating a state with success and failure counts
    mock_websocket.state.get_state.return_value = {
        "success_count": 0,
        "failure_count": 0,
    }
    mock_websocket.state.set_state = mock.MagicMock()
    mock_websocket.recv = AsyncMock(side_effect=Exception("Error!"))
    mock_websocket.remote_address = ("127.0.0.1", 8765)
    path = "/test"

    # Simulating the async call to receive_message method
    asyncio.run(mock_websocket.receive_message(mock_websocket, path))

    # Assertions to ensure correct methods were called or not called
    mock_websocket.output.save.assert_not_called()
    mock_websocket.state.set_state.assert_called_once_with(
        mock_websocket.id, {"success_count": 0, "failure_count": 1}
    )
