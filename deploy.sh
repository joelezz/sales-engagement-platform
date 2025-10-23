#!/bin/bash

# Sales Engagement Platform - Tuotantokäyttöönotto
# Käyttö: ./deploy.sh

set -e

echo "🚀 Sales Engagement Platform - Tuotantokäyttöönotto"
echo "=================================================="

# Värit
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Tarkista että ollaan oikeassa hakemistossa
if [ ! -f "docker-compose.prod.yml" ]; then
    echo -e "${RED}❌ docker-compose.prod.yml ei löydy. Aja skripti projektin juuressa.${NC}"
    exit 1
fi

# Tarkista että .env.production on olemassa
if [ ! -f ".env.production" ]; then
    echo -e "${RED}❌ .env.production ei löydy. Kopioi .env.production ja täytä oikeat arvot.${NC}"
    exit 1
fi

# Kopioi tuotantoasetukset
echo -e "${YELLOW}📋 Kopioidaan tuotantoasetukset...${NC}"
cp .env.production .env

# Tarkista Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker ei ole asennettu. Asenna Docker ensin.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose ei ole asennettu. Asenna Docker Compose ensin.${NC}"
    exit 1
fi

# Pysäytä vanhat kontainerit
echo -e "${YELLOW}🛑 Pysäytetään vanhat kontainerit...${NC}"
docker-compose -f docker-compose.prod.yml down || true

# Rakenna ja käynnistä uudet kontainerit
echo -e "${YELLOW}🔨 Rakennetaan ja käynnistetään kontainerit...${NC}"
docker-compose -f docker-compose.prod.yml up -d --build

# Odota että tietokanta käynnistyy
echo -e "${YELLOW}⏳ Odotetaan tietokannan käynnistymistä...${NC}"
sleep 10

# Suorita migraatiot
echo -e "${YELLOW}🗄️ Suoritetaan tietokannan migraatiot...${NC}"
docker-compose -f docker-compose.prod.yml exec -T backend alembic upgrade head

# Tarkista palveluiden tila
echo -e "${YELLOW}🔍 Tarkistetaan palveluiden tila...${NC}"
docker-compose -f docker-compose.prod.yml ps

# Testaa backend
echo -e "${YELLOW}🧪 Testataan backend...${NC}"
sleep 5
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend toimii!${NC}"
else
    echo -e "${RED}❌ Backend ei vastaa. Tarkista lokit: docker-compose -f docker-compose.prod.yml logs backend${NC}"
fi

# Testaa frontend
echo -e "${YELLOW}🧪 Testataan frontend...${NC}"
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend toimii!${NC}"
else
    echo -e "${RED}❌ Frontend ei vastaa. Tarkista lokit: docker-compose -f docker-compose.prod.yml logs frontend${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Käyttöönotto valmis!${NC}"
echo ""
echo "📊 Hyödylliset komennot:"
echo "  Lokit:           docker-compose -f docker-compose.prod.yml logs -f"
echo "  Tila:            docker-compose -f docker-compose.prod.yml ps"
echo "  Pysäytä:         docker-compose -f docker-compose.prod.yml down"
echo "  Käynnistä:       docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "🌐 Palvelut:"
echo "  Backend:         http://localhost:8001"
echo "  Frontend:        http://localhost:3000"
echo "  API Docs:        http://localhost:8001/docs"
echo ""
echo "🔧 Seuraavat vaiheet:"
echo "  1. Konfiguroi Nginx reverse proxy"
echo "  2. Hanki SSL-sertifikaatit (Let's Encrypt)"
echo "  3. Aseta DNS-asetukset (call.duoai.tech)"
echo "  4. Testaa Twilio webhook-toiminnot"
echo ""
echo -e "${YELLOW}📖 Katso täydelliset ohjeet: PRODUCTION_DEPLOYMENT_GUIDE.md${NC}"