#!/bin/bash

echo "🧪 Sales Engagement Platform - CORS ja API testit"
echo "=================================================="
echo ""

# Värit
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Testaa backend
echo -e "${YELLOW}1. Backend testi:${NC}"
if curl -s http://localhost:8001/health > /dev/null; then
    echo -e "   ${GREEN}✅ Backend käynnissä (port 8001)${NC}"
    BACKEND_STATUS=$(curl -s http://localhost:8001/health | jq -r '.status')
    echo "   Status: $BACKEND_STATUS"
else
    echo -e "   ${RED}❌ Backend ei vastaa${NC}"
    exit 1
fi

echo ""

# Testaa frontend
echo -e "${YELLOW}2. Frontend testi:${NC}"
if curl -s http://localhost:3000 > /dev/null; then
    echo -e "   ${GREEN}✅ Frontend käynnissä (port 3000)${NC}"
else
    echo -e "   ${RED}❌ Frontend ei vastaa${NC}"
fi

echo ""

# Testaa CORS
echo -e "${YELLOW}3. CORS testit:${NC}"

# Preflight test
echo "   Testaa preflight (OPTIONS)..."
CORS_RESPONSE=$(curl -s -X OPTIONS \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization" \
  http://localhost:8001/api/v1/auth/login \
  -w "%{http_code}" -o /dev/null)

if [ "$CORS_RESPONSE" = "200" ]; then
    echo -e "   ${GREEN}✅ CORS preflight toimii${NC}"
else
    echo -e "   ${RED}❌ CORS preflight epäonnistui (HTTP $CORS_RESPONSE)${NC}"
fi

# Testaa CORS headerit
echo "   Testaa CORS headerit..."
CORS_HEADERS=$(curl -s -X OPTIONS \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  http://localhost:8001/api/v1/auth/login \
  -i | grep -i "access-control")

if echo "$CORS_HEADERS" | grep -q "access-control-allow-origin"; then
    echo -e "   ${GREEN}✅ CORS headerit palautetaan${NC}"
    echo "   Origin sallittu: $(echo "$CORS_HEADERS" | grep "access-control-allow-origin" | cut -d' ' -f2-)"
else
    echo -e "   ${RED}❌ CORS headerit puuttuvat${NC}"
fi

echo ""

# Testaa API endpointit
echo -e "${YELLOW}4. API endpoint testit:${NC}"

# Health endpoint
if curl -s http://localhost:8001/health | jq -e '.status == "healthy"' > /dev/null; then
    echo -e "   ${GREEN}✅ Health endpoint toimii${NC}"
else
    echo -e "   ${RED}❌ Health endpoint ei toimi${NC}"
fi

# API docs
if curl -s http://localhost:8001/docs | grep -q "Sales Engagement Platform"; then
    echo -e "   ${GREEN}✅ API dokumentaatio saatavilla${NC}"
else
    echo -e "   ${RED}❌ API dokumentaatio ei saatavilla${NC}"
fi

# OpenAPI spec
if curl -s http://localhost:8001/openapi.json | jq -e '.info.title' > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ OpenAPI spec saatavilla${NC}"
else
    echo -e "   ${RED}❌ OpenAPI spec ei saatavilla${NC}"
fi

echo ""

# Testaa auth endpoint
echo -e "${YELLOW}5. Auth endpoint testi:${NC}"
AUTH_RESPONSE=$(curl -s -X POST \
  -H "Origin: http://localhost:3000" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass"}' \
  http://localhost:8001/api/v1/auth/login \
  -w "%{http_code}" -o /dev/null)

if [ "$AUTH_RESPONSE" = "401" ]; then
    echo -e "   ${GREEN}✅ Auth endpoint vastaa (odotetusti 401 väärillä tunnuksilla)${NC}"
else
    echo -e "   ${YELLOW}⚠️  Auth endpoint vastaa HTTP $AUTH_RESPONSE${NC}"
fi

echo ""
echo -e "${GREEN}🎉 CORS ja API testit suoritettu!${NC}"
echo ""
echo "Voit nyt:"
echo "1. Avata selaimen osoitteeseen http://localhost:3000"
echo "2. Testata sovelluksen toimivuutta"
echo "3. Tarkistaa että CORS-virheitä ei tule Developer Tools -konsolissa"
echo ""
echo "API dokumentaatio: http://localhost:8001/docs"
echo "Backend health: http://localhost:8001/health"