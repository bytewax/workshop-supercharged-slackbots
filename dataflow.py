"""A Bytewax stream for processing Slack messages."""

import logging

from bytewax.dataflow import Dataflow

import dotenv


def _build_dataflow() -> Dataflow:
    flow = Dataflow("supercharged-slackbot")

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
