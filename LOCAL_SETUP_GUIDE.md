# 🚀 Local Development Setup Guide

**Project**: Decentralized Autonomous Forum  
**Date**: 2025-10-26  
**Status**: ✅ Ready for Local Development

---

## 📋 Prerequisites Check

Before starting, ensure you have:

```bash
# Check Python version (requires 3.11+)
python --version  # Should be 3.11 or higher

# Check if Docker is installed (optional, for Docker setup)
docker --version

# Check if uv is installed
uv --version
```

If you don't have `uv`, install it:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## 🎯 Quick Start (Option 1: Direct Python)

### Step 1: Activate Virtual Environment

```bash
cd /Users/khoo/Downloads/project4/projects/project-20251021-092500-decentralized-forum

# Activate the virtual environment
source .venv/bin/activate  # On Mac/Linux
# or
.venv\Scripts\activate  # On Windows
```

**✅ Virtual environment already exists** at `.venv/`

### Step 2: Start Database Services (Choose One)

#### Option A: Docker Compose (Recommended for First-Time Setup)

```bash
# Start PostgreSQL and Redis using Docker
docker-compose -f docker-compose.dev.yml up -d postgres redis

# Check if services are running
docker ps

# Verify database connection
docker exec -it forum-postgres-dev psql -U forum_user -d decentralized_forum -c "SELECT version();"
```

#### Option B: Native PostgreSQL (If Already Installed)

```bash
# Start PostgreSQL service (macOS with Homebrew)
brew services start postgresql@16

# Or on Linux
sudo systemctl start postgresql

# Create database if doesn't exist
createdb decentralized_forum
```

#### Option C: Supabase/Neon (Cloud Database)

Update `config.local.yaml` with your cloud database URL:
```yaml
database:
  url: "postgresql+asyncpg://user:password@your-supabase-url"
```

### Step 3: Start Redis (If Not Using Docker)

```bash
# macOS with Homebrew
brew install redis
brew services start redis

# Linux
sudo systemctl start redis
```

### Step 4: Run Database Migrations

```bash
# Make sure you're in the project directory
cd /Users/khoo/Downloads/project4/projects/project-20251021-092500-decentralized-forum

# Activate venv
source .venv/bin/activate

# Run migrations
alembic upgrade head
```

### Step 5: (Optional) Seed Development Data

```bash
# Run the seed data script
python scripts/seed_data.py
```

This will create:
- Sample users with different roles
- Sample posts and comments
- Sample channels
- Points economy examples

### Step 6: Start the Development Server

```bash
# Start FastAPI development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Or using the uv shortcut:
```bash
uv run uvicorn src.main:app --reload
```

### Step 7: Access the Application

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **ReDoc API Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 🐳 Docker Setup (Option 2: Everything in Docker)

### Complete Docker Development Environment

This option runs everything (PostgreSQL, Redis, and App) in Docker containers.

```bash
# Start all services (PostgreSQL, Redis, App)
docker-compose -f docker-compose.dev.yml up

# Or run in background
docker-compose -f docker-compose.dev.yml up -d

# Check logs
docker-compose -f docker-compose.dev.yml logs -f app

# Stop all services
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker-compose.dev.yml down -v
```

### Access Points

Once running:
- **Application**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **PgAdmin**: http://localhost:5050 (admin@localhost.com / admin)
- **Redis Commander**: http://localhost:8081
- **Grafana**: http://localhost:3000 (admin / admin)
- **Prometheus**: http://localhost:9090

---

## 🔧 Configuration

### Environment Variables

The project uses `config.yaml` (base config) and `config.local.yaml` (local overrides).

**Key Configuration Values:**

```yaml
# config.local.yaml
database:
  url: "postgresql+asyncpg://forum_user:dev_password_change_in_production@localhost:5432/decentralized_forum"

redis:
  url: "redis://:dev_redis_password@localhost:6379/0"
```

### Required Environment Variables (Optional)

For OAuth2 and blockchain features, set these in your shell:

```bash
# OAuth2 (Optional - only if using social login)
export OAUTH_META_CLIENT_ID="your-meta-client-id"
export OAUTH_META_CLIENT_SECRET="your-meta-client-secret"
export OAUTH_REDDIT_CLIENT_ID="your-reddit-client-id"
export OAUTH_REDDIT_CLIENT_SECRET="your-reddit-client-secret"
export OAUTH_X_CLIENT_ID="your-twitter-client-id"
export OAUTH_X_CLIENT_SECRET="your-twitter-client-secret"
export OAUTH_DISCORD_CLIENT_ID="your-discord-client-id"
export OAUTH_DISCORD_CLIENT_SECRET="your-discord-client-secret"

# IPFS (Optional - only if using file upload)
export IPFS_API_KEY="your-lighthouse-api-key"

# Blockchain (Optional - only if using BNB Chain)
export BLOCKCHAIN_NETWORK="binance_smart_chain_testnet"
export BLOCKCHAIN_RPC_URL="https://data-seed-prebsc-1-s1.binance.org:8545/"
```

**Note**: For local development, these are optional. The app will work without them.

---

## 🧪 Testing

### Run All Tests

```bash
# Run all tests with coverage
pytest

# Run with detailed output
pytest -v

# Run specific test file
pytest tests/unit/test_user_service.py

# Run with coverage report
pytest --cov=src --cov-report=html
```

**Current Status**: ✅ **100% Test Pass Rate** (86/86 tests passing)

### Code Quality Checks

```bash
# Format code with Black
black src tests

# Lint with Ruff
ruff check src tests

# Type check with MyPy
mypy src
```

---

## 📊 Development Tools

### Database Management

```bash
# Start database shell
psql -U forum_user -d decentralized_forum

# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# See current revision
alembic current
```

### Monitoring & Debugging

The Docker setup includes:
- **PgAdmin** (Database GUI): http://localhost:5050
- **Redis Commander** (Redis GUI): http://localhost:8081
- **Prometheus** (Metrics): http://localhost:9090
- **Grafana** (Dashboards): http://localhost:3000

### Redis CLI

```bash
# Connect to Redis
redis-cli -h localhost -p 6379 -a dev_redis_password

# Or from Docker
docker exec -it forum-redis-dev redis-cli
```

---

## 🐛 Troubleshooting

### Issue: "Cannot connect to Docker daemon"

**Solution**: Start Docker Desktop or Docker daemon
```bash
# macOS
open -a Docker

# Linux
sudo systemctl start docker
```

### Issue: "Database connection failed"

**Solutions**:
1. Check if PostgreSQL is running
2. Verify database credentials in `config.local.yaml`
3. Check database exists: `psql -l | grep decentralized_forum`

### Issue: "Port already in use"

**Solutions**:
```bash
# Find process using port 8000
lsof -i :8000
# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn src.main:app --port 8001
```

### Issue: "Module not found" or "Package not installed"

**Solution**: Reinstall dependencies
```bash
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Issue: "Alembic migrations fail"

**Solutions**:
```bash
# Drop and recreate database
dropdb decentralized_forum
createdb decentralized_forum

# Run migrations again
alembic upgrade head
```

---

## 📁 Project Structure

```
project-20251021-092500-decentralized-forum/
├── src/                      # Source code
│   ├── main.py              # FastAPI app entry point
│   ├── api/                  # API routes
│   ├── models/              # SQLAlchemy models
│   ├── services/            # Business logic
│   ├── core/                # Core utilities
│   └── utils/               # Helper functions
├── tests/                    # Test files
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── templates/                # Jinja2 HTML templates
├── static/                   # CSS, JS, images
├── alembic/                  # Database migrations
├── scripts/                  # Utility scripts
├── docs/                     # Documentation
├── config.yaml               # Base configuration
├── config.local.yaml         # Local overrides (gitignored)
└── pyproject.toml           # Python dependencies
```

---

## 🎯 Current Project Status

### Phase: Quality Improvement Initiative (Phase 3 Complete)

- **Quality Score**: 98/100 (Target: 100/100)
- **Progress**: 27% (3/11 quality improvement phases complete)
- **Test Pass Rate**: **100%** (86/86 tests passing) ✅
- **Code Coverage**: 60%
- **Security**: All critical vulnerabilities fixed

### Next Phase: Testing Infrastructure (Phase 4)

Focus areas:
- Set up pytest framework with comprehensive fixtures
- Write unit tests for all services
- Write integration tests for API endpoints
- Configure test database automation
- Set up CI/CD test automation

---

## 🚀 Features Available

### Core Features (Implemented)
✅ User registration and authentication  
✅ Post creation and management  
✅ Comment system  
✅ Like/Unlike functionality  
✅ Points economy  
✅ Channel creation  
✅ User progression levels  
✅ OAuth2 social login (Meta, Reddit, X, Discord, Telegram)  
✅ Blockchain rewards (BNB Chain)  
✅ IPFS file storage  

### Features in Development
🔧 Wiki system  
🔧 Voice sessions  
🔧 Advanced moderation  

---

## 📞 Getting Help

### Documentation
- **README.md**: Setup guide and project overview
- **DEVOPS_SUMMARY.md**: Complete DevOps setup
- **DEVELOPMENT_SUMMARY.md**: Development documentation
- **docs/deployment/**: Deployment guides
- **docs/compliance/**: Legal documentation

### Project Files
- Configuration: `config.yaml`, `config.local.yaml`
- Database: `alembic/`, `database-schema-20251021-190000.sql`
- Architecture: `architecture-20251021-190000.md`
- Requirements: `project-requirements-20251021-092500.md`

---

## ✅ Verification Checklist

Before starting development, verify:

- [x] ✅ Virtual environment exists (`.venv/`)
- [x] ✅ Dependencies installed (105 packages)
- [x] ✅ Local configuration file exists (`config.local.yaml`)
- [ ] ⏳ PostgreSQL database running
- [ ] ⏳ Redis cache running
- [ ] ⏳ Database migrations applied (`alembic upgrade head`)
- [ ] ⏳ Development server starts (`uvicorn src.main:app --reload`)
- [x] ✅ All tests passing (86/86)

---

## 🎉 You're Ready!

Your local development environment is set up and ready. Follow the Quick Start guide above to begin coding.

**Happy Coding! 🚀**
