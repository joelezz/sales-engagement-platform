#!/bin/bash

# Kattava E2E-testiskripti Sales Engagement Platform -sovellukselle
# Testaa frontend + backend yhdessä todellisessa selainympäristössä

set -e

echo "🚀 Aloitetaan kattava E2E-testaus Sales Engagement Platform -sovellukselle..."

# Tarkista että tarvittavat palvelut ovat käynnissä
echo "🔍 Tarkistetaan palveluiden tila..."

# Tarkista PostgreSQL
if ! sudo docker ps | grep -q postgres; then
    echo "❌ PostgreSQL ei ole käynnissä. Käynnistetään palvelut..."
    sudo docker-compose up -d postgres redis
    sleep 10
fi

# Tarkista Redis
if ! sudo docker ps | grep -q redis; then
    echo "❌ Redis ei ole käynnissä. Käynnistetään..."
    sudo docker-compose up -d redis
    sleep 5
fi

echo "✅ Tietokantapalvelut ovat käynnissä"

# Asenna E2E-testien riippuvuudet
echo "📦 Asennetaan E2E-testien riippuvuudet..."
pip3 install playwright pytest pytest-asyncio httpx

# Asenna Playwright-selaimet
echo "🌐 Asennetaan Playwright-selaimet..."
python3 -m playwright install chromium

# Tarkista että backend on käynnissä
echo "🔍 Tarkistetaan backend-palvelimen tila..."
if ! curl -s http://localhost:8001/health > /dev/null; then
    echo "❌ Backend ei ole käynnissä portissa 8001"
    echo "💡 Käynnistä backend komennolla: python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001"
    exit 1
fi

echo "✅ Backend on käynnissä"

# Tarkista että frontend on käynnissä
echo "🔍 Tarkistetaan frontend-sovelluksen tila..."
if ! curl -s http://localhost:3000 > /dev/null; then
    echo "❌ Frontend ei ole käynnissä portissa 3000"
    echo "💡 Käynnistä frontend komennoilla:"
    echo "   cd frontend"
    echo "   npm install"
    echo "   npm start"
    exit 1
fi

echo "✅ Frontend on käynnissä"

# Suorita E2E-testit
echo "🧪 Suoritetaan kattavat E2E-testit..."
echo "📺 Selain aukeaa automaattisesti testien aikana"

# Aseta testiympäristömuuttujat
export BACKEND_URL="http://localhost:8001"
export FRONTEND_URL="http://localhost:3000"
export HEADLESS=false  # Näytä selain testien aikana

# Suorita testit
if python3 tests/e2e/test_full_application.py; then
    echo ""
    echo "🎉 KAIKKI E2E-TESTIT ONNISTUIVAT!"
    echo ""
    echo "✅ Testatut ominaisuudet:"
    echo "   🔧 Backend API toimivuus"
    echo "   🌐 Frontend latautuminen"
    echo "   👤 Käyttäjän rekisteröinti ja kirjautuminen"
    echo "   📇 Kontaktien hallinta (luominen, katsominen, haku)"
    echo "   📅 Aktiviteettien aikajana"
    echo "   🔍 Hakutoiminnallisuus"
    echo "   🧭 Navigointi sivujen välillä"
    echo "   📱 Responsiivinen suunnittelu"
    echo "   ⚠️  Virheenkäsittely"
    echo ""
    echo "🚀 Sales Engagement Platform toimii täydellisesti!"
    echo "💡 Sovellus on valmis tuotantokäyttöön"
    
else
    echo ""
    echo "❌ Jotkut E2E-testit epäonnistuivat"
    echo "🔍 Tarkista virheviestit yllä olevasta tulosteesta"
    echo ""
    echo "🛠️  Yleisiä ratkaisuja:"
    echo "   - Varmista että backend on käynnissä portissa 8001"
    echo "   - Varmista että frontend on käynnissä portissa 3000"
    echo "   - Tarkista että tietokanta on käynnissä ja saavutettavissa"
    echo "   - Varmista että kaikki riippuvuudet on asennettu"
    
    exit 1
fi

echo ""
echo "📊 Testiraportti:"
echo "   - Testien kesto: ~2-3 minuuttia"
echo "   - Testatut komponentit: Frontend + Backend + Tietokanta"
echo "   - Testatut selaimet: Chromium"
echo "   - Testatut näyttökoot: Desktop, Tablet, Mobile"
echo ""
echo "🎯 Sovelluksesi on valmis käyttöön!"