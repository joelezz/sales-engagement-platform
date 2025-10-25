# Sales Engagement Platform - Frontend

React frontend for the Sales Engagement Platform with VoIP, Email, SMS, and CRM capabilities.

## Features

- 🎯 Multi-tenant Architecture
- 📞 VoIP Integration with Twilio
- ⚡ Real-time Notifications via WebSocket
- 👥 Advanced Contact Management
- 📊 Activity Timeline
- 🔒 Security & Compliance (GDPR)

## Quick Start

### Development

```bash
# Install dependencies
npm install

# Start development server
npm start

# Open http://localhost:3000
```

### Production Build

```bash
# Build for production
npm run build

# Serve locally
npm install -g serve
serve -s build
```

## Deployment

### Deploy to Koyeb

1. **Create Koyeb Service**
   - Go to https://app.koyeb.com
   - Create Service → GitHub
   - Select this repository
   - Build type: Docker
   - Service name: `sales-engagement-frontend`

2. **Environment Variables**
   ```
   NODE_ENV=production
   ```

3. **Deploy**
   - Click Deploy
   - Wait 5-10 minutes for build completion

### Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

### Deploy to Netlify

1. Connect repository to Netlify
2. Build command: `npm run build`
3. Publish directory: `build`

## Configuration

### Environment Variables

- `REACT_APP_API_URL`: Backend API URL (default: `/api/v1`)
- `REACT_APP_WS_URL`: WebSocket URL (default: `/ws`)
- `REACT_APP_ENVIRONMENT`: Environment (development/production)

### Backend Integration

The frontend is configured to work with the Sales Engagement Platform backend:
- Backend Repository: https://github.com/joelezz/sales-engagement-platform
- API Documentation: Available at `/docs` on backend service

## Architecture

### Components

- **Authentication**: Login/logout with JWT tokens
- **Dashboard**: Overview with statistics and quick actions
- **Contacts**: Contact management with search and filtering
- **Activities**: Timeline view of all interactions
- **Real-time**: WebSocket integration for live updates

### State Management

- React Query for server state
- Context API for global state
- Local state for component-specific data

### Styling

- Custom CSS with design system variables
- Responsive design for mobile and desktop
- Consistent component library

## Development

### Project Structure

```
src/
├── components/          # React components
├── contexts/           # React contexts
├── hooks/              # Custom hooks
├── services/           # API services
├── App.js              # Main app component
└── index.js            # Entry point
```

### Available Scripts

- `npm start`: Development server
- `npm run build`: Production build
- `npm test`: Run tests
- `npm run eject`: Eject from Create React App

### API Integration

The frontend communicates with the backend via:
- REST API for CRUD operations
- WebSocket for real-time updates
- JWT authentication for security

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## License

Proprietary - Sales Engagement Platform