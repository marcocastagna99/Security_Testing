import unittest
from my_library.scan_service import ScanService

class TestScanService(unittest.TestCase):

    def setUp(self):
        self.scan_service = ScanService('localhost', 9390, 'admin', 'admin')

    def test_perform_scan(self):
        scan_name = "Sample scan"
        targets = ["192.168.1.2", "192.168.1.3"]
        result_details = self.scan_service.perform_scan(scan_name, targets)
        
        self.assertIsNotNone(result_details)
        self.assertTrue(len(result_details) > 0)

    def test_summarize_results(self):
        result_details = [
            {
                "endpoint": "192.168.1.2:80",
                "cve": "CVE-2024-001",
                "score": 9.1,
                "av": "N",
                "ac": "L",
                "pr": "N",
                "ui": "N",
                "s": "U",
                "c": "H",
                "i": "H",
                "a": "N"
            }
        ]
        summary = self.scan_service.summarize_results(result_details)
        
        self.assertIsNotNone(summary)
        self.assertTrue("192.168.1.2:80" in summary)

if __name__ == '__main__':
    unittest.main()
