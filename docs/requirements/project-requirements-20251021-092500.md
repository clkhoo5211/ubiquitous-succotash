# Project Requirements - Decentralized Autonomous Forum
**Generated**: 2025-10-21 09:25:00
**Project**: Decentralized Autonomous Forum
**Timeline**: 1 Year MVP Launch

## 1. Project Overview

### Vision
Create a decentralized autonomous forum platform that empowers users to become community moderators and leaders through a gamified point-based reward system integrated with BNB Chain blockchain for transparent governance, eliminating the need for centralized admin control.

### Core Value Proposition
- **Decentralized Governance**: No admin panel; community-driven moderation
- **Gamified Engagement**: Earn and spend points for all platform activities
- **User Progression**: Level-based advancement from User to Admin
- **Blockchain Integration**: BNB Chain for transparent reward distribution
- **Multi-Format Content**: Support all modern content types (images, videos, wiki, ads)
- **Social Integration**: Seamless OAuth2 login with major platforms

## 2. Target Audience

### Primary Users
- Content creators and bloggers
- Community builders and moderators
- Crypto-enthusiasts interested in decentralized platforms
- Social media users seeking alternative platforms
- Knowledge contributors (wiki editors)

### User Personas
1. **The Content Creator**: Posts regularly, earns through engagement
2. **The Moderator**: Helps grow community, resolves disputes
3. **The Lurker**: Consumes content, occasional engagement
4. **The Influencer**: Hosts voice sessions, builds follower base
5. **The Knowledge Contributor**: Maintains wiki, shares expertise

## 3. Content & Media Features

### 3.1 Content Types Supported
- **Text Posts**: Rich text with markdown support
- **Images**: All formats (JPEG, PNG, GIF, WebP, SVG, HEIC)
  - Auto-compression and optimization
  - Storage via IPFS (Lighthouse SDK) or Cloudinary
  - Maximum size: 10MB per image (configurable)

- **Videos**: Embedded links only (YouTube, Vimeo, TikTok, Dailymotion)
  - Preview thumbnails generated
  - In-platform video player for embedded content

- **Advertisements**: User-posted promotional content
  - Flagged as "Advertisement" automatically
  - Higher point cost to post (10 points vs 5 for regular posts)
  - Revenue share model for platform sustainability

- **Knowledge Base (Wiki)**: Collaborative documentation
  - Version control system (Git-based or custom)
  - Collaborative editing with conflict resolution
  - Structured documentation with categories
  - Search and indexing

### 3.2 Media Storage Strategy
- **Free Open-Source Options**:
  - IPFS via Lighthouse SDK (perpetual storage, pay-once model)
  - Cloudinary Free Tier (25GB storage/month)
  - Imgur API for image hosting
  - Embed-only for videos (no self-hosting)

### 3.3 Content Moderation
- **Community-Driven**: Flagging system for inappropriate content
- **Reputation-Based Authority**: Higher-level users review flagged content
- **Voting System**: Community votes on removal decisions
- **Automated Filters**: Keyword and image detection for illegal content
- **Escalation Path**: Complex cases escalated to Moderators/Admins

## 4. Point Economy System

### 4.1 Registration & Onboarding
- **Registration Bonus**: +100 points (one-time)
- **Email Verification Required**: Prevents spam accounts
- **Referral Bonus**: +25 points for inviting verified users

### 4.2 Recharge System
**Packages**:
- $5 = 500 points
- $10 = 1,100 points (10% bonus)
- $25 = 2,750 points (10% bonus)
- $50 = 5,750 points (15% bonus)

**Automated Bonus Events**:
- Every 3 months, automated bonus toggle (ON/OFF)
- Bonus days: Alternate days when enabled
- Notification system for bonus events

**Payment Integration**:
- PayPal REST API for subscriptions and one-time payments
- Creator receives all recharge revenue via PayPal
- Transaction fees handled by PayPal

### 4.3 Point Spending (Costs)
| Action | Cost | Rationale |
|--------|------|-----------|
| Create Post | -5 points | Prevents spam, ensures quality |
| Create Comment | -2 points | Encourages thoughtful replies |
| Like Post/Comment | -1 point | Prevents like-bombing |
| Share Externally | -1 point | Optional cost for external shares |
| Create Channel | -50 points | Ensures committed channel owners |
| Post Advertisement | -10 points | Higher cost for promotional content |
| Create Poll | -3 points | Engagement feature |
| Host Voice Session | -20 points | Resource-intensive feature |

### 4.4 Point Earning (Rewards)
| Achievement | Reward | Conditions |
|-------------|--------|------------|
| 10 Likes Received | +3 points | Per post/comment |
| 100 Likes Received | +30 points | Cumulative bonus |
| 1,000 Likes Received | +350 points | Viral content bonus |
| Quality Post Badge | +10 points | Moderator-verified quality |
| Successful Referral | +25 points | New user must verify email |
| Wiki Contribution | +5 points | Per approved wiki edit |
| Helpful Comment Badge | +3 points | Community-voted helpful |
| Daily Login Streak (7 days) | +10 points | Engagement incentive |
| Monthly Top Contributor | +100 points | Leaderboard reward |

### 4.5 Anti-Spam Mechanisms
- **Cannot self-like**: Users cannot like their own posts/comments
- **Rate Limiting**: Max 50 posts/day, 200 comments/day
- **New User Restrictions**: Limited actions first 7 days
- **Suspicious Activity Detection**: Machine learning for bot detection
- **Point Decay**: Inactive accounts lose 10% points/month (after 90 days)
- **Vote Weight**: Higher-level users' votes carry more weight

### 4.6 Point Inflation Control
**Spending vs Earning Ratio**: ~1.5:1
- Users spend more points than they can easily earn
- Encourages recharge purchases for active users
- Prevents point inflation over time
- **Burn Mechanism**: Platform takes 30% of spent points out of circulation
- **Example**: User spends 5 points to post → 1.5 points burned, 3.5 points recyclable

### 4.7 Point Transfer
- **Internal Transfers**: Users can gift points to each other
- **Transfer Fee**: 10% fee on transfers (anti-gaming measure)
- **Daily Limit**: Max 100 points transferred per day
- **No Real Currency Conversion**: Points stay within platform ecosystem

## 5. User Progression & Role System

### 5.1 Level Tiers (Inspired by Stack Overflow & Reddit)

| Level | Title | Requirements | Permissions |
|-------|-------|--------------|-------------|
| 0 | New User | 0-7 days old | Limited posting (5/day), basic features |
| 1 | User | 100+ points | Full posting access, like, comment |
| 2 | Contributor | 500+ points, 30+ days, 10+ quality posts | Flag content, edit wiki |
| 3 | Trusted | 1,500+ points, 60+ days | Vote on disputes, review flags |
| 4 | Moderator | 2,500+ points, 90+ days, 50+ quality posts | Remove content, resolve disputes, temporary bans |
| 5 | Senior Moderator | 10,000+ points, 180+ days, community vote | Permanent bans, channel management |
| 6 | Channel Owner | Create channel (50 points), 5,000+ points | Manage own channel, host voice sessions |
| 7 | Admin | 25,000+ points, 365+ days, community vote (75% approval) | Platform governance, policy decisions |

### 5.2 Demotion System
- **Inactivity**: Drop one level after 180 days of no engagement
- **Negative Behavior**: Community vote to demote (requires evidence)
- **Abuse of Power**: Moderators can be demoted for unfair actions
- **Appeal Process**: Users can appeal demotions with evidence

### 5.3 Verified Badges
**Premium Feature** (unlocked via payment or achievement):
- Verified Creator Badge: $5/month or 10,000 lifetime points
- Verified Business Badge: $10/month (Meta-style business verification)
- Verified Influencer Badge: 50,000+ points + community recognition
- Custom badges for top contributors (free, auto-awarded)

## 6. Voice & Live Features

### 6.1 Voice Sessions (Space-like)
- **Hosting Requirements**: Level 6 (Channel Owner) or Moderator+
- **Verification**: Meta-style business/influencer verification for public sessions
- **Recording**: Optional recording, stored on IPFS
- **Moderation**: Host can mute/remove participants
- **Capacity**: Up to 100 listeners, 10 speakers simultaneously
- **Point Cost**: -20 points to host, free to join
- **Scheduling**: Calendar integration for scheduled sessions

### 6.2 Technical Implementation
- **WebRTC**: For peer-to-peer voice connections
- **Fallback**: Server-based relay for poor connections
- **Compression**: Opus codec for bandwidth efficiency
- **Platform**: Agora, Daily.co, or Jitsi (open-source)

## 7. Social Integration

### 7.1 OAuth2 Single Sign-On
**Supported Platforms**:
- Meta/Facebook Login
- Reddit OAuth2
- X/Twitter OAuth2
- Discord OAuth2
- Telegram Bot Login

**Implementation**:
- Authlib (Python) for OAuth2 flow
- Session management via JWT tokens
- Optional email/password fallback

### 7.2 Content Sharing
**External Sharing** (no point rewards, but costs 1 point):
- Share to Meta, X, Reddit, Discord, Telegram
- Custom share messages with platform branding
- Deep links back to forum post

**Referral System** (point rewards):
- Unique referral links for each user
- +25 points per verified signup via referral
- Leaderboard for top referrers

## 8. Technical Architecture

### 8.1 Technology Stack

**Backend**:
- **Framework**: FastAPI (async, high-performance, modern)
- **Language**: Python 3.11+
- **Package Manager**: uv (10-100x faster than pip)
- **ORM**: SQLAlchemy (async)
- **Migrations**: Alembic

**Frontend**:
- **Templates**: Jinja2 (server-side rendering)
- **Interactivity**: HTMX (no heavy JS frameworks)
- **Styling**: Tailwind CSS (utility-first)
- **Progressive Enhancement**: Works without JS

**Database**:
- **Primary**: PostgreSQL (Supabase or Neon serverless)
- **Caching**: Redis (sessions, rate limiting)
- **Search**: PostgreSQL full-text search or Meilisearch

**Blockchain**:
- **Chain**: BNB Chain (low fees, fast transactions)
- **Integration**: web3.py library
- **Smart Contract**: ERC-20-like token for points (optional future feature)
- **Governance**: On-chain voting for major decisions

**File Storage**:
- **Images/Media**: IPFS via Lighthouse SDK (perpetual, decentralized)
- **Fallback**: Cloudinary free tier
- **Videos**: Embedded links only (YouTube, Vimeo, etc.)

**Payments**:
- **Provider**: PayPal REST API
- **Methods**: One-time payments, subscriptions
- **Currency**: USD (convertible to points)

**Deployment**:
- **Preferred**: Vercel (serverless, free tier)
- **Alternatives**: Railway, Render, PythonAnywhere
- **Containerization**: Docker (for portability)
- **CI/CD**: GitHub Actions

### 8.2 No Admin Panel Requirement
- **Configuration**: Environment variables only
- **Database Management**: Direct SQL or Alembic migrations
- **Monitoring**: External tools (Sentry, LogRocket)
- **User Management**: All via platform features (no backdoor admin)

### 8.3 Scalability Considerations
- **Async Everything**: FastAPI async endpoints
- **Database Connection Pooling**: pgBouncer or SQLAlchemy pool
- **Caching Strategy**: Redis for hot data, PostgreSQL for cold
- **CDN**: Cloudflare for static assets
- **Rate Limiting**: Redis-based, per-user tracking

## 9. Security & Privacy

### 9.1 Email Verification
- **Registration**: Email verification required before full access
- **Duplicate Prevention**: One email = one account (strict enforcement)
- **Implementation**: SMTP via SendGrid or Mailgun
- **Timeout**: Verification links expire in 24 hours

### 9.2 GDPR Compliance
**Data Subject Rights**:
- Right to Access: Export all user data via API
- Right to Erasure: Delete account and all personal data
- Right to Rectification: Edit profile and personal info
- Right to Data Portability: Download JSON export

**Technical Measures**:
- Encryption at rest (PostgreSQL encryption)
- Encryption in transit (TLS/HTTPS)
- Password hashing (bcrypt with salt)
- Session security (HTTP-only cookies, CSRF protection)

**Privacy Policy**: Auto-generated, legally reviewed

### 9.3 Anonymous Posting
**Tier-Based Access**:
- Level 3+ (Trusted): Can enable anonymous mode per post
- Level 5+ (Senior Moderator): Always available
- Tracked internally for moderation (hidden from public)
- Disabled for advertisements (always attributed)

### 9.4 Encryption
- **End-to-End**: DMs between users (optional feature)
- **Voice Sessions**: WebRTC encryption (SRTP)
- **Data at Rest**: Database-level encryption

## 10. MVP Features (Phase 1 - Target: Month 6)

### Must-Have for Launch
✅ User registration with email verification
✅ OAuth2 social login (Meta, Reddit, Discord)
✅ Create/read/update/delete posts and comments
✅ Point system (spending and earning)
✅ PayPal recharge integration
✅ Image upload to IPFS/Cloudinary
✅ Video embedding (YouTube, Vimeo)
✅ User progression (Levels 0-4)
✅ Basic moderation (flag content)
✅ Community voting on disputes
✅ Responsive design (mobile-friendly)
✅ GDPR compliance (data export/deletion)

### Nice-to-Have for Launch
- Wiki/Knowledge base
- Voice sessions (Spaces-like)
- BNB Chain integration (governance)
- Advanced analytics dashboard
- Referral system
- Custom badges

### Post-MVP (Phase 2 - Month 7-12)
- Wiki implementation
- Voice sessions
- Blockchain rewards (BNB Chain)
- Custom channels
- Advanced search
- Notifications system
- Mobile app (PWA first, then native)

## 11. Success Metrics

### Platform Health
- **Active Users**: 10,000+ MAU in first year
- **User Retention**: 40%+ 30-day retention
- **Content Quality**: 70%+ posts with 5+ likes
- **Moderation Efficiency**: <2 hour response time for flags

### Economic Metrics
- **Point Circulation**: Balanced spending/earning ratio
- **Recharge Revenue**: $10,000+ MRR by month 12
- **Average Revenue Per User (ARPU)**: $2+/month
- **Churn Rate**: <5% monthly

### Engagement Metrics
- **Posts Per Day**: 500+ daily posts by month 6
- **Comments Per Post**: Average 5+ comments
- **Voice Sessions**: 10+ weekly sessions by month 12
- **Wiki Contributions**: 100+ wiki pages by month 12

## 12. Compliance & Legal

### Required Documentation
- Privacy Policy (GDPR-compliant)
- Terms of Service
- Community Guidelines
- Acceptable Use Policy
- Content Moderation Policy
- Data Processing Agreement (DPA)

### Regulatory Compliance
- **GDPR** (EU users): Full compliance
- **CCPA** (California users): Data deletion rights
- **COPPA** (13+ age requirement): Age verification on signup
- **Payment Compliance**: PCI-DSS via PayPal

### Content Policies
- No illegal content (automated detection + community flagging)
- No hate speech or harassment
- No spam or manipulation
- No impersonation
- Copyright respect (DMCA takedown process)

## 13. Development Team & Timeline

### Team (Using .claude Multi-Agent Framework)
- Init Agent: Requirements gathering ✅
- Product Agent: Market research and product strategy
- Plan Agent: Roadmap and project timeline
- UX Agent: User experience and wireframes
- Design Agent: Technical architecture
- Data Agent: Database and analytics infrastructure
- Develop Agent: Code implementation
- DevOps Agent: Infrastructure and deployment
- Security Agent: Security assessment
- Compliance Agent: GDPR and legal compliance
- Test Agent: QA and user testing
- Debug Agent: Bug fixes and optimization
- Audit Agent: Final quality review
- Deploy Agent: Production launch

### Timeline (1 Year MVP)

**Months 1-2**: Planning & Design
- Product strategy and market research
- Technical architecture design
- UX wireframes and user flows
- Database schema design

**Months 3-6**: Core Development
- User authentication and authorization
- Post/comment CRUD operations
- Point system implementation
- PayPal integration
- Basic moderation features

**Month 6**: MVP Launch (Private Beta)
- Limited user testing (100-500 users)
- Bug fixes and optimization
- User feedback collection

**Months 7-9**: Feature Expansion
- Wiki/Knowledge base
- Voice sessions
- BNB Chain integration
- Advanced moderation tools

**Months 10-11**: Polish & Scale
- Performance optimization
- Security hardening
- GDPR compliance finalization
- Marketing and growth

**Month 12**: Public Launch
- Open registration
- Community onboarding
- Continuous improvement

## 14. Risks & Mitigation

### Technical Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Scalability issues | High | Load testing, async architecture, caching |
| Data loss | Critical | Automated backups, IPFS redundancy |
| DDoS attacks | High | Cloudflare protection, rate limiting |
| Smart contract bugs | Medium | Audited contracts, testnet deployment first |

### Business Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Low user adoption | Critical | Marketing, referral incentives, beta testing |
| Point inflation | High | Economic modeling, burn mechanisms |
| Regulatory changes | Medium | Legal monitoring, compliance team |
| Payment fraud | Medium | PayPal fraud detection, manual review |

### Community Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Toxic community | High | Strong moderation, clear guidelines |
| Spam content | Medium | Point costs, rate limiting, ML detection |
| Power user dominance | Medium | Level caps, democratic voting |

## 15. Open Questions for Future Clarification

1. **Mobile App**: Native apps or PWA (Progressive Web App) first?
2. **API Access**: Public API for third-party developers?
3. **Internationalization**: Multi-language support priority?
4. **Content Moderation**: AI-based content filtering or human-only?
5. **Blockchain Governance**: Immediate integration or Phase 2?
6. **Premium Tiers**: Additional premium features beyond verified badges?
7. **Partnership Strategy**: Integrate with existing platforms (Discord bots, etc.)?
8. **Open Source**: Will this be open-source or proprietary?

---

**Document Version**: 1.0
**Last Updated**: 2025-10-21 09:25:00
**Next Review**: After Product Agent analysis
