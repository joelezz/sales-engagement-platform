#!/bin/bash

echo "🚀 Käynnistetään Sales Engagement Platform Frontend..."

# Siirry frontend-hakemistoon
cd frontend

# Asenna riippuvuudet jos tarvitaan
if [ ! -d "node_modules" ]; then
    echo "📦 Asennetaan riippuvuudet..."
    npm install
fi

# Käynnistä development server
echo "🌐 Käynnistetään React development server..."
echo "📱 Sovellus aukeaa osoitteessa: http://localhost:3000"
echo "🔗 Backend API: http://localhost:8001"
echo ""
echo "✨ Voit nyt testata sovellusta selaimessa!"
echo ""

npm start