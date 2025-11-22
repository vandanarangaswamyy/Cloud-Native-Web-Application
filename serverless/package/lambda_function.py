import os
import json
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# -------------------------------------------------------
# Setup
# -------------------------------------------------------
log = logging.getLogger()
log.setLevel(logging.INFO)

# -------------------------------------------------------
# Lambda Handler
# -------------------------------------------------------
def lambda_handler(event, context):
    try:
        log.info("Received event: %s", json.dumps(event))

        # SNS message payload
        record = event['Records'][0]
        message_raw = record['Sns']['Message']
        message = json.loads(message_raw) if isinstance(message_raw, str) else message_raw

        recipient = message.get('email')
        token = message.get('token')

        app_domain = os.environ.get("APP_DOMAIN", "https://dev.vandanarangaswamy.com")
        verification_link = f"{app_domain}/verify?email={recipient}&token={token}"

        log.info(f"Sending verification email to: {recipient}")
        log.info(f"Verification link: {verification_link}")

        # HTML email content
        html_content = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.5; color:#333;">
            <p>Hello,</p>
            <p>Thank you for registering with <b>vandanarangaswamy.com</b>.</p>
            <p>Please verify your account by clicking the button below:</p>
            <table role="presentation" cellspacing="0" cellpadding="0">
              <tr>
                <td align="center" bgcolor="#1a73e8" style="border-radius:4px;">
                  <a href="{verification_link}" target="_blank" 
                     style="display:inline-block; padding:10px 20px; color:#ffffff;
                            text-decoration:none; font-weight:bold; border-radius:4px;">
                    Verify Account
                  </a>
                </td>
              </tr>
            </table>
            <p>If the button doesn’t work, copy and paste this link into your browser:</p>
            <p><a href="{verification_link}">{verification_link}</a></p>
            <p>If you didn’t create this account, please ignore this email.</p>
            <p>— The Vandanarangaswamy.com Team</p>
          </body>
        </html>
        """

        email = Mail(
            from_email=os.environ['FROM_EMAIL'],
            to_emails=recipient,
            subject='Verify your account - vandanarangaswamy.com',
            html_content=html_content
        )

        sg = SendGridAPIClient(os.environ['SENDGRID_API_KEY'])
        response = sg.send(email)

        log.info(f"Email sent! Status: {response.status_code}")
        return {"statusCode": 200, "body": json.dumps({"message": "Email sent successfully"})}

    except Exception as e:
        log.error(f"Error sending email: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
