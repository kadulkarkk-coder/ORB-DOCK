# ORB DOCK architecture

## Phase 1 components

- **Windows host:** Python asyncio application. Owns the WebSocket listener, pairing lifecycle, and UDP discovery endpoint.
- **Protocol layer:** versioned JSON envelope with strict message-type and payload validation.
- **Pairing manager:** temporary six-digit code, fresh per-connection challenge, PBKDF2-derived proof key, HMAC verification, attempt throttling, and single-use code rotation.
- **Android client (next task):** Kotlin + Jetpack Compose. It will discover the host over UDP, display discovered PCs, request the pairing code, compute the proof, and show connection state.

## Network defaults

- WebSocket TCP: 8765
- Discovery UDP: 8766
- Bind address: 0.0.0.0

The host must be reachable only on a trusted private LAN. The user should allow the Python host through Windows Firewall on Private networks only. Do not create router port-forwarding rules.

## Design boundaries

Phase 1 does not execute operating-system commands or expose arbitrary command dispatch. Future Windows capabilities must be implemented as named, allow-listed handlers with input validation and explicit user-visible permissions.

## Next security milestone

Before adding remote input or sensitive data:
1. Add TLS and Android certificate pinning.
2. Persist paired device identities securely and provide revocation.
3. Replace the short pairing code with a stronger authenticated enrollment flow.
4. Add authorization scopes for each capability.
5. Add integration tests on a real Windows host and Android device.
