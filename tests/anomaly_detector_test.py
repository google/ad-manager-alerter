# Copyright 2023 Google LLC.
# SPDX-License-Identifier: Apache-2.0
import unittest
import anomaly_detector

class TestAnomalyDetector(unittest.TestCase):

    def test_should_notify(self):
        example = MockDataFrame([False, True, False, True, True, True])
        self.assertTrue(anomaly_detector.should_notify(example, 3))

    def test_should_not_notify_recovery(self):
        example = MockDataFrame([True, True, True, False, True])
        self.assertFalse(anomaly_detector.should_notify(example, 3))

    def test_should_not_notify_two_events(self):
        example = MockDataFrame([True, True])
        self.assertFalse(anomaly_detector.should_notify(example, 3))

    def test_should_not_notify_empty_list(self):
        example = MockDataFrame([])
        self.assertFalse(anomaly_detector.should_notify(example, 3))

class MockDataFrame:
    def __init__(self, data):
        self.is_anomaly = data
if __name__ == '__main__':
    unittest.main()
