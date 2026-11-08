"""UDP broadcast discovery for ORB DOCK clients."""

from __future__ import annotations

import ipaddress
import json
import logging
import socket
from asyncio import DatagramProtocol, Transport

from . import PROTOCOL_VERSION

logger = logging.getLogger(__name__)
DISCOVERY_REQUEST = b"ORB_DOCK_DISCOVER_V1"


class DiscoveryProtocol(DatagramProtocol):
    def __init__(self, *, device_name: str, websocket_port: int) -> None:
        self.device_name = device_name
        self.websocket_port = websocket_port
        self.transport: Transport | None = None

    def connection_made(self, transport: Transport) -> None:
        self.transport = transport
        logger.info("UDP discovery listening")

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        if data != DISCOVERY_REQUEST or self.transport is None:
            return
        response = {
            "type": "orb_dock.discovery.response",
            "protocol_version": PROTOCOL_VERSION,
            "name": self.device_name,
            "websocket_port": self.websocket_port,
        }
        self.transport.sendto(json.dumps(response).encode("utf-8"), addr)

    def error_received(self, exc: Exception) -> None:
        logger.warning("UDP discovery socket error: %s", exc)


def get_local_ipv4_addresses() -> list[str]:
    """Return private IPv4 addresses that may be used for manual client entry."""
    try:
        records = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET, socket.SOCK_DGRAM)
    except OSError:
        return []
    addresses = {
        record[4][0]
        for record in records
        if ipaddress.ip_address(record[4][0]).is_private
        and not ipaddress.ip_address(record[4][0]).is_loopback
        and not ipaddress.ip_address(record[4][0]).is_link_local
    }
    return sorted(addresses)


def discovery_socket_options() -> list[tuple[int, int, int]]:
    """Return reusable socket options for a broadcast-friendly UDP socket."""
    return [(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)]
