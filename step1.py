"""A Bytewax stream for processing Slack messages."""

from __future__ import annotations

from typing import Callable

import logging
import os

import dotenv

import bytewax.operators as op
from bytewax.dataflow import Dataflow
from bytewax.connectors.stdio import StdOutSink

from utils.connectors.slack import SlackSource
from utils.connectors.slack import SlackMessage

log = logging.getLogger(__name__)


def channel_is(channel: str) -> Callable[[SlackMessage], bool]:
    """Predicate function to check if the message was posted on the given channel."""

    def _func(msg: SlackMessage) -> bool:
        return msg.channel == channel

    return _func


def _build_dataflow():
    # Create a bytewax stream object.
    flow = Dataflow("supercharged-slackbot")

    # Data will be flowing in from the Slack stream.
    stream = op.input("input", flow, SlackSource(url=os.environ["SLACK_PROXY_URL"]))

    # Inspect will show what entries are in the stream.
    op.inspect_debug("debug", stream)

    # Filter the messages based on which Slack channel they were posted on.
    stream = op.filter("filter_channel", stream, channel_is("C06JETUAX2S"))

    # Output the messages into the console
    op.output("output", stream, StdOutSink())

    return flow


# Load environment variables from .env
dotenv.load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-7s %(message)s",
    handlers=[logging.StreamHandler()],
)

# Dataflow needs to be assigned to a global variable called "flow"
flow = _build_dataflow()
