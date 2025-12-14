# Railway Deployment Guide

## Quick Start

### 1. Prepare Your Repository
Ensure all changes are committed and pushed to GitHub:
```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### 2. Sign Up for Railway
1. Go to https://railway.app
2. Sign up with GitHub (recommended for easy integration)

### 3. Create New Project
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your repository: `RetirementScenarioApp`
4. Railway will auto-detect it's a Django project

### 4. Add PostgreSQL Database (Recommended)
1. In your Railway project, click "New"
2. Select "Database" → "Add PostgreSQL"
3. Railway will automatically create a `DATABASE_URL` environment variable
4. Your app will use this instead of SQLite

To use PostgreSQL, add to requirements.txt:
```
psycopg2-binary==2.9.9
dj-database-url==2.2.0
```

Then update settings.py to parse DATABASE_URL:
```python
import dj_database_url

# Replace existing DATABASES with:
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600,
        conn_health_checks=True,
    )
}
```

### 5. Configure Environment Variables
In Railway dashboard, go to your service → Variables:

**Required:**
- `SECRET_KEY`: Generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `DEBUG`: `False`
- `ALLOWED_HOSTS`: Your Railway domain (e.g., `your-app.up.railway.app`)

**Email (Optional but recommended):**
- `EMAIL_BACKEND`: `django.core.mail.backends.smtp.EmailBackend`
- `EMAIL_HOST`: `smtp.gmail.com` (or your provider)
- `EMAIL_PORT`: `587`
- `EMAIL_USE_TLS`: `True`
- `EMAIL_HOST_USER`: `your-email@gmail.com`
- `EMAIL_HOST_PASSWORD`: `your-app-password`
- `DEFAULT_FROM_EMAIL`: `noreply@yourdomain.com`

**Note:** Railway automatically provides `DATABASE_URL` if you added PostgreSQL.

### 6. Deploy
1. Railway automatically deploys when you push to GitHub
2. Watch the build logs in Railway dashboard
3. First deployment runs migrations and collects static files (via Procfile)

### 7. Post-Deployment Setup

**Create Superuser:**
1. In Railway dashboard, go to your service
2. Click on "Settings" → "Service"
3. Under "Deploy Logs", you can access the shell
4. Run: `python manage.py createsuperuser`

Or use Railway CLI:
```bash
railway run python manage.py createsuperuser
```

**Set Custom Domain (Optional):**
1. In Railway dashboard → Settings
2. Click "Generate Domain" or add custom domain
3. Update `ALLOWED_HOSTS` environment variable with your domain

### 8. Testing
Visit your Railway URL (e.g., `https://your-app.up.railway.app`)
- [ ] Test homepage loads
- [ ] Test user registration
- [ ] Test login
- [ ] Test scenario calculator
- [ ] Test email functionality (if configured)
- [ ] Access admin panel at `/admin`

## Railway CLI (Optional)

Install Railway CLI for easier management:
```bash
# Install
npm i -g @railway/cli

# Login
railway login

# Link to project
railway link

# View logs
railway logs

# Run commands in production
railway run python manage.py migrate
railway run python manage.py createsuperuser

# Open project in browser
railway open
```

## Troubleshooting

### Build Fails
- Check build logs in Railway dashboard
- Ensure `requirements.txt` is up to date
- Verify Python version compatibility

### Static Files Not Loading
- Check that `collectstatic` ran in release step (Procfile)
- Verify WhiteNoise is in MIDDLEWARE
- Check browser console for errors

### Database Connection Errors
- Ensure PostgreSQL database is added in Railway
- Check `DATABASE_URL` environment variable exists
- Verify `psycopg2-binary` and `dj-database-url` are in requirements.txt

### Application Won't Start
- Check deploy logs in Railway dashboard
- Verify `ALLOWED_HOSTS` includes Railway domain
- Ensure `SECRET_KEY` is set
- Check Procfile syntax

### Emails Not Sending
- Verify all EMAIL_* environment variables are set
- Check email provider credentials
- Review Railway logs for email errors
- Test with a simple email send via Django shell

## Updating Your App

Simply push to GitHub:
```bash
git add .
git commit -m "Update feature"
git push origin main
```

Railway automatically:
1. Detects the push
2. Builds the new version
3. Runs migrations (via Procfile release command)
4. Collects static files
5. Deploys with zero downtime

## Cost Estimate

**Free Tier Includes:**
- $5 USD credit per month
- Enough for small apps with light traffic
- PostgreSQL database included

**Typical Usage:**
- Small Django app: ~$3-5/month
- With PostgreSQL: Included in above
- Can upgrade for more resources as needed

## Monitoring

**View Logs:**
- Railway Dashboard → Your Service → Deployments → View Logs

**Metrics:**
- Railway Dashboard shows CPU, Memory, Network usage
- Set up alerts for downtime or errors

**Database:**
- Railway provides PostgreSQL metrics
- Can connect with external tools like pgAdmin

## Backups

**Database Backups:**
Railway doesn't auto-backup PostgreSQL on free tier.
Options:
1. Upgrade to paid tier for automated backups
2. Set up manual backup script:
   ```bash
   railway run pg_dump $DATABASE_URL > backup.sql
   ```

## Next Steps

- [ ] Monitor application performance
- [ ] Set up error tracking (e.g., Sentry)
- [ ] Configure custom domain
- [ ] Set up automated backups
- [ ] Review and optimize database queries
- [ ] Add monitoring/alerting

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- GitHub Issues: For app-specific issues
