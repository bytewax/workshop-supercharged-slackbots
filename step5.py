"""A Bytewax stream for processing Slack messages."""

from __future__ import annotations

import logging
import os
from typing import Callable
from typing import NewType
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import dotenv
import dataclasses

import bytewax.operators as op
from bytewax.connectors.stdio import StdOutSink
from bytewax.dataflow import Dataflow
from bytewax.operators.window import EventClockConfig
from bytewax.operators.window import TumblingWindow
from bytewax.operators.window import WindowMetadata

import openai

from utils.connectors.slack import SlackMessage
from utils.connectors.slack import SlackSource
from utils.qdrant import DocumentDatabase

log = logging.getLogger(__name__)

Summary = NewType("Summary", str)
Context = NewType("Context", list[str])


@dataclasses.dataclass
class AugmentedMessage:
    """Extension of the SlackMessage, with fields for summary and context."""

    message: SlackMessage
    related_summary: Summary
    related_context: Context

    def __str__(self) -> str:
        """String-representation of the message, used by StdOutSink."""
        context = "\n".join(f"    - {s}" for s in self.related_context)
        return f"""Question: {self.message.text}

  Related summary:
    {self.related_summary}

  Related context:
{context}
        """


def get_message_channel(msg: SlackMessage) -> str:
    """Extract the channel identifier from a message."""
    return msg.channel


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


def _create_llm_client() -> openai.AzureOpenAI:
    return openai.AzureOpenAI(
        api_version="2023-09-01-preview",
        azure_endpoint=os.environ["LLM_ENDPOINT"],
        api_key=os.environ["OPENAI_API_KEY"],
        azure_deployment=os.environ["LLM_DEPLOYMENT"],
        default_headers={"Ocp-Apim-Subscription-Key": os.environ["YOKOTAI_APIKEY"]},
    )


class Summarizer:
    """A callable type which can be used in Bytewax `stateful_map`."""

    def __init__(self):
        """Initialize a summarizer with an LLM client and a prompt template."""
        self._llm_client = _create_llm_client()
        self._prompt = """Your task is to maintain a summary of the current ongoing discussion. You are given the current summary (which can be empty, if the discussion is just starting), and a set of new messages, the content of which you will add to the summary. Try to keep the summary under 200 words long.

The messages will come in the format \"<username>: <Message>\". Respond with the new summary of the discussion.

Here is the current summary:

   {summary}
"""

    @classmethod
    def create_initial_state(cls) -> Summary:
        """Get initial state for the stateful stream step."""
        return Summary("No-one has said anything yet.")

    def __call__(
        self, previous_state: str, item: tuple[WindowMetadata, list[SlackMessage]]
    ) -> tuple[Summary, Summary]:
        """This is called whenewer a new window of messages arrive.

        It gets the previous state as the first argument, and returns the new
        state and an object to be passed downstream.
        """
        _, messages = item  # we don't need the window metadata here

        system_prompt = self._prompt.format(summary=previous_state)

        user_prompt = "\n".join(
            [f" - {message.user}: {message.text}" for message in messages]
        )
        completion = self._llm_client.chat.completions.create(
            model=os.environ["LLM_DEPLOYMENT"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1024,
        )

        summary = Summary(completion.choices[0].message.content)

        new_state = summary
        return new_state, summary


def context_retriever(
    document_storage: DocumentDatabase,
) -> Callable[[tuple[str, SlackMessage]], tuple[str, AugmentedMessage]]:
    """Get a function for retrieving context from the given document database."""

    def _func(
        item: tuple[str, SlackMessage],
    ) -> tuple[str, AugmentedMessage]:
        key, msg = item
        results = document_storage.search(msg.text, limit=10)
        return key, AugmentedMessage(
            message=msg, related_summary=Summary(""), related_context=Context(results)
        )

    return _func


def join_summary_to_question(
    previous_question_id: str | None, item: tuple[AugmentedMessage, Summary]
) -> tuple[str, tuple[AugmentedMessage, bool]]:
    """Join the summary data with the question message."""
    message, summary = item

    if message is None:
        return None, (None, False)

    if summary is None:
        summary = Summarizer.create_initial_state()

    message.related_summary = summary
    return message.message.id, (message, message.message.id != previous_question_id)


def has_unique_flag_set(
    item: tuple[str, tuple[AugmentedMessage, bool]],
) -> bool:
    _, (_, is_unique) = item
    return is_unique


def _build_dataflow() -> Dataflow:
    # Initialize a vector database in-memory
    document_storage = DocumentDatabase(model="BAAI/bge-small-en-v1.5")

    # Load the preloaded documents
    # This step will calculate the embeddings for all of the chapters in the
    # document.
    log.info("Loading documents to document database...")
    document_storage.upload_text_chapterwise("data/dataset.txt")
    log.info("Document loading finished")

    # Create a bytewax stream object.
    flow = Dataflow("supercharged-slackbot")

    # Data will be flowing in from the Slack stream.
    stream = op.input("input", flow, SlackSource(url=os.environ["SLACK_PROXY_URL"]))

    # Key the stream elements based on the channel id. In here we are not processing
    # any channels separately, but this approach very much allows it. The windowing
    # step requires a keyed stream, so that's why we are adding it here.
    keyed_stream = op.key_on("key_on_channel", stream, get_message_channel)

    # Filter the messages based on which Slack channel they were posted on.
    filtered_stream = op.filter(
        "filter_channel", keyed_stream, channel_is("C06JETUAX2S")
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
        length=timedelta(seconds=10), align_to=datetime(2024, 1, 1, tzinfo=timezone.utc)
    )
    windowed_messages = op.window.collect_window("window", messages, clock, windower)

    # Create a stateful step which keeps track of the current discussion summary
    summarizer = Summarizer()
    summary_stream = op.stateful_map(
        "summarize", windowed_messages, summarizer.create_initial_state, summarizer
    )

    # Augment the message with the context from document database
    mentions_with_context = op.map(
        "augment_with_context", mentions, context_retriever(document_storage)
    )

    # Join the two streams back together
    joined = op.join(
        "join_streams",
        mentions_with_context,
        summary_stream,
        running=True,
    )

    # Our running join will emit a new item each time either of the upstreams changes.
    # In our case we are only caring about the change in the mentions-stream.
    # Thus, we only let each mention/question go through this step once by first
    # flagging them with a `stateful_map` and filtering the flagged items with `filter`.
    flagged = op.stateful_map(
        "augment_with_summary", joined, lambda: None, join_summary_to_question
    )

    unique_questions = op.filter("filter_flagged", flagged, has_unique_flag_set)

    questions = op.map("remove_flag_and_key", unique_questions, lambda x: x[1][0])

    # Output the augmented messages into the console
    op.output("output", questions, StdOutSink())

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
