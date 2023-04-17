# Ad Manager Anomaly detection

Please note: this is not an officially supported Google product.

This project is meant to serve as inspiration for how you can do anomaly detection for an Ad Manager account by using the Ad Manager API and BigQuery ML.

- [Ad Manager Anomaly detection](#ad-manager-anomaly-detection)
  - [Setup](#setup)
    - [Create service account](#create-service-account)
    - [Create a Google Cloud Bucket](#create-a-google-cloud-bucket)
    - [Create a BigQuery dataset (used for alerting)](#create-a-bigquery-dataset-used-for-alerting)
    - [Grant access to run Ad Manager Reports](#grant-access-to-run-ad-manager-reports)
    - [Deploy to cloud](#deploy-to-cloud)
      - [Making sure we can send emails](#making-sure-we-can-send-emails)
      - [Enable services to deploy to functions / workflows](#enable-services-to-deploy-to-functions--workflows)
      - [Deploy Cloud Function](#deploy-cloud-function)
      - [Deploy as Cloud Workflow](#deploy-as-cloud-workflow)
      - [Deploy to Cloud Scheduler](#deploy-to-cloud-scheduler)
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

For the setup instructions below we're using
[Google Cloud CLI](https://cloud.google.com/sdk/docs/install-sdk) to run some
commands for us, if you haven't installed and configured that yet - do it now.


To get started, clone this repository and make a copy of the config file.

```bash
git clone https://github.com/google/ad-manager-alerter.git
cd ad-manager-alerter
cp src/config.example.py src/config.py
```

We will edit `src/config.py` during the rest of the steps below.

### Create service account

[Create a service account](https://console.cloud.google.com/iam-admin/serviceaccounts/create) in Google Cloud.

Enter the service account email address as SERVICE_ACCOUNT in `src/config.py`.

### Create a Google Cloud Bucket

[Create a new bucket](https://console.cloud.google.com/storage/create-bucket) in Google Cloud Storage.

Save the name of the bucket in `src/config.py`.

**Important!**
Make sure you grant access for the service account to read/write to this bucket.

### Create a BigQuery dataset (used for alerting)

*If you're not planning to use the alerting features you can skip this step.*

[Create a new BigQuery data set](https://cloud.google.com/bigquery/docs/datasets#console) save the name of the dataset in `src/config.py`.

**Important!** Make sure you grant access for the service account to run queries onthis data set. You can do this by adding them as a Principal with the role **"Big Query Data Owner"**.

### Grant access to run Ad Manager Reports

For this project to work it needs to first fetch reports from the Ad Manager API. If you already are using the API then step 1 can be ignored.

1. [Enable API access in Ad Manager](https://support.google.com/admanager/answer/3088588?hl=en)
2. [Add the service account email to Ad Manager](https://support.google.com/admanager/answer/6078734?hl=en) with rights to run reports. (Eg. role "[Executive](https://support.google.com/admanager/answer/177403?hl=en)")

### Deploy to cloud

#### Making sure we can send emails

*If you're not planning to use the alerting features you can skip this step.*

Making sure emails are sent and received correctly can be tricky, to make it easier this example uses SendGrid in order to send emails.

If you don't have a SendGrid account you can create one throught the [SendGrid page on Cloud Marketplace](https://console.cloud.google.com/marketplace/details/sendgrid-app/sendgrid-email).

Once your sendgrid account is created you can follow the steps to setup a send account and get your API KEY.

#### Enable services to deploy to functions / workflows

First time running the commands below you might be prompted to enable some APIs to be able to deploy.

If you want to you can enable them beforehand with the following command:

```bash
gcloud services enable artifactregistry.googleapis.com cloudbuild.googleapis.com cloudfunctions.googleapis.com cloudscheduler.googleapis.com containerregistry.googleapis.com  logging.googleapis.com monitoring.googleapis.com pubsub.googleapis.com run.googleapis.com workflows.googleapis.com
```

#### Deploy Cloud Function

```bash
gcloud functions deploy ad-manager-alerter \
 --source=src/ --trigger-http --gen2 --runtime=python311 \
 --region=us-central1 --entry-point=ad_manager_alerter \
 --memory=512M --timeout=3600 \
 --service-account=[YOUR_SERVICE_ACCOUNT] \
 --set-env-vars SENDGRID_API_KEY=[SENDGRID_API_KEY]
```

When this command finishes you should see something like:

```txt
...
  uri: https://your_cloud_function-abc123.run.app
state: ACTIVE
```

Copy and save the "uri", you need this in the next stage.

#### Deploy as Cloud Workflow

Copy the `workflow.example.yaml` to `workflow.yaml` and edit the cloud function URL to match the URL you got from the previous step.

*If you want to only run parts of this example library (eg. only export to GCS)
modify this file and remove the steps you don't want to run.*

```bash
gcloud workflows deploy ad-manager-alert-workflow --source workflow.yaml
```

Verify that it's working by running the workflow, this can be done in the terminal via:

```bash
gcloud workflows run ad-manager-alert-workflow
```

If it runs without issue now could be a good time to set it up to run on a schedule via Cloud Scheduler.

If there are issues here, pause and fix them before continuing.

#### Deploy to Cloud Scheduler

When you verified it's working you can
[setup a new Cloud Scheduler](https://console.cloud.google.com/cloudscheduler/jobs/new)
to run the workflow at an interval.

## Overview of modules

In order to setup the entire workflow to detect anomalies
we've created three modules, [Ad Manager report downloader](report_downloader.py), [BigQuery import and Model creation](ml_builder.py) and the [Anomaly Detector and alerter](anomaly_detector.py).

### Ad Manager report downloader

This module is responsible for requesting and downloading Ad Manager reports into Google Cloud Storage.

It has two main entry points "download_report" and "download_all_saved_reports".

* `download_report` is used for the report that will be used for alerting
  purposes.
* `download_all_saved_reports` downloads all reports that have been shared with
  the service account used to run the script.

The authentication method chosen for this project is to generate access tokens directly from the Cloud Function as described here: [Authenticating applications directly with access tokens](https://cloud.google.com/compute/docs/access/create-enable-service-accounts-for-instances#applications).

### BigQuery import and model creation

This module is responsible for importing the CSV from the report downloader into a BigQuery table, and build the forecasting model from that table given the settings in config.py.

### Anomaly Detector and alerter

This module is reponsible for detecting anomalies and send email alerts with charts when they occur.
