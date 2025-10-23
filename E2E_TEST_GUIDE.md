# Sales Engagement Platform - E2E Testausopas

## 🎯 Yleiskatsaus

Tämä opas kertoo kuinka suorittaa kattavat End-to-End (E2E) testit Sales Engagement Platform -sovellukselle. E2E-testit testaavat koko sovelluksen toimivuuden frontend + backend yhdessä todellisessa selainympäristössä.

## 🧪 Mitä E2E-testit testaavat

### ✅ **Testatut toiminnallisuudet:**
- **Backend API toimivuus** - Palvelimen terveys ja API-vastaukset
- **Frontend latautuminen** - React-sovelluksen käynnistyminen
- **Käyttäjän rekisteröinti** - Uuden käyttäjän luominen
- **Kirjautuminen** - JWT-autentikointi
- **Kontaktien hallinta** - CRUD-operaatiot (Create, Read, Update, Delete)
- **Aktiviteettien aikajana** - Aktiviteettien luominen ja katsominen
- **Hakutoiminnallisuus** - Kontaktien haku
- **Navigointi** - Sivujen välinen liikkuminen
- **Responsiivinen suunnittelu** - Mobile, tablet, desktop
- **Virheenkäsittely** - Virhetilanteiden hallinta

### 🔧 **Tekninen toteutus:**
- **Playwright** - Selainautomatisointi
- **Python pytest** - Testikehys
- **Chromium-selain** - Testien suoritus
- **Visuaalinen testaus** - Selain näkyy testien aikana

## 🚀 Kuinka suorittaa E2E-testit

### **Vaihe 1: Valmistelut**

Varmista että seuraavat palvelut ovat käynnissä:

```bash
# 1. Käynnistä tietokantapalvelut
sudo docker-compose up -d postgres redis

# 2. Käynnistä backend (terminaali 1)
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001

# 3. Käynnistä frontend (terminaali 2)
cd frontend
npm install
npm start
```

### **Vaihe 2: Suorita E2E-testit**

```bash
# Automaattinen testiskripti (suositeltu)
./scripts/run_full_e2e_test.sh

# TAI manuaalinen suoritus
python3 tests/e2e/test_full_application.py
```

## 📊 Testien tulokset

### **Onnistunut testi näyttää:**
```
🎉 KAIKKI E2E-TESTIT ONNISTUIVAT!

✅ Testatut ominaisuudet:
   🔧 Backend API toimivuus
   🌐 Frontend latautuminen
   👤 Käyttäjän rekisteröinti ja kirjautuminen
   📇 Kontaktien hallinta (luominen, katsominen, haku)
   📅 Aktiviteettien aikajana
   🔍 Hakutoiminnallisuus
   🧭 Navigointi sivujen välillä
   📱 Responsiivinen suunnittelu
   ⚠️  Virheenkäsittely

🚀 Sales Engagement Platform toimii täydellisesti!
```

### **Testien kesto:**
- **Kokonaisaika**: ~2-3 minuuttia
- **Selain näkyy** testien aikana (ei headless)
- **Hidastettua toimintaa** paremman näkyvyyden vuoksi

## 🛠️ Vianmääritys

### **Yleiset ongelmat ja ratkaisut:**

#### ❌ "Backend ei ole käynnissä"
```bash
# Tarkista backend-palvelimen tila
curl http://localhost:8001/health

# Käynnistä backend uudelleen
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

#### ❌ "Frontend ei ole käynnissä"
```bash
# Tarkista frontend-sovelluksen tila
curl http://localhost:3000

# Käynnistä frontend uudelleen
cd frontend
npm start
```

#### ❌ "Tietokanta ei ole saavutettavissa"
```bash
# Tarkista Docker-kontainerit
sudo docker ps

# Käynnistä tietokantapalvelut
sudo docker-compose up -d postgres redis
```

#### ❌ "Playwright ei ole asennettu"
```bash
# Asenna Playwright
pip3 install playwright pytest pytest-asyncio httpx
python3 -m playwright install chromium
```

## 📋 Testien yksityiskohdat

### **Test 1: Backend Health Check**
- Tarkistaa `/health` endpoint
- Varmistaa että API vastaa oikein
- Tarkistaa palvelun tilan

### **Test 2: Frontend Loading**
- Lataa React-sovelluksen
- Tarkistaa että kirjautumissivu näkyy
- Varmistaa että CSS ja JavaScript latautuvat

### **Test 3: User Registration & Login**
- Luo uuden käyttäjän
- Täyttää rekisteröintilomakkeen
- Kirjautuu sisään automaattisesti
- Tarkistaa JWT-tokenin toimivuuden

### **Test 4: Contact Management**
- Luo uuden kontaktin
- Täyttää kaikki kontaktitiedot
- Tarkistaa että kontakti näkyy listassa
- Testaa kontaktin tietojen katsomisen

### **Test 5: Activities Timeline**
- Navigoi aktiviteettien aikajanaan
- Luo uuden aktiviteetin (muistiinpano)
- Testaa suodatustoiminnallisuuden
- Tarkistaa että aktiviteetti näkyy aikajanassa

### **Test 6: Search Functionality**
- Testaa kontaktien hakua
- Syöttää hakutermin
- Tarkistaa hakutulosten näkymisen

### **Test 7: Navigation & UI**
- Testaa navigointia sivujen välillä
- Tarkistaa että kaikki linkit toimivat
- Testaa uloskirjautumisen

### **Test 8: Responsive Design**
- Testaa mobiilikoossa (375x667)
- Testaa tablettikoossa (768x1024)
- Testaa desktop-koossa (1280x720)
- Varmistaa että UI toimii kaikissa koossa

### **Test 9: Error Handling**
- Testaa virheellisiä kirjautumistietoja
- Tarkistaa virheilmoitusten näkymisen

## 🎯 Testien hyödyt

### **Laadunvarmistus:**
- Varmistaa että koko sovellus toimii yhdessä
- Testaa todellista käyttäjäkokemusta
- Löytää integraatio-ongelmat

### **Automaatio:**
- Säästää aikaa manuaalisesta testauksesta
- Voidaan suorittaa säännöllisesti
- Varmistaa että muutokset eivät riko toiminnallisuutta

### **Dokumentaatio:**
- Toimii käyttöohjeena sovelluksen käytölle
- Näyttää mitä ominaisuuksia sovelluksessa on
- Auttaa uusia kehittäjiä ymmärtämään sovelluksen

## 🚀 Tuotantovalmius

Kun kaikki E2E-testit menevät läpi, sovelluksesi on valmis tuotantokäyttöön:

- ✅ **Frontend ja backend** toimivat yhdessä
- ✅ **Tietokantayhteydet** ovat kunnossa
- ✅ **Käyttöliittymä** on toimiva ja responsiivinen
- ✅ **Kaikki pääominaisuudet** toimivat odotetusti
- ✅ **Virheenkäsittely** on kunnossa

**Onnea sovelluksesi kanssa! 🎉**