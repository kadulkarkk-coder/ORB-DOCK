import json
import unittest

from windows.orb_dock.discovery import DISCOVERY_REQUEST, DiscoveryProtocol


class FakeTransport:
    def __init__(self):
        self.sent = []

    def sendto(self, data, address):
        self.sent.append((data, address))


class DiscoveryTests(unittest.TestCase):
    def test_answers_discovery_request(self):
        protocol = DiscoveryProtocol(device_name="Test PC", websocket_port=8765)
        transport = FakeTransport()
        protocol.connection_made(transport)
        protocol.datagram_received(DISCOVERY_REQUEST, ("192.168.1.25", 8766))

        self.assertEqual(len(transport.sent), 1)
        raw, address = transport.sent[0]
        response = json.loads(raw.decode("utf-8"))
        self.assertEqual(address, ("192.168.1.25", 8766))
        self.assertEqual(response["name"], "Test PC")
        self.assertEqual(response["websocket_port"], 8765)

    def test_ignores_unrecognized_datagram(self):
        protocol = DiscoveryProtocol(device_name="Test PC", websocket_port=8765)
        transport = FakeTransport()
        protocol.connection_made(transport)
        protocol.datagram_received(b"something-else", ("192.168.1.25", 8766))
        self.assertEqual(transport.sent, [])


if __name__ == "__main__":
    unittest.main()
