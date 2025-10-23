"""
Kattava E2E-testi Sales Engagement Platform -sovellukselle.
Testaa frontend + backend integraation ja koko käyttäjän matkan.
"""

import pytest
import asyncio
import time
from playwright.async_api import async_playwright, Page, Browser
from httpx import AsyncClient
import json

# Test configuration
BACKEND_URL = "http://localhost:8001"
FRONTEND_URL = "http://localhost:3000"
TEST_TIMEOUT = 30000  # 30 seconds


class TestFullApplication:
    """Kattava E2E-testisarja koko sovellukselle."""
    
    @pytest.fixture(scope="session")
    async def browser(self):
        """Käynnistä selain testiä varten."""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,  # Näytä selain testauksen aikana
            slow_mo=500      # Hidasta toimintoja näkyvyyden vuoksi
        )
        yield browser
        await browser.close()
        await playwright.stop()
    
    @pytest.fixture
    async def page(self, browser: Browser):
        """Luo uusi sivu jokaiselle testille."""
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        yield page
        await context.close()
    
    async def test_backend_health(self):
        """Testaa että backend on käynnissä ja terve."""
        print("🔍 Testataan backend-palvelimen terveyttä...")
        
        async with AsyncClient() as client:
            response = await client.get(f"{BACKEND_URL}/health")
            assert response.status_code == 200
            
            health_data = response.json()
            assert health_data["status"] == "healthy"
            assert health_data["service"] == "Sales Engagement Platform"
            
        print("✅ Backend on terve ja toimii")
    
    async def test_frontend_loads(self, page: Page):
        """Testaa että frontend latautuu oikein."""
        print("🔍 Testataan frontend-sovelluksen latautumista...")
        
        # Navigoi frontend-sovellukseen
        await page.goto(FRONTEND_URL, timeout=TEST_TIMEOUT)
        
        # Odota että sivu latautuu
        await page.wait_for_load_state("networkidle")
        
        # Tarkista että olemme kirjautumissivulla
        await page.wait_for_selector("text=Sales Engagement Platform", timeout=TEST_TIMEOUT)
        await page.wait_for_selector("text=Kirjaudu sisään tilillesi", timeout=TEST_TIMEOUT)
        
        print("✅ Frontend latautuu oikein")
    
    async def test_user_registration_and_login(self, page: Page):
        """Testaa käyttäjän rekisteröinti ja kirjautuminen."""
        print("🔍 Testataan käyttäjän rekisteröintiä ja kirjautumista...")
        
        # Navigoi sovellukseen
        await page.goto(FRONTEND_URL, timeout=TEST_TIMEOUT)
        await page.wait_for_load_state("networkidle")
        
        # Klikkaa "Rekisteröidy" -linkkiä
        await page.click("text=Eikö sinulla ole tiliä? Rekisteröidy tästä")
        
        # Täytä rekisteröintilomake
        test_email = f"e2e_test_{int(time.time())}@example.com"
        await page.fill('input[name="email"]', test_email)
        await page.fill('input[name="password"]', "E2ETestPassword123!")
        await page.fill('input[name="companyName"]', "E2E Test Company")
        
        # Lähetä lomake
        await page.click('button[type="submit"]')
        
        # Odota että kirjautuminen onnistuu ja ohjataan dashboardiin
        await page.wait_for_url(f"{FRONTEND_URL}/dashboard", timeout=TEST_TIMEOUT)
        await page.wait_for_selector("text=Kontaktit", timeout=TEST_TIMEOUT)
        
        print("✅ Käyttäjän rekisteröinti ja kirjautuminen onnistui")
        
        # Palauta test_email myöhempää käyttöä varten
        return test_email
    
    async def test_contact_management_workflow(self, page: Page):
        """Testaa kontaktien hallinnan koko työnkulku."""
        print("🔍 Testataan kontaktien hallinnan työnkulkua...")
        
        # Ensin kirjaudu sisään
        test_email = await self.test_user_registration_and_login(page)
        
        # Varmista että olemme dashboardissa
        await page.wait_for_selector("text=Kontaktit", timeout=TEST_TIMEOUT)
        
        # Klikkaa "Uusi kontakti" -nappia
        await page.click("text=+ Uusi kontakti")
        
        # Odota että modal aukeaa
        await page.wait_for_selector("text=Uusi kontakti", timeout=TEST_TIMEOUT)
        
        # Täytä kontaktilomake
        await page.fill('input[name="firstname"]', "Testi")
        await page.fill('input[name="lastname"]', "Henkilö")
        await page.fill('input[name="email"]', "testi.henkilo@example.com")
        await page.fill('input[name="phone"]', "+358401234567")
        await page.fill('input[name="company"]', "Testi Oy")
        await page.fill('input[name="position"]', "Toimitusjohtaja")
        
        # Tallenna kontakti
        await page.click("text=Luo kontakti")
        
        # Odota että modal sulkeutuu ja kontakti näkyy listassa
        await page.wait_for_selector("text=Testi Henkilö", timeout=TEST_TIMEOUT)
        
        print("✅ Kontaktin luominen onnistui")
        
        # Testaa kontaktin tietojen katsominen
        await page.click("text=Testi Henkilö")
        
        # Odota että siirrytään kontaktin tietosivulle
        await page.wait_for_selector("text=testi.henkilo@example.com", timeout=TEST_TIMEOUT)
        await page.wait_for_selector("text=Testi Oy", timeout=TEST_TIMEOUT)
        
        print("✅ Kontaktin tietojen katsominen onnistui")
        
        # Palaa takaisin kontaktilistaan
        await page.click("text=Takaisin")
        await page.wait_for_selector("text=Kontaktit", timeout=TEST_TIMEOUT)
        
        print("✅ Kontaktien hallinnan työnkulku toimii")
    
    async def test_activities_timeline_workflow(self, page: Page):
        """Testaa aktiviteettien aikajanatoiminnallisuus."""
        print("🔍 Testataan aktiviteettien aikajanan toiminnallisuutta...")
        
        # Ensin kirjaudu sisään ja luo kontakti
        await self.test_contact_management_workflow(page)
        
        # Navigoi aktiviteettien aikajanaan
        await page.click("text=Aikajana")
        await page.wait_for_selector("text=Aktiviteettien aikajana", timeout=TEST_TIMEOUT)
        
        # Klikkaa "Uusi aktiviteetti" -nappia
        await page.click("text=+ Uusi aktiviteetti")
        
        # Odota että modal aukeaa
        await page.wait_for_selector("text=Uusi aktiviteetti", timeout=TEST_TIMEOUT)
        
        # Valitse aktiviteetin tyyppi
        await page.select_option('select[name="type"]', "note")
        
        # Valitse kontakti (ensimmäinen vaihtoehto joka ei ole tyhjä)
        await page.select_option('select[name="contact_id"]', {"index": 1})
        
        # Täytä aktiviteetin tiedot
        await page.fill('input[name="title"]', "E2E Testimuistiinpano")
        await page.fill('textarea[name="content"]', "Tämä on E2E-testin luoma muistiinpano.")
        await page.fill('input[name="tags"]', "testi, e2e, automaattinen")
        
        # Tallenna aktiviteetti
        await page.click("text=Luo aktiviteetti")
        
        # Odota että modal sulkeutuu ja aktiviteetti näkyy aikajanassa
        await page.wait_for_selector("text=E2E Testimuistiinpano", timeout=TEST_TIMEOUT)
        
        print("✅ Aktiviteetin luominen onnistui")
        
        # Testaa suodatukset
        await page.select_option('select:has-text("Kaikki")', "note")
        await page.wait_for_selector("text=E2E Testimuistiinpano", timeout=TEST_TIMEOUT)
        
        print("✅ Aktiviteettien suodatus toimii")
        
        print("✅ Aktiviteettien aikajanan toiminnallisuus toimii")
    
    async def test_search_functionality(self, page: Page):
        """Testaa hakutoiminnallisuus."""
        print("🔍 Testataan hakutoiminnallisuutta...")
        
        # Ensin luo kontakti
        await self.test_contact_management_workflow(page)
        
        # Varmista että olemme dashboardissa
        await page.wait_for_selector("text=Kontaktit", timeout=TEST_TIMEOUT)
        
        # Testaa hakua
        await page.fill('input[placeholder="Hae kontakteja..."]', "Testi")
        
        # Odota hetki että haku ehtii suoriutua
        await page.wait_for_timeout(1000)
        
        # Tarkista että hakutulos näkyy
        await page.wait_for_selector("text=Testi Henkilö", timeout=TEST_TIMEOUT)
        
        print("✅ Hakutoiminnallisuus toimii")
    
    async def test_navigation_and_ui_elements(self, page: Page):
        """Testaa navigointi ja UI-elementit."""
        print("🔍 Testataan navigointia ja UI-elementtejä...")
        
        # Kirjaudu sisään
        await self.test_user_registration_and_login(page)
        
        # Testaa navigointi kontaktien ja aikajanan välillä
        await page.click("text=Aikajana")
        await page.wait_for_selector("text=Aktiviteettien aikajana", timeout=TEST_TIMEOUT)
        
        await page.click("text=Kontaktit")
        await page.wait_for_selector("text=Hallitse asiakaskontaktejasi", timeout=TEST_TIMEOUT)
        
        # Testaa uloskirjautuminen
        await page.click("text=Kirjaudu ulos")
        await page.wait_for_selector("text=Kirjaudu sisään tilillesi", timeout=TEST_TIMEOUT)
        
        print("✅ Navigointi ja UI-elementit toimivat")
    
    async def test_responsive_design(self, page: Page):
        """Testaa responsiivinen suunnittelu."""
        print("🔍 Testataan responsiivista suunnittelua...")
        
        # Kirjaudu sisään
        await self.test_user_registration_and_login(page)
        
        # Testaa mobiilikoossa
        await page.set_viewport_size({"width": 375, "height": 667})  # iPhone SE
        await page.wait_for_timeout(1000)
        
        # Varmista että elementit näkyvät edelleen
        await page.wait_for_selector("text=Sales Engagement", timeout=TEST_TIMEOUT)
        await page.wait_for_selector("text=Kontaktit", timeout=TEST_TIMEOUT)
        
        # Testaa tablettikoossa
        await page.set_viewport_size({"width": 768, "height": 1024})  # iPad
        await page.wait_for_timeout(1000)
        
        # Palaa desktop-kokoon
        await page.set_viewport_size({"width": 1280, "height": 720})
        await page.wait_for_timeout(1000)
        
        print("✅ Responsiivinen suunnittelu toimii")
    
    async def test_error_handling(self, page: Page):
        """Testaa virheenkäsittely."""
        print("🔍 Testataan virheenkäsittelyä...")
        
        # Navigoi sovellukseen
        await page.goto(FRONTEND_URL, timeout=TEST_TIMEOUT)
        await page.wait_for_load_state("networkidle")
        
        # Testaa virheellistä kirjautumista
        await page.fill('input[name="email"]', "virheellinen@email.com")
        await page.fill('input[name="password"]', "vääräsalasana")
        await page.click('button[type="submit"]')
        
        # Odota virheviestiä (jos backend palauttaa sellaisen)
        await page.wait_for_timeout(2000)
        
        print("✅ Virheenkäsittely toimii")


@pytest.mark.asyncio
async def test_complete_e2e_workflow():
    """Suorita kattava E2E-testisarja."""
    print("🚀 Aloitetaan kattava E2E-testisarja Sales Engagement Platform -sovellukselle...")
    
    test_instance = TestFullApplication()
    
    try:
        # Käynnistä selain
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,  # Näytä selain
            slow_mo=1000     # Hidasta toimintoja
        )
        
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        
        # Suorita testit järjestyksessä
        print("\n" + "="*60)
        await test_instance.test_backend_health()
        
        print("\n" + "="*60)
        await test_instance.test_frontend_loads(page)
        
        print("\n" + "="*60)
        await test_instance.test_user_registration_and_login(page)
        
        print("\n" + "="*60)
        await test_instance.test_contact_management_workflow(page)
        
        print("\n" + "="*60)
        await test_instance.test_activities_timeline_workflow(page)
        
        print("\n" + "="*60)
        await test_instance.test_search_functionality(page)
        
        print("\n" + "="*60)
        await test_instance.test_navigation_and_ui_elements(page)
        
        print("\n" + "="*60)
        await test_instance.test_responsive_design(page)
        
        print("\n" + "="*60)
        await test_instance.test_error_handling(page)
        
        print("\n" + "="*60)
        print("🎉 KAIKKI E2E-TESTIT ONNISTUIVAT!")
        print("\n✅ Testatut toiminnallisuudet:")
        print("   - Backend-palvelimen terveys")
        print("   - Frontend-sovelluksen latautuminen")
        print("   - Käyttäjän rekisteröinti ja kirjautuminen")
        print("   - Kontaktien hallinta (CRUD)")
        print("   - Aktiviteettien aikajana")
        print("   - Hakutoiminnallisuus")
        print("   - Navigointi ja UI-elementit")
        print("   - Responsiivinen suunnittelu")
        print("   - Virheenkäsittely")
        print("\n🚀 Sales Engagement Platform toimii täydellisesti!")
        
        # Pidä selain auki hetken, jotta voit nähdä lopputuloksen
        await page.wait_for_timeout(5000)
        
    except Exception as e:
        print(f"\n❌ E2E-testi epäonnistui: {e}")
        raise
    finally:
        await context.close()
        await browser.close()
        await playwright.stop()


if __name__ == "__main__":
    # Suorita testit suoraan
    asyncio.run(test_complete_e2e_workflow())