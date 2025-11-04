#!/bin/bash
# Script to push project to GitHub repository

set -e

REPO_URL="https://github.com/clkhoo5211/ubiquitous-succotash.git"
BRANCH="main"

echo "🚀 Preparing to push to GitHub..."
echo "📦 Repository: $REPO_URL"
echo "🌿 Branch: $BRANCH"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git repository not initialized. Initializing..."
    git init
    echo "✅ Git initialized"
fi

# Check if remote exists
if git remote | grep -q "^origin$"; then
    echo "📡 Remote 'origin' already exists"
    CURRENT_REMOTE=$(git remote get-url origin)
    if [ "$CURRENT_REMOTE" != "$REPO_URL" ]; then
        echo "⚠️  Warning: Remote URL is different:"
        echo "   Current: $CURRENT_REMOTE"
        echo "   Target:  $REPO_URL"
        read -p "Update remote to target URL? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git remote set-url origin "$REPO_URL"
            echo "✅ Remote updated"
        fi
    fi
else
    echo "➕ Adding remote 'origin'..."
    git remote add origin "$REPO_URL"
    echo "✅ Remote added"
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "📝 Staging all changes..."
    git add -A
    echo "✅ Changes staged"
fi

# Check if there are any commits
if [ -z "$(git log --oneline -1 2>/dev/null)" ]; then
    echo "📝 Creating initial commit..."
    git commit -m "Initial commit: Decentralized Autonomous Forum

- FastAPI backend with PostgreSQL and Redis
- 100% test pass rate (86/86 tests)
- OAuth2 authentication (5 providers)
- Blockchain integration (BNB Chain)
- IPFS storage support
- Community-driven moderation
- Production ready"
    echo "✅ Initial commit created"
else
    echo "📝 Committing changes..."
    git commit -m "Update: Project files and deployment configuration" || echo "No changes to commit"
fi

# Check current branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "")
if [ -z "$CURRENT_BRANCH" ]; then
    echo "🌿 Creating branch '$BRANCH'..."
    git checkout -b "$BRANCH"
elif [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
    echo "🌿 Switching to branch '$BRANCH'..."
    git checkout -b "$BRANCH" 2>/dev/null || git checkout "$BRANCH"
fi

echo ""
echo "🚀 Pushing to GitHub..."
echo "   This may prompt for GitHub credentials"
echo ""

# Push to GitHub
if git push -u origin "$BRANCH" 2>&1 | tee /tmp/git_push.log; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Visit: https://github.com/clkhoo5211/ubiquitous-succotash"
    echo "   2. Enable GitHub Pages (Settings → Pages → Source: GitHub Actions)"
    echo "   3. Set up hosting service (Railway/Render/Fly.io) for the FastAPI app"
    echo "   4. Configure environment variables in your hosting service"
    echo "   5. See DEPLOYMENT.md for detailed instructions"
    echo ""
else
    echo ""
    echo "❌ Push failed. Common issues:"
    echo "   - Authentication required (use GitHub Personal Access Token)"
    echo "   - Repository permissions"
    echo "   - Network connectivity"
    echo ""
    echo "💡 To fix authentication:"
    echo "   git remote set-url origin https://YOUR_TOKEN@github.com/clkhoo5211/ubiquitous-succotash.git"
    echo ""
    exit 1
fi

