from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from config import Config
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import requests
import pandas as pd
from time import sleep
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
import os
from google_sheets import get_google_sheet
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from groq import Groq
from email_scheduler import EmailScheduler, ScheduledEmail  # Add ScheduledEmail to import
import threading
from datetime import datetime
import json
from flask import Response
from queue import Queue
from time import time


# Initialize Groq Client
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
# App configuration
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY  # Needed for session management

# Initialize SendGrid client
sendgrid_client = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))

# Create a global event queue
event_queue = Queue()

# Create a dictionary to store client connections
clients = {}
# Initialize global variables for email analytics
email_analytics = {
    'total_sent': 0,
    'pending': 0,
    'failed': 0
}

# Initialize email scheduler with SendGrid client
email_scheduler = EmailScheduler(sendgrid_client=sendgrid_client)
scheduler_thread = threading.Thread(target=email_scheduler.run_scheduler)
scheduler_thread.daemon = True
scheduler_thread.start()

class ServerSentEvent:
    def __init__(self, data, event=None):
        self.data = data
        self.event = event

    def encode(self):
        message = f"data: {json.dumps(self.data)}\n"
        if self.event is not None:
            message = f"event: {self.event}\n{message}"
        return f"{message}\n"

def send_notification(message, notification_type='info'):
    """Send notification to all connected clients"""
    event_data = {
        'message': message,
        'type': notification_type,
        'timestamp': datetime.now().isoformat()
    }
    event_queue.put(event_data)


# Add this route to handle successful login messages
@app.route('/login_success')
def login_success():
    return jsonify({'status': 'Account logged in successfully'})

@app.route('/preview-email', methods=['POST'])
def preview_email():
    try:
        data = request.json
        template = data['template']
        sample_data = data['sample_data']
        
        # Generate preview using Groq
        llm_response = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional email writer. Create personalized, engaging emails."
                },
                {
                    "role": "user",
                    "content": template.format(**sample_data)
                }
            ],
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=500
        )
        
        preview_content = llm_response.choices[0].message.content
        
        return jsonify({
            'status': 'success',
            'preview': preview_content
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    
# Example route that triggers notifications
@app.route('/test-notification')
def test_notification():
    send_notification("This is a test notification", "info")
    return jsonify({'status': 'success'})

@app.route('/campaign-events')
def campaign_events():
    def generate():
        client_id = str(time.time())  # Generate unique client ID
        clients[client_id] = True
        try:
            while clients.get(client_id):
                # Send initial connection message
                yield ServerSentEvent({
                    'message': 'Connected to event stream',
                    'type': 'info'
                }).encode()

                while True:
                    # Check for new notifications
                    try:
                        event_data = event_queue.get(timeout=20)  # 20 second timeout
                        yield ServerSentEvent(event_data).encode()
                    except Queue.Empty:
                        # Send keepalive
                        yield ServerSentEvent({
                            'type': 'keepalive',
                            'timestamp': datetime.now().isoformat()
                        }).encode()

        except GeneratorExit:
            # Client disconnected
            if client_id in clients:
                del clients[client_id]

    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
    )

# Function to send SSE notifications
def send_notification(message, type='info'):
    event_queue.put({
        'message': message,
        'type': type
    })
# Route to send emails with SendGrid
@app.route('/send_email', methods=['POST'])

# Your existing send_email_via_esp function for immediate sending
def send_email_via_esp(to_email, content):
    try:
        message = Mail(
            from_email=os.getenv('roushanraj6641@gmail.com'),
            to_emails=to_email,
            subject='Your Customized Email',
            html_content=content
        )
        response = sendgrid_client.send(message)
        send_notification(f"Email sent successfully to {to_email}", 'success')
        return response
    except Exception as e:
        print(f"Error sending immediate email to {to_email}: {str(e)}")
        send_notification(f"Failed to send email to {to_email}", 'error')
        return None

    if response:
        return response
    else:
        return None  # Return None if there's an error

def send_email_via_gmail(to_email):
    if 'credentials' not in session:
        flash("User not authenticated")
        return

    credentials = Credentials(**session['credentials'])

    service = build('gmail', 'v1', credentials=credentials)

    message = {
        'raw': base64.urlsafe_b64encode(f'To: {to_email}\nSubject: Hello from Flask!\n\nThis is a test email!'.encode()).decode()
    }

    try:
        service.users().messages().send(userId='me', body=message).execute()
        print(f'Message sent to {to_email}')
    except Exception as e:
        print(f'An error occurred: {e}')

# Route to upload CSV and send emails from CSV data
@app.route('/upload', methods=['POST'])
def upload():
    try:
        print("Starting upload process...")
        
        # Get form data
        file = request.files.get('file')
        email_prompt = request.form.get('email_prompt')
        scheduled_time = request.form.get('scheduled_time')
        
        print(f"Email Prompt Template: {email_prompt}")  # Debug log

        if not all([file, email_prompt, scheduled_time]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400

        # Read CSV file
        df = pd.read_csv(file)
        scheduled_datetime = datetime.strptime(scheduled_time, '%Y-%m-%dT%H:%M')

        send_notification(
            f"Starting to schedule {len(df)} emails",
            'info'
        )
        success_count = 0
        error_count = 0

        # Process each row
        for _, row in df.iterrows():
            try:
                # Format the prompt with row data
                formatted_prompt = email_prompt
                for column in row.index:
                    placeholder = f"{{{column}}}"
                    if placeholder in email_prompt:
                        formatted_prompt = formatted_prompt.replace(placeholder, str(row[column]))
                
                print(f"Formatted prompt for {row['Email']}: {formatted_prompt}")  # Debug log

                # Generate content using Groq
                llm_response = groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional email writer. Create personalized, engaging emails."
                        },
                        {
                            "role": "user",
                            "content": formatted_prompt
                        }
                    ],
                    model="llama3-8b-8192",
                    temperature=0.7,
                    max_tokens=500
                )

                # Extract the generated content
                email_content = llm_response.choices[0].message.content
                print(f"Generated content length: {len(email_content)}")  # Debug log

                if not email_content or len(email_content.strip()) == 0:
                    raise ValueError("Empty content generated by Groq")

                # Schedule the email with the generated content
                email_scheduler.schedule_email(
                    email=row['Email'],
                    content=email_content,
                    scheduled_time=scheduled_datetime,
                    company_name=row.get('Company', None)
                )
                success_count += 1
                print(f"Successfully scheduled email for {row['Email']}")
                send_notification(
                    f"Successfully scheduled email for {row['Email']}",
                    'success'
                )

            except Exception as e:
                error_count += 1
                print(f"Error processing row for {row['Email']}: {str(e)}")
                send_notification(
                    f"Failed to schedule email for {row['Email']}: {str(e)}",
                    'error'
                )
                continue
        # Final status notification
        send_notification(
            f"Campaign scheduled: {success_count} successful, {error_count} failed",
            'info'
        )

        return jsonify({
            'status': 'success',
            'message': f'Successfully scheduled {success_count} emails. {error_count} failed.',
            'total_scheduled': success_count,
            'total_failed': error_count
        })

    except Exception as e:
        print(f"Error in upload route: {str(e)}")
        send_notification(f"Error in campaign scheduling: {str(e)}", 'error')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/analytics', methods=['GET'])
def get_email_analytics():
    return jsonify(email_analytics)

# Google OAuth2 flow to connect Gmail account
@app.route('/authorize_gmail')
def authorize_gmail():
    flow = Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=['https://www.googleapis.com/auth/gmail.send'],
        redirect_uri=url_for('oauth2_callback', _external=True)
    )
    authorization_url, _ = flow.authorization_url(prompt='consent')
    return redirect(authorization_url)

@app.route('/oauth2_callback')
def oauth2_callback():
    import os
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    flow = Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=['https://www.googleapis.com/auth/gmail.send'],
        redirect_uri=url_for('oauth2_callback', _external=True)
    )
    flow.fetch_token(authorization_response=request.url)

    creds = flow.credentials
    session['credentials'] = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }
    flash("Account logged in successfully")
    return redirect(url_for('dashboard'))  # Redirect back to dashboard

@app.route('/logout')
def logout():
    session.pop('credentials', None)  # Clear the session
    flash("You have been logged out.")  # Optional: Flash message for logout
    return redirect(url_for('dashboard'))

# Route to display the dashboard
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/schedule-email', methods=['POST'])
def schedule_email():
    try:
        data = request.json
        scheduled_time = datetime.fromisoformat(data['scheduled_time'])
        emails = data['emails']
        content = data['content']
        company_name = data.get('company_name')
        
        for email in emails:
            email_scheduler.schedule_email(
                email=email,
                content=content,
                scheduled_time=scheduled_time,
                company_name=company_name
            )
            
        return jsonify({'message': 'Emails scheduled successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/scheduled-emails', methods=['GET'])
def get_scheduled_emails():
    try:
        scheduled = email_scheduler.session.query(ScheduledEmail).all()
        return jsonify([{
            'id': email.id,
            'email': email.email,
            'scheduled_time': email.scheduled_time.isoformat(),
            'status': email.status,
            'company_name': email.company_name
        } for email in scheduled]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Add this route to check scheduled email status
@app.route('/scheduled-emails-status')
def scheduled_emails_status():
    emails = ScheduledEmail.query.all()
    return jsonify([{
        'id': email.id,
        'email': email.email,
        'scheduled_time': email.scheduled_time.isoformat(),
        'status': email.status,
        'company_name': email.company_name
    } for email in emails])

@app.route('/test-sendgrid-config')
def test_sendgrid_config():
    try:
        # Print configuration
        config = {
            'from_email': os.getenv('FROM_EMAIL'),
            'api_key_exists': bool(os.getenv('SENDGRID_API_KEY')),
            'api_key_preview': os.getenv('SENDGRID_API_KEY')[:5] + '...' if os.getenv('SENDGRID_API_KEY') else None
        }
        
        # Test message
        message = {
            "personalizations": [
                {
                    "to": [{"email": os.getenv('FROM_EMAIL')}]
                }
            ],
            "from": {"email": os.getenv('FROM_EMAIL')},
            "subject": "SendGrid Test",
            "content": [
                {
                    "type": "text/html",
                    "value": "<p>This is a test email.</p>"
                }
            ]
        }
        
        # Try to send
        response = sendgrid_client.client.mail.send.post(request_body=message)
        
        return jsonify({
            'status': 'success',
            'config': config,
            'response_code': response.status_code,
            'message': 'Test email sent successfully'
        })
        
    except Exception as e:
        error_details = {
            'error_type': type(e).__name__,
            'error_message': str(e)
        }
        
        if hasattr(e, 'body'):
            try:
                error_details['sendgrid_error'] = json.loads(e.body.decode('utf-8'))
            except:
                error_details['raw_error_body'] = str(e.body)
                
        return jsonify({
            'status': 'error',
            'config': config,
            'error_details': error_details
        }), 500

@app.route('/scheduler-status')
def scheduler_status():
    try:
        current_time = datetime.now()
        pending_count = ScheduledEmail.query.filter_by(status='pending').count()
        sent_count = ScheduledEmail.query.filter_by(status='sent').count()
        failed_count = ScheduledEmail.query.filter_by(status='failed').count()
        
        return jsonify({
            'status': 'success',
            'scheduler_running': True,  # Add logic to check if scheduler is running
            'current_time': current_time.isoformat(),
            'pending_emails': pending_count,
            'sent_emails': sent_count,
            'failed_emails': failed_count
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True)