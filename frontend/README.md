# Sales Engagement Platform - Frontend

Modern React frontend for the Sales Engagement Platform with Finnish language support.

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ 
- Your Sales Engagement Platform backend running on http://localhost:8001

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

The app will open at http://localhost:3000 and automatically proxy API requests to your backend.

## 🎨 Features

### ✅ Implemented
- **Finnish Language UI** - Complete Finnish localization
- **Modern Design** - Clean, professional interface using CSS variables
- **Responsive Layout** - Works on desktop, tablet, and mobile
- **Authentication** - Login/registration with JWT tokens
- **Contact Management** - Create, view, edit, and search contacts
- **Real-time Integration** - Connected to your backend API
- **Activity Timeline** - View contact interaction history

### 🎯 Key Components
- **LoginScreen** - User authentication (kirjautumisnäyttö)
- **Dashboard** - Main contact list view (kontaktilistausnäyttö)
- **ContactDetails** - Individual contact view (kontaktin tietojen näyttö)
- **ContactForm** - Create/edit contact modal
- **Header** - Navigation with search functionality

## 🔧 Configuration

### API Integration
The frontend is configured to work with your backend:
- **Development**: http://localhost:8001
- **Production**: Configure in `src/services/api.js`

### Styling
Uses CSS variables for easy theming in `src/index.css`:
- Colors, spacing, typography
- Responsive breakpoints
- Component styles

## 📱 Responsive Design

- **Desktop**: Full-featured layout with sidebar
- **Tablet**: Adapted grid layouts
- **Mobile**: Stacked layouts with touch-friendly controls

## 🌐 Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 🚀 Deployment

```bash
# Build for production
npm run build

# Serve static files
# Deploy the 'build' folder to your web server
```

## 🔗 Backend Integration

Perfect integration with your Sales Engagement Platform backend:
- JWT authentication
- Contact CRUD operations
- Activity timeline
- Real-time search
- Error handling

Your frontend is ready to use with the backend running on port 8001! 🎯