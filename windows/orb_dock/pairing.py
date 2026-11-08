"""Short-lived pairing challenge and proof verification."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import string
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field


PAIRING_SALT = b"ORB-DOCK-PAIRING-V1"


def derive_pairing_key(pin: str) -> bytes:
    """Derive a proof key from a six-digit code.

    The Android implementation must use the same PBKDF2 parameters and salt.
    """
    if len(pin) != 6 or any(char not in string.digits for char in pin):
        raise ValueError("Pairing code must contain exactly six digits")
    return hashlib.pbkdf2_hmac("sha256", pin.encode("ascii"), PAIRING_SALT, 300_000)


def create_client_proof(pin: str, nonce: str, device_id: str, device_name: str) -> str:
    """Create the HMAC proof expected by the host."""
    key = derive_pairing_key(pin)
    message = f"{nonce}:{device_id}:{device_name}".encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


@dataclass(slots=True)
class PairingManager:
    ttl_seconds: int = 180
    max_attempts: int = 5
    attempt_window_seconds: int = 300
    _pin: str = field(init=False, repr=False)
    _expires_at: float = field(init=False, repr=False)
    _attempts: dict[str, deque[float]] = field(default_factory=lambda: defaultdict(deque), repr=False)

    def __post_init__(self) -> None:
        if self.ttl_seconds <= 0 or self.max_attempts <= 0 or self.attempt_window_seconds <= 0:
            raise ValueError("Pairing limits must be positive")
        self.rotate_code()

    def rotate_code(self) -> str:
        self._pin = "".join(secrets.choice(string.digits) for _ in range(6))
        self._expires_at = time.monotonic() + self.ttl_seconds
        self._attempts.clear()
        return self._pin

    @property
    def expires_in(self) -> int:
        return max(0, int(self._expires_at - time.monotonic()))

    def create_challenge(self) -> str:
        return secrets.token_urlsafe(32)

    def verify(
        self,
        *,
        peer: str,
        nonce: str,
        device_id: str,
        device_name: str,
        proof: str,
        now: float | None = None,
    ) -> bool:
        current = time.monotonic() if now is None else now
        if current >= self._expires_at:
            return False
        if not all(isinstance(value, str) and value for value in (peer, nonce, device_id, device_name, proof)):
            return False
        if len(device_id) > 128 or len(device_name) > 80 or len(proof) != 64:
            return False

        attempts = self._attempts[peer]
        cutoff = current - self.attempt_window_seconds
        while attempts and attempts[0] < cutoff:
            attempts.popleft()
        if len(attempts) >= self.max_attempts:
            return False
        attempts.append(current)

        expected = create_client_proof(self._pin, nonce, device_id, device_name)
        accepted = hmac.compare_digest(expected, proof)
        if accepted:
            # Pairing codes are single-use. A fresh code is required for another device.
            self.rotate_code()
        return accepted
