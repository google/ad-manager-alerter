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
"""This module is responsible for importing the CSV from the report downloader
into a BigQuery table, and build the forecasting model from that table given
the settings in config.py.
The function prepare_bq is responsible for executing these two steps.
"""
from google.cloud import bigquery

from config import BUCKET, REPORT_FILE, DATASET, TABLE, ML_MODEL_NAME, COLUMN_TO_MONITOR


def run_query_and_wait(query):
  """Runs a BigQuery query function and waits until it completes, will throw
  exceptions in case of any error with the query"""
  client = bigquery.Client()
  query_job = client.query(query)
  # Blocks until result is available, will throw exception in case of error.
  return query_job.result()

def import_csv_to_bq_table():
  query = f"""LOAD DATA OVERWRITE {DATASET}.{TABLE}
                  FROM FILES (
                  format = 'CSV',
                  uris = ['gs://{BUCKET}/{REPORT_FILE}'],
                  skip_leading_rows = 1
                  )"""
  run_query_and_wait(query)

def build_ml_model():
  query = f"""
          CREATE OR REPLACE MODEL {DATASET}.{ML_MODEL_NAME}
              OPTIONS(
                  MODEL_TYPE='ARIMA_PLUS',
                  TIME_SERIES_TIMESTAMP_COL='date_hour',
                  TIME_SERIES_DATA_COL='{COLUMN_TO_MONITOR}',
                  HOLIDAY_REGION='US'
              ) AS
          SELECT
              DATETIME_ADD(DATETIME(Dimension_DATE), INTERVAL Dimension_HOUR HOUR) date_hour,
              {COLUMN_TO_MONITOR}
          FROM {DATASET}.{TABLE}
          """
  run_query_and_wait(query)
  # Blocks until result is available will throw exception in case of error.


def prepare_bq():
  import_csv_to_bq_table()
  build_ml_model()
  return "OK. BigQuery data imported and ML model built"
