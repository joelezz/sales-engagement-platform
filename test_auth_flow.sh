#!/bin/bash

echo "🔐 Testataan autentikointi ja CORS yhdessä"
echo "=========================================="
echo ""

# Värit
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Rekisteröi uusi käyttäjä
echo -e "${YELLOW}1. Rekisteröidään uusi käyttäjä...${NC}"
REGISTER_RESPONSE=$(curl -s -X POST \
  -H "Origin: http://localhost:3000" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "TestPassword123!",
    "full_name": "Test User",
    "company_name": "Test Company"
  }' \
  http://localhost:8001/api/v1/auth/register \
  -w "%{http_code}")

HTTP_CODE="${REGISTER_RESPONSE: -3}"
RESPONSE_BODY="${REGISTER_RESPONSE%???}"

if [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "409" ]; then
    echo -e "   ${GREEN}✅ Rekisteröinti onnistui tai käyttäjä on jo olemassa${NC}"
else
    echo -e "   ${RED}❌ Rekisteröinti epäonnistui (HTTP $HTTP_CODE)${NC}"
    echo "   Response: $RESPONSE_BODY"
fi

echo ""

# 2. Kirjaudu sisään
echo -e "${YELLOW}2. Kirjaudutaan sisään...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST \
  -H "Origin: http://localhost:3000" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "TestPassword123!"
  }' \
  http://localhost:8001/api/v1/auth/login \
  -w "%{http_code}")

HTTP_CODE="${LOGIN_RESPONSE: -3}"
RESPONSE_BODY="${LOGIN_RESPONSE%???}"

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "   ${GREEN}✅ Kirjautuminen onnistui${NC}"
    
    # Pura token vastauksesta
    TOKEN=$(echo "$RESPONSE_BODY" | jq -r '.access_token' 2>/dev/null)
    
    if [ "$TOKEN" != "null" ] && [ "$TOKEN" != "" ]; then
        echo "   Token saatu: ${TOKEN:0:20}..."
    else
        echo -e "   ${RED}❌ Token puuttuu vastauksesta${NC}"
        exit 1
    fi
else
    echo -e "   ${RED}❌ Kirjautuminen epäonnistui (HTTP $HTTP_CODE)${NC}"
    echo "   Response: $RESPONSE_BODY"
    exit 1
fi

echo ""

# 3. Testaa suojattua endpointia
echo -e "${YELLOW}3. Testataan suojattua endpointia tokenilla...${NC}"
CONTACTS_RESPONSE=$(curl -s -X GET \
  -H "Origin: http://localhost:3000" \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/v1/contacts \
  -w "%{http_code}")

HTTP_CODE="${CONTACTS_RESPONSE: -3}"
RESPONSE_BODY="${CONTACTS_RESPONSE%???}"

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "   ${GREEN}✅ Suojattu endpoint toimii tokenilla${NC}"
    echo "   Kontaktien määrä: $(echo "$RESPONSE_BODY" | jq '. | length' 2>/dev/null || echo "Ei voitu laskea")"
else
    echo -e "   ${RED}❌ Suojattu endpoint epäonnistui (HTTP $HTTP_CODE)${NC}"
    echo "   Response: $RESPONSE_BODY"
fi

echo ""

# 4. Testaa CORS headerit suojatussa endpointissa
echo -e "${YELLOW}4. Tarkistetaan CORS headerit suojatussa endpointissa...${NC}"
CORS_HEADERS=$(curl -s -X GET \
  -H "Origin: http://localhost:3000" \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/v1/contacts \
  -i | grep -i "access-control")

if echo "$CORS_HEADERS" | grep -q "access-control-allow-origin"; then
    echo -e "   ${GREEN}✅ CORS headerit löytyvät suojatusta endpointista${NC}"
else
    echo -e "   ${RED}❌ CORS headerit puuttuvat suojatusta endpointista${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Autentikointi ja CORS testit suoritettu!${NC}"
echo ""
echo "Nyt voit testata frontend-sovellusta:"
echo "1. Avaa http://localhost:3000"
echo "2. Kirjaudu sisään tunnuksilla: testuser@example.com / TestPassword123!"
echo "3. Testaa kontaktien luomista ja hakua"
echo "4. Tarkista että CORS-virheitä ei tule konsolissa"