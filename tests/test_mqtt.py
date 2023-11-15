import pytest
import json
from unittest import mock
from paho.mqtt.client import MQTTMessage
from geniusrise import State, StreamingOutput
from geniusrise_listeners.mqtt import MQTT

# Fixtures


@pytest.fixture
def mock_output():
    """Fixture to mock StreamingOutput."""
    return mock.MagicMock(spec=StreamingOutput)


@pytest.fixture
def mock_state():
    """Fixture to mock State."""
    return mock.MagicMock(spec=State)


@pytest.fixture
def mock_mqtt_client():
    """Fixture to mock paho.mqtt.client.Client."""
    with mock.patch("paho.mqtt.client.Client") as mock_client:
        yield mock_client


def test_mqtt_initialization(mock_output, mock_state):
    """Test to ensure MQTT object is initialized with correct top level arguments."""
    mqtt_spout = MQTT(mock_output, mock_state, arg1="value1", arg2="value2")
    
    assert mqtt_spout.top_level_arguments == {"arg1": "value1", "arg2": "value2"}


def test_on_connect():
    """Test to ensure correct topic is subscribed upon connection."""
    mqtt_spout = MQTT(mock.MagicMock(), mock.MagicMock())
    mqtt_spout.topic = "test_topic"
    mock_client = mock.Mock()

    mqtt_spout._on_connect(mock_client, None, None, 0)
    mock_client.subscribe.assert_called_with("test_topic")


def test_on_message_successful_processing(mock_state):
    """Test to ensure successful message processing is tracked in state."""
    mqtt_spout = MQTT(mock.MagicMock(), mock_state)
    mock_msg = mock.Mock()
    mock_msg.payload = json.dumps({"key": "value"})
    mock_msg.topic = "test_topic"

    # Mocking return value for get_state method
    mock_state.get_state.return_value = {"success_count": 0, "failure_count": 0}

    mqtt_spout._on_message(None, None, mock_msg)
    
    state = mqtt_spout.state.get_state(mqtt_spout.id)
    assert state["success_count"] == 1
    assert state["failure_count"] == 0


def test_on_message_error_processing(mock_state):
    """Test to ensure message processing errors are tracked in state."""
    mqtt_spout = MQTT(mock.MagicMock(), mock_state)
    mock_msg = mock.Mock()
    mock_msg.payload = "invalid_json"
    mock_msg.topic = "test_topic"

    # Mocking return value for get_state method
    mock_state.get_state.return_value = {"success_count": 0, "failure_count": 0}

    mqtt_spout._on_message(None, None, mock_msg)
    
    state = mqtt_spout.state.get_state(mqtt_spout.id)
    assert state["success_count"] == 0
    assert state["failure_count"] == 1


def test_on_message_with_empty_payload(mock_state):
    """Test to ensure empty payload is treated as a failed message."""
    mqtt_spout = MQTT(mock.MagicMock(), mock_state)
    mock_msg = mock.Mock()
    mock_msg.payload = ""
    mock_msg.topic = "test_topic"

    mock_state.get_state.return_value = {"success_count": 0, "failure_count": 0}

    mqtt_spout._on_message(None, None, mock_msg)
    
    state = mqtt_spout.state.get_state(mqtt_spout.id)
    assert state["success_count"] == 0
    assert state["failure_count"] == 1


def test_listen_failure(mock_output, mock_state, mock_mqtt_client):
    """Test to ensure that listen method handles connection failures."""
    mqtt_spout = MQTT(mock_output, mock_state)
    mqtt_spout._on_connect = mock.MagicMock()
    mqtt_spout._on_message = mock.MagicMock()

    # Simulate an exception raised during listen
    mock_mqtt_client().connect.side_effect = Exception("Connection failed")

    with pytest.raises(Exception) as excinfo:
        mqtt_spout.listen(host="localhost", port=1883, topic="test_topic")
    
    assert "Connection failed" in str(excinfo.value)

    # Assert that loop_forever was not called due to the exception
    assert not mock_mqtt_client().loop_forever.called


def test_listen_success(mock_output, mock_state, mock_mqtt_client):
    """Test to ensure that the listen method correctly sets up the client and starts it."""
    mqtt_spout = MQTT(mock_output, mock_state)
    host = "localhost"
    port = 1883
    topic = "test_topic"
    
    # Simulate calling the listen method, which should configure the client
    mqtt_spout.listen(host=host, port=port, topic=topic)

    # Assert that connect was called with the right arguments
    mock_mqtt_client().connect.assert_called_with(host, port, 60)

    # Manually invoke the _on_connect callback
    mqtt_spout._on_connect(mock_mqtt_client(), None, None, 0)

    # Assert that subscribe was called with the right topic
    mock_mqtt_client().subscribe.assert_called_with(topic)

    # Create a mock MQTTMessage
    message = mock.MagicMock(spec=MQTTMessage)
    message.payload = json.dumps({"test": "data"}).encode()
    message.topic = topic

    # Manually invoke the _on_message callback
    mqtt_spout._on_message(mock_mqtt_client(), None, message)

    # Assert that loop_forever was called
    mock_mqtt_client().loop_forever.assert_called_once()
