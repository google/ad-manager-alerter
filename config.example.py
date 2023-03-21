# Copyright 2023 Google LLC.
# SPDX-License-Identifier: Apache-2.0
"""Config file for the ad manager anomaly detection module"""

# Copy this file to config.py and update the fields below to match your project
# settings

# Step 1, download report to GCS
SERVICE_ACCOUNT = "default"

NETWORK_CODE = "[YOUR_NETWORK_CODE]"

BUCKET = "[YOUR_GCS_BUCKET]"
REPORT_FILE = "report.csv.gz"
COLUMNS_TO_REPORT = ["AD_SERVER_IMPRESSIONS"]
DAYS_IN_REPORT = 60


# Step 2, upload report to bigquery and build model
DATASET = "[YOUR_DATASET]"
TABLE = "historical_report"
ML_MODEL_NAME = "historical_report_model"

COLUMNS_TO_REPORT = ["AD_SERVER_IMPRESSIONS"]
DAYS_IN_REPORT = 60

COLUMN_TO_MONITOR = "Column_AD_SERVER_IMPRESSIONS"
