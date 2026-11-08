"""Versioned JSON message helpers shared by the host and future Android client."""

from __future__ import annotations

import json
import uuid
from typing import Any

from . import PROTOCOL_VERSION

MAX_MESSAGE_BYTES = 64 * 1024
ALLOWED_TYPES = {
    "pair.challenge",
    "pair.request",
    "connection.ping",
    "connection.pong",
    "connection.ready",
    "error",
}


class ProtocolError(ValueError):
    """Raised when an incoming protocol message is invalid."""


def make_message(message_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    if message_type not in ALLOWED_TYPES:
        raise ProtocolError(f"Unsupported message type: {message_type}")
    return {
        "version": PROTOCOL_VERSION,
        "type": message_type,
        "request_id": uuid.uuid4().hex,
        "payload": payload or {},
    }


def encode_message(message: dict[str, Any]) -> str:
    validate_message(message)
    return json.dumps(message, separators=(",", ":"), ensure_ascii=False)


def decode_message(raw: str | bytes, max_bytes: int = MAX_MESSAGE_BYTES) -> dict[str, Any]:
    if isinstance(raw, bytes):
        try:
            raw = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ProtocolError("Message must be UTF-8") from exc
    if len(raw.encode("utf-8")) > max_bytes:
        raise ProtocolError("Message exceeds the configured size limit")
    try:
        message = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProtocolError("Message is not valid JSON") from exc
    validate_message(message)
    return message


def validate_message(message: Any) -> None:
    if not isinstance(message, dict):
        raise ProtocolError("Message must be a JSON object")
    if message.get("version") != PROTOCOL_VERSION:
        raise ProtocolError("Unsupported protocol version")
    if message.get("type") not in ALLOWED_TYPES:
        raise ProtocolError("Unsupported or missing message type")
    request_id = message.get("request_id")
    if not isinstance(request_id, str) or not 1 <= len(request_id) <= 64:
        raise ProtocolError("request_id must be a non-empty string of at most 64 characters")
    if not isinstance(message.get("payload"), dict):
        raise ProtocolError("payload must be a JSON object")
