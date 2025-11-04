# 🐳 Local Development Guide
**Decentralized Autonomous Forum - Local Docker Setup**

---

## Quick Start

### Prerequisites
- Docker Desktop installed
- Docker Compose installed
- 8GB+ RAM available
- 10GB+ disk space

### Start Everything
```bash
# Start all services (PostgreSQL, Redis, App, Prometheus, Grafana)
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f app

# Stop everything
docker-compose -f docker-compose.dev.yml down
```

### Access Services
- **Application**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **PgAdmin**: http://localhost:5050 (admin@localhost.com/admin)
- **Redis Commander**: http://localhost:8081

---

## Detailed Setup

### 1. First Time Setup

```bash
# Clone repository (if not already done)
cd /Users/khoo/Downloads/project4/projects/project-20251021-092500-decentralized-forum

# Build and start services
docker-compose -f docker-compose.dev.yml up --build -d

# Wait for services to be healthy (30-60 seconds)
docker-compose -f docker-compose.dev.yml ps

# Check application health
curl http://localhost:8000/health
```

### 2. Database Migrations

```bash
# Migrations run automatically on startup
# To run manually:
docker-compose -f docker-compose.dev.yml exec app alembic upgrade head

# Create new migration
docker-compose -f docker-compose.dev.yml exec app alembic revision --autogenerate -m "description"

# Rollback migration
docker-compose -f docker-compose.dev.yml exec app alembic downgrade -1
```

### 3. Seed Data

```bash
# Seed initial data (runs automatically on first startup)
docker-compose -f docker-compose.dev.yml exec app python -m src.scripts.seed_data

# Clear and re-seed
docker-compose -f docker-compose.dev.yml exec app python -m src.scripts.reset_data
```

---

## Service Details

### PostgreSQL
- **Host**: localhost
- **Port**: 5432
- **Database**: decentralized_forum
- **User**: forum_user
- **Password**: dev_password_change_in_production

**Connect via psql**:
```bash
docker-compose -f docker-compose.dev.yml exec postgres psql -U forum_user -d decentralized_forum
```

### Redis
- **Host**: localhost
- **Port**: 6379
- **Password**: dev_redis_password

**Connect via redis-cli**:
```bash
docker-compose -f docker-compose.dev.yml exec redis redis-cli -a dev_redis_password
```

### Application
- **Host**: localhost
- **Port**: 8000
- **Environment**: development
- **Debug**: enabled
- **Hot Reload**: enabled

---

## Development Workflow

### Making Code Changes

```bash
# Code changes are automatically detected (hot reload)
# Just edit files in your IDE

# If you need to restart the app manually:
docker-compose -f docker-compose.dev.yml restart app
```

### Running Tests

```bash
# Run all tests
docker-compose -f docker-compose.dev.yml exec app pytest

# Run with coverage
docker-compose -f docker-compose.dev.yml exec app pytest --cov=src --cov-report=html

# Run specific test file
docker-compose -f docker-compose.dev.yml exec app pytest tests/unit/test_security.py

# Run with output
docker-compose -f docker-compose.dev.yml exec app pytest -v -s
```

### Code Quality Checks

```bash
# Format code with Black
docker-compose -f docker-compose.dev.yml exec app black src/ tests/

# Lint with Ruff
docker-compose -f docker-compose.dev.yml exec app ruff check src/ tests/

# Type checking with MyPy
docker-compose -f docker-compose.dev.yml exec app mypy src/
```

---

## Monitoring & Debugging

### View Logs

```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f app
docker-compose -f docker-compose.dev.yml logs -f postgres
docker-compose -f docker-compose.dev.yml logs -f redis

# Last 100 lines
docker-compose -f docker-compose.dev.yml logs --tail=100 app
```

### Database Management (PgAdmin)

1. Open http://localhost:5050
2. Login: admin@localhost.com / admin
3. Add server:
   - Name: Forum Dev
   - Host: postgres
   - Port: 5432
   - Database: decentralized_forum
   - Username: forum_user
   - Password: dev_password_change_in_production

### Redis Management (Redis Commander)

1. Open http://localhost:8081
2. Browse keys, run commands, view stats

### Metrics & Monitoring (Grafana)

1. Open http://localhost:3000
2. Login: admin / admin
3. Explore dashboards (auto-provisioned)
4. Query metrics from Prometheus

---

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
lsof -i :8000  # or :5432, :6379, etc.

# Kill the process
kill -9 [PID]

# Or change port in docker-compose.dev.yml
```

### Database Connection Failed

```bash
# Check if PostgreSQL is running
docker-compose -f docker-compose.dev.yml ps postgres

# Check logs
docker-compose -f docker-compose.dev.yml logs postgres

# Restart PostgreSQL
docker-compose -f docker-compose.dev.yml restart postgres
```

### Redis Connection Failed

```bash
# Check if Redis is running
docker-compose -f docker-compose.dev.yml ps redis

# Test connection
docker-compose -f docker-compose.dev.yml exec redis redis-cli -a dev_redis_password ping
# Expected: PONG
```

### Application Won't Start

```bash
# Check logs
docker-compose -f docker-compose.dev.yml logs app

# Common issues:
# - Database not ready → Wait 30-60 seconds
# - Port conflict → Change port in docker-compose.dev.yml
# - Missing dependencies → Rebuild: docker-compose -f docker-compose.dev.yml up --build
```

### Clean Slate (Nuclear Option)

```bash
# Stop and remove everything (including volumes)
docker-compose -f docker-compose.dev.yml down -v

# Remove images
docker-compose -f docker-compose.dev.yml down --rmi all

# Start fresh
docker-compose -f docker-compose.dev.yml up --build
```

---

## Performance Tips

### Speed Up Startup

```bash
# Don't rebuild if code hasn't changed
docker-compose -f docker-compose.dev.yml up -d

# Start only essential services
docker-compose -f docker-compose.dev.yml up -d postgres redis app
```

### Reduce Resource Usage

```bash
# Edit docker-compose.dev.yml and add resource limits:
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

---

## Next Steps

1. ✅ Services running
2. ✅ Database migrations complete
3. ✅ Initial data seeded
4. 🔨 Start development!

### Start Developing

```bash
# Create new API endpoint
# Edit: src/api/routes/posts.py

# Create database model
# Edit: src/models/content.py

# Write tests
# Edit: tests/integration/test_posts_api.py

# Run tests
docker-compose -f docker-compose.dev.yml exec app pytest
```

---

**Local Development Environment Ready!** 🎉
**Happy Coding!** 🚀
