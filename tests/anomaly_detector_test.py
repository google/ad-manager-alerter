# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Some minimal tests to make sure alerting works as expected"""
import unittest
import anomaly_detector

class TestAnomalyDetector(unittest.TestCase):
  """ minimal tests to make sure alerting works as expected"""
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
