# Necessary imports for the test suite
import pytest
from unittest import mock
from requests.exceptions import RequestException
from geniusrise import State, StreamingOutput
from geniusrise_listeners.http_polling import RESTAPIPoll


# Fixture to mock the StreamingOutput
@pytest.fixture
def mock_output():
    return mock.MagicMock(spec=StreamingOutput)


# Fixture to mock the State
@pytest.fixture
def mock_state():
    return mock.MagicMock(spec=State)


# Fixture to mock the requests.get method
@pytest.fixture
def mock_requests_get():
    with mock.patch("requests.get") as mock_get:
        yield mock_get


# Test initialization of the RESTAPIPoll class
def test_init_method(mock_output, mock_state):
    """Test the __init__ method of RESTAPIPoll class."""
    kwargs = {"key1": "value1", "key2": "value2"}
    spout = RESTAPIPoll(mock_output, mock_state, **kwargs)
    # Assert that the arguments passed during initialization are stored correctly
    assert spout.top_level_arguments == kwargs


# Test the listen method of the RESTAPIPoll class with a successful response
def test_listen_method(mock_output, mock_state, mock_requests_get):
    """Test the listen method with a successful mock response."""
    mock_response = mock.MagicMock()
    mock_response.json.return_value = {"key": "value"}
    mock_response.status_code = 200
    mock_requests_get.return_value = mock_response

    spout = RESTAPIPoll(mock_output, mock_state)

    # Mock the poll_api and time.sleep methods and test the listen method
    with mock.patch.object(spout, "poll_api") as mock_poll, mock.patch(
        "time.sleep", side_effect=[None, SystemExit]
    ):
        try:
            spout.listen(url="http://test-url.com", method="GET", interval=1)
        except SystemExit:
            pass

    # Assert the poll_api method was called twice
    assert mock_poll.call_count == 2


def test_listen_method_different_response(mock_output, mock_state, mock_requests_get):
    """Test the listen method with a different mock response."""
    mock_response = mock.MagicMock()
    mock_response.json.return_value = {"another_key": "another_value"}
    mock_response.status_code = 200
    mock_requests_get.return_value = mock_response

    spout = RESTAPIPoll(mock_output, mock_state)

    with mock.patch.object(spout, "poll_api") as mock_poll, mock.patch(
        "time.sleep", side_effect=[None, SystemExit]
    ):
        try:
            spout.listen(url="http://test-url-different.com", method="GET", interval=1)
        except SystemExit:
            pass

    assert mock_poll.call_count == 2


def test_listen_method_server_error(mock_output, mock_state, mock_requests_get):
    """Test the listen method in case of server error in the mock response."""
    mock_response = mock.MagicMock()
    mock_response.json.return_value = {"error": "Internal Server Error"}
    mock_response.status_code = 500
    mock_requests_get.return_value = mock_response

    spout = RESTAPIPoll(mock_output, mock_state)

    with mock.patch.object(spout, "poll_api") as mock_poll, mock.patch(
        "time.sleep", side_effect=[None, SystemExit]
    ):
        try:
            spout.listen(url="http://test-url-error.com", method="GET", interval=1)
        except SystemExit:
            pass

    assert mock_poll.call_count == 2


def test_listen_method_request_exception(mock_output, mock_state, mock_requests_get):
    """Test the listen method when facing a request exception (e.g., network error)."""
    mock_requests_get.side_effect = RequestException("Network Error")

    spout = RESTAPIPoll(mock_output, mock_state)

    with mock.patch.object(spout, "poll_api") as mock_poll, mock.patch(
        "time.sleep", side_effect=[None, SystemExit]
    ):
        try:
            spout.listen(
                url="http://test-url-network-error.com", method="GET", interval=1
            )
        except SystemExit:
            pass

    assert mock_poll.call_count == 2


def test_poll_api_success(mock_output, mock_state, mock_requests_get):
    """Test the poll_api method with a successful mock response."""
    mock_response = mock.MagicMock()
    mock_response.json.return_value = {"key": "value"}
    mock_response.status_code = 200
    mock_requests_get.return_value = mock_response

    spout = RESTAPIPoll(mock_output, mock_state)
    spout.state.get_state.return_value = {"success_count": 0, "failure_count": 0}

    spout.poll_api(url="http://test-url.com", method="GET")

    # Asserting the save method was called once with the expected data
    mock_output.save.assert_called_once_with(
        {
            "data": {"key": "value"},
            "url": "http://test-url.com",
            "method": "GET",
            "headers": None,
            "params": None,
        }
    )

    # Assert that the state was updated correctly
    state_data = spout.state.get_state(spout.id)
    assert state_data["success_count"] == 1
    assert state_data["failure_count"] == 0
