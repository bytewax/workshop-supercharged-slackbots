"""A data structure representing a slack message."""
import dataclasses
from datetime import datetime


@dataclasses.dataclass
class SlackMessage:
    """A datastructure representing a Slack message.

    id: The identifier of the message. Is just a string-representation of the
        message timestamp. Slack uses this to refer to messages to for example
        handle replies
    user: The identifier of the user who submitted this message. Not the human-readable
          version of the name, but instead a "Uxxxxxxxxxx"-style string.
    channel: The identifier of the slack channel. "Cxxxxxxxxxx"-style string.
    text: The textual contents of the message.
    timestamp: A UTC timestamp of the message.
    """

    id: str
    user: str
    channel: str
    text: str
    timestamp: datetime

    def __str__(self) -> str:
        """String-representation of the message, used by StdOutSink."""
        return f"Channel {self.channel}: User {self.user} says \"{self.text}\""
