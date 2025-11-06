# Decentralized Autonomous Forum

Welcome to the documentation for the Decentralized Autonomous Forum - a community-driven platform with blockchain rewards and gamification.

## Quick Start

```bash
# Install dependencies
uv pip install -e ".[dev]"

# Configure
cp config.local.yaml.example config.local.yaml

# Run
uvicorn src.main:app --reload
```

## Features

- 🎮 **Gamification** - Points, levels, progression
- 🔗 **Blockchain** - BNB Chain rewards
- 👥 **Social** - OAuth2 login (Meta, Reddit, X, Discord, Telegram)
- 🗣️ **Voice Sessions** - Live audio rooms
- 📊 **Community-Driven** - No admin panel, democratic moderation

## Architecture

This is a FastAPI-based backend with:

- **Database**: PostgreSQL + Redis
- **Blockchain**: BNB Chain (web3.py)
- **Storage**: IPFS (Lighthouse)
- **Payments**: Crypto (auto-swap via PancakeSwap)

## Status

✅ **100% Test Pass Rate** (69/69 tests passing)  
✅ **52.71% Code Coverage**  
✅ **Ready for Deployment**

---

[View on GitHub](https://github.com/clkhoo5211/ubiquitous-succotash)
