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
"""This script is used as point for the Cloud Function"""
import anomaly_detector
import ml_builder
import functions_framework
import report_downloader

METHODS_MAP = {
    "download_report": report_downloader.download_report,
    "prepare_bq": ml_builder.prepare_bq,
    "detect_anomalies": anomaly_detector.detect_and_notify,
}

@functions_framework.http
def ad_manager_alerter(request):
  """Handle HTTP request, query argument "method" determines what part of the
  code will execute. Possible values: download_report, prepare_bq,
  detect_anomalies"""
  method = request.args["method"]
  if method is None:
    raise RuntimeError("Method not provided, please provide?method=method_name")

  if method not in METHODS_MAP:
    raise RuntimeError("Method unknown, please provide?method=method_name")

  return METHODS_MAP[method]()
