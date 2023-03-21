# Copyright 2023 Google LLC.
# SPDX-License-Identifier: Apache-2.0
"""Running detect_and_notify() int his file detects anomalies in a BigQuery
forecast model and triggers an alert"""

import matplotlib.pyplot as plt
import yagmail

from google.cloud import bigquery

from config import DATASET, ML_MODEL_NAME, DAYS_IN_CHART, COLUMN_TO_MONITOR, SENDER_GMAIL_ADDRESS, SENDER_GMAIL_PASSWORD, ALERT_RECEIVERS, CONSECUTIVE_ANOMALIES_REQ


def save_alert_chart(data, filename):
  """Builds and saves a chart based on the anomaly data provided.

  Will use lower_bound and upper_bound in the data to visualize the confidence
  interval of where we expect the data. Together with a line visualizing the
  actual data with red dots when the data is classified as "is_anomaly".
  """
  fig = plt.figure(figsize=(10, 4))
  plt.fill_between(data["date_hour"], data["lower_bound"],
                    data["upper_bound"], color="#eef", edgecolor="#aac")
  # Plots the data for COLUMN_TO_MONITOR
  plt.plot(data["date_hour"], data[COLUMN_TO_MONITOR], "b")

  # Filter out the anomalies to visualize
  anomalies = data[data.is_anomaly]
  # Plots red dots ("ro") for all anomaly datapoints
  plt.plot(anomalies["date_hour"],
            anomalies[COLUMN_TO_MONITOR], "ro", markersize=10)

  # Formats dates nice
  fig.autofmt_xdate()

  #Saves to file
  plt.savefig(filename)


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
  filename = "chart.png"
  save_alert_chart(forecasting_data, filename)
  yag = yagmail.SMTP(SENDER_GMAIL_ADDRESS, SENDER_GMAIL_PASSWORD)
  contents = [
    "<h1>Anomaly detected</h1>",
    yagmail.inline(filename)
  ]
  subject = "Anomaly detected"
  yag.send(ALERT_RECEIVERS, subject, contents)


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
