import os
from slack_sdk.webhook import WebhookClient

print(os.getenv('SOURCE_BIGQUERY_TABLE'))
webhook = WebhookClient(os.environ['SLACK_WEBHOOK_URL'])


def send_slack_message(msg):
    try:
        response = webhook.send(
            attachments=[
                {
                    "mrkdwn_in": ["text"],
                    "color": "warning",
                    "title": msg["title"],
                    "fields": [
                        {
                            "title": msg["body_title"],
                            "value": msg["body"],
                            "short": False
                        },
                    ],
                }
            ]
        )
        assert response.status_code == 200
        assert response.body == "ok"
        print(f"Sent GCP billing summary for {msg['billing_date']} to Slack channel.")
    except Exception as e:
        print(f"Encountered error when sending Slack message: {e}")