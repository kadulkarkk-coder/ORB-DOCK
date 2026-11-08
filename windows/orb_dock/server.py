"""Async WebSocket host for ORB DOCK."""

from __future__ import annotations

import asyncio
import logging
import secrets
from typing import Any

from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed

from .config import Settings
from .discovery import DiscoveryProtocol
from .pairing import PairingManager
from .protocol import ProtocolError, decode_message, encode_message, make_message

logger = logging.getLogger(__name__)


class OrbDockServer:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_environment()
        self.pairing = PairingManager(
            ttl_seconds=self.settings.pairing_code_ttl,
            max_attempts=self.settings.max_pair_attempts,
            attempt_window_seconds=self.settings.pair_attempt_window,
        )
        self._udp_transport: asyncio.DatagramTransport | None = None

    async def start_discovery(self) -> None:
        loop = asyncio.get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: DiscoveryProtocol(
                device_name=self.settings.device_name,
                websocket_port=self.settings.websocket_port,
            ),
            local_addr=(self.settings.host, self.settings.discovery_port),
            allow_broadcast=True,
        )
        self._udp_transport = transport  # type: ignore[assignment]
        logger.info("Discovery listening on UDP port %s", self.settings.discovery_port)

    async def close(self) -> None:
        if self._udp_transport is not None:
            self._udp_transport.close()
            self._udp_transport = None

    async def handle_connection(self, websocket: ServerConnection) -> None:
        remote = websocket.remote_address
        peer = str(remote[0]) if isinstance(remote, tuple) and remote else "unknown"
        nonce = self.pairing.create_challenge()
        challenge = make_message(
            "pair.challenge",
            {"nonce": nonce, "expires_in": self.pairing.expires_in},
        )
        try:
            await websocket.send(encode_message(challenge))
            raw = await asyncio.wait_for(websocket.recv(), timeout=30)
            request = decode_message(raw, self.settings.max_message_bytes)
            if request["type"] != "pair.request":
                await self._send_error(websocket, "pairing_required", "Pairing is required.")
                return

            payload: dict[str, Any] = request["payload"]
            device_id = payload.get("device_id")
            device_name = payload.get("device_name")
            proof = payload.get("proof")
            accepted = self.pairing.verify(
                peer=peer,
                nonce=nonce,
                device_id=device_id,
                device_name=device_name,
                proof=proof,
            )
            if not accepted:
                await self._send_error(websocket, "pairing_failed", "Pairing failed or the code expired.")
                return

            session_id = secrets.token_urlsafe(24)
            logger.info("Paired device %s (%s) from %s", device_name, device_id, peer)
            logger.info("New one-time pairing code: %s", self.pairing.current_code)
            await websocket.send(
                encode_message(
                    make_message(
                        "connection.ready",
                        {
                            "session_id": session_id,
                            "device_name": self.settings.device_name,
                            "protocol_version": 1,
                        },
                    )
                )
            )
            await self._heartbeat_loop(websocket)
        except asyncio.TimeoutError:
            logger.info("Pairing timed out for %s", peer)
        except (ProtocolError, ValueError) as exc:
            logger.warning("Rejected invalid message from %s: %s", peer, exc)
            try:
                await self._send_error(websocket, "invalid_message", str(exc))
            except ConnectionClosed:
                pass
        except ConnectionClosed:
            logger.info("Device disconnected: %s", peer)

    async def _heartbeat_loop(self, websocket: ServerConnection) -> None:
        async for raw in websocket:
            message = decode_message(raw, self.settings.max_message_bytes)
            if message["type"] == "connection.ping":
                await websocket.send(
                    encode_message(
                        make_message(
                            "connection.pong",
                            {"echo": message["payload"].get("sent_at")},
                        )
                    )
                )
            else:
                await self._send_error(websocket, "unsupported_message", "Message is not available in Phase 1.")

    @staticmethod
    async def _send_error(websocket: ServerConnection, code: str, message: str) -> None:
        await websocket.send(
            encode_message(make_message("error", {"code": code, "message": message}))
        )

    async def run(self) -> None:
        await self.start_discovery()
        logger.warning(
            "LAN development mode: WebSocket traffic is not TLS-encrypted. "
            "Use only on a trusted private network."
        )
        logger.info("Pairing code (valid %ss): %s", self.settings.pairing_code_ttl, self.pairing.current_code)
        logger.info(
            "WebSocket listening on %s:%s",
            self.settings.host,
            self.settings.websocket_port,
        )
        try:
            async with serve(
                self.handle_connection,
                self.settings.host,
                self.settings.websocket_port,
                ping_interval=20,
                ping_timeout=20,
                max_size=self.settings.max_message_bytes,
            ) as websocket_server:
                await websocket_server.serve_forever()
        finally:
            await self.close()
