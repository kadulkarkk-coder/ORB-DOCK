# ORB DOCK protocol v1

All messages are UTF-8 JSON objects with this envelope:

```json
{
  "version": 1,
  "type": "connection.ping",
  "request_id": "unique-request-id",
  "payload": {}
}
```

## Pairing flow

1. The host sends `pair.challenge` with a random, single-connection nonce and remaining PIN lifetime.
2. The Android client asks the user to enter the six-digit code shown locally on Windows.
3. Both sides derive a key using PBKDF2-HMAC-SHA256, 300,000 iterations, and salt `ORB-DOCK-PAIRING-V1`.
4. The client computes HMAC-SHA256 over `nonce:device_id:device_name` and sends the proof in `pair.request`.
5. The host verifies the proof using constant-time comparison. A successful code is single-use.
6. The host replies with `connection.ready` and an ephemeral session identifier.

The PIN is not sent as a protocol field. The pairing challenge is fresh per connection.

## Message types in Phase 1

- `pair.challenge`: host nonce and remaining pairing-code lifetime.
- `pair.request`: client proof and device metadata.
- `connection.ping`: client heartbeat.
- `connection.pong`: host heartbeat response.
- `connection.ready`: successful pairing response.
- `error`: safe, non-sensitive error response.

Unknown message types and protocol versions are rejected. Messages are size-limited.

## Security limitations

Phase 1 currently uses a local WebSocket transport without TLS. The challenge-response flow prevents a plain PIN field and makes proofs connection-specific, but it does not provide transport confidentiality and a captured proof can be attacked offline because the PIN has only six digits. Use only on a trusted private LAN. Before real remote-control actions are added, implement TLS with Android certificate pinning, stronger device authorization, and revocation.
