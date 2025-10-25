#!/bin/bash

# Script to create separate frontend repository

echo "🚀 Creating separate frontend repository..."

# Create directory
mkdir -p ../sales-engagement-frontend
cd ../sales-engagement-frontend

# Initialize git
git init
git branch -m main

# Copy frontend files
echo "📁 Copying frontend files..."
cp -r ../sales_engagement_platform/frontend/* .
cp ../sales_engagement_platform/frontend/.env* . 2>/dev/null || true
cp ../sales_engagement_platform/frontend/.dockerignore . 2>/dev/null || true

# Copy standalone files
cp ../sales_engagement_platform/frontend-standalone/Dockerfile .
cp ../sales_engagement_platform/frontend-standalone/README.md .
cp ../sales_engagement_platform/frontend-standalone/.gitignore .

# Remove monorepo-specific files
rm -f koyeb.toml

echo "📝 Files copied successfully!"

# Show next steps
echo ""
echo "✅ Frontend repository created at: ../sales-engagement-frontend"
echo ""
echo "🔧 Next steps:"
echo "1. cd ../sales-engagement-frontend"
echo "2. Create GitHub repository: https://github.com/new"
echo "3. Repository name: sales-engagement-frontend"
echo "4. git add ."
echo "5. git commit -m 'Initial frontend repository'"
echo "6. git remote add origin https://github.com/joelezz/sales-engagement-frontend.git"
echo "7. git push -u origin main"
echo ""
echo "🚀 Then deploy to Koyeb:"
echo "- Go to https://app.koyeb.com"
echo "- Create Service → GitHub"
echo "- Select: sales-engagement-frontend repository"
echo "- Build type: Docker"
echo "- Deploy!"
echo ""

# Test build
echo "🧪 Testing build..."
if command -v npm &> /dev/null; then
    npm install
    if npm run build; then
        echo "✅ Build successful!"
    else
        echo "❌ Build failed - check for errors"
    fi
else
    echo "⚠️  npm not found - install Node.js to test build"
fi

echo "🎉 Setup complete!"