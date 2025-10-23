# 🚀 Deployment Checklist - Sales Engagement Platform

## Pre-Deployment Checklist

### ✅ Code Quality
- [ ] All tests passing (`pytest` and `npm test`)
- [ ] Code formatted (`black`, `prettier`)
- [ ] No security vulnerabilities
- [ ] Environment variables documented
- [ ] API documentation up to date

### ✅ Configuration
- [ ] Production environment variables set
- [ ] Database connection string configured
- [ ] Redis connection string configured
- [ ] JWT secrets generated (32+ characters)
- [ ] CORS origins configured for frontend domain
- [ ] Twilio credentials configured (optional)

### ✅ Infrastructure
- [ ] PostgreSQL database provisioned
- [ ] Redis instance provisioned
- [ ] Domain name configured (optional)
- [ ] SSL certificate ready (automatic with Koyeb)

## Koyeb Deployment Steps

### 1. Prepare Repository
```bash
# Ensure code is committed and pushed
git add .
git commit -m "feat: prepare for Koyeb deployment"
git push origin main
```

### 2. Create Koyeb Account
- [ ] Sign up at [koyeb.com](https://www.koyeb.com)
- [ ] Verify email address
- [ ] Add payment method (if needed)

### 3. Set Up Database Services

#### PostgreSQL
- [ ] Create PostgreSQL service in Koyeb
- [ ] Note connection string
- [ ] Run initial migrations

#### Redis
- [ ] Create Redis service in Koyeb
- [ ] Note connection string
- [ ] Test connectivity

### 4. Configure Environment Variables

Set these in Koyeb dashboard:

#### Required Variables
```bash
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
REDIS_URL=redis://user:password@host:port/0
SECRET_KEY=your-super-secret-key-minimum-32-characters
JWT_SECRET_KEY=your-jwt-secret-key-minimum-32-characters
ENVIRONMENT=production
DEBUG=false
```

#### Optional Variables
```bash
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
CORS_ORIGINS=https://your-frontend-domain.com
```

### 5. Deploy Backend Service

#### Option A: Koyeb Dashboard
- [ ] Connect GitHub repository
- [ ] Select `Dockerfile.koyeb`
- [ ] Configure port 8000
- [ ] Set health check path: `/health`
- [ ] Deploy service

#### Option B: GitHub Actions
- [ ] Add `KOYEB_API_TOKEN` to GitHub Secrets
- [ ] Push to main branch
- [ ] Monitor deployment in Actions tab

### 6. Deploy Frontend

#### Option A: Netlify (Recommended)
```bash
cd frontend
npm run build
netlify deploy --prod --dir=build
```

#### Option B: Vercel
```bash
cd frontend
vercel --prod
```

#### Option C: Koyeb Static Site
- [ ] Create static site service
- [ ] Point to `frontend/build` directory
- [ ] Configure build command: `npm run build`

### 7. Configure Domain (Optional)
- [ ] Add custom domain in Koyeb
- [ ] Update DNS records
- [ ] Verify SSL certificate

## Post-Deployment Checklist

### ✅ Functionality Tests
- [ ] Health check endpoint: `GET /health`
- [ ] API documentation: `GET /docs`
- [ ] User registration: `POST /api/v1/auth/register`
- [ ] User login: `POST /api/v1/auth/login`
- [ ] Contact creation: `POST /api/v1/contacts`
- [ ] Contact listing: `GET /api/v1/contacts`
- [ ] Activity creation: `POST /api/v1/activities`

### ✅ Frontend Tests
- [ ] Application loads correctly
- [ ] Login/registration works
- [ ] Contact management functional
- [ ] Activities timeline working
- [ ] Real-time notifications active
- [ ] Responsive design on mobile

### ✅ Integration Tests
- [ ] Frontend connects to backend API
- [ ] WebSocket connections established
- [ ] VoIP calling works (if configured)
- [ ] Database operations successful
- [ ] Redis caching functional

### ✅ Performance Tests
- [ ] API response times < 200ms
- [ ] Frontend load time < 3s
- [ ] Database queries optimized
- [ ] Memory usage stable
- [ ] No memory leaks

### ✅ Security Tests
- [ ] HTTPS enabled
- [ ] JWT authentication working
- [ ] CORS configured correctly
- [ ] No sensitive data in logs
- [ ] Environment variables secure

### ✅ Monitoring Setup
- [ ] Health checks configured
- [ ] Error tracking active
- [ ] Performance monitoring enabled
- [ ] Log aggregation working
- [ ] Alerts configured

## Rollback Plan

### If Deployment Fails
1. **Check logs**: `koyeb logs service-name`
2. **Verify environment variables**
3. **Test database connectivity**
4. **Check Docker build logs**
5. **Rollback to previous version if needed**

### Emergency Rollback
```bash
# Rollback to previous deployment
koyeb service update service-name --git-sha previous-commit-hash

# Or redeploy from working branch
koyeb service update service-name --git-branch stable
```

## Success Criteria

### ✅ Deployment Successful When:
- [ ] All services running without errors
- [ ] Health checks passing
- [ ] Frontend accessible via HTTPS
- [ ] Backend API responding correctly
- [ ] Database migrations completed
- [ ] User authentication working
- [ ] Core features functional
- [ ] Performance metrics within targets
- [ ] No critical security issues
- [ ] Monitoring and alerts active

## Maintenance Tasks

### Daily
- [ ] Check service health
- [ ] Monitor error rates
- [ ] Review performance metrics

### Weekly
- [ ] Update dependencies
- [ ] Review security alerts
- [ ] Backup database
- [ ] Check disk usage

### Monthly
- [ ] Security audit
- [ ] Performance optimization
- [ ] Cost optimization review
- [ ] Update documentation

## Support Contacts

### Technical Issues
- **Koyeb Support**: [support@koyeb.com](mailto:support@koyeb.com)
- **Documentation**: [docs.koyeb.com](https://docs.koyeb.com)
- **Community**: [community.koyeb.com](https://community.koyeb.com)

### Application Issues
- **GitHub Issues**: Create issue in repository
- **Email**: [support@yourcompany.com](mailto:support@yourcompany.com)
- **Documentation**: Check project README and guides

---

## 🎉 Congratulations!

If all items are checked, your Sales Engagement Platform is successfully deployed and ready for production use!

**Next Steps:**
1. Share the application URL with your team
2. Set up user accounts and permissions
3. Configure VoIP settings (if needed)
4. Import existing contact data
5. Train users on the new system

**Application URLs:**
- **Frontend**: https://your-app.koyeb.app
- **Backend API**: https://your-api.koyeb.app
- **API Docs**: https://your-api.koyeb.app/docs
- **Health Check**: https://your-api.koyeb.app/health