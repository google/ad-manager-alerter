# Copyright 2023 Google LLC.
# SPDX-License-Identifier: Apache-2.0
"""This script is used as point for the Cloud Function"""
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
  else:
    raise RuntimeError("Method unknown, please provide?method=method_name")
