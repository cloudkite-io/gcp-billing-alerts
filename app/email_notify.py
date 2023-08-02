import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def build_email_msg(changes_list, days_to_average, currency, alert_msg):
    email_msg = {"title": alert_msg["title"], 
                    "body": f"""
                    <p>{alert_msg["body_title"]}</p><p>

                    <table border="1" cellpadding="1" cellspacing="1"">
                    <tr>
                        <th>Project ID</th>
                        <th>SKU ID</th>
                        <th>SKU Description</th>
                        <th>Day's Spend ({currency})</th>
                        <th>Metric Exceeded</th>
                        <th>Exceeded Amount ({currency})</th>
                        <th>Exceeded %</th>
                    </tr>
                    """}
    for change in changes_list:
        email_msg["body"] += (f"""
                                <tr>
                                <td>{change['project_id']}</td>
                                <td>{change['sku_id']}</td>
                                <td>{change['sku_description']}</td>
                                <td>{change['spend']}</td>
                                <td>{days_to_average}-day {change['change_type']}</td>
                                <td>{change['change']}</td>
                                <td>{change['perc_change']}</td>
                            </tr>
                                """)
    email_msg["body"] += "</table></p>"
    if pretext := alert_msg.get("pretext", ""):
        email_msg["body"] += f"<p><i>{pretext}</i></p>"
    return email_msg

def send_email(changes_list, days_to_average, currency, alert_msg):
    try:     
        sender = os.environ.get('EMAIL_SENDER')
        recipients = os.environ.get('EMAIL_RECIPIENTS')
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')

        if sendgrid_api_key and sender and recipients:
            msg = build_email_msg(changes_list, days_to_average, currency, alert_msg)
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