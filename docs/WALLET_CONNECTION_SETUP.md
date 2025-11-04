# Wallet Connection - Setup Guide

**Status**: ✅ Fixed and Ready
**Last Updated**: 2025-01-27

---

## 🎯 Quick Steps to Test Wallet Connection

### Step 1: Start the Application

```bash
cd /Users/khoo/Downloads/project4/projects/project-20251021-092500-decentralized-forum
source .venv/bin/activate

# Start services (if not already running)
docker-compose -f docker-compose.dev.yml up -d postgres redis

# Run migrations
alembic upgrade head

# Start the server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Access**: http://localhost:8000

---

### Step 2: Register/Login

**Option A: Register New Account**
1. Go to: http://localhost:8000/auth/register
2. Fill in:
   - Username
   - Email
   - Password (min 8 characters)
   - Age confirmation (13+)
   - Accept terms
3. Click "Create Account"
4. You'll receive 100 bonus points!

**Option B: Login** (if you have an account)
1. Go to: http://localhost:8000/auth/login
2. Enter email and password
3. Click "Login"

---

### Step 3: Test Wallet Connection

Once logged in:

1. Go to: http://localhost:8000/rewards/crypto
2. You'll see "Wallet Not Connected"
3. Click "Connect Wallet" button
4. MetaMask popup appears:
   - Click "Next" → "Connect"
   - Sign the message
5. Success! Wallet is connected
6. Refresh the page to see your wallet address

---

## 🐛 Troubleshooting

### Error: "Authentication required" 401

**Problem**: You're not logged in  
**Solution**: 
1. Go to http://localhost:8000/auth/login
2. Login with your credentials
3. Try connecting wallet again

### Error: "MetaMask not detected"

**Problem**: MetaMask extension not installed  
**Solution**: 
1. Install MetaMask from:
   - Chrome: https://chrome.google.com/webstore/detail/metamask
   - Firefox: https://addons.mozilla.org/en-US/firefox/addon/ether-metamask/
2. Refresh the page

### Error: Database connection failed

**Problem**: PostgreSQL not running  
**Solution**:
```bash
# Start PostgreSQL
docker-compose -f docker-compose.dev.yml up -d postgres

# Check status
docker ps | grep postgres
```

### Error: Port 8000 already in use

**Solution**:
```bash
# Kill existing process
pkill -f uvicorn

# Or use different port
uvicorn src.main:app --reload --port 8001
```

---

## 📋 Complete Test Checklist

- [ ] Application running on http://localhost:8000
- [ ] User account created and logged in
- [ ] MetaMask installed in browser
- [ ] Navigate to /rewards/crypto page
- [ ] See "Wallet Not Connected" message
- [ ] Click "Connect Wallet" button
- [ ] MetaMask popup appears
- [ ] Approve connection request
- [ ] Sign the verification message
- [ ] See "Wallet connected successfully" alert
- [ ] Page reloads with wallet address displayed
- [ ] Click "Disconnect" to test disconnect flow
- [ ] Confirm disconnection works

---

## 🎉 Success Indicators

**You're ready when:**
- ✅ 401 errors are gone (you're logged in)
- ✅ MetaMask popup appears when clicking "Connect"
- ✅ Signature request appears
- ✅ Success alert shows
- ✅ Wallet address displays on page
- ✅ Disconnect button works

---

**Last Fixed**: Authentication requirement enforced correctly  
**Status**: ✅ Ready for Testing

