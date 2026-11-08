# ORB DOCK Android client

This is the Kotlin + Jetpack Compose companion app.

## Open in Android Studio

1. Open the `android/` folder as a project.
2. Let Gradle sync.
3. Connect an Android device with USB debugging enabled, or start an emulator.
4. Run the `app` configuration.

The client discovers the Windows host using UDP broadcast on port 8766, then pairs over WebSocket on the port announced by the host (default 8765).

## Current limitations

- This is an early local-network development client.
- WebSocket transport currently uses `ws://`, not TLS. Only test on a trusted private Wi-Fi network.
- Android broadcast discovery depends on router/AP broadcast behavior. Manual host entry and a TLS/certificate-pinning setup are follow-up tasks.
- The app currently implements discovery, pairing, connection state, and heartbeat only. Remote controls and the customizable dock come later.
