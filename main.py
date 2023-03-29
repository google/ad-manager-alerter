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

@functions_framework.http
def ad_manager_anomaly_detector(request):
  """Handle HTTP request, query argument "method" determines what part of the
  code will execute. Possible values: download_report, prepare_bq,
  detect_anomalies"""
  method = request.args["method"]
  if "download_report" == method:
    return report_downloader.download_report()
  elif "prepare_bq" == method:
    return ml_builder.prepare_bq()
  elif "detect_anomalies" == method:
    return anomaly_detector.detect_and_notify()
  else:
    raise RuntimeError("Method unknown, please provide?method=method_name")
