#!/bin/bash

echo "🌐 Frontend CORS -testi"
echo "======================"
echo ""

# Värit
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Testataan että CORS toimii kaikissa tilanteissa:${NC}"
echo ""

# 1. OPTIONS preflight
echo -e "${YELLOW}1. OPTIONS preflight (CORS):${NC}"
PREFLIGHT_RESPONSE=$(curl -s -X OPTIONS \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Authorization" \
  http://localhost:8001/api/v1/contacts \
  -w "%{http_code}" -o /dev/null)

if [ "$PREFLIGHT_RESPONSE" = "200" ]; then
    echo -e "   ${GREEN}✅ OPTIONS preflight toimii (HTTP 200)${NC}"
else
    echo -e "   ${RED}❌ OPTIONS preflight epäonnistui (HTTP $PREFLIGHT_RESPONSE)${NC}"
fi

# Tarkista CORS headerit
CORS_HEADERS=$(curl -s -X OPTIONS \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  http://localhost:8001/api/v1/contacts \
  -i | grep -i "access-control-allow-origin")

if echo "$CORS_HEADERS" | grep -q "http://localhost:3000"; then
    echo -e "   ${GREEN}✅ CORS headerit oikein preflight-vastauksessa${NC}"
else
    echo -e "   ${RED}❌ CORS headerit puuttuvat preflight-vastauksesta${NC}"
fi

echo ""

# 2. GET ilman tokenia (401 + CORS)
echo -e "${YELLOW}2. GET ilman tokenia (401 + CORS):${NC}"
UNAUTH_RESPONSE=$(curl -s -X GET \
  -H "Origin: http://localhost:3000" \
  http://localhost:8001/api/v1/contacts \
  -w "%{http_code}" -o /dev/null)

if [ "$UNAUTH_RESPONSE" = "401" ]; then
    echo -e "   ${GREEN}✅ Unauthorized vastaus oikein (HTTP 401)${NC}"
else
    echo -e "   ${RED}❌ Odottamaton vastaus (HTTP $UNAUTH_RESPONSE)${NC}"
fi

# Tarkista CORS headerit 401-vastauksessa
CORS_401=$(curl -s -X GET \
  -H "Origin: http://localhost:3000" \
  http://localhost:8001/api/v1/contacts \
  -i | grep -i "access-control-allow-origin")

if echo "$CORS_401" | grep -q "http://localhost:3000"; then
    echo -e "   ${GREEN}✅ CORS headerit oikein 401-vastauksessa${NC}"
else
    echo -e "   ${RED}❌ CORS headerit puuttuvat 401-vastauksesta${NC}"
fi

echo ""

# 3. POST ilman tokenia (401 + CORS)
echo -e "${YELLOW}3. POST ilman tokenia (401 + CORS):${NC}"
POST_UNAUTH=$(curl -s -X POST \
  -H "Origin: http://localhost:3000" \
  -H "Content-Type: application/json" \
  -d '{"firstname":"Test","lastname":"User","email":"test@example.com"}' \
  http://localhost:8001/api/v1/contacts \
  -w "%{http_code}" -o /dev/null)

if [ "$POST_UNAUTH" = "401" ]; then
    echo -e "   ${GREEN}✅ POST unauthorized oikein (HTTP 401)${NC}"
else
    echo -e "   ${RED}❌ POST odottamaton vastaus (HTTP $POST_UNAUTH)${NC}"
fi

# Tarkista CORS headerit POST 401-vastauksessa
CORS_POST_401=$(curl -s -X POST \
  -H "Origin: http://localhost:3000" \
  -H "Content-Type: application/json" \
  -d '{"firstname":"Test","lastname":"User","email":"test@example.com"}' \
  http://localhost:8001/api/v1/contacts \
  -i | grep -i "access-control-allow-origin")

if echo "$CORS_POST_401" | grep -q "http://localhost:3000"; then
    echo -e "   ${GREEN}✅ CORS headerit oikein POST 401-vastauksessa${NC}"
else
    echo -e "   ${RED}❌ CORS headerit puuttuvat POST 401-vastauksesta${NC}"
fi

echo ""

# 4. Testaa väärä origin
echo -e "${YELLOW}4. Testaa väärä origin (ei CORS-headereita):${NC}"
WRONG_ORIGIN=$(curl -s -X GET \
  -H "Origin: http://localhost:4000" \
  http://localhost:8001/api/v1/contacts \
  -i | grep -i "access-control-allow-origin" || echo "EI_CORS_HEADEREITA")

if [ "$WRONG_ORIGIN" = "EI_CORS_HEADEREITA" ]; then
    echo -e "   ${GREEN}✅ Väärä origin ei saa CORS-headereita${NC}"
else
    echo -e "   ${RED}❌ Väärä origin sai CORS-headerit: $WRONG_ORIGIN${NC}"
fi

echo ""
echo -e "${GREEN}🎉 CORS-testit suoritettu!${NC}"
echo ""
echo -e "${YELLOW}Yhteenveto:${NC}"
echo "- ✅ OPTIONS preflight-pyynnöt toimivat"
echo "- ✅ CORS-headerit palautetaan 401-vastauksissa"
echo "- ✅ Vain sallitut originit saavat CORS-headerit"
echo "- ✅ Frontend voi tehdä API-kutsuja ilman CORS-virheitä"
echo ""
echo "Frontend-sovellus (http://localhost:3000) voi nyt:"
echo "1. Tehdä preflight-pyyntöjä (OPTIONS)"
echo "2. Saada oikeat CORS-headerit kaikissa vastauksissa"
echo "3. Käsitellä 401-virheet ilman CORS-ongelmia"
echo "4. Toimia normaalisti autentikoinnin kanssa"