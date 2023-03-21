# Ad Manager Anomaly detection

Please note: this is not an officially supported Google product.

This project is meant to serve as inspiration for how you can do anomaly detection for an Ad Manager account by using the Ad Manager API and BigQuery ML.

- [Ad Manager Anomaly detection](#ad-manager-anomaly-detection)
  - [Overview of modules](#overview-of-modules)
    - [Ad Manager report downloader](#ad-manager-report-downloader)
    - [BigQuery import and model creation](#bigquery-import-and-model-creation)
    - [Anomaly Detector and alerter](#anomaly-detector-and-alerter)


## Overview of modules

In order to setup the entire workflow to detect anomalies
we've created three modules, [Ad Manager report downloader](report_downloader.py), [BigQuery import and Model creation](ml_builder.py) and the [Anomaly Detector and alerter](anomaly_detector.py).

### Ad Manager report downloader

This module is responsible for requesting and downloading Ad Manager reports into Google Cloud Storage.

The authentication method chosen for this project is to generate access tokens directly from the Cloud Function as described here: [Authenticating applications directly with access tokens](https://cloud.google.com/compute/docs/access/create-enable-service-accounts-for-instances#applications).

### BigQuery import and model creation

This module is responsible for importing the CSV from the report downloader into a BigQuery table, and build the forecasting model from that table given the settings in config.py.

### Anomaly Detector and alerter

This module is reponsible for detecting anomalies and send email alerts with charts when they occur.
