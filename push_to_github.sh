#!/bin/bash

# Sales Engagement Platform - GitHub Push Script
# Käyttö: ./push_to_github.sh YOUR_GITHUB_USERNAME

if [ -z "$1" ]; then
    echo "❌ Anna GitHub-käyttäjänimesi parametrina:"
    echo "   ./push_to_github.sh YOUR_GITHUB_USERNAME"
    exit 1
fi

GITHUB_USERNAME=$1
REPO_NAME="sales-engagement-platform"

echo "🚀 Lähetetään Sales Engagement Platform GitHub:iin..."
echo "👤 Käyttäjä: $GITHUB_USERNAME"
echo "📁 Repositorio: $REPO_NAME"
echo ""

# Tarkista että ollaan oikeassa hakemistossa
if [ ! -f "README.md" ] || [ ! -f ".gitignore" ]; then
    echo "❌ Virhe: Aja skripti projektin juurihakemistossa"
    exit 1
fi

# Lisää GitHub remote
echo "📡 Lisätään GitHub remote..."
git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git

# Vaihda branch main:iksi
echo "🌿 Vaihdetaan branch main:iksi..."
git branch -M main

# Lähetä koodi GitHub:iin
echo "☁️ Lähetetään koodi GitHub:iin..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 ONNISTUI! Koodi on nyt GitHub:issa!"
    echo ""
    echo "🌐 Repositorio: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
    echo "📚 README: https://github.com/$GITHUB_USERNAME/$REPO_NAME#readme"
    echo "🚀 Actions: https://github.com/$GITHUB_USERNAME/$REPO_NAME/actions"
    echo ""
    echo "🔧 Seuraavat vaiheet:"
    echo ""
    echo "🚀 KOYEB DEPLOYMENT (Suositeltu):"
    echo "1. Luo tili: https://www.koyeb.com"
    echo "2. Konfiguroi GitHub Secrets (Settings > Secrets and variables > Actions):"
    echo "   - KOYEB_API_TOKEN (Koyeb API token)"
    echo "3. Lue deployment-opas: KOYEB_DEPLOYMENT_GUIDE.md"
    echo "4. Deploy automaattisesti: git push origin main"
    echo ""
    echo "🐳 DOCKER DEPLOYMENT (Vaihtoehto):"
    echo "1. Konfiguroi GitHub Secrets:"
    echo "   - PRODUCTION_HOST (VPS IP-osoite)"
    echo "   - PRODUCTION_USER (SSH käyttäjä)"
    echo "   - PRODUCTION_SSH_KEY (SSH private key)"
    echo "2. Deploy tuotantoon: ./deploy.sh"
    echo ""
    echo "📚 Dokumentaatio:"
    echo "   - Koyeb: KOYEB_DEPLOYMENT_GUIDE.md"
    echo "   - Docker: PRODUCTION_DEPLOYMENT_GUIDE.md"
    echo "   - VoIP: VOIP_SETUP_GUIDE.md"
else
    echo ""
    echo "❌ Virhe GitHub:iin lähettämisessä!"
    echo "Tarkista että:"
    echo "1. GitHub-repositorio on luotu: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
    echo "2. Sinulla on push-oikeudet repositorioon"
    echo "3. Git-tunnukset on konfiguroitu: git config --global user.name ja user.email"
fi