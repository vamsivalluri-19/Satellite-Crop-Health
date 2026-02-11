import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

class AlertManager:
    """
    Manages crop health alerts via email and notifications
    """
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.sender_email = os.getenv('SENDER_EMAIL', 'your-email@gmail.com')
        self.sender_password = os.getenv('SENDER_PASSWORD', 'your-password')
    
    def send_email_alert(self, recipient_email, subject, message, html_content=None):
        """
        Send email alert to farmer
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            
            # Add text and HTML parts
            text_part = MIMEText(message, 'plain')
            msg.attach(text_part)
            
            if html_content:
                html_part = MIMEText(html_content, 'html')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            return {'status': 'sent', 'message': 'Alert sent successfully'}
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to send email: {str(e)}")
            return {'status': 'failed', 'message': str(e)}
    
    def create_disease_alert(self, disease, confidence, email):
        """
        Create formatted disease alert
        """
        subject = f"⚠️ Crop Disease Alert: {disease} Detected"
        
        message = f"""
        Dear Farmer,
        
        A potential crop disease has been detected in your field:
        
        Disease: {disease}
        Confidence: {confidence * 100:.1f}%
        Detected: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Please take necessary action or contact an agricultural expert.
        
        Best regards,
        Crop Health Monitoring System
        """
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #d32f2f;">⚠️ Crop Disease Alert</h2>
                <p>Dear Farmer,</p>
                <p>A potential crop disease has been detected in your field:</p>
                <table style="border-collapse: collapse; border: 1px solid #ddd;">
                    <tr style="background-color: #f2f2f2;">
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Disease</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{disease}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Confidence</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{confidence * 100:.1f}%</td>
                    </tr>
                    <tr style="background-color: #f2f2f2;">
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Detected</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                </table>
                <p style="margin-top: 20px; color: #666;">Please take necessary action or contact an agricultural expert.</p>
                <p style="color: #999; font-size: 12px;">© Crop Health Monitoring System</p>
            </body>
        </html>
        """
        
        return self.send_email_alert(email, subject, message, html_content)
    
    def create_health_alert(self, health_score, ndvi, email):
        """
        Create formatted health alert
        """
        colors = {
            'Poor': '#d32f2f',
            'Fair': '#f57f17',
            'Good': '#fbc02d',
            'Excellent': '#388e3c'
        }
        
        subject = f"Crop Health Report: {health_score}"
        
        message = f"""
        Crop Health Report
        
        Health Score: {health_score}
        NDVI Value: {ndvi:.2f}
        Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: {colors.get(health_score, '#000')};">Crop Health Report</h2>
                <div style="background-color: {colors.get(health_score, '#fff')}; padding: 20px; border-radius: 5px; color: white;">
                    <h3>{health_score}</h3>
                    <p>NDVI Value: {ndvi:.2f}</p>
                    <p>Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </body>
        </html>
        """
        
        return self.send_email_alert(email, subject, message, html_content)

# Initialize alert manager
alert_manager = AlertManager()

def send_email_alert(recipient_email, subject, message):
    """
    Public function to send email alert
    """
    return alert_manager.send_email_alert(recipient_email, subject, message)

def send_disease_alert(disease, confidence, email):
    """
    Public function to send disease alert
    """
    return alert_manager.create_disease_alert(disease, confidence, email)

def send_health_alert(health_score, ndvi, email):
    """
    Public function to send health alert
    """
    return alert_manager.create_health_alert(health_score, ndvi, email)
