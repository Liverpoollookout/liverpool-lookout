# 🔴 Liverpool Lookout — Fully Automated LFC News Site

> **20 AI-generated Liverpool FC articles per day. Zero manual effort. Free hosting.**

---

## What This Is

A fully automated Hugo static site that:
- Generates **10 articles at 8am + 10 articles at 5pm UTC** daily via GitHub Actions
- Uses **Claude Haiku** (cheapest Claude model) to write SEO-optimised articles
- Pulls **real live data** from TheSportsDB (free, no API key needed) for fixtures, results & squad
- Deploys **automatically to Netlify** on every commit
- Has **Google AdSense** ad slots pre-wired throughout
- Is **SEO-hardened** with Schema.org JSON-LD, Open Graph, sitemaps, canonical tags, robots.txt

**Estimated running cost: ~£2–4/month** (Claude Haiku API only — everything else is free)

---

## Stack

| Layer | Service | Cost |
|---|---|---|
| Content generation | Claude Haiku via Anthropic API | ~£2–4/month |
| Site framework | Hugo (static site generator) | Free |
| Automation | GitHub Actions | Free (2,000 min/month) |
| Hosting | Netlify | Free |
| Data | TheSportsDB API | Free |
| Domain (optional) | Namecheap / GoDaddy | ~£10/year |

---

## One-Time Setup (30 minutes)

### Step 1 — Create GitHub Repository

1. Go to [github.com](https://github.com) and sign in (create a free account if needed)
2. Click **New repository**
3. Name it `liverpool-lookout`
4. Set it to **Public** (required for free GitHub Actions minutes)
5. Click **Create repository**
6. Upload all these project files to the repository

### Step 2 — Add Your Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com) and sign up
2. Click **API Keys** → **Create Key** → copy it
3. In your GitHub repo, go to **Settings → Secrets and variables → Actions**
4. Click **New repository secret**
5. Name: `ANTHROPIC_API_KEY`
6. Value: paste your key
7. Click **Add secret**

> 💡 Add £5–10 credit to your Anthropic account. At Haiku rates (~$0.25/million tokens), 20 articles/day costs roughly $0.10/day.

### Step 3 — Deploy to Netlify

1. Go to [netlify.com](https://netlify.com) and sign up (free)
2. Click **Add new site → Import an existing project**
3. Connect to **GitHub** and select your `liverpool-lookout` repository
4. Netlify will auto-detect the settings from `netlify.toml`:
   - **Base directory:** `site`
   - **Build command:** `hugo --minify`
   - **Publish directory:** `site/public`
5. Click **Deploy site**
6. Your site will be live at a URL like `random-name-123.netlify.app`

### Step 4 — Set Your Domain (Optional but recommended for SEO)

**Option A — Use a custom domain:**
1. Buy a domain (e.g. `liverpool-lookout.com`) from Namecheap (~£10/year)
2. In Netlify: **Domain management → Add custom domain**
3. Follow Netlify's DNS instructions
4. Netlify provides free SSL automatically

**Option B — Keep the free Netlify subdomain:**
- Your site stays at `your-site-name.netlify.app` — fully functional

### Step 5 — Update hugo.toml

Open `site/hugo.toml` and change line 1:
```toml
baseURL = "https://YOUR-ACTUAL-DOMAIN.com/"
```
Replace with your Netlify URL or custom domain.

### Step 6 — Set Up Google AdSense

1. Go to [adsense.google.com](https://adsense.google.com) and apply
2. Add your site URL and wait for approval (can take 1–4 weeks — start this early)
3. Once approved, get your **Publisher ID** (looks like `ca-pub-1234567890123456`)
4. In `site/hugo.toml`, replace the placeholder values:
```toml
adsensePublisher = "ca-pub-YOUR-ID-HERE"
adsenseSlotLeaderboard = "YOUR-SLOT-ID"
adsenseSlotInArticle   = "YOUR-SLOT-ID"
adsenseSlotSidebar     = "YOUR-SLOT-ID"
```
5. In `site/static/ads.txt`, replace the placeholder with your real publisher ID:
```
google.com, pub-YOUR-ID-HERE, DIRECT, f08c47fec0942fa0
```

### Step 7 — Trigger First Run

1. In your GitHub repo, go to **Actions**
2. Click **Generate Liverpool Lookout Content**
3. Click **Run workflow → Run workflow**
4. Watch the logs — it should generate 10 articles and push them to the repo
5. Netlify will auto-detect the new commit and rebuild the site within 1–2 minutes

---

## How It Works (Technical)

```
GitHub Actions (cron: 8am + 5pm UTC)
    │
    ├── Fetches live data from TheSportsDB API
    │   ├── Upcoming fixtures
    │   ├── Recent results  
    │   └── Squad list
    │
    ├── Fetches BBC Sport LFC RSS headlines (for context)
    │
    ├── Builds a plan of 10 varied article types:
    │   match_preview, player_spotlight, transfer_news,
    │   tactical_analysis, stats_analysis, team_news,
    │   historical, opinion, youth_academy
    │
    ├── Sends each to Claude Haiku API
    │   └── Returns JSON: title, meta_description, content (markdown), tags, category
    │
    ├── Saves each as a Hugo markdown file in site/content/posts/
    │
    └── Git commits & pushes → Netlify auto-deploys
```

---

## File Structure

```
liverpool-lookout/
├── .github/
│   └── workflows/
│       └── generate-content.yml    ← GitHub Actions schedule
├── scripts/
│   ├── generate_articles.py        ← Main content engine
│   └── requirements.txt
└── site/                           ← Hugo site root
    ├── hugo.toml                   ← Site config (update this!)
    ├── netlify.toml                ← Netlify build config
    ├── content/
    │   ├── posts/                  ← Auto-generated articles land here
    │   ├── about.md
    │   └── privacy.md
    ├── layouts/
    │   ├── index.html              ← Homepage
    │   ├── _default/
    │   │   ├── baseof.html         ← Base HTML shell
    │   │   ├── single.html         ← Article page
    │   │   └── list.html           ← Archive/category pages
    │   └── partials/
    │       ├── head.html           ← SEO meta tags
    │       ├── header.html
    │       ├── footer.html
    │       └── adsense.html
    └── static/
        ├── css/style.css           ← Liverpool-themed stylesheet
        ├── robots.txt
        └── ads.txt                 ← Required for AdSense
```

---

## SEO Features Built In

- ✅ **Schema.org NewsArticle** JSON-LD on every article
- ✅ **Open Graph** meta tags (Facebook/WhatsApp sharing)
- ✅ **Twitter Card** meta tags
- ✅ **Canonical URLs** (prevents duplicate content)
- ✅ **XML Sitemap** auto-generated at `/sitemap.xml`
- ✅ **RSS Feed** at `/index.xml`
- ✅ **robots.txt** with sitemap declaration
- ✅ **ads.txt** for AdSense authority
- ✅ **Breadcrumb Schema** on article pages
- ✅ **Meta descriptions** from AI (max 155 chars)
- ✅ **Reading time** on articles
- ✅ **Internal linking** via related articles
- ✅ **Category & tag taxonomy** pages
- ✅ **Minified HTML** (Hugo `--minify` flag)
- ✅ **Static site = fast Core Web Vitals** (important for Google ranking)
- ✅ **www → non-www redirect** (canonical domain)
- ✅ **Security headers** (trust signals for Google)

---

## AdSense Ad Placement

Each article page contains **4 ad placements**:

| Position | Format | Size |
|---|---|---|
| Below article header | Leaderboard | 728×90 responsive |
| After 3rd paragraph | In-article | Fluid/responsive |
| End of article | Responsive | Auto |
| Sidebar (desktop) | Display | 300×250 ×2 |

---

## Customisation

### Change article schedule
Edit `.github/workflows/generate-content.yml`:
```yaml
- cron: "0 8 * * *"   # Change 8 to any UTC hour
- cron: "0 17 * * *"  # Evening run
```

### Change number of articles per run
Edit `scripts/generate_articles.py` — the `build_article_plan()` function returns a list of article types. Add or remove entries to change the count.

### Add more player names
In `generate_articles.py`, add to `KEY_PLAYERS` list.

### Change article length
Each prompt in `PROMPTS` dict specifies word count — edit the numbers in brackets e.g. `(650–850 words)`.

---

## Troubleshooting

**Build fails on Netlify:**
- Check Hugo version in `netlify.toml` matches a real Hugo release
- Make sure `baseURL` in `hugo.toml` is set correctly

**GitHub Actions fails:**
- Check `ANTHROPIC_API_KEY` secret is set correctly
- Check your Anthropic account has credit

**No articles generated:**
- Run the workflow manually via Actions tab
- Check the workflow logs for error messages

**AdSense not showing:**
- Make sure your site is approved by AdSense first
- Replace ALL placeholder IDs in `hugo.toml` and `ads.txt`

---

## Important Notes

- This site is for **fan/editorial content** — it uses responsible language for transfer rumours ("according to reports") and does not fabricate specific quotes
- You **must have AdSense approval** before ads show — apply early
- The site clearly states it is **not affiliated with Liverpool FC**
- Content is generated by AI — review the Privacy Policy and consider adding an AI disclosure

---

## Questions?

Check the GitHub Actions logs first — they're very detailed and will tell you exactly what went wrong.
