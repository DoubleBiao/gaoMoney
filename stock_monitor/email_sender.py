import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pandas as pd
from config import EMAIL
import logging

class EmailSender:
    def __init__(self):
        self.settings = EMAIL
        self.logger = logging.getLogger('EmailSender')

    def create_email_content(self, stocks_data):
        """Create HTML email content from stocks data"""
        if not stocks_data:
            return "No stocks of interest found today."

        # Convert stocks data to DataFrame for better formatting
        df = pd.DataFrame(stocks_data)
        
        # Create HTML table
        html_table = df.to_html(index=False)
        
        # Create email content
        html_content = f"""
        <html>
            <body>
                <h2>Stocks of Interest - {datetime.now().strftime('%Y-%m-%d')}</h2>
                <p>Found {len(stocks_data)} stocks with significant volume today:</p>
                {html_table}
                <p><small>This is an automated message from your Stock Monitor system.</small></p>
            </body>
        </html>
        """
        return html_content

    def send_email(self, stocks_data):
        """Send email with stocks of interest"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"StocksOfInterest_{datetime.now().strftime('%Y-%m-%d')}"
            msg['From'] = self.settings['sender_email']
            msg['To'] = self.settings['recipient_email']

            # Create HTML content
            html_content = self.create_email_content(stocks_data)
            msg.attach(MIMEText(html_content, 'html'))

            # Connect to SMTP server and send email
            with smtplib.SMTP(self.settings['smtp_server'], self.settings['smtp_port']) as server:
                if self.settings['use_tls']:
                    server.starttls()
                server.login(self.settings['sender_email'], self.settings['sender_password'])
                server.send_message(msg)

            self.logger.info("Email sent successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")
            return False 