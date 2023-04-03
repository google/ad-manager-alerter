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
import logging

from datetime import timedelta, datetime
from googleads import ad_manager
from googleads import oauth2
from googleads import errors
from google.cloud import storage
from config import (
    SERVICE_ACCOUNT,
    NETWORK_CODE,
    BUCKET,
    REPORT_FILE,
    COLUMNS_TO_REPORT,
    DAYS_IN_REPORT,
    DIMENSIONS_TO_REPORT
)

API_VERSION="v202302"

APPLICATION_NAME = "Anomaly detection"
METADATA_URL = "http://metadata.google.internal/computeMetadata/v1/"
METADATA_HEADERS = {"Metadata-Flavor": "Google"}
SCOPES="https://www.googleapis.com/auth/dfp"


def get_access():
  url = (f"{METADATA_URL}instance/service-accounts/" +
         f"{SERVICE_ACCOUNT}/token?scopes={SCOPES}")
  # Request an access token from the metadata server.
  r = requests.get(url, headers=METADATA_HEADERS, timeout=60)
  r.raise_for_status()
  return r.json()


def get_oauth2_client_access_token(access):
  access_token = access["access_token"]
  expires_in = int(access["expires_in"])
  token_expiry = datetime.now() + timedelta(seconds=36000+expires_in)
  return oauth2.GoogleAccessTokenClient(access_token, token_expiry)


def get_and_download_report(ad_manager_client, report_job):
  # Initialize a DataDownloader.
  report_downloader = ad_manager_client.GetDataDownloader(version=API_VERSION)

  try:
      # Run the report and wait for it to finish.
    report_job_id = report_downloader.WaitForReport(report_job)
  except errors.AdManagerReportError as e:
    logging.error("Failed to generate report. Error was: %s", e)

  # Change to your preferred export format.
  export_format = "CSV_DUMP"

  with tempfile.NamedTemporaryFile(suffix=".csv.gz", delete=False) as tmp_file:
    # Download report data.
    report_downloader.DownloadReportToFile(
        report_job_id, export_format, tmp_file)

    tmp_file.close()

    # Display results.
    logging.info("Report job with id '%s' downloaded to:%s", report_job_id,
                 tmp_file.name)
    return tmp_file.name
  raise RuntimeError("Error with file download")


def upload_to_gcs(filename, gcs_filename):
  client = storage.Client()
  bucket = client.get_bucket(BUCKET)
  blob = bucket.blob(gcs_filename)
  blob.upload_from_filename(filename)

def create_report_job():
  statement = (ad_manager.StatementBuilder(
    version=API_VERSION).Limit(None).Offset(None))

  # Create report job.
  report_job = {
      "reportQuery": {
          "dimensions": DIMENSIONS_TO_REPORT,
          "statement": statement.ToStatement(),
          "columns": COLUMNS_TO_REPORT
      }
  }
  report_job = set_date_for_report_job(report_job)
  return report_job

def get_all_saved_queries(ad_manager_client):
  report_service = ad_manager_client.GetService("ReportService",
                                                version=API_VERSION)

  # Create statement object to filter for an order.
  statement = ad_manager.StatementBuilder(version=API_VERSION)

  response = report_service.getSavedQueriesByStatement(
      statement.ToStatement())
  if "results" in response and len(response["results"]):
    return response["results"]
  raise RuntimeError("Could not find any saved reports")

def set_date_for_report_job(report_job):
  end_date = datetime.now().date()
  start_date = end_date - timedelta(days=DAYS_IN_REPORT)
  report_job["reportQuery"]["dateRangeType"] = "CUSTOM_DATE"
  report_job["reportQuery"]["startDate"] = start_date
  report_job["reportQuery"]["endDate"] = end_date
  return report_job

def get_filename_from_saved_query(saved_query):
  report_id = saved_query["id"]
  return f"report-id-{report_id}.csv.gz"

def get_ad_manager_client():
  oauth2_client = get_oauth2_client_access_token(get_access())
  ad_manager_client = ad_manager.AdManagerClient(oauth2_client,
                                                 APPLICATION_NAME,
                                                 network_code=NETWORK_CODE)
  return ad_manager_client

def download_all_saved_reports():
  """This method downloads all saved reports shared with the current user"""
  ad_manager_client = get_ad_manager_client()
  saved_queries = get_all_saved_queries(ad_manager_client)
  num_reports = []
  for saved_query in saved_queries:
    if not saved_query["isCompatibleWithApiVersion"]:
      logging.warning("""Can't run report id=%s because
                      isCompatibleWithApiVersion=False, check date-range.""",
                      saved_query["report_id"])
      continue
    report_job = {}
    report_job["reportQuery"] = saved_query["reportQuery"]
    report_job = set_date_for_report_job(report_job)
    filename = get_and_download_report(ad_manager_client, report_job)
    gcs_filename = get_filename_from_saved_query(saved_query)
    upload_to_gcs(filename, gcs_filename)
    num_reports.append(gcs_filename)
  return (f"OK. Uploaded {len(num_reports)} to gs://{BUCKET}/,"+
         f"filenames: {gcs_filename.join(',')}")

def download_report():
  """This method downloads a report from Ad Manager into Google Cloud Storage"""
  ad_manager_client = get_ad_manager_client()
  report_job = create_report_job()
  filename = get_and_download_report(ad_manager_client, report_job)
  upload_to_gcs(filename, REPORT_FILE)
  return f"OK. Report uploaded to: gs://{BUCKET}/{REPORT_FILE}"
