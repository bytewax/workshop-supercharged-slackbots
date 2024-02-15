from __future__ import annotations

import json
import logging
import queue
import random
import threading
import time
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Iterable
from typing import Optional

import websockets.sync.client
from bytewax.inputs import DynamicSource
from bytewax.inputs import StatelessSourcePartition

from . import SlackMessage

log = logging.getLogger(__name__)


class _SlackSourcePartition(StatelessSourcePartition[SlackMessage]):
    def __init__(self, queue: queue.Queue, *args, max_batch_size: int = 10, **kwargs):
        super().__init__(*args, **kwargs)
        self._queue = queue
        self._max_batch_size = max_batch_size

    def next_batch(self, sched: datetime) -> Iterable[SlackMessage]:
        batch = []
        for _ in range(self._max_batch_size):
            try:
                batch.append(self._build_message(self._queue.get_nowait()))
            except queue.Empty:
                break
        return batch

    def _build_message(self, data: bytes) -> SlackMessage:
        msg = json.loads(data)
        return SlackMessage(
            channel=msg["channel"],
            id=msg["ts"],
            user=msg["user"],
            text=msg["text"],
            timestamp=datetime.fromtimestamp(float(msg["ts"])).astimezone(timezone.utc),
        )

    def next_awake(self) -> Optional[datetime]:
        # Reduce polling rate
        return datetime.now(timezone.utc) + timedelta(milliseconds=100)


class SlackSource(DynamicSource[SlackMessage]):
    """Bytewax-compatible Slack source."""

    def __init__(self, url: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._url = f"{url}/source"

        # One queue for each worker
        self._queues: list[queue.Queue[bytes]] = []

        self._thread = threading.Thread(target=self._receive_messages, daemon=True)
        self._lock = threading.Lock()
        self._thread.start()

    def _receive_messages(self):
        while True:
            try:
                socket = websockets.sync.client.connect(self._url)
            except Exception as e:
                log.exception(e)
                log.error("Connection failed, reconnecting in 1 second...")
                time.sleep(1)

            while True:
                try:
                    message = socket.recv()
                except Exception as e:
                    log.exception(e)
                    log.error("Receive failed, reconnecting...")
                    break

                # distribute to a worker
                with self._lock:
                    self._queues[random.randint(0, len(self._queues) - 1)].put(message)

    def build(
        self,
        now: datetime,
        worker_index: int,
        worker_count: int,
    ) -> _SlackSourcePartition:
        q: queue.Queue[bytes] = queue.Queue()
        with self._lock:
            self._queues.append(q)

        return _SlackSourcePartition(queue=q)
