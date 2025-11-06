# 🚀 Vercel Deployment - Step by Step Guide

## What You Need (All Free!):
1. ✅ Vercel account (free)
2. ✅ Supabase account (free PostgreSQL)
3. ✅ Upstash account (free Redis)

---

## Step 1: Create Free Accounts (5 minutes)

### A. Vercel (Hosting)
1. Go to https://vercel.com/signup
2. Sign up with GitHub (easiest)
3. That's it! ✅

### B. Supabase (PostgreSQL Database)
1. Go to https://supabase.com/
2. Click "Start your project"
3. Sign in with GitHub
4. Click "New project"
5. Fill in:
   - Name: `decentralized-forum`
   - Database Password: (save this!)
   - Region: Choose closest to you
6. Wait 2 minutes for setup
7. Go to **Settings** → **Database**
8. Copy **Connection string** (URI format)
   - Example: `postgresql://postgres.xxx:password@aws-0-region.pooler.supabase.com:6543/postgres`
9. Change `postgresql://` to `postgresql+asyncpg://` (important!)
10. Save this URL! ✅

### C. Upstash (Redis Cache)
1. Go to https://upstash.com/
2. Sign in with GitHub
3. Click "Create Database"
4. Choose:
   - Name: `forum-cache`
   - Type: Regional
   - Region: Choose closest to you
5. Click "Create"
6. Go to **Details** tab
7. Copy **REST URL** (looks like `https://xxx.upstash.io`)
8. Copy **REST Token**
9. Your Redis URL format: `redis://default:{REST_TOKEN}@{HOST}:6379`
10. Save this URL! ✅

---

## Step 2: Deploy to Vercel

### Open your terminal and run these commands:

```bash
# 1. Go to your project directory
cd /Users/khoo/Downloads/project4/projects/project-20251021-092500-decentralized-forum

# 2. Login to Vercel (will open browser)
vercel login

# 3. Deploy! (Follow the prompts)
vercel

# Prompts will ask:
# - Set up and deploy? → Y (yes)
# - Which scope? → Your username
# - Link to existing project? → N (no)
# - Project name? → Press Enter (use default)
# - Directory? → Press Enter (./ is correct)
# - Override settings? → N (no)

# ⏳ Wait 1-2 minutes for deployment...

# 4. You'll get a URL like: https://your-project.vercel.app
```

---

## Step 3: Add Environment Variables

Your deployment will fail initially (that's normal!). Now add the environment variables:

### Go to Vercel Dashboard:
1. Visit https://vercel.com/dashboard
2. Click your project
3. Go to **Settings** → **Environment Variables**

### Add These Variables (One by One):

**1. APP_SECRET_KEY**
```
Value: your-super-secret-key-minimum-32-characters-long-for-security
```

**2. SECURITY_JWT_SECRET_KEY**
```
Value: another-super-secret-jwt-key-minimum-32-characters-long-here
```

**3. DATABASE_URL**
```
Value: [Paste your Supabase URL from Step 1B]
Example: postgresql+asyncpg://postgres.xxx:password@aws-0-region.pooler.supabase.com:6543/postgres
```

**4. REDIS_URL**
```
Value: [Paste your Upstash URL from Step 1C]
Example: redis://default:your-token@example.upstash.io:6379
```

**5. IPFS_API_KEY** (Optional - can skip for now)
```
Value: dummy_ipfs_key_for_now
```

### Important: Check These:
- ✅ Select **All Environments** (Production, Preview, Development)
- ✅ Click **Save** after each variable

---

## Step 4: Redeploy

```bash
# Trigger a new deployment with environment variables
vercel --prod

# ⏳ Wait 1-2 minutes...
```

---

## Step 5: Initialize Database

Once deployed, you need to create database tables:

### Option A: Run Migrations Locally (Easiest)

```bash
# 1. Set your Supabase database URL
export DATABASE_URL="[Your Supabase URL here]"

# 2. Run migrations
alembic upgrade head

# 3. Done! ✅
```

### Option B: Manual SQL (Alternative)

1. Go to Supabase Dashboard → **SQL Editor**
2. Run the SQL from `database-schema-20251021-190000.sql`

---

## Step 6: Test Your Forum! 🎉

Visit your Vercel URL: `https://your-project.vercel.app`

You should see:
- ✅ Beautiful forum homepage
- ✅ Register/Login buttons
- ✅ Full UI with all features
- ✅ Database working
- ✅ Sessions working

---

## 🎯 Quick Checklist

- [ ] Vercel account created
- [ ] Supabase PostgreSQL created
- [ ] Upstash Redis created
- [ ] Deployed to Vercel (`vercel`)
- [ ] Added all 5 environment variables
- [ ] Redeployed with env vars (`vercel --prod`)
- [ ] Ran database migrations (`alembic upgrade head`)
- [ ] Tested the live site! 🎉

---

## 🆘 Troubleshooting

### Error: "500 Internal Server Error"
**Fix:** Check environment variables are set correctly in Vercel dashboard

### Error: "Database connection failed"
**Fix:** 
1. Make sure DATABASE_URL uses `postgresql+asyncpg://` (not just `postgresql://`)
2. Check password is correct
3. Verify database is running in Supabase dashboard

### Error: "Redis connection failed"
**Fix:**
1. Verify REDIS_URL format: `redis://default:token@host:6379`
2. Check Upstash database is active

### Error: "Static files not loading"
**Fix:** Static files are included in Vercel deployment automatically

---

## 💰 Cost Breakdown

| Service | Free Tier | What You Get |
|---------|-----------|--------------|
| **Vercel** | ✅ Free forever | 100GB bandwidth, unlimited deployments |
| **Supabase** | ✅ Free forever | 500MB database, 2GB storage, 1GB file uploads |
| **Upstash** | ✅ Free forever | 10,000 commands/day, 256MB storage |

**Total Cost: $0/month** for hobby/small projects! 🎉

---

## 🚀 Next Steps After Deployment

Once live, you can:
1. Share your forum URL with users
2. Connect custom domain (Settings → Domains in Vercel)
3. Enable OAuth providers (Meta, Discord, Twitter, etc.)
4. Set up blockchain wallet connections
5. Monitor traffic in Vercel Analytics

---

## Need Help?

If you get stuck at any step, just ask! I can help with:
- Environment variable issues
- Database setup problems
- Deployment errors
- Custom domain setup
- OAuth configuration

Let's get your forum live! 🚀

