# Ad Manager Anomaly detection

Please note: this is not an officially supported Google product.

This project is meant to serve as inspiration for how you can do anomaly detection for an Ad Manager account by using the Ad Manager API and BigQuery ML.

- [Ad Manager Anomaly detection](#ad-manager-anomaly-detection)
  - [Setup](#setup)
    - [Create service account](#create-service-account)
    - [Create a Google Cloud Bucket](#create-a-google-cloud-bucket)
    - [Create a BigQuery dataset](#create-a-bigquery-dataset)
    - [Grant access to run Ad Manager Reports](#grant-access-to-run-ad-manager-reports)
    - [Deploy as Cloud Function](#deploy-as-cloud-function)
    - [Deploy as Cloud Workflow](#deploy-as-cloud-workflow)
  - [Overview of modules](#overview-of-modules)
    - [Ad Manager report downloader](#ad-manager-report-downloader)
    - [BigQuery import and model creation](#bigquery-import-and-model-creation)
    - [Anomaly Detector and alerter](#anomaly-detector-and-alerter)

## Setup

This code repository is prepared to be deployed to run directly on Google Cloud
What you will need in order to deploy this to Google Cloud:

Products needed:

- Google Ad Manager
- Google Cloud Project with billing enabled (billing is required for cloud
  functions, check [https://cloud.google.com/free](https://cloud.google.com/free) for the current free tier limits)

This setup assumes that you're using the default service account for the account
in order to make it as easy as possible to install.

To get started, **copy** `src/config.example.py` to `src/config.py`

   ```bash
   cp src/config.example.py src/config.py
   ```

We will edit this copy during the rest of the steps below.

### Create service account

[Create a service account](https://console.cloud.google.com/iam-admin/serviceaccounts/create) in Google Cloud.

Enter the service account email address as SERVICE_ACCOUNT in `src/config.py`.

### Create a Google Cloud Bucket

[Create a new bucket](https://console.cloud.google.com/storage/create-bucket) in Google Cloud Storage.

Save the name of the bucket in `src/config.py`.

**Important!**
Make sure you grant access for the service account to read/write to this bucket.

### Create a BigQuery dataset

[Create a new BigQuery data set](https://cloud.google.com/bigquery/docs/datasets#console) save the name of the dataset in `src/config.py`.

**Important!** Make sure you grant access for the service account to run queries onthis data set. You can do this by adding them as a Principal with the role **"Big Query Data Owner"**.

### Grant access to run Ad Manager Reports

For this project to work it needs to first fetch reports from the Ad Manager API. If you already are using the API then step 1 can be ignored.

1. [Enable API access in Ad Manager](https://support.google.com/admanager/answer/3088588?hl=en)
2. [Add the service account email to Ad Manager](https://support.google.com/admanager/answer/6078734?hl=en) with rights to run reports. (Eg. role "[Executive](https://support.google.com/admanager/answer/177403?hl=en)")

### Deploy as Cloud Function

```bash
gcloud functions deploy ad-manager-alerter \
 --source=src/ --trigger-http --gen2 --runtime=python311 \
 --region=us-central1 --entry-point=ad_manager_alerter
 --service-account=[YOUR_SERVICE_ACCOUNT]
```

First time running this command you might be prompted to enable some APIs to be able to deploy.

### Deploy as Cloud Workflow

Copy the `workflow.example.yaml` to `workflow.yaml` and edit the cloud function URL to match the URL you got from the previous step.

```bash
gcloud workflows deploy ad-manager-alert-workflow --source workflow.yaml
```

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
