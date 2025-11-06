# Deployment Guide

This FastAPI application **cannot be deployed to GitHub Pages** because GitHub Pages only supports static sites. This application requires:
- Python runtime (FastAPI)
- PostgreSQL database
- Redis cache
- Server-side rendering (Jinja2 templates)

## Deployment Options

### Option 1: Railway (Recommended - Easiest)

1. **Sign up**: Go to [railway.app](https://railway.app) and connect your GitHub account
2. **Create Project**: Click "New Project" → "Deploy from GitHub repo"
3. **Select Repository**: Choose `ubiquitous-succotash`
4. **Configure Environment Variables**:
   - `DATABASE_URL`: Your PostgreSQL connection string
   - `REDIS_URL`: Your Redis connection string
   - `SECRET_KEY`: Generate with `openssl rand -hex 32`
   - Add other required vars from `config.local.yaml.example`

5. **Deploy**: Railway will automatically detect the Dockerfile and deploy

### Option 2: Render

1. **Sign up**: Go to [render.com](https://render.com)
2. **Create Web Service**: New → Web Service → Connect GitHub repo
3. **Settings**:
   - Build Command: `pip install -r requirements.txt` (or use Docker)
   - Start Command: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
   - Environment: Docker (recommended)
4. **Add Environment Variables**: Same as Railway
5. **Deploy**: Render will auto-deploy on push to main

### Option 3: Fly.io

1. **Install Fly CLI**: `curl -L https://fly.io/install.sh | sh`
2. **Login**: `fly auth login`
3. **Create App**: `fly launch` (follow prompts)
4. **Set Secrets**: `fly secrets set DATABASE_URL=... REDIS_URL=...`
5. **Deploy**: `fly deploy`

### Option 4: Vercel (Serverless Functions)

1. **Install Vercel CLI**: `npm i -g vercel`
2. **Create `vercel.json`**:
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "src/main.py",
         "use": "@vercel/python"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "src/main.py"
       }
     ]
   }
   ```
3. **Deploy**: `vercel --prod`

## GitHub Actions Auto-Deployment

The repository includes `.github/workflows/deploy.yml` that will:
- Build Docker image on push to `main`
- Push to DockerHub (if credentials configured)
- Deploy to Railway/Render (if tokens configured)

### Required Secrets

Add these in GitHub → Settings → Secrets → Actions:

**For Railway:**
- `RAILWAY_TOKEN`: Your Railway API token
- `RAILWAY_SERVICE_ID`: Your Railway service ID

**For Render:**
- `RENDER_API_KEY`: Your Render API key
- `RENDER_SERVICE_ID`: Your Render service ID

**For DockerHub:**
- `DOCKERHUB_USERNAME`: Your DockerHub username
- `DOCKERHUB_TOKEN`: Your DockerHub access token

## Documentation Site (GitHub Pages)

The `.github/workflows/docs.yml` workflow will automatically deploy documentation to GitHub Pages at:
`https://clkhoo5211.github.io/ubiquitous-succotash/`

This hosts static documentation only, not the application itself.

## Manual Deployment Steps

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/clkhoo5211/ubiquitous-succotash.git
   git push -u origin main
   ```

2. **Set up hosting service** (Railway/Render/Fly.io)

3. **Configure environment variables** in hosting dashboard

4. **Deploy** - service will auto-deploy on git push

## Database Setup

Before deploying, ensure you have:
- PostgreSQL database (Supabase, Neon, or Railway PostgreSQL)
- Redis instance (Railway Redis, Upstash, or Redis Cloud)
- Environment variables configured

## Post-Deployment

1. Run migrations: The app should auto-run migrations on startup
2. Check health endpoint: `https://your-app.com/health`
3. Verify database connection
4. Test authentication endpoints

## Troubleshooting

- **Database connection errors**: Check `DATABASE_URL` format
- **Redis connection errors**: Verify `REDIS_URL` is accessible
- **Port binding**: Ensure app listens on `0.0.0.0:$PORT` (not `localhost`)
- **Static files**: Verify `static/` and `templates/` are included in Docker image

