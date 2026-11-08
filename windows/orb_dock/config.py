"""Configuration for the ORB DOCK Windows host."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    host: str = "0.0.0.0"
    websocket_port: int = 8765
    discovery_port: int = 8766
    device_name: str = "ORB DOCK Windows Host"
    pairing_code_ttl: int = 180
    max_message_bytes: int = 64 * 1024
    max_pair_attempts: int = 5
    pair_attempt_window: int = 300

    @classmethod
    def from_environment(cls) -> "Settings":
        """Load settings while rejecting invalid port and limit values."""
        settings = cls(
            host=os.getenv("ORB_DOCK_HOST", "0.0.0.0"),
            websocket_port=_read_int("ORB_DOCK_WS_PORT", 8765),
            discovery_port=_read_int("ORB_DOCK_DISCOVERY_PORT", 8766),
            device_name=os.getenv("ORB_DOCK_DEVICE_NAME", "ORB DOCK Windows Host"),
            pairing_code_ttl=_read_int("ORB_DOCK_PAIRING_TTL", 180),
            max_message_bytes=_read_int("ORB_DOCK_MAX_MESSAGE_BYTES", 64 * 1024),
            max_pair_attempts=_read_int("ORB_DOCK_MAX_PAIR_ATTEMPTS", 5),
            pair_attempt_window=_read_int("ORB_DOCK_PAIR_WINDOW", 300),
        )
        if not 1 <= settings.websocket_port <= 65535:
            raise ValueError("ORB_DOCK_WS_PORT must be between 1 and 65535")
        if not 1 <= settings.discovery_port <= 65535:
            raise ValueError("ORB_DOCK_DISCOVERY_PORT must be between 1 and 65535")
        if settings.pairing_code_ttl <= 0:
            raise ValueError("ORB_DOCK_PAIRING_TTL must be positive")
        if settings.max_message_bytes < 1024:
            raise ValueError("ORB_DOCK_MAX_MESSAGE_BYTES must be at least 1024")
        if settings.max_pair_attempts < 1 or settings.pair_attempt_window < 1:
            raise ValueError("Pairing rate-limit settings must be positive")
        return settings


def _read_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
