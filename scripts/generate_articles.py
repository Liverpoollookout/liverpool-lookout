#!/usr/bin/env python3
"""
Liverpool Lookout - Automated Content Generator
Runs twice daily via GitHub Actions.
Generates 10 SEO-optimised articles per run using Claude API + free football data APIs.
Includes animated SVG illustrations for each article category.
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

# CONFIG
TEAM_ID = "133602"
TEAM_NAME = "Liverpool FC"
MANAGER = "Arne Slot"
STADIUM = "Anfield"
SEASON = "2025-26"
CONTENT_DIR = "site/content/posts"
STATIC_DIR = "site/static"
IMAGES_DIR = "site/static/images/articles"

# Current 2025-26 squad - updated March 2025
# IMPORTANT: Trent Alexander-Arnold left for Real Madrid in summer 2024.
# Do NOT include departed players here.
KEY_PLAYERS = [
    "Mohamed Salah",
    "Virgil van Dijk",
    "Alisson Becker",
    "Dominik Szoboszlai",
    "Darwin Nunez",
    "Luis Diaz",
    "Ryan Gravenberch",
    "Alexis Mac Allister",
    "Cody Gakpo",
    "Joe Gomez",
    "Ibrahima Konate",
    "Harvey Elliott",
    "Jarell Quansah",
    "Caoimhin Kelleher",
    "Federico Chiesa",
    "Konstantinos Tsimikas",
    "Conor Bradley",
    "Curtis Jones",
    "Wataru Endo",
    "Diogo Jota"
]

# Players who have LEFT Liverpool - NEVER write about them as current squad members
DEPARTED_PLAYERS = [
    "Trent Alexander-Arnold (left for Real Madrid, summer 2024)",
    "Joel Matip (left 2024)",
    "Thiago Alcantara (left 2024)",
    "James Milner (left 2023)",
    "Jordan Henderson (left 2023)",
    "Fabinho (left 2023)",
    "Roberto Firmino (left 2023)",
    "Naby Keita (left 2023)",
    "Alex Oxlade-Chamberlain (left 2023)",
]

ARTICLE_TYPES = [
    "match_preview", "match_report", "player_spotlight", "transfer_news",
    "tactical_analysis", "stats_analysis", "team_news", "historical",
    "opinion", "youth_academy"
]

CATEGORIES = {
    "match_preview": "Match Previews",
    "match_report": "Match Reports",
    "player_spotlight": "Player Analysis",
    "transfer_news": "Transfer News",
    "tactical_analysis": "Tactical Analysis",
    "stats_analysis": "Stats & Data",
    "team_news": "Team News",
    "historical": "History",
    "opinion": "Opinion",
    "youth_academy": "Academy"
}

# ANIMATED SVG ILLUSTRATIONS
def get_animated_svg(article_type, title=""):
    svgs = {
        "match_preview": _svg_match_preview,
        "match_report": _svg_match_report,
        "player_spotlight": _svg_player_spotlight,
        "transfer_news": _svg_transfer_news,
        "tactical_analysis": _svg_tactical_analysis,
        "stats_analysis": _svg_stats_analysis,
        "team_news": _svg_team_news,
        "historical": _svg_historical,
        "opinion": _svg_opinion,
        "youth_academy": _svg_academy,
    }
    fn = svgs.get(article_type, _svg_default)
    return fn()

def _svg_match_preview():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#2d7a2d" rx="8"/><rect x="60" y="40" width="680" height="320" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="2"/><circle cx="400" cy="200" r="60" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="2"/><line x1="400" y1="40" x2="400" y2="360" stroke="rgba(255,255,255,0.5)" stroke-width="2"/><circle cx="400" cy="200" r="16" fill="white" stroke="#333" stroke-width="2"><animate attributeName="cx" values="200;600;200" dur="3s" repeatCount="indefinite"/><animate attributeName="cy" values="200;120;200" dur="3s" repeatCount="indefinite"/></circle><text x="400" y="210" text-anchor="middle" font-family="Arial Black,sans-serif" font-size="28" font-weight="900" fill="white">MATCH PREVIEW</text><rect x="290" y="50" width="220" height="50" rx="6" fill="#C8102E" opacity="0.9"/><text x="400" y="82" text-anchor="middle" font-family="Arial,sans-serif" font-size="16" font-weight="700" fill="white">COMING UP</text></svg>'

def _svg_match_report():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#111111" rx="8"/><rect x="200" y="80" width="400" height="180" rx="12" fill="rgba(0,0,0,0.5)"/><text x="300" y="200" text-anchor="middle" font-family="Arial Black,sans-serif" font-size="72" font-weight="900" fill="white">LFC</text><text x="400" y="200" text-anchor="middle" font-family="Arial Black,sans-serif" font-size="48" font-weight="900" fill="#C8102E">VS</text><text x="500" y="200" text-anchor="middle" font-family="Arial Black,sans-serif" font-size="72" font-weight="900" fill="#aaa">OPP</text><text x="400" y="320" text-anchor="middle" font-family="Arial,sans-serif" font-size="20" font-weight="700" fill="white" letter-spacing="4">MATCH REPORT</text></svg>'

def _svg_player_spotlight():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#111" rx="8"/><text x="400" y="330" text-anchor="middle" font-family="Arial,sans-serif" font-size="22" fill="#F6EB61">&#9733; &#9733; &#9733; &#9733; &#9733;</text><text x="400" y="360" text-anchor="middle" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="white" letter-spacing="3">PLAYER SPOTLIGHT</text><ellipse cx="400" cy="180" rx="200" ry="180" fill="#C8102E" opacity="0.15"/><circle cx="400" cy="140" r="40" fill="#C8102E" opacity="0.7"/><rect x="370" y="178" width="60" height="80" rx="10" fill="#C8102E" opacity="0.7"/></svg>'

def _svg_transfer_news():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#0a0a2e" rx="8"/><path d="M 250 200 L 550 200" stroke="#C8102E" stroke-width="4" fill="none" stroke-dasharray="10,5"><animate attributeName="stroke-dashoffset" values="0;-60" dur="1s" repeatCount="indefinite"/></path><polygon points="560,190 580,200 560,210" fill="#C8102E"/><rect x="100" y="165" width="130" height="70" rx="8" fill="rgba(200,16,46,0.8)"/><text x="165" y="205" text-anchor="middle" font-family="Arial Black,sans-serif" font-size="16" font-weight="900" fill="white">SELLING</text><rect x="570" y="165" width="130" height="70" rx="8" fill="rgba(200,16,46,0.8)"/><text x="635" y="205" text-anchor="middle" font-family="Arial Black,sans-serif" font-size="16" font-weight="900" fill="white">ANFIELD</text><text x="400" y="320" text-anchor="middle" font-family="Arial,sans-serif" font-size="18" font-weight="700" fill="white" letter-spacing="4">TRANSFER NEWS</text></svg>'

def _svg_tactical_analysis():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#1a1a2e" rx="8"/><rect x="80" y="40" width="640" height="320" rx="6" fill="#2d7a2d"/><rect x="100" y="60" width="600" height="280" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/><circle cx="400" cy="200" r="50" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/><circle cx="200" cy="200" r="12" fill="#C8102E"/><circle cx="300" cy="130" r="12" fill="#C8102E"/><circle cx="300" cy="200" r="12" fill="#C8102E"/><circle cx="300" cy="270" r="12" fill="#C8102E"/><circle cx="430" cy="130" r="12" fill="#C8102E"/><circle cx="430" cy="200" r="12" fill="#C8102E"/><circle cx="430" cy="270" r="12" fill="#C8102E"/><circle cx="550" cy="160" r="12" fill="#C8102E"/><circle cx="550" cy="240" r="12" fill="#C8102E"/><text x="400" y="385" text-anchor="middle" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="white" letter-spacing="3">TACTICAL ANALYSIS</text></svg>'

def _svg_stats_analysis():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#0d1117" rx="8"/><rect x="80" y="140" width="60" height="180" fill="#C8102E"/><rect x="160" y="100" width="60" height="220" fill="#C8102E" opacity="0.85"/><rect x="240" y="160" width="60" height="160" fill="#C8102E" opacity="0.7"/><rect x="320" y="60" width="60" height="260" fill="#C8102E" opacity="0.9"/><rect x="400" y="120" width="60" height="200" fill="#C8102E" opacity="0.75"/><rect x="480" y="80" width="60" height="240" fill="#C8102E" opacity="0.8"/><rect x="560" y="130" width="60" height="190" fill="#4CAF50" opacity="0.8"/><rect x="640" y="50" width="60" height="270" fill="#4CAF50" opacity="0.9"/><line x1="70" y1="320" x2="740" y2="320" stroke="rgba(255,255,255,0.3)" stroke-width="1"/><text x="400" y="370" text-anchor="middle" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="white" letter-spacing="3">STATS &amp; DATA</text></svg>'

def _svg_team_news():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#111827" rx="8"/><rect x="60" y="40" width="680" height="300" rx="6" fill="white" opacity="0.95"/><rect x="60" y="40" width="680" height="55" rx="6" fill="#C8102E"/><text x="400" y="78" text-anchor="middle" font-family="Arial Black,sans-serif" font-size="22" font-weight="900" fill="white" letter-spacing="2">TEAM NEWS</text><circle cx="120" cy="67" r="8" fill="#ff0"><animate attributeName="opacity" values="1;0.2;1" dur="0.8s" repeatCount="indefinite"/></circle><rect x="90" y="115" width="400" height="14" rx="4" fill="#e0e0e0"/><rect x="90" y="140" width="500" height="14" rx="4" fill="#e0e0e0"/><rect x="90" y="165" width="350" height="14" rx="4" fill="#e0e0e0"/><rect x="90" y="190" width="450" height="14" rx="4" fill="#e0e0e0"/><rect x="90" y="215" width="300" height="14" rx="4" fill="#e0e0e0"/></svg>'

def _svg_historical():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#1a0a00" rx="8"/><g transform="translate(400,200)"><path d="M-40,-80 Q-50,-40 -30,0 L-20,30 L-5,30 L-5,50 L-25,50 L-25,65 L25,65 L25,50 L5,50 L5,30 L20,30 L30,0 Q50,-40 40,-80 Z" fill="#F6EB61" opacity="0.9"/><path d="M-40,-50 Q-65,-50 -65,-20 Q-65,10 -30,0" stroke="#F6EB61" stroke-width="8" fill="none"/><path d="M40,-50 Q65,-50 65,-20 Q65,10 30,0" stroke="#F6EB61" stroke-width="8" fill="none"/></g><text x="400" y="340" text-anchor="middle" font-family="Georgia,serif" font-size="16" font-style="italic" fill="#F6EB61" opacity="0.9">On This Day in Liverpool FC History</text><rect x="30" y="20" width="740" height="360" rx="8" fill="none" stroke="#F6EB61" stroke-width="2" stroke-dasharray="10,6" opacity="0.4"/></svg>'

def _svg_opinion():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#1a1a2e" rx="8"/><rect x="60" y="80" width="280" height="160" rx="16" fill="#C8102E"/><polygon points="100,240 80,280 140,240" fill="#C8102E"/><text x="200" y="150" text-anchor="middle" font-family="Georgia,serif" font-size="48" fill="white" opacity="0.9">"</text><text x="200" y="195" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" fill="white">My View...</text><rect x="460" y="120" width="280" height="160" rx="16" fill="#444"/><polygon points="700,280 720,320 660,280" fill="#444"/><text x="600" y="190" text-anchor="middle" font-family="Georgia,serif" font-size="48" fill="white" opacity="0.6">"</text><text x="600" y="235" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" fill="#ccc">Counter point...</text><text x="400" y="215" text-anchor="middle" font-family="Arial Black,sans-serif" font-size="32" font-weight="900" fill="white">VS</text><text x="400" y="360" text-anchor="middle" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="white" letter-spacing="4">OPINION</text></svg>'

def _svg_academy():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#0d2137" rx="8"/><text x="400" y="60" text-anchor="middle" font-family="Arial Black,sans-serif" font-size="14" font-weight="700" fill="#F6EB61" letter-spacing="4">STARS OF THE FUTURE</text><g transform="translate(400,260)"><circle cx="0" cy="-40" r="16" fill="#C8102E" opacity="0.85"/><rect x="-12" y="-24" width="24" height="35" rx="6" fill="#C8102E" opacity="0.85"/></g><text x="400" y="360" text-anchor="middle" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="white" letter-spacing="3">ACADEMY &amp; YOUTH</text></svg>'

def _svg_default():
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg"><rect width="800" height="400" fill="#C8102E" rx="8"/><text x="400" y="210" text-anchor="middle" font-family="Arial Black,sans-serif" font-size="42" font-weight="900" fill="white">LFC</text><text x="400" y="360" text-anchor="middle" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="white" letter-spacing="4">LIVERPOOL LOOKOUT</text></svg>'

# DATA FETCHING
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

def fetch_squad():
    data = fetch_json(f"https://www.thesportsdb.com/api/v1/json/3/lookup_all_players.php?id={TEAM_ID}")
    players = data.get("player", []) or []
    return [p for p in players if p.get("strStatus") == "Active"]

def fetch_lfc_news_rss():
    try:
        r = requests.get(
            "https://feeds.bbci.co.uk/sport/football/teams/liverpool/rss.xml",
            timeout=12,
            headers={"User-Agent": "LiverpoolLookout/1.0"}
        )
        headlines = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", r.text)
        return [h for h in headlines if "Liverpool" in h or "LFC" in h][:10]
    except Exception:
        return []

# SLUG / FILE HELPERS
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

def date_slug_prefix():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

# ARTICLE PROMPTS
BASE_INSTRUCTIONS = """
You are a professional football journalist specialising in Liverpool FC for LiverpoolLookout.com.
CRITICAL RULES you MUST follow on every article:
- Every article MUST be specifically about Liverpool FC: players, staff, matches, tactics, transfers, or history. NEVER write generic football content.
- Always name specific Liverpool FC players from the key_players list in context.
- Always use UK English spelling (colour, defence, favour, etc.).
- Never fabricate specific scorelines, direct quotes, or confirmed transfer fees unless provided in context.
- Label all transfer rumours clearly: use "according to reports", "sources suggest", "it is claimed".
- Every JSON response MUST include: meta_title (max 60 chars, must contain "Liverpool" or a player surname), meta_description (max 155 chars, LFC-focused), keywords (5 specific LFC tags).
"""

PROMPTS = {
    "match_preview": lambda ctx: f"""{BASE_INSTRUCTIONS}
Write a Liverpool FC MATCH PREVIEW article (650-850 words).
Context data: {json.dumps(ctx, indent=2)}
Cover: expected lineups, key battles, tactical approach, recent form, prediction.
Make the headline compelling and include both team names.
End with a confident prediction section.
Return ONLY valid JSON: {{"meta_title": "...(max 60 chars, must include 'Liverpool' or player surname)", "title": "...", "meta_description": "...(max 155 chars, LFC-specific)", "keywords": ["lfc-kw1","kw2","kw3","kw4","kw5"], "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Match Previews"}}
""",
    "match_report": lambda ctx: f"""{BASE_INSTRUCTIONS}
Write a Liverpool FC MATCH REPORT article (750-950 words).
Context data: {json.dumps(ctx, indent=2)}
Cover: match narrative, key moments, goals, standout performers, manager reaction tone.
Include a "## Player Ratings" section (1-10) at the end.
Return ONLY valid JSON: {{"meta_title": "...(max 60 chars, must include 'Liverpool' or player surname)", "title": "...", "meta_description": "...(max 155 chars, LFC-specific)", "keywords": ["lfc-kw1","kw2","kw3","kw4","kw5"], "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Match Reports"}}
""",
    "player_spotlight": lambda ctx: f"""{BASE_INSTRUCTIONS}
Write a Liverpool FC PLAYER SPOTLIGHT article (650-850 words).
Focus player: {ctx.get("player", "Mohamed Salah")}
Context data: {json.dumps(ctx, indent=2)}
Cover: recent form, role in the team, strengths, areas to improve, statistics context, fan verdict.
Return ONLY valid JSON: {{"meta_title": "...(max 60 chars, must include 'Liverpool' or player surname)", "title": "...", "meta_description": "...(max 155 chars, LFC-specific)", "keywords": ["lfc-kw1","kw2","kw3","kw4","kw5"], "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Player Analysis"}}
""",
    "transfer_news": lambda ctx: f"""{BASE_INSTRUCTIONS}
Write a Liverpool FC TRANSFER NEWS article (550-750 words).
Context data: {json.dumps(ctx, indent=2)}
Cover: potential targets, reported links, likely fees (use "reported" language), how they would fit at Anfield.
Be responsible - clearly label rumours vs confirmed news.
Return ONLY valid JSON: {{"meta_title": "...(max 60 chars, must include 'Liverpool' or player surname)", "title": "...", "meta_description": "...(max 155 chars, LFC-specific)", "keywords": ["lfc-kw1","kw2","kw3","kw4","kw5"], "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Transfer News"}}
""",
    "tactical_analysis": lambda ctx: f"""{BASE_INSTRUCTIONS}
Write a Liverpool FC TACTICAL ANALYSIS article (750-950 words).
Context data: {json.dumps(ctx, indent=2)}
Cover: Arne Slot's system (4-2-3-1 / 4-3-3 hybrid), pressing triggers, build-up patterns, set-piece routines.
Use proper tactical terminology.
Return ONLY valid JSON: {{"meta_title": "...(max 60 chars, must include 'Liverpool' or player surname)", "title": "...", "meta_description": "...(max 155 chars, LFC-specific)", "keywords": ["lfc-kw1","kw2","kw3","kw4","kw5"], "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Tactical Analysis"}}
""",
    "stats_analysis": lambda ctx: f"""{BASE_INSTRUCTIONS}
Write a Liverpool FC STATS AND DATA article (650-850 words).
Context data: {json.dumps(ctx, indent=2)}
Focus on one statistical theme. Use plausible, contextually appropriate statistics.
Clearly present stats in markdown tables where appropriate.
Return ONLY valid JSON: {{"meta_title": "...(max 60 chars, must include 'Liverpool' or player surname)", "title": "...", "meta_description": "...(max 155 chars, LFC-specific)", "keywords": ["lfc-kw1","kw2","kw3","kw4","kw5"], "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Stats & Data"}}
""",
    "team_news": lambda ctx: f"""{BASE_INSTRUCTIONS}
Write a Liverpool FC TEAM NEWS article (450-650 words).
Context data: {json.dumps(ctx, indent=2)}
Cover: injury updates, returns from fitness, suspensions, squad rotation plans.
Return ONLY valid JSON: {{"meta_title": "...(max 60 chars, must include 'Liverpool' or player surname)", "title": "...", "meta_description": "...(max 155 chars, LFC-specific)", "keywords": ["lfc-kw1","kw2","kw3","kw4","kw5"], "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Team News"}}
""",
    "historical": lambda ctx: f"""{BASE_INSTRUCTIONS}
Write an "On This Day" or HISTORICAL RETROSPECTIVE article about Liverpool FC (750-950 words).
Context data: {json.dumps(ctx, indent=2)}
Choose a famous match, signing, trophy, or moment in Liverpool history. Rich storytelling approach.
Return ONLY valid JSON: {{"meta_title": "...(max 60 chars, must include 'Liverpool' or player surname)", "title": "...", "meta_description": "...(max 155 chars, LFC-specific)", "keywords": ["lfc-kw1","kw2","kw3","kw4","kw5"], "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "History"}}
""",
    "opinion": lambda ctx: f"""{BASE_INSTRUCTIONS}
Write an OPINION COLUMN article about Liverpool FC (600-800 words).
Context data: {json.dumps(ctx, indent=2)}
Take a clear, well-argued stance on a topical Liverpool FC debate.
Structure: hook intro, argument, counter-argument, your verdict.
Return ONLY valid JSON: {{"meta_title": "...(max 60 chars, must include 'Liverpool' or player surname)", "title": "...", "meta_description": "...(max 155 chars, LFC-specific)", "keywords": ["lfc-kw1","kw2","kw3","kw4","kw5"], "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Opinion"}}
""",
    "youth_academy": lambda ctx: f"""{BASE_INSTRUCTIONS}
Write a Liverpool FC ACADEMY AND YOUTH article (550-750 words).
Context data: {json.dumps(ctx, indent=2)}
Cover rising talent from Liverpool's academy, U21s, or loan players.
Return ONLY valid JSON: {{"meta_title": "...(max 60 chars, must include 'Liverpool' or player surname)", "title": "...", "meta_description": "...(max 155 chars, LFC-specific)", "keywords": ["lfc-kw1","kw2","kw3","kw4","kw5"], "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Academy"}}
""",
}

# GENERATION

def generate_illustration(client, article_type, context, slug):
    """Generate a unique SVG sketch illustration of the player/subject for this article."""
    if not client:
        return None
    subject = context.get("player", context.get("focus", "Liverpool FC"))
    # Build a descriptive subject string
    if isinstance(subject, list):
        subject = subject[0] if subject else "Liverpool FC"
    subject = str(subject)[:80]
    prompt = (
        "You are an SVG illustrator. Create a stylised sketch/drawing illustration for a Liverpool FC blog post.\n\n"
        f"Subject: {subject}\n"
        f"Article type: {article_type}\n\n"
        "REQUIREMENTS:\n"
        "- Return ONLY a valid SVG element, nothing else. No markdown, no explanation.\n"
        "- viewBox=\"0 0 800 420\"\n"
        "- Dark navy background (#0a1628)\n"
        "- Sketch/drawing style using strokes and shapes\n"
        "- If subject is a player: draw a simplified sketched figure in Liverpool red kit (#C8102E)\n"
        "- If tactical/stats: draw a stylised pitch diagram with Liverpool red accents\n"
        "- If transfer news: draw a figure silhouette with directional arrows\n"
        "- Include Liverpool FC colours: red #C8102E, white #FFFFFF, navy #0a1628, gold #F6EB61\n"
        "- Add the subject name as text in the illustration\n"
        "- SVG must be self-contained (no external images, no external fonts)\n"
        "- Add class=\"article-svg\" to the svg element\n"
        "- Return only raw SVG starting with <svg and ending with </svg>"
    )
    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = message.content[0].text.strip()
        raw = re.sub(r"^```(?:svg|xml|html)?\s*", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
        raw = raw.strip()
        # Sanitize XML entities - replace bare & with &amp; to prevent invalid SVG
        raw = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', '&amp;', raw)
        if not raw.startswith("<svg"):
            m = re.search(r"(<svg[\s\S]*?</svg>)", raw)
            raw = m.group(1) if m else None
        if not raw:
            return None
        os.makedirs(IMAGES_DIR, exist_ok=True)
        img_path = os.path.join(IMAGES_DIR, slug + ".svg")
        with open(img_path, "w", encoding="utf-8") as f:
            f.write(raw)
        return "/images/articles/" + slug + ".svg"
    except Exception as e:
        print("  Warning: illustration failed: " + str(e))
        return None
def generate_article(client, article_type, context):
    prompt_fn = PROMPTS.get(article_type, PROMPTS["team_news"])
    prompt = prompt_fn(context)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = message.content[0].text.strip()
    raw = re.sub(r"^```json\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()
    return json.loads(raw)

def save_article(article, article_type, existing_slugs, client=None, context=None):
    now = datetime.now(timezone.utc)
    iso_date = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    prefix = now.strftime("%Y-%m-%d")
    title = article.get("title", "Liverpool FC Update")
    slug_base = slugify(title)
    slug = f"{prefix}-{slug_base}"
    if slug in existing_slugs:
        slug = f"{slug}-{random.randint(100, 999)}"
    existing_slugs.add(slug)
    filename = f"{slug}.md"
    filepath = os.path.join(CONTENT_DIR, filename)
    # Generate unique illustration for this article
    image_path = generate_illustration(client, article_type, context or {}, slug) if client else None
    tags = article.get("tags", ["Liverpool FC", "LFC", "Premier League"])
    category = article.get("category", "News")
    meta_title = article.get("meta_title", title)[:60]
    meta_desc = article.get("meta_description", "")[:155]
    keywords = article.get("keywords", ["Liverpool FC", "LFC", "Premier League", "Anfield", "Arne Slot"])
    content_body = article.get("content", "")
    svg_content = get_animated_svg(article_type, title)
    tags_yaml = "\n".join(f'  - "{t}"' for t in tags)
    keywords_yaml = "\n".join(f'  - "{k}"' for k in keywords)
    image_fm = ('\nimage: "' + image_path + '"') if image_path else ""
    frontmatter = f"""---
title: "{title.replace(chr(34), chr(39))}"
meta_title: "{meta_title.replace(chr(34), chr(39))}"
date: {iso_date}
description: "{meta_desc.replace(chr(34), chr(39))}"{image_fm}
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
    full_content = frontmatter + f'\n<div class="article-illustration">\n{svg_content}\n</div>\n\n' + content_body
    os.makedirs(CONTENT_DIR, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_content)
    return filename

# ARTICLE PLAN
def build_article_plan(fixtures, results, headlines):
    base = {
        "team": TEAM_NAME,
        "manager": MANAGER,
        "stadium": STADIUM,
        "season": SEASON,
        "key_players": KEY_PLAYERS,
        "departed_players": DEPARTED_PLAYERS,
        "recent_headlines": headlines[:5],
        "today": datetime.now(timezone.utc).strftime("%d %B %Y"),
        "day_of_week": datetime.now(timezone.utc).strftime("%A"),
    }
    next_match = fixtures[0] if fixtures else {}
    last_result = results[0] if results else {}
    recent_results = results[:3] if results else []
    players_pool = KEY_PLAYERS.copy()
    random.shuffle(players_pool)

    # Full pool of Liverpool-specific article types
    all_articles = [
        ("match_preview", {**base, "next_match": next_match, "recent_form": recent_results, "focus": "detailed Liverpool FC match preview with lineup predictions, key player battles and Slot's tactical approach"}),
        ("match_report", {**base, "last_result": last_result, "recent_results": recent_results, "focus": "Liverpool FC match report - player ratings, key moments, Slot tactical decisions"}),
        ("player_spotlight", {**base, "player": players_pool[0], "recent_results": recent_results, "focus": "current season form, statistics and contribution to Liverpool FC"}),
        ("player_spotlight", {**base, "player": players_pool[1], "focus": "role in Liverpool FC system, strengths, areas for improvement this season"}),
        ("transfer_news", {**base, "focus": "Liverpool FC transfer targets - specific player links to Anfield, fee estimates, likelihood", "rumour_tier": "Tier 1-2 links from credible sources"}),
        ("transfer_news", {**base, "focus": "Liverpool FC transfer rumours - outgoings, contract situations, potential departures from Anfield", "rumour_tier": "Tier 2 links"}),
        ("tactical_analysis", {**base, "recent_results": recent_results, "focus": "Liverpool FC tactical breakdown - Slot 4-2-3-1 or 4-3-3 system, pressing triggers, build-up patterns, set pieces"}),
        ("stats_analysis", {**base, "focus": "Liverpool FC player statistics deep dive", "metric_theme": random.choice(["Salah goal contributions vs Premier League top scorers", "Liverpool xG and xGA vs top 6", "Gravenberch progressive passes and ball recoveries", "Liverpool pressing intensity and PPDA stats", "Van Dijk aerial duels and clearances", "Liverpool goals from set pieces this season", "Szoboszlai shot-creating actions and key passes"])}),
        ("team_news", {**base, "upcoming": next_match, "focus": "Liverpool FC injury and fitness update - availability for next fixture, expected return dates, Slot press conference hints"}),
        ("historical", {**base, "focus": "famous Liverpool FC moment, legendary player or iconic match from Anfield history", "era_hint": random.choice(["Shankly era (1959-74)", "Paisley golden age (1974-83)", "Dalglish era", "Gerrard years (2000s)", "Klopp era (2015-2024)", "Slot's debut season (2024-25)"])}),
        ("opinion", {**base, "last_result": last_result, "topic": random.choice(["Why Salah is irreplaceable for Liverpool FC", "Is Slot already better than Klopp?", "Liverpool's must-have summer transfer priorities", "Why Van Dijk deserves the Ballon d'Or vote", "Liverpool's title credentials - a realistic assessment", "The academy player ready for Slot's first team"])}),
        ("youth_academy", {**base, "focus": "Liverpool FC Academy graduate scouting report and first-team potential", "player_hint": random.choice(["Ben Doak", "Bobby Clark", "Luke Chambers", "James McConnell", "Trey Nyoni"])}),
    ]
    # Always include a match_report; fill remaining 2 slots from shuffled pool
    match_reports = [a for a in all_articles if a[0] == "match_report"]
    other_articles = [a for a in all_articles if a[0] != "match_report"]
    random.shuffle(other_articles)
    return match_reports[:1] + other_articles[:2]

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
        sys.exit(1)
    client = anthropic.Anthropic(api_key=api_key)
    print("Fetching Liverpool FC data from TheSportsDB...")
    fixtures = fetch_fixtures()
    results = fetch_last_results()
    headlines = fetch_lfc_news_rss()
    print(f"  {len(fixtures)} upcoming fixtures, {len(results)} recent results, {len(headlines)} headlines")
    plan = build_article_plan(fixtures, results, headlines)
    existing_slugs = get_existing_slugs()
    print(f"  {len(existing_slugs)} existing articles found")
    generated, errors = 0, 0
    for i, (article_type, context) in enumerate(plan, 1):
        print(f"[{i}/{len(plan)}] Generating {article_type}...")
        try:
            article = generate_article(client, article_type, context)
            filename = save_article(article, article_type, existing_slugs, client=client, context=context)
            print(f"  Saved: {filename}")
            generated += 1
            time.sleep(1.5)
        except json.JSONDecodeError as e:
            print(f"  JSON parse error: {e}")
            errors += 1
        except Exception as e:
            print(f"  Error: {e}")
            errors += 1
    print(f"Generated: {generated} | Errors: {errors}")
    if generated == 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
