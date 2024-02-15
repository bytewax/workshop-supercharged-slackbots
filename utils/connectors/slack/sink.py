from __future__ import annotations

import json
import logging
import queue
import threading
import time

import websockets
from bytewax.outputs import DynamicSink
from bytewax.outputs import StatelessSinkPartition

from . import SlackMessage

log = logging.getLogger(__name__)


class _SlackSinkPartition(StatelessSinkPartition[SlackMessage]):
    def __init__(self, queue: queue.Queue[SlackMessage], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._queue = queue

    def write_batch(self, items: list[SlackMessage]) -> None:
        for item in items:
            self._queue.put(item)


# TODO: Move thread to partition


class SlackSink(DynamicSink[SlackMessage]):
    """Bytewax -compatible Slack-sink."""

    def __init__(self, url: str):
        self._url = f"{url}/sink"

        self._thread = threading.Thread(target=self._send_messages, daemon=True)
        self._lock = threading.Lock()
        self._thread.start()
        self._queue: queue.Queue[SlackMessage] = queue.Queue()

    def _send_messages(self):
        while True:
            try:
                socket = websockets.sync.client.connect(self._url)
            except Exception as e:
                log.exception(e)
                log.error("Connection failed, reconnecting in 1 seconds...")
                time.sleep(1)

            while True:
                try:
                    msg = self._queue.get_nowait()
                except queue.Empty:
                    time.sleep(1)
                    continue

                msg_str = json.dumps(
                    {"ts": msg.id, "text": msg.text, "channel": msg.channel}
                )

                try:
                    socket.send(msg_str)
                except Exception as e:
                    log.exception(e)
                    log.error("Send failed, reconnecting...")
                    break

    def build(self, worker_index: int, worker_count: int) -> _SlackSinkPartition:
        return _SlackSinkPartition(queue=self._queue)
