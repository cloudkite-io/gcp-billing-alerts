import os
from slack_sdk.webhook import WebhookClient


def send_slack_message(msg):
    slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    try:
        if slack_webhook_url:
            webhook = WebhookClient(slack_webhook_url)
            response = webhook.send(
                attachments=[
                    {
                        "mrkdwn_in": ["text"],
                        "color": "warning",
                        "title": msg["title"],
                        "pretext": msg.get("pretext", ""),
                        "fields": [
                            {
                                "title": msg["body_title"],
                                "value": msg["slack_body"],
                                "short": False
                            },
                        ],
                    }
                ]
            )
            assert response.status_code == 200
            assert response.body == "ok"
            print(f"Sent GCP billing summary for {msg['billing_date']} to Slack channel.")
        else:
            print("Could not send slack message, please pass SLACK_WEBHOOK_URL")
    except Exception as slackErr:
        print(f"Encountered error when sending Slack message: {slackErr}")