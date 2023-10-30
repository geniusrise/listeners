import pytest
import socket
import time
from unittest import mock
from geniusrise import State, StreamingOutput, InMemoryState
from geniusrise_listeners.udp import (
    Udp,
)


@pytest.fixture
def mock_output():
    """Fixture to mock StreamingOutput."""
    mock_output = mock.MagicMock(spec=StreamingOutput)
    mock_output.log = mock.MagicMock()
    return mock_output


@pytest.fixture
def ims_state():
    """Fixture to create an in-memory state for the tests."""
    return InMemoryState()


@pytest.fixture
def mock_state():
    """Fixture to mock State object."""
    return mock.MagicMock(spec=State)


@pytest.fixture
def mock_udp(mock_output, mock_state):
    """Fixture to create a Udp instance with mocked output and state."""
    return Udp(mock_output, mock_state)


@pytest.fixture
def udp_server():
    """Fixture to simulate a UDP server."""

    def send_data(host, port, message):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(message.encode("utf-8"), (host, port))

    return send_data


def test_udp_init(mock_output, mock_state):
    """Test if Udp initialization with basic arguments works as expected."""
    udp = Udp(mock_output, mock_state)
    assert udp.output == mock_output
    assert udp.state == mock_state
    assert udp.top_level_arguments == {}


def test_udp_init_with_args():
    """Test if Udp initialization with custom arguments works as expected."""
    output = mock.MagicMock(spec=StreamingOutput)
    state = mock.MagicMock(spec=State)
    custom_kwargs = {
        "arg1": "value1",
        "arg2": "value2",
    }
    udp = Udp(output, state, **custom_kwargs)
    assert udp.output == output
    assert udp.state == state
    assert udp.top_level_arguments == custom_kwargs


def test_udp_init_with_add_args():
    """Test Udp initialization with additional custom arguments."""
    output = mock.MagicMock(spec=StreamingOutput)
    state = mock.MagicMock(spec=State)
    add_kwargs = {
        "arg3": "value3",
        "arg4": "value4",
    }
    udp = Udp(output, state, **add_kwargs)
    assert udp.output == output
    assert udp.state == state
    assert udp.top_level_arguments == add_kwargs


def test_udp_init_empty_custom_args(mock_output, mock_state):
    """Test Udp initialization with empty custom arguments."""
    udp = Udp(mock_output, mock_state, **{})
    assert udp.output == mock_output
    assert udp.state == mock_state
    assert udp.top_level_arguments == {}


def test_udp_init_non_string_custom_args(mock_output, mock_state):
    """Test Udp initialization with non-string custom arguments."""
    custom_kwargs = {
        "arg_int": 123,
        "arg_float": 456.789,
        "arg_list": [1, 2, 3],
        "arg_dict": {"key": "value"},
    }
    udp = Udp(mock_output, mock_state, **custom_kwargs)
    assert udp.output == mock_output
    assert udp.state == mock_state
    assert udp.top_level_arguments == custom_kwargs


def test_udp_listen_successful_data_processing(mock_output):
    """Test Udp's listen method processes data correctly."""
    state = InMemoryState()
    udp = Udp(mock_output, state)

    # Mock socket interactions
    mock_socket = mock.MagicMock()

    def side_effect(*args, **kwargs):
        if mock_socket.recvfrom.call_count == 1:  # Return data for one call
            return (b"test_data", ("localhost", 8945))
        time.sleep(10)  # Simulate a socket waiting for data

    mock_socket.recvfrom.side_effect = side_effect

    with mock.patch("socket.socket") as mock_socket_constructor:
        mock_socket_constructor.return_value.__enter__.return_value = mock_socket

        # Run the listen method in a separate thread so that we can terminate it
        from threading import Thread

        t = Thread(target=udp.listen)
        t.start()
        time.sleep(1)  # Wait for 1 second to ensure data is processed

        # stop the infinite loop by Keyboard Interrupt
        mock_socket.recvfrom.side_effect = KeyboardInterrupt

        t.join(timeout=2)  # Try to join the thread, but move on after 2 seconds

        # Check if data was correctly enriched and saved
        expected_enriched_data = {
            "data": "test_data",
            "sender_address": "localhost",
            "sender_port": 8945,
        }
        mock_output.save.assert_called_with(expected_enriched_data)

        # Check if the state was updated correctly
        assert state.get_state(udp.id)["success_count"] == 1


def test_udp_listen_no_data_received(mock_output):
    """Test Udp's listen method when no data is received."""
    state = InMemoryState()
    udp = Udp(mock_output, state)

    # Mock socket interactions
    mock_socket = mock.MagicMock()

    def side_effect(*args, **kwargs):
        time.sleep(10)  # Simulate a socket waiting for data

    mock_socket.recvfrom.side_effect = side_effect

    with mock.patch("socket.socket") as mock_socket_constructor:
        mock_socket_constructor.return_value.__enter__.return_value = mock_socket

        # Run the listen method in a separate thread so that we can terminate it
        from threading import Thread

        t = Thread(target=udp.listen)
        t.start()
        time.sleep(1)  # Wait for 1 second to ensure data is processed

        # Interrupt the socket's recvfrom method to stop the infinite loop
        mock_socket.recvfrom.side_effect = KeyboardInterrupt

        t.join(timeout=2)  # Try to join the thread, but move on after 2 seconds

        # Check if no data was saved when no data was received
        mock_output.save.assert_not_called()


def test_udp_listen_exc_handling(mock_output):
    """Test Udp's listen method handles exceptions correctly."""
    state = InMemoryState()
    udp = Udp(mock_output, state)

    # Mock socket interactions
    mock_socket = mock.MagicMock()

    def side_effect(*args, **kwargs):
        if mock_socket.recvfrom.call_count == 1:  # Return derror for one call
            return RuntimeError("Simulated socket error")
        time.sleep(10)  # Simulate a socket waiting for data

    mock_socket.recvfrom.side_effect = side_effect

    with mock.patch("socket.socket") as mock_socket_constructor:
        mock_socket_constructor.return_value.__enter__.return_value = mock_socket

        # Run the listen method in a separate thread so that we can terminate it
        from threading import Thread

        t = Thread(target=udp.listen)
        t.start()
        time.sleep(1)  # Wait for 1 second to ensure data is processed

        # stop the infinite loop by Keyboard Interrupt
        mock_socket.recvfrom.side_effect = KeyboardInterrupt

        t.join(timeout=2)  # Try to join the thread, but move on after 2 seconds

        # Check if the state was updated correctly for failure
        assert state.get_state(udp.id)["failure_count"] == 1
