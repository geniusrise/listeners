# Required libraries are imported
import pytest
import json
import asyncio
from unittest.mock import MagicMock, patch, ANY
from geniusrise import State, StreamingOutput
from geniusrise_listeners.quic import Quic


# Fixtures are defined for the pytest framework. These are reusable components for the test functions.
@pytest.fixture
def mock_output():
    # A MagicMock object mimicking the StreamingOutput class is returned
    return MagicMock(spec=StreamingOutput)


@pytest.fixture
def mock_state():
    # A MagicMock object mimicking the State class is returned
    return MagicMock(spec=State)


@pytest.fixture
def quic_instance(mock_output, mock_state):
    # A Quic instance is created with mocked output and state, using a patched QuicConfiguration
    with patch("geniusrise_listeners.quic.QuicConfiguration"):
        return Quic(mock_output, mock_state, extra_arg="extra_value")


@pytest.fixture
def mock_configuration():
    # A mock for QuicConfiguration is created and yielded for use in tests
    with patch("geniusrise_listeners.quic.QuicConfiguration") as mock:
        yield mock


@pytest.fixture
def mock_serve():
    # A mock for the serve function is created and yielded for use in tests
    with patch("geniusrise_listeners.quic.serve") as mock:
        yield mock


@pytest.fixture
def mock_loop():
    # A mock for the asyncio event loop is created with mocked methods run_until_complete, run_forever, and close
    with patch("geniusrise_listeners.quic.asyncio.get_event_loop") as mock:
        mock.return_value.run_until_complete = MagicMock()
        mock.return_value.run_forever = MagicMock()
        mock.return_value.close = MagicMock()
        yield mock.return_value


@pytest.fixture
def mock_server():
    # A mock for QuicConnectionProtocol is created with a mocked wait_closed method
    with patch("geniusrise_listeners.quic.QuicConnectionProtocol") as mock:
        mock.wait_closed = MagicMock()
        yield mock


# Tests for Quic class initialization
def test_quic_initialization(quic_instance):
    # Verifies if the Quic instance has the correct 'extra_arg' attribute
    assert quic_instance.top_level_arguments["extra_arg"] == "extra_value"


def test_quic_initialization_basic(mock_output, mock_state):
    # Tests the basic initialization of the Quic class
    quic = Quic(mock_output, mock_state)
    assert quic.output == mock_output
    assert quic.state == mock_state
    # Verifies that 'top_level_arguments' attribute is not set if not provided
    assert not hasattr(quic, 'top_level_arguments') or not quic.top_level_arguments


def test_quic_initialization_extra_args(mock_output, mock_state):
    # Tests the initialization of the Quic class with extra arguments
    quic = Quic(mock_output, mock_state, key1="value1", key2="value2")
    # Verifies the 'top_level_arguments' dictionary has the correct keys and values
    assert quic.top_level_arguments["key1"] == "value1"
    assert quic.top_level_arguments["key2"] == "value2"


@patch("json.loads")
def test_handle_stream_data_successful(mock_loads, quic_instance, mock_output, mock_state):
    # Mocks json.loads method to return a sample dictionary
    mock_loads.return_value = {"key": "value"}
    stream_data = json.dumps({"key": "value"}).encode()

    # Executes the handle_stream_data method
    asyncio.run(quic_instance.handle_stream_data(stream_data, 1))

    # Verifies that the output's save method was called with the correct data
    mock_output.save.assert_called_once_with({
        "data": {"key": "value"},
        "stream_id": 1,
    })

    # Verifies that the state was updated
    mock_state.set_state.assert_called_once()


@patch("json.loads")
def test_handle_stream_data_failure(mock_loads, quic_instance, mock_output, mock_state):
    # Mocks json.loads method to raise an exception
    mock_loads.side_effect = Exception("JSON Decode Error")
    stream_data = b"invalid_json_data"

    # Executes the handle_stream_data method
    asyncio.run(quic_instance.handle_stream_data(stream_data, 1))

    # Ensures that the output's save method was never called
    mock_output.save.assert_not_called()

    # Verifies that the state's failure_count was updated
    mock_state.get_state.assert_called_once_with(quic_instance.id)
    mock_state.set_state.assert_called_once()


@patch('geniusrise_listeners.quic.serve')
@patch('geniusrise_listeners.quic.asyncio')
@patch('geniusrise_listeners.quic.QuicConfiguration')
def test_listen_setup(mock_QuicConfiguration, mock_asyncio, mock_serve, quic_instance):
    # Mocks and preparations for the test
    mock_loop = MagicMock()
    mock_asyncio.get_event_loop.return_value = mock_loop
    mock_configuration = MagicMock()
    mock_QuicConfiguration.return_value = mock_configuration
    cert_path = '/cert/path'
    key_path = '/key/path'
    host = 'host'
    port = 1234

    # Executes the listen method
    quic_instance.listen(cert_path=cert_path, key_path=key_path, host=host, port=port)
    # Verifies that the QuicConfiguration was loaded with the correct certificate and key
    mock_configuration.load_cert_chain.assert_called_once_with(cert_path, key_path)
    # Verifies that the server was scheduled to start with the correct parameters
    mock_serve.assert_called_once_with(
        host=host,
        port=port,
        configuration=mock_configuration,
        create_protocol=ANY
    )
    # Verifies that the event loop's run_forever method was called
    mock_loop.run_forever.assert_called_once()


def test_listen_starts_server(quic_instance, mock_configuration, mock_serve, mock_loop):
    # Variables for the test
    cert_path = '/cert/path'
    key_path = '/key/path'
    host = 'host'
    port = 1234

    # Executes the listen method
    quic_instance.listen(cert_path=cert_path, key_path=key_path, host=host, port=port)

    # Verifies the configuration and server setup was done once
    mock_configuration.assert_called_once()
    mock_serve.assert_called_once_with(
        host=host,
        port=port,
        configuration=ANY,
        create_protocol=ANY
    )
    # Verifies that the event loop's run_forever and close methods were called
    assert mock_loop.run_forever.call_count == 1
    assert mock_loop.close.call_count == 1


def test_listen_server_exception_handling(quic_instance, mock_configuration, mock_serve, mock_loop, mock_server):
    # Variables for the test
    cert_path = '/cert/path'
    key_path = '/key/path'
    host = 'host'
    port = 1234

    # Sets up mocks to simulate an exception during server startup
    mock_serve.return_value = mock_server
    mock_loop.run_until_complete.side_effect = Exception("Server error")

    # Attempts to start the server and expects an exception
    with pytest.raises(Exception) as excinfo:
        quic_instance.listen(cert_path=cert_path, key_path=key_path, host=host, port=port)

    # Verifies the exception message is as expected
    assert "Server error" in str(excinfo.value)
