# Production Deployment Guide

## Pre-Deployment Checklist

### 1. Environment Configuration
Create a `.env` file based on `.env.example` with production values:

```bash
# Django Settings
SECRET_KEY=<generate-a-strong-secret-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Email Configuration (SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com  # Or your SMTP provider
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

**Generating a Secret Key:**
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2. Email Provider Setup

#### Option A: Gmail (for small-scale)
1. Enable 2-factor authentication on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the app password as `EMAIL_HOST_PASSWORD`

#### Option B: SendGrid (recommended for production)
1. Sign up at https://sendgrid.com
2. Create an API key
3. Configure:
   - `EMAIL_HOST=smtp.sendgrid.net`
   - `EMAIL_HOST_USER=apikey`
   - `EMAIL_HOST_PASSWORD=<your-sendgrid-api-key>`

#### Option C: AWS SES (cost-effective, scalable)
1. Set up AWS SES in your region
2. Verify your domain
3. Get SMTP credentials
4. Configure accordingly

### 3. Static Files
Ensure static files are collected:
```bash
python manage.py collectstatic --noinput
```

### 4. Database

**Development (SQLite):**
- Default configuration, no changes needed

**Production (PostgreSQL recommended):**
1. Install PostgreSQL on your server
2. Create database and user:
   ```sql
   CREATE DATABASE retirement_planner;
   CREATE USER retirement_user WITH PASSWORD 'strong_password';
   GRANT ALL PRIVILEGES ON DATABASE retirement_planner TO retirement_user;
   ```
3. Install psycopg2: `pip install psycopg2-binary`
4. Add to `.env`:
   ```
   DATABASE_URL=postgresql://retirement_user:strong_password@localhost/retirement_planner
   ```
5. Update `settings.py` to parse DATABASE_URL (using dj-database-url)

### 5. Security Checklist

- [ ] `DEBUG=False` in production `.env`
- [ ] Strong `SECRET_KEY` generated and set
- [ ] `ALLOWED_HOSTS` configured with your domain(s)
- [ ] HTTPS/SSL certificate installed (Let's Encrypt recommended)
- [ ] Security headers enabled (already in settings.py when DEBUG=False)

### 6. Dependencies
Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### 7. Database Migrations
Run migrations on production database:
```bash
python manage.py migrate
```

### 8. Create Superuser
Create admin account:
```bash
python manage.py createsuperuser
```

## Deployment Platforms

### Option A: Railway (Easiest)
1. Sign up at https://railway.app
2. Connect your GitHub repository
3. Add environment variables from your `.env`
4. Railway auto-detects Django and deploys
5. Configure custom domain (optional)

### Option B: Render (Free tier available)
1. Sign up at https://render.com
2. Create new Web Service
3. Connect repository
4. Configure:
   - Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - Start Command: `gunicorn retirement_planner.wsgi:application`
5. Add environment variables
6. Add PostgreSQL database (recommended)

### Option C: DigitalOcean App Platform
1. Sign up at https://digitalocean.com
2. Create new app from GitHub
3. Configure build and run commands
4. Add environment variables
5. Provision managed PostgreSQL database (recommended)

### Option D: Traditional VPS (Advanced)
Use services like DigitalOcean Droplets, Linode, or AWS EC2:
1. Set up Ubuntu server
2. Install Nginx, PostgreSQL, Python
3. Configure Gunicorn as WSGI server
4. Set up Nginx as reverse proxy
5. Use systemd to manage processes
6. Configure SSL with Let's Encrypt

## Post-Deployment

### Testing
- [ ] Test user registration and login
- [ ] Test email functionality (verify emails are sent)
- [ ] Test scenario creation and calculations
- [ ] Test email scenario reports feature
- [ ] Check Django admin panel access

### Monitoring
- Set up error tracking (Sentry recommended)
- Monitor email sending (check bounce rates)
- Set up uptime monitoring
- Review Django logs regularly

### Backups
- Set up automated database backups
- Back up user-uploaded media files (if any)
- Keep backup of `.env` file (securely)

## Common Issues

### Static Files Not Loading
- Ensure `collectstatic` was run
- Check WhiteNoise is in MIDDLEWARE (it is)
- Verify STATIC_ROOT is correct

### Emails Not Sending
- Check EMAIL_* settings in `.env`
- Verify SMTP credentials
- Check firewall allows outbound port 587/465
- Review email provider's sending limits

### Database Connection Errors
- Verify DATABASE_URL is correct
- Check database server is running
- Ensure database user has proper permissions

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| SECRET_KEY | Yes | - | Django secret key |
| DEBUG | Yes | False | Debug mode (False for production) |
| ALLOWED_HOSTS | Yes | - | Comma-separated list of allowed hostnames |
| EMAIL_BACKEND | No | console | Email backend class |
| EMAIL_HOST | No | localhost | SMTP server hostname |
| EMAIL_PORT | No | 25 | SMTP server port |
| EMAIL_USE_TLS | No | False | Use TLS for email |
| EMAIL_HOST_USER | No | - | SMTP username |
| EMAIL_HOST_PASSWORD | No | - | SMTP password |
| DEFAULT_FROM_EMAIL | No | noreply@retirementplanner.com | Default from email |
| DATABASE_URL | No | SQLite | PostgreSQL connection string |

## Updating Production

```bash
# Pull latest code
git pull origin main

# Install/update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart application server
# (method varies by platform)
```
