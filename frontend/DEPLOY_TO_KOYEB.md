# Deploy React Frontend to Koyeb

This guide shows how to deploy the React frontend as a separate Koyeb service.

## Prerequisites

1. Koyeb account
2. GitHub repository with the frontend code
3. Backend API already deployed (https://equal-correna-joelezz-d150d717.koyeb.app)

## Deployment Steps

### Option 1: Deploy via Koyeb Dashboard (Recommended)

1. **Login to Koyeb Dashboard**
   - Go to https://app.koyeb.com
   - Login to your account

2. **Create New Service**
   - Click "Create Service"
   - Choose "GitHub" as source
   - Select your repository
   - **DO NOT** set a source directory (leave empty)

3. **Configure Build Settings**
   - Build type: `Docker`
   - Dockerfile path: `frontend/Dockerfile`
   - Build context: `.` (root directory)

4. **Configure Service Settings**
   - Service name: `sales-engagement-frontend`
   - Region: Choose your preferred region
   - Instance type: `nano` (sufficient for frontend)

5. **Environment Variables** (Optional)
   ```
   NODE_ENV=production
   ```

6. **Deploy**
   - Click "Deploy"
   - Wait for deployment to complete (5-10 minutes)

### Option 2: Deploy via Koyeb CLI

1. **Install Koyeb CLI**
   ```bash
   # Install via npm
   npm install -g @koyeb/koyeb-cli
   
   # Or download binary from https://github.com/koyeb/koyeb-cli/releases
   ```

2. **Login**
   ```bash
   koyeb auth login
   ```

3. **Deploy from frontend directory**
   ```bash
   cd frontend
   koyeb service create sales-engagement-frontend \
     --git github.com/joelezz/sales-engagement-platform \
     --git-branch main \
     --git-build-command "npm run build" \
     --git-run-command "npm start" \
     --ports 80:http \
     --regions fra \
     --instance-type nano
   ```

## Configuration Details

### Dockerfile
The frontend uses a multi-stage Docker build:
- **Stage 1**: Build the React app with Node.js
- **Stage 2**: Serve with Nginx

### Nginx Configuration
- Serves static files from `/usr/share/nginx/html`
- Proxies API calls to backend service
- Handles client-side routing for React Router
- Includes security headers and gzip compression

### Environment Variables
The frontend is configured to use relative URLs:
- `REACT_APP_API_URL=/api/v1`
- `REACT_APP_WS_URL=/ws`

Nginx proxies these to your backend service.

## Post-Deployment

1. **Get Frontend URL**
   - Your frontend will be available at: `https://your-frontend-app.koyeb.app`
   - Note the URL from the Koyeb dashboard

2. **Update CORS Settings**
   - Add your frontend URL to the backend CORS configuration
   - Update `app/core/config.py` in your backend:
   ```python
   CORS_ORIGINS = [
       "http://localhost:3000",
       "https://your-frontend-app.koyeb.app"  # Add this line
   ]
   ```

3. **Test the Application**
   - Visit your frontend URL
   - Try logging in and using the features
   - Check that API calls work correctly

## Troubleshooting

### Build Failures
- Check the build logs in Koyeb dashboard
- Ensure all dependencies are in `package.json`
- Verify Dockerfile syntax

### Runtime Issues
- Check service logs in Koyeb dashboard
- Verify nginx configuration
- Test API connectivity

### CORS Issues
- Ensure frontend URL is added to backend CORS settings
- Check browser developer tools for CORS errors
- Verify API proxy configuration in nginx.conf

## Scaling and Performance

### Instance Types
- **nano**: Good for development/testing
- **micro**: Suitable for small production loads
- **small**: For higher traffic applications

### Monitoring
- Use Koyeb dashboard to monitor:
  - CPU and memory usage
  - Request metrics
  - Error rates
  - Response times

## Cost Optimization

1. **Use nano instances** for frontend (they're usually sufficient)
2. **Enable auto-scaling** based on traffic
3. **Monitor usage** and adjust instance types as needed

## Security Considerations

1. **HTTPS**: Koyeb provides automatic HTTPS
2. **Security Headers**: Configured in nginx.conf
3. **Environment Variables**: Store sensitive data in Koyeb environment variables
4. **CORS**: Properly configure allowed origins

## Next Steps

After successful deployment:
1. Set up custom domain (optional)
2. Configure monitoring and alerts
3. Set up CI/CD pipeline for automatic deployments
4. Consider CDN for static assets (for global applications)
## A
lternative: Create Separate Frontend Repository

If you continue having issues with the monorepo approach, you can create a separate repository for the frontend:

### Steps:

1. **Create New Repository**
   ```bash
   # Create new repository on GitHub: sales-engagement-frontend
   ```

2. **Copy Frontend Files**
   ```bash
   # Create new directory
   mkdir ../sales-engagement-frontend
   cd ../sales-engagement-frontend
   
   # Initialize git
   git init
   
   # Copy frontend files (excluding node_modules)
   cp -r ../sales-engagement-platform/frontend/* .
   cp ../sales-engagement-platform/frontend/.* . 2>/dev/null || true
   
   # Remove monorepo-specific files
   rm -f koyeb.toml
   
   # Update Dockerfile for standalone deployment
   ```

3. **Update Dockerfile for Standalone**
   ```dockerfile
   # Multi-stage build for React frontend
   FROM node:18-alpine as build
   
   WORKDIR /app
   COPY package*.json ./
   RUN npm ci --only=production
   COPY . .
   RUN npm run build
   
   FROM nginx:alpine
   COPY --from=build /app/build /usr/share/nginx/html
   COPY nginx.conf /etc/nginx/conf.d/default.conf
   EXPOSE 80
   CMD ["nginx", "-g", "daemon off;"]
   ```

4. **Deploy to Koyeb**
   - Use the new repository
   - No need to specify subdirectories
   - Standard Docker deployment

This approach is simpler and avoids monorepo complexity.