import unittest

from jasp_nexus.platform_support import describe_host


class PlatformSupportTests(unittest.TestCase):
    def test_macos_native_is_supported(self):
        self.assertEqual(describe_host("Darwin"), ("macOS (native)", True))

    def test_windows_native_needs_wsl(self):
        name, supported = describe_host("Windows")
        self.assertIn("WSL2", name)
        self.assertFalse(supported)

    def test_wsl_recognized_by_release(self):
        name, supported = describe_host("Linux", "5.15.153.1-microsoft-standard-WSL2")
        self.assertIn("WSL", name)
        self.assertTrue(supported)

    def test_native_linux(self):
        self.assertEqual(describe_host("Linux", "6.10.2"), ("Linux (native)", True))

    def test_unknown_not_claimed_supported(self):
        self.assertFalse(describe_host("FreeBSD")[1])


if __name__ == "__main__":
    unittest.main()
