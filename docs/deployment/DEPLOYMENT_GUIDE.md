# 🚀 Deployment Guide - Decentralized Forum

Your forum is ready to deploy! Here are your options:

## Quick Deploy Options

### Option 1: Vercel (Easiest - 5 minutes)

**Perfect for:** Production-ready deployment with automatic scaling

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Deploy:**
   ```bash
   cd /Users/khoo/Downloads/project4/projects/project-20251021-092500-decentralized-forum
   vercel
   ```

3. **Set Environment Variables in Vercel Dashboard:**
   - `APP_SECRET_KEY`
   - `SECURITY_JWT_SECRET_KEY`
   - `DATABASE_URL` (Use Supabase free tier)
   - `REDIS_URL` (Use Upstash free tier)
   - `IPFS_API_KEY`

4. **Done!** Your forum will be live at: `https://your-project.vercel.app`

---

### Option 2: Railway (Database Included)

**Perfect for:** All-in-one solution with PostgreSQL + Redis included

1. **Connect to GitHub:**
   - Go to https://railway.app/
   - Click "Deploy from GitHub repo"
   - Select your repository

2. **Add PostgreSQL + Redis:**
   - In your project, click "New"
   - Add PostgreSQL
   - Add Redis

3. **Set Environment Variables:**
   - Railway auto-sets `DATABASE_URL` and `REDIS_URL`
   - Add your other secrets manually

4. **Done!** Auto-deploys on every push

---

### Option 3: Render (Free Tier Available)

**Perfect for:** Simple deployment with free PostgreSQL

1. **Create Web Service:**
   - Go to https://render.com/
   - Click "New +"
   - Select "Web Service"
   - Connect your GitHub repo

2. **Configure:**
   - Build Command: `pip install -e .`
   - Start Command: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`

3. **Add Database:**
   - Create PostgreSQL instance
   - Add Redis (external like Upstash)

---

## Local Development (Test Locally First)

```bash
cd /Users/khoo/Downloads/project4/projects/project-20251021-092500-decentralized-forum

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Set environment variables
export APP_SECRET_KEY=your-secret-key-min-32-chars
export SECURITY_JWT_SECRET_KEY=your-jwt-secret-min-32-chars
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/forum
export REDIS_URL=redis://localhost:6379/0
export IPFS_API_KEY=your-ipfs-key

# Run migrations
alembic upgrade head

# Start server
uvicorn src.main:app --reload
```

**Visit:** http://localhost:8000

You'll see:
- ✅ Beautiful forum homepage
- ✅ User registration/login
- ✅ Post creation/comments
- ✅ Points system
- ✅ Crypto rewards
- ✅ All the UI you saw in the templates!

---

## Free Database Options

### PostgreSQL (Choose One):
- **Supabase** - https://supabase.com (500MB free)
- **Neon** - https://neon.tech (3GB free)
- **Railway** - Included in their free tier

### Redis (Choose One):
- **Upstash** - https://upstash.com (10K commands/day free)
- **Redis Cloud** - https://redis.com/try-free (30MB free)

---

## Why GitHub Pages Doesn't Work

GitHub Pages **cannot** host your forum because:

| Requirement | GitHub Pages | Vercel/Railway/Render |
|-------------|--------------|----------------------|
| Static HTML | ✅ Yes | ✅ Yes |
| Python Backend | ❌ No | ✅ Yes |
| Database | ❌ No | ✅ Yes |
| Server-Side Rendering | ❌ No | ✅ Yes |
| Dynamic Content | ❌ No | ✅ Yes |

**Your forum needs:**
- Python/FastAPI running 24/7
- PostgreSQL database
- Redis cache
- Server-side rendering (Jinja2)

**GitHub Pages only serves:**
- Pre-built HTML files
- No server, no database
- Only documentation sites

---

## Quick Start - Deploy in 5 Minutes

```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. Deploy
cd /Users/khoo/Downloads/project4/projects/project-20251021-092500-decentralized-forum
vercel

# 3. Set up free databases:
# - Supabase for PostgreSQL: https://supabase.com
# - Upstash for Redis: https://upstash.com

# 4. Add environment variables in Vercel dashboard

# 5. Done! Your forum is live! 🎉
```

---

## What You'll Get

Once deployed, your forum will have:

✅ **Full UI** - All the templates you have (index.html, posts, profiles, etc.)  
✅ **User System** - Registration, login, OAuth  
✅ **Points Economy** - Earn/spend points  
✅ **Crypto Rewards** - BNB Chain integration  
✅ **Forums** - Create posts, comment, like  
✅ **Gamification** - Level up system  
✅ **Leaderboards** - Top contributors  
✅ **Beautiful Design** - Your 3000+ lines of CSS!  

---

## Need Help?

If you get stuck deploying, I can:
1. Help you set up Vercel/Railway
2. Configure environment variables
3. Set up free databases
4. Debug deployment issues

Just ask! 🚀

