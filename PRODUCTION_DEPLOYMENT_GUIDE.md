# Sales Engagement Platform - Tuotantokäyttöönotto

## 🚀 Tuotantoympäristön käyttöönotto Hostinger VPS:lle

**Domain:** call.duoai.tech  
**Palvelu:** Hostinger VPS  
**Arkkitehtuuri:** Docker + Nginx + PostgreSQL + Redis

---

## 📋 Esivalmistelut

### 1. VPS-palvelimen valmistelu

```bash
# Päivitä järjestelmä
sudo apt update && sudo apt upgrade -y

# Asenna tarvittavat paketit
sudo apt install -y curl wget git nginx postgresql postgresql-contrib redis-server

# Asenna Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Asenna Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Uudelleenkäynnistä sessio
newgrp docker
```

### 2. Domain-asetukset

**Hostinger DNS-asetukset:**
```
A Record: call.duoai.tech → [VPS IP-osoite]
A Record: api.call.duoai.tech → [VPS IP-osoite]
```

---

## 🐳 Docker-konfiguraatio

### 1. Luo tuotanto Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # PostgreSQL tietokanta
  postgres:
    image: postgres:15
    container_name: sales_postgres
    environment:
      POSTGRES_DB: sales_engagement
      POSTGRES_USER: sales_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - sales_network

  # Redis cache
  redis:
    image: redis:7-alpine
    container_name: sales_redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    ports:
      - "6379:6379"
    restart: unless-stopped
    networks:
      - sales_network

  # Backend API
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: sales_backend
    environment:
      - DATABASE_URL=postgresql+asyncpg://sales_user:${POSTGRES_PASSWORD}@postgres:5432/sales_engagement
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}
      - TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}
      - TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER}
      - BASE_URL=https://api.call.duoai.tech
      - ALLOWED_ORIGINS=https://call.duoai.tech,https://api.call.duoai.tech
      - DEBUG=false
    ports:
      - "8001:8001"
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - sales_network

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
      args:
        - REACT_APP_API_URL=https://api.call.duoai.tech
    container_name: sales_frontend
    ports:
      - "3000:80"
    restart: unless-stopped
    networks:
      - sales_network

volumes:
  postgres_data:

networks:
  sales_network:
    driver: bridge
```

### 2. Backend Dockerfile

```dockerfile
# Dockerfile.backend
FROM python:3.11-slim

WORKDIR /app

# Asenna järjestelmäriippuvuudet
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Kopioi requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopioi sovellus
COPY . .

# Luo käyttäjä
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Käynnistä sovellus
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
```

### 3. Frontend Dockerfile

```dockerfile
# frontend/Dockerfile.prod
FROM node:18-alpine as build

WORKDIR /app

# Kopioi package files
COPY package*.json ./
RUN npm ci --only=production

# Kopioi lähdekoodi
COPY . .

# Build tuotantoversiota varten
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL
RUN npm run build

# Nginx stage
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 4. Nginx-konfiguraatio frontendille

```nginx
# frontend/nginx.conf
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;

        # Gzip compression
        gzip on;
        gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

        # Handle React Router
        location / {
            try_files $uri $uri/ /index.html;
        }

        # Cache static assets
        location /static/ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

---

## 🔧 Palvelimen konfiguraatio

### 1. Nginx reverse proxy

```nginx
# /etc/nginx/sites-available/sales-engagement
server {
    listen 80;
    server_name call.duoai.tech;
    return 301 https://$server_name$request_uri;
}

server {
    listen 80;
    server_name api.call.duoai.tech;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name call.duoai.tech;

    ssl_certificate /etc/letsencrypt/live/call.duoai.tech/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/call.duoai.tech/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 443 ssl http2;
    server_name api.call.duoai.tech;

    ssl_certificate /etc/letsencrypt/live/call.duoai.tech/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/call.duoai.tech/privkey.pem;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### 2. SSL-sertifikaatti (Let's Encrypt)

```bash
# Asenna Certbot
sudo apt install -y certbot python3-certbot-nginx

# Hanki SSL-sertifikaatti
sudo certbot --nginx -d call.duoai.tech -d api.call.duoai.tech

# Automaattinen uusinta
sudo crontab -e
# Lisää rivi:
0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 🔐 Ympäristömuuttujat

### 1. Luo tuotanto .env tiedosto

```bash
# .env.production
# Tietokanta
POSTGRES_PASSWORD=your_super_secure_postgres_password_here

# Redis
REDIS_PASSWORD=your_super_secure_redis_password_here

# JWT
SECRET_KEY=your_super_secure_jwt_secret_key_here_at_least_32_chars

# Twilio (oikeat tuotantoarvot)
TWILIO_ACCOUNT_SID=your_real_twilio_account_sid
TWILIO_AUTH_TOKEN=your_real_twilio_auth_token
TWILIO_PHONE_NUMBER=your_real_twilio_phone_number

# Sovellus
DEBUG=false
BASE_URL=https://api.call.duoai.tech
ALLOWED_ORIGINS=https://call.duoai.tech,https://api.call.duoai.tech

# Tietokanta (tuotanto)
DATABASE_URL=postgresql+asyncpg://sales_user:${POSTGRES_PASSWORD}@postgres:5432/sales_engagement
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
```

### 2. Tietokannan alustus

```sql
-- init.sql
-- Luo Row-Level Security käyttäjä
CREATE USER sales_user WITH PASSWORD 'your_postgres_password';
GRANT ALL PRIVILEGES ON DATABASE sales_engagement TO sales_user;

-- Ota käyttöön RLS
ALTER DATABASE sales_engagement SET row_security = on;
```

---

## 🚀 Käyttöönotto

### 1. Kloonaa projekti palvelimelle

```bash
# Kirjaudu VPS:lle
ssh root@your_vps_ip

# Kloonaa projekti
git clone https://github.com/your-username/sales-engagement-platform.git
cd sales-engagement-platform

# Kopioi tuotanto-asetukset
cp .env.production .env
```

### 2. Käynnistä palvelut

```bash
# Rakenna ja käynnistä kontainerit
docker-compose -f docker-compose.prod.yml up -d --build

# Tarkista että kaikki toimii
docker-compose -f docker-compose.prod.yml ps

# Seuraa lokeja
docker-compose -f docker-compose.prod.yml logs -f
```

### 3. Tietokannan migraatiot

```bash
# Suorita migraatiot
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Luo ensimmäinen admin-käyttäjä (valinnainen)
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.core.database import get_db
from app.services.auth_service import AuthService
import asyncio

async def create_admin():
    async for db in get_db():
        auth_service = AuthService(db)
        await auth_service.create_user({
            'email': 'admin@duoai.tech',
            'password': 'AdminPassword123!',
            'full_name': 'Admin User',
            'company_name': 'Duoai Oy'
        })
        break

asyncio.run(create_admin())
"
```

### 4. Nginx-konfiguraatio

```bash
# Ota käyttöön site
sudo ln -s /etc/nginx/sites-available/sales-engagement /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔍 Testaus ja varmistus

### 1. Testaa palvelut

```bash
# Backend API
curl https://api.call.duoai.tech/health

# Frontend
curl https://call.duoai.tech

# WebSocket (valinnainen)
wscat -c wss://api.call.duoai.tech/ws
```

### 2. Twilio webhook-testaus

```bash
# Testaa Twilio webhook
curl -X POST https://api.call.duoai.tech/api/v1/webhooks/twilio/call-status \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "CallSid=test&CallStatus=completed&From=%2B1234567890&To=%2B0987654321"
```

---

## 📊 Seuranta ja ylläpito

### 1. Lokien seuranta

```bash
# Kaikki palvelut
docker-compose -f docker-compose.prod.yml logs -f

# Vain backend
docker-compose -f docker-compose.prod.yml logs -f backend

# Nginx access log
sudo tail -f /var/log/nginx/access.log
```

### 2. Automaattinen varmuuskopiointi

```bash
# Luo backup-skripti
cat > /root/backup-sales.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/root/backups"
mkdir -p $BACKUP_DIR

# Tietokanta backup
docker-compose -f /root/sales-engagement-platform/docker-compose.prod.yml exec -T postgres pg_dump -U sales_user sales_engagement > $BACKUP_DIR/db_backup_$DATE.sql

# Poista vanhat backupit (yli 7 päivää)
find $BACKUP_DIR -name "db_backup_*.sql" -mtime +7 -delete
EOF

chmod +x /root/backup-sales.sh

# Lisää crontab
echo "0 2 * * * /root/backup-sales.sh" | sudo crontab -
```

### 3. Päivitysprosessi

```bash
# Päivitä sovellus
cd /root/sales-engagement-platform
git pull origin main
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 🎯 Lopputulos

**Kun kaikki on valmis, sinulla on:**

- ✅ **Frontend:** https://call.duoai.tech
- ✅ **Backend API:** https://api.call.duoai.tech
- ✅ **SSL-sertifikaatit** automaattisella uusinnalla
- ✅ **Tietokanta** varmuuskopioinnilla
- ✅ **VoIP-soittotoiminto** täysin toimiva
- ✅ **Skaalautuva arkkitehtuuri** Docker:lla
- ✅ **Turvallinen** tuotantoympäristö

**Sales Engagement Platform on nyt tuotannossa! 🚀**

---

## 🆘 Vianmääritys

### Yleiset ongelmat:

1. **502 Bad Gateway** → Tarkista että kontainerit ovat käynnissä
2. **SSL-virheet** → Varmista että DNS osoittaa oikeaan IP:hen
3. **Tietokantayhteys** → Tarkista salasanat ja verkkoasetukset
4. **Twilio-virheet** → Varmista webhook URL ja tunnukset

### Hyödylliset komennot:

```bash
# Kontainerien tila
docker ps

# Palvelun uudelleenkäynnistys
docker-compose -f docker-compose.prod.yml restart backend

# Tietokannan tila
docker-compose -f docker-compose.prod.yml exec postgres psql -U sales_user -d sales_engagement -c "\dt"
```