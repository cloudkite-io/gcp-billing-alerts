This application sends Slack/Email alerts displaying the GCP Project-SKUs that have exceeded the maximum/average spend over the last N days.

If you'd like to receive organization-level billing alerts instead, see [organization level alerts](https://github.com/cloudkite-io/gcp-billing-alerts/tree/org-level-alerts)

# Prerequisites.
1. Export cloud billing data to BigQuery.  
    When selecting what kind of report to export, select the `Standard usage cost` report.  
    Follow instructions outlined [here](https://cloud.google.com/billing/docs/how-to/export-data-bigquery-setup)
    Note down the complete path of the BigQuery table created by this step.
2. Following the steps outlined [here](https://api.slack.com/messaging/webhooks#getting_started), create an incoming Slack Webhook and obtain the Slack webhook URL.
3. Create a SendGrid API Key [docs](https://docs.sendgrid.com/ui/account-and-settings/api-keys#creating-an-api-key).

# How it works.
Upon startup, this application will query the BigQuery table where your Standard billing report has been exported to and check if the current day's GCP Project-SKU cost has exceeded the max/average spend over the past N days. If any Project-SKU has exceeded, it checks if it's by more that the user-defined threshold after which a Slack message with more details will be sent to your Channel as well as an email (if SendGrid API Key is provided). 
The application will then exit after the check. If you wish to have this application run on a daily basis, you can use an external scheduler to run it at your preferred intervals.

# Usage.
The application is started by running:  
```
python ./app/main.py
```
The table below shows the input parameters which should be set as environment variables before running the app.  

| PARAMETER NAME                                  | DESCRIPTION                                                                                          |         REQUIRED? |         DEFAULT VALUE |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ---------------------- | ---------------------- |
| SOURCE_BIGQUERY_TABLE_ID | The Table ID for the BigQuery table where the standard billing report is configured to export data (see step 1 of prerequisites). The table ID will be in the format `<Project ID>.<Dataset Name>.<Table Name>` | Yes |  |
| SLACK_WEBHOOK_URL | The Slack Webhook URL obtained from step 2 of prerequisites. This is the URL that allows the app to post messages to your Slack channel. | No |  |
| DAYS_TO_AVERAGE | The number of days before the current day whose cost should be used for comparison. | No | 30 |
| ALERT_METRIC | The metric on which alerts should be based. Options are: `all`, `mean`, `max`.  For instance, if `max` is selected, alerts will be sent when the day's cost exceeds the N-day max. In the case of `all`, both the N-day mean and N-day max are used to determine if alerts will be triggered.| No | `all` |
| CHANGE_THRESHOLD | This is used to determine how much above the average/max spend over `DAYS_TO_AVERAGE` days should trigger an alert. e.g. If `CHANGE_THRESHOLD` is set to 10, a Slack message and email will be sent if the current day's cost is 10/= above the average/max cost for the past `DAYS_TO_AVERAGE` days. | No | 0 |
| SENDGRID_API_KEY | The SendGrid API key obtained from step 3 of prerequisites. This is the key that allows the app to send email alerts. | No |  |
| EMAIL_SENDER | The email that will appear as the sender of email alerts sent by the application via SendGrid. Must be provided to send emails. | No |  |
| EMAIL_RECIPIENTS | A comma-separated string of email addresses to whom billing alerts will be sent. | No |  |

A `sample.env` file is provided in the root folder to be used as a template for the environment variables.

# Docker image
You can pull the Docker image of this application here:  

```
gcr.io/cloudkite-public/gcp-billing-alerts:latest
```