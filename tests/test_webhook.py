import pytest
import base64
import cherrypy
from unittest import mock
from geniusrise import State, StreamingOutput
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


def test_webhook_initialization(mock_output, mock_state):
    # Testing initialization
    webhook = Webhook(mock_output, mock_state)
    assert (
        webhook.output == mock_output
    )  # Assert that the attributes are correctly set during initialization
    assert webhook.state == mock_state
    assert isinstance(webhook.buffer, list)
    assert len(webhook.buffer) == 0


def test_check_auth_valid(mock_output, mock_state):
    # Test for checking valid authentication
    with mock.patch(
        "cherrypy.request.headers",
        {
            "Authorization": "Basic "
            + base64.b64encode(b"testuser:testpass").decode("utf-8")
        },
    ):
        webhook = Webhook(mock_output, mock_state)
        webhook._check_auth("testuser", "testpass")


def test_check_auth_invalid(mock_output, mock_state):
    # Test for checking invalid authentication
    with mock.patch(
        "cherrypy.request.headers",
        {"Authorization": "Basic " + base64.b64encode(b"user:pass").decode("utf-8")},
    ):
        webhook = Webhook(mock_output, mock_state)
        with pytest.raises(cherrypy.HTTPError) as error_info:  # http status error 401
            webhook._check_auth("testuser", "testpass")
            assert error_info.value.status == 401


def test_check_auth_missing_header(mock_output, mock_state):
    # Test for checking if missing header
    with mock.patch("cherrypy.request.headers", {}):
        webhook = Webhook(mock_output, mock_state)
        with pytest.raises(cherrypy.HTTPError) as error_info:  # http status error 401
            webhook._check_auth("testuser", "testpass")
            assert error_info.value.status == 401


def test_check_auth_wrong_header(mock_output, mock_state):
    # Test for checking if wrong header
    with mock.patch(
        "cherrypy.request.headers",
        {"Authorization": "Basic " + base64.b64encode(b"user").decode("utf-8")},
    ):
        webhook = Webhook(mock_output, mock_state)
        with pytest.raises(ValueError) as error_info:  # split not working so valueerror
            webhook._check_auth("user", "pass")


def test_default_without_auth(mock_output, mock_state):
    # Test for checking default without authorization
    webhook = Webhook(mock_output, mock_state)
    cherrypy.request.json = {"test": "data"}
    response = webhook.default()
    assert response == ""  # returns an empty string
    mock_output.save.assert_called_once()
    mock_state.get_state.assert_called_once_with(webhook.id)
    mock_state.set_state.assert_called_once()


def test_default_with_valid_auth(mock_output, mock_state):
    # Test for checking default with valid authorization
    webhook = Webhook(mock_output, mock_state)
    cherrypy.request.json = {"test": "data"}
    cherrypy.request.headers = {
        "Authorization": "Basic "
        + base64.b64encode(b"testuser:testpass").decode("utf-8")
    }
    response = webhook.default(username="testuser", password="testpass")
    assert response == ""  # successful
    mock_output.save.assert_called_once()
    mock_state.get_state.assert_called_once_with(webhook.id)
    mock_state.set_state.assert_called_once()


def test_default_with_invalid_auth(mock_output, mock_state):
    # Test for checking default with invalid authorization
    webhook = Webhook(mock_output, mock_state)
    cherrypy.request.json = {"test": "data"}
    cherrypy.request.headers = {
        "Authorization": "Basic " + base64.b64encode(b"user:pass").decode("utf-8")
    }
    with pytest.raises(cherrypy.HTTPError) as error_info:
        webhook.default(username="testuser", password="testpass")
    assert error_info.value.status == 401


def test_default_with_data_processing_exception(mock_output, mock_state):
    # Test for checking default when exception
    webhook = Webhook(mock_output, mock_state)
    cherrypy.request.json = {"test": "data"}
    mock_output.save.side_effect = Exception("Exception")
    mock_state.get_state.return_value = {"success_count": 0, "failure_count": 0}
    response = webhook.default()
    assert response == "Error processing data"
    assert cherrypy.response.status == 500
    mock_state.set_state.assert_called()
    updated_state = {
        "success_count": 0,  # This remains unchanged
        "failure_count": 1,  # This should increment by 1 due to the error
    }
    mock_state.set_state.assert_called_once_with(webhook.id, updated_state)


def test_default_success(mock_output, mock_state):
    # Test for checking default when successful
    webhook = Webhook(mock_output, mock_state)
    cherrypy.request.json = {"test": "data"}
    mock_state.get_state.return_value = {"success_count": 0, "failure_count": 0}
    response = webhook.default()
    assert response == ""
    mock_output.save.assert_called_once()
    mock_state.set_state.assert_called_once_with(
        webhook.id, {"success_count": 1, "failure_count": 0}
    )


def test_default_without_success(mock_output, mock_state):
    # Test for checking default when not successful
    webhook = Webhook(mock_output, mock_state)
    cherrypy.request.json = {"test": "data"}
    mock_state.get_state.return_value = {"failure_count": 0}
    response = webhook.default()
    assert response == ""
    mock_output.save.assert_called_once()
    mock_state.set_state.assert_called_once_with(
        webhook.id, {"success_count": 1, "failure_count": 0}
    )


def test_default_without_failure(mock_output, mock_state):
    webhook = Webhook(mock_output, mock_state)
    cherrypy.request.json = {"test": "data"}
    mock_state.get_state.return_value = {"success_count": 1}
    response = webhook.default()
    assert response == ""
    mock_output.save.assert_called_once()
    mock_state.set_state.assert_called_once_with(webhook.id, {"success_count": 2})


def test_default_state_when_none(mock_output, mock_state):
    # test when default state is none
    webhook = Webhook(mock_output, mock_state)
    cherrypy.request.json = {"test": "data"}
    mock_state.get_state.return_value = None
    response = webhook.default()
    assert response == ""
    mock_output.save.assert_called_once()
    mock_state.set_state.assert_called_once_with(
        webhook.id, {"success_count": 1, "failure_count": 0}
    )


def test_default_enriched_data(mock_output, mock_state):
    # tests the enriched data of deafult
    webhook = Webhook(mock_output, mock_state)
    cherrypy.request.json = {"test": "data"}
    mock_url = "http://localhost:3000"
    mock_headers = {"header_key": "header_value"}
    cherrypy.url = mock.Mock(return_value=mock_url)
    cherrypy.request.headers = mock_headers
    webhook.default()
    expected_enriched_data = {
        "data": {"test": "data"},
        "endpoint": mock_url,
        "headers": mock_headers,
    }
    mock_output.save.assert_called_once_with(expected_enriched_data)


def test_default_with_empty_json(mock_output, mock_state):
    # test default with empty json data
    webhook = Webhook(mock_output, mock_state)
    cherrypy.request.json = None
    response = webhook.default()
    assert response == ""


def test_listen_starts_server_with_default_config(mock_webhook):
    # test for listen checking default config
    mock_engine_start = mock.MagicMock()
    mock_engine_block = mock.MagicMock()
    cherrypy.engine.start = mock_engine_start
    cherrypy.engine.block = mock_engine_block

    mock_webhook.listen()

    assert cherrypy.config["server.socket_host"] == "0.0.0.0"
    assert cherrypy.config["server.socket_port"] == 3000

    mock_engine_start.assert_called_once()
    mock_engine_block.assert_called_once()


def test_listen_starts_server_with_custom_port(mock_webhook):
    # test for listen checking with custom port
    mock_engine_start = mock.MagicMock()
    mock_engine_block = mock.MagicMock()
    cherrypy.engine.start = mock_engine_start
    cherrypy.engine.block = mock_engine_block

    mock_webhook.listen(port=4000)

    assert cherrypy.config["server.socket_port"] == 4000

    mock_engine_start.assert_called_once()
    mock_engine_block.assert_called_once()


def test_listen_starts_server_with_default_host(mock_webhook):
    # test for listen checking with default host
    mock_engine_start = mock.MagicMock()
    mock_engine_block = mock.MagicMock()
    cherrypy.engine.start = mock_engine_start
    cherrypy.engine.block = mock_engine_block

    mock_webhook.listen()

    assert cherrypy.config["server.socket_host"] == "0.0.0.0"

    mock_engine_start.assert_called_once()
    mock_engine_block.assert_called_once()


def test_listen_uses_webhook_logger(mock_webhook):
    # test for checking if listen uses webhook loggers
    mock_engine_start = mock.MagicMock()
    mock_engine_block = mock.MagicMock()
    cherrypy.engine.start = mock_engine_start
    cherrypy.engine.block = mock_engine_block
    mock_webhook.listen()
    assert mock_webhook.log in cherrypy.log.error_log.handlers
    assert mock_webhook.log in cherrypy.log.access_log.handlers

    mock_engine_start.assert_called_once()
    mock_engine_block.assert_called_once()
