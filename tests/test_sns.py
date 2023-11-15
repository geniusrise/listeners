import pytest
from unittest import mock
from unittest.mock import MagicMock, patch
from geniusrise import State, StreamingOutput, InMemoryState
from geniusrise_listeners.sns import SNS


@pytest.fixture
def mock_output():
    # Create a MagicMock object for StreamingOutput
    mock_output = mock.MagicMock(spec=StreamingOutput)
    # Mock the 'log' method of the StreamingOutput
    mock_output.log = mock.MagicMock()
    return mock_output


@pytest.fixture
def ims_state():
    # Create an instance of InMemoryState
    return InMemoryState()


@pytest.fixture
def mock_state():
    # Create a MagicMock object for State
    return mock.MagicMock(spec=State)


@pytest.fixture
def mock_sns(mock_output, mock_state):
    # Create an instance of SNS using mocked output and state
    return SNS(mock_output, mock_state)


@patch('boto3.resource')
def test_sns_init(mock_boto_resource, mock_output, mock_state):
    # Mock the boto3 resource creation
    mock_boto_resource.return_value = mock.MagicMock()

    # Initialize SNS with mocked output and state
    sns = SNS(mock_output, mock_state)
    # Assertions to ensure proper initialization
    assert sns.output == mock_output
    assert sns.state == mock_state
    assert sns.top_level_arguments == {}


@patch('boto3.resource')
def test_sns_init_with_args(mock_boto_resource, mock_output, mock_state):
    # Mock the boto3 resource creation
    mock_boto_resource.return_value = mock.MagicMock()

    # Custom arguments for SNS initialization
    custom_kwargs = {
        "arg1": "value1",
        "arg2": "value2",
    }
    # Initialize SNS with mocked output, state, and custom arguments
    sns = SNS(mock_output, mock_state, **custom_kwargs)
    # Assertions to ensure proper initialization with custom arguments
    assert sns.output == mock_output
    assert sns.state == mock_state
    assert sns.top_level_arguments == custom_kwargs


@patch('boto3.resource')
def test_listen_successful(mock_sns_resource, ims_state, mock_output):
    # Mocking the AWS SNS resource
    mock_sns = MagicMock()
    mock_subscription = MagicMock()
    # Mocking the 'get_messages' method to simulate message receiving and KeyboardInterrupt
    mock_subscription.get_messages.side_effect = [
        [{"Body": "Message 1"}],
        KeyboardInterrupt
    ]
    # Mocking SNS topic subscriptions
    mock_sns.topics.all.return_value = [MagicMock(subscriptions=MagicMock(all=MagicMock(return_value=[mock_subscription])))]
    mock_sns_resource.return_value = mock_sns

    # Testing the _listen method
    sns_spout = SNS(mock_output, ims_state)
    with pytest.raises(KeyboardInterrupt):  # Simulating a keyboard interrupt
        sns_spout.listen()
    # Ensure that 'get_messages' was called and messages were processed
    mock_subscription.get_messages.assert_called()
    mock_output.save.assert_called_once()


@patch('boto3.resource')
def test_listen_no_messages_received(mock_sns_resource, ims_state, mock_output):
    # Mocking the AWS SNS resource
    mock_sns = MagicMock()
    mock_subscription = MagicMock()
    # Simulating no messages received
    mock_subscription.get_messages.side_effect = [
        [],  # No messages received
        KeyboardInterrupt
    ]
    # Mocking SNS topic subscriptions
    mock_sns.topics.all.return_value = [MagicMock(subscriptions=MagicMock(all=MagicMock(return_value=[mock_subscription])))]
    mock_sns_resource.return_value = mock_sns

    # Testing the _listen method
    sns_spout = SNS(mock_output, ims_state)
    with pytest.raises(KeyboardInterrupt):
        sns_spout.listen()
    # Ensure 'get_messages' was called but no messages were processed
    mock_subscription.get_messages.assert_called()
    mock_output.save.assert_not_called()  # Save should not be called


@patch('boto3.resource')
def test_listen_exception_occurred(mock_sns_resource, ims_state, mock_output):
    # Mocking the AWS SNS resource
    mock_sns = MagicMock()
    mock_subscription = MagicMock()
    # Simulating an exception on message retrieval
    mock_subscription.get_messages.side_effect = [
        Exception("AWS SNS Error"),  # Exception on first call
        KeyboardInterrupt
    ]
    # Mocking SNS topic subscriptions
    mock_sns.topics.all.return_value = [MagicMock(subscriptions=MagicMock(all=MagicMock(return_value=[mock_subscription])))]
    mock_sns_resource.return_value = mock_sns

    # Testing the _listen method
    sns_spout = SNS(mock_output, ims_state)
    with pytest.raises(KeyboardInterrupt):
        sns_spout.listen()
    # Ensure 'get_messages' was called but no messages were processed due to exception
    mock_subscription.get_messages.assert_called()
    mock_output.save.assert_not_called()  # Save should not be called
