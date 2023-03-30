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
"""This module is responsible for requesting and downloading Ad Manager reports
into Google Cloud Storage.
The function download_report downloads ad manager report into google cloud
storage based on settings in config.py"""


import requests
import tempfile

from datetime import timedelta, datetime
from googleads import ad_manager
from googleads import oauth2
from googleads import errors
from google.cloud import storage
from config import SERVICE_ACCOUNT, NETWORK_CODE, BUCKET, REPORT_FILE, COLUMNS_TO_REPORT, DAYS_IN_REPORT

APPLICATION_NAME = 'Anomaly detection'
METADATA_URL = 'http://metadata.google.internal/computeMetadata/v1/'
METADATA_HEADERS = {'Metadata-Flavor': 'Google'}
SCOPES='https://www.googleapis.com/auth/dfp'

API_VERSION='v202302'

def get_access():
  url = (f'{METADATA_URL}instance/service-accounts/' +
         f'{SERVICE_ACCOUNT}/token?scopes={SCOPES}')
  # Request an access token from the metadata server.
  r = requests.get(url, headers=METADATA_HEADERS, timeout=60)
  r.raise_for_status()
  return r.json()


def get_oauth2_client_access_token(access):
  access_token = access['access_token']
  expires_in = int(access['expires_in'])
  token_expiry = datetime.now() + timedelta(seconds=36000+expires_in)
  return oauth2.GoogleAccessTokenClient(access_token, token_expiry)


def get_and_download_report(ad_manager_client):
  statement = (ad_manager.StatementBuilder(
    version=API_VERSION).Limit(None).Offset(None))
  # Set the start and end dates of the report to run (past 8 days).
  end_date = datetime.now().date()
  start_date = end_date - timedelta(days=DAYS_IN_REPORT)

  # Create report job.
  report_job = {
      'reportQuery': {
          'dimensions': ['DATE', 'HOUR'],
          'statement': statement.ToStatement(),
          'columns': COLUMNS_TO_REPORT,
          'dateRangeType': 'CUSTOM_DATE',
          'startDate': start_date,
          'endDate': end_date
      }
  }

  # Initialize a DataDownloader.
  report_downloader = ad_manager_client.GetDataDownloader(version=API_VERSION)

  try:
      # Run the report and wait for it to finish.
    report_job_id = report_downloader.WaitForReport(report_job)
  except errors.AdManagerReportError as e:
    print(f'Failed to generate report. Error was: {e}')

  # Change to your preferred export format.
  export_format = 'CSV_DUMP'

  with tempfile.NamedTemporaryFile(suffix='.csv.gz', delete=False) as tmp_file:
    # Download report data.
    report_downloader.DownloadReportToFile(
        report_job_id, export_format, tmp_file)

    tmp_file.close()

    # Display results.
    print(f'Report job with id "{report_job_id}" downloaded to:{tmp_file.name}')
    return tmp_file.name
  raise RuntimeError('Error with file download')


def upload_to_gcs(filename):
  client = storage.Client()
  bucket = client.get_bucket(BUCKET)
  blob = bucket.blob(REPORT_FILE)
  blob.upload_from_filename(filename)


def download_report():
  """This method downloads a report from Ad Manager into Google Cloud Storage"""
  oauth2_client = get_oauth2_client_access_token(get_access())
  ad_manager_client = ad_manager.AdManagerClient(
    oauth2_client, APPLICATION_NAME, network_code=NETWORK_CODE)
  filename = get_and_download_report(ad_manager_client)
  upload_to_gcs(filename)
  return f'OK. Report uploaded to: gs://{BUCKET}/{REPORT_FILE}'
