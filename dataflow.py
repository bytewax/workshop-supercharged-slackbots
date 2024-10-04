"""A Bytewax stream for processing Slack messages."""

import logging

from bytewax.dataflow import Dataflow

import dotenv

flow = Dataflow("supercharged-slackbot")

# Load environment variables from .env
dotenv.load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-7s %(message)s",
    handlers=[logging.StreamHandler()],
)
