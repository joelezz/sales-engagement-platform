# Koyeb Deployment Guide - Sales Engagement Platform

## 🚀 Deploy to Koyeb

This guide will help you deploy the Sales Engagement Platform to Koyeb, a modern serverless platform.

## Prerequisites

1. **Koyeb Account**: Sign up at [koyeb.com](https://www.koyeb.com)
2. **GitHub Repository**: Your code should be pushed to GitHub
3. **Database**: PostgreSQL database (Koyeb provides managed PostgreSQL)
4. **Redis**: Redis instance (Koyeb provides managed Redis)

## Step 1: Prepare External Services

### PostgreSQL Database
```bash
# Koyeb provides managed PostgreSQL
# Or use external providers like:
# - Neon (neon.tech)
# - Supabase (supabase.com)
# - Railway (railway.app)
```

### Redis Cache
```bash
# Koyeb provides managed Redis
# Or use external providers like:
# - Upstash (upstash.com)
# - Redis Cloud (redis.com)
```

## Step 2: Environment Variables

Set these environment variables in Koyeb dashboard:

### Required Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@host:port/database
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=sales_engagement_platform

# Redis
REDIS_URL=redis://user:password@host:port/0

# Security
SECRET_KEY=your-super-secret-key-here-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key-here-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Twilio (VoIP)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
TWILIO_WEBHOOK_URL=https://your-app.koyeb.app/api/v1/webhooks/twilio

# Application
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=https://your-frontend-domain.com,https://your-app.koyeb.app
```

### Optional Variables
```bash
# Monitoring
PROMETHEUS_ENABLED=true
LOG_LEVEL=INFO

# Email (if using email features)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## Step 3: Deploy Backend to Koyeb

### Option A: Deploy from GitHub (Recommended)

1. **Connect GitHub Repository**
   - Go to Koyeb dashboard
   - Click "Create App"
   - Select "GitHub" as source
   - Connect your repository

2. **Configure Build Settings**
   ```yaml
   Build Type: Docker
   Dockerfile: Dockerfile.koyeb
   Build Context: /
   ```

3. **Configure Service Settings**
   ```yaml
   Service Name: sales-engagement-backend
   Port: 8000
   Health Check: /health
   Instance Type: Small (512MB RAM, 0.5 CPU)
   Scaling: Min 1, Max 3
   ```

4. **Set Environment Variables**
   - Add all the environment variables listed above
   - Make sure to use production values

### Option B: Deploy with Koyeb CLI

```bash
# Install Koyeb CLI
curl -fsSL https://cli.koyeb.com/install.sh | sh

# Login to Koyeb
koyeb auth login

# Deploy the application
koyeb app create sales-engagement-platform \
  --git github.com/yourusername/sales-engagement-platform \
  --git-branch main \
  --docker-dockerfile Dockerfile.koyeb \
  --ports 8000:http \
  --routes /:8000 \
  --env DATABASE_URL=$DATABASE_URL \
  --env REDIS_URL=$REDIS_URL \
  --env SECRET_KEY=$SECRET_KEY \
  --env JWT_SECRET_KEY=$JWT_SECRET_KEY \
  --env TWILIO_ACCOUNT_SID=$TWILIO_ACCOUNT_SID \
  --env TWILIO_AUTH_TOKEN=$TWILIO_AUTH_TOKEN \
  --env TWILIO_PHONE_NUMBER=$TWILIO_PHONE_NUMBER \
  --env ENVIRONMENT=production
```

## Step 4: Deploy Frontend

### Option A: Deploy to Koyeb (Static Site)

1. **Create Frontend Service**
   ```bash
   # Build the frontend
   cd frontend
   npm run build
   
   # Deploy to Koyeb static hosting
   koyeb service create frontend \
     --app sales-engagement-platform \
     --type static \
     --static-path ./build
   ```

### Option B: Deploy to Netlify/Vercel (Recommended)

1. **Netlify Deployment**
   ```bash
   # Install Netlify CLI
   npm install -g netlify-cli
   
   # Build and deploy
   cd frontend
   npm run build
   netlify deploy --prod --dir=build
   ```

2. **Vercel Deployment**
   ```bash
   # Install Vercel CLI
   npm install -g vercel
   
   # Deploy
   cd frontend
   vercel --prod
   ```

## Step 5: Database Migration

After deployment, run database migrations:

```bash
# Connect to your deployed app
koyeb exec sales-engagement-backend -- alembic upgrade head

# Or run via API call
curl -X POST https://your-app.koyeb.app/api/v1/admin/migrate \
  -H "Authorization: Bearer your-admin-token"
```

## Step 6: Configure Domain (Optional)

1. **Custom Domain**
   - Go to Koyeb dashboard
   - Navigate to your app settings
   - Add custom domain
   - Update DNS records

2. **SSL Certificate**
   - Koyeb automatically provides SSL certificates
   - No additional configuration needed

## Step 7: Monitoring and Logs

### View Logs
```bash
# View application logs
koyeb logs sales-engagement-backend

# Follow logs in real-time
koyeb logs sales-engagement-backend --follow
```

### Monitoring
- Koyeb provides built-in monitoring
- Access metrics in the dashboard
- Set up alerts for critical issues

## Step 8: Post-Deployment Checklist

- [ ] ✅ Backend API responding at `/health`
- [ ] ✅ Frontend loading correctly
- [ ] ✅ Database connection working
- [ ] ✅ Redis connection working
- [ ] ✅ Authentication flow working
- [ ] ✅ VoIP integration configured
- [ ] ✅ WebSocket connections working
- [ ] ✅ CORS configured for frontend domain
- [ ] ✅ Environment variables set correctly
- [ ] ✅ SSL certificate active
- [ ] ✅ Custom domain configured (if applicable)

## Troubleshooting

### Common Issues

1. **"No command to run your application" Error**
   ```bash
   # This is fixed by the Procfile in the repository
   # If you still see this error:
   # 1. Ensure Procfile exists in your repository
   # 2. Check that the run command is set in Koyeb dashboard
   # 3. Use: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
   ```

2. **Database Connection Failed**
   ```bash
   # Check DATABASE_URL format
   # Should be: postgresql://user:password@host:port/database
   ```

3. **Redis Connection Failed**
   ```bash
   # Check REDIS_URL format
   # Should be: redis://user:password@host:port/0
   ```

4. **CORS Errors**
   ```bash
   # Update CORS_ORIGINS environment variable
   # Include your frontend domain
   ```

5. **Health Check Failing**
   ```bash
   # Check if /health endpoint is accessible
   curl https://your-app.koyeb.app/health
   ```

6. **Port Issues**
   ```bash
   # Koyeb automatically sets the PORT environment variable
   # The application should use $PORT, not hardcoded 8000
   ```

### Support

- **Koyeb Documentation**: [docs.koyeb.com](https://docs.koyeb.com)
- **Koyeb Community**: [community.koyeb.com](https://community.koyeb.com)
- **GitHub Issues**: Create an issue in your repository

## Cost Estimation

### Koyeb Pricing (Approximate)
- **Small Instance**: $7/month (512MB RAM, 0.5 CPU)
- **Medium Instance**: $15/month (1GB RAM, 1 CPU)
- **PostgreSQL**: $10-20/month (depending on size)
- **Redis**: $5-10/month (depending on size)

**Total Estimated Cost**: $25-50/month for production deployment

## Performance Optimization

1. **Enable Caching**
   - Redis caching is already implemented
   - Configure cache TTL values

2. **Database Optimization**
   - Database indexes are already created
   - Monitor query performance

3. **CDN Integration**
   - Use Koyeb's built-in CDN
   - Optimize static asset delivery

4. **Monitoring**
   - Set up alerts for high CPU/memory usage
   - Monitor response times

🎉 **Your Sales Engagement Platform is now live on Koyeb!**