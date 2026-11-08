# ORB DOCK

**ORB DOCK** is an independent Android-to-Windows companion dock. The goal is to provide a customizable phone dock and a safe, local control surface for a Windows PC.

## Current status

**Phase 1 — Windows connectivity foundation (in progress)**

The first milestone establishes:
- A lightweight Python WebSocket host.
- UDP LAN discovery.
- A short-lived, one-time pairing code.
- A versioned JSON message protocol.
- Heartbeat and connection lifecycle handling.
- Unit tests for protocol and pairing primitives.

The Android client is planned as a Kotlin + Jetpack Compose application in a later Phase 1 task. No Gemini, cloud account, or paid API is required.

## Repository layout

```text
ORB-DOCK/
├── windows/
│   ├── requirements.txt
│   └── orb_dock/
│       ├── __init__.py
│       ├── config.py
│       ├── discovery.py
│       ├── main.py
│       ├── pairing.py
│       ├── protocol.py
│       └── server.py
├── tests/
│   ├── test_pairing.py
│   └── test_protocol.py
├── docs/
│   ├── ARCHITECTURE.md
│   └── PROTOCOL.md
├── .gitignore
└── README.md
```

## Windows host setup

Requires Python 3.11 or newer.

```powershell
cd windows
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m orb_dock.main
```

The host prints its temporary pairing code and listening port at startup. Keep both devices on the same trusted private Wi-Fi network. Allow Python through Windows Firewall only on **Private networks** when prompted.

## Run tests

From the repository root:

```powershell
py -m pip install -r windows/requirements.txt
py -m unittest discover -s tests -v
```

## Security status

This is an early LAN development build. The pairing proof avoids sending the PIN as a message and uses a fresh challenge, but **the current transport is not TLS-encrypted**. Use only on a trusted private network. Do not expose the host port to the internet or use this build for sensitive data. TLS with certificate pinning and persistent device authorization are required before production use.

## Roadmap

1. Phase 1: foundation, discovery, pairing, protocol, Android connection screen.
2. Phase 2: explicit Windows application and media integrations.
3. Phase 3: customizable Android dock.
4. Phase 4: touchpad, keyboard, and other user-approved controls.
5. Phase 5: WEBSTER-inspired visual polish.
6. Phase 6: USB, profiles, plugins, and optional WEBSTER integration.

## License

MIT. See [LICENSE](LICENSE).
