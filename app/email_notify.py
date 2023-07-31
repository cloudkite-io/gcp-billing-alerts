import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_email(msg):
    try:
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        email_source = os.environ.get('EMAIL_SOURCE')
        recipient = os.environ.get('EMAIL_RECIPIENTS')
        if sendgrid_api_key and email_source and recipient:
            message = Mail(
            from_email='',
            to_emails=recipient,
            subject=msg["title"],
            html_content=msg["body"])
            
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        else:
            print("Could not send email, please pass SENDGRID_API_KEY, EMAIL_SOURCE and EMAIL_RECIPIENTS")
    except Exception as e:
        print("Error sending email: {e.message}")