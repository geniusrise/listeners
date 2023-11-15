import pytest
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch
from geniusrise import State, StreamingOutput, InMemoryState
from geniusrise_listeners.sqs import SQS


# Fixture to mock StreamingOutput
@pytest.fixture
def mock_output():
    mock_output = mock.MagicMock(spec=StreamingOutput)
    mock_output.log = mock.MagicMock()
    return mock_output


# Fixture to create an instance of InMemoryState
@pytest.fixture
def ims_state():
    return InMemoryState()


# Fixture to mock State
@pytest.fixture
def mock_state():
    return mock.MagicMock(spec=State)


# Fixture to create an SQS object with mocked dependencies
@pytest.fixture
def mock_sqs(mock_output, mock_state):
    return SQS(mock_output, mock_state)


# Test the initialization of SQS class
@patch('boto3.client')
def test_sqs_init(mock_boto_client, mock_output, mock_state):
    sqs = SQS(mock_output, mock_state)
    assert sqs.output == mock_output
    assert sqs.state == mock_state
    assert sqs.top_level_arguments == {}


# Test the initialization of SQS class with additional arguments
@patch('boto3.client')
def test_sqs_init_with_args(mock_boto_client, mock_output, mock_state):
    custom_kwargs = {
        "arg1": "value1",
        "arg2": "value2",
    }
    sqs = SQS(mock_output, mock_state, **custom_kwargs)
    assert sqs.output == mock_output
    assert sqs.state == mock_state
    assert sqs.top_level_arguments == custom_kwargs


# Test the listen method when a message is successfully received
@patch('boto3.client')
def test_listen_successful(mock_sqs_client, mock_output, ims_state):
    # Mocking the AWS SQS client
    mock_sqs = MagicMock()
    mock_sqs.receive_message.side_effect = [
        {"Messages": [{"ReceiptHandle": "handle1", "MessageId": "id1"}]},
        KeyboardInterrupt
    ]
    mock_sqs_client.return_value = mock_sqs

    # Testing the listen method
    sqs_spout = SQS(mock_output, ims_state)
    with unittest.TestCase().assertRaises(KeyboardInterrupt):  # Simulating a keyboard interrupt
        sqs_spout.listen("dummy_queue_url")
    mock_sqs.receive_message.assert_called()
    mock_output.save.assert_called_once()
    mock_sqs.delete_message.assert_called_once_with(
        QueueUrl="dummy_queue_url",
        ReceiptHandle="handle1"
    )


# Test the listen method when multiple messages are successfully received
@patch('boto3.client')
def test_listen_multiple_messages_successfully(mock_sqs_client, mock_output, ims_state):
    # Mocking the AWS SQS client
    mock_sqs = MagicMock()
    mock_sqs.receive_message.side_effect = [
        {
            "Messages": [
                {"ReceiptHandle": "handle1", "MessageId": "id1"},
                {"ReceiptHandle": "handle2", "MessageId": "id2"}
            ]
        },
        {},  # Simulate empty response on second call
        KeyboardInterrupt  # Raise interrupt on third call
    ]
    mock_sqs_client.return_value = mock_sqs

    # Testing the listen method
    sqs_spout = SQS(mock_output, ims_state)
    with unittest.TestCase().assertRaises(KeyboardInterrupt):
        sqs_spout.listen("dummy_queue_url")
    assert mock_sqs.receive_message.call_count == 3
    assert mock_output.save.call_count == 2
    assert mock_sqs.delete_message.call_count == 2


# Test the listen method when no messages are received
@patch('boto3.client')
def test_listen_no_messages_received(mock_sqs_client, mock_output, ims_state):
    # Mocking the AWS SQS client
    mock_sqs = MagicMock()
    mock_sqs.receive_message.side_effect = [
        {},  # No messages received
        KeyboardInterrupt
    ]
    mock_sqs_client.return_value = mock_sqs

    # Testing the listen method
    sqs_spout = SQS(mock_output, ims_state)
    with unittest.TestCase().assertRaises(KeyboardInterrupt):
        sqs_spout.listen("dummy_queue_url")
    mock_sqs.receive_message.assert_called()
    mock_output.save.assert_not_called()  # Save should not be called
    mock_sqs.delete_message.assert_not_called()  # Delete should not be called


# Test the listen method when an exception occurs
@patch('boto3.client')
def test_listen_exception_occurred(mock_sqs_client, mock_output, ims_state):
    # Mocking the AWS SQS client
    mock_sqs = MagicMock()
    mock_sqs.receive_message.side_effect = [
        Exception("AWS SQS Error"),  # Exception on first call
        KeyboardInterrupt
    ]
    mock_sqs_client.return_value = mock_sqs

    # Testing the listen method
    sqs_spout = SQS(mock_output, ims_state)
    with unittest.TestCase().assertRaises(KeyboardInterrupt):
        sqs_spout.listen("dummy_queue_url")
    mock_sqs.receive_message.assert_called()
    mock_output.save.assert_not_called()  # Save should not be called
    mock_sqs.delete_message.assert_not_called()  # Delete should not be called
