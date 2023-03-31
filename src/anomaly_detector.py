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
"""Running detect_and_notify() int his file detects anomalies in a BigQuery
forecast model and triggers an alert"""

import base64
import io
import matplotlib.pyplot as plt
from sendgrid import SendGridAPIClient, Attachment
from sendgrid.helpers.mail import Mail

from google.cloud import bigquery

from config import DATASET, ML_MODEL_NAME, DAYS_IN_CHART, COLUMN_TO_MONITOR, SENDER_ADDRESS, SENDGRID_API_KEY, ALERT_RECEIVERS, CONSECUTIVE_ANOMALIES_REQ, TIME_SERIES_ID_COL


def save_alert_chart(data, title):
  """Builds and saves a chart based on the anomaly data provided.

  Will use lower_bound and upper_bound in the data to visualize the confidence
  interval of where we expect the data. Together with a line visualizing the
  actual data with red dots when the data is classified as "is_anomaly".
  """
  fig = plt.figure(figsize=(10, 4))
  # Add title to chart
  plt.title(title)
  # Draw the confidence interval
  plt.fill_between(data["date_hour"], data["lower_bound"],
                    data["upper_bound"], color="#eef", edgecolor="#aac")
  # Plots the data for COLUMN_TO_MONITOR
  plt.plot(data["date_hour"], data[COLUMN_TO_MONITOR], "b")

  # Filter out the anomalies to visualize
  anomalies = data[data.is_anomaly]
  # Plots red dots ("ro") for all anomaly datapoints
  plt.plot(anomalies["date_hour"],
            anomalies[COLUMN_TO_MONITOR], "ro", markersize=10)

  # Formats dates nicely
  fig.autofmt_xdate()

  # Return as base64
  bytes_io = io.BytesIO()
  plt.savefig(bytes_io, format="png")
  bytes_io.seek(0)
  return base64.b64encode(bytes_io.read()).decode()


def get_anomaly_data():
  """Returns a pandas.DataFrame from the of ML.DETECT_ANOMALIES.

  Example output:
  i date_hour                 COL..TO_MONITOR is_anomaly lower_bound upper_bound
  0 2023-03-20 16:00:00+00:00 24.5            true       214.88      241.58
  1 2023-03-20 17:00:00+00:00 28.8            true       197.24      223.93
  ...

  """
  client = bigquery.Client()
  query = f"""SELECT
                date_hour,
                {TIME_SERIES_ID_COL},
                {COLUMN_TO_MONITOR},
                is_anomaly,
                lower_bound,
                upper_bound
              FROM ML.DETECT_ANOMALIES(MODEL {DATASET}.{ML_MODEL_NAME})
              WHERE
                date_hour > TIMESTAMP_SUB(
                  CURRENT_TIMESTAMP(), INTERVAL {DAYS_IN_CHART} DAY
                )"""

  query_job = client.query(query)  # Make an API request.
  return query_job.to_dataframe()


def notify(forecasting_data):
  alert_chart_b64 = save_alert_chart(forecasting_data, COLUMN_TO_MONITOR)

  message = Mail(
      from_email=SENDER_ADDRESS,
      to_emails=ALERT_RECEIVERS,
      subject=f"Anomaly detected on {COLUMN_TO_MONITOR}",
      html_content=f"""
      <p>
        Anomalies were detected on {COLUMN_TO_MONITOR}
      </p>
      <img src="cid:alert_chart">
      """
      )
  message.attachment = Attachment(
    disposition="inline",
    file_name="alert_chart.png",
    file_type="image/png",
    file_content=alert_chart_b64,
    content_id="alert_chart"
  )
  sg = SendGridAPIClient(SENDGRID_API_KEY)
  sg.send(message)


def should_notify(forecasting_data, consecutive_anomalies_req):
  """Runs rules and tells us if we should send a notification."""

  ## Don't notify if we have less than 3 datapoints.
  if len(forecasting_data.is_anomaly) < consecutive_anomalies_req:
    return False
  ## Notify if the three last datapoints were anomalies
  return all(forecasting_data.is_anomaly[-consecutive_anomalies_req:])

def detect_and_notify():
  forecasting_data = get_anomaly_data()

  if should_notify(forecasting_data, CONSECUTIVE_ANOMALIES_REQ):
    notify(forecasting_data)
    return "ALERT_SENT"
  else:
    return "OK"
