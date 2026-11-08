import unittest

from windows.orb_dock.protocol import (
    ProtocolError,
    decode_message,
    encode_message,
    make_message,
)


class ProtocolTests(unittest.TestCase):
    def test_round_trip(self):
        original = make_message("connection.ping", {"sent_at": 123})
        decoded = decode_message(encode_message(original))
        self.assertEqual(decoded, original)

    def test_rejects_invalid_json(self):
        with self.assertRaises(ProtocolError):
            decode_message("{not-json")

    def test_rejects_wrong_version(self):
        with self.assertRaises(ProtocolError):
            decode_message('{"version":99,"type":"connection.ping","request_id":"x","payload":{}}')

    def test_rejects_oversized_message(self):
        message = encode_message(make_message("connection.ping", {"data": "x" * 100}))
        with self.assertRaises(ProtocolError):
            decode_message(message, max_bytes=32)

    def test_rejects_unknown_message_type(self):
        with self.assertRaises(ProtocolError):
            make_message("system.execute", {})


if __name__ == "__main__":
    unittest.main()
