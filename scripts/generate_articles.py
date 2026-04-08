#!/usr/bin/env python3
"""
Liverpool Lookout - Automated Content Generator
Runs ONCE daily via GitHub Actions.
Generates 3 SEO-optimised articles per run using Claude API + free football data APIs.
Uses static SVG illustrations to conserve API credits.

Credit-saving measures vs previous version:
  - 3 articles/run (was 5), schedule changed to once-daily (was twice-daily)
  - claude-haiku-3-5 (cheaper) for simpler article types
  - Per-type max_tokens tuned to actual word-count targets
  - Shorter prompts to cut input token usage
  - Skip match_report when no result data is available
  - Hard stop on PermissionDeniedError (credit exhaustion)
"""
import os
import sys
import json
import time
import random
import re
import requests
from datetime import datetime, timezone
import anthropic

# ── CONFIG ──────────────────────────────────────────────────────────────────
TEAM_ID       = "133602"
TEAM_NAME     = "Liverpool FC"
MANAGER       = "Arne Slot"
STADIUM       = "Anfield"
SEASON        = "2025-26"
CONTENT_DIR   = "site/content/posts"
STATIC_DIR    = "site/static"
IMAGES_DIR    = "site/static/images/articles"

ARTICLES_PER_RUN = 3   # keep low to stay inside credit limits

# Model tiers
MODEL_HEAVY   = "claude-haiku-4-5-20251001"   # complex long-form
MODEL_LIGHT   = "claude-haiku-3-5-20251001"   # shorter / simpler

KEY_PLAYERS = [
    "Mohamed Salah", "Virgil van Dijk", "Alisson Becker",
    "Dominik Szoboszlai", "Darwin Nunez", "Luis Diaz",
    "Ryan Gravenberch", "Alexis Mac Allister", "Cody Gakpo",
    "Joe Gomez", "Ibrahima Konate", "Harvey Elliott",
    "Jarell Quansah", "Caoimhin Kelleher", "Federico Chiesa",
    "Konstantinos Tsimikas", "Conor Bradley", "Curtis Jones",
    "Wataru Endo", "Diogo Jota",
]

DEPARTED_PLAYERS = [
    "Trent Alexander-Arnold (Real Madrid, 2024)",
    "Joel Matip (2024)", "Thiago Alcantara (2024)",
    "James Milner (2023)", "Jordan Henderson (2023)",
    "Fabinho (2023)", "Roberto Firmino (2023)",
]

CATEGORIES = {
    "match_preview":     "Match Previews",
    "match_report":      "Match Reports",
    "player_spotlight":  "Player Analysis",
    "transfer_news":     "Transfer News",
    "tactical_analysis": "Tactical Analysis",
    "stats_analysis":    "Stats & Data",
    "team_news":         "Team News",
    "historical":        "History",
    "opinion":           "Opinion",
    "youth_academy":     "Academy",
}

# Per-type output token budgets (sized to word targets + JSON overhead)
MAX_TOKENS = {
    "match_preview":     900,
    "match_report":      950,
    "player_spotlight":  900,
    "transfer_news":     800,
    "tactical_analysis": 950,
    "stats_analysis":    900,
    "team_news":         750,
    "historical":        950,
    "opinion":           850,
    "youth_academy":     800,
}

MODEL_FOR = {
    "match_preview":     MODEL_HEAVY,
    "match_report":      MODEL_HEAVY,
    "player_spotlight":  MODEL_LIGHT,
    "transfer_news":     MODEL_LIGHT,
    "tactical_analysis": MODEL_HEAVY,
    "stats_analysis":    MODEL_LIGHT,
    "team_news":         MODEL_LIGHT,
    "historical":        MODEL_HEAVY,
    "opinion":           MODEL_LIGHT,
    "youth_academy":     MODEL_LIGHT,
}


# ── STATIC SVG ILLUSTRATIONS ────────────────────────────────────────────────
def get_animated_svg(article_type, title=""):
    svgs = {
        "match_preview":     _svg_match_preview,
        "match_report":      _svg_match_report,
        "player_spotlight":  _svg_player_spotlight,
        "transfer_news":     _svg_transfer_news,
        "tactical_analysis": _svg_tactical_analysis,
        "stats_analysis":    _svg_stats_analysis,
        "team_news":         _svg_team_news,
        "historical":        _svg_historical,
        "opinion":           _svg_opinion,
        "youth_academy":     _svg_academy,
    }
    return svgs.get(article_type, _svg_default)()

def _svg_match_preview():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#2d7a2d" rx="8"/><rect x="60" y="40" width="680" height="320" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="2"/><circle cx="400" cy="200" r="60" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="2"/><line x1="400" y1="40" x2="400" y2="360" stroke="rgba(255,255,255,0.5)" stroke-width="2"/><circle cx="400" cy="200" r="16" fill="white" stroke="#333" stroke-width="2"><animate attributeName="cx" values="200;600;200" dur="3s" repeatCount="indefinite"/><animate attributeName="cy" values="200;120;200" dur="3s" repeatCount="indefinite"/></circle><text x="400" y="210" text-anchor="middle" font-family="Arial Black,sans-serif" font-size="28" font-weight="900" fill="white">MATCH PREVIEW</text><rect x="290" y="50" width="220" height="50" rx="6" fill="#C8102E" opacity="0.9"/><text x="400" y="82" text-anchor="middle" font-family="Arial,sans-serif" font-size="16" font-weight="700" fill="white">COMING UP</text></svg>'

def _svg_match_report():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#111111" rx="8"/><rect x="200" y="80" width="400" height="180" rx="12" fill="rgba(0,0,0,0.5)"/><text x="300" y="200" text-anchor="middle" font-family="Arial Black,sans-serif" font-size="72" font-weight="900" fill="white">LFC</text><text x="400" y="200" text-anchor="middle" font-family="Arial Black,sans-serif" font-size="48" font-weight="900" fill="#C8102E">VS</text><text x="500" y="200" text-anchor="middle" font-family="Arial Black,sans-serif" font-size="72" font-weight="900" fill="#aaa">OPP</text><text x="400" y="320" text-anchor="middle" font-family="Arial,sans-serif" font-size="20" font-weight="700" fill="white" letter-spacing="4">MATCH REPORT</text></svg>'

def _svg_player_spotlight():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#111" rx="8"/><text x="400" y="330" text-anchor="middle" font-family="Arial,sans-serif" font-size="22" fill="#F6EB61">&#9733; &#9733; &#9733; &#9733; &#9733;</text><text x="400" y="360" text-anchor="middle" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="white" letter-spacing="3">PLAYER SPOTLIGHT</text><ellipse cx="400" cy="180" rx="200" ry="180" fill="#C8102E" opacity="0.15"/><circle cx="400" cy="140" r="40" fill="#C8102E" opacity="0.7"/><rect x="370" y="178" width="60" height="80" rx="10" fill="#C8102E" opacity="0.7"/></svg>'

def _svg_transfer_news():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#0a0a2e" rx="8"/><path d="M 250 200 L 550 200" stroke="#C8102E" stroke-width="4" fill="none" stroke-dasharray="10,5"><animate attributeName="stroke-dashoffset" values="0;-60" dur="1s" repeatCount="indefinite"/></path><polygon points="560,190 580,200 560,210" fill="#C8102E"/><text x="400" y="320" text-anchor="middle" font-family="Arial,sans-serif" font-size="18" font-weight="700" fill="white" letter-spacing="4">TRANSFER NEWS</text></svg>'

def _svg_tactical_analysis():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#1a1a2e" rx="8"/><rect x="80" y="40" width="640" height="320" rx="6" fill="#2d7a2d"/><rect x="100" y="60" width="600" height="280" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/><circle cx="400" cy="200" r="50" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/><circle cx="200" cy="200" r="12" fill="#C8102E"/><circle cx="300" cy="130" r="12" fill="#C8102E"/><circle cx="300" cy="200" r="12" fill="#C8102E"/><circle cx="300" cy="270" r="12" fill="#C8102E"/><circle cx="430" cy="130" r="12" fill="#C8102E"/><circle cx="430" cy="200" r="12" fill="#C8102E"/><circle cx="430" cy="270" r="12" fill="#C8102E"/><text x="400" y="385" text-anchor="middle" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="white" letter-spacing="3">TACTICAL ANALYSIS</text></svg>'

def _svg_stats_analysis():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#0d1117" rx="8"/><rect x="80" y="140" width="60" height="180" fill="#C8102E"/><rect x="160" y="100" width="60" height="220" fill="#C8102E" opacity="0.85"/><rect x="240" y="160" width="60" height="160" fill="#C8102E" opacity="0.7"/><rect x="320" y="60" width="60" height="260" fill="#C8102E" opacity="0.9"/><rect x="400" y="120" width="60" height="200" fill="#C8102E" opacity="0.75"/><text x="400" y="370" text-anchor="middle" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="white" letter-spacing="3">STATS &amp; DATA</text></svg>'

def _svg_team_news():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#111827" rx="8"/><rect x="60" y="40" width="680" height="300" rx="6" fill="white" opacity="0.95"/><rect x="60" y="40" width="680" height="55" rx="6" fill="#C8102E"/><text x="400" y="78" text-anchor="middle" font-family="Arial Black,sans-serif" font-size="22" font-weight="900" fill="white" letter-spacing="2">TEAM NEWS</text><circle cx="120" cy="67" r="8" fill="#ff0"><animate attributeName="opacity" values="1;0.2;1" dur="0.8s" repeatCount="indefinite"/></circle><rect x="90" y="115" width="400" height="14" rx="4" fill="#e0e0e0"/><rect x="90" y="140" width="500" height="14" rx="4" fill="#e0e0e0"/></svg>'

def _svg_historical():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#1a0a00" rx="8"/><g transform="translate(400,200)"><path d="M-40,-80 Q-50,-40 -30,0 L-20,30 L-5,30 L-5,50 L-25,50 L-25,65 L25,65 L25,50 L5,50 L5,30 L20,30 L30,0 Q50,-40 40,-80 Z" fill="#F6EB61" opacity="0.9"/></g><text x="400" y="340" text-anchor="middle" font-family="Georgia,serif" font-size="16" font-style="italic" fill="#F6EB61" opacity="0.9">On This Day in Liverpool FC History</text></svg>'

def _svg_opinion():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#1a1a2e" rx="8"/><rect x="60" y="80" width="280" height="160" rx="16" fill="#C8102E"/><polygon points="100,240 80,280 140,240" fill="#C8102E"/><text x="200" y="150" text-anchor="middle" font-family="Georgia,serif" font-size="48" fill="white" opacity="0.9">"</text><text x="400" y="360" text-anchor="middle" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="white" letter-spacing="4">OPINION</text></svg>'

def _svg_academy():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#0d2137" rx="8"/><text x="400" y="60" text-anchor="middle" font-family="Arial Black,sans-serif" font-size="14" font-weight="700" fill="#F6EB61" letter-spacing="4">STARS OF THE FUTURE</text><text x="400" y="360" text-anchor="middle" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="white" letter-spacing="3">ACADEMY &amp; YOUTH</text></svg>'

def _svg_default():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#C8102E" rx="8"/><text x="400" y="210" text-anchor="middle" font-family="Arial Black,sans-serif" font-size="42" font-weight="900" fill="white">LFC</text></svg>'


# ── DATA FETCHING ────────────────────────────────────────────────────────────
def fetch_json(url, fallback=None):
    try:
        r = requests.get(url, timeout=12, headers={"User-Agent": "LiverpoolLookout/1.0"})
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  Warning: Fetch failed {url}: {e}")
        return fallback or {}

def fetch_fixtures():
    data = fetch_json(f"https://www.thesportsdb.com/api/v1/json/3/eventsnext.php?id={TEAM_ID}")
    return data.get("events", [])[:5]

def fetch_last_results():
    data = fetch_json(f"https://www.thesportsdb.com/api/v1/json/3/eventslast.php?id={TEAM_ID}")
    return data.get("results", [])[:5]

def fetch_lfc_news_rss():
    try:
        r = requests.get(
            "https://feeds.bbci.co.uk/sport/football/teams/liverpool/rss.xml",
            timeout=12, headers={"User-Agent": "LiverpoolLookout/1.0"}
        )
        headlines = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", r.text)
        return [h for h in headlines if "Liverpool" in h or "LFC" in h][:8]
    except Exception:
        return []


# ── SLUG / FILE HELPERS ──────────────────────────────────────────────────────
def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:80].strip("-")

def get_existing_slugs():
    if not os.path.exists(CONTENT_DIR):
        return set()
    return {f.replace(".md", "") for f in os.listdir(CONTENT_DIR) if f.endswith(".md")}


# ── PROMPTS ──────────────────────────────────────────────────────────────────
# Kept short to reduce input tokens - only essential rules.
BASE = """You are a professional Liverpool FC journalist for LiverpoolLookout.com.
RULES: UK English. Name specific LFC players. Never fabricate scores/quotes/fees.
Label rumours: according to reports / sources suggest.
Respond ONLY with valid JSON matching the schema."""

_SCHEMA = ('{"meta_title":"(max 60 chars, include Liverpool or surname)",'
           '"title":"...","meta_description":"(max 155 chars)",'
           '"keywords":["k1","k2","k3","k4","k5"],'
           '"content":"...markdown...",'
           '"tags":["t1","t2","t3","t4","t5"],"category":"..."}')

PROMPTS = {
    "match_preview": lambda ctx: (
        f"{BASE}\n\nWrite a Liverpool FC MATCH PREVIEW (600-800 words).\n"
        f"Context: {json.dumps(ctx)}\n"
        f"Cover: expected lineup, key battles, tactics, form, prediction.\n"
        f"Return JSON: {_SCHEMA}"
    ),
    "match_report": lambda ctx: (
        f"{BASE}\n\nWrite a Liverpool FC MATCH REPORT (700-900 words).\n"
        f"Context: {json.dumps(ctx)}\n"
        f"Cover: narrative, goals, standout performers. End with ## Player Ratings.\n"
        f"Return JSON: {_SCHEMA}"
    ),
    "player_spotlight": lambda ctx: (
        f"{BASE}\n\nWrite a Liverpool FC PLAYER SPOTLIGHT (600-800 words) on {ctx.get('player','Mohamed Salah')}.\n"
        f"Context: {json.dumps(ctx)}\n"
        f"Cover: form, role, strengths, stats, fan verdict.\n"
        f"Return JSON: {_SCHEMA}"
    ),
    "transfer_news": lambda ctx: (
        f"{BASE}\n\nWrite a Liverpool FC TRANSFER NEWS piece (500-700 words).\n"
        f"Context: {json.dumps(ctx)}\n"
        f"Cover: targets/links, potential fees (label as rumours), Anfield fit.\n"
        f"Return JSON: {_SCHEMA}"
    ),
    "tactical_analysis": lambda ctx: (
        f"{BASE}\n\nWrite a Liverpool FC TACTICAL ANALYSIS (700-900 words).\n"
        f"Context: {json.dumps(ctx)}\n"
        f"Cover: Slot's system, pressing, build-up, set pieces.\n"
        f"Return JSON: {_SCHEMA}"
    ),
    "stats_analysis": lambda ctx: (
        f"{BASE}\n\nWrite a Liverpool FC STATS ANALYSIS (600-800 words).\n"
        f"Context: {json.dumps(ctx)}\n"
        f"One statistical theme. Use markdown tables where useful.\n"
        f"Return JSON: {_SCHEMA}"
    ),
    "team_news": lambda ctx: (
        f"{BASE}\n\nWrite a Liverpool FC TEAM NEWS update (400-600 words).\n"
        f"Context: {json.dumps(ctx)}\n"
        f"Cover: injuries, suspensions, fitness returns, rotation hints.\n"
        f"Return JSON: {_SCHEMA}"
    ),
    "historical": lambda ctx: (
        f"{BASE}\n\nWrite an ON THIS DAY / HISTORICAL article about Liverpool FC (700-900 words).\n"
        f"Context: {json.dumps(ctx)}\n"
        f"Choose a famous match, signing, trophy or moment. Rich storytelling.\n"
        f"Return JSON: {_SCHEMA}"
    ),
    "opinion": lambda ctx: (
        f"{BASE}\n\nWrite an OPINION COLUMN about Liverpool FC (550-750 words).\n"
        f"Context: {json.dumps(ctx)}\n"
        f"Clear stance, argument, counter-argument, verdict.\n"
        f"Return JSON: {_SCHEMA}"
    ),
    "youth_academy": lambda ctx: (
        f"{BASE}\n\nWrite a Liverpool FC ACADEMY article (500-700 words).\n"
        f"Context: {json.dumps(ctx)}\n"
        f"Cover rising talent from Liverpool's academy, U21s, or loan players.\n"
        f"Return JSON: {_SCHEMA}"
    ),
}


# ── API CALL ─────────────────────────────────────────────────────────────────
def api_call_with_retry(client, model, max_tokens, prompt, max_retries=4):
    """Exponential backoff on rate limit; immediate exit on billing errors."""
    for attempt in range(max_retries):
        try:
            return client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait = (2 ** attempt) * 10  # 10s, 20s, 40s
            print(f"  Rate limit. Waiting {wait}s (attempt {attempt+2}/{max_retries})...")
            time.sleep(wait)
        except (anthropic.PermissionDeniedError, anthropic.AuthenticationError) as e:
            print(f"  Billing/auth error - stopping run: {e}")
            raise
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and attempt < max_retries - 1:
                wait = (2 ** attempt) * 15
                print(f"  API overloaded. Waiting {wait}s...")
                time.sleep(wait)
            else:
                raise


# ── ARTICLE GENERATION ───────────────────────────────────────────────────────
def generate_article(client, article_type, context):
    prompt   = PROMPTS[article_type](context)
    model    = MODEL_FOR.get(article_type, MODEL_LIGHT)
    max_tok  = MAX_TOKENS.get(article_type, 900)
    last_err = None
    for attempt in range(3):
        try:
            msg = api_call_with_retry(client, model, max_tok, prompt)
            raw = msg.content[0].text.strip()
            raw = re.sub(r"^```json\s*", "", raw, flags=re.MULTILINE)
            raw = re.sub(r"\s*```$",     "", raw, flags=re.MULTILINE)
            return json.loads(raw.strip())
        except json.JSONDecodeError as e:
            last_err = e
            print(f"  JSON parse error (attempt {attempt+1}/3): {e}")
            if attempt < 2:
                time.sleep(3)
    raise last_err


def save_article(article, article_type, existing_slugs):
    now      = datetime.now(timezone.utc)
    iso_date = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    prefix   = now.strftime("%Y-%m-%d")
    title    = article.get("title", "Liverpool FC Update")
    slug     = f"{prefix}-{slugify(title)}"
    if slug in existing_slugs:
        slug = f"{slug}-{random.randint(100, 999)}"
    existing_slugs.add(slug)

    tags       = article.get("tags",     ["Liverpool FC", "LFC", "Premier League"])
    category   = article.get("category", "News")
    meta_title = article.get("meta_title", title)[:60]
    meta_desc  = article.get("meta_description", "")[:155]
    keywords   = article.get("keywords", ["Liverpool FC", "LFC", "Premier League", "Anfield", "Arne Slot"])
    content    = article.get("content",  "")
    svg        = get_animated_svg(article_type, title)

    tags_yaml     = "\n".join(f'  - "{t}"' for t in tags)
    keywords_yaml = "\n".join(f'  - "{k}"' for k in keywords)

    frontmatter = f"""---
title: "{title.replace(chr(34), chr(39))}"
meta_title: "{meta_title.replace(chr(34), chr(39))}"
date: {iso_date}
description: "{meta_desc.replace(chr(34), chr(39))}"
tags:
{tags_yaml}
keywords:
{keywords_yaml}
categories:
  - "{category}"
article_type: "{article_type}"
draft: false
sitemap:
  changefreq: daily
  priority: 0.8
---
"""
    illustration = f'\n<div class="article-illustration">\n{svg}\n</div>\n\n'
    full_content = frontmatter + illustration + content

    os.makedirs(CONTENT_DIR, exist_ok=True)
    filepath = os.path.join(CONTENT_DIR, slug + ".md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_content)
    return slug + ".md"


# ── ARTICLE PLAN ─────────────────────────────────────────────────────────────
def build_article_plan(fixtures, results, headlines):
    base = {
        "team":        TEAM_NAME,
        "manager":     MANAGER,
        "stadium":     STADIUM,
        "season":      SEASON,
        "key_players": KEY_PLAYERS,
        "departed":    DEPARTED_PLAYERS,
        "headlines":   headlines[:5],
        "today":       datetime.now(timezone.utc).strftime("%d %B %Y"),
    }
    next_match  = fixtures[0] if fixtures else {}
    last_result = results[0]  if results  else {}
    recent      = results[:3] if results  else []
    players     = KEY_PLAYERS.copy()
    random.shuffle(players)

    candidates = []

    # Only include match_report if we actually have result data
    if last_result:
        candidates.append(("match_report", {**base, "last_result": last_result, "recent_results": recent}))

    candidates += [
        ("match_preview",    {**base, "next_match": next_match, "recent_form": recent}),
        ("player_spotlight", {**base, "player": players[0], "recent_results": recent}),
        ("player_spotlight", {**base, "player": players[1]}),
        ("transfer_news",    {**base, "focus": "incomings - specific player links and fit at Anfield"}),
        ("transfer_news",    {**base, "focus": "outgoings and contract situations"}),
        ("tactical_analysis",{**base, "recent_results": recent}),
        ("stats_analysis",   {**base, "metric_theme": random.choice([
            "Salah goal contributions vs top scorers",
            "Liverpool xG and xGA vs top 6",
            "Gravenberch progressive passes",
            "Liverpool pressing PPDA stats",
            "Van Dijk aerial duels and clearances",
        ])}),
        ("team_news",     {**base, "upcoming": next_match}),
        ("historical",    {**base, "era_hint": random.choice([
            "Shankly era (1959-74)", "Paisley golden age (1974-83)",
            "Dalglish era", "Gerrard years (2000s)",
            "Klopp era (2015-2024)", "Slot debut season (2024-25)",
        ])}),
        ("opinion",       {**base, "last_result": last_result, "topic": random.choice([
            "Why Salah is irreplaceable for Liverpool FC",
            "Is Slot already better than Klopp?",
            "Liverpool's must-have summer transfer priorities",
            "The academy player ready for Slot's first team",
        ])}),
        ("youth_academy", {**base, "player_hint": random.choice(
            ["Ben Doak", "Bobby Clark", "Luke Chambers", "James McConnell", "Trey Nyoni"]
        )}),
    ]

    # Always include match_preview; shuffle rest; take ARTICLES_PER_RUN total
    priority  = [c for c in candidates if c[0] == "match_preview"]
    remainder = [c for c in candidates if c[0] != "match_preview"]
    random.shuffle(remainder)
    return (priority + remainder)[:ARTICLES_PER_RUN]


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print("Fetching Liverpool FC data...")
    fixtures  = fetch_fixtures()
    results   = fetch_last_results()
    headlines = fetch_lfc_news_rss()
    print(f"  {len(fixtures)} fixtures, {len(results)} results, {len(headlines)} headlines")

    plan           = build_article_plan(fixtures, results, headlines)
    existing_slugs = get_existing_slugs()
    print(f"  {len(existing_slugs)} existing articles | generating {len(plan)} this run")

    generated, errors = 0, 0
    for i, (article_type, context) in enumerate(plan, 1):
        print(f"[{i}/{len(plan)}] {article_type}...")
        try:
            article  = generate_article(client, article_type, context)
            filename = save_article(article, article_type, existing_slugs)
            print(f"  Saved: {filename}")
            generated += 1
            if i < len(plan):
                time.sleep(2)
        except (anthropic.PermissionDeniedError, anthropic.AuthenticationError):
            print("  STOPPING: billing/auth error - no more API calls.")
            break
        except json.JSONDecodeError as e:
            print(f"  JSON error: {e}")
            errors += 1
        except Exception as e:
            print(f"  Error: {e}")
            errors += 1

    print("=" * 50)
    print(f"Generated: {generated} | Errors: {errors}")
    print("=" * 50)
    if generated == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
