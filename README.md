This application sends Slack alerts when the daily GCP spend reaches user-defined thresholds.
The four thresholds supported by the application are:  
- When the day's GCP bill is X amount more than the previous day.
- When the day's GCP bill is Y% greater than that of the previous day.
- When the day's GCP bill is X amount greater than the average spend over the past Z days.
- When the day's GCP bill is Y% greater than the average spend over the past Z days.


# Prerequisites.
1. Export cloud billing data to BigQuery.  
    When selecting what kind of report to export, select the `Standard usage cost` report.  
    Follow instructions outlined [here](https://cloud.google.com/billing/docs/how-to/export-data-bigquery-setup)
    Note down the complete path of the BigQuery table created by this step.
2. Following the steps outlined [here](https://api.slack.com/messaging/webhooks#getting_started), create an incoming Slack Webhook and obtain the Slack webhook URL.

# How it works.
Upon startup, this application will query the BigQuery table where your Standard billing report has been exported to and check if the previous day's GCP bill has exceeded any of the user-defined thresholds. If any threshold has been exceeded, a Slack message with more details will be sent to your Channel. 
The application will then exit after the check. If you wish to have this application run on a daily basis, you can use an external scheduler to run it at your preferred intervals.

# Usage.
The application is started by running:  
```
python ./app/main.py
```
The table below shows the input parameters which should be set as environment variables before running the app.  

| PARAMETER NAME                                  | DESCRIPTION                                                                                          |         REQUIRED? |         DEFAULT VALUE |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ---------------------- | ---------------------- |
| SLACK_WEBHOOK_URL | The Slack Webhook URL obtained from step 2 of prerequisites. This is the URL that allows the app to post messages to your Slack channel. | Yes |  |
| SOURCE_BIGQUERY_TABLE_ID | The Table ID for the BigQuery table where the standard billing report is configured to export data (see step 1 of prerequisites). The table ID will be in the format `<Project ID>.<Dataset Name>.<Table Name>` | Yes |  |
| DAYS_TO_AVERAGE | The number of days before the previous day whose cost should be averaged for comparison. | No | 7 |
| AVERAGE_UPPER_LIMIT_AMOUNT_CHANGE | This is used to determine how much above the average spend over `DAYS_TO_AVERAGE` days should trigger a Slack notification. e.g. If `AVERAGE_UPPER_LIMIT_AMOUNT_CHANGE` is set to 10, a Slack message will be sent to your channel if the previous day's cost is 10/= above the average cost for the past `DAYS_TO_AVERAGE` days. | No |  |
| AVERAGE_UPPER_LIMIT_PERCENTAGE_CHANGE | This is used to determine what percentage above the average spend over `DAYS_TO_AVERAGE` days should trigger a Slack notification. e.g. If `AVERAGE_UPPER_LIMIT_PERCENTAGE_CHANGE` is set to 10, a Slack message will be sent to your channel if the previous day's cost is 10% higher than the average cost for the past `DAYS_TO_AVERAGE` days. | No |  |
| DAILY_UPPER_LIMIT_AMOUNT_CHANGE | This is used to check if the previous day's cost has exceeded the (previous day - 1) billing cost by this amount e.g. If `DAILY_UPPER_LIMIT_AMOUNT_CHANGE` is set to 10, a Slack message will be sent to your channel if the previous day's cost is higher than the (previous day - 1) by 10/= | No |  |
| DAILY_UPPER_LIMIT_PERCENTAGE_CHANGE | This is used to check if the previous day's cost has exceeded the (previous day - 1) billing cost by this percentage e.g. If `DAILY_UPPER_LIMIT_PERCENTAGE_CHANGE` is set to 10, a Slack message will be sent to your channel if the previous day's cost is 10% higher than the (previous day - 1) | No |  |

A `sample.env` file is provided in the root folder to be used as a template for the environment variables.

# Docker image
You can access the Docker image of this application here:  

```
gcr.io/cloudkite-public/gcp-billing-alerts:latest
```