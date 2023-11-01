import pytest
import json
from unittest import mock
from geniusrise import State, StreamingOutput
from geniusrise_listeners.kinesis import Kinesis


@pytest.fixture
def mock_output():
    return mock.MagicMock(spec=StreamingOutput)


@pytest.fixture
def mock_state():
    return mock.MagicMock(spec=State)


@pytest.fixture
def mock_kinesis_client():
    """Create a mock boto3 Kinesis client."""
    return mock.MagicMock()


@mock.patch("boto3.client")
def test_kinesis_init_default(mock_boto_client, mock_output, mock_state, mock_kinesis_client):
    """Test the default initialization of Kinesis class without additional keyword arguments."""
    mock_boto_client.return_value = mock_kinesis_client
    
    kinesis_spout = Kinesis(mock_output, mock_state)

    assert isinstance(kinesis_spout, Kinesis)
    assert kinesis_spout.output == mock_output
    assert kinesis_spout.state == mock_state
    mock_boto_client.assert_called_once_with("kinesis")
    assert kinesis_spout.top_level_arguments == {}


@mock.patch("boto3.client")
def test_kinesis_init_with_kwargs(mock_boto_client, mock_output, mock_state, mock_kinesis_client):
    """Test the initialization of Kinesis class with additional keyword arguments."""
    mock_boto_client.return_value = mock_kinesis_client
    
    kwargs = {"example_arg": "value"}
    kinesis_spout = Kinesis(mock_output, mock_state, **kwargs)

    assert isinstance(kinesis_spout, Kinesis)
    assert kinesis_spout.output == mock_output
    assert kinesis_spout.state == mock_state
    mock_boto_client.assert_called_once_with("kinesis")
    assert kinesis_spout.top_level_arguments == kwargs


@mock.patch("boto3.client")
def test_kinesis_listen_default(mock_boto_client, mock_output, mock_state, mock_kinesis_client):
    """Test the listen method with default arguments."""
    # Mock responses from the Kinesis client methods
    mock_kinesis_client.get_shard_iterator.return_value = {"ShardIterator": "some_iterator"}
    mock_kinesis_client.get_records.return_value = {
        "Records": [{"Data": json.dumps({"test": "data"}), "SequenceNumber": "12345"}],
        "NextShardIterator": "next_iterator"
    }
    mock_boto_client.return_value = mock_kinesis_client
    
    kinesis_spout = Kinesis(mock_output, mock_state)
    
    with mock.patch.object(kinesis_spout, "output") as mock_output_save:
        mock_output_save.save.side_effect = SystemExit  # Raise SystemExit to exit loop
        with pytest.raises(SystemExit):
            kinesis_spout.listen("test_stream")
    
    assert mock_output_save.save.call_count == 1


@mock.patch("boto3.client")
def test_kinesis_listen_loop_with_valid_data(mock_boto_client, mock_output, mock_state, mock_kinesis_client):
    """Test the listen loop with valid data for a few iterations."""
    
    # Mock get_shard_iterator to return a mock iterator
    mock_kinesis_client.get_shard_iterator.return_value = {"ShardIterator": "some_iterator"}

    # Counter to keep track of iterations
    counter = {'value': 0}
    
    def mock_get_records(*args, **kwargs):
        # After 2 iterations, raise SystemExit to exit the loop
        if counter['value'] >= 2:
            raise SystemExit()
        counter['value'] += 1
        return {
            "Records": [{"Data": json.dumps({"test": "data"}), "SequenceNumber": "12345"}],
            "NextShardIterator": "next_iterator"
        }

    mock_kinesis_client.get_records = mock_get_records
    mock_boto_client.return_value = mock_kinesis_client

    kinesis_spout = Kinesis(mock_output, mock_state)
    
    with pytest.raises(SystemExit):
        kinesis_spout.listen("test_stream")
    
    assert counter['value'] == 2
    assert mock_output.save.call_count == 2


@mock.patch("boto3.client")
def test_kinesis_listen_exception_handling(mock_boto_client, mock_output, mock_state, mock_kinesis_client):
    """Test the exception handling in the listen method."""
    # Mock responses from the Kinesis client methods
    mock_kinesis_client.get_shard_iterator.return_value = {"ShardIterator": "some_iterator"}
    mock_kinesis_client.get_records.side_effect = Exception("Kinesis error")  # Simulate an error
    mock_boto_client.return_value = mock_kinesis_client

    kinesis_spout = Kinesis(mock_output, mock_state)

    with mock.patch.object(kinesis_spout, "log") as mock_log:
        mock_log.error.side_effect = SystemExit  # Raise SystemExit to exit loop
        with pytest.raises(SystemExit):
            kinesis_spout.listen("test_stream")

    assert mock_log.error.call_count == 1