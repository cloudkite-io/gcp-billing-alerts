import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_email(msg):
    try:     
        sender = os.environ.get('EMAIL_SENDER')
        recipients = os.environ.get('EMAIL_RECIPIENTS')
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')

        if sendgrid_api_key and sender and recipients:
            recipients = recipients.replace(" ", "")
            recipients = recipients.split(",")
            message = Mail(
            from_email=sender,
            to_emails=recipients,
            subject=msg["title"],
            html_content=msg["body"])
            
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        else:
            print("Could not send email, please pass SENDGRID_API_KEY, EMAIL_SOURCE and EMAIL_RECIPIENTS")
    except Exception as emailErr:
        print(f"Error sending email: {emailErr}")