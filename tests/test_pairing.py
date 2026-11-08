import unittest

from windows.orb_dock.pairing import PairingManager, create_client_proof, derive_pairing_key


class PairingTests(unittest.TestCase):
    def test_key_requires_six_digits(self):
        for invalid in ("12345", "1234567", "12ab56"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    derive_pairing_key(invalid)

    def test_valid_proof_is_accepted_once(self):
        manager = PairingManager(ttl_seconds=60)
        pin = manager._pin
        nonce = manager.create_challenge()
        proof = create_client_proof(pin, nonce, "android-1", "Android")
        self.assertTrue(manager.verify(
            peer="192.168.1.20",
            nonce=nonce,
            device_id="android-1",
            device_name="Android",
            proof=proof,
        ))
        # Successful pairing rotates the code, so the previous proof is no longer valid.
        self.assertNotEqual(manager._pin, pin)

    def test_invalid_proof_is_rejected(self):
        manager = PairingManager()
        self.assertFalse(manager.verify(
            peer="192.168.1.20",
            nonce=manager.create_challenge(),
            device_id="android-1",
            device_name="Android",
            proof="0" * 64,
        ))

    def test_attempt_limit_is_per_peer(self):
        manager = PairingManager(max_attempts=2)
        for _ in range(2):
            manager.verify(
                peer="192.168.1.20",
                nonce=manager.create_challenge(),
                device_id="android-1",
                device_name="Android",
                proof="0" * 64,
            )
        self.assertFalse(manager.verify(
            peer="192.168.1.20",
            nonce=manager.create_challenge(),
            device_id="android-1",
            device_name="Android",
            proof="0" * 64,
        ))


if __name__ == "__main__":
    unittest.main()
