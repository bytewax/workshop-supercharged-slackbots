"""A simple websocket proxy for combating the rate limits of the Slack API."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

import dotenv
import fastapi
import uvicorn
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp
from slack_bolt.async_app import AsyncSay
from starlette.datastructures import Address
from starlette.websockets import WebSocketDisconnect

log = logging.getLogger(__name__)


# This won't work with many workers, but we are limiting ours to just 1
SOURCE_QUEUES: dict[Address, asyncio.Queue] = {}
SINK_QUEUE: asyncio.Queue = asyncio.Queue()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
    handlers=[logging.StreamHandler()],
)

dotenv.load_dotenv()

slack_app = None


@asynccontextmanager
async def slack_connector(app: fastapi.FastAPI):
    # TODO: Ugly, but good enough for demo
    global slack_app

    slack_app = AsyncApp(
        token=os.environ.get("SLACK_BOT_TOKEN"),
        signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    )

    slack_app.event(
        {
            "type": "message",
            "subtype": None,
        }
    )(distribute_message_to_listeners)

    loop = asyncio.get_event_loop()

    loop.create_task(
        AsyncSocketModeHandler(
            slack_app, os.environ.get("SLACK_APP_TOKEN")
        ).start_async()
    )

    yield


fastapi_app = fastapi.FastAPI(lifespan=slack_connector)


@fastapi_app.websocket("/source")
async def source_handler(websocket: fastapi.WebSocket):
    await websocket.accept()

    assert websocket.client is not None

    SOURCE_QUEUES[websocket.client] = asyncio.Queue()
    try:
        while True:
            try:
                msg = SOURCE_QUEUES[websocket.client].get_nowait()
            except asyncio.queues.QueueEmpty:
                await asyncio.sleep(0.3)
                continue

            try:
                log.info("Received message: %s", msg)
                await websocket.send_bytes(msg.encode("utf-8"))
            except WebSocketDisconnect:
                break
    finally:
        SOURCE_QUEUES.pop(websocket.client)


@fastapi_app.websocket("/sink")
async def sink_handler(websocket: fastapi.WebSocket):
    await websocket.accept()

    while True:
        try:
            msg_bytes = await websocket.receive_text()
        except WebSocketDisconnect:
            return

        msg = json.loads(msg_bytes)
        log.info("Sending message: %s", msg)

        reply = msg["text"]

        if slack_app is not None:
            say = AsyncSay(slack_app.client, msg["channel"])
            await say(reply, username="Bytewax", thread_ts=msg["ts"])


async def distribute_message_to_listeners(body: dict[str, Any], say):
    event = body["event"]
    if event.get("bot_id") is not None:
        return  # avoid infinite loop

    for queue in SOURCE_QUEUES.values():
        # We dont want to await here, as the dict can change size
        try:
            queue.put_nowait(json.dumps(event))
        except asyncio.queues.QueueFull:
            continue


def main():
    """Run the server."""
    uvicorn.run(
        "main:fastapi_app",
        host="0.0.0.0",  # This is necessary when running in docker
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
