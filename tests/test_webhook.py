import pytest
import base64
import cherrypy
from unittest import mock
from geniusrise import State, StreamingOutput, InMemoryState
from geniusrise_listeners.webhook import (
    Webhook,
)


# Fixtures
@pytest.fixture
def mock_output():
    return mock.MagicMock(spec=StreamingOutput)


@pytest.fixture
def mock_state():
    return mock.MagicMock(spec=State)


@pytest.fixture
def mock_webhook(mock_output, mock_state):
    return Webhook(mock_output, mock_state)


@pytest.fixture
def mock_request():
    with mock.patch("cherrypy.request") as mock_request:
        yield mock_request


@pytest.fixture
def mock_cherrypy_engine():
    with mock.patch("cherrypy.engine") as mock_engine:
        yield mock_engine


def test_webhook_initialization(mock_output, mock_state):
    # Testing initialization
    webhook = Webhook(mock_output, mock_state)
    assert webhook.output == mock_output
    assert webhook.state == mock_state


def test_default_method_success(mock_webhook, mock_request):
    mock_request.json = {"test": "data"}
    mock_request.headers = {}

    mock_webhook.default()

    assert mock_webhook.output.save.call_count == 1
    assert mock_webhook.state.set_state.call_count == 1


def test_default_method_auth_success(mock_webhook, mock_request):
    valid_credentials = base64.b64encode(b"testuser:testpass").decode("utf-8")
    mock_request.headers = {"Authorization": f"Basic {valid_credentials}"}
    mock_request.json = {"test": "data"}

    mock_webhook.default(username="testuser", password="testpass")

    assert mock_webhook.output.save.call_count == 1


def test_default_method_auth_failure(mock_webhook, mock_request):
    invalid_credentials = base64.b64encode(b"wronguser:wrongpass").decode("utf-8")
    mock_request.headers = {"Authorization": f"Basic {invalid_credentials}"}
    mock_request.json = {"test": "data"}

    with pytest.raises(cherrypy.HTTPError):
        mock_webhook.default(username="testuser", password="testpass")


def test_default_method_error_handling(mock_webhook, mock_request):
    mock_request.json = {"test": "data"}
    mock_request.headers = {}
    mock_webhook.output.save.side_effect = Exception("Test Error")

    response = mock_webhook.default()

    assert "Error processing data" in response
    assert mock_webhook.state.set_state.call_count == 1


# Test for Webhook's listen method
def test_webhook_listen(mock_output, mock_state, mock_cherrypy_engine):
    webhook_instance = Webhook(mock_output, mock_state)
    port = 3000
    endpoint = "/"

    webhook_instance.listen(endpoint=endpoint, port=port)

    # Check if CherryPy config is updated correctly
    assert cherrypy.config["server.socket_host"] == "0.0.0.0"
    assert cherrypy.config["server.socket_port"] == port

    # Check if CherryPy engine methods are called
    mock_cherrypy_engine.start.assert_called_once()
    mock_cherrypy_engine.block.assert_called_once()


def test_webhook_listen_handles_exceptions(mock_output, mock_cherrypy_engine):
    ims = InMemoryState()
    webhook_instance = Webhook(mock_output, ims)

    # Simulate an exception when starting the CherryPy server
    mock_cherrypy_engine.start.side_effect = Exception("Server start failed")

    with pytest.raises(Exception) as exc_info:
        webhook_instance.listen(endpoint="/", port=3000)

    # Check that the exception message is as expected
    assert str(exc_info.value) == "Server start failed"
