from datetime import datetime
import threading
import time
from queue import Queue
import schedule
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

Base = declarative_base()

class ScheduledEmail(Base):
    __tablename__ = 'scheduled_emails'
    
    id = Column(Integer, primary_key=True)
    email = Column(String)
    content = Column(String)
    scheduled_time = Column(DateTime)
    company_name = Column(String, nullable=True)
    status = Column(String, default='pending')

class EmailScheduler:
    def __init__(self, db_url='sqlite:///emails.db', sendgrid_client=None):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Store SendGrid client
        if sendgrid_client:
            self.sendgrid_client = sendgrid_client
        else:
            self.sendgrid_client = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        
        self.from_email = os.getenv('FROM_EMAIL')
        print(f"Initialized EmailScheduler with FROM_EMAIL: {self.from_email}")

    def send_email_via_esp(self, to_email, content):
        """
        Send email using SendGrid with improved error handling
        """
        try:
            print(f"\nPreparing to send email to: {to_email}")
            print(f"Content preview: {content[:100]}...")  # Debug log

            if not content or len(content.strip()) == 0:
                raise ValueError("Email content is empty")

            # Create the email
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject='Your Customized Email',
                html_content=content
            )

            # Send the email
            response = self.sendgrid_client.send(message)
            print(f"SendGrid Response Status Code: {response.status_code}")
            
            return response

        except Exception as e:
            print(f"Error sending email to {to_email}: {str(e)}")
            if hasattr(e, 'body'):
                print(f"SendGrid error details: {e.body}")
            return None
        
    def schedule_email(self, email, content, scheduled_time, company_name=None):
        """
        Schedule an email for sending
        """
        try:
            print(f"Scheduling email for {email} at {scheduled_time}")
            
            # Validate email
            if not email or '@' not in email:
                raise ValueError(f"Invalid email address: {email}")

            # Validate content
            if not content or not content.strip():
                raise ValueError("Email content cannot be empty")

            # Validate scheduled time
            if scheduled_time < datetime.now():
                raise ValueError("Scheduled time must be in the future")

            # Create scheduled email record
            scheduled_email = ScheduledEmail(
                email=email,
                content=content,
                scheduled_time=scheduled_time,
                company_name=company_name,
                status='pending'
            )

            self.session.add(scheduled_email)
            self.session.commit()
            
            print(f"Successfully scheduled email {scheduled_email.id} for {email}")
            return scheduled_email

        except Exception as e:
            print(f"Error scheduling email for {email}: {e}")
            self.session.rollback()
            raise
        
    def process_scheduled_emails(self):
        current_time = datetime.now()
        pending_emails = self.session.query(ScheduledEmail).filter(
            ScheduledEmail.status == 'pending',
            ScheduledEmail.scheduled_time <= current_time
        ).all()
        print(f"\n=== Processing Scheduled Emails ===")
        print(f"Found {len(pending_emails)} pending emails at {current_time}")
        
        for email in pending_emails:
            print(f"\nProcessing email ID: {email.id}")
            print(f"Recipient: {email.email}")
            print(f"Scheduled Time: {email.scheduled_time}")
            try:
                if not email.content or len(email.content.strip()) == 0:
                    print("Error: Empty content")
                    email.status = 'failed'
                    continue
                response = self.send_email_via_esp(email.email, email.content)
                
                if response and response.status_code == 202:
                    email.status = 'sent'
                    print(f"Successfully sent scheduled email to {email.email}")
                else:
                    email.status = 'failed'
                    print(f"Failed to send scheduled email to {email.email}")
            except Exception as e:
                print(f"Error: {str(e)}")
                email.status = 'failed'
            
        self.session.commit()
        print("\n=== Finished Processing Scheduled Emails ===")

    def run_scheduler(self):
        schedule.every(1).minutes.do(self.process_scheduled_emails)
        while True:
            schedule.run_pending()
            time.sleep(1)