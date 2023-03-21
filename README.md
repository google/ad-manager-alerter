# Ad Manager Anomaly detection

Please note: this is not an officially supported Google product.

This project is meant to serve as inspiration for how you can do anomaly detection for an Ad Manager account by using the Ad Manager API and BigQuery ML.


- [Ad Manager Anomaly detection](#ad-manager-anomaly-detection)
  - [Overview of modules](#overview-of-modules)
    - [Ad Manager report downloader](#ad-manager-report-downloader)

## Overview of modules

In order to setup the entire workflow to detect anomalies
we've created three modules, [Ad Manager report downloader](report_downloader.py), BigQuery import and Model creation and the Anomaly Detector and alerter.

### Ad Manager report downloader

This module is responsible for requesting and downloading Ad Manager reports into Google Cloud Storage.

The authentication method chosen for this project is to generate access tokens directly from the Cloud Function as described here: [Authenticating applications directly with access tokens](https://cloud.google.com/compute/docs/access/create-enable-service-accounts-for-instances#applications).
