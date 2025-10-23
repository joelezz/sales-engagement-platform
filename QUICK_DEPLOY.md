# 🚀 Pikaohje: Tuotantokäyttöönotto

## 1. VPS-palvelimen valmistelu

```bash
# Kirjaudu VPS:lle
ssh root@your_hostinger_vps_ip

# Päivitä järjestelmä
apt update && apt upgrade -y

# Asenna Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Asenna Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Asenna Nginx ja Certbot
apt install -y nginx certbot python3-certbot-nginx
```

## 2. Projektin käyttöönotto

```bash
# Kloonaa projekti
git clone https://github.com/your-username/sales-engagement-platform.git
cd sales-engagement-platform

# Kopioi ja muokkaa tuotantoasetukset
cp .env.production .env
nano .env  # Vaihda salasanat ja Twilio-asetukset!

# Käynnistä sovellus
./deploy.sh
```

## 3. DNS-asetukset (Hostinger)

**Lisää DNS-tietueet:**
```
A Record: call.duoai.tech → [VPS IP]
A Record: api.call.duoai.tech → [VPS IP]
```

## 4. SSL ja Nginx

```bash
# Kopioi Nginx-konfiguraatio
cp nginx-site.conf /etc/nginx/sites-available/sales-engagement
ln -s /etc/nginx/sites-available/sales-engagement /etc/nginx/sites-enabled/

# Hanki SSL-sertifikaatti
certbot --nginx -d call.duoai.tech -d api.call.duoai.tech

# Käynnistä Nginx uudelleen
systemctl reload nginx
```

## 5. Testaa

- **Frontend:** https://call.duoai.tech
- **Backend:** https://api.call.duoai.tech/health
- **API Docs:** https://api.call.duoai.tech/docs

## 6. Twilio-asetukset

1. Kirjaudu Twilio Console:iin
2. Aseta webhook URL: `https://api.call.duoai.tech/api/v1/webhooks/twilio/call-status`
3. Testaa soittotoiminto

## ✅ Valmis!

**Sales Engagement Platform on nyt tuotannossa!**

- Frontend: https://call.duoai.tech
- Backend: https://api.call.duoai.tech
- VoIP-soittotoiminto toimii täydellisesti!

---

**Tarvitsetko apua?** Katso täydelliset ohjeet: `PRODUCTION_DEPLOYMENT_GUIDE.md`