import os
import unittest
from unittest.mock import patch

from windows.orb_dock.config import Settings


class SettingsTests(unittest.TestCase):
    def test_defaults_are_valid(self):
        settings = Settings.from_environment()
        self.assertEqual(settings.websocket_port, 8765)
        self.assertEqual(settings.discovery_port, 8766)

    def test_rejects_invalid_port(self):
        with patch.dict(os.environ, {"ORB_DOCK_WS_PORT": "70000"}):
            with self.assertRaises(ValueError):
                Settings.from_environment()

    def test_rejects_non_integer_environment_value(self):
        with patch.dict(os.environ, {"ORB_DOCK_DISCOVERY_PORT": "not-a-port"}):
            with self.assertRaises(ValueError):
                Settings.from_environment()


if __name__ == "__main__":
    unittest.main()
