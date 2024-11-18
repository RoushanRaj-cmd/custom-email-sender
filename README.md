# AI-Powered Email Campaign System

A sophisticated email campaign management system that leverages AI for content generation, featuring real-time analytics, Google authentication, and automated scheduling.

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [API Configuration](#api-configuration)
- [Email Configuration](#email-configuration)
- [Usage Guide](#usage-guide)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)
- [Security](#security)
- [Support](#support)

## Features

### Core Functionality
- 🤖 AI-powered email content generation using Groq API
- 📊 Real-time campaign analytics and tracking
- 📅 Automated email scheduling with throttling
- 🔐 Secure Google OAuth authentication
- 📝 Dynamic email templates with variable support
- 📈 Interactive analytics dashboard
- 🔔 Real-time notifications
- 📧 Preview functionality
- 📁 CSV integration for recipient management

### Technical Features
- Flask-based backend
- SQLAlchemy ORM
- SendGrid ESP integration
- Server-Sent Events (SSE)
- Responsive UI design
- Chart.js analytics
- Error handling & logging
- Rate limiting & throttling

## Prerequisites
- Python 3.8+
- pip
- Git
- SendGrid account
- Groq API access
- Google Cloud account

## Installation

1. **Clone Repository**
bash
git clone https://github.com/yourusername/email-campaign-system.git
cd email-campaign-system

2. **Set Up Virtual Environment**
bash
python -m venv venv
Windows
venv\Scripts\activate
Unix/MacOS
source venv/bin/activate

3. **Install Dependencies**
bash
pip install -r requirements.txt

4. **Environment Setup**
bash
cp .env.example .env

Edit `.env` with your credentials:
env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secure_secret_key
SENDGRID_API_KEY=your_sendgrid_api_key
GROQ_API_KEY=your_groq_api_key
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret

5. **Database Initialization**

## API Configuration

### SendGrid Setup
1. Create account at [SendGrid](https://sendgrid.com)
2. Verify sender identity:
   - Domain authentication
   - Single sender verification
3. Generate API key with required permissions:
   - Mail Send
   - Template Engine
   - Stats

### Groq API Setup
1. Sign up at [Groq](https://groq.com)
2. Generate API key
3. Configure permissions for LLM access

### Google OAuth Setup
1. Create project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable required APIs:
   - Google OAuth2
   - Gmail API
3. Configure OAuth consent screen
4. Create credentials
5. Add authorized redirect URIs:
   ```
   http://localhost:5000/google/auth
   https://yourdomain.com/google/auth
   ```

## Email Configuration

### Throttling Settings
```env
MAX_EMAILS_PER_DAY=2000
MAX_EMAILS_PER_HOUR=500
MAX_BATCH_SIZE=100
THROTTLE_RATE=10
```

### Scheduler Configuration
```python
class EmailScheduler:
    def __init__(self):
        self.max_daily = int(os.getenv('MAX_EMAILS_PER_DAY'))
        self.max_hourly = int(os.getenv('MAX_EMAILS_PER_HOUR'))
        self.batch_size = int(os.getenv('MAX_BATCH_SIZE'))
        self.throttle_rate = int(os.getenv('THROTTLE_RATE'))
```

## Usage Guide

### Creating a Campaign

1. **Login**
   - Use Google authentication
   - Authorize application access

2. **Upload Recipients**
   - Prepare CSV with headers:
     - Email (required)
     - Name (required)
     - Company
     - Role
     - Custom fields
   - Upload via drag-drop or file selector

3. **Create Template**
   - Use variable syntax: `{VariableName}`
   - Example:
     ```
     Hello {Name},
     
     I noticed you work at {Company} as {Role}...
     ```
   - Preview generated content
   - Save template for reuse

4. **Schedule Campaign**
   - Select date/time
   - Choose sending speed
   - Configure throttling
   - Start campaign

### Monitoring

1. **Dashboard Analytics**
   - Real-time sending status
   - Success/failure rates
   - Open/click rates
   - Queue status

2. **Notifications**
   - Campaign start/completion
   - Error alerts
   - Rate limit warnings

## Troubleshooting

### Common Issues

1. **Rate Limiting**
   ```
   Error: Too many requests
   Solution: Adjust throttling settings
   ```

2. **Authentication**
   ```
   Error: Invalid credentials
   Solution: Verify API keys and OAuth setup
   ```

3. **Email Failures**
   ```
   Error: Email bounce
   Solution: Check recipient email format
   ```

## Maintenance

### Regular Tasks

1. **Daily**
   - Monitor error logs
   - Check sending limits
   - Review analytics

2. **Weekly**
   - Clean failed emails
   - Update templates
   - Backup database

3. **Monthly**
   - Review API usage
   - Update dependencies
   - Optimize performance

## Security

### Best Practices
1. **API Security**
   - Regular key rotation
   - Environment variable usage
   - Access logging

2. **Authentication**
   - HTTPS enforcement
   - Rate limiting
   - Session management

3. **Data Protection**
   - Encryption at rest
   - Regular backups
   - Access control

## Support

### Contact
- Email: roushanraj6641@gmail.com

