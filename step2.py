"""A Bytewax stream for processing Slack messages."""

from __future__ import annotations

import logging
import os
from typing import Callable
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import bytewax.operators as op
import dotenv
from bytewax.connectors.stdio import StdOutSink
from bytewax.dataflow import Dataflow
from bytewax.operators.window import EventClockConfig
from bytewax.operators.window import TumblingWindow

from utils.connectors.slack import SlackMessage
from utils.connectors.slack import SlackSource

log = logging.getLogger(__name__)


def channel_is(channel: str) -> Callable[[tuple[str, SlackMessage]], bool]:
    """Predicate function to check if the message was posted on the given channel."""

    def _func(item: tuple[str, SlackMessage]) -> bool:
        _, msg = item
        return msg.channel == channel

    return _func


def is_mention(item: tuple[str, SlackMessage]) -> bool:
    """Predicate function to check if the message contains a mention of the bot.

    Note, this could be done directly via the Slack SDK API, but then we would
    not be able to easily branch on it.
    """
    _, msg = item
    return "<@U06JJAU0M9B>" in msg.text  # check for @mention


def get_message_channel(msg: SlackMessage) -> str:
    """Extract the channel identifier from a message."""
    return msg.channel


def _build_dataflow() -> Dataflow:
    # Create a bytewax stream object.
    flow = Dataflow("supercharged-slackbot")

    # Data will be flowing in from the Slack stream.
    stream = op.input("input", flow, SlackSource(url=os.environ["SLACK_PROXY_URL"]))

    keyed_stream = op.key_on("key_on_channel", stream, get_message_channel)

    # Filter the messages based on which Slack channel they were posted on.
    filtered_stream = op.filter(
        "filter_channel", keyed_stream, channel_is(os.environ["SLACK_CHANNEL_ID"])
    )

    # Branch the stream into two: one for bot mentions, one for the rest
    b_out = op.branch("is_mention", filtered_stream, is_mention)

    messages = b_out.falses
    mentions = b_out.trues

    # Inspect what messages got to which stream
    op.inspect_debug("message", messages)
    op.inspect_debug("mention", mentions)

    # We use windowing to throttle the amount of requests we are making to the
    # LLM API.
    clock = EventClockConfig(
        lambda msg: msg.timestamp, wait_for_system_duration=timedelta(seconds=0)
    )
    windower = TumblingWindow(
        length=timedelta(seconds=10), align_to=datetime(2024, 2, 1, tzinfo=timezone.utc)
    )
    windowed_messages = op.window.collect_window("window", messages, clock, windower)

    # Output the message windows into the console
    op.output("output", windowed_messages, StdOutSink())

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
