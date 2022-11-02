import os
from slack_sdk.webhook import WebhookClient

print(os.getenv('SOURCE_BIGQUERY_TABLE'))
webhook = WebhookClient(os.environ['SLACK_WEBHOOK_URL'])


def send_slack_message(msg):
    try:
        response = webhook.send(
            text="fallback",
            blocks=[
                {
                    "type": "header",
                    "text": {
                            "type": "plain_text",
                        "text": msg["title"],
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": msg["body"]
                    }
                }
            ]
        )
        assert response.status_code == 200
        assert response.body == "ok"
    except Exception as e:
        print(f"Encountered error when sending Slack message: {e}")
