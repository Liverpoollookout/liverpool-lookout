#!/usr/bin/env python3
"""
Liverpool Lookout — Automated Content Generator
Runs twice daily via GitHub Actions.
Generates 10 SEO-optimised articles per run using Claude API + free football data APIs.
"""

import os
import sys
import json
import time
import random
import re
import requests
from datetime import datetime, timezone, timedelta
import anthropic

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
TEAM_ID = "133602"          # Liverpool FC on TheSportsDB
TEAM_NAME = "Liverpool FC"
MANAGER = "Arne Slot"
STADIUM = "Anfield"
SEASON = "2025-26"
CONTENT_DIR = "site/content/posts"

KEY_PLAYERS = [
    "Mohamed Salah", "Virgil van Dijk", "Alisson Becker",
    "Dominik Szoboszlai", "Darwin Núñez", "Luis Díaz",
    "Ryan Gravenberch", "Alexis Mac Allister", "Cody Gakpo",
    "Joe Gomez", "Ibrahima Konaté", "Trent Alexander-Arnold",
    "Harvey Elliott", "Jarell Quansah", "Caoimhin Kelleher"
]

ARTICLE_TYPES = [
    "match_preview", "match_report", "player_spotlight",
    "transfer_news", "tactical_analysis", "stats_analysis",
    "team_news", "historical", "opinion", "youth_academy"
]

CATEGORIES = {
    "match_preview":    "Match Previews",
    "match_report":     "Match Reports",
    "player_spotlight": "Player Analysis",
    "transfer_news":    "Transfer News",
    "tactical_analysis":"Tactical Analysis",
    "stats_analysis":   "Stats & Data",
    "team_news":        "Team News",
    "historical":       "History",
    "opinion":          "Opinion",
    "youth_academy":    "Academy"
}

# ──────────────────────────────────────────────
# DATA FETCHING
# ──────────────────────────────────────────────

def fetch_json(url, fallback=None):
    try:
        r = requests.get(url, timeout=12, headers={"User-Agent": "LiverpoolLookout/1.0"})
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  ⚠ Fetch failed {url}: {e}")
        return fallback or {}

def fetch_fixtures():
    data = fetch_json(f"https://www.thesportsdb.com/api/v1/json/3/eventsnext.php?id={TEAM_ID}")
    return data.get("events", [])[:5]

def fetch_last_results():
    data = fetch_json(f"https://www.thesportsdb.com/api/v1/json/3/eventslast.php?id={TEAM_ID}")
    return data.get("results", [])[:5]

def fetch_squad():
    data = fetch_json(f"https://www.thesportsdb.com/api/v1/json/3/lookup_all_players.php?id={TEAM_ID}")
    players = data.get("player", []) or []
    return [p for p in players if p.get("strStatus") == "Active"]

def fetch_lfc_news_rss():
    """Pull headlines from BBC Sport RSS for context (no scraping needed)."""
    try:
        r = requests.get(
            "https://feeds.bbci.co.uk/sport/football/teams/liverpool/rss.xml",
            timeout=12, headers={"User-Agent": "LiverpoolLookout/1.0"}
        )
        headlines = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", r.text)
        # Strip feed title
        return [h for h in headlines if "Liverpool" in h or "LFC" in h][:10]
    except:
        return []

# ──────────────────────────────────────────────
# SLUG / FILE HELPERS
# ──────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:80].strip("-")

def get_existing_slugs() -> set:
    if not os.path.exists(CONTENT_DIR):
        return set()
    return {f.replace(".md", "") for f in os.listdir(CONTENT_DIR) if f.endswith(".md")}

def date_slug_prefix() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

# ──────────────────────────────────────────────
# ARTICLE PROMPTS
# ──────────────────────────────────────────────

BASE_INSTRUCTIONS = """
You are a professional football journalist specialising in Liverpool FC.
Write authoritative, engaging, original content for LiverpoolLookout.com.
Always use UK English spelling (colour, defence, favour, etc.).
Never make up specific scorelines, quotes from named people, or confirmed transfer fees unless given in context.
Use "according to reports", "sources suggest" for rumours.
"""

PROMPTS = {
    "match_preview": lambda ctx: f"""{BASE_INSTRUCTIONS}
Write a Liverpool FC MATCH PREVIEW article (650–850 words).
Context data: {json.dumps(ctx, indent=2)}
Cover: expected lineups, key battles, tactical approach, recent form, prediction.
Make the headline compelling and include both team names.
End with a confident prediction section.
Return ONLY valid JSON:
{{"title": "...", "meta_description": "...(max 155 chars)", "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Match Previews"}}
""",

    "match_report": lambda ctx: f"""{BASE_INSTRUCTIONS}
Write a Liverpool FC MATCH REPORT article (750–950 words).
Context data: {json.dumps(ctx, indent=2)}
Cover: match narrative, key moments, goals, standout performers, manager reaction tone.
Include a "## Player Ratings" section (1–10) at the end.
Return ONLY valid JSON:
{{"title": "...", "meta_description": "...(max 155 chars)", "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Match Reports"}}
""",

    "player_spotlight": lambda ctx: f"""{BASE_INSTRUCTIONS}
Write a Liverpool FC PLAYER SPOTLIGHT article (650–850 words).
Focus player: {ctx.get("player", "Mohamed Salah")}
Context data: {json.dumps(ctx, indent=2)}
Cover: recent form, role in the team, strengths, areas to improve, statistics context, fan verdict.
Return ONLY valid JSON:
{{"title": "...", "meta_description": "...(max 155 chars)", "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Player Analysis"}}
""",

    "transfer_news": lambda ctx: f"""{BASE_INSTRUCTIONS}
Write a Liverpool FC TRANSFER NEWS article (550–750 words).
Context data: {json.dumps(ctx, indent=2)}
Cover: potential targets, reported links, likely fees (use "reported" language), how they'd fit at Anfield.
Be responsible — clearly label rumours vs confirmed news.
Return ONLY valid JSON:
{{"title": "...", "meta_description": "...(max 155 chars)", "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Transfer News"}}
""",

    "tactical_analysis": lambda ctx: f"""{BASE_INSTRUCTIONS}
Write a Liverpool FC TACTICAL ANALYSIS article (750–950 words).
Context data: {json.dumps(ctx, indent=2)}
Cover: Arne Slot's system (4-2-3-1 / 4-3-3 hybrid), pressing triggers, build-up patterns, set-piece routines, comparison to Klopp era.
Use proper tactical terminology. Include a "## Key Tactical Principles" section.
Return ONLY valid JSON:
{{"title": "...", "meta_description": "...(max 155 chars)", "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Tactical Analysis"}}
""",

    "stats_analysis": lambda ctx: f"""{BASE_INSTRUCTIONS}
Write a Liverpool FC STATS & DATA article (650–850 words).
Context data: {json.dumps(ctx, indent=2)}
Focus on one statistical theme (xG, pressing stats, defensive solidity, attacking output, home vs away).
Use plausible, contextually appropriate statistics and comparisons to other top-6 clubs.
Clearly present stats in markdown tables where appropriate.
Return ONLY valid JSON:
{{"title": "...", "meta_description": "...(max 155 chars)", "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Stats & Data"}}
""",

    "team_news": lambda ctx: f"""{BASE_INSTRUCTIONS}
Write a Liverpool FC TEAM NEWS article (450–650 words).
Context data: {json.dumps(ctx, indent=2)}
Cover: injury updates, returns from fitness, suspensions, squad rotation plans.
Use "reported", "understood to be", "expected to" language. Do NOT invent specific medical diagnoses.
Return ONLY valid JSON:
{{"title": "...", "meta_description": "...(max 155 chars)", "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Team News"}}
""",

    "historical": lambda ctx: f"""{BASE_INSTRUCTIONS}
Write an "On This Day" or HISTORICAL RETROSPECTIVE article about Liverpool FC (750–950 words).
Context data: {json.dumps(ctx, indent=2)}
Choose a famous match, signing, trophy, or moment in Liverpool's history relevant to today's date or current season context.
Rich storytelling approach — bring the moment to life.
Return ONLY valid JSON:
{{"title": "...", "meta_description": "...(max 155 chars)", "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "History"}}
""",

    "opinion": lambda ctx: f"""{BASE_INSTRUCTIONS}
Write an OPINION / COLUMN article about Liverpool FC (600–800 words).
Context data: {json.dumps(ctx, indent=2)}
Take a clear, well-argued stance on a topical Liverpool FC debate (contract situation, summer targets, Slot's system, title race).
Structure: hook intro → argument → counter-argument → your verdict.
Return ONLY valid JSON:
{{"title": "...", "meta_description": "...(max 155 chars)", "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Opinion"}}
""",

    "youth_academy": lambda ctx: f"""{BASE_INSTRUCTIONS}
Write a Liverpool FC ACADEMY / YOUTH article (550–750 words).
Context data: {json.dumps(ctx, indent=2)}
Cover rising talent from Liverpool's academy, U21s, or loan players. Discuss their development path and first-team potential.
Return ONLY valid JSON:
{{"title": "...", "meta_description": "...(max 155 chars)", "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Academy"}}
""",
}

# ──────────────────────────────────────────────
# GENERATION
# ──────────────────────────────────────────────

def generate_article(client: anthropic.Anthropic, article_type: str, context: dict) -> dict:
    prompt_fn = PROMPTS.get(article_type, PROMPTS["team_news"])
    prompt = prompt_fn(context)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    # Strip markdown code fences if present
    raw = re.sub(r"^```json\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()

    return json.loads(raw)

def save_article(article: dict, existing_slugs: set) -> str | None:
    now = datetime.now(timezone.utc)
    iso_date = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    prefix = now.strftime("%Y-%m-%d")

    title = article.get("title", "Liverpool FC Update")
    slug_base = slugify(title)
    slug = f"{prefix}-{slug_base}"

    # Avoid collisions
    if slug in existing_slugs:
        slug = f"{slug}-{random.randint(100, 999)}"
    existing_slugs.add(slug)

    filename = f"{slug}.md"
    filepath = os.path.join(CONTENT_DIR, filename)

    tags = article.get("tags", ["Liverpool FC", "LFC", "Premier League"])
    category = article.get("category", "News")
    meta_desc = article.get("meta_description", "")[:155]
    content_body = article.get("content", "")

    # Add internal anchor text for SEO
    tags_yaml = "\n".join(f'  - "{t}"' for t in tags)

    frontmatter = f"""---
title: "{title.replace('"', "'")}"
date: {iso_date}
description: "{meta_desc.replace('"', "'")}"
tags:
{tags_yaml}
categories:
  - "{category}"
draft: false
sitemap:
  changefreq: daily
  priority: 0.8
---

"""

    os.makedirs(CONTENT_DIR, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(frontmatter + content_body)

    return filename

# ──────────────────────────────────────────────
# ARTICLE PLAN
# ──────────────────────────────────────────────

def build_article_plan(fixtures, results, headlines) -> list[tuple[str, dict]]:
    """Build 10 varied articles for this run."""

    base = {
        "team": TEAM_NAME,
        "manager": MANAGER,
        "stadium": STADIUM,
        "season": SEASON,
        "key_players": KEY_PLAYERS,
        "recent_headlines": headlines[:5],
        "today": datetime.now(timezone.utc).strftime("%d %B %Y"),
        "day_of_week": datetime.now(timezone.utc).strftime("%A"),
    }

    next_match = fixtures[0] if fixtures else {}
    last_result = results[0] if results else {}
    recent_results = results[:3] if results else []

    players_pool = KEY_PLAYERS.copy()
    random.shuffle(players_pool)

    plan = [
        ("match_preview", {
            **base,
            "next_match": next_match,
            "recent_form": recent_results,
            "focus": "detailed match preview with lineup predictions"
        }),
        ("player_spotlight", {
            **base,
            "player": players_pool[0],
            "recent_results": recent_results,
            "focus": "current season form and contribution"
        }),
        ("transfer_news", {
            **base,
            "focus": "summer transfer targets and potential incomings",
            "rumour_tier": "Tier 2-3 links from European clubs"
        }),
        ("tactical_analysis", {
            **base,
            "recent_results": recent_results,
            "focus": "pressing system, high line, and build-up play under Arne Slot"
        }),
        ("stats_analysis", {
            **base,
            "focus": "Premier League attacking statistics comparison — top 6 clubs",
            "metric_theme": random.choice([
                "xG and xGA", "pressing intensity", "goals from set pieces",
                "clean sheet ratio", "shots on target percentage"
            ])
        }),
        ("team_news", {
            **base,
            "upcoming": next_match,
            "focus": "injury and fitness update ahead of next fixture"
        }),
        ("historical", {
            **base,
            "focus": "famous Liverpool FC moment, signing or match from club history",
            "era_hint": random.choice([
                "Shankly era (1959-74)", "Paisley golden age (1974-83)",
                "Dalglish era", "Gerrard years (2000s)", "Klopp era (2015-2024)"
            ])
        }),
        ("player_spotlight", {
            **base,
            "player": players_pool[1],
            "focus": "xG contribution, progressive carries, and impact on pressing"
        }),
        ("opinion", {
            **base,
            "last_result": last_result,
            "topic": random.choice([
                "Is Slot's Liverpool better than Klopp's?",
                "The title race — can Liverpool hold on?",
                "Why Liverpool must prioritise the summer transfer window",
                "The case for promoting an academy player to first-team",
                "Liverpool's injury crisis: is the fixture calendar too demanding?"
            ])
        }),
        ("youth_academy", {
            **base,
            "focus": "Liverpool Academy graduates and current U21 standouts",
            "player_hint": random.choice([
                "Ben Doak", "Bobby Clark", "Luke Chambers", "James McConnell", "Trey Nyoni"
            ])
        }),
    ]

    random.shuffle(plan)
    return plan

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable is not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print("📡 Fetching Liverpool FC data from TheSportsDB...")
    fixtures = fetch_fixtures()
    results = fetch_last_results()
    headlines = fetch_lfc_news_rss()
    print(f"  ✓ {len(fixtures)} upcoming fixtures, {len(results)} recent results, {len(headlines)} headlines")

    plan = build_article_plan(fixtures, results, headlines)
    existing_slugs = get_existing_slugs()
    print(f"  ✓ {len(existing_slugs)} existing articles found\n")

    generated, errors = 0, 0

    for i, (article_type, context) in enumerate(plan, 1):
        print(f"[{i}/{len(plan)}] Generating {article_type}...")
        try:
            article = generate_article(client, article_type, context)
            filename = save_article(article, existing_slugs)
            print(f"  ✅ Saved: {filename}")
            generated += 1
            # Be polite to the API
            time.sleep(1.5)
        except json.JSONDecodeError as e:
            print(f"  ❌ JSON parse error: {e}")
            errors += 1
        except Exception as e:
            print(f"  ❌ Error: {e}")
            errors += 1

    print(f"\n{'='*50}")
    print(f"✅ Generated: {generated}  |  ❌ Errors: {errors}")
    print(f"{'='*50}")

    if generated == 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
