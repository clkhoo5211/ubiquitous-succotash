# ☁️ Cloud Deployment Guide
**Decentralized Autonomous Forum Platform**
**Version**: 1.0
**Last Updated**: 2025-10-24

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [PostgreSQL Deployment](#postgresql-deployment)
3. [Redis Deployment](#redis-deployment)
4. [Application Deployment](#application-deployment)
5. [Monitoring & Logging](#monitoring--logging)
6. [Domain & SSL Setup](#domain--ssl-setup)
7. [Environment Configuration](#environment-configuration)
8. [Post-Deployment Verification](#post-deployment-verification)

---

## Prerequisites

### Required Accounts
- [ ] Cloud provider account (AWS/Azure/GCP) OR managed service accounts
- [ ] Domain registrar account (Namecheap, Google Domains, Cloudflare)
- [ ] GitHub account (for CI/CD)
- [ ] Email service (SendGrid, Mailgun, AWS SES)

### Required Tools
```bash
# Install required CLI tools
brew install docker docker-compose  # macOS
brew install postgresql redis        # For local testing
brew install kubectl                 # Kubernetes CLI
brew install terraform              # Infrastructure as Code (optional)
```

### Payment Methods
- Cloud infrastructure: ~$50-100/month for production
- Domain: ~$10-15/year
- Email service: Free tier available

---

## 1. PostgreSQL Deployment

Choose ONE of the following PostgreSQL deployment options:

### Option A: Supabase (Recommended - Easy, Free Tier Available)

**Pros**: Free tier, managed backups, auto-scaling, built-in auth
**Cons**: 500MB limit on free tier
**Cost**: Free tier → $25/month Pro

#### Setup Steps:

1. **Create Supabase Account**
   ```bash
   # Visit https://supabase.com
   # Click "Start your project"
   # Sign up with GitHub
   ```

2. **Create New Project**
   ```
   Project Name: decentralized-forum
   Database Password: [GENERATE STRONG PASSWORD - Save to password manager]
   Region: [Choose closest to your users]
   ```

3. **Get Connection Details**
   ```
   Go to Project Settings → Database

   Connection String (URI):
   postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

   Connection Pooling (recommended):
   postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:6543/postgres?pgbouncer=true
   ```

4. **Save to Environment Variables**
   ```bash
   # Add to .env.production
   DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:6543/postgres?pgbouncer=true"
   DATABASE_POOL_SIZE=10
   DATABASE_MAX_OVERFLOW=20
   ```

5. **Enable Extensions**
   ```sql
   -- Run in Supabase SQL Editor
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For full-text search
   CREATE EXTENSION IF NOT EXISTS "unaccent"; -- For search normalization
   ```

---

### Option B: Neon (Recommended - Serverless, Free Tier)

**Pros**: Serverless, instant branching, free tier
**Cons**: 512MB limit on free tier
**Cost**: Free tier → $19/month Pro

#### Setup Steps:

1. **Create Neon Account**
   ```bash
   # Visit https://neon.tech
   # Sign up with GitHub
   ```

2. **Create Project**
   ```
   Project Name: decentralized-forum
   Region: [Choose closest to your users]
   PostgreSQL Version: 16
   ```

3. **Get Connection String**
   ```
   Dashboard → Connection Details

   Connection String:
   postgresql://[user]:[password]@[endpoint].neon.tech/[dbname]?sslmode=require
   ```

4. **Save to Environment**
   ```bash
   # .env.production
   DATABASE_URL="postgresql://[user]:[password]@[endpoint].neon.tech/[dbname]?sslmode=require"
   ```

---

### Option C: Railway (Recommended - All-in-One Platform)

**Pros**: Simple deployment, PostgreSQL + Redis together, $5 trial credit
**Cons**: No permanent free tier
**Cost**: $5 trial → Pay as you go

#### Setup Steps:

1. **Create Railway Account**
   ```bash
   # Visit https://railway.app
   # Sign up with GitHub
   ```

2. **Create New Project**
   ```
   Click "New Project"
   Select "Provision PostgreSQL"
   ```

3. **Get Connection Details**
   ```
   Dashboard → PostgreSQL → Connect

   DATABASE_URL will be auto-generated:
   postgresql://postgres:[password]@[host].railway.app:5432/railway
   ```

4. **Add Redis**
   ```
   Same project → "New" → "Database" → "Add Redis"

   REDIS_URL will be auto-generated:
   redis://default:[password]@[host].railway.app:6379
   ```

---

### Option D: Self-Hosted on Cloud VM (Advanced)

**Pros**: Full control, cost-effective at scale
**Cons**: Requires maintenance, backup management
**Cost**: ~$20-40/month for VM

#### AWS EC2 Setup:

```bash
# 1. Launch EC2 instance (t3.medium, 2 vCPU, 4GB RAM)
# 2. SSH into instance
ssh -i your-key.pem ubuntu@ec2-xx-xx-xx-xx.compute.amazonaws.com

# 3. Install PostgreSQL 16
sudo apt update
sudo apt install -y postgresql-16 postgresql-contrib-16

# 4. Configure PostgreSQL
sudo -u postgres psql
CREATE DATABASE decentralized_forum;
CREATE USER forum_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE decentralized_forum TO forum_user;
\q

# 5. Configure remote access
sudo nano /etc/postgresql/16/main/postgresql.conf
# Set: listen_addresses = '*'

sudo nano /etc/postgresql/16/main/pg_hba.conf
# Add: host all all 0.0.0.0/0 md5

sudo systemctl restart postgresql

# 6. Configure firewall
sudo ufw allow 5432/tcp

# 7. Connection string
postgresql://forum_user:your_secure_password@ec2-xx-xx-xx-xx.compute.amazonaws.com:5432/decentralized_forum
```

---

## 2. Redis Deployment

Choose ONE of the following Redis deployment options:

### Option A: Upstash (Recommended - Serverless, Free Tier)

**Pros**: Free tier (10k commands/day), serverless, global
**Cons**: Free tier limits
**Cost**: Free tier → $10/month Pro

#### Setup Steps:

1. **Create Upstash Account**
   ```bash
   # Visit https://upstash.com
   # Sign up with GitHub
   ```

2. **Create Redis Database**
   ```
   Click "Create Database"
   Name: decentralized-forum-cache
   Region: [Choose closest to your users]
   Type: Regional (or Global for multi-region)
   ```

3. **Get Connection Details**
   ```
   Database → Details

   Redis URL:
   redis://default:[password]@[endpoint].upstash.io:6379

   Or REST API (serverless):
   https://[endpoint].upstash.io
   ```

4. **Save to Environment**
   ```bash
   # .env.production
   REDIS_URL="redis://default:[password]@[endpoint].upstash.io:6379"
   ```

---

### Option B: Railway (If using for PostgreSQL too)

**Pros**: All-in-one with PostgreSQL
**Cons**: No permanent free tier
**Cost**: Included in Railway usage

#### Setup Steps:

1. **Add Redis to Existing Project**
   ```
   Railway Dashboard → Your Project
   Click "New" → "Database" → "Add Redis"
   ```

2. **Get Connection String**
   ```
   Automatically provisioned:
   redis://default:[password]@redis.railway.internal:6379
   ```

---

### Option C: Redis Cloud (Managed by Redis Labs)

**Pros**: Official Redis hosting, free 30MB tier
**Cons**: Small free tier
**Cost**: Free tier → $7/month Basic

#### Setup Steps:

1. **Create Account**
   ```bash
   # Visit https://redis.com/try-free/
   # Sign up
   ```

2. **Create Database**
   ```
   Click "New Database"
   Database Name: forum-cache
   Cloud Provider: AWS/GCP/Azure
   Region: [Choose closest]
   Memory: 30MB (free) or more
   ```

3. **Get Connection String**
   ```
   redis://default:[password]@redis-[id].c[xxx].cloud.redislabs.com:6379
   ```

---

## 3. Application Deployment

Choose ONE deployment platform:

### Option A: Railway (Recommended - Easiest)

#### Setup Steps:

1. **Connect GitHub Repository**
   ```bash
   Railway Dashboard → New Project
   → "Deploy from GitHub repo"
   → Select your repository
   ```

2. **Configure Build Settings**
   ```
   Root Directory: /
   Build Command: docker build -t app .
   Start Command: uvicorn src.main:app --host 0.0.0.0 --port $PORT
   ```

3. **Add Environment Variables**
   ```bash
   # In Railway Dashboard → Variables
   APP_SECRET_KEY=[generate with: openssl rand -hex 32]
   SECURITY_JWT_SECRET_KEY=[generate with: openssl rand -hex 32]
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   REDIS_URL=${{Redis.REDIS_URL}}
   ENVIRONMENT=production
   DEBUG=false
   ```

4. **Deploy**
   ```
   Railway will auto-deploy on git push
   ```

---

### Option B: Docker on Cloud VM (AWS EC2, Google Compute, Azure VM)

#### AWS EC2 Setup:

```bash
# 1. Launch EC2 instance (t3.medium or larger)
# 2. SSH into instance
ssh -i your-key.pem ubuntu@ec2-xx-xx-xx-xx.compute.amazonaws.com

# 3. Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# 4. Clone repository
git clone https://github.com/yourusername/decentralized-forum.git
cd decentralized-forum

# 5. Create .env.production file
nano .env.production
# Add all environment variables (see Environment Configuration section)

# 6. Build and run with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# 7. Check logs
docker-compose logs -f app

# 8. Configure Nginx reverse proxy (optional)
sudo apt install -y nginx
sudo nano /etc/nginx/sites-available/forum
# Add configuration (see Nginx section below)
```

---

### Option C: Kubernetes (Advanced - For Production Scale)

#### Prerequisites:
```bash
# Install kubectl and helm
brew install kubectl helm

# Create cluster (example with GKE)
gcloud container clusters create forum-cluster \
  --num-nodes=3 \
  --machine-type=e2-medium \
  --region=us-central1
```

#### Deployment:

```bash
# 1. Create namespace
kubectl create namespace forum

# 2. Create secrets
kubectl create secret generic forum-secrets \
  --from-literal=app-secret-key=[YOUR_KEY] \
  --from-literal=jwt-secret-key=[YOUR_KEY] \
  --from-literal=database-url=[DB_URL] \
  --from-literal=redis-url=[REDIS_URL] \
  -n forum

# 3. Apply Kubernetes manifests
kubectl apply -f kubernetes/ -n forum

# 4. Check deployment
kubectl get pods -n forum
kubectl get services -n forum

# 5. Get external IP
kubectl get service forum-app -n forum
```

---

## 4. Monitoring & Logging

### Option A: Grafana Cloud (Free Tier Available)

#### Setup Steps:

1. **Create Grafana Cloud Account**
   ```bash
   # Visit https://grafana.com/auth/sign-up/create-user
   # Sign up
   ```

2. **Get Prometheus Endpoint**
   ```
   Stack Details → Prometheus
   Remote Write Endpoint: https://prometheus-[xxx].grafana.net/api/prom/push
   Username: [your-user-id]
   Password: [API key]
   ```

3. **Configure Application to Send Metrics**
   ```python
   # Add to src/main.py
   from prometheus_client import make_asgi_app, Counter, Histogram

   # Add Prometheus metrics endpoint
   metrics_app = make_asgi_app()
   app.mount("/metrics", metrics_app)
   ```

4. **Install Grafana Agent**
   ```bash
   # On your application server
   wget https://github.com/grafana/agent/releases/latest/download/agent-linux-amd64.zip
   unzip agent-linux-amd64.zip
   chmod +x agent-linux-amd64

   # Configure agent
   nano agent-config.yaml
   # Add Prometheus scrape config pointing to your app

   # Run agent
   ./agent-linux-amd64 -config.file=agent-config.yaml
   ```

---

### Option B: Self-Hosted Prometheus + Grafana

```bash
# docker-compose-monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus_data:
  grafana_data:
```

---

## 5. Domain & SSL Setup

### Step 1: Purchase Domain

```bash
# Recommended registrars:
# - Namecheap: ~$10/year
# - Google Domains: ~$12/year
# - Cloudflare: ~$10/year (includes CDN)
```

### Step 2: Configure DNS

```bash
# Add A record pointing to your server IP
Type: A
Name: @
Value: [Your server IP or load balancer IP]
TTL: 3600

# Add www subdomain
Type: CNAME
Name: www
Value: yourdomain.com
TTL: 3600
```

### Step 3: SSL with Let's Encrypt (Free)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (certbot sets this up automatically)
sudo certbot renew --dry-run
```

---

## 6. Environment Configuration

### Complete .env.production Template

```bash
# Application Settings
APP_NAME="Decentralized Autonomous Forum"
APP_SECRET_KEY="[GENERATE: openssl rand -hex 32]"
ENVIRONMENT="production"
DEBUG="false"
ALLOWED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"

# Database
DATABASE_URL="postgresql://user:pass@host:5432/dbname"
DATABASE_POOL_SIZE="10"
DATABASE_MAX_OVERFLOW="20"
DATABASE_ECHO="false"

# Redis
REDIS_URL="redis://default:pass@host:6379"

# Security & JWT
SECURITY_JWT_SECRET_KEY="[GENERATE: openssl rand -hex 32]"
SECURITY_JWT_ALGORITHM="HS256"
SECURITY_JWT_EXPIRATION_HOURS="24"
SECURITY_SESSION_EXPIRATION_HOURS="168"
SECURITY_BCRYPT_ROUNDS="12"

# OAuth2 Providers (configure in respective developer consoles)
# Meta/Facebook
OAUTH_META_CLIENT_ID="your_meta_client_id"
OAUTH_META_CLIENT_SECRET="your_meta_client_secret"
OAUTH_META_REDIRECT_URI="https://yourdomain.com/api/v1/auth/oauth/meta/callback"

# Reddit
OAUTH_REDDIT_CLIENT_ID="your_reddit_client_id"
OAUTH_REDDIT_CLIENT_SECRET="your_reddit_client_secret"
OAUTH_REDDIT_REDIRECT_URI="https://yourdomain.com/api/v1/auth/oauth/reddit/callback"

# X/Twitter
OAUTH_X_CLIENT_ID="your_x_client_id"
OAUTH_X_CLIENT_SECRET="your_x_client_secret"
OAUTH_X_REDIRECT_URI="https://yourdomain.com/api/v1/auth/oauth/x/callback"

# Discord
OAUTH_DISCORD_CLIENT_ID="your_discord_client_id"
OAUTH_DISCORD_CLIENT_SECRET="your_discord_client_secret"
OAUTH_DISCORD_REDIRECT_URI="https://yourdomain.com/api/v1/auth/oauth/discord/callback"

# Telegram
OAUTH_TELEGRAM_BOT_TOKEN="your_telegram_bot_token"

# IPFS (Lighthouse)
IPFS_API_KEY="your_lighthouse_api_key"
IPFS_GATEWAY_URL="https://gateway.lighthouse.storage"

# Blockchain (BNB Chain)
BLOCKCHAIN_NETWORK="binance_smart_chain"
BLOCKCHAIN_RPC_URL="https://bsc-dataseed.binance.org/"
BLOCKCHAIN_CHAIN_ID="56"

# PayPal
PAYPAL_MODE="live"  # or "sandbox" for testing
PAYPAL_CLIENT_ID="your_paypal_client_id"
PAYPAL_CLIENT_SECRET="your_paypal_client_secret"

# Email (SendGrid example)
EMAIL_PROVIDER="sendgrid"
SENDGRID_API_KEY="your_sendgrid_api_key"
EMAIL_FROM="noreply@yourdomain.com"

# Monitoring
SENTRY_DSN="https://[key]@[org].ingest.sentry.io/[project]"  # Optional

# Rate Limiting
RATE_LIMIT_ENABLED="true"
```

---

## 7. Post-Deployment Verification

### Checklist

```bash
# 1. Health check
curl https://yourdomain.com/health
# Expected: {"status": "healthy"}

# 2. Database connectivity
curl https://yourdomain.com/api/v1/health/database
# Expected: {"database": "connected"}

# 3. Redis connectivity
curl https://yourdomain.com/api/v1/health/redis
# Expected: {"redis": "connected"}

# 4. API endpoints
curl https://yourdomain.com/api/v1/auth/register \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"TestPass123!"}'

# 5. SSL certificate
curl -I https://yourdomain.com | grep -i "strict-transport-security"
# Expected: strict-transport-security header present

# 6. Security headers
curl -I https://yourdomain.com | grep -E "(X-Frame-Options|X-Content-Type-Options|Content-Security-Policy)"

# 7. Rate limiting
for i in {1..6}; do curl -X POST https://yourdomain.com/api/v1/auth/register; done
# Expected: 6th request returns 429 Too Many Requests
```

---

## 8. Deployment Scripts

### deploy.sh (Complete Deployment Script)

```bash
#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# 1. Build Docker image
echo "📦 Building Docker image..."
docker build -t decentralized-forum:latest .

# 2. Tag for registry
echo "🏷️  Tagging image..."
docker tag decentralized-forum:latest registry.yourdomain.com/forum:latest

# 3. Push to registry
echo "⬆️  Pushing to registry..."
docker push registry.yourdomain.com/forum:latest

# 4. Update deployment
echo "🔄 Updating deployment..."
kubectl set image deployment/forum-app forum=registry.yourdomain.com/forum:latest -n forum

# 5. Wait for rollout
echo "⏳ Waiting for rollout..."
kubectl rollout status deployment/forum-app -n forum

# 6. Run database migrations
echo "🗄️  Running migrations..."
kubectl exec -it deployment/forum-app -n forum -- alembic upgrade head

# 7. Verify deployment
echo "✅ Verifying deployment..."
curl -f https://yourdomain.com/health || (echo "❌ Health check failed" && exit 1)

echo "✅ Deployment complete!"
```

---

## 9. Cost Estimation

### Free Tier Setup (Suitable for MVP/Testing)

| Service | Provider | Free Tier | Cost After |
|---------|----------|-----------|------------|
| PostgreSQL | Supabase | 500MB | $25/month |
| Redis | Upstash | 10k cmds/day | $10/month |
| Application | Railway | $5 credit | Pay-as-go |
| Monitoring | Grafana Cloud | 10k series | $49/month |
| Domain | Namecheap | - | $10/year |
| SSL | Let's Encrypt | Free forever | Free |
| **Total** | | **~$5 one-time** | **~$45/month** |

### Production Setup (Recommended for Launch)

| Service | Provider | Tier | Monthly Cost |
|---------|----------|------|--------------|
| PostgreSQL | Supabase Pro | 8GB | $25 |
| Redis | Upstash Pro | 1GB | $10 |
| Application | AWS EC2 | t3.medium | $30 |
| Load Balancer | AWS ALB | - | $20 |
| CDN | Cloudflare | Pro | $20 |
| Monitoring | Grafana Cloud | Pro | $49 |
| Email | SendGrid | Essentials | $20 |
| Domain | Namecheap | - | $1 |
| **Total** | | | **~$175/month** |

---

## 10. Troubleshooting

### Common Issues

#### Database Connection Failed
```bash
# Check database URL format
echo $DATABASE_URL
# Should be: postgresql://user:pass@host:port/db

# Test connection
psql $DATABASE_URL
```

#### Redis Connection Failed
```bash
# Check Redis URL
echo $REDIS_URL
# Should be: redis://default:pass@host:port

# Test connection
redis-cli -u $REDIS_URL ping
# Expected: PONG
```

#### Application Won't Start
```bash
# Check logs
docker logs [container-id]
# or
kubectl logs deployment/forum-app -n forum

# Common issues:
# - Missing environment variables
# - Database migrations not run
# - Port conflicts
```

---

## 11. Next Steps After Deployment

1. ✅ Run database migrations: `alembic upgrade head`
2. ✅ Seed initial data (user levels, point economy)
3. ✅ Configure OAuth2 apps (Meta, Reddit, X, Discord, Telegram)
4. ✅ Set up monitoring dashboards
5. ✅ Configure alerts (uptime, errors, performance)
6. ✅ Enable backups (database, Redis)
7. ✅ Set up CI/CD (auto-deploy on git push)
8. ✅ Load testing (ensure 1000+ concurrent users)
9. ✅ Security audit (penetration testing)
10. ✅ Launch! 🚀

---

**Deployment Guide Complete**
**Last Updated**: 2025-10-24
**Questions?** Check the troubleshooting section or project documentation.
