# AuraCRM — Infrastructure Guide

## Deployment Options

### Option 1: Frappe Cloud (Recommended)

Frappe Cloud provides managed hosting with automatic updates, backups, and monitoring.

```
1. Create account at frappecloud.com
2. Create new site
3. Install apps: frappe, erpnext, auracrm
4. Configure AuraCRM Settings
5. License auto-detected — Premium features enabled
```

**Specs (Recommended)**:
- Plan: $25/month minimum
- MariaDB included
- Redis included
- Automatic SSL
- Daily backups

### Option 2: Self-Hosted (Docker)

```yaml
# docker-compose.yml (simplified)
version: "3"
services:
  frappe:
    image: frappe/bench:latest
    volumes:
      - sites:/home/frappe/frappe-bench/sites
    ports:
      - "8080:8080"
    
  mariadb:
    image: mariadb:10.11
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
    volumes:
      - db-data:/var/lib/mysql
  
  redis-cache:
    image: redis:7-alpine
  
  redis-queue:
    image: redis:7-alpine
```

### Option 3: Self-Hosted (Bare Metal)

```bash
# Ubuntu 22.04 LTS
sudo apt update && sudo apt upgrade -y
sudo apt install python3.11 python3.11-venv nodejs npm redis-server mariadb-server

# Install bench
pip3 install frappe-bench
bench init frappe-bench --frappe-branch version-16
cd frappe-bench

# Install apps
bench get-app erpnext --branch version-16
bench get-app auracrm --branch main
bench new-site mysite.com
bench --site mysite.com install-app erpnext
bench --site mysite.com install-app auracrm

# Production setup
sudo bench setup production $USER
```

## System Requirements

### Minimum (< 50 users)

| Resource | Spec |
|----------|------|
| CPU | 2 vCPU |
| RAM | 4 GB |
| Storage | 40 GB SSD |
| OS | Ubuntu 22.04 LTS |
| Database | MariaDB 10.6+ |
| Python | 3.10+ |
| Node.js | 18+ |

### Recommended (50–500 users)

| Resource | Spec |
|----------|------|
| CPU | 4 vCPU |
| RAM | 8 GB |
| Storage | 100 GB SSD |
| Database | MariaDB 10.11 |
| Redis | 6+ (dedicated instance) |

### Enterprise (500+ users)

| Resource | Spec |
|----------|------|
| CPU | 8+ vCPU |
| RAM | 16+ GB |
| Storage | 250+ GB SSD (NVMe preferred) |
| Database | MariaDB cluster or RDS |
| Redis | Dedicated cluster |
| Load Balancer | Nginx / HAProxy |

## Network Architecture

```
Internet → Nginx (SSL termination)
             ├── Frappe Web (Gunicorn, port 8000)
             └── Socket.IO (port 9000)

Internal:
  Frappe ←→ MariaDB (port 3306)
  Frappe ←→ Redis Cache (port 13000)
  Frappe ←→ Redis Queue (port 11000)
  Workers ←→ Redis Queue
```

## External Service Dependencies

| Service | Required | Purpose |
|---------|----------|---------|
| MariaDB | ✅ Yes | Primary database |
| Redis | ✅ Yes | Cache + job queue |
| SMTP Server | ⚠️ Optional | Email sending |
| OpenAI / Anthropic | ⚠️ Optional | AI engines (Premium) |
| OSINT APIs | ⚠️ Optional | Intelligence (Premium) |
| WhatsApp Cloud API | ⚠️ Optional | WhatsApp integration |
| Social APIs | ⚠️ Optional | Social publishing |

## SSL Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name crm.example.com;
    
    ssl_certificate /etc/letsencrypt/live/crm.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/crm.example.com/privkey.pem;
    
    # Frappe upstream
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /socket.io {
        proxy_pass http://127.0.0.1:9000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Backup Strategy

```bash
# Daily backup (add to crontab)
0 2 * * * cd /home/frappe/frappe-bench && bench --site mysite.com backup --with-files

# Backup to S3
bench --site mysite.com backup --with-files
aws s3 cp sites/mysite.com/private/backups/ s3://my-backups/ --recursive
```
